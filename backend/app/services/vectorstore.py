"""Simple document store for SEC filing sections.

Uses a lightweight JSON-based storage instead of ChromaDB embeddings
to avoid the heavy model download and slow inference on free tier hosting.
"""

import os
import json
from typing import Optional
from pathlib import Path


class VectorStoreError(Exception):
    """Base exception for vector store errors."""
    pass


class VectorStore:
    """Simple document store for filing sections."""

    def __init__(self, persist_directory: str = "./data/filings"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_file = self.persist_directory / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> dict:
        """Load the index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        """Save the index to disk."""
        with open(self.index_file, "w") as f:
            json.dump(self._index, f)

    def _get_ticker_file(self, ticker: str) -> Path:
        """Get the file path for a ticker's data."""
        return self.persist_directory / f"{ticker.upper()}.json"

    def add_sections(self, sections: list[dict], ticker: str) -> int:
        """Add filing sections for a ticker."""
        if not sections:
            return 0

        ticker = ticker.upper()

        # Store sections
        data = {
            "ticker": ticker,
            "sections": sections
        }

        ticker_file = self._get_ticker_file(ticker)
        with open(ticker_file, "w") as f:
            json.dump(data, f)

        # Update index
        self._index[ticker] = {
            "sections": [s["name"] for s in sections],
            "fiscal_year": sections[0].get("fiscal_year", "") if sections else ""
        }
        self._save_index()

        return len(sections)

    def search(
        self,
        query: str,
        ticker: str,
        n_results: int = 3
    ) -> list[dict]:
        """Get relevant sections for a ticker based on query keywords."""
        ticker = ticker.upper()
        ticker_file = self._get_ticker_file(ticker)

        if not ticker_file.exists():
            return []

        try:
            with open(ticker_file, "r") as f:
                data = json.load(f)
        except Exception:
            return []

        sections = data.get("sections", [])
        if not sections:
            return []

        # Simple keyword-based relevance scoring
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Priority sections based on common queries
        section_priority = {
            "Risk Factors": ["risk", "risks", "factors", "challenges", "threats"],
            "Business": ["business", "model", "overview", "company", "products", "services", "revenue", "competitors"],
            "MD&A": ["management", "discussion", "analysis", "financial", "performance", "results", "growth"],
            "Financial Statements": ["financial", "statements", "income", "balance", "cash", "flow"],
            "Properties": ["properties", "facilities", "locations", "real", "estate"],
            "Legal Proceedings": ["legal", "proceedings", "litigation", "lawsuits", "regulatory"],
            "Directors and Officers": ["directors", "officers", "management", "executives", "board"],
            "Executive Compensation": ["compensation", "salary", "bonus", "equity", "pay"],
        }

        scored_sections = []
        for section in sections:
            section_name = section.get("name", "")
            content_preview = section.get("content", "")[:1000].lower()

            score = 0

            # Score based on section name matching priority keywords
            priority_words = section_priority.get(section_name, [])
            for word in query_words:
                if word in priority_words:
                    score += 10
                if word in section_name.lower():
                    score += 5
                if word in content_preview:
                    score += 1

            # Boost important sections slightly
            if section_name in ["Business", "Risk Factors", "MD&A"]:
                score += 2

            scored_sections.append((score, section))

        # Sort by score descending and return top n
        scored_sections.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, section in scored_sections[:n_results]:
            results.append({
                "content": section.get("content", ""),
                "name": section.get("name", "Unknown"),
                "ticker": ticker,
                "fiscal_year": section.get("fiscal_year", ""),
                "distance": 1.0 - (score / 20.0),  # Fake distance for compatibility
            })

        # If no good matches, return first n sections
        if not results or all(s[0] == 0 for s in scored_sections[:n_results]):
            for section in sections[:n_results]:
                if section not in [r for _, r in scored_sections[:n_results]]:
                    results.append({
                        "content": section.get("content", ""),
                        "name": section.get("name", "Unknown"),
                        "ticker": ticker,
                        "fiscal_year": section.get("fiscal_year", ""),
                        "distance": 0.5,
                    })

        return results[:n_results]

    def has_ticker(self, ticker: str) -> bool:
        """Check if a ticker has been indexed."""
        return ticker.upper() in self._index

    def get_indexed_tickers(self) -> list[str]:
        """Get list of all indexed tickers."""
        return sorted(list(self._index.keys()))


# Singleton instance
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
