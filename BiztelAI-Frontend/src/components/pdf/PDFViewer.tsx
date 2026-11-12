import React, { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCcw, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { apiClient, API_BASE_URL } from "../../services/apiClient";

// Configure PDF.js worker
if (typeof window !== "undefined") {
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;
  } catch {
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
  }
}

interface PDFViewerProps {
  documentId: string;
  initialPage?: number;
  onPageChange?: (page: number) => void;
  className?: string;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  documentId,
  initialPage = 1,
  onPageChange,
  className = "",
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderTaskRef = useRef<{ cancel: () => void } | null>(null);
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(initialPage);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [scale, setScale] = useState<number>(1.2);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);


  // Load PDF Document via authenticated binary stream
  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setError(null);

    // Prefer fetching via authenticated apiClient for bulletproof header/CORS support
    apiClient
      .get<ArrayBuffer>(`/documents/${documentId}/file`, {
        responseType: "arraybuffer",
      })
      .then((res) => {
        if (isCancelled) return null;
        const loadingTask = pdfjsLib.getDocument({
          data: res.data,
          cMapPacked: true,
        });
        return loadingTask.promise;
      })
      .then((doc) => {
        if (isCancelled || !doc) return;
        setPdfDoc(doc);
        setTotalPages(doc.numPages);
        setCurrentPage(Math.min(initialPage, doc.numPages));
        setIsLoading(false);
      })
      .catch((primaryErr: unknown) => {
        if (isCancelled) return;
        // Fallback: URL with query token
        const token = localStorage.getItem("plantassist_token");
        const fileUrl = token
          ? `${API_BASE_URL}/documents/${documentId}/file?token=${encodeURIComponent(token)}`
          : `${API_BASE_URL}/documents/${documentId}/file`;

        const fallbackTask = pdfjsLib.getDocument({
          url: fileUrl,
          httpHeaders: token ? { Authorization: `Bearer ${token}` } : {},
        });

        fallbackTask.promise
          .then((doc) => {
            if (isCancelled) return;
            setPdfDoc(doc);
            setTotalPages(doc.numPages);
            setCurrentPage(Math.min(initialPage, doc.numPages));
            setIsLoading(false);
          })
          .catch((fallbackErr: unknown) => {
            if (isCancelled) return;
            let msg = "Could not load document preview via PDF.js";
            const errObj = fallbackErr || primaryErr;
            if (errObj && typeof errObj === "object" && "message" in errObj) {
              msg = String((errObj as { message: string }).message);
            }
            setError(msg);
            setIsLoading(false);
          });
      });

    return () => {
      isCancelled = true;
    };
  }, [documentId, API_BASE_URL, initialPage]);

  // Render Current Page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let isRenderCancelled = false;

    pdfDoc.getPage(currentPage).then((page) => {
      if (isRenderCancelled) return;

      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current;
      if (!canvas) return;

      const context = canvas.getContext("2d");
      if (!context) return;

      if (renderTaskRef.current) {
        try {
          renderTaskRef.current.cancel();
        } catch {
          // Ignore cancel error
        }
      }

      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
        canvas: canvas,
      };

      const renderTask = page.render(renderContext);
      renderTaskRef.current = renderTask;

      renderTask.promise.catch((err) => {
        if (err && typeof err === "object" && "name" in err && (err as { name: string }).name === "RenderingCancelledException") {
          return;
        }
        console.error("PDF render warning:", err);
      });
    });

    return () => {
      isRenderCancelled = true;
      if (renderTaskRef.current) {
        try {
          renderTaskRef.current.cancel();
        } catch {
          // Ignore
        }
      }
    };
  }, [pdfDoc, currentPage, scale]);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const next = currentPage - 1;
      setCurrentPage(next);
      onPageChange?.(next);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      const next = currentPage + 1;
      setCurrentPage(next);
      onPageChange?.(next);
    }
  };

  const handleZoomIn = () => setScale((s) => Math.min(s + 0.2, 2.5));
  const handleZoomOut = () => setScale((s) => Math.max(s - 0.2, 0.6));
  const handleResetZoom = () => setScale(1.2);

  return (
    <div className={`flex flex-col h-full bg-slate-900 border border-border/80 rounded-xl overflow-hidden shadow-inner ${className}`}>
      {/* Controls Bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-950 border-b border-border/60 text-xs text-slate-300 font-mono select-none">
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePrevPage}
            disabled={currentPage <= 1 || isLoading}
            className="h-7 w-7 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </Button>

          <span className="text-[11px] px-1 font-semibold text-slate-200">
            PAGE {currentPage} OF {totalPages || 1}
          </span>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages || isLoading}
            className="h-7 w-7 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomOut}
            disabled={scale <= 0.6 || isLoading}
            className="h-7 w-7 text-slate-300 hover:text-white hover:bg-slate-800"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>

          <span className="text-[10px] w-10 text-center font-bold text-amber-400 tabular-nums">
            {Math.round(scale * 100)}%
          </span>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomIn}
            disabled={scale >= 2.5 || isLoading}
            className="h-7 w-7 text-slate-300 hover:text-white hover:bg-slate-800"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleResetZoom}
            disabled={isLoading}
            className="h-7 w-7 text-slate-300 hover:text-white hover:bg-slate-800 ml-1"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-4 bg-slate-900/90 relative min-h-[300px]">
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-2 text-slate-400 font-mono text-xs">
            <Loader2 className="w-5 h-5 animate-spin text-amber-500" />
            <span>RENDERING PDF.JS CANVAS...</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center gap-2 p-6 max-w-sm text-center bg-destructive/10 border border-destructive/30 rounded-xl">
            <AlertTriangle className="w-6 h-6 text-destructive" />
            <span className="text-xs font-semibold text-destructive font-mono">
              PREVIEW UNAVAILABLE
            </span>
            <p className="text-[11px] text-muted-foreground font-sans">{error}</p>
          </div>
        )}

        <canvas
          ref={canvasRef}
          className={`shadow-2xl rounded-sm transition-opacity duration-200 border border-slate-700/60 bg-white ${
            isLoading || error ? "hidden" : "block"
          }`}
        />
      </div>
    </div>
  );
};
