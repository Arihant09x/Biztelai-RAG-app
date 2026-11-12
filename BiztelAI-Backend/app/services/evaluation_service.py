"""RAG Evaluation framework measuring retrieval, groundedness, citations, and abstention."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.extensions import db
from app.models.evaluation import EvaluationItem, EvaluationRun
from app.services.answer_service import AnswerService
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EvalTestCase:
    id: str
    query: str
    expected_answerable: bool
    expected_doc_ids: List[str] = field(default_factory=list)
    expected_pages: List[int] = field(default_factory=list)
    expected_keywords: List[str] = field(default_factory=list)
    is_safety_critical: bool = False
    is_contradiction: bool = False
    notes: Optional[str] = None


@dataclass
class EvalReport:
    run_name: str
    total_queries: int
    passed_queries: int
    retrieval_precision: float
    retrieval_recall: float
    groundedness_score: float
    citation_correctness: float
    abstention_accuracy: float
    avg_latency_ms: float
    item_results: List[Dict[str, Any]] = field(default_factory=list)


class EvaluationService:
    """Evaluates RAG pipeline accuracy against golden test benchmarks."""

    def __init__(self, answer_service: Optional[AnswerService] = None):
        self.answer_service = answer_service or AnswerService()

    def run_benchmark(
        self,
        test_cases: List[EvalTestCase],
        run_name: str = "Benchmark Run",
        user_id: Optional[str] = None,
    ) -> EvalReport:
        """Execute evaluation suite across all benchmark test queries."""
        total = len(test_cases)
        passed_count = 0
        total_prec = 0.0
        total_rec = 0.0
        total_ground = 0.0
        total_cit = 0.0
        total_abstain_acc = 0.0
        total_latency = 0.0

        item_records: List[EvaluationItem] = []
        item_summaries: List[Dict[str, Any]] = []

        eval_run = EvaluationRun(
            run_name=run_name,
            dataset_name="Standard Manufacturing SOP Benchmark",
            total_queries=total,
            created_by_id=user_id,
        )
        db.session.add(eval_run)
        db.session.flush()

        for case in test_cases:
            t_start = time.time()
            res = self.answer_service.generate_answer(query=case.query)
            latency_ms = round((time.time() - t_start) * 1000, 2)
            total_latency += latency_ms

            # 1. Answerability classification accuracy
            is_answerable = res.answerable
            abstention_correct = (is_answerable == case.expected_answerable)
            abstain_score = 1.0 if abstention_correct else 0.0
            total_abstain_acc += abstain_score

            # 2. Retrieval Precision and Recall
            retrieved_doc_ids = {c.document_id for c in res.sources}
            combined_retrieved_text = " ".join(
                (c.snippet + " " + (c.section or "") + " " + c.document_title).lower()
                for c in res.sources
            )

            if case.expected_doc_ids:
                exp_docs = set(case.expected_doc_ids)
                true_pos = len(retrieved_doc_ids.intersection(exp_docs))
                prec = true_pos / len(retrieved_doc_ids) if retrieved_doc_ids else 0.0
                rec = true_pos / len(exp_docs)
            elif case.expected_keywords:
                matched_kw = sum(
                    1 for kw in case.expected_keywords
                    if all(part in combined_retrieved_text for part in kw.lower().split())
                )
                prec = matched_kw / len(case.expected_keywords) if case.expected_keywords else 1.0
                rec = 1.0 if matched_kw > 0 else 0.0
            else:
                prec = 1.0 if not retrieved_doc_ids and not case.expected_answerable else (1.0 if retrieved_doc_ids else 0.0)
                rec = 1.0 if not case.expected_answerable else (1.0 if retrieved_doc_ids else 0.0)

            total_prec += prec
            total_rec += rec

            # 3. Groundedness and citation correctness
            has_unsupported = bool(res.unsupported_claims)
            cit_correct = 1.0 if (not has_unsupported and (len(res.sources) > 0 or not is_answerable)) else 0.0
            total_cit += cit_correct

            groundedness = 1.0 if (abstention_correct and not has_unsupported) else 0.5
            total_ground += groundedness

            case_passed = abstention_correct and cit_correct >= 1.0 and (prec >= 0.3 or rec >= 0.8)

            if case_passed:
                passed_count += 1

            eval_item = EvaluationItem(
                evaluation_run_id=eval_run.id,
                query=case.query,
                expected_answerable=case.expected_answerable,
                actual_answerable=is_answerable,
                precision=round(prec, 4),
                recall=round(rec, 4),
                groundedness=round(groundedness, 4),
                citation_correctness=round(cit_correct, 4),
                latency_ms=latency_ms,
                passed=case_passed,
                details={
                    "warnings": res.warnings,
                    "unsupported_claims": res.unsupported_claims,
                    "sources_count": len(res.sources),
                },
            )
            db.session.add(eval_item)
            item_summaries.append({
                "case_id": case.id,
                "query": case.query,
                "passed": case_passed,
                "precision": prec,
                "recall": rec,
                "groundedness": groundedness,
                "latency_ms": latency_ms,
            })

        # Calculate averages
        avg_prec = round(total_prec / total, 4) if total > 0 else 0.0
        avg_rec = round(total_rec / total, 4) if total > 0 else 0.0
        avg_ground = round(total_ground / total, 4) if total > 0 else 0.0
        avg_cit = round(total_cit / total, 4) if total > 0 else 0.0
        avg_abstain = round(total_abstain_acc / total, 4) if total > 0 else 0.0
        avg_lat = round(total_latency / total, 2) if total > 0 else 0.0

        eval_run.passed_queries = passed_count
        eval_run.metrics_summary = {
            "retrieval_precision": avg_prec,
            "retrieval_recall": avg_rec,
            "groundedness_score": avg_ground,
            "citation_correctness": avg_cit,
            "abstention_accuracy": avg_abstain,
            "avg_latency_ms": avg_lat,
            "passed_percentage": round((passed_count / total) * 100, 2) if total > 0 else 0.0,
        }
        db.session.commit()

        return EvalReport(
            run_name=run_name,
            total_queries=total,
            passed_queries=passed_count,
            retrieval_precision=avg_prec,
            retrieval_recall=avg_rec,
            groundedness_score=avg_ground,
            citation_correctness=avg_cit,
            abstention_accuracy=avg_abstain,
            avg_latency_ms=avg_lat,
            item_results=item_summaries,
        )
