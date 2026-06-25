# Technical Design Document — Atlas, Financial Planning Assistant

> **Living document.** Update before changing agent behavior or evals.
> Update the TDD first, then update evals to match.

---

## Agent Design

### Architecture

**Modality:** Voice-capable, chat-first. Model: `gemini-3.1-flash-live` (confirmed during requirements gathering). Audio modality is active at launch; eval design must account for this (target +4–6 max_turns vs text baselines, similarity thresholds require tuning for natural audio phrasing variation).

**GCP Project:** `financial-advisor-500419` | **Location:** `eu` | **App short name:** `atlas` | **Display name:** `Atlas, Financial Planning Assistant`

**Languages:** English (primary), German. **Switching mode:** explicit-only (user must explicitly request a language switch, e.g., "speak German" / "auf Deutsch bitte"). Auto-detection is not in scope for v1 per configuration decisions confirmed with the user.

**Proposed hierarchy:** multi-agent, because Atlas has 3+ meaningfully distinct CUJs with different toolsets and reasoning styles. The GECX design guide recommends pivoting from single to multi-agent when "you have multiple disjoint CUJs that do not need to share context" or "the role/persona are meaningfully different between use cases."

| Agent | Role | Justification |
|---|---|---|
| `root_agent` | Entry point: PIN-based auth, identity disclosure, discovery conversation, intent classification, proactive opportunity surfacing, language routing. Routes to sub-agents. | PRD: "run a short discovery conversation … before offering any framing." Discovery must happen before any routing; root agent owns this. PRD also requires identity disclosure at session start — a deterministic callback concern. Auth is resolved here before any account-data tools are called. |
| `planning_agent` | Personalized tradeoff analysis: pulls account data, runs planning math, presents side-by-side comparisons. | PRD section "Personalized Tradeoff Analysis": "pulls the customer's real balances, loan APRs, and savings yields, runs the relevant planning math … and presents the options as a clear side-by-side comparison." Distinct toolset (account retrieval + calculation tools) and reasoning mode — quantitative, data-grounded — warrants isolation. |
| `education_agent` | Financial education Q&A grounded in the Northwind knowledge base. | PRD section "Financial Education And Concept Explanation": "answers from Northwind's vetted financial-education knowledge base, clearly distinguishing general educational principles from the customer's specific numbers." KB-dependent, RAG-driven — fundamentally different from the deterministic planning math in `planning_agent`. Separation prevents the LLM from conflating KB-sourced education content with user-specific account figures. |
| `guardrail_agent` | Regulated-advice boundary enforcement: detects, refuses, and redirects requests that constitute licensed advice; performs warm handoff to licensed human advisor. | PRD section "Regulated-Advice Boundary": "boundary must be enforced by a dedicated guardrail observer in code, independent of prompt phrasing." PRD section "Licensed-Advisor Escalation": carries full context summary on handoff. Isolated to prevent guardrail instructions from being diluted by other CUJ context. |

> **Design note:** Proactive opportunity surfacing (PRD section "Proactive Opportunity Surfacing") is handled inside `root_agent` immediately after account snapshot is available and auth is confirmed, before routing to a sub-agent. It is a single, bounded pattern ("surface once, with the quantified benefit") that does not require a dedicated sub-agent. Revisit if surfacing logic grows beyond the single idle-cash pattern.

---

### Tools

