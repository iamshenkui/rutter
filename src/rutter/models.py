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