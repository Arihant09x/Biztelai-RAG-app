import React, { useState } from "react";
import {
  User,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  Clock,
  BookOpen,
  ArrowRight,
  ExternalLink,
  FileText,
} from "lucide-react";
import { ChatMessage, SourceCitation } from "../../types/chat";
import { ResponseRenderer } from "../response-blocks/ResponseRenderer";
import { CitationsDialog } from "./CitationsDialog";
import { useChatStore } from "../../stores/useChatStore";
import { useDocumentStore } from "../../stores/useDocumentStore";
import { cn, formatDate } from "../../lib/utils";
import { Button } from "../ui/button";

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showCitationsDialog, setShowCitationsDialog] = useState(false);
  const { submitFeedback, sendMessage } = useChatStore();
  const { openPreview } = useDocumentStore();

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = (type: "positive" | "negative") => {
    if (type === "negative") {
      setShowFeedbackModal(true);
    } else {
      submitFeedback(message.id, "positive");
    }
  };

  const submitNegativeFeedback = () => {
    submitFeedback(message.id, "negative", feedbackComment);
    setShowFeedbackModal(false);
    setFeedbackComment("");
  };

  const handleOpenSourcePDF = (src: SourceCitation) => {
    openPreview(src.document_id, src.page_number || 1);
  };

  return (
    <div
      className={cn(
        "flex gap-3 my-4 group transition-opacity",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* Assistant Avatar (Precision Slate & Safety Amber) */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-900 border border-amber-500/40 flex items-center justify-center text-amber-500 font-mono font-bold text-xs shrink-0 mt-0.5 select-none shadow-sm ring-1 ring-amber-500/20">
          PA
        </div>
      )}

      {/* Message Bubble (ChatGPT / WhatsApp Industrial Styling) */}
      <div
        className={cn(
          "max-w-2xl sm:max-w-3xl rounded-2xl p-4 sm:p-5 transition-colors shadow-sm",
          isUser
            ? "bg-slate-800/90 text-slate-100 border border-slate-700/80 rounded-tr-sm ml-12"
            : "bg-card/95 border border-border/80 text-foreground rounded-tl-sm mr-12"
        )}
      >
        {/* User Question */}
        {isUser ? (
          <p className="text-xs sm:text-sm font-normal leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          <div className="space-y-3.5">
            {/* Structured response blocks or formatted markdown */}
            <ResponseRenderer
              blocks={message.blocks}
              fallbackContent={message.content}
              onOpenCitation={(cid) => {
                const found = message.sources?.find((s) => s.id === cid);
                if (found) handleOpenSourcePDF(found);
              }}
            />

            {/* Source Citations & PDF Tag Links (Directly Below Response) */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3.5 pt-3 border-t border-border/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-amber-500" />
                    Verified Ground Truth Sources ({message.sources.length})
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowCitationsDialog(true)}
                    className="text-[11px] font-mono text-amber-500 hover:text-amber-400 font-medium inline-flex items-center gap-1 hover:underline transition-colors cursor-pointer"
                  >
                    <span>Inspect Quotes</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>

                {/* Clickable Citation Tag Links */}
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((src, idx) => (
                    <button
                      key={src.id || idx}
                      type="button"
                      onClick={() => handleOpenSourcePDF(src)}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono bg-muted/60 hover:bg-amber-500/10 border border-border/80 hover:border-amber-500/40 text-foreground transition-all cursor-pointer group/tag text-left shadow-sm"
                      title={`Click to open ${src.document_title || "SOP"} on Page ${src.page_number || 1}`}
                    >
                      <FileText className="w-3.5 h-3.5 text-amber-500 shrink-0 group-hover/tag:scale-110 transition-transform" />
                      <span className="font-sans font-medium text-xs text-foreground/90 group-hover/tag:text-amber-500 transition-colors truncate max-w-[200px] sm:max-w-[260px]">
                        {src.document_title || "SOP Document"}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-background border border-border/60 text-muted-foreground font-mono shrink-0">
                        Page {src.page_number || 1}
                      </span>
                      {src.relevance_score !== undefined && (
                        <span className="text-[10px] font-bold text-amber-500/80 font-mono shrink-0">
                          {Math.round(src.relevance_score * 100)}%
                        </span>
                      )}
                      <ExternalLink className="w-3 h-3 text-amber-500/60 group-hover/tag:text-amber-400 shrink-0" />
                    </button>
                  ))}
                </div>

                <CitationsDialog
                  isOpen={showCitationsDialog}
                  onClose={() => setShowCitationsDialog(false)}
                  sources={message.sources}
                />
              </div>
            )}

            {/* Related Operational Inquiries */}
            {message.suggested_followups && message.suggested_followups.length > 0 && (
              <div className="pt-3 border-t border-border/60">
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground block mb-2">
                  Related Operational Inquiries:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {message.suggested_followups.map((followup, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(followup)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-muted/60 hover:bg-muted text-xs text-foreground/90 hover:text-amber-500 transition-colors border border-border/60 text-left"
                    >
                      <ArrowRight className="w-3 h-3 text-amber-500 shrink-0" />
                      <span>{followup}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer Meta (Timestamp, Latency, Feedback, Copy) */}
        <div
          className={cn(
            "flex items-center gap-3 mt-3 pt-2 text-[10px] font-mono border-t border-border/40 text-muted-foreground",
            isUser ? "justify-end" : "justify-between"
          )}
        >
          <div className="flex items-center gap-2">
            <span>{formatDate(message.created_at)}</span>
            {message.latency_ms !== undefined && (
              <span className="inline-flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {message.latency_ms}ms
              </span>
            )}
            {message.confidence !== undefined && (
              <span className="px-1.5 py-0.2 rounded bg-muted text-muted-foreground font-semibold">
                {(message.confidence * 100).toFixed(0)}% MATCH
              </span>
            )}
          </div>

          {!isUser && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                title="Copy Answer"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              </button>

              <button
                onClick={() => handleFeedback("positive")}
                className={cn(
                  "p-1 rounded hover:bg-muted transition-colors cursor-pointer",
                  message.feedback === "positive"
                    ? "text-emerald-500 font-bold"
                    : "text-muted-foreground hover:text-foreground"
                )}
                title="Verified Ground Truth"
              >
                <ThumbsUp className="w-3 h-3" />
              </button>

              <button
                onClick={() => handleFeedback("negative")}
                className={cn(
                  "p-1 rounded hover:bg-muted transition-colors cursor-pointer",
                  message.feedback === "negative"
                    ? "text-red-500 font-bold"
                    : "text-muted-foreground hover:text-foreground"
                )}
                title="Needs Review"
              >
                <ThumbsDown className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      )}

      {/* Feedback Review Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-card border border-border p-5 rounded-xl max-w-md w-full shadow-xl">
            <h4 className="font-semibold text-xs text-foreground mb-1 uppercase tracking-wider font-mono">
              FLAG SOP RESPONSE FOR CORRECTION
            </h4>
            <p className="text-xs text-muted-foreground mb-3 font-sans">
              Help us maintain precision. What discrepancy did you notice vs the verified operating manual?
            </p>
            <textarea
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="e.g., The pressure spec was 180 bar instead of 200 bar in the revised manual..."
              rows={3}
              className="w-full rounded-lg border border-border bg-background p-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-amber-500 font-sans"
            />
            <div className="flex justify-end gap-2 mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFeedbackModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="amber"
                size="sm"
                onClick={submitNegativeFeedback}
              >
                Submit Discrepancy
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
