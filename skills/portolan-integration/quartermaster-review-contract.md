---
name: portolan-integration-quartermaster-review-contract
description: Review-contract rules for Hermes when sending completed attempts to Quartermaster and mapping the result back into orchestration behavior.
---

# Portolan Integration: Quartermaster Review Contract

> Applies `portolan-integration-system-map`.

## Goal

Treat Quartermaster as an independent reviewer that evaluates one completed worker attempt at a time. Hermes should send context-rich review requests and translate the returned verdict into orchestration actions without mutating review semantics.

## Required Inputs

Preferred review request fields:

- `task_id`
- `instruction`
- `repo_path`
- `diff`
- `changed_files`
- `validation_command`
- `validation_exit_code`
- `validation_stdout`
- `validation_stderr`
- `policy_refs`
- `metadata`

Only `task_id`, `instruction`, and `repo_path` are strictly required, but omitting the implementation diff for a non-documentation task should usually be treated as a review-quality failure.

## Verdict Mapping

- `APPROVED`: mark the attempt as complete.
- `REVISION_REQUIRED`: return the task to a retryable flow with reviewer guidance.
- `NEEDS_SPLIT`: stop retrying and return to planning/decomposition.
- `UNSAFE`: stop automatic continuation and require policy or human intervention.

## Operating Rules

- Quartermaster should return findings and verdicts; Hermes should not rewrite them into a new private schema.
- Keep the original review artifact so later operators can replay why a task was accepted or rejected.
- If validation failed before review, still pass the validation output so the reviewer can explain the failure path.
- Use Quartermaster during LimeNet `EVALUATING`; do not bypass review by marking tasks complete directly from worker self-report.
