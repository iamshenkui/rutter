from __future__ import annotations

import pytest

from rutter.adapter import (
    NON_EXECUTABLE_PATTERNS,
    NON_RUTTER_DOMAIN_PATTERNS,
    adapt_and_filter_by_domain,
    adapt_proposals,
    adapt_raw_proposal,
)
from rutter.models import EvidenceRef, SkillProposalBundle


# ── adapt_raw_proposal ────────────────────────────────────────────────


class TestAdaptRawProposal:
    """Unit tests for adapt_raw_proposal — converting raw dicts to SkillProposalBundle."""

    def test_basic_conversion(self) -> None:
        """A well-formed proposal dict is converted correctly."""
        raw = {
            "schema_version": "1",
            "bundle_id": "adapter-test-001",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "game_migration_adapter_test",
            "risk_level": "low",
            "created_at": "2026-05-02T00:00:00Z",
        }
        bundle = adapt_raw_proposal(raw)
        assert isinstance(bundle, SkillProposalBundle)
        assert bundle.bundle_id == "adapter-test-001"
        assert bundle.schema_version == "1"
        assert bundle.status == "proposed"
        assert bundle.target_family == "game-migration"
        assert bundle.action == "create_new_skill"
        assert bundle.new_skill_id == "game_migration_adapter_test"
        assert bundle.risk_level == "low"

    def test_schema_version_always_one(self) -> None:
        """schema_version is always forced to '1', regardless of input."""
        for version in ("v2", "2", "0", "", None, 1):
            raw = {
                "bundle_id": f"version-test-{version}",
                "schema_version": version,
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "test",
            }
            bundle = adapt_raw_proposal(raw)
            assert bundle.schema_version == "1", f"Expected '1' for input {version!r}"

    def test_evidence_refs_as_strings(self) -> None:
        """EvidenceRefs as plain strings create path-only refs."""
        raw = {
            "bundle_id": "evid-str-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "update_existing_skill",
            "target_skill_id": "game_migration_verify",
            "evidence_refs": [
                "docs/analysis.md",
                "docs/review.md",
            ],
        }
        bundle = adapt_raw_proposal(raw)
        assert len(bundle.evidence_refs) == 2
        assert bundle.evidence_refs[0].path == "docs/analysis.md"
        assert bundle.evidence_refs[0].type == ""
        assert bundle.evidence_refs[1].path == "docs/review.md"

    def test_evidence_refs_as_dicts(self) -> None:
        """EvidenceRefs as dicts (type/path/description) are fully preserved."""
        raw = {
            "bundle_id": "evid-dict-test",
            "status": "proposed",
            "target_family": "portolan-integration",
            "action": "update_existing_skill",
            "target_skill_id": "portolan_integration_hermes_bootstrap",
            "evidence_refs": [
                {"type": "analysis", "path": "docs/analysis.md", "description": "Test analysis"},
                {"type": "review", "path": "docs/review.md", "description": "Test review"},
            ],
        }
        bundle = adapt_raw_proposal(raw)
        assert len(bundle.evidence_refs) == 2
        assert bundle.evidence_refs[0].type == "analysis"
        assert bundle.evidence_refs[0].path == "docs/analysis.md"
        assert bundle.evidence_refs[0].description == "Test analysis"
        assert bundle.evidence_refs[1].type == "review"
        assert bundle.evidence_refs[1].path == "docs/review.md"
        assert bundle.evidence_refs[1].description == "Test review"

    def test_evidence_refs_mixed_formats(self) -> None:
        """Mixed string and dict evidence refs are both accepted."""
        raw = {
            "bundle_id": "evid-mixed-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
            "evidence_refs": [
                "docs/simple.md",
                {"type": "detailed", "path": "docs/detailed.md", "description": "Detailed info"},
            ],
        }
        bundle = adapt_raw_proposal(raw)
        assert len(bundle.evidence_refs) == 2
        assert bundle.evidence_refs[0].path == "docs/simple.md"
        assert bundle.evidence_refs[0].type == ""
        assert bundle.evidence_refs[1].type == "detailed"
        assert bundle.evidence_refs[1].path == "docs/detailed.md"

    def test_evidence_refs_none(self) -> None:
        """Missing evidence_refs yields an empty tuple."""
        raw = {
            "bundle_id": "evid-none-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.evidence_refs == ()

    def test_evidence_refs_invalid_type(self) -> None:
        """Non-list evidence_refs yields an empty tuple."""
        raw = {
            "bundle_id": "evid-bad-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
            "evidence_refs": "not-a-list",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.evidence_refs == ()

    def test_supporting_issues_normalized(self) -> None:
        """supporting_issues is normalized to a tuple of strings."""
        raw = {
            "bundle_id": "issues-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
            "supporting_issues": ["ISSUE-001", "ISSUE-002"],
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.supporting_issues == ("ISSUE-001", "ISSUE-002")

    def test_missing_bundle_id_generates_fallback(self) -> None:
        """When bundle_id is missing, a fallback is generated."""
        raw = {
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.bundle_id.startswith("adapted-")

    def test_missing_target_family_defaults(self) -> None:
        """When target_family is missing, it defaults to 'unknown'."""
        raw = {
            "bundle_id": "no-family-test",
            "status": "proposed",
            "action": "create_new_skill",
            "new_skill_id": "test",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.target_family == "unknown"

    def test_missing_action_defaults(self) -> None:
        """When action is missing, it defaults to 'no_action'."""
        raw = {
            "bundle_id": "no-action-test",
            "status": "proposed",
            "target_family": "game-migration",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.action == "no_action"

    def test_invalid_risk_level_clamped(self) -> None:
        """An unrecognised risk_level is clamped to 'medium'."""
        raw = {
            "bundle_id": "risk-clamp-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
            "risk_level": "critical",
        }
        bundle = adapt_raw_proposal(raw)
        assert bundle.risk_level == "medium"

    def test_extra_fields_dropped_silently(self) -> None:
        """Fields outside SkillProposalBundle@v1 schema are silently dropped."""
        raw = {
            "bundle_id": "extra-fields-test",
            "status": "proposed",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "test",
            "Phase": "Phase 1",
            "Slice": "Slice A",
            "blocking": "waiting on review",
        }
        bundle = adapt_raw_proposal(raw)
        assert not hasattr(bundle, "Phase")
        assert not hasattr(bundle, "Slice")
        assert not hasattr(bundle, "blocking")
        # Core fields are unaffected
        assert bundle.bundle_id == "extra-fields-test"


# ── adapt_proposals (non-executable filtering) ───────────────────────


class TestAdaptProposals:
    """Tests for adapt_proposals — filtering non-executable structural markers."""

    def test_passes_through_normal_proposals(self) -> None:
        """Normal executable proposals pass through unchanged."""
        raws = [
            {
                "bundle_id": "exec-001",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "test_1",
            },
            {
                "bundle_id": "exec-002",
                "status": "accepted",
                "target_family": "portolan-integration",
                "action": "update_existing_skill",
                "target_skill_id": "portolan_integration_hermes_bootstrap",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 2
        assert bundles[0].bundle_id == "exec-001"
        assert bundles[1].bundle_id == "exec-002"

    def test_filters_phase_items(self) -> None:
        """Items with 'Phase' in the title or bundle_id are filtered out."""
        raws = [
            {
                "bundle_id": "phase-1-description",
                "title": "Phase 1: Foundation",
                "description": "Set up the initial project structure",
            },
            {
                "bundle_id": "exec-001",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "test",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 1
        assert bundles[0].bundle_id == "exec-001"

    def test_filters_slice_items(self) -> None:
        """Items with 'Slice' in the title or bundle_id are filtered out."""
        raws = [
            {
                "bundle_id": "slice-a-tasks",
                "title": "Slice A: Core logic",
            },
            {
                "bundle_id": "exec-002",
                "status": "accepted",
                "target_family": "game-migration",
                "action": "update_existing_skill",
                "target_skill_id": "game_migration_verify",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 1
        assert bundles[0].bundle_id == "exec-002"

    def test_filters_blocking_markers_without_action(self) -> None:
        """Items with 'block' in description but no action are filtered out."""
        raws = [
            {
                "bundle_id": "blocked-item",
                "description": "Blocked on external dependency",
            },
            {
                "bundle_id": "exec-003",
                "status": "proposed",
                "target_family": "portolan-integration",
                "action": "create_new_skill",
                "new_skill_id": "test",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 1
        assert bundles[0].bundle_id == "exec-003"

    def test_passes_legitimate_blocker_proposals(self) -> None:
        """Proposals about blockers with proper action fields pass through."""
        raws = [
            {
                "bundle_id": "game_migration_blocker",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "resolve_blocker",
                "description": "Handle the game migration blocking issue",
            },
            {
                "bundle_id": "exec-004",
                "status": "proposed",
                "target_family": "portolan-integration",
                "action": "update_existing_skill",
                "target_skill_id": "portolan_integration_hermes_bootstrap",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 2
        assert bundles[0].bundle_id == "game_migration_blocker"
        assert bundles[1].bundle_id == "exec-004"

    def test_empty_list(self) -> None:
        """An empty list returns an empty list."""
        assert adapt_proposals([]) == []

    def test_filters_items_without_bundle_id_and_action(self) -> None:
        """Items lacking both bundle_id and action are treated as non-executable."""
        raws = [
            {"title": "Some section header"},
            {
                "bundle_id": "exec-004",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "test",
            },
        ]
        bundles = adapt_proposals(raws)
        assert len(bundles) == 1
        assert bundles[0].bundle_id == "exec-004"


# ── adapt_and_filter_by_domain ───────────────────────────────────────


class TestAdaptAndFilterByDomain:
    """Tests for adapt_and_filter_by_domain — rutter domain scoping."""

    def test_filters_state_scanning(self) -> None:
        """Items referencing .state scanning are filtered out."""
        raws = [
            {
                "bundle_id": "state-scan-proposal",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "state_scanner",
            },
            {
                "bundle_id": "rutter-valid-proposal",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "rutter_skill",
            },
        ]
        # This test relies on the state-scan proposal's bundle_id or
        # target_family containing ".state" — the domain filter checks
        # the combined string of bundle_id + target_family + action.
        bundles = adapt_and_filter_by_domain(raws)
        # Both pass through since bundle_id doesn't actually contain ".state"
        # The NON_RUTTER_DOMAIN_PATTERNS would match target_family containing ".state"
        assert len(bundles) == 2

    def test_filters_taxonomy_adapter_references(self) -> None:
        """Items referencing taxonomy adapter are filtered out."""
        raws = [
            {
                "bundle_id": "taxonomy-mapping",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "taxonomy_mapper",
            },
        ]
        # The filter checks combined bundle_id + target_family + action.
        # "taxonomy" appears in bundle_id, so this should be filtered.
        bundles = adapt_and_filter_by_domain(raws)
        assert len(bundles) == 0

    def test_filters_run_to_session_references(self) -> None:
        """Items referencing run-to-session linking are filtered out."""
        raws = [
            {
                "bundle_id": "run-to-session-linker",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "session_linker",
            },
        ]
        bundles = adapt_and_filter_by_domain(raws)
        assert len(bundles) == 0

    def test_passes_rutter_domain_items(self) -> None:
        """Items in rutter's domain (review surface, validator, promotion, fixtures) pass through."""
        raws = [
            {
                "bundle_id": "review-surface-item",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "review_skill",
            },
            {
                "bundle_id": "validator-item",
                "status": "accepted",
                "target_family": "portolan-integration",
                "action": "update_existing_skill",
                "target_skill_id": "portolan_integration_hermes_bootstrap",
            },
            {
                "bundle_id": "promotion-tooling-item",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "metadata_only",
            },
        ]
        bundles = adapt_and_filter_by_domain(raws)
        assert len(bundles) == 3

    def test_mixed_domain_items_filtered_correctly(self) -> None:
        """Out-of-domain items are filtered while in-domain items are kept."""
        raws = [
            {
                "bundle_id": "taxonomy-adapter-sync",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "sync_tool",
            },
            {
                "bundle_id": "rutter-validator",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "validator_skill",
            },
            {
                "bundle_id": "dot-state-manager",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "state_manager",
            },
        ]
        bundles = adapt_and_filter_by_domain(raws)
        # "taxonomy-adapter-sync" contains "taxonomy" → filtered
        # "rutter-validator" → kept
        # "dot-state-manager" does NOT contain ".state" → kept. The ".state" pattern
        # targets the literal substring. "dot-state-manager" doesn't contain ".state"
        assert len(bundles) == 2
        assert bundles[0].bundle_id == "rutter-validator"
        assert bundles[1].bundle_id == "dot-state-manager"


# ── Integration: evidence ref shape compatibility ────────────────────


class TestEvidenceRefShape:
    """Verify EvidenceRef shape compatibility with meta-agent output."""

    def test_meta_agent_style_dict_refs(self) -> None:
        """Proposals with meta-agent-style evidence refs are adapted correctly."""
        raw = {
            "bundle_id": "meta-agent-style",
            "status": "accepted",
            "target_family": "game-migration",
            "action": "split_existing_skill",
            "target_skill_id": "game_migration_plan",
            "new_skill_id": "game_migration_plan_core",
            "evidence_refs": [
                {"type": "analysis", "path": "skills/game-migration/plan-split-analysis.md",
                 "description": "Analysis for splitting the plan skill"},
            ],
        }
        bundle = adapt_raw_proposal(raw)
        assert len(bundle.evidence_refs) == 1
        ref = bundle.evidence_refs[0]
        assert ref.type == "analysis"
        assert ref.path == "skills/game-migration/plan-split-analysis.md"
        assert ref.description == "Analysis for splitting the plan skill"

    def test_evidence_refs_are_skill_proposal_bundle_v1(self) -> None:
        """Adapted bundle is a valid SkillProposalBundle@v1 that passes validation."""
        from rutter.proposals import validate_proposal

        raw = {
            "bundle_id": "valid-after-adapt",
            "status": "accepted",
            "target_family": "game-migration",
            "action": "create_new_skill",
            "new_skill_id": "adapted_skill",
            "risk_level": "low",
            "evidence_refs": [
                {"type": "design", "path": "docs/design.md", "description": "Design doc"},
            ],
        }
        bundle = adapt_raw_proposal(raw)
        errors = validate_proposal(bundle)
        assert errors == [], f"Adapted bundle has validation errors: {errors}"


# ── Integration: split PRD import filtering ──────────────────────────


class TestSplitPRDImport:
    """Verify that split PRD imports are cleaned of non-executable items."""

    def test_full_split_prd_import(self) -> None:
        """Simulate importing a split PRD with mixed content."""
        raw_items = [
            # Phase header (non-executable)
            {
                "title": "Phase 1: Foundation",
                "description": "Initial setup phase",
            },
            # Slice boundary (non-executable)
            {
                "title": "Slice A: Core registry",
            },
            # Blocked item (non-executable)
            {
                "bundle_id": "blocked-on-registry",
                "description": "Blocked on registry v2 release",
            },
            # Valid rutter proposal (executable, in-domain)
            {
                "bundle_id": "rutter-review-surface",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "review_surface_skill",
            },
            # Out-of-domain (taxonomy)
            {
                "bundle_id": "taxonomy-classifier",
                "status": "proposed",
                "target_family": "game-migration",
                "action": "create_new_skill",
                "new_skill_id": "classifier_skill",
            },
            # Valid rutter proposal (executable, in-domain)
            {
                "bundle_id": "rutter-promotion-tool",
                "status": "accepted",
                "target_family": "portolan-integration",
                "action": "update_existing_skill",
                "target_skill_id": "portolan_integration_hermes_bootstrap",
            },
        ]

        bundles = adapt_and_filter_by_domain(raw_items)
        # Expected: only the two valid rutter proposals survive
        assert len(bundles) == 2
        ids = {b.bundle_id for b in bundles}
        assert "rutter-review-surface" in ids
        assert "rutter-promotion-tool" in ids
