"""
Callback Tests — after_model_callback 1 (Guardrail Agent: guardrail_logger)

Tests the observability logging callback that records every guardrail refusal.

WHAT THIS TESTS:
    No-op path (is_guardrail_event = False):
        - Normal LLM response with no end_session and no refusal text → None, no log written
        - Text does not contain any refusal keywords → no log written

    Logging path (is_guardrail_event = True):
        - end_session in response → log entry written to guardrail_trigger_log
        - Refusal text ("licensed advisor") → log entry written
        - Log entry contains required fields: timestamp, guardrail_type, triggering_intent, session_escalated
        - New entry appended to existing log (not overwritten)
        - Malformed existing log handled gracefully (reset to empty list)
        - session_escalated = True when end_session present
        - session_escalated = False when only refusal text (no end_session)
        - guardrail_type classification: specific_security_fund, suitability_kyc, tax_legal,
          return_prediction, general_regulated_advice (default)

    Return value:
        - Callback always returns None (never modifies the LLM response — observability only)

RUNNING:
    pytest evals/callback_tests/tests/ -v
"""

import sys
import os
import json
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
    "..", "..", "..", "..", "agents", "guardrail_agent",
    "after_model_callbacks", "after_model_1",
))

if 'python_code' in sys.modules:
    del sys.modules['python_code']
import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import after_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402


def _build_response(text="", has_end_session=False):
    """Build a minimal LlmResponse mock."""
    resp = MagicMock()
    parts = []

    if text:
        text_part = MagicMock()
        text_part.has_function_call = lambda name: False
        text_part.text_or_transcript = lambda: text
        parts.append(text_part)

    if has_end_session:
        end_part = MagicMock()
        end_part.has_function_call = lambda name: name == "end_session"
        end_part.text_or_transcript = lambda: None
        parts.append(end_part)

    resp.content = MagicMock()
    resp.content.parts = parts
    return resp


def _ctx(state=None):
    return CallbackContext(state=state or {})


def _read_log(ctx):
    """Parse guardrail_trigger_log from state."""
    raw = ctx.state.get("guardrail_trigger_log", "[]")
    return json.loads(raw)


# =============================================================================
# No-op path
# =============================================================================

class TestNoOp:
    """Normal LLM responses that are not guardrail events → no log written, return None."""

    def test_normal_response_returns_none(self):
        """Plain LLM text with no guardrail indicators → None."""
        ctx = _ctx()
        result = after_model_callback(ctx, _build_response(text="An emergency fund covers 3-6 months of expenses."))
        assert result is None

    def test_normal_response_does_not_write_log(self):
        """Non-guardrail response must not write to guardrail_trigger_log."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(text="An emergency fund covers 3-6 months of expenses."))
        assert ctx.state.get("guardrail_trigger_log") is None

    def test_empty_response_returns_none(self):
        """Empty response → None."""
        ctx = _ctx()
        result = after_model_callback(ctx, _build_response(text=""))
        assert result is None


# =============================================================================
# Logging path — end_session trigger
# =============================================================================

class TestLoggingOnEndSession:
    """Responses containing end_session are treated as guardrail events and logged."""

    def test_end_session_triggers_log(self):
        """end_session in response → log entry written."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(has_end_session=True))
        log = _read_log(ctx)
        assert len(log) == 1

    def test_end_session_log_has_timestamp(self):
        """Log entry must have a 'timestamp' field."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(has_end_session=True))
        entry = _read_log(ctx)[0]
        assert "timestamp" in entry
        assert len(entry["timestamp"]) > 0

    def test_end_session_log_has_guardrail_type(self):
        """Log entry must have a 'guardrail_type' field."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(has_end_session=True))
        entry = _read_log(ctx)[0]
        assert "guardrail_type" in entry

    def test_end_session_log_has_triggering_intent(self):
        """Log entry must have a 'triggering_intent' field."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(has_end_session=True))
        entry = _read_log(ctx)[0]
        assert "triggering_intent" in entry

    def test_end_session_log_session_escalated_true(self):
        """session_escalated = True when end_session is present."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(has_end_session=True))
        entry = _read_log(ctx)[0]
        assert entry["session_escalated"] is True

    def test_logging_returns_none(self):
        """Callback always returns None — observability only, never modifies response."""
        ctx = _ctx()
        result = after_model_callback(ctx, _build_response(has_end_session=True))
        assert result is None


