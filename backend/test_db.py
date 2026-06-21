import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://postgres.rquswtjcmgefdndluxxt:MahmoudKamel1%40@aws-0-eu-west-1.pooler.supabase.com:6543/postgres')
        print('Success Pooler!')
        await conn.close()
    except Exception as e:
        print("Pooler error:", e)

    try:
        conn2 = await asyncpg.connect('postgresql://postgres:MahmoudKamel1%40@db.rquswtjcmgefdndluxxt.supabase.co:5432/postgres')
        print('Success Direct!')
        await conn2.close()
    except Exception as e:
        print("Direct error:", e)

asyncio.run(main())
