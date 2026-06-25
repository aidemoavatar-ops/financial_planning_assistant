"""
Callback Tests — before_agent_callback (Root Agent)

Tests the combined auth_init + account_snapshot_init callback.

WHAT THIS TESTS:
    Phase 1 (auth_init):
        - Correct PIN sets auth_status = "authenticated"
        - Wrong PIN sets auth_status = "unauthenticated"
        - Guard: already-set auth_status is not overwritten on re-entry

    Phase 2 (account_snapshot_init):
        - Skipped entirely when unauthenticated
        - Skipped when account_snapshot already populated (guard)
        - Skipped when customer_id is missing → sets account_snapshot_failed flag
        - Calls retrieve_account_snapshot on success path
        - Writes account_snapshot to state on API success
        - Sets account_snapshot_failed on API error response
        - Sets account_snapshot_failed on exception

RUNNING:
    pytest evals/callback_tests/tests/ -v
"""

import sys
import os
from unittest.mock import MagicMock
import json

# -------------------------------------------------------------------------
# MOCK INJECTION: Must happen BEFORE importing python_code.
# The GECX runtime provides a 'tools' global that doesn't exist in test env.
# -------------------------------------------------------------------------
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "before_agent_callbacks", "before_agent",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from python_code import before_agent_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part  # noqa: E402

_MOCK_PIN = "atlas-test-pin-v1"
_WRONG_PIN = "wrong-pin"


def _make_ctx(state):
    ctx = CallbackContext(state=state)
    return ctx


# =============================================================================
# Phase 1: auth_init
# =============================================================================

class TestAuthInit:
    """Tests for the auth_init phase (PIN comparison and auth_status derivation)."""

    def test_correct_pin_sets_authenticated(self):
        """Correct PIN → auth_status = 'authenticated'."""
        ctx = _make_ctx({"customer_pin": _MOCK_PIN})
        result = before_agent_callback(ctx)
        assert ctx.state["auth_status"] == "authenticated"

    def test_correct_pin_sets_attempt_count_zero(self):
        """Correct PIN → auth_attempt_count = '0'."""
        ctx = _make_ctx({"customer_pin": _MOCK_PIN})
        before_agent_callback(ctx)
        assert ctx.state["auth_attempt_count"] == "0"

    def test_wrong_pin_sets_unauthenticated(self):
        """Wrong PIN → auth_status = 'unauthenticated'."""
        ctx = _make_ctx({"customer_pin": _WRONG_PIN})
        before_agent_callback(ctx)
        assert ctx.state["auth_status"] == "unauthenticated"

    def test_wrong_pin_sets_attempt_count_zero(self):
        """Wrong PIN → auth_attempt_count = '0' (initial attempt)."""
        ctx = _make_ctx({"customer_pin": _WRONG_PIN})
        before_agent_callback(ctx)
        assert ctx.state["auth_attempt_count"] == "0"

    def test_missing_pin_treated_as_wrong(self):
        """Missing customer_pin → unauthenticated (empty string != mock PIN)."""
        ctx = _make_ctx({})
        before_agent_callback(ctx)
        assert ctx.state["auth_status"] == "unauthenticated"

    def test_auth_status_guard_prevents_overwrite(self):
        """Re-entry guard: if auth_status already set, it is NOT overwritten."""
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_pin": _WRONG_PIN,  # different PIN — would flip to unauthenticated if no guard
            "customer_id": "",
        })
        before_agent_callback(ctx)
        # Must remain authenticated — guard fired
        assert ctx.state["auth_status"] == "authenticated"

    def test_callback_returns_none(self):
        """before_agent_callback always returns None (never blocks the agent)."""
        ctx = _make_ctx({"customer_pin": _MOCK_PIN, "customer_id": ""})
        result = before_agent_callback(ctx)
        assert result is None


# =============================================================================
# Phase 2: account_snapshot_init
# =============================================================================

