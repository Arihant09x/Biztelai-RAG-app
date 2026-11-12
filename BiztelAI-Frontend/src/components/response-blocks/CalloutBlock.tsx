import React from "react";
import { AlertOctagon, AlertTriangle, CheckCircle, Info, ShieldAlert } from "lucide-react";
import { cn } from "../../lib/utils";

interface CalloutBlockProps {
  level?: "info" | "warning" | "danger" | "success" | "note";
  variant?: string;
  title?: string;
  message?: string;
  content?: string;
}

export const CalloutBlock: React.FC<CalloutBlockProps> = ({
  level,
  variant,
  title,
  message,
  content,
}) => {
  const resolvedLevel = level || (variant as "info" | "warning" | "danger" | "success" | "note") || "info";
  const text = message || content || "";

  const config = {
    danger: {
      border: "border-red-500/40 bg-red-500/10 text-red-900 dark:text-red-200",
      icon: AlertOctagon,
      iconColor: "text-red-500",
      defaultTitle: "DANGER / CRITICAL SAFETY HAZARD",
    },
    warning: {
      border: "border-amber-500/40 bg-amber-500/10 text-amber-900 dark:text-amber-200",
      icon: AlertTriangle,
      iconColor: "text-amber-500",
      defaultTitle: "WARNING / CAUTION REQUIRED",
    },
    info: {
      border: "border-border/80 bg-muted/40 text-foreground",
      icon: Info,
      iconColor: "text-muted-foreground",
      defaultTitle: "OPERATIONAL NOTE",
    },
    success: {
      border: "border-emerald-500/40 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200",
      icon: CheckCircle,
      iconColor: "text-emerald-500",
      defaultTitle: "VERIFIED STANDARD",
    },
    note: {
      border: "border-border/80 bg-muted/40 text-foreground",
      icon: ShieldAlert,
      iconColor: "text-amber-500",
      defaultTitle: "SPECIFICATION NOTICE",
    },
  }[resolvedLevel] || {
    border: "border-border/80 bg-muted/40 text-foreground",
    icon: Info,
    iconColor: "text-muted-foreground",
    defaultTitle: "NOTE",
  };

  const Icon = config.icon;

  return (
    <div
      className={cn(
        "my-3 flex items-start gap-3 rounded-lg border p-3.5 shadow-sm font-sans",
        config.border
      )}
    >
      <div className="shrink-0 mt-0.5">
        <Icon className={cn("w-4 h-4", config.iconColor)} />
      </div>

      <div className="flex-1 min-w-0">
        <h5 className="font-mono font-bold text-[11px] uppercase tracking-wider mb-1">
          {title || config.defaultTitle}
        </h5>
        <div className="text-xs leading-relaxed font-normal opacity-95 whitespace-pre-wrap">
          {text}
        </div>
      </div>
    </div>
  );
};
