"""Configurable LLM interface with a required rule-based fallback."""

import os
from typing import Optional


def configured_provider() -> Optional[str]:
    provider = os.environ.get("LLM_PROVIDER", "").strip()
    key = os.environ.get("LLM_API_KEY", "").strip()
    if provider and key:
        return provider
    return None


def complete(prompt: str, fallback: str) -> dict:
    """
    Return grounded text.

    No provider call is made unless both LLM_PROVIDER and LLM_API_KEY are set.
    The prompt must already contain only verified fields; this function does not
    invent detections, coordinates, or repair status.
    """
    provider = configured_provider()
    if not provider:
        return {
            "source": "rule_based",
            "provider": None,
            "text": fallback,
            "note": "Set LLM_PROVIDER and LLM_API_KEY to enable a hosted model. The fallback uses stored fields only.",
        }
    return {
        "source": "unsent",
        "provider": provider,
        "text": fallback,
        "note": (
            f"Provider '{provider}' is configured, but this build does not send prompts "
            "until a reviewed client for that provider is enabled. The rule-based report is returned."
        ),
    }