# =============================================================================
# Logging path — refusal text trigger (no end_session)
# =============================================================================

class TestLoggingOnRefusalText:
    """Responses containing refusal language are logged even without end_session."""

    def test_licensed_advisor_phrase_triggers_log(self):
        ctx = _ctx()
        after_model_callback(ctx, _build_response(
            text="This requires a licensed advisor — I cannot provide that guidance."
        ))
        log = _read_log(ctx)
        assert len(log) == 1

    def test_cannot_advise_phrase_triggers_log(self):
        ctx = _ctx()
        after_model_callback(ctx, _build_response(text="I cannot advise on specific fund selection."))
        log = _read_log(ctx)
        assert len(log) == 1

    def test_outside_atlas_phrase_triggers_log(self):
        ctx = _ctx()
        after_model_callback(ctx, _build_response(text="That falls outside what Atlas can advise on."))
        log = _read_log(ctx)
        assert len(log) == 1

    def test_refusal_without_end_session_session_escalated_false(self):
        """Refusal text without end_session → session_escalated = False."""
        ctx = _ctx()
        after_model_callback(ctx, _build_response(
            text="This requires a licensed financial advisor."
        ))
        entry = _read_log(ctx)[0]
        assert entry["session_escalated"] is False


# =============================================================================
# Log accumulation
# =============================================================================

class TestLogAccumulation:
    """New log entries are appended to the existing list."""

    def test_second_entry_appended(self):
        """Second guardrail event appends to existing log."""
        ctx = _ctx(state={
            "guardrail_trigger_log": json.dumps([{
                "timestamp": "2026-06-24T00:00:00+00:00",
                "guardrail_type": "specific_security_fund",
                "triggering_intent": "first event",
                "session_escalated": False,
            }])
        })
        after_model_callback(ctx, _build_response(text="This requires a licensed advisor."))
        log = _read_log(ctx)
        assert len(log) == 2

    def test_malformed_log_reset_to_empty(self):
        """Malformed existing log JSON → reset to empty list, entry still appended."""
        ctx = _ctx(state={"guardrail_trigger_log": "not-valid-json"})
        after_model_callback(ctx, _build_response(text="requires a licensed financial advisor."))
        log = _read_log(ctx)
        assert len(log) == 1

    def test_non_list_log_reset(self):
        """Existing log that is a dict (not list) → reset and append."""
        ctx = _ctx(state={"guardrail_trigger_log": json.dumps({"unexpected": "structure"})})
        after_model_callback(ctx, _build_response(text="outside what atlas can advise on."))
        log = _read_log(ctx)
        assert isinstance(log, list)
        assert len(log) == 1


# =============================================================================
# guardrail_type classification
# =============================================================================

class TestGuardrailTypeClassification:
    """Response text is classified into the correct guardrail category."""

    def _get_guardrail_type(self, text, has_end_session=False):
        ctx = _ctx()
        after_model_callback(ctx, _build_response(text=text, has_end_session=has_end_session))
        log = _read_log(ctx)
        if not log:
            return None
        return log[0]["guardrail_type"]

    def test_fund_keyword_classified_as_specific_security_fund(self):
        gt = self._get_guardrail_type("I cannot advise on which fund to buy.")
        assert gt == "specific_security_fund"

    def test_suitability_keyword_classified_correctly(self):
        gt = self._get_guardrail_type(
            "This requires a licensed advisor. Suitability assessments are out of scope.",
            has_end_session=True,
        )
        assert gt == "suitability_kyc"

    def test_tax_keyword_classified_as_tax_legal(self):
        gt = self._get_guardrail_type(
            "I cannot advise on tax deductions — this requires a licensed advisor.",
            has_end_session=True,
        )
        assert gt == "tax_legal"

    def test_return_prediction_keyword_classified_correctly(self):
        gt = self._get_guardrail_type(
            "I cannot make a return prediction for any investment.",
            has_end_session=True,
        )
        assert gt == "return_prediction"

    def test_generic_refusal_classified_as_general(self):
        gt = self._get_guardrail_type(
            "This falls outside what Atlas can advise on — please speak with a licensed financial advisor."
        )
        assert gt == "general_regulated_advice"
