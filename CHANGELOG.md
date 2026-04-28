# Changelog

## 0.2.1 - 2026-04-29

- **release: rutter 0.2.1** — Expanded game-migration guidance for UI-heavy migrations.
  - Bumped package version to `0.2.1`
  - Upgraded the bundled `game-migration` family to `v0.2`
  - Added `game_migration_ui_product_sense` for game-screen UI quality guidance
  - Added `game_migration_unity_ui_recon` for source-first Unity UI migration workflow

## 0.2.0 - 2026-04-25

- **release: rutter 0.2.0** — First functional registry and MCP release.
  - Bumped package version to `0.2.0`
  - Published the registry foundation, read-only query layer, and FastMCP server in one release slice
  - Documented runtime usage for CLI and MCP transports

## 2026-04-25

- **rutter registry foundation implemented** — Added the first runnable registry package and CLI.
  - Python package scaffolded under `src/rutter/` with `rutter validate`, `rutter build-index`, and `rutter search`
  - Added registry loader, schema checks, dependency validation, and deterministic index generation
  - Migrated `game-migration` into `registry/game-migration/v0.1/` as atomic YAML skill assets
  - Added focused tests for registry validation, index building, and CLI execution

- **read-only query layer implemented** — Added the first MCP-friendly retrieval surface.
  - Added `list_skill_families`, `get_skill_family`, `get_skill`, and `get_skill_dependencies`
  - Exposed matching CLI commands: `list-families`, `get-family`, `get-skill`, and `get-dependencies`
  - Added `src/rutter/query.py` as a thin adapter layer for future MCP tool wrapping

- **MCP server implemented** — Added a real FastMCP wrapper over the read-only query layer.
  - Added `src/rutter/mcp_server.py` with `list_skill_families`, `search_skills`, `get_skill_family`, `get_skill`, `get_skill_dependencies`, and `validate_registry` tools
  - Added `rutter serve --transport ...` CLI support for stdio, SSE, and streamable HTTP transports
  - Added an optional `mcp` dependency extra and focused tests for tool registration and CLI dispatch

## 2026-04-25

- **rutter v0.1 roadmap** — Refocused PRD around a git-backed skill registry and MCP-friendly query layer.
  - PRD: `.design/plans/PRD-rutter-skill-registry-v0.1.md`
  - Chinese PRD: `.design/plans/PRD-rutter-skill-registry-v0.1.zh-CN.md`
  - Scope: skill splitting, registry indexing, query tools, validation, external-source integration path
  - 6 user stories, 11 functional requirements, phased delivery defined

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
