"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, AlertCircle, FileText, RefreshCw, Clock } from "lucide-react";
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
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  // Timer for elapsed time
  useEffect(() => {
    if (hasStarted && !isComplete && !errorMsg) {
      const timer = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [hasStarted, isComplete, errorMsg]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const startIndexing = async () => {
    let cancelled = false;

    try {
      const result = await indexCompany(ticker);

      if (cancelled) return;

      if (result.status === "already_indexed" || result.status === "indexed") {
        setIsComplete(true);
        onComplete();
        return;
      }

      // Poll for status if still processing
      const pollStatus = async () => {
        if (cancelled) return;

        try {
          const currentStatus = await getIndexStatus(ticker);

          if (currentStatus.status === "complete") {
            setIsComplete(true);
            onComplete();
          } else if (currentStatus.status === "error") {
            setErrorMsg(currentStatus.message || "Indexing failed");
            onError(currentStatus.message || "Indexing failed");
          } else {
            setTimeout(pollStatus, 1000);
          }
        } catch {
          // Status check failed, keep polling
          setTimeout(pollStatus, 2000);
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

    return () => { cancelled = true; };
  };

  useEffect(() => {
    if (!hasStarted) {
      setHasStarted(true);
      startIndexing();
    }
  }, [ticker, hasStarted]);

  const handleRetry = () => {
    setErrorMsg(null);
    setIsRetrying(true);
    setElapsedTime(0);
    startIndexing().finally(() => setIsRetrying(false));
  };

  if (isComplete) {
    return null; // Don't show anything, move to analysis
  }

  if (errorMsg) {
    const isTimeout = errorMsg.includes("timed out") || errorMsg.includes("timeout");
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <div>
              <p className="font-medium">{isTimeout ? "Request timed out" : errorMsg}</p>
              {isTimeout && (
                <p className="text-sm text-muted-foreground mt-1">
                  Large SEC filings can take a while to download. The server may still be processing.
                </p>
              )}
            </div>
            <Button onClick={handleRetry} disabled={isRetrying} variant="outline" size="sm">
              {isRetrying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Retrying...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Loading state with elapsed time
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
            <p className="text-sm text-muted-foreground mt-1">
              {elapsedTime < 10
                ? "This usually takes a few seconds"
                : elapsedTime < 30
                ? "Downloading filing from SEC..."
                : elapsedTime < 60
                ? "Processing large filing, please wait..."
                : "Still working on it, almost there..."}
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Elapsed: {formatTime(elapsedTime)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
