"""
Sprint #9 — Observability & Backups (BLOCKER #9)
================================================
Verifies:
  * /api/health (shallow, deep, launch-check)
  * X-Request-ID echo
  * JSON structured logging
  * PII sweep on auth login (no email f-string in log line)
  * Sentry skipped when SENTRY_DSN empty (no boot errors)
  * Stripe webhook bad-signature still 400
  * No regressions on /api/auth/login, /api/platform/stats,
    /api/portal/me, /api/portal/giving/history, /api/stripe/create-payment-intent
  * backup.sh runs cleanly with --target /tmp/solomon-bak --retain-days 7
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
ADMIN = ("admin@solomonai.us", os.environ.get("TEST_PASSWORD", "Demo2026!"))
MEMBER = ("member@abundant.church", os.environ.get("TEST_PASSWORD", "Demo2026!"))


# ─────────────────────────────────────────────────────────── fixtures
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": ADMIN[0], "password": ADMIN[1]})
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token") or r.json().get("session_token")


@pytest.fixture(scope="module")
def member_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": MEMBER[0], "password": MEMBER[1]})
    if r.status_code != 200:
        pytest.skip(f"member login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token") or r.json().get("session_token")


# ────────────────────────────────────────────────── 1. health endpoints
class TestHealthEndpoints:
    def test_shallow_health(self, session):
        r = session.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "ok"
        assert "version" in d
        assert "uptime_s" in d
        assert isinstance(d["uptime_s"], (int, float))

    def test_deep_health(self, session):
        r = session.get(f"{BASE_URL}/api/health?deep=true")
        assert r.status_code in (200, 503), r.text
        d = r.json()
        assert "checks" in d
        assert "mongo" in d["checks"]
        assert "latency_ms" in d["checks"]["mongo"] or d["checks"]["mongo"]["status"] == "down"
        assert "sentry" in d["checks"]
        assert d["checks"]["sentry"]["status"] in ("configured", "disabled")
        assert "environment" in d

    def test_launch_check(self, session):
        r = session.get(f"{BASE_URL}/api/health/launch-check")
        assert r.status_code == 200
        d = r.json()
        assert d == {"status": "ok", "service": "solomon-ai"}


# ────────────────────────────────────────────── 2. correlation id header
class TestCorrelationId:
    def test_unique_request_id_echoed(self, session):
        r1 = session.get(f"{BASE_URL}/api/health")
        r2 = session.get(f"{BASE_URL}/api/health")
        cid1 = r1.headers.get("X-Request-ID") or r1.headers.get("x-request-id")
        cid2 = r2.headers.get("X-Request-ID") or r2.headers.get("x-request-id")
        assert cid1 and cid2, f"Missing X-Request-ID: {dict(r1.headers)}"
        assert cid1 != cid2, "Request IDs should be unique per request"

    def test_request_id_propagated_when_supplied(self, session):
        my_id = f"test-{uuid.uuid4().hex[:8]}"
        r = session.get(f"{BASE_URL}/api/health", headers={"X-Request-ID": my_id})
        echoed = r.headers.get("X-Request-ID") or r.headers.get("x-request-id")
        assert echoed == my_id, f"expected {my_id} echoed, got {echoed}"


# ────────────────────────────────────────────── 3. auth flows
class TestAuth:
    def test_admin_login_success(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": ADMIN[0], "password": ADMIN[1]})
        assert r.status_code == 200, r.text
        d = r.json()
        # token field varies; either "token" or "session_token"
        assert d.get("token") or d.get("session_token"), d

    def test_member_login_success(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": MEMBER[0], "password": MEMBER[1]})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("token") or d.get("session_token"), d

    def test_invalid_login_returns_401_no_500(self, session):
        bogus_email = f"TEST_invalid_iter109_{uuid.uuid4().hex[:6]}@example.com"
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": bogus_email, "password": "wrong"})
        assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"
        body = r.json()
        # Error message must NOT echo the input email back
        body_str = json.dumps(body).lower()
        assert bogus_email.lower() not in body_str, "Error response leaks input email"


# ────────────────────────────────────────────── 4. PII log sweep verification
class TestPiiLogSweep:
    """Trigger an invalid login then scan backend logs for PII leak."""

    def _read_logs(self) -> str:
        # Supervisor log location
        candidates = [
            "/var/log/supervisor/backend.err.log",
            "/var/log/supervisor/backend.out.log",
        ]
        out = ""
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, "rb") as f:
                        f.seek(0, 2)
                        size = f.tell()
                        f.seek(max(0, size - 200_000))
                        out += f.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
        return out

    def test_failed_login_log_redacts_email(self, session):
        unique_email = f"TEST_piiscan_iter109_{uuid.uuid4().hex[:8]}@solomon-pii-probe.test"
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": unique_email, "password": "wrongpass"})
        assert r.status_code == 401
        time.sleep(0.6)  # let log flush
        logs = self._read_logs()
        # Email should NOT appear verbatim in logs (PII filter scrubs it).
        # Even if logging code uses extras (no f-string), the redaction
        # filter must still scrub any accidental leak.
        assert unique_email not in logs, (
            f"PII LEAK: unique email `{unique_email}` found verbatim in backend logs"
        )

    def test_logs_are_json_structured(self, session):
        # Hit any endpoint to generate a log line
        session.get(f"{BASE_URL}/api/health")
        time.sleep(0.4)
        logs = self._read_logs()
        # find at least one JSON line that has the expected keys
        json_lines = []
        for line in logs.splitlines()[-300:]:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            json_lines.append(obj)
        assert json_lines, "no JSON-formatted log lines found in last 300 lines"
        # at least one record should expose the structured keys
        keys_seen = set()
        for o in json_lines:
            keys_seen.update(o.keys())
        # required structured keys (timestamp + level + logger + message)
        for k in ("timestamp", "level", "logger", "message"):
            assert k in keys_seen, f"missing structured key {k} in any log; saw {keys_seen}"

    def test_auth_login_failed_event_present_without_email(self, session):
        unique_email = f"TEST_evtprobe_iter109_{uuid.uuid4().hex[:8]}@solomon-pii-probe.test"
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": unique_email, "password": "wrongpass"})
        assert r.status_code == 401
        time.sleep(0.6)
        logs = self._read_logs()
        # Look for the structured event name
        assert "auth_login_failed" in logs, "structured 'auth_login_failed' event missing in logs"
        # And the unique email should not appear
        assert unique_email not in logs


# ────────────────────────────────────────────── 5. Sentry skipped on empty DSN
class TestSentryDisabled:
    def test_sentry_disabled_in_deep_health(self, session):
        # SENTRY_DSN is empty in /app/backend/.env
        r = session.get(f"{BASE_URL}/api/health?deep=true")
        assert r.status_code == 200
        d = r.json()
        assert d["checks"]["sentry"]["status"] == "disabled"

    def test_backend_boots_clean(self, session):
        # if backend is responding 200 to health, no boot error happened
        r = session.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200


# ────────────────────────────────────────────── 6. Stripe webhook bad sig
class TestStripeWebhookSignature:
    def test_bad_signature_rejected(self, session):
        # Webhook secret is configured, so bad sig must 400
        r = session.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=b'{"id":"evt_test_iter109_badsig","type":"ping"}',
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1,v1=bogus",
            },
        )
        # 400 expected; sometimes server returns 401 if no sig
        assert r.status_code in (400, 401), f"got {r.status_code}: {r.text[:200]}"


# ────────────────────────────────────────────── 7. regression — business endpoints
class TestRegression:
    def test_platform_stats(self, session, admin_token):
        r = session.get(f"{BASE_URL}/api/platform/stats",
                        headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d, dict)

    def test_portal_me(self, session, member_token):
        r = session.get(f"{BASE_URL}/api/portal/me",
                        headers={"Authorization": f"Bearer {member_token}"})
        assert r.status_code == 200, r.text
        d = r.json()
        # Should contain a user-ish payload
        assert "email" in d or "user" in d or "user_id" in d, d

    def test_portal_giving_history(self, session, member_token):
        r = session.get(f"{BASE_URL}/api/portal/giving/history",
                        headers={"Authorization": f"Bearer {member_token}"})
        # 200 OK or empty list — must not be 5xx
        assert r.status_code < 500, r.text

    def test_create_payment_intent_no_500(self, session):
        # Anonymous PI create against demo tenant — must NOT 5xx;
        # acceptable codes: 200 (intent created), 400 (validation),
        # 403 (gate), 404 (no tenant). We just want NO regressions.
        body = {
            "amount": 25.00,
            "donor_email": f"TEST_pi_iter109_{uuid.uuid4().hex[:6]}@example.com",
            "donor_name": "Sprint9 Test",
            "fund_id": "general",
            "church_slug": "abundant-church",
            "cover_fees": False,
        }
        r = session.post(f"{BASE_URL}/api/stripe/create-payment-intent", json=body)
        assert r.status_code < 500, f"5xx regression on PI create: {r.status_code} {r.text[:300]}"


# ────────────────────────────────────────────── 8. backup.sh smoke
class TestBackupScript:
    def test_backup_runs(self):
        script = Path("/app/backend/scripts/backup.sh")
        if not script.exists():
            pytest.skip("backup.sh missing")
        if subprocess.run(["which", "mongodump"], capture_output=True).returncode != 0:
            pytest.skip("mongodump not installed")
        target = "/tmp/solomon-bak"
        os.makedirs(target, exist_ok=True)
        proc = subprocess.run(
            ["bash", str(script), "--target", target, "--retain-days", "7"],
            capture_output=True, text=True, timeout=120,
        )
        assert proc.returncode == 0, (
            f"backup.sh failed: rc={proc.returncode}\nSTDOUT:{proc.stdout[-1500:]}\n"
            f"STDERR:{proc.stderr[-1500:]}"
        )
        # Verify a .gz/.archive artifact landed in target
        artifacts = []
        for root, _, files in os.walk(target):
            for fn in files:
                artifacts.append(os.path.join(root, fn))
        assert artifacts, f"no backup artifacts created in {target}"
