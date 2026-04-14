import sqlite3

conn = sqlite3.connect('coredent_dev.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("📊 Tables in database:")
print("=" * 50)
for table in sorted(tables):
    print(f"  ✅ {table[0]}")
print("=" * 50)
print(f"Total tables: {len(tables)}")

conn.close()
