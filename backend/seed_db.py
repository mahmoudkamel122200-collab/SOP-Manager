import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv('d:/SOP Manager/backend/.env')

async def main():
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    
    with open('d:/SOP Manager/database/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        
    with open('d:/SOP Manager/database/seed.sql', 'r', encoding='utf-8') as f:
        seed_sql = f.read()

    async with engine.begin() as conn:
        from sqlalchemy import text
        # schema.sql has multiple statements, need to execute them
        # await conn.execute(text(schema_sql))
        await conn.execute(text(seed_sql))
        print("Database seeded successfully.")
        
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
