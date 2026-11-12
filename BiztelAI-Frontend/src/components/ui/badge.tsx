import React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "amber" | "emerald" | "destructive";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  ...props
}) => {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-mono font-medium transition-colors border",
        {
          "bg-primary/10 text-primary border-primary/20": variant === "default",
          "bg-muted text-muted-foreground border-border": variant === "secondary",
          "border-border text-foreground bg-transparent": variant === "outline",
          "bg-amber-500/10 text-amber-500 dark:text-amber-400 border-amber-500/30":
            variant === "amber",
          "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30":
            variant === "emerald",
          "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30":
            variant === "destructive",
        },
        className
      )}
      {...props}
    />
  );
};

