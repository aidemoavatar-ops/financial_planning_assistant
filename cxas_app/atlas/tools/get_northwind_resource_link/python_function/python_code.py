"""
get_northwind_resource_link — Official Resource URL Tool

PURPOSE:
    Returns official Northwind URLs for product pages, rate disclosures, and
    advisor scheduling. Points customers to the authoritative source of record
    rather than quoting terms or rates inline.

    Do NOT quote rates or terms from this tool's output — only share the URL
    and instruct the customer to visit the official page for current figures.
"""

# Northwind official URL registry — update when URLs change
NORTHWIND_URLS = {
    "savings_rates": "https://www.northwindbank.example.com/rates/savings",
    "loan_rates": "https://www.northwindbank.example.com/rates/loans",
    "advisor_scheduling": "https://www.northwindbank.example.com/advisors/schedule",
    "product_overview": "https://www.northwindbank.example.com/products",
    "rate_disclosures": "https://www.northwindbank.example.com/legal/rate-disclosures",
}

TOPIC_BUTTON_LABELS = {
    "savings_rates": "View Current Savings Rates",
    "loan_rates": "View Current Loan Rates",
    "advisor_scheduling": "Schedule a Meeting with an Advisor",
    "product_overview": "Explore Northwind Products",
    "rate_disclosures": "Read Rate Disclosures",
}

VALID_TOPICS = list(NORTHWIND_URLS.keys())


def get_northwind_resource_link(topic: str) -> dict:
    """Return the official Northwind URL for the requested topic.

    Do NOT quote rates or terms inline — direct the customer to the official URL.
    The URL is the authoritative source of record for current rates and product terms.

    Args:
        topic: The resource topic to look up. (REQUIRED) One of:
            'savings_rates' — current savings account APY rates,
            'loan_rates' — current loan APR rates,
            'advisor_scheduling' — book an appointment with a licensed advisor,
            'product_overview' — overview of Northwind financial products,
            'rate_disclosures' — official legal rate disclosure documents.

    Returns:
        dict with:
            'status' (str): 'success' or 'error'.
            'topic' (str): The requested topic.
            'url' (str): On success — the official Northwind URL.
            'agent_action' (str): Instruction for how to present the URL to the customer.
            'error' (str): On error — description of what failed.
    """
    if not topic:
        return {
            "status": "error",
            "error": "topic is required.",
            "agent_action": f"Ask the customer which resource they need. Available topics: {', '.join(VALID_TOPICS)}."
        }

    url = NORTHWIND_URLS.get(topic)
    if not url:
        return {
            "status": "error",
            "error": f"Unknown topic: '{topic}'. Valid topics: {', '.join(VALID_TOPICS)}.",
            "agent_action": f"Inform the customer that the requested topic is not available. Offer one of: {', '.join(VALID_TOPICS)}."
        }

    import json
    context.state["_pending_widget"] = json.dumps([[
        {
            "type": "button",
            "text": TOPIC_BUTTON_LABELS.get(topic, "View Official Resource"),
            "link": url
        }
    ]])

    return {
        "status": "success",
        "topic": topic,
        "url": url,
        "agent_action": (
            f"Share this official Northwind URL with the customer: {url}. "
            "Do NOT quote specific rates, terms, or figures from memory — "
            "the official page has the current and authoritative information. "
            "Tell the customer to visit the link for the most up-to-date details."
        ),
    }
