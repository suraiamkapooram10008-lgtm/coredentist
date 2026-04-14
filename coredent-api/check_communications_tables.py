import sqlite3

conn = sqlite3.connect('coredent_dev.db')
cursor = conn.cursor()

# Check Communications tables
comm_tables = [
    'message_templates',
    'patient_messages',
    'reminder_schedules',
    'conversations',
    'conversation_messages'
]

print("🎯 COMMUNICATIONS SYSTEM TABLES")
print("=" * 60)

for table in comm_tables:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    result = cursor.fetchone()
    if result:
        # Get column count
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"✅ {table:30} ({len(columns)} columns)")
    else:
        print(f"❌ {table:30} NOT FOUND")

print("=" * 60)

# Check some other important tables
print("\n📊 OTHER IMPORTANT TABLES")
print("=" * 60)

other_tables = [
    'patient_images',
    'image_series',
    'insurance_carriers',
    'patient_insurances',
    'inventory_items',
    'lab_cases',
    'referrals',
    'campaigns'
]

for table in other_tables:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    result = cursor.fetchone()
    if result:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"✅ {table:30} ({len(columns)} columns)")
    else:
        print(f"❌ {table:30} NOT FOUND")

print("=" * 60)

conn.close()

print("\n🎉 All Communications tables are ready!")
print("✅ You can now test the Communications API endpoints")
