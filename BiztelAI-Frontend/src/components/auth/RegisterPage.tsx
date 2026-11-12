import React, { useState } from "react";
import { Lock, Mail, User, Building, Loader2, ArrowRight } from "lucide-react";
import { useAuthStore } from "../../stores/useAuthStore";
import { UserRole } from "../../types/auth";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Logo } from "../brand/Logo";

interface RegisterPageProps {
  onToggleLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onToggleLogin }) => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState("");
  const [role, setRole] = useState<UserRole>("operator");

  const { register, isLoading, error } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !fullName) return;

    try {
      await register({
        full_name: fullName,
        email,
        password,
        department: department || undefined,
        role,
      });
    } catch {
      // Handled in store
    }
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
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. John Doe"
                  required
                  disabled={isLoading}
                  className="pl-8"
                />
              </div>
            </div>

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
                  placeholder="operator@company.com"
                  required
                  disabled={isLoading}
                  className="pl-8"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                Password (min 8 chars)
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  minLength={8}
                  disabled={isLoading}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                  Department
                </label>
                <div className="relative">
                  <Building className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="Assembly A"
                    disabled={isLoading}
                    className="pl-8"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                  Factory Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  disabled={isLoading}
                  className="w-full h-9 rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-amber-500 font-mono"
                >
                  <option value="operator">Operator</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="admin">Admin</option>
                </select>
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
              disabled={isLoading || !email || !password || !fullName}
              className="w-full gap-2 h-9 text-xs font-semibold shadow-sm mt-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>REGISTERING...</span>
                </>
              ) : (
                <>
                  <span>CREATE CREDENTIALS</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </Button>
          </form>
        </div>

        {/* Toggle to Login */}
        <p className="text-center text-xs text-muted-foreground">
          Already registered?{" "}
          <button
            onClick={onToggleLogin}
            className="font-medium text-amber-500 hover:underline"
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};
