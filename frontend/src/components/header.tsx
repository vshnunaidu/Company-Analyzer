"use client";

import { ThemeToggle } from "@/components/theme-toggle";
import { FileSearch, Github } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="flex items-center gap-2 font-semibold">
          <FileSearch className="h-5 w-5" />
          <span>Company Analyzer</span>
        </div>

        <div className="flex-1" />

        <nav className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="h-4 w-4 mr-2" />
              Source
            </a>
          </Button>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
