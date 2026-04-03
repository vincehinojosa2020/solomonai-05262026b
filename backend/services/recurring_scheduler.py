"""
Solomon Pay — Recurring Giving Background Scheduler
=====================================================
Runs on a configurable interval (default: every hour).
Processes all active recurring_giving records where next_charge_date <= today.
Idempotent: uses last_processed_date guard to prevent double-charging.
Retry logic: up to 3 attempts over 3 days; after 3 consecutive failures → pause.
Logs every run to recurring_giving_runs collection.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("solomonpay.scheduler")

# Run interval in seconds (3600 = 1 hour)
SCHEDULER_INTERVAL_SECONDS = 3600

# ─── Helper ───────────────────────────────────────────────────────────────────

def _calculate_next_charge_date(frequency: str, from_date: str) -> str:
    """Advance a charge date by one frequency period."""
    base = datetime.strptime(from_date, "%Y-%m-%d")
    if frequency == "weekly":
        nxt = base + timedelta(days=7)
    elif frequency == "biweekly":
        nxt = base + timedelta(days=14)
    elif frequency == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        day = min(base.day, 28)
        nxt = base.replace(year=year, month=month, day=day)
    elif frequency == "annually":
        nxt = base.replace(year=base.year + 1)
    else:
        nxt = base + timedelta(days=30)
    return nxt.strftime("%Y-%m-%d")


# ─── Core processor ───────────────────────────────────────────────────────────

async def _process_single_schedule(db, schedule: dict, today_str: str) -> dict:
    """
    Process one recurring giving schedule.
    Returns {"status": "success"|"failed"|"skipped", "message": str, "donation_id": Optional[str]}.
    """
    from services.processor_adapter import ACTIVE_ADAPTER, ChargeStatus

    sid = schedule.get("id", "unknown")

    # ── Idempotency guard ──
    if schedule.get("last_processed_date") == today_str:
        return {"status": "skipped", "message": "Already processed today", "donation_id": None}

    # ── Resolve payment token ──
    token = None
    pm_id = schedule.get("payment_method_id")
    if pm_id:
        pm = await db.payment_methods.find_one(
            {"id": pm_id, "is_active": True}, {"_id": 0}
        )
        if pm:
            token = pm.get("token") or pm.get("solomonpay_token", f"tok_recurring_{pm.get('card_last_four','0000')}")
    if not token:
        token = f"tok_recurring_auto_{uuid.uuid4().hex[:8]}"

    # ── Charge ──
    amount = schedule.get("amount", 0)
    amount_cents = int(round(amount * 100))
    method = schedule.get("payment_method_type", "card")
    tenant_id = schedule.get("tenant_id", "")
    description = f"Recurring {schedule.get('frequency','monthly')} gift to {schedule.get('fund_name','General Fund')}"

    try:
        if method == "ach":
            result = await ACTIVE_ADAPTER.charge_ach(
                token=token, amount_cents=amount_cents, description=description,
                metadata={"tenant_id": tenant_id, "schedule_id": sid, "recurring": True}
            )
        else:
            result = await ACTIVE_ADAPTER.charge_card(
                token=token, amount_cents=amount_cents, description=description,
                metadata={"tenant_id": tenant_id, "schedule_id": sid, "recurring": True}
            )

        if result.status == ChargeStatus.SUCCESS:
            # ── Record transaction + donation ──
            txn_id = f"sp_rec_{uuid.uuid4().hex[:12]}"
            fee_rate = 0.008 if method == "ach" else 0.019
            fee = round(amount * fee_rate + 0.30, 2)
            net = round(amount - fee, 2)

            await db.solomonpay_transactions.insert_one({
                "id": txn_id, "tenant_id": tenant_id,
                "type": "recurring_charge", "amount": amount,
                "fee_amount": fee, "net_amount": net,
                "status": "completed",
                "payment_method_type": method,
                "payment_method_last_four": result.card_last_four or "",
                "card_brand": result.card_brand or "",
                "donor_person_id": schedule.get("person_id"),
                "fund_id": schedule.get("fund_id"),
                "fund_name": schedule.get("fund_name", "General Fund"),
                "processor_reference_id": result.processor_reference_id,
                "recurring_schedule_id": sid,
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
            })

            donation_id = str(uuid.uuid4())
            await db.donations.insert_one({
                "id": donation_id, "tenant_id": tenant_id,
                "person_id": schedule.get("person_id"),
                "fund_id": schedule.get("fund_id"),
                "fund_name": schedule.get("fund_name", "General Fund"),
                "amount": amount, "donation_date": today_str,
                "payment_method": method, "is_recurring": True,
                "status": "completed", "source": "solomonpay_recurring",
                "fee_amount": fee, "net_amount": net,
                "transaction_id": txn_id,
                "recurring_schedule_id": sid,
                "created_at": datetime.now(timezone.utc),
            })

            # ── Advance next_charge_date ──
            next_date = _calculate_next_charge_date(
                schedule.get("frequency", "monthly"), today_str
            )
            await db.recurring_giving.update_one(
                {"id": sid},
                {"$set": {
                    "next_charge_date": next_date,
                    "last_processed_date": today_str,
                    "consecutive_failures": 0,
                    "last_transaction_id": txn_id,
                    "last_donation_id": donation_id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
            logger.info(f"[SCHEDULER] Processed schedule {sid}: ${amount:.2f} → {txn_id}")
            return {"status": "success", "message": result.message, "donation_id": donation_id}

        else:
            # Declined — treat as failure
            raise Exception(result.message)

    except Exception as exc:
        failures = (schedule.get("consecutive_failures") or 0) + 1
        update = {
            "consecutive_failures": failures,
            "last_failure_reason": str(exc),
            "last_failure_date": today_str,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if failures >= 3:
            update["is_active"] = False
            update["paused_reason"] = "auto_paused_3_failures"
            logger.warning(f"[SCHEDULER] Schedule {sid} auto-paused after {failures} failures")
        else:
            # Schedule retry for next day
            retry_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
            update["next_charge_date"] = retry_date
            logger.warning(f"[SCHEDULER] Schedule {sid} failed (attempt {failures}): {exc}. Retry: {retry_date}")

        await db.recurring_giving.update_one({"id": sid}, {"$set": update})
        return {"status": "failed", "message": str(exc), "donation_id": None}


# ─── Main batch runner ────────────────────────────────────────────────────────

async def run_recurring_batch(db) -> dict:
    """
    Execute one full batch run: find all due schedules and process them.
    Returns a run summary dict that gets stored in recurring_giving_runs.
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now(timezone.utc)
    today_str = started_at.strftime("%Y-%m-%d")

    logger.info(f"[SCHEDULER] Starting batch run {run_id} for {today_str}")

    # Find all active schedules due today or overdue
    due_schedules = await db.recurring_giving.find(
        {
            "is_active": True,
            "next_charge_date": {"$lte": today_str},
        },
        {"_id": 0}
    ).to_list(500)

    total = len(due_schedules)
    results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

    for schedule in due_schedules:
        try:
            outcome = await _process_single_schedule(db, schedule, today_str)
            if outcome["status"] == "success":
                results["success"] += 1
            elif outcome["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "schedule_id": schedule.get("id"),
                    "person_id": schedule.get("person_id"),
                    "amount": schedule.get("amount"),
                    "error": outcome["message"],
                })
        except Exception as exc:
            results["failed"] += 1
            results["errors"].append({
                "schedule_id": schedule.get("id"),
                "error": str(exc),
            })
            logger.error(f"[SCHEDULER] Unexpected error for schedule {schedule.get('id')}: {exc}")

    finished_at = datetime.now(timezone.utc)
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)

    run_doc = {
        "id": run_id,
        "run_date": today_str,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": duration_ms,
        "total_scheduled": total,
        "successful": results["success"],
        "failed": results["failed"],
        "skipped": results["skipped"],
        "errors": results["errors"][:50],  # cap stored errors
        "status": "completed",
    }
    await db.recurring_giving_runs.insert_one(run_doc)
    logger.info(
        f"[SCHEDULER] Run {run_id} complete: "
        f"{results['success']} success, {results['failed']} failed, "
        f"{results['skipped']} skipped out of {total} due in {duration_ms}ms"
    )
    return run_doc


# ─── Continuous loop ──────────────────────────────────────────────────────────

_scheduler_task: Optional[asyncio.Task] = None


async def _scheduler_loop(db):
    """Runs run_recurring_batch every SCHEDULER_INTERVAL_SECONDS."""
    logger.info(f"[SCHEDULER] Starting — interval: {SCHEDULER_INTERVAL_SECONDS}s")
    while True:
        try:
            await run_recurring_batch(db)
        except Exception as exc:
            logger.error(f"[SCHEDULER] Batch run crashed: {exc}")
        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


def start_scheduler(db):
    """Start the recurring giving scheduler as a background asyncio task."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        logger.info("[SCHEDULER] Already running, skipping start")
        return
    _scheduler_task = asyncio.create_task(_scheduler_loop(db))
    logger.info("[SCHEDULER] Recurring giving scheduler started")


def stop_scheduler():
    """Cancel the background scheduler task (called on shutdown)."""
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        logger.info("[SCHEDULER] Recurring giving scheduler stopped")
