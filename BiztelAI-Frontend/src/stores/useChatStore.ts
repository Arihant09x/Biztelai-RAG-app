import { create } from "zustand";
import { chatApi } from "../services/chatApi";
import { ChatMessage, Conversation, SourceCitation } from "../types/chat";
import { ContentBlock } from "../types/blocks";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingStage: string;
  streamingContent: string;
  error: string | null;
  abortController: AbortController | null;

  // Active filters for RAG
  selectedCategory: string | null;
  selectedDocumentId: string | null;

  // Actions
  fetchConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  createNewChat: () => void;
  sendMessage: (query: string) => Promise<void>;
  stopGeneration: () => void;
  submitFeedback: (messageId: string, feedback: "positive" | "negative", comment?: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  setSelectedCategory: (cat: string | null) => void;
  setSelectedDocumentId: (docId: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingStage: "",
  streamingContent: "",
  error: null,
  abortController: null,

  selectedCategory: null,
  selectedDocumentId: null,

  fetchConversations: async () => {
    try {
      const convs = await chatApi.listConversations();
      set({ conversations: convs });
    } catch {
      // Ignore initial list error
    }
  },

  selectConversation: async (id: string) => {
    set({
      activeConversationId: id,
      isLoading: true,
      error: null,
      messages: [],
    });

    try {
      const convData = await chatApi.getConversation(id);
      const loadedMessages: ChatMessage[] = (convData.messages || []).map(
        (m: {
          id: string;
          sender_type: string;
          content: string;
          structured_response?: {
            answer?: string;
            confidence?: number;
            response?: { blocks?: ContentBlock[]; suggested_followups?: string[] };
            sources?: SourceCitation[];
          };
          sources?: SourceCitation[];
          latency_ms?: number;
          created_at: string;
        }) => {
        const struct = m.structured_response as Record<string, unknown> | undefined;
        const structResponse = struct?.response as Record<string, unknown> | undefined;
        const blocks = (structResponse?.blocks || struct?.blocks || []) as ContentBlock[];
        const sources = ((m.sources && m.sources.length > 0) ? m.sources : (struct?.sources || [])) as SourceCitation[];
        const followups = (structResponse?.suggested_followups || struct?.suggested_followups || []) as string[];

        let text = m.content || "";
        if (!text || text === "Structured SOP Response") {
          text = typeof struct?.answer === "string" ? struct.answer : "";
          if (!text && blocks.length > 0) {
            text = blocks
              .map((b) => {
                const raw = b as unknown as Record<string, unknown>;
                return String(raw.content || raw.message || raw.title || "");
              })
              .filter(Boolean)
              .join("\n\n");
          }
        }

        return {
          id: m.id,
          conversation_id: id,
          role: m.sender_type === "assistant" ? "assistant" : "user",
          content: text || "Verified Standard Operating Procedure documentation retrieved.",
          blocks: blocks.length > 0 ? blocks : undefined,
          sources: sources.length > 0 ? sources : undefined,
          confidence: typeof struct?.confidence === "number" ? struct.confidence : undefined,
          suggested_followups: followups.length > 0 ? followups : undefined,
          created_at: m.created_at,
          latency_ms: m.latency_ms,
        };
        }
      );

      set({ messages: loadedMessages, isLoading: false });
    } catch (err: unknown) {
      let msg = "Failed to load conversation.";
      if (err && typeof err === "object" && "message" in err) {
        msg = String((err as { message: string }).message);
      }
      set({ error: msg, isLoading: false });
    }
  },

  createNewChat: () => {
    if (get().abortController) {
      get().abortController?.abort();
    }
    set({
      activeConversationId: null,
      messages: [],
      error: null,
      isLoading: false,
      isStreaming: false,
      streamingContent: "",
      streamingStage: "",
    });
  },

  sendMessage: async (queryText: string) => {
    const trimmed = queryText.trim();
    if (!trimmed || get().isLoading) return;

    const controller = new AbortController();
    set({ isLoading: true, error: null, abortController: controller });

    const userMessageId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMessageId,
      conversation_id: get().activeConversationId || undefined,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
    }));

    try {
      const activeId = get().activeConversationId;
      const res = await chatApi.sendQuery({
        query: trimmed,
        conversation_id: activeId || undefined,
        document_ids: get().selectedDocumentId ? [get().selectedDocumentId!] : undefined,
        category: get().selectedCategory || undefined,
      });

      const resData = res.data as Record<string, any>;
      const responseBlocks = (resData?.response?.blocks || resData?.blocks || []) as ContentBlock[];
      const sources = (resData?.sources || []) as SourceCitation[];
      const followups = (resData?.response?.suggested_followups || resData?.suggested_followups || []) as string[];
      let answerText = resData?.answer || "";

      if (!answerText || answerText === "Structured SOP Response") {
        if (responseBlocks.length > 0) {
          answerText = responseBlocks
            .map((b) => {
              const raw = b as unknown as Record<string, unknown>;
              return String(raw.content || raw.message || raw.title || "");
            })
            .filter(Boolean)
            .join("\n\n");
        }
      }

      const assistantMsg: ChatMessage = {
        id: res.message_id || `asst-${Date.now()}`,
        conversation_id: res.conversation_id,
        role: "assistant",
        content: answerText || "Verified Standard Operating Procedure documentation retrieved.",
        blocks: responseBlocks.length > 0 ? responseBlocks : undefined,
        sources: sources.length > 0 ? sources : undefined,
        confidence: res.data?.confidence,
        suggested_followups: followups.length > 0 ? followups : undefined,
        created_at: new Date().toISOString(),
        latency_ms: res.latency_ms,
      };

      set((state) => ({
        messages: [...state.messages, assistantMsg],
        activeConversationId: res.conversation_id,
        isLoading: false,
        abortController: null,
      }));

      // Refresh conversations list in background
      get().fetchConversations();
    } catch (err: unknown) {
      if (controller.signal.aborted) {
        set({ isLoading: false, abortController: null });
        return;
      }

      let msg = "Failed to get response from PlantAssist Copilot.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { error?: { message?: string }; message?: string } } };
        msg = axErr.response?.data?.error?.message || axErr.response?.data?.message || msg;
      }
      set({ error: msg, isLoading: false, abortController: null });
    }
  },

  stopGeneration: () => {
    if (get().abortController) {
      get().abortController?.abort();
      set({ isLoading: false, isStreaming: false, abortController: null });
    }
  },

  submitFeedback: async (messageId: string, feedback: "positive" | "negative", comment?: string) => {
    try {
      await chatApi.submitFeedback({
        message_id: messageId,
        feedback,
        comment,
      });

      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === messageId ? { ...m, feedback } : m
        ),
      }));
    } catch {
      // Ignore feedback submit errors
    }
  },

  deleteConversation: async (id: string) => {
    try {
      await chatApi.deleteConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        ...(state.activeConversationId === id
          ? { activeConversationId: null, messages: [] }
          : {}),
      }));
    } catch {
      // Ignore
    }
  },

  setSelectedCategory: (cat) => set({ selectedCategory: cat }),
  setSelectedDocumentId: (docId) => set({ selectedDocumentId: docId }),
}));

