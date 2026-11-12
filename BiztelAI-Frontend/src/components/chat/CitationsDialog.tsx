import React from "react";
import { X, BookOpen, ExternalLink, Copy, Check, ShieldCheck, FileText } from "lucide-react";
import { SourceCitation } from "../../types/chat";
import { useDocumentStore } from "../../stores/useDocumentStore";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";

interface CitationsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sources: SourceCitation[];
}

export const CitationsDialog: React.FC<CitationsDialogProps> = ({ isOpen, onClose, sources }) => {
  const { documents, openPreview } = useDocumentStore();
  const [copiedIdx, setCopiedIdx] = React.useState<number | null>(null);

  if (!isOpen || !sources || sources.length === 0) return null;

  const handleOpenDoc = (src: SourceCitation) => {
    // Find matching document item or create placeholder
    const foundDoc = documents.find((d) => d.id === src.document_id);
    if (foundDoc) {
      openPreview(foundDoc, src.page_number);
    } else {
      openPreview(
        {
          id: src.document_id,
          title: src.document_title || "SOP Reference Document",
          category: "sop",
          status: "indexed",
          file_size_bytes: 0,
          page_count: src.page_number || 1,
          chunk_count: 0,
          created_at: new Date().toISOString(),
        },
        src.page_number
      );
    }
    onClose();
  };

  const handleCopySnippet = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-150 select-none">
      <div className="bg-card border border-border w-full max-w-2xl max-h-[85vh] rounded-xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-border/80 flex items-center justify-between bg-muted/40 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono flex items-center gap-2">
                GROUND TRUTH CITATIONS
                <Badge variant="amber" className="text-[10px] py-0">
                  {sources.length} VERIFIED SOURCES
                </Badge>
              </h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">
                Exact SOP paragraphs and pages retrieved to generate this response.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Citations List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {sources.map((src, idx) => {
            const similarityPercent =
              src.similarity !== undefined ? Math.round(src.similarity * 100) : null;

            return (
              <div
                key={idx}
                className="rounded-xl border border-border/70 bg-muted/20 hover:bg-muted/30 transition-colors p-4 space-y-3"
              >
                {/* Source Top Meta */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <span className="font-semibold text-xs text-foreground block truncate">
                        {src.document_title || "Manufacturing Standard Operating Procedure"}
                      </span>
                      <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground mt-0.5">
                        <span className="text-amber-500 font-bold">PAGE {src.page_number}</span>
                        <span>•</span>
                        <span>DOC ID: {src.document_id.slice(0, 8)}</span>
                      </div>
                    </div>
                  </div>

                  {similarityPercent !== null && (
                    <Badge variant="secondary" className="font-mono text-[10px] shrink-0">
                      {similarityPercent}% RELEVANCE
                    </Badge>
                  )}
                </div>

                {/* Excerpt Box */}
                <div className="relative p-3 rounded-lg bg-background/80 border border-border/60 text-xs font-mono text-foreground/90 leading-relaxed whitespace-pre-wrap selection:bg-amber-500/20">
                  <span className="text-amber-500/60 font-serif text-lg leading-none absolute -top-1 left-2 select-none">
                    “
                  </span>
                  <div className="pl-3">{src.snippet}</div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-1 text-xs">
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-emerald-500">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    GROUNDED FACTORY RECORD
                  </span>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopySnippet(src.snippet, idx)}
                      className="h-7 text-[11px] gap-1 text-muted-foreground hover:text-foreground"
                    >
                      {copiedIdx === idx ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-500" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Quote</span>
                        </>
                      )}
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenDoc(src)}
                      className="h-7 text-[11px] gap-1.5 text-amber-500 hover:text-amber-400 border-amber-500/30 hover:border-amber-500/60 bg-amber-500/5 hover:bg-amber-500/10"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Inspect PDF (Page {src.page_number})</span>
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 border-t border-border/80 bg-muted/40 flex items-center justify-between text-[11px] font-mono text-muted-foreground shrink-0">
          <span>SOURCE VALIDATION: STRICT STRICT-GROUNDED RAG</span>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-7 text-xs">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

