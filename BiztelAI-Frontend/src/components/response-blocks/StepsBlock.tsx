import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Circle, Wrench, BookOpen } from "lucide-react";
import { StepItem } from "../../types/blocks";
import { cn } from "../../lib/utils";

interface StepsBlockProps {
  title?: string;
  steps: StepItem[];
  onOpenCitation?: (citation: string) => void;
}

export const StepsBlock: React.FC<StepsBlockProps> = ({ title, steps, onOpenCitation }) => {
  const [completedSteps, setCompletedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (stepNumber: number) => {
    setCompletedSteps((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  const completedCount = Object.values(completedSteps).filter(Boolean).length;
  const progressPercent = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;

  return (
    <div className="my-3 rounded-xl border border-border/80 bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-border/60 mb-3">
        <div>
          <h4 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            {title || "STANDARD OPERATING PROCEDURE STEPS"}
          </h4>
          <p className="text-[11px] text-muted-foreground mt-0.5 font-sans">
            Floor verification checklist ({completedCount} of {steps.length} verified)
          </p>
        </div>

        {/* Progress pill */}
        <div className="flex items-center gap-2 font-mono">
          <div className="w-16 bg-muted rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-amber-500 h-full transition-all duration-200"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span className="text-[11px] font-bold text-foreground">{progressPercent}%</span>
        </div>
      </div>

      <div className="space-y-2">
        {steps.map((step, idx) => {
          const stepNum = step.step_number || idx + 1;
          const isDone = !!completedSteps[stepNum];
          const instructionText = step.instruction || (step as unknown as { content?: string }).content || "";

          return (
            <div
              key={stepNum}
              onClick={() => toggleStep(stepNum)}
              className={cn(
                "group relative rounded-lg border p-3 transition-colors cursor-pointer select-none",
                isDone
                  ? "border-emerald-500/40 bg-emerald-500/5"
                  : step.critical
                  ? "border-amber-500/50 bg-amber-500/5"
                  : "border-border/60 bg-muted/15 hover:bg-muted/30"
              )}
            >
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  className="mt-0.5 text-muted-foreground hover:text-amber-500 transition-colors"
                  aria-label={`Toggle step ${stepNum}`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <Circle className="w-4 h-4 text-muted-foreground/60" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span
                      className={cn(
                        "inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[10px] font-bold font-mono border",
                        isDone
                          ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                          : step.critical
                          ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                          : "bg-muted text-foreground border-border"
                      )}
                    >
                      STEP {stepNum}
                    </span>

                    {step.critical && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-mono uppercase bg-red-500/10 text-red-500 border border-red-500/30">
                        <AlertTriangle className="w-3 h-3" /> Critical Safety Point
                      </span>
                    )}

                    {step.tool && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground bg-muted/60 px-1.5 py-0.2 rounded font-mono border border-border/40">
                        <Wrench className="w-2.5 h-2.5 text-amber-500" /> {step.tool}
                      </span>
                    )}
                  </div>

                  <p
                    className={cn(
                      "text-xs font-normal leading-relaxed font-sans",
                      isDone ? "line-through text-muted-foreground" : "text-foreground"
                    )}
                  >
                    {instructionText}
                  </p>

                  {step.warning && (
                    <div className="mt-2 flex items-start gap-1.5 p-2 rounded bg-amber-500/10 border border-amber-500/30 text-xs text-amber-600 dark:text-amber-300 font-sans">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                      <span>{step.warning}</span>
                    </div>
                  )}

                  {step.citation && (
                    <div className="mt-2 flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenCitation?.(step.citation!);
                        }}
                        className="inline-flex items-center gap-1 text-[10px] text-amber-500 hover:underline font-mono"
                      >
                        <BookOpen className="w-3 h-3" />
                        REF: {step.citation}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
