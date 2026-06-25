"""
Callback Tests — after_model_callback (Root Agent: farewell_injection)

Tests the farewell-injection callback that prevents silent end_session calls.

WHAT THIS TESTS:
    No-op paths:
        - Response has no end_session → None (pass-through)
        - Response has end_session AND text in same call → None (no double-inject)
        - Response has end_session but agent already spoke earlier in turn → None

    Injection path:
        - Response has end_session, no text in this call, no prior agent text →
          inject farewell text before end_session parts
        - Farewell text comes before end_session part in injected response
        - English farewell by default
        - German farewell when active_language = 'German'

RUNNING:
    pytest evals/callback_tests/tests/ -v
"""

import sys
import os
from unittest.mock import MagicMock

# -------------------------------------------------------------------------
# MOCK INJECTION: Must happen BEFORE importing python_code.
# -------------------------------------------------------------------------
import builtins as _builtins
from cxas_scrapi.utils.callback_libs import (  # noqa: E402
    CallbackContext as _CC, Content as _Ct, Part as _Pt,
    LlmRequest as _LR, LlmResponse as _LRsp,
)
_builtins.CallbackContext = _CC
_builtins.Content = _Ct
_builtins.Part = _Pt
_builtins.LlmRequest = _LR
_builtins.LlmResponse = _LRsp

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "after_model_callbacks", "after_model",
))

if 'python_code' in sys.modules:
    del sys.modules['python_code']
import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import after_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part, LlmResponse  # noqa: E402


def _llm_response_with_end_session_only():
    """LLM called end_session with no text in this model call."""
    return LlmResponse.from_parts(parts=[
        Part.from_end_session(reason="session_complete"),
    ])


def _llm_response_with_end_session_and_text():
    """LLM said something AND called end_session in the same model call."""
    return LlmResponse.from_parts(parts=[
        Part.from_text(text="Goodbye and good luck!"),
        Part.from_end_session(reason="session_complete"),
    ])


def _llm_response_no_end_session():
    """Normal LLM response with only text."""
    return LlmResponse.from_parts(parts=[
        Part.from_text(text="Here's what I found."),
    ])


def _ctx_no_prior_agent_text(state=None):
    """Context where no prior agent text exists in this turn."""
    ctx = CallbackContext(state=state or {})
    # events: only a user event (no prior agent text)
    user_event = MagicMock()
    user_event.is_user.return_value = True
    user_event.is_agent.return_value = False
    ctx.events = [user_event]
    return ctx


def _ctx_with_prior_agent_text(state=None):
    """Context where agent already spoke earlier in this turn."""
    ctx = CallbackContext(state=state or {})

    prior_text_part = MagicMock()
    prior_text_part.text_or_transcript = lambda: "Let me check that for you."

    agent_event = MagicMock()
    agent_event.is_user.return_value = False
    agent_event.is_agent.return_value = True
    agent_event.parts = lambda: [prior_text_part]

    user_event = MagicMock()
    user_event.is_user.return_value = True
    user_event.is_agent.return_value = False

    # Most-recent event first in reversed iteration
    ctx.events = [user_event, agent_event]
    return ctx


# =============================================================================
# No-op paths
# =============================================================================

class TestNoOp:
    """Callback returns None when injection is not needed."""

    def test_no_end_session_returns_none(self):
        """No end_session in response → pass-through (None)."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_no_end_session())
        assert result is None

    def test_end_session_with_text_returns_none(self):
        """Response has end_session AND text → LLM already spoke, no injection needed."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_and_text())
        assert result is None

    def test_end_session_with_prior_agent_text_returns_none(self):
        """Agent spoke earlier in this turn → do not double-inject farewell."""
        ctx = _ctx_with_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        assert result is None


# =============================================================================
# Injection path
# =============================================================================

class TestFarewellInjection:
    """Farewell is injected when end_session appears with no text anywhere in the turn."""

    def test_injection_returns_response(self):
        """Injection path → response is not None."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        assert result is not None

    def test_injected_response_contains_text(self):
        """Injected response must contain farewell text."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_injected_response_preserves_end_session(self):
        """Injected response still contains the end_session call."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_farewell_text_comes_before_end_session(self):
        """Farewell text part must appear before the end_session part in the response."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        parts = result.content.parts
        text_indices = [i for i, p in enumerate(parts) if getattr(p, "text", None)]
        end_indices = [i for i, p in enumerate(parts) if p.has_function_call("end_session")]
        assert text_indices, "No text parts found"
        assert end_indices, "No end_session parts found"
        assert min(text_indices) < min(end_indices), "Text must come before end_session"

    def test_english_farewell_by_default(self):
        """active_language absent → English farewell."""
        ctx = _ctx_no_prior_agent_text(state={})
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "northwind" in text.lower()

    def test_german_farewell_when_active_language_german(self):
        """active_language = 'German' → German farewell text."""
        ctx = _ctx_no_prior_agent_text(state={"active_language": "German"})
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        # German farewell uses "Vielen Dank"
        assert "vielen dank" in text.lower()

    def test_english_farewell_when_active_language_english_explicit(self):
        """active_language = 'English' → English farewell."""
        ctx = _ctx_no_prior_agent_text(state={"active_language": "English"})
        result = after_model_callback(ctx, _llm_response_with_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "thank you" in text.lower()
