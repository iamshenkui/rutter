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
        schema_version="1",
        bundle_id="proposal-001",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-002",
        status="needs_revision",
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
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-004",
        status="proposed",
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
        schema_version="1",
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
        schema_version="1",
        bundle_id="proposal-006",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-007",
        status="proposed",
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
        schema_version="1",
        bundle_id="",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-008",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-009",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-010",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-011",
        status="proposed",
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
        schema_version="1",
        bundle_id="proposal-012",
        status="proposed",
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
        schema_version="1",
        bundle_id="test-submit-001",
        status="proposed",
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
    assert raw["status"] == "proposed"
    assert raw["target_family"] == "game-migration"


def test_submit_proposal_validates_before_write(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import ProposalValidationError, submit_proposal

    proposal = SkillProposalBundle(
        schema_version="v2",
        bundle_id="bad-version",
        status="proposed",
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
        schema_version="1",
        bundle_id="dup-test",
        status="proposed",
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
        schema_version="1",
        bundle_id="overwrite-test",
        status="proposed",
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
        schema_version="1", bundle_id="list-001", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="skill_a", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    )
    p2 = SkillProposalBundle(
        schema_version="1", bundle_id="list-002", status="needs_revision",
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
            schema_version="1", bundle_id=f"filter-{i:03d}", status="proposed",
            target_family="game-migration", action="create_new_skill",
            new_skill_id=f"skill_{i}", risk_level="low",
            created_at="2026-05-02T00:00:00Z",
        ), tmp_path)

    # One in review
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="filter-review", status="needs_revision",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="skill_review", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    drafts = list_proposals(tmp_path, status_filter="proposed")
    assert len(drafts) == 3

    reviews = list_proposals(tmp_path, status_filter="needs_revision")
    assert len(reviews) == 1


def test_list_proposals_family_filter(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import list_proposals, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="fam-game", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="s1", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="fam-portolan", status="proposed",
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
        schema_version="1", bundle_id="get-test", status="proposed",
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
        schema_version="1", bundle_id="review-me", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    review_proposal(tmp_path, "review-me", "needs_revision")
    bundle = get_proposal(tmp_path, "review-me")
    assert bundle is not None
    assert bundle.status == "needs_revision"


def test_review_proposal_invalid_status(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import ProposalValidationError, review_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="bad-status", status="proposed",
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
        review_proposal(tmp_path, "nonexistent", "accepted")
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
        "--status", "proposed",
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
        schema_version="1", bundle_id="cli-list-001", status="proposed",
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
        schema_version="1", bundle_id="cli-get-001", status="proposed",
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


# ── promote_proposal ─────────────────────────────────────────────────────


def test_promote_proposal_rejects_non_accepted(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import ProposalValidationError, promote_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="promote-draft", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    with pytest.raises(ProposalValidationError) as exc:
        promote_proposal(tmp_path, "promote-draft")
    assert any("accepted" in e for e in exc.value.errors)


def test_promote_proposal_rejects_not_found(tmp_path: Path) -> None:
    from rutter.proposals import ProposalValidationError, promote_proposal

    with pytest.raises(ProposalValidationError) as exc:
        promote_proposal(tmp_path, "nonexistent")
    assert any("not found" in e for e in exc.value.errors)


def test_promote_proposal_creates_plan_for_create_new_skill(tmp_path: Path) -> None:
    from rutter.models import EvidenceRef, SkillProposalBundle
    from rutter.proposals import promote_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="promote-create", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_migration_asset_optimizer", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
        evidence_refs=(EvidenceRef(path="skills/game-migration/asset-optimizer.md"),),
    ), tmp_path)

    plan = promote_proposal(tmp_path, "promote-create")
    item = plan["promotion_plan"]
    assert item["proposal"]["bundle_id"] == "promote-create"
    assert item["proposal"]["action"] == "create_new_skill"
    assert item["proposal"]["status"] == "accepted"
    assert item["v0.1_note"] != ""

    # Should generate two operations: create YAML + update manifest
    ops = item["registry_operations"]
    assert len(ops) == 2
    assert ops[0]["type"] == "create_skill_yaml"
    assert "game_migration_asset_optimizer" in ops[0]["path"]
    assert ops[1]["type"] == "update_manifest"
    assert "manifest.yaml" in ops[1]["path"]


def test_promote_proposal_creates_plan_for_update_existing_skill(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import promote_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="promote-update", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    plan = promote_proposal(tmp_path, "promote-update")
    item = plan["promotion_plan"]
    assert item["proposal"]["bundle_id"] == "promote-update"
    assert item["proposal"]["action"] == "update_existing_skill"
    assert item["v0.1_note"] != ""

    ops = item["registry_operations"]
    assert len(ops) == 1
    assert ops[0]["type"] == "update_skill_yaml"
    assert "game_migration_verify" in ops[0]["path"]


def test_promote_proposal_plan_includes_v0_1_note(tmp_path: Path) -> None:
    from rutter.models import SkillProposalBundle
    from rutter.proposals import promote_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="promote-v01", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    plan = promote_proposal(tmp_path, "promote-v01")
    note = plan["promotion_plan"]["v0.1_note"]
    assert isinstance(note, str)
    assert len(note) > 0
    assert "No automatic changes" in note


def test_promote_proposal_resolves_registry_target_version(tmp_path: Path) -> None:
    """When registry_root is provided, the plan includes the resolved version."""
    from pathlib import Path
    from rutter.models import SkillProposalBundle
    from rutter.proposals import promote_proposal, submit_proposal

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="promote-registry", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), tmp_path)

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    plan = promote_proposal(tmp_path, "promote-registry", registry_root=PROJECT_ROOT)
    target = plan["promotion_plan"]["proposal"]["target_version"]
    assert target is not None
    assert target != "<unknown-version>"
    assert target == "v0.2"