| Tool Name | Type | Purpose | Justifying Source |
|---|---|---|---|
| `retrieve_account_snapshot` | API connector | Retrieves the customer's financial state from the bank's system of record: account balances, savings APY, loan balances and APRs, recent cash-flow signals. Idempotent; safe to retry. Returns a structured JSON snapshot stored in `account_snapshot`. Only called after `auth_status` is `"authenticated"`. | PRD "Account Data And Personalization": "retrieve the customer's relevant financial state … reason over real values rather than customer estimates. State must be snapshotted to the session before any calculation, and tools must be idempotent." |
| `run_planning_calculation` | Python function | Deterministic planning math: emergency-fund target and gap, debt-vs-invest comparison (including "guaranteed return" of debt payoff), payoff timelines, proposed allocation splits. Returns results and an explicit `agent_action` instruction for presentation framing, so the model does not invent numbers or framing. | PRD "Planning Calculations And Tradeoff Logic": "run all planning math in deterministic code, not in the model … The calculation tool should return both the results and an explicit instruction for how the agent presents them." |
| `search_knowledge_base` | Data Store (RAG) | Retrieves vetted Northwind financial-education content for conceptual and policy questions. The Northwind knowledge base contains content in **both English and German** (confirmed). The agent queries the KB directly in the user's active language (`active_language`). The translate-around-tool-calls pattern is **not required** because the KB already has native content in both supported languages — no cross-language translation at the tool boundary is needed. | PRD "Financial Education And Knowledge Grounding": "answer conceptual and policy questions from a curated Northwind financial-education knowledge base via retrieval-augmented generation." |
| `get_northwind_resource_link` | Python function | Returns official Northwind URLs (product pages, rate disclosures, advisor scheduling flow) for a given topic. Does not quote rates or terms inline — points to the official source of record. | PRD "Official Resource And Product Guidance": "point customers to official Northwind destinations … without completing the action. Must not quote rates or terms that conflict with the official source of record." |
| `generate_advisor_handoff_summary` | Python function | Assembles and returns a structured handoff summary: identity-verified context, discovery answers (goals, time horizon, safety net, highest-cost debt), any proposed framing, and the open question that triggered escalation. Passed to the advisor routing/calendar system on transfer. | PRD "Licensed-Advisor Escalation": "delivers a generated summary to the advisor — verified context, the discovery answers, any proposed framing, and the open question — so the customer does not repeat themselves." |
| `update_language` | Python function | Gates explicit language-switch requests by updating `active_language` in session state. Must be called before the first response in the new language. Required per `gecx-design-guide.md` → "The `update_language` Tool" for `gemini-3.1-flash-live` multilingual agents. Supports: `"English"`, `"German"`. | Configuration decisions: English + German, explicit-only switching mode; gecx-design-guide.md multilingual failure mode 2 mitigation. |
| `set_session_state` | Python function | Writes a key-value pair to session state. Used by the trigger pattern: the LLM sets a state flag (e.g., `_action_trigger = "escalate_to_advisor"`), the `before_model_callback` reads it and returns deterministic tool calls. Required on every agent that uses the trigger pattern. | gecx-design-guide.md "Trigger pattern for deterministic tool calls": "The state-setting tool MUST be in the agent's tool list. In multi-agent architectures, the trigger-handling callback must exist on ALL agents." |
| `end_session` | System | Terminates the session. Used by the escalation trigger pattern (via callback), by the guardrail agent after warm handoff completes, and by the silence-detection callback after 3 consecutive silence events. Cannot be called from callbacks — callbacks construct the `LlmResponse` that includes the system tool call. | GECX platform standard. |

> **TODO — advisor routing/calendar system:** PRD states "Licensed-advisor availability and scheduling should come from the advisor routing/calendar system, not be asserted by the agent." A tool to check availability and initiate the scheduling flow will be needed. The API endpoint and authentication method are not specified in the PRD. **Recommend: confirm the advisor routing system API details with the team before scaffolding.**

> **TODO — proactive opportunity surfacing trigger:** PRD describes one pattern for v1: idle cash in a low-yield account. The `retrieve_account_snapshot` tool provides the data. Whether surfacing logic is embedded in `root_agent` instructions or triggered by a dedicated Python function is a design choice. Recommend embedding in `root_agent` instructions using account snapshot data, with a guardrail in the instruction to surface "once only." If surfacing rules grow, extract to a dedicated tool.

---

### Routing Logic

**Session start → root_agent:**

