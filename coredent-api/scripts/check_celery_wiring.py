"""Phase 3 check: Celery beat schedule references real, registered tasks.

Mirrors worker startup: celery_app.conf.include modules are imported by the
worker before consuming, so registration is checked AFTER importing them.
"""
from app.core.celery_app import celery_app

for _mod in celery_app.conf.include or []:
    __import__(_mod)

beat = celery_app.conf.beat_schedule or {}
print("Beat schedule entries:")
for name, entry in beat.items():
    task = entry.get("task")
    print(f"  {name}: {task}")

registered = set(celery_app.tasks.keys())
missing = [e["task"] for e in beat.values() if e.get("task") not in registered]
print("MISSING TASKS:", missing if missing else "none")
