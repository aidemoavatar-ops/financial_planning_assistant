"""
run_planning_calculation — Deterministic Planning Math Tool

PURPOSE:
    Runs all planning math in deterministic code, not in the model. Returns both
    results AND an explicit agent_action instruction for presentation framing, so
    the model does not invent numbers or framing.

    Supports four calculation types:
    - emergency_fund_gap: target vs current emergency fund
    - debt_vs_invest: guaranteed return of debt payoff vs investment yield
    - payoff_timeline: months to pay off a loan at the current payment rate
    - allocation_split: proposed savings/debt allocation from available cash

PLATFORM GLOBALS:
    context (and context.state) are provided by the platform at runtime.
"""

import json


def run_planning_calculation(
    calculation_type: str,
    monthly_expenses: float = 0.0,
    available_cash: float = 0.0,
    investment_yield: float = 0.0
) -> dict:
    """Run deterministic financial planning calculations using real account data.

    All numeric inputs from the customer's account come from account_snapshot in
    session state — do NOT pass balance/APR values as arguments. Only supply the
    parameters listed below. The tool reads account_snapshot internally.

    Args:
        calculation_type: Which calculation to run. One of: (REQUIRED)
            'emergency_fund_gap' — compares 3-month expense target to current savings balance,
            'debt_vs_invest' — compares guaranteed APR savings from debt payoff to investment yield,
            'payoff_timeline' — projects months to pay off highest-APR loan at current payment,
            'allocation_split' — proposes how to split available cash between savings and debt.
        monthly_expenses: Customer's estimated monthly expenses in EUR. Required for
            'emergency_fund_gap' and 'allocation_split'. (REQUIRED for those types)
        available_cash: Cash amount available to allocate, in EUR. Required for
            'allocation_split'. (REQUIRED for allocation_split)
        investment_yield: Expected annual yield of proposed investment as a decimal (e.g., 0.07
            for 7%). Required for 'debt_vs_invest'. (REQUIRED for debt_vs_invest)

    Returns:
        dict with:
            'status' (str): 'success' or 'error'.
            'calculation_type' (str): The calculation that was run.
            'results' (dict): Numeric results of the calculation.
            'agent_action' (str): Exact instruction for how to present results as a
                side-by-side comparison. The agent MUST follow this instruction verbatim
                and MUST NOT add, remove, or modify any figures.
            'richContent' (list): On success — the richContent array for
                {@Widget: planning_widget}. Pass to the widget tool verbatim.
            'error' (str): On error — description of what failed.
    """
    auth_status = context.state.get("auth_status", "")
    if auth_status != "authenticated":
        return {
            "status": "error",
            "error": "Planning calculations require an authenticated session with account data.",
            "agent_action": "Inform the customer that personalized calculations are not available without account verification."
        }

    snapshot_raw = context.state.get("account_snapshot", "")
    if not snapshot_raw:
        return {
            "status": "error",
            "error": "account_snapshot is not populated. Retrieve account data first.",
            "agent_action": "Account data is not yet loaded. Retrieve the account snapshot before running calculations."
        }

    try:
        snapshot = json.loads(snapshot_raw)
    except Exception:
        return {
            "status": "error",
            "error": "account_snapshot is malformed and could not be parsed.",
            "agent_action": "There was a data issue retrieving account details. Inform the customer and offer to assist with general financial education instead."
        }

    try:
        if calculation_type == "emergency_fund_gap":
            savings_balance = sum(
                acc.get("balance", 0) for acc in snapshot.get("savings_accounts", [])
            )
            target = monthly_expenses * 3
            gap = max(0.0, target - savings_balance)
            months_to_close = round(gap / max(available_cash, 1), 1) if available_cash > 0 else None

            results = {
                "current_savings_eur": savings_balance,
                "monthly_expenses_eur": monthly_expenses,
                "three_month_target_eur": target,
                "gap_eur": gap,
                "months_to_close_gap": months_to_close
            }
            action = (
                "Present this as a side-by-side comparison: "
                f"Current safety net: EUR {savings_balance:,.2f}. "
                f"3-month target: EUR {target:,.2f}. "
                f"Gap to close: EUR {gap:,.2f}. "
                + (f"At EUR {available_cash:,.2f}/month, you would reach the target in {months_to_close} months. " if months_to_close else "")
                + "Offer to discuss options for closing the gap. Do not recommend specific products. "
                + "Then call planning_widget with the richContent array from this response as the richContent argument — pass it verbatim, do not modify."
            )
            rich_content = {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "Emergency Fund Status",
                        "subtitle": f"Gap to close: EUR {gap:,.2f}",
                        "text": f"Current savings: EUR {savings_balance:,.2f}  |  3-month target: EUR {target:,.2f}"
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "How can I close this gap?"},
                            {"text": "What is an emergency fund?"},
                            {"text": "Talk to a licensed advisor"}
                        ]
                    }
                ]]
            }

        elif calculation_type == "debt_vs_invest":
            loans = snapshot.get("loan_accounts", [])
            if not loans:
                return {
                    "status": "error",
                    "error": "No loan accounts found in snapshot.",
                    "agent_action": "Inform the customer that no active loan accounts were found. Offer emergency fund or allocation analysis instead."
                }
            highest_apr_loan = max(loans, key=lambda x: x.get("apr", 0))
            loan_apr = highest_apr_loan.get("apr", 0)
            loan_balance = highest_apr_loan.get("balance", 0)
            loan_id = highest_apr_loan.get("account_id", "loan")

            guaranteed_return = loan_apr  # paying off debt = guaranteed APR return
            comparison_delta = round(guaranteed_return - investment_yield, 4)

            results = {
                "highest_apr_loan_id": loan_id,
                "loan_apr": loan_apr,
                "loan_balance_eur": loan_balance,
                "investment_yield": investment_yield,
                "guaranteed_return_from_payoff": guaranteed_return,
                "apr_vs_yield_delta": comparison_delta
            }
            action = (
                "Present this as a side-by-side comparison: "
                f"Option A — Pay down {loan_id}: guaranteed {loan_apr*100:.1f}% return (equal to the APR you stop paying). "
                f"Option B — Invest at {investment_yield*100:.1f}% yield: "
                + ("lower return than debt payoff" if comparison_delta > 0 else "higher return than debt cost")
                + f" (delta: {abs(comparison_delta)*100:.1f}%). "
                "Present both options neutrally. Do NOT recommend one over the other. "
                "Offer to route to a licensed advisor for a recommendation. "
                "Then call planning_widget with the richContent array from this response as the richContent argument — pass it verbatim, do not modify."
            )
            rich_content = {
                "richContent": [[
                    {
                        "type": "info",
                        "title": f"Option A — Pay off {loan_id}",
                        "subtitle": f"{loan_apr*100:.1f}% guaranteed return",
                        "text": "Risk: None — saves certain interest cost"
                    },
                    {
                        "type": "info",
                        "title": "Option B — Invest",
                        "subtitle": f"{investment_yield*100:.1f}% projected yield",
                        "text": "Risk: Market risk — returns not guaranteed"
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "Tell me more about Option A"},
                            {"text": "Tell me more about Option B"},
                            {"text": "Talk to a licensed advisor"}
                        ]
                    }
                ]]
            }

        elif calculation_type == "payoff_timeline":
            loans = snapshot.get("loan_accounts", [])
            if not loans:
                return {
                    "status": "error",
                    "error": "No loan accounts found for payoff timeline.",
                    "agent_action": "Inform the customer that no active loan accounts were found."
                }
            highest_apr_loan = max(loans, key=lambda x: x.get("apr", 0))
            balance = highest_apr_loan.get("balance", 0)
            monthly_payment = highest_apr_loan.get("monthly_payment", 0)
            apr = highest_apr_loan.get("apr", 0)
            loan_id = highest_apr_loan.get("account_id", "loan")

            monthly_rate = apr / 12
            if monthly_payment <= balance * monthly_rate:
                months = None  # payment doesn't cover interest
            elif monthly_rate == 0:
                months = round(balance / monthly_payment, 0) if monthly_payment > 0 else None
            else:
                import math
                months = round(
                    -math.log(1 - (balance * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate),
                    0
                ) if monthly_payment > balance * monthly_rate else None

            results = {
                "loan_id": loan_id,
                "balance_eur": balance,
                "apr": apr,
                "monthly_payment_eur": monthly_payment,
                "payoff_months": months
            }
            payoff_label = (
                f"{int(months)} months ({int(months)//12}y {int(months)%12}m)"
                if months else "Payment too low to cover interest"
            )
            action = (
                f"Present payoff projection for {loan_id}: "
                f"Balance EUR {balance:,.2f} at {apr*100:.1f}% APR, "
                f"current payment EUR {monthly_payment:,.2f}/month. "
                + (f"Projected payoff: {int(months)} months ({int(months)//12} years {int(months)%12} months). " if months else "Current payment does not cover interest — increasing the payment is required. ")
                + "Present as a factual projection. Do not recommend specific payment amounts. "
                + "Then call planning_widget with the richContent array from this response as the richContent argument — pass it verbatim, do not modify."
            )
            rich_content = {
                "richContent": [[
                    {
                        "type": "info",
                        "title": f"Payoff Timeline — {loan_id}",
                        "subtitle": f"Balance: EUR {balance:,.2f} at {apr*100:.1f}% APR",
                        "text": f"Monthly payment: EUR {monthly_payment:,.2f}   |   Projected payoff: {payoff_label}"
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "What if I paid more each month?"},
                            {"text": "Compare with investing instead"},
                            {"text": "Talk to a licensed advisor"}
                        ]
                    }
                ]]
            }

        elif calculation_type == "allocation_split":
            savings_apy = 0.0
            for acc in snapshot.get("savings_accounts", []):
                savings_apy = max(savings_apy, acc.get("apy", 0))
            loans = snapshot.get("loan_accounts", [])
            highest_apr_loan = max(loans, key=lambda x: x.get("apr", 0)) if loans else {}
            loan_apr = highest_apr_loan.get("apr", 0)
            loan_id = highest_apr_loan.get("account_id", "")

            # Split ratios: weight toward whichever rate is higher
            if loan_apr > savings_apy and loans:
                debt_pct = 0.70
                savings_pct = 0.30
            else:
                debt_pct = 0.30
                savings_pct = 0.70

            debt_amount = round(available_cash * debt_pct, 2)
            savings_amount = round(available_cash * savings_pct, 2)

            # 1-year monetary benefit for all 3 scenarios
            benefit_all_loan = round(available_cash * loan_apr, 2)
            benefit_all_savings = round(available_cash * savings_apy, 2)
            benefit_split = round(debt_amount * loan_apr + savings_amount * savings_apy, 2)

            best = max(
                [("A", benefit_all_loan), ("B", benefit_all_savings), ("C", benefit_split)],
                key=lambda x: x[1]
            )

            # Unicode bar chart scaled to 15 chars
            max_b = max(benefit_all_loan, benefit_all_savings, benefit_split)
            def _bar(v, width=15):
                filled = round(v / max_b * width) if max_b else 0
                return "█" * filled + "░" * (width - filled)

            results = {
                "available_cash_eur": available_cash,
                "loan_apr": loan_apr,
                "savings_apy": savings_apy,
                "scenario_all_loan": {"amount_eur": available_cash, "benefit_1yr_eur": benefit_all_loan},
                "scenario_all_savings": {"amount_eur": available_cash, "benefit_1yr_eur": benefit_all_savings},
                "scenario_split": {
                    "debt_eur": debt_amount,
                    "savings_eur": savings_amount,
                    "benefit_1yr_eur": benefit_split,
                    "debt_pct": debt_pct,
                    "savings_pct": savings_pct,
                },
                "highest_return_scenario": best[0],
            }
            best_label = {"A": "Option A", "B": "Option B", "C": "Option C"}[best[0]]
            action = (
                f"Present 3 scenarios for EUR {available_cash:,.2f}: "
                f"A) All to loan ({loan_id or 'highest-APR loan'}): EUR {benefit_all_loan:,.2f} benefit in year 1 at {loan_apr*100:.1f}% APR. "
                f"B) All to savings: EUR {benefit_all_savings:,.2f} benefit in year 1 at {savings_apy*100:.1f}% APY. "
                f"C) {int(debt_pct*100)}/{int(savings_pct*100)} split: EUR {benefit_split:,.2f} benefit in year 1. "
                f"State factually that {best_label} yields the highest mathematical return over one year. "
                "Note that Option C preserves liquidity in accessible savings. "
                "Do NOT say 'you should' or direct the customer toward any option. "
                "Offer to route to a licensed advisor for a personalized recommendation. "
                "Then call planning_widget with the richContent array from this response as the richContent argument — pass it verbatim, do not modify."
            )
            rich_content = {
                "richContent": [[
                    {
                        "type": "info",
                        "title": f"A — All to Loan ({loan_id or 'highest-APR loan'})" + ("  ★ highest return" if best[0] == "A" else ""),
                        "subtitle": f"EUR {benefit_all_loan:,.2f} / year",
                        "text": f"{_bar(benefit_all_loan)}  {loan_apr*100:.1f}% APR on EUR {available_cash:,.2f}"
                    },
                    {
                        "type": "info",
                        "title": "B — All to Savings" + ("  ★ highest return" if best[0] == "B" else ""),
                        "subtitle": f"EUR {benefit_all_savings:,.2f} / year",
                        "text": f"{_bar(benefit_all_savings)}  {savings_apy*100:.1f}% APY on EUR {available_cash:,.2f}"
                    },
                    {
                        "type": "info",
                        "title": f"C — {int(debt_pct*100)}% Loan / {int(savings_pct*100)}% Savings" + ("  ★ highest return" if best[0] == "C" else ""),
                        "subtitle": f"EUR {benefit_split:,.2f} / year",
                        "text": f"{_bar(benefit_split)}  Balanced — preserves liquidity"
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": f"Tell me more about Option {best[0]}"},
                            {"text": "Show full comparison"},
                            {"text": "Talk to a licensed advisor"}
                        ]
                    }
                ]]
            }

        else:
            return {
                "status": "error",
                "error": f"Unknown calculation_type: '{calculation_type}'. Valid values: emergency_fund_gap, debt_vs_invest, payoff_timeline, allocation_split.",
                "agent_action": "Ask the customer what type of analysis they would like: emergency fund gap, debt versus investing comparison, payoff timeline, or allocation split."
            }

        return {
            "status": "success",
            "calculation_type": calculation_type,
            "results": results,
            "agent_action": action,
            "richContent": rich_content["richContent"],
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Calculation failed: {str(e)}",
            "agent_action": "Inform the customer that there was an issue running the calculation and offer to try a different analysis."
        }
