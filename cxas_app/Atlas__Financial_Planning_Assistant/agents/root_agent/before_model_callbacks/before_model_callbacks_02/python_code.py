"""
before_model_callback 02 — Root Agent (silence_handler)

PURPOSE:
    Detects consecutive silence events from the voice channel. Tracks a running
    count in _silence_count session state. After 3 consecutive silence events,
    constructs and returns an LlmResponse that calls end_session, bypassing the LLM.
    Resets the counter if the user speaks.

    Standard voice pattern for audio-modality agents on gemini-3.1-flash-live.

SILENCE DETECTION:
    The platform sends a "<context>no user activity detected for X seconds.</context>"
    message when no audio input is received. This is detected via regex.

PLATFORM GLOBALS:
    CallbackContext, LlmRequest, LlmResponse, Part are auto-provided.
    Do NOT import them. Only re, typing need explicit import.
"""

import re
from typing import Iterator, Optional


def _is_user_inactive(contents: list) -> bool:
    """Check if the latest user message is a 'no user activity' silence signal."""
    silence_pattern = r"<context>no user activity detected for \d+ seconds\.</context>"
    return len(contents) > 1 and any(
        re.search(silence_pattern, p.text, re.IGNORECASE)
        for p in contents[-1].parts
        if p.text
    )


def _get_reversed_agent_messages(contents: list) -> Iterator[str]:
    """Yield agent text messages from most recent to oldest."""
    for content in reversed(contents):
        texts = []
        for part in content.parts:
            if content.role == "model" and part.text is not None:
                texts.append(part.text)
        if texts:
            yield "".join(texts)


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    state = callback_context.state

    try:
        if _is_user_inactive(llm_request.contents):
            silence_count = int(state.get("_silence_count", "0") or "0") + 1
            state["_silence_count"] = str(silence_count)

            if silence_count < 3:
                reversed_msgs = _get_reversed_agent_messages(llm_request.contents)
                if silence_count == 1:
                    last_msg = next(reversed_msgs, "How can I help you today?")
                    return LlmResponse.from_parts(parts=[
                        Part.from_text(text=f"Sorry, I didn't hear anything. {last_msg}")
                    ])
                else:
                    next(reversed_msgs, None)  # skip the "Sorry" repeat
                    original_msg = next(reversed_msgs, "How can I help you today?")
                    return LlmResponse.from_parts(parts=[
                        Part.from_text(text=f"I still can't hear you. {original_msg}")
                    ])
            else:
                # 3 consecutive silences — end the session
                return LlmResponse.from_parts(parts=[
                    Part.from_text(
                        text="I'm unable to hear you after several attempts. "
                             "Please try calling Northwind again when you're ready. "
                             "Have a great day!"
                    ),
                    Part.from_function_call(
                        name="end_session",
                        args={"session_escalated": False, "reason": "silence_limit_reached"},
                    ),
                ])
        else:
            # User spoke — reset silence counter
            state["_silence_count"] = "0"

    except Exception as e:
        print(f"[silence_handler] Error: {e}")

    return None
