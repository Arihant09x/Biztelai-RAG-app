"""Token counting and context budget management utilities."""

import re
from typing import List, Optional


def estimate_tokens(text: Optional[str]) -> int:
    """Estimate token count for a text string using standard subword heuristics (~4 chars/token)."""
    if not text:
        return 0
    # Words + punctuation heuristic
    words = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    # Typically 1 word = 1.3 tokens on average for English technical text
    return max(1, int(len(words) * 1.25))


def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """Safely truncate text so it does not exceed the specified token limit."""
    if not text:
        return ""
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text

    # Approximate character limit based on 4 characters per token
    approx_chars = max_tokens * 4
    truncated = text[:approx_chars]
    # Back up to last sentence or newline if possible
    last_period = truncated.rfind(".")
    last_newline = truncated.rfind("\n")
    cutoff = max(last_period, last_newline)
    if cutoff > approx_chars // 2:
        return truncated[: cutoff + 1] + "\n...[Content truncated to fit token budget]"
    return truncated + "...[Truncated]"

