#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('coredent_dev.db')
cursor = conn.cursor()
cursor.execute('UPDATE users SET role = ? WHERE email = ?', ('ADMIN', 'admin@coredent.com'))
conn.commit()
conn.close()
print('Updated user role to ADMIN')