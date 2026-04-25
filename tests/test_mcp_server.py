from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from rutter.cli import main
from rutter.mcp_server import create_server


pytest.importorskip("mcp.server.fastmcp")

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_create_server_registers_expected_tools() -> None:
    server = create_server(PROJECT_ROOT)

    tools = asyncio.run(server.list_tools())
    tool_names = sorted(tool.name for tool in tools)

    assert tool_names == [
        "get_skill",
        "get_skill_dependencies",
        "get_skill_family",
        "list_skill_families",
        "search_skills",
        "validate_registry",
    ]


def test_cli_serve_dispatches_to_run_server(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_run_server(
        registry_root: str,
        *,
        transport: str,
        host: str,
        port: int,
        debug: bool,
    ) -> None:
        calls["registry_root"] = registry_root
        calls["transport"] = transport
        calls["host"] = host
        calls["port"] = port
        calls["debug"] = debug

    monkeypatch.setattr("rutter.cli.run_server", fake_run_server)

    exit_code = main(
        [
            "serve",
            "--path",
            str(PROJECT_ROOT),
            "--transport",
            "stdio",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--debug",
        ]
    )

    assert exit_code == 0
    assert calls == {
        "registry_root": str(PROJECT_ROOT),
        "transport": "stdio",
        "host": "0.0.0.0",
        "port": 9000,
        "debug": True,
    }