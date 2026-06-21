import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres123@localhost:5432/factory_db")
    cur = conn.cursor()
    
    # 1. First, delete Ahmed's additional section accesses (keep only Warehouse)
    cur.execute("""
    DELETE FROM user_sections 
    WHERE user_id = '00000000-0000-0000-0001-000000000002' 
      AND section_id != '00000000-0000-0000-0002-000000000003';
    """)
    
    # 2. Insert new users
    cur.execute("""
    INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active) VALUES
        ('00000000-0000-0000-0001-000000000003',
         'fatima_labs',
         'fatima.labs@factory.local',
         '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',
         'Fatima (Labs)',
         '00000000-0000-0000-0000-000000000002',
         TRUE),

        ('00000000-0000-0000-0001-000000000004',
         'omar_prod',
         'omar.prod@factory.local',
         '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',
         'Omar (Production)',
         '00000000-0000-0000-0000-000000000002',
         TRUE),

        ('00000000-0000-0000-0001-000000000005',
         'sara_quality',
         'sara.quality@factory.local',
         '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',
         'Sara (Quality)',
         '00000000-0000-0000-0000-000000000002',
         TRUE)
    ON CONFLICT DO NOTHING;
    """)

    # 3. Assign them to their sections
    cur.execute("""
    INSERT INTO user_sections (user_id, section_id, permission_level) VALUES
        ('00000000-0000-0000-0001-000000000003', '00000000-0000-0000-0002-000000000002', 'WRITE'),
        ('00000000-0000-0000-0001-000000000004', '00000000-0000-0000-0002-000000000001', 'WRITE'),
        ('00000000-0000-0000-0001-000000000005', '00000000-0000-0000-0002-000000000004', 'WRITE')
    ON CONFLICT DO NOTHING;
    """)
    
    conn.commit()
    print("Database updated successfully.")
except Exception as e:
    print(f"Error: {e}")
