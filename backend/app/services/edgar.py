"""SEC EDGAR API integration for fetching company filings."""

import httpx
import re
import time
import logging
from typing import Optional
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dataclasses import dataclass
import warnings

# Suppress XML parsing warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logger = logging.getLogger(__name__)


class EdgarError(Exception):
    """Base exception for EDGAR-related errors."""
    pass


class TickerNotFoundError(EdgarError):
    """Raised when a ticker symbol cannot be found."""
    pass


class FilingNotFoundError(EdgarError):
    """Raised when no filings are found for a company."""
    pass


class RateLimitError(EdgarError):
    """Raised when SEC rate limit is exceeded."""
    pass


@dataclass
class FilingSection:
    """A parsed section from a 10-K filing."""
    name: str
    content: str
    fiscal_year: str
    ticker: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "content": self.content,
            "fiscal_year": self.fiscal_year,
            "ticker": self.ticker,
        }


# Section patterns for 10-K filings
SECTION_PATTERNS = {
    "Business": r"(?:ITEM\s*1\.?\s*[-–—]?\s*BUSINESS)",
    "Risk Factors": r"(?:ITEM\s*1A\.?\s*[-–—]?\s*RISK\s*FACTORS)",
    "Properties": r"(?:ITEM\s*2\.?\s*[-–—]?\s*PROPERTIES)",
    "Legal Proceedings": r"(?:ITEM\s*3\.?\s*[-–—]?\s*LEGAL\s*PROCEEDINGS)",
    "MD&A": r"(?:ITEM\s*7\.?\s*[-–—]?\s*MANAGEMENT'?S?\s*DISCUSSION)",
    "Financial Statements": r"(?:ITEM\s*8\.?\s*[-–—]?\s*FINANCIAL\s*STATEMENTS)",
    "Directors and Officers": r"(?:ITEM\s*10\.?\s*[-–—]?\s*DIRECTORS)",
    "Executive Compensation": r"(?:ITEM\s*11\.?\s*[-–—]?\s*EXECUTIVE\s*COMPENSATION)",
}


