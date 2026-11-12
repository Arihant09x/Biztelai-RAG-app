import React, { useState } from "react";
import {
  Plus,
  MessageSquare,
  FileText,
  Trash2,
  Moon,
  Sun,
  LogOut,
  Search,
  ShieldCheck,
  UserCheck,
  X,
} from "lucide-react";
import { useChatStore } from "../../stores/useChatStore";
import { useAuthStore } from "../../stores/useAuthStore";
import { useThemeStore } from "../../stores/useThemeStore";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { Logo } from "../brand/Logo";

interface SidebarProps {
  currentTab: "chat" | "documents";
  onTabChange: (tab: "chat" | "documents") => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  isOpenMobile,
  onCloseMobile,
}) => {
  const [searchFilter, setSearchFilter] = useState("");
  const { conversations, activeConversationId, selectConversation, createNewChat, deleteConversation } =
    useChatStore();
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const handleSelectConv = (id: string) => {
    selectConversation(id);
    onTabChange("chat");
    onCloseMobile();
  };

  const handleNewChat = () => {
    createNewChat();
    onTabChange("chat");
    onCloseMobile();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-black/70 md:hidden backdrop-blur-sm"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-card border-r border-border transition-transform duration-200 md:static md:translate-x-0 select-none",
          isOpenMobile ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Precision Brand Header */}
        <div className="p-3 border-b border-border/80 flex items-center justify-between">
          <Logo size="sm" />

          <button
            onClick={onCloseMobile}
            className="p-1 rounded text-muted-foreground hover:text-foreground md:hidden"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action: New Inquiry */}
        <div className="p-3">
          <Button
            variant="amber"
            onClick={handleNewChat}
            className="w-full gap-2 h-8 text-xs font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Inquiry</span>
          </Button>
        </div>

        {/* Primary Navigation */}
        <div className="px-3 py-1 space-y-1">
          <button
            onClick={() => {
              onTabChange("chat");
              onCloseMobile();
            }}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors",
              currentTab === "chat"
                ? "bg-muted text-foreground font-semibold"
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            )}
          >
            <MessageSquare className="w-4 h-4 text-amber-500" />
            <span>Copilot Chat</span>
          </button>

          <button
            onClick={() => {
              onTabChange("documents");
              onCloseMobile();
            }}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors",
              currentTab === "documents"
                ? "bg-muted text-foreground font-semibold"
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            )}
          >
            <FileText className="w-4 h-4 text-amber-500" />
            <span>SOP Documents</span>
          </button>
        </div>

        {/* Conversation Search */}
        <div className="px-3 pt-3 pb-1">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Filter inquiries..."
              className="w-full pl-8 pr-2.5 py-1 rounded-md border border-border bg-background text-[11px] text-foreground focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5">
          <div className="px-1 py-1 text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Inquiry History
          </div>

          {filteredConversations.length === 0 ? (
            <p className="px-2 py-4 text-center text-[11px] text-muted-foreground italic font-sans">
              {searchFilter ? "No matches found" : "No active inquiries"}
            </p>
          ) : (
            filteredConversations.map((c) => {
              const isActive = activeConversationId === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => handleSelectConv(c.id)}
                  className={cn(
                    "group flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors border",
                    isActive
                      ? "bg-muted/80 text-foreground font-medium border-border/80"
                      : "text-muted-foreground hover:bg-muted/40 hover:text-foreground border-transparent"
                  )}
                >
                  <span className="truncate flex-1 pr-1 font-sans">{c.title || "Untitled Inquiry"}</span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversation(c.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-destructive transition-opacity"
                    title="Delete inquiry"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* User Card & Controls */}
        <div className="p-3 border-t border-border/80 bg-muted/20">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded bg-muted border border-border flex items-center justify-center font-mono font-bold text-xs uppercase shrink-0 text-foreground">
                {user?.full_name?.charAt(0) || "U"}
              </div>
              <div className="min-w-0">
                <span className="block font-medium text-xs text-foreground truncate">
                  {user?.full_name || user?.email || "Supervisor"}
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground capitalize font-mono">
                  {user?.role === "admin" ? (
                    <ShieldCheck className="w-3 h-3 text-amber-500" />
                  ) : (
                    <UserCheck className="w-3 h-3 text-emerald-500" />
                  )}
                  {user?.role || "Supervisor"}
                </span>
              </div>
            </div>

            <button
              onClick={toggleTheme}
              className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="w-full gap-2 h-7 text-[11px] font-mono text-muted-foreground hover:text-foreground"
          >
            <LogOut className="w-3 h-3" />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>
    </>
  );
};
