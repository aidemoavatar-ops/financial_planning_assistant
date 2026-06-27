# Evals

## Eval types

| Type | Source file | Runner |
|---|---|---|
| Callback unit tests | `evals/callback_tests/tests/**/*.py` | `pytest` |
| Tool tests | `evals/tool_tests/tool_tests.yaml` | `agents-cli eval run` |
| Golden evals (turn-level) | `evals/goldens/goldens.yaml` | `agents-cli eval run` |
| Simulation evals | `evals/simulations/simulations.yaml` | `agents-cli eval run` |

## Running

```bash
# Callback unit tests (fast, no GCP)
pytest evals/callback_tests/tests/ -v
pytest evals/callback_tests/tests/root_agent/before_agent_callbacks/before_agent/test.py -v

# All GECX eval types (requires GCP auth + gecx-config.json)
agents-cli eval run --config gecx-config.json
```

Eval reports land in `eval-reports/` (gitignored).

## Session parameter rules

- `customer_pin: "atlas-test-pin-v1"` → `auth_status` becomes `"authenticated"`
- `customer_pin: "wrong-pin-1"` → `auth_status` becomes `"unauthenticated"`
- **Never** set `auth_status` or `account_snapshot` directly in evals — they are always derived by `before_agent_callback`.
- **Never** set `_action_trigger`, `_pending_widget`, or `_silence_count` in evals (internal variables).

## Callback test pattern

Callback tests mock the `tools` global before importing `python_code`, then import the callback function directly:

```python
import python_code
python_code.tools = MagicMock()
from python_code import before_agent_callback
from cxas_scrapi.utils.callback_libs import CallbackContext, Content, Part
```

`CallbackContext(state=dict)` is the test double for callback context.

## Golden eval thresholds (from `app.json`)

- `semanticSimilaritySuccessThreshold`: 3
- `overallToolInvocationCorrectnessThreshold`: 1
- `extraToolCallBehavior`: `ALLOW`
- Hallucination metric: `DISABLED`

Audio evals use `max_turns` set +5 above text baselines (TTS/STT overhead on `gemini-3.1-flash-live`).
