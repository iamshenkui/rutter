# Portolan Integration Skill Family

Explain how Hermes and other external control-plane clients should operate against LimeNet, Quartermaster, rutter, and meta-agent without collapsing their responsibilities.

## Skills

| Skill | File | When to Call |
|---|---|---|
| `portolan-integration-system-map` | `system-map.md` | First contact: establish which module owns which contract |
| `portolan-integration-limenet-task-lifecycle` | `limenet-task-lifecycle.md` | Before implementing task submission, claim, heartbeat, or submit flows |
| `portolan-integration-quartermaster-review-contract` | `quartermaster-review-contract.md` | When mapping review results back into orchestration decisions |

## Typical Workflow

1. Read `portolan-integration-system-map` to align module boundaries.
2. Use `portolan-integration-limenet-task-lifecycle` to implement the LimeNet client flow.
3. Use `portolan-integration-quartermaster-review-contract` to interpret review results during `EVALUATING`.

## Version

- **v0.1** (2026-05-01): Initial Portolan integration family for Hermes-facing task and review flows
