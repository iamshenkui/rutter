from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AtomicSkill:
    id: str
    name: str
    description: str
    category: str
    incremental_rules: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SkillFileRef:
    id: str
    file: str


@dataclass(frozen=True)
class SkillManifest:
    family: str
    version: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    skills: list[SkillFileRef] = field(default_factory=list)


@dataclass(frozen=True)
class SkillFamily:
    manifest: SkillManifest
    directory: Path
    skills: dict[str, AtomicSkill]


# ── SkillProposalBundle@v1 ──────────────────────────────────────────────

VALID_PROPOSAL_SCHEMA_VERSIONS = {"1"}
VALID_PROPOSAL_STATUSES = {"proposed", "needs_revision", "accepted", "rejected", "promoted"}
VALID_PROPOSAL_ACTIONS = {
    "create_new_skill",
    "update_existing_skill",
    "split_existing_skill",
    "deprecate_skill",
    "metadata_only",
    "no_action",
}
VALID_RISK_LEVELS = {"low", "medium", "high"}


@dataclass(frozen=True)
class EvidenceRef:
    type: str = ""
    path: str = ""
    description: str = ""


@dataclass(frozen=True)
class SkillProposalBundle:
    schema_version: str
    bundle_id: str
    status: str
    target_family: str
    action: str
    supporting_issues: tuple[str, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    risk_level: str = "medium"
    created_at: str = ""
    target_skill_id: str | None = None
    new_skill_id: str | None = None