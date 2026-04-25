---
name: game-migration-blocker
description: Blocker classification and resolution guide for game migration. Decides whether a migration obstacle justifies framework patches or game-layer implementation.
---

# Game Migration: Blocker

> Applies Core Rule 3 from `game-migration-core`.

## When to Use

Use this skill whenever you encounter a migration obstacle: a source game feature that cannot be directly expressed with the current framework/engine types.

## Classification Flow

```
Is the missing capability needed by ANY future game,
not just this source game?
├── NO  →  game-gap → Implement in game crate only
│
└── YES → Is it a core type capability?
    ├── YES → core-gap → Patch framework core + regression test
    └── NO  → framework-gap → Patch specific crate + regression test
```

## Classification Examples

| Source Game Need | Classification | Reason |
|---|---|---|
| "Stress" resource mechanic | **game-gap** | Game-specific mechanic; framework provides generic resource system |
| "Limit 3 times per turn" | **game-gap** | Game-specific rule; implement in game-layer skill logic |
| Stackable status effects with complex interactions | **framework-gap** | Any turn-based game needs status stacking |
| Actor references a non-existent component type | **core-gap** | Core entity/component system missing a primitive |
| Damage formula with specific game constants | **game-gap** | Framework provides damage pipeline; game provides formula |

## Resolution Steps

### game-gap

1. Implement entirely in the target game crate
2. Do not modify framework or engine crates
3. No regression test required in framework
4. Update `MIGRATION_BLOCKERS.md`: status = `resolved-in-game`

### framework-gap

1. Identify the specific framework crate that should provide this feature
2. Design the generic API (no game-specific names or constants)
3. Implement in the framework crate
4. Add regression test in that crate's test suite
5. The test must verify the generic capability, never game-specific behavior
6. Update `MIGRATION_BLOCKERS.md`: status = `resolved-framework`

### core-gap

1. Identify the core type that needs extension
2. Design the minimal addition to the core type
3. Implement and add regression test
4. Check downstream crates for breakage
5. Update `MIGRATION_BLOCKERS.md`: status = `resolved-core`

## Anti-Patterns

**Never do these:**
- Add a game-specific enum variant to a framework type
- Hardcode game balance numbers in framework crates
- Name framework APIs after game characters or skills
- Bypass classification and patch framework "just in case"

## Ledger Format

`MIGRATION_BLOCKERS.md` should contain one entry per active blocker:

```markdown
## BLOCKER-001: Status stacking rules
- **Discovered:** 2026-04-25, Batch 2
- **Classification:** framework-gap
- **Description:** Framework `framework_rules::Status` does not support stacking multiplicity.
- **Resolution:** Add `StackableStatus` trait to `framework_rules`.
- **Status:** resolved-framework
- **PR:** #42
```
