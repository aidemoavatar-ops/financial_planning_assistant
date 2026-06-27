## Capability: run-planning-calculation

**Change type:** Modified — return contract extended to include `richContent`.

### What changes

The tool's success response now includes a `richContent` field containing the widget payload. Previously, `richContent` was written to `_pending_widget` session state as a side effect — it did not appear in the tool response. That side effect is removed.

### Current return contract (before this change)

```python
# On success
{
    "status": "success",
    "calculation_type": str,   # e.g. "emergency_fund_gap"
    "results": dict,            # numeric outputs
    "agent_action": str         # exact presentation instruction
}
# richContent was NOT in the return value — stored in context.state["_pending_widget"] instead
```

### New return contract (after this change)

```python
# On success
{
    "status": "success",
    "calculation_type": str,   # e.g. "emergency_fund_gap"
    "results": dict,            # numeric outputs (unchanged)
    "agent_action": str,        # exact presentation instruction (updated — see below)
    "richContent": list         # [[{type, ...}, ...]] — widget payload for planning_widget
}
# context.state["_pending_widget"] is NO LONGER written
```

### agent_action field changes

For `debt_vs_invest` and `allocation_split`, the current `agent_action` text incorrectly ends with:
> "Then call `{@TOOL: customize_response}` with the 'richContent' value from this tool response as the richContent argument."

This instruction references `customize_response` (wrong tool) and claims richContent is in the tool response (it wasn't). Both errors are fixed:
- Replace `{@TOOL: customize_response}` with `{@Widget: planning_widget}`.
- The widget call instruction is added uniformly to all four calculation types.

**Updated agent_action suffix for all four types:**
> "Then call `{@Widget: planning_widget}` with the `richContent` array from this response as the `richContent` argument — pass it verbatim, do not modify."

The `emergency_fund_gap` and `payoff_timeline` types currently have no widget call in their `agent_action`. This change adds the suffix to all four.

### Side effects removed

- `context.state["_pending_widget"] = json.dumps(rich_content["richContent"])` — remove this line (line 342 in current code).
- The `json` import remains (still used for `json.loads(snapshot_raw)` and other calls).

### Error responses — unchanged

All error response shapes are unchanged. `richContent` is only present on `status: "success"` responses.

### Docstring update

The function's `Returns:` docstring block is updated to document the new `richContent` field:

```
'richContent' (list): On success — the richContent array for planning_widget.
    Pass to {@Widget: planning_widget} verbatim.
```
