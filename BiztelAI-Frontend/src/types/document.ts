export type DocumentCategory =
  | "sop"
  | "safety"
  | "maintenance"
  | "quality"
  | "general";

export type IngestionStatus = "pending" | "processing" | "completed" | "indexed" | "failed";

export interface DocumentItem {
  id: string;
  title: string;
  category: DocumentCategory;
  version?: string;
  status: IngestionStatus;
  file_path?: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  page_number: number;
  chunk_index: number;
  content: string;
  section_title?: string;
  token_count?: number;
  has_tables?: boolean;
  has_images?: boolean;
}

export interface IngestionJobResponse {
  job_id: string;
  document_id: string;
  status: IngestionStatus;
  progress_percent: number;
  current_stage?: string;
  stage_name?: string;
  pages_processed?: number;
  chunks_created?: number;
  error_message?: string;
  created_at: string;
}

export interface UploadResponse {
  document: DocumentItem;
  job_id: string;
  message: string;
}

export interface DocumentPageContent {
  page_number: number;
  raw_text: string;
  text_content?: string;
  has_ocr: boolean;
  page_metadata?: Record<string, unknown>;
}

