# Company Analyzer

AI-powered public company auditor that analyzes SEC filings. Enter any stock ticker to get instant financial intelligence, risk analysis, and natural language Q&A.

![Company Audit Demo](docs/demo.png)

## Features

- **SEC Filing Analysis** - Automatically fetches and parses 10-K filings from SEC EDGAR
- **Financial Health Score** - AI-generated health assessment (0-100) based on filing analysis
- **Risk Factor Extraction** - Identifies and categorizes key risk factors with severity ratings
- **Natural Language Q&A** - Ask questions about company financials in plain English
- **Real-time Streaming** - Chat responses stream in real-time
- **Dark Mode** - Full dark mode support
- **Mobile Responsive** - Works on all screen sizes

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Next.js        │────▶│  FastAPI        │────▶│  SEC EDGAR      │
│  Frontend       │     │  Backend        │     │  API            │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │           │ │           │ │           │
            │  ChromaDB │ │  Claude   │ │  Yahoo    │
            │  (Vector) │ │  API      │ │  Finance  │
            │           │ │           │ │           │
            └───────────┘ └───────────┘ └───────────┘
```

### Data Flow

1. User enters a stock ticker (e.g., AAPL)
2. Backend fetches company info from Yahoo Finance
3. Backend fetches latest 10-K filing from SEC EDGAR
4. Filing is parsed into sections (Business, Risk Factors, MD&A, etc.)
5. Sections are embedded and stored in ChromaDB vector database
6. Claude AI analyzes sections and generates health score + insights
7. User can ask questions, which retrieves relevant sections via RAG

## Tech Stack

### Frontend
- Next.js 15 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- next-themes for dark mode

### Backend
- Python 3.11+
- FastAPI
- ChromaDB (vector embeddings)
- Anthropic Claude API (no LangChain - raw API calls)
- httpx for async HTTP
- BeautifulSoup for HTML parsing

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Anthropic API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Pre-cache Popular Tickers (Optional)

For instant demo experience, pre-cache common tickers:

```bash
cd backend
python -m scripts.precache
```

## Usage

1. Open http://localhost:3000
2. Enter any stock ticker (e.g., AAPL, NVDA, TSLA)
3. Wait for SEC filing to be indexed (first time only)
4. View financial health score, risk factors, and insights
5. Use the chat to ask questions about the company

## Design Decisions

### Why No LangChain?
Raw Claude API calls are cleaner, more debuggable, and avoid unnecessary abstraction. The codebase is simpler and you can see exactly what's happening.

### Section-Based Chunking
Instead of arbitrary character chunking, we parse 10-K filings by their actual structure (Item 1 - Business, Item 1A - Risk Factors, etc.). This preserves context and improves retrieval quality.

### Streaming Chat
Responses stream in real-time using Server-Sent Events, providing better UX than waiting for complete responses.

### Vector Store Transparency
The UI shows which sections were used to generate each response, proving the RAG pipeline is working.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/company/{ticker}` | GET | Get company info |
| `/api/company/{ticker}/financial` | GET | Get financial metrics |
| `/api/analysis/index` | POST | Index a company's 10-K |
| `/api/analysis/{ticker}` | GET | Get AI analysis |
| `/api/chat/stream` | POST | Stream chat response |

## Project Structure

```
company-audit/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main page
│   │   │   └── layout.tsx        # Root layout
│   │   ├── components/
│   │   │   ├── ui/               # shadcn components
│   │   │   ├── ticker-search.tsx
│   │   │   ├── company-overview.tsx
│   │   │   ├── analysis-card.tsx
│   │   │   └── chat-interface.tsx
│   │   └── lib/
│   │       └── api.ts            # API client
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── company.py
│   │   │   ├── analysis.py
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── edgar.py          # SEC EDGAR client
│   │   │   ├── claude.py         # Claude AI client
│   │   │   ├── vectorstore.py    # ChromaDB wrapper
│   │   │   └── finance.py        # Yahoo Finance
│   │   └── main.py
│   ├── scripts/
│   │   └── precache.py
│   └── requirements.txt
└── README.md
```

## License

MIT
