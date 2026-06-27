# Architecture

## Agent hierarchy

```
root_agent          — Orchestrator: auth, discovery, routing
├── planning_agent  — Personalized tradeoff calculations (loan vs. invest, savings split)
├── education_agent — Conceptual/educational questions grounded in Northwind knowledge base
└── guardrail_agent — Regulated-advice boundary enforcement + warm advisor handoff
```

`root_agent` owns the full session lifecycle: authentication, discovery conversation, intent classification, and escalation. Sub-agents complete one request and return; `root_agent` resumes.

## GECX app layout (`cxas_app/atlas/`)

```
app.json                                        — App manifest: model, language, session variables, tools, eval thresholds
agents/<name>/
  <name>.json                                   — Descriptor: instruction ref, tools, child agents, callback refs
  instruction.txt                               — Agent persona, hard rules, taskflow (authored manually — no scripts)
  before_agent_callbacks/<n>/python_code.py
  before_model_callbacks/<n>/python_code.py
  after_model_callbacks/<n>/python_code.py
tools/<name>/
  <name>.json                                   — Tool descriptor: schema, description
  python_function/python_code.py                — Tool implementation
```

**Two copies:** `cxas_app/atlas/` is the working copy (edit here); `cxas_app/atlas/Atlas__Financial_Planning_Assistant/` is the platform-synced copy. Always edit the working copy; push with `agents-cli sync`.

## Session state variables

| Variable | Set by | Notes |
|---|---|---|
| `auth_status` | `before_agent_callback` (auth_init) | Never set directly in evals |
| `customer_pin` | Telephony platform / eval session param | |
| `account_snapshot` | `before_agent_callback` (snapshot_init) | Never set directly in evals |
| `discovery_state` | `root_agent` via `set_session_state` | JSON: goals, time_horizon, emergency_fund_status, highest_cost_debt, discovery_complete |
| `_action_trigger` | LLM via `set_session_state` | Read+cleared by `trigger_handler` callback; values: `escalate_to_advisor`, `end_session_clean` |
| `_pending_widget` | Widget-enabled tools | Read+cleared by `widget_injector` after_model_callback |
| `_silence_count` | `silence_handler` callback | Resets on user speech; triggers `end_session` at 3 |

Variables prefixed with `_` are internal — never override in evals.

## Callback pattern

Callbacks are plain Python functions in `python_code.py`. Platform globals `CallbackContext`, `Content`, and `Part` are auto-injected at runtime — **do not import them**. Only standard library imports need explicit `import` statements.

The `before_agent_callback` on `root_agent` combines `auth_init` (runs every unauthenticated turn — intentional, to pick up PIN retries) and `account_snapshot_init` (one-time, guarded). Both use one-way guards on `auth_status` and `account_snapshot` respectively.

## Tools

| Tool | Purpose |
|---|---|
| `retrieve_account_snapshot` | Fetch customer financial state (stub — bank API TBD) |
| `run_planning_calculation` | Debt-vs-invest / savings-split math |
| `search_knowledge_base` | RAG over Northwind product/policy docs |
| `get_northwind_resource_link` | Deep-link to Northwind portal pages |
| `generate_advisor_handoff_summary` | Structured summary for warm advisor transfer |
| `update_language` | Switch conversation language (en-US ↔ de-DE) |
| `set_session_state` | Write arbitrary session variables |
| `verify_pin` | PIN check (delegates to session state) |

Widget-returning tools (`retrieve_account_snapshot`, `run_planning_calculation`, `get_northwind_resource_link`) write a `richContent` blob to `_pending_widget`; the `widget_injector` after_model_callback injects it via `customize_response` in the same turn.

## Code generation rules

- Do NOT write scripts to bulk-generate or auto-patch files. Use the write_file tool manually, or delegate to an approved sub-agent (`lint-fixer`, `eval-writer`).
- Every `instruction.txt` must contain the complete persona, hard rules, and taskflow — no stubs.
- The GECX linter enforces a zero-warnings policy: missing tool docstrings, unreferenced tools, and schema issues are blockers.
- The mock PIN `"atlas-test-pin-v1"` is hardcoded in `root_agent/before_agent_callbacks/before_agent_callbacks_01/python_code.py`. Real auth API integration is tracked in `tdd.md` Known Issues.