class TestAccountSnapshotInitSkipped:
    """Tests for early-return conditions that skip account snapshot retrieval."""

    def test_unauthenticated_skips_snapshot(self):
        """Unauthenticated session: snapshot phase is skipped entirely."""
        python_code.tools.reset_mock()
        ctx = _make_ctx({"customer_pin": _WRONG_PIN})
        before_agent_callback(ctx)
        python_code.tools.retrieve_account_snapshot.assert_not_called()
        assert "account_snapshot" not in ctx.state

    def test_already_loaded_snapshot_skips_retrieval(self):
        """If account_snapshot already in state, retrieval is not repeated."""
        python_code.tools.reset_mock()
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "account_snapshot": '{"checking_balance": "5000"}',
            "customer_id": "cust-123",
        })
        before_agent_callback(ctx)
        python_code.tools.retrieve_account_snapshot.assert_not_called()
        # Existing snapshot must be preserved
        assert ctx.state["account_snapshot"] == '{"checking_balance": "5000"}'

    def test_missing_customer_id_sets_failed_flag(self):
        """Missing customer_id → account_snapshot_failed = 'true', no API call."""
        python_code.tools.reset_mock()
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "",
        })
        before_agent_callback(ctx)
        python_code.tools.retrieve_account_snapshot.assert_not_called()
        assert ctx.state.get("account_snapshot_failed") == "true"
        assert ctx.state.get("account_snapshot_fail_reason") == "customer_id missing"

    def test_absent_customer_id_key_sets_failed_flag(self):
        """Absent customer_id key → treated same as empty string."""
        python_code.tools.reset_mock()
        ctx = _make_ctx({"auth_status": "authenticated"})
        before_agent_callback(ctx)
        python_code.tools.retrieve_account_snapshot.assert_not_called()
        assert ctx.state.get("account_snapshot_failed") == "true"


class TestAccountSnapshotInitSuccess:
    """Tests for the successful snapshot retrieval path."""

    def _mock_success(self, snapshot_data=None):
        if snapshot_data is None:
            snapshot_data = {"checking_balance": 1000.0, "savings_accounts": []}
        python_code.tools.reset_mock()
        python_code.tools.retrieve_account_snapshot.return_value = {
            "status": "success",
            "snapshot": snapshot_data,
        }

    def test_successful_retrieval_writes_snapshot(self):
        """Successful API call → account_snapshot written to state as JSON string."""
        snapshot = {"checking_balance": 5000.0}
        self._mock_success(snapshot)
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-001",
        })
        before_agent_callback(ctx)
        assert "account_snapshot" in ctx.state
        loaded = json.loads(ctx.state["account_snapshot"])
        assert loaded["checking_balance"] == 5000.0

    def test_retrieve_called_with_customer_id(self):
        """retrieve_account_snapshot is called with the customer_id from state."""
        self._mock_success()
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-xyz",
        })
        before_agent_callback(ctx)
        python_code.tools.retrieve_account_snapshot.assert_called_once_with(customer_id="cust-xyz")

    def test_failed_flag_not_set_on_success(self):
        """Successful retrieval: account_snapshot_failed NOT set."""
        self._mock_success()
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-001",
        })
        before_agent_callback(ctx)
        assert ctx.state.get("account_snapshot_failed") != "true"


class TestAccountSnapshotInitFailure:
    """Tests for error paths in snapshot retrieval."""

    def test_api_error_status_sets_failed_flag(self):
        """API returns error status → account_snapshot_failed = 'true'."""
        python_code.tools.retrieve_account_snapshot.return_value = {
            "status": "error",
            "error": "account not found",
        }
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-bad",
        })
        before_agent_callback(ctx)
        assert ctx.state.get("account_snapshot_failed") == "true"
        assert ctx.state.get("account_snapshot_fail_reason") == "account not found"

    def test_api_exception_sets_failed_flag(self):
        """API raises exception → account_snapshot_failed = 'true', reason is exception str."""
        python_code.tools.retrieve_account_snapshot.side_effect = RuntimeError("timeout")
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-timeout",
        })
        before_agent_callback(ctx)
        assert ctx.state.get("account_snapshot_failed") == "true"
        assert "timeout" in ctx.state.get("account_snapshot_fail_reason", "")
        # Reset side_effect so it doesn't bleed into other tests
        python_code.tools.retrieve_account_snapshot.side_effect = None

    def test_api_failure_does_not_write_snapshot(self):
        """API failure: account_snapshot must NOT be written to state."""
        python_code.tools.retrieve_account_snapshot.return_value = {
            "status": "error",
            "error": "server error",
        }
        ctx = _make_ctx({
            "auth_status": "authenticated",
            "customer_id": "cust-err",
        })
        before_agent_callback(ctx)
        assert "account_snapshot" not in ctx.state