**Auth flow (pre-discovery, pre-routing):**
- `root_agent` `before_agent_callback` (`auth_init`) fires at session start. It reads `customer_pin` from session parameters and compares it to the hardcoded mock PIN value. The result is written to `auth_status` (`"authenticated"` or `"unauthenticated"`). This happens before any LLM call, before identity disclosure, and before account retrieval.
- If `auth_status = "authenticated"`: the session proceeds to the standard flow described below.
- If `auth_status = "unauthenticated"`: `root_agent` enters a PIN-retry loop. The LLM prompts the customer to re-enter their PIN (up to **3 total attempts**). On each retry, `root_agent` re-invokes the auth check (via `set_session_state` trigger or direct callback re-evaluation). If the customer fails 3 attempts, `root_agent` triggers auth-lockout: it informs the customer that account access is locked and calls `end_session` directly. Auth-lockout is treated as a terminal state; no planning or education features are available. No warm handoff is performed.

> **Auth note — v1 mock:** For v1, the PIN check is mocked with a hardcoded value (real auth API is out of scope). `auth_status` is derived entirely in `before_agent_callback`; it is **NEVER overridden in evals** — use mock session parameters (`customer_pin`) to drive auth outcomes in test scenarios instead.

**Post-auth standard flow:**
- `root_agent` discloses identity at the start of substantive interactions (PRD "Identity": "Atlas should introduce itself as 'Atlas, Northwind's planning assistant,' and proactively disclose … that it provides educational guidance and is not a licensed financial advisor."). This is enforced by `before_model_callback` (deterministic greeting pattern) rather than relying on the LLM to remember to disclose.
- `root_agent` calls `retrieve_account_snapshot` (idempotent, safe to call at session start). If account data is available, it checks for the proactive opportunity-surfacing pattern (PRD: "large balance earning near-zero interest while a high-yield product exists") and surfaces once if triggered.
- `root_agent` runs the discovery conversation — near-term goals, time horizon, current safety net, highest-cost debt — "gathering only what it needs to reason responsibly before offering any framing" (PRD "Financial Discovery And Goal Setting"). Discovery answers are stored in `discovery_state`.

**Intent classification → sub-agent routing (from root_agent):**

| User intent | Route to | Justifying source |
|---|---|---|
| Personalized tradeoff (balance-based, rate-based, allocation math) | `planning_agent` | PRD "Personalized Tradeoff Analysis" |
| Conceptual / policy question ("what is an emergency fund," "what does APR mean") | `education_agent` | PRD "Financial Education And Concept Explanation" |
| Regulated advice request (specific security/fund, suitability, tax/legal, return prediction) | `guardrail_agent` | PRD "Regulated-Advice Boundary": "detect and refuse requests that constitute licensed advice" |
| Customer requests a licensed advisor, or boundary is hit during any sub-agent flow | `guardrail_agent` | PRD "Licensed-Advisor Escalation": "escalate to a licensed human advisor on request or when the boundary is hit" |

**Sources do not specify routing rules for:** re-entry after a sub-agent completes (e.g., does root_agent resume or does the session end?), or how to handle mixed intents in a single turn (e.g., "explain APR and then tell me which fund to buy"). **Recommend: default to root_agent resuming after sub-agent returns; flag mixed intents to guardrail_agent for the regulated portion.**

**Language routing:** At any point, if the user explicitly requests a language switch, `update_language` is called before the next response. The `<language_detection>` instruction block (gecx-design-guide.md) is appended to every agent's instruction. All agents carry the `update_language` tool.

---

### Variables

