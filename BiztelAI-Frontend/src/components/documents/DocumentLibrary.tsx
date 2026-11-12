import React, { useEffect, useState } from "react";
import {
  FileText,
  Plus,
  Search,
  Trash2,
  ExternalLink,
  MessageSquare,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { useDocumentStore } from "../../stores/useDocumentStore";
import { useChatStore } from "../../stores/useChatStore";
import { useAuthStore } from "../../stores/useAuthStore";
import { DocumentCategory, DocumentItem } from "../../types/document";
import { DocumentUploader } from "./DocumentUploader";
import { formatBytes, formatDate } from "../../lib/utils";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "../ui/card";
import { Input } from "../ui/input";
import { SourceDrawer } from "../chat/SourceDrawer";

interface DocumentLibraryProps {
  onSwitchToChat: () => void;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({ onSwitchToChat }) => {
  const [isUploaderOpen, setIsUploaderOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const {
    documents,
    isLoading,
    activeJob,
    selectedCategory,
    searchQuery,
    fetchDocuments,
    setSelectedCategory,
    setSearchQuery,
    deleteDocument,
    openPreview,
  } = useDocumentStore();

  const { setSelectedDocumentId, createNewChat } = useChatStore();
  const { user } = useAuthStore();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const canUpload = user?.role === "admin" || user?.role === "supervisor" || user?.is_supervisor || user?.is_admin;

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "all" || doc.category.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  const handleAskAboutDoc = (doc: DocumentItem) => {
    setSelectedDocumentId(doc.id);
    createNewChat();
    onSwitchToChat();
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      setDeleteConfirmId(null);
    } catch {
      // Handled
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-y-auto p-4 sm:p-8 select-none">
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <FileText className="w-5 h-5 text-amber-500" />
              SOP Document Repository
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5 font-sans">
              Verified operating manuals, equipment maintenance procedures, and quality inspection guidelines
            </p>
          </div>

          <Button
            variant="amber"
            onClick={() => setIsUploaderOpen(true)}
            disabled={!canUpload}
            className="gap-2 h-9 text-xs font-semibold self-start sm:self-auto shadow-sm"
            title={!canUpload ? "Supervisor or Admin role required to upload" : "Upload SOP Document"}
          >
            <Plus className="w-4 h-4" />
            <span>Upload New SOP</span>
          </Button>
        </div>

        {/* Active Ingestion Job Banner */}
        {activeJob && (
          <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 flex items-center justify-between text-xs animate-in slide-in-from-top duration-200">
            <div className="flex items-center gap-2.5">
              <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
              <div>
                <span className="font-semibold text-foreground font-mono">
                  INGESTION PIPELINE ACTIVE:
                </span>{" "}
                <span className="text-muted-foreground">
                  Chunking and vectorizing PDF pages into pgvector ({activeJob.progress_percent || 0}%)
                </span>
              </div>
            </div>
            <span className="font-mono text-amber-500 font-bold">
              {activeJob.progress_percent || 0}%
            </span>
          </div>
        )}

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search SOP by title, equipment code, or category..."
              className="pl-9 h-9"
            />
          </div>

          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
            {(["all", "sop", "safety", "maintenance", "quality"] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat as DocumentCategory | "all")}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium uppercase whitespace-nowrap transition-colors border ${
                  selectedCategory === cat
                    ? "bg-foreground text-background border-foreground font-semibold"
                    : "bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                }`}
              >
                {cat === "all" ? "All Documents" : cat}
              </button>
            ))}
          </div>
        </div>

        {/* Documents Cards */}
        {isLoading && documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
            <Loader2 className="w-6 h-6 animate-spin text-amber-500 mb-2" />
            <span className="text-xs font-mono">Loading SOP collection...</span>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center p-12 border border-dashed rounded-xl bg-card">
            <FileText className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-40" />
            <h4 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
              NO SOP DOCUMENTS FOUND
            </h4>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto font-sans">
              {searchQuery
                ? `No manual matches "${searchQuery}". Verify search terms.`
                : "No documents have been indexed in this category yet."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDocuments.map((doc) => {
              const isIndexed = doc.status === "indexed" || doc.status === "completed";
              const isProcessing = doc.status === "processing" || doc.status === "pending";

              return (
                <Card
                  key={doc.id}
                  className="flex flex-col justify-between hover:border-amber-500/50 transition-colors group"
                >
                  <CardHeader className="p-4 pb-2">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className="text-amber-500 border-amber-500/30 bg-amber-500/5">
                        {doc.category.toUpperCase()}
                      </Badge>

                      {isIndexed ? (
                        <Badge variant="emerald" className="gap-1">
                          <CheckCircle2 className="w-3 h-3" /> INDEXED
                        </Badge>
                      ) : isProcessing ? (
                        <Badge variant="amber" className="gap-1">
                          <Clock className="w-3 h-3 animate-spin" /> INGESTING
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="gap-1">
                          <AlertTriangle className="w-3 h-3" /> FAILED
                        </Badge>
                      )}
                    </div>

                    <CardTitle className="text-xs font-semibold text-foreground line-clamp-2 leading-relaxed group-hover:text-amber-500 transition-colors">
                      {doc.title}
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="p-4 pt-1 pb-3">
                    <div className="grid grid-cols-3 gap-2 text-center py-2 px-3 rounded-lg bg-muted/40 text-[11px] font-mono border border-border/40">
                      <div>
                        <span className="block text-muted-foreground text-[10px]">PAGES</span>
                        <span className="font-bold text-foreground">
                          {doc.page_count || 1}
                        </span>
                      </div>
                      <div>
                        <span className="block text-muted-foreground text-[10px]">CHUNKS</span>
                        <span className="font-bold text-foreground">
                          {doc.chunk_count || 0}
                        </span>
                      </div>
                      <div>
                        <span className="block text-muted-foreground text-[10px]">SIZE</span>
                        <span className="font-bold text-foreground">
                          {formatBytes(doc.file_size_bytes)}
                        </span>
                      </div>
                    </div>
                  </CardContent>

                  <CardFooter className="p-4 pt-2 border-t border-border/60 flex items-center justify-between text-xs">
                    <span className="text-[10px] font-mono text-muted-foreground">
                      {formatDate(doc.created_at)}
                    </span>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openPreview(doc, 1)}
                        className="h-7 w-7 text-muted-foreground hover:text-foreground"
                        title="Open PDF.js Live Canvas"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleAskAboutDoc(doc)}
                        className="h-7 w-7 text-amber-500 hover:text-amber-400 hover:bg-amber-500/10"
                        title="Query Copilot on this SOP"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                      </Button>

                      {canUpload && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteConfirmId(doc.id)}
                          className="h-7 w-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          title="Delete SOP"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteConfirmId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
            <div className="bg-card border border-border p-5 rounded-xl max-w-sm w-full shadow-2xl">
              <h4 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono mb-1">
                DELETE SOP DOCUMENT
              </h4>
              <p className="text-xs text-muted-foreground mb-4 font-sans">
                This permanently deletes the document and all associated embeddings from the pgvector database.
              </p>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setDeleteConfirmId(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(deleteConfirmId)}
                >
                  Confirm Delete
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Document Uploader Modal */}
        <DocumentUploader
          isOpen={isUploaderOpen}
          onClose={() => setIsUploaderOpen(false)}
        />

        {/* Slide-over PDF and Extracted Text Inspector for SOP Library */}
        <SourceDrawer />
      </div>
    </div>
  );
};
