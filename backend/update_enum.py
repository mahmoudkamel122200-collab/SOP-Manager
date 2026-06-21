import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres123@localhost:5432/factory_db")
conn.autocommit = True
cur = conn.cursor()

values_to_add = ['CREATE_LOCATION', 'CREATE_ITEM', 'SEARCH_ITEM', 'VIEW_HISTORY']

for val in values_to_add:
    try:
        cur.execute(f"ALTER TYPE audit_action_enum ADD VALUE '{val}';")
        print(f"Added {val}")
    except psycopg2.errors.DuplicateObject:
        print(f"{val} already exists")
    except Exception as e:
        print(f"Error adding {val}: {e}")

cur.close()
conn.close()
print("Enum updated!")
