export type BlockType =
  | "markdown"
  | "steps"
  | "checklist"
  | "callout"
  | "table"
  | "mermaid"
  | "image"
  | "source"
  | "quote"
  | "comparison"
  | "accordion"
  | "progress"
  | "code";

export interface MarkdownBlock {
  type: "markdown";
  content: string;
}

export interface StepItem {
  step_number: number;
  instruction: string;
  warning?: string;
  critical?: boolean;
  tool?: string;
  citation?: string;
  completed?: boolean;
}

export interface StepsBlock {
  type: "steps";
  title?: string;
  steps: StepItem[];
}

export interface ChecklistItem {
  id: string;
  label: string;
  required?: boolean;
  checked?: boolean;
  tip?: string;
}

export interface ChecklistBlock {
  type: "checklist";
  title?: string;
  items: ChecklistItem[];
}

export interface CalloutBlock {
  type: "callout";
  level: "info" | "warning" | "danger" | "success" | "note";
  title?: string;
  message: string;
}

export interface TableBlock {
  type: "table";
  title?: string;
  headers: string[];
  rows: (string | number)[][];
}

export interface MermaidBlock {
  type: "mermaid";
  code: string;
  title?: string;
}

export interface ImageBlock {
  type: "image";
  url?: string;
  caption?: string;
  page_number?: number;
  document_title?: string;
}

export interface SourceBlock {
  type: "source";
  document_id: string;
  document_title: string;
  page_number: number;
  snippet: string;
  similarity?: number;
}

export interface QuoteBlock {
  type: "quote";
  quote: string;
  source: string;
  page_number?: number;
}

export interface ComparisonBlock {
  type: "comparison";
  title?: string;
  headers: string[];
  items: Array<{
    feature: string;
    option_a: string;
    option_b: string;
  }>;
}

export interface AccordionBlock {
  type: "accordion";
  title: string;
  content: string;
}

export interface ProgressBlock {
  type: "progress";
  label: string;
  value: number;
  max?: number;
  unit?: string;
}

export interface CodeBlock {
  type: "code";
  code: string;
  language?: string;
}

export type ContentBlock =
  | MarkdownBlock
  | StepsBlock
  | ChecklistBlock
  | CalloutBlock
  | TableBlock
  | MermaidBlock
  | ImageBlock
  | SourceBlock
  | QuoteBlock
  | ComparisonBlock
  | AccordionBlock
  | ProgressBlock
  | CodeBlock;

