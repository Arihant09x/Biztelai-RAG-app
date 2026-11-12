import React, { useEffect, useRef } from "react";
import { AlertCircle, RefreshCw, Loader2 } from "lucide-react";
import { useChatStore } from "../../stores/useChatStore";
import { MessageBubble } from "./MessageBubble";
import { EmptyChatState } from "./EmptyChatState";
import { SourceDrawer } from "./SourceDrawer";
import { Button } from "../ui/button";

export const ChatContainer: React.FC = () => {
  const { messages, isLoading, error, sendMessage } = useChatStore();
  const scrollEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const lastUserQuery = [...messages].reverse().find((m) => m.role === "user")?.content;

  return (
    <div className="relative flex-1 overflow-y-auto px-4 py-6 sm:px-6">
      <div className="max-w-3xl mx-auto flex flex-col min-h-full">
        {messages.length === 0 ? (
          <EmptyChatState />
        ) : (
          <div className="flex-1 space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {/* Loading / Generating State */}
            {isLoading && (
              <div className="flex gap-3 my-4 animate-in fade-in duration-200">
                <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500 font-mono font-bold text-[11px] shrink-0 mt-1 select-none">
                  PA
                </div>
                <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm max-w-md">
                  <div className="flex items-center gap-2 text-xs font-mono font-medium text-amber-500">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    SEARCHING FACTORY SOP DATABASE...
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 font-sans">
                    Matching pgvector chunks, extracting tables and grounding answer with verified citations.
                  </p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-3 p-3.5 rounded-xl border border-destructive/40 bg-destructive/10 text-destructive my-3">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1 text-xs">
                  <h5 className="font-semibold font-mono uppercase text-[11px] mb-0.5">COPILOT QUERY FAILED</h5>
                  <p className="font-sans">{error}</p>
                </div>
                {lastUserQuery && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage(lastUserQuery)}
                    className="gap-1 h-7 text-xs border-destructive/40 hover:bg-destructive/20 text-destructive"
                  >
                    <RefreshCw className="w-3 h-3" /> Retry
                  </Button>
                )}
              </div>
            )}

            <div ref={scrollEndRef} />
          </div>
        )}
      </div>

      {/* Slide-over document source drawer with PDF.js */}
      <SourceDrawer />
    </div>
  );
};
