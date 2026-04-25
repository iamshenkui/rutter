# Changelog

## 2026-04-25

- **rutter v0.1 roadmap** — Created PRD for upgrading rutter to a Skill Registry & Package Manager.
  - PRD: `.design/plans/PRD-rutter-skill-registry-v0.1.md`
  - Scope: skill splitting, registry indexing, meta-agent integration, third-party skill management
  - 5 user stories, 8 functional requirements, 4 non-goals defined

## 2026-04-25

- **game-migration skill family v0.1** — Split monolithic skill into fine-grained skill family for meta-agent orchestration.
  - `game-migration-core` — 8 core rules (referenced by all other skills)
  - `game-migration-plan` — Planning phase: analysis, mapping, batch assignment
  - `game-migration-migrate` — Batch execution (parameterized by batch 1-7)
  - `game-migration-verify` — Verification checklist and parity test gating
  - `game-migration-blocker` — Blocker classification and resolution guide
  - See `skills/game-migration/README.md` for installation and usage

- **game-migration v0.1** — Initial rule set derived from DDGC → WorldEngine + glowing-fishstick-framwork migration.
  - 8 core rules: semantic parity, three-layer isolation, blocker classification, headless-first, batch order, fixture-driven content, parity test gates, artifact discipline
  - Verification checklist for batch completion
