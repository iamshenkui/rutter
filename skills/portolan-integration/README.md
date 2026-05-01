# Portolan Integration Skill Family

Explain how Hermes and other external control-plane clients should operate against LimeNet, Quartermaster, rutter, and meta-agent without collapsing their responsibilities.

## Skills

| Skill | File | When to Call |
|---|---|---|
| `portolan-integration-hermes-bootstrap` | `hermes-bootstrap.md` | Global Hermes startup/context discovery: find Portolan, rutter, LimeNet, and Quartermaster without per-conversation reminders |
| `portolan-integration-system-map` | `system-map.md` | First contact: establish which module owns which contract |
| `portolan-integration-limenet-task-lifecycle` | `limenet-task-lifecycle.md` | Before implementing task submission, claim, heartbeat, or submit flows |
| `portolan-integration-quartermaster-review-contract` | `quartermaster-review-contract.md` | When mapping review results back into orchestration decisions |

## Typical Workflow

1. Install or invoke `portolan-integration-hermes-bootstrap` for global Hermes discovery.
2. Read `portolan-integration-system-map` to align module boundaries.
3. Use `portolan-integration-limenet-task-lifecycle` to implement the LimeNet client flow.
4. Use `portolan-integration-quartermaster-review-contract` to interpret review results during `EVALUATING`.

## Version

- **v0.1** (2026-05-01): Initial Portolan integration family for Hermes-facing bootstrap, task, and review flows
