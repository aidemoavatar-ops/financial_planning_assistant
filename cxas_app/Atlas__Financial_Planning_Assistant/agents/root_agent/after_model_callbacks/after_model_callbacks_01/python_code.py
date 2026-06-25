"""
after_model_callback 01 — Root Agent (farewell_injection)

PURPOSE:
    Detects when the LLM is about to call end_session without producing any text,
    and injects a closing farewell message before the session terminates.

    The LLM frequently calls end_session without speaking first, causing the customer
    to hear silence before disconnect. This callback ensures the customer always hears
    a goodbye message.

MULTI-MODEL-CALL TURN HANDLING:
    A single conversational turn can span multiple model calls. This callback fires on
    EACH model call separately. We walk callback_context.events backwards to check if
    the agent already produced text earlier in this same turn — if so, we do NOT inject
    a second farewell (prevents double-text injection).

    Use text_or_transcript() instead of part.text — in audio mode the LLM produces
    audio transcripts, not plain text.

PLATFORM GLOBALS:
    CallbackContext, LlmResponse, Part are auto-provided. Do NOT import them.
"""

from typing import Optional


_FAREWELL_EN = (
    "Thank you for speaking with Atlas today. "
    "If you need anything else, Northwind is here for you. Have a great day!"
)

_FAREWELL_DE = (
    "Vielen Dank, dass Sie heute mit Atlas gesprochen haben. "
    "Wenn Sie weitere Fragen haben, stehen wir Ihnen bei Northwind gerne zur Verfügung. "
    "Auf Wiederhören!"
)


def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    state = callback_context.state

    # Step 1: Check if THIS model call contains end_session AND text
    has_end_session = False
    has_text_this_call = False

    for part in llm_response.content.parts:
        if part.has_function_call("end_session"):
            has_end_session = True
        else:
            content = part.text_or_transcript()
            if content and len(content.strip()) > 0:
                has_text_this_call = True

    # If no end_session in this call, or LLM already said something — no-op
    if not has_end_session or has_text_this_call:
        return None

    # Step 2: Check if agent produced text in an earlier model call within this turn
    for event in reversed(callback_context.events):
        if event.is_user():
            # Reached the last user message — no prior agent text found
            break
        if event.is_agent():
            for p in event.parts():
                content = p.text_or_transcript()
                if content and len(content.strip()) > 0:
                    # Agent already spoke in an earlier model call — don't double-inject
                    return None

    # Step 3: No text anywhere in this turn — inject farewell before end_session
    active_language = state.get("active_language", "English")
    farewell = _FAREWELL_DE if active_language == "German" else _FAREWELL_EN

    new_parts = [Part.from_text(text=farewell)]
    new_parts.extend(llm_response.content.parts)
    return LlmResponse.from_parts(parts=new_parts)
