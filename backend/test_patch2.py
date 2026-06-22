import asyncio
import httpx
import jwt
import uuid
from datetime import datetime, timedelta, timezone

def get_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "role": "ADMIN",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, "replace_with_strong_random_secret_min_32_chars", algorithm="HS256")

async def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        res = await client.get("https://sop-manager-sr33.vercel.app/api/v1/sections", headers=headers)
        secs = res.json()["data"]
        sec_id = secs[0]["id"]

        res = await client.get("https://sop-manager-sr33.vercel.app/api/v1/documents", headers=headers)
        docs = res.json()["data"]["documents"]
        doc_id = docs[0]["id"]
        
        print(f"Patching document {doc_id} with section {sec_id}...")
        res = await client.patch(
            f"https://sop-manager-sr33.vercel.app/api/v1/documents/{doc_id}",
            json={"title": "new title", "section_ids": [sec_id]},
            headers=headers
        )
        print("PATCH response:", res.status_code)
        print(res.text)

asyncio.run(main())
