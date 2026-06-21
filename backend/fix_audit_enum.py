"""
Fix audit_action_enum in the live PostgreSQL database.
Adds any missing enum values that the Python model expects.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


EXPECTED_VALUES = [
    "LOGIN", "LOGOUT", "CREATE", "READ", "UPDATE", "DELETE",
    "UPLOAD_DOCUMENT", "OPEN_DOCUMENT", "ARCHIVE_DOCUMENT",
    "MOVE_ITEM", "ADD_ITEM", "REMOVE_ITEM",
    "CREATE_LOCATION", "CREATE_ITEM", "SEARCH_ITEM", "VIEW_HISTORY",
    "GRANT_ACCESS", "REVOKE_ACCESS",
]


async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres123@localhost:5432/factory_db"
    )
    async with engine.begin() as conn:
        # Get current enum values
        result = await conn.execute(text(
            "SELECT enumlabel FROM pg_enum "
            "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
            "WHERE pg_type.typname = 'audit_action_enum' "
            "ORDER BY pg_enum.enumsortorder"
        ))
        current = {row[0] for row in result}
        print(f"Current DB enum values: {sorted(current)}")

        missing = [v for v in EXPECTED_VALUES if v not in current]
        if not missing:
            print("All enum values are already present. Nothing to do.")
        else:
            print(f"Missing values: {missing}")
            for val in missing:
                stmt = f"ALTER TYPE audit_action_enum ADD VALUE IF NOT EXISTS '{val}'"
                # Each ADD VALUE must be in its own transaction for asyncpg
                await conn.execute(text("COMMIT"))
                await conn.execute(text(stmt))
                print(f"  Added: {val}")

            print("Done! All missing enum values have been added.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
