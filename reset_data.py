"""
reset_data.py

Backs up and clears data files used by the bot. Safe to run from the project root.
Files affected:
- credentials.csv -> header only
- groups.json -> []
- groups_database.json -> {}
- stats.json -> {'total_sent':0,'last_run':None,'groups':{}}
- config.json -> clears 'target_groups', 'ad_forward_from_chat', 'ad_forward_message_id'

Creates timestamped backups: <file>.bak.YYYYmmddHHMMSS

Use carefully. You can restore from backups if needed.
"""
import os
import shutil
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = {
    'credentials.csv': {'type': 'csv', 'path': os.path.join(ROOT, 'credentials.csv')},
    'groups.json': {'type': 'json_list', 'path': os.path.join(ROOT, 'groups.json')},
    'groups_database.json': {'type': 'json_obj', 'path': os.path.join(ROOT, 'groups_database.json')},
    'stats.json': {'type': 'stats', 'path': os.path.join(ROOT, 'stats.json')},
    'config.json': {'type': 'config', 'path': os.path.join(ROOT, 'config.json')},
}

BACKUPS = []

def backup_file(path):
    if not os.path.exists(path):
        return None
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = path + f'.bak.{ts}'
    shutil.copy2(path, bak)
    BACKUPS.append(bak)
    return bak


def write_credentials_header(path):
    header = 'credential_type,api_id,api_hash,bot_token,phone,session_name,description,active\n'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(header)


def write_json_list(path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=4)


def write_json_obj(path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=4)


def write_stats(path):
    data = {'total_sent': 0, 'last_run': None, 'groups': {}}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def modify_config(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    # Clear target groups and ad forward fields
    cfg['target_groups'] = []
    cfg.pop('ad_forward_from_chat', None)
    cfg.pop('ad_forward_message_id', None)
    # Optionally keep other settings intact
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)


def main():
    print('Resetting data files (backups will be created)...')
    for name, info in FILES.items():
        path = info['path']
        print(f'Processing {name}...')
        bak = backup_file(path)
        if bak:
            print(f'  Backup created: {bak}')
        else:
            print(f'  No existing file to backup: {path}')

        t = info['type']
        try:
            if t == 'csv':
                write_credentials_header(path)
            elif t == 'json_list':
                write_json_list(path)
            elif t == 'json_obj':
                write_json_obj(path)
            elif t == 'stats':
                write_stats(path)
            elif t == 'config':
                modify_config(path)
            print('  Cleared')
        except Exception as e:
            print(f'  Failed to clear {name}: {e}')

    print('\nDone. Backups created:')
    for b in BACKUPS:
        print(' -', b)
    print('\nIf you need to restore a file, copy the .bak.* file back to the original filename.')

if __name__ == '__main__':
    main()
