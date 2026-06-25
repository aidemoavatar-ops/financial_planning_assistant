"""
before_model_callback 01 — Guardrail Agent (trigger_handler)

PURPOSE:
    Reads _action_trigger from session state. If set to "escalate_to_advisor",
    calls generate_advisor_handoff_summary and returns a deterministic farewell
    + end_session response, bypassing the LLM.

    This is the guardrail_agent's copy of the trigger_handler. It MUST exist here
    because the guardrail_agent is the primary handler of advisor escalation requests.
    The trigger is set by the LLM via set_session_state when a boundary is hit.

    Per gecx-design-guide.md: "In multi-agent architectures, the trigger-handling
    callback must exist on ALL agents."

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
            print(f"[guardrail_agent trigger_handler] generate_advisor_handoff_summary failed: {e}")

        farewell = (
            "I completely understand. Let me connect you with a licensed Northwind advisor now. "
            "I've prepared a full summary of our conversation — you won't need to repeat yourself. "
            "Thank you for your patience, and have a great day!"
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
            "Thank you for speaking with Atlas today. "
            "If you need anything else, a licensed Northwind advisor is always available. "
            "Have a great day!"
        )
        return LlmResponse.from_parts(parts=[
            Part.from_text(text=farewell),
            Part.from_function_call(
                name="end_session",
                args={"session_escalated": False, "reason": "clean_close"},
            ),
        ])

    print(f"[guardrail_agent trigger_handler] Unknown _action_trigger: '{trigger_value}'")
    return None
