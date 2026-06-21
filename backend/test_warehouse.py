"""
test_warehouse.py

End-to-end integration test for the Warehouse Management System.

Prerequisites:
  1. pip install httpx
  2. uvicorn app.main:app --reload   (in another terminal)
  3. Seed data applied (psql -f ../database/seed.sql)

Usage:
  cd backend/
  python test_warehouse.py
"""

import asyncio
import sys
import uuid
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Run  pip install httpx  first.")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000/api/v1"

ADMIN_CREDS    = {"username": "admin",     "password": "Admin@1234"}
EMPLOYEE_CREDS = {"username": "ahmed_ali", "password": "Employee@1234"}

GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
RESET = "\033[0m";  BOLD = "\033[1m"

def ok(m):   print(f"  {GREEN}✓{RESET} {m}")
def fail(m): print(f"  {RED}✗{RESET} {m}"); sys.exit(1)
def step(m): print(f"\n{BOLD}{YELLOW}▶ {m}{RESET}")
def info(m): print(f"    {m}")


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as c:

        # ── 1. LOGIN ADMIN ────────────────────────────────────────────────────
        step("1. Login as Admin")
        r = await c.post("/auth/login", json=ADMIN_CREDS)
        assert r.status_code == 200, r.text
        admin_token = r.json()["data"]["access_token"]
        ok("Admin logged in successfully.")

        # ── 2. CREATE LOCATIONS (Feature 1) ───────────────────────────────────
        step("2. Create warehouse locations (Admin only)")
        # Location 1
        r = await c.post(
            "/warehouse/locations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "warehouse_name": "Warehouse A",
                "rack": "R01",
                "shelf": "S03",
                "position": "P05"
            }
        )
        assert r.status_code == 201, f"Failed to create Location 1: {r.text}"
        loc1 = r.json()["data"]
        loc1_id = loc1["id"]
        assert loc1["location_code"] == "A-R01-S03-P05"
        ok(f"Location 1 created: {loc1['location_code']} (ID: {loc1_id})")

        # Location 2
        r = await c.post(
            "/warehouse/locations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "warehouse_name": "Warehouse A",
                "rack": "R02",
                "shelf": "S01",
                "position": "P02"
            }
        )
        assert r.status_code == 201, f"Failed to create Location 2: {r.text}"
        loc2 = r.json()["data"]
        loc2_id = loc2["id"]
        assert loc2["location_code"] == "A-R02-S01-P02"
        ok(f"Location 2 created: {loc2['location_code']} (ID: {loc2_id})")

        # Duplicate check
        r = await c.post(
            "/warehouse/locations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "warehouse_name": "Warehouse A",
                "rack": "R01",
                "shelf": "S03",
                "position": "P05"
            }
        )
        assert r.status_code == 409, f"Expected 409 conflict, got {r.status_code}: {r.text}"
        ok("Duplicate location validation works.")

        # ── 3. LIST LOCATIONS ─────────────────────────────────────────────────
        step("3. List warehouse locations")
        # Let's perform select-section for admin first so they have active section (Production or Warehouse)
        # Note: Admin has bypass for section verification in require_section_permission, but require_section_permission() 
        # still allows admin without section. But to list_locations which has `_read` dependency, 
        # let's select section first or check if admin bypass works. Yes, ADMIN bypass returns token payload directly.
        r = await c.get(
            "/warehouse/locations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200, r.text
        locations_list = r.json()["data"]
        assert len(locations_list) >= 2
        ok(f"Successfully retrieved {len(locations_list)} locations.")

        # ── 4. CREATE ITEM (Feature 2) ────────────────────────────────────────
        step("4. Create item/bag (Admin only)")
        # Item 1
        item_code = f"BG-000123"
        r = await c.post(
            "/warehouse/items",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "item_code": item_code,
                "material_name": "Raw Material X",
                "quantity": 50.0,
                "unit": "KG",
                "location_id": loc1_id
            }
        )
        assert r.status_code == 201, f"Failed to create Item: {r.text}"
        item1 = r.json()["data"]
        item1_id = item1["id"]
        assert item1["item_code"] == item_code
        ok(f"Item created: {item1['item_code']} at {item1['location']['location_code']} (ID: {item1_id})")

        # Duplicate check
        r = await c.post(
            "/warehouse/items",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "item_code": item_code,
                "material_name": "Raw Material X duplicate",
                "quantity": 25.0,
                "unit": "KG",
                "location_id": loc2_id
            }
        )
        assert r.status_code == 409, f"Expected 409 conflict, got {r.status_code}: {r.text}"
        ok("Duplicate item code validation works.")

        # ── 5. SEARCH ITEM LOCATION (Feature 3) ───────────────────────────────
        step("5. Search item location")
        # Employee login and select section to search
        r = await c.post("/auth/login", json=EMPLOYEE_CREDS)
        assert r.status_code == 200, r.text
        emp_token = r.json()["data"]["access_token"]
        emp_sections = r.json()["data"]["available_sections"]
        warehouse_sec = next(s for s in emp_sections if s["name"] == "Warehouse")
        warehouse_sec_id = warehouse_sec["id"]
        
        # Select active section for employee
        r = await c.post(
            "/auth/select-section",
            headers={"Authorization": f"Bearer {emp_token}"},
            json={"section_id": warehouse_sec_id}
        )
        assert r.status_code == 200, r.text
        emp_active_token = r.json()["data"]["access_token"]
        ok("Employee selected Warehouse section.")

        # Worker searches for item
        r = await c.get(
            f"/warehouse/items/{item_code}",
            headers={"Authorization": f"Bearer {emp_active_token}"}
        )
        assert r.status_code == 200, r.text
        search_data = r.json()["data"]
        assert search_data["item_code"] == item_code
        assert search_data["material"] == "Raw Material X"
        assert search_data["quantity"] == 50.0
        assert search_data["location"]["warehouse"] == "Warehouse A"
        assert search_data["location"]["rack"] == "R01"
        assert search_data["location"]["shelf"] == "S03"
        assert search_data["location"]["position"] == "P05"
        ok("Item search returned exact required format.")

        # ── 6. MOVE ITEM (Feature 4) ──────────────────────────────────────────
        step("6. Move item to another location")
        r = await c.post(
            f"/warehouse/items/{item1_id}/move",
            headers={"Authorization": f"Bearer {emp_active_token}"},
            json={
                "new_location_id": loc2_id,
                "notes": "Moved for production"
            }
        )
        assert r.status_code == 200, r.text
        moved_item = r.json()["data"]
        assert moved_item["location"]["location_code"] == "A-R02-S01-P02"
        ok(f"Moved item {item_code} successfully to A-R02-S01-P02.")

        # ── 7. MOVEMENT HISTORY (Feature 5) ───────────────────────────────────
        step("7. Retrieve movement history")
        r = await c.get(
            f"/warehouse/items/{item1_id}/history",
            headers={"Authorization": f"Bearer {emp_active_token}"}
        )
        assert r.status_code == 200, r.text
        history = r.json()["data"]
        assert len(history) >= 2, f"Expected at least 2 logs, got {len(history)}"
        
        # Verify the structure matches: from, to, moved_by, date
        latest_move = history[0]
        assert latest_move["from"] == "A-R01-S03-P05"
        assert latest_move["to"] == "A-R02-S01-P02"
        assert "moved_by" in latest_move
        assert "date" in latest_move
        ok("Movement history returns the exact required format.")

        # ── 8. AUTHORIZATION CHECKS ───────────────────────────────────────────
        step("8. Run authorization protection checks")
        # Employee attempts to create a location -> should fail
        r = await c.post(
            "/warehouse/locations",
            headers={"Authorization": f"Bearer {emp_active_token}"},
            json={
                "warehouse_name": "Warehouse A",
                "rack": "R03",
                "shelf": "S01",
                "position": "P01"
            }
        )
        assert r.status_code == 403, f"Expected 403 forbidden, got {r.status_code}"
        ok("Employee is blocked from creating locations.")

        # Employee attempts to create an item -> should fail
        r = await c.post(
            "/warehouse/items",
            headers={"Authorization": f"Bearer {emp_active_token}"},
            json={
                "item_code": "BG-999999",
                "material_name": "Illegal Material",
                "quantity": 10.0,
                "unit": "KG",
                "location_id": loc2_id
            }
        )
        assert r.status_code == 403, f"Expected 403 forbidden, got {r.status_code}"
        ok("Employee is blocked from creating items.")

        print(f"\n{GREEN}{BOLD}═══════════════════════════════════════")
        print(f"  ALL WAREHOUSE TESTS PASSED ✓")
        print(f"═══════════════════════════════════════{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run())
