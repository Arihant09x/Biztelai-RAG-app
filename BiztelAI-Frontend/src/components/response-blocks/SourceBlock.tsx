import React from "react";
import { FileText, ExternalLink, Hash } from "lucide-react";
import { useDocumentStore } from "../../stores/useDocumentStore";

interface SourceBlockProps {
  document_id: string;
  document_title: string;
  page_number: number;
  snippet: string;
  similarity?: number;
}

export const SourceBlock: React.FC<SourceBlockProps> = ({
  document_id,
  document_title,
  page_number,
  snippet,
  similarity,
}) => {
  const { documents, openPreview } = useDocumentStore();

  const handleOpen = () => {
    const doc = documents.find((d) => d.id === document_id) || {
      id: document_id,
      title: document_title,
      category: "sop",
      status: "indexed",
      file_size_bytes: 0,
      page_count: page_number,
      chunk_count: 1,
      created_at: new Date().toISOString(),
    };
    openPreview(doc, page_number);
  };

  return (
    <div
      onClick={handleOpen}
      className="group my-2 flex flex-col rounded-lg border border-border/80 bg-muted/20 p-3 hover:bg-muted/40 hover:border-amber-500/40 transition-colors cursor-pointer select-none"
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-3.5 h-3.5 text-amber-500 shrink-0" />
          <span className="font-semibold text-xs text-foreground truncate font-sans">
            {document_title}
          </span>
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded text-[10px] font-mono bg-muted text-muted-foreground border border-border/60">
            <Hash className="w-2.5 h-2.5" /> p.{page_number}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {similarity !== undefined && (
            <span className="text-[10px] font-mono font-medium text-amber-500 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">
              {(similarity * 100).toFixed(0)}% MATCH
            </span>
          )}
          <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-amber-500 transition-colors" />
        </div>
      </div>

      <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed font-sans">
        "{snippet}"
      </p>
    </div>
  );
};