| Variable | Schema | Source | Notes |
|---|---|---|---|
| `customer_id` | `string` | Session parameter (provided by the caller / telephony platform) | Required for `retrieve_account_snapshot`. If absent, account-grounded features are unavailable; agent falls back to education-only mode. |
| `customer_pin` | `string` | Session parameter (provided by the caller / telephony platform at session start) | PIN submitted by the customer for identity verification. Read by `auth_init` callback in `before_agent_callback` on `root_agent`. Never logged or included in handoff summaries. |
| `auth_status` | `string`, enum: `"authenticated"` \| `"unauthenticated"` | Derived: set by `auth_init` `before_agent_callback` on `root_agent` by comparing `customer_pin` to hardcoded mock value (v1) | **NEVER override in evals.** Use `customer_pin` session parameter to drive auth outcomes. When `auth_status = "unauthenticated"`, account-data tools are blocked and the agent enters the PIN-retry/lockout flow. |
| `auth_attempt_count` | `integer`, default: `0` | Incremented by `root_agent` on each failed PIN attempt (via `set_session_state`) | Tracks retry count. When `auth_attempt_count >= 3`, auth-lockout flow triggers. |
| `active_language` | `string`, enum: `"English"` \| `"German"` | Session parameter (default: `"English"`); updated by `update_language` tool | Determines response language across all agents. |
| `account_snapshot` | JSON object — fields TBD pending API spec: at minimum `{savings_accounts: [...], loan_accounts: [...], checking_balance: float, snapshot_timestamp: string}` | Derived: populated by `retrieve_account_snapshot` call in `root_agent` `before_agent_callback` | **NEVER override in evals** — this is callback-derived from a live API call. Use mock tool responses in evals instead. Fields depend on the bank's system-of-record API spec: **TBD.** Only populated when `auth_status = "authenticated"`. |
| `discovery_state` | JSON object: `{goals: string, time_horizon: string, emergency_fund_status: string, highest_cost_debt: string, discovery_complete: bool}` | Built progressively by `root_agent` during discovery conversation; updated via `set_session_state` | Passed to `planning_agent` and `guardrail_agent` to avoid repeating discovery questions. `discovery_complete` gates routing to planning or education sub-agents. |
| `_action_trigger` | `string`, enum: `"escalate_to_advisor"` \| `"end_session_clean"` (extend as needed) | Set by LLM via `set_session_state`; read and cleared by `before_model_callback` | **NEVER override in evals.** Underscore prefix marks it as an internal observability/trigger variable per gecx-design-guide.md naming convention. |
| `guardrail_trigger_log` | JSON array: `[{timestamp, triggering_intent, guardrail_type}]` | Appended by `guardrail_agent` on each boundary-enforcement event | Supports PRD requirement: "Log every guardrail trigger … to identify coverage gaps and tune the instruction layers above it." Used for observability, not routing. |

---

### Callbacks

| Callback | Agent | Type | Purpose | Justifying Source |
|---|---|---|---|---|
| `auth_init` | `root_agent` | `before_agent_callback` | Fires at session start (once per session; guarded with early-return check). Reads `customer_pin` and compares it to the hardcoded mock value. Writes `auth_status` (`"authenticated"` or `"unauthenticated"`) to session state. If unauthenticated, sets `auth_attempt_count = 0`. Does **not** call `retrieve_account_snapshot` — that only runs after auth succeeds. | PRD "Account Data And Personalization": "gate account-data access behind identity verification." v1 config: PIN-based auth, mocked hardcoded value. gecx-design-guide.md `before_agent_callback` pattern for derived variables. |
| `deterministic_greeting` | `root_agent` | `before_model_callback` | Intercepts session start (first model call) only when `auth_status = "authenticated"`, and returns the static identity disclosure + greeting, bypassing the LLM. Prevents the agent from skipping or varying the disclosure. Skips (no-op) during the auth/PIN-retry phase. | PRD "Identity": "proactively disclose at the start of substantive interactions that it provides educational guidance and is not a licensed financial advisor." gecx-design-guide.md "Deterministic greeting" callback pattern. |
| `account_snapshot_init` | `root_agent` | `before_agent_callback` | Calls `retrieve_account_snapshot` using `customer_id` after `auth_status = "authenticated"` is confirmed. Writes result to `account_snapshot`. If `customer_id` is absent or API fails, writes a fallback state and sets a flag so `root_agent` knows to operate in education-only mode. Runs once per session (guard with early-return check). Does not run when `auth_status = "unauthenticated"`. | PRD "Account Data And Personalization": "State must be snapshotted to the session before any calculation." gecx-design-guide.md: `before_agent_callback` for profile variable derivation. |
| `silence_handler` | `root_agent` | `before_model_callback` | Detects consecutive silence events from the voice channel. Tracks a running count of consecutive silences in session state. After **3 consecutive silence events**, constructs and returns an `LlmResponse` that calls `end_session`, bypassing the LLM. Resets the counter if the user speaks. Standard voice pattern for audio-modality agents. | gecx-design-guide.md "Callback Patterns for Deterministic Behavior" — "Silence handling (voice): `before_model_callback` detects 'no user activity' signals, tracks counter in state, ends session after 3 silences." |
| `trigger_handler` | `root_agent`, `planning_agent`, `education_agent`, `guardrail_agent` | `before_model_callback` | Reads `_action_trigger`; if set to `"escalate_to_advisor"`, calls `generate_advisor_handoff_summary` and returns an `LlmResponse` combining the farewell text and the advisor transfer — deterministically, bypassing the LLM. Clears `_action_trigger` after firing. | PRD "Licensed-Advisor Escalation": warm handoff with full context. gecx-design-guide.md: "Trigger pattern for deterministic tool calls" and "In multi-agent architectures, the trigger-handling callback must exist on ALL agents." |
| `farewell_injection` | `root_agent`, `guardrail_agent` | `after_model_callback` | Detects when the LLM is about to call `end_session` (or `escalate_to_advisor` trigger fires) and injects the closing text before the session ends. Checks `callback_context.events` to avoid double-injection on multi-model-call turns. | gecx-design-guide.md "Deterministic farewell" pattern: "LLM often calls `end_session` without speaking first." |
| `guardrail_logger` | `guardrail_agent` | `after_model_callback` | After a guardrail refusal fires, appends an entry to `guardrail_trigger_log` with timestamp, the triggering intent category, and which guardrail boundary was hit. | PRD "Safety, Brand, And Trust Requirements": "Log every guardrail trigger (which guardrail, the triggering scenario, what the user was trying to do) to identify coverage gaps." |

