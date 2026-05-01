---
name: portolan-integration-system-map
description: System map for Hermes and other external control-plane clients operating across LimeNet, Quartermaster, rutter, and meta-agent.
---

# Portolan Integration: System Map

## Primary Rule

Treat each Portolan module as a separate contract owner. Hermes may coordinate them, but it should not absorb their source-of-truth responsibilities.

## Ownership Map

- `LimeNet`: task DAG storage, task state transitions, leases, retries, backoff, dependency activation
- `Quartermaster`: review requests, review results, findings, verdicts
- `rutter`: reusable skills, skill families, query and MCP-friendly retrieval
- `meta-agent`: planning, decomposition, skill selection, orchestration policy, artifact and state handling
- `Hermes`: runtime execution, task I/O adapters, worker coordination, contract translation

## Non-Ownership Rules

Hermes should not:

- invent task state outside LimeNet
- invent review truth outside Quartermaster
- fork long-lived skill knowledge outside rutter
- silently replace planning policy that belongs to meta-agent

## Practical Decision Rule

When adding new Hermes behavior, ask which module would still own that behavior if Hermes were replaced.

- If the answer is task state or lease semantics, it belongs in LimeNet.
- If the answer is review semantics, it belongs in Quartermaster.
- If the answer is reusable guidance, it belongs in rutter.
- If the answer is planning or routing policy, it belongs in meta-agent.
- If the answer is runtime execution glue, it belongs in Hermes.
