import { create } from "zustand";
import { documentApi } from "../services/documentApi";
import { DocumentCategory, DocumentItem, IngestionJobResponse } from "../types/document";

interface DocumentState {
  documents: DocumentItem[];
  total: number;
  isLoading: boolean;
  error: string | null;
  selectedCategory: DocumentCategory | "all";
  searchQuery: string;

  // Ingestion tracking
  activeJob: IngestionJobResponse | null;
  isUploading: boolean;
  uploadProgress: number;

  // Slide-over preview
  previewDocument: DocumentItem | null;
  previewPageNumber: number;
  previewPageContent: string | null;
  isPreviewLoading: boolean;

  // Actions
  fetchDocuments: (category?: DocumentCategory | "all") => Promise<void>;
  setSelectedCategory: (cat: DocumentCategory | "all") => void;
  setSearchQuery: (query: string) => void;
  uploadDocument: (file: File, metadata: { title?: string; category?: string; department?: string }) => Promise<void>;
  pollJobStatus: (jobId: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  openPreview: (docOrId: DocumentItem | string, pageNumber?: number) => Promise<void>;
  loadPage: (docId: string, pageNumber: number) => Promise<void>;
  closePreview: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  total: 0,
  isLoading: false,
  error: null,
  selectedCategory: "all",
  searchQuery: "",

  activeJob: null,
  isUploading: false,
  uploadProgress: 0,

  previewDocument: null,
  previewPageNumber: 1,
  previewPageContent: null,
  isPreviewLoading: false,

  fetchDocuments: async (category) => {
    set({ isLoading: true, error: null });
    try {
      const activeCat = category !== undefined ? category : get().selectedCategory;
      const res = await documentApi.listDocuments({
        category: activeCat === "all" ? undefined : activeCat,
        limit: 100,
      });
      set({ documents: res.items, total: res.total, isLoading: false });
    } catch (err: unknown) {
      let msg = "Failed to fetch documents.";
      if (err && typeof err === "object" && "message" in err) {
        msg = String((err as { message: string }).message);
      }
      set({ error: msg, isLoading: false });
    }
  },

  setSelectedCategory: (cat) => {
    set({ selectedCategory: cat });
    get().fetchDocuments(cat);
  },

  setSearchQuery: (query) => {
    set({ searchQuery: query });
  },

  uploadDocument: async (file, metadata) => {
    set({ isUploading: true, uploadProgress: 0, error: null });
    try {
      const res = await documentApi.uploadDocument(file, metadata, (p) => {
        if (p.total) {
          set({ uploadProgress: Math.round((p.loaded / p.total) * 100) });
        }
      });

      set({ isUploading: false, uploadProgress: 100 });
      // Refresh documents list
      await get().fetchDocuments();

      if (res.job_id) {
        get().pollJobStatus(res.job_id);
      }
    } catch (err: unknown) {
      let msg = "Failed to upload document.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { error?: { message?: string }; message?: string } } };
        msg = axErr.response?.data?.error?.message || axErr.response?.data?.message || msg;
      }
      set({ isUploading: false, error: msg });
      throw new Error(msg);
    }
  },

  pollJobStatus: async (jobId: string) => {
    let attempts = 0;
    let consecutiveErrors = 0;
    const maxAttempts = 120; // 120 * 2s = 240s resilient timeout
    const interval = setInterval(async () => {
      attempts++;
      try {
        const job = await documentApi.getJobStatus(jobId);
        consecutiveErrors = 0;
        set({ activeJob: job });

        if (job.status === "completed" || job.status === "failed" || attempts >= maxAttempts) {
          clearInterval(interval);
          get().fetchDocuments();
          if (job.status === "completed") {
            setTimeout(() => set({ activeJob: null }), 5000);
          }
        }
      } catch {
        consecutiveErrors++;
        if (consecutiveErrors >= 6) {
          clearInterval(interval);
          get().fetchDocuments();
        }
      }
    }, 2000);
  },

  deleteDocument: async (id: string) => {
    try {
      await documentApi.deleteDocument(id);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== id),
        total: state.total - 1,
      }));
    } catch (err: unknown) {
      let msg = "Failed to delete document.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { message?: string } } };
        msg = axErr.response?.data?.message || msg;
      }
      throw new Error(msg);
    }
  },

  openPreview: async (docOrId: DocumentItem | string, pageNumber = 1) => {
    let doc: DocumentItem | null = null;
    if (typeof docOrId === "string") {
      doc = get().documents.find((d) => d.id === docOrId) || null;
      if (!doc) {
        try {
          doc = await documentApi.getDocument(docOrId);
        } catch {
          doc = {
            id: docOrId,
            title: "SOP Reference Document",
            category: "sop",
            status: "indexed",
            file_size_bytes: 0,
            page_count: pageNumber || 1,
            chunk_count: 0,
            created_at: new Date().toISOString(),
          };
        }
      }
    } else {
      doc = docOrId;
    }

    set({
      previewDocument: doc,
      previewPageNumber: pageNumber,
      previewPageContent: null,
      isPreviewLoading: true,
    });
    await get().loadPage(doc.id, pageNumber);
  },

  loadPage: async (docId: string, pageNumber: number) => {
    set({ isPreviewLoading: true, previewPageNumber: pageNumber });
    try {
      const pageData = await documentApi.getDocumentPage(docId, pageNumber);
      const text = pageData.text_content || pageData.raw_text || "";
      set({ previewPageContent: text, isPreviewLoading: false });
    } catch {
      set({
        previewPageContent: "Page content preview unavailable for this document.",
        isPreviewLoading: false,
      });
    }
  },

  closePreview: () => {
    set({
      previewDocument: null,
      previewPageNumber: 1,
      previewPageContent: null,
    });
  },
}));

