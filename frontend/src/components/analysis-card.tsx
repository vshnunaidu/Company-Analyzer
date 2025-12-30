"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Target,
  Brain,
  FileSearch,
  BarChart3,
  Clock,
  Loader2,
} from "lucide-react";
import { Analysis, RiskFactor } from "@/lib/api";

interface AnalysisCardProps {
  analysis: Analysis | null;
  isLoading?: boolean;
}

function HealthScoreGauge({ score }: { score: number }) {
  const getColor = () => {
    if (score >= 70) return "text-green-500";
    if (score >= 40) return "text-yellow-500";
    return "text-red-500";
  };

  const getLabel = () => {
    if (score >= 70) return "Healthy";
    if (score >= 40) return "Moderate";
    return "At Risk";
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90">
          <circle
            cx="64"
            cy="64"
            r="56"
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            className="text-muted"
          />
          <circle
            cx="64"
            cy="64"
            r="56"
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            strokeDasharray={`${(score / 100) * 352} 352`}
            className={getColor()}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${getColor()}`}>{score}</span>
          <span className="text-xs text-muted-foreground">/ 100</span>
        </div>
      </div>
      <span className={`mt-2 font-medium ${getColor()}`}>{getLabel()}</span>
    </div>
  );
}

function RiskFactorItem({ risk }: { risk: RiskFactor }) {
  const getSeverityIcon = () => {
    switch (risk.severity) {
      case "high":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    }
  };

  const getSeverityBadge = () => {
    const variants: Record<string, "destructive" | "secondary" | "outline"> = {
      high: "destructive",
      medium: "secondary",
      low: "outline",
    };
    return (
      <Badge variant={variants[risk.severity] || "outline"}>
        {risk.severity}
      </Badge>
    );
  };

  return (
    <div className="flex gap-3 p-3 rounded-lg bg-muted/50">
      <div className="mt-0.5">{getSeverityIcon()}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium">{risk.title}</span>
          {getSeverityBadge()}
          <Badge variant="outline" className="text-xs">
            {risk.category}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground mt-1">{risk.description}</p>
      </div>
    </div>
  );
}

function AnalysisLoadingState() {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentPhase, setCurrentPhase] = useState(0);

  const phases = [
    { name: "Reading SEC filings", icon: FileSearch },
    { name: "Analyzing financial data", icon: BarChart3 },
    { name: "Generating insights", icon: Brain },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    // Cycle through phases every 5 seconds for visual feedback
    const phaseTimer = setInterval(() => {
      setCurrentPhase((prev) => (prev + 1) % phases.length);
    }, 5000);

    return () => {
      clearInterval(timer);
      clearInterval(phaseTimer);
    };
  }, [phases.length]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const CurrentIcon = phases[currentPhase].icon;

  return (
    <Card>
      <CardContent className="py-10">
        <div className="flex flex-col items-center text-center space-y-6">
          {/* Animated brain icon */}
          <div className="relative">
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
              <CurrentIcon className="h-10 w-10 text-primary animate-pulse" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-background border-2 border-primary flex items-center justify-center">
              <Loader2 className="h-3 w-3 text-primary animate-spin" />
            </div>
          </div>

          {/* Status text */}
          <div className="space-y-2">
            <h3 className="font-semibold text-lg">AI Analysis in Progress</h3>
            <p className="text-sm text-primary font-medium">
              {phases[currentPhase].name}...
            </p>
          </div>

          {/* Time info */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Elapsed: {formatTime(elapsedTime)}</span>
            <span className="text-muted-foreground/50">•</span>
            <span>Usually takes 5-15 seconds</span>
          </div>

          {/* Progress dots */}
          <div className="flex gap-2">
            {phases.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === currentPhase ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>

          {/* What's happening */}
          <div className="text-xs text-muted-foreground max-w-sm">
            Claude AI is reviewing the filing content to generate a financial health score,
            identify risk factors, and provide actionable insights.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AnalysisCard({ analysis, isLoading }: AnalysisCardProps) {
  if (isLoading) {
    return <AnalysisLoadingState />;
  }

  if (!analysis) return null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Financial Health Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center gap-6">
            <HealthScoreGauge score={analysis.financial_health_score} />
            <div className="flex-1 space-y-2">
              <p className="text-sm text-muted-foreground">
                Based on {analysis.company_name}&apos;s latest 10-K filing (
                {analysis.filing_date})
              </p>
              <p className="text-sm">
                Analysis covers {analysis.sections_indexed} sections from SEC
                filings.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Risk Factors
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analysis.risk_factors.map((risk, i) => (
              <RiskFactorItem key={i} risk={risk} />
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Lightbulb className="h-5 w-5" />
              Key Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {analysis.key_insights.map((insight, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Target className="h-5 w-5" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {analysis.recommendations.map((rec, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-primary font-medium">{i + 1}.</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
