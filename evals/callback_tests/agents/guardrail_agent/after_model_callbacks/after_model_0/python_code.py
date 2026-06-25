"""
after_model_callback 01 — Guardrail Agent (farewell_injection)

PURPOSE:
    Detects when guardrail_agent's LLM is about to call end_session without
    producing any text, and injects a closing farewell message.

    The guardrail_agent may call end_session after a warm handoff completes.
    This ensures the customer always hears a goodbye before disconnect.

    Uses the same multi-model-call deduplication pattern as root_agent's
    farewell_injection to prevent double-text injection.

PLATFORM GLOBALS:
    CallbackContext, LlmResponse, Part are auto-provided. Do NOT import them.
"""


from typing import Optional


_FAREWELL_EN = (
    "Thank you for speaking with Atlas. "
    "A licensed Northwind advisor will be with you shortly. Have a great day!"
)

_FAREWELL_DE = (
    "Vielen Dank, dass Sie mit Atlas gesprochen haben. "
    "Ein lizenzierter Northwind-Berater wird in Kürze für Sie da sein. Auf Wiederhören!"
)


def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    state = callback_context.state

    # Step 1: Check if THIS model call contains end_session AND has no text
    has_end_session = False
    has_text_this_call = False

    for part in llm_response.content.parts:
        if part.has_function_call("end_session"):
            has_end_session = True
        else:
            content = part.text_or_transcript()
            if content and len(content.strip()) > 0:
                has_text_this_call = True

    if not has_end_session or has_text_this_call:
        return None

    # Step 2: Check if agent produced text in an earlier model call in this turn
    for event in reversed(callback_context.events):
        if event.is_user():
            break
        if event.is_agent():
            for p in event.parts():
                content = p.text_or_transcript()
                if content and len(content.strip()) > 0:
                    return None

    # Step 3: Inject farewell before end_session
    active_language = state.get("active_language", "English")
    farewell = _FAREWELL_DE if active_language == "German" else _FAREWELL_EN

    new_parts = [Part.from_text(text=farewell)]
    new_parts.extend(llm_response.content.parts)
    return LlmResponse.from_parts(parts=new_parts)
