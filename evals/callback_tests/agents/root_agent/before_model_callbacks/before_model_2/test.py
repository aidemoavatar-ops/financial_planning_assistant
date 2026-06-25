"""
Callback Tests — before_model_callback 2 (Root Agent: trigger_handler)

Tests the deterministic action-trigger dispatch callback.

WHAT THIS TESTS:
    No-op path:
        - _action_trigger absent → None
        - _action_trigger = "" → None

    escalate_to_advisor trigger:
        - Clears _action_trigger after firing
        - Calls generate_advisor_handoff_summary with open_question
        - Returns LlmResponse with farewell text
        - Returns LlmResponse with end_session(session_escalated=True)
        - Works even when generate_advisor_handoff_summary raises an exception

    end_session_clean trigger:
        - Clears _action_trigger after firing
        - Returns LlmResponse with farewell text
        - Returns LlmResponse with end_session(session_escalated=False)

    Unknown trigger:
        - Clears _action_trigger (logged, then cleared)
        - Returns None (LLM continues)

RUNNING:
    pytest evals/callback_tests/tests/ -v
"""

import sys
import os
from unittest.mock import MagicMock, call

# -------------------------------------------------------------------------
# MOCK INJECTION: Must happen BEFORE importing python_code.
# -------------------------------------------------------------------------
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "before_model_callbacks", "before_model_2",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import before_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402


def _ctx(state):
    ctx = CallbackContext(state=state)
    ctx.user_content = Content(role="user", parts=[Part(text="Goodbye")])
    return ctx


# =============================================================================
# No-op path
# =============================================================================

class TestNoOp:
    """No trigger set → callback returns None and does not call any tools."""

    def test_no_trigger_key_returns_none(self):
        """_action_trigger key absent → None."""
        ctx = _ctx({})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_empty_trigger_returns_none(self):
        """_action_trigger = '' → None."""
        ctx = _ctx({"_action_trigger": ""})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_no_op_does_not_call_tools(self):
        """No trigger → generate_advisor_handoff_summary not called."""
        python_code.tools.reset_mock()
        ctx = _ctx({"_action_trigger": ""})
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_not_called()


# =============================================================================
# escalate_to_advisor trigger
# =============================================================================

class TestEscalateToAdvisor:
    """escalate_to_advisor trigger fires advisor handoff deterministically."""

    def _escalate_ctx(self, **extra_state):
        state = {
            "_action_trigger": "escalate_to_advisor",
            "_escalation_open_question": "Which fund should I buy?",
            **extra_state,
        }
        python_code.tools.reset_mock()
        python_code.tools.generate_advisor_handoff_summary.return_value = {}
        return _ctx(state)

    def test_returns_response(self):
        """escalate_to_advisor → response is not None."""
        ctx = self._escalate_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is not None

    def test_clears_trigger(self):
        """_action_trigger is cleared to '' after firing."""
        ctx = self._escalate_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""

    def test_calls_handoff_summary(self):
        """generate_advisor_handoff_summary is called with the open_question."""
        ctx = self._escalate_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_called_once_with(
            open_question="Which fund should I buy?"
        )

    def test_uses_default_open_question_when_missing(self):
        """Missing _escalation_open_question → uses default string."""
        ctx = _ctx({"_action_trigger": "escalate_to_advisor"})
        python_code.tools.reset_mock()
        python_code.tools.generate_advisor_handoff_summary.return_value = {}
        before_model_callback(ctx, llm_request=MagicMock())
        call_args = python_code.tools.generate_advisor_handoff_summary.call_args
        assert "open_question" in call_args.kwargs
        assert len(call_args.kwargs["open_question"]) > 0

    def test_response_includes_text(self):
        """Escalation response includes farewell text."""
        ctx = self._escalate_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_response_includes_end_session(self):
        """Escalation response includes end_session function call."""
        ctx = self._escalate_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_end_session_session_escalated_true(self):
        """end_session is called with session_escalated=True on advisor transfer."""
        ctx = self._escalate_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("session_escalated") is True

    def test_end_session_reason_advisor_transfer(self):
        """end_session reason = 'advisor_transfer'."""
        ctx = self._escalate_ctx()
        result = before_model_callback(ctx, llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("reason") == "advisor_transfer"

    def test_handoff_exception_does_not_crash(self):
        """generate_advisor_handoff_summary raises → callback still returns response."""
        python_code.tools.generate_advisor_handoff_summary.side_effect = RuntimeError("network error")
        ctx = _ctx({"_action_trigger": "escalate_to_advisor"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        # Must return a valid response despite tool failure
        assert result is not None
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end
        # Reset side_effect
        python_code.tools.generate_advisor_handoff_summary.side_effect = None


# =============================================================================
# end_session_clean trigger
# =============================================================================

class TestEndSessionClean:
    """end_session_clean trigger returns a clean-close response."""

    def _clean_ctx(self):
        python_code.tools.reset_mock()
        return _ctx({"_action_trigger": "end_session_clean"})

    def test_returns_response(self):
        """end_session_clean → response is not None."""
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        assert result is not None

    def test_clears_trigger(self):
        """_action_trigger cleared to '' after end_session_clean."""
        ctx = self._clean_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""

    def test_response_includes_text(self):
        """Clean-close response includes farewell text."""
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_response_includes_end_session(self):
        """Clean-close response includes end_session function call."""
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_end_session_session_escalated_false(self):
        """Clean close: end_session called with session_escalated=False."""
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("session_escalated") is False

    def test_end_session_reason_clean_close(self):
        """Clean close: end_session reason = 'clean_close'."""
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("reason") == "clean_close"

    def test_clean_close_does_not_call_handoff_summary(self):
        """end_session_clean does NOT call generate_advisor_handoff_summary."""
        ctx = self._clean_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_not_called()


# =============================================================================
# Unknown trigger
# =============================================================================

class TestUnknownTrigger:
    """Unknown trigger value: log and return None; always clear the trigger."""

    def test_unknown_trigger_returns_none(self):
        """Unknown trigger value → None (LLM continues normally)."""
        ctx = _ctx({"_action_trigger": "some_unknown_action"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_unknown_trigger_clears_trigger(self):
        """Unknown trigger: _action_trigger is still cleared to prevent loops."""
        ctx = _ctx({"_action_trigger": "some_unknown_action"})
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""