> **Design note — guardrail enforcement:** The PRD requires the regulated-advice boundary to be "enforced by a dedicated guardrail observer in code, independent of prompt phrasing." The `guardrail_agent` sub-agent is the code-level isolation mechanism. Within it, the `trigger_handler` callback ensures the advisor transfer and farewell text fire deterministically even if the LLM omits the tool call. The instruction alone is insufficient for a compliance-critical boundary — callbacks provide the safety net.

> **Design note — auth callback ordering:** `auth_init` and `account_snapshot_init` are both `before_agent_callback` on `root_agent`. `auth_init` must run first and its result (`auth_status`) must be checked before `account_snapshot_init` attempts to call `retrieve_account_snapshot`. Implement as a single combined `before_agent_callback` that executes auth check first, then conditionally runs account retrieval, to avoid ordering ambiguity.

---

## Eval Design

### Coverage Map

| Requirement | Eval Type | Rationale | Priority | Severity | Tags |
|---|---|---|---|---|---|
| Auth success: correct PIN → `auth_status = "authenticated"`, session proceeds | Golden | Callback-enforced; `auth_status` derived deterministically from PIN comparison | P0 | NO-GO | `auth, identity-verification, FR-auth` |
| Auth failure / retry: incorrect PIN → retry prompt, `auth_attempt_count` increments | Golden | Deterministic counter increment and retry prompt; assert LLM prompts for re-entry and count updates | P0 | NO-GO | `auth, retry, FR-auth` |
| Auth lockout: 3 failed attempts → lockout message + direct `end_session` | Golden | Callback-enforced terminal state after 3 attempts; deterministic; no warm handoff | P0 | NO-GO | `auth, lockout, FR-auth` |
| Account data blocked when unauthenticated | Golden | `retrieve_account_snapshot` must NOT be called when `auth_status = "unauthenticated"`; assert tool absence | P0 | NO-GO | `auth, account-data, FR-auth` |
| Identity disclosure at session start (authenticated users only) | Golden | Callback-enforced (deterministic greeting), fixed output, fires only post-auth | P0 | NO-GO | `identity, disclosure, FR-identity` |
| Discovery conversation runs before any framing | Golden | Deterministic flow: root_agent asks discovery questions in fixed sequence; `discovery_complete` flag gates routing | P0 | NO-GO | `discovery, routing, FR-discovery` |
| Account data retrieved from system of record (not model memory) | Golden | Tool call is deterministic; assert `retrieve_account_snapshot` is called and `account_snapshot` is populated before any planning response | P0 | NO-GO | `account-data, tool-call, FR-account` |
| Personalized tradeoff analysis uses real account figures | Golden | `run_planning_calculation` is called with snapshot values; output asserts no figures appear that weren't returned by the tool | P0 | NO-GO | `planning, numerical-accuracy, FR-planning` |
| Planning calculation returns side-by-side comparison, never a single directive | Sim | LLM presentation of the comparison naturally varies; assert behavioral goal (comparison present, no directive "you should buy X") | P0 | HIGH | `planning, comparison-format, FR-planning` |
| Financial education Q&A grounded in Northwind KB | Sim | KB retrieval returns varying results per query; behavioral goal is that the answer cites KB content and separates it from personal figures | P1 | HIGH | `education, kb-grounding, FR-education` |
| Education response separates general principles from personal figures | Sim | Behavioral goal (no blending of KB content and account numbers) requires LLM-as-judge | P1 | HIGH | `education, separation, FR-education` |
| KB query issued in user's active language (EN or DE) | Golden | `search_knowledge_base` query must use `active_language`; assert the query language matches the active session language for both EN and DE sessions | P1 | HIGH | `multilingual, kb-language, FR-language` |
| Regulated-advice guardrail: specific security/fund selection refused | Golden | Trigger-based: instruction detects intent → `set_session_state(_action_trigger="escalate_to_advisor")` → callback fires deterministically | P0 | NO-GO | `guardrail, boundary, FR-guardrail` |
| Regulated-advice guardrail: suitability / KYC request refused | Golden | Same trigger pattern — deterministic | P0 | NO-GO | `guardrail, boundary, FR-guardrail` |
| Regulated-advice guardrail: tax or legal advice request refused | Golden | Same trigger pattern — deterministic | P0 | NO-GO | `guardrail, boundary, FR-guardrail` |
| Regulated-advice guardrail: return prediction / market timing refused | Golden | Same trigger pattern — deterministic | P0 | NO-GO | `guardrail, boundary, FR-guardrail` |
| Guardrail refusal uses constructive redirect (not flat "I can't") | Sim | Phrasing naturally varies; behavioral goal is presence of constructive redirect + advisor offer | P0 | HIGH | `guardrail, redirect, FR-guardrail` |
| Warm handoff carries full context summary to advisor | Golden | `generate_advisor_handoff_summary` is called with `discovery_state` and open question; assert tool is called and `end_session` (transfer) follows | P0 | HIGH | `handoff, context-summary, FR-handoff` |
| Advisor handoff: customer does not repeat discovery answers | Sim | Behavioral goal; judge verifies summary contains discovery data | P1 | HIGH | `handoff, discovery-state, FR-handoff` |
| Proactive opportunity surfacing: surfaces once, with quantified benefit | Golden | Rule is deterministic (if account_snapshot shows idle cash in low-yield account, surface once); assert `run_planning_calculation` is called and surfacing happens before routing | P1 | HIGH | `proactive, opportunity, FR-proactive` |
| Proactive surfacing does not pressure or upsell | Sim | Behavioral goal (tone/framing); LLM-as-judge for salesy language | P1 | MEDIUM | `proactive, tone, FR-proactive` |
| Language switch: explicit German request handled correctly | Golden | `update_language` tool call is deterministic on explicit request; subsequent response in German | P1 | HIGH | `multilingual, language-switch, FR-language` |
| Language switch: stays in current language for short/ambiguous utterances | Golden | `update_language` NOT called on single-word or ambiguous input; deterministic absence of tool call | P1 | HIGH | `multilingual, language-guardrail, FR-language` |
| Silence handling: 3 consecutive silences → end_session | Golden | Callback-enforced (`silence_handler`): assert `end_session` is called after exactly 3 consecutive silence events; assert session does NOT end after 1 or 2 silences | P1 | HIGH | `voice, silence-handling, FR-voice` |
| Silence reset: user speaks after silence, counter resets | Golden | Assert silence counter resets to 0 on a non-silence event; session continues normally | P1 | MEDIUM | `voice, silence-handling, FR-voice` |
| No fabricated figures: all personalized numbers trace to a tool call | Golden | Assert zero personalized numeric values in the response that are not present in tool call outputs for that turn | P0 | NO-GO | `numerical-accuracy, hallucination, FR-accuracy` |
| Atlas does not impersonate a human or licensed advisor | Sim | Behavioral goal — adversarial probe ("are you a real advisor?"); judge verifies correct denial | P0 | NO-GO | `identity, trust, FR-identity` |
| Guardrail trigger logged (observability) | Golden | Assert `guardrail_trigger_log` is updated after each boundary event | P2 | LOW | `observability, logging, FR-guardrail` |
| Account API failure: graceful fallback to education-only mode | Golden | Callback-enforced: if `retrieve_account_snapshot` fails, flag is set and root_agent routes to education-only; assert no account figures are cited | P1 | HIGH | `error-handling, resilience, FR-account` |

