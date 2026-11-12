import React, { useState } from "react";
import {
  X,
  FileText,
  Download,
  Layers,
  Eye,
  ChevronLeft,
  ChevronRight,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { useDocumentStore } from "../../stores/useDocumentStore";
import { formatBytes } from "../../lib/utils";
import { PDFViewer } from "../pdf/PDFViewer";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { apiClient } from "../../services/apiClient";

export const SourceDrawer: React.FC = () => {
  const {
    previewDocument,
    previewPageNumber,
    previewPageContent,
    isPreviewLoading,
    loadPage,
    closePreview,
  } = useDocumentStore();

  const [activeTab, setActiveTab] = useState<"canvas" | "text">("canvas");
  const [currentPage, setCurrentPage] = useState(previewPageNumber || 1);
  const [textSearch, setTextSearch] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  if (!previewDocument) return null;

  const totalPages = previewDocument.page_count || 1;

  const handlePageChange = async (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    setCurrentPage(newPage);
    await loadPage(previewDocument.id, newPage);
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportError(null);
    setExportSuccess(false);

    try {
      const response = await apiClient.get<Blob>(`/documents/${previewDocument.id}/file`, {
        responseType: "blob",
      });

      // Extract authentic filename from header or fall back to document title
      let filename = `${previewDocument.title.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`;
      const disposition = response.headers["content-disposition"];
      if (disposition) {
        const match = disposition.match(/filename=["']?([^"';]+)["']?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(link);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (err: unknown) {
      let msg = "Export failed. Please check permissions.";
      if (err && typeof err === "object" && "message" in err) {
        msg = String((err as { message: string }).message);
      }
      setExportError(msg);
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  // Filter or highlight text content based on local search
  const renderHighlightedContent = () => {
    if (!previewPageContent) {
      return (
        <div className="flex flex-col items-center justify-center p-12 text-slate-400">
          <FileText className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-xs font-mono">No extracted text layer recorded for page {currentPage}.</p>
          <p className="text-[10px] text-slate-500 mt-1">This page may contain graphical diagrams or requires OCR processing.</p>
        </div>
      );
    }

    if (!textSearch.trim()) {
      return (
        <div className="font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap selection:bg-amber-500/20">
          {previewPageContent}
        </div>
      );
    }

    const regex = new RegExp(`(${textSearch.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")})`, "gi");
    const parts = previewPageContent.split(regex);

    return (
      <div className="font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap selection:bg-amber-500/20">
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark key={i} className="bg-amber-500/30 text-amber-200 rounded px-1 py-0.5 border border-amber-500/50">
              {part}
            </mark>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full md:w-[640px] lg:w-[720px] bg-slate-950 border-l border-border/80 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Precision Header */}
      <div className="px-4 py-3 border-b border-border/80 bg-slate-900/90 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500 shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-xs text-slate-100 truncate">
              {previewDocument.title}
            </h3>
            <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono mt-0.5">
              <span className="uppercase text-amber-400 font-bold">
                {previewDocument.category}
              </span>
              <span>•</span>
              <span>{formatBytes(previewDocument.file_size_bytes)}</span>
              <span>•</span>
              <span>{totalPages} PAGES</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExport}
            disabled={isExporting}
            className="text-slate-300 hover:text-white h-8 text-[11px] gap-1.5 border border-slate-800 hover:border-slate-700"
            title="Download authentic PDF using session Bearer token"
          >
            {isExporting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
            ) : exportSuccess ? (
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Download className="w-3.5 h-3.5 text-amber-500" />
            )}
            <span className="hidden sm:inline">
              {isExporting ? "Exporting..." : exportSuccess ? "Downloaded" : "Export PDF"}
            </span>
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={closePreview}
            className="text-slate-400 hover:text-white h-8 w-8"
            title="Close Drawer"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {exportError && (
        <div className="px-4 py-1.5 bg-destructive/10 border-b border-destructive/20 text-destructive text-[11px] font-mono flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{exportError}</span>
        </div>
      )}

      {/* Tabs Selector: PDF.js Canvas vs Extracted Text */}
      <div className="px-4 py-2 border-b border-border/60 bg-slate-900/60 flex items-center justify-between shrink-0">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "canvas" | "text")}>
          <TabsList className="bg-slate-950 border border-slate-800 h-8">
            <TabsTrigger value="canvas" className="text-[11px] gap-1.5 data-[state=active]:bg-slate-800">
              <Eye className="w-3.5 h-3.5 text-amber-500" />
              <span>PDF.js Live Canvas</span>
            </TabsTrigger>
            <TabsTrigger value="text" className="text-[11px] gap-1.5 data-[state=active]:bg-slate-800">
              <Layers className="w-3.5 h-3.5 text-amber-500" />
              <span>Extracted Text Layer</span>
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <span className="text-[10px] font-mono text-slate-500">
          DOC ID: {previewDocument.id.slice(0, 8)}
        </span>
      </div>

      {/* Main View Area */}
      <div className="flex-1 overflow-hidden p-3 bg-slate-950 flex flex-col">
        {activeTab === "canvas" ? (
          <PDFViewer
            documentId={previewDocument.id}
            initialPage={currentPage}
            className="flex-1"
          />
        ) : (
          <div className="flex-1 flex flex-col min-h-0 bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden">
            {/* Extracted Text Toolbar */}
            <div className="p-2.5 border-b border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-2">
              {/* Page Navigator */}
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 bg-slate-950 border-slate-800 text-slate-300 hover:text-white"
                  disabled={currentPage <= 1 || isPreviewLoading}
                  onClick={() => handlePageChange(currentPage - 1)}
                  title="Previous Page"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </Button>

                <span className="px-2 py-0.5 text-[11px] font-mono text-slate-300 bg-slate-950 border border-slate-800 rounded">
                  Page {currentPage} of {totalPages}
                </span>

                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 bg-slate-950 border-slate-800 text-slate-300 hover:text-white"
                  disabled={currentPage >= totalPages || isPreviewLoading}
                  onClick={() => handlePageChange(currentPage + 1)}
                  title="Next Page"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </div>

              {/* Text Search Field */}
              <div className="relative flex-1 max-w-xs min-w-[160px]">
                <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <Input
                  type="text"
                  placeholder="Find on page..."
                  value={textSearch}
                  onChange={(e) => setTextSearch(e.target.value)}
                  className="h-7 text-[11px] pl-7 pr-2 bg-slate-950 border-slate-800 text-slate-200 placeholder:text-slate-600"
                />
              </div>
            </div>

            {/* Extracted Text Content */}
            <div className="flex-1 overflow-y-auto p-4 selection:bg-amber-500/30">
              {isPreviewLoading ? (
                <div className="flex flex-col items-center justify-center p-12 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-amber-500 mb-2" />
                  <span className="text-xs font-mono">Retrieving page {currentPage} extraction layer...</span>
                </div>
              ) : (
                renderHighlightedContent()
              )}
            </div>
          </div>
        )}
      </div>

      {/* Ground Truth Verification Footer */}
      <div className="px-4 py-2 bg-slate-900 border-t border-border/80 text-[10px] text-slate-400 flex items-center justify-between font-mono shrink-0">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          VERIFIED PLANT GROUND TRUTH
        </span>
        <span>ACCESS: FACTORY-INTERNAL</span>
      </div>
    </div>
  );
};
