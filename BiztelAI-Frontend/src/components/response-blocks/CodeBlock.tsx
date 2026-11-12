import React, { useState } from "react";
import { Terminal, Copy, Check } from "lucide-react";

export interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language = "plaintext", title }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2.5 rounded-lg border border-border/80 bg-slate-900 dark:bg-slate-950 overflow-hidden text-slate-100 shadow-sm font-mono">
      <div className="flex items-center justify-between px-3 py-1 bg-slate-800/80 border-b border-slate-700/60 text-[10px] text-slate-400">
        <span className="flex items-center gap-1.5 uppercase font-semibold text-amber-400">
          <Terminal className="w-3 h-3" />
          {title || language}
        </span>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1 text-slate-400 hover:text-slate-100 px-1.5 py-0.5 rounded transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" /> Copied
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" /> Copy
            </>
          )}
        </button>
      </div>

      <pre className="p-3 text-xs overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};
