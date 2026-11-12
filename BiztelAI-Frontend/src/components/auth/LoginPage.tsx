import React, { useState } from "react";
import { Lock, Mail, Loader2, ArrowRight, ShieldCheck, UserCheck, Wrench } from "lucide-react";
import { useAuthStore } from "../../stores/useAuthStore";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Logo } from "../brand/Logo";

interface LoginPageProps {
  onToggleRegister: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onToggleRegister }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    try {
      await login({ email, password });
    } catch {
      // Handled in store
    }
  };

  const handleDemoFill = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("Password123!");
    clearError();
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-background select-none">
      <div className="w-full max-w-sm space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center justify-center text-center space-y-2">
          <Logo size="lg" className="justify-center" />
        </div>

        {/* Card Form */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                Work Email Address
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="supervisor@biztelai.com"
                  required
                  disabled={isLoading}
                  className="pl-8"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  disabled={isLoading}
                  className="pl-8"
                />
              </div>
            </div>

            {error && (
              <div className="p-2.5 rounded bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="amber"
              disabled={isLoading || !email || !password}
              className="w-full gap-2 h-9 text-xs font-semibold shadow-sm mt-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>AUTHENTICATING...</span>
                </>
              ) : (
                <>
                  <span>SIGN IN TO COPILOT</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </Button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="pt-3 border-t border-border">
            <span className="block text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-2 text-center">
              1-Click Demo Profiles:
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoFill("supervisor@biztelai.com")}
                className="flex flex-col items-center p-2 rounded-lg border border-border bg-muted/20 hover:bg-muted/50 hover:border-amber-500/40 transition-colors text-center"
              >
                <UserCheck className="w-3.5 h-3.5 text-emerald-500 mb-1" />
                <span className="text-[10px] font-mono font-bold text-foreground">SUPERVISOR</span>
                <span className="text-[9px] text-muted-foreground">Full Scope</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill("admin@biztelai.com")}
                className="flex flex-col items-center p-2 rounded-lg border border-border bg-muted/20 hover:bg-muted/50 hover:border-amber-500/40 transition-colors text-center"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-amber-500 mb-1" />
                <span className="text-[10px] font-mono font-bold text-foreground">ADMIN</span>
                <span className="text-[9px] text-muted-foreground">System Mgmt</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill("operator@biztelai.com")}
                className="flex flex-col items-center p-2 rounded-lg border border-border bg-muted/20 hover:bg-muted/50 hover:border-amber-500/40 transition-colors text-center"
              >
                <Wrench className="w-3.5 h-3.5 text-blue-500 mb-1" />
                <span className="text-[10px] font-mono font-bold text-foreground">OPERATOR</span>
                <span className="text-[9px] text-muted-foreground">Shop Floor</span>
              </button>
            </div>
          </div>
        </div>

        {/* Toggle to Register */}
        <p className="text-center text-xs text-muted-foreground">
          New plant personnel?{" "}
          <button
            onClick={onToggleRegister}
            className="font-medium text-amber-500 hover:underline"
          >
            Register operator credentials
          </button>
        </p>
      </div>
    </div>
  );
};
