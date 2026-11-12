import React from "react";
import { cn } from "../../lib/utils";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ className, size = "md", showText = true }) => {
  const sizeClasses = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-10 h-10",
  };

  return (
    <div className={cn("flex items-center gap-2.5 select-none", className)}>
      <div
        className={cn(
          "rounded-lg bg-slate-900 border border-amber-500/30 flex items-center justify-center p-1 relative shadow-sm shrink-0",
          sizeClasses[size]
        )}
      >
        <svg
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Caliper arms */}
          <path
            d="M14 10V20L20 24L14 28V38"
            stroke="#F59E0B"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M34 10V20L28 24L34 28V38"
            stroke="#F59E0B"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Caliper rails */}
          <path d="M12 14H36" stroke="#64748B" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M12 34H36" stroke="#64748B" strokeWidth="2.5" strokeLinecap="round" />
          {/* Center focus indicator */}
          <circle cx="24" cy="24" r="3.5" fill="#F59E0B" />
        </svg>
      </div>

      {showText && (
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-xs sm:text-sm text-foreground tracking-tight">
              PlantAssist<span className="text-amber-500">.AI</span>
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase font-semibold">
              SOP COPILOT
            </span>
          </div>
          <p className="text-[10px] text-muted-foreground truncate font-sans">
            Manufacturing Knowledge Copilot
          </p>
        </div>
      )}
    </div>
  );
};

