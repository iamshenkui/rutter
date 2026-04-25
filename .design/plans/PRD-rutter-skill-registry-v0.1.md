# PRD: Rutter Skill Registry & Query Layer v0.1

## Introduction

Rutter currently stores game-migration rules as a monolithic Markdown file. Meta-agent has its own atomic skill injection system (`meta_agent/skills/core.py`), but there is no stable discovery interface between the two: skills authored in rutter are not indexable as first-class assets, and agent clients such as meta-agent or Claude Code cannot query them through a common protocol. This PRD upgrades rutter from a static document repository into a **git-backed skill registry with an MCP-friendly query layer**, enabling skill splitting, indexing, validation, and agent-facing retrieval.

Rutter remains the source of truth for skill content and metadata. MCP is used as an access layer for discovery and retrieval, not as the persistence layer for skill authoring.

## Goals

- Provide a standard YAML format for atomic skills that maps 1:1 to meta-agent's `AtomicSkill` schema
- Enable splitting monolithic Markdown skills into fine-grained atomic skill families
- Maintain a central registry index of all available skills with versioning and dependency tracking
- Provide a stable query surface for agent clients via MCP-friendly read tools
- Support importing third-party skills via URL or local path into the registry

## Product Positioning

- **Rutter registry:** Owns skill content, manifests, versions, dependency metadata, and validation.
- **Rutter query layer:** Exposes discovery and retrieval operations for agents through MCP or equivalent local tool adapters.
- **Meta-agent:** Owns planning, resolution, injection, and runtime selection of skills.
- **Claude Code and other agents:** Consume skill search and fetch APIs; they do not mutate registry internals directly.

## User Stories

### US-001: Split monolithic skill into atomic skills
**Description:** As a skill author, I want to split a large Markdown skill into atomic YAML skills so that meta-agent can inject them selectively based on task requirements.

**Acceptance Criteria:**
- [ ] A monolithic Markdown skill can be split into multiple YAML files, each representing one `AtomicSkill`
- [ ] Each YAML file validates against the rutter skill schema
- [ ] The split preserves all incremental rules and metadata

### US-002: Index skills in a central registry
**Description:** As a skill user, I want to browse available skills in a central index so that I can discover what I need and retrieve it consistently.

**Acceptance Criteria:**
- [ ] `registry/index.yaml` lists all skill families with name, version, description, and tags
- [ ] Each skill family has a `manifest.yaml` describing its atomic skills and dependencies
- [ ] The index is machine-readable and human-browsable

### US-003: Query skills through MCP
**Description:** As an agent client, I want to query rutter through MCP-compatible tools so that I can search and fetch relevant skills without understanding the repository layout.

**Acceptance Criteria:**
- [ ] Rutter exposes read-only query operations for listing families, searching skills, and fetching manifests or atomic skill payloads
- [ ] Query results include enough metadata for an agent to rank or select relevant skills
- [ ] The query layer works against the registry as the source of truth and does not require patching meta-agent source files

### US-004: Import third-party skills
**Description:** As a team lead, I want to import external skills into rutter so that my team can use community-contributed skills.

**Acceptance Criteria:**
- [ ] `rutter add <url>` imports a skill from a GitHub repo or local path
- [ ] Imported skills are validated against the rutter schema
- [ ] Imported skills appear in the index after registration

### US-005: Validate skill registry integrity
**Description:** As a CI pipeline, I want to validate the entire skill registry so that broken or malformed skills are caught before deployment.

**Acceptance Criteria:**
- [ ] `rutter validate` checks all YAML files against the schema
- [ ] Validation reports missing dependencies, duplicate IDs, and malformed rules
- [ ] CI exits non-zero on validation failure

### US-006: Register rutter as an external skill source
**Description:** As a meta-agent developer, I want meta-agent to mount rutter as an external source so that runtime injection can evolve without rutter editing meta-agent internals.

**Acceptance Criteria:**
- [ ] Meta-agent can register a rutter source by local path or repository URL
- [ ] Source registration does not require modifying `meta_agent/skills/core.py`
- [ ] Built-in skills remain available as fallback until external source loading is complete

## Functional Requirements

