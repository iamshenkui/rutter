from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models import (
    VALID_PROPOSAL_ACTIONS,
    VALID_PROPOSAL_SCHEMA_VERSIONS,
    VALID_PROPOSAL_STATUSES,
    VALID_RISK_LEVELS,
    SkillProposalBundle,
)
from .registry import load_registry, resolve_registry_root


class ProposalValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Proposal validation failed")
        self.errors = errors


def _get_all_registry_families(registry_root: str | Path) -> set[str]:
    try:
        families = load_registry(registry_root)
    except Exception:
        return set()
    return {f.manifest.family for f in families}


def _get_all_registry_skill_ids(registry_root: str | Path) -> set[str]:
    try:
        families = load_registry(registry_root)
    except Exception:
        return set()
    return {sid for f in families for sid in f.skills}


def _parse_proposal_yaml(
    path: Path, errors: list[str]
) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"Proposal file not found: {path}")
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in {path}: {exc}")
        return None
    if not isinstance(raw, dict):
        errors.append(f"Proposal file must contain a YAML mapping: {path}")
        return None
    return raw


def _require_bool(
    raw: dict[str, Any], field: str, path: Path, errors: list[str]
) -> bool | None:
    val = raw.get(field)
    if not isinstance(val, bool):
        errors.append(f"Field '{field}' must be a boolean in {path}")
        return None
    return val


def _opt_string(raw: dict[str, Any], field: str) -> str | None:
    val = raw.get(field)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _require_string(
    raw: dict[str, Any], field: str, path: Path, errors: list[str]
) -> str | None:
    val = raw.get(field)
    if not isinstance(val, str) or not val.strip():
        errors.append(f"Field '{field}' must be a non-empty string in {path}")
        return None
    return val.strip()


def _require_string_list(
    raw: dict[str, Any], field: str, path: Path, errors: list[str]
) -> list[str] | None:
    val = raw.get(field)
    if val is None:
        return []
    if not isinstance(val, list):
        errors.append(f"Field '{field}' must be a list in {path}")
        return None
    result: list[str] = []
    for i, item in enumerate(val):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"Field '{field}' contains an invalid string at index {i} in {path}"
            )
            continue
        result.append(item.strip())
    return result


def load_proposals(proposal_dir: str | Path) -> list[SkillProposalBundle]:
    """Load all proposals from a directory tree structured as proposals/<family>/<bundle_id>.yaml."""
    root = Path(proposal_dir).resolve()
    if not root.is_dir():
        raise ProposalValidationError([f"Proposal directory not found: {root}"])

    bundles: list[SkillProposalBundle] = []
    errors: list[str] = []

    # Sort for deterministic order
    for family_dir in sorted(root.iterdir()):
        if not family_dir.is_dir():
            continue
        for yaml_file in sorted(family_dir.glob("*.yaml")):
            bundle = _load_single_proposal(yaml_file, errors)
            if bundle is not None:
                bundles.append(bundle)

    if errors:
        raise ProposalValidationError(errors)
    return bundles


def load_proposal_files(proposal_dir: str | Path) -> list[SkillProposalBundle]:
    """Load all .yaml proposal files directly from a flat directory."""
    root = Path(proposal_dir).resolve()
    if not root.is_dir():
        raise ProposalValidationError([f"Proposal directory not found: {root}"])

    bundles: list[SkillProposalBundle] = []
    errors: list[str] = []

    for yaml_file in sorted(root.glob("*.yaml")):
        bundle = _load_single_proposal(yaml_file, errors)
        if bundle is not None:
            bundles.append(bundle)

    if errors:
        raise ProposalValidationError(errors)
    return bundles


def _load_single_proposal(
    path: Path, errors: list[str]
) -> SkillProposalBundle | None:
    raw = _parse_proposal_yaml(path, errors)
    if raw is None:
        return None

    schema_version = _require_string(raw, "schema_version", path, errors)
    bundle_id = _require_string(raw, "bundle_id", path, errors)
    status = _require_string(raw, "status", path, errors)
    target_family = _require_string(raw, "target_family", path, errors)
    action = _require_string(raw, "action", path, errors)
    created_at = _opt_string(raw, "created_at")
    target_skill_id = _opt_string(raw, "target_skill_id")
    new_skill_id = _opt_string(raw, "new_skill_id")
    risk_level = _opt_string(raw, "risk_level") or "medium"
    supporting_issues = _require_string_list(raw, "supporting_issues", path, errors) or []
    evidence_refs = _require_string_list(raw, "evidence_refs", path, errors) or []

    if any(v is None for v in (schema_version, bundle_id, status, target_family, action)):
        return None

    return SkillProposalBundle(
        schema_version=schema_version,
        bundle_id=bundle_id,
        status=status,
        target_family=target_family,
        action=action,
        supporting_issues=tuple(supporting_issues),
        evidence_refs=tuple(evidence_refs),
        risk_level=risk_level,
        created_at=created_at or bundle_id,
        target_skill_id=target_skill_id,
        new_skill_id=new_skill_id,
    )


