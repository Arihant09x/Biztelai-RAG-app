import apiClient from "./apiClient";
import { AuthTokens, LoginRequest, RegisterRequest, User } from "../types/auth";

export const authApi = {
  async login(credentials: LoginRequest): Promise<{ tokens: AuthTokens; user: User }> {
    const res = await apiClient.post("/auth/login", credentials);
    const tokens: AuthTokens = res.data.data;

    // Immediately fetch the user profile with the token
    const userRes = await apiClient.get("/auth/me", {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });

    const user: User = userRes.data.data;
    return { tokens, user };
  },

  async register(data: RegisterRequest): Promise<User> {
    const res = await apiClient.post("/auth/register", data);
    return res.data.data;
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get("/auth/me");
    return res.data.data;
  },

  async refresh(refreshToken: string): Promise<AuthTokens> {
    const res = await apiClient.post("/auth/refresh", { refresh_token: refreshToken });
    return res.data.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Ignore network errors on logout
    }
  },
};

