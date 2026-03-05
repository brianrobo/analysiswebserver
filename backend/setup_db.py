"""One-time database setup script"""
import sys

print("Setting up database...", flush=True)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    print("psycopg2 imported OK", flush=True)
except ImportError as e:
    print(f"Import error: {e}", flush=True)
    sys.exit(1)

passwords_to_try = ['postgres123', 'postgres', '', 'admin']

conn = None
for pwd in passwords_to_try:
    try:
        print(f"Trying password: {'(empty)' if not pwd else '***'}", flush=True)
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password=pwd,
            dbname='postgres',
            options='-c client_encoding=UTF8'
        )
        print(f"Connected with password!", flush=True)
        break
    except Exception as e:
        err = str(e)
        # Try to decode if bytes
        if isinstance(e, UnicodeDecodeError):
            print(f"Unicode error (likely wrong password in Korean locale)", flush=True)
        else:
            print(f"Failed: {err[:100]}", flush=True)

if conn is None:
    print("Could not connect with any password", flush=True)
    sys.exit(1)

try:
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    print("Connected to PostgreSQL", flush=True)

    # Check if analysisdb exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='analysisdb'")
    exists = cur.fetchone()

    if exists:
        print("analysisdb already exists - skipping creation", flush=True)
    else:
        cur.execute("CREATE DATABASE analysisdb OWNER postgres ENCODING 'UTF8'")
        print("Created analysisdb database!", flush=True)

    cur.close()
    conn.close()
    print("Database setup complete!", flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

