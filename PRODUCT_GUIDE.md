# Company Analyzer - Product Guide

## What It Is

**Company Analyzer** is an AI-powered financial analysis tool that lets anyone instantly analyze any publicly traded company by simply entering its stock ticker. It reads official SEC filings (the same documents Wall Street analysts use) and uses Claude AI to generate actionable insights in seconds.

---

## The Problem It Solves

### For Investors & Traders
- **10-K filings are 100+ pages** of dense legal/financial text
- Reading one properly takes **4-8 hours**
- Most retail investors **never read them** and miss critical information
- Professional analysts charge **$500-2000** for similar reports

### For Students & Researchers
- Understanding company fundamentals is time-consuming
- Academic research requires analyzing multiple companies
- No easy way to compare risk factors across companies

### For Financial Professionals
- Due diligence is repetitive and time-intensive
- Need quick preliminary analysis before deep dives
- Want to ask specific questions without re-reading entire documents

---

## How It Works

### User Experience (30 seconds)

1. **Enter any stock ticker** (e.g., AAPL, TSLA, NVDA)
2. **Wait 30-60 seconds** while the system processes SEC filings
3. **Get instant results:**
   - Financial Health Score (0-100)
   - Top Risk Factors with severity ratings
   - Key Business Insights
   - Investment Recommendations
4. **Ask follow-up questions** in plain English via chat

### Behind The Scenes

```
User enters "AAPL"
        ↓
┌─────────────────────────────────────────────────────────┐
│  1. FETCH COMPANY DATA                                  │
│     • Yahoo Finance → Current stock price, market cap   │
│     • SEC EDGAR → Company CIK, filing history           │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  2. DOWNLOAD 10-K FILING                                │
│     • Get latest annual report from SEC (100+ pages)    │
│     • Parse HTML into clean text                        │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  3. INTELLIGENT PARSING                                 │
│     • Split by official SEC sections:                   │
│       - Item 1: Business Description                    │
│       - Item 1A: Risk Factors                           │
│       - Item 7: Management Discussion & Analysis        │
│       - Item 8: Financial Statements                    │
│     • Preserves context (not random chunks)             │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  4. VECTOR EMBEDDING                                    │
│     • Convert sections to mathematical vectors          │
│     • Store in ChromaDB for semantic search             │
│     • Enables "find relevant content" for any question  │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  5. AI ANALYSIS                                         │
│     • Claude AI reads the key sections                  │
│     • Generates structured analysis:                    │
│       - Health score based on financial indicators      │
│       - Categorized risk factors with severity          │
│       - Strategic insights                              │
│       - Actionable recommendations                      │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  6. INTERACTIVE Q&A (RAG)                               │
│     • User asks: "What are their biggest competitors?"  │
│     • System finds most relevant filing sections        │
│     • Claude answers using actual SEC data              │
│     • Shows which sections were used (transparency)     │
└─────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Financial Health Score (0-100)
A single number that summarizes the company's financial position based on:
- Revenue growth trends
- Profit margins
- Debt levels
- Cash flow health
- Risk factor severity

**Color-coded:** Green (70+) = Healthy | Yellow (40-69) = Moderate | Red (<40) = At Risk

### 2. Risk Factor Analysis
Extracts and categorizes risks from the official "Risk Factors" section:
- **Categories:** Market, Operational, Financial, Regulatory, Competitive
- **Severity:** High / Medium / Low
- **Plain English:** Converts legal jargon to understandable summaries

### 3. Natural Language Chat
Ask anything about the company:
- "What is their main source of revenue?"
- "How do they compare to competitors?"
- "What legal issues are they facing?"
- "Summarize their growth strategy"

**Powered by RAG (Retrieval-Augmented Generation):**
- Finds the most relevant sections of the 10-K
- Answers are grounded in real SEC data
- Shows source sections for verification

### 4. Real-Time Streaming
- Chat responses stream word-by-word
- No waiting for complete responses
- Feels like talking to a human analyst

### 5. Progress Visibility
- Shows exactly what step the system is on
- Displays elapsed time and estimates
- Users know what to expect

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                     (Next.js + React)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Search    │  │  Analysis   │  │    Chat     │              │
│  │  Component  │  │   Cards     │  │  Interface  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          BACKEND                                 │
│                    (Python + FastAPI)                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API ENDPOINTS                         │    │
│  │  /api/company/{ticker}     → Company info               │    │
│  │  /api/analysis/index       → Process SEC filing         │    │
│  │  /api/analysis/{ticker}    → Get AI analysis            │    │
│  │  /api/chat/stream          → Streaming Q&A              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────┬───────────────┬───────────────┐              │
│  │    EDGAR      │    Claude     │   ChromaDB    │              │
│  │   Service     │   Service     │   Service     │              │
│  │ (SEC filings) │  (AI model)   │  (vectors)    │              │
│  └───────────────┴───────────────┴───────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │  SEC EDGAR  │     │   Claude    │     │   Yahoo     │
   │     API     │     │    API      │     │  Finance    │
   │ (Official   │     │ (Anthropic) │     │   (Prices)  │
   │  filings)   │     │             │     │             │
   └─────────────┘     └─────────────┘     └─────────────┘
```

