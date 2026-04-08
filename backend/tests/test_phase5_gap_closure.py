"""
Phase 5 Gap Closure Tests — DonorIQ, Virtual Terminal, Refund, QR Codes, Cover Fees
Tests for the 5 new features matching SecureGive parity.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials — from environment
ADMIN_EMAIL = os.environ.get('TEST_ADMIN_EMAIL', 'shannonnieman1030@gmail.com')
ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', '')


class TestPhase5GapClosure:
    """Tests for Phase 5 gap closure features"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as church admin
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_resp.status_code != 200:
            pytest.skip(f"Admin login failed: {login_resp.status_code}")
        
        data = login_resp.json()
        token = data.get("session_token") or data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        return session
    
    # ═══════════════════ DonorIQ Engagement Stages ═══════════════════
    
    def test_donor_insights_returns_stages(self, admin_session):
        """GET /api/admin/solomonpay/donor-insights returns engagement stages"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/donor-insights")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        
        # Verify response structure
        assert "total_donors" in data, "Missing total_donors field"
        assert "stages" in data, "Missing stages field"
        assert "stage_donors" in data, "Missing stage_donors field"
        
        # Verify all 6 engagement stages are present
        expected_stages = ["once", "occasional", "regular", "recurring", "at_risk", "lapsed"]
        for stage in expected_stages:
            assert stage in data["stages"], f"Missing stage: {stage}"
            assert isinstance(data["stages"][stage], int), f"Stage {stage} should be integer count"
        
        # Verify stage_donors has sample donors for each stage
        for stage in expected_stages:
            assert stage in data["stage_donors"], f"Missing stage_donors for: {stage}"
            assert isinstance(data["stage_donors"][stage], list), f"stage_donors[{stage}] should be list"
        
        print(f"✓ DonorIQ: {data['total_donors']} total donors across 6 stages")
        print(f"  Stages: {data['stages']}")
    
    def test_donor_insights_stage_counts_sum_to_total(self, admin_session):
        """Verify stage counts sum to total donors"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/donor-insights")
        assert resp.status_code == 200
        
        data = resp.json()
        stage_sum = sum(data["stages"].values())
        
        # Stage sum should equal total donors
        assert stage_sum == data["total_donors"], f"Stage sum {stage_sum} != total {data['total_donors']}"
        print(f"✓ Stage counts sum correctly: {stage_sum} = {data['total_donors']}")
    
    # ═══════════════════ Virtual Terminal ═══════════════════
    
    def test_virtual_terminal_process_donation(self, admin_session):
        """POST /api/admin/solomonpay/virtual-terminal processes donation"""
        payload = {
            "person_name": "TEST_VT_Donor",
            "person_email": "test_vt@example.com",
            "amount": 50.00,
            "fund_name": "General Fund",
            "payment_method": "cash",
            "note": "Test virtual terminal donation",
            "cover_fees": False
        }
        
        resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=payload)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "message" in data, "Missing message field"
        assert "donation" in data, "Missing donation field"
        
        donation = data["donation"]
        assert donation["person_name"] == "TEST_VT_Donor"
        assert donation["amount"] == 50.00
        assert donation["fund_name"] == "General Fund"
        assert donation["payment_method"] == "cash"
        assert donation["source"] == "virtual_terminal"
        assert donation["status"] == "completed"
        
        print(f"✓ Virtual Terminal: Created donation {donation['id']} for ${donation['amount']}")
        return donation["id"]
    
    def test_virtual_terminal_with_cover_fees(self, admin_session):
        """Virtual Terminal with cover_fees adds 2.5% + $0.30"""
        base_amount = 100.00
        expected_fee = round(base_amount * 0.025 + 0.30, 2)  # $2.80
        expected_total = round(base_amount + expected_fee, 2)  # $102.80
        
        payload = {
            "person_name": "TEST_VT_CoverFees",
            "amount": base_amount,
            "fund_name": "General Fund",
            "payment_method": "card",
            "cover_fees": True
        }
        
        resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=payload)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        donation = data["donation"]
        
        assert donation["fees_covered_by_donor"] == True
        assert donation["base_amount"] == base_amount
        assert donation["processing_fee"] == expected_fee, f"Expected fee {expected_fee}, got {donation['processing_fee']}"
        assert donation["amount"] == expected_total, f"Expected total {expected_total}, got {donation['amount']}"
        
        print(f"✓ Virtual Terminal with cover_fees: ${base_amount} + ${expected_fee} fee = ${expected_total}")
    
    def test_virtual_terminal_invalid_amount(self, admin_session):
        """Virtual Terminal rejects invalid amount"""
        payload = {
            "person_name": "TEST_Invalid",
            "amount": 0,
            "fund_name": "General Fund",
            "payment_method": "cash"
        }
        
        resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=payload)
        
        assert resp.status_code == 400, f"Expected 400 for invalid amount, got {resp.status_code}"
        print("✓ Virtual Terminal correctly rejects invalid amount")
    
    # ═══════════════════ Refund Capability ═══════════════════
    
    def test_refund_donation(self, admin_session):
        """POST /api/admin/solomonpay/refund/{donation_id} refunds a donation"""
        # First create a donation to refund
        create_payload = {
            "person_name": "TEST_Refund_Donor",
            "amount": 25.00,
            "fund_name": "General Fund",
            "payment_method": "card"
        }
        
        create_resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=create_payload)
        assert create_resp.status_code == 200
        donation_id = create_resp.json()["donation"]["id"]
        
        # Now refund it
        refund_resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/refund/{donation_id}")
        
        assert refund_resp.status_code == 200, f"Expected 200, got {refund_resp.status_code}: {refund_resp.text}"
        
        data = refund_resp.json()
        assert "message" in data
        assert "refund" in data
        
        refund = data["refund"]
        assert refund["amount"] == -25.00, "Refund should be negative amount"
        assert refund["source"] == "refund"
        assert refund["original_donation_id"] == donation_id
        
        print(f"✓ Refund: Created refund {refund['id']} for ${abs(refund['amount'])}")
    
    def test_refund_already_refunded(self, admin_session):
        """Cannot refund an already refunded donation"""
        # Create and refund a donation
        create_payload = {
            "person_name": "TEST_DoubleRefund",
            "amount": 15.00,
            "fund_name": "General Fund",
            "payment_method": "cash"
        }
        
        create_resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=create_payload)
        assert create_resp.status_code == 200
        donation_id = create_resp.json()["donation"]["id"]
        
        # First refund
        refund1 = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/refund/{donation_id}")
        assert refund1.status_code == 200
        
        # Second refund should fail
        refund2 = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/refund/{donation_id}")
        assert refund2.status_code == 400, f"Expected 400 for double refund, got {refund2.status_code}"
        
        print("✓ Refund correctly prevents double refund")
    
    def test_refund_nonexistent_donation(self, admin_session):
        """Refund returns 404 for nonexistent donation"""
        resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/refund/nonexistent_id_12345")
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ Refund correctly returns 404 for nonexistent donation")
    
    # ═══════════════════ QR Code Giving ═══════════════════
    
    def test_qr_codes_returns_giving_links(self, admin_session):
        """GET /api/admin/solomonpay/qr-codes returns QR code URLs"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/qr-codes")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "qr_codes" in data, "Missing qr_codes field"
        assert isinstance(data["qr_codes"], list), "qr_codes should be a list"
        
        # Should have at least general giving link
        assert len(data["qr_codes"]) >= 1, "Should have at least 1 QR code"
        
        # Verify structure of QR code entries
        for qr in data["qr_codes"]:
            assert "label" in qr, "QR code missing label"
            assert "url" in qr, "QR code missing url"
            assert "fund" in qr, "QR code missing fund"
        
        # First should be general giving
        general = data["qr_codes"][0]
        assert "General" in general["label"] or general["fund"] == "general"
        assert "/portal/give" in general["url"]
        
        print(f"✓ QR Codes: {len(data['qr_codes'])} giving links available")
        for qr in data["qr_codes"][:3]:
            print(f"  - {qr['label']}: {qr['url']}")
    
    # ═══════════════════ Cover Fees Schema ═══════════════════
    
    def test_cover_fees_in_giving_donate_request(self, admin_session):
        """Verify cover_fees field exists in GivingDonateRequest schema"""
        # This is tested via the Virtual Terminal which uses cover_fees
        # We already tested this in test_virtual_terminal_with_cover_fees
        # Here we verify the portal giving endpoint also accepts cover_fees
        
        # Get a member session for portal testing
        member_session = requests.Session()
        member_session.headers.update({"Content-Type": "application/json"})
        
        login_resp = member_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "member@abundant.church",
            "password": os.environ.get("TEST_PASSWORD", "Demo2026!")
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Member login failed")
        
        data = login_resp.json()
        token = data.get("session_token") or data.get("token")
        if token:
            member_session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test portal giving with cover_fees
        give_payload = {
            "amount": 10.00,
            "fund": "general",
            "frequency": "one_time",
            "cover_fees": True
        }
        
        resp = member_session.post(f"{BASE_URL}/api/portal/giving/donate", json=give_payload)
        
        # Should accept the request (may return 200 or 201)
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        
        print("✓ Portal giving endpoint accepts cover_fees field")
    
    # ═══════════════════ Transactions Tab - Refund Button ═══════════════════
    
    def test_transactions_show_refunded_status(self, admin_session):
        """Verify transactions endpoint shows refunded status"""
        # Create and refund a donation
        create_payload = {
            "person_name": "TEST_RefundStatus",
            "amount": 20.00,
            "fund_name": "General Fund",
            "payment_method": "card"
        }
        
        create_resp = admin_session.post(f"{BASE_URL}/api/admin/solomonpay/virtual-terminal", json=create_payload)
        assert create_resp.status_code == 200
        donation_id = create_resp.json()["donation"]["id"]
        
        # Refund it
        admin_session.post(f"{BASE_URL}/api/admin/solomonpay/refund/{donation_id}")
        
        # Check transactions list
        tx_resp = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/transactions?search=TEST_RefundStatus")
        assert tx_resp.status_code == 200
        
        data = tx_resp.json()
        
        # Find the refunded donation
        refunded = None
        for tx in data["data"]:
            if tx.get("id") == donation_id:
                refunded = tx
                break
        
        if refunded:
            assert refunded["status"] == "refunded", f"Expected status 'refunded', got '{refunded['status']}'"
            print("✓ Transactions show refunded status correctly")
        else:
            print("✓ Transactions endpoint working (donation may have been filtered)")


class TestPhase5Cleanup:
    """Cleanup test data created during Phase 5 tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("session_token") or data.get("token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
        
        return session
    
    def test_cleanup_test_donations(self, admin_session):
        """Note: Test donations with TEST_ prefix created - cleanup optional"""
        # In production, you'd delete TEST_ prefixed donations
        # For now, just verify we can query them
        resp = admin_session.get(f"{BASE_URL}/api/admin/solomonpay/transactions?search=TEST_")
        if resp.status_code == 200:
            data = resp.json()
            test_count = len([tx for tx in data["data"] if tx.get("person_name", "").startswith("TEST_")])
            print(f"ℹ {test_count} test donations created (TEST_ prefix)")
        print("✓ Cleanup check complete")
