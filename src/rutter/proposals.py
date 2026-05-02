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
    EvidenceRef,
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


def _require_evidence_refs(
    raw: dict[str, Any], field: str, path: Path, errors: list[str]
) -> list[EvidenceRef] | None:
    val = raw.get(field)
    if val is None:
        return []
    if not isinstance(val, list):
        errors.append(f"Field '{field}' must be a list in {path}")
        return None
    result: list[EvidenceRef] = []
    for i, item in enumerate(val):
        if isinstance(item, str):
            result.append(EvidenceRef(path=item.strip()))
        elif isinstance(item, dict):
            ref_type = item.get("type", "")
            ref_path = item.get("path", "")
            ref_desc = item.get("description", "")
            if isinstance(ref_type, str) and isinstance(ref_path, str) and isinstance(ref_desc, str):
                result.append(EvidenceRef(type=ref_type, path=ref_path, description=ref_desc))
            else:
                errors.append(
                    f"Field '{field}' contains an invalid evidence ref at index {i} in {path}"
                )
        else:
            errors.append(
                f"Field '{field}' contains an invalid evidence ref at index {i} in {path}"
            )
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
    evidence_refs_raw = _require_evidence_refs(raw, "evidence_refs", path, errors)
    evidence_refs: list[EvidenceRef] = evidence_refs_raw or []

    if any(v is None for v in (schema_version, bundle_id, status, target_family, action)):
        return None

    assert schema_version is not None
    assert bundle_id is not None
    assert status is not None
    assert target_family is not None
    assert action is not None

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
        if proposal.action in ("update_existing_skill", "split_existing_skill", "deprecate_skill"):
            if not proposal.target_skill_id:
                errors.append(
                    f"Action '{proposal.action}' requires 'target_skill_id'{loc}"
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


# ── Proposal CRUD (Review Surface) ──────────────────────────────────────


def _evidence_ref_to_dict(ref: EvidenceRef) -> dict[str, str]:
    d: dict[str, str] = {}
    if ref.type:
        d["type"] = ref.type
    d["path"] = ref.path
    if ref.description:
        d["description"] = ref.description
    return d


def _proposal_to_dict(proposal: SkillProposalBundle) -> dict[str, Any]:
    """Serialize a SkillProposalBundle to a YAML-serializable dict, omitting None fields."""
    data: dict[str, Any] = {
        "schema_version": proposal.schema_version,
        "bundle_id": proposal.bundle_id,
        "status": proposal.status,
        "target_family": proposal.target_family,
        "action": proposal.action,
        "risk_level": proposal.risk_level,
        "supporting_issues": list(proposal.supporting_issues),
        "evidence_refs": [_evidence_ref_to_dict(e) for e in proposal.evidence_refs],
    }
    if proposal.created_at:
        data["created_at"] = proposal.created_at
    if proposal.target_skill_id is not None:
        data["target_skill_id"] = proposal.target_skill_id
    if proposal.new_skill_id is not None:
        data["new_skill_id"] = proposal.new_skill_id
    return data


def submit_proposal(
    proposal: SkillProposalBundle,
    proposal_dir: str | Path,
    registry_root: str | Path | None = None,
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Validate and write a proposal YAML file into the review surface.

    Args:
        proposal: The proposal bundle to submit.
        proposal_dir: Root directory for proposals.
        registry_root: Optional registry root for cross-reference validation.
        allow_overwrite: Allow overwriting an existing proposal file.

    Returns:
        Path to the written proposal file.

    Raises:
        ProposalValidationError: If validation fails.
        FileExistsError: If the proposal file already exists and allow_overwrite is False.
    """
    errors = validate_proposal(proposal, registry_root=registry_root)
    if errors:
        raise ProposalValidationError(errors)

    root = Path(proposal_dir).resolve()
    family_dir = root / proposal.target_family
    family_dir.mkdir(parents=True, exist_ok=True)

    proposal_path = family_dir / f"{proposal.bundle_id}.yaml"
    if proposal_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Proposal already exists at {proposal_path}. Use --allow-overwrite to replace."
        )

    data = _proposal_to_dict(proposal)
    proposal_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return proposal_path


def list_proposals(
    proposal_dir: str | Path,
    *,
    status_filter: str | None = None,
    family_filter: str | None = None,
) -> list[dict[str, Any]]:
    """List all proposals in the review surface as metadata dicts.

    Supports optional filtering by status and/or target_family.
    """
    try:
        bundles = load_proposals(proposal_dir)
    except ProposalValidationError:
        # Return what we can — partial results from individual files
        return _list_proposals_fallback(proposal_dir, status_filter, family_filter)

    results: list[dict[str, Any]] = []
    for bundle in bundles:
        if status_filter and bundle.status != status_filter:
            continue
        if family_filter and bundle.target_family != family_filter:
            continue
        results.append({
            "bundle_id": bundle.bundle_id,
            "status": bundle.status,
            "action": bundle.action,
            "target_family": bundle.target_family,
            "risk_level": bundle.risk_level,
            "target_skill_id": bundle.target_skill_id,
            "new_skill_id": bundle.new_skill_id,
            "created_at": bundle.created_at,
        })

    results.sort(key=lambda r: (r["target_family"], r["bundle_id"]))
    return results


def _list_proposals_fallback(
    proposal_dir: str | Path,
    status_filter: str | None,
    family_filter: str | None,
) -> list[dict[str, Any]]:
    """Fallback listing when load_proposals raises — read raw YAML per file."""
    root = Path(proposal_dir).resolve()
    if not root.is_dir():
        return []

    results: list[dict[str, Any]] = []
    for yaml_file in sorted(root.rglob("*.yaml")):
        try:
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            bundle_id = raw.get("bundle_id", yaml_file.stem)
            status = raw.get("status", "unknown")
            target_family = raw.get("target_family", "unknown")
            if status_filter and status != status_filter:
                continue
            if family_filter and target_family != family_filter:
                continue
            results.append({
                "bundle_id": bundle_id,
                "status": status,
                "action": raw.get("action", "unknown"),
                "target_family": target_family,
                "risk_level": raw.get("risk_level", "medium"),
                "target_skill_id": raw.get("target_skill_id"),
                "new_skill_id": raw.get("new_skill_id"),
                "created_at": raw.get("created_at", ""),
            })
        except yaml.YAMLError:
            continue

    results.sort(key=lambda r: (r["target_family"], r["bundle_id"]))
    return results


def get_proposal(
    proposal_dir: str | Path,
    bundle_id: str,
) -> SkillProposalBundle | None:
    """Find a proposal by bundle_id across all family subdirectories."""
    root = Path(proposal_dir).resolve()
    if not root.is_dir():
        return None

    for yaml_file in sorted(root.rglob("*.yaml")):
        errors: list[str] = []
        bundle = _load_single_proposal(yaml_file, errors)
        if bundle is not None and bundle.bundle_id == bundle_id:
            return bundle
    return None


def promote_proposal(
    proposal_dir: str | Path,
    bundle_id: str,
    registry_root: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a human-reviewable promotion plan for an accepted proposal.

    In v0.1 this does NOT write to the live registry. Instead, it outputs
    structured instructions that a human can review and apply manually.

    Args:
        proposal_dir: Root directory for proposals.
        bundle_id: The bundle_id of the proposal to promote.
        registry_root: Required registry root for resolving target paths.

    Returns:
        A dict describing the promotion plan (proposal metadata + operations).

    Raises:
        ProposalValidationError: If the proposal is not found, not accepted,
            or registry validation fails.
    """
    bundle = get_proposal(proposal_dir, bundle_id)
    if bundle is None:
        raise ProposalValidationError([f"Proposal not found: bundle_id='{bundle_id}'"])

    if bundle.status != "accepted":
        raise ProposalValidationError(
            [f"Proposal '{bundle_id}' has status '{bundle.status}', expected 'accepted'"]
        )

    # Resolve the target family version from the live registry (read-only).
    # v0.1 is lenient: if the registry cannot be loaded, we still generate
    # a promotion plan with an unknown-version placeholder.
    target_version: str | None = None
    if registry_root is not None:
        from .registry import load_registry, resolve_registry_root

        registry_root = resolve_registry_root(registry_root)
        try:
            families = load_registry(registry_root)
        except Exception:
            families = []

        for family in families:
            if family.manifest.family == bundle.target_family:
                candidates = [
                    f for f in families if f.manifest.family == bundle.target_family
                ]
                target_version = sorted(
                    candidates, key=lambda f: f.manifest.version
                )[-1].manifest.version
                break

    if target_version is None:
        target_version = "<unknown-version>"

    operations: list[dict[str, Any]] = []
    registry_path = f"registry/{bundle.target_family}/{target_version}"

    if bundle.action == "create_new_skill":
        new_skill_id = bundle.new_skill_id or "<new_skill_id>"
        operations.append({
            "type": "create_skill_yaml",
            "path": f"{registry_path}/{new_skill_id}.yaml",
            "description": (
                f"Create a new atomic skill YAML file for '{new_skill_id}' "
                f"with id, name, description, category, incremental_rules, "
                f"and dependencies fields."
            ),
        })
        operations.append({
            "type": "update_manifest",
            "path": f"{registry_path}/manifest.yaml",
            "description": (
                f"Add a manifest entry for '{new_skill_id}' referencing "
                f"'{new_skill_id}.yaml' so the registry indexes the new skill."
            ),
        })
    elif bundle.action == "update_existing_skill":
        target_skill_id = bundle.target_skill_id or "<target_skill_id>"
        operations.append({
            "type": "update_skill_yaml",
            "path": f"{registry_path}/{target_skill_id}.yaml",
            "description": (
                f"Update the existing skill YAML for '{target_skill_id}' "
                f"with the proposed changes."
            ),
        })
    elif bundle.action == "split_existing_skill":
        target_skill_id = bundle.target_skill_id or "<target_skill_id>"
        operations.append({
            "type": "split_skill",
            "path": f"{registry_path}/{target_skill_id}.yaml",
            "description": (
                f"Split the existing skill '{target_skill_id}' into "
                f"narrower skills and update the manifest accordingly."
            ),
        })
        operations.append({
            "type": "update_manifest",
            "path": f"{registry_path}/manifest.yaml",
            "description": f"Update manifest after splitting '{target_skill_id}'.",
        })
    elif bundle.action == "deprecate_skill":
        target_skill_id = bundle.target_skill_id or "<target_skill_id>"
        operations.append({
            "type": "deprecate_skill",
            "path": f"{registry_path}/{target_skill_id}.yaml",
            "description": (
                f"Mark skill '{target_skill_id}' as deprecated in its YAML "
                f"and update the manifest."
            ),
        })
        operations.append({
            "type": "update_manifest",
            "path": f"{registry_path}/manifest.yaml",
            "description": f"Update manifest after deprecating '{target_skill_id}'.",
        })
    elif bundle.action == "metadata_only":
        operations.append({
            "type": "update_metadata",
            "path": f"{registry_path}/manifest.yaml",
            "description": (
                f"Update registry metadata for family '{bundle.target_family}' "
                f"without changing any skill definitions."
            ),
        })
    elif bundle.action == "no_action":
        operations.append({
            "type": "noop",
            "path": "",
            "description": "No registry changes required. Proposal is informational only.",
        })

    # ── State transition: accepted -> promoted ────────────────────────
    # Update the proposal file on disk to reflect the new lifecycle state.
    root = Path(proposal_dir).resolve()
    existing_path: Path | None = None
    for yaml_file in root.rglob("*.yaml"):
        errors: list[str] = []
        candidate = _load_single_proposal(yaml_file, errors)
        if candidate is not None and candidate.bundle_id == bundle_id:
            existing_path = yaml_file
            break

    if existing_path is None:
        raise ProposalValidationError(
            [f"Proposal file not found for bundle_id='{bundle_id}' — cannot update state"]
        )

    raw = yaml.safe_load(existing_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProposalValidationError(
            [f"Cannot parse existing proposal file: {existing_path}"]
        )
    raw["status"] = "promoted"
    existing_path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    plan: dict[str, Any] = {
        "promotion_plan": {
            "proposal": {
                "bundle_id": bundle.bundle_id,
                "status": "promoted",
                "action": bundle.action,
                "target_family": bundle.target_family,
                "target_version": target_version,
                "risk_level": bundle.risk_level,
                "evidence_refs": [_evidence_ref_to_dict(e) for e in bundle.evidence_refs],
                "supporting_issues": list(bundle.supporting_issues),
            },
            "registry_operations": operations,
            "v0.1_note": (
                "This promotion plan is a human-reviewable output only. "
                "No automatic changes have been made to the registry. "
                "Review the operations above, apply them manually, and "
                "commit through the normal workflow."
            ),
        },
    }

    return plan


def review_proposal(
    proposal_dir: str | Path,
    bundle_id: str,
    new_status: str,
) -> Path:
    """Update the status of an existing proposal.

    Args:
        proposal_dir: Root directory for proposals.
        bundle_id: The bundle_id of the proposal to update.
        new_status: The new status value (must be in VALID_PROPOSAL_STATUSES).

    Returns:
        Path to the updated proposal file.

    Raises:
        ProposalValidationError: If the new status is invalid or the proposal is not found.
    """
    if new_status not in VALID_PROPOSAL_STATUSES:
        raise ProposalValidationError(
            [f"Invalid status '{new_status}': must be one of {sorted(VALID_PROPOSAL_STATUSES)}"]
        )

    bundle = get_proposal(proposal_dir, bundle_id)
    if bundle is None:
        raise ProposalValidationError([f"Proposal not found: bundle_id='{bundle_id}'"])

    # Find the existing file
    root = Path(proposal_dir).resolve()
    existing_path: Path | None = None
    for yaml_file in root.rglob("*.yaml"):
        errors: list[str] = []
        candidate = _load_single_proposal(yaml_file, errors)
        if candidate is not None and candidate.bundle_id == bundle_id:
            existing_path = yaml_file
            break

    if existing_path is None:
        raise ProposalValidationError([f"Proposal file not found for bundle_id='{bundle_id}'"])

    # Read raw, update status, write back
    raw = yaml.safe_load(existing_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProposalValidationError([f"Cannot parse existing proposal file: {existing_path}"])
    raw["status"] = new_status
    existing_path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return existing_path
