export interface ProcedureStep {
  step_number: number;
  instruction: string;
  warning?: string;
  critical?: boolean;
  tool?: string;
  citation?: string;
  completed: boolean;
  notes?: string;
}

export interface ProcedureExecution {
  id: string;
  title: string;
  document_id?: string;
  steps: ProcedureStep[];
  started_at: string;
  completed_at?: string;
  current_step_index: number;
  status: "in_progress" | "completed" | "aborted";
}

export interface StepProgressUpdate {
  step_number: number;
  completed: boolean;
  notes?: string;
}

