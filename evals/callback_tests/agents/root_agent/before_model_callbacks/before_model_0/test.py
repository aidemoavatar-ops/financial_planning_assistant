"""
Callback Tests — before_model_callback 0 (Root Agent: deterministic_greeting)

Tests the deterministic identity-disclosure greeting callback.

WHAT THIS TESTS:
    - Session-start event + authenticated → returns fixed English greeting
    - Session-start event + authenticated + German → returns German greeting
    - Session-start event + unauthenticated → returns None (LLM handles PIN prompt)
    - Non-session-start message → returns None (no-op)
    - Greeting text includes Atlas identity and advisor disclaimer

RUNNING:
    pytest evals/callback_tests/tests/ -v
"""

import sys
import os
from unittest.mock import MagicMock

# -------------------------------------------------------------------------
# MOCK INJECTION: Must happen BEFORE importing python_code.
# -------------------------------------------------------------------------
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "before_model_callbacks", "before_model_0",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import before_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402


def _session_start_ctx(state=None):
    """Context with a welcome event as last user input."""
    ctx = CallbackContext(state=state or {"auth_status": "authenticated"})
    ctx.user_content = Content(
        role="user",
        parts=[Part(text="<event>welcome</event>")],
    )
    return ctx


def _normal_turn_ctx(state=None, text="What is an emergency fund?"):
    """Context with a normal user message as last user input."""
    ctx = CallbackContext(state=state or {"auth_status": "authenticated"})
    ctx.user_content = Content(
        role="user",
        parts=[Part(text=text)],
    )
    return ctx


# =============================================================================
# Session-start + authenticated
# =============================================================================

class TestGreetingOnSessionStart:
    """Greeting is returned deterministically at session start when authenticated."""

    def test_returns_response_not_none(self):
        """Session start + authenticated → response is not None."""
        ctx = _session_start_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is not None

    def test_response_contains_text(self):
        """Response must include at least one text part."""
        ctx = _session_start_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        texts = [p.text for p in result.content.parts if hasattr(p, "text") and p.text]
        assert len(texts) > 0

    def test_english_greeting_by_default(self):
        """Default language (English) → greeting is in English."""
        ctx = _session_start_ctx(state={"auth_status": "authenticated"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "atlas" in text.lower(), "Greeting must mention Atlas by name"

    def test_english_greeting_contains_disclaimer(self):
        """English greeting contains the non-advisor disclaimer."""
        ctx = _session_start_ctx(state={"auth_status": "authenticated"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        # PRD mandates this disclaimer — must be present
        assert "not a licensed" in text.lower() or "not a financial advisor" in text.lower()

    def test_german_greeting_when_active_language_german(self):
        """active_language = 'German' → German greeting is returned."""
        ctx = _session_start_ctx(state={
            "auth_status": "authenticated",
            "active_language": "German",
        })
        result = before_model_callback(ctx, llm_request=MagicMock())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        # German greeting must be in German
        assert "northwind" in text.lower()
        assert "atlas" in text.lower()
        # Should not use the English greeting text
        assert "hello" not in text.lower()

    def test_english_greeting_when_active_language_english_explicit(self):
        """active_language = 'English' explicitly → English greeting."""
        ctx = _session_start_ctx(state={
            "auth_status": "authenticated",
            "active_language": "English",
        })
        result = before_model_callback(ctx, llm_request=MagicMock())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "hello" in text.lower()


# =============================================================================
# Session-start + unauthenticated (no-op)
# =============================================================================

class TestGreetingSkippedWhenUnauthenticated:
    """Greeting is not returned when auth_status != 'authenticated'."""

    def test_unauthenticated_returns_none(self):
        """Unauthenticated at session start → None (LLM handles PIN prompt)."""
        ctx = _session_start_ctx(state={"auth_status": "unauthenticated"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_missing_auth_status_returns_none(self):
        """Missing auth_status → treated as not authenticated → None."""
        ctx = _session_start_ctx(state={})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None


# =============================================================================
# Non-session-start (no-op)
# =============================================================================

class TestGreetingSkippedOnNormalTurns:
    """Greeting is not returned on subsequent (non-session-start) turns."""

    def test_normal_message_returns_none(self):
        """Regular user message (not session start) → None."""
        ctx = _normal_turn_ctx(state={"auth_status": "authenticated"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_empty_message_returns_none(self):
        """Empty user message → None."""
        ctx = _normal_turn_ctx(state={"auth_status": "authenticated"}, text="")
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_partial_session_start_text_returns_none(self):
        """Text that contains 'session start' but not the exact sentinel → None."""
        ctx = _normal_turn_ctx(
            state={"auth_status": "authenticated"},
            text="I want to start a session",
        )
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None
