"""
before_model_callback 02 — Planning Agent (widget_injector)

PURPOSE:
    Reads _pending_widget from session state. If set, injects a
    customize_response call with the stored richContent to display
    a visual comparison widget — then clears the flag.

    The tool (run_planning_calculation, get_northwind_resource_link)
    writes the widget data to _pending_widget after each successful run.
    This callback fires deterministically on the next model call to display it.
    The LLM never touches the richContent args — this avoids the common failure
    where the LLM substitutes a plain-text 'content' arg instead of the
    structured 'richContent' array.

    Must run AFTER the trigger_handler (before_model_callbacks_01) so
    escalation takes priority over widget display.

PLATFORM GLOBALS:
    CallbackContext, LlmRequest, LlmResponse, Part are auto-provided.
    Do NOT import them.
"""

import json
from typing import Optional


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    state = callback_context.state

    pending = state.get("_pending_widget", "")
    if not pending:
        return None

    # Clear immediately to prevent re-firing on the next model call
    state["_pending_widget"] = ""

    try:
        rich_content = json.loads(pending)
    except Exception as e:
        print(f"[widget_injector] Failed to parse _pending_widget: {e}")
        return None

    return LlmResponse.from_parts(parts=[
        Part.from_function_call(
            name="customize_response",
            args={"richContent": rich_content},
        ),
    ])
