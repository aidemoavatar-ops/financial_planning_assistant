## Context

The current widget delivery mechanism is:
1. `run_planning_calculation` builds a `richContent` payload and writes it to `_pending_widget` session state.
2. An `after_model_callback` (widget_injector) reads `_pending_widget` on the next model call and appends `Part.from_function_call(name="customize_response", args={"richContent": ...})` to the LlmResponse.

The GECX rich response widget documentation specifies that rich content must be delivered through a **`widgetTool`** — a dedicated tool descriptor with a JSON schema — called by the agent (LLM). `customize_response` injected from a callback is not processed as a widget render by the platform. The callback-based approach silently fails.

The `retrieve_account_snapshot` and `get_northwind_resource_link` tools on `root_agent` have the same broken pattern but are out of scope for this change (tracked separately).

## Goals / Non-Goals

**Goals:**
- Widgets (table + chips / info + chips) appear in the chat UI for all four planning calculation types.
- Voice output is preserved — LLM still speaks the verbal summary; the widget is supplementary.
- Dead callback code is removed.
- The fix follows the documented GECX widgetTool mechanism.

**Non-Goals:**
- Fixing the same broken pattern on `root_agent` (`retrieve_account_snapshot`, `get_northwind_resource_link`) — separate issue.
- Changing the calculation math in `run_planning_calculation`.
- Adding custom widget templates beyond what the platform provides.

## Decisions

### Decision 1: One shared `planning_widget` tool, not four separate tools

**Chosen:** A single `planning_widget` widgetTool that accepts a generic `richContent` array.

**Alternative:** Four separate tools (`emergency_fund_widget`, `debt_vs_invest_widget`, etc.), each with a typed schema matching its specific output.

**Rationale:** `run_planning_calculation` already owns the richContent structure. Separate tools would duplicate the schema in four places and require four instruction entries. One generic tool keeps things DRY and matches how the platform handles custom widgets (free-form JSON parameters).

---

### Decision 2: Return `richContent` from `run_planning_calculation` — do not pass through session state

**Chosen:** Add `"richContent": rich_content["richContent"]` to the tool's success return dict.

**Alternative:** Keep `_pending_widget` session state and have the widget tool read from it.

**Rationale:** Passing richContent via session state adds indirection and requires the callback machinery. Returning it directly in the tool response lets the LLM pass it to the widget tool in a single model call, which is the platform's intended pattern. The LLM is instructed to pass the value verbatim, reducing hallucination risk.

---

### Decision 3: `agent_action` drives widget call — no new instruction subtask

**Chosen:** The `agent_action` field in the tool response includes the `{@Widget: planning_widget}` call instruction. The existing `Present_Comparison` step in instruction.txt says "follow the agent_action exactly."

**Alternative:** Add a dedicated `<step name="Show_Widget">` to instruction.txt.

**Rationale:** `agent_action` already drives how results are presented. Adding the widget call there keeps the instruction lean and avoids duplicating the widget call trigger in two places. The existing "follow the agent_action exactly" rule covers it.

---

### Decision 4: Remove `after_model_callbacks_01` entirely — no replacement

**Chosen:** Delete the file; update `planning_agent.json` to have an empty `afterModelCallbacks` array.

**Alternative:** Keep the callback but make it a no-op / redirect to the new tool path.

**Rationale:** The callback's sole purpose was widget injection. With widget delivery moving to the tool layer, the callback has no remaining function. Leaving dead callbacks adds confusion and cognitive overhead.

## Risks / Trade-offs

**Risk: LLM does not pass `richContent` verbatim to the widget tool**
→ Mitigation: `agent_action` text explicitly says "pass the `richContent` array from this response to `{@Widget: planning_widget}` verbatim — do not modify it." Eval golden conversations will verify the widget call is made with correct args. If the LLM corrupts the data, the widget renders incorrectly (visible failure, not silent) — easier to catch and fix than the current silent non-render.

**Risk: `planning_widget` widgetTool schema needs to match the platform's expected format**
→ Mitigation: The `widgetTool` JSON schema is set to accept a free-form `richContent` array (custom widget type), consistent with the GECX documentation's "write your own JSON parameters" path. If the platform has stricter validation, the linter (`agents-cli lint`) will surface it before deployment.

**Risk: Removing `customize_response` from planning_agent tools breaks existing goldens**
→ Mitigation: `customize_response` was never successfully called (widget never appeared), so no goldens should depend on it. Run `agents-cli eval run` after the change to confirm.

## Migration Plan

1. Create `planning_widget` widgetTool descriptor.
2. Update `run_planning_calculation` to return `richContent`.
3. Update `planning_agent` instruction (via agent_action strings — no instruction.txt change needed).
4. Register `planning_widget` in `planning_agent.json`; remove `customize_response`.
5. Delete `after_model_callbacks_01/python_code.py`; remove from `planning_agent.json`.
6. Delete `before_model_callbacks_02/python_code.py` (unregistered dead code).
7. Remove `_pending_widget` from `app.json` variable declarations.
8. Run `agents-cli lint --config gecx-config.json` — 0 errors, 0 warnings required.
9. Run `pytest evals/callback_tests/tests/ -v` — all tests must pass.
10. Run `agents-cli eval run --config gecx-config.json`.

**Rollback:** Revert the commit. The old code is preserved in git history. No data migrations required — `_pending_widget` is ephemeral session state.

## Open Questions

- Does the `planning_widget` widgetTool need to be registered in `app.json` top-level `tools` array, or only in `planning_agent.json`? (The `run_planning_calculation` tool follows agent-level registration only — assume same pattern.)
- Does removing `customize_response` from `planning_agent.json` tools affect the linter? (`customize_response` is a system tool; the linter T008 rule checks custom tools only.)
