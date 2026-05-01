---
name: portolan-integration-hermes-bootstrap
description: Global Hermes bootstrap instructions for discovering Portolan, rutter, LimeNet, and Quartermaster when Hermes is not launched from the Portolan workspace.
---

# Portolan Integration: Hermes Bootstrap

## Purpose

Use this when Hermes is a global agent and is not running from the Portolan workspace. This skill tells Hermes how to discover the Portolan workspace, treat rutter as the skill authority, and find LimeNet and Quartermaster without requiring the user to repeat that context in every conversation.

## Trigger Conditions

Invoke this skill whenever the user mentions any of:

- Portolan
- LimeNet
- Quartermaster
- rutter
- meta-agent
- adding tasks for Hermes into LimeNet
- Hermes working as a Portolan control-plane or worker agent

## Discovery Order

1. Determine `PORTOLAN_HOME`:
   - first use the `PORTOLAN_HOME` environment variable if set
   - otherwise try `/root/projects/portolan`
   - if neither exists, ask the user for the Portolan workspace path once
2. Set `RUTTER_HOME=$PORTOLAN_HOME/rutter`.
3. Treat rutter as the canonical skill registry for Portolan-specific runtime skills.
4. Treat LimeNet as the task backend at `LIMENET_BASE_URL` or `http://127.0.0.1:3000` by default.
5. Treat Quartermaster as the review gate; prefer its CLI or documented review contract.

## Required Behavior

Before creating, claiming, submitting, or reviewing Portolan tasks:

1. Load or inspect the Portolan integration skill family from rutter.
2. Use `portolan_integration_system_map` for module boundaries.
3. Use `portolan_integration_limenet_task_lifecycle` before calling LimeNet.
4. Use `portolan_integration_quartermaster_review_contract` before mapping review verdicts.

## Local Commands

When terminal access is available, prefer these checks:

```bash
cd "$PORTOLAN_HOME/rutter"
PYTHONPATH=src python3 -m rutter search portolan --path .
PYTHONPATH=src python3 -m rutter get-skill portolan_integration_limenet_task_lifecycle --path .
PYTHONPATH=src python3 -m rutter get-skill portolan_integration_quartermaster_review_contract --path .
```

For MCP-style integration:

```bash
cd "$PORTOLAN_HOME/rutter"
PYTHONPATH=src python3 -m rutter serve --path .
```

## Guardrails

- Do not ask the user on every conversation whether rutter or LimeNet exists.
- Do not copy Portolan skill content into Hermes memory as the long-term source of truth.
- Do not bypass rutter when a Portolan-specific workflow skill is needed.
- Do not mark LimeNet tasks complete directly from Hermes self-report; use the documented task lifecycle and Quartermaster review path.
