"""
after_model_callback 02 — Guardrail Agent (guardrail_logger)

PURPOSE:
    After a guardrail refusal fires, appends an entry to guardrail_trigger_log
    with timestamp, triggering intent category, and which guardrail boundary was hit.

    Implements PRD requirement: "Log every guardrail trigger (which guardrail,
    the triggering scenario, what the user was trying to do) to identify coverage
    gaps and tune the instruction layers above it."

DETECTION APPROACH:
    The LLM-generated refusal text is inspected for presence of key indicators
    from the guardrail_agent instruction's refusal pattern:
    - Mentions of "licensed advisor", "fund", "suitability", "tax", "return prediction"
    - Presence of end_session or escalate call signals a boundary was enforced

    NOTE: This is EXECUTION detection (logging after a guardrail fires), not
    INTENT detection (classifying user input). The guardrail_agent instruction
    handles intent classification — this callback logs the outcome.

PLATFORM GLOBALS:
    CallbackContext, LlmResponse, Part are auto-provided. Do NOT import them.
    json, datetime need explicit import.
"""


import json
from datetime import datetime, timezone
from typing import Optional


# Guardrail category phrases for classification (execution logging only — not intent detection)
_GUARDRAIL_PHRASES = {
    "specific_security_fund": ["which fund", "fund to buy", "stock", "etf", "security", "investment recommendation"],
    "suitability_kyc": ["suitability", "risk level", "right for me", "my situation", "profile"],
    "tax_legal": ["tax", "deduct", "legal", "jurisdiction", "bracket"],
    "return_prediction": ["return prediction", "market timing", "will the market", "when to sell", "predict"],
}


def _classify_guardrail_type(text: str) -> str:
    """Classify which guardrail category was triggered based on response text."""
    text_lower = text.lower()
    for category, kw_list in _GUARDRAIL_PHRASES.items():
        if any(kw in text_lower for kw in kw_list):
            return category
    return "general_regulated_advice"


def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    state = callback_context.state

    # Check if this response contains a guardrail refusal
    # Indicators: response contains end_session (advisor transfer) or refusal language
    has_end_session = any(
        part.has_function_call("end_session")
        for part in llm_response.content.parts
    )

    response_text = ""
    for part in llm_response.content.parts:
        content = part.text_or_transcript()
        if content:
            response_text += content

    # Only log if there's a guardrail-related event (end_session or refusal text)
    # Detect refusal pattern: "licensed advisor", "cannot", "outside what Atlas can"
    is_guardrail_event = has_end_session or any(
        phrase in response_text.lower()
        for phrase in [
            "licensed advisor", "licensed financial advisor",
            "outside what atlas", "cannot advise", "can't advise",
            "requires a licensed", "falls outside"
        ]
    )

    if not is_guardrail_event:
        return None

    # Build log entry
    guardrail_type = _classify_guardrail_type(response_text)
    timestamp = datetime.now(timezone.utc).isoformat()

    log_entry = {
        "timestamp": timestamp,
        "guardrail_type": guardrail_type,
        "triggering_intent": response_text[:200] if response_text else "unknown",
        "session_escalated": has_end_session
    }

    # Append to guardrail_trigger_log
    existing_log_raw = state.get("guardrail_trigger_log", "[]")
    try:
        existing_log = json.loads(existing_log_raw)
        if not isinstance(existing_log, list):
            existing_log = []
    except Exception:
        existing_log = []

    existing_log.append(log_entry)
    state["guardrail_trigger_log"] = json.dumps(existing_log)

    # Do not modify the LLM response — just log
    return None
