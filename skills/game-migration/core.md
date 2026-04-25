---
name: game-migration-core
description: Core rules for game migration onto Rust headless framework + engine. Referenced by other game-migration skills.
---

# Game Migration: Core Rules

## Rule 1: Semantic Parity Over Structural Translation

Migrate for **behavioral equivalence**, not code-line correspondence. Internal implementation may differ entirely as long as every **player-observable behavior** produces identical outcomes for identical inputs.

**Observable boundary (must match):**
- Damage output after all modifiers
- Turn order and action resolution
- Status application, stacking, ticking, expiry
- Resource changes (HP, stress, etc.) at correct times
- Skill availability under same conditions
- Combat outcomes given same inputs

**Internal boundary (may differ):**
- Class hierarchy and type names
- Method dispatch mechanism
- Data layout and storage
- Status implementation technique (marker strings vs typed classes)

## Rule 2: Three-Layer Isolation

```
Source Game Content  →  Framework APIs  →  Engine Runtime
(DDGC-specific)        (generic crates)    (infrastructure)
```

- **Framework crates** must contain zero game-specific constants, types, or logic branches
- **Engine crates** must contain zero game-specific content or rules
- **Game crate** (target) contains all migrated content, game-layer logic, and fixtures
- Enforcement: integration test `no_game_content_in_framework_crates` gates build

## Rule 3: Blocker Classification System

| Label | Definition | Resolution |
|---|---|---|
| **core-gap** | Framework core types lack a capability needed by the source game | Patch framework core crate + add regression test |
| **framework-gap** | A framework crate lacks a feature the source game needs | Patch specific crate + add regression test |
| **game-gap** | Framework provides building blocks; source game needs game-specific logic | Implement in game crate only; no framework changes |

**Backflow rejection criteria:** A patch to framework/engine crates is only justified if the capability would benefit *any* consumer, not just the source game.

**Regression test requirement:** Every core-gap or framework-gap patch must include a regression test in the patched crate's test suite. The test verifies the generic capability, never game-specific names or behavior.

## Rule 4: Headless-First, Deterministic Verification

All migrated systems must run without UI. Verification uses deterministic execution traces:

- Combat encounters produce identical `CombatTrace` for identical seeds/inputs
- Run progression produces identical `RunTrace` for identical seeds/inputs
- Traces are the regression test baseline; they gate all merges
- Randomness is seed-stable (LCG PRNG or equivalent)

## Rule 5: Batch Dependency Order

Migrate in strict dependency order. Each batch is self-contained, buildable, and tested before the next begins:

```
Batch 1: Actors + Base Attributes
    → Batch 2: Status Effects + Modifiers
        → Batch 3: Combat Skills + Effect Nodes
            → Batch 4: AI Decision Policies
                → Batch 5: Encounters + Formation
                    → Batch 6: Progression (Runs, Floors, Rooms)
                        → Batch 7: Town + Meta-Systems
```

**Rule:** No code in batch N may depend on types or logic introduced in batch > N.

## Rule 6: Fixture-Driven Content Migration

Game data (heroes, monsters, skills, statuses, items) is migrated as **fixtures**, not inline code:

- Define fixtures in `fixtures/` directory (YAML, JSON, or Rust const data)
- Fixtures declare content parameters; logic lives in `src/content/`
- Never copy-paste original data structures into the new codebase
- Map original concepts to framework types via documented mapping tables

## Rule 7: Parity Test Gates

Every batch must have a corresponding semantic parity test suite. Tests fail → migration blocked.

**Parity test pattern:**
1. Define a canonical input state (actors, skills, formation, seed)
2. Run the migrated system to produce output trace
3. Compare against expected trace (previously validated or derived from original)
4. Any deviation triggers investigation: is it a bug, an acceptable approximation, or semantic drift?

**Acceptable approximations** (documented in `SEMANTIC_GAPS.md`):
- Known behavioral differences that are bounded and restorable without changing test structure
- Example: damage range (min/max) averaged to fixed value; variance restorable via game-layer roll step

**Unacceptable semantic drift** (release blocker):
- Qualitatively different player experience that cannot be fixed by adding game-layer code
- Must be resolved before the batch is considered complete

## Rule 8: Artifact Discipline

Maintain these living documents throughout migration:

| Document | Purpose | Update Trigger |
|---|---|---|
| `MIGRATION_MAP.md` | System-to-system mapping, batch assignments | Every new system identified |
| `MIGRATION_BLOCKERS.md` | Active blocker ledger with classification | Every obstacle discovered |
| `SEMANTIC_PARITY.md` | Parity vocabulary and boundary definitions | When parity concepts need clarification |
| `SEMANTIC_GAPS.md` | Acceptable approximations with rationale | When an approximation is accepted |
| `README.md` | Build/test commands and project overview | When commands or structure change |
