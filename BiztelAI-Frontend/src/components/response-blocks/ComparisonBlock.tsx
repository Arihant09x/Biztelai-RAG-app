import React from "react";
import { GitCompare } from "lucide-react";

interface ComparisonBlockProps {
  title?: string;
  headers?: string[];
  items?: Array<{
    feature: string;
    option_a: string;
    option_b: string;
  }>;
  leftTitle?: string;
  rightTitle?: string;
  leftItems?: string[];
  rightItems?: string[];
}

export const ComparisonBlock: React.FC<ComparisonBlockProps> = ({
  title,
  headers,
  items,
  leftTitle,
  rightTitle,
  leftItems,
  rightItems,
}) => {
  const tableHeaders = headers || [
    "Parameter / Condition",
    leftTitle || "Specification A",
    rightTitle || "Specification B",
  ];

  const normalizedItems = items || (leftItems || []).map((left, idx) => ({
    feature: `Check ${idx + 1}`,
    option_a: left,
    option_b: (rightItems && rightItems[idx]) || "—",
  }));
  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card overflow-hidden shadow-sm">
      <div className="px-4 py-2 bg-muted/40 border-b border-border/60 flex items-center gap-2">
        <GitCompare className="w-3.5 h-3.5 text-amber-500" />
        <h5 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
          {title || "SPECIFICATION COMPARISON MATRIX"}
        </h5>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-muted/70 border-b border-border text-foreground font-semibold font-mono text-[11px]">
              <th className="px-3.5 py-2">{tableHeaders[0] || "Parameter"}</th>
              <th className="px-3.5 py-2">{tableHeaders[1] || "Option A"}</th>
              <th className="px-3.5 py-2">{tableHeaders[2] || "Option B"}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50 font-sans">
            {normalizedItems.map((item, idx) => (
              <tr key={idx} className="hover:bg-muted/20 transition-colors even:bg-muted/5">
                <td className="px-3.5 py-2 font-medium text-foreground">{item.feature}</td>
                <td className="px-3.5 py-2 text-foreground/80 tabular-nums">{item.option_a}</td>
                <td className="px-3.5 py-2 text-foreground/80 tabular-nums">{item.option_b}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
