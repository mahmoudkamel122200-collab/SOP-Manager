"""
check_and_fix_db.py
Checks the documents table columns and applies the needed schema migration:
  - Renames 'version' -> 'version_number' (if it exists)
  - Adds 'version_label' column (if missing)
  - Adds 'file_name', 'file_size_bytes', 'mime_type' (if missing)
  - Adds 'is_deleted', 'deleted_at', 'deleted_by' (if missing)
  - Drops old unique constraint and adds the new one
"""
import asyncio
import asyncpg

DB_URL = "postgresql://postgres:postgres123@localhost:5432/factory_db"


async def main():
    conn = await asyncpg.connect(DB_URL)

    # ── 1. Show current columns ─────────────────────────────────────────────
    rows = await conn.fetch("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents'
        ORDER BY ordinal_position;
    """)
    print("=== CURRENT DOCUMENTS TABLE COLUMNS ===")
    col_names = set()
    for r in rows:
        col_names.add(r["column_name"])
        print(f"  {r['column_name']:30s} {r['data_type']:30s} nullable={r['is_nullable']}")

    print("\n=== APPLYING MIGRATIONS ===")

    # ── 2. Rename 'version' -> 'version_number' if needed ──────────────────
    if "version" in col_names and "version_number" not in col_names:
        print("  Renaming column 'version' -> 'version_number' ...")
        # First, check the data type - it may be varchar, need to cast to integer
        col_info = await conn.fetchrow("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name='documents' AND column_name='version'
        """)
        print(f"    Current 'version' type: {col_info['data_type']}")
        
        # Add new integer column
        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS version_number INTEGER;")
        # Copy data (try to cast; fallback to 1)
        await conn.execute("""
            UPDATE documents 
            SET version_number = COALESCE(
                CASE WHEN version ~ '^[0-9]+$' THEN version::integer ELSE NULL END,
                1
            )
            WHERE version_number IS NULL;
        """)
        # Set NOT NULL and default
        await conn.execute("ALTER TABLE documents ALTER COLUMN version_number SET NOT NULL;")
        await conn.execute("ALTER TABLE documents ALTER COLUMN version_number SET DEFAULT 1;")
        # Drop old column
        await conn.execute("ALTER TABLE documents DROP COLUMN version;")
        print("  ✓ 'version' renamed to 'version_number'")
    elif "version_number" not in col_names:
        print("  Adding 'version_number' column ...")
        await conn.execute("""
            ALTER TABLE documents 
            ADD COLUMN version_number INTEGER NOT NULL DEFAULT 1;
        """)
        print("  ✓ 'version_number' added")
    else:
        print("  ✓ 'version_number' already exists")

    # ── 3. Add 'version_label' if missing ──────────────────────────────────
    if "version_label" not in col_names:
        print("  Adding 'version_label' column ...")
        await conn.execute("ALTER TABLE documents ADD COLUMN version_label VARCHAR(50);")
        print("  ✓ 'version_label' added")
    else:
        print("  ✓ 'version_label' already exists")

    # ── 4. Add 'file_name' if missing ──────────────────────────────────────
    if "file_name" not in col_names:
        print("  Adding 'file_name' column ...")
        await conn.execute("""
            ALTER TABLE documents 
            ADD COLUMN file_name VARCHAR(512);
        """)
        # Populate with the basename of file_path
        await conn.execute("""
            UPDATE documents
            SET file_name = REVERSE(SPLIT_PART(REVERSE(file_path), '/', 1))
            WHERE file_name IS NULL;
        """)
        await conn.execute("ALTER TABLE documents ALTER COLUMN file_name SET NOT NULL;")
        print("  ✓ 'file_name' added")
    else:
        print("  ✓ 'file_name' already exists")

    # ── 5. Add 'file_size_bytes' if missing ────────────────────────────────
    if "file_size_bytes" not in col_names:
        print("  Adding 'file_size_bytes' column ...")
        await conn.execute("ALTER TABLE documents ADD COLUMN file_size_bytes INTEGER;")
        print("  ✓ 'file_size_bytes' added")
    else:
        print("  ✓ 'file_size_bytes' already exists")

    # ── 6. Add 'mime_type' if missing ──────────────────────────────────────
    if "mime_type" not in col_names:
        print("  Adding 'mime_type' column ...")
        await conn.execute("ALTER TABLE documents ADD COLUMN mime_type VARCHAR(100);")
        print("  ✓ 'mime_type' added")
    else:
        print("  ✓ 'mime_type' already exists")

    # ── 7. Add soft delete columns if missing ──────────────────────────────
    if "is_deleted" not in col_names:
        print("  Adding 'is_deleted' column ...")
        await conn.execute("""
            ALTER TABLE documents 
            ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
        """)
        print("  ✓ 'is_deleted' added")
    else:
        print("  ✓ 'is_deleted' already exists")

    if "deleted_at" not in col_names:
        print("  Adding 'deleted_at' column ...")
        await conn.execute("ALTER TABLE documents ADD COLUMN deleted_at TIMESTAMPTZ;")
        print("  ✓ 'deleted_at' added")
    else:
        print("  ✓ 'deleted_at' already exists")

    if "deleted_by" not in col_names:
        print("  Adding 'deleted_by' column ...")
        await conn.execute("""
            ALTER TABLE documents 
            ADD COLUMN deleted_by UUID 
            REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;
        """)
        print("  ✓ 'deleted_by' added")
    else:
        print("  ✓ 'deleted_by' already exists")

    # ── 8. Handle unique constraint ────────────────────────────────────────
    constraints = await conn.fetch("""
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'documents'::regclass AND contype = 'u';
    """)
    print("\n  Current unique constraints:", [r["conname"] for r in constraints])

    # Drop old constraint if any has 'version' in it
    for r in constraints:
        if r["conname"] in ("uq_documents_title_version", "documents_title_version_key"):
            print(f"  Dropping old constraint: {r['conname']}")
            await conn.execute(f"ALTER TABLE documents DROP CONSTRAINT {r['conname']};")

    # Add the new unique constraint if it doesn't exist
    new_constraint = "uq_documents_title_section_version"
    existing = [r["conname"] for r in constraints]
    if new_constraint not in existing:
        # Check if it would conflict
        try:
            await conn.execute(f"""
                ALTER TABLE documents 
                ADD CONSTRAINT {new_constraint} 
                UNIQUE (title, section_id, version_number);
            """)
            print(f"  ✓ Added constraint '{new_constraint}'")
        except Exception as e:
            print(f"  ⚠ Could not add unique constraint: {e}")
    else:
        print(f"  ✓ Constraint '{new_constraint}' already exists")

    # ── 9. Add check constraint for version_number >= 1 ───────────────────
    try:
        await conn.execute("""
            ALTER TABLE documents 
            ADD CONSTRAINT chk_documents_version_positive 
            CHECK (version_number >= 1);
        """)
        print("  ✓ Added check constraint for version_number >= 1")
    except Exception as e:
        if "already exists" in str(e):
            print("  ✓ Check constraint already exists")
        else:
            print(f"  ⚠ Check constraint issue: {e}")

    # ── 10. Show final state ────────────────────────────────────────────────
    final_rows = await conn.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents'
        ORDER BY ordinal_position;
    """)
    print("\n=== FINAL DOCUMENTS TABLE COLUMNS ===")
    for r in final_rows:
        print(f"  {r['column_name']:30s} {r['data_type']:30s} nullable={r['is_nullable']}")

    await conn.close()
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())
