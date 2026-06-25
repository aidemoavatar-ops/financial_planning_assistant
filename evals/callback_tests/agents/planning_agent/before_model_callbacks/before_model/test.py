"""
Callback Tests — before_model_callback (Planning Agent: trigger_handler)

Tests the trigger_handler callback on planning_agent.

This is the same trigger pattern as root_agent's trigger_handler (before_model_2),
required to exist on ALL agents so escalation triggers set during planning sessions
are intercepted here without needing to return to root_agent.

WHAT THIS TESTS:
    No-op path:
        - No trigger → None
        - Empty trigger → None

    escalate_to_advisor trigger:
        - Clears trigger
        - Calls generate_advisor_handoff_summary with open_question
        - Returns farewell text + end_session(session_escalated=True)
        - Survives generate_advisor_handoff_summary exception

    end_session_clean trigger:
        - Clears trigger
        - Returns farewell text + end_session(session_escalated=False, reason='clean_close')
        - Does not call generate_advisor_handoff_summary

    Unknown trigger:
        - Clears trigger
        - Returns None

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
    "..", "..", "..", "..", "agents", "planning_agent",
    "before_model_callbacks", "before_model",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import before_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402


def _ctx(state):
    ctx = CallbackContext(state=state)
    ctx.user_content = Content(role="user", parts=[Part(text="Show me my options")])
    return ctx


# =============================================================================
# No-op path
# =============================================================================

class TestNoOp:
    """No trigger set → callback returns None."""

    def test_no_trigger_key_returns_none(self):
        ctx = _ctx({})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_empty_trigger_returns_none(self):
        ctx = _ctx({"_action_trigger": ""})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_no_op_does_not_call_tools(self):
        python_code.tools.reset_mock()
        ctx = _ctx({"_action_trigger": ""})
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_not_called()


# =============================================================================
# escalate_to_advisor
# =============================================================================

class TestEscalateToAdvisor:
    """escalate_to_advisor trigger fires advisor handoff for planning_agent."""

    def _escalate_ctx(self, **extra):
        python_code.tools.reset_mock()
        python_code.tools.generate_advisor_handoff_summary.return_value = {}
        state = {
            "_action_trigger": "escalate_to_advisor",
            "_escalation_open_question": "Should I pay off my car loan first?",
            **extra,
        }
        return _ctx(state)

    def test_returns_response(self):
        result = before_model_callback(self._escalate_ctx(), llm_request=MagicMock())
        assert result is not None

    def test_clears_trigger(self):
        ctx = self._escalate_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""

    def test_calls_handoff_summary_with_open_question(self):
        ctx = self._escalate_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_called_once_with(
            open_question="Should I pay off my car loan first?"
        )

    def test_response_includes_text(self):
        result = before_model_callback(self._escalate_ctx(), llm_request=MagicMock())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_response_includes_end_session(self):
        result = before_model_callback(self._escalate_ctx(), llm_request=MagicMock())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_end_session_escalated_true(self):
        result = before_model_callback(self._escalate_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("session_escalated") is True

    def test_end_session_reason_advisor_transfer(self):
        result = before_model_callback(self._escalate_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("reason") == "advisor_transfer"

    def test_handoff_exception_does_not_crash(self):
        python_code.tools.generate_advisor_handoff_summary.side_effect = RuntimeError("timeout")
        ctx = _ctx({"_action_trigger": "escalate_to_advisor"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is not None
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end
        python_code.tools.generate_advisor_handoff_summary.side_effect = None

    def test_uses_default_open_question_when_missing(self):
        python_code.tools.reset_mock()
        python_code.tools.generate_advisor_handoff_summary.return_value = {}
        ctx = _ctx({"_action_trigger": "escalate_to_advisor"})
        before_model_callback(ctx, llm_request=MagicMock())
        call_kwargs = python_code.tools.generate_advisor_handoff_summary.call_args.kwargs
        assert len(call_kwargs.get("open_question", "")) > 0


# =============================================================================
# end_session_clean
# =============================================================================

class TestEndSessionClean:
    """end_session_clean trigger fires clean close."""

    def _clean_ctx(self):
        python_code.tools.reset_mock()
        return _ctx({"_action_trigger": "end_session_clean"})

    def test_returns_response(self):
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        assert result is not None

    def test_clears_trigger(self):
        ctx = self._clean_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""

    def test_response_includes_text(self):
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        texts = [p.text for p in result.content.parts if getattr(p, "text", None)]
        assert len(texts) > 0

    def test_response_includes_end_session(self):
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        has_end = any(p.has_function_call("end_session") for p in result.content.parts)
        assert has_end

    def test_end_session_escalated_false(self):
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("session_escalated") is False

    def test_end_session_reason_clean_close(self):
        result = before_model_callback(self._clean_ctx(), llm_request=MagicMock())
        end_part = next(p for p in result.content.parts if p.has_function_call("end_session"))
        assert end_part.function_call.args.get("reason") == "clean_close"

    def test_does_not_call_handoff_summary(self):
        ctx = self._clean_ctx()
        before_model_callback(ctx, llm_request=MagicMock())
        python_code.tools.generate_advisor_handoff_summary.assert_not_called()


# =============================================================================
# Unknown trigger
# =============================================================================

class TestUnknownTrigger:
    """Unknown trigger value is cleared and returns None."""

    def test_unknown_trigger_returns_none(self):
        ctx = _ctx({"_action_trigger": "unknown_value"})
        result = before_model_callback(ctx, llm_request=MagicMock())
        assert result is None

    def test_unknown_trigger_clears_trigger(self):
        ctx = _ctx({"_action_trigger": "unknown_value"})
        before_model_callback(ctx, llm_request=MagicMock())
        assert ctx.state["_action_trigger"] == ""
