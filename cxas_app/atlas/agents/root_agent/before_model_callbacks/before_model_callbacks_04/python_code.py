"""
before_model_callback 04 — Root Agent (widget_injector)

PURPOSE:
    Reads _pending_widget from session state. If set, injects a
    customize_response call with the stored richContent to display
    a visual account overview card — then clears the flag.

    The retrieve_account_snapshot tool writes the account summary widget
    to _pending_widget after a successful snapshot load. This callback
    fires deterministically on the next model call to display it.
    The LLM never touches the richContent args.

    Must run LAST (after pin_reevaluation, silence_handler, trigger_handler)
    so those critical behaviors take priority.

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
