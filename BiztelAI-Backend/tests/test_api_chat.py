"""API integration tests for Chat, Conversations, and Feedback."""

import pytest
from tests.conftest import MockLLMProvider
from app.services.answer_service import AnswerService
from app.services.context_service import EngineeredContext
from app.schemas.response_blocks import SourceCitation


def test_chat_endpoint_success(client, supervisor_auth_headers, monkeypatch):
    # Patch LLM provider with MockLLMProvider
    mock_provider = MockLLMProvider(answerable=True)

    # Mock retrieval and context to provide valid ground evidence
    def mock_hybrid_search(*args, **kwargs):
        from app.services.retrieval_service import RetrievedChunk
        return [
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="CNC Maintenance SOP",
                page_number=1,
                section_heading="Spindle Pressure",
                subheading=None,
                content="Pneumatic lock pressure must be 50 PSI.",
                token_count=30,
                similarity_score=0.92,
            )
        ]

    monkeypatch.setattr("app.services.retrieval_service.RetrievalService.hybrid_search", mock_hybrid_search)
    monkeypatch.setattr("app.services.answer_service.AnswerService._get_provider", lambda self: mock_provider)

    res = client.post(
        "/api/v1/chat",
        json={"question": "What is the pneumatic lock pressure for the CNC spindle?"},
        headers=supervisor_auth_headers,
    )

    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "conversation_id" in data
    assert "data" in data
    assert data["data"]["answerable"] is True
    assert len(data["data"]["response"]["blocks"]) >= 2


def test_chat_abstention_on_unanswerable_query(client, supervisor_auth_headers, monkeypatch):
    # Return empty retrieval candidates
    monkeypatch.setattr("app.services.retrieval_service.RetrievalService.hybrid_search", lambda *args, **kwargs: [])

    res = client.post(
        "/api/v1/chat",
        json={"question": "How to make a chocolate cake?"},
        headers=supervisor_auth_headers,
    )

    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["answerable"] is False
    assert data["data"]["confidence_score"] == 0.0


def test_submit_feedback(client, supervisor_auth_headers, supervisor_user, db_session):
    from app.models.conversation import Conversation, Message
    # Create conversation and message with valid user UUID
    conv = Conversation(user_id=supervisor_user.id, title="Test Conv")
    db_session.add(conv)
    db_session.flush()

    msg = Message(
        conversation_id=conv.id,
        sender_type="assistant",
        content="Here is the procedure.",
        structured_response_json={},
    )
    db_session.add(msg)
    db_session.commit()

    res = client.post(
        "/api/v1/feedback",
        json={
            "message_id": str(msg.id),
            "rating": 1,
            "comment": "Accurate procedure with page citation.",
            "flag_for_review": False,
        },
        headers=supervisor_auth_headers,
    )

    assert res.status_code == 201
    assert res.get_json()["success"] is True
