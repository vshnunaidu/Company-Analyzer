"""Vector store service using ChromaDB for RAG."""

import os
from typing import Optional
import chromadb
from chromadb.config import Settings


class VectorStoreError(Exception):
    """Base exception for vector store errors."""
    pass


class VectorStore:
    """ChromaDB vector store for filing sections."""

    def __init__(self, persist_directory: str = "./data/chroma"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            metadata={"hnsw:space": "cosine"}
        )

    def add_sections(self, sections: list[dict], ticker: str) -> int:
        """Add filing sections to the vector store."""
        if not sections:
            return 0

        # Remove existing documents for this ticker
        try:
            existing = self.collection.get(
                where={"ticker": ticker.upper()}
            )
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])
        except Exception:
            pass  # Collection might be empty

        ids = []
        documents = []
        metadatas = []

        for i, section in enumerate(sections):
            doc_id = f"{ticker.upper()}_{section['name']}_{i}"
            ids.append(doc_id)
            documents.append(section["content"])
            metadatas.append({
                "ticker": ticker.upper(),
                "section": section["name"],
                "fiscal_year": section.get("fiscal_year", ""),
            })

        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            return len(ids)
        except Exception as e:
            raise VectorStoreError(f"Failed to add sections: {str(e)}")

    def search(
        self,
        query: str,
        ticker: str,
        n_results: int = 3
    ) -> list[dict]:
        """Search for relevant sections."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"ticker": ticker.upper()}
            )

            sections = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    sections.append({
                        "content": doc,
                        "name": metadata.get("section", "Unknown"),
                        "ticker": metadata.get("ticker", ticker),
                        "fiscal_year": metadata.get("fiscal_year", ""),
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    })

            return sections

        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}")

    def has_ticker(self, ticker: str) -> bool:
        """Check if a ticker has been indexed."""
        try:
            results = self.collection.get(
                where={"ticker": ticker.upper()},
                limit=1
            )
            return len(results["ids"]) > 0
        except Exception:
            return False

    def get_indexed_tickers(self) -> list[str]:
        """Get list of all indexed tickers."""
        try:
            results = self.collection.get()
            tickers = set()
            for metadata in results.get("metadatas", []):
                if metadata and "ticker" in metadata:
                    tickers.add(metadata["ticker"])
            return sorted(list(tickers))
        except Exception:
            return []


# Singleton instance
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
