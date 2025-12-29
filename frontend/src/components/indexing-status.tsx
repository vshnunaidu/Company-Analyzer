"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, CheckCircle2, AlertCircle, FileSearch, Download, FileText, Database, Clock } from "lucide-react";
import { IndexStatus, getIndexStatus, indexCompany } from "@/lib/api";

interface IndexingStatusProps {
  ticker: string;
  onComplete: () => void;
  onError: (error: string) => void;
}

const STEPS = [
  { id: 1, name: "Fetching filing info", icon: FileSearch, estimate: "5-10 sec" },
  { id: 2, name: "Downloading content", icon: Download, estimate: "10-20 sec" },
  { id: 3, name: "Parsing sections", icon: FileText, estimate: "5-10 sec" },
  { id: 4, name: "Indexing for search", icon: Database, estimate: "5-10 sec" },
];

export function IndexingStatus({ ticker, onComplete, onError }: IndexingStatusProps) {
  const [status, setStatus] = useState<IndexStatus>({ status: "not_started", progress: 0 });
  const [hasStarted, setHasStarted] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let timerInterval: NodeJS.Timeout;

    const startIndexing = async () => {
      // Start elapsed time counter
      const startTime = Date.now();
      timerInterval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      try {
        // Start indexing
        await indexCompany(ticker);

        // Poll for status
        const pollStatus = async () => {
          if (cancelled) return;

          const currentStatus = await getIndexStatus(ticker);
          setStatus(currentStatus);

          if (currentStatus.status === "complete") {
            clearInterval(timerInterval);
            onComplete();
          } else if (currentStatus.status === "error") {
            clearInterval(timerInterval);
            onError(currentStatus.message || "Indexing failed");
          } else if (currentStatus.status === "processing") {
            setTimeout(pollStatus, 1000);
          }
        };

        await pollStatus();
      } catch (error) {
        clearInterval(timerInterval);
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Failed to index";
          // Check if already indexed
          if (message.includes("already_indexed")) {
            onComplete();
          } else {
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
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [ticker, hasStarted, onComplete, onError]);

  const getCurrentStep = () => {
    if (status.progress < 25) return 1;
    if (status.progress < 50) return 2;
    if (status.progress < 75) return 3;
    return 4;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  if (status.status === "complete") {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
            <div>
              <p className="font-medium">Filing indexed successfully!</p>
              <p className="text-sm text-muted-foreground mt-1">
                Completed in {formatTime(elapsedTime)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status.status === "error") {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <div>
              <p className="font-medium">{status.message || "Failed to index filing"}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStep = getCurrentStep();

  return (
    <Card>
      <CardContent className="py-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="text-center">
            <h3 className="font-semibold text-lg">Processing {ticker} SEC Filings</h3>
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mt-1">
              <Clock className="h-4 w-4" />
              <span>Elapsed: {formatTime(elapsedTime)}</span>
              <span className="text-muted-foreground/50">•</span>
              <span>Usually takes 30-60 seconds</span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full max-w-md mx-auto">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl mx-auto">
            {STEPS.map((step) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isComplete = currentStep > step.id;

              return (
                <div
                  key={step.id}
                  className={`flex flex-col items-center p-3 rounded-lg transition-colors ${
                    isActive
                      ? "bg-primary/10 border border-primary/20"
                      : isComplete
                      ? "bg-green-500/10"
                      : "bg-muted/50"
                  }`}
                >
                  <div className={`mb-2 ${isActive ? "text-primary" : isComplete ? "text-green-500" : "text-muted-foreground"}`}>
                    {isActive ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : isComplete ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span className={`text-xs font-medium text-center ${
                    isActive ? "text-foreground" : isComplete ? "text-green-600 dark:text-green-400" : "text-muted-foreground"
                  }`}>
                    {step.name}
                  </span>
                  <span className="text-xs text-muted-foreground mt-0.5">
                    {isComplete ? "Done" : step.estimate}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
