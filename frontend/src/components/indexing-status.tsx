"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, CheckCircle2, AlertCircle, FileText } from "lucide-react";
import { getIndexStatus, indexCompany } from "@/lib/api";

interface IndexingStatusProps {
  ticker: string;
  onComplete: () => void;
  onError: (error: string) => void;
}

export function IndexingStatus({ ticker, onComplete, onError }: IndexingStatusProps) {
  const [hasStarted, setHasStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const startIndexing = async () => {
      try {
        // Start indexing - this returns quickly
        const result = await indexCompany(ticker);

        if (cancelled) return;

        // Check if already indexed or just completed
        if (result.status === "already_indexed" || result.status === "indexed") {
          setIsComplete(true);
          onComplete();
          return;
        }

        // Poll for status if still processing
        const pollStatus = async () => {
          if (cancelled) return;

          const currentStatus = await getIndexStatus(ticker);

          if (currentStatus.status === "complete") {
            setIsComplete(true);
            onComplete();
          } else if (currentStatus.status === "error") {
            setErrorMsg(currentStatus.message || "Indexing failed");
            onError(currentStatus.message || "Indexing failed");
          } else {
            setTimeout(pollStatus, 500); // Poll faster
          }
        };

        await pollStatus();
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Failed to index";
          if (message.includes("already_indexed")) {
            setIsComplete(true);
            onComplete();
          } else {
            setErrorMsg(message);
            onError(message);
          }
        }
      }
    };

    if (!hasStarted) {
      setHasStarted(true);
      startIndexing();
    }

    return () => {
      cancelled = true;
    };
  }, [ticker, hasStarted, onComplete, onError]);

  if (isComplete) {
    return null; // Don't show anything, move to analysis
  }

  if (errorMsg) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="font-medium">{errorMsg}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Simple loading state - indexing is fast now
  return (
    <Card>
      <CardContent className="py-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="relative">
            <FileText className="h-8 w-8 text-primary" />
            <Loader2 className="h-4 w-4 text-primary animate-spin absolute -bottom-1 -right-1" />
          </div>
          <div>
            <p className="font-medium">Fetching SEC filings for {ticker}...</p>
            <p className="text-sm text-muted-foreground mt-1">This usually takes a few seconds</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
