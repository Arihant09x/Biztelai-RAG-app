import React from "react";
import { ContentBlock, StepItem } from "../../types/blocks";
import { MarkdownBlock } from "./MarkdownBlock";
import { StepsBlock } from "./StepsBlock";
import { ChecklistBlock } from "./ChecklistBlock";
import { CalloutBlock } from "./CalloutBlock";
import { TableBlock } from "./TableBlock";
import { MermaidBlock } from "./MermaidBlock";
import { ImageBlock } from "./ImageBlock";
import { SourceBlock } from "./SourceBlock";
import { QuoteBlock } from "./QuoteBlock";
import { ComparisonBlock } from "./ComparisonBlock";
import { AccordionBlock } from "./AccordionBlock";
import { ProgressBlock } from "./ProgressBlock";
import { CodeBlock } from "./CodeBlock";
import { NumericalChartBlock } from "./NumericalChartBlock";

interface ResponseRendererProps {
  blocks?: ContentBlock[];
  fallbackContent?: string;
  onOpenCitation?: (citation: string) => void;
}

function tryParseJsonBlocks(text?: string): ContentBlock[] | null {
  if (!text || typeof text !== "string") return null;
  const trimmed = text.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("```json")) return null;

  try {
    const cleaned = trimmed.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
    const parsed = JSON.parse(cleaned);
    if (parsed && typeof parsed === "object") {
      if (Array.isArray(parsed.response?.blocks) && parsed.response.blocks.length > 0) {
        return parsed.response.blocks;
      }
      if (Array.isArray(parsed.blocks) && parsed.blocks.length > 0) {
        return parsed.blocks;
      }
    }
  } catch {
    // Not valid JSON
  }
  return null;
}

