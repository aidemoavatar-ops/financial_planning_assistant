## Why

Rich response widgets (tables, chips) never appear in the chat UI after planning calculations. The current implementation uses a callback to inject `customize_response` as a function call — but the GECX platform only renders rich content widgets when they are delivered through a **`widgetTool`** called by the agent, as documented in the GECX rich response widget guide. The callback-injection approach is architecturally wrong and silently ignored by the platform.

## What Changes

- **NEW** `planning_widget` widgetTool descriptor (`tools/planning_widget/planning_widget.json`) accepting a `richContent` array parameter
- **MODIFIED** `run_planning_calculation` — returns `richContent` in the tool response (replacing session-state storage in `_pending_widget`) so the LLM can pass it to the widget tool
- **MODIFIED** `planning_agent` instruction — adds `{@Widget: planning_widget}` call instruction after each successful calculation
- **MODIFIED** `planning_agent.json` — registers `planning_widget` in the tools array
- **REMOVED** `after_model_callbacks/after_model_callbacks_01/python_code.py` (widget_injector callback — no longer needed)
- **REMOVED** `before_model_callbacks/before_model_callbacks_02/python_code.py` (dead, unregistered widget injector)
- **REMOVED** `_pending_widget` session variable from `app.json`
- **REMOVED** `customize_response` from `planning_agent.json` tools array (no longer needed for widget delivery)
- **NEW** callback tests for `planning_agent` after_model_callback (currently zero coverage — the removed callback_01 needs a replacement test confirming widget path is now tool-driven)

## Capabilities

### New Capabilities

- `planning-widget-tool`: A `widgetTool` that the planning agent calls after calculations to deliver richContent (table + chips) to the chat UI. Covers all four calculation types: `emergency_fund_gap`, `debt_vs_invest`, `payoff_timeline`, `allocation_split`.

### Modified Capabilities

- `run-planning-calculation`: The tool's return contract changes — `richContent` is now a returned field in the success response (alongside `results` and `agent_action`), replacing the side-effect of writing to `_pending_widget`.

## Impact

- `cxas_app/atlas/tools/run_planning_calculation/python_function/python_code.py` — add `richContent` to return value, remove `context.state["_pending_widget"]` writes
- `cxas_app/atlas/tools/planning_widget/planning_widget.json` — new file
- `cxas_app/atlas/agents/planning_agent/planning_agent.json` — add `planning_widget`, remove `customize_response`
- `cxas_app/atlas/agents/planning_agent/instruction.txt` — add widget call step
- `cxas_app/atlas/agents/planning_agent/after_model_callbacks/after_model_callbacks_01/python_code.py` — remove (widget delivery moves to tool layer)
- `cxas_app/atlas/agents/planning_agent/before_model_callbacks/before_model_callbacks_02/python_code.py` — remove (dead code)
- `cxas_app/atlas/app.json` — remove `_pending_widget` variable declaration
- `evals/callback_tests/` — no new after_model tests needed (callback removed); existing before_model tests unaffected
