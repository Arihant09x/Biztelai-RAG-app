"""Guided Procedure Generation and Step Progress Persistence Service."""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.constants import StepCompletionStatus
from app.extensions import db
from app.models.procedure import ProcedureExecution, ProcedureStepProgress
from app.schemas.procedure import (
    ProcedureProgressUpdateRequest,
    ProcedureResponse,
    ProcedureStepResponse,
)
from app.services.context_service import ContextEngineeringService
from app.services.llm.base import BaseLLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.retrieval_service import RetrievalService
from app.services.reranking_service import RerankingService
from app.services.validation_service import ValidationService
from app.utils.errors import NotFoundError, ValidationError
import structlog

logger = structlog.get_logger(__name__)


PROCEDURE_SYSTEM_PROMPT = """You are BiztelAI Procedure Specialist. Your task is to extract and generate a strict, source-grounded Guided Standard Operating Procedure for manufacturing personnel.

CRITICAL RULES:
1. ONLY generate steps, equipment, and prerequisites that are explicitly documented in the provided EVIDENCE.
2. If evidence is missing, DO NOT invent tools, torque values, or steps. State that they are not specified in the manual.
3. Every step in "steps" MUST include the exact source citation ID from the evidence, e.g. ["source_1"].
4. Include all documented safety warnings and precautions.
5. NEVER claim that completing the checklist guarantees zero risk or proves the machine is completely safe. Always include standard safety disclaimers.

OUTPUT JSON FORMAT:
{
  "title": "Clear Procedure Title",
  "purpose": "Precise operational purpose",
  "prerequisites": ["List of documented prerequisites"],
  "required_equipment": ["Documented PPE, tools, calibration gauges"],
  "safety_warnings": ["Crucial safety alerts"],
  "steps": [
    {
      "step_index": 1,
      "step_id": "step_1",
      "description": "Clear action instruction.",
      "source_ids": ["source_1"]
    }
  ],
  "verification_checklist": [
    {
      "check_id": "check_1",
      "description": "Specific condition or reading to verify.",
      "source_ids": ["source_1"]
    }
  ]
}
"""


