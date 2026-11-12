"""Pytest fixtures providing in-memory database, test client, and mock services."""

import io
from typing import Generator
import pytest
import pymupdf
from app import create_app
from app.constants import UserRole
from app.extensions import db
from app.models.user import Role, User
from app.services.auth_service import AuthService
from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMTokenUsage
from app.utils.security import hash_password


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider returning valid structured JSON blocks."""

    def __init__(self, answerable: bool = True):
        self._answerable = answerable

    @property
    def provider_name(self) -> str:
        return "MockLLM"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def generate_chat_completion(self, messages, temperature=None, max_tokens=None, response_format_json=False):
        if not self._answerable:
            content = '{"answerable": false, "confidence_score": 0.0, "response": {"blocks": [{"type": "callout", "variant": "warning", "title": "Insufficient Evidence", "content": "No documentation found."}]}, "sources": [], "warnings": ["Abstained."]}'
        else:
            content = """{
  "answerable": true,
  "confidence_score": 0.95,
  "response": {
    "blocks": [
      {
        "type": "markdown",
        "content": "Overview: Inspect spindle lock pressure."
      },
      {
        "type": "callout",
        "variant": "warning",
        "title": "Safety Alert",
        "content": "Wear safety glasses and hearing protection.",
        "source_ids": ["source_1"]
      },
      {
        "type": "steps",
        "title": "Inspection Steps",
        "items": [
          {
            "id": "step_1",
            "content": "Verify pneumatic pressure is at 50 PSI.",
            "source_ids": ["source_1"]
          }
        ]
      },
      {
        "type": "checklist",
        "title": "Verification",
        "items": [
          {
            "id": "check_1",
            "content": "Check pressure gauge reading.",
            "source_ids": ["source_1"],
            "checked": false
          }
        ]
      }
    ]
  },
  "warnings": []
}"""
        return LLMResponse(
            content=content,
            token_usage=LLMTokenUsage(prompt_tokens=100, completion_tokens=80, total_tokens=180),
            model_name="mock-model",
            finish_reason="stop",
            latency_ms=15.0,
        )

    def stream_chat_completion(self, messages, temperature=None, max_tokens=None):
        tokens = ["Verify ", "pneumatic ", "pressure ", "is ", "at ", "50 PSI."]
        for t in tokens:
            yield t

    def test_connection(self):
        return {
            "success": True,
            "provider": "MockLLM",
            "endpoint": "mock://api",
            "model": "mock-model",
            "response_text": "OK",
            "latency_ms": 10.0,
            "masked_api_key": "mock...mock",
            "error": None,
        }


@pytest.fixture(scope="session")
def app():
    """Create Flask application configured for testing with in-memory SQLite."""
    test_app = create_app("testing")
    return test_app


@pytest.fixture(scope="function")
def db_session(app):
    """Create fresh database tables for each test and drop them afterwards."""
    with app.app_context():
        db.create_all()

        # Seed standard roles
        for r_name in [UserRole.ADMIN.value, UserRole.SUPERVISOR.value, UserRole.OPERATOR.value, UserRole.AUDITOR.value]:
            if not Role.query.filter_by(name=r_name).first():
                db.session.add(Role(name=r_name, description=f"{r_name} role"))
        db.session.commit()

        yield db.session

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app, db_session):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def supervisor_user(db_session) -> User:
    """Create and return a test supervisor user."""
    sup_role = Role.query.filter_by(name=UserRole.SUPERVISOR.value).first()
    user = User(
        email="supervisor.test@biztelai.com",
        password_hash=hash_password("Password123!"),
        full_name="Test Supervisor",
        department="Machining",
        role_id=sup_role.id,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def operator_user(db_session) -> User:
    """Create and return a test operator user."""
    op_role = Role.query.filter_by(name=UserRole.OPERATOR.value).first()
    user = User(
        email="operator.test@biztelai.com",
        password_hash=hash_password("Password123!"),
        full_name="Test Operator",
        department="Machining",
        role_id=op_role.id,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def supervisor_auth_headers(app, supervisor_user) -> dict:
    """Generate Authorization header with supervisor JWT token."""
    with app.app_context():
        auth_service = AuthService()
        _, tokens = auth_service.authenticate_user(supervisor_user.email, "Password123!")
        return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def operator_auth_headers(app, operator_user) -> dict:
    """Generate Authorization header with operator JWT token."""
    with app.app_context():
        auth_service = AuthService()
        _, tokens = auth_service.authenticate_user(operator_user.email, "Password123!")
        return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate in-memory valid PDF bytes for testing upload and extraction."""
    doc = pymupdf.open()
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text(
        (50, 50),
        "SECTION 1: HYDRAULIC PRESSURE OPERATING LIMITS\n"
        "Maximum allowable operating pressure for press HP-200 is 180 bar.\n"
        "[SAFETY WARNING]\n"
        "Wear steel-toe boots and face shield during high pressure hydraulic testing.",
        fontsize=11,
    )
    pdf_data = doc.tobytes()
    doc.close()
    return pdf_data

