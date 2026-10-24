"""Command-line interface:  python -m mas_agent [demo|process|profile]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import MasAgent
from .config import load_settings


def _sample_leads_path() -> Path:
    candidates = [
        Path.cwd() / "data" / "sample_leads.json",
        Path(__file__).resolve().parents[2] / "data" / "sample_leads.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _print_result(result: dict, show_draft: bool = True) -> None:
    lead, score, draft = result["lead"], result["score"], result["draft"]
    print("=" * 72)
    print(f"LEAD: {lead.name or '(no name)'} — {lead.city}, {lead.state} "
          f"— {lead.service or '(no service)'}")
    print(f"SCORE: {score.score}/100  GRADE: {score.grade.upper()}"
          + (f"  FLAGS: {', '.join(score.flags)}" if score.flags else ""))
    for reason in score.reasons:
        print(f"  - {reason}")
    if show_draft:
        print("-" * 72)
        print("FOLLOW-UP DRAFT (not sent):")
        print(draft.render())
    if result.get("hubspot") is not None:
        print("-" * 72)
        print(f"HUBSPOT: {result['hubspot']}")
    print()


def cmd_demo(_args) -> int:
    agent = MasAgent()
    mode = "DRY-RUN (no HubSpot token)" if agent.hubspot.dry_run else "LIVE HubSpot"
    print(f"Mas Cabinets AI Agent — demo with sample leads  [{mode}]")
    print(f"Work email: {agent.settings.work_email} | "
          f"HubSpot portal: {agent.profile.hubspot_portal_name} "
          f"({agent.settings.hubspot_portal_id})\n")
    leads = agent.load_leads(_sample_leads_path())
    results = []
    for lead in leads:  # process + print one at a time, so output stays in order
        result = agent.process_lead(lead, push=True)  # push honours dry-run mode
        results.append(result)
        _print_result(result)
    hot = sum(1 for r in results if r["score"].grade == "hot")
    print(f"Summary: {len(results)} leads processed, {hot} hot. "
          f"Drafts generated for all; nothing was sent.")
    return 0


def cmd_process(args) -> int:
    agent = MasAgent()
    leads = agent.load_leads(args.file)
    for lead in leads:
        result = agent.process_lead(lead, push=args.push)
        _print_result(result, show_draft=not args.no_draft)
    return 0


def cmd_profile(_args) -> int:
    settings = load_settings()
    p = settings.business
    print(f"{p.legal_name} (aka {p.aka})")
    print(f"{p.address}")
    print(f"Phone: {p.phone} | Website: {p.website} | Email: {settings.work_email}")
    print(f"Hours: {p.hours}")
    print(f"Services: {', '.join(p.services)}")
    print(f"Focus: {p.focus_state} — counties: {', '.join(p.focus_counties)}")
    print(f"HubSpot: {p.hubspot_portal_name} (portal {settings.hubspot_portal_id}), "
          f"mode: {'dry-run' if settings.hubspot_dry_run else 'live'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mas_agent",
                                     description="Mas Cabinets AI lead agent")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("demo", help="Run the sample-leads demo (default)")
    p_process = sub.add_parser("process", help="Score leads from a JSON file")
    p_process.add_argument("file", help="Path to a leads JSON file")
    p_process.add_argument("--push", action="store_true",
                           help="Push results to HubSpot (dry-run without a token)")
    p_process.add_argument("--no-draft", action="store_true",
                           help="Do not print follow-up drafts")
    sub.add_parser("profile", help="Print the business profile in use")

    args = parser.parse_args(argv)
    if args.command == "process":
        return cmd_process(args)
    if args.command == "profile":
        return cmd_profile(args)
    return cmd_demo(args)  # default: demo


if __name__ == "__main__":
    sys.exit(main())
