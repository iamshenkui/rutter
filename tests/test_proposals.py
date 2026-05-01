from __future__ import annotations

from pathlib import Path

from rutter.cli import main
from rutter.proposals import (
    dump_proposal_validation_result,
    load_proposal_files,
    load_proposals,
    validate_proposal,
    validate_proposals,
)
from rutter.registry import validate_registry

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = PROJECT_ROOT / "registry"
FIXTURES_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "proposals"


# ── validate_proposal (single proposal, no registry) ────────────────────


def test_valid_create_new_skill_passes_without_registry() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-001",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="some_new_skill",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert errors == []


def test_valid_update_existing_skill_passes_without_registry() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-002",
        status="review",
        target_family="game-migration",
        action="update_existing_skill",
        target_skill_id="game_migration_verify",
        risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert errors == []


def test_invalid_schema_version() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v2",
        bundle_id="proposal-003",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert any("schema_version" in e for e in errors)


def test_invalid_action() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-004",
        status="draft",
        target_family="game-migration",
        action="delete_skill",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert any("action" in e for e in errors)


def test_invalid_status() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-005",
        status="cancelled",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert any("status" in e for e in errors)


def test_invalid_risk_level() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-006",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="critical",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert any("risk_level" in e for e in errors)


def test_invalid_created_at() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-007",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="not-a-date",
    )
    errors = validate_proposal(bundle)
    assert any("created_at" in e for e in errors)


def test_empty_bundle_id() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle)
    assert any("bundle_id" in e for e in errors)


# ── validate_proposal with registry cross-references ────────────────────


def test_update_existing_skill_requires_target_skill_id() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-008",
        status="draft",
        target_family="game-migration",
        action="update_existing_skill",
        target_skill_id=None,
        risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle, registry_root=REGISTRY_ROOT)
    assert any("target_skill_id" in e for e in errors)


def test_update_existing_skill_requires_existing_skill_id() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-009",
        status="draft",
        target_family="game-migration",
        action="update_existing_skill",
        target_skill_id="nonexistent_skill",
        risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle, registry_root=REGISTRY_ROOT)
    assert any("not found" in e for e in errors)


def test_create_new_skill_requires_non_empty_new_skill_id() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-010",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id=None,
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle, registry_root=REGISTRY_ROOT)
    assert any("new_skill_id" in e for e in errors)


def test_create_new_skill_collides_with_existing_skill() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-011",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="game_migration_verify",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle, registry_root=REGISTRY_ROOT)
    assert any("collides" in e for e in errors)


def test_unknown_target_family() -> None:
    from rutter.models import SkillProposalBundle

    bundle = SkillProposalBundle(
        schema_version="v1",
        bundle_id="proposal-012",
        status="draft",
        target_family="nonexistent",
        action="create_new_skill",
        new_skill_id="some_new_skill",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    errors = validate_proposal(bundle, registry_root=REGISTRY_ROOT)
    assert any("target_family" in e for e in errors)
    assert any("nonexistent" in e for e in errors)


# ── validate_proposals (scan directories) ───────────────────────────────


def test_validate_proposals_valid_directory() -> None:
    results = validate_proposals(FIXTURES_ROOT / "valid", registry_root=REGISTRY_ROOT)
    assert len(results) == 4
    for path, errors in results.items():
        assert errors == [], f"Expected {path} to have no errors, got: {errors}"


def test_validate_proposals_invalid_directory() -> None:
    results = validate_proposals(FIXTURES_ROOT / "invalid", registry_root=REGISTRY_ROOT)
    assert len(results) == 8
    for path, errors in results.items():
        assert len(errors) > 0, f"Expected {path} to have errors"


def test_validate_proposals_does_not_modify_registry() -> None:
    """Confirm validate-proposals is read-only: registry must still pass validation."""
    results = validate_proposals(FIXTURES_ROOT / "valid", registry_root=REGISTRY_ROOT)
    assert any(errors == [] for errors in results.values())
    # Registry itself must be unmodified
    assert validate_registry(REGISTRY_ROOT) == []


def test_dump_proposal_validation_result() -> None:
    results = {"file1.yaml": [], "file2.yaml": ["error 1", "error 2"]}
    dumped = dump_proposal_validation_result(results)
    assert dumped["total"] == 2
    assert dumped["valid"] == 1
    assert dumped["invalid"] == 1
    assert dumped["details"][0]["file"] == "file1.yaml"
    assert dumped["details"][0]["valid"] is True
    assert dumped["details"][1]["file"] == "file2.yaml"
    assert dumped["details"][1]["valid"] is False
    assert dumped["details"][1]["errors"] == ["error 1", "error 2"]


# ── CLI tests ───────────────────────────────────────────────────────────


def test_cli_validate_proposals_valid(capsys) -> None:
    exit_code = main(
        [
            "validate-proposals",
            "--path",
            str(PROJECT_ROOT),
            "--proposal-dir",
            str(FIXTURES_ROOT / "valid"),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
    assert "OK" in captured.out


def test_cli_validate_proposals_invalid(capsys) -> None:
    exit_code = main(
        [
            "validate-proposals",
            "--path",
            str(PROJECT_ROOT),
            "--proposal-dir",
            str(FIXTURES_ROOT / "invalid"),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1, captured.err
    assert "FAIL" in captured.err


def test_cli_validate_proposals_json(capsys) -> None:
    exit_code = main(
        [
            "validate-proposals",
            "--path",
            str(PROJECT_ROOT),
            "--proposal-dir",
            str(FIXTURES_ROOT / "valid"),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "total" in captured.out
    assert "valid" in captured.out
    assert "details" in captured.out


# ── Loading proposals from directory tree ───────────────────────────────


def test_load_proposals_flat_dir() -> None:
    bundles = load_proposal_files(FIXTURES_ROOT / "valid" / "create_new_skill")
    assert len(bundles) == 2
    ids = {b.bundle_id for b in bundles}
    assert "proposal-20260502-valid-new-001" in ids
    assert "proposal-20260502-valid-new-002" in ids


def test_load_proposals_nested_dir() -> None:
    bundles = load_proposals(FIXTURES_ROOT / "valid")
    assert len(bundles) == 4
    families = {b.target_family for b in bundles}
    assert "game-migration" in families
    assert "portolan-integration" in families


def test_load_proposals_missing_dir() -> None:
    from rutter.proposals import ProposalValidationError

    try:
        load_proposals(FIXTURES_ROOT / "nonexistent")
        assert False, "Expected ProposalValidationError"
    except ProposalValidationError as exc:
        assert any("not found" in e for e in exc.errors)
