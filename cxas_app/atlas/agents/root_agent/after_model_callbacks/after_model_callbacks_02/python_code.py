"""
after_model_callback 02 — Root Agent (widget_injector)

PURPOSE:
    Reads _pending_widget from session state. If the LLM produced verbal text
    in this model call, appends a customize_response call with the stored
    richContent to display an account overview widget — then clears the flag.

    Fires AFTER the LLM speaks (unlike before_model_callback which replaced the
    LLM's turn entirely, causing silent responses). The account snapshot tool
    writes to _pending_widget; this callback injects the widget alongside the
    LLM's verbal summary.

    Must run AFTER the farewell_injection callback (after_model_callbacks_01)
    because farewell_injection handles end_session early-exit and this one
    handles normal turns only.

PLATFORM GLOBALS:
    CallbackContext, LlmResponse, Part are auto-provided. Do NOT import them.
"""

import json
from typing import Optional


def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    state = callback_context.state

    pending = state.get("_pending_widget", "")
    if not pending:
        return None

    # Only inject alongside verbal text — not on pure tool-calling turns
    has_text = any(
        part.text_or_transcript() and len(part.text_or_transcript().strip()) > 0
        for part in llm_response.content.parts
    )
    if not has_text:
        return None

    # Clear before building response to prevent re-injection on follow-up calls
    state["_pending_widget"] = ""

    try:
        rich_content = json.loads(pending)
    except Exception as e:
        print(f"[widget_injector] Failed to parse _pending_widget: {e}")
        return None

    # Append customize_response after the LLM's existing parts
    new_parts = list(llm_response.content.parts) + [
        Part.from_function_call(
            name="customize_response",
            args={"richContent": rich_content},
        ),
    ]
    return LlmResponse.from_parts(parts=new_parts)
