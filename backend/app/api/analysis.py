"""Analysis endpoints for processing 10-K filings."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.edgar import (
    get_edgar_client,
    EdgarError,
    TickerNotFoundError,
    FilingNotFoundError,
    RateLimitError,
)
from app.services.finance import get_financial_data, FinanceError
from app.services.vectorstore import get_vector_store, VectorStoreError
from app.services.claude import get_claude_client, ClaudeError

router = APIRouter()


class RiskFactor(BaseModel):
    category: str
    title: str
    description: str
    severity: str


class AnalysisResponse(BaseModel):
    ticker: str
    company_name: str
    filing_date: str
    financial_health_score: float
    metrics: dict
    risk_factors: list[RiskFactor]
    key_insights: list[str]
    recommendations: list[str]
    sections_indexed: int


class IndexRequest(BaseModel):
    ticker: str


class IndexResponse(BaseModel):
    ticker: str
    status: str
    sections_indexed: int
    filing_date: str


# In-memory status tracking for indexing
_indexing_status: dict[str, dict] = {}


def get_indexing_status(ticker: str) -> Optional[dict]:
    return _indexing_status.get(ticker.upper())


def set_indexing_status(ticker: str, status: dict):
    _indexing_status[ticker.upper()] = status


@router.post("/index", response_model=IndexResponse)
async def index_company(request: IndexRequest):
    """Index a company's 10-K filing for analysis."""
    ticker = request.ticker.upper()

    # Check if already indexed
    store = get_vector_store()
    if store.has_ticker(ticker):
        return IndexResponse(
            ticker=ticker,
            status="already_indexed",
            sections_indexed=0,
            filing_date="",
        )

    try:
        # Set status to processing
        set_indexing_status(ticker, {"status": "processing", "progress": 0})

        # Fetch filing info
        edgar = await get_edgar_client()
        filing_info = await edgar.get_latest_10k(ticker)

        set_indexing_status(ticker, {"status": "processing", "progress": 25})

        # Fetch filing content
        content = await edgar.fetch_filing_content(filing_info["filing_url"])

        set_indexing_status(ticker, {"status": "processing", "progress": 50})

        # Parse sections
        sections = edgar.parse_10k_sections(
            content,
            ticker,
            filing_info["filing_date"][:4]
        )

        set_indexing_status(ticker, {"status": "processing", "progress": 75})

        # Add to vector store
        sections_data = [s.to_dict() for s in sections]
        count = store.add_sections(sections_data, ticker)

        set_indexing_status(ticker, {"status": "complete", "progress": 100})

        return IndexResponse(
            ticker=ticker,
            status="indexed",
            sections_indexed=count,
            filing_date=filing_info["filing_date"],
        )

    except TickerNotFoundError as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except FilingNotFoundError as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=429, detail=str(e))
    except EdgarError as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    except VectorStoreError as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        set_indexing_status(ticker, {"status": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/index/{ticker}/status")
async def get_index_status(ticker: str):
    """Check indexing status for a ticker."""
    status = get_indexing_status(ticker)
    if status:
        return status

    store = get_vector_store()
    if store.has_ticker(ticker):
        return {"status": "complete", "progress": 100}

    return {"status": "not_started", "progress": 0}


@router.get("/{ticker}", response_model=AnalysisResponse)
async def analyze_company(ticker: str):
    """Get AI-powered analysis of a company's 10-K filing."""
    ticker = ticker.upper()

    # Check if indexed
    store = get_vector_store()
    if not store.has_ticker(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Company {ticker} not indexed. Please index first."
        )

    try:
        # Get sections from vector store (all of them for analysis)
        sections = store.search("company overview risk factors financial performance", ticker, n_results=5)

        if not sections:
            raise HTTPException(status_code=404, detail="No filing data found")

        # Get financial data
        try:
            financial_data = get_financial_data(ticker)
        except FinanceError:
            financial_data = None

        # Get company info from EDGAR
        edgar = await get_edgar_client()
        company_info = await edgar.get_company_info(ticker)
        filing_info = await edgar.get_latest_10k(ticker)

        # Run Claude analysis
        claude = get_claude_client()
        analysis = await claude.analyze_filing(sections, company_info, financial_data)

        return AnalysisResponse(
            ticker=ticker,
            company_name=company_info["name"],
            filing_date=filing_info["filing_date"],
            financial_health_score=analysis.get("financial_health_score", 50),
            metrics=analysis.get("metrics", {}),
            risk_factors=[
                RiskFactor(**rf) for rf in analysis.get("risk_factors", [])
            ],
            key_insights=analysis.get("key_insights", []),
            recommendations=analysis.get("recommendations", []),
            sections_indexed=len(sections),
        )

    except ClaudeError as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
    except EdgarError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{ticker}/sections")
async def get_sections(ticker: str):
    """Get indexed sections for a company (for transparency)."""
    store = get_vector_store()

    if not store.has_ticker(ticker):
        raise HTTPException(status_code=404, detail=f"Company {ticker} not indexed")

    # Get all sections
    sections = store.search("", ticker, n_results=10)

    return {
        "ticker": ticker.upper(),
        "sections": [
            {
                "name": s["name"],
                "fiscal_year": s["fiscal_year"],
                "content_preview": s["content"][:500] + "..." if len(s["content"]) > 500 else s["content"],
            }
            for s in sections
        ]
    }
