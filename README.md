# Rutter

Skill Registry & Package Manager for meta-agent.

Rutter manages atomic skills for meta-agent's selective injection system. It provides skill splitting, indexing, installation, and third-party skill management.

## Design Assets

| Asset | Location | Purpose |
|---|---|---|
| Active Plans | `.design/plans/` | Current execution plans (PRDs) |
| Wiki | `.design/wiki/` | Detailed design knowledge |
| History | `.design/history/` | Completed / archived plans |
| Changelog | `CHANGELOG.md` | Latest changes and active plans |

## Skills

| Skill | Version | Description |
|---|---|---|
| [Game Migration](skills/game-migration/README.md) | v0.1 | Migrate existing games onto Rust headless framework + engine architecture |

## Usage

Skills in this repo are living documents. Update them as migration practices evolve.

### meta-agent Workflow

```bash
# Check current state
meta-agent status

# Run pending tasks
meta-agent run --working-dir .

# Install this skill to Claude Code
meta-agent skill install
```
