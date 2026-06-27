"""
after_model_callback 01 — Planning Agent (widget_injector)

PURPOSE:
    Reads _pending_widget from session state. If the LLM produced verbal text
    in this model call, appends a customize_response call with the stored
    richContent to display a visual comparison widget — then clears the flag.

    This callback fires AFTER the LLM has produced its verbal response, so the
    customer hears the explanation AND sees the widget. The before_model_callback
    approach was replaced because it bypassed the LLM entirely, causing silence.

    Safe for multi-model-call turns: only injects when text is present. Clears
    _pending_widget on first injection, preventing double-firing.

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
