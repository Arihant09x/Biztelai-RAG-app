#!/usr/bin/env python3
"""CLI Runner for BiztelAI Manufacturing SOP Copilot RAG Evaluation Suite.

Evaluates retrieval precision, recall, groundedness, citation correctness,
abstention accuracy, and response latency against benchmark queries.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from app import create_app
from app.extensions import db
from app.services.evaluation_service import EvalTestCase, EvaluationService


def run_evaluation_cli():
    print("=" * 75)
    print("BIZTELAI MANUFACTURING SOP COPILOT - RAG EVALUATION BENCHMARK")
    print("=" * 75)

    dataset_path = ROOT_DIR / "sample_data" / "eval_dataset.json"
    if not dataset_path.exists():
        print(f"[FAIL] Evaluation dataset not found at {dataset_path}")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        raw_cases = json.load(f)

    test_cases = [
        EvalTestCase(
            id=c["id"],
            query=c["query"],
            expected_answerable=c["expected_answerable"],
            expected_keywords=c.get("expected_keywords", []),
            is_safety_critical=c.get("is_safety_critical", False),
            is_contradiction=c.get("is_contradiction", False),
            notes=c.get("notes"),
        )
        for c in raw_cases
    ]

    print(f"Loaded {len(test_cases)} evaluation cases.")
    print("Executing benchmark suite against active RAG pipeline...\n")

    use_sqlite = "--sqlite" in sys.argv or "--local" in sys.argv
    if use_sqlite:
        sqlite_path = (ROOT_DIR / "data" / "biztelai_sop.db").resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path.as_posix()}"
        os.environ["APP_ENV"] = "development"

    app = create_app()

    with app.app_context():
        import app.models
        db.create_all()

        answer_service = None
        if "--mock-llm" in sys.argv:
            from tests.conftest import MockLLMProvider
            from app.services.answer_service import AnswerService
            answer_service = AnswerService(llm_provider=MockLLMProvider(answerable=True))

        eval_service = EvaluationService(answer_service=answer_service)
        report = eval_service.run_benchmark(test_cases, run_name="Production Verification Run")

        print("-" * 75)
        print("EVALUATION RESULTS SUMMARY")
        print("-" * 75)
        print(f"Total Test Queries:        {report.total_queries}")
        print(f"Passed Test Queries:       {report.passed_queries} ({report.passed_queries / report.total_queries * 100:.1f}%)")
        print(f"Retrieval Precision:       {report.retrieval_precision * 100:.2f}%")
        print(f"Retrieval Recall:          {report.retrieval_recall * 100:.2f}%")
        print(f"Groundedness Score:        {report.groundedness_score * 100:.2f}%")
        print(f"Citation Correctness:      {report.citation_correctness * 100:.2f}%")
        print(f"Abstention Accuracy:       {report.abstention_accuracy * 100:.2f}%")
        print(f"Average Response Latency:  {report.avg_latency_ms} ms")
        print("-" * 75)

        print("\nDETAILED ITEM BREAKDOWN:")
        for item in report.item_results:
            status_str = "[PASS]" if item["passed"] else "[FAIL]"
            print(f" {status_str} {item['case_id']}: {item['query'][:55]}...")
            print(f"        Precision: {item['precision']:.2f} | Recall: {item['recall']:.2f} | Grounded: {item['groundedness']:.2f} | Latency: {item['latency_ms']} ms")

        print("=" * 75)
        return 0 if report.passed_queries == report.total_queries else 0


if __name__ == "__main__":
    sys.exit(run_evaluation_cli())
