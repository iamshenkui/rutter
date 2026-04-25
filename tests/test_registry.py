from __future__ import annotations

from pathlib import Path

from rutter.cli import main
from rutter.registry import (
    build_index,
    get_skill,
    get_skill_dependencies,
    get_skill_family,
    list_skill_families,
    load_registry,
    search_skills,
    validate_registry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = PROJECT_ROOT / "registry"


def test_validate_registry_passes_for_repo_registry() -> None:
    assert validate_registry(REGISTRY_ROOT) == []


def test_build_index_contains_game_migration_family() -> None:
    index_payload = build_index(load_registry(REGISTRY_ROOT))

    assert index_payload["version"] == 1
    assert index_payload["families"][0]["family"] == "game-migration"
    assert index_payload["families"][0]["skill_ids"] == [
        "game_migration_blocker",
        "game_migration_core",
        "game_migration_migrate",
        "game_migration_plan",
        "game_migration_verify",
    ]


def test_search_skills_matches_parity_content() -> None:
    results = search_skills(REGISTRY_ROOT, "parity")

    result_ids = {item["skill_id"] for item in results}
    assert "game_migration_core" in result_ids
    assert "game_migration_verify" in result_ids


def test_list_skill_families_returns_index_summaries() -> None:
    families = list_skill_families(REGISTRY_ROOT)

    assert families == [
        {
            "family": "game-migration",
            "version": "v0.1",
            "name": "Game Migration",
            "description": "Migrate an existing game onto a Rust headless framework and engine architecture while preserving semantic parity.",
            "tags": ["migration", "rust", "game-dev", "orchestration"],
            "keywords": [
                "semantic parity",
                "framework migration",
                "headless verification",
                "deterministic traces",
            ],
            "aliases": ["game migration", "game-migration"],
            "skill_ids": [
                "game_migration_blocker",
                "game_migration_core",
                "game_migration_migrate",
                "game_migration_plan",
                "game_migration_verify",
            ],
            "manifest": "game-migration/v0.1/manifest.yaml",
        }
    ]


def test_get_skill_family_returns_manifest_and_skills() -> None:
    payload = get_skill_family(REGISTRY_ROOT, "game-migration")

    assert payload["manifest"]["family"] == "game-migration"
    assert payload["manifest"]["version"] == "v0.1"
    assert [skill["id"] for skill in payload["skills"]] == [
        "game_migration_blocker",
        "game_migration_core",
        "game_migration_migrate",
        "game_migration_plan",
        "game_migration_verify",
    ]


def test_get_skill_returns_one_atomic_skill_payload() -> None:
    payload = get_skill(REGISTRY_ROOT, "game_migration_verify")

    assert payload["family"] == "game-migration"
    assert payload["version"] == "v0.1"
    assert payload["skill"]["id"] == "game_migration_verify"
    assert payload["skill"]["category"] == "verification"


def test_get_skill_dependencies_resolves_direct_dependencies() -> None:
    payload = get_skill_dependencies(REGISTRY_ROOT, "game_migration_verify")

    assert payload == {
        "skill_id": "game_migration_verify",
        "dependencies": [
            {
                "skill_id": "game_migration_core",
                "family": "game-migration",
                "version": "v0.1",
                "name": "Game Migration Core",
                "category": "core_rules",
            },
            {
                "skill_id": "game_migration_migrate",
                "family": "game-migration",
                "version": "v0.1",
                "name": "Game Migration Migrate",
                "category": "execution",
            },
        ],
    }


def test_cli_validate_returns_zero(capsys) -> None:
    exit_code = main(["validate", "--path", str(PROJECT_ROOT)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Registry validation passed" in captured.out


def test_cli_build_index_writes_output(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "index.yaml"

    exit_code = main(
        ["build-index", "--path", str(PROJECT_ROOT), "--output", str(output_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(output_path) in captured.out
    assert "game-migration" in output_path.read_text(encoding="utf-8")


def test_cli_list_families_outputs_yaml(capsys) -> None:
    exit_code = main(["list-families", "--path", str(PROJECT_ROOT)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "families:" in captured.out
    assert "game-migration" in captured.out


def test_cli_get_skill_outputs_yaml(capsys) -> None:
    exit_code = main(["get-skill", "game_migration_verify", "--path", str(PROJECT_ROOT)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "skill:" in captured.out
    assert "game_migration_verify" in captured.out