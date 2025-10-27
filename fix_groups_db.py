#!/usr/bin/env python3
"""
fix_groups_db.py
Utility to scan `groups_database.json`, auto-unblock expired entries and optionally persist.
Usage:
  python fix_groups_db.py --dry-run    # show what would change
  python fix_groups_db.py --apply      # write changes back
"""
import json
import os
from datetime import datetime
import argparse

DB_PATH = os.path.abspath('groups_database.json')


def _parse_iso(s):
    from datetime import datetime as _dt
    if not s:
        return None
    try:
        return _dt.fromisoformat(s)
    except Exception:
        pass
    try:
        if s.endswith('Z'):
            return _dt.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        pass
    patterns = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for p in patterns:
        try:
            return _dt.strptime(s, p)
        except Exception:
            continue
    return None


def scan_and_fix(dry_run=True):
    if not os.path.exists(DB_PATH):
        print('groups_database.json not found')
        return 0
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            db = json.load(f)
        except Exception as e:
            print(f'Failed to load DB: {e}')
            return 0

    changed = False
    now = datetime.now()
    expired = []
    for k, v in list(db.items()):
        if not v:
            continue
        if not v.get('blocked'):
            continue
        bu = v.get('blocked_until')
        until = _parse_iso(bu)
        if until is None:
            # Can't parse, treat as still blocked
            continue
        # compare timezone-aware vs naive
        now_cmp = datetime.now(until.tzinfo) if until.tzinfo else now
        if now_cmp >= until:
            expired.append((k, bu))
            if not dry_run:
                v.pop('blocked', None)
                v.pop('blocked_until', None)
                v.pop('blocked_reason', None)
                changed = True

    print(f'Found {len(expired)} expired blocked entries')
    for k, bu in expired:
        print(f' - {k} blocked_until={bu}')

    if changed:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print('Applied changes to groups_database.json')
    else:
        print('No changes applied')

    return len(expired)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true', help='Persist changes to groups_database.json')
    p.add_argument('--dry-run', action='store_true', help='Show changes without writing (default)')
    args = p.parse_args()
    dry = not args.apply
    scan_and_fix(dry_run=dry)
