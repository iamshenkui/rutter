from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import (
    EvidenceRef,
    SkillProposalBundle,
    VALID_RISK_LEVELS,
)

# ── Non-executable item patterns ─────────────────────────────────────
# These are structural markers from split PRDs that don't represent
# actionable proposal bundles: Phase headers and Slice boundaries.
# Block-related structural markers are handled separately in
# _is_executable so that legitimate blocker-shaped proposals (e.g.
# game_migration_blocker with a real action) are not dropped.
NON_EXECUTABLE_PATTERNS: list[str] = [
    "phase",
    "slice",
]

# ── Domain filter patterns ───────────────────────────────────────────
# Task categories that belong to domains outside rutter's scope.
NON_RUTTER_DOMAIN_PATTERNS: list[str] = [
    ".state",
    "taxonomy",
    "run-to-session",
]


def adapt_raw_proposal(raw: dict[str, Any]) -> SkillProposalBundle:
    """Convert a raw proposal dict into a normalized SkillProposalBundle@v1.

    * schema_version is always forced to ``"1"``.
    * evidence_refs are parsed from both string (path-only) and dict
      (type/path/description) formats — compatible with meta-agent output.
    * Fields outside the SkillProposalBundle@v1 schema are silently dropped.

    Args:
        raw: Raw proposal data from meta-agent, hand-authored YAML, or a
             split PRD import.

    Returns:
        A normalized SkillProposalBundle instance.
    """
    bundle_id = _req_str(raw, "bundle_id")
    status = _req_str(raw, "status", "proposed")
    target_family = _req_str(raw, "target_family")
    action = _req_str(raw, "action")
    risk_level = _req_str(raw, "risk_level", "medium")
    created_at = _req_str(raw, "created_at", "")
    target_skill_id = _opt_str(raw.get("target_skill_id"))
    new_skill_id = _opt_str(raw.get("new_skill_id"))

    # Normalize supporting_issues to a list of non-empty strings
    supporting_issues = _normalize_string_list(raw.get("supporting_issues"))

    # Normalize evidence_refs: accept string or dict entries
    evidence_refs = _adapt_evidence_refs(raw.get("evidence_refs"))

    # Clamp risk_level to a known value
    if risk_level not in VALID_RISK_LEVELS:
        risk_level = "medium"

    return SkillProposalBundle(
        schema_version="1",
        bundle_id=bundle_id or _generate_bundle_id(raw),
        status=status if status else "proposed",
        target_family=target_family or "unknown",
        action=action or "no_action",
        supporting_issues=tuple(supporting_issues),
        evidence_refs=tuple(evidence_refs),
        risk_level=risk_level,
        created_at=created_at or "",
        target_skill_id=target_skill_id,
        new_skill_id=new_skill_id,
    )


def adapt_proposals(raw_list: list[dict[str, Any]]) -> list[SkillProposalBundle]:
    """Adapt multiple raw proposal dicts, filtering out non-executable items.

    Non-executable items are structural markers from split PRDs (Phase, Slice)
    that don't represent actionable proposal bundles. Items whose description
    contains "block" are considered non-executable only when they lack an
    action field — legitimate blocker-shaped proposals with proper actions
    are preserved.

    Args:
        raw_list: Raw proposal dicts, possibly mixed with structural markers.

    Returns:
        List of SkillProposalBundle instances (non-executable items removed).
    """
    return [
        adapt_raw_proposal(raw)
        for raw in raw_list
        if _is_executable(raw)
    ]


def adapt_and_filter_by_domain(
    raw_list: list[dict[str, Any]],
) -> list[SkillProposalBundle]:
    """Adapt proposals and filter to rutter's core domain.

    Items belonging to out-of-scope domains (``.state`` scanning, taxonomy
    adapter, run-to-session linking) are excluded. Only rutter-relevant
    proposals (review surface, validator, promotion tooling, fixtures/tests)
    are returned.

    Args:
        raw_list: Raw proposal dicts from a split PRD or meta-agent.

    Returns:
        Filtered list of SkillProposalBundle instances in rutter's domain.
    """
    return [
        bundle
        for bundle in adapt_proposals(raw_list)
        if not _is_out_of_domain(bundle)
    ]


# ── Internal helpers ────────────────────────────────────────────────────────


def _is_executable(raw: dict[str, Any]) -> bool:
    """Check whether a raw entry represents an actionable proposal.

    Non-executable items are structural markers (Phase, Slice) that should
    be excluded from the adapted output. Block-related descriptions are
    excluded only when the item lacks an action field — this preserves
    legitimate blocker-shaped proposals while dropping structural markers.
    """
    bundle_id = str(raw.get("bundle_id", "")).strip().lower()
    title = str(raw.get("title", "")).strip().lower()
    description = str(raw.get("description", "")).strip().lower()

    # Phase and slice are always structural markers
    combined = f"{bundle_id} {title} {description}"
    for pattern in NON_EXECUTABLE_PATTERNS:
        if pattern in combined:
            return False

    # Block-related structural markers: items whose description contains
    # "block" but lack an action field are non-executable markers (e.g.
    # "Blocked on external dependency"), not real proposals.
    if not raw.get("action") and "block" in description:
        return False

    # An entry without bundle_id and without action is non-executable
    if not bundle_id and not raw.get("action"):
        return False

    return True


def _is_out_of_domain(bundle: SkillProposalBundle) -> bool:
    """Check whether a proposal falls outside rutter's core scope."""
    combined = (
        f"{bundle.bundle_id} {bundle.target_family} {bundle.action}"
    ).lower()
    for pattern in NON_RUTTER_DOMAIN_PATTERNS:
        if pattern in combined:
            return True
    return False


def _adapt_evidence_refs(raw_refs: Any) -> list[EvidenceRef]:
    """Convert raw evidence refs (string or dict) into a list of EvidenceRef."""
    if not isinstance(raw_refs, list):
        return []

    result: list[EvidenceRef] = []
    for item in raw_refs:
        if isinstance(item, str):
            result.append(EvidenceRef(path=item.strip()))
        elif isinstance(item, dict):
            result.append(
                EvidenceRef(
                    type=str(item.get("type", "")),
                    path=str(item.get("path", "")),
                    description=str(item.get("description", "")),
                )
            )
    return result


def _req_str(raw: dict[str, Any], key: str, default: str = "") -> str:
    """Extract a trimmed string value or return a default."""
    val = raw.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    if val is not None:
        s = str(val).strip()
        return s if s else default
    return default


def _opt_str(val: Any) -> str | None:
    """Convert a value to None or a non-empty trimmed string."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _normalize_string_list(raw: Any) -> list[str]:
    """Convert a raw list value into a list of non-empty strings."""
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if isinstance(item, str) and item.strip()]


def _generate_bundle_id(raw: dict[str, Any]) -> str:
    """Generate a fallback bundle_id from available data."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    action = str(raw.get("action", "proposal")).strip() or "proposal"
    return f"adapted-{action}-{ts}"
