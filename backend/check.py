import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionFactory

async def main():
    async with AsyncSessionFactory() as s:
        res = await s.execute(text('SELECT count(*) FROM audit_logs'))
        print('count:', res.scalar())

if __name__ == "__main__":
    asyncio.run(main())
