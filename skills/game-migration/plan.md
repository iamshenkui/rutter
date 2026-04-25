---
name: game-migration-plan
description: Planning phase for game migration. Analyzes source game and produces migration map, batch assignments, and artifact scaffolding.
---

# Game Migration: Planning Phase

> Applies Core Rules 1, 2, 5, 6, 8 from `game-migration-core`.

## Input

- Source game codebase (typically Unity/C#)
- Target framework and engine repositories
- Any existing design documents or architecture diagrams

## Output

1. `MIGRATION_MAP.md` — System-to-system mapping
2. `MIGRATION_BLOCKERS.md` — Initial blocker ledger (empty or pre-populated)
3. `SEMANTIC_PARITY.md` — Parity vocabulary for this specific game
4. `SEMANTIC_GAPS.md` — Acceptable approximations (initially empty)
5. Batch assignment for each system/feature

## Steps

### 1. Inventory Source Systems

List all systems in the source game that need migration. For each system, record:
- System name and responsibility
- Key types/classes
- Dependencies on other systems
- Observable behaviors (inputs → outputs)
- Data sources (SOs, JSON, hardcoded, etc.)

### 2. Map to Framework Types

For each source system, identify the corresponding framework/engine types:

| Source System | Framework Crate | Engine Crate | Target Crate | Batch |
|---|---|---|---|---|
| (example) Hero stats | `framework_rules::Actor` | `simulation_core::Entity` | `ddgc::actors` | 1 |

If a source system has **no corresponding framework type**, flag as a **blocker** and classify it (see `game-migration-blocker`).

### 3. Assign Batches

Assign each system to a batch following Rule 5 (dependency order). Check:
- Does this system depend on any system in a higher-numbered batch? If yes, reorder.
- Can this batch be built and tested independently? If no, split or reorder.

### 4. Define Fixture Strategy

For each content type (heroes, monsters, skills, statuses, items), decide:
- Fixture format (YAML / JSON / Rust const)
- Directory structure under `fixtures/`
- Mapping from source data format to fixture schema

### 5. Scaffold Artifacts

Create the initial versions of all required living documents:

```bash
touch MIGRATION_MAP.md
touch MIGRATION_BLOCKERS.md
touch SEMANTIC_PARITY.md
touch SEMANTIC_GAPS.md
```

Populate `MIGRATION_MAP.md` with the system mapping table from Step 2.

### 6. Verification

Before declaring planning complete:
- [ ] Every source system is assigned to exactly one batch
- [ ] No cross-batch dependency violations
- [ ] Every framework gap is classified as a blocker
- [ ] `MIGRATION_MAP.md` is committed to target repo
