"use client";

import { useState, useCallback } from "react";
import { Header } from "@/components/header";
import { TickerSearch } from "@/components/ticker-search";
import { CompanyOverview, FinancialMetricsCard } from "@/components/company-overview";
import { AnalysisCard } from "@/components/analysis-card";
import { ChatInterface } from "@/components/chat-interface";
import { IndexingStatus } from "@/components/indexing-status";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, BarChart3, MessageSquare, FileText } from "lucide-react";
import {
  getCompany,
  getFinancials,
  getAnalysis,
  Company,
  FinancialData,
  Analysis,
} from "@/lib/api";

type AppState = "idle" | "loading" | "indexing" | "analyzing" | "ready" | "error";

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [ticker, setTicker] = useState("");
  const [company, setCompany] = useState<Company | null>(null);
  const [financials, setFinancials] = useState<FinancialData | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (searchTicker: string) => {
    setTicker(searchTicker);
    setState("loading");
    setError(null);
    setCompany(null);
    setFinancials(null);
    setAnalysis(null);

    try {
      // Fetch company info and financials in parallel
      const [companyData, financialData] = await Promise.all([
        getCompany(searchTicker),
        getFinancials(searchTicker),
      ]);

      setCompany(companyData);
      setFinancials(financialData);

      // Check if already indexed
      if (companyData.is_indexed) {
        setState("analyzing");
        const analysisData = await getAnalysis(searchTicker);
        setAnalysis(analysisData);
        setState("ready");
      } else {
        setState("indexing");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch company";
      setError(message);
      setState("error");
    }
  };

  const handleIndexComplete = useCallback(async () => {
    setState("analyzing");
    try {
      const analysisData = await getAnalysis(ticker);
      setAnalysis(analysisData);
      setState("ready");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to analyze";
      setError(message);
      setState("error");
    }
  }, [ticker]);

  const handleIndexError = useCallback((message: string) => {
    setError(message);
    setState("error");
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container py-8">
        {state === "idle" ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8">
            <div className="text-center space-y-4">
              <h1 className="text-4xl font-bold tracking-tight">
                AI-Powered Company Auditor
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl">
                Enter any stock ticker to instantly analyze SEC filings with AI.
                Get financial health scores, risk factors, and ask questions in
                natural language.
              </p>
            </div>
            <TickerSearch onSearch={handleSearch} />

            <div className="grid md:grid-cols-3 gap-6 mt-12 max-w-4xl">
              <div className="text-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-medium">SEC Filing Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  Automatically parse 10-K filings and extract key sections
                </p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                  <BarChart3 className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-medium">Financial Health Score</h3>
                <p className="text-sm text-muted-foreground">
                  AI-generated health assessment with risk factors
                </p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                  <MessageSquare className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-medium">Natural Language Q&A</h3>
                <p className="text-sm text-muted-foreground">
                  Ask questions about company financials in plain English
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <TickerSearch
              onSearch={handleSearch}
              isLoading={state === "loading" || state === "indexing" || state === "analyzing"}
            />

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {state === "indexing" && ticker && (
              <IndexingStatus
                ticker={ticker}
                onComplete={handleIndexComplete}
                onError={handleIndexError}
              />
            )}

            {(company || state === "loading" || state === "analyzing") && (
              <div className="space-y-6">
                <CompanyOverview
                  data={financials}
                  isLoading={state === "loading"}
                />

                <Tabs defaultValue="analysis" className="space-y-4">
                  <TabsList>
                    <TabsTrigger value="analysis" className="gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Analysis
                    </TabsTrigger>
                    <TabsTrigger value="chat" className="gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Chat
                    </TabsTrigger>
                    <TabsTrigger value="financials" className="gap-2">
                      <FileText className="h-4 w-4" />
                      Financials
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="analysis">
                    <AnalysisCard
                      analysis={analysis}
                      isLoading={state === "analyzing" || state === "indexing"}
                    />
                  </TabsContent>

                  <TabsContent value="chat">
                    <ChatInterface
                      ticker={ticker}
                      isReady={state === "ready"}
                    />
                  </TabsContent>

                  <TabsContent value="financials">
                    <FinancialMetricsCard
                      data={financials}
                      isLoading={state === "loading"}
                    />
                  </TabsContent>
                </Tabs>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="border-t py-6">
        <div className="container text-center text-sm text-muted-foreground">
          <p>
            Data sourced from SEC EDGAR and Yahoo Finance. AI analysis powered
            by Claude.
          </p>
          <p className="mt-1">
            This tool is for informational purposes only. Not financial advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
