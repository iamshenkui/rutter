# PRD: Rutter Skill Accumulation Loop v0.1

## Introduction

Rutter is now the source of truth for long-lived skill content, but Portolan still lacks a practical loop for turning real execution failures into new skills or skill updates. The intended long-term architecture includes checker output, reviewer verdicts, and phase-level orchestration, but `Quartermaster` is still too early to be the primary loop anchor.

The next slice should therefore focus on a smaller, usable loop:

- collect stable execution evidence from `meta-agent`
- summarize recurring domain failures with a cheap model
- consolidate them into candidate skill deltas with a stronger model
- store the result in a reviewable proposal surface before touching the live registry

This plan defines that first skill accumulation loop.

## Goals

- Capture recurring domain-specific failure patterns from real runs
- Focus on missing or weak skills, not on generic model capability scoring
- Allow cheap large-scale triage using a low-cost model such as MiniMax
- Allow higher-quality consolidation using a stronger model such as DeepSeek Pro
- Preserve human review between runtime evidence and registry mutation
- Make the loop portable across machines by keeping artifacts in the repository

## Non-Goals

- No automatic mutation of the live `registry/` on first pass
- No dependency on `Quartermaster` for v0.1 of this loop
- No attempt to grade generic tool-calling or low-level coding ability
- No requirement to capture every token-level or tool-level agent step
- No hosted service or always-on daemon in the first slice

## Product Positioning

- **meta-agent:** owns run execution, task decomposition, and evidence capture
- **Claude/local worker traces:** provide rich raw trajectory evidence when available
- **Rutter:** owns durable skill proposals, validation, and eventual promotion into the live registry
- **Human operator:** approves, edits, or rejects candidate skill updates

## Problem Statement

The most valuable runtime learning signals are not generic coding failures. They are repeated gaps such as:

- UI migration work drifting into generic web layouts
- source-first Unity asset analysis being skipped
- a large migration task being decomposed at the wrong level
- acceptance criteria missing important domain checks

Current `.state` artifacts are already sufficient for run-level reflection, but they are not enough to capture the full reasoning path of the worker. At the same time, raw Claude local history exists on the machine and can be mined when available.

The loop must therefore combine:

1. stable structured run evidence from `meta-agent`
2. optional richer worker trajectory evidence from local Claude history
3. a proposal surface inside rutter that stores candidate skill deltas safely

## User Stories

### US-001: Summarize recurring domain failures cheaply
**Description:** As an operator, I want a cheap model to scan many completed runs and group repeated domain-specific failures so that I can detect missing skills early.

**Acceptance Criteria:**
- [ ] The system reads `runs.jsonl`, `decisions.jsonl`, and `progress/log.jsonl`
- [ ] It emits structured issue records instead of free-form prose only
- [ ] Issues are classified into domain-relevant categories such as `missing_domain_skill`, `needs_phase_split`, and `weak_acceptance_contract`

### US-002: Consolidate issues into skill proposals
**Description:** As a skill author, I want a stronger model to turn grouped issues into candidate skill additions or updates so that useful lessons can be promoted into rutter.

**Acceptance Criteria:**
- [ ] A consolidation step consumes many issue records and produces proposal bundles
- [ ] A proposal bundle names the target skill family and recommended action
- [ ] The output is reviewable and does not directly overwrite the live registry

### US-003: Preserve local trajectory evidence when available
**Description:** As an operator, I want the loop to use local Claude history when it can be reliably linked to a run so that domain failures can be explained with richer evidence.

**Acceptance Criteria:**
- [ ] The design supports linking `meta-agent` run IDs to local Claude sessions
- [ ] Missing trajectory data does not break the loop
- [ ] The first implementation can run with `.state` data only

### US-004: Continue development across machines
**Description:** As a developer, I want the plan and proposed artifact shape stored in the repo so that I can continue implementation on another machine without reconstructing the design from memory.

**Acceptance Criteria:**
- [ ] The repository contains a design document for the loop
- [ ] The document names scope, phases, artifact shapes, and next steps
- [ ] The plan is specific enough to continue implementation later without chat history

## Functional Requirements

