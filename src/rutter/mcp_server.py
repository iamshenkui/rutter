from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from .query import (
    get_skill_dependencies_tool,
    get_skill_family_tool,
    get_skill_tool,
    get_proposal_tool,
    list_proposals_tool,
    list_skill_families_tool,
    search_skills_tool,
    validate_proposals_tool,
    validate_registry_tool,
)

MCP_IMPORT_ERROR = (
    "MCP support is not installed. Use `uv run --extra mcp ...` or install the `mcp` extra."
)


def create_server(
    registry_root: str | Path = ".",
    *,
    proposal_dir: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
) -> Any:
    FastMCP = _load_fastmcp()
    resolved_root = str(Path(registry_root).resolve())
    resolved_proposal_dir = str(
        Path(proposal_dir).resolve() if proposal_dir
        else Path(registry_root).resolve() / "proposals"
    )

    server = FastMCP(
        name="rutter",
        instructions=(
            "Read-only skill registry server. Use these tools to list, search, and fetch "
            "skill families or atomic skill payloads from the local registry."
        ),
        host=host,
        port=port,
        debug=debug,
        dependencies=("PyYAML", "mcp"),
    )

    @server.tool(
        name="list_skill_families",
        description="List indexed skill families with summary metadata.",
    )
    def list_skill_families() -> list[dict[str, Any]]:
        return list_skill_families_tool(resolved_root)

    @server.tool(
        name="search_skills",
        description="Search skills and registry metadata by free-text query.",
    )
    def search_skills(query: str) -> list[dict[str, Any]]:
        return search_skills_tool(resolved_root, query)

    @server.tool(
        name="get_skill_family",
        description="Fetch one skill family manifest and its atomic skill payloads.",
    )
    def get_skill_family(
        family_name: str,
        version: str | None = None,
    ) -> dict[str, Any]:
        return get_skill_family_tool(resolved_root, family_name, version)

    @server.tool(
        name="get_skill",
        description="Fetch one atomic skill payload by its global skill id.",
    )
    def get_skill(skill_id: str) -> dict[str, Any]:
        return get_skill_tool(resolved_root, skill_id)

    @server.tool(
        name="get_skill_dependencies",
        description="Fetch the direct dependencies for one atomic skill.",
    )
    def get_skill_dependencies(skill_id: str) -> dict[str, Any]:
        return get_skill_dependencies_tool(resolved_root, skill_id)

    @server.tool(
        name="validate_registry",
        description="Validate registry YAML, uniqueness rules, and dependencies.",
    )
    def validate_registry() -> list[str]:
        return validate_registry_tool(resolved_root)

    @server.tool(
        name="list_proposals",
        description="List proposals in the review surface, optionally filtered by status or family.",
    )
    def list_proposals(
        status_filter: str | None = None,
        family_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        return list_proposals_tool(
            resolved_proposal_dir,
            status_filter=status_filter,
            family_filter=family_filter,
        )

    @server.tool(
        name="get_proposal",
        description="Fetch one proposal bundle by bundle_id.",
    )
    def get_proposal(bundle_id: str) -> dict[str, Any] | None:
        return get_proposal_tool(resolved_proposal_dir, bundle_id)

    @server.tool(
        name="validate_proposals",
        description="Validate all proposals in the review surface against the registry.",
    )
    def validate_proposals() -> dict[str, Any]:
        return validate_proposals_tool(resolved_proposal_dir, resolved_root)

    return server


def run_server(
    registry_root: str | Path = ".",
    *,
    proposal_dir: str | Path | None = None,
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
) -> None:
    server = create_server(
        registry_root, proposal_dir=proposal_dir, host=host, port=port, debug=debug
    )
    server.run(transport=transport)


def _load_fastmcp() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised via CLI error handling
        raise RuntimeError(MCP_IMPORT_ERROR) from exc
    return FastMCP