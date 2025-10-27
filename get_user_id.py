#!/usr/bin/env python3
"""
Get Your Telegram User ID
Run this script and it will show your user ID
"""

import asyncio
from telethon import TelegramClient

async def get_user_id():
    # Load credentials
    import csv
    try:
        with open('credentials.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['credential_type'] == 'telegram_api' and row['active'].lower() == 'true':
                    api_id = row['api_id']
                    api_hash = row['api_hash']
                    session_name = row['session_name']
                    break
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return

    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        
        print("🆔 YOUR TELEGRAM USER ID:")
        print("=" * 40)
        print(f"User ID: {me.id}")
        print(f"Name: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username or 'No username'}")
        print(f"Phone: {me.phone}")
        print("=" * 40)
        print(f"Add this ID to admin_users in config.json:")
        print(f'"admin_users": [{me.id}]')
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_user_id())
