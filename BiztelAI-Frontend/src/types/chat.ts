import { ContentBlock } from "./blocks";

export interface SourceCitation {
  id?: string;
  chunk_id?: string;
  document_id: string;
  document_title: string;
  page_number: number;
  snippet: string;
  similarity?: number;
  relevance_score?: number;
  section_title?: string;
}

export interface CopilotAnswerResponse {
  query: string;
  answer: string;
  blocks: ContentBlock[];
  sources: SourceCitation[];
  confidence: number;
  suggested_followups?: string[];
  query_type?: string;
  model_used?: string;
  latency_ms?: number;
}

export interface ChatMessage {
  id: string;
  conversation_id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  blocks?: ContentBlock[];
  sources?: SourceCitation[];
  confidence?: number;
  suggested_followups?: string[];
  feedback?: "positive" | "negative" | null;
  created_at: string;
  latency_ms?: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string;
  message_count?: number;
  last_message?: string;
}

export interface QueryRequest {
  query: string;
  conversation_id?: string;
  document_ids?: string[];
  category?: string;
  stream?: boolean;
}

export interface FeedbackRequest {
  message_id: string;
  feedback: "positive" | "negative";
  comment?: string;
}

