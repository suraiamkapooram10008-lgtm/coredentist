#!/usr/bin/env python3
"""
Fix all `datetime.now()` calls to use `datetime.now(timezone.utc)` across the codebase.
Naive datetimes cause comparison bugs with timezone-aware database values.
"""
import os
import re
import glob

# Files to fix: all Python files in coredent-api/app
files = glob.glob("coredent-api/app/**/*.py", recursive=True)

fixed_count = 0
for filepath in sorted(files):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, UnicodeError):
        # Try Windows encoding
        try:
            with open(filepath, 'r', encoding='cp1252') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Skipped (encoding): {filepath} -> {e}")
            continue

    original = content

    # 1. Fix imports: add timezone to datetime imports
    content = re.sub(
        r'^from datetime import datetime$',
        r'from datetime import datetime, timezone',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^from datetime import (datetime,\s*\w+)$',
        lambda m: f'from datetime import {m.group(1)}, timezone' if 'timezone' not in m.group(1) else m.group(0),
        content,
        flags=re.MULTILINE
    )

    # 2. Fix comparisons with timedelta
    content = content.replace("datetime.now() - timedelta", "datetime.now(timezone.utc) - timedelta")
    content = content.replace("datetime.now() + timedelta", "datetime.now(timezone.utc) + timedelta")
    content = content.replace("datetime.now() < ", "datetime.now(timezone.utc) < ")
    content = content.replace("datetime.now() > ", "datetime.now(timezone.utc) > ")
    content = content.replace("datetime.now() <= ", "datetime.now(timezone.utc) <= ")
    content = content.replace("datetime.now() >= ", "datetime.now(timezone.utc) >= ")

    # 3. Fix standalone datetime.now()
    content = re.sub(
        r'(?<!timezone\.)datetime\.now\(\)(?!\.date\(\))',
        'datetime.now(timezone.utc)',
        content
    )

    # 4. Fix datetime.now().date()
    content = re.sub(
        r'(?<!timezone\.)datetime\.now\(\)\.date\(\)',
        'datetime.now(timezone.utc).date()',
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
        fixed_count += 1

print(f"\n{'='*60}")
print(f"Fixed {fixed_count} files total")
print(f"{'='*60}")