### Technology Choices

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | Next.js 15 | Modern React framework, great performance |
| UI Components | shadcn/ui | Beautiful, accessible, customizable |
| Styling | Tailwind CSS | Fast development, consistent design |
| Backend | FastAPI | Async Python, automatic API docs, fast |
| AI Model | Claude (Anthropic) | Best-in-class reasoning, long context |
| Vector DB | ChromaDB | Simple, embedded, no infrastructure needed |
| SEC Data | EDGAR API | Official source, free, comprehensive |
| Financials | Yahoo Finance | Real-time prices, free tier |

---

## What Makes It Different

### 1. Uses Real SEC Data
- Not summaries or third-party analysis
- Reads the actual legally-required disclosures
- Same source Wall Street uses

### 2. Section-Based Intelligence
- Understands 10-K structure (Item 1, 1A, 7, etc.)
- Doesn't randomly chunk text
- Preserves context for better AI understanding

### 3. Transparent AI
- Shows which sections were used for each answer
- Answers are verifiable against source
- No hallucination from general knowledge

### 4. No Dependencies on LangChain
- Clean, direct API integration
- Easier to debug and maintain
- Full control over prompts and behavior

### 5. Production-Ready UX
- Loading states with time estimates
- Real-time streaming responses
- Dark mode, mobile responsive
- Error handling with clear messages

---

## Use Cases

### Individual Investors
> "I want to invest in NVIDIA but the 10-K is 150 pages. Company Analyzer gave me the key risks and insights in 60 seconds."

### Financial Advisors
> "Before recommending a stock to clients, I run it through Company Analyzer to quickly identify any red flags in the risk factors."

### Business Students
> "For my case study on Apple's competitive strategy, I used the chat to extract exactly what I needed from their SEC filings."

### Due Diligence Teams
> "We use it as a first-pass screening tool. If the health score is below 50, we know to dig deeper before proceeding."

### Journalists
> "When covering a company, I ask specific questions about their revenue breakdown or legal issues and get instant, sourced answers."

---

## Competitive Advantages

| Feature | Company Analyzer | Bloomberg Terminal | Free Research Sites |
|---------|-----------------|-------------------|---------------------|
| Price | Free/Low-cost | $24,000/year | Free |
| AI Analysis | ✅ Claude AI | Limited | ❌ |
| Natural Language Q&A | ✅ | ❌ | ❌ |
| SEC Filing Parsing | ✅ Automatic | Manual reading | ❌ |
| Real-time Streaming | ✅ | ❌ | ❌ |
| Source Transparency | ✅ Shows sections | N/A | N/A |

---

## Monetization Potential

### Freemium Model
- **Free:** 3 companies/month, basic analysis
- **Pro ($19/mo):** Unlimited companies, chat history, export reports
- **Team ($49/mo):** Shared workspace, API access, priority support

### Enterprise
- **Custom deployment** for hedge funds, banks, research firms
- **API access** for integration with existing workflows
- **White-label** options for financial platforms

### Data Products
- Aggregate risk factor trends across industries
- Sentiment analysis over time
- Competitive intelligence reports

---

## Demo Script (2 minutes)

1. **Open the app** → "This is Company Analyzer - AI-powered SEC filing analysis"

2. **Enter AAPL** → "Let's analyze Apple. I just enter the ticker..."

3. **Show loading** → "It's fetching Apple's 10-K from the SEC - the same 150-page document analysts read. Takes about 45 seconds."

4. **Show results** → "Here's the Financial Health Score - 78 out of 100, that's healthy. Below are the top risk factors extracted from the Risk Factors section, categorized and rated by severity."

5. **Show insights** → "These are AI-generated insights and recommendations based on the actual filing content."

6. **Demo chat** → "Now the powerful part - I can ask questions. 'What percentage of revenue comes from iPhone?' ...and it answers using the actual SEC data, showing which section it used."

7. **Close** → "This analysis would take a professional analyst hours. Company Analyzer does it in under a minute, for any publicly traded US company."

---

## Future Roadmap

- [ ] **Multi-filing comparison** - Compare 10-Ks across years
- [ ] **Competitor analysis** - Side-by-side company comparison
- [ ] **Earnings call transcripts** - Add 8-K and earnings call analysis
- [ ] **Export reports** - PDF/DOCX generation
- [ ] **Alerts** - Notify when new filings are published
- [ ] **API access** - Programmatic access for developers
- [ ] **International support** - Non-US company filings

---

## Summary

**Company Analyzer** democratizes financial analysis by making SEC filings accessible to everyone. It combines official regulatory data with state-of-the-art AI to deliver institutional-quality insights in seconds, not hours.

**For Users:** Save hours of reading, get actionable insights, ask any question
**For Business:** Scalable SaaS model, clear monetization, growing market

*Built with Next.js, FastAPI, Claude AI, and ChromaDB.*
