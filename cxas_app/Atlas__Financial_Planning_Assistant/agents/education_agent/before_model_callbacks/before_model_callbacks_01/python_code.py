"""
before_model_callback 01 — Education Agent (trigger_handler)

PURPOSE:
    Reads _action_trigger from session state. If set, executes the corresponding
    action deterministically, bypassing the LLM.

    This MUST exist on ALL agents per gecx-design-guide.md:
    "In multi-agent architectures, the trigger-handling callback must exist on ALL agents."

    education_agent does not have escalation triggers as a primary flow, but the
    trigger_handler guards against cross-agent trigger leakage.

PLATFORM GLOBALS:
    CallbackContext, LlmRequest, LlmResponse, Part are auto-provided.
    Do NOT import them.
"""

from typing import Optional


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    state = callback_context.state

    trigger_value = state.get("_action_trigger", "")
    if not trigger_value:
        return None

    # Clear trigger immediately to prevent re-firing
    state["_action_trigger"] = ""

    if trigger_value == "escalate_to_advisor":
        open_question = state.get("_escalation_open_question", "Customer requested licensed advisor assistance.")

        try:
            tools.generate_advisor_handoff_summary(open_question=open_question)
        except Exception as e:
            print(f"[education_agent trigger_handler] generate_advisor_handoff_summary failed: {e}")

        farewell = (
            "Of course — let me connect you with a licensed Northwind advisor now. "
            "They'll have the full context of our conversation. "
            "Thank you for using Atlas today!"
        )
        return LlmResponse.from_parts(parts=[
            Part.from_text(text=farewell),
            Part.from_function_call(
                name="end_session",
                args={"session_escalated": True, "reason": "advisor_transfer"},
            ),
        ])

    elif trigger_value == "end_session_clean":
        farewell = (
            "Thank you for the great questions today. "
            "Northwind's knowledge base is always here whenever you want to learn more. "
            "Have a wonderful day!"
        )
        return LlmResponse.from_parts(parts=[
            Part.from_text(text=farewell),
            Part.from_function_call(
                name="end_session",
                args={"session_escalated": False, "reason": "clean_close"},
            ),
        ])

    print(f"[education_agent trigger_handler] Unknown _action_trigger: '{trigger_value}'")
    return None
