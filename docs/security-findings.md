# Container Security Findings and Remediation

## Purpose and scope

The CI workflow builds the RetailOps API, order-service, and inventory-service images and scans them with Trivy for operating-system and application-library vulnerabilities. The workflow keeps full JSON reports as a downloadable artifact and publishes a concise summary in the GitHub Actions run summary.

The scan is currently **report-only**: Trivy's `exit-code: "0"` setting does not fail the workflow solely because findings exist. This is intentional while the baseline is being triaged. It must not be interpreted as a clean security scan.

## How to read the CI summary

- **Severity counts** are individual package-vulnerability findings returned by Trivy, grouped by severity. They are not counts of distinct CVE IDs; the same CVE can affect multiple packages.
- **Fixable** means the report has a non-empty `FixedVersion` field for that finding. This is a prioritization signal, not proof that upgrading is risk-free or that the version is available from the image's configured repositories.
- **No fixed version listed** means Trivy's JSON has a blank `FixedVersion` for that finding. It does **not** prove that no upstream fix exists or that a distribution backport is unavailable. Check the relevant distribution security tracker/advisory and the package's changelog before closing a finding.
- An absent or invalid report is explicitly shown as unavailable; it is not reported as zero vulnerabilities.
- Keep the full `trivy-container-vulnerability-reports` artifact for investigation. Do not filter out unfixed findings merely to lower the displayed count.

## Baseline recorded on 15 October 2026

The reviewed CI JSON reports for the three images each contained 176 package-vulnerability findings: 0 Critical, 44 High, 68 Medium, 63 Low, and 1 Unknown. These are point-in-time scan results, not a claim that 176 distinct CVEs exist. Re-run the workflow to refresh the baseline as the image, packages, and Trivy vulnerability database change.

The reports showed these High-severity OS package/version pairs with a blank `FixedVersion` field:

| Vulnerability ID | Package(s) reported | Installed version in the reviewed report |
|---|---|---|
| CVE-2025-69720 | `libncursesw6` | `6.5+20250216-2` |
| CVE-2026-16742 | `libsystemd0` | `257.13-1~deb13u1` |
| CVE-2026-54369 | `libacl1` | `2.3.2-2+b1` |
| CVE-2026-76642 | `bsdutils`, `util-linux` | `1:2.41.5-0+deb13u1` for `bsdutils`; `2.41.5-0+deb13u1` for `util-linux` |
| CVE-2026-78408 | `bsdutils`, `util-linux` | Same versions as above |
| CVE-2026-78409 | `bsdutils`, `util-linux` | Same versions as above |
| CVE-2026-78410 | `bsdutils`, `util-linux` | Same versions as above |

The `apt-get update && apt-get upgrade -y` instruction was added to the runtime stages, but the reviewed CI report still showed these package versions and findings. Therefore the package-upgrade instruction alone did not resolve this observed baseline. Do not assume that a blank `FixedVersion` means the finding is false-positive; check the advisory, package status, installed package, and runtime exposure.

## Triage and remediation workflow

1. **Confirm the finding.** Record the image, CVE, package, installed version, severity, and Trivy report timestamp. Inspect the relevant image's JSON artifact, not only the aggregate count.
2. **Check authoritative package guidance.** Review the distribution's security tracker/advisory and upstream advisory. Distinguish a fix published in another distribution release from a fix available for the image's actual Debian suite and configured repositories.
3. **Prioritize based on risk.** Consider severity, exploitability, whether the affected binary/library is used, whether the code path is reachable, container privileges, network exposure, and available mitigations. A package finding alone does not prove that a vulnerable service is running or reachable.
4. **Make a controlled change.** Prefer a fix available for the chosen stable base-image suite. Avoid moving to testing/unstable solely to make a scan green. If changing the base image or adding/removing packages, document the reason and compatibility trade-offs.
5. **Verify after rebuilding.** Build fresh images, inspect the affected package versions in the resulting image, run the application tests and Compose validation, and re-run Trivy. Compare severity and fixability counts and review the individual findings that remain.
6. **Document residual risk.** For findings with no fixed version listed, document the advisory checked, exposure assessment, available mitigation, owner, and next review trigger. Revisit when the distribution publishes updated guidance.

## Guardrails

- Do not suppress all unfixed findings or alter scanner severity settings just to create a green result.
- Do not claim “vulnerability-free” solely because CI passed; this workflow is currently report-only.
- Retain Trivy JSON artifacts for reproducibility and review. The workflow currently retains them for 30 days.
- Treat package/version and vulnerability counts as time-sensitive; the database and distribution advisories can change independently of application code.

## Advisory references

Use the current upstream/distribution records during each triage; do not treat this static baseline as a permanent advisory status:

- [Debian Security Tracker — ncurses](https://security-tracker.debian.org/tracker/source-package/ncurses)
- [Debian Security Tracker — systemd](https://security-tracker.debian.org/tracker/source-package/systemd)
- [Debian Security Tracker — acl](https://security-tracker.debian.org/tracker/source-package/acl)
- [Debian Security Tracker — util-linux](https://security-tracker.debian.org/tracker/source-package/util-linux)
- [Trivy vulnerability scanner documentation](https://trivy.dev/docs/latest/scanner/vulnerability/)
