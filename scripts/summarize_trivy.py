#!/usr/bin/env python3
"""Summarize Trivy JSON reports for GitHub Actions and local review.

Counts are Trivy package-vulnerability findings, not distinct CVE IDs.
A non-empty FixedVersion means Trivy lists a candidate fixed version. A blank
FixedVersion means no fixed version is listed in that report; it does not by
itself prove that no upstream or distribution-specific fix exists.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
REPORTS = (
    ("RetailOps API", "retailops-api.json"),
    ("Order Service", "order-service.json"),
    ("Inventory Service", "inventory-service.json"),
)


def read_findings(report_path: Path) -> list[dict[str, Any]]:
    """Return vulnerability objects from a Trivy report."""
    data = json.loads(report_path.read_text(encoding="utf-8-sig"))
    findings: list[dict[str, Any]] = []
    for result in data.get("Results") or []:
        if not isinstance(result, dict):
            continue
        vulnerabilities = result.get("Vulnerabilities") or []
        for vulnerability in vulnerabilities:
            if isinstance(vulnerability, dict):
                findings.append(vulnerability)
    return findings


def summarize_report(name: str, report_path: Path) -> tuple[list[str], bool]:
    """Build rows for a report; return its Markdown lines and parse status."""
    if not report_path.is_file():
        severity_cells = " | ".join(["—"] * (len(SEVERITIES) + 1))
        return [
            f"| {name} (report not generated) | {severity_cells} |",
            f"| {name} (report unavailable) | — | — | — |",
        ], False

    try:
        findings = read_findings(report_path)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        safe_error = str(exc).replace("|", "\\|").replace("\n", " ")
        severity_cells = " | ".join(["—"] * (len(SEVERITIES) + 1))
        return [
            f"| {name} (report parse error: {safe_error}) | {severity_cells} |",
            f"| {name} (report unavailable) | — | — | — |",
        ], False

    counts: Counter[str] = Counter()
    fixable = 0
    for finding in findings:
        severity = str(finding.get("Severity") or "UNKNOWN").upper()
        if severity not in SEVERITIES:
            severity = "UNKNOWN"
        counts[severity] += 1
        fixed_version = finding.get("FixedVersion")
        if fixed_version is not None and str(fixed_version).strip():
            fixable += 1

    total = len(findings)
    no_fixed_version = total - fixable
    severity_row = "| " + " | ".join(
        [name] + [str(counts[severity]) for severity in SEVERITIES] + [str(total)]
    ) + " |"
    remediation_row = (
        f"| {name} | {fixable} | {no_fixed_version} | {total} |"
    )
    return [severity_row, remediation_row], True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("trivy-reports"),
        help="Directory containing the three Trivy JSON reports (default: trivy-reports)",
    )
    args = parser.parse_args()

    severity_lines = [
        "## Container vulnerability summary",
        "",
        "Counts are package-vulnerability findings, not distinct CVE IDs.",
        "",
        "| Image | " + " | ".join(SEVERITIES) + " | Total |",
        "|---|" + "|".join(["---:"] * (len(SEVERITIES) + 1)) + "|",
    ]
    remediation_lines = [
        "## Remediation status",
        "",
        "`Fixable` means Trivy lists a non-empty `FixedVersion`. `No fixed version listed` means that field is blank in the report; verify the relevant distribution advisory before concluding that no fix exists.",
        "",
        "| Image | Fixable | No fixed version listed | Total |",
        "|---|---:|---:|---:|",
    ]

    valid_reports = 0
    for name, filename in REPORTS:
        rows, valid = summarize_report(name, args.report_dir / filename)
        severity_lines.append(rows[0])
        remediation_lines.append(rows[1])
        valid_reports += int(valid)

    summary = "\n".join(severity_lines + [""] + remediation_lines) + "\n"
    print(summary, end="")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as summary_file:
                summary_file.write(summary)
        except OSError as exc:
            # Keep this reporting-only step from masking the scan/build outcome.
            print(f"Warning: unable to write GitHub step summary: {exc}")

    if valid_reports != len(REPORTS):
        print(
            f"Warning: parsed {valid_reports} of {len(REPORTS)} Trivy reports; "
            "see rows marked unavailable above."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