- **FR-1:** The first loop must use stable run boundary artifacts from `meta-agent`, especially `runs.jsonl`, `decisions.jsonl`, and `progress/log.jsonl`
- **FR-2:** The loop may optionally enrich evidence with local Claude session history when a reliable run-to-session link exists
- **FR-3:** Cheap-model extraction must emit structured issue records, not just Markdown summaries
- **FR-4:** Structured issues must distinguish at least these categories: `missing_domain_skill`, `needs_phase_split`, `weak_acceptance_contract`, `checker_reviewer_gap`, and `wrong_routing_or_context`
- **FR-5:** The strong-model consolidation step must emit reviewable proposal bundles for rutter, not direct registry mutations
- **FR-6:** Proposal bundles must identify a target family, suggested action, rationale, evidence references, and candidate rules or metadata changes
- **FR-7:** Rutter must store proposal bundles under a dedicated review surface such as `proposals/` or `registry_drafts/`
- **FR-8:** Promotion from proposal to live registry remains a deliberate human-reviewed action in v0.1
- **FR-9:** The loop must prioritize domain and decomposition learning over generic model-performance scoring

## Evidence Sources

### Minimum viable evidence

- `meta-agent/.state/runs.jsonl`
- `meta-agent/.state/decisions.jsonl`
- `meta-agent/.state/progress/log.jsonl`

### Optional richer evidence

- local Claude history under `~/.claude/`
- run-specific worker outputs if `meta-agent` later records explicit session pointers

## Proposed Artifact Shapes

### Structured issue record

```json
{
  "issue_id": "traj-20260429-001",
  "source": "meta-agent",
  "repo": "DDGC_newArch",
  "task_ids": ["US-101", "US-118"],
  "run_ids": ["run-a", "run-b"],
  "category": "missing_domain_skill",
  "summary": "UI migration repeatedly degraded into generic web layout",
  "evidence": [
    "decision=retry",
    "risk=visual fidelity regression",
    "failure_summary=layout drift"
  ],
  "candidate_skills": [
    "game_migration_ui_product_sense",
    "game_migration_unity_ui_recon"
  ],
  "confidence": 0.82
}
```

### Proposal bundle

```json
{
  "bundle_id": "skill-feedback-20260429-01",
  "target_family": "game-migration",
  "action": "update_existing_skill",
  "target_skill_id": "game_migration_ui_product_sense",
  "summary": "Strengthen UI migration review rules for game-screen fidelity",
  "why_now": "Repeated failure across multiple DDGC migration phases",
  "recommended_rules": [
    "Reject generic dashboard composition for game town screens",
    "Require landscape viewport verification for core loops"
  ],
  "supporting_issues": [
    "traj-20260429-001",
    "traj-20260429-004"
  ]
}
```

## Proposed Workflow

### Phase 1: Cheap extraction

- Run a low-cost model such as MiniMax over new or changed runtime evidence
- Produce normalized issue records
- Deduplicate highly similar issues

### Phase 2: Strong consolidation

- Run a stronger model such as DeepSeek Pro over the issue set
- Group issues by family, skill gap, decomposition gap, or acceptance gap
- Generate proposal bundles for human review

### Phase 3: Proposal storage in rutter

- Write proposal bundles into a reviewable repository surface
- Validate shape and required fields with a simple CLI check
- Keep proposals versioned in git for discussion and editing

### Phase 4: Human promotion

- Review accepted proposals
- Convert them into registry updates
- Regenerate `registry/index.yaml`
- Update family docs and changelog as needed

## Immediate Development Plan

### Slice A: meta-agent evidence export

- Add a `reflect-skills` command to `meta-agent`
- Read stable `.state` artifacts only
- Emit issue records to a machine-readable JSONL file

### Slice B: run-to-session linking

- Extend `meta-agent` to record a worker session pointer when available
- Make it possible to enrich a run with local Claude history later

### Slice C: rutter proposal surface

- Add `proposals/` or `registry_drafts/`
- Define a small schema for proposal bundles
- Add `rutter validate-proposals`

### Slice D: promotion tooling

- Add a helper command to turn an accepted proposal into a family update patch
- Keep the final edit human-reviewed before merge

## Machine Handoff Notes

On a new machine, continue from this order:

1. Bootstrap Portolan and initialize submodules
2. Install `meta-agent` and `rutter` as editable tools
3. Start with `Slice A: meta-agent evidence export`
4. Delay `Quartermaster` integration until its contracts and reviewer surface are more stable
5. Keep the first implementation focused on domain skill gaps and phase decomposition problems

## Open Questions

- What is the smallest reliable key for linking a `meta-agent` run to a Claude local session?
- Should proposal bundles live in `rutter/proposals/` or under `.design/` first?
- Should decomposition issues become skill proposals, planner policy proposals, or both?
- When `Quartermaster` matures, should `checker_reviewer_gap` become a first-class issue category with stronger weight than plain runtime failure?