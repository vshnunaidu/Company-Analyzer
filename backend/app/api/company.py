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
    ticker = ticker.upper()

    # Check if already indexed
    store = get_vector_store()
    is_indexed = store.has_ticker(ticker)

    # Try Yahoo Finance first, fall back to SEC EDGAR if rate limited
    try:
        financial_data = get_financial_data(ticker)
        return CompanyResponse(
            ticker=financial_data["ticker"],
            name=financial_data["name"],
            sector=financial_data.get("sector"),
            industry=financial_data.get("industry"),
            market_cap=financial_data.get("market_cap"),
            description=financial_data.get("description"),
            is_indexed=is_indexed,
        )
    except FinanceError:
        # Fall back to SEC EDGAR for basic company info
        try:
            edgar = await get_edgar_client()
            company_info = await edgar.get_company_info(ticker)
            return CompanyResponse(
                ticker=ticker,
                name=company_info.get("name", ticker),
                sector=company_info.get("sic_description"),
                industry=company_info.get("sic_description"),
                market_cap=None,
                description=None,
                is_indexed=is_indexed,
            )
        except (EdgarError, TickerNotFoundError) as e:
            raise HTTPException(status_code=404, detail=f"Company not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{ticker}/financial")
async def get_company_financials(ticker: str):
    """Get detailed financial data for a company."""
    ticker = ticker.upper()
    try:
        return get_financial_data(ticker)
    except FinanceError:
        # Return placeholder data when Yahoo Finance is rate limited
        # The app can still function with SEC data for analysis
        return {
            "ticker": ticker,
            "name": ticker,
            "sector": None,
            "industry": None,
            "market_cap": None,
            "price": None,
            "revenue": None,
            "net_income": None,
            "gross_margin": None,
            "operating_margin": None,
            "profit_margin": None,
            "debt_to_equity": None,
            "current_ratio": None,
            "return_on_equity": None,
            "return_on_assets": None,
            "pe_ratio": None,
            "forward_pe": None,
            "peg_ratio": None,
            "beta": None,
            "dividend_yield": None,
            "fifty_two_week_high": None,
            "fifty_two_week_low": None,
            "average_volume": None,
            "description": None,
            "_limited": True,  # Flag to indicate data is limited
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/", response_model=IndexStatusResponse)
async def get_indexed_companies():
    """Get list of all indexed companies."""
    store = get_vector_store()
    return IndexStatusResponse(indexed_tickers=store.get_indexed_tickers())
