import React, { useState } from "react";
import { ChevronDown, ChevronRight, HelpCircle } from "lucide-react";
import { MarkdownBlock } from "./MarkdownBlock";

export interface AccordionSection {
  id?: string;
  title: string;
  content: string;
}

export interface AccordionBlockProps {
  title?: string;
  content?: string;
  sections?: AccordionSection[];
}

export const AccordionBlock: React.FC<AccordionBlockProps> = ({ title, content, sections }) => {
  const [openStates, setOpenStates] = useState<Record<number, boolean>>({});

  const list: AccordionSection[] =
    sections && sections.length > 0
      ? sections
      : title && content
      ? [{ title, content }]
      : [];

  const toggle = (idx: number) => {
    setOpenStates((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="my-2 space-y-1.5">
      {list.map((sec, idx) => {
        const isOpen = !!openStates[idx];
        return (
          <div
            key={sec.id || idx}
            className="rounded-lg border border-border/80 bg-card overflow-hidden transition-colors"
          >
            <button
              type="button"
              onClick={() => toggle(idx)}
              className="w-full flex items-center justify-between px-3.5 py-2 text-left bg-muted/20 hover:bg-muted/40 transition-colors"
            >
              <span className="flex items-center gap-2 text-xs font-semibold text-foreground font-sans">
                <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
                {sec.title}
              </span>
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
              )}
            </button>

            {isOpen && (
              <div className="p-3.5 pt-2 border-t border-border/50 bg-background/50 text-xs">
                <MarkdownBlock content={sec.content} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
