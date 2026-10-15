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

## Residual Debian base-image findings (reviewed 2026-10-15)

### Scan summary

Source artifact: trivy-container-vulnerability-reports (6).zip

| Severity | Findings per application image |
|---|---:|
| Critical | 0 |
| High | 44 |
| Medium | 58 |
| Low | 61 |
| Unknown | 1 |
| Total | 164 |

These counts represent package-vulnerability findings, not distinct CVEs.
The three application images had the same severity counts.

Trivy listed no non-empty FixedVersion values for these findings. This does
not prove that fixes do not exist. Debian security advisories and applicable
stable-release package updates must be checked independently.

### Distinct HIGH CVEs identified

| CVE | Affected package(s) in the scan | Follow-up action |
|---|---|---|
| CVE-2025-69720 | libncursesw6, libtinfo6, ncurses-base, ncurses-bin | Verify Debian status and whether affected functionality is used. |
| CVE-2026-16742 | libsystemd0, libudev1 | Verify Debian status and applicability to the container runtime. |
| CVE-2026-54369 | libacl1 | Verify Debian status and exposure to affected ACL operations. |
| CVE-2026-76642 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Review applicable advisory, package versions, and mount-related privileges. |
| CVE-2026-78408 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Review applicable advisory and whether affected functionality is available or used. |
| CVE-2026-78409 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Review applicable advisory and mount configuration exposure. |
| CVE-2026-78410 | bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util-linux | Review applicable advisory and privileged mount configuration exposure. |
| CVE-2026-9538 | perl-base | Verify Debian status and whether the affected functionality is used. |

### Remediation and risk-management plan

1. Retain the non-root application user.
2. Continue applying available Debian package updates and rebuilding images.
3. Re-scan rebuilt images and compare results with previous scan artifacts.
4. Verify each finding against the applicable Debian security tracker entry.
5. Do not introduce unstable repositories or suppress findings simply to obtain a green scan.
6. Reassess residual findings when applicable stable-release fixes become available.
7. Record subsequent scan dates, findings, and remediation decisions.
8. Treat exposure and exploitability as not yet fully validated until runtime configuration and service usage have been reviewed.

### Debian security tracker references

- https://security-tracker.debian.org/tracker/CVE-2025-69720
- https://security-tracker.debian.org/tracker/CVE-2026-16742
- https://security-tracker.debian.org/tracker/CVE-2026-54369
- https://security-tracker.debian.org/tracker/CVE-2026-76642
- https://security-tracker.debian.org/tracker/CVE-2026-78408
- https://security-tracker.debian.org/tracker/CVE-2026-78409
- https://security-tracker.debian.org/tracker/CVE-2026-78410
- https://security-tracker.debian.org/tracker/CVE-2026-9538
