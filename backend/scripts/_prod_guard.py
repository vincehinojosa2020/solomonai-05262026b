"""Centralized production-mode guard for all seed/maintenance scripts.

BLOCKER #6 from production audit (2026-04-28).

Usage:
    from scripts._prod_guard import refuse_in_production
    refuse_in_production(__file__)

Behavior:
    * If ENVIRONMENT=production and I_KNOW_WHAT_IM_DOING != "yes": raises SystemExit.
    * Otherwise: returns silently.
"""
from __future__ import annotations

import os
import sys


def refuse_in_production(script_path: str = "<unknown>") -> None:
    if os.environ.get("ENVIRONMENT", "").lower() != "production":
        return
    if os.environ.get("I_KNOW_WHAT_IM_DOING") == "yes":
        sys.stderr.write(
            f"[prod_guard] {script_path} running against ENVIRONMENT=production "
            f"with I_KNOW_WHAT_IM_DOING=yes — proceeding.\n"
        )
        return
    raise SystemExit(
        f"Refusing to run {script_path} against ENVIRONMENT=production. "
        f"This script writes demo/seed data. Set I_KNOW_WHAT_IM_DOING=yes "
        f"only if you have a written reason and a backup."
    )
