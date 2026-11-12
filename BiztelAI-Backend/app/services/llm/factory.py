"""Factory for instantiating configured LLM providers."""

from typing import Optional
from flask import current_app
from app.config import Config
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAICompatibleProvider


def get_llm_provider(config: Optional[Config] = None) -> BaseLLMProvider:
    """Instantiate and return the configured LLM provider."""
    cfg = config or (current_app.config if current_app else Config)

    base_url = cfg.get("LLM_API_BASE_URL") if isinstance(cfg, dict) else getattr(cfg, "LLM_API_BASE_URL", "https://api.openai.com/v1")
    api_key = cfg.get("LLM_API_KEY") if isinstance(cfg, dict) else getattr(cfg, "LLM_API_KEY", "")
    model_name = cfg.get("LLM_MODEL") if isinstance(cfg, dict) else getattr(cfg, "LLM_MODEL", "gpt-4o-mini")
    temperature = cfg.get("LLM_TEMPERATURE") if isinstance(cfg, dict) else getattr(cfg, "LLM_TEMPERATURE", 0.0)
    max_tokens = cfg.get("LLM_MAX_TOKENS") if isinstance(cfg, dict) else getattr(cfg, "LLM_MAX_TOKENS", 2048)
    timeout = cfg.get("LLM_TIMEOUT_SECONDS") if isinstance(cfg, dict) else getattr(cfg, "LLM_TIMEOUT_SECONDS", 45)

    return OpenAICompatibleProvider(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
        timeout_seconds=int(timeout),
    )

