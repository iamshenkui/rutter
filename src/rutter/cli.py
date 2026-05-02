from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .mcp_server import MCP_IMPORT_ERROR, run_server
from .models import EvidenceRef, SkillProposalBundle, VALID_PROPOSAL_ACTIONS, VALID_RISK_LEVELS, VALID_PROPOSAL_STATUSES
from .proposals import (
    ProposalValidationError,
    dump_proposal_validation_result,
    get_proposal,
    list_proposals,
    promote_proposal,
    review_proposal,
    submit_proposal,
    validate_proposals,
)
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
        proposal_root = args.proposal_dir or str(Path(args.path) / "proposals")
        registry_root = args.path
        validation_results = validate_proposals(proposal_root, registry_root=registry_root)
        if args.json:
            import json
            output = dump_proposal_validation_result(validation_results)
            print(json.dumps(output, indent=2))
        else:
            for path in sorted(validation_results):
                errors = validation_results[path]
                if errors:
                    print(f"FAIL  {path}", file=sys.stderr)
                    for error in errors:
                        print(f"       {error}", file=sys.stderr)
                else:
                    print(f"OK    {path}")
        has_errors = any(errors for errors in validation_results.values())
        return 1 if has_errors else 0

    if args.command == "propose":
        proposal_dir = args.proposal_dir or str(Path(args.path) / "proposals")
        registry_root = args.path

        proposal = SkillProposalBundle(
            schema_version="1",
            bundle_id=args.bundle_id,
            status=args.status,
            target_family=args.target_family,
            action=args.action,
            risk_level=args.risk_level or "medium",
            created_at=args.created_at or "",
            target_skill_id=args.target_skill_id,
            new_skill_id=args.new_skill_id,
            supporting_issues=tuple(args.supporting_issues or []),
            evidence_refs=tuple(
                EvidenceRef(path=s) for s in (args.evidence_refs or [])
            ),
        )

        try:
            result_path = submit_proposal(
                proposal,
                proposal_dir,
                registry_root=registry_root,
                allow_overwrite=args.allow_overwrite,
            )
        except ProposalValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(result_path)
        return 0

    if args.command == "list-proposals":
        proposal_dir = args.proposal_dir or str(Path(args.path) / "proposals")
        proposals = list_proposals(
            proposal_dir,
            status_filter=args.status,
            family_filter=args.family,
        )
        if args.json:
            import json
            print(json.dumps(proposals, indent=2))
        else:
            if not proposals:
                print("No proposals found.")
                return 0
            header = f"{'Bundle ID':<40} {'Status':<16} {'Action':<26} {'Family':<24} {'Risk':<8}"
            print(header)
            print("-" * len(header))
            for p in proposals:
                print(
                    f"{p['bundle_id']:<40} {p['status']:<16} {p['action']:<26} "
                    f"{p['target_family']:<24} {p['risk_level']:<8}"
                )
        return 0

    if args.command == "get-proposal":
        proposal_dir = args.proposal_dir or str(Path(args.path) / "proposals")
        bundle = get_proposal(proposal_dir, args.bundle_id)
        if bundle is None:
            print(f"Proposal not found: bundle_id='{args.bundle_id}'", file=sys.stderr)
            return 1
        from dataclasses import asdict
        print(yaml.safe_dump(asdict(bundle), sort_keys=False, allow_unicode=True), end="")
        return 0

    if args.command == "review-proposal":
        proposal_dir = args.proposal_dir or str(Path(args.path) / "proposals")
        try:
            result_path = review_proposal(proposal_dir, args.bundle_id, args.status)
        except ProposalValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        print(f"Updated: {result_path}")
        return 0

    if args.command == "promote-proposal":
        proposal_dir = args.proposal_dir or str(Path(args.path) / "proposals")
        try:
            plan = promote_proposal(
                proposal_dir,
                args.bundle_id,
                registry_root=args.path,
            )
        except ProposalValidationError as exc:
            for error in exc.errors:
                print(error, file=sys.stderr)
            return 1
        print(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True), end="")
        return 0

    if args.command == "serve":
        try:
            run_server(
                args.path,
                proposal_dir=args.proposal_dir,
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

    propose_parser = subparsers.add_parser(
        "propose", help="Submit a new skill proposal to the review surface"
    )
    propose_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    propose_parser.add_argument(
        "--proposal-dir", default=None, help="Proposal directory (default: --path/proposals)"
    )
    propose_parser.add_argument("--bundle-id", required=True, help="Unique bundle identifier")
    propose_parser.add_argument(
        "--status", default="proposed", choices=sorted(VALID_PROPOSAL_STATUSES),
        help="Proposal status (default: proposed)"
    )
    propose_parser.add_argument(
        "--target-family", required=True, help="Target skill family in the registry"
    )
    propose_parser.add_argument(
        "--action", required=True, choices=sorted(VALID_PROPOSAL_ACTIONS),
        help="Proposal action type"
    )
    propose_parser.add_argument(
        "--risk-level", default="medium", choices=sorted(VALID_RISK_LEVELS),
        help="Risk level (default: medium)"
    )
    propose_parser.add_argument(
        "--target-skill-id", default=None,
        help="Required for update_existing_skill action"
    )
    propose_parser.add_argument(
        "--new-skill-id", default=None,
        help="Required for create_new_skill action"
    )
    propose_parser.add_argument(
        "--created-at", default=None,
        help="ISO 8601 creation timestamp (default: auto)"
    )
    propose_parser.add_argument(
        "--supporting-issues", nargs="*", default=[],
        help="Supporting issue references"
    )
    propose_parser.add_argument(
        "--evidence-refs", nargs="*", default=[],
        help="Evidence file references"
    )
    propose_parser.add_argument(
        "--allow-overwrite", action="store_true",
        help="Overwrite existing proposal file if it exists"
    )

    list_proposals_parser = subparsers.add_parser(
        "list-proposals", help="List proposals in the review surface"
    )
    list_proposals_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    list_proposals_parser.add_argument(
        "--proposal-dir", default=None,
        help="Proposal directory (default: --path/proposals)"
    )
    list_proposals_parser.add_argument(
        "--status", default=None, choices=sorted(VALID_PROPOSAL_STATUSES),
        help="Filter by status"
    )
    list_proposals_parser.add_argument(
        "--family", default=None,
        help="Filter by target family"
    )
    list_proposals_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    get_proposal_parser = subparsers.add_parser(
        "get-proposal", help="Show one proposal by bundle_id"
    )
    get_proposal_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    get_proposal_parser.add_argument(
        "--proposal-dir", default=None,
        help="Proposal directory (default: --path/proposals)"
    )
    get_proposal_parser.add_argument("bundle_id", help="Bundle identifier of the proposal")

    review_proposal_parser = subparsers.add_parser(
        "review-proposal", help="Change the status of an existing proposal"
    )
    review_proposal_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    review_proposal_parser.add_argument(
        "--proposal-dir", default=None,
        help="Proposal directory (default: --path/proposals)"
    )
    review_proposal_parser.add_argument("bundle_id", help="Bundle identifier of the proposal")
    review_proposal_parser.add_argument(
        "--status", required=True, choices=sorted(VALID_PROPOSAL_STATUSES),
        help="New status value"
    )

    promote_proposal_parser = subparsers.add_parser(
        "promote-proposal", help="Generate a human-reviewable promotion plan for an accepted proposal"
    )
    promote_proposal_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    promote_proposal_parser.add_argument(
        "--proposal-dir", default=None,
        help="Proposal directory (default: --path/proposals)"
    )
    promote_proposal_parser.add_argument("bundle_id", help="Bundle identifier of the accepted proposal")

    serve_parser = subparsers.add_parser(
        "serve", help="Start the read-only MCP server over the registry"
    )
    serve_parser.add_argument(
        "--path", default=".", help="Repository root or registry directory"
    )
    serve_parser.add_argument(
        "--proposal-dir", default=None,
        help="Proposal directory (default: --path/proposals)"
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