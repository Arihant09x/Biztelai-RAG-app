import React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost" | "destructive" | "amber";
  size?: "sm" | "default" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-500 disabled:pointer-events-none disabled:opacity-50 select-none text-xs rounded-lg",
          {
            "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm":
              variant === "default",
            "bg-muted text-foreground hover:bg-muted/80": variant === "secondary",
            "border border-border bg-transparent hover:bg-muted text-foreground":
              variant === "outline",
            "hover:bg-muted text-foreground": variant === "ghost",
            "bg-destructive text-destructive-foreground hover:bg-destructive/90":
              variant === "destructive",
            "bg-amber-500 text-slate-950 font-semibold hover:bg-amber-400 shadow-sm":
              variant === "amber",
          },
          {
            "h-8 px-3": size === "sm",
            "h-9 px-4 py-2": size === "default",
            "h-10 px-6": size === "lg",
            "h-8 w-8 p-0": size === "icon",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