def _fmt_location(file: Path) -> str:
    return str(file.resolve())


def validate_proposal(
    proposal: SkillProposalBundle,
    source: Path | None = None,
    registry_root: str | Path | None = None,
) -> list[str]:
    """Validate a single proposal bundle against the SkillProposalBundle@v1 contract.

    Returns a list of error messages (empty means valid).
    Does NOT modify any files.
    """
    errors: list[str] = []
    loc = f" in {_fmt_location(source)}" if source else ""

    # schema_version
    if proposal.schema_version not in VALID_PROPOSAL_SCHEMA_VERSIONS:
        errors.append(
            f"Invalid schema_version '{proposal.schema_version}'{loc}: "
            f"must be one of {sorted(VALID_PROPOSAL_SCHEMA_VERSIONS)}"
        )

    # bundle_id
    if not proposal.bundle_id:
        errors.append(f"Empty bundle_id{loc}")

    # status
    if proposal.status not in VALID_PROPOSAL_STATUSES:
        errors.append(
            f"Invalid status '{proposal.status}'{loc}: "
            f"must be one of {sorted(VALID_PROPOSAL_STATUSES)}"
        )

    # action
    if proposal.action not in VALID_PROPOSAL_ACTIONS:
        errors.append(
            f"Invalid action '{proposal.action}'{loc}: "
            f"must be one of {sorted(VALID_PROPOSAL_ACTIONS)}"
        )

    # risk_level
    if proposal.risk_level not in VALID_RISK_LEVELS:
        errors.append(
            f"Invalid risk_level '{proposal.risk_level}'{loc}: "
            f"must be one of {sorted(VALID_RISK_LEVELS)}"
        )

    # created_at should be an ISO datetime if present
    if proposal.created_at:
        try:
            datetime.fromisoformat(proposal.created_at)
        except (ValueError, TypeError):
            errors.append(f"Invalid created_at '{proposal.created_at}'{loc}: must be ISO 8601")

    # Validate against registry when a registry root is given
    if registry_root is not None:
        existing_families = _get_all_registry_families(registry_root)
        existing_skill_ids = _get_all_registry_skill_ids(registry_root)

        # target_family must exist
        if proposal.target_family not in existing_families:
            errors.append(
                f"Unknown target_family '{proposal.target_family}'{loc}: "
                f"not found in registry (known: {sorted(existing_families)})"
            )

        # action-specific checks
        if proposal.action == "update_existing_skill":
            if not proposal.target_skill_id:
                errors.append(
                    f"Action 'update_existing_skill' requires 'target_skill_id'{loc}"
                )
            elif proposal.target_skill_id not in existing_skill_ids:
                errors.append(
                    f"target_skill_id '{proposal.target_skill_id}'{loc} "
                    f"not found in registry"
                )
        elif proposal.action == "create_new_skill":
            if not proposal.new_skill_id:
                errors.append(
                    f"Action 'create_new_skill' requires non-empty 'new_skill_id'{loc}"
                )
            elif proposal.new_skill_id in existing_skill_ids:
                errors.append(
                    f"new_skill_id '{proposal.new_skill_id}'{loc} "
                    f"collides with existing registry skill"
                )

    return errors


def validate_proposals(
    proposal_root: str | Path,
    registry_root: str | Path | None = None,
) -> dict[str, list[str]]:
    """Validate all proposals under proposal_root against the registry.

    Returns a dict mapping file paths to lists of error messages.
    Empty lists mean that proposal is valid.
    Does NOT modify any files.
    """
    root = Path(proposal_root).resolve()
    if not root.is_dir():
        return {str(root): [f"Proposal directory not found: {root}"]}

    if registry_root is not None:
        registry_root = resolve_registry_root(registry_root)

    results: dict[str, list[str]] = {}

    for yaml_file in sorted(root.rglob("*.yaml")):
        parse_errors: list[str] = []
        bundle = _load_single_proposal(yaml_file, parse_errors)
        if bundle is None:
            results[str(yaml_file)] = parse_errors or ["Failed to parse proposal YAML"]
            continue
        errors = validate_proposal(bundle, source=yaml_file, registry_root=registry_root)
        results[str(yaml_file)] = errors

    # Also collect files that aren't valid proposals from load errors
    # (already captured as parse failures above)
    return results


def dump_proposal_validation_result(
    results: dict[str, list[str]],
) -> dict[str, Any]:
    total = len(results)
    valid_count = sum(1 for errs in results.values() if not errs)
    invalid_count = total - valid_count
    details = []
    for path in sorted(results):
        errors = results[path]
        details.append(
            {
                "file": path,
                "valid": len(errors) == 0,
                "errors": errors,
            }
        )
    return {
        "total": total,
        "valid": valid_count,
        "invalid": invalid_count,
        "details": details,
    }
