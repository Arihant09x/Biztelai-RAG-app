import React, { useEffect, useState } from "react";
import { useAuthStore } from "./stores/useAuthStore";
import { useChatStore } from "./stores/useChatStore";
import { LoginPage } from "./components/auth/LoginPage";
import { RegisterPage } from "./components/auth/RegisterPage";
import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { ChatContainer } from "./components/chat/ChatContainer";
import { ChatComposer } from "./components/chat/ChatComposer";
import { DocumentLibrary } from "./components/documents/DocumentLibrary";
import { Loader2 } from "lucide-react";

export const App: React.FC = () => {
  const { isAuthenticated, isLoading: isAuthLoading, initAuth } = useAuthStore();
  const { fetchConversations } = useChatStore();

  const [currentTab, setCurrentTab] = useState<"chat" | "documents">("chat");
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isRegisterMode, setIsRegisterMode] = useState(false);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchConversations();
    }
  }, [isAuthenticated, fetchConversations]);

  // Initial Authentication Splash Loader
  if (isAuthLoading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-background text-foreground select-none">
        <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/40 flex items-center justify-center text-amber-500 font-mono font-bold text-sm mb-3">
          PA
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
          <span>INITIALIZING PLANTASSIST COPILOT...</span>
        </div>
      </div>
    );
  }

  // Auth Screen (Login / Register)
  if (!isAuthenticated) {
    return isRegisterMode ? (
      <RegisterPage onToggleLogin={() => setIsRegisterMode(false)} />
    ) : (
      <LoginPage onToggleRegister={() => setIsRegisterMode(true)} />
    );
  }

  // Main Application Shell
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground antialiased font-sans">
      {/* Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={(tab) => setCurrentTab(tab)}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          currentTab={currentTab}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />

        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {currentTab === "chat" ? (
            <>
              <ChatContainer />
              <ChatComposer />
            </>
          ) : (
            <DocumentLibrary onSwitchToChat={() => setCurrentTab("chat")} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
