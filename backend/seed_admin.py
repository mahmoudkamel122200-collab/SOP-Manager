import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv('d:/SOP Manager/backend/.env')

async def main():
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Create Roles
        await conn.execute(text("""
            INSERT INTO roles (id, name, description) VALUES
            ('00000000-0000-0000-0000-000000000001', 'ADMIN', 'Admin Role'),
            ('00000000-0000-0000-0000-000000000002', 'EMPLOYEE', 'Employee Role')
            ON CONFLICT (name) DO NOTHING;
        """))
        
        # Create Admin
        await conn.execute(text("""
            INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active) VALUES
            ('00000000-0000-0000-0001-000000000001', 'admin', 'admin@factory.local', 
             '$argon2id$v=19$m=65536,t=2,p=2$q0gDpoMUKgpZJeMsl7n/fw$owpFcqtDu/2FQv3FFRtUX2iQsN4e5UJ+Abr0fIjtvJY',
             'System Administrator', '00000000-0000-0000-0000-000000000001', TRUE)
            ON CONFLICT (username) DO NOTHING;
        """))
        print("Admin user seeded successfully. Username: admin, Password: Admin@1234")
        
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
