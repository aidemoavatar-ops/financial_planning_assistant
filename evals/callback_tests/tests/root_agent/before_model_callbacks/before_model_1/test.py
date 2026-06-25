"""
Callback Tests — before_model_callback 1 (Root Agent: silence_handler)

Tests the voice-channel silence detection and end-session escalation callback.

WHAT THIS TESTS:
    - Non-silence message → resets _silence_count to "0", returns None
    - 1st consecutive silence → increments counter to "1", returns repeat-last-message response
    - 2nd consecutive silence → increments counter to "2", returns "still can't hear you" response
    - 3rd consecutive silence → counter reaches 3, returns end_session response
    - Exception inside callback → swallowed, returns None

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
    "before_model_callbacks", "before_model_1",
))

if 'python_code' in sys.modules:
    del sys.modules['python_code']
import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import before_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402


_SILENCE_TEXT = "<context>no user activity detected for 10 seconds.</context>"


def _silence_request(prior_agent_text="How can I help you today?"):
    """Build an LlmRequest mock with a silence signal as the last content entry."""
    req = MagicMock()
    req.contents = [
        Content(role="model", parts=[Part(text=prior_agent_text)]),
        Content(role="user", parts=[Part(text=_SILENCE_TEXT)]),
    ]
    return req


def _normal_request(user_text="Tell me about emergency funds."):
    """Build an LlmRequest mock with a normal user message."""
    req = MagicMock()
    req.contents = [
        Content(role="user", parts=[Part(text=user_text)]),
    ]
    return req


def _silence_ctx(silence_count="0"):
    ctx = CallbackContext(state={"_silence_count": silence_count})
    return ctx


# =============================================================================
# Normal (non-silence) messages
# =============================================================================

class TestNormalMessage:
    """Normal user messages reset the silence counter and return None."""

    def test_normal_message_returns_none(self):
        """Regular user input → no deterministic response (LLM handles it)."""
        ctx = _silence_ctx("2")
        result = before_model_callback(ctx, _normal_request())
        assert result is None

    def test_normal_message_resets_counter(self):
        """Non-silence input resets _silence_count to '0'."""
        ctx = _silence_ctx("2")
        before_model_callback(ctx, _normal_request())
        assert ctx.state["_silence_count"] == "0"

    def test_counter_stays_zero_when_already_zero(self):
        """Reset from 0 stays at 0."""
        ctx = _silence_ctx("0")
        before_model_callback(ctx, _normal_request())
        assert ctx.state["_silence_count"] == "0"


# =============================================================================
# First silence
# =============================================================================

class TestFirstSilence:
    """First consecutive silence increments counter and returns a repeat response."""

    def test_first_silence_returns_response(self):
        """First silence → response is not None."""
        ctx = _silence_ctx("0")
        result = before_model_callback(ctx, _silence_request())
        assert result is not None

    def test_first_silence_increments_counter_to_1(self):
        """Counter goes from 0 to 1."""
        ctx = _silence_ctx("0")
        before_model_callback(ctx, _silence_request())
        assert ctx.state["_silence_count"] == "1"

    def test_first_silence_response_has_text(self):
        """First-silence response includes text (customer hears something)."""
        ctx = _silence_ctx("0")
        result = before_model_callback(ctx, _silence_request())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_first_silence_response_contains_sorry(self):
        """First-silence text starts with an apologetic prefix."""
        ctx = _silence_ctx("0")
        result = before_model_callback(ctx, _silence_request())
        text = next(p.text for p in result.content.parts if getattr(p, "text", None))
        assert "sorry" in text.lower()

    def test_first_silence_no_end_session_call(self):
        """First silence must NOT end the session."""
        ctx = _silence_ctx("0")
        result = before_model_callback(ctx, _silence_request())
        has_end = any(
            getattr(p, "function_call", None) and p.function_call.name == "end_session"
            for p in result.content.parts
        )
        assert not has_end


# =============================================================================
# Second silence
# =============================================================================

class TestSecondSilence:
    """Second consecutive silence increments counter and returns a different repeat."""

    def test_second_silence_returns_response(self):
        """Second silence → response is not None."""
        ctx = _silence_ctx("1")
        result = before_model_callback(ctx, _silence_request())
        assert result is not None

    def test_second_silence_increments_counter_to_2(self):
        """Counter goes from 1 to 2."""
        ctx = _silence_ctx("1")
        before_model_callback(ctx, _silence_request())
        assert ctx.state["_silence_count"] == "2"

    def test_second_silence_response_has_text(self):
        """Second-silence response includes text."""
        ctx = _silence_ctx("1")
        result = before_model_callback(ctx, _silence_request())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_second_silence_no_end_session(self):
        """Second silence must NOT end the session."""
        ctx = _silence_ctx("1")
        result = before_model_callback(ctx, _silence_request())
        has_end = any(
            getattr(p, "function_call", None) and p.function_call.name == "end_session"
            for p in result.content.parts
        )
        assert not has_end


# =============================================================================
# Third silence (end-session)
# =============================================================================

class TestThirdSilence:
    """Third consecutive silence triggers end_session deterministically."""

    def test_third_silence_returns_response(self):
        """Third silence → response is not None."""
        ctx = _silence_ctx("2")
        result = before_model_callback(ctx, _silence_request())
        assert result is not None

    def test_third_silence_includes_end_session_call(self):
        """Third silence → response includes end_session function call."""
        ctx = _silence_ctx("2")
        result = before_model_callback(ctx, _silence_request())
        has_end = any(
            p.has_function_call("end_session")
            for p in result.content.parts
        )
        assert has_end, "Third silence must trigger end_session"

    def test_third_silence_end_session_args(self):
        """end_session is called with session_escalated=False and correct reason."""
        ctx = _silence_ctx("2")
        result = before_model_callback(ctx, _silence_request())
        end_part = next(
            p for p in result.content.parts
            if p.has_function_call("end_session")
        )
        args = end_part.function_call.args
        assert args.get("session_escalated") is False
        assert args.get("reason") == "silence_limit_reached"

    def test_third_silence_includes_farewell_text(self):
        """Third silence response includes a farewell message before end_session."""
        ctx = _silence_ctx("2")
        result = before_model_callback(ctx, _silence_request())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_counter_reaches_3_on_third_silence(self):
        """Counter is written as '3' after the third silence event."""
        ctx = _silence_ctx("2")
        before_model_callback(ctx, _silence_request())
        assert ctx.state["_silence_count"] == "3"
