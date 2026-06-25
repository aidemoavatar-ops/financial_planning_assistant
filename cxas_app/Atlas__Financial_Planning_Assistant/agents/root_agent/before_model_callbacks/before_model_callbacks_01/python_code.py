"""
before_model_callback 01 — Root Agent (pin_reevaluation + deterministic_greeting)

PURPOSE:
    1. PIN re-evaluation (runs first): if auth_status is still "unauthenticated",
       re-checks customer_pin against the mock PIN. This catches the retry case where
       the LLM has just called set_session_state to update customer_pin in the same
       turn — before_agent_callback only runs at turn start, so auth_status would
       otherwise remain "unauthenticated" until the next turn. Re-evaluating here
       (before the LLM's final response) lets the LLM see auth_status = "authenticated"
       immediately and respond correctly.

    2. Deterministic greeting (session start only): when auth_status is "authenticated"
       and the turn is the welcome event, returns the static identity disclosure +
       greeting, bypassing the LLM.

    - Prevents the agent from skipping or varying the mandatory identity disclosure.
    - Skips greeting (no-op) during the auth/PIN-retry phase (auth_status = "unauthenticated").

PLATFORM GLOBALS:
    CallbackContext, LlmRequest, LlmResponse, Part are auto-provided.
    Do NOT import them. Only standard library imports need explicit import statements.
"""

from typing import Optional

# Must match _MOCK_PIN in before_agent_callbacks_01.
_MOCK_PIN = "atlas-test-pin-v1"

# Identity disclosure text — mandated by PRD "Identity" section.
# TODO: Get legal/compliance sign-off on exact wording before production launch.
# See tdd.md Known Issues: "Regulatory / compliance disclosure requirements unspecified."
_GREETING_EN = (
    "Hello! I'm Atlas, Northwind's financial planning assistant. "
    "I can help you with financial education, personalized planning tools, and connecting you "
    "with a licensed Northwind advisor when needed. "
    "Just so you know, I provide educational guidance — I'm not a licensed financial advisor "
    "and I don't give investment recommendations or financial advice. "
    "How can I help you today?"
)

_GREETING_DE = (
    "Hallo! Ich bin Atlas, der Finanzplanungsassistent von Northwind. "
    "Ich kann Ihnen bei der Finanzbildung, personalisierten Planungstools und der Verbindung "
    "mit einem lizenzierten Northwind-Berater helfen. "
    "Nur zur Information: Ich biete allgemeine Finanzbildung an — ich bin kein lizenzierter "
    "Finanzberater und gebe keine Anlageempfehlungen. "
    "Wie kann ich Ihnen heute helfen?"
)


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    state = callback_context.state

    # =========================================================================
    # PHASE 1: PIN re-evaluation
    # Fires on every model call (including after tool calls). If the LLM just
    # called set_session_state to update customer_pin, re-evaluate auth_status
    # so the LLM sees the correct value before generating its final response.
    # =========================================================================
    if state.get("auth_status") != "authenticated":
        if state.get("customer_pin", "") == _MOCK_PIN:
            state["auth_status"] = "authenticated"

    # =========================================================================
    # PHASE 2: Deterministic greeting (welcome event + authenticated only)
    # =========================================================================
    uc = callback_context.user_content
    user_parts = (uc.parts or []) if uc else callback_context.get_last_user_input()
    for part in user_parts:
        if part.text == "<event>welcome</event>":
            if state.get("auth_status") == "authenticated":
                active_language = state.get("active_language", "English")
                greeting = _GREETING_DE if active_language == "German" else _GREETING_EN
                return LlmResponse.from_parts(parts=[
                    Part.from_text(text=greeting),
                ])
            # Unauthenticated at session start — let the LLM handle the PIN prompt
            break

    return None
