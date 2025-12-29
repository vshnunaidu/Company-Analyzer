"""Financial data service using yfinance."""

from typing import Optional
import yfinance as yf


class FinanceError(Exception):
    """Base exception for finance-related errors."""
    pass


def get_financial_data(ticker: str) -> dict:
    """Fetch financial data for a ticker from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            raise FinanceError(f"No data found for ticker {ticker}")

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "price": info.get("regularMarketPrice"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else None,
            "current_ratio": info.get("currentRatio"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "average_volume": info.get("averageVolume"),
            "description": info.get("longBusinessSummary"),
        }
    except Exception as e:
        raise FinanceError(f"Failed to fetch financial data: {str(e)}")


def get_stock_history(ticker: str, period: str = "1y") -> list[dict]:
    """Fetch stock price history."""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)

        if hist.empty:
            return []

        return [
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
            }
            for date, row in hist.iterrows()
        ]
    except Exception as e:
        raise FinanceError(f"Failed to fetch stock history: {str(e)}")
