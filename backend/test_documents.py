"""
test_documents.py

End-to-end integration test for the SOP Document Management System.

Prerequisites:
  1. pip install httpx
  2. uvicorn app.main:app --reload   (in another terminal)
  3. Seed data applied (psql -f ../database/seed.sql)
  4. A test PDF file at backend/test_files/test_sop.pdf
     (we create a minimal one if missing)

Usage:
  cd backend/
  python test_documents.py
"""

import asyncio
import io
import os
import sys
import uuid
from pathlib import Path

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


def _minimal_pdf() -> bytes:
    """Return a tiny valid PDF for testing."""
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


async def run():
    # ── Ensure test PDF exists ────────────────────────────────────────────────
    test_pdf = Path("test_files/test_sop.pdf")
    test_pdf.parent.mkdir(exist_ok=True)
    if not test_pdf.exists():
        test_pdf.write_bytes(_minimal_pdf())
        info(f"Created minimal test PDF at {test_pdf}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as c:

        # ── Login ─────────────────────────────────────────────────────────────
        step("1. Login as Admin")
        r = await c.post("/auth/login", json=ADMIN_CREDS)
        assert r.status_code == 200, r.text
        admin_token  = r.json()["data"]["access_token"]
        all_sections = r.json()["data"]["available_sections"]
        assert len(all_sections) > 0, "No sections found — run seed.sql"
        section_id   = all_sections[0]["id"]
        section_name = all_sections[0]["name"]
        ok(f"Admin logged in. Using section: '{section_name}' ({section_id})")

        # ── Upload document (first version) ───────────────────────────────────
        step("2. Upload SOP Document v1 (Admin)")
        with open(test_pdf, "rb") as f:
            r = await c.post(
                "/documents",
                headers={"Authorization": f"Bearer {admin_token}"},
                data={
                    "section_id":  section_id,
                    "title":       "Machine Safety SOP",
                    "description": "Procedures for safe machine operation",
                },
                files={"file": ("test_sop.pdf", f, "application/pdf")},
            )
        assert r.status_code == 201, f"Upload failed: {r.text}"
        doc1 = r.json()["data"]
        doc1_id = doc1["id"]
        assert doc1["version_number"] == 1, f"Expected v1, got {doc1['version_number']}"
        ok(f"Uploaded: '{doc1['title']}' v{doc1['version_number']} (id: {doc1_id[:8]}…)")
        info(f"File stored at: {doc1['download_url']}")

        # ── Upload same title again — should auto-increment to v2 ─────────────
        step("3. Upload same title again → auto-version to v2")
        with open(test_pdf, "rb") as f:
            r = await c.post(
                "/documents",
                headers={"Authorization": f"Bearer {admin_token}"},
                data={
                    "section_id":  section_id,
                    "title":       "Machine Safety SOP",   # same title!
                    "description": "Updated with new safety regulations",
                    "version_label": "Rev. B",
                },
                files={"file": ("test_sop_v2.pdf", f, "application/pdf")},
            )
        assert r.status_code == 201, f"Upload v2 failed: {r.text}"
        doc2 = r.json()["data"]
        doc2_id = doc2["id"]
        assert doc2["version_number"] == 2, f"Expected v2, got {doc2['version_number']}"
        ok(f"Auto-versioning works: '{doc2['title']}' v{doc2['version_number']} '{doc2['version_label']}'")

        # ── List section documents ────────────────────────────────────────────
        step("4. List documents in section (Admin)")
        r = await c.get(
            f"/documents/section/{section_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        data  = r.json()["data"]
        docs  = data["documents"]
        total = data["total"]
        ok(f"Got {len(docs)} documents (total: {total})")
        assert any(d["id"] == doc1_id for d in docs)
        assert any(d["id"] == doc2_id for d in docs)

        # ── Search ────────────────────────────────────────────────────────────
        step("5. Search documents")
        r = await c.get(
            f"/documents/section/{section_id}?search=safety",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        search_docs = r.json()["data"]["documents"]
        ok(f"Search 'safety' → {len(search_docs)} result(s)")
        assert len(search_docs) >= 1

        # ── Get single document metadata ──────────────────────────────────────
        step("6. Get document metadata (OPEN_DOCUMENT logged)")
        r = await c.get(
            f"/documents/{doc1_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        meta = r.json()["data"]
        assert meta["id"] == doc1_id
        assert "download_url" in meta
        ok(f"Metadata OK. download_url: {meta['download_url']}")

        # ── Download file ─────────────────────────────────────────────────────
        step("7. Download file")
        r = await c.get(
            f"/documents/{doc1_id}/download",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, f"Download failed: {r.status_code}"
        assert len(r.content) > 0
        ok(f"File downloaded ({len(r.content)} bytes, Content-Type: {r.headers.get('content-type')})")

        # ── Version history ───────────────────────────────────────────────────
        step("8. Version history")
        r = await c.get(
            f"/documents/{doc1_id}/versions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        vers = r.json()["data"]["versions"]
        ok(f"Version history: {len(vers)} versions")
        assert len(vers) == 2, f"Expected 2 versions, got {len(vers)}"
        version_nums = sorted(v["version_number"] for v in vers)
        assert version_nums == [1, 2], f"Expected [1,2], got {version_nums}"

        # ── Status transition ─────────────────────────────────────────────────
        step("9. Status transition DRAFT → UNDER_REVIEW → APPROVED")
        r = await c.patch(
            f"/documents/{doc1_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "UNDER_REVIEW"},
        )
        assert r.status_code == 200, r.text
        ok(f"Transitioned to: {r.json()['data']['status']}")

        r = await c.patch(
            f"/documents/{doc1_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "APPROVED"},
        )
        assert r.status_code == 200, r.text
        ok(f"Transitioned to: {r.json()['data']['status']}")

        # ── Invalid status transition ─────────────────────────────────────────
        step("10. Invalid status transition (APPROVED → DRAFT should fail)")
        r = await c.patch(
            f"/documents/{doc1_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "DRAFT"},
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        ok(f"Correctly rejected: {r.json()['message'][:60]}…")

        # ── Employee login + section selection ────────────────────────────────
        step("11. Employee login + section selection")
        r = await c.post("/auth/login", json=EMPLOYEE_CREDS)
        emp_data    = r.json()["data"]
        emp_token   = emp_data["access_token"]
        emp_refresh = emp_data["refresh_token"]
        emp_sections = emp_data["available_sections"]
        ok(f"Employee logged in. Sections: {[s['name'] for s in emp_sections]}")

        if emp_sections:
            # Select first employee section
            r = await c.post(
                "/auth/select-section",
                json={"section_id": emp_sections[0]["id"]},
                headers={"Authorization": f"Bearer {emp_token}"},
            )
            assert r.status_code == 200, r.text
            emp_section_token = r.json()["data"]["access_token"]
            ok(f"Employee selected: {r.json()['data']['section']['name']}")

            # Employee tries to upload → should fail
            step("12. Employee cannot upload (403 expected)")
            with open(test_pdf, "rb") as f:
                r = await c.post(
                    "/documents",
                    headers={"Authorization": f"Bearer {emp_section_token}"},
                    data={"section_id": section_id, "title": "Hack Attempt"},
                    files={"file": ("hack.pdf", f, "application/pdf")},
                )
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
            ok("Employee correctly denied upload access")

        # ── Admin list all ────────────────────────────────────────────────────
        step("13. Admin lists ALL documents")
        r = await c.get(
            "/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        all_docs = r.json()["data"]
        ok(f"Admin sees all: {all_docs['total']} document(s) total")

        # ── Soft delete ───────────────────────────────────────────────────────
        step("14. Soft delete document")
        r = await c.delete(
            f"/documents/{doc2_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        ok(f"Soft deleted: {r.json()['data']['message']}")

        # Deleted doc should not appear in list
        r = await c.get(
            f"/documents/section/{section_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ids_visible = [d["id"] for d in r.json()["data"]["documents"]]
        assert doc2_id not in ids_visible, "Soft-deleted doc still visible in list!"
        ok("Soft-deleted document correctly hidden from list")

        # But should still 404 when accessed directly
        r = await c.get(
            f"/documents/{doc2_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404, f"Expected 404 for deleted doc, got {r.status_code}"
        ok("Accessing deleted doc returns 404 ✓")

        # ── Audit trail ───────────────────────────────────────────────────────
        step("15. Audit trail for document")
        r = await c.get(
            f"/documents/{doc1_id}/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        logs = r.json()["data"]["logs"]
        ok(f"Audit trail: {len(logs)} event(s)")
        actions = [log["action"] for log in logs]
        info(f"  Actions recorded: {actions}")
        assert "UPLOAD_DOCUMENT" in actions
        assert "OPEN_DOCUMENT"   in actions

        # ── Final summary ─────────────────────────────────────────────────────
        print(f"\n{GREEN}{BOLD}═══════════════════════════════════════")
        print(f"  ALL 15 DOCUMENT TESTS PASSED ✓")
        print(f"═══════════════════════════════════════{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run())
