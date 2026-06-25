"""
before_model_callback 01 — Planning Agent (trigger_handler)

PURPOSE:
    Reads _action_trigger from session state. If set to "escalate_to_advisor",
    calls generate_advisor_handoff_summary and returns a deterministic farewell
    + end_session response, bypassing the LLM.

    This is the SAME trigger pattern as root_agent's trigger_handler. It MUST
    exist on ALL agents — not just root_agent. Without it, escalation triggers
    set while the customer is talking to planning_agent would never be intercepted.

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
            print(f"[planning_agent trigger_handler] generate_advisor_handoff_summary failed: {e}")

        farewell = (
            "I've prepared a summary of your planning session for the licensed advisor. "
            "They'll have the full context — you won't need to start over. "
            "Connecting you now. Take care!"
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
            "Thank you for using Atlas today. "
            "If you have more planning questions, Northwind is always here. Have a great day!"
        )
        return LlmResponse.from_parts(parts=[
            Part.from_text(text=farewell),
            Part.from_function_call(
                name="end_session",
                args={"session_escalated": False, "reason": "clean_close"},
            ),
        ])

    print(f"[planning_agent trigger_handler] Unknown _action_trigger: '{trigger_value}'")
    return None
