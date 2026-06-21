"""Quick script to update password hashes from bcrypt to argon2id in the database."""
import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres123@localhost:5432/factory_db")
cur = conn.cursor()

# Admin@1234
cur.execute(
    "UPDATE users SET password_hash = %s WHERE username = %s",
    ("$argon2id$v=19$m=65536,t=2,p=2$q0gDpoMUKgpZJeMsl7n/fw$owpFcqtDu/2FQv3FFRtUX2iQsN4e5UJ+Abr0fIjtvJY", "admin")
)
print(f"Updated admin: {cur.rowcount} row(s)")

# Employee@1234
cur.execute(
    "UPDATE users SET password_hash = %s WHERE username = %s",
    ("$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI", "ahmed_ali")
)
print(f"Updated ahmed_ali: {cur.rowcount} row(s)")

conn.commit()
cur.close()
conn.close()
print("Done! Password hashes updated to Argon2id.")