- **FR-1:** Rutter atomic skill YAML payloads must be compatible with meta-agent's `AtomicSkill` runtime fields (`id`, `name`, `description`, `category`, `incremental_rules`, `dependencies`)
- **FR-2:** Skill families are namespaced under `registry/<family-name>/<version>/`
- **FR-3:** Each skill family must contain a `manifest.yaml` with family metadata and a list of its atomic skills
- **FR-4:** `registry/index.yaml` must be auto-generated from manifests and must not be hand-edited
- **FR-5:** Manifest metadata must include query-oriented fields such as family name, version, description, tags, keywords, and aliases
- **FR-6:** Third-party skill imports must accept both Git URLs (`https://github.com/...`) and local filesystem paths
- **FR-7:** All atomic skill IDs must be globally unique within the registry; family versioning must not require patching existing IDs
- **FR-8:** Circular dependencies between skills are prohibited and must be detected by validation
- **FR-9:** Rutter must provide a read-only MCP-compatible tool surface for listing, searching, and fetching skills
- **FR-10:** Query results must be deterministic for the same registry revision
- **FR-11:** Rutter must not modify meta-agent source code as part of v0.1

## Non-Goals

- No web UI or hosted registry service (rutter remains a git-based, file-system registry)
- No direct runtime mutation of meta-agent built-in skill tables
- No skill versioning beyond semantic version strings (no complex dependency resolution like pip)
- No backward compatibility with pre-v0.1 monolithic Markdown format as a runtime format (Markdown can still be used as a source for splitting)
- No write APIs over MCP in v0.1 (query only)

## Phased Delivery

### Phase 1: Registry Foundation

- Define atomic skill YAML payload schema and family manifest schema
- Split the `game-migration` family into registry assets
- Generate `registry/index.yaml`
- Implement `rutter validate`

### Phase 2: Query Layer

- Expose MCP-friendly read tools over the registry
- Support list, search, fetch, and dependency inspection operations
- Keep query results aligned with the generated index and manifests

### Phase 3: External Source Integration

- Extend meta-agent to mount rutter as an external skill source
- Allow meta-agent to resolve and inject external skills without source patching
- Retain built-in fallback skills during migration

## Design Considerations

- **Registry layout:** Flat namespace under `registry/`, with versioning at the directory level. This allows multiple versions of the same skill family to coexist.
- **Skill ID convention:** Use `snake_case` with family prefix to avoid collisions, e.g., `game_migration_migrate`.
- **Two-level schema:** Manifest metadata serves registry and query use cases; atomic skill payloads stay close to the runtime schema.
- **Query model:** MCP returns compact metadata for discovery and full skill payloads for injection or local rendering.
- **Resolver boundary:** Rutter returns candidate skills and metadata; meta-agent remains responsible for final selection and prompt injection.

## Technical Considerations

- Rutter CLI can be implemented as a Python script using `pyyaml` and `pydantic` for schema validation
- MCP support can be implemented as a thin adapter over the registry index and manifest loader
- Meta-agent should be extended to support external skill loading from a registered source, eliminating the need to patch source code
- The registry index should be generated via a pre-commit hook or CI step to prevent drift

## MCP Query Surface

The first MCP-compatible query surface should remain read-only and cover:

- `list_skill_families`
- `search_skills(query, tags, category, keywords)`
- `get_skill_family(name, version?)`
- `get_skill(skill_id)`
- `get_skill_dependencies(skill_id)`
- `validate_registry()`

## Success Metrics

- `game-migration` skill family is fully migrated to the rutter registry format
- An agent client can discover and fetch `game-migration` skills through the query layer without repository-specific path knowledge
- `rutter validate` passes with zero errors
- A third-party skill can be imported, indexed, and queried end-to-end within 3 CLI commands

## Open Questions

- Should rutter CLI be a standalone Python package, or a set of scripts inside the rutter repo?
- Should MCP be shipped as `rutter serve --mcp` inside this repo, or as a thin companion package over the same registry?
- What is the minimal meta-agent source-registry contract needed to consume rutter without duplicating resolver logic?
- What is the minimal meta-agent version that rutter v0.1 will support?
