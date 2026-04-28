# Game Migration Skill Family

Migrate an existing game (typically Unity/C#) onto a Rust headless framework + engine architecture, preserving semantic parity.

## Skills

| Skill | File | When to Call |
|---|---|---|
| `game-migration-core` | `core.md` | Referenced by other skills; defines shared rules |
| `game-migration-plan` | `plan.md` | Project start: analyze source game, create migration map |
| `game-migration-migrate` | `migrate.md` | Per batch: implement migrated systems |
| `game-migration-verify` | `verify.md` | Post-batch or CI: run verification checklist |
| `game-migration-blocker` | `blocker.md` | When encountering framework/engine gaps |
| `game-migration-ui-product-sense` | `ui-product-sense.md` | UI-heavy phases: keep migrated screens feeling like the original game |
| `game-migration-unity-ui-recon` | `unity-ui-recon.md` | Before frontend UI migration: inspect Unity prefabs, scenes, atlases, and assets |

## Installation

### Option A: Install to Claude Code (global)

Copy the skill files to your Claude Code skills directory:

```bash
# For flat layout (if subdirectories not supported)
cp skills/game-migration/*.md ~/.claude/skills/

# Then rename for namespacing
# core.md → game-migration-core.md
# plan.md → game-migration-plan.md
# etc.
```

Then invoke with `/game-migration-plan`, `/game-migration-migrate`, etc.

### Option B: Reference from target repo (project-local)

Copy the `skills/game-migration/` directory into your target repo. In conversations, reference the skill file directly:

```
@skills/game-migration/migrate.md 请执行 Batch 1 的迁移...
```

### Option C: meta-agent PRD Integration

In your meta-agent PRD, specify the skill to use for each task:

```markdown
## Task: Batch 1 Migration
- **Skill:** `game-migration-migrate`
- **Parameters:** batch=1
- **Output:** Migrated actors + parity tests passing
```

Then run:

```bash
meta-agent kickoff --mode prd --prd-path design/plans/migration-batch-1.md
```

## Typical Workflow

1. **Plan** (`game-migration-plan`):
   - Analyze source game
   - Produce `MIGRATION_MAP.md`, assign batches
   - Identify initial blockers

2. **Migrate** (`game-migration-migrate`) × 7:
   - Run once per batch (1 through 7)
   - Each batch: patch framework → migrate fixtures → implement game layer → write parity tests
   - Use `game-migration-blocker` when stuck

3. **Verify** (`game-migration-verify`):
   - After each batch and at project end
   - Run full verification checklist

## Batch Order

```
Batch 1: Actors + Base Attributes
    → Batch 2: Status Effects + Modifiers
        → Batch 3: Combat Skills + Effect Nodes
            → Batch 4: AI Decision Policies
                → Batch 5: Encounters + Formation
                    → Batch 6: Progression (Runs, Floors, Rooms)
                        → Batch 7: Town + Meta-Systems
```

No code in batch N may depend on types or logic introduced in batch > N.

## Version

- **v0.2** (2026-04-29): Added UI product-sense and Unity UI recon skills for frontend-heavy migration phases
- **v0.1** (2026-04-25): Initial skill family split from monolithic `game-migration-v0.1.md`
