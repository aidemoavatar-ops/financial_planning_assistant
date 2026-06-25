"""
before_model_callback 01 — Root Agent (deterministic_greeting)

PURPOSE:
    Intercepts the very first model call (session start) when auth_status is
    "authenticated" and returns the static identity disclosure + greeting,
    bypassing the LLM.

    - Prevents the agent from skipping or varying the mandatory identity disclosure.
    - Skips (no-op) during the auth/PIN-retry phase (auth_status = "unauthenticated").
    - Fires ONLY on the session-start event, not on subsequent turns.

PLATFORM GLOBALS:
    CallbackContext, LlmRequest, LlmResponse, Part are auto-provided.
    Do NOT import them. Only standard library imports need explicit import statements.
"""


from typing import Optional


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

    # Only fire on the welcome event (session start)
    # Check user_content (current turn) first; fall back to event history
    uc = callback_context.user_content
    user_parts = (uc.parts or []) if uc else callback_context.get_last_user_input()
    for part in user_parts:
        if part.text == "<event>welcome</event>":
            # Only deliver greeting when authenticated
            if state.get("auth_status") == "authenticated":
                active_language = state.get("active_language", "English")
                greeting = _GREETING_DE if active_language == "German" else _GREETING_EN
                return LlmResponse.from_parts(parts=[
                    Part.from_text(text=greeting),
                ])
            # If unauthenticated at session start: let the LLM handle the PIN prompt
            break

    return None
