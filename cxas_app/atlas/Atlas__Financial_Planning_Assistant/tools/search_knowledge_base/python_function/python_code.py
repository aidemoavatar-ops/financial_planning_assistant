"""
search_knowledge_base — Financial Education RAG Tool

PURPOSE:
    Retrieves vetted Northwind financial-education content for conceptual and
    policy questions. The Northwind KB contains native content in both English
    and German — query directly in the user's active language. No translation
    is needed at the tool boundary (bilingual KB confirmed).

    Use for: definitions, concepts, general policy ("what is APR", "how does
    compound interest work", "what is an emergency fund").

    Do NOT use for: personalized calculations, account-specific figures, or
    regulated advice. Route those to run_planning_calculation or guardrail_agent.

TODO:
    Replace stub response with real Vertex AI Data Store / RAG retrieval call.
    Connect to the Northwind KB Data Store resource.

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
"""


def search_knowledge_base(user_query: str, language: str = "English") -> dict:
    """Search the Northwind financial-education knowledge base for educational content.

    The KB contains vetted content in both English and German. Query in the user's
    active language to retrieve native-language content — no translation required.

    Args:
        user_query: The customer's conceptual or policy question, in the language
            specified by the language parameter. Example: "What is an emergency fund?"
            or "Was ist ein Notfallfonds?". (REQUIRED)
        language: The language to query in. Must match active_language session variable.
            Values: 'English' or 'German'. Determines which KB content partition to query.
            Default: 'English'. (REQUIRED for German sessions)

    Returns:
        dict with:
            'status' (str): 'success' or 'error'.
            'result' (str): On success — educational content from the KB in the requested
                language. Cite as Northwind knowledge base content.
            'source' (str): KB article title or identifier (for attribution).
            'agent_action' (str): Instruction for how to present the result.
            'error' (str): On error — description of what failed.
    """
    if not user_query:
        return {
            "status": "error",
            "error": "user_query is required.",
            "agent_action": "Ask the customer what financial concept or policy they would like to learn about."
        }

    active_language = context.state.get("active_language", "English")
    effective_language = language if language else active_language

    try:
        # TODO: Replace with real Vertex AI Data Store RAG call.
        # Example: Use the Vertex AI Search API to query the Northwind KB.
        # The KB supports both English and German natively — query in effective_language.
        # Data Store resource name: TBD (confirm with engineering team).

        if effective_language == "German":
            stub_result = (
                "Ein Notfallfonds ist ein Liquiditätspuffer für unerwartete Ausgaben, "
                "wie Autoreparaturen oder medizinische Kosten. "
                "Northwind empfiehlt, mindestens 3 Monatsausgaben auf einem leicht zugänglichen "
                "Sparkonto zu halten. Dies ist allgemeines Bildungsmaterial — für eine "
                "persönliche Empfehlung wenden Sie sich bitte an einen zugelassenen Berater."
            )
            stub_source = "Northwind Wissensbank: Grundlagen der Notfallvorsorge"
        else:
            stub_result = (
                "An emergency fund is a liquid cash reserve held for unexpected expenses "
                "such as car repairs, medical bills, or sudden income loss. "
                "Northwind's general guidance is to maintain at least 3 months of living "
                "expenses in an easily accessible savings account. "
                "This is general educational content — for personalized guidance, "
                "please speak with a licensed financial advisor."
            )
            stub_source = "Northwind Knowledge Base: Emergency Fund Basics"

        return {
            "status": "success",
            "result": stub_result,
            "source": stub_source,
            "agent_action": (
                "Present this educational content to the customer, clearly attributing it to "
                "the Northwind knowledge base. Explicitly distinguish this general educational "
                "guidance from the customer's personal account figures. Do NOT blend KB content "
                "with account numbers. If the customer asks for personalized analysis based on "
                "their specific situation, route to planning_agent."
            )
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Knowledge base search failed: {str(e)}",
            "agent_action": "Inform the customer that the knowledge base is temporarily unavailable and offer to answer general questions from memory if appropriate, or suggest they visit the Northwind website for resources."
        }
