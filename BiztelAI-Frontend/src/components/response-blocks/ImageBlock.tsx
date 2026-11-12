import React from "react";
import { Image as ImageIcon, ExternalLink } from "lucide-react";

interface ImageBlockProps {
  url?: string;
  alt?: string;
  caption?: string;
  page_number?: number;
  document_title?: string;
  onOpenPage?: (page: number) => void;
}

export const ImageBlock: React.FC<ImageBlockProps> = ({
  url,
  caption,
  page_number,
  document_title,
  onOpenPage,
}) => {
  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card overflow-hidden shadow-sm">
      <div className="relative bg-muted/30 flex items-center justify-center p-4 min-h-[140px]">
        {url ? (
          <img
            src={url}
            alt={caption || "SOP Diagram / Illustration"}
            className="max-h-96 w-auto rounded-lg object-contain shadow-sm border border-border/50"
            loading="lazy"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-muted-foreground p-5">
            <ImageIcon className="w-8 h-8 mb-1.5 opacity-50 text-amber-500" />
            <span className="text-xs font-mono font-medium">TECHNICAL DIAGRAM / SCHEMATIC</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 font-sans">
              Extracted from {document_title || "SOP Document"}
            </span>
          </div>
        )}

        {page_number && (
          <div className="absolute top-2.5 right-2.5">
            <button
              onClick={() => onOpenPage?.(page_number)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-background/90 backdrop-blur border border-border text-[10px] font-mono font-medium text-foreground hover:bg-background transition-colors"
            >
              PAGE {page_number}
              <ExternalLink className="w-3 h-3 text-muted-foreground" />
            </button>
          </div>
        )}
      </div>

      {caption && (
        <div className="px-3.5 py-1.5 border-t border-border/60 bg-muted/10 text-xs text-muted-foreground italic flex items-center justify-between font-sans">
          <span>{caption}</span>
          {document_title && (
            <span className="text-[10px] font-mono not-italic text-foreground/80">
              {document_title}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
