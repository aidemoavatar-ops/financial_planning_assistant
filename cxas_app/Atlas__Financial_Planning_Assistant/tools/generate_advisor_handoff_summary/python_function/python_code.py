"""
generate_advisor_handoff_summary — Advisor Handoff Context Tool

PURPOSE:
    Assembles a structured summary to transfer to a licensed human advisor.
    Includes: identity-verified status, discovery answers, any framing discussed,
    and the open question or regulated-advice boundary that triggered escalation.

    Called by the trigger_handler before_model_callback when _action_trigger is
    set to 'escalate_to_advisor'. The callback calls this tool directly, then
    returns the farewell text + end_session deterministically.

    IMPORTANT: Never include customer_pin in the summary.

TODO:
    Replace stub advisor routing call with real advisor routing/calendar system API.
    API endpoint and authentication method are TBD.
    See tdd.md Known Issues: "Advisor routing/calendar system API unspecified."

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
"""

import json


def generate_advisor_handoff_summary(open_question: str) -> dict:
    """Assemble a structured handoff summary for the receiving licensed advisor.

    Reads discovery_state and account context from session state. The advisor
    receives this summary so the customer does not need to repeat themselves.
    customer_pin is never included.

    Args:
        open_question: The specific question, request, or regulated-advice boundary
            that triggered the escalation to a licensed advisor. Be specific — this
            is what the advisor needs to address first. Example: "Customer asked which
            specific fund to invest their EUR 8,500 surplus in." (REQUIRED)

    Returns:
        dict with:
            'status' (str): 'success' or 'error'.
            'summary' (dict): Structured handoff context for the advisor:
                'identity_verified' (bool): Whether auth_status is 'authenticated',
                'customer_id' (str): Customer identifier (not the PIN),
                'discovery_answers' (dict): Goals, time horizon, safety net, highest-cost debt,
                'open_question' (str): The specific question or boundary that triggered escalation,
                'active_language' (str): Language the customer was using.
            'agent_action' (str): Instruction confirming the summary is ready.
            'error' (str): On error.
    """
    if not open_question:
        return {
            "status": "error",
            "error": "open_question is required — describe what triggered the escalation.",
            "agent_action": "Provide the specific question or boundary that triggered the advisor escalation."
        }

    auth_status = context.state.get("auth_status", "unauthenticated")
    customer_id = context.state.get("customer_id", "")
    active_language = context.state.get("active_language", "English")

    # Parse discovery_state if available
    discovery_raw = context.state.get("discovery_state", "")
    discovery_answers = {}
    if discovery_raw:
        try:
            discovery_answers = json.loads(discovery_raw)
        except Exception:
            discovery_answers = {"raw": discovery_raw}

    summary = {
        "identity_verified": auth_status == "authenticated",
        "customer_id": customer_id,
        "discovery_answers": {
            "goals": discovery_answers.get("goals", "Not collected"),
            "time_horizon": discovery_answers.get("time_horizon", "Not collected"),
            "emergency_fund_status": discovery_answers.get("emergency_fund_status", "Not collected"),
            "highest_cost_debt": discovery_answers.get("highest_cost_debt", "Not collected"),
            "discovery_complete": discovery_answers.get("discovery_complete", False)
        },
        "open_question": open_question,
        "active_language": active_language
    }

    # TODO: Call advisor routing/calendar system API to initiate the transfer.
    # Endpoint: TBD. Authentication: TBD. Confirm API spec before implementing.
    # The routing system should receive the summary and assign an available advisor.

    return {
        "status": "success",
        "summary": summary,
        "agent_action": (
            "Advisor handoff summary generated. "
            "Now deliver the farewell message to the customer and transfer them to the licensed advisor. "
            "The advisor will receive the full context summary."
        )
    }
