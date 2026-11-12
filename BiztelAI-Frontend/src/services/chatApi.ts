import { apiClient, API_BASE_URL } from "./apiClient";
import { Conversation, FeedbackRequest, QueryRequest } from "../types/chat";
import { ContentBlock } from "../types/blocks";
import { SourceCitation } from "../types/chat";

export interface ChatResponseData {
  answer: string;
  blocks: ContentBlock[];
  sources: SourceCitation[];
  confidence: number;
  suggested_followups?: string[];
  query_type?: string;
  model_used?: string;
  latency_ms?: number;
  answerable?: boolean;
}

export interface ChatApiResponse {
  success: boolean;
  conversation_id: string;
  message_id: string;
  data: {
    answer: string;
    answerable: boolean;
    confidence: number;
    intent?: string;
    response: {
      blocks: ContentBlock[];
      suggested_followups?: string[];
    };
    sources: SourceCitation[];
  };
  latency_ms: number;
}

export const chatApi = {
  async sendQuery(req: QueryRequest): Promise<ChatApiResponse> {
    const res = await apiClient.post("/chat", {
      question: req.query,
      conversation_id: req.conversation_id,
      document_ids: req.document_ids,
      category: req.category,
    });
    return res.data;
  },

  async streamQuery(
    req: QueryRequest,
    callbacks: {
      onStatus?: (stage: string) => void;
      onToken?: (token: string) => void;
      onError?: (error: string) => void;
      onDone?: () => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem("plantassist_token");

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question: req.query,
        conversation_id: req.conversation_id,
        document_ids: req.document_ids,
        category: req.category,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Streaming failed with status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("Response body is not readable");

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;
          const matchEvent = block.match(/event:\s*([a-zA-Z0-9_-]+)/);
          const matchData = block.match(/data:\s*(.*)/s);

          const eventType = matchEvent ? matchEvent[1] : "message";
          const dataStr = matchData ? matchData[1].trim() : "";

          if (eventType === "status") {
            try {
              const data = JSON.parse(dataStr);
              callbacks.onStatus?.(data.stage || "");
            } catch {
              // Ignore parse error
            }
          } else if (eventType === "token") {
            try {
              const data = JSON.parse(dataStr);
              callbacks.onToken?.(data.token || "");
            } catch {
              callbacks.onToken?.(dataStr);
            }
          } else if (eventType === "error") {
            try {
              const data = JSON.parse(dataStr);
              callbacks.onError?.(data.error || "Unknown stream error");
            } catch {
              callbacks.onError?.(dataStr);
            }
          } else if (eventType === "done" || dataStr === "[DONE]") {
            callbacks.onDone?.();
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  async listConversations(skip = 0, limit = 30): Promise<Conversation[]> {
    const res = await apiClient.get("/conversations", {
      params: { skip, limit },
    });
    return res.data.data;
  },

  async getConversation(id: string) {
    const res = await apiClient.get(`/conversations/${id}`);
    return res.data.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await apiClient.delete(`/conversations/${id}`);
  },

  async submitFeedback(data: FeedbackRequest): Promise<void> {
    await apiClient.post("/feedback", {
      message_id: data.message_id,
      rating: data.feedback === "positive" ? 1 : -1,
      comment: data.comment,
    });
  },
};

