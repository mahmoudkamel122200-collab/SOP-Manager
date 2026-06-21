import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres123@localhost:5432/factory_db')
    rows = await conn.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='documents' ORDER BY ordinal_position"
    )
    print("=== documents table columns ===")
    for r in rows:
        print(f"  {r['column_name']}  ({r['data_type']})")
    await conn.close()

asyncio.run(main())
