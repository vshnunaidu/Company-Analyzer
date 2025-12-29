"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Building2, TrendingUp, DollarSign, BarChart3 } from "lucide-react";
import { FinancialData, formatCurrency, formatPercent } from "@/lib/api";

interface CompanyOverviewProps {
  data: FinancialData | null;
  isLoading?: boolean;
}

export function CompanyOverview({ data, isLoading }: CompanyOverviewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-24" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const metrics = [
    {
      label: "Market Cap",
      value: formatCurrency(data.market_cap),
      icon: DollarSign,
    },
    {
      label: "Price",
      value: data.price ? `$${data.price.toFixed(2)}` : "N/A",
      icon: TrendingUp,
    },
    {
      label: "P/E Ratio",
      value: data.pe_ratio?.toFixed(2) || "N/A",
      icon: BarChart3,
    },
    {
      label: "Beta",
      value: data.beta?.toFixed(2) || "N/A",
      icon: TrendingUp,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Building2 className="h-6 w-6" />
              {data.name}
            </CardTitle>
            <p className="text-muted-foreground mt-1">{data.ticker}</p>
          </div>
          <div className="flex gap-2">
            {data.sector && <Badge variant="secondary">{data.sector}</Badge>}
            {data.industry && <Badge variant="outline">{data.industry}</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="space-y-1">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <metric.icon className="h-3 w-3" />
                {metric.label}
              </p>
              <p className="text-lg font-semibold">{metric.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function FinancialMetricsCard({
  data,
  isLoading,
}: CompanyOverviewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-24" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const margins = [
    { label: "Revenue (TTM)", value: formatCurrency(data.revenue) },
    { label: "Net Income", value: formatCurrency(data.net_income) },
    { label: "Gross Margin", value: formatPercent(data.gross_margin) },
    { label: "Operating Margin", value: formatPercent(data.operating_margin) },
    { label: "Profit Margin", value: formatPercent(data.profit_margin) },
    { label: "Debt/Equity", value: data.debt_to_equity?.toFixed(2) || "N/A" },
    { label: "Current Ratio", value: data.current_ratio?.toFixed(2) || "N/A" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Financial Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {margins.map((metric) => (
            <div key={metric.label} className="space-y-1">
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className="text-lg font-semibold">{metric.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
