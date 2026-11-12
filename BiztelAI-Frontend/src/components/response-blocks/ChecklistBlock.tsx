import React, { useState } from "react";
import { CheckSquare, Square, RotateCcw, AlertCircle } from "lucide-react";
import { ChecklistItem } from "../../types/blocks";
import { cn } from "../../lib/utils";

interface ChecklistBlockProps {
  title?: string;
  items: ChecklistItem[];
}

export const ChecklistBlock: React.FC<ChecklistBlockProps> = ({ title, items }) => {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    items.forEach((item) => {
      if (item.checked) initial[item.id] = true;
    });
    return initial;
  });

  const toggleItem = (id: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const resetAll = () => setCheckedItems({});

  const completedCount = Object.values(checkedItems).filter(Boolean).length;
  const isComplete = items.length > 0 && completedCount === items.length;

  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-border/60 mb-3">
        <div>
          <h4 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono flex items-center gap-2">
            <CheckSquare className="w-3.5 h-3.5 text-amber-500" />
            {title || "OPERATIONAL VERIFICATION CHECKLIST"}
          </h4>
          <span className="text-[11px] text-muted-foreground font-sans">
            {completedCount} of {items.length} verified
          </span>
        </div>

        <div className="flex items-center gap-2 font-mono">
          {completedCount > 0 && (
            <button
              onClick={resetAll}
              className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground px-2 py-0.5 rounded bg-muted/60 transition-colors"
              title="Reset checklist"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          )}

          <span
            className={cn(
              "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
              isComplete
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                : "bg-muted text-muted-foreground border-border"
            )}
          >
            {isComplete ? "VERIFIED" : "PENDING"}
          </span>
        </div>
      </div>

      <div className="space-y-1.5 font-sans">
        {items.map((item) => {
          const isChecked = !!checkedItems[item.id];
          const labelText = item.label || (item as unknown as { content?: string }).content || "";

          return (
            <div
              key={item.id}
              onClick={() => toggleItem(item.id)}
              className={cn(
                "flex items-start gap-2.5 p-2 rounded-lg border transition-colors cursor-pointer select-none",
                isChecked
                  ? "border-emerald-500/30 bg-emerald-500/5"
                  : "border-border/50 bg-muted/10 hover:bg-muted/25"
              )}
            >
              <button
                type="button"
                className="mt-0.5 text-muted-foreground hover:text-amber-500 transition-colors"
                aria-label={`Toggle checklist item ${labelText}`}
              >
                {isChecked ? (
                  <CheckSquare className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <Square className="w-3.5 h-3.5 text-muted-foreground/60" />
                )}
              </button>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "text-xs font-normal leading-tight",
                      isChecked ? "line-through text-muted-foreground" : "text-foreground"
                    )}
                  >
                    {labelText}
                  </span>

                  {item.required && (
                    <span className="text-[9px] uppercase font-mono font-bold text-red-500 bg-red-500/10 px-1 py-0.2 rounded border border-red-500/20">
                      REQUIRED
                    </span>
                  )}
                </div>

                {item.tip && (
                  <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1 font-sans">
                    <AlertCircle className="w-3 h-3 shrink-0 text-amber-500" />
                    {item.tip}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