> **Already covered:** None — this is an initial draft TDD; no evals exist yet.

> **Note — translate-around-tool-calls (future consideration):** The Northwind KB is confirmed bilingual (EN + DE), so the translate-around-tool-calls pattern is not required for v1. If additional languages are added in a future release and the KB does not have native content in those languages, this pattern should be revisited per `gecx-design-guide.md` → "Multilingual Agents — Failure Mode 1."

> **TODO — audio eval tuning:** All evals will run against a `gemini-3.1-flash-live` audio model. This requires: (a) `max_turns` set higher than text baselines (add +4–6 per eval, per interview-guide.md Round 1 note on audio modality), (b) similarity thresholds calibrated for natural audio phrasing variation. Calibrate after the first eval run and record in Pass Rate History.

---

### Test Data

No customer profiles or mock data artifacts were provided for this dispatch. The following profiles represent the minimum needed to cover the Coverage Map above. They are proposed (not sourced from a fixture file) and must be validated against the actual bank system-of-record API schema before use.

| Profile | `customer_id` | `customer_pin` | `account_snapshot` (representative) | Scenario |
|---|---|---|---|---|
| Authenticated — windfall allocator | TBD | `"correct-pin"` (mock) | Checking: high balance; savings APY: low; no loans | Triggers proactive opportunity surfacing; routes to planning_agent after discovery |
| Authenticated — debt vs save | TBD | `"correct-pin"` (mock) | Checking: moderate balance; 1 loan at high APR | Does not trigger opportunity surfacing; routes to planning_agent for debt-vs-invest calc |
| Authenticated — early-stage saver | TBD | `"correct-pin"` (mock) | Checking: low balance; no savings account; no loans | Routes to planning_agent for emergency-fund gap calculation |
| Authenticated — education seeker | TBD | `"correct-pin"` (mock) | Any (education path does not depend on specific balances) | Routes to education_agent; no personalized figures cited |
| Auth failure — 1st attempt | N/A | `"wrong-pin-1"` (mock) | N/A | Asserts retry prompt and `auth_attempt_count = 1` |
| Auth failure — lockout (3rd attempt) | N/A | `"wrong-pin-3"` (mock, 3rd attempt in sequence) | N/A | Asserts lockout message and direct `end_session`; no warm handoff |
| Unauthenticated / API failure | N/A | `"correct-pin"` (mock), `customer_id` absent or API error | `account_snapshot` absent (API error path) | Tests fallback to education-only mode; assert no account figures cited |
| Adversarial — regulated advice seeker | TBD | `"correct-pin"` (mock) | Any | Asks for specific fund/security recommendation; guardrail_agent fires; warm handoff triggered |
| German-language user | TBD | `"correct-pin"` (mock) | Any | Explicitly requests German; `update_language` called; response in German; KB queried in German |
| Voice — silence scenario | TBD | `"correct-pin"` (mock) | Any | 3 consecutive silence events sent; assert `end_session` fires |

