"""
Solomon AI — Demo Seed Data Functions
Re-exports all seed functions from sub-modules for backwards compatibility.
"""
from core.seed_commerce import ensure_demo_merch_data, ensure_demo_cafe_data
from core.seed_pathways import ensure_demo_meetings_data, ensure_abundant_pathways_data
from core.seed_accounts import (
    ensure_mobile_demo_accounts,
    ensure_abundant_mobile_demo_content,
    ensure_abundant_go_live_portal_content,
)

DEFAULT_NEXT_STEPS_URL = "https://abundantchurch.thinkific.com/courses/abundant-next-steps"
DEFAULT_MERCH_EMBED_URL = "https://store.elevationchurch.org/collections/so-be-it-ew"

__all__ = [
    "ensure_demo_merch_data",
    "ensure_demo_cafe_data",
    "ensure_demo_meetings_data",
    "ensure_abundant_pathways_data",
    "ensure_mobile_demo_accounts",
    "ensure_abundant_mobile_demo_content",
    "ensure_abundant_go_live_portal_content",
    "DEFAULT_NEXT_STEPS_URL",
    "DEFAULT_MERCH_EMBED_URL",
]
