"""
retrieve_account_snapshot — Account Data Tool

PURPOSE:
    Retrieves the customer's financial state from the Northwind bank system of record.
    Returns checking balance, savings accounts with APY, loan accounts with APRs, and
    cash-flow signals. Idempotent; safe to retry.

    Only called after auth_status is 'authenticated'. Stores result in account_snapshot
    session variable for use by run_planning_calculation.

TODO:
    Replace stub response with real bank system-of-record API call.
    API endpoint, authentication method, and response schema are TBD.
    See tdd.md Known Issues: "Bank system-of-record API unspecified."

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
"""


def retrieve_account_snapshot(customer_id: str) -> dict:
    """Retrieve the customer's complete financial state from the bank system of record.

    Idempotent and safe to retry. Must only be called when auth_status is 'authenticated'.
    The returned snapshot is used as input to run_planning_calculation.

    Args:
        customer_id: The unique customer identifier from session state. (REQUIRED)
            Use the customer_id session variable value.

    Returns:
        dict with:
            'status' (str): 'success' or 'error'.
            'snapshot' (dict): On success — customer financial state with keys:
                'customer_id' (str),
                'checking_balance' (float): current checking account balance in EUR,
                'savings_accounts' (list[dict]): each with 'account_id', 'balance', 'apy',
                'loan_accounts' (list[dict]): each with 'account_id', 'balance', 'apr', 'monthly_payment',
                'snapshot_timestamp' (str): ISO 8601 timestamp of data retrieval.
            'agent_action' (str): Instruction for how the agent should proceed.
            'error' (str): On error — description of what failed.
    """
    auth_status = context.state.get("auth_status", "")
    if auth_status != "authenticated":
        return {
            "status": "error",
            "error": "Account data access requires an authenticated session.",
            "agent_action": "Inform the customer that account data cannot be retrieved without successful PIN verification. Do not reveal any account figures."
        }

    if not customer_id:
        return {
            "status": "error",
            "error": "customer_id is required to retrieve account snapshot.",
            "agent_action": "The customer_id session variable is missing. Inform the customer that account data is unavailable and offer to assist with general financial education instead."
        }

    try:
        # TODO: Replace with real bank API call.
        # Example endpoint: POST /v1/accounts/snapshot?customer_id={customer_id}
        # Authentication: Bearer token from Secret Manager (TBD)
        # Response schema: TBD — confirm field names and units with bank API team.
        snapshot = {
            "customer_id": customer_id,
            "checking_balance": 8500.00,        # Stub: replace with real API value
            "savings_accounts": [
                {
                    "account_id": "SAV-001",
                    "balance": 12000.00,         # Stub
                    "apy": 0.005                 # Stub: 0.5% APY (low-yield, triggers proactive surfacing)
                }
            ],
            "loan_accounts": [
                {
                    "account_id": "LOAN-001",
                    "balance": 5200.00,          # Stub
                    "apr": 0.189,                # Stub: 18.9% APR (high-cost debt)
                    "monthly_payment": 185.00    # Stub
                }
            ],
            "snapshot_timestamp": "2026-06-24T00:00:00Z"  # Stub: use real timestamp
        }

        # Write snapshot to session state so callbacks and tools can access it
        import json
        context.state["account_snapshot"] = json.dumps(snapshot)

        return {
            "status": "success",
            "snapshot": snapshot,
            "agent_action": "Account snapshot retrieved successfully. Use these figures for any personalized planning calculations. Do not invent or estimate numbers — use only the values returned here."
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to retrieve account snapshot: {str(e)}",
            "agent_action": "Inform the customer that account data is temporarily unavailable and offer to assist with general financial education instead. Do not cite any account figures."
        }
