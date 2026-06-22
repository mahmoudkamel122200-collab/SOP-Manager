import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://localhost:8000/api/v1/auth/login', json={'username': 'admin', 'password': 'Admin@1234'})
        token = r.json()['data']['access_token']
        
        tasks = []
        for _ in range(5):
            tasks.append(client.get('http://localhost:8000/api/v1/logs', headers={'Authorization': f'Bearer {token}'}))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"Request {i} failed with exception: {res}")
            else:
                print(f"Request {i} returned status: {res.status_code}")
                if res.status_code == 500:
                    print(res.text)

if __name__ == "__main__":
    asyncio.run(test())
