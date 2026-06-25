"""
before_model_callback 03 — Root Agent (trigger_handler)

PURPOSE:
    Reads _action_trigger from session state. If set to "escalate_to_advisor",
    calls generate_advisor_handoff_summary and returns an LlmResponse with
    farewell text + end_session, bypassing the LLM entirely.

    The LLM decides WHAT to do (detection via set_session_state tool call).
    This callback decides HOW (execution — deterministic, reliable).

    Clears _action_trigger after firing to prevent re-firing on the next model call.

    Also handles "end_session_clean": clean session termination without advisor transfer.

CRITICAL:
    This callback (trigger_handler) MUST exist on ALL agents — not just root_agent.
    Sub-agents have their own copy in their before_model_callbacks/ directory.
    Without it, escalation triggers set while a sub-agent handles the conversation
    would never be intercepted.

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
        # Call generate_advisor_handoff_summary directly from callback
        # The LLM set _action_trigger — we know escalation is warranted.
        # Read the open_question from the context if available (best-effort)
        open_question = state.get("_escalation_open_question", "Customer requested licensed advisor assistance.")

        try:
            summary_response = tools.generate_advisor_handoff_summary(
                open_question=open_question
            )
        except Exception as e:
            print(f"[trigger_handler] generate_advisor_handoff_summary failed: {e}")
            summary_response = {}

        farewell = (
            "Thank you for speaking with Atlas today. I've prepared a full summary "
            "of our conversation so the licensed advisor will have your context — "
            "you won't need to repeat yourself. Connecting you now. Take care!"
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
            "If you have any other questions in the future, don't hesitate to call. "
            "Have a wonderful day!"
        )
        return LlmResponse.from_parts(parts=[
            Part.from_text(text=farewell),
            Part.from_function_call(
                name="end_session",
                args={"session_escalated": False, "reason": "clean_close"},
            ),
        ])

    # Unknown trigger value — log and let LLM continue
    print(f"[trigger_handler] Unknown _action_trigger value: '{trigger_value}'")
    return None
