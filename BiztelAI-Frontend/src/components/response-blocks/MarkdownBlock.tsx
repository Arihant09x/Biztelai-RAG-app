import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownBlockProps {
  content: string;
  className?: string;
}

export const MarkdownBlock: React.FC<MarkdownBlockProps> = ({ content, className = "" }) => {
  return (
    <div
      className={`prose prose-slate dark:prose-invert max-w-none text-xs sm:text-sm leading-relaxed prose-p:my-2 prose-headings:font-semibold prose-headings:my-2.5 prose-ul:my-2 prose-li:my-0.5 prose-strong:text-foreground prose-strong:font-semibold font-sans ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const isInline = !className;
            return isInline ? (
              <code
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-amber-500 dark:text-amber-400 font-medium border border-border/50"
                {...props}
              >
                {children}
              </code>
            ) : (
              <pre className="rounded-lg bg-slate-900 dark:bg-slate-950 p-3 text-xs text-slate-100 overflow-x-auto my-2 border border-border/80 font-mono">
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-2 border border-border/80 rounded-lg">
                <table className="w-full text-xs text-left">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="bg-muted/70 px-3 py-2 font-mono text-[11px] font-semibold text-foreground border-b border-border">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3 py-2 border-b border-border/50 text-foreground/80 tabular-nums">
                {children}
              </td>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
