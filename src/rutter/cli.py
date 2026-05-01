from __future__ import annotations

import argparse
import sys

import yaml

from .mcp_server import MCP_IMPORT_ERROR, run_server
from .proposals import dump_proposal_validation_result, validate_proposals
from .registry import (
    RegistryLookupError,
    RegistryValidationError,
    get_skill,
    get_skill_dependencies,
    get_skill_family,
    list_skill_families,
    search_skills,
    validate_registry,
    write_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        errors = validate_registry(args.path)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("Registry validation passed")
        return 0

    if args.command == "build-index":
        try:
            output_path = write_index(args.path, args.output)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        print(output_path)
        return 0

    if args.command == "search":
        try:
            results = search_skills(args.path, args.query)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        print(yaml.safe_dump({"results": results}, sort_keys=False), end="")
        return 0

    if args.command == "list-families":
        try:
            results = list_skill_families(args.path)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        print(yaml.safe_dump({"families": results}, sort_keys=False), end="")
        return 0

    if args.command == "get-family":
        try:
            result = get_skill_family(args.path, args.family, args.version)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        except RegistryLookupError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(yaml.safe_dump(result, sort_keys=False), end="")
        return 0

    if args.command == "get-skill":
        try:
            result = get_skill(args.path, args.skill_id)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        except RegistryLookupError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(yaml.safe_dump(result, sort_keys=False), end="")
        return 0

    if args.command == "get-dependencies":
        try:
            result = get_skill_dependencies(args.path, args.skill_id)
        except RegistryValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        except RegistryLookupError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(yaml.safe_dump(result, sort_keys=False), end="")
        return 0

    if args.command == "validate-proposals":
        proposal_root = args.proposal_dir if args.proposal_dir else args.path
        registry_root = args.path if args.proposal_dir else None
        results = validate_proposals(proposal_root, registry_root=registry_root)
        if args.json:
            import json
            output = dump_proposal_validation_result(results)
            print(json.dumps(output, indent=2))
        else:
            for path in sorted(results):
                errors = results[path]
                if errors:
                    print(f"FAIL  {path}", file=sys.stderr)
                    for error in errors:
                        print(f"       {error}", file=sys.stderr)
                else:
                    print(f"OK    {path}")
        has_errors = any(errors for errors in results.values())
        return 1 if has_errors else 0

    if args.command == "serve":
        try:
            run_server(
                args.path,
                transport=args.transport,
                host=args.host,
                port=args.port,
                debug=args.debug,
            )
        except RuntimeError as exc:
            if str(exc) == MCP_IMPORT_ERROR:
                print(str(exc), file=sys.stderr)
                return 1
            raise
        return 0

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rutter", description="Rutter skill registry CLI")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="Validate registry YAML and dependencies")
    validate_parser.add_argument("--path", default=".", help="Repository root or registry directory")

    index_parser = subparsers.add_parser("build-index", help="Generate registry/index.yaml")
    index_parser.add_argument("--path", default=".", help="Repository root or registry directory")
    index_parser.add_argument("--output", default=None, help="Optional output path for index.yaml")

    search_parser = subparsers.add_parser("search", help="Search skills across the registry")
    search_parser.add_argument("query", help="Free-text query")
    search_parser.add_argument("--path", default=".", help="Repository root or registry directory")

    list_families_parser = subparsers.add_parser(
        "list-families", help="List all indexed skill families"
    )
    list_families_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )

    get_family_parser = subparsers.add_parser(
        "get-family", help="Get one skill family manifest and skill payloads"
    )
    get_family_parser.add_argument("family", help="Family name, for example game-migration")
    get_family_parser.add_argument(
        "--version", default=None, help="Optional family version, defaults to latest"
    )
    get_family_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )

    get_skill_parser = subparsers.add_parser(
        "get-skill", help="Get one atomic skill payload by id"
    )
    get_skill_parser.add_argument("skill_id", help="Atomic skill id")
    get_skill_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )

    dependencies_parser = subparsers.add_parser(
        "get-dependencies", help="Get direct dependencies for one skill"
    )
    dependencies_parser.add_argument("skill_id", help="Atomic skill id")
    dependencies_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )

    validate_proposals_parser = subparsers.add_parser(
        "validate-proposals", help="Validate SkillProposalBundle@v1 proposals against the registry"
    )
    validate_proposals_parser.add_argument(
        "--path", default=".", help="Registry root (default) or proposal directory when --proposal-dir is used"
    )
    validate_proposals_parser.add_argument(
        "--proposal-dir", default=None, help="Proposal directory (overrides --path for proposals)"
    )
    validate_proposals_parser.add_argument(
        "--json", action="store_true", help="Output validation results as JSON"
    )

    serve_parser = subparsers.add_parser(
        "serve", help="Start the read-only MCP server over the registry"
    )
    serve_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    serve_parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport to use",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports")
    serve_parser.add_argument("--port", default=8000, type=int, help="Port for HTTP transports")
    serve_parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode for the MCP server"
    )
    return parser