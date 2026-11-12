import React from "react";
import { cn } from "../../lib/utils";

export const Separator: React.FC<{
  orientation?: "horizontal" | "vertical";
  className?: string;
}> = ({ orientation = "horizontal", className }) => {
  return (
    <div
      role="none"
      className={cn(
        "shrink-0 bg-border",
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
        className
      )}
    />
  );
};

