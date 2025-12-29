"""Company information endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.edgar import (
    get_edgar_client,
    EdgarError,
    TickerNotFoundError,
    RateLimitError,
)
from app.services.finance import get_financial_data, FinanceError
from app.services.vectorstore import get_vector_store
from app.services.search import get_search_service

router = APIRouter()


class CompanyResponse(BaseModel):
    ticker: str
    name: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    description: str | None
    is_indexed: bool


class SearchResult(BaseModel):
    ticker: str
    name: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


class IndexStatusResponse(BaseModel):
    indexed_tickers: list[str]


@router.get("/search", response_model=SearchResponse)
async def search_companies(
    q: str = Query(..., min_length=1, description="Search query (company name or ticker)")
):
    """Search for companies by name using fuzzy matching."""
    try:
        service = get_search_service()
        matches = await service.search(q, limit=10)
        return SearchResponse(
            results=[SearchResult(**m.to_dict()) for m in matches]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{ticker}", response_model=CompanyResponse)
async def get_company(ticker: str):
    """Get company information by ticker."""
    try:
        # Get financial data from yfinance
        financial_data = get_financial_data(ticker)

        # Check if already indexed
        store = get_vector_store()
        is_indexed = store.has_ticker(ticker)

        return CompanyResponse(
            ticker=financial_data["ticker"],
            name=financial_data["name"],
            sector=financial_data.get("sector"),
            industry=financial_data.get("industry"),
            market_cap=financial_data.get("market_cap"),
            description=financial_data.get("description"),
            is_indexed=is_indexed,
        )

    except FinanceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{ticker}/financial")
async def get_company_financials(ticker: str):
    """Get detailed financial data for a company."""
    try:
        return get_financial_data(ticker)
    except FinanceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/", response_model=IndexStatusResponse)
async def get_indexed_companies():
    """Get list of all indexed companies."""
    store = get_vector_store()
    return IndexStatusResponse(indexed_tickers=store.get_indexed_tickers())
