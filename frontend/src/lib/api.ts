const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Company {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  description: string | null;
  is_indexed: boolean;
}

export interface FinancialData {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  price: number | null;
  revenue: number | null;
  net_income: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  profit_margin: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  pe_ratio: number | null;
  beta: number | null;
}

export interface RiskFactor {
  category: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
}

export interface Analysis {
  ticker: string;
  company_name: string;
  filing_date: string;
  financial_health_score: number;
  metrics: Record<string, string>;
  risk_factors: RiskFactor[];
  key_insights: string[];
  recommendations: string[];
  sections_indexed: number;
}

export interface IndexStatus {
  status: "not_started" | "processing" | "complete" | "error";
  progress: number;
  message?: string;
}

export interface ChatSource {
  section: string;
  fiscal_year: string;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }
  return response.json();
}

export interface SearchResult {
  ticker: string;
  name: string;
  score: number;
}

export async function searchCompanies(query: string): Promise<SearchResult[]> {
  if (!query.trim()) return [];
  const response = await fetch(`${API_URL}/api/company/search?q=${encodeURIComponent(query)}`);
  const data = await handleResponse<{ results: SearchResult[] }>(response);
  return data.results;
}

export async function getCompany(ticker: string): Promise<Company> {
  const response = await fetch(`${API_URL}/api/company/${ticker}`);
  return handleResponse<Company>(response);
}

export async function getFinancials(ticker: string): Promise<FinancialData> {
  const response = await fetch(`${API_URL}/api/company/${ticker}/financial`);
  return handleResponse<FinancialData>(response);
}

export async function indexCompany(ticker: string): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/api/analysis/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });
  return handleResponse(response);
}

export async function getIndexStatus(ticker: string): Promise<IndexStatus> {
  // Add cache-busting for polling
  const response = await fetch(`${API_URL}/api/analysis/index/${ticker}/status?_t=${Date.now()}`, {
    cache: 'no-store',
  });
  return handleResponse<IndexStatus>(response);
}

export async function getAnalysis(ticker: string): Promise<Analysis> {
  // Add cache-busting to ensure fresh data
  const response = await fetch(`${API_URL}/api/analysis/${ticker}?_t=${Date.now()}`, {
    cache: 'no-store',
  });
  return handleResponse<Analysis>(response);
}

export async function getSections(ticker: string): Promise<{
  ticker: string;
  sections: { name: string; fiscal_year: string; content_preview: string }[];
}> {
  const response = await fetch(`${API_URL}/api/analysis/${ticker}/sections`);
  return handleResponse(response);
}

export async function getSuggestions(): Promise<{ suggestions: string[] }> {
  const response = await fetch(`${API_URL}/api/chat/suggestions`);
  return handleResponse(response);
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function* streamChat(
  ticker: string,
  message: string,
  history: ChatMessage[]
): AsyncGenerator<{ type: string; data?: unknown }> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, message, history }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Chat failed" }));
    throw new ApiError(response.status, error.detail);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}

export function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return "N/A";
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

export function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}
