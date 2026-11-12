import React, { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { GitBranch, Copy, Check } from "lucide-react";
import { useThemeStore } from "../../stores/useThemeStore";

interface MermaidBlockProps {
  code?: string;
  chart?: string;
  title?: string;
}

export const MermaidBlock: React.FC<MermaidBlockProps> = ({ code, chart, title }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const theme = useThemeStore((state) => state.theme);

  const rawCode = code || chart || "";

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: theme === "dark" ? "dark" : "default",
      securityLevel: "loose",
      fontFamily: "Inter, sans-serif",
    });

    const renderDiagram = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, rawCode);
        setSvgContent(svg);
        setError(null);
      } catch (err: unknown) {
        let msg = "Failed to render Mermaid diagram";
        if (err && typeof err === "object" && "message" in err) {
          msg = String((err as { message: string }).message);
        }
        setError(msg);
      }
    };

    if (rawCode) {
      renderDiagram();
    }
  }, [rawCode, theme]);

  const handleCopy = () => {
    navigator.clipboard.writeText(rawCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card overflow-hidden shadow-sm">
      <div className="px-4 py-2.5 bg-muted/40 border-b border-border/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-amber-500" />
          <h5 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
            {title || "DECISION LOGIC / PROCESS FLOWCHART"}
          </h5>
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1 text-[11px] font-mono text-muted-foreground hover:text-foreground px-2 py-0.5 rounded bg-muted/60 transition-colors"
          title="Copy Mermaid source"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-500" /> Copied
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" /> Copy
            </>
          )}
        </button>
      </div>

      <div className="p-4 overflow-x-auto flex justify-center bg-background/50">
        {error ? (
          <div className="text-left w-full">
            <p className="text-xs text-amber-500 mb-1 font-mono">
              Syntax Diagram Preview:
            </p>
            <pre className="text-xs p-3 rounded bg-muted font-mono whitespace-pre-wrap overflow-x-auto">
              {code}
            </pre>
          </div>
        ) : (
          <div
            ref={containerRef}
            className="mermaid-wrapper max-w-full"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}
      </div>
    </div>
  );
};
