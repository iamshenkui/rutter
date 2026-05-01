---
name: portolan-integration-limenet-task-lifecycle
description: Operating rules for Hermes when creating, claiming, heartbeating, and submitting LimeNet tasks.
---

# Portolan Integration: LimeNet Task Lifecycle

> Applies `portolan-integration-system-map`.

## Goal

Use LimeNet as the source of truth for task execution state. Hermes should call the documented HTTP contract instead of reconstructing local task state.

## Required Flow

1. Write a task graph with `POST /api/v1/tasks/batch`.
2. Claim one ready task with `POST /api/v1/tasks/claim`.
3. Renew the lease with `POST /api/v1/tasks/{task_id}/heartbeat` while work is still running.
4. Submit completion data with `POST /api/v1/tasks/{task_id}/submit`.
5. Hand the attempt to Quartermaster during `EVALUATING`.

## Operating Rules

- Treat `201 Created` from `batch` as the only success signal that the graph was accepted.
- Treat `204 No Content` from `claim` as idle capacity, not as an error.
- Heartbeat only tasks currently leased by the same `agent_id`.
- Submit only after the worker has produced a real result summary and changed-file list.
- Replace `{task_id}` with the actual UUID in the request path.
- Expect `capabilities` to be accepted but currently not enforced in task selection.

## Error Handling

- `400` from `batch`: assume graph-shape error such as a dependency cycle; repair the task graph before retrying.
- `404` from `heartbeat` or `submit`: assume the task no longer exists or no longer matches the expected active state.
- `409` from `heartbeat`: assume lease ownership mismatch.
- `409` from `submit`: assume the task is no longer in a submittable state.
- `403` from `submit`: assume Hermes is not the current lease holder.

## State Expectations

- Root tasks enter `READY`.
- Dependent tasks enter `PENDING` until dependencies complete.
- Claimed tasks move to `IN_PROGRESS`.
- Submitted tasks move to `EVALUATING`.
- Post-review orchestration decides whether the task becomes `COMPLETED`, retries, or re-enters planning.
