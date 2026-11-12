"""Tests for Guided Procedure generation and progress updates."""

from tests.conftest import MockLLMProvider
from app.constants import StepCompletionStatus


def test_generate_guided_procedure(client, supervisor_auth_headers, monkeypatch):
    # Mock retrieval
    def mock_hybrid_search(*args, **kwargs):
        from app.services.retrieval_service import RetrievedChunk
        return [
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Hydraulic Press SOP",
                page_number=2,
                section_heading="Safety Interlock Test",
                subheading=None,
                content="Test light curtain alignment. Press dual palm buttons simultaneously.",
                token_count=40,
                similarity_score=0.91,
            )
        ]

    monkeypatch.setattr("app.services.retrieval_service.RetrievalService.hybrid_search", mock_hybrid_search)

    # Mock provider returning procedure JSON
    class MockProcLLM(MockLLMProvider):
        def generate_chat_completion(self, messages, temperature=None, max_tokens=None, response_format_json=False):
            from app.services.llm.base import LLMResponse, LLMTokenUsage
            content = """{
  "title": "Hydraulic Press Daily Safety Inspection",
  "purpose": "Verify safety interlocks and dual palm buttons before shift start",
  "prerequisites": ["Machine power ON", "Hydraulic fluid at normal operating level"],
  "required_equipment": ["Safety glasses", "Test rod for light curtain"],
  "safety_warnings": ["Crush hazard: Do not place hands into die cavity"],
  "steps": [
    {
      "step_index": 1,
      "step_id": "step_1",
      "description": "Obstruct light curtain beam with test rod; verify immediate ram stop.",
      "source_ids": ["source_1"]
    },
    {
      "step_index": 2,
      "step_id": "step_2",
      "description": "Test dual palm buttons simultaneously within 0.5s.",
      "source_ids": ["source_1"]
    }
  ]
}"""
            return LLMResponse(
                content=content,
                token_usage=LLMTokenUsage(prompt_tokens=100, completion_tokens=100, total_tokens=200),
                model_name="mock-model",
            )

    monkeypatch.setattr("app.services.procedure_service.ProcedureService._get_provider", lambda self: MockProcLLM())

    res = client.post(
        "/api/v1/procedures/generate",
        json={"query": "How to inspect hydraulic press safety interlocks?"},
        headers=supervisor_auth_headers,
    )

    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    proc = data["data"]
    assert "Hydraulic Press" in proc["title"]
    assert len(proc["steps"]) == 2
    assert proc["steps"][0]["step_id"] == "step_1"

    # Now test updating progress on step 1
    proc_id = proc["id"]
    progress_res = client.post(
        f"/api/v1/procedures/{proc_id}/progress",
        json={
            "step_id": "step_1",
            "status": StepCompletionStatus.COMPLETED.value,
            "notes": "Light curtain beam interrupted; ram stopped in 42ms.",
        },
        headers=supervisor_auth_headers,
    )

    assert progress_res.status_code == 200
    prog_data = progress_res.get_json()
    assert prog_data["success"] is True
    assert prog_data["data"]["status"] == "completed"
    assert "42ms" in prog_data["data"]["notes"]