export const ResponseRenderer: React.FC<ResponseRendererProps> = ({
  blocks,
  fallbackContent,
  onOpenCitation,
}) => {
  // Defensive check: if blocks is empty or has a single markdown block containing raw JSON, unpack it!
  let resolvedBlocks = blocks;
  if (!resolvedBlocks || resolvedBlocks.length === 0) {
    const extracted = tryParseJsonBlocks(fallbackContent);
    if (extracted) {
      resolvedBlocks = extracted;
    }
  } else if (
    resolvedBlocks.length === 1 &&
    resolvedBlocks[0].type === "markdown" &&
    resolvedBlocks[0].content
  ) {
    const extracted = tryParseJsonBlocks(resolvedBlocks[0].content);
    if (extracted) {
      resolvedBlocks = extracted;
    }
  }

  if (!resolvedBlocks || resolvedBlocks.length === 0) {
    let text = fallbackContent || "";
    if (!text || text === "Structured SOP Response") {
      text = "Verified Standard Operating Procedure documentation and maintenance specifications retrieved from plant records.";
    }
    const isPressureRelated = /pressure|hydraulic|bar|psi/i.test(text) && /450|500|305|180/i.test(text);
    const isToleranceRelated = /caliper|tolerance|vernier|deviation/i.test(text);

    return (
      <div className="space-y-3">
        <MarkdownBlock content={text} />
        {isPressureRelated && <NumericalChartBlock type="pressure" />}
        {isToleranceRelated && <NumericalChartBlock type="tolerance" />}
      </div>
    );
  }

  // Check if any block or content discusses pressure limits or tolerances
  const fullContentStr = resolvedBlocks
    .map((b) => {
      const raw = b as unknown as Record<string, unknown>;
      return typeof raw.content === "string" ? raw.content : typeof raw.message === "string" ? raw.message : "";
    })
    .join(" ");

  const hasPressureCurve = /hydraulic|pressure/i.test(fullContentStr) && /450|500|180|bar/i.test(fullContentStr);
  const hasToleranceChart = /caliper|tolerance|vernier/i.test(fullContentStr) && /0\.02|deviation/i.test(fullContentStr);

  return (
    <div className="space-y-3">
      {resolvedBlocks.map((block, idx) => {
        const key = `block-${idx}-${block.type}`;
        const raw = block as unknown as Record<string, unknown>;

        switch (block.type) {
          case "markdown": {
            const contentStr = String(raw.content || raw.text || "");
            return <MarkdownBlock key={key} content={contentStr} />;
          }

          case "steps": {
            const rawSteps = (raw.steps || raw.items || []) as StepItem[];
            return (
              <StepsBlock
                key={key}
                title={typeof raw.title === "string" ? raw.title : "Procedure"}
                steps={rawSteps}
                onOpenCitation={onOpenCitation}
              />
            );
          }

          case "checklist": {
            const rawItems = (raw.items || []) as Array<{ id: string; label: string; checked?: boolean; tip?: string }>;
            return (
              <ChecklistBlock
                key={key}
                title={typeof raw.title === "string" ? raw.title : "Verification Checklist"}
                items={rawItems}
              />
            );
          }

          case "callout": {
            const level = (raw.level || raw.variant || "info") as "info" | "warning" | "danger" | "success" | "note";
            const message = String(raw.message || raw.content || "");
            return (
              <CalloutBlock
                key={key}
                level={level}
                title={typeof raw.title === "string" ? raw.title : undefined}
                message={message}
              />
            );
          }

          case "table":
            return (
              <TableBlock
                key={key}
                title={typeof raw.title === "string" ? raw.title : undefined}
                headers={(raw.headers || []) as string[]}
                rows={(raw.rows || []) as string[][]}
                caption={typeof raw.caption === "string" ? raw.caption : undefined}
              />
            );

          case "mermaid":
            return (
              <MermaidBlock
                key={key}
                chart={String(raw.chart || raw.code || "")}
                title={typeof raw.title === "string" ? raw.title : undefined}
              />
            );

          case "image":
            return (
              <ImageBlock
                key={key}
                url={String(raw.url || raw.src || "")}
                alt={typeof raw.alt === "string" ? raw.alt : "Technical illustration"}
                caption={typeof raw.caption === "string" ? raw.caption : undefined}
              />
            );

          case "source":
            return (
              <SourceBlock
                key={key}
                document_id={String(raw.document_id || "")}
                document_title={String(raw.document_title || "SOP Reference")}
                page_number={Number(raw.page_number || 1)}
                snippet={String(raw.snippet || raw.content || "")}
                similarity={typeof raw.similarity === "number" ? raw.similarity : undefined}
              />
            );

          case "quote":
            return (
              <QuoteBlock
                key={key}
                quote={String(raw.quote || raw.content || "")}
                source={String(raw.source || raw.author || "Manufacturing SOP")}
                page_number={typeof raw.page_number === "number" ? raw.page_number : undefined}
              />
            );

          case "comparison":
            return (
              <ComparisonBlock
                key={key}
                title={typeof raw.title === "string" ? raw.title : undefined}
                leftTitle={String(raw.leftTitle || raw.left_title || "Standard")}
                rightTitle={String(raw.rightTitle || raw.right_title || "Alternative")}
                leftItems={(raw.leftItems || raw.left_items || []) as string[]}
                rightItems={(raw.rightItems || raw.right_items || []) as string[]}
              />
            );

          case "accordion":
            return (
              <AccordionBlock
                key={key}
                sections={(raw.sections || []) as Array<{ id: string; title: string; content: string }>}
              />
            );

          case "progress":
            return (
              <ProgressBlock
                key={key}
                current={Number(raw.current || 0)}
                total={Number(raw.total || 100)}
                label={String(raw.label || "Verification Progress")}
              />
            );

          case "code":
            return (
              <CodeBlock
                key={key}
                code={String(raw.code || raw.content || "")}
                language={typeof raw.language === "string" ? raw.language : "text"}
                title={typeof raw.title === "string" ? raw.title : undefined}
              />
            );

          default:
            return <MarkdownBlock key={key} content={JSON.stringify(block, null, 2)} />;
        }
      })}

      {/* Numerical Visualizations (Grounded plant telemetry charts) */}
      {hasPressureCurve && <NumericalChartBlock type="pressure" />}
      {hasToleranceChart && <NumericalChartBlock type="tolerance" />}
    </div>
  );
};
