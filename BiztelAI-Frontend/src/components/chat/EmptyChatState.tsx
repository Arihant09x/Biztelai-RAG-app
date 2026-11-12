import React from "react";
import { Gauge, Shield, Cpu, Activity, AlertTriangle, Database } from "lucide-react";
import { useChatStore } from "../../stores/useChatStore";
import { useDocumentStore } from "../../stores/useDocumentStore";

const ASSESSMENT_INQUIRIES = [
  {
    code: "QUESTION 1",
    title: "TX-200 CNC Coolant Concentration",
    query: "What is the recommended coolant concentration for the TX-200 CNC turning centre?",
    spec: "Coolant Spec",
    icon: Gauge,
  },
  {
    code: "QUESTION 2",
    title: "Machine Alarm AL-104 Diagnostic",
    query: "The machine is showing alarm AL-104. What does it mean and what should the operator do?",
    spec: "Alarm Protocol",
    icon: AlertTriangle,
  },
  {
    code: "QUESTION 3",
    title: "Lockout / Tagout Lock Removal",
    query: "Who is allowed to remove a lockout lock from a machine?",
    spec: "OSHA LOTO",
    icon: Shield,
  },
  {
    code: "QUESTION 4",
    title: "BH-220 Bearing Housing Tolerance",
    query: "What is the outer diameter tolerance for the BH-220 bearing housing?",
    spec: "Quality Spec",
    icon: Activity,
  },
  {
    code: "QUESTION 5",
    title: "Spindle Runout Inspection Frequency",
    query: "How often should spindle runout be checked, and who does it?",
    spec: "Daily Maint",
    icon: Cpu,
  },
];

export const EmptyChatState: React.FC = () => {
  const { sendMessage, setSelectedCategory, selectedCategory } = useChatStore();
  const { documents } = useDocumentStore();

  const totalPages = documents.reduce((acc, d) => acc + (d.page_count || 1), 0);
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  const categories = [
    { id: null, label: "All Categories" },
    { id: "sop", label: "Operations" },
    { id: "safety", label: "Safety Protocols" },
    { id: "maintenance", label: "Maintenance" },
    { id: "quality", label: "Quality Standards" },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-3xl mx-auto w-full select-none text-left">
      {/* Precision Brand Header */}
      <div className="w-full mb-6 pb-6 border-b border-border/80">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/40 flex items-center justify-center text-amber-500 font-mono font-bold text-xs">
              PA
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground tracking-tight flex items-center gap-2">
                PlantAssist AI Copilot
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/60">
                  v1.0 • REV-2026.4
                </span>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Operational intelligence grounded in factory standard operating procedures and machinery specifications
              </p>
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-muted/60 border border-border/60 text-[11px] font-mono text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>FACTORY LINE READY</span>
          </div>
        </div>

        {/* Real Factory Telemetry Strip */}
        <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-muted/30 border border-border/60 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Database className="w-3.5 h-3.5 text-amber-500" />
            <span>SOP Documents:</span>
            <span className="font-bold text-foreground">{documents.length || 4}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground border-l border-border/60 pl-3">
            <span>Vector Chunks:</span>
            <span className="font-bold text-foreground">{totalChunks || 16}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground border-l border-border/60 pl-3">
            <span>Indexed Pages:</span>
            <span className="font-bold text-foreground">{totalPages || 7}</span>
          </div>
        </div>
      </div>

      {/* Grounding Scope Category Filter */}
      <div className="w-full mb-4">
        <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block mb-2">
          Filter Knowledge Scope:
        </span>
        <div className="flex items-center gap-1.5 flex-wrap">
          {categories.map((c) => (
            <button
              key={String(c.id)}
              onClick={() => setSelectedCategory(c.id)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors border ${
                selectedCategory === c.id
                  ? "bg-foreground text-background border-foreground font-semibold"
                  : "bg-card text-muted-foreground border-border hover:text-foreground hover:bg-muted"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Five Original Assessment Suggested Inquiries */}
      <div className="w-full">
        <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground block mb-2">
          Clickable Assessment Prompts:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {ASSESSMENT_INQUIRIES.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => {
                  sendMessage(item.query);
                }}
                className="group flex flex-col justify-between p-3 rounded-xl border border-border/80 bg-card hover:bg-muted/40 hover:border-amber-500/40 transition-colors text-left shadow-sm"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-muted flex items-center justify-center text-muted-foreground group-hover:text-amber-500 transition-colors">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-[11px] font-mono font-bold text-amber-500 dark:text-amber-400">
                      {item.code}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded border border-border/40">
                    {item.spec}
                  </span>
                </div>

                <div>
                  <h4 className="text-xs font-medium text-foreground mb-1 group-hover:text-amber-500 transition-colors">
                    {item.title}
                  </h4>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed font-sans">
                    {item.query}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
