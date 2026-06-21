"""
test_auth_flow.py

Manual end-to-end test for the complete authentication flow.

Run from the backend/ directory AFTER:
  1. pip install httpx
  2. uvicorn app.main:app --reload   (in another terminal)
  3. Seed data applied (psql -f ../database/seed.sql)

Usage:
  python test_auth_flow.py

Expected output: All tests PASSED
"""

import asyncio
import json
import sys

try:
    import httpx
except ImportError:
    print("ERROR: Run  pip install httpx  first.")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000/api/v1"

ADMIN_USER     = {"username": "admin",     "password": "Admin@1234"}
EMPLOYEE_USER  = {"username": "ahmed_ali", "password": "Employee@1234"}

# Colours for terminal output
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}");  sys.exit(1)
def step(msg):  print(f"\n{BOLD}{YELLOW}▶ {msg}{RESET}")
def info(msg):  print(f"    {msg}")


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:

        # ─────────────────────────────────────────────────────────────────────
        step("1. Health check")
        r = await c.get("http://127.0.0.1:8000/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        ok("Server is running")

        # ─────────────────────────────────────────────────────────────────────
        step("2. Admin login")
        r = await c.post("/auth/login", json=ADMIN_USER)
        assert r.status_code == 200, f"Admin login failed: {r.text}"
        data = r.json()["data"]

        admin_token = data["access_token"]
        assert admin_token, "No access_token in response"
        assert data["refresh_token"], "No refresh_token in response"
        assert data["user"]["role"] == "ADMIN"
        assert data["requires_section_selection"] is False, "Admin should not need section selection"
        assert len(data["available_sections"]) > 0, "Admin should see all sections"
        ok(f"Admin logged in — role: {data['user']['role']}")
        info(f"Available sections: {[s['name'] for s in data['available_sections']]}")

        # ─────────────────────────────────────────────────────────────────────
        step("3. Admin /auth/me")
        r = await c.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200, f"/me failed: {r.text}"
        me = r.json()["data"]
        assert me["role"] == "ADMIN"
        assert me["requires_section_selection"] is False
        ok(f"/me returned: {me['username']} ({me['role']})")

        # ─────────────────────────────────────────────────────────────────────
        step("4. Admin selects a section (optional)")
        section_id = data["available_sections"][0]["id"]
        r = await c.post(
            "/auth/select-section",
            json={"section_id": section_id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, f"Select section failed: {r.text}"
        sel = r.json()["data"]
        assert "access_token" in sel
        assert sel["permission_level"] == "ADMIN"
        ok(f"Admin selected section: {sel['section']['name']} (perm: {sel['permission_level']})")

        # ─────────────────────────────────────────────────────────────────────
        step("5. Employee login")
        r = await c.post("/auth/login", json=EMPLOYEE_USER)
        assert r.status_code == 200, f"Employee login failed: {r.text}"
        emp_data = r.json()["data"]

        emp_token = emp_data["access_token"]
        emp_refresh = emp_data["refresh_token"]
        assert emp_data["user"]["role"] == "EMPLOYEE"
        assert emp_data["requires_section_selection"] is True, "Employee should need section selection"
        ok(f"Employee logged in — role: {emp_data['user']['role']}")
        info(f"Sections available to employee: {[s['name'] for s in emp_data['available_sections']]}")

        # ─────────────────────────────────────────────────────────────────────
        step("6. Employee tries to access warehouse without section selection")
        r = await c.get("/warehouse/items", headers={"Authorization": f"Bearer {emp_token}"})
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
        ok(f"Got 403 as expected — '{r.json()['message']}'")

        # ─────────────────────────────────────────────────────────────────────
        step("7. Employee selects section")
        assert len(emp_data["available_sections"]) > 0, "Employee has no section assignments!"
        emp_section_id = emp_data["available_sections"][0]["id"]
        emp_section_name = emp_data["available_sections"][0]["name"]

        r = await c.post(
            "/auth/select-section",
            json={"section_id": emp_section_id},
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert r.status_code == 200, f"Employee section select failed: {r.text}"
        sel = r.json()["data"]
        assert "access_token" in sel
        emp_section_token = sel["access_token"]
        ok(f"Employee selected: {sel['section']['name']} (perm: {sel['permission_level']})")

        # ─────────────────────────────────────────────────────────────────────
        step("8. Employee tries to access an unassigned section")
        # Get a section the employee doesn't have access to
        all_sections_r = await c.get(
            "/auth/sections",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        all_sections = all_sections_r.json()["data"]["sections"]
        emp_section_ids = {s["id"] for s in emp_data["available_sections"]}
        forbidden_sections = [s for s in all_sections if s["id"] not in emp_section_ids]

        if forbidden_sections:
            forbidden_id = forbidden_sections[0]["id"]
            r = await c.post(
                "/auth/select-section",
                json={"section_id": forbidden_id},
                headers={"Authorization": f"Bearer {emp_token}"},
            )
            assert r.status_code == 403, f"Expected 403 for unauthorized section, got {r.status_code}"
            ok(f"403 correctly blocked access to section the employee doesn't have")
        else:
            info("Employee has access to all sections — skipping forbidden section test")

        # ─────────────────────────────────────────────────────────────────────
        step("9. Token refresh")
        r = await c.post("/auth/refresh", json={"refresh_token": emp_refresh})
        assert r.status_code == 200, f"Refresh failed: {r.text}"
        new_tokens = r.json()["data"]
        assert new_tokens["access_token"] != emp_token, "Refreshed token should differ"
        ok("Token pair rotated successfully")

        # ─────────────────────────────────────────────────────────────────────
        step("10. Invalid credentials")
        r = await c.post("/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        ok(f"401 returned for bad credentials: '{r.json()['message']}'")

        # ─────────────────────────────────────────────────────────────────────
        step("11. Invalid token")
        r = await c.get("/auth/me", headers={"Authorization": "Bearer totally.invalid.token"})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        ok(f"401 returned for invalid token")

        # ─────────────────────────────────────────────────────────────────────
        step("12. Logout + token revocation")
        r = await c.post("/auth/logout", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200, f"Logout failed: {r.text}"
        ok("Logout successful")

        # Use the revoked token — should get 401
        r = await c.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 401, f"Expected 401 after logout, got {r.status_code}: {r.text}"
        ok("Revoked token correctly rejected with 401")

        # ─────────────────────────────────────────────────────────────────────
        step("13. GET /auth/sections")
        r = await c.post("/auth/login", json=ADMIN_USER)  # re-login after logout
        fresh_admin_token = r.json()["data"]["access_token"]

        r = await c.get("/auth/sections", headers={"Authorization": f"Bearer {fresh_admin_token}"})
        assert r.status_code == 200
        sections = r.json()["data"]["sections"]
        assert len(sections) > 0
        ok(f"Got {len(sections)} sections from /auth/sections")

        # ─────────────────────────────────────────────────────────────────────
        print(f"\n{GREEN}{BOLD}═══════════════════════════════════════")
        print(f"  ALL 13 TESTS PASSED ✓")
        print(f"═══════════════════════════════════════{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run())
