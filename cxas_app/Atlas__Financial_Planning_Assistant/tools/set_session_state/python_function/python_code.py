"""
set_session_state — State-Setting Tool

PURPOSE:
    Writes key-value pairs to session state. This is the "detection" half of the
    trigger pattern: the LLM calls this tool to signal WHAT should happen, then
    the before_model_callback reads the state on the next model call and
    executes HOW.

    Also used to update mutable state variables during the conversation:
    - auth_attempt_count (incremented on each failed PIN attempt)
    - discovery_state (updated as root_agent gathers discovery answers)
    - _action_trigger (set to 'escalate_to_advisor' or 'end_session_clean')

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
    Do NOT add context as a function parameter.
"""


def set_session_state(
    _action_trigger: str = "",
    auth_attempt_count: str = "",
    discovery_state: str = "",
    active_language: str = ""
) -> dict:
    """Write session state variables. Used for the trigger pattern and state updates.

    Args:
        _action_trigger: Action for before_model_callback to execute deterministically.
            Values: 'escalate_to_advisor' (warm handoff to licensed advisor) or
            'end_session_clean' (close session gracefully). Read and cleared by
            before_model_callback. (REQUIRED when triggering an action)
        auth_attempt_count: Number of consecutive failed PIN attempts (as string integer).
            Set by root_agent on each failed auth attempt. When value reaches '3',
            auth-lockout flow triggers. (REQUIRED when updating auth retry count)
        discovery_state: JSON string representing discovery conversation progress.
            Schema: {"goals": str, "time_horizon": str, "emergency_fund_status": str,
            "highest_cost_debt": str, "discovery_complete": bool}.
            Update incrementally as root_agent collects each answer. (REQUIRED when
            updating discovery progress)
        active_language: Language for the conversation. Values: 'English' or 'German'.
            Prefer using update_language tool for language switches. (REQUIRED when
            updating language via this tool)

    Returns:
        dict with 'status' (str) and 'updated_variables' (dict) listing what was set,
        or 'agent_action' (str) with instructions if no variables were provided.
    """
    updated = {}

    if _action_trigger:
        context.state["_action_trigger"] = _action_trigger
        updated["_action_trigger"] = _action_trigger

    if auth_attempt_count:
        context.state["auth_attempt_count"] = auth_attempt_count
        updated["auth_attempt_count"] = auth_attempt_count

    if discovery_state:
        context.state["discovery_state"] = discovery_state
        updated["discovery_state"] = discovery_state

    if active_language:
        context.state["active_language"] = active_language
        updated["active_language"] = active_language

    if not updated:
        return {
            "status": "error",
            "agent_action": "At least one parameter must be provided to set_session_state. Specify _action_trigger, auth_attempt_count, discovery_state, or active_language."
        }

    return {
        "status": "success",
        "updated_variables": updated,
        "agent_action": "State updated successfully. Continue the conversation."
    }
