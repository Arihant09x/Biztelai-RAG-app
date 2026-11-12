import apiClient from "./apiClient";

export interface LLMStatus {
  configured_provider: string;
  api_base_url: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout_seconds: number;
  status: string;
  capabilities: Record<string, unknown>;
}

export interface AdminMetrics {
  total_documents: number;
  indexed_documents: number;
  total_pages: number;
  total_chunks: number;
  total_users: number;
  total_queries: number;
  average_latency_ms: number;
  positive_feedback_rate: number;
}

export const adminApi = {
  async getLLMStatus(): Promise<LLMStatus> {
    const res = await apiClient.get("/llm/status");
    return res.data.data;
  },

  async testLLMConnection(): Promise<{ success: boolean; response: string; latency_ms: number }> {
    const res = await apiClient.post("/llm/test-connection");
    return res.data;
  },

  async getAdminMetrics(): Promise<AdminMetrics> {
    const res = await apiClient.get("/admin/metrics");
    return res.data.data;
  },
};

