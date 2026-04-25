from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .models import AtomicSkill, SkillFamily, SkillFileRef, SkillManifest


class RegistryValidationError(Exception):
    """Raised when the registry content is malformed."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("Registry validation failed")
        self.errors = errors


class RegistryLookupError(Exception):
    """Raised when a requested registry object cannot be found."""


def resolve_registry_root(path: str | Path) -> Path:
    candidate = Path(path).resolve()
    if candidate.name == "registry" and candidate.is_dir():
        return candidate
    registry_dir = candidate / "registry"
    if registry_dir.is_dir():
        return registry_dir
    return candidate


def scan_registry(registry_root: str | Path) -> tuple[list[SkillFamily], list[str]]:
    root = resolve_registry_root(registry_root)
    errors: list[str] = []
    families: list[SkillFamily] = []
    global_skill_ids: dict[str, Path] = {}

    if not root.exists():
        return [], [f"Registry root does not exist: {root}"]
    if not root.is_dir():
        return [], [f"Registry root is not a directory: {root}"]

    family_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    for family_dir in family_dirs:
        version_dirs = sorted(path for path in family_dir.iterdir() if path.is_dir())
        for version_dir in version_dirs:
            manifest_path = version_dir / "manifest.yaml"
            manifest = _load_manifest(manifest_path, errors)
            if manifest is None:
                continue

            skills: dict[str, AtomicSkill] = {}
            referenced_files: set[str] = set()
            for skill_ref in manifest.skills:
                referenced_files.add(skill_ref.file)
                skill = _load_atomic_skill(version_dir / skill_ref.file, errors)
                if skill is None:
                    continue
                if skill.id != skill_ref.id:
                    errors.append(
                        f"Skill id mismatch in {version_dir / skill_ref.file}: "
                        f"manifest declares {skill_ref.id}, file contains {skill.id}"
                    )
                if skill.id in skills:
                    errors.append(f"Duplicate skill id {skill.id} in manifest {manifest_path}")
                    continue
                if skill.id in global_skill_ids:
                    errors.append(
                        f"Duplicate global skill id {skill.id}: "
                        f"{global_skill_ids[skill.id]} and {version_dir / skill_ref.file}"
                    )
                else:
                    global_skill_ids[skill.id] = version_dir / skill_ref.file
                skills[skill.id] = skill

            extra_yaml_files = sorted(
                path.name
                for path in version_dir.glob("*.yaml")
                if path.name not in {"manifest.yaml"} and path.name not in referenced_files
            )
            for extra_file in extra_yaml_files:
                errors.append(
                    f"Unreferenced skill file in {version_dir}: {extra_file} is not listed in manifest.yaml"
                )

            families.append(SkillFamily(manifest=manifest, directory=version_dir, skills=skills))

    dependency_graph = {
        skill.id: list(skill.dependencies)
        for family in families
        for skill in family.skills.values()
    }
    errors.extend(_validate_dependencies(dependency_graph))
    return families, errors


def load_registry(registry_root: str | Path) -> list[SkillFamily]:
    families, errors = scan_registry(registry_root)
    if errors:
        raise RegistryValidationError(errors)
    return families


def validate_registry(registry_root: str | Path) -> list[str]:
    _, errors = scan_registry(registry_root)
    return errors


def build_index(families: list[SkillFamily]) -> dict[str, Any]:
    return {
        "version": 1,
        "families": [
            {
                "family": family.manifest.family,
                "version": family.manifest.version,
                "name": family.manifest.name,
                "description": family.manifest.description,
                "tags": list(family.manifest.tags),
                "keywords": list(family.manifest.keywords),
                "aliases": list(family.manifest.aliases),
                "skill_ids": sorted(family.skills.keys()),
                "manifest": str(
                    Path(family.manifest.family) / family.manifest.version / "manifest.yaml"
                ),
            }
            for family in sorted(
                families, key=lambda item: (item.manifest.family, item.manifest.version)
            )
        ],
    }


def list_skill_families(registry_root: str | Path) -> list[dict[str, Any]]:
    families = load_registry(registry_root)
    return build_index(families)["families"]


def write_index(registry_root: str | Path, output_path: str | Path | None = None) -> Path:
    families = load_registry(registry_root)
    index_payload = build_index(families)
    root = resolve_registry_root(registry_root)
    destination = Path(output_path).resolve() if output_path else root / "index.yaml"
    destination.write_text(yaml.safe_dump(index_payload, sort_keys=False), encoding="utf-8")
    return destination


def search_skills(registry_root: str | Path, query: str) -> list[dict[str, Any]]:
    families = load_registry(registry_root)
    needle = query.strip().lower()
    if not needle:
        return []

    results: list[dict[str, Any]] = []
    for family in sorted(families, key=lambda item: (item.manifest.family, item.manifest.version)):
        family_terms = [
            family.manifest.family,
            family.manifest.name,
            family.manifest.description,
            *family.manifest.tags,
            *family.manifest.keywords,
            *family.manifest.aliases,
        ]
        for skill in sorted(family.skills.values(), key=lambda item: item.id):
            skill_terms = [
                skill.id,
                skill.name,
                skill.description,
                skill.category,
                *skill.incremental_rules,
                *skill.dependencies,
                *family_terms,
            ]
            haystack = "\n".join(skill_terms).lower()
            if needle in haystack:
                results.append(
                    {
                        "family": family.manifest.family,
                        "version": family.manifest.version,
                        "skill_id": skill.id,
                        "skill_name": skill.name,
                        "category": skill.category,
                        "description": skill.description,
                        "dependencies": list(skill.dependencies),
                    }
                )
    return results


def get_skill_family(
    registry_root: str | Path,
    family_name: str,
    version: str | None = None,
) -> dict[str, Any]:
    families = load_registry(registry_root)
    matches = [family for family in families if family.manifest.family == family_name]
    if not matches:
        raise RegistryLookupError(f"Skill family not found: {family_name}")

    if version is not None:
        for family in matches:
            if family.manifest.version == version:
                return dump_skill_family(family)
        raise RegistryLookupError(
            f"Skill family version not found: {family_name}@{version}"
        )

    selected = sorted(matches, key=lambda item: item.manifest.version)[-1]
    return dump_skill_family(selected)


def get_skill(registry_root: str | Path, skill_id: str) -> dict[str, Any]:
    families = load_registry(registry_root)
    for family in sorted(families, key=lambda item: (item.manifest.family, item.manifest.version)):
        skill = family.skills.get(skill_id)
        if skill is not None:
            return {
                "family": family.manifest.family,
                "version": family.manifest.version,
                "manifest": asdict(family.manifest),
                "skill": asdict(skill),
            }
    raise RegistryLookupError(f"Skill not found: {skill_id}")


def get_skill_dependencies(registry_root: str | Path, skill_id: str) -> dict[str, Any]:
    skill_payload = get_skill(registry_root, skill_id)
    dependencies: list[dict[str, Any]] = []
    for dependency_id in skill_payload["skill"]["dependencies"]:
        dependency_payload = get_skill(registry_root, dependency_id)
        dependencies.append(
            {
                "skill_id": dependency_id,
                "family": dependency_payload["family"],
                "version": dependency_payload["version"],
                "name": dependency_payload["skill"]["name"],
                "category": dependency_payload["skill"]["category"],
            }
        )
    return {
        "skill_id": skill_id,
        "dependencies": dependencies,
    }


def dump_skill_family(family: SkillFamily) -> dict[str, Any]:
    return {
        "manifest": asdict(family.manifest),
        "skills": [asdict(skill) for skill in sorted(family.skills.values(), key=lambda item: item.id)],
    }


def _load_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"Missing YAML file: {path}")
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"YAML root must be a mapping in {path}")
        return None
    return payload


def _load_manifest(path: Path, errors: list[str]) -> SkillManifest | None:
    payload = _load_yaml(path, errors)
    if payload is None:
        return None

    family = _require_string(payload, "family", path, errors)
    version = _require_string(payload, "version", path, errors)
    name = _require_string(payload, "name", path, errors)
    description = _require_string(payload, "description", path, errors)
    tags = _require_string_list(payload, "tags", path, errors)
    keywords = _require_string_list(payload, "keywords", path, errors)
    aliases = _require_string_list(payload, "aliases", path, errors)
    skills_payload = payload.get("skills")
    skill_refs: list[SkillFileRef] = []
    if not isinstance(skills_payload, list) or not skills_payload:
        errors.append(f"Field 'skills' must be a non-empty list in {path}")
    else:
        for index, item in enumerate(skills_payload):
            if not isinstance(item, dict):
                errors.append(f"Manifest skill entry at index {index} must be a mapping in {path}")
                continue
            skill_id = item.get("id")
            file_name = item.get("file")
            if not isinstance(skill_id, str) or not skill_id.strip():
                errors.append(f"Manifest skill entry at index {index} is missing a valid id in {path}")
                continue
            if not isinstance(file_name, str) or not file_name.strip():
                errors.append(f"Manifest skill entry at index {index} is missing a valid file in {path}")
                continue
            skill_refs.append(SkillFileRef(id=skill_id.strip(), file=file_name.strip()))

    if any(
        value is None
        for value in (family, version, name, description, tags, keywords, aliases)
    ):
        return None
    if not skill_refs:
        return None

    return SkillManifest(
        family=family,
        version=version,
        name=name,
        description=description,
        tags=tags,
        keywords=keywords,
        aliases=aliases,
        skills=skill_refs,
    )


def _load_atomic_skill(path: Path, errors: list[str]) -> AtomicSkill | None:
    payload = _load_yaml(path, errors)
    if payload is None:
        return None

    skill_id = _require_string(payload, "id", path, errors)
    name = _require_string(payload, "name", path, errors)
    description = _require_string(payload, "description", path, errors)
    category = _require_string(payload, "category", path, errors)
    incremental_rules = _require_string_list(payload, "incremental_rules", path, errors)
    dependencies = _require_string_list(payload, "dependencies", path, errors)

    if any(
        value is None
        for value in (skill_id, name, description, category, incremental_rules, dependencies)
    ):
        return None

    return AtomicSkill(
        id=skill_id,
        name=name,
        description=description,
        category=category,
        incremental_rules=incremental_rules,
        dependencies=dependencies,
    )


def _require_string(
    payload: dict[str, Any],
    field_name: str,
    path: Path,
    errors: list[str],
) -> str | None:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"Field '{field_name}' must be a non-empty string in {path}")
        return None
    return value.strip()


def _require_string_list(
    payload: dict[str, Any],
    field_name: str,
    path: Path,
    errors: list[str],
) -> list[str] | None:
    value = payload.get(field_name)
    if not isinstance(value, list):
        errors.append(f"Field '{field_name}' must be a list in {path}")
        return None
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"Field '{field_name}' contains an invalid string at index {index} in {path}"
            )
            continue
        normalized.append(item.strip())
    return normalized


def _validate_dependencies(graph: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    for skill_id, dependencies in sorted(graph.items()):
        for dependency in dependencies:
            if dependency not in graph:
                errors.append(f"Skill {skill_id} depends on missing skill {dependency}")
    errors.extend(_detect_cycles(graph))
    return errors


def _detect_cycles(graph: dict[str, list[str]]) -> list[str]:
    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []
    cycles: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        visited.add(node)
        active.add(node)
        stack.append(node)

        for dependency in graph.get(node, []):
            if dependency not in graph:
                continue
            if dependency not in visited:
                visit(dependency)
            elif dependency in active:
                start_index = stack.index(dependency)
                cycle = tuple(stack[start_index:] + [dependency])
                cycles.add(cycle)

        stack.pop()
        active.remove(node)

    for node in sorted(graph):
        if node not in visited:
            visit(node)

    return [f"Circular dependency detected: {' -> '.join(cycle)}" for cycle in sorted(cycles)]