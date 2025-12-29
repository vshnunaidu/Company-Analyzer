"""Company search service with fuzzy matching."""

import httpx
from typing import Optional
from rapidfuzz import fuzz, process
from dataclasses import dataclass
import asyncio


@dataclass
class CompanyMatch:
    """A matched company from search."""
    ticker: str
    name: str
    score: float

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "score": self.score,
        }


class CompanySearchService:
    """Service for searching companies by name using fuzzy matching."""

    SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    HEADERS = {
        "User-Agent": "CompanyAudit contact@example.com",
        "Accept": "application/json",
    }

    def __init__(self):
        self._companies: Optional[dict[str, str]] = None  # ticker -> name
        self._names_list: Optional[list[tuple[str, str]]] = None  # [(name, ticker), ...]
        self._lock = asyncio.Lock()

    async def _load_companies(self) -> None:
        """Load company data from SEC."""
        if self._companies is not None:
            return

        async with self._lock:
            # Double-check after acquiring lock
            if self._companies is not None:
                return

            async with httpx.AsyncClient(headers=self.HEADERS, timeout=30.0) as client:
                response = await client.get(self.SEC_TICKERS_URL)
                response.raise_for_status()
                data = response.json()

            self._companies = {}
            self._names_list = []

            for entry in data.values():
                ticker = entry.get("ticker", "")
                name = entry.get("title", "")
                if ticker and name:
                    self._companies[ticker] = name
                    self._names_list.append((name, ticker))

    async def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 50.0
    ) -> list[CompanyMatch]:
        """Search for companies by name using fuzzy matching."""
        await self._load_companies()

        if not query or not self._names_list:
            return []

        query = query.strip()

        # Check if query looks like a ticker (all caps, short)
        if query.isupper() and len(query) <= 5 and query in self._companies:
            return [CompanyMatch(
                ticker=query,
                name=self._companies[query],
                score=100.0
            )]

        # Fuzzy search on company names
        results = process.extract(
            query.upper(),
            [name.upper() for name, _ in self._names_list],
            scorer=fuzz.WRatio,
            limit=limit * 2,  # Get extra results to filter
        )

        matches = []
        seen_tickers = set()

        for name_upper, score, idx in results:
            if score < min_score:
                continue

            original_name, ticker = self._names_list[idx]

            # Skip duplicates (some companies have multiple entries)
            if ticker in seen_tickers:
                continue
            seen_tickers.add(ticker)

            matches.append(CompanyMatch(
                ticker=ticker,
                name=original_name,
                score=score,
            ))

            if len(matches) >= limit:
                break

        return matches

    async def get_ticker_for_name(self, name: str) -> Optional[str]:
        """Get the best matching ticker for a company name."""
        matches = await self.search(name, limit=1, min_score=70.0)
        return matches[0].ticker if matches else None


# Singleton instance
_service: Optional[CompanySearchService] = None


def get_search_service() -> CompanySearchService:
    """Get or create the search service singleton."""
    global _service
    if _service is None:
        _service = CompanySearchService()
    return _service
