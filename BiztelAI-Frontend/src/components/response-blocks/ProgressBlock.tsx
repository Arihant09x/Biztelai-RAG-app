import React from "react";
import { Activity } from "lucide-react";

export interface ProgressBlockProps {
  label: string;
  value?: number;
  current?: number;
  max?: number;
  total?: number;
  unit?: string;
}

export const ProgressBlock: React.FC<ProgressBlockProps> = ({
  label,
  value,
  current,
  max,
  total,
  unit = "%",
}) => {
  const resolvedValue = current ?? value ?? 0;
  const resolvedMax = total ?? max ?? 100;
  const percent = Math.min(
    100,
    Math.max(0, Math.round((resolvedValue / (resolvedMax || 1)) * 100))
  );

  return (
    <div className="my-2.5 rounded-lg border border-border/80 bg-card p-3 shadow-sm font-mono">
      <div className="flex items-center justify-between mb-1.5">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
          <Activity className="w-3.5 h-3.5 text-amber-500" />
          {label}
        </span>
        <span className="text-xs font-bold text-foreground tabular-nums">
          {resolvedValue} {unit !== "%" ? unit : ""} ({percent}%)
        </span>
      </div>

      <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-amber-500 h-full transition-all duration-200"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
};
