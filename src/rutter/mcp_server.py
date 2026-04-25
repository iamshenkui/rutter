from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from .query import (
    get_skill_dependencies_tool,
    get_skill_family_tool,
    get_skill_tool,
    list_skill_families_tool,
    search_skills_tool,
    validate_registry_tool,
)

MCP_IMPORT_ERROR = (
    "MCP support is not installed. Use `uv run --extra mcp ...` or install the `mcp` extra."
)


def create_server(
    registry_root: str | Path = ".",
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
) -> Any:
    FastMCP = _load_fastmcp()
    resolved_root = str(Path(registry_root).resolve())

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

    return server


def run_server(
    registry_root: str | Path = ".",
    *,
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
) -> None:
    server = create_server(registry_root, host=host, port=port, debug=debug)
    server.run(transport=transport)


def _load_fastmcp() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised via CLI error handling
        raise RuntimeError(MCP_IMPORT_ERROR) from exc
    return FastMCP