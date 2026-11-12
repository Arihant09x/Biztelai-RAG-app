"""OpenAI-compatible LLM provider implementing exponential backoff, rate limiting, and timeout."""

import json
import random
import time
from typing import Any, Dict, Generator, List, Optional
from openai import OpenAI, APIError, RateLimitError, APITimeoutError, AuthenticationError
from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMTokenUsage
from app.utils.errors import LLMProviderError
from app.utils.security import mask_secret
import structlog

logger = structlog.get_logger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Universal provider for OpenAI, Gemini OpenAI-compatible endpoint, OpenRouter, etc."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout_seconds: int = 45,
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Initialize official OpenAI client pointing to configured base URL
        self.client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key or "sk-dummy-key-for-test",
            timeout=float(self.timeout_seconds),
            max_retries=0,  # We manage retries with custom exponential backoff & jitter
        )

    @property
    def provider_name(self) -> str:
        if "generativelanguage.googleapis.com" in self._base_url:
            return "Gemini (OpenAI-compatible)"
        if "openrouter.ai" in self._base_url:
            return "OpenRouter"
        if "api.openai.com" in self._base_url:
            return "OpenAI"
        return "OpenAI-Compatible Generic"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
    ) -> LLMResponse:
        """Call LLM completion with exponential retry, token tracking, and latency measurement."""
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens or self.default_max_tokens

        kwargs: Dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        if response_format_json:
            # Check if json_object format is accepted
            kwargs["response_format"] = {"type": "json_object"}

        attempt = 0
        last_error = None
        start_time = time.time()

        while attempt <= self.max_retries:
            try:
                logger.info(
                    "llm_completion_request",
                    provider=self.provider_name,
                    model=self._model_name,
                    attempt=attempt + 1,
                )
                response = self.client.chat.completions.create(**kwargs)

                duration_ms = round((time.time() - start_time) * 1000, 2)
                content = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason

                usage = LLMTokenUsage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                )

                return LLMResponse(
                    content=content,
                    token_usage=usage,
                    model_name=self._model_name,
                    finish_reason=finish_reason,
                    latency_ms=duration_ms,
                )

            except RateLimitError as e:
                attempt += 1
                last_error = e
                delay = (2 ** attempt) + random.uniform(0.1, 1.0)
                logger.warning("llm_rate_limited_backing_off", delay=delay, attempt=attempt)
                if attempt > self.max_retries:
                    break
                time.sleep(delay)

            except APITimeoutError as e:
                attempt += 1
                last_error = e
                delay = (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning("llm_timeout_retrying", delay=delay, attempt=attempt)
                if attempt > self.max_retries:
                    break
                time.sleep(delay)

            except AuthenticationError as e:
                logger.error("llm_authentication_failed", provider=self.provider_name)
                raise LLMProviderError(f"LLM authentication failed for {self.provider_name}: Invalid API Key.", status_code=401)

            except Exception as e:
                logger.error("llm_request_failed", error=str(e), attempt=attempt)
                # If json_object is rejected by provider, retry without response_format
                if response_format_json and "response_format" in kwargs and ("unsupported" in str(e).lower() or "400" in str(e)):
                    logger.info("retrying_without_response_format_json")
                    kwargs.pop("response_format", None)
                    continue

                attempt += 1
                last_error = e
                if attempt > self.max_retries:
                    break
                time.sleep(1.0 * attempt)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        raise LLMProviderError(
            f"LLM request to {self.provider_name} ({self._model_name}) failed after {self.max_retries} attempts: {str(last_error)}"
        )

    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Stream chat tokens incrementally."""
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens or self.default_max_tokens

        try:
            stream = self.client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as e:
            logger.error("llm_stream_error", error=str(e))
            raise LLMProviderError(f"LLM streaming error: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Dynamically test authenticated connection by requesting a small real completion."""
        start_time = time.time()
        test_messages = [
            {"role": "system", "content": "You are a test assistant. Answer with exactly the word OK."},
            {"role": "user", "content": "Respond with OK."},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self._model_name,
                messages=test_messages,
                max_tokens=10,
                temperature=0.0,
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            content = response.choices[0].message.content or ""
            is_valid = bool(content.strip())

            return {
                "success": is_valid,
                "provider": self.provider_name,
                "endpoint": self._base_url,
                "model": self._model_name,
                "response_text": content.strip(),
                "latency_ms": latency_ms,
                "masked_api_key": mask_secret(self._api_key),
                "error": None,
            }
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("llm_dynamic_test_failed", error=str(e))
            return {
                "success": False,
                "provider": self.provider_name,
                "endpoint": self._base_url,
                "model": self._model_name,
                "response_text": None,
                "latency_ms": latency_ms,
                "masked_api_key": mask_secret(self._api_key),
                "error": str(e),
            }

