"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Send, MessageSquare, Bot, User, Loader2, FileText } from "lucide-react";
import { ChatMessage, ChatSource, streamChat } from "@/lib/api";

const SUGGESTED_QUESTIONS = [
  "What are the main risk factors?",
  "Summarize the business model",
  "What's the competitive advantage?",
  "How has revenue changed?",
];

interface ChatInterfaceProps {
  ticker: string;
  isReady: boolean;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

export function ChatInterface({ ticker, isReady }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSources, setCurrentSources] = useState<ChatSource[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset messages when ticker changes
  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [ticker]);

  const handleSend = async (message: string) => {
    if (!message.trim() || isStreaming || !isReady) return;

    const userMessage: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);
    setCurrentSources([]);

    // Add placeholder for assistant message
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const history: ChatMessage[] = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      let fullContent = "";
      let sources: ChatSource[] = [];

      for await (const event of streamChat(ticker, message, history)) {
        if (event.type === "sources") {
          sources = event.data as ChatSource[];
          setCurrentSources(sources);
        } else if (event.type === "content") {
          fullContent += event.data as string;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: fullContent,
              sources,
            };
            return updated;
          });
        } else if (event.type === "error") {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: `Error: ${event.data}`,
            };
            return updated;
          });
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  if (!isReady) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Ask Questions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p>Indexing company filings...</p>
            <p className="text-sm mt-2">Chat will be available once complete</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Ask About {ticker}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[200px] max-h-[400px]">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                Ask any question about {ticker}&apos;s SEC filings
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <Button
                    key={q}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSend(q)}
                    disabled={isStreaming}
                  >
                    {q}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, i) => (
              <div
                key={i}
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : ""
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2"
                      : "space-y-2"
                  }`}
                >
                  {message.role === "user" ? (
                    <p>{message.content}</p>
                  ) : (
                    <>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        {message.content || (
                          <Skeleton className="h-4 w-48" />
                        )}
                      </div>
                      {message.sources && message.sources.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          <FileText className="h-3 w-3 text-muted-foreground" />
                          {message.sources.map((source, j) => (
                            <Badge
                              key={j}
                              variant="outline"
                              className="text-xs"
                            >
                              {source.section}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Sources indicator */}
        {isStreaming && currentSources.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
            <FileText className="h-3 w-3" />
            <span>Using:</span>
            {currentSources.map((source, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {source.section}
              </Badge>
            ))}
          </div>
        )}

        {/* Input area */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={isStreaming || !input.trim()}>
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
