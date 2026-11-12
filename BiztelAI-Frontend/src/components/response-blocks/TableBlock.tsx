import React from "react";
import { Table as TableIcon } from "lucide-react";

interface TableBlockProps {
  title?: string;
  headers: string[];
  rows: (string | number)[][];
  caption?: string;
}

export const TableBlock: React.FC<TableBlockProps> = ({ title, headers, rows, caption }) => {
  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card overflow-hidden shadow-sm">
      {title && (
        <div className="px-4 py-2 bg-muted/40 border-b border-border/60 flex items-center gap-2">
          <TableIcon className="w-3.5 h-3.5 text-amber-500" />
          <h5 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
            {title}
          </h5>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-muted/70 border-b border-border text-foreground font-semibold font-mono text-[11px]">
              {headers.map((h, i) => (
                <th key={i} className="px-3.5 py-2 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50 font-sans">
            {rows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-muted/20 transition-colors even:bg-muted/5"
              >
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3.5 py-2 text-foreground/90 whitespace-nowrap tabular-nums">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {caption && (
        <div className="px-4 py-1.5 bg-muted/20 border-t border-border/40 text-[11px] text-muted-foreground italic font-sans">
          {caption}
        </div>
      )}
    </div>
  );
};
