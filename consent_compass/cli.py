"""Command line interface for Consent Compass."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from .core import ALLOWED, BLOCKED, REVIEW, UNKNOWN, check_boundary


def load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: the top level must be an object")
    return value


def _md_value(value: Any) -> str:
    if value is None:
        return "(not supplied)"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(report: Dict[str, Any]) -> str:
    counts = report["finding_counts"]
    lines = [
        "# Consent Compass Boundary Report", "",
        f"**Overall status:** `{report['overall_status']}`",
        f"**Dataset:** `{report.get('dataset', {}).get('id', 'unknown')}`",
        f"**Intent:** `{report.get('intent_id') or 'unnamed'}`", "",
        f"Counts: ALLOWED={counts[ALLOWED]}, NEEDS_REVIEW={counts[REVIEW]}, BLOCKED={counts[BLOCKED]}, UNKNOWN={counts[UNKNOWN]}", "",
        "> This report is a data-use preflight. It is not legal advice, ethics approval, a consent determination, or permission to publish.", "",
        "## Findings", "",
    ]
    for finding in report["findings"]:
        lines.extend([
            f"### {finding['id']} — `{finding['status']}`", "",
            f"- Category: `{finding['category']}`",
            f"- Requested: {_md_value(finding.get('requested'))}",
            f"- Policy value: {_md_value(finding.get('policy_value'))}",
            f"- Rule: `{finding['rule_id']}`",
            f"- Explanation: {finding['explanation']}",
            f"- Evidence: {', '.join('`' + str(ref) + '`' for ref in finding.get('evidence', [])) or '(no source location supplied)' }",
        ])
        if finding.get("lower_risk_alternative"):
            lines.append(f"- Lower-risk alternative: {finding['lower_risk_alternative']}")
        lines.append("")
    lines.extend(["## Review boundary", "", report["disclaimer"], ""])
    return "\n".join(lines)


def render_html(report: Dict[str, Any]) -> str:
    title = html.escape(f"Consent Compass — {report['overall_status']}")
    cards = []
    for finding in report["findings"]:
        evidence = ", ".join(html.escape(str(x)) for x in finding.get("evidence", [])) or "No source location supplied"
        alternative = ""
        if finding.get("lower_risk_alternative"):
            alternative = f"<p><strong>Lower-risk alternative:</strong> {html.escape(finding['lower_risk_alternative'])}</p>"
        cards.append(
            f"<article class='finding {html.escape(finding['status'].lower())}'>"
            f"<h2>{html.escape(finding['id'])} <span>{html.escape(finding['status'])}</span></h2>"
            f"<p><strong>{html.escape(finding['category'])}</strong> — {html.escape(finding['explanation'])}</p>"
            f"<dl><dt>Requested</dt><dd>{html.escape(str(finding.get('requested')))}</dd>"
            f"<dt>Policy value</dt><dd>{html.escape(str(finding.get('policy_value')))}</dd>"
            f"<dt>Rule</dt><dd>{html.escape(finding['rule_id'])}</dd>"
            f"<dt>Evidence</dt><dd>{evidence}</dd></dl>{alternative}</article>"
        )
    template = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font:16px system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#172033;background:#f7f8fb}}
.banner{{padding:20px;border-radius:14px;background:white;border:1px solid #dfe4ee;margin-bottom:20px}}
.finding{{background:white;border:1px solid #dfe4ee;border-left:7px solid #64748b;border-radius:10px;padding:16px;margin:14px 0}}
.blocked{{border-left-color:#dc2626}}.needs_review{{border-left-color:#d97706}}.unknown{{border-left-color:#7c3aed}}.allowed{{border-left-color:#16a34a}}
h1{{margin-top:0}}h2{{margin:0 0 8px}}h2 span{{font-size:.7em;padding:4px 8px;border-radius:999px;background:#eef2ff}}
dt{{font-weight:700;float:left;clear:left;width:130px}}dd{{margin-left:140px;margin-bottom:6px;overflow-wrap:anywhere}}
.disclaimer{{color:#475569;font-size:.92em}}
</style></head><body><section class="banner"><h1>Consent Compass</h1>
<p><strong>Overall status:</strong> <code>{status}</code></p><p>{counts}</p>
<p class="disclaimer">{disclaimer}</p></section>{cards}</body></html>"""
    return template.format(
        title=title,
        status=html.escape(report["overall_status"]),
        counts=html.escape(json.dumps(report["finding_counts"], ensure_ascii=False)),
        disclaimer=html.escape(report["disclaimer"]),
        cards="\n".join(cards),
    )


def check_command(args: argparse.Namespace) -> int:
    policy = load_json(Path(args.policy))
    intent = load_json(Path(args.intent))
    report = check_boundary(policy, intent)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "boundary-decision.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "BOUNDARY_REPORT.md").write_text(render_markdown(report), encoding="utf-8")
    (output / "BOUNDARY_REPORT.html").write_text(render_html(report), encoding="utf-8")
    print(f"Overall: {report['overall_status']}")
    print(json.dumps(report["finding_counts"], ensure_ascii=False, sort_keys=True))
    if args.fail_on and report["overall_status"] in set(args.fail_on):
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare a declared data-use policy with an analysis intent.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run a local preflight check")
    check.add_argument("--policy", required=True, help="path to a policy JSON file")
    check.add_argument("--intent", required=True, help="path to an analysis-intent JSON file")
    check.add_argument("--output", required=True, help="directory for JSON, Markdown and HTML reports")
    check.add_argument("--fail-on", nargs="+", choices=[ALLOWED, REVIEW, BLOCKED, UNKNOWN], help="exit 2 when the overall status matches")
    check.set_defaults(handler=check_command)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2
