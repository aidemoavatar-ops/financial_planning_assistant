"""
before_agent_callback — Root Agent (auth_init + account_snapshot_init)

PURPOSE:
    Combined auth_init and account_snapshot_init callback. Runs once per session
    at the first agent invocation (guarded by early-return checks).

    1. auth_init: Reads customer_pin from session state and compares to the
       hardcoded mock PIN. Writes auth_status ("authenticated" or "unauthenticated")
       and auth_attempt_count. Runs before any LLM call, before identity disclosure,
       and before account retrieval.

    2. account_snapshot_init: If auth_status is "authenticated" and account_snapshot
       is not yet populated, calls retrieve_account_snapshot using customer_id.
       Writes result to account_snapshot. If customer_id is missing or API fails,
       sets a flag so root_agent operates in education-only mode.

DESIGN NOTE:
    auth_init and account_snapshot_init are combined into a single before_agent_callback
    to guarantee auth_init always runs first. Platform callback ordering within the same
    array is sequential, but combining them into one function eliminates any ordering
    ambiguity entirely.

CRITICAL:
    before_agent_callback fires on EVERY agent turn, not just at session start.
    auth_init re-runs on every turn while unauthenticated — this is intentional:
    the LLM updates customer_pin via set_session_state on each retry, and the
    callback picks up the new value to re-evaluate. Once authenticated, the guard
    skips auth_init permanently (one-way door). account_snapshot_init is still
    guarded to run only once.

PLATFORM GLOBALS:
    CallbackContext, Content, Part are auto-provided. Do NOT import them.
    Only standard library imports need explicit import statements.
"""

from typing import Optional

# v1 mock PIN. Replace with real auth API call when available.
# See tdd.md Known Issues: "Auth API (v1 mock)".
_MOCK_PIN = "atlas-test-pin-v1"


def before_agent_callback(callback_context: CallbackContext) -> Optional[Content]:
    state = callback_context.state

    # =========================================================================
    # PHASE 1: auth_init
    # Guard: skip only when already authenticated (one-way door).
    # Re-evaluates on every unauthenticated turn so PIN retries take effect
    # after the LLM updates customer_pin via set_session_state.
    # =========================================================================
    if state.get("auth_status") != "authenticated":
        customer_pin = state.get("customer_pin", "")

        if customer_pin == _MOCK_PIN:
            state["auth_status"] = "authenticated"
        else:
            state["auth_status"] = "unauthenticated"
            if not state.get("auth_attempt_count"):
                state["auth_attempt_count"] = "0"

    # =========================================================================
    # PHASE 2: account_snapshot_init
    # Only runs if authenticated and snapshot not yet loaded.
    # Guard: if account_snapshot already set, skip.
    # =========================================================================
    if state.get("auth_status") != "authenticated":
        return None

    if state.get("account_snapshot"):
        return None  # already loaded

    customer_id = state.get("customer_id", "")
    if not customer_id:
        # No customer_id provided — flag for education-only mode
        state["account_snapshot_failed"] = "true"
        state["account_snapshot_fail_reason"] = "customer_id missing"
        return None

    try:
        response = tools.retrieve_account_snapshot(customer_id=customer_id)

        if response.get("status") == "success":
            import json
            snapshot = response.get("snapshot", {})
            state["account_snapshot"] = json.dumps(snapshot)
        else:
            state["account_snapshot_failed"] = "true"
            state["account_snapshot_fail_reason"] = response.get("error", "unknown error")

    except Exception as e:
        state["account_snapshot_failed"] = "true"
        state["account_snapshot_fail_reason"] = str(e)

    return None
