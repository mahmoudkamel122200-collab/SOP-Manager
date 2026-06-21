import asyncio
from sqlalchemy import text
from app.core.database import engine

async def run():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS 'CREATE_LOCATION'"))
        await conn.execute(text("ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS 'CREATE_ITEM'"))
        await conn.execute(text("ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS 'SEARCH_ITEM'"))
        await conn.execute(text("ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS 'VIEW_HISTORY'"))
        print("Done adding enum values to PostgreSQL!")

asyncio.run(run())
