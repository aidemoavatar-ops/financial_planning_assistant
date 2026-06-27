## Capability: planning-widget-tool

A `widgetTool` that the `planning_agent` calls after each successful planning calculation to render a rich content widget (table + chips or info + chips) in the chat UI.

### Tool descriptor

**File:** `cxas_app/atlas/tools/planning_widget/planning_widget.json`

**Tool type:** `widgetTool`

**Name:** `planning_widget`

**Description (linter-required, rule T012):**
> "Renders a rich content widget in the chat UI after a planning calculation. Call this immediately after run_planning_calculation succeeds, passing the richContent array from the tool response verbatim."

### Parameters schema

```json
{
  "type": "object",
  "properties": {
    "richContent": {
      "type": "array",
      "description": "The richContent array from run_planning_calculation's response. Pass verbatim — do not modify.",
      "items": {
        "type": "array",
        "items": {
          "type": "object"
        }
      }
    }
  },
  "required": ["richContent"]
}
```

The outer array is a carousel (one card per element). The inner array is a widget stack per card. All four calculation types return exactly one card (outer array length = 1).

### Registration

- Registered in `planning_agent.json` tools array.
- Does **not** need to be in `app.json` top-level tools array (agent-level registration only, consistent with `run_planning_calculation`).

### Agent instruction reference

The tool is referenced in `planning_agent` instruction using `{@Widget: planning_widget}` syntax. The LLM is instructed to call it immediately after `run_planning_calculation` succeeds, passing the `richContent` array from the tool response verbatim.

### Widget shapes by calculation type

| Calculation type | Widget stack |
|---|---|
| `emergency_fund_gap` | `table` (3 rows: current savings, target, gap) + `chips` |
| `debt_vs_invest` | `table` (2 rows: Option A/B with return and risk) + `chips` |
| `payoff_timeline` | `info` (balance, APR, monthly payment, payoff projection) + `chips` |
| `allocation_split` | `table` (2 rows: debt reduction, savings — amount and share) + `chips` |

The widget shapes are determined entirely by `run_planning_calculation`. The `planning_widget` tool is shape-agnostic — it accepts any valid richContent array.

### Invariants

- Called only after `run_planning_calculation` returns `status: "success"`.
- Never called on error responses.
- Called in the same model turn as the verbal result summary.
- `richContent` is passed verbatim from the tool response — the LLM must not rewrite, summarize, or reorder widget contents.