> **TODO:** Replace all `customer_id: TBD` values with real test account IDs from the bank's sandbox/staging environment. Confirm `account_snapshot` field names and types against the actual API spec. Define the mock PIN value convention for the test harness (e.g., a constant like `"atlas-test-pin-v1"`) and document it here once agreed.

---

## Tracking

### Pass Rate History

| Date | Goldens | Sims | Tool Tests | Callback Tests | Notes |
|---|---|---|---|---|---|
| — | — | — | — | — | No runs yet |

---

### Known Issues

- **Auth API (v1 mock):** Authentication is implemented in v1 with a hardcoded mock PIN value. The real auth API integration is out of scope for v1. When a real auth API is available, replace the `auth_init` callback's PIN comparison logic with an API call; `auth_status` derivation and the "NEVER override in evals" constraint remain unchanged.
- **Advisor routing/calendar system API unspecified:** PRD requires licensed-advisor availability and scheduling to come from a routing/calendar system, but no API endpoint, authentication method, or data contract is described. A tool for this must be designed before scaffolding is complete. **Open: provide API spec.**
- **Bank system-of-record API unspecified:** `retrieve_account_snapshot` is proposed, but the API endpoint, auth method, response schema (field names, types, units), and failure modes are not in the PRD. **Open: provide API spec and sandbox credentials.**
- **Mock PIN value convention:** Resolved — v1 hardcoded mock PIN is `"atlas-test-pin-v1"`. All authenticated test profiles use `customer_pin: "atlas-test-pin-v1"`.
- **Silence counter variable name:** Resolved — named `_silence_count` (underscore prefix per gecx-design-guide.md naming convention).
- **Auth-lockout escalation path:** Resolved — auth lockout calls `end_session` directly (no warm handoff).
- **Proactive opportunity surfacing policy unspecified:** PRD Open Questions section acknowledges: "What is the approved policy for proactive opportunity surfacing — which signals qualify, and what frequency/consent model is acceptable?" The TDD assumes the single idle-cash pattern described in the PRD body, but additional signals or a consent model may constrain or expand this. **Open: compliance sign-off needed.**
- **Regulatory / compliance disclosure requirements unspecified:** PRD Open Questions section: "Which exact regulatory and compliance review requirements … apply to an unlicensed advisory assistant for Northwind?" Specific disclosure language, recordkeeping obligations, and jurisdiction limits may affect the identity disclosure callback content and guardrail boundary definitions. **Open: legal/compliance review needed before production launch.**
- **Tax-adjacent education boundary unspecified:** PRD Open Questions section: "Where is the precise line on tax-adjacent education … versus regulated tax advice, and who signs off?" This affects `guardrail_agent` instruction boundary definition and Coverage Map test cases for tax-adjacent queries. **Open: compliance sign-off needed.**
- **GCS eval bucket:** `gs://atlas-financial-advisor-evals` will be created during implementation. Use this name in eval configuration.
- **No sample conversations, mock data, or customer profiles were provided:** The Coverage Map rows are derived from PRD requirement statements only. Once sample conversations are available, revisit Coverage Map to add or refine rows, and populate Test Data with real profile IDs.

---

### Changelog

| Date | Change | Author |
|---|---|---|
| 2026-06-24 | Initial requirements-derived TDD draft (sources: `advisory-financial-planning-agent-prd.md`, configuration decisions confirmed during requirements gathering) | tdd-writer |
| 2026-06-24 | Applied three user-approved change requests: (1) Added PIN-based auth — `customer_pin` session param, `auth_status` callback-derived variable (NEVER override in evals), `auth_init` before_agent_callback, auth routing branch (retry loop up to 3 attempts, lockout), auth test profiles, and auth coverage map rows (success, failure/retry, lockout, account-data blocked when unauth). (2) Updated `search_knowledge_base` — Northwind KB confirmed bilingual (EN + DE); translate-around-tool-calls pattern not required; updated tool note and replaced coverage row with KB-query-language assertion row; retained translate-around as future consideration note. (3) Added silence handling — `silence_handler` before_model_callback on root_agent tracks consecutive silences, end_session after 3; added silence reset; added two coverage map rows (lockout at 3 silences, reset on user speech); added silence test profile; resolved open question on silence handling. | tdd-writer |

---

*Review and approve before scaffolding the agent.*
