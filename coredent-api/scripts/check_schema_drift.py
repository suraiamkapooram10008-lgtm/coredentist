"""One-off drift check: compare ORM metadata against the alembic-migrated schema.

Run: python scripts/check_schema_drift.py
Exits non-zero when model columns are missing from the migrated database.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SECRET_KEY", "drift-check-key-not-for-production-usage")
os.environ.setdefault("ENCRYPTION_KEY", "dHJ1c3RlZC10ZXN0LWtleS1mb3ItZHJpZnQtY2hlY2s=")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ENVIRONMENT", "test")

db_path = Path(".drift-check.sqlite")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.base import Base  # noqa: E402

config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
command.upgrade(config, "head")

import sqlite3  # noqa: E402

conn = sqlite3.connect(db_path)
missing = []
for table in Base.metadata.sorted_tables:
    rows = conn.execute(f"PRAGMA table_info({table.name})").fetchall()
    if not rows:
        missing.append((table.name, "<entire table missing>", [c.name for c in table.columns]))
        continue
    existing = {row[1] for row in rows}
    for column in table.columns:
        if column.name not in existing:
            missing.append((table.name, column.name, None))
conn.close()
db_path.unlink(missing_ok=True)

if missing:
    print("SCHEMA DRIFT DETECTED (model column -> not in migrated DB):")
    for table, column, all_cols in missing:
        if all_cols is not None:
            print(f"  TABLE MISSING: {table}")
        else:
            print(f"  {table}.{column}")
    sys.exit(1)

print("No schema drift: every model column exists in the migrated database.")
