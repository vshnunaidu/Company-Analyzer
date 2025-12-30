"""Analysis endpoints for processing 10-K filings."""

import time
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

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
        start_time = time.time()
        logger.info(f"=== Starting indexing for {ticker} ===")

        # Set status to processing
        set_indexing_status(ticker, {"status": "processing", "progress": 0})

        # Fetch filing info
        step_start = time.time()
        edgar = await get_edgar_client()
        filing_info = await edgar.get_latest_10k(ticker)
        logger.info(f"Step 1 - Get filing info: {time.time() - step_start:.1f}s")

        set_indexing_status(ticker, {"status": "processing", "progress": 25})

        # Fetch filing content
        step_start = time.time()
        content = await edgar.fetch_filing_content(filing_info["filing_url"])
        logger.info(f"Step 2 - Download content: {time.time() - step_start:.1f}s ({len(content) // 1024}KB)")

        set_indexing_status(ticker, {"status": "processing", "progress": 50})

        # Parse sections
        step_start = time.time()
        sections = edgar.parse_10k_sections(
            content,
            ticker,
            filing_info["filing_date"][:4]
        )
        logger.info(f"Step 3 - Parse sections: {time.time() - step_start:.1f}s ({len(sections)} sections)")

        set_indexing_status(ticker, {"status": "processing", "progress": 75})

        # Add to vector store
        step_start = time.time()
        sections_data = [s.to_dict() for s in sections]
        count = store.add_sections(sections_data, ticker)
        logger.info(f"Step 4 - Store sections: {time.time() - step_start:.1f}s")

        set_indexing_status(ticker, {"status": "complete", "progress": 100})
        logger.info(f"=== Indexing complete for {ticker}: {time.time() - start_time:.1f}s total ===")

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


@router.delete("/index/{ticker}")
async def delete_index(ticker: str):
    """Delete cached data for a ticker (forces re-index on next request)."""
    ticker = ticker.upper()
    store = get_vector_store()

    if store.delete_ticker(ticker):
        logger.info(f"Deleted cached data for {ticker}")
        return {"status": "deleted", "ticker": ticker}
    else:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in cache")


@router.get("/{ticker}", response_model=AnalysisResponse)
async def analyze_company(ticker: str):
    """Get AI-powered analysis of a company's 10-K filing."""
    ticker = ticker.upper()
    start_time = time.time()
    logger.info(f"=== Starting analysis for {ticker} ===")

    # Check if indexed
    store = get_vector_store()
    if not store.has_ticker(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Company {ticker} not indexed. Please index first."
        )

    try:
        # Get sections from vector store (all of them for analysis)
        step_start = time.time()
        sections = store.search("company overview risk factors financial performance", ticker, n_results=5)
        logger.info(f"Step 1 - Get sections: {time.time() - step_start:.1f}s ({len(sections)} sections)")

        if not sections:
            raise HTTPException(status_code=404, detail="No filing data found")

        # Get financial data
        step_start = time.time()
        try:
            financial_data = get_financial_data(ticker)
            logger.info(f"Step 2 - Yahoo Finance: {time.time() - step_start:.1f}s")
        except FinanceError:
            financial_data = None
            logger.info(f"Step 2 - Yahoo Finance: skipped (rate limited)")

        # Get company info from EDGAR
        step_start = time.time()
        edgar = await get_edgar_client()
        company_info = await edgar.get_company_info(ticker)
        filing_info = await edgar.get_latest_10k(ticker)
        logger.info(f"Step 3 - EDGAR info: {time.time() - step_start:.1f}s")

        # Run Claude analysis
        step_start = time.time()
        claude = get_claude_client()
        analysis = await claude.analyze_filing(sections, company_info, financial_data)
        logger.info(f"Step 4 - Claude analysis: {time.time() - step_start:.1f}s")
        logger.info(f"=== Analysis complete for {ticker}: {time.time() - start_time:.1f}s total ===")

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
