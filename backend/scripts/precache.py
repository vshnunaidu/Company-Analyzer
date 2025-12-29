"""Script to pre-cache popular tickers for instant demo.

Run from the backend directory:
    python -m scripts.precache
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.edgar import get_edgar_client, EdgarError
from app.services.vectorstore import get_vector_store

POPULAR_TICKERS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "NVDA",  # NVIDIA
    "GOOGL", # Alphabet
    "AMZN",  # Amazon
    "META",  # Meta
    "TSLA",  # Tesla
    "JPM",   # JPMorgan
    "V",     # Visa
    "WMT",   # Walmart
]


async def precache_ticker(ticker: str) -> bool:
    """Pre-cache a single ticker."""
    store = get_vector_store()

    if store.has_ticker(ticker):
        print(f"  {ticker}: Already cached")
        return True

    try:
        edgar = await get_edgar_client()

        print(f"  {ticker}: Fetching 10-K...")
        filing_info = await edgar.get_latest_10k(ticker)

        print(f"  {ticker}: Downloading filing...")
        content = await edgar.fetch_filing_content(filing_info["filing_url"])

        print(f"  {ticker}: Parsing sections...")
        sections = edgar.parse_10k_sections(
            content,
            ticker,
            filing_info["filing_date"][:4]
        )

        print(f"  {ticker}: Indexing {len(sections)} sections...")
        sections_data = [s.to_dict() for s in sections]
        store.add_sections(sections_data, ticker)

        print(f"  {ticker}: Done!")
        return True

    except EdgarError as e:
        print(f"  {ticker}: Error - {str(e)}")
        return False
    except Exception as e:
        print(f"  {ticker}: Unexpected error - {str(e)}")
        return False


async def main():
    print("Pre-caching popular tickers for demo...")
    print("=" * 50)

    success_count = 0
    for ticker in POPULAR_TICKERS:
        if await precache_ticker(ticker):
            success_count += 1
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

    print("=" * 50)
    print(f"Successfully cached {success_count}/{len(POPULAR_TICKERS)} tickers")

    store = get_vector_store()
    print(f"Total indexed tickers: {store.get_indexed_tickers()}")


if __name__ == "__main__":
    asyncio.run(main())
