"""
update_language — Language Switch Gate Tool

PURPOSE:
    Gates explicit language-switch requests by updating active_language in session
    state. Required per gecx-design-guide multilingual pattern for gemini-3.1-flash-live
    agents (Failure Mode 2 mitigation: non-deterministic language switch detection).

    ONLY call this tool when the user EXPLICITLY requests a language switch.
    Do NOT call for single words, politeness markers, or ambiguous utterances.

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
"""

SUPPORTED_LANGUAGES = {"English", "German"}


def update_language(new_language: str) -> dict:
    """Update the active conversation language when the user explicitly requests a switch.

    Call this BEFORE generating your first response in the new language. Only call
    when the user has made an explicit request (e.g., "speak German" / "auf Deutsch bitte").
    Do NOT call for single words, cognates, or short ambiguous utterances.

    Args:
        new_language: The language to switch to. (REQUIRED)
            Supported values: 'English', 'German'.

    Returns:
        dict with:
            'success' (bool): Whether the language was updated.
            'active_language' (str): The new active language.
            'agent_action' (str): Instruction to continue the entire conversation in new_language.
            'error' (str): On error — if unsupported language requested.
    """
    if not new_language:
        return {
            "success": False,
            "active_language": context.state.get("active_language", "English"),
            "error": "new_language is required.",
            "agent_action": "Ask the customer which language they would like to use: English or German."
        }

    if new_language not in SUPPORTED_LANGUAGES:
        return {
            "success": False,
            "active_language": context.state.get("active_language", "English"),
            "error": f"Unsupported language: '{new_language}'. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}.",
            "agent_action": f"Inform the customer that Atlas currently supports English and German. Ask which they prefer."
        }

    context.state["active_language"] = new_language

    return {
        "success": True,
        "active_language": new_language,
        "agent_action": f"Continue the entire conversation in {new_language} from this point forward. All responses, tool queries, and knowledge base searches should use {new_language}."
    }
