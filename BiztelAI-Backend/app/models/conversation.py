"""Conversation, Message, and MessageSource models for RAG dialogue history."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID


class Conversation(BaseModel):
    """Dialogue thread between user and Copilot."""
    __tablename__ = "conversations"

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New SOP Discussion", nullable=False)
    department_filter = Column(String(100), nullable=True)
    category_filter = Column(String(100), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<Conversation {self.id} title={self.title}>"


class Message(BaseModel):
    """Individual interaction turn with structured block response."""
    __tablename__ = "messages"

    conversation_id = Column(GUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    structured_response_json = Column(JSON, default=dict, nullable=False)
    intent = Column(String(50), nullable=True)
    token_usage = Column(JSON, default=dict, nullable=False)
    latency_ms = Column(Float, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    sources = relationship("MessageSource", back_populates="message", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="message", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Message {self.id} sender={self.sender_type}>"


class MessageSource(BaseModel):
    """Grounded document citations verifying the assistant's answer."""
    __tablename__ = "message_sources"

    message_id = Column(GUID, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(GUID, ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    citation_label = Column(String(50), nullable=False)  # e.g., 'source_1'
    relevance_score = Column(Float, nullable=True)
    snippet = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)

    message = relationship("Message", back_populates="sources")
    document = relationship("Document")
    chunk = relationship("DocumentChunk")

    def __repr__(self) -> str:
        return f"<MessageSource label={self.citation_label} doc={self.document_id} page={self.page_number}>"

