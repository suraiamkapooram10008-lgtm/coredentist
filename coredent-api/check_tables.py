#!/usr/bin/env python3
"""Check database tables"""
import sqlite3

conn = sqlite3.connect('coredent_dev.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print(f'Total tables: {len(tables)}\n')
for table in tables:
    print(f'  - {table[0]}')
conn.close()
