"""Sprint 10 — Real-time visibility verification + 50-concurrent load test.

Uses Stripe's reserved `pm_card_visa` test PaymentMethod so the PI actually
moves to status=succeeded and the donation row gets inserted. This exercises
the FULL write path: create-PI → server-side confirm → /api/stripe/confirm-donation
→ db.donations insert → cache bust → visible in /api/realtime/donations.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)

import stripe
import httpx

stripe.api_key = os.environ["STRIPE_API_KEY"]
API_URL = "http://localhost:8001"
SLUG = "abundant-east"

print(f"API: {API_URL}  slug: {SLUG}")


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    r = await client.post(f"{API_URL}/api/auth/login", json={"email": email, "password": password})
    return r.json()["token"]


async def realtime_tail(client: httpx.AsyncClient, token: str, since_iso: str) -> dict:
    r = await client.get(f"{API_URL}/api/realtime/donations?since={since_iso}",
                         headers={"Authorization": f"Bearer {token}"})
    return r.json() if r.status_code == 200 else {}


async def make_full_donation(client: httpx.AsyncClient, idx: int, amount: float):
    """Create-PI → server-confirm with pm_card_visa → confirm-donation."""
    t0 = time.perf_counter()
    try:
        # 1. Create PI via our API. Vary email to avoid idempotency dedup.
        cr = await client.post(f"{API_URL}/api/stripe/create-payment-intent", json={
            "amount": amount, "church_slug": SLUG, "fund": "Tithes",
            "donor_first_name": "Load", "donor_last_name": f"Test{idx}",
            "donor_email": f"loadtest+{idx}-{int(time.time())}@solomonai.us",
        })
        if cr.status_code != 200:
            return {"ok": False, "stage": "create_pi", "code": cr.status_code, "ms": (time.perf_counter()-t0)*1000, "body": cr.text[:200]}
        cdat = cr.json()
        pi_id = cdat["payment_intent_id"]
        acct = cdat["connected_account_id"]
        t_after_pi = time.perf_counter()

        # 2. Server-side Stripe confirm with reserved test PM. Block on threadpool.
        await asyncio.to_thread(
            stripe.PaymentIntent.confirm, pi_id,
            payment_method="pm_card_visa", stripe_account=acct,
        )
        t_after_stripe = time.perf_counter()

        # 3. Confirm-donation via our API → inserts db.donations row
        confirm = await client.post(f"{API_URL}/api/stripe/confirm-donation", json={
            "payment_intent_id": pi_id, "church_slug": SLUG,
        })
        ok = confirm.status_code == 200 and confirm.json().get("status") == "succeeded"
        return {
            "ok": ok, "code": confirm.status_code,
            "ms": (time.perf_counter() - t0) * 1000,
            "ms_create_pi": (t_after_pi - t0) * 1000,
            "ms_stripe_confirm": (t_after_stripe - t_after_pi) * 1000,
            "ms_donation_confirm": (time.perf_counter() - t_after_stripe) * 1000,
            "pi_id": pi_id,
        }
    except Exception as e:
        return {"ok": False, "stage": "exception", "ms": (time.perf_counter()-t0)*1000, "err": f"{type(e).__name__}: {str(e)[:120]}"}


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        print("\n=== STEP 1: Login ===")
        token = await login(client, "admin@solomonai.us", "Demo2026!")
        print(f"  ok: {token[:18]}...")

        baseline_iso = datetime.now(timezone.utc).isoformat()

        print("\n=== STEP 2: Single E2E donation w/ pm_card_visa ===")
        r = await make_full_donation(client, idx=0, amount=1.00)
        print(f"  total: {r['ms']:.0f}ms  ok={r['ok']}")
        if r["ok"]:
            print(f"    create-PI:        {r['ms_create_pi']:.0f}ms")
            print(f"    stripe confirm:   {r['ms_stripe_confirm']:.0f}ms")
            print(f"    confirm-donation: {r['ms_donation_confirm']:.0f}ms")
            pi_id = r["pi_id"]
            # Time to visible in realtime tail
            visible_in = None
            vstart = time.perf_counter()
            for _ in range(20):
                await asyncio.sleep(0.15)
                tail = await realtime_tail(client, token, baseline_iso)
                if any(d.get("stripe_payment_intent_id") == pi_id for d in tail.get("donations", [])):
                    visible_in = time.perf_counter() - vstart
                    break
            print(f"  visible in realtime tail: {(visible_in*1000):.0f}ms" if visible_in else "  NOT VISIBLE in 3s")
            print(f"  TOTAL confirm→visible: {(visible_in*1000):.0f}ms" if visible_in else "")
        else:
            print(f"  FAIL: {r}")
            return

        # Audit: also check /admin/giving/report shows it (cache bust verification)
        ar = await client.get(f"{API_URL}/api/admin/giving/report", headers={"Authorization": f"Bearer {token}"})
        gd = ar.json()
        # find pi_id in recent
        rows = gd.get("recent_donations", [])
        in_report = any(d.get("stripe_payment_intent_id") == pi_id for d in rows[:50])
        print(f"  visible in /admin/giving/report: {'YES' if in_report else 'no (might be paginated past 50)'}")

        print("\n=== STEP 3: 50 concurrent E2E donations (load test) ===")
        # Vary amount widely so idempotency_key differs per request
        burst_start = time.perf_counter()
        results = await asyncio.gather(*[make_full_donation(client, i, 0.50 + i * 0.10) for i in range(50)], return_exceptions=False)
        burst = time.perf_counter() - burst_start

        succ = [r for r in results if r["ok"]]
        fails = [r for r in results if not r["ok"]]
        succ_times = sorted([r["ms"] for r in succ])

        if succ_times:
            p50 = succ_times[len(succ_times)//2]
            p95 = succ_times[max(0, int(len(succ_times)*0.95)-1)]
            p99 = succ_times[-1]
        else:
            p50 = p95 = p99 = 0

        print(f"  wall: {burst:.2f}s  success: {len(succ)}/50  fail: {len(fails)}")
        print(f"  p50={p50:.0f}ms  p95={p95:.0f}ms  p99={p99:.0f}ms")
        if fails:
            print(f"  first fail: {fails[0]}")

        pi_ids = [r.get("pi_id") for r in succ]
        print(f"  unique PI ids: {len(set(pi_ids))} / created {len(pi_ids)}  → {'OK' if len(set(pi_ids))==len(pi_ids) else 'DEDUP (idempotency working — params identical)'}")

        # Wait for any async webhook to settle, then verify visibility
        await asyncio.sleep(2)
        final_tail = await realtime_tail(client, token, baseline_iso)
        seen_pi = set(d.get("stripe_payment_intent_id") for d in final_tail.get("donations", []) if d.get("stripe_payment_intent_id"))
        matched = sum(1 for pid in pi_ids if pid in seen_pi)
        print(f"  donations in realtime tail: {matched}/{len(succ)}  ({100*matched/max(1,len(succ)):.0f}%)")

        # Average time to visibility for last few
        print("\n=== STEP 4: Launch status snapshot (post-burst) ===")
        r = await client.get(f"{API_URL}/api/health/launch-status", headers={"Authorization": f"Bearer {token}"})
        ls = r.json()
        print(f"  overall: {ls.get('overall')}")
        print(f"  mongo: {ls['checks']['mongo']['status']} ({ls['checks']['mongo']['latency_ms']}ms)")
        print(f"  webhooks: 1h={ls['checks']['stripe_webhooks']['received_last_hour']}, stale={ls['checks']['stripe_webhooks']['stale_unprocessed']}")
        print(f"  donations: 1h={ls['donations']['last_hour']}, last_min={ls['donations']['last_minute']}")
        print(f"  last donation: ${ls['donations']['last_amount']} at {ls['donations']['last_at']}")


if __name__ == "__main__":
    asyncio.run(main())