def test_cli_promote_proposal_accepted(capsys, tmp_path: Path) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-001", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="cli_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-001",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "promotion_plan" in captured.out
    assert "cli-promote-001" in captured.out
    assert "registry_operations" in captured.out


def test_cli_promote_proposal_rejects_non_accepted(capsys, tmp_path: Path) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-draft", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="cli_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-draft",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_not_found(capsys, tmp_path: Path) -> None:
    from rutter.cli import main

    exit_code = main([
        "promote-proposal",
        "nonexistent",
        "--path", str(tmp_path),
        "--proposal-dir", str(tmp_path / "proposals"),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_with_registry_resolves_version(capsys, tmp_path: Path) -> None:
    """CLI promote-proposal resolves the target version when --path points to the project root."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-v", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="versioned_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-v",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "v0.2" in captured.out


def test_cli_promote_proposal_with_registry_rejects_non_accepted(capsys, tmp_path: Path) -> None:
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-rej", status="rejected",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="rejected_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-rej",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_with_accepted_and_registry(capsys, tmp_path: Path) -> None:
    """Full integration: accepted proposal with real registry returns a valid promotion plan."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-full", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-full",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "update_skill_yaml" in captured.out
    assert "game_migration_verify" in captured.out
    assert "registry/game-migration/v0.2" in captured.out
    assert "No automatic changes" in captured.out


def test_cli_promote_proposal_show_help(capsys) -> None:
    from rutter.cli import main

    try:
        main(["promote-proposal", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "accepted" in captured.out.lower()


def test_cli_promote_proposal_with_accepted_create_skill_with_registry(capsys, tmp_path: Path) -> None:
    """Accepted create_new_skill proposal with real registry provides correct operations."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-create-001", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_migration_new_feature", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-create-001",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "create_skill_yaml" in captured.out
    assert "update_manifest" in captured.out
    assert "game_migration_new_feature" in captured.out
    assert "No automatic changes" in captured.out


def test_cli_promote_proposal_with_accepted_update_skill_with_registry(capsys, tmp_path: Path) -> None:
    """Accepted update_existing_skill proposal with real registry provides correct operations."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-update-001", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="high",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-update-001",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "update_skill_yaml" in captured.out
    assert "game_migration_verify" in captured.out
    assert "No automatic changes" in captured.out


def test_cli_promote_proposal_without_proposal_dir_uses_default(tmp_path: Path, capsys) -> None:
    """When --proposal-dir is omitted, use --path/proposals as default."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-default-dir", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="default_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-default-dir",
        "--path", str(tmp_path),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "cli-default-dir" in captured.out


def test_cli_promote_proposal_with_v0_1_note(tmp_path: Path, capsys) -> None:
    """The promotion plan always includes the v0.1 human-review note."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-v01-note", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="note_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-v01-note",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "v0.1_note" in captured.out
    assert "No automatic changes" in captured.out


def test_cli_promote_proposal_generates_yaml_output(tmp_path: Path, capsys) -> None:
    """The promotion plan output is valid YAML."""
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-yaml-test", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="yaml_test_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-yaml-test",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Must be parseable YAML
    parsed = yaml.safe_load(captured.out)
    assert parsed is not None
    assert "promotion_plan" in parsed
    assert parsed["promotion_plan"]["proposal"]["bundle_id"] == "cli-yaml-test"


def test_cli_promote_proposal_unknown_family_with_registry(tmp_path: Path, capsys) -> None:
    """Even with an unknown family in the registry, the plan is still generated."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-unknown-family", status="accepted",
        target_family="nonexistent-family", action="create_new_skill",
        new_skill_id="unknown_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-unknown-family",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    # Should still succeed since the plan is still generated
    assert exit_code == 0


def test_cli_promote_proposal_approved_is_not_accepted(capsys, tmp_path: Path) -> None:
    """approved proposal cannot be promoted — only accepted is valid."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-approved-not-accepted", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="approved_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-approved-not-accepted",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_review_is_not_accepted(capsys, tmp_path: Path) -> None:
    """review proposal cannot be promoted — only accepted is valid."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-review-not-accepted", status="needs_revision",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="review_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-review-not-accepted",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_help_includes_description(capsys) -> None:
    """Help text mentions 'accepted proposal' in the description."""
    from rutter.cli import main

    try:
        main(["promote-proposal", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "accepted" in captured.out.lower()


def test_cli_promote_proposal_rejected_is_not_accepted(capsys, tmp_path: Path) -> None:
    """rejected proposal cannot be promoted — only accepted is valid."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-rejected-not-accepted", status="rejected",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="rejected_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-rejected-not-accepted",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_draft_is_not_accepted(capsys, tmp_path: Path) -> None:
    """draft proposal cannot be promoted — only accepted is valid."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-draft-not-accepted", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="draft_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-draft-not-accepted",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_update_skill_with_registry_version(tmp_path: Path, capsys) -> None:
    """update_existing_skill promotion plan uses resolved registry version."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-update-v2", status="accepted",
        target_family="portolan-integration", action="update_existing_skill",
        target_skill_id="portolan_integration_hermes_bootstrap", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-update-v2",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "portolan-integration/v0.1" in captured.out
    assert "portolan_integration_hermes_bootstrap" in captured.out


def test_cli_promote_proposal_create_with_registry_uses_correct_ops(tmp_path: Path, capsys) -> None:
    """create_new_skill with real registry generates create_skill_yaml + update_manifest."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-create-ops", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="portolan_integration_new_tool", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-create-ops",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "create_skill_yaml" in captured.out
    assert "update_manifest" in captured.out
    assert "portolan-integration/v0.1" in captured.out
    assert "portolan_integration_new_tool" in captured.out


def test_cli_promote_proposal_create_with_missing_registry_graceful(tmp_path: Path, capsys) -> None:
    """When the registry path has no registry subdir, the plan still generates."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-no-reg", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="no_reg_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-no-reg",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "create_skill_yaml" in captured.out


def test_cli_promote_proposal_empty_proposal_dir(tmp_path: Path, capsys) -> None:
    """Empty proposal directory returns an error."""
    from rutter.cli import main

    exit_code = main([
        "promote-proposal",
        "any-bundle-id",
        "--path", str(tmp_path),
        "--proposal-dir", str(tmp_path / "nonexistent"),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_update_existing_skill_with_evidence_refs(tmp_path: Path, capsys) -> None:
    """Promotion plan for update_existing_skill includes evidence refs."""
    from rutter.cli import main
    from rutter.models import EvidenceRef, SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-evidence-update", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        evidence_refs=(EvidenceRef(path="skills/game-migration/verify-update.md"),),
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-evidence-update",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "update_skill_yaml" in captured.out
    assert "game_migration_verify" in captured.out


def test_cli_promote_proposal_multiple_proposals_one_accepted(tmp_path: Path, capsys) -> None:
    """When multiple proposals exist, only the accepted one can be promoted."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="proposal-draft", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="draft_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="proposal-accepted", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="accepted_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="proposal-rejected", status="rejected",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="rejected_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    # Draft should fail
    assert main(["promote-proposal", "proposal-draft",
        "--path", str(tmp_path), "--proposal-dir", str(proposal_dir)]) == 1

    # Rejected should fail
    assert main(["promote-proposal", "proposal-rejected",
        "--path", str(tmp_path), "--proposal-dir", str(proposal_dir)]) == 1

    # Accepted should succeed
    assert main(["promote-proposal", "proposal-accepted",
        "--path", str(tmp_path), "--proposal-dir", str(proposal_dir)]) == 0


def test_cli_promote_proposal_create_new_skill_with_registry_and_supporting_issues(tmp_path: Path, capsys) -> None:
    """Create new skill plan includes supporting issues from the proposal."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-issues", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="issue_skill", risk_level="low",
        supporting_issues=("ISSUE-123", "ISSUE-456"),
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-issues",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ISSUE-123" in captured.out
    assert "ISSUE-456" in captured.out


def test_cli_promote_proposal_with_real_registry_preserves_registry(tmp_path: Path, capsys) -> None:
    """Promotion plan does NOT modify the live registry."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal
    from rutter.registry import validate_registry

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"

    # Snapshot registry state
    pre_errors = validate_registry(PROJECT_ROOT / "registry")

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-promote-safe", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="safe_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-promote-safe",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0

    # Registry must be unmodified
    post_errors = validate_registry(PROJECT_ROOT / "registry")
    assert pre_errors == post_errors


def test_cli_promote_proposal_includes_structured_output(tmp_path: Path, capsys) -> None:
    """The promotion plan is structured YAML with proposal, operations, and v0.1 note."""
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-structured", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="structured_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-structured",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)

    plan = parsed["promotion_plan"]
    assert "proposal" in plan
    assert "registry_operations" in plan
    assert "v0.1_note" in plan
    assert plan["proposal"]["bundle_id"] == "cli-structured"
    assert plan["proposal"]["action"] == "create_new_skill"
    assert plan["proposal"]["status"] == "accepted"


def test_cli_promote_proposal_risk_level_in_plan(tmp_path: Path, capsys) -> None:
    """The promotion plan includes the risk level from the proposal."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-risk-test", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="risk_test_skill", risk_level="high",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-risk-test",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "high" in captured.out


def test_cli_promote_proposal_with_default_proposal_dir(tmp_path: Path, capsys) -> None:
    """Default proposal dir is --path/proposals, creates the expected path."""
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-default-proposals-dir", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="default_proposal_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-default-proposals-dir",
        "--path", str(tmp_path),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "cli-default-proposals-dir" in captured.out


def test_cli_promote_proposal_non_existent_proposal_dir_returns_error(tmp_path: Path, capsys) -> None:
    """A non-existent proposal directory should cause an error exit."""
    from rutter.cli import main

    exit_code = main([
        "promote-proposal",
        "some-bundle",
        "--path", str(tmp_path),
        "--proposal-dir", str(tmp_path / "does-not-exist"),
    ])
    assert exit_code == 1


def test_cli_promote_proposal_with_registry_and_portolan_family(tmp_path: Path, capsys) -> None:
    """Promotion plan for portolan-integration family resolves correctly."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-portolan-promote", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="portolan_integration_new_capability", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-portolan-promote",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Should reference portolan-integration in the path
    assert "portolan-integration" in captured.out
    assert "portolan_integration_new_capability" in captured.out
    assert "create_skill_yaml" in captured.out or "update_manifest" in captured.out


def test_cli_promote_proposal_registry_is_read_only(tmp_path: Path, capsys) -> None:
    """Ensure the live registry is not written to during promotion."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal
    from rutter.registry import validate_registry

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"

    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-readonly-check", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="readonly_check_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-readonly-check",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0

    captured = capsys.readouterr()
    # Confirm the output explicitly says no automatic changes
    assert "No automatic changes" in captured.out

    # Registry unchanged
    errors = validate_registry(PROJECT_ROOT / "registry")
    assert errors == []


def test_cli_promote_proposal_with_registry_and_version_in_output(tmp_path: Path, capsys) -> None:
    """When using the real registry, the output contains a concrete version string."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-version-check", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="version_check_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-version-check",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    # The target_version should be "v0.1" for portolan-integration
    assert "v0.1" in captured.out


def test_cli_promote_proposal_with_registry_and_game_migration_version(tmp_path: Path, capsys) -> None:
    """When using the real registry for game-migration, the output shows v0.2."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-game-mig-version", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_migration_new_verification", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-game-mig-version",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "v0.2" in captured.out


def test_cli_promote_proposal_update_existing_skill_with_registry_path(tmp_path: Path, capsys) -> None:
    """update_existing_skill plan includes the correct registry path."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-update-path", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-update-path",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "registry/game-migration/v0.2/game_migration_verify.yaml" in captured.out


def test_cli_promote_proposal_update_existing_skill_with_registry_path_portolan(tmp_path: Path, capsys) -> None:
    """update_existing_skill for portolan shows the correct registry path."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-update-path-portolan", status="accepted",
        target_family="portolan-integration", action="update_existing_skill",
        target_skill_id="portolan_integration_hermes_bootstrap", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-update-path-portolan",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "registry/portolan-integration/v0.1/portolan_integration_hermes_bootstrap.yaml" in captured.out


def test_cli_promote_proposal_create_skill_with_registry_path(tmp_path: Path, capsys) -> None:
    """create_new_skill plan includes the correct registry path for the new file."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-path", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_migration_awesome_feature", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-path",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "game_migration_awesome_feature.yaml" in captured.out
    # Manifest path should also be in the output
    assert "manifest.yaml" in captured.out


def test_cli_promote_proposal_create_skill_with_registry_path_portolan(tmp_path: Path, capsys) -> None:
    """create_new_skill for portolan shows the correct registry path."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-path-portolan", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="portolan_integration_awesome_feature", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-path-portolan",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "portolan_integration_awesome_feature.yaml" in captured.out


def test_cli_promote_proposal_create_and_update_operations_mutually_exclusive(tmp_path: Path, capsys) -> None:
    """create_new_skill should only generate create operations, not update operations."""
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-only", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="create_only_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-only",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)
    ops = parsed["promotion_plan"]["registry_operations"]
    types = {op["type"] for op in ops}
    assert "create_skill_yaml" in types
    assert "update_manifest" in types
    assert "update_skill_yaml" not in types


def test_cli_promote_proposal_update_only_has_update_ops(tmp_path: Path, capsys) -> None:
    """update_existing_skill should only generate update operations, not create operations."""
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-update-only", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-update-only",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)
    ops = parsed["promotion_plan"]["registry_operations"]
    types = {op["type"] for op in ops}
    assert "update_skill_yaml" in types
    assert "create_skill_yaml" not in types
    assert "update_manifest" not in types


def test_cli_promote_proposal_update_shows_correct_registry_path(tmp_path: Path, capsys) -> None:
    """update_existing_skill shows correct registry path relative to repo root."""
    from pathlib import Path
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-update-reg-path", status="accepted",
        target_family="game-migration", action="update_existing_skill",
        target_skill_id="game_migration_verify", risk_level="medium",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-update-reg-path",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)
    ops = parsed["promotion_plan"]["registry_operations"]
    op_paths = [op["path"] for op in ops]
    assert any("game_migration_verify.yaml" in p for p in op_paths)


def test_cli_promote_proposal_create_shows_correct_registry_manifest_path(tmp_path: Path, capsys) -> None:
    """create_new_skill shows manifest.yaml path for manifest update."""
    from pathlib import Path
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-manifest-path", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="manifest_path_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-manifest-path",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)
    ops = parsed["promotion_plan"]["registry_operations"]
    op_paths = [op["path"] for op in ops]
    assert any("manifest.yaml" in p for p in op_paths)
    assert any("manifest_path_skill.yaml" in p for p in op_paths)


def test_cli_promote_proposal_create_shows_correct_registry_manifest_path_portolan(tmp_path: Path, capsys) -> None:
    """create_new_skill for portolan shows manifest.yaml path for manifest update."""
    from pathlib import Path
    import yaml
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-manifest-path-portolan", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="portolan_new_manifest_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-manifest-path-portolan",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    parsed = yaml.safe_load(captured.out)
    ops = parsed["promotion_plan"]["registry_operations"]
    op_paths = [op["path"] for op in ops]
    assert any("manifest.yaml" in p for p in op_paths)
    assert any("portolan_new_manifest_skill.yaml" in p for p in op_paths)


def test_cli_promote_proposal_create_shows_correct_registry_manifest_path_portolan_path(tmp_path: Path, capsys) -> None:
    """create_new_skill for portolan has the full registry path in the output."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-manifest-path-portolan-2", status="accepted",
        target_family="portolan-integration", action="create_new_skill",
        new_skill_id="portolan_manifest_skill_2", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-manifest-path-portolan-2",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "portolan-integration/v0.1" in captured.out
    assert "portolan_manifest_skill_2.yaml" in captured.out


def test_cli_promote_proposal_create_shows_correct_registry_manifest_path_game_migration(tmp_path: Path, capsys) -> None:
    """create_new_skill for game-migration has the full registry path in the output."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-manifest-path-game", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_new_manifest_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-manifest-path-game",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "game-migration/v0.2" in captured.out
    assert "game_new_manifest_skill.yaml" in captured.out


def test_cli_promote_proposal_create_shows_correct_registry_manifest_path_game_v0_2(tmp_path: Path, capsys) -> None:
    """create_new_skill for game-migration shows game-migration/v0.2 path."""
    from pathlib import Path
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import submit_proposal

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-create-manifest-path-game-v2", status="accepted",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="game_v2_manifest_skill", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "promote-proposal",
        "cli-create-manifest-path-game-v2",
        "--path", str(PROJECT_ROOT),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Should reference the correct path
    assert "game-migration/v0.2" in captured.out


def test_cli_review_proposal_updates_status(tmp_path: Path, capsys) -> None:
    from rutter.cli import main
    from rutter.models import SkillProposalBundle
    from rutter.proposals import get_proposal, submit_proposal

    proposal_dir = tmp_path / "proposals"
    submit_proposal(SkillProposalBundle(
        schema_version="1", bundle_id="cli-review-001", status="proposed",
        target_family="game-migration", action="create_new_skill",
        new_skill_id="test", risk_level="low",
        created_at="2026-05-02T00:00:00Z",
    ), proposal_dir)

    exit_code = main([
        "review-proposal",
        "cli-review-001",
        "--status", "accepted",
        "--path", str(tmp_path),
        "--proposal-dir", str(proposal_dir),
    ])
    assert exit_code == 0

    bundle = get_proposal(proposal_dir, "cli-review-001")
    assert bundle is not None
    assert bundle.status == "accepted"

