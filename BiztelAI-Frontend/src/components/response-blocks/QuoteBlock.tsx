import React from "react";
import { Quote } from "lucide-react";

interface QuoteBlockProps {
  quote: string;
  source: string;
  page_number?: number;
}

export const QuoteBlock: React.FC<QuoteBlockProps> = ({ quote, source, page_number }) => {
  return (
    <div className="my-2.5 rounded-lg border-l-2 border-amber-500 bg-muted/20 p-3 pl-3.5">
      <div className="flex items-start gap-2">
        <Quote className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5 opacity-70" />
        <div className="flex-1">
          <p className="text-xs font-serif italic text-foreground leading-relaxed">
            "{quote}"
          </p>
          <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground font-mono">
            <span>— {source}</span>
            {page_number && <span>PAGE {page_number}</span>}
          </div>
        </div>
      </div>
    </div>
  );
};
