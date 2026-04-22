"""
Dependency baseline — enforced minimum versions.

This test locks in every Snyk / CVE-driven upgrade the team has shipped so
that a careless `pip freeze` or requirements.txt rewrite cannot silently
downgrade us back into vulnerable territory.

Add an entry whenever you upgrade a package for a CVE. The list IS the
security posture — CI will fail fast if anyone rolls it back.

Maintained by: Security / Platform
Last audited:  2026-04-22 (Snyk scan SolomonAI-Snyk-Fixes-2)
"""
from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

import pytest
from packaging.version import Version


# Minimum versions required to close specific CVEs. Do NOT lower these without
# a security review; do NOT remove entries. Upgrades above the minimum are
# fine and encouraged.
#
# Format: package_name -> (min_version, "rationale / CVE refs")
SECURITY_FLOOR: dict[str, tuple[str, str]] = {
    # ── Snyk 2026-02 / 2026-04 — backend/requirements.txt ───────────────
    "aiohttp":      ("3.13.4",  "27 issues incl. SSRF CWE-918, req smuggling CWE-444"),
    "urllib3":      ("2.6.3",   "Data amplification CWE-409, creds leak CWE-212, open redirect CWE-601"),
    "cryptography": ("46.0.7",  "CWE-345 auth data, CWE-295 cert validation, CWE-787 OOB write"),
    "requests":     ("2.33.0",  "CWE-670 control flow, CWE-201 cross-origin leak, CWE-377 insecure tmp"),
    "pyasn1":       ("0.6.3",   "CWE-770 DoS, CWE-674 uncontrolled recursion"),
    "PyJWT":        ("2.12.0",  "CWE-347 signature verification bypass — AUTH CRITICAL"),
    "zipp":         ("3.19.1",  "CWE-835 infinite loop on crafted zip"),
}

# Packages that must be ABSENT (removed due to unfixable issues)
SECURITY_DENYLIST: dict[str, str] = {
    "python-jose": "CVE-unfixed signature forgery; replaced with PyJWT",
    "ecdsa":       "CVE-timing leak; replaced by cryptography.hazmat primitives",
}


@pytest.mark.parametrize("pkg,floor_rationale", list(SECURITY_FLOOR.items()))
def test_installed_version_meets_security_floor(pkg: str, floor_rationale: tuple[str, str]) -> None:
    floor, rationale = floor_rationale
    try:
        actual = version(pkg)
    except PackageNotFoundError:
        pytest.fail(
            f"{pkg} is not installed but is required at >= {floor} "
            f"({rationale}). If you removed it intentionally, also remove it "
            f"from SECURITY_FLOOR in this file and add it to SECURITY_DENYLIST."
        )
    assert Version(actual) >= Version(floor), (
        f"SECURITY REGRESSION — {pkg}=={actual} is below the required minimum "
        f"{floor}. Reason: {rationale}. "
        f"Either upgrade {pkg} or (if unavoidable) open a security review."
    )


@pytest.mark.parametrize("pkg,reason", list(SECURITY_DENYLIST.items()))
def test_package_is_not_installed(pkg: str, reason: str) -> None:
    try:
        v = version(pkg)
    except PackageNotFoundError:
        return  # good — package is absent
    pytest.fail(
        f"SECURITY REGRESSION — {pkg}=={v} is installed but is on the "
        f"security denylist. Reason: {reason}. Remove it from "
        f"requirements.txt; we don't accept this package at any version."
    )


def test_python_runtime_is_supported() -> None:
    """Snyk reports flag Python 3.7 runtime. We run 3.11+ which means the
    upgraded dep versions are even applicable. Fail fast if anyone
    downgrades the interpreter (e.g., a docker rebase)."""
    import sys
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 11), (
        f"Python {major}.{minor} is below the minimum supported 3.11. "
        f"Several security-critical deps (cryptography 46, aiohttp 3.13) "
        f"require Python >= 3.9."
    )
