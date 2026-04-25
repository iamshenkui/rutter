---
name: game-migration-migrate
description: Execute a migration batch. Implements source game systems onto the Rust framework + engine, preserving semantic parity.
---

# Game Migration: Migrate Batch

> Applies all Core Rules from `game-migration-core`.

## Parameters

- `batch`: Required. Batch number (1-7) or batch name.
- `source_path`: Optional. Path to source game codebase (default: repo root).

## Batch Reference

| Batch | Name | Systems | Framework Crates Typically Used |
|---|---|---|---|
| 1 | Actors + Base Attributes | Heroes, monsters, base stats, resources | `framework_rules` |
| 2 | Status Effects + Modifiers | Buffs, debuffs, DOTs, modifiers, stacking | `framework_rules` |
| 3 | Combat Skills + Effect Nodes | Skills, targeting, damage calc, effect trees | `framework_combat` |
| 4 | AI Decision Policies | Enemy AI, skill selection, targeting logic | `framework_ai` |
| 5 | Encounters + Formation | Encounter definitions, formation layout, spawn rules | `framework_combat` |
| 6 | Progression | Runs, floors, rooms, rewards, unlocks | `framework_progression` |
| 7 | Town + Meta-Systems | Town, upgrades, meta-currency, NG+ | `framework_progression` |

## Steps

### 1. Review Batch Scope

Read `MIGRATION_MAP.md` and confirm which systems are in this batch. For each system:
- Identify source files in the source game
- Identify target framework types it should use
- Check `MIGRATION_BLOCKERS.md` for any pre-existing blockers affecting this batch

### 2. Implement Framework Patches (if any)

If blockers classified as `core-gap` or `framework-gap` affect this batch:
1. Patch the relevant framework/engine crate
2. Add regression test verifying the generic capability
3. Update `MIGRATION_BLOCKERS.md` with resolution
4. **Do not proceed with game-layer code until framework patches are merged**

### 3. Migrate Content as Fixtures

For each content type in this batch:
1. Define fixture schema (do not copy source data structures)
2. Extract source data into fixtures
3. Map source concepts to framework types
4. Place fixtures in `fixtures/<batch-name>/`

### 4. Implement Game-Layer Logic

In the target game crate:
1. Wire fixtures to framework APIs
2. Implement game-specific logic (always `game-gap`, never framework patches)
3. Follow source game's observable behavior exactly (Rule 1)

### 5. Write Parity Tests

For each system in this batch:
1. Define canonical input state
2. Produce expected trace (from source game or validated baseline)
3. Write test that runs migrated system with same input
4. Assert trace equality

Tests must fail if behavior deviates. Do not weaken assertions to make tests pass.

### 6. Run Verification Checklist

- [ ] `cargo check --workspace` passes
- [ ] `cargo test --workspace` passes
- [ ] `cargo clippy --workspace -- -D warnings` passes
- [ ] All parity tests for this batch pass
- [ ] No game-specific content in framework or engine crates
- [ ] All blockers in this batch classified and resolved or deferred
- [ ] CHANGELOG entry appended

### 7. Update Artifacts

- `MIGRATION_MAP.md`: Mark migrated systems as complete
- `SEMANTIC_GAPS.md`: Document any acceptable approximations discovered
- `CHANGELOG.md`: Append entry for this batch

## Constraints

- **Never skip parity tests.** A batch without parity tests is not complete.
- **Never patch framework for game-specific mechanics.** If the framework doesn't support "stress", "chaos", or "limit per turn", implement these in the game crate.
- **Never depend on future batches.** If you need a type from Batch 4 while implementing Batch 2, either reorder or stub minimally.
