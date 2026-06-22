import asyncio
import httpx
import json

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://localhost:8000/api/v1/auth/login', json={'username': 'admin', 'password': 'Admin@1234'})
        if r.status_code != 200:
            print("Login failed:", r.status_code, r.text)
            return
        token = r.json()['data']['access_token']
        res = await client.get('http://localhost:8000/api/v1/logs', headers={'Authorization': f'Bearer {token}'})
        
        with open('logs_output.json', 'w', encoding='utf-8') as f:
            f.write(res.text)
        print("Logs endpoint response code:", res.status_code)

if __name__ == "__main__":
    asyncio.run(test())
