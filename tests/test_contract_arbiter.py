"""Contract arbiter tests: validate proposal fixture files against SkillProposalBundle@v1.

These tests form the arbiter layer, ensuring that proposal YAML files — whether
produced by meta-agent or hand-authored — are correctly validated by rutter's
validator against the cross-repository contract. This prevents regression in
the contract between meta-agent (proposal producer) and rutter (proposal consumer).

Key properties tested:
- Each valid fixture passes validation cleanly.
- Each invalid fixture fails with the expected error messages.
- The validator remains consistent between fixture-driven and programmatic paths.
- No external dependencies (meta-agent) are required for validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rutter.models import SkillProposalBundle
from rutter.proposals import validate_proposal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = PROJECT_ROOT / "registry"
FIXTURES_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "proposals"


def _load_yaml_as_bundle(path: Path) -> SkillProposalBundle | None:
    """Load a single fixture YAML file into a SkillProposalBundle."""
    if not path.exists():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(raw, dict):
        return None
    return SkillProposalBundle(
        schema_version=raw.get("schema_version", ""),
        bundle_id=raw.get("bundle_id", ""),
        status=raw.get("status", ""),
        target_family=raw.get("target_family", ""),
        action=raw.get("action", ""),
        supporting_issues=tuple(raw.get("supporting_issues", []) or []),
        evidence_refs=tuple(raw.get("evidence_refs", []) or []),
        risk_level=raw.get("risk_level", "medium"),
        created_at=raw.get("created_at", ""),
        target_skill_id=raw.get("target_skill_id"),
        new_skill_id=raw.get("new_skill_id"),
    )


# ── Fixture contract matrix ────────────────────────────────────────────
# Each entry: (relative_path, expect_valid, required_error_hints)
# required_error_hints are substrings that must appear in at least one
# validation error when expect_valid is False; ignored when True.

FIXTURE_CONTRACTS: list[tuple[str, bool, list[str]]] = [
    # Valid: create_new_skill for game-migration
    (
        "valid/create_new_skill/valid-new-skill.yaml",
        True,
        [],
    ),
    # Valid: create_new_skill for portolan-integration
    (
        "valid/create_new_skill/valid-new-portolan-skill.yaml",
        True,
        [],
    ),
    # Valid: update_existing_skill for game-migration
    (
        "valid/update_existing_skill/valid-update-skill.yaml",
        True,
        [],
    ),
    # Valid: update_existing_skill for portolan-integration
    (
        "valid/update_existing_skill/valid-update-portolan-skill.yaml",
        True,
        [],
    ),
    # Invalid: new_skill_id collides with existing registry skill
    (
        "invalid/create-colliding-id.yaml",
        False,
        ["collides", "skill"],
    ),
    # Invalid: new_skill_id is empty string
    (
        "invalid/create-empty-id.yaml",
        False,
        ["new_skill_id", "non-empty"],
    ),
    # Invalid: action is not in the allowed set
    (
        "invalid/invalid-action.yaml",
        False,
        ["action", "delete_skill"],
    ),
    # Invalid: target_family does not exist in registry
    (
        "invalid/invalid-family.yaml",
        False,
        ["target_family", "nonexistent"],
    ),
    # Invalid: risk_level is not in the allowed set
    (
        "invalid/invalid-risk-level.yaml",
        False,
        ["risk_level", "critical"],
    ),
    # Invalid: schema_version is not in the allowed set
    (
        "invalid/invalid-schema-version.yaml",
        False,
        ["schema_version", "0"],
    ),
    # Invalid: bundle_id is empty string
    (
        "invalid/missing-bundle-id.yaml",
        False,
        ["bundle_id", "empty"],
    ),
    # Invalid: update_existing_skill without target_skill_id
    (
        "invalid/update-missing-target.yaml",
        False,
        ["target_skill_id"],
    ),
]


class TestArbiterFixtureContracts:
    """Fixture-driven contract tests for the arbiter layer."""

    @pytest.mark.parametrize(
        ("rel_path", "expect_valid", "error_hints"),
        FIXTURE_CONTRACTS,
        ids=[e[0].replace("/", "-") for e in FIXTURE_CONTRACTS],
    )
    def test_fixture_validation_contract(
        self,
        rel_path: str,
        expect_valid: bool,
        error_hints: list[str],
    ) -> None:
        """Every fixture YAML must produce exactly its expected validation outcome.

        This is the core arbiter assertion: it validates that proposal files
        conforming to the contract pass validation, and files violating specific
        contract rules fail with the correct diagnostics.
        """
        fixture_path = FIXTURES_ROOT / rel_path
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        bundle = _load_yaml_as_bundle(fixture_path)
        assert bundle is not None, f"Could not parse fixture: {fixture_path}"

        errors = validate_proposal(bundle, source=fixture_path, registry_root=REGISTRY_ROOT)

        if expect_valid:
            assert errors == [], (
                f"Expected {rel_path} to be valid, but got {len(errors)} error(s):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        else:
            assert len(errors) > 0, (
                f"Expected {rel_path} to be invalid, but it passed validation"
            )
            for hint in error_hints:
                assert any(hint.lower() in e.lower() for e in errors), (
                    f"Expected error containing {hint!r} for {rel_path}, "
                    f"but got: {errors}"
                )

    # ── Parsing resilience ──────────────────────────────────────────────

    def test_all_valid_fixtures_are_loadable(self) -> None:
        """All valid fixture YAML files must be parseable as SkillProposalBundle."""
        valid_root = FIXTURES_ROOT / "valid"
        yaml_files = sorted(valid_root.rglob("*.yaml"))
        assert len(yaml_files) == 4, f"Expected 4 valid fixtures, found {len(yaml_files)}"

        for yf in yaml_files:
            bundle = _load_yaml_as_bundle(yf)
            assert bundle is not None, f"Failed to load valid fixture: {yf}"
            # All field-level validations must pass too
            errors = validate_proposal(bundle, source=yf, registry_root=REGISTRY_ROOT)
            assert errors == [], f"Valid fixture {yf.name} has validation errors: {errors}"

    def test_all_invalid_fixtures_are_loadable(self) -> None:
        """All invalid fixture YAML files must be parseable as SkillProposalBundle."""
        invalid_root = FIXTURES_ROOT / "invalid"
        yaml_files = sorted(invalid_root.glob("*.yaml"))
        assert len(yaml_files) == 8, f"Expected 8 invalid fixtures, found {len(yaml_files)}"

        for yf in yaml_files:
            bundle = _load_yaml_as_bundle(yf)
            assert bundle is not None, f"Failed to load invalid fixture: {yf}"
            # Must produce at least one validation error
            errors = validate_proposal(bundle, source=yf, registry_root=REGISTRY_ROOT)
            assert len(errors) > 0, f"Invalid fixture {yf.name} passed validation"

    # ── No external dependency test ──────────────────────────────────────

    def test_validator_works_without_meta_agent(self) -> None:
        """Validator can run standalone — no meta-agent imports or runtime required.

        This test validates the core FR-2 requirement: rutter must validate
        proposals independently of meta-agent. We verify by importing only
        from rutter.* and executing validation without any external harness.
        """
        # Load a valid fixture directly
        fixture = FIXTURES_ROOT / "valid" / "create_new_skill" / "valid-new-skill.yaml"
        raw = yaml.safe_load(fixture.read_text(encoding="utf-8"))

        bundle = SkillProposalBundle(
            schema_version=raw["schema_version"],
            bundle_id=raw["bundle_id"],
            status=raw["status"],
            target_family=raw["target_family"],
            action=raw["action"],
            new_skill_id=raw.get("new_skill_id"),
            risk_level=raw.get("risk_level", "medium"),
            supporting_issues=tuple(raw.get("supporting_issues", []) or []),
            evidence_refs=tuple(raw.get("evidence_refs", []) or []),
            created_at=raw.get("created_at", ""),
        )
        errors = validate_proposal(bundle)
        assert errors == [], f"Standalone validation failed: {errors}"

    # ── Schema contract consistency ─────────────────────────────────────

    def test_valid_fixtures_use_correct_schema_and_enum_values(self) -> None:
        """All valid fixtures must use schema_version 1 and valid enum values."""
        valid_root = FIXTURES_ROOT / "valid"
        for yf in sorted(valid_root.rglob("*.yaml")):
            raw = yaml.safe_load(yf.read_text(encoding="utf-8"))
            assert raw["schema_version"] == "1", f"{yf.name}: schema_version must be 1"
            assert raw["status"] in {
                "proposed", "needs_revision", "accepted", "rejected", "promoted"
            }, f"{yf.name}: invalid status"
            assert raw["action"] in {
                "create_new_skill", "update_existing_skill", "split_existing_skill",
                "deprecate_skill", "metadata_only", "no_action"
            }, f"{yf.name}: invalid action"
            assert raw.get("risk_level", "medium") in {
                "low", "medium", "high"
            }, f"{yf.name}: invalid risk_level"
            assert raw.get("target_family", ""), f"{yf.name}: missing target_family"
            assert raw.get("bundle_id", ""), f"{yf.name}: missing bundle_id"

    def test_invalid_fixtures_have_contract_violations(self) -> None:
        """Each invalid fixture must violate at least one contract rule."""
        invalid_root = FIXTURES_ROOT / "invalid"
        for yf in sorted(invalid_root.glob("*.yaml")):
            bundle = _load_yaml_as_bundle(yf)
            assert bundle is not None, f"Failed to load fixture: {yf}"
            errors = validate_proposal(
                bundle,
                source=yf,
                registry_root=REGISTRY_ROOT,
            )
            assert len(errors) >= 1, (
                f"Invalid fixture {yf.name} does not trigger any validation error"
            )

            # Every error should reference the fixture file
            fixture_str = str(yf.resolve())
            assert any(fixture_str in e for e in errors), (
                f"Validation errors must reference the source file: {errors}"
            )

    # ── Fixture stability ───────────────────────────────────────────────

    def test_fixture_count_is_stable(self) -> None:
        """The number of fixture files must remain as expected.

        This is a stability test: if the count changes, the contract matrix
        above must be updated accordingly. The arbiter layers relies on a
        known set of fixture files for deterministic contract verification.
        """
        valid_count = len(list((FIXTURES_ROOT / "valid").rglob("*.yaml")))
        invalid_count = len(list((FIXTURES_ROOT / "invalid").glob("*.yaml")))
        assert valid_count == 4, f"Expected 4 valid fixtures, found {valid_count}"
        assert invalid_count == 8, f"Expected 8 invalid fixtures, found {invalid_count}"
