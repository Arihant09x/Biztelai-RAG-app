import React, { useEffect, useState } from "react";
import { Menu, Database } from "lucide-react";
import { useChatStore } from "../../stores/useChatStore";
import { adminApi, LLMStatus } from "../../services/adminApi";
import { Badge } from "../ui/badge";
import { Logo } from "../brand/Logo";

interface HeaderProps {
  onOpenMobileSidebar: () => void;
  currentTab: "chat" | "documents";
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileSidebar, currentTab }) => {
  const { conversations, activeConversationId } = useChatStore();
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);

  const activeConv = conversations.find((c) => c.id === activeConversationId);

  useEffect(() => {
    adminApi
      .getLLMStatus()
      .then((status) => setLlmStatus(status))
      .catch(() => {
        // Fallback default
      });
  }, []);

  return (
    <header className="h-12 border-b border-border/80 bg-card px-4 flex items-center justify-between shrink-0 select-none">
      {/* Left: Mobile trigger & view title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileSidebar}
          className="p-1 rounded text-muted-foreground hover:text-foreground md:hidden"
          aria-label="Toggle navigation"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2.5 min-w-0">
          <Logo size="sm" showText={false} className="hidden sm:flex" />
          <span className="font-semibold text-xs sm:text-sm text-foreground truncate">
            {currentTab === "documents"
              ? "Manufacturing SOP Library"
              : activeConv?.title || "PlantAssist Copilot Workspace"}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Model Readouts */}
      <div className="flex items-center gap-2">
        <Badge variant="emerald" className="hidden md:inline-flex items-center gap-1.5 py-0.5">
          <Database className="w-3 h-3 text-emerald-500" />
          <span>PGVECTOR GROUNDED</span>
        </Badge>

        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-muted border border-border text-[10px] font-mono text-muted-foreground">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          <span className="truncate max-w-[120px] sm:max-w-none uppercase font-semibold text-foreground">
            {llmStatus?.model_name || "GROQ / GPT-OSS-120B"}
          </span>
        </div>
      </div>
    </header>
  );
};
