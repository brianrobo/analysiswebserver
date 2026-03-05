"""Run the sharing migration SQL"""
import sys

print("Running migration...", flush=True)

try:
    import psycopg2
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        user='postgres',
        password='postgres',
        dbname='analysisdb',
        options='-c client_encoding=UTF8'
    )
    conn.autocommit = True
    cur = conn.cursor()
    print("Connected to analysisdb", flush=True)

    # Read and run the migration SQL
    with open('migrations/001_add_sharing.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Execute the migration (skip if table already exists)
    try:
        cur.execute(sql)
        print("Migration ran successfully!", flush=True)
    except Exception as e:
        if 'already exists' in str(e):
            print(f"Tables already exist (migration already applied)", flush=True)
        else:
            print(f"Migration note: {e}", flush=True)

    cur.close()
    conn.close()
    print("Done!", flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
