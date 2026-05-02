from __future__ import annotations

from pathlib import Path
from typing import Any

from .proposals import (
    dump_proposal_validation_result,
    get_proposal,
    list_proposals,
    submit_proposal,
    validate_proposals,
)
from .registry import (
    get_skill,
    get_skill_dependencies,
    get_skill_family,
    list_skill_families,
    search_skills,
    validate_registry,
)


def list_skill_families_tool(registry_root: str | Path) -> list[dict[str, Any]]:
    return list_skill_families(registry_root)


def search_skills_tool(registry_root: str | Path, query: str) -> list[dict[str, Any]]:
    return search_skills(registry_root, query)


def get_skill_family_tool(
    registry_root: str | Path,
    family_name: str,
    version: str | None = None,
) -> dict[str, Any]:
    return get_skill_family(registry_root, family_name, version)


def get_skill_tool(registry_root: str | Path, skill_id: str) -> dict[str, Any]:
    return get_skill(registry_root, skill_id)


def get_skill_dependencies_tool(
    registry_root: str | Path,
    skill_id: str,
) -> dict[str, Any]:
    return get_skill_dependencies(registry_root, skill_id)


def validate_registry_tool(registry_root: str | Path) -> list[str]:
    return validate_registry(registry_root)


# ── Proposal query tools ────────────────────────────────────────────────


def list_proposals_tool(
    proposal_dir: str | Path,
    *,
    status_filter: str | None = None,
    family_filter: str | None = None,
) -> list[dict[str, Any]]:
    return list_proposals(proposal_dir, status_filter=status_filter, family_filter=family_filter)


def get_proposal_tool(
    proposal_dir: str | Path,
    bundle_id: str,
) -> dict[str, Any] | None:
    bundle = get_proposal(proposal_dir, bundle_id)
    if bundle is None:
        return None
    from dataclasses import asdict
    return asdict(bundle)


def validate_proposals_tool(
    proposal_dir: str | Path,
    registry_root: str | Path | None = None,
) -> dict[str, Any]:
    results = validate_proposals(proposal_dir, registry_root=registry_root)
    return dump_proposal_validation_result(results)