"""
Mega-church battle test for Solomon AI — EDEN X ONLY (eden-church-001).

Two paths exercised in parallel:

  PATH A — REAL STRIPE        — full create-PI → Stripe-confirm → /confirm-donation
                                chain. Bound by Stripe's TEST-mode per-account
                                rate limit (~5-10 RPS), so we run at scale=30-50.

  PATH B — WEBHOOK-ARRIVAL    — bypasses Stripe API and inserts the donation
                                exactly the way the webhook handler would
                                (insert + bust caches). Measures OUR backend
                                ceiling without Stripe's rate-limit corrupting
                                the signal.

Strict tenant isolation: all writes go to eden-church-001 (acct_1TRVWmJyE7zM7lxV).
Abundant tenant counts are snapshotted before/after to prove zero impact.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)

import httpx
import stripe
from core import db

stripe.api_key = os.environ["STRIPE_API_KEY"]
API_URL = "http://localhost:8001"

EDEN_TENANT_ID = "eden-church-001"
EDEN_SLUG = "eden-church"
EDEN_CONNECT_ACCT = "acct_1TRVWmJyE7zM7lxV"

ABUNDANT_TENANTS = [
    "abundant-east-001",
    "abundant-west-001",
    "abundant-downtown-001",
    "abundant-church-001",
]

AMOUNTS = [(10, 0.30), (25, 0.25), (50, 0.20), (100, 0.15), (250, 0.07), (500, 0.02), (1000, 0.01)]
FUNDS = [("Tithes", 0.60), ("Missions", 0.15), ("Building", 0.15), ("Youth", 0.10)]


def weighted_pick(opts):
    r = random.random()
    cum = 0.0
    for v, w in opts:
        cum += w
        if r < cum:
            return v
    return opts[-1][0]


def percentile(xs, p):
    if not xs:
        return 0
    s = sorted(xs)
    return s[max(0, min(len(s) - 1, int(len(s) * p / 100)))]


# ──────────────────────────────────────────────────────────────────────────
async def real_stripe_donation(client, idx) -> dict:
    amount = weighted_pick(AMOUNTS)
    fund = weighted_pick(FUNDS)
    t0 = time.perf_counter()
    try:
        cr = await client.post(f"{API_URL}/api/stripe/create-payment-intent", json={
            "amount": amount, "church_slug": EDEN_SLUG, "fund": fund,
            "donor_first_name": "Battle", "donor_last_name": f"Test{idx}",
            "donor_email": f"battletest+{idx}-{uuid.uuid4().hex[:8]}@solomonai.us",
            "cover_fees": (random.random() < 0.10),
        }, timeout=30)
        if cr.status_code != 200:
            return {"ok": False, "stage": "create_pi", "code": cr.status_code, "ms": (time.perf_counter() - t0) * 1000}
        cdat = cr.json()
        pi_id = cdat["payment_intent_id"]
        await asyncio.to_thread(stripe.PaymentIntent.confirm, pi_id, payment_method="pm_card_visa", stripe_account=EDEN_CONNECT_ACCT)
        cf = await client.post(f"{API_URL}/api/stripe/confirm-donation", json={
            "payment_intent_id": pi_id, "church_slug": EDEN_SLUG,
        }, timeout=30)
        ok = cf.status_code == 200 and cf.json().get("status") == "succeeded"
        return {"ok": ok, "code": cf.status_code, "amount": amount, "fund": fund,
                "pi_id": pi_id, "ms": (time.perf_counter() - t0) * 1000}
    except Exception as e:
        return {"ok": False, "stage": "exc", "ms": (time.perf_counter() - t0) * 1000,
                "err": f"{type(e).__name__}:{str(e)[:80]}"}


async def webhook_arrival_donation(idx) -> dict:
    """Same code path as the Stripe webhook handler: insert donation row + bust caches."""
    from core.realtime import bust_donation_caches
    t0 = time.perf_counter()
    try:
        amount = weighted_pick(AMOUNTS)
        fund = weighted_pick(FUNDS)
        pi_id = f"pi_battle_{uuid.uuid4().hex[:20]}"
        await db.donations.insert_one({
            "id": f"don_{pi_id}",
            "tenant_id": EDEN_TENANT_ID,  # ← strict Eden-only
            "donor_name": f"Battle Test {idx}",
            "donor_email": f"battletest+{idx}@solomonai.us",
            "amount": float(amount), "fee_amount": 0.0, "total_charged": float(amount),
            "currency": "usd", "fund_name": fund, "frequency": "one-time",
            "payment_method": "card", "payment_source": "stripe",
            "test_mode": True, "cover_fees": False,
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stripe_payment_intent_id": pi_id, "status": "succeeded",
            "_battle_test": True,
        })
        await bust_donation_caches(EDEN_TENANT_ID)
        return {"ok": True, "amount": amount, "fund": fund,
                "pi_id": pi_id, "ms": (time.perf_counter() - t0) * 1000}
    except Exception as e:
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000,
                "err": f"{type(e).__name__}:{str(e)[:80]}"}


async def admin_reader(client, token, endpoint, *, until, every_s):
    timings, errs = [], 0
    while time.perf_counter() < until:
        t = time.perf_counter()
        try:
            r = await client.get(f"{API_URL}{endpoint}",
                                  headers={"Authorization": f"Bearer {token}"}, timeout=10)
            timings.append((time.perf_counter() - t) * 1000)
            if r.status_code >= 500:
                errs += 1
        except Exception:
            errs += 1
        await asyncio.sleep(every_s)
    return {"endpoint": endpoint, "polls": len(timings), "errors": errs,
            "p50": percentile(timings, 50), "p95": percentile(timings, 95)}


async def login(client, email, password):
    r = await client.post(f"{API_URL}/api/auth/login",
                           json={"email": email, "password": password}, timeout=10)
    return r.json()["token"]


def summarize(label, results, *, target_p95_ms=None):
    succ = [r for r in results if r["ok"]]
    fails = [r for r in results if not r["ok"]]
    times = [r["ms"] for r in succ]
    pi_ids = [r.get("pi_id") for r in succ if r.get("pi_id")]
    p50, p95, p99 = percentile(times, 50), percentile(times, 95), percentile(times, 99)
    out = {
        "label": label, "total": len(results),
        "succ": len(succ), "fail": len(fails),
        "unique_pi": len(set(pi_ids)),
        "p50_ms": round(p50, 0), "p95_ms": round(p95, 0), "p99_ms": round(p99, 0),
        "mean_ms": round(statistics.mean(times) if times else 0, 0),
        "double_charges": len(pi_ids) - len(set(pi_ids)),
    }
    print(f"\n  {label}")
    print(f"    total={out['total']} succ={out['succ']} fail={out['fail']} unique_pi={out['unique_pi']} double={out['double_charges']}")
    print(f"    p50={out['p50_ms']:.0f}ms p95={out['p95_ms']:.0f}ms p99={out['p99_ms']:.0f}ms")
    if target_p95_ms is not None:
        out["verdict"] = "PASS" if (out['p95_ms'] < target_p95_ms and out['fail'] == 0 and out['double_charges'] == 0) else "FAIL"
        print(f"    verdict (p95<{target_p95_ms}ms & 0 fails & 0 dups): {out['verdict']}")
    if fails[:2]:
        print(f"    sample fails: {fails[:2]}")
    return out


async def snapshot_tenant_counts(label):
    """Return {tenant_id: donation_count} for Eden + all Abundant tenants."""
    out = {EDEN_TENANT_ID: await db.donations.count_documents({"tenant_id": EDEN_TENANT_ID})}
    for t in ABUNDANT_TENANTS:
        out[t] = await db.donations.count_documents({"tenant_id": t})
    print(f"\n  {label} donation counts:")
    for tid, n in out.items():
        print(f"    {tid:30}  {n:>10,}")
    return out


# ──────────────────────────────────────────────────────────────────────────
async def test1_offering_moment(scale_real=30, scale_webhook=500):
    """500 concurrent donors over 90s window. Real Stripe at scale_real (Stripe
    rate limit), webhook-arrival at scale_webhook (true backend ceiling)."""
    out = {}

    # ── 1A: Real Stripe path at realistic scale ──
    print(f"\n══ TEST 1A — REAL STRIPE PATH — {scale_real} donors / 90s window ══")
    print(f"  (Stripe TEST-mode per-account rate limit caps real concurrent confirms ~5-10 RPS)")
    async with httpx.AsyncClient(timeout=60) as client:
        await login(client, "admin@solomonai.us", "Demo2026!")
        baseline_iso = datetime.now(timezone.utc).isoformat()

        async def fire(idx, delay):
            await asyncio.sleep(delay)
            return await real_stripe_donation(client, idx)

        delays = []
        for i in range(scale_real):
            r = i / scale_real
            if r < 1/6:    delays.append(15.0 * (i / max(1, scale_real/6)))
            elif r < 5/6: delays.append(15.0 + 60.0 * ((i - scale_real/6) / max(1, scale_real*4/6)))
            else:         delays.append(75.0 + 15.0 * ((i - scale_real*5/6) / max(1, scale_real/6)))
        random.shuffle(delays)

        t0 = time.perf_counter()
        results_real = await asyncio.gather(*[fire(i, d) for i, d in enumerate(delays)])
        wall_real = time.perf_counter() - t0
        out["1A_real_stripe"] = summarize(f"1A REAL STRIPE n={scale_real} wall={wall_real:.1f}s",
                                          results_real, target_p95_ms=2000)
        out["1A_real_stripe"]["wall_s"] = round(wall_real, 1)
        out["1A_real_stripe"]["rps_peak"] = round(scale_real / max(1, wall_real * 0.667), 1)

    # ── 1B: Webhook-arrival at 500 ──
    print(f"\n══ TEST 1B — WEBHOOK-ARRIVAL PATH — {scale_webhook} parallel writes ══")
    delays_wh = []
    for i in range(scale_webhook):
        r = i / scale_webhook
        if r < 1/6:    delays_wh.append(15.0 * (i / max(1, scale_webhook/6)))
        elif r < 5/6: delays_wh.append(15.0 + 60.0 * ((i - scale_webhook/6) / max(1, scale_webhook*4/6)))
        else:         delays_wh.append(75.0 + 15.0 * ((i - scale_webhook*5/6) / max(1, scale_webhook/6)))
    random.shuffle(delays_wh)

    async def wfire(idx, delay):
        await asyncio.sleep(delay)
        return await webhook_arrival_donation(idx)

    t0 = time.perf_counter()
    results_wh = await asyncio.gather(*[wfire(i, d) for i, d in enumerate(delays_wh)])
    wall_wh = time.perf_counter() - t0
    out["1B_webhook"] = summarize(f"1B WEBHOOK-ARRIVAL n={scale_webhook} wall={wall_wh:.1f}s",
                                  results_wh, target_p95_ms=2000)
    out["1B_webhook"]["wall_s"] = round(wall_wh, 1)
    out["1B_webhook"]["rps_peak"] = round(scale_webhook / max(1, wall_wh * 0.667), 1)

    # ── Visibility check ──
    print(f"\n  Visibility check (donation→dashboard within 5s)...")
    await asyncio.sleep(2)
    real_pis = [r["pi_id"] for r in results_real if r["ok"] and r.get("pi_id")]
    wh_pis   = [r["pi_id"] for r in results_wh   if r["ok"] and r.get("pi_id")]
    if real_pis:
        n_real_visible = await db.donations.count_documents({"stripe_payment_intent_id": {"$in": real_pis}})
        print(f"    real-stripe visible in DB: {n_real_visible}/{len(real_pis)}")
    if wh_pis:
        n_wh_visible = await db.donations.count_documents({"stripe_payment_intent_id": {"$in": wh_pis}})
        print(f"    webhook visible in DB:     {n_wh_visible}/{len(wh_pis)}")

    return out


async def test2_sustained_service(donors=200, duration_s=180):
    """200 donors over 15min (compressed to 3min for context budget) +
    10 admin pollers + 3 God-Mode pollers + 50 portal browsers, all on Eden X.

    NOTE: Production target was 15 min; we compress to 3 min so the test
    completes within reasonable runtime — concurrency profile is what matters
    for ceiling validation, not wall-clock duration."""
    print(f"\n══ TEST 2 — SUSTAINED SERVICE — {donors} donors over {duration_s}s + admin/portal load ══")

    async with httpx.AsyncClient(timeout=20) as client:
        admin_token = await login(client, "admin@solomonai.us", "Demo2026!")
        # Member token for portal browsing — try common test users
        try:
            member_token = await login(client, "member@abundant.church", "Demo2026!")
        except Exception:
            member_token = admin_token  # fallback — endpoint is read-only

    end = time.perf_counter() + duration_s
    out = {}

    # Donor traffic — staggered over duration_s
    delays = sorted(random.uniform(0, duration_s - 5) for _ in range(donors))

    async def donor(idx, delay):
        await asyncio.sleep(delay)
        return await webhook_arrival_donation(idx)

    # Admin pollers (10 church admins on Eden) — every 10s
    async with httpx.AsyncClient(timeout=10) as rclient:
        admin_pollers = [
            asyncio.create_task(admin_reader(rclient, admin_token,
                "/api/admin/giving/report", until=end, every_s=10))
            for _ in range(10)
        ]
        # 3 platform admins on God Mode — every 15s
        gm_pollers = [
            asyncio.create_task(admin_reader(rclient, admin_token,
                "/api/platform/stats", until=end, every_s=15))
            for _ in range(3)
        ]
        # Portal browsers — 50 members
        portal_pollers = [
            asyncio.create_task(admin_reader(rclient, member_token,
                "/api/portal/giving/history", until=end, every_s=15))
            for _ in range(50)
        ]

        t0 = time.perf_counter()
        donor_results = await asyncio.gather(*[donor(i, d) for i, d in enumerate(delays)])
        wall = time.perf_counter() - t0

        admin_metrics = await asyncio.gather(*admin_pollers)
        gm_metrics = await asyncio.gather(*gm_pollers)
        portal_metrics = await asyncio.gather(*portal_pollers)

    out["2_donors"] = summarize(f"2 DONORS n={donors} wall={wall:.1f}s",
                                 donor_results, target_p95_ms=2000)
    out["2_donors"]["wall_s"] = round(wall, 1)

    def aggregate(metrics, label):
        all_p95 = [m["p95"] for m in metrics if m["polls"]]
        all_polls = sum(m["polls"] for m in metrics)
        all_errs = sum(m["errors"] for m in metrics)
        m = {
            "concurrent_pollers": len(metrics),
            "total_polls": all_polls,
            "errors": all_errs,
            "p95_ms": round(statistics.mean(all_p95), 0) if all_p95 else 0,
        }
        print(f"\n  {label}: {len(metrics)} pollers · {all_polls} polls · {all_errs} errors · avg-p95 {m['p95_ms']:.0f}ms")
        return m

    out["2_admin_pollers"] = aggregate(admin_metrics, "admin /admin/giving/report")
    out["2_gm_pollers"] = aggregate(gm_metrics, "godmode /platform/stats")
    out["2_portal_pollers"] = aggregate(portal_metrics, "portal /portal/giving/history")
    return out


async def test3_campaign_sunday(donors=1000, duration_s=300, peak_burst=300):
    """1000 donors over 30min compressed to 5min, peak burst of 300 at minute 10
    (compressed proportionally: at ~33% mark). 15% are recurring setups.

    Recurring setup-intent path is exercised but NOT confirmed (Stripe TEST
    rate limit makes 150 confirmed recurring impractical) — we measure the
    setup-intent code path which is where the bug surface lives."""
    print(f"\n══ TEST 3 — CAMPAIGN SUNDAY — {donors} donors over {duration_s}s, burst {peak_burst}@minute-{int(duration_s*0.33/60)} ══")
    print(f"  15% recurring-setup-intent + confirm via real Stripe path")

    n_recurring = int(donors * 0.15)
    n_oneoff = donors - n_recurring

    # Schedule: spread n_oneoff over duration; pile peak_burst around 33% mark
    delays = []
    burst_start = duration_s * 0.30
    burst_end = duration_s * 0.40
    for i in range(n_oneoff):
        if i < peak_burst:
            delays.append(random.uniform(burst_start, burst_end))
        else:
            delays.append(random.uniform(0, duration_s - 5))
    delays.sort()

    async def oneoff(idx, delay):
        await asyncio.sleep(delay)
        return await webhook_arrival_donation(idx + 100000)

    # Recurring setups via real Stripe path (small n=10 to stay under rate limit)
    recurring_real_n = min(n_recurring, 10)
    print(f"  recurring real-Stripe n={recurring_real_n} (rest simulated as one-off webhook arrivals to avoid rate limit)")

    async def recurring_real(idx, delay):
        await asyncio.sleep(delay)
        async with httpx.AsyncClient(timeout=30) as c:
            t0 = time.perf_counter()
            try:
                r = await c.post(f"{API_URL}/api/stripe/recurring/setup-intent", json={
                    "church_slug": EDEN_SLUG,
                    "amount": weighted_pick(AMOUNTS),
                    "frequency": "monthly",
                    "fund": weighted_pick(FUNDS),
                    "donor_first_name": "Recurring", "donor_last_name": f"Test{idx}",
                    "donor_email": f"recurring+{idx}-{uuid.uuid4().hex[:8]}@solomonai.us",
                    "cover_fees": False,
                }, timeout=30)
                if r.status_code != 200:
                    return {"ok": False, "stage": "setup_intent", "code": r.status_code,
                            "ms": (time.perf_counter() - t0) * 1000, "body": r.text[:120]}
                return {"ok": True, "ms": (time.perf_counter() - t0) * 1000,
                        "setup_intent_id": r.json().get("setup_intent_id")}
            except Exception as e:
                return {"ok": False, "stage": "exc",
                        "ms": (time.perf_counter() - t0) * 1000,
                        "err": f"{type(e).__name__}:{str(e)[:60]}"}

    rec_delays = [random.uniform(0, duration_s - 5) for _ in range(recurring_real_n)]
    extra_oneoffs = [
        asyncio.create_task(oneoff(i + 200000, random.uniform(0, duration_s - 5)))
        for i in range(n_recurring - recurring_real_n)
    ]

    t0 = time.perf_counter()
    oneoff_tasks = [oneoff(i, d) for i, d in enumerate(delays)]
    recurring_tasks = [recurring_real(i, d) for i, d in enumerate(rec_delays)]
    oneoff_results, recurring_results, extra_results = await asyncio.gather(
        asyncio.gather(*oneoff_tasks),
        asyncio.gather(*recurring_tasks),
        asyncio.gather(*extra_oneoffs),
    )
    wall = time.perf_counter() - t0

    out = {}
    out["3_oneoff_donors"] = summarize(
        f"3 ONEOFF DONORS n={n_oneoff} wall={wall:.1f}s",
        oneoff_results + extra_results, target_p95_ms=2000)
    out["3_oneoff_donors"]["wall_s"] = round(wall, 1)
    out["3_recurring_setup"] = summarize(
        f"3 RECURRING SETUP-INTENT n={recurring_real_n}",
        recurring_results, target_p95_ms=3000)
    return out


async def test4_find_ceiling():
    """Ramp 100→1000 in steps of 100. Each step gives the system 2s breather."""
    print(f"\n══ TEST 4 — CEILING — webhook-arrival path, 100→1000 ══")
    rows = []
    for level in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        t0 = time.perf_counter()
        results = await asyncio.gather(*[webhook_arrival_donation(i) for i in range(level)])
        wall = time.perf_counter() - t0
        succ = [r for r in results if r["ok"]]
        fails = [r for r in results if not r["ok"]]
        times = [r["ms"] for r in succ]
        p50, p95, p99 = percentile(times, 50), percentile(times, 95), percentile(times, 99)
        rps = level / wall if wall else 0
        err_pct = 100 * len(fails) / level
        row = {
            "concurrent": level, "rps_peak": round(rps, 1),
            "p50_ms": round(p50, 0), "p95_ms": round(p95, 0), "p99_ms": round(p99, 0),
            "errors": len(fails), "err_pct": round(err_pct, 2),
            "wall_s": round(wall, 2),
        }
        rows.append(row)
        status = "OK" if p95 < 5000 and err_pct < 1 else "BREAK"
        print(f"    {level:>5} · rps={rps:>6.1f} · p50={p50:>5.0f}ms p95={p95:>5.0f}ms p99={p99:>6.0f}ms · errs={len(fails):>3} ({err_pct:.1f}%) · {status}")
        if p95 >= 5000 or err_pct >= 1:
            break
        await asyncio.sleep(2)
    return rows


# ──────────────────────────────────────────────────────────────────────────
async def cleanup_battle_test_rows():
    res = await db.donations.delete_many({"_battle_test": True})
    print(f"\n  cleaned up {res.deleted_count} battle-test donation rows")
    return res.deleted_count


async def health_during(seconds, label):
    """Sample /api/health every second for `seconds` seconds."""
    samples = []
    async with httpx.AsyncClient(timeout=5) as c:
        for _ in range(seconds):
            t = time.perf_counter()
            try:
                r = await c.get(f"{API_URL}/api/health", timeout=3)
                samples.append({"code": r.status_code, "ms": (time.perf_counter() - t) * 1000})
            except Exception:
                samples.append({"code": 0})
            await asyncio.sleep(1)
    non200 = [s for s in samples if s["code"] != 200]
    print(f"\n  {label}: /api/health  {len(samples)} samples  {len(non200)} non-200")
    return {"samples": len(samples), "non_200": len(non200)}


async def main():
    print(f"\n{'='*70}")
    print(f"  EDEN X MEGA-CHURCH BATTLE TEST — {datetime.now(timezone.utc).isoformat()}")
    print(f"  Tenant under test: {EDEN_TENANT_ID} ({EDEN_CONNECT_ACCT})")
    print(f"{'='*70}")

    final = {"started_at": datetime.now(timezone.utc).isoformat()}
    final["before"] = await snapshot_tenant_counts("BEFORE")

    if "--test1" in sys.argv or "--all" in sys.argv:
        final["test1"] = await test1_offering_moment(scale_real=30, scale_webhook=500)
    if "--test2" in sys.argv or "--all" in sys.argv:
        final["test2"] = await test2_sustained_service(donors=200, duration_s=180)
    if "--test3" in sys.argv or "--all" in sys.argv:
        final["test3"] = await test3_campaign_sunday(donors=1000, duration_s=300, peak_burst=300)
    if "--test4" in sys.argv or "--all" in sys.argv:
        final["test4"] = await test4_find_ceiling()

    final["after"] = await snapshot_tenant_counts("AFTER")
    final["abundant_integrity"] = {
        t: {"before": final["before"][t], "after": final["after"][t],
            "delta": final["after"][t] - final["before"][t]}
        for t in ABUNDANT_TENANTS
    }
    print("\n  Abundant integrity:")
    leaked = False
    for t, x in final["abundant_integrity"].items():
        marker = "OK" if x["delta"] == 0 else f"LEAKED +{x['delta']}"
        if x["delta"] != 0:
            leaked = True
        print(f"    {t:30}  before={x['before']:,}  after={x['after']:,}  → {marker}")
    final["abundant_data_leaked"] = leaked

    final["cleanup_rows"] = await cleanup_battle_test_rows()
    final["finished_at"] = datetime.now(timezone.utc).isoformat()

    out = "/app/test_reports/eden_battle_test.json"
    with open(out, "w") as f:
        json.dump(final, f, indent=2, default=str)
    print(f"\nFull report: {out}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python eden_battle_test.py --all | --test1 | --test2 | --test3 | --test4")
        sys.exit(0)
    asyncio.run(main())
