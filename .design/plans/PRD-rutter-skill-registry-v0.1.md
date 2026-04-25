# PRD: Rutter Skill Registry v0.1

## Introduction

Rutter currently stores game-migration rules as a monolithic Markdown file. Meta-agent has its own atomic skill injection system (`meta_agent/skills/core.py`), but there is no bridge between the two: skills authored in rutter cannot be registered into meta-agent's runtime, and meta-agent has no mechanism to load external skills. This PRD upgrades rutter from a static document repository into a **Skill Registry & Package Manager** for meta-agent, enabling skill splitting, indexing, and third-party skill management.

## Goals

- Provide a standard YAML format for atomic skills that maps 1:1 to meta-agent's `AtomicSkill` schema
- Enable splitting monolithic Markdown skills into fine-grained atomic skill families
- Maintain a central registry index of all available skills with versioning and dependency tracking
- Provide a CLI tool to install skills into meta-agent's runtime (modifying `core.py` or project-local `.design/skills/`)
- Support importing third-party skills via URL or local path

## User Stories

### US-001: Split monolithic skill into atomic skills
**Description:** As a skill author, I want to split a large Markdown skill into atomic YAML skills so that meta-agent can inject them selectively based on task requirements.

**Acceptance Criteria:**
- [ ] A monolithic Markdown skill can be split into multiple YAML files, each representing one `AtomicSkill`
- [ ] Each YAML file validates against the rutter skill schema
- [ ] The split preserves all incremental rules and metadata

### US-002: Index skills in a central registry
**Description:** As a skill user, I want to browse available skills in a central index so that I can discover and install what I need.

**Acceptance Criteria:**
- [ ] `registry/index.yaml` lists all skill families with name, version, description, and tags
- [ ] Each skill family has a `manifest.yaml` describing its atomic skills and dependencies
- [ ] The index is machine-readable and human-browsable

### US-003: Install skills into meta-agent
**Description:** As a developer, I want to install skills from rutter into meta-agent so that they are injected during task execution.

**Acceptance Criteria:**
- [ ] `rutter install <skill-name>` registers the skill into meta-agent's `ATOMIC_SKILLS`
- [ ] Installation updates `SKILL_KEYWORD_MAPPING` for automatic inference
- [ ] Installation is idempotent (running twice produces the same result)

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

## Functional Requirements

- **FR-1:** Rutter skill YAML format must be compatible with meta-agent's `AtomicSkill` dataclass (`id`, `name`, `description`, `category`, `incremental_rules`, `dependencies`, `keywords`)
- **FR-2:** Skill families are namespaced under `registry/<family-name>/<version>/`
- **FR-3:** Each skill family must contain a `manifest.yaml` with family metadata and a list of its atomic skills
- **FR-4:** `registry/index.yaml` must be auto-generated from manifests and must not be hand-edited
- **FR-5:** The CLI must support installing skills to either meta-agent source (modifying `core.py`) or a project-local `.design/skills/` directory
- **FR-6:** Third-party skill imports must accept both Git URLs (`https://github.com/...`) and local filesystem paths
- **FR-7:** All skill IDs must be globally unique within the registry
- **FR-8:** Circular dependencies between skills are prohibited and must be detected by validation

## Non-Goals

- No web UI or hosted registry service (rutter remains a git-based, file-system registry)
- No runtime skill loading (meta-agent still requires restart after skill installation)
- No skill versioning beyond semantic version strings (no complex dependency resolution like pip)
- No backward compatibility with pre-v0.1 monolithic Markdown format as a runtime format (Markdown can still be used as a source for splitting)

## Design Considerations

- **Registry layout:** Flat namespace under `registry/`, with versioning at the directory level. This allows multiple versions of the same skill family to coexist.
- **Skill ID convention:** Use `snake_case` with family prefix to avoid collisions, e.g., `game_migration_migrate`.
- **Keyword mapping:** Keywords in skill YAML are used to populate `SKILL_KEYWORD_MAPPING` during installation, enabling automatic skill inference from task text.

## Technical Considerations

- Rutter CLI can be implemented as a Python script using `pyyaml` and `pydantic` for schema validation
- Modifying meta-agent's `core.py` requires careful AST manipulation or string templating to avoid breaking existing code
- Alternatively, meta-agent could be extended to support external skill loading from `.design/skills/`, eliminating the need to patch source code
- The registry index should be generated via a pre-commit hook or CI step to prevent drift

## Success Metrics

- `game-migration` skill family is fully migrated to the rutter registry format
- `rutter install game-migration` successfully registers all 5 atomic skills into meta-agent
- `rutter validate` passes with zero errors
- A third-party skill can be imported and installed end-to-end within 3 CLI commands

## Open Questions

- Should rutter CLI be a standalone Python package, or a set of scripts inside the rutter repo?
- Should installation target meta-agent source code directly, or should meta-agent first be extended to support `.design/skills/` external loading?
- What is the minimal meta-agent version that rutter v0.1 will support?
