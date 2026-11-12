import React, { useState, useRef, useEffect } from "react";
import { Send, Square, Filter, X } from "lucide-react";
import { useChatStore } from "../../stores/useChatStore";
import { Button } from "../ui/button";

export const ChatComposer: React.FC = () => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const {
    isLoading,
    sendMessage,
    stopGeneration,
    selectedCategory,
    setSelectedCategory,
    selectedDocumentId,
    setSelectedDocumentId,
  } = useChatStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border/80 bg-background/95 backdrop-blur px-4 py-3 sm:px-6">
      <div className="max-w-3xl mx-auto">
        {/* Active Filters Scope Banner */}
        {(selectedCategory || selectedDocumentId) && (
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
              <Filter className="w-3 h-3 text-amber-500" /> SCOPE:
            </span>
            {selectedCategory && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                CATEGORY: {selectedCategory.toUpperCase()}
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="hover:text-foreground ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {selectedDocumentId && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                DOC: {selectedDocumentId.slice(0, 8)}
                <button
                  onClick={() => setSelectedDocumentId(null)}
                  className="hover:text-foreground ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
        )}

        {/* Form Box */}
        <form
          onSubmit={handleSubmit}
          className="relative flex items-end gap-2 rounded-xl border border-border bg-card p-2 shadow-sm focus-within:border-amber-500/60 focus-within:ring-1 focus-within:ring-amber-500/30 transition-colors"
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Inquire on machine specifications, operating tolerances, LOTO procedures..."
            rows={1}
            disabled={isLoading}
            className="flex-1 max-h-36 min-h-[40px] resize-none bg-transparent px-3 py-2 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 font-sans"
          />

          <div className="flex items-center gap-1 shrink-0 pb-1">
            {isLoading ? (
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={stopGeneration}
                className="gap-1.5 h-8 text-xs font-mono"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>STOP</span>
              </Button>
            ) : (
              <Button
                type="submit"
                variant="amber"
                size="icon"
                disabled={!input.trim()}
                className="h-8 w-8 rounded-lg shadow-sm"
                aria-label="Send query"
              >
                <Send className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </form>

        <div className="flex items-center justify-between mt-2 px-1 text-[11px] font-mono text-muted-foreground">
          <span>Grounded in indexed factory SOP database</span>
          <span className="hidden sm:inline">↵ to send, Shift + ↵ for newline</span>
        </div>
      </div>
    </div>
  );
};
