from __future__ import annotations

from pathlib import Path

import pytest

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


# ── submit_proposal ─────────────────────────────────────────────────────


def test_submit_proposal_creates_yaml(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal = SkillProposalBundle(
        schema_version="v1",
        bundle_id="test-submit-001",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="some_new_skill",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )

    result_path = submit_proposal(proposal, tmp_path)
    assert result_path.exists()
    assert result_path.name == "test-submit-001.yaml"
    assert result_path.parent.name == "game-migration"

    import yaml
    raw = yaml.safe_load(result_path.read_text(encoding="utf-8"))
    assert raw["bundle_id"] == "test-submit-001"
    assert raw["status"] == "draft"
    assert raw["target_family"] == "game-migration"


def test_submit_proposal_validates_before_write(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import ProposalValidationError, submit_proposal

    proposal = SkillProposalBundle(
        schema_version="v2",
        bundle_id="bad-version",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
    )

    with pytest.raises(ProposalValidationError) as exc:
        submit_proposal(proposal, tmp_path)
    assert any("schema_version" in e for e in exc.value.errors)


def test_submit_proposal_rejects_duplicate(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal = SkillProposalBundle(
        schema_version="v1",
        bundle_id="dup-test",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )

    submit_proposal(proposal, tmp_path)
    with pytest.raises(FileExistsError):
        submit_proposal(proposal, tmp_path)


def test_submit_proposal_allow_overwrite(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal = SkillProposalBundle(
        schema_version="v1",
        bundle_id="overwrite-test",
        status="draft",
        target_family="game-migration",
        action="create_new_skill",
        new_skill_id="test",
        risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )

    p1 = submit_proposal(proposal, tmp_path)
    p2 = submit_proposal(proposal, tmp_path, allow_overwrite=True)
    assert p1 == p2


# ── list_proposals ──────────────────────────────────────────────────────


def test_list_proposals_empty_dir(tmp_path: Path) -> None:
    from rutter.proposals import list_proposals

    proposals = list_proposals(tmp_path)
    assert proposals == []


def test_list_proposals_with_proposals(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import list_proposals, submit_proposal

    p1 = SkillProposalBundle(
        schema_version="v1", bundle_id="list-001", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="skill_a", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    p2 = SkillProposalBundle(
        schema_version="v1", bundle_id="list-002", status="review",
        target_family="portolan-integration", action="update_existing_skill",
        target_skill_id="some_skill", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    )
    submit_proposal(p1, tmp_path)
    submit_proposal(p2, tmp_path)

    proposals = list_proposals(tmp_path)
    assert len(proposals) == 2
    assert proposals[0]["bundle_id"] == "list-001"
    assert proposals[1]["bundle_id"] == "list-002"


def test_list_proposals_status_filter(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import list_proposals, submit_proposal

    for i in range(3):
        submit_proposal(SkillProposalBundle(
            schema_version="v1", bundle_id=f"filter-{i:03d}", status="draft",
            target_family="game-migration", action="create_new_skill",
            new_skill_id=f"skill_{i}", risk_level="low",
            created_at="2026-05-02T00:00:00Z",
        ), tmp_path)

    # One in review
    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="filter-review", status="review",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="skill_review", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    drafts = list_proposals(tmp_path, status_filter="draft")
    assert len(drafts) == 3

    reviews = list_proposals(tmp_path, status_filter="review")
    assert len(reviews) == 1


def test_list_proposals_family_filter(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import list_proposals, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="fam-game", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="s1", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)
    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="fam-portolan", status="draft",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="s2", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    game = list_proposals(tmp_path, family_filter="game-migration")
    assert len(game) == 1
    assert game[0]["bundle_id"] == "fam-game"


# ── get_proposal ────────────────────────────────────────────────────────


def test_get_proposal_found(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import get_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="get-test", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    bundle = get_proposal(tmp_path, "get-test")
    assert bundle is not None
    assert bundle.bundle_id == "get-test"
    assert bundle.target_family == "game-migration"


def test_get_proposal_not_found(tmp_path: Path) -> None:
    from rutter.proposals import get_proposal

    bundle = get_proposal(tmp_path, "nonexistent")
    assert bundle is None


# ── review_proposal ─────────────────────────────────────────────────────


def test_review_proposal_updates_status(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import get_proposal, review_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="review-me", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    review_proposal(tmp_path, "review-me", "review")
    bundle = get_proposal(tmp_path, "review-me")
    assert bundle is not None
    assert bundle.status == "review"


def test_review_proposal_invalid_status(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import ProposalValidationError, review_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="bad-status", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    with pytest.raises(ProposalValidationError) as exc:
        review_proposal(tmp_path, "bad-status", "invalid_status")
    assert any("status" in e for e in exc.value.errors)


def test_review_proposal_not_found(tmp_path: Path) -> None:
    from rutter.proposals import ProposalValidationError, review_proposal

    with pytest.raises(ProposalValidationError) as exc:
        review_proposal(tmp_path, "nonexistent", "approved")
    assert any("not found" in e for e in exc.value.errors)


# ── CLI proposal commands ───────────────────────────────────────────────


def test_cli_propose_creates_file(tmp_path: Path) -> None:
    from rutter.cli import main
    from rutter.proposals import load_proposals

    proposal_dir = tmp_path / "proposals"
    exit_code = main([
        "propose",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
        "--bundle-id", "cli-propose-001",
        "--target-family", "game-migration",
        "--action", "create_new_skill",
        "--new-skill-id", "cli_test_skill",
        "--risk-level", "low",
        "--status", "draft",
        "--created-at", "2026-05-02T00:00:00Z",
    ])
    assert exit_code == 0

    bundles = load_proposals(proposal_dir)
    assert len(bundles) == 1
    assert bundles[0].bundle_id == "cli-propose-001"


def test_cli_propose_validates_failure(tmp_path: Path) -> None:
    from rutter.cli import main

    exit_code = main([
        "propose",
        "--path", str(tmp_path),
        "--bundle-id", "bad-cli",
        "--target-family", "nonexistent-family",
        "--action", "create_new_skill",
        "--new-skill-id", "test",
    ])
    assert exit_code == 1  # Validation should fail


def test_cli_list_proposals_empty(tmp_path: Path) -> None:
    from rutter.cli import main

    exit_code = main([
        "list-proposals",
        "--path", str(tmp_path),
        "--proposal-dir", str(tmp_path / "empty_proposals"),
    ])
    assert exit_code == 0


def test_cli_list_proposals_with_data(tmp_path: Path, capsys) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="cli-list-001", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "list-proposals",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "cli-list-001" in captured.out


def test_cli_get_proposal_found(tmp_path: Path, capsys) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="cli-get-001", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "get-proposal",
        "cli-get-001",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "cli-get-001" in captured.out


def test_cli_get_proposal_not_found(tmp_path: Path, capsys) -> None:
    from rutter.cli import main

    exit_code = main([
        "get-proposal",
        "nonexistent",
        "--path", str(tmp_path),
        "--proposal-dir", str(tmp_path / "proposals"),
    ])
    assert exit_code == 1


def test_cli_review_proposal_updates_status(tmp_path: Path, capsys) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import get_proposal, submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="v1", bundle_id="cli-review-001", status="draft",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "review-proposal",
        "cli-review-001",
        "--status", "approved",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0

    bundle = get_proposal(proposal_dir, "cli-review-001")
    assert bundle is not None
    assert bundle.status == "approved"
