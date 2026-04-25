---
name: game-migration-verify
description: Verification phase for game migration. Runs the complete verification checklist for a batch or the entire migration.
---

# Game Migration: Verify

> Applies Core Rules 1, 4, 7 from `game-migration-core`.

## Parameters

- `scope`: Optional. `batch-N` to verify a specific batch, or `full` to verify entire migration. Default: `full`.

## Checks

### 1. Build Hygiene

```bash
cargo check --workspace
cargo test --workspace
cargo clippy --workspace -- -D warnings
```

All three must pass. Warnings are treated as errors (`-D warnings`).

### 2. No Game Content in Framework/Engine

Run or verify the integration test `no_game_content_in_framework_crates`.

If this test does not exist yet, perform a manual audit:
- Search framework crates for game-specific strings (hero names, skill names, status names)
- Search engine crates for game-specific content references
- Any match = violation of Rule 2

### 3. Parity Tests

For the specified scope, run all parity tests:

```bash
cargo test --workspace parity
```

Or run batch-specific parity tests:

```bash
cargo test batch_1_parity  # example pattern
```

**Pass criteria:**
- All tests pass
- No tests are `#[ignore]` without documented reason
- Trace outputs match expected baselines exactly

If a parity test fails, investigate:
1. Is it a bug in the migrated code? → Fix and rerun.
2. Is it an acceptable approximation? → Document in `SEMANTIC_GAPS.md` with rationale.
3. Is it semantic drift? → Block release. Must be fixed before batch is complete.

### 4. Artifact Completeness

Verify all living documents exist and are up to date:

| Document | Check |
|---|---|
| `MIGRATION_MAP.md` | All batch-N systems marked complete? |
| `MIGRATION_BLOCKERS.md` | No unresolved blockers in scope? |
| `SEMANTIC_PARITY.md` | Parity vocabulary covers all tested behaviors? |
| `SEMANTIC_GAPS.md` | All approximations documented with rationale? |
| `README.md` | Build/test commands still correct? |
| `CHANGELOG.md` | Entry exists for the verified batch? |

### 5. Determinism Check

Run the same parity test twice with the same seed. Traces must be byte-identical.

If traces differ:
- Check for unseeded randomness
- Check for iteration order over unordered collections (HashMap, HashSet)
- Check for system time or other non-deterministic inputs

## Output

- Verification report: pass/fail per check
- If any check fails: block the batch and file/update blockers
- If all checks pass: batch is complete, append sign-off to CHANGELOG