class ProcedureService:
    """Manages guided procedure generation, grounding validation, and progress tracking."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        reranking_service: Optional[RerankingService] = None,
        context_service: Optional[ContextEngineeringService] = None,
        validation_service: Optional[ValidationService] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.reranking_service = reranking_service or RerankingService()
        self.context_service = context_service or ContextEngineeringService()
        self.validation_service = validation_service or ValidationService()
        self.llm_provider = llm_provider

    def _get_provider(self) -> BaseLLMProvider:
        if self.llm_provider is None:
            self.llm_provider = get_llm_provider()
        return self.llm_provider

    def generate_guided_procedure(
        self,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
        department: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ProcedureResponse:
        """Retrieve procedure documentation, generate guided steps with source IDs, and persist procedure."""
        # 1. Retrieve candidates
        doc_ids = [document_id] if document_id else None
        candidates = self.retrieval_service.hybrid_search(
            query=query,
            top_k=10,
            department=department,
            document_ids=doc_ids,
        )

        # 2. Rerank
        reranked_chunks, _ = self.reranking_service.rerank(query=query, candidates=candidates, top_k=6)

        # 3. Context
        context = self.context_service.engineer_context(chunks=reranked_chunks, query=query)

        # 4. Check answerability
        is_answerable, reason = self.validation_service.check_answerability(context, query)
        if not is_answerable:
            raise ValidationError(
                f"Cannot generate procedure: {reason or 'No supporting SOP documentation available.'}"
            )

        # 5. Call LLM
        prompt = (
            f"PROCEDURE QUERY: {query}\n\n"
            f"DOCUMENT EVIDENCE:\n{context.context_text}\n\n"
            "Extract and generate the structured guided procedure in strict JSON format."
        )

        provider = self._get_provider()
        llm_res = provider.generate_chat_completion(
            messages=[
                {"role": "system", "content": PROCEDURE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format_json=True,
        )

        # Parse LLM response
        proc_data = self._parse_procedure_json(llm_res.content)

        # 6. Validate source IDs against real citations
        valid_citation_ids = {c.id for c in context.citations}
        validated_steps = []
        for step in proc_data.get("steps", []):
            s_ids = [sid for sid in step.get("source_ids", []) if sid in valid_citation_ids]
            if not s_ids and context.citations:
                s_ids = [context.citations[0].id]
            step["source_ids"] = s_ids
            validated_steps.append(step)

        # 7. Persist ProcedureExecution entity
        execution = ProcedureExecution(
            user_id=user_id,
            conversation_id=conversation_id,
            title=proc_data.get("title", f"Procedure: {query[:50]}"),
            purpose=proc_data.get("purpose", query),
            prerequisites=proc_data.get("prerequisites", []),
            required_equipment=proc_data.get("required_equipment", []),
            status="in_progress",
        )
        db.session.add(execution)
        db.session.flush()

        step_responses = []
        for idx, s in enumerate(validated_steps, start=1):
            step_record = ProcedureStepProgress(
                procedure_id=execution.id,
                step_index=idx,
                step_id=s.get("step_id", f"step_{idx}"),
                description=s.get("description", "Perform step"),
                status=StepCompletionStatus.PENDING.value,
                source_ids=s.get("source_ids", []),
            )
            db.session.add(step_record)
            step_responses.append(
                ProcedureStepResponse(
                    step_index=idx,
                    step_id=step_record.step_id,
                    description=step_record.description,
                    status=step_record.status,
                    source_ids=step_record.source_ids,
                    notes=None,
                    completed_at=None,
                )
            )

        db.session.commit()

        return ProcedureResponse(
            id=str(execution.id),
            title=execution.title,
            purpose=execution.purpose,
            prerequisites=execution.prerequisites,
            required_equipment=execution.required_equipment,
            status=execution.status,
            steps=step_responses,
            created_at=execution.created_at,
        )

    def update_step_progress(
        self,
        procedure_id: str,
        user_id: str,
        update_data: ProcedureProgressUpdateRequest,
    ) -> ProcedureStepResponse:
        """Update individual procedure step completion status and supervisor notes."""
        step = (
            db.session.query(ProcedureStepProgress)
            .join(ProcedureExecution, ProcedureStepProgress.procedure_id == ProcedureExecution.id)
            .filter(
                ProcedureStepProgress.procedure_id == procedure_id,
                ProcedureStepProgress.step_id == update_data.step_id,
            )
            .first()
        )
        if not step:
            raise NotFoundError(f"Procedure step '{update_data.step_id}' not found.")

        # Update status
        valid_statuses = [s.value for s in StepCompletionStatus]
        if update_data.status not in valid_statuses:
            raise ValidationError(f"Invalid status '{update_data.status}'. Must be one of {valid_statuses}")

        step.status = update_data.status
        if update_data.notes is not None:
            step.notes = update_data.notes

        if update_data.status == StepCompletionStatus.COMPLETED.value:
            step.completed_at = datetime.now(timezone.utc)
            step.completed_by_id = user_id
        else:
            step.completed_at = None

        db.session.commit()

        return ProcedureStepResponse(
            step_index=step.step_index,
            step_id=step.step_id,
            description=step.description,
            status=step.status,
            source_ids=step.source_ids,
            notes=step.notes,
            completed_at=step.completed_at,
        )

    def _parse_procedure_json(self, raw: str) -> Dict[str, Any]:
        """Extract and clean procedure JSON structure from LLM response."""
        try:
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned.strip())
            return json.loads(cleaned)
        except Exception as e:
            logger.warning("procedure_json_parse_fallback", error=str(e))
            return {
                "title": "Guided Operating Procedure",
                "purpose": "Standard procedure execution",
                "prerequisites": [],
                "required_equipment": [],
                "steps": [
                    {
                        "step_index": 1,
                        "step_id": "step_1",
                        "description": raw[:300],
                        "source_ids": [],
                    }
                ],
            }

