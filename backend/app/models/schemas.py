from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyInfo(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None


class FilingInfo(BaseModel):
    filing_type: str
    filing_date: str
    accession_number: str
    primary_document: str


class FinancialMetrics(BaseModel):
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None


class RiskFactor(BaseModel):
    category: str
    title: str
    description: str
    severity: str  # low, medium, high


class AuditReport(BaseModel):
    ticker: str
    company_name: str
    analysis_date: str
    financial_health_score: float
    metrics: FinancialMetrics
    risk_factors: list[RiskFactor]
    key_insights: list[str]
    recommendations: list[str]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    ticker: str
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []
