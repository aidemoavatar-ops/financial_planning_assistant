# Experiment Log

Tracking what was tried, results across all eval types, and failure details.

## Iteration 1 — 2026-06-24
**Change:** Initial baseline

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/42 (0%) |

**Golden failures:**
- `SCORES_PASS_BUT_FAIL` planning_calculation_uses_real_figures x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` discovery_before_framing x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` guardrail_specific_fund_selection_refused x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` auth_success_correct_pin x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` guardrail_return_prediction_refused x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` account_data_from_tool_not_memory x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` auth_lockout_three_failures x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` auth_failure_first_retry x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` warm_handoff_full_context_summary x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` no_fabricated_figures_all_trace_to_tools x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` guardrail_suitability_kyc_refused x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` account_data_blocked_unauthenticated x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` identity_disclosure_authenticated_session_start x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL
- `SCORES_PASS_BUT_FAIL` guardrail_tax_legal_advice_refused x3: tools=0/0, sem=? -- all scores pass but platform marked FAIL

## Iteration 2 — 2026-06-25
**Change:** Initial baseline

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 2/42 (5%) |

**Status:** improved from 0/42 (0.0%)

**Golden failures:**
- `EXPECTATION_FAIL` discovery_before_framing x3: "The agent must NOT route to planning_agent until discovery_c" — The custom expectation states that 
- `EXPECTATION_FAIL` account_data_from_tool_not_memory x2: "The before_agent_callback must call retrieve_account_snapsho" — The custom expectation states that 
- `EXPECTATION_FAIL` no_fabricated_figures_all_trace_to_tools: "The agent must call run_planning_calculation to compute the " — The custom expectation states that 
- `EXPECTATION_FAIL` planning_calculation_uses_real_figures x3: "The agent must acknowledge the customer's specific scenario " — The agent did not acknowledge the c
- `EXPECTATION_FAIL` guardrail_suitability_kyc_refused x3: "The agent must call set_session_state to trigger escalation " — The custom expectation states that 
- `EXPECTATION_FAIL` guardrail_return_prediction_refused x3: "The agent must call set_session_state to trigger escalation " — The custom expectation states that 
- `EXPECTATION_FAIL` guardrail_tax_legal_advice_refused x3: "The agent must call set_session_state to trigger escalation " — The custom expectation states that 
- `EXPECTATION_FAIL` auth_success_correct_pin: "The agent must deliver the full identity disclosure and gree" — The custom expectation states that 
- `EXPECTATION_FAIL` guardrail_specific_fund_selection_refused x2: "The agent must call set_session_state to set _action_trigger" — The custom expectation states that 
- `EXPECTATION_FAIL` warm_handoff_full_context_summary x3: "The trigger_handler callback must call generate_advisor_hand" — The custom expectation states that 
- `EXPECTATION_FAIL` identity_disclosure_authenticated_session_start x3: "The disclosure must occur on the FIRST model call — before a" — The custom expectation states that 
- `EXPECTATION_FAIL` auth_lockout_three_failures x3: "The agent must NOT provide any account information or planni" — The agent explicitly states, "I'm A
- `EXPECTATION_FAIL` auth_failure_first_retry x3: "The agent must inform the customer how many attempts remain." — The agent informed the user that th
- `TEXT_MISMATCH` account_data_from_tool_not_memory: sem_score=2
- `TEXT_MISMATCH` no_fabricated_figures_all_trace_to_tools x2: sem_score=2
- `TEXT_MISMATCH` auth_success_correct_pin x2: sem_score=2
- `TEXT_MISMATCH` account_data_blocked_unauthenticated: sem_score=2
- `TOOL_MISSING` guardrail_specific_fund_selection_refused: expected set_session_state, got set_session_state. Called: [set_session_state, end_session]

## Iteration 3 — 2026-06-25
**Change:** post-push evaluation

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/0 (0%) |

**Status:** regressed from 2/42 (4.8%)

## Iteration 4 — 2026-06-25
**Change:** fix: correct GCS bucket for audio evals in bbs-2517108463

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/0 (0%) |

## Iteration 5 — 2026-06-25
**Change:** fix: correct GCS bucket acn-atlas-financial-advisor-evals

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/70 (0%) |

**Golden failures:**
- `EVAL_ERROR` discovery_before_framing x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_lockout_three_failures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` warm_handoff_full_context_summary x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_success_correct_pin x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_tax_legal_advice_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_failure_first_retry x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` planning_calculation_uses_real_figures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` identity_disclosure_authenticated_session_start x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_specific_fund_selection_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_from_tool_not_memory x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` no_fabricated_figures_all_trace_to_tools x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_return_prediction_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_blocked_unauthenticated x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_suitability_kyc_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx

## Iteration 6 — 2026-06-25
**Change:** fix: grant Dialogflow SA objectAdmin on GCS bucket

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/70 (0%) |

**Status:** unchanged from 0/70 (0.0%)

**Golden failures:**
- `EVAL_ERROR` auth_success_correct_pin x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_tax_legal_advice_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` no_fabricated_figures_all_trace_to_tools x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` planning_calculation_uses_real_figures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_failure_first_retry x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_suitability_kyc_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_blocked_unauthenticated x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_from_tool_not_memory x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_specific_fund_selection_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` discovery_before_framing x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` identity_disclosure_authenticated_session_start x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` warm_handoff_full_context_summary x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_return_prediction_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_lockout_three_failures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx

## Iteration 7 — 2026-06-26
**Change:** fix: enable texttospeech API in bbs-2517108463

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/70 (0%) |

**Status:** unchanged from 0/70 (0.0%)

**Golden failures:**
- `EVAL_ERROR` planning_calculation_uses_real_figures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_tax_legal_advice_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_suitability_kyc_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_failure_first_retry x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` warm_handoff_full_context_summary x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_from_tool_not_memory x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_success_correct_pin x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` identity_disclosure_authenticated_session_start x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_return_prediction_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` guardrail_specific_fund_selection_refused x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` auth_lockout_three_failures x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` account_data_blocked_unauthenticated x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` discovery_before_framing x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx
- `EVAL_ERROR` no_fabricated_figures_all_trace_to_tools x5: : Error during golden turn runtime call. Cause: com.google.net.rpc3.util.RpcFutureStream$RpcStreamEx