class EdgarClient:
    """Client for fetching SEC EDGAR filings."""

    BASE_URL = "https://data.sec.gov"
    SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    HEADERS = {
        "User-Agent": "CompanyAudit contact@example.com",
        "Accept": "application/json",
    }

    # Maximum file size to download (50MB) - handles large filings like BRK
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers=self.HEADERS,
            timeout=httpx.Timeout(180.0, connect=15.0),  # 3 min read, 15s connect
            follow_redirects=True,
        )

    async def close(self):
        await self.client.aclose()

    async def get_cik(self, ticker: str) -> str:
        """Get CIK number for a ticker symbol."""
        url = f"{self.BASE_URL}/submissions/CIK{ticker.upper()}.json"

        # First try direct lookup
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("cik", "").zfill(10)
        except httpx.HTTPError:
            pass

        # Fall back to company tickers file (note: different domain)
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        try:
            response = await self.client.get(tickers_url)
            if response.status_code == 429:
                raise RateLimitError("SEC rate limit exceeded. Please wait a moment.")
            response.raise_for_status()

            data = response.json()
            ticker_upper = ticker.upper()

            for entry in data.values():
                if entry.get("ticker") == ticker_upper:
                    return str(entry.get("cik_str", "")).zfill(10)

            raise TickerNotFoundError(f"Ticker '{ticker}' not found in SEC database")

        except httpx.HTTPError as e:
            raise EdgarError(f"Failed to fetch company data: {str(e)}")

    async def get_company_info(self, ticker: str) -> dict:
        """Get company information from SEC."""
        cik = await self.get_cik(ticker)
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"

        try:
            response = await self.client.get(url)
            if response.status_code == 429:
                raise RateLimitError("SEC rate limit exceeded. Please wait a moment.")
            response.raise_for_status()

            data = response.json()
            return {
                "cik": cik,
                "name": data.get("name", ""),
                "ticker": ticker.upper(),
                "sic": data.get("sic", ""),
                "sic_description": data.get("sicDescription", ""),
                "fiscal_year_end": data.get("fiscalYearEnd", ""),
            }
        except httpx.HTTPError as e:
            raise EdgarError(f"Failed to fetch company info: {str(e)}")

    async def get_latest_10k(self, ticker: str) -> dict:
        """Get the latest 10-K filing for a company."""
        cik = await self.get_cik(ticker)
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"

        try:
            response = await self.client.get(url)
            if response.status_code == 429:
                raise RateLimitError("SEC rate limit exceeded. Please wait a moment.")
            response.raise_for_status()

            data = response.json()
            filings = data.get("filings", {}).get("recent", {})

            forms = filings.get("form", [])
            accession_numbers = filings.get("accessionNumber", [])
            filing_dates = filings.get("filingDate", [])
            primary_docs = filings.get("primaryDocument", [])

            for i, form in enumerate(forms):
                if form in ["10-K", "10-K/A"]:
                    accession = accession_numbers[i].replace("-", "")
                    # CIK in archive URLs has no leading zeros
                    cik_no_padding = cik.lstrip("0") or "0"
                    # Use www.sec.gov for Archives (data.sec.gov doesn't have all files)
                    return {
                        "cik": cik,
                        "accession_number": accession_numbers[i],
                        "filing_date": filing_dates[i],
                        "primary_document": primary_docs[i],
                        "filing_url": f"https://www.sec.gov/Archives/edgar/data/{cik_no_padding}/{accession}/{primary_docs[i]}",
                    }

            raise FilingNotFoundError(f"No 10-K filing found for {ticker}")

        except httpx.HTTPError as e:
            raise EdgarError(f"Failed to fetch filings: {str(e)}")

    async def fetch_filing_content(self, filing_url: str) -> str:
        """Fetch the HTML content of a filing with streaming and size limit."""
        start_time = time.time()
        logger.info(f"Starting download from: {filing_url}")

        try:
            # Use streaming to handle large files and enforce size limit
            async with self.client.stream("GET", filing_url) as response:
                if response.status_code == 429:
                    raise RateLimitError("SEC rate limit exceeded. Please wait a moment.")
                response.raise_for_status()

                # Check content-length if available
                content_length = response.headers.get("content-length")
                if content_length:
                    logger.info(f"File size: {int(content_length) // 1024}KB")
                    if int(content_length) > self.MAX_FILE_SIZE:
                        raise EdgarError(
                            f"Filing too large ({int(content_length) // 1024 // 1024}MB). "
                            "Some companies like BRK have very large filings. Try a different company."
                        )

                # Stream and accumulate content with size check
                chunks = []
                total_size = 0
                async for chunk in response.aiter_bytes():
                    total_size += len(chunk)
                    if total_size > self.MAX_FILE_SIZE:
                        # Stop downloading but use what we have
                        logger.warning(f"File exceeded size limit, stopping at {total_size // 1024}KB")
                        break
                    chunks.append(chunk)

                elapsed = time.time() - start_time
                logger.info(f"Download complete: {total_size // 1024}KB in {elapsed:.1f}s")
                return b"".join(chunks).decode("utf-8", errors="ignore")

        except httpx.TimeoutException:
            raise EdgarError("Request timed out. The SEC server may be slow. Please try again.")
        except httpx.HTTPError as e:
            raise EdgarError(f"Failed to fetch filing content: {str(e)}")

    def parse_10k_sections(
        self,
        html_content: str,
        ticker: str,
        fiscal_year: str
    ) -> list[FilingSection]:
        """Parse a 10-K filing into sections based on SEC structure."""
        start_time = time.time()
        logger.info(f"Parsing {len(html_content) // 1024}KB of HTML for {ticker}")

        # Use html.parser as fallback if lxml not available
        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception:
            soup = BeautifulSoup(html_content, "html.parser")

        logger.info(f"BeautifulSoup parsing took {time.time() - start_time:.1f}s")

        # Remove scripts, styles, and tables (financial tables are noisy)
        for element in soup(["script", "style"]):
            element.decompose()

        text = soup.get_text(separator="\n")
        text = re.sub(r"\n{3,}", "\n\n", text)  # Reduce excessive newlines
        text = re.sub(r" {2,}", " ", text)  # Reduce excessive spaces

        sections = []
        text_upper = text.upper()

        # Find section positions
        section_positions = []
        for section_name, pattern in SECTION_PATTERNS.items():
            for match in re.finditer(pattern, text_upper, re.IGNORECASE):
                section_positions.append((match.start(), section_name))

        # Sort by position
        section_positions.sort(key=lambda x: x[0])

        # Extract sections
        for i, (start_pos, section_name) in enumerate(section_positions):
            # Find end position (start of next section or end of document)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = min(start_pos + 50000, len(text))  # Cap at 50k chars

            content = text[start_pos:end_pos].strip()

            # Skip if content is too short
            if len(content) < 500:
                continue

            # Truncate very long sections
            if len(content) > 30000:
                content = content[:30000] + "\n\n[Content truncated...]"

            sections.append(FilingSection(
                name=section_name,
                content=content,
                fiscal_year=fiscal_year,
                ticker=ticker.upper(),
            ))

        # If no sections found, create a general section
        if not sections:
            content = text[:50000] if len(text) > 50000 else text
            sections.append(FilingSection(
                name="Full Filing",
                content=content,
                fiscal_year=fiscal_year,
                ticker=ticker.upper(),
            ))

        elapsed = time.time() - start_time
        logger.info(f"Parsing complete: {len(sections)} sections in {elapsed:.1f}s")
        return sections


# Singleton instance
_client: Optional[EdgarClient] = None


async def get_edgar_client() -> EdgarClient:
    """Get or create the EDGAR client singleton."""
    global _client
    if _client is None:
        _client = EdgarClient()
    return _client
