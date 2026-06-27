## 1. Feature Branch

- [x] 1.1 Create feature branch: `git checkout -b feature/3-widget-tool-delivery`

## 2. New widgetTool

- [x] 2.1 Create `cxas_app/atlas/tools/planning_widget/planning_widget.json` with `widgetTool` type, name, description, and `richContent` JSON schema
- [x] 2.2 Verify linter accepts the new tool: `agents-cli lint --config gecx-config.json`

## 3. Update run_planning_calculation

- [x] 3.1 Add `"richContent": rich_content["richContent"]` to the success return dict for all four calculation types
- [x] 3.2 Remove `context.state["_pending_widget"] = json.dumps(rich_content["richContent"])` (line 342)
- [x] 3.3 Update `agent_action` for `debt_vs_invest` and `allocation_split` — replace `{@TOOL: customize_response}` with `{@Widget: planning_widget}` and update the suffix to match the new widgetTool call pattern
- [x] 3.4 Add the `{@Widget: planning_widget}` call suffix to `agent_action` for `emergency_fund_gap` and `payoff_timeline` (currently missing)
- [x] 3.5 Update the function's `Returns:` docstring to document the new `richContent` field

## 4. Update planning_agent.json

- [x] 4.1 Add `"planning_widget"` to the `tools` array
- [x] 4.2 Remove `"customize_response"` from the `tools` array
- [x] 4.3 Remove the `"afterModelCallbacks"` entry for `after_model_callbacks_01` (set to empty array `[]`)

## 5. Update planning_agent instruction.txt

- [x] 5.1 Add a step in the taskflow that instructs the agent to call `{@Widget: planning_widget}` immediately after `run_planning_calculation` returns success, passing `richContent` from the tool response verbatim

## 6. Remove dead code and state

- [x] 6.1 Delete `cxas_app/atlas/agents/planning_agent/after_model_callbacks/after_model_callbacks_01/python_code.py`
- [x] 6.2 Delete `cxas_app/atlas/agents/planning_agent/before_model_callbacks/before_model_callbacks_02/python_code.py` (unregistered dead code)
- [x] 6.3 Remove the `_pending_widget` entry from `variableDeclarations` in `cxas_app/atlas/app.json`

## 7. Quality gates

- [x] 7.1 Run linter: `agents-cli lint --config gecx-config.json` — 0 errors, 0 warnings required
- [x] 7.2 Run callback tests: `pytest evals/callback_tests/tests/ -v` — all must pass
- [ ] 7.3 Run evals: `agents-cli eval run --config gecx-config.json`

## 8. Pull Request

- [ ] 8.1 Commit all changes with message referencing issue #3
- [ ] 8.2 Open PR with `Closes #3` and OpenSpec change path `openspec/changes/issue-3-widget-tool-delivery/`
