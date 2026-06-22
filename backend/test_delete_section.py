import asyncio
import uuid
from sqlalchemy import select
from app.db.session import async_session
from app.models.models import Section

async def main():
    async with async_session() as db:
        result = await db.execute(select(Section))
        sections = result.scalars().all()
        for s in sections:
            print(f"ID: {s.id}, Name: {s.name}")
            
        # Try to delete the first one
        if sections:
            s_to_delete = sections[0]
            print(f"Deleting {s_to_delete.name}")
            await db.delete(s_to_delete)
            try:
                await db.commit()
                print("Deleted successfully")
            except Exception as e:
                print(f"Error deleting: {e}")

asyncio.run(main())
