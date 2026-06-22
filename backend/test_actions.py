import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionFactory

async def main():
    async with AsyncSessionFactory() as s:
        res = await s.execute(text('SELECT DISTINCT action FROM audit_logs'))
        print('actions:', [r[0] for r in res.all()])

if __name__ == "__main__":
    asyncio.run(main())
