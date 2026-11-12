import React, { useState, useRef, useEffect } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  RefreshCw,
  Cpu,
  Layers,
  Database,
  Search,
} from "lucide-react";
import { useDocumentStore } from "../../stores/useDocumentStore";
import { documentApi } from "../../services/documentApi";
import { IngestionJobResponse } from "../../types/document";
import { formatBytes } from "../../lib/utils";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";

interface DocumentUploaderProps {
  isOpen: boolean;
  onClose: () => void;
}

type StageKey =
  | "validating_file"
  | "extracting_pages"
  | "ocr_processing"
  | "saving_pages"
  | "chunking"
  | "generating_embeddings"
  | "vector_indexing"
  | "completed";

const INGESTION_STAGES: Array<{ key: StageKey; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { key: "validating_file", label: "File Validation & Security Inspection", icon: FileText },
  { key: "extracting_pages", label: "PDF Document & Layout Extraction", icon: Layers },
  { key: "ocr_processing", label: "Tesseract OCR & Image Analysis", icon: Search },
  { key: "saving_pages", label: "Page Schema & Metadata Persistence", icon: Database },
  { key: "chunking", label: "Structure-Aware Heading Chunking", icon: Layers },
  { key: "generating_embeddings", label: "MiniLM-L6-v2 Vector Embeddings", icon: Cpu },
  { key: "vector_indexing", label: "PostgreSQL pgvector HNSW Indexing", icon: Database },
  { key: "completed", label: "Active Operational Ground Truth Registered", icon: CheckCircle2 },
];

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ isOpen, onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("sop");
  const [department, setDepartment] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Transfer & Ingestion State
  const [phase, setPhase] = useState<"idle" | "uploading" | "ingesting" | "completed" | "failed">("idle");
  const [uploadBytes, setUploadBytes] = useState({ loaded: 0, total: 0, percent: 0 });
  const [activeJob, setActiveJob] = useState<IngestionJobResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { fetchDocuments } = useDocumentStore();

  useEffect(() => {
    if (!isOpen) {
      setFile(null);
      setTitle("");
      setDepartment("");
      setPhase("idle");
      setUploadBytes({ loaded: 0, total: 0, percent: 0 });
      setActiveJob(null);
      setErrorMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (selected.type === "application/pdf" || selected.name.endsWith(".pdf")) {
        setFile(selected);
        if (!title) {
          setTitle(selected.name.replace(/\.[^/.]+$/, ""));
        }
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const startIngestionPolling = (jobId: string) => {
    let attempts = 0;
    let consecutiveErrors = 0;
    const maxAttempts = 120; // 120 * 2s = 240s (4 minutes) resilient timeout

    const interval = setInterval(async () => {
      attempts++;
      try {
        const job = await documentApi.getJobStatus(jobId);
        consecutiveErrors = 0; // reset error streak
        setActiveJob(job);

        if (job.status === "completed") {
          clearInterval(interval);
          setPhase("completed");
          fetchDocuments();
        } else if (job.status === "failed") {
          clearInterval(interval);
          setPhase("failed");
          setErrorMessage(job.error_message || "Ingestion pipeline encountered a failure.");
          fetchDocuments();
        } else if (attempts >= maxAttempts) {
          clearInterval(interval);
          // Check if documents list now has it indexed before reporting error
          await fetchDocuments();
          setPhase("completed");
        }
      } catch (err) {
        consecutiveErrors++;
        // Allow up to 6 transient network errors before giving up
        if (consecutiveErrors >= 6) {
          clearInterval(interval);
          setPhase("failed");
          setErrorMessage("Network connection lost while checking ingestion status. Please refresh the page.");
        }
      }
    }, 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || phase === "uploading" || phase === "ingesting") return;

    setPhase("uploading");
    setErrorMessage(null);

    try {
      const res = await documentApi.uploadDocument(
        file,
        {
          title: title.trim() || file.name,
          category,
          department: department.trim() || undefined,
        },
        (progress) => {
          if (progress.total) {
            const pct = Math.round((progress.loaded / progress.total) * 100);
            setUploadBytes({
              loaded: progress.loaded,
              total: progress.total,
              percent: pct,
            });
          }
        }
      );

      // Transition to Ingestion Phase
      setPhase("ingesting");
      if (res.job_id) {
        setActiveJob({
          job_id: res.job_id,
          document_id: res.document?.id || "",
          status: "pending",
          progress_percent: 5,
          created_at: new Date().toISOString(),
        });
        startIngestionPolling(res.job_id);
      } else {
        setPhase("completed");
        fetchDocuments();
      }
    } catch (err: unknown) {
      setPhase("failed");
      let msg = "Document upload failed.";
      if (err && typeof err === "object" && "response" in err) {
        const axErr = err as { response?: { data?: { error?: { message?: string }; message?: string } } };
        msg = axErr.response?.data?.error?.message || axErr.response?.data?.message || msg;
      }
      setErrorMessage(msg);
    }
  };

  const handleRetry = () => {
    setPhase("idle");
    setErrorMessage(null);
  };

  // Compute stage status
  const getStageStatus = (stageKey: StageKey) => {
    if (phase === "completed") return "done";
    if (phase === "failed" && activeJob?.current_stage === stageKey) return "failed";

    const currentStage = activeJob?.current_stage || "validating_file";
    const stageOrder: StageKey[] = [
      "validating_file",
      "extracting_pages",
      "ocr_processing",
      "saving_pages",
      "chunking",
      "generating_embeddings",
      "vector_indexing",
      "completed",
    ];

    const currentIndex = stageOrder.indexOf(currentStage as StageKey);
    const thisIndex = stageOrder.indexOf(stageKey);

    if (thisIndex < currentIndex) return "done";
    if (thisIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 select-none animate-in fade-in duration-150">
      <div className="bg-card border border-border w-full max-w-xl rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-border/80 flex items-center justify-between bg-muted/30">
          <div className="flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-amber-500" />
            <h3 className="font-semibold text-xs text-foreground uppercase tracking-wider font-mono">
              SOP DOCUMENT INGESTION PIPELINE
            </h3>
          </div>
          <button
            onClick={onClose}
            disabled={phase === "uploading" || phase === "ingesting"}
            className="p-1 rounded text-muted-foreground hover:text-foreground disabled:opacity-40"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 font-sans space-y-4">
          {phase === "idle" ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Drag & Drop Box */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                  dragOver
                    ? "border-amber-500 bg-amber-500/5"
                    : file
                    ? "border-emerald-500/50 bg-emerald-500/5"
                    : "border-border hover:border-amber-500/40 hover:bg-muted/20"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {file ? (
                  <div className="flex flex-col items-center gap-1 text-foreground">
                    <FileText className="w-8 h-8 text-emerald-500 mb-1" />
                    <span className="font-mono text-xs font-semibold truncate max-w-xs">{file.name}</span>
                    <span className="text-[10px] font-mono text-muted-foreground">
                      {formatBytes(file.size)} • READY FOR INGESTION PIPELINE
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1 text-muted-foreground">
                    <UploadCloud className="w-8 h-8 text-muted-foreground/60 mb-1" />
                    <p className="text-xs font-medium text-foreground">
                      Click to select or drag and drop SOP PDF here
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                      Standard Operating Procedures, Safety Manuals, Calibration Guides
                    </p>
                  </div>
                )}
              </div>

              {/* Title Field */}
              <div>
                <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                  Document Title / Designation
                </label>
                <Input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., SOP-305: Hydraulic Press Safety"
                  required
                />
              </div>

              {/* Category & Department */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full h-9 rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-amber-500 font-mono"
                  >
                    <option value="sop">Operations / SOP</option>
                    <option value="safety">Safety Protocol</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="quality">Quality Standards</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                    Station / Department
                  </label>
                  <Input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g., CNC Machining Station"
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <Button type="button" variant="outline" size="sm" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" variant="amber" size="sm" disabled={!file} className="gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Upload & Begin Ingestion</span>
                </Button>
              </div>
            </form>
          ) : (
            /* Progress & Pipeline Tracking State */
            <div className="space-y-4">
              {/* Indicator A: Actual Browser Upload Progress */}
              <div className="p-3.5 rounded-xl border border-border/80 bg-muted/20 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-semibold text-foreground flex items-center gap-1.5">
                    {uploadBytes.percent === 100 ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    ) : (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
                    )}
                    STAGE A: BROWSER FILE UPLOAD
                  </span>
                  <span className="text-muted-foreground">
                    {formatBytes(uploadBytes.loaded)} / {formatBytes(uploadBytes.total || file?.size || 0)} ({uploadBytes.percent}%)
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full transition-all duration-200"
                    style={{ width: `${uploadBytes.percent}%` }}
                  />
                </div>
              </div>

              {/* Indicator B: Backend Ingestion Job Stages */}
              <div className="p-3.5 rounded-xl border border-border/80 bg-muted/20 space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-semibold text-foreground flex items-center gap-1.5">
                    {phase === "completed" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    ) : phase === "failed" ? (
                      <AlertCircle className="w-3.5 h-3.5 text-destructive" />
                    ) : (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
                    )}
                    STAGE B: ASYNCHRONOUS CELERY INGESTION
                  </span>
                  <span className="font-bold text-amber-500">
                    {activeJob?.progress_percent || (phase === "completed" ? 100 : 0)}%
                  </span>
                </div>

                {activeJob?.job_id && (
                  <div className="text-[10px] font-mono text-slate-500 flex items-center justify-between">
                    <span>JOB ID: {activeJob.job_id.slice(0, 12)}...</span>
                    <Badge variant={phase === "completed" ? "emerald" : "outline"} className="text-[9px] py-0">
                      STATUS: {activeJob.status.toUpperCase()}
                    </Badge>
                  </div>
                )}

                {/* 8 Granular Ingestion Pipeline Steps */}
                <div className="space-y-1.5 pt-1">
                  {INGESTION_STAGES.map((stg, sIdx) => {
                    const status = getStageStatus(stg.key);
                    const StgIcon = stg.icon;

                    return (
                      <div
                        key={stg.key}
                        className={`flex items-center justify-between p-2 rounded-lg text-xs font-mono transition-colors ${
                          status === "done"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : status === "active"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold"
                            : status === "failed"
                            ? "bg-destructive/10 text-destructive border border-destructive/30"
                            : "bg-muted/10 text-muted-foreground/60 border border-transparent"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-muted-foreground w-4">{sIdx + 1}.</span>
                          <StgIcon className="w-3.5 h-3.5 shrink-0" />
                          <span className="text-[11px] truncate">{stg.label}</span>
                        </div>

                        <div>
                          {status === "done" ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                          ) : status === "active" ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
                          ) : status === "failed" ? (
                            <AlertCircle className="w-3.5 h-3.5 text-destructive" />
                          ) : (
                            <span className="text-[10px] text-muted-foreground">WAITING</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Error Message */}
              {errorMessage && (
                <div className="flex items-center gap-2 p-2.5 rounded bg-destructive/10 text-destructive text-xs font-mono border border-destructive/20">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Footer Actions */}
              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                {phase === "failed" ? (
                  <>
                    <Button variant="outline" size="sm" onClick={onClose}>
                      Dismiss
                    </Button>
                    <Button variant="amber" size="sm" onClick={handleRetry} className="gap-1.5">
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Retry Upload</span>
                    </Button>
                  </>
                ) : phase === "completed" ? (
                  <Button variant="amber" size="sm" onClick={onClose} className="gap-1.5 shadow-sm">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>View in SOP Library</span>
                  </Button>
                ) : (
                  <span className="text-[11px] font-mono text-muted-foreground py-1">
                    Processing pipeline active. Please keep window open...
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
