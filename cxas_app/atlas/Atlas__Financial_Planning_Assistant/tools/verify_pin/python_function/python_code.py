"""
verify_pin — PIN Verification Tool

PURPOSE:
    Verifies a PIN provided by the customer during the auth-retry flow.
    Called by root_agent when auth_status is "unauthenticated" and the customer
    has spoken their PIN.

    Sets auth_status in session state synchronously — the result is available
    immediately in the same turn without waiting for the next before_agent_callback
    cycle. Also increments auth_attempt_count.

    Root_agent must NOT separately call set_session_state for auth_attempt_count
    after calling verify_pin — this tool handles it.

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
    Do NOT add context as a function parameter.
"""


def verify_pin(pin: str = "") -> dict:
    """Verify the customer's PIN during the auth-retry flow.

    Call this when auth_status is 'unauthenticated' and the customer has
    provided a PIN. Returns the auth result immediately so root_agent can
    respond in the same turn without waiting for a callback re-evaluation.

    Args:
        pin: The PIN provided by the customer, verbatim and without spaces.

    Returns:
        dict with auth_status ('authenticated' or 'unauthenticated'),
        auth_attempt_count (updated count as string), and agent_action
        describing exactly what root_agent should do next.
    """
    _MOCK_PIN = "atlas-test-pin-v1"

    attempt = int(context.state.get("auth_attempt_count", "0") or "0") + 1
    context.state["auth_attempt_count"] = str(attempt)

    if pin == _MOCK_PIN:
        context.state["auth_status"] = "authenticated"
        return {
            "auth_status": "authenticated",
            "auth_attempt_count": str(attempt),
            "agent_action": (
                "PIN verified. Deliver the identity disclosure and proceed to "
                "the discovery conversation."
            ),
        }

    context.state["auth_status"] = "unauthenticated"
    remaining = 3 - attempt
    if remaining <= 0:
        return {
            "auth_status": "unauthenticated",
            "auth_attempt_count": str(attempt),
            "agent_action": (
                "PIN rejected after 3 attempts. Inform the customer their account "
                "is locked and call end_session immediately."
            ),
        }

    return {
        "auth_status": "unauthenticated",
        "auth_attempt_count": str(attempt),
        "agent_action": (
            f"PIN rejected. {remaining} attempt(s) remaining. "
            "Inform the customer and ask them to try again."
        ),
    }
