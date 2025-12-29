"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { searchCompanies, SearchResult } from "@/lib/api";

const SUGGESTED_TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"];

interface TickerSearchProps {
  onSearch: (ticker: string) => void;
  isLoading?: boolean;
}

export function TickerSearch({ onSearch, isLoading }: TickerSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search
  useEffect(() => {
    const trimmed = query.trim();

    // If it looks like a ticker (all caps, 1-5 chars), don't search
    if (trimmed.length <= 5 && trimmed === trimmed.toUpperCase() && /^[A-Z]+$/.test(trimmed)) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    if (trimmed.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const searchResults = await searchCompanies(trimmed);
        setResults(searchResults);
        setShowDropdown(searchResults.length > 0);
        setSelectedIndex(-1);
      } catch {
        setResults([]);
        setShowDropdown(false);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIndex >= 0 && results[selectedIndex]) {
      handleSelect(results[selectedIndex]);
    } else if (query.trim()) {
      onSearch(query.trim().toUpperCase());
      setShowDropdown(false);
    }
  };

  const handleSelect = (result: SearchResult) => {
    setQuery(result.ticker);
    setShowDropdown(false);
    onSearch(result.ticker);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === "Escape") {
      setShowDropdown(false);
      setSelectedIndex(-1);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1" ref={dropdownRef}>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={inputRef}
            type="text"
            placeholder="Search by company name or ticker..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => results.length > 0 && setShowDropdown(true)}
            className="pl-10 h-12 text-lg"
            disabled={isLoading}
          />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
          )}

          {/* Autocomplete dropdown */}
          {showDropdown && results.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-background border rounded-lg shadow-lg max-h-64 overflow-auto">
              {results.map((result, index) => (
                <button
                  key={result.ticker}
                  type="button"
                  className={`w-full px-4 py-3 text-left hover:bg-muted flex items-center justify-between transition-colors ${
                    index === selectedIndex ? "bg-muted" : ""
                  }`}
                  onClick={() => handleSelect(result)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div>
                    <span className="font-semibold text-primary">{result.ticker}</span>
                    <span className="text-muted-foreground ml-2 text-sm">
                      {result.name}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {Math.round(result.score)}% match
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
        <Button type="submit" size="lg" disabled={isLoading || !query.trim()}>
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Analyze"
          )}
        </Button>
      </form>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-muted-foreground">Try:</span>
        {SUGGESTED_TICKERS.map((t) => (
          <Button
            key={t}
            variant="outline"
            size="sm"
            onClick={() => {
              setQuery(t);
              onSearch(t);
            }}
            disabled={isLoading}
          >
            {t}
          </Button>
        ))}
      </div>
    </div>
  );
}
