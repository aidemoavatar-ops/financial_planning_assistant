"""
Callback Tests — after_model_callback 0 (Guardrail Agent: farewell_injection)

Tests the farewell-injection callback on guardrail_agent.

Same behavioral pattern as root_agent's farewell_injection — prevents silent
end_session calls in the guardrail flow (warm handoff + clean close). Uses
guardrail-specific farewell text that references the licensed advisor.

WHAT THIS TESTS:
    No-op paths:
        - Response has no end_session → None
        - Response has end_session AND text in same call → None
        - Response has end_session but agent already spoke earlier in turn → None

    Injection path:
        - end_session with no text anywhere in turn → inject farewell
        - Farewell text comes before end_session in injected response
        - English farewell by default
        - German farewell when active_language = 'German'
        - Injected response preserves the original end_session call

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
    "..", "..", "..", "..", "agents", "guardrail_agent",
    "after_model_callbacks", "after_model_0",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import after_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part, LlmResponse  # noqa: E402


def _llm_response_end_session_only():
    """LLM emitted end_session with no text."""
    return LlmResponse.from_parts(parts=[
        Part.from_end_session(reason="advisor_transfer"),
    ])


def _llm_response_end_session_with_text():
    """LLM emitted text AND end_session in the same model call."""
    return LlmResponse.from_parts(parts=[
        Part.from_text(text="I'm connecting you now."),
        Part.from_end_session(reason="advisor_transfer"),
    ])


def _llm_response_no_end_session():
    """Normal LLM response with only text."""
    return LlmResponse.from_parts(parts=[
        Part.from_text(text="This falls outside what Atlas can advise on."),
    ])


def _ctx_no_prior_agent_text(state=None):
    """Context with no prior agent text in this turn."""
    ctx = CallbackContext(state=state or {})
    user_event = MagicMock()
    user_event.is_user.return_value = True
    user_event.is_agent.return_value = False
    ctx.events = [user_event]
    return ctx


def _ctx_with_prior_agent_text(state=None):
    """Context where agent already spoke earlier in this turn."""
    ctx = CallbackContext(state=state or {})

    prior_text_part = MagicMock()
    prior_text_part.text_or_transcript = lambda: "Let me transfer you to an advisor."

    agent_event = MagicMock()
    agent_event.is_user.return_value = False
    agent_event.is_agent.return_value = True
    agent_event.parts = lambda: [prior_text_part]

    user_event = MagicMock()
    user_event.is_user.return_value = True
    user_event.is_agent.return_value = False

    ctx.events = [user_event, agent_event]
    return ctx


# =============================================================================
# No-op paths
# =============================================================================

class TestNoOp:
    """Callback returns None when farewell injection is not needed."""

    def test_no_end_session_returns_none(self):
        """No end_session in response → pass-through."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_no_end_session())
        assert result is None

    def test_end_session_with_text_returns_none(self):
        """LLM already included text with end_session → no injection needed."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_with_text())
        assert result is None

    def test_prior_agent_text_returns_none(self):
        """Agent already spoke in this turn → do not double-inject farewell."""
        ctx = _ctx_with_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_only())
        assert result is None


# =============================================================================
# Injection path
# =============================================================================

class TestFarewellInjection:
    """Farewell is injected when end_session appears alone with no turn text."""

    def test_injection_returns_response(self):
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_only())
        assert result is not None

    def test_injected_response_contains_text(self):
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_only())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_injected_response_preserves_end_session(self):
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_only())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_farewell_text_before_end_session(self):
        """Text part appears before end_session part in the injected response."""
        ctx = _ctx_no_prior_agent_text()
        result = after_model_callback(ctx, _llm_response_end_session_only())
        parts = result.content.parts
        text_indices = [i for i, p in enumerate(parts) if getattr(p, "text", None)]
        end_indices = [i for i, p in enumerate(parts) if p.has_function_call("end_session")]
        assert text_indices and end_indices
        assert min(text_indices) < min(end_indices)

    def test_english_farewell_by_default(self):
        """Default language → English farewell text."""
        ctx = _ctx_no_prior_agent_text(state={})
        result = after_model_callback(ctx, _llm_response_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "thank you" in text.lower() or "northwind" in text.lower()

    def test_guardrail_farewell_references_advisor(self):
        """Guardrail-specific farewell mentions the licensed advisor."""
        ctx = _ctx_no_prior_agent_text(state={})
        result = after_model_callback(ctx, _llm_response_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "advisor" in text.lower()

    def test_german_farewell_when_active_language_german(self):
        """active_language = 'German' → German farewell."""
        ctx = _ctx_no_prior_agent_text(state={"active_language": "German"})
        result = after_model_callback(ctx, _llm_response_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "vielen dank" in text.lower()

    def test_english_farewell_when_active_language_english(self):
        """active_language = 'English' explicitly → English farewell."""
        ctx = _ctx_no_prior_agent_text(state={"active_language": "English"})
        result = after_model_callback(ctx, _llm_response_end_session_only())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "thank you" in text.lower()
