"""Abstract base class and response data models for LLM provider integration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional


@dataclass
class LLMTokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    token_usage: LLMTokenUsage
    model_name: str
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0


class BaseLLMProvider(ABC):
    """Abstract interface for large language model completion providers."""

    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
    ) -> LLMResponse:
        """Execute chat completion request with retry and backoff."""
        pass

    @abstractmethod
    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Stream chunks of chat completion response."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test API connectivity and authenticated completion with configured model."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

