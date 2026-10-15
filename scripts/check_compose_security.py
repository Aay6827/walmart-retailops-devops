"""Fail CI if application container runtime hardening is missing."""

import json
import subprocess
import sys


SERVICES = (
    "retailops-api",
    "order-service",
    "inventory-service",
)


def main() -> int:
    try:
        result = subprocess.run(
            ["docker", "compose", "config", "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
        )
        config = json.loads(result.stdout)
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ):
        print(
            "FAIL: Could not resolve Docker Compose configuration.",
            file=sys.stderr,
        )
        return 2

    services = config.get("services", {})
    failures = []

    for name in SERVICES:
        service = services.get(name)

        if not isinstance(service, dict):
            failures.append(f"{name}: service is missing")
            continue

        checks = {
            "runs as UID/GID 10001:10001":
                service.get("user") == "10001:10001",
            "root filesystem is read-only":
                service.get("read_only") is True,
            "drops all Linux capabilities":
                "ALL" in (service.get("cap_drop") or []),
            "enables no-new-privileges":
                "no-new-privileges:true"
                in (service.get("security_opt") or []),
        }

        tmpfs_entries = service.get("tmpfs") or []
        checks["has protected temporary /tmp"] = any(
            isinstance(entry, str)
            and entry.startswith("/tmp:")
            and "noexec" in entry.split(":")[-1].split(",")
            and "nosuid" in entry.split(":")[-1].split(",")
            for entry in tmpfs_entries
        )

        failed = [label for label, passed in checks.items() if not passed]

        if failed:
            failures.extend(f"{name}: {label}" for label in failed)
            print(f"FAIL: {name}")
            for label in failed:
                print(f"  - {label}")
        else:
            print(f"PASS: {name} meets all runtime security checks")

    if failures:
        print(f"\nSecurity policy failed: {len(failures)} issue(s).")
        return 1

    print("\nAll application runtime security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())