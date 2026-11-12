import { create } from "zustand";
import { authApi } from "../services/authApi";
import { LoginRequest, RegisterRequest, User } from "../types/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  initAuth: () => Promise<void>;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem("plantassist_token"),
  isAuthenticated: !!localStorage.getItem("plantassist_token"),
  isLoading: true,
  error: null,

  initAuth: async () => {
    const token = localStorage.getItem("plantassist_token");
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true, isLoading: false, error: null });
    } catch {
      localStorage.removeItem("plantassist_token");
      localStorage.removeItem("plantassist_refresh_token");
      set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null });
    try {
      const { tokens, user } = await authApi.login(credentials);
      localStorage.setItem("plantassist_token", tokens.access_token);
      if (tokens.refresh_token) {
        localStorage.setItem("plantassist_refresh_token", tokens.refresh_token);
      }
      set({
        user,
        accessToken: tokens.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      let msg = "Invalid email or password.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { error?: { message?: string }; message?: string } } };
        msg = axErr.response?.data?.error?.message || axErr.response?.data?.message || msg;
      }
      set({ isLoading: false, error: msg });
      throw new Error(msg);
    }
  },

  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.register(data);
      // Auto-login after registration
      const { tokens, user } = await authApi.login({
        email: data.email,
        password: data.password,
      });
      localStorage.setItem("plantassist_token", tokens.access_token);
      if (tokens.refresh_token) {
        localStorage.setItem("plantassist_refresh_token", tokens.refresh_token);
      }
      set({
        user,
        accessToken: tokens.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      let msg = "Registration failed.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { error?: { message?: string }; message?: string } } };
        msg = axErr.response?.data?.error?.message || axErr.response?.data?.message || msg;
      }
      set({ isLoading: false, error: msg });
      throw new Error(msg);
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore
    } finally {
      localStorage.removeItem("plantassist_token");
      localStorage.removeItem("plantassist_refresh_token");
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  clearError: () => set({ error: null }),
}));

