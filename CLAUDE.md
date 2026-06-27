# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Atlas** — voice-first financial planning assistant for Northwind bank, built on Google GECX (`gemini-3.1-flash-live`, audio modality). GCP project: `bbs-2517108463`, region: `eu`.

## Commands

```bash
# Setup
.agents/skills/cxas-agent-foundry/scripts/setup.sh
.venv\Scripts\activate                          # Windows

# Test (callback unit tests)
pytest evals/callback_tests/tests/ -v

# Lint / sync / deploy / eval
agents-cli lint   --config gecx-config.json    # 0 errors AND 0 warnings required
agents-cli sync   --config gecx-config.json
agents-cli deploy --config gecx-config.json
agents-cli eval run --config gecx-config.json  # goldens + simulations + tool_tests
```

## Detail files — load when relevant

| When you are... | Read |
|---|---|
| Implementing a GitHub Issue, writing a PR, or working with OpenSpec | `.claude/workflow.md` |
| Reading or modifying agent code, callbacks, tools, or session state | `.claude/architecture.md` |
| Writing, running, or debugging evals or callback tests | `.claude/evals.md` |
