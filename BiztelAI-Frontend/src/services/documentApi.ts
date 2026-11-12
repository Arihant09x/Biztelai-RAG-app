import apiClient from "./apiClient";
import { DocumentItem, IngestionJobResponse } from "../types/document";

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentPageContent {
  id: string;
  document_id: string;
  page_number: number;
  text_content: string;
  raw_text?: string;
  tables_json?: unknown[];
  has_images?: boolean;
}

export const documentApi = {
  async uploadDocument(
    file: File,
    metadata: {
      title?: string;
      category?: string;
      department?: string;
    },
    onUploadProgress?: (progressEvent: { loaded: number; total?: number }) => void
  ): Promise<{ document: DocumentItem; job_id: string; status: string }> {
    const formData = new FormData();
    formData.append("file", file);
    if (metadata.title) formData.append("title", metadata.title);
    if (metadata.category) formData.append("category", metadata.category);
    if (metadata.department) formData.append("department", metadata.department);

    const res = await apiClient.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress) {
          onUploadProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
          });
        }
      },
    });

    return res.data.data;
  },

  async listDocuments(params?: {
    category?: string;
    department?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<DocumentListResponse> {
    const res = await apiClient.get("/documents", { params });
    return res.data.data;
  },

  async getDocument(id: string): Promise<DocumentItem & { total_pages?: number; total_chunks?: number }> {
    const res = await apiClient.get(`/documents/${id}`);
    return res.data.data;
  },

  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  },

  async reprocessDocument(id: string): Promise<{ job_id: string; status: string }> {
    const res = await apiClient.post(`/documents/${id}/reprocess`);
    return res.data.data;
  },

  async getJobStatus(jobOrDocId: string): Promise<IngestionJobResponse> {
    const res = await apiClient.get(`/ingestion/jobs/${jobOrDocId}`);
    return res.data.data;
  },

  async getDocumentPage(docId: string, pageNumber: number): Promise<DocumentPageContent> {
    const res = await apiClient.get(`/documents/${docId}/pages/${pageNumber}`);
    return res.data.data;
  },
};

