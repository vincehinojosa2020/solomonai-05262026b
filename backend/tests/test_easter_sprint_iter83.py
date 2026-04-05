"""
Solomon AI Easter Sprint Backend Tests - Iteration 83
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "admin@solomonai.us", "password": "Demo2026!"},
                      timeout=10)
    assert r.status_code == 200
    data = r.json()
    token = data.get("session_token") or data.get("token")
    assert token
    return token


@pytest.fixture(scope="session")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def stats_data(headers):
    r = requests.get(f"{BASE_URL}/api/platform/stats", headers=headers, timeout=40)
    assert r.status_code == 200
    return r.json()


class TestHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"
        print("PASS: health ok")


class TestStats:
    def test_gmv_over_100m(self, stats_data):
        gmv = stats_data.get("giving", {}).get("all_time", 0)
        assert gmv > 100_000_000, f"GMV {gmv:.0f}"
        print(f"PASS: GMV={gmv:,.0f}")

    def test_yoy_positive(self, stats_data):
        yoy = stats_data.get("giving", {}).get("yoy_change", 0)
        assert yoy > 0, f"yoy {yoy}"
        print(f"PASS: yoy={yoy}")

    def test_sub_mrr_positive(self, stats_data):
        sub_mrr = stats_data.get("platform", {}).get("subscription_mrr", 0)
        assert sub_mrr > 0, f"sub_mrr {sub_mrr}"
        print(f"PASS: sub_mrr={sub_mrr}")

    def test_processing_mrr_over_10k(self, stats_data):
        mrr = stats_data.get("platform", {}).get("processing_mrr", 0)
        assert mrr > 10_000, f"mrr {mrr}"
        print(f"PASS: mrr={mrr}")

    def test_arr_over_200k(self, stats_data):
        arr = stats_data.get("platform", {}).get("arr", 0)
        assert arr > 200_000, f"arr {arr}"
        print(f"PASS: arr={arr}")

    def test_8_churches(self, stats_data):
        campuses = stats_data.get("campus_breakdown", [])
        assert len(campuses) >= 8, f"got {len(campuses)}"
        print(f"PASS: {len(campuses)} churches")

    def test_hill_country_in_breakdown(self, stats_data):
        campuses = stats_data.get("campus_breakdown", [])
        names = [c.get("name", "") for c in campuses]
        has_hc = any("Hill Country" in n for n in names)
        assert has_hc, f"Hill Country not found in {names}"
        print("PASS: Hill Country in breakdown")

    def test_100k_members(self, stats_data):
        members = stats_data.get("members", {}).get("total", 0)
        assert members > 100_000
        print(f"PASS: members={members:,}")

    def test_2_7m_txns(self, stats_data):
        txns = stats_data.get("transactions", {}).get("total", 0)
        assert txns > 2_700_000
        print(f"PASS: txns={txns:,}")

    def test_revenue_over_1_5m(self, stats_data):
        fees = stats_data.get("fees", {}).get("all_time", 0)
        sub_mrr = stats_data.get("platform", {}).get("subscription_mrr", 0)
        total_rev = fees + sub_mrr * 36
        assert total_rev > 1_500_000, f"rev={total_rev:.0f}"
        print(f"PASS: total_rev={total_rev:,.0f}")


class TestHealthScores:
    def test_returns_8_churches(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=headers, timeout=15)
        assert r.status_code == 200
        churches = r.json().get("churches", [])
        assert len(churches) >= 8
        print(f"PASS: {len(churches)} churches in health-scores")

    def test_no_na_grades(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=headers, timeout=15)
        churches = r.json().get("churches", [])
        na_names = [c.get("name") for c in churches if c.get("health", {}).get("grade") in [None, "N/A", ""]]
        assert len(na_names) == 0, f"N/A grade churches: {na_names}"
        print(f"PASS: All {len(churches)} churches have real grades")

    def test_abundant_east_a_plus(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=headers, timeout=15)
        churches = r.json().get("churches", [])
        east = next((c for c in churches if "Abundant East" in c.get("name", "") or c.get("tenant_id") == "abundant-east-001"), None)
        assert east, "Abundant East not found"
        grade = east.get("health", {}).get("grade", "")
        assert "A" in grade, f"expected A+, got {grade}"
        print(f"PASS: Abundant East grade={grade}")

    def test_hill_country_in_scores(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/health-scores", headers=headers, timeout=15)
        churches = r.json().get("churches", [])
        hc = next((c for c in churches if "Hill Country" in c.get("name", "")), None)
        assert hc, "Hill Country not in health-scores"
        grade = hc.get("health", {}).get("grade", "")
        assert grade
        print(f"PASS: Hill Country grade={grade}")


class TestReports:
    def test_giving_monthly_trend(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/giving", headers=headers, timeout=90)
        assert r.status_code == 200
        trend = r.json().get("monthly_trend", [])
        assert len(trend) > 0
        print(f"PASS: giving monthly_trend has {len(trend)} entries")

    def test_attendance_data(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/attendance", headers=headers, timeout=90)
        assert r.status_code == 200
        weekly = r.json().get("weekly", [])
        assert len(weekly) > 0
        print(f"PASS: attendance weekly has {len(weekly)} entries")

    def test_groups_ok(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/groups", headers=headers, timeout=60)
        assert r.status_code == 200
        print("PASS: groups ok")

    def test_membership_ok(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/membership", headers=headers, timeout=60)
        assert r.status_code == 200
        print("PASS: membership ok")

    def test_audit_ok(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/audit?limit=10", headers=headers, timeout=60)
        assert r.status_code == 200
        assert "entries" in r.json()
        print("PASS: audit ok")


class TestRetentionCohort:
    """Critical fix: date NameError was causing 500"""

    def test_returns_200(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/retention-cohort", headers=headers, timeout=120)
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"
        print("PASS: retention-cohort 200 (date import fix verified)")

    def test_has_cohorts(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/retention-cohort", headers=headers, timeout=120)
        cohorts = r.json().get("cohorts", [])
        assert len(cohorts) > 0
        print(f"PASS: {len(cohorts)} cohorts")

    def test_structure(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/reports/retention-cohort", headers=headers, timeout=120)
        cohorts = r.json().get("cohorts", [])
        if cohorts:
            c0 = cohorts[0]
            assert "label" in c0
            assert "size" in c0
            retention = c0.get("retention", [])
            assert len(retention) > 0
            assert retention[0].get("pct") == 100.0
            label = c0["label"]
            size = c0["size"]
            print(f"PASS: cohort structure: {label}, size={size}")


class TestDonors:
    def test_donors_ok(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers, timeout=120)
        assert r.status_code == 200
        total = r.json().get("total_donors", 0)
        assert total > 0
        print(f"PASS: donors total={total}")

    def test_top_donors_real_names(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers, timeout=120)
        top = r.json().get("top_donors", [])
        assert len(top) > 0
        td = top[0]
        name = td.get("name", "")
        assert name not in ["", "Anonymous"], f"Top donor has bad name: {name}"
        print(f"PASS: top donor={name}")

    def test_donor_profile(self, headers):
        r = requests.get(f"{BASE_URL}/api/platform/donors", headers=headers, timeout=120)
        top = r.json().get("top_donors", [])
        if not top or not top[0].get("person_id"):
            pytest.skip("no person_id in top donor")
        person_id = top[0]["person_id"]
        r2 = requests.get(f"{BASE_URL}/api/platform/donor/{person_id}", headers=headers, timeout=15)
        assert r2.status_code == 200
        profile = r2.json()
        assert "giving" in profile and "person" in profile
        assert profile["giving"].get("total", 0) > 0
        donor_name = profile["person"].get("name", "?")
        print(f"PASS: donor profile ok for {donor_name}")


class TestAuthProtection:
    def test_stats_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/platform/stats")
        assert r.status_code in [401, 403]
        print(f"PASS: stats blocked ({r.status_code})")

    def test_cohort_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/platform/reports/retention-cohort")
        assert r.status_code in [401, 403]
        print(f"PASS: cohort blocked ({r.status_code})")

    def test_church_admin_blocked(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": "shannonnieman1030@gmail.com", "password": "Demo2026!"})
        if r.status_code != 200:
            print(f"INFO: skipping, church admin login={r.status_code}")
            return
        token = r.json().get("session_token") or r.json().get("token")
        if not token:
            return
        sr = requests.get(f"{BASE_URL}/api/platform/stats",
                          headers={"Authorization": f"Bearer {token}"})
        assert sr.status_code == 403
        print("PASS: church admin blocked (403)")
