"""
Eden X — TRUE-CEILING RAMP TEST (preview backend, webhook-arrival path).

Methodology
-----------
* Path: webhook-arrival (insert donation + bust cache) — same code Stripe's
  webhook handler runs. Bypasses Stripe API rate limits so we measure OUR
  application ceiling, not Stripe's throttle.
* Tenant: eden-church-001 ONLY. Every row tagged `_battle_test:true`.
* Ramp: 1K → 2K → 3K → 5K → 7.5K → 10K → 15K → 20K → 25K → 30K
* Stop conditions: error% > 5  OR  p95 > 10,000 ms
* Sustain at the highest passing level for 120 s (rolling waves).
* Recovery: 100 normal-rate calls — verify p95 returns to baseline.
* Health probe: hammered every 1 s throughout via HTTP — records pass rate.
* Mongo + asyncio constraints will surface naturally; that's the *real* ceiling
  of the application code from this single load-gen pod.

Output: prints a markdown ramp table + writes JSON to /app/test_reports/.
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)

import httpx
from core import db
from core.realtime import bust_donation_caches

EDEN_TENANT_ID = "eden-church-001"
LOCAL_API = "http://localhost:8001"

LEVELS = [1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000, 25000, 30000]


def pct(xs, p):
    if not xs:
        return 0
    s = sorted(xs)
    return s[max(0, min(len(s) - 1, int(len(s) * p / 100)))]


async def webhook_donation(idx: int) -> dict:
    """Match the production webhook handler exactly: insert + bust caches."""
    t0 = time.perf_counter()
    try:
        amount = 25 + (idx % 7) * 25  # 25, 50, 75, 100, 125, 150, 175
        pi_id = f"pi_ramp_{uuid.uuid4().hex[:20]}"
        await db.donations.insert_one({
            "id": f"don_{pi_id}",
            "tenant_id": EDEN_TENANT_ID,
            "donor_name": f"Ramp Test {idx}",
            "donor_email": f"ramp+{idx}@solomonai.us",
            "amount": float(amount),
            "fee_amount": 0.0,
            "total_charged": float(amount),
            "currency": "usd",
            "fund_name": "Tithes",
            "frequency": "one-time",
            "payment_method": "card",
            "payment_source": "stripe",
            "test_mode": True,
            "cover_fees": False,
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stripe_payment_intent_id": pi_id,
            "status": "succeeded",
            "_battle_test": True,
            "_ramp_test": True,
        })
        await bust_donation_caches(EDEN_TENANT_ID)
        return {"ok": True, "pi_id": pi_id, "ms": (time.perf_counter() - t0) * 1000}
    except Exception as e:
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000,
                "err": f"{type(e).__name__}:{str(e)[:120]}"}


async def health_watcher(stop_evt: asyncio.Event) -> dict:
    """Hammer /api/health every 1s. Record pass rate + max latency."""
    timings = []
    fails = 0
    async with httpx.AsyncClient(timeout=5.0) as client:
        while not stop_evt.is_set():
            t = time.perf_counter()
            try:
                r = await client.get(f"{LOCAL_API}/api/health")
                if r.status_code != 200:
                    fails += 1
                else:
                    timings.append((time.perf_counter() - t) * 1000)
            except Exception:
                fails += 1
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
    return {
        "polls": len(timings) + fails,
        "fails": fails,
        "p50": pct(timings, 50),
        "p95": pct(timings, 95),
        "max": max(timings) if timings else 0,
    }


async def run_level(n: int) -> dict:
    """Fire N concurrent webhook donations via asyncio.gather."""
    t0 = time.perf_counter()
    results = await asyncio.gather(*[webhook_donation(i) for i in range(n)],
                                    return_exceptions=False)
    elapsed = time.perf_counter() - t0
    succ = [r for r in results if r.get("ok")]
    fails = [r for r in results if not r.get("ok")]
    times = [r["ms"] for r in succ]
    err_types = {}
    for f in fails:
        e = f.get("err", "Unknown").split(":", 1)[0]
        err_types[e] = err_types.get(e, 0) + 1
    return {
        "n": n,
        "rps": round(n / elapsed, 1) if elapsed > 0 else 0,
        "elapsed_s": round(elapsed, 2),
        "succ": len(succ),
        "fail": len(fails),
        "err_pct": round(100 * len(fails) / n, 2) if n else 0,
        "p50": round(pct(times, 50), 1),
        "p95": round(pct(times, 95), 1),
        "p99": round(pct(times, 99), 1),
        "max": round(max(times), 1) if times else 0,
        "err_types": err_types,
    }


async def sustain_test(rps: int, duration_s: int) -> dict:
    """Sustain `rps` writes/sec for `duration_s` via rolling waves."""
    end = time.perf_counter() + duration_s
    all_results = []
    wave = 0
    while time.perf_counter() < end:
        wt = time.perf_counter()
        results = await asyncio.gather(*[webhook_donation(100_000 + wave * rps + i)
                                         for i in range(rps)])
        all_results.extend(results)
        wave += 1
        # sleep remainder of the 1s wave window
        slp = 1.0 - (time.perf_counter() - wt)
        if slp > 0:
            await asyncio.sleep(slp)
    succ = [r for r in all_results if r.get("ok")]
    fails = [r for r in all_results if not r.get("ok")]
    times = [r["ms"] for r in succ]
    return {
        "duration_s": duration_s,
        "target_rps": rps,
        "total": len(all_results),
        "succ": len(succ),
        "fail": len(fails),
        "actual_rps": round(len(all_results) / duration_s, 1),
        "p50": round(pct(times, 50), 1),
        "p95": round(pct(times, 95), 1),
        "p99": round(pct(times, 99), 1),
    }


async def recovery_test(n: int = 100) -> dict:
    """Sequential calls — measure if latency normalises after the storm."""
    times = []
    fails = 0
    for i in range(n):
        r = await webhook_donation(900_000 + i)
        if r["ok"]:
            times.append(r["ms"])
        else:
            fails += 1
    return {
        "n": n,
        "succ": len(times),
        "fail": fails,
        "p50": round(pct(times, 50), 1),
        "p95": round(pct(times, 95), 1),
        "max": round(max(times), 1) if times else 0,
    }


async def cleanup() -> int:
    res = await db.donations.delete_many({"_ramp_test": True})
    return res.deleted_count


async def integrity_check() -> dict:
    rows = await db.donations.count_documents({"_ramp_test": True})
    pi_ids = await db.donations.distinct("stripe_payment_intent_id", {"_ramp_test": True})
    return {
        "ramp_rows_in_db": rows,
        "unique_pis": len(pi_ids),
        "duplicates": rows - len(pi_ids),
    }


async def main():
    print("=" * 80)
    print("EDEN X — TRUE CEILING RAMP TEST (preview, webhook-arrival)")
    print("=" * 80)

    stop_evt = asyncio.Event()
    health_task = asyncio.create_task(health_watcher(stop_evt))

    levels_data = []
    breaking_point = None
    last_passing = None

    for level in LEVELS:
        print(f"\n▶ Level: {level:>6} concurrent ...", flush=True)
        try:
            r = await run_level(level)
        except Exception as e:
            print(f"   level crashed: {type(e).__name__}: {e}")
            breaking_point = {"level": level, "reason": f"crashed: {e}"}
            break

        status = "PASS"
        if r["err_pct"] > 5:
            status = "FAIL (err%)"
        elif r["p95"] > 10000:
            status = "FAIL (p95)"

        r["status"] = status
        levels_data.append(r)
        print(f"   RPS={r['rps']:>7} p50={r['p50']:>6}ms p95={r['p95']:>7}ms "
              f"p99={r['p99']:>7}ms err={r['err_pct']}% [{status}]", flush=True)
        if r.get("err_types"):
            print(f"   err_types: {r['err_types']}", flush=True)

        if status != "PASS":
            breaking_point = {"level": level, "reason": status, "metrics": r}
            break
        last_passing = level
        # 5 s cool-down between levels
        await asyncio.sleep(5)

    # Sustain at peak
    sustain = None
    if last_passing and not breaking_point:
        print(f"\n▶ Sustain test: {last_passing} writes/sec for 120 s ...", flush=True)
        sustain = await sustain_test(last_passing, 120)
        print(f"   total={sustain['total']} actual_rps={sustain['actual_rps']} "
              f"p50={sustain['p50']}ms p95={sustain['p95']}ms err={sustain['fail']}",
              flush=True)
    elif last_passing:
        print(f"\n▶ Sustain test at last passing level ({last_passing}) for 60 s ...", flush=True)
        sustain = await sustain_test(last_passing, 60)
        print(f"   total={sustain['total']} actual_rps={sustain['actual_rps']} "
              f"p50={sustain['p50']}ms p95={sustain['p95']}ms err={sustain['fail']}",
              flush=True)

    # Recovery
    print("\n▶ Recovery test (100 sequential calls) ...", flush=True)
    recovery = await recovery_test(100)
    print(f"   p50={recovery['p50']}ms p95={recovery['p95']}ms max={recovery['max']}ms "
          f"fail={recovery['fail']}", flush=True)

    # Stop health watcher
    stop_evt.set()
    health = await health_task
    print(f"\n▶ Health probe: {health['polls']} polls, {health['fails']} fails, "
          f"p50={health['p50']}ms p95={health['p95']}ms max={health['max']}ms",
          flush=True)

    # Integrity + cleanup
    integrity = await integrity_check()
    print(f"\n▶ Integrity: rows={integrity['ramp_rows_in_db']} "
          f"unique_pis={integrity['unique_pis']} duplicates={integrity['duplicates']}",
          flush=True)

    deleted = await cleanup()
    print(f"\n▶ Cleanup: deleted {deleted} ramp-test rows", flush=True)

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ramp": levels_data,
        "breaking_point": breaking_point,
        "last_passing_level": last_passing,
        "sustain": sustain,
        "recovery": recovery,
        "health_during_test": health,
        "integrity": integrity,
        "rows_cleaned": deleted,
    }

    out_path = f"/app/test_reports/eden_ramp_test_{int(time.time())}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n📄 Full report: {out_path}")

    # Markdown table
    print("\n" + "=" * 80)
    print("RAMP RESULTS")
    print("=" * 80)
    print(f"| {'Concurrent':>10} | {'RPS':>7} | {'p50 ms':>7} | {'p95 ms':>8} | "
          f"{'p99 ms':>8} | {'Errors':>6} | {'Err %':>6} | Status      |")
    print("|" + "-" * 12 + "|" + "-" * 9 + "|" + "-" * 9 + "|" + "-" * 10 + "|"
          + "-" * 10 + "|" + "-" * 8 + "|" + "-" * 8 + "|-------------|")
    for r in levels_data:
        print(f"| {r['n']:>10,} | {r['rps']:>7} | {r['p50']:>7} | {r['p95']:>8} | "
              f"{r['p99']:>8} | {r['fail']:>6} | {r['err_pct']:>6} | {r['status']:<11} |")

    if breaking_point:
        print(f"\n🔥 Breaking point: {breaking_point['level']:,} concurrent — "
              f"{breaking_point['reason']}")
    else:
        print(f"\n✅ Never broke up to {LEVELS[-1]:,} concurrent (single-pod ceiling).")
    if last_passing:
        print(f"\n📣 ONE-LINER: \"Solomon AI handles {last_passing:,} concurrent donors "
              f"at p95={[r['p95'] for r in levels_data if r['n']==last_passing][0]} ms with "
              f"{[r['err_pct'] for r in levels_data if r['n']==last_passing][0]}% error rate.\"")


if __name__ == "__main__":
    asyncio.run(main())
