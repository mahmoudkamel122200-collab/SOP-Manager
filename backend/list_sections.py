import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionFactory
from app.models.models import Section

async def main():
    async with AsyncSessionFactory() as db:
        result = await db.execute(select(Section))
        sections = result.scalars().all()
        print(f"Total sections in DB: {len(sections)}")
        for s in sections:
            print(f"ID: {s.id}, Name: {s.name}")

if __name__ == '__main__':
    asyncio.run(main())
