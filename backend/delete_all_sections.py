import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker

async def clear_sections():
    async with async_session_maker() as session:
        # Using DELETE over TRUNCATE to avoid permission issues, 
        # and letting CASCADE handle the rest if configured.
        # If there are foreign keys without cascade, this might fail,
        # but let's try it first.
        try:
            await session.execute(text("DELETE FROM sections;"))
            await session.commit()
            print("Successfully deleted all sections from the database.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(clear_sections())
