from __future__ import annotations

from pathlib import Path
from typing import Any

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