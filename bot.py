#!/usr/bin/env python3
"""
🤖 TELEGRAM AD SENDER - HYBRID BOT
- Control via Bot Commands
- Operations via User Client
- Full Group Scraping Access

Credit: All code and logic by @TheLonelyRoot
"""

import asyncio
import sqlite3
import random
import os
import json
import csv
import logging
from datetime import datetime, timedelta

# Rich terminal helpers
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
except Exception:
    # If rich isn't available, define fallbacks to avoid import-time crashes
    Console = None
    Panel = None
    Align = None
    Live = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None


# Telethon imports (clients, events, buttons) and errors
try:
    from telethon import TelegramClient, events, Button
    from telethon.errors import FloodWaitError, SessionPasswordNeededError
    from telethon.errors.rpcerrorlist import PersistentTimestampOutdatedError, QueryIdInvalidError
    from telethon.tl.types import Channel, Chat
    # For premium emoji support
    try:
        from telethon.tl.types import MessageEntityCustomEmoji
    except Exception:
        MessageEntityCustomEmoji = None
    # UpdateProfileRequest used to change bio/profile
    try:
        from telethon.tl.functions.account import UpdateProfileRequest
    except Exception:
        UpdateProfileRequest = None
except Exception:
    # Provide safe fallbacks for environments without Telethon available at edit-time
    TelegramClient = None
    events = None
    Button = None
    FloodWaitError = Exception
    Channel = None
    Chat = None
    SessionPasswordNeededError = Exception
    PersistentTimestampOutdatedError = Exception
    QueryIdInvalidError = Exception
    UpdateProfileRequest = None
    MessageEntityCustomEmoji = None

# ---- Terminal UI helpers (stylish, ASCII-art header, credit MRNOL) ----
def term_header(title: str = '', credit: str = 'MRNOL'):
    """Return an ASCII-art header string. Title is optional; credit is shown below."""
    art = r"""
 ,--.   ,--.,------. ,--.  ,--. ,-----. ,--.         ,---.  ,------.  ,-----.   ,-----. ,--------. 
 |   `.'   ||  .--. '|  ,'.|  |'  .-.  '|  |        /  O  \ |  .-.  \ |  |) /_ '  .-.  ''--.  .--' 
 |  |'.'|  ||  '--'.'|  |' '  ||  | |  ||  |       |  .-.  ||  |  \  :|  .-.  \|  | |  |   |  |    
 |  |   |  ||  |\  \ |  | `   |'  '-'  '|  '--.    |  | |  ||  '--'  /|  '--' /'  '-'  '   |  |    
 `--'   `--'`--' '--'`--'  `--' `-----' `-----'    `--' `--'`-------' `------'  `-----'    `--'    
 """

    # Build header block
    header_lines = []
    header_lines.append(art.rstrip())
    if title:
        header_lines.append('')
        header_lines.append(title)
    header_lines.append('')
    header_lines.append(f'Powered by {credit}')
    return '\n'.join(header_lines) + '\n'


def term_print_block(lines, width: int = 40):
    print('\n' + '\n'.join(lines) + '\n')


# Lightweight terminal UI with spinner (no external deps)
# Lightweight terminal UI with spinner (no external deps)
# Rich-based terminal UI
console = Console()

# Configure logging to INFO to suppress debug-level output in the terminal
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger('hybrid_bot')
logger.setLevel(logging.INFO)

# Suppress noisy third-party loggers (e.g., Telethon sync messages)
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pytgcalls').setLevel(logging.WARNING)

def print_term_header(title: str = '', credit: str = 'MRNOL'):
    """Print the ASCII-art header via Rich console."""
    try:
        console.print(term_header(title, credit=credit))
    except Exception:
        console.rule(f"[bold blue]{title}[/bold blue] — Powered by {credit}")

def term_spinner(message: str):
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[bold green]{message}[/bold green]"),
        transient=True,
        console=console
    )

# Custom exception for signaling skip/wait/tombstone actions
class SkipTargetError(Exception):
    pass
# --- Premium emoji helper ---
import re
async def parse_premium_emojis(client, text):
    """
    Replace :custom_emoji_id: in text with MessageEntityCustomEmoji if possible.
    Example: 'Hello <emoji_id:1234567890123456789>'
    """
    if not MessageEntityCustomEmoji:
        return text, None
    # Find all <emoji_id:...> or :emoji_id: patterns
    pattern = r'<emoji_id:(\d+)>|:([0-9]{19,20}):'
    entities = []
    for match in re.finditer(pattern, text):
        emoji_id = match.group(1) or match.group(2)
        if emoji_id:
            entities.append(MessageEntityCustomEmoji(
                offset=match.start(),
                length=len(match.group(0)),
                document_id=int(emoji_id)
            ))
    # Remove the emoji_id markup from text for display
    clean_text = re.sub(pattern, '', text)
    return clean_text, entities if entities else None
    """Exception raised to signal that a target should be skipped, waited, or tombstoned."""
    def __init__(self, action='skip', wait_seconds=0, reason=''):
        """
        Args:
            action: 'skip', 'wait', or 'tombstone'
            wait_seconds: How long to wait (for 'skip' or 'wait' actions)
            reason: Description of why this action is needed
        """
        self.action = action
        self.wait_seconds = wait_seconds
        self.reason = reason
        super().__init__(f"{action.upper()}: {reason} (wait={wait_seconds}s)")
 
class TerminalUI:
    """Minimal terminal UI wrapper using rich. Provides header, print_block and spinner."""
    def __init__(self, credit: str = 'MRNOL'):
        self.console = console
        self.credit = credit

    def header(self, title: str):
        # Print ASCII-art header via rich console
        try:
            self.console.print(term_header(title, credit=self.credit))
        except Exception:
            self.console.rule(f"[bold blue]{title}[/bold blue] — Powered by {self.credit}")

    def print_block(self, lines):
        for line in lines:
            self.console.print(line)

    def spinner(self, message: str):
        return Progress(SpinnerColumn(), TextColumn(f"[bold green]{message}[/bold green]"), transient=True, console=self.console)


term_ui = TerminalUI()


async def startup_animation(title: str = 'STARTING HYBRID AD BOT', credit: str = 'MRNOL', duration: float = 1.2):
    """Display a clean startup screen."""
    # Clear screen for better visual
    console.clear()
    
    # Simple header
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold white]{title.center(60)}[/bold white]")
    console.print(f"[dim]{f'Powered by {credit}'.center(60)}[/dim]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")
    
    # Short loading animation
    with console.status("[bold green]Initializing...", spinner="dots") as status:
        await asyncio.sleep(duration)


# Configuration
CONFIG_FILE = 'config.json'
STATS_FILE = 'stats.json'
GROUPS_FILE = 'groups.json'
CREDENTIALS_FILE = 'credentials.csv'

DEFAULT_CONFIG = {
    'message_delay': 30,
    'cycle_delay': 300,
    'max_messages': 999999,  # Unlimited
    'target_groups': [],
    'ad_message': 'Your ad message here',
    'admin_users': [7909897153],
    'min_members': 1,  # No minimum limit
    'max_members': 999999999,  # No maximum limit
    'bot_token': '',
    'log_channel_id': None,  # Channel/Group ID for logs
    'rate_limit_delay': 25,  # Only rate limiting delay
    'unlimited_mode': True,
    'max_forum_topics': 3,  # Maximum topics to send to per forum
    'forum_topic_delay': 5,  # Delay between topics in same forum (seconds)
    'target_topic_name': 'instagram',  # Specific topic name to target in forums
    'set_bio_on_start': True,
    'auto_bio': '🚀 ADBOT Active • Managed by @mrnol',
    'enforce_bio': True,
    'bio_enforce_max_failures': 3,
    'bio_fallback_text': 'AdBotN • MRNOL',
    'bio_enforce_interval_minutes': 15,
    'long_wait_threshold': 1800,
    # Consent settings: require console consent before changing the user's bio
    'owner_chat_id': 7909897153,
    'require_bio_consent': True,
    'bio_consent_given': False,
    'auto_skip_failures': 2,
    # Control which log levels are forwarded to the configured log channel
    # Example: ['START','SEND'] to only forward startup alerts and send events
    'log_channel_send_levels': ['START', 'SEND'],
    'log_channel_send_json': False,
    # Behavior for long FloodWaits: 'tombstone' will mark group blocked (reversible), 'delete' will remove from DB
    'long_wait_action': 'tombstone',
    # If using tombstone, how many days to block by default
    'long_wait_block_days': 7,
    # If true, any FloodWait will be treated as immediate skip for the target (re-raise to caller)
    'skip_on_any_flood': False,
}

class HybridAdBot:
    def __init__(self):
        # ...existing code...
        self._groups_db_path = os.path.abspath('groups_database.json')

    def filter_targets_to_groups(self):
        """Remove all channel IDs from target_groups and groups_database, keeping only groups, supergroups, and forums. Strict: only keep IDs with valid info."""
        # Filter groups_database first
        if hasattr(self, 'groups_database') and isinstance(self.groups_database, dict):
            filtered_db = {}
            valid_ids = set()
            for k, v in self.groups_database.items():
                if v.get('type') in ('group', 'supergroup', 'forum'):
                    filtered_db[k] = v
                    valid_ids.add(int(v.get('id', k)))
            self.groups_database = filtered_db
            try:
                with open(self._groups_db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.log_and_send(f"Error saving filtered groups_database: {e}", "ERROR")
            self.log_and_send(f"Filtered groups_database: now {len(filtered_db)} groups/supergroups/forums only.", "SUCCESS")
        else:
            valid_ids = set()

        # Filter target_groups strictly: only keep IDs present in valid_ids
        tg = self.config.get('target_groups', [])
        filtered_tg = [gid for gid in tg if int(gid) in valid_ids]
        self.config['target_groups'] = filtered_tg
        self.save_config()
        self.log_and_send(f"Filtered target_groups: now {len(filtered_tg)} groups/supergroups/forums only.", "SUCCESS")


    def auto_clean_duplicates(self):
        """Remove duplicate group IDs from target_groups and groups_database, save changes."""
        # Clean target_groups
        tg = self.config.get('target_groups', [])
        unique_tg = list(dict.fromkeys(tg))
        if len(unique_tg) != len(tg):
            self.config['target_groups'] = unique_tg
            self.save_config()
            self.log_and_send(f"Cleaned duplicates: target_groups now has {len(unique_tg)} unique IDs.", "SUCCESS")

        # Clean groups_database keys
        if hasattr(self, 'groups_database') and isinstance(self.groups_database, dict):
            unique_db = {}
            for k, v in self.groups_database.items():
                key = str(v.get('id', k))
                if key not in unique_db:
                    unique_db[key] = v
            if len(unique_db) != len(self.groups_database):
                self.groups_database = unique_db
                try:
                    with open(self._groups_db_path, 'w', encoding='utf-8') as f:
                        json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.log_and_send(f"Error saving cleaned groups_database: {e}", "ERROR")
                self.log_and_send(f"Cleaned duplicates: groups_database now has {len(unique_db)} unique IDs.", "SUCCESS")

    def __init__(self):
        self.config = self.load_config()
        self.credentials = self.load_credentials()
        self.stats = self.load_stats()
        self.groups_database = self.load_groups_database()
        # Initialize audit DB
        try:
            self._audit_db_path = os.path.abspath('audit.db')
            self.init_audit_db()
        except Exception:
            pass
        
        # Ensure stats has required keys
        if 'total_sent' not in self.stats:
            self.stats['total_sent'] = 0
        if 'last_run' not in self.stats:
            self.stats['last_run'] = None
        if 'groups' not in self.stats:
            self.stats['groups'] = {}
            
        self.user_client = None
        self.bot_client = None
        self.is_sending = False
        # When True (set by admin via Send Ads button) use manual sending mode with shorter cycle delay
        self.manual_mode = False
        self.message_count = 0
        self.is_scraping = False
        self.is_paused = False
        self.session_start_time = datetime.now()
        # in-memory log buffer used until a Telegram client is available
        self._log_buffer = []
        
        # Auto-populate target groups from scraped data on startup
        if not self.config.get('target_groups') or len(self.config['target_groups']) == 0:
            self.log_and_send("No target groups configured, auto-populating from groups database...", "INFO")
            populated = self.auto_populate_target_groups()
            if populated > 0:
                self.log_and_send(f"Auto-populated {populated} target groups from database", "SUCCESS")
        else:
            self.log_and_send(f"Using {len(self.config['target_groups'])} pre-configured target groups", "INFO")
    
    def load_credentials(self):
        """Load credentials from CSV file"""
        credentials = {}
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Skip comment lines
                    if row['credential_type'].startswith('#'):
                        continue
                    
                    cred_type = row['credential_type']
                    # Only load active credentials (default to true if not specified)
                    is_active = row.get('active', 'true').lower() == 'true'
                    if is_active:
                        credentials[cred_type] = {
                            'api_id': row['api_id'],
                            'api_hash': row['api_hash'],
                            'bot_token': row['bot_token'],
                            'phone': row['phone'],
                            'session_name': row['session_name'],
                            'description': row['description']
                        }
            return credentials
        except FileNotFoundError:
            print(term_header('CREDENTIALS MISSING'))
            print(f"Credentials file '{CREDENTIALS_FILE}' not found!")
            print("Please create credentials.csv with required API credentials")
            return {}
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return {}
    
    def get_telegram_credentials(self):
        """Get Telegram API credentials"""
        if 'telegram_api' in self.credentials:
            creds = self.credentials['telegram_api']
            return creds['api_id'], creds['api_hash'], creds['session_name']
        return None, None, None
    
    def get_bot_token(self):
        """Get bot token"""
        if 'bot_token' in self.credentials:
            return self.credentials['bot_token']['bot_token']
        return self.config.get('bot_token', '')

    async def ensure_user_authorized(self, client, max_attempts: int = 3):
        """Ensure the user client is authorized. Prompts for phone/code/password with a clean UI."""
        if await client.is_user_authorized():
            return True

        print(term_header('USER LOGIN'))

        attempts = 0
        while attempts < max_attempts:
            phone = input("  Phone (with country code, e.g. +123...): ")
            if not phone.strip():
                print("Phone is required. Try again.")
                attempts += 1
                continue

            try:
                await client.send_code_request(phone)
            except Exception as e:
                print(f"Failed to send code: {e}")
                attempts += 1
                continue

            code = input("  Enter OTP code: ")
            try:
                await client.sign_in(phone, code)
                # Ask for consent before updating bio, if required
                if self.config.get('set_bio_on_start') and self.config.get('auto_bio'):
                    if self.config.get('require_bio_consent') and not self.config.get('bio_consent_given'):
                        consent = input("Do you consent to update your Telegram bio to the advertised text? (yes/no): ")
                        if consent.strip().lower() in ('y', 'yes'):
                            self.config['bio_consent_given'] = True
                            self.save_config()
                        else:
                            print("Bio update skipped (consent not given).")
                            return True

                    if self.config.get('bio_consent_given'):
                        try:
                            await client(UpdateProfileRequest(about=self.config.get('auto_bio')))
                        except Exception:
                            pass
                return True
            except SessionPasswordNeededError:
                # handle 2FA
                pwd = input("  Two-step password required. Enter your password: ")
                try:
                    await client.sign_in(password=pwd)
                    return True
                except Exception as e:
                    print(f"Password sign-in failed: {e}")
                    attempts += 1
                    continue
            except Exception as e:
                print(f"Sign-in failed: {e}")
                attempts += 1
                continue

        print("Failed to authenticate after multiple attempts.")
        return False
    async def interactive_setup_and_authorize(self):
        """Interactive first-time setup: collect credentials, perform user login (with 2FA), and save credentials."""
        client = None
        try:
            print(term_header('FIRST-TIME SETUP', credit='MRNOL'))
            api_id = input("Telegram API ID: ").strip()
            api_hash = input("Telegram API Hash: ").strip()
            phone = input("Phone (with country code, e.g. +123...): ").strip()
            session_name = input("Session name [pure_user_session]: ").strip() or 'pure_user_session'
            bot_token = input("Bot token (optional, press Enter to skip): ").strip()

            # Prompt for owner chat ID
            owner_id = input("Owner chat ID (your Telegram user ID, required for admin): ").strip()
            if owner_id:
                try:
                    owner_id_int = int(owner_id)
                    self.config['owner_chat_id'] = owner_id_int
                    # Also add to admin_users if not present
                    if 'admin_users' in self.config and owner_id_int not in self.config['admin_users']:
                        self.config['admin_users'].append(owner_id_int)
                    # Persist the owner chat id and admin list to the config file
                    try:
                        self.save_config()
                    except Exception:
                        # If saving fails, continue but warn the user
                        print("Warning: failed to write owner_chat_id to config.json")
                except Exception:
                    print("Invalid owner chat ID. It must be a number.")
                    return False

            # Validate api_id is an integer
            try:
                api_id_int = int(api_id)
            except Exception:
                print("Invalid Telegram API ID. It must be a number.")
                return False

            # Create a Telethon client for the user session and authorize
            client = TelegramClient(session_name, api_id_int, api_hash)
            try:
                await client.connect()
            except Exception:
                # Some environments require start() instead
                try:
                    await client.start()
                except Exception as e:
                    print(f"Failed to start Telegram client: {e}")
                    return False

            # Ensure the user is authorized (prompts for phone/code/password as needed)
            ok = await self.ensure_user_authorized(client)
            if not ok:
                try:
                    await client.disconnect()
                except Exception:
                    pass
                return False

            # At this point client should be authorized — save credentials to CSV
            try:
                with open(CREDENTIALS_FILE, 'w', encoding='utf-8', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["credential_type","api_id","api_hash","bot_token","phone","session_name","description","active"])
                    writer.writerow(["telegram_api", api_id, api_hash, "", phone, session_name, "Auto-created user session", "true"])
                    if bot_token:
                        writer.writerow(["bot_token","","", bot_token, "", "", "Bot token from BotFather", "true"])
            except Exception as e:
                print(f"Failed to save credentials.csv: {e}")

            # Reload credentials and set user_client
            self.credentials = self.load_credentials()
            self.user_client = client
            print("Setup complete — credentials saved and user client authenticated.")
            return True

        except Exception as e:
            print(f"Interactive setup failed: {e}")
            try:
                if client:
                    await client.disconnect()
            except Exception:
                pass
            return False
    
    async def handle_scraping_task(self, original_event):
        """Handle scraping in background and update the original message"""
        try:
            count = await self.scrape_groups()
            # Try to edit the original message
            try:
                await original_event.edit(f"🎉 **UNLIMITED SCRAPING COMPLETE!**\n\n✅ Scraped: {count} groups/channels\n📊 All groups saved to database\n\nUse /addgroup [ID] to add targets.")
            except:
                # If we can't edit, send a new message via bot
                if hasattr(self, 'bot_client'):
                    try:
                        await self.bot_client.send_message(
                            original_event.chat_id,
                            f"🎉 **UNLIMITED SCRAPING COMPLETE!**\n\n✅ Scraped: {count} groups/channels\n📊 All groups saved to database\n\nUse /addgroup [ID] to add targets."
                        )
                    except:
                        pass
        except Exception as e:
            print(f"❌ Background scraping error: {e}")
    
    async def safe_callback_answer(self, event, message="✅ Done!", edit_text=None):
        """Safely answer callback queries with error handling"""
        try:
            if edit_text:
                # Set a shorter timeout for edits
                await asyncio.wait_for(event.edit(edit_text), timeout=5.0)
            else:
                # Set a shorter timeout for answers
                await asyncio.wait_for(event.answer(message), timeout=3.0)
            return True
        except asyncio.TimeoutError:
            print(f"⚠️ Callback operation timed out")
            return False
        except QueryIdInvalidError:
            print(f"⚠️ Callback query expired, ignoring answer attempt")
            return False
        except Exception as e:
            print(f"❌ Callback answer error: {e}")
            return False

    # ---- Audit DB helpers ----
    def init_audit_db(self):
        conn = sqlite3.connect(self._audit_db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                actor TEXT,
                details TEXT,
                ts TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def record_audit(self, action, actor, details=''):
        try:
            conn = sqlite3.connect(self._audit_db_path)
            cur = conn.cursor()
            cur.execute('INSERT INTO audit (action, actor, details, ts) VALUES (?,?,?,?)',
                        (action, str(actor), str(details), datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to write audit: {e}")

    async def cleanup_groups_database(self, dry_run=True, max_checks=None):
        """Prune unreachable or invalid group IDs from groups_database.
        If dry_run is True, returns a list of bad ids without saving.
        max_checks limits how many entries to test (None = all).
        """
        bad_ids = []
        total = 0
        try:
            keys = list(self.groups_database.keys()) if getattr(self, 'groups_database', None) else []
            if max_checks:
                keys = keys[:int(max_checks)]

            for gid in keys:
                total += 1
                try:
                    await self.user_client.get_entity(gid)
                except Exception as e:
                    msg = str(e)
                    # treat as unreachable/migrated
                    bad_ids.append((gid, msg))

            if dry_run:
                return {'checked': total, 'bad': bad_ids}

            # Remove bad ids and save
            for gid, _ in bad_ids:
                try:
                    del self.groups_database[gid]
                except Exception:
                    pass
            # persist
            try:
                with open(self._groups_db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.log_and_send(f"Failed to save cleaned groups_database: {e}", "ERROR")

            return {'checked': total, 'removed': [g for g, _ in bad_ids]}
        except Exception as e:
            return {'error': str(e)}

    def mark_group_blocked(self, group_id, reason='', block_minutes=60*24):
        """Mark a group as blocked in groups_database so future sends skip it.
        block_minutes defaults to 1 day.
        """
        try:
            if not getattr(self, 'groups_database', None):
                self.groups_database = {}
            now = datetime.now()
            blocked_until = (now + timedelta(minutes=int(block_minutes))).isoformat()
            # normalize key as string
            key = str(group_id)
            if key not in self.groups_database:
                self.groups_database[key] = {'id': group_id, 'title': None}
            self.groups_database[key]['blocked'] = True
            self.groups_database[key]['blocked_until'] = blocked_until
            self.groups_database[key]['blocked_reason'] = str(reason)
            # persist safely
            try:
                db_path = os.path.abspath('groups_database.json')
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.log_and_send(f"Failed to persist blocked state for {group_id}: {e}", "WARN")
            self.log_and_send(f"Marked {group_id} as blocked until {blocked_until}: {reason}", "WARN")
        except Exception as e:
            self.log_and_send(f"Error marking group blocked {group_id}: {e}", "ERROR")

    def increment_group_failure(self, group_id, limit=2):
        """Increment a failure counter for a group and mark blocked if limit exceeded."""
        try:
            key = str(group_id)
            if not getattr(self, 'groups_database', None):
                self.groups_database = {}
            if key not in self.groups_database:
                self.groups_database[key] = {'id': group_id, 'title': None}
            failures = int(self.groups_database[key].get('failures', 0)) + 1
            self.groups_database[key]['failures'] = failures
            # Persist
            try:
                db_path = os.path.abspath('groups_database.json')
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            if failures >= int(self.config.get('auto_skip_failures', limit)):
                # mark blocked if repeated failures
                try:
                    self.mark_group_blocked(group_id, reason=f'auto_failures={failures}', block_minutes=60*24)
                except Exception:
                    pass
                return True
            return False
        except Exception:
            return False

    def is_group_blocked(self, group_id):
        """Return True if the group is currently marked blocked in groups_database."""
        try:
            key = str(group_id)
            gd = (self.groups_database or {}).get(key)
            if not gd:
                return False
            if not gd.get('blocked'):
                return False
            blocked_until = gd.get('blocked_until')
            # If no expiry is set, treat as permanently blocked
            if not blocked_until:
                return True

            # Helper: try several parsing strategies for ISO-like timestamps
            def _parse_iso(s):
                from datetime import datetime as _dt
                # Try direct fromisoformat first
                try:
                    return _dt.fromisoformat(s)
                except Exception:
                    pass
                # Handle trailing Z (UTC)
                try:
                    if s.endswith('Z'):
                        return _dt.fromisoformat(s.replace('Z', '+00:00'))
                except Exception:
                    pass
                # Try common strptime patterns
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
                # Give up
                return None

            until = _parse_iso(blocked_until)
            if not until:
                # Can't parse -> keep blocked (safer)
                return True

            now = datetime.now(until.tzinfo) if until.tzinfo else datetime.now()
            if now < until:
                return True

            # expired -> auto-unblock and persist change
            try:
                gd.pop('blocked', None)
                gd.pop('blocked_until', None)
                gd.pop('blocked_reason', None)
                try:
                    self._write_json_atomic('groups_database.json', self.groups_database)
                except Exception as e:
                    self.log_and_send(f"Failed persisting auto-unblock for {group_id}: {e}", "WARN")
                self.log_and_send(f"Auto-unblocked group {group_id} (blocked_until passed)", "INFO")
            except Exception:
                pass
            return False
        except Exception:
            return False

    def normalize_group_id(self, group_id):
        """Normalize a group id: convert numeric strings to int when appropriate."""
        try:
            if isinstance(group_id, str):
                s = group_id.strip()
                if s.startswith('-') and s[1:].isdigit():
                    return int(s)
                if s.isdigit():
                    return int(s)
            return group_id
        except Exception:
            return group_id

    # ---- Groups DB management helpers for admin commands ----
    def list_blocked_groups(self):
        """Return a list of (group_id, meta) for currently blocked groups."""
        try:
            out = []
            for gid, meta in (self.groups_database or {}).items():
                if meta and meta.get('blocked'):
                    out.append((gid, meta))
            return out
        except Exception:
            return []

    def unblock_group(self, group_id):
        """Clear blocked state and failure counters for a group and persist DB."""
        try:
            gid = self.normalize_group_id(group_id)
            if gid in self.groups_database:
                meta = self.groups_database[gid]
                meta.pop('blocked', None)
                meta.pop('blocked_until', None)
                meta.pop('failure_count', None)
                meta.pop('topic_failures', None)
                meta.pop('deleted_topics', None)
                # persist
                self._write_json_atomic('groups_database.json', self.groups_database)
                return True
            return False
        except Exception:
            return False

    def list_topic_failures(self, group_id):
        """Return topic_failures dict for a group or empty dict."""
        try:
            gid = self.normalize_group_id(group_id)
            meta = self.groups_database.get(gid, {})
            return meta.get('topic_failures', {})
        except Exception:
            return {}

    def clear_topic_failures(self, group_id):
        """Clear topic_failures for a group and persist DB."""
        try:
            gid = self.normalize_group_id(group_id)
            if gid in self.groups_database:
                meta = self.groups_database[gid]
                meta['topic_failures'] = {}
                # also remove deleted_topics tombstones if present
                meta.pop('deleted_topics', None)
                self._write_json_atomic('groups_database.json', self.groups_database)
                return True
            return False
        except Exception:
            return False

    async def ensure_client_connected(self, client, max_attempts: int = 5, base_delay: float = 2.0):
        """Ensure the given Telethon client is connected; try to reconnect with exponential backoff.

        Returns True if connected, False otherwise.
        """
        try:
            if client is None:
                return False
            # Telethon clients have .is_connected() (async) in newer versions; use attribute where possible
            try:
                is_conn = await client.is_connected()
            except Exception:
                # Fallback: assume client has .connect method and check via ._client
                try:
                    is_conn = client.session and client.session.auth_key is not None
                except Exception:
                    is_conn = False

            if is_conn:
                return True

            attempt = 0
            delay = base_delay
            while attempt < max_attempts:
                try:
                    self.log_and_send(f"Attempting to reconnect client (attempt {attempt+1}/{max_attempts})...", "WARN")
                    await client.connect()
                    try:
                        ok = await client.is_connected()
                    except Exception:
                        ok = True
                    if ok:
                        self.log_and_send("Client reconnected", "INFO")
                        return True
                except Exception as e:
                    self.log_and_send(f"Reconnect attempt {attempt+1} failed: {e}", "WARN")
                attempt += 1
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
            self.log_and_send("Failed to reconnect client after multiple attempts", "ERROR")
            return False
        except Exception as e:
            self.log_and_send(f"ensure_client_connected unexpected error: {e}", "ERROR")
            return False

    # ---- Resilient sending helper ----
    def _classify_send_exception(self, exc):
        """Classify exceptions and either return a dict or raise SkipTargetError.

        Returns: None meaning continue normal retry logic, or raises SkipTargetError(action, wait_seconds, reason)
        where action is one of: 'skip', 'tombstone', 'delete', 'wait'
        """
        try:
            # FloodWaitError -> may include seconds
            if isinstance(exc, FloodWaitError):
                seconds = int(getattr(exc, 'seconds', 0) or 0)
                # If configured to skip on any flood, instruct skip
                if str(self.config.get('skip_on_any_flood', False)).lower() in ('1', 'true', 'yes'):
                    raise SkipTargetError('skip', wait_seconds=seconds, reason='FloodWait')
                # If it's longer than configured long_wait_threshold -> tombstone or delete
                try:
                    threshold = int(self.config.get('long_wait_threshold', 1800))
                except Exception:
                    threshold = 1800
                if seconds > threshold:
                    action = self.config.get('long_wait_action', 'tombstone') or 'tombstone'
                    raise SkipTargetError(action, wait_seconds=seconds, reason='long_flood')
                # Else, instruct caller to wait
                raise SkipTargetError('wait', wait_seconds=seconds, reason='flood')

            # PersistentTimestampOutdatedError - treat as recoverable but skip this target for now
            if isinstance(exc, PersistentTimestampOutdatedError):
                raise SkipTargetError('skip', reason='PersistentTimestampOutdated')

            # Textual detection
            txt = str(exc)
            if 'A wait of' in txt and 'seconds is required' in txt:
                import re
                m = re.search(r"A wait of (\d+) seconds is required", txt)
                if m:
                    seconds = int(m.group(1))
                    if str(self.config.get('skip_on_any_flood', False)).lower() in ('1', 'true', 'yes'):
                        raise SkipTargetError('skip', wait_seconds=seconds, reason='textual_flood')
                    try:
                        threshold = int(self.config.get('long_wait_threshold', 1800))
                    except Exception:
                        threshold = 1800
                    if seconds > threshold:
                        action = self.config.get('long_wait_action', 'tombstone') or 'tombstone'
                        raise SkipTargetError(action, wait_seconds=seconds, reason='textual_long_flood')
                    raise SkipTargetError('wait', wait_seconds=seconds, reason='textual_flood')

            # Write forbidden or banned
            forbid_markers = ['You can\'t write in this chat', 'CHAT_WRITE_FORBIDDEN', 'USER_BANNED_IN_CHANNEL', 'USER_BAN', "You can't write in this chat"]
            for fm in forbid_markers:
                if fm in txt:
                    raise SkipTargetError('tombstone', reason='write_forbidden')

            # Topic deleted / closed
            if 'The topic was deleted' in txt or 'topic was deleted' in txt or 'TOPIC_CLOSED' in txt:
                raise SkipTargetError('tombstone', reason='topic_deleted')

            # Entity not found / migrated
            if 'Cannot find any entity' in txt or 'ENTITY_MIGRATE' in txt:
                raise SkipTargetError('skip', reason='entity_missing')

        except SkipTargetError:
            # re-raise to caller
            raise
        except Exception:
            # classification failed: continue normal handling
            return None

    async def safe_send_message(self, client, entity, message, **kwargs):
        """Send a message with FloodWait handling, retries and exponential backoff.
        Returns the sent message object or raises the last exception."""
        max_retries = int(self.config.get('max_send_retries', 5))
        base_delay = float(self.config.get('rate_limit_delay', 5))
        attempt = 0
        last_exc = None
        # --- Premium emoji support ---
        if MessageEntityCustomEmoji and isinstance(message, str):
            clean_text, entities = await parse_premium_emojis(client, message)
            if entities:
                kwargs['entities'] = entities
                message = clean_text
        while attempt <= max_retries:
            try:
                msg = await client.send_message(entity, message, **kwargs)
                # small fixed delay after a successful send to respect rate limits
                await asyncio.sleep(base_delay)
                return msg
            except FloodWaitError as fw:
                # Classify and signal caller what to do (skip/wait/tombstone)
                try:
                    self._classify_send_exception(fw)
                except SkipTargetError:
                    # Re-raise a SkipTargetError for caller to handle
                    raise
                # If classifier returned None, fallback to default behavior
                wait = min(fw.seconds, 3600)
                self.log_and_send(f"FloodWait {wait}s for {entity}", "WAIT")
                await asyncio.sleep(wait)
                last_exc = fw
                attempt += 1
                continue
            except Exception as e:
                # Detect textual flood/wait messages returned by the server and treat as FloodWait
                try:
                    import re
                    txt = str(e)
                    m = re.search(r"A wait of (\d+) seconds is required", txt)
                    if m:
                        wait = min(int(m.group(1)), 3600)
                        # let classifier decide if we should skip
                        try:
                            self._classify_send_exception(e)
                        except SkipTargetError:
                            raise
                        self.log_and_send(f"Server requested wait {wait}s for {entity}", "WAIT")
                        await asyncio.sleep(wait)
                        last_exc = e
                        attempt += 1
                        continue
                except Exception:
                    pass
                # If error indicates server closed connection or zero-bytes read, try reconnecting once
                try:
                    txtlow = str(e).lower()
                    if 'server closed the connection' in txtlow or '0 bytes read' in txtlow or 'connection reset by peer' in txtlow:
                        # Attempt to reconnect client before counting this as a failure
                        try:
                            ok = await self.ensure_client_connected(client)
                            if ok:
                                # Retry send immediately
                                attempt += 1
                                continue
                        except Exception:
                            pass
                except Exception:
                    pass

                # Use classifier to decide whether to skip/tombstone/delete
                try:
                    self._classify_send_exception(e)
                except SkipTargetError:
                    raise
                # If classifier didn't instruct skip, fall back to existing heuristics
                msg = str(e)
                if ('TOPIC_CLOSED' in msg or 'The topic was deleted' in msg or 'topic was deleted' in msg
                        or 'Cannot find any entity' in msg or 'ENTITY_MIGRATE' in msg
                        or "You can't write in this chat" in msg or 'CHAT_WRITE_FORBIDDEN' in msg
                        or 'USER_BANNED_IN_CHANNEL' in msg or 'USER_BAN' in msg):
                    raise e
                last_exc = e
                # jittered exponential backoff
                backoff = base_delay * (2 ** attempt) + random.random()
                self.log_and_send(f"Send attempt {attempt} failed for {entity}: {e}; backing off {backoff}s", "WARN")
                await asyncio.sleep(backoff)
                attempt += 1
                continue

        # all retries exhausted
        raise last_exc if last_exc else Exception("Unknown send failure")

    # ---- Resilient forwarding helper ----
    async def safe_forward_message(self, client, target, from_chat, message_id, event=None, **kwargs):
        """Forward a message with retries and floodwait handling. Replies with error details if event is provided."""
        max_retries = int(self.config.get('max_send_retries', 5))
        base_delay = float(self.config.get('rate_limit_delay', 5))
        attempt = 0
        last_exc = None
        while attempt <= max_retries:
            try:
                # If from_chat is a username string, resolve to an entity first
                resolved_from = from_chat
                if isinstance(from_chat, str) and not from_chat.startswith('-'):
                    try:
                        # Prefer the user client for resolution if available
                        resolver = client
                        try:
                            # If bot has a user_client use that to resolve (more permissions)
                            if hasattr(self, 'user_client') and self.user_client:
                                resolver = self.user_client
                        except Exception:
                            pass
                        resolved_from = await resolver.get_entity(from_chat)
                    except Exception:
                        # leave as-is; Telethon may still accept username strings
                        resolved_from = from_chat

                await client.forward_messages(target, message_id, resolved_from)
                await asyncio.sleep(base_delay)
                return True
            except FloodWaitError as fw:
                wait = min(fw.seconds, 3600)
                msg = f"Forward FloodWait {wait}s for {target}"
                self.log_and_send(msg, "WAIT")
                if event:
                    await event.reply(f"⚠️ {msg}")
                await asyncio.sleep(wait)
                last_exc = fw
                attempt += 1
                continue
            except Exception as e:
                import re
                txt = str(e)
                m = re.search(r"A wait of (\d+) seconds is required", txt)
                if m:
                    wait = min(int(m.group(1)), 3600)
                    msg = f"Server requested wait {wait}s for forward to {target}"
                    self.log_and_send(msg, "WAIT")
                    if event:
                        await event.reply(f"⚠️ {msg}")
                    await asyncio.sleep(wait)
                    last_exc = e
                    attempt += 1
                    continue
                txtlow = txt.lower()
                if 'server closed the connection' in txtlow or '0 bytes read' in txtlow or 'connection reset by peer' in txtlow:
                    try:
                        ok = await self.ensure_client_connected(client)
                        if ok:
                            attempt += 1
                            continue
                    except Exception:
                        pass
                msg = str(e)
                # Permission/entity errors: reply with details
                if ('TOPIC_CLOSED' in msg or 'The topic was deleted' in msg or 'topic was deleted' in msg
                        or 'Cannot find any entity' in msg or 'ENTITY_MIGRATE' in msg
                        or "You can't write in this chat" in msg or 'CHAT_WRITE_FORBIDDEN' in msg
                        or 'USER_BANNED_IN_CHANNEL' in msg or 'USER_BAN' in msg):
                    self.log_and_send(f"Forward error: {msg}", "ERROR")
                    if event:
                        await event.reply(f"❌ Forward error: {msg}")
                    raise e
                backoff = base_delay * (2 ** attempt) + random.random()
                self.log_and_send(f"Forward attempt {attempt} failed for {target}: {e}; backing off {backoff}s", "WARN")
                if event:
                    await event.reply(f"❌ Forward attempt {attempt} failed: {e}")
                await asyncio.sleep(backoff)
                last_exc = e
                attempt += 1
                continue
        # Final failure: reply with last error
        if event and last_exc:
            await event.reply(f"❌ Forwarding failed: {last_exc}")
        raise last_exc if last_exc else Exception("Unknown forward failure")

    async def _deliver_ad_to_target(self, target_id, reply_to=None):
        """Deliver ad to a target by forwarding if configured, otherwise send text.
        Returns True on success, raises exception on failure.
        """
        # Prefer forwarding when configured and source present
        forward_chat = self.config.get('ad_forward_from_chat')
        forward_msg = self.config.get('ad_forward_message_id')
        if forward_chat and forward_msg:
            try:
                await self.safe_forward_message(self.user_client, target_id, forward_chat, forward_msg)
                return True
            except Exception as e:
                # re-raise to be handled by caller
                raise
        # fallback: send text (could be forum reply)
        text = self.config.get('ad_message', '')
        if reply_to:
            return await self.safe_send_message(self.user_client, target_id, text, reply_to=reply_to)
        return await self.safe_send_message(self.user_client, target_id, text)
    
    async def log_to_channel(self, message, level="INFO"):
        """Send logs to specified channel/group"""
        try:
            channel_id = self.config.get('log_channel_id')
            if not channel_id:
                # no log channel configured
                return

            # Only forward certain levels to the log channel
            allowed = self.config.get('log_channel_send_levels', []) or []
            # Normalize level comparison
            if level not in allowed and level.upper() not in [l.upper() for l in allowed]:
                # Skip sending this level to channel
                return

            timestamp = datetime.now().strftime("%H:%M:%S")
            # If configured, send JSON-formatted logs for easier processing in channels
            if self.config.get('log_channel_send_json'):
                import json as _json
                payload = {
                    'level': level,
                    'timestamp': timestamp,
                    'message': message
                }
                # Send as a formatted code block so it remains parseable in Telegram
                log_message = "```" + _json.dumps(payload, indent=2, ensure_ascii=False) + "\n```"
            else:
                log_message = f"[{level}] {timestamp}\n{message}"

            # Prefer user_client if available (user sessions often have broader permissions)
            client = None
            if hasattr(self, 'user_client') and self.user_client:
                client = self.user_client
            elif hasattr(self, 'bot_client') and self.bot_client:
                client = self.bot_client

            if not client:
                print(f"Failed to send log: no Telegram client available to send message to {channel_id}")
                return

            await client.send_message(channel_id, log_message)
        except Exception as e:
            print(f"Failed to send log to {self.config.get('log_channel_id')}: {e}")

    def has_active_client(self):
        """Return True if either user_client or bot_client exists (not None)."""
        return (hasattr(self, 'user_client') and self.user_client) or (hasattr(self, 'bot_client') and self.bot_client)
    
    def log_and_send(self, message, level="INFO"):
        """Print and send log simultaneously with clean formatting"""
        # Only print non-debug messages to the terminal to keep output clean
        lvl = str(level).upper()
        
        # Define simple prefixes and colors for each log level
        log_styles = {
            'INFO': ('cyan', 'INFO'),
            'SUCCESS': ('green', 'SUCCESS'),
            'SEND': ('blue', 'SEND'),
            'WARN': ('yellow', 'WARN'),
            'WARNING': ('yellow', 'WARN'),
            'ERROR': ('red', 'ERROR'),
            'WAIT': ('magenta', 'WAIT'),
            'START': ('bright_green', 'START'),
            'STOP': ('bright_red', 'STOP'),
            'SCRAPE': ('bright_cyan', 'SCRAPE'),
        }
        
        if lvl != 'DEBUG':
            color, label = log_styles.get(lvl, ('white', lvl))
            console.print(f"[{color}][{label}][/{color}] {message}")

        # Buffer or record DEBUG-level messages without printing to the terminal
        if lvl == 'DEBUG':
            try:
                self.record_audit('DEBUG', 'system', message)
            except Exception:
                pass
            # also log via Python logger at DEBUG level (will be suppressed by logger level)
            logger.debug(message)

        # Only send/buffer messages whose level is configured to be forwarded
        allowed = self.config.get('log_channel_send_levels', []) or []
        if level not in allowed and level.upper() not in [l.upper() for l in allowed]:
            return

        # If there's an active client, send immediately, otherwise buffer
        if self.has_active_client():
            asyncio.create_task(self.log_to_channel(message, level))
        else:
            # Buffer tuples of (message, level)
            self._log_buffer.append((message, level))

    async def flush_log_buffer(self):
        """Send any buffered logs once a Telegram client is available."""
        if not self._log_buffer:
            return
        if not self.has_active_client():
            return
        # send buffered messages sequentially to preserve order
        for message, level in list(self._log_buffer):
            try:
                await self.log_to_channel(message, level)
            except Exception as e:
                print(f"Failed flushing buffered log: {e}")
        # clear buffer after attempting
        self._log_buffer.clear()

    async def set_user_bio(self, client):
        """Set the user's bio (about) if configured in config."""
        # New behavior: return (success: bool, info: str) for diagnostics
        target_bio = self.config.get('auto_bio')
        if not target_bio:
            self.log_and_send('No auto_bio configured; skipping set_user_bio', 'INFO')
            return False, 'no_auto_bio'

        if not client:
            self.log_and_send('No client provided for set_user_bio', 'WARN')
            return False, 'no_client'

        # Ensure this is a user session and authorized
        try:
            if not await client.is_user_authorized():
                self.log_and_send('Client not authorized; cannot set bio', 'WARN')
                return False, 'not_authorized'
        except Exception as e:
            self.log_and_send(f'Failed to verify client authorization state: {e}', 'WARN')
            return False, f'auth_check_failed: {e}'

        # Trim bio to avoid exceeding Telegram limits (conservative)
        bio = target_bio
        max_about = 70
        if len(bio) > max_about:
            bio = bio[:max_about]

        # Fetch current about for diagnostics
        try:
            me = await client.get_me()
            current_about = getattr(me, 'about', None)
        except Exception as e:
            current_about = None
            self.log_and_send(f'Failed to fetch current profile: {e}', 'WARN')

        if current_about == bio:
            # Already set, no need to log
            return True, 'already_set'
        # Attempt to update the profile about text
        try:
            # Use Telethon UpdateProfileRequest to set the 'about' field
            await client(UpdateProfileRequest(about=bio))
            # Don't log to keep terminal clean
            return True, 'updated'
        except Exception as e:
            # Only log failures
            self.log_and_send(f'Failed to set user bio: {e}', 'WARN')
            return False, f'set_failed: {e}'

    # ---- Bot admin command handlers (list/unblock topics/groups) ----
    async def _handle_listblocked(self, event):
        """Bot command: /listblocked - lists currently blocked groups with metadata."""
        try:
            blocked = self.list_blocked_groups()
            if not blocked:
                await event.respond('No blocked groups.')
                return
            lines = []
            for gid, meta in blocked:
                s = f"ID: {gid} — blocked_until: {meta.get('blocked_until')} failures: {meta.get('failure_count',0)}"
                lines.append(s)
            await event.respond('\n'.join(lines))
        except Exception as e:
            await event.respond(f'Error listing blocked groups: {e}')

    async def _handle_unblock(self, event):
        """Bot command: /unblock <id> - clear blocked state for a group id"""
        try:
            text = (event.raw_text or '').strip()
            parts = text.split()
            if len(parts) < 2:
                await event.respond('Usage: /unblock <group_id>')
                return
            gid = parts[1]
            ok = self.unblock_group(gid)
            if ok:
                await event.respond(f'Group {gid} unblocked and failure counters cleared.')
            else:
                await event.respond(f'Group {gid} not found in database.')
        except Exception as e:
            await event.respond(f'Error unblocking group: {e}')

    async def _handle_listtopicfails(self, event):
        """Bot command: /listtopicfails <group_id> - show per-topic failure counts for a forum/group"""
        try:
            text = (event.raw_text or '').strip()
            parts = text.split()
            if len(parts) < 2:
                await event.respond('Usage: /listtopicfails <group_id>')
                return
            gid = parts[1]
            tf = self.list_topic_failures(gid)
            if not tf:
                await event.respond('No topic failures recorded for this group.')
                return
            lines = []
            for topic_id, count in tf.items():
                lines.append(f'{topic_id}: {count}')
            await event.respond('\n'.join(lines))
        except Exception as e:
            await event.respond(f'Error listing topic failures: {e}')

    async def _handle_cleartopicfails(self, event):
        """Bot command: /cleartopicfails <group_id> - clear per-topic failure counters and tombstones"""
        try:
            text = (event.raw_text or '').strip()
            parts = text.split()
            if len(parts) < 2:
                await event.respond('Usage: /cleartopicfails <group_id>')
                return
            gid = parts[1]
            ok = self.clear_topic_failures(gid)
            if ok:
                await event.respond(f'Topic failures and tombstones cleared for group {gid}.')
            else:
                await event.respond(f'Group {gid} not found in database.')
        except Exception as e:
            await event.respond(f'Error clearing topic failures: {e}')

        # Try to update
        try:
            await client(UpdateProfileRequest(about=bio))
        except Exception as e:
            self.log_and_send(f'UpdateProfileRequest failed: {e}', 'WARN')
            return False, f'update_failed: {e}'

        # Verify change using both get_me and GetFullUserRequest for deeper diagnostics
        try:
            me2 = await client.get_me()
            new_about = getattr(me2, 'about', None)
        except Exception as e:
            self.log_and_send(f'Failed to re-fetch profile after update: {e}', 'WARN')
            new_about = None

        full_about = None
        full_repr = None
        try:
            full = await client(GetFullUserRequest(id=me2.id))
            # Try common locations for 'about'
            if hasattr(full, 'about'):
                full_about = getattr(full, 'about')
            elif hasattr(full, 'full_user') and hasattr(full.full_user, 'about'):
                full_about = getattr(full.full_user, 'about')
            elif hasattr(full, 'user') and hasattr(full.user, 'about'):
                full_about = getattr(full.user, 'about')
            full_repr = repr(full)
        except PersistentTimestampOutdatedError as pte:
            # Telethon may surface this when channel diffs / timestamps are stale on server.
            # Try to reconnect and continue gracefully.
            self.log_and_send(f'PersistentTimestampOutdatedError in GetFullUserRequest: {pte}', 'WARN')
            full_repr = f'getfull_failed_persistent:{pte}'
            try:
                await self.ensure_client_connected(client)
            except Exception:
                pass
        except Exception as e:
            self.log_and_send(f'GetFullUserRequest failed: {e}', 'DEBUG')
            full_repr = f'getfull_failed: {e}'

        # Log diagnostics
        self.log_and_send(f'debug: get_me.about={new_about} full_about={full_about} target={bio}', 'DEBUG')
        self.log_and_send(f'debug: me2_repr={repr(me2)}', 'DEBUG')
        self.log_and_send(f'debug: full_repr={full_repr}', 'DEBUG')

        # Decide result
        if new_about == bio or full_about == bio:
            # Don't log to keep terminal clean
            return True, 'ok'
        else:
            self.log_and_send(f'User bio update attempted but verification mismatch (get_me={new_about} full_about={full_about})', 'WARN')
            return False, f'verify_mismatch: get_me={new_about} full={full_about}'

    async def enforce_bio_loop(self):
        """Background loop that enforces the configured bio on the user account every X minutes.

        Uses only the user client (bots cannot change user bios). Interval is configurable
        via `bio_enforce_interval_minutes` in `config.json` (defaults to 15 minutes).
        """
        interval_minutes = self.config.get('bio_enforce_interval_minutes', 15)
        try:
            interval = max(1, int(interval_minutes)) * 60
        except Exception:
            interval = 15 * 60

        # Exponential backoff on repeated failures (multiplier applied to base interval)
        base_interval = interval
        backoff_multiplier = 1
        consecutive_failures = 0

        while True:
            try:
                if not self.config.get('enforce_bio'):
                    await asyncio.sleep(base_interval)
                    continue

                if not self.user_client:
                    self.log_and_send('Bio enforcement skipped: no user client available', 'WARN')
                    await asyncio.sleep(base_interval)
                    continue

                try:
                    if not await self.user_client.is_user_authorized():
                        self.log_and_send('Bio enforcement skipped: user client not authorized', 'WARN')
                        await asyncio.sleep(base_interval)
                        continue

                    success, info = await self.set_user_bio(self.user_client)
                    if success:
                        consecutive_failures = 0
                        backoff_multiplier = 1
                        self.log_and_send('Bio enforcement: updated', 'INFO')
                    else:
                        consecutive_failures += 1
                        self.log_and_send(f'Bio enforcement failed: {info}', 'WARN')
                        # Increase backoff multiplier (max 16x)
                        backoff_multiplier = min(backoff_multiplier * 2, 16)
                        # If repeated failures exceed threshold, attempt fallback and disable automatic enforcement
                        max_fail = int(self.config.get('bio_enforce_max_failures', 3))
                        if consecutive_failures >= max_fail:
                            # Attempt a short fallback bio by temporarily using the fallback text
                            fallback = self.config.get('bio_fallback_text', 'AdBotN')
                            old_bio = self.config.get('auto_bio')
                            try:
                                self.config['auto_bio'] = fallback
                                fb_success, fb_info = await self.set_user_bio(self.user_client)
                            except Exception as e:
                                fb_success, fb_info = False, f'fallback_exception: {e}'
                            finally:
                                # restore original auto_bio
                                try:
                                    self.config['auto_bio'] = old_bio
                                except Exception:
                                    pass
                            # Disable enforcement to avoid further repeated failures
                            self.config['enforce_bio'] = False
                            self.save_config()
                            self.log_and_send(f'Bio enforcement disabled after {consecutive_failures} failures. Fallback result: success={fb_success} info={fb_info}', 'ERROR')
                except Exception as e:
                    consecutive_failures += 1
                    backoff_multiplier = min(backoff_multiplier * 2, 16)
                    self.log_and_send(f'Bio enforcement unexpected error: {e}', 'ERROR')

            except Exception as e:
                # Catch any unexpected error in the loop so it doesn't stop
                consecutive_failures += 1
                backoff_multiplier = min(backoff_multiplier * 2, 16)
                self.log_and_send(f'Unexpected error in bio enforcer loop: {e}', 'ERROR')

            # Sleep scaled by backoff multiplier
            await asyncio.sleep(base_interval * backoff_multiplier)
    
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            config = DEFAULT_CONFIG.copy()
            # Save the default config to file
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return config
    
    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def load_stats(self):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'total_sent': 0, 'last_run': None, 'groups': {}}
    
    def save_stats(self):
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4)
    
    def reset_stats(self):
        """Reset stats to default state"""
        self.stats = {
            'total_sent': 0,
            'last_run': None,
            'groups': {}
        }
        self.message_count = 0
        self.save_stats()
        self.log_and_send("📊 Stats reset to default state", "INFO")
    
    def load_groups(self):
        try:
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            # If no credentials, run setup
            if not self.credentials or (not self.credentials.get('telegram_api') and not self.credentials.get('bot_token')):
                print("No credentials found. Starting setup...")
                self.setup_credentials()

    def setup_credentials(self):
        print(term_header('HYBRID BOT SETUP', credit='MRNOL'))
        term_print_block([
            'Welcome to the Hybrid Bot setup wizard.',
            'Please enter the required information below.',
            '--- Telegram API Setup ---'
        ])
        api_id = input("    Telegram API ID: ")
        api_hash = input("    Telegram API Hash: ")
        phone = input("    Phone number (with country code): ")
        session_name = input("    Session name [pure_user_session]: ") or "pure_user_session"
        bot_token = input("    Bot token (from BotFather, or leave blank): ")
        print("\n--- Saving credentials ---")
        spinner = term_ui.spinner('Saving credentials')
        spinner.start()
        try:
            # Write to credentials.csv
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["credential_type","api_id","api_hash","bot_token","phone","session_name","description","active"])
                writer.writerow(["telegram_api", api_id, api_hash, "", phone, session_name, "Main Telegram API credentials for user client", "true"])
                if bot_token:
                    writer.writerow(["bot_token", "", "", bot_token, "", "", "Bot token from BotFather", "true"])
        finally:
            spinner.stop()
            print('Setup complete. Credentials saved to credentials.csv.')
            print('Please restart the bot to continue.')
            print('\n')
            exit(0)
    
    def save_groups(self, groups):
        """Save groups to both the legacy groups.json and groups_database.json"""
        # Save to legacy format
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, indent=4)
        
        # Convert and save to database format
        groups_db = {}
        for group in (groups or []):
            group_id = group.get('id') if isinstance(group, dict) else None
            if not group_id:
                continue
            
            # Determine group type
            if group.get('is_forum', False):
                group_type = 'forum'
            elif group.get('is_supergroup', False):
                group_type = 'supergroup'
            elif group.get('type') == 'channel' or group.get('is_broadcast', False):
                group_type = 'channel'
            else:
                group_type = 'regular_group'
            
            groups_db[str(group_id)] = {
                'id': group_id,
                'title': group.get('title', 'Unknown'),
                'username': group.get('username'),
                'participant_count': group.get('members', 0),
                'type': 'group' if group_type != 'channel' else 'channel',
                'group_type': group_type,
                'is_forum': group.get('is_forum', False),
                'is_supergroup': group.get('is_supergroup', False),
                'is_broadcast': group.get('is_broadcast', False),
                'scraped_at': group.get('scraped_at')
            }
        
        # Save to groups_database.json
        db_path = os.path.abspath('groups_database.json')
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(groups_db, f, indent=4)
        
        self.log_and_send(f"💾 Saved {len(groups_db)} groups to database", "INFO")
    
    def load_groups_database(self):
        """Load groups database in dictionary format for enhanced classification"""
        # Prefer a dedicated groups database file if present
        db_path = os.path.abspath('groups_database.json')
        fallback_path = os.path.abspath(GROUPS_FILE)

        def _convert_list_to_db(groups_list):
            groups_db = {}
            for group in (groups_list or []):
                group_id = group.get('id') if isinstance(group, dict) else None
                if not group_id:
                    continue
                if group.get('is_forum', False):
                    group_type = 'forum'
                elif group.get('is_supergroup', False):
                    group_type = 'supergroup'
                elif group.get('type') == 'channel' or group.get('is_broadcast', False):
                    group_type = 'channel'
                else:
                    group_type = 'regular_group'

                groups_db[group_id] = {
                    'id': group_id,
                    'title': group.get('title', 'Unknown'),
                    'username': group.get('username'),
                    'participant_count': group.get('members', 0),
                    'type': 'group' if group_type != 'channel' else 'channel',
                    'group_type': group_type,
                    'is_forum': group.get('is_forum', False),
                    'is_supergroup': group.get('is_supergroup', False),
                    'is_broadcast': group.get('is_broadcast', False),
                    'scraped_at': group.get('scraped_at')
                }
            return groups_db

        # Attempt to load the dedicated DB file first
        try:
            if os.path.exists(db_path):
                # Empty file protection
                if os.path.getsize(db_path) == 0:
                    # Create an empty JSON object and persist it
                    with open(db_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    return {}

                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # If it's already a dict (id -> record), return as-is
                if isinstance(data, dict):
                    return data
                # If it's a list, convert
                if isinstance(data, list):
                    db = _convert_list_to_db(data)
                    return db

        except Exception as e:
            print(f"Warning: couldn't load groups_database.json cleanly: {e}")

        # Fallback: load older groups list format from GROUPS_FILE
        try:
            if os.path.exists(fallback_path):
                if os.path.getsize(fallback_path) == 0:
                    return {}
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    groups_data = json.load(f)
                return _convert_list_to_db(groups_data)
        except Exception as e:
            print(f"❌ Error loading groups file '{GROUPS_FILE}': {e}")

        # If all fails, return empty DB
        return {}
    
    def auto_populate_target_groups(self, prefer_forums_supergroups=True):
        """Automatically populate target_groups with preference for forums and supergroups"""
        try:
            all_groups = self.load_groups()
            
            # Separate groups by type with priority
            forums = []
            supergroups = []
            regular_groups = []
            
            for group in all_groups:
                members = group.get('members', 0)
                # Apply member filters
                if (members >= self.config.get('min_members', 100) and 
                    members <= self.config.get('max_members', 1000000)):
                    
                    group_type = group.get('type', 'group')
                    if group_type == 'forum' or group.get('is_forum', False):
                        forums.append(group)
                    elif group_type == 'supergroup' or group.get('is_supergroup', False):
                        supergroups.append(group)
                    elif group_type == 'group' and not group.get('is_broadcast', False):
                        regular_groups.append(group)
            
            # Prioritize forums and supergroups
            if prefer_forums_supergroups:
                # Sort by member count (descending)
                forums.sort(key=lambda x: x.get('members', 0), reverse=True)
                supergroups.sort(key=lambda x: x.get('members', 0), reverse=True)
                regular_groups.sort(key=lambda x: x.get('members', 0), reverse=True)
                
                # Combine with priority: Forums > Supergroups > Regular groups
                prioritized_groups = forums + supergroups + regular_groups
            else:
                # Just use all suitable groups
                prioritized_groups = forums + supergroups + regular_groups
            
            # Extract group IDs
            group_ids = [g['id'] for g in prioritized_groups]
            
            # Update config with filtered group IDs
            if group_ids:
                self.config['target_groups'] = group_ids
                self.save_config()
                
                stats_msg = f"🎯 Auto-populated {len(group_ids)} target groups:\n"
                stats_msg += f"🏛️ Forums: {len(forums)}\n"
                stats_msg += f"🏢 Supergroups: {len(supergroups)}\n"
                stats_msg += f"👥 Regular Groups: {len(regular_groups)}"
                
                self.log_and_send(stats_msg, "INFO")
                return len(group_ids)
            else:
                self.log_and_send("⚠️ No suitable groups found in database", "WARN")
                return 0
                
        except Exception as e:
            self.log_and_send(f"❌ Error auto-populating groups: {e}", "ERROR")
            return 0
    
    def get_groups_stats(self):
        """Get detailed statistics about available groups including forums and supergroups"""
        try:
            all_groups = self.load_groups()
            stats = {
                'total': len(all_groups),
                'forums': 0,
                'supergroups': 0,
                'regular_groups': 0,
                'channels': 0,
                'suitable_forums': 0,
                'suitable_supergroups': 0,
                'suitable_regular_groups': 0
            }
            
            # Count by type and suitability
            for group in all_groups:
                group_type = group.get('type', 'group')
                members = group.get('members', 0)
                is_suitable = (members >= self.config.get('min_members', 100) and 
                              members <= self.config.get('max_members', 1000000))
                
                if group_type == 'forum' or group.get('is_forum', False):
                    stats['forums'] += 1
                    if is_suitable:
                        stats['suitable_forums'] += 1
                elif group_type == 'supergroup' or group.get('is_supergroup', False):
                    stats['supergroups'] += 1
                    if is_suitable:
                        stats['suitable_supergroups'] += 1
                elif group_type == 'channel' or group.get('is_broadcast', False):
                    stats['channels'] += 1
                else:  # regular group
                    stats['regular_groups'] += 1
                    if is_suitable and not group.get('is_broadcast', False):
                        stats['suitable_regular_groups'] += 1
            
            stats['total_suitable'] = (stats['suitable_forums'] + 
                                     stats['suitable_supergroups'] + 
                                     stats['suitable_regular_groups'])
            
            return stats
        except:
            return {
                'total': 0, 'forums': 0, 'supergroups': 0, 'regular_groups': 0, 
                'channels': 0, 'suitable_forums': 0, 'suitable_supergroups': 0, 
                'suitable_regular_groups': 0, 'total_suitable': 0
            }
    
    async def scrape_groups(self):
        """Scrape ALL groups with no limits using pure user client"""
        self.is_scraping = True
        groups = []
        
        try:
            self.log_and_send("🔍 Starting UNLIMITED group scraping...", "INFO")
            
            # First verify we have user access
            me = await self.user_client.get_me()
            if me.bot:
                raise Exception("Session is a bot session, not user session!")
            
            self.log_and_send(f"👤 Authenticated as user: {me.first_name}", "INFO")
            
            # Get ALL dialogs with NO LIMITS
            dialog_count = 0
            scraped_count = 0
            
            from rich.progress import Progress
            with Progress() as progress:
                task = progress.add_task("[cyan]Scraping groups...", total=None)

                async for dialog in self.user_client.iter_dialogs():
                    dialog_count += 1

                    try:
                        if isinstance(dialog.entity, (Channel, Chat)):
                            # Enhanced classification for forums and supergroups
                            progress.update(task, advance=1)

                            member_count = getattr(dialog.entity, 'participants_count', 0)
                            is_broadcast = getattr(dialog.entity, 'broadcast', False)
                            is_megagroup = getattr(dialog.entity, 'megagroup', False)
                            has_forum = getattr(dialog.entity, 'forum', False)

                            # Determine group type with enhanced detection
                            if has_forum:
                                group_type = 'forum'
                            elif is_megagroup:
                                group_type = 'supergroup'
                            elif is_broadcast:
                                group_type = 'channel'
                            else:
                                group_type = 'group'

                            group_info = {
                                'id': dialog.entity.id,
                                'title': getattr(dialog.entity, 'title', None),
                                'username': getattr(dialog.entity, 'username', None),
                                'members': member_count,
                                'type': group_type,
                                'is_forum': has_forum,
                                'is_supergroup': is_megagroup,
                                'is_broadcast': is_broadcast,
                                'scraped_at': datetime.now().isoformat()
                            }
                            groups.append(group_info)
                            scraped_count += 1

                            # Enhanced logging with group type
                            type_label = {
                                'forum': 'FORUM',
                                'supergroup': 'SUPERGROUP',
                                'group': 'GROUP',
                                'channel': 'CHANNEL'
                            }
                            label = type_label.get(group_type, 'UNKNOWN')

                            self.log_and_send(f"[{scraped_count}] {dialog.entity.title} | {label} | {member_count:,} members", "SCRAPE")

                            # Small delay to avoid rate limits
                            if scraped_count % 50 == 0:
                                await asyncio.sleep(self.config.get('rate_limit_delay', 2))
                    except Exception as e:
                        # Log and continue on per-dialog errors
                        try:
                            title = getattr(dialog.entity, 'title', str(dialog.entity))
                        except Exception:
                            title = 'unknown'
                        self.log_and_send(f"Error processing {title}: {e}", "WARN")
                        continue

                    # Progress update every 100 dialogs
                    if dialog_count % 100 == 0:
                        self.log_and_send(f"Progress: {scraped_count} groups from {dialog_count} dialogs", "INFO")

                    # Remove or reduce delay for scraping speedup
                    # Old: if scraped_count % 50 == 0: await asyncio.sleep(self.config.get('rate_limit_delay', 2))
                    # New: only sleep every 500 groups, and for a much shorter time
                    if scraped_count % 500 == 0 and scraped_count > 0:
                        await asyncio.sleep(0.5)

            # Save all groups
            self.save_groups(groups)

            # After scraping, auto-populate target_groups with unique group IDs (forums/supergroups/regular groups)
            all_ids = set()
            for g in groups:
                if g['type'] in ('forum', 'supergroup', 'group'):
                    all_ids.add(g['id'])
            # Remove duplicates and update config
            self.config['target_groups'] = list(all_ids)
            self.save_config()
            self.log_and_send(f"Auto-populated {len(all_ids)} unique target groups after scraping.", "SUCCESS")

            # Display completion summary with clean formatting
            console.print(f"\n[bold green]{'=' * 60}[\/bold green]")
            console.print(f"[bold white]SCRAPING COMPLETE[\/bold white]")
            console.print(f"[bold green]{'=' * 60}[\/bold green]")
            console.print(f"[cyan]Total Groups: {scraped_count}[\/cyan]")
            console.print(f"[cyan]Total Dialogs: {dialog_count}[\/cyan]")
            console.print(f"[yellow]Channels: {len([g for g in groups if g['type'] == 'channel'])}[\/yellow]")
            console.print(f"[blue]Groups: {len([g for g in groups if g['type'] == 'group'])}[\/blue]")
            console.print(f"[bold green]{'=' * 60}[\/bold green]\n")

            return scraped_count
            
        except PersistentTimestampOutdatedError as pte:
            # Telethon may raise this during dialog diffs; attempt reconnect and log a warning
            self.log_and_send(f'PersistentTimestampOutdatedError during scraping: {pte}', 'WARN')
            try:
                await self.ensure_client_connected(self.user_client)
            except Exception:
                pass
            return 0
        except Exception as e:
            error_msg = f"❌ Scraping error: {e}"
            self.log_and_send(error_msg, "ERROR")
            if "bot users" in str(e):
                self.log_and_send("💡 The session appears to be a bot session. Please use a user session.", "ERROR")
            return 0
        finally:
            self.is_scraping = False
    
    async def send_to_groups(self):
        # Auto-scan and filter targets before every send cycle
        self.filter_targets_to_groups()
        """Send messages to target groups - UNLIMITED MODE"""
        self.is_sending = True
        cycle_count = 0
        
        # Ensure stats has required keys
        if 'total_sent' not in self.stats:
            self.stats['total_sent'] = 0
        if 'groups' not in self.stats:
            self.stats['groups'] = {}
        
        self.log_and_send("Starting UNLIMITED sending mode...", "START")
        
        while self.is_sending:
            cycle_count += 1
            console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
            console.print(f"[bold white]CYCLE #{cycle_count}[/bold white]")
            console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")
            
            successful_sends = 0
            failed_sends = 0
            
            # Merge groups_database keys and config target_groups so both normal groups and forums are included
            targets = []
            try:
                cfg_targets = list(self.config.get('target_groups', []) or [])
                db_targets = []
                if getattr(self, 'groups_database', None) and len(self.groups_database) > 0:
                    # groups_database is a dict of id->{...}
                    db_targets = [self.normalize_group_id(k) for k in self.groups_database.keys() if not self.is_group_blocked(k)]

                # Combine and deduplicate, then filter blocked status defensively
                combined = list(dict.fromkeys([self.normalize_group_id(x) for x in (db_targets + cfg_targets)]))
                targets = [t for t in combined if not self.is_group_blocked(t)]
            except Exception:
                targets = list(self.config.get('target_groups', []) or [])

            # Diagnostic: report source counts so we can see why targets may be empty
            try:
                db_count = len(self.groups_database) if getattr(self, 'groups_database', None) else 0
            except Exception:
                db_count = 0
            cfg_count = len(self.config.get('target_groups', []) or [])
            self.log_and_send(f"Cycle target sources: groups_database_count={db_count} config_targets={cfg_count}", "INFO")

            # Normalize targets for safe resolving and accurate counts
            normalized_targets = [self.normalize_group_id(t) for t in targets]
            total_targets = len(normalized_targets)

            # If no targets, print a short diagnostic sample of why (blocked/status)
            if total_targets == 0:
                try:
                    if db_count > 0:
                        sample_keys = list(self.groups_database.keys())[:5]
                        sample_info = []
                        for k in sample_keys:
                            gd = (self.groups_database or {}).get(k, {}) or {}
                            blocked = bool(gd.get('blocked'))
                            blocked_until = gd.get('blocked_until')
                            sample_info.append(f"{k}(blocked={blocked} until={blocked_until})")
                        self.log_and_send(f"Cycle diagnostic: groups_database sample: {', '.join(sample_info)}", "WARN")
                    elif cfg_count > 0:
                        sample_cfg = (self.config.get('target_groups') or [])[:5]
                        sample_info = []
                        for t in sample_cfg:
                            try:
                                b = self.is_group_blocked(t)
                            except Exception:
                                b = 'err'
                            sample_info.append(f"{t}(blocked={b})")
                        self.log_and_send(f"Cycle diagnostic: config sample: {', '.join(sample_info)}", "WARN")
                    else:
                        self.log_and_send("Cycle diagnostic: no targets configured in groups_database or config", "WARN")
                except Exception:
                    pass

            # Debug: log a preview of targets for this cycle
            try:
                preview = ', '.join([str(x) for x in normalized_targets[:5]])
            except Exception:
                preview = str(normalized_targets[:5])
            self.log_and_send(f"Cycle targets: total={total_targets} preview={preview}", "INFO")

            for i, group_id in enumerate(normalized_targets, 1):
                if not self.is_sending:
                    break
                
                try:
                    # Get group info for logging
                    try:
                        entity = await self.user_client.get_entity(group_id)
                        group_name = entity.title
                        is_forum = hasattr(entity, 'forum') and entity.forum
                        
                        # Check if this is a channel and if it's owned by the user
                        from telethon.tl.types import Channel
                        if isinstance(entity, Channel):
                            # Check if user is creator/admin of this channel
                            try:
                                me = await self.user_client.get_me()
                                my_id = me.id
                                
                                # Get channel full info to check creator
                                from telethon.tl.functions.channels import GetFullChannelRequest
                                full_channel = await self.user_client(GetFullChannelRequest(entity))
                                
                                # Skip if this is user's own channel (they are the creator)
                                if hasattr(full_channel, 'full_chat') and hasattr(full_channel.full_chat, 'participants_count'):
                                    # Check if user has admin rights or is creator
                                    if entity.creator or (hasattr(entity, 'admin_rights') and entity.admin_rights):
                                        self.log_and_send(f"Skipping own channel: {group_name}", "INFO")
                                        continue
                            except Exception:
                                # If we can't determine ownership, proceed
                                pass
                                
                    except:
                        group_name = f"Group {group_id}"
                        is_forum = False
                    
                    # Handle forum vs regular group sending
                    if is_forum:
                        # For forums, send to all available topics (or up to max_forum_topics)
                        topics_sent = 0
                        try:
                            from telethon.tl.functions.channels import GetForumTopicsRequest
                            forum_topics = await self.user_client(GetForumTopicsRequest(
                                channel=entity,
                                offset_date=None,
                                offset_id=0,
                                offset_topic=0,
                                limit=100
                            ))

                            max_topics = int(self.config.get('max_forum_topics', 0))
                            count = 0
                            # Load persisted deleted topics for this group (avoid retrying them)
                            deleted_topic_ids = []
                            try:
                                key = str(group_id)
                                deleted_topic_ids = (self.groups_database.get(key, {}) or {}).get('deleted_topics', []) or []
                            except Exception:
                                deleted_topic_ids = []
                            for topic in forum_topics.topics:
                                if max_topics and count >= max_topics:
                                    break
                                topic_title = getattr(topic, 'title', '') if hasattr(topic, 'title') else ''
                                # Skip if this topic is known deleted
                                if getattr(topic, 'id', None) and topic.id in deleted_topic_ids:
                                    self.log_and_send(f"   └ Skipping known-deleted topic '{topic_title}' in {group_name}", "INFO")
                                    continue
                                try:
                                    await self._deliver_ad_to_target(group_id, reply_to=topic.id)
                                    topics_sent += 1
                                    count += 1
                                    self.log_and_send(f"   └ Sent to topic '{topic_title}' in {group_name}", "SEND")
                                    # reset any topic failure counter on success
                                    try:
                                        key = str(group_id)
                                        if key in (self.groups_database or {}):
                                            topic_failures = self.groups_database[key].get('topic_failures', {}) or {}
                                            if str(topic.id) in topic_failures:
                                                del topic_failures[str(topic.id)]
                                                self.groups_database[key]['topic_failures'] = topic_failures
                                                with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                    except Exception:
                                        pass
                                except SkipTargetError as ste:
                                    # Topic-level skip/tombstone/delete/wait handling
                                    action = getattr(ste, 'action', 'skip')
                                    reason = getattr(ste, 'reason', '')
                                    wait_seconds = getattr(ste, 'wait_seconds', None)
                                    self.log_and_send(f"SkipTargetError for topic {topic_title} in {group_name}: action={action} reason={reason}", "WARN")
                                    if action == 'wait' and wait_seconds:
                                        await asyncio.sleep(min(wait_seconds, 3600))
                                        # retry once after wait
                                        try:
                                            await self._deliver_ad_to_target(group_id, reply_to=topic.id)
                                            topics_sent += 1
                                            count += 1
                                            self.log_and_send(f"   └ Retry sent to topic '{topic_title}' in {group_name}", "SEND")
                                        except Exception:
                                            self.log_and_send(f"⚠️ Retry failed for topic '{topic_title}' in {group_name}", "WARN")
                                            break
                                    elif action == 'skip':
                                        # skip this topic
                                        continue
                                    elif action == 'tombstone':
                                        # record deleted topic id and persist
                                        try:
                                            key = str(group_id)
                                            if not getattr(self, 'groups_database', None):
                                                self.groups_database = {}
                                            if key not in self.groups_database:
                                                self.groups_database[key] = {'id': group_id, 'title': group_name}
                                            deleted = self.groups_database[key].get('deleted_topics', []) or []
                                            tid = getattr(topic, 'id', None)
                                            if tid is not None and tid not in deleted:
                                                deleted.append(tid)
                                                self.groups_database[key]['deleted_topics'] = deleted
                                                try:
                                                    self._write_json_atomic('groups_database.json', self.groups_database)
                                                except Exception:
                                                    try:
                                                        with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                                            json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            pass
                                        # mark group briefly blocked to avoid immediate retries
                                        try:
                                            self.mark_group_blocked(group_id, reason=f'topic_tombstone:{topic_title}', block_minutes=60)
                                        except Exception:
                                            pass
                                        continue
                                    elif action == 'delete':
                                        # remove group entirely from DB
                                        try:
                                            key = str(group_id)
                                            if getattr(self, 'groups_database', None) and key in self.groups_database:
                                                del self.groups_database[key]
                                                try:
                                                    self._write_json_atomic('groups_database.json', self.groups_database)
                                                except Exception:
                                                    try:
                                                        with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                                            json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            pass
                                        break
                                except FloodWaitError as flood:
                                    wait_time = flood.seconds
                                    if wait_time > 1800:
                                        self.log_and_send(f"⚠️ Topic '{topic_title}' in {group_name} requires {wait_time//60} min wait - skipping", "WARN")
                                        break
                                    else:
                                        self.log_and_send(f"⏳ FloodWait: {wait_time}s for topic '{topic_title}'", "WAIT")
                                        await asyncio.sleep(wait_time)
                                        # retry once after wait
                                        try:
                                            await self._deliver_ad_to_target(group_id, reply_to=topic.id)
                                            topics_sent += 1
                                            count += 1
                                            self.log_and_send(f"   └ Retry sent to topic '{topic_title}' in {group_name}", "SEND")
                                        except Exception:
                                            self.log_and_send(f"⚠️ Retry failed for topic '{topic_title}' in {group_name}", "WARN")
                                            break
                                except Exception as topic_error:
                                    terr = str(topic_error)
                                    # If topic was deleted, record audit and persist a tombstone to avoid future retries
                                    # increment topic-specific failure counter
                                    try:
                                        key = str(group_id)
                                        if not getattr(self, 'groups_database', None):
                                            self.groups_database = {}
                                        if key not in self.groups_database:
                                            self.groups_database[key] = {'id': group_id, 'title': group_name}
                                        topic_failures = self.groups_database[key].get('topic_failures', {}) or {}
                                        tid_str = str(getattr(topic, 'id', ''))
                                        topic_failures[tid_str] = int(topic_failures.get(tid_str, 0)) + 1
                                        self.groups_database[key]['topic_failures'] = topic_failures
                                        # persist immediately
                                        try:
                                            with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                                json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass

                                    # If failures for this topic exceed threshold, treat as deleted and persist tombstone
                                    try:
                                        key = str(group_id)
                                        topic_failures = (self.groups_database.get(key, {}) or {}).get('topic_failures', {}) or {}
                                        tid = getattr(topic, 'id', None)
                                        tid_str = str(tid) if tid is not None else None
                                        t_fail_count = int(topic_failures.get(tid_str, 0)) if tid_str else 0
                                        if t_fail_count >= int(self.config.get('auto_skip_failures', 2)):
                                            # persist tombstone in deleted_topics
                                            deleted = (self.groups_database.get(key, {}) or {}).get('deleted_topics', []) or []
                                            if tid is not None and tid not in deleted:
                                                deleted.append(tid)
                                            if key not in self.groups_database:
                                                self.groups_database[key] = {'id': group_id, 'title': group_name}
                                            self.groups_database[key]['deleted_topics'] = deleted
                                            try:
                                                with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                            except Exception:
                                                pass
                                            # mark group blocked briefly to avoid immediate retries
                                            try:
                                                self.mark_group_blocked(group_id, reason=f'topic_auto_skipped:{topic_title}', block_minutes=60)
                                            except Exception:
                                                pass
                                            self.record_audit('TOPIC_AUTOSKIP', group_id, f'topic_id={tid} title={topic_title} failures={t_fail_count}')
                                            self.log_and_send(f"⚠️ Topic auto-skipped after {t_fail_count} failures: '{topic_title}' in {group_name}", "WARN")
                                            continue

                                    except Exception:
                                        pass

                                    if 'topic was deleted' in terr or 'The topic was deleted' in terr:
                                        try:
                                            tid = getattr(topic, 'id', None)
                                            self.record_audit('TOPIC_DELETED', group_id, f'topic_id={tid} title={topic_title}')
                                        except Exception:
                                            pass
                                        try:
                                            # Persist deleted topic ids in groups_database under 'deleted_topics'
                                            key = str(group_id)
                                            if not getattr(self, 'groups_database', None):
                                                self.groups_database = {}
                                            if key not in self.groups_database:
                                                self.groups_database[key] = {'id': group_id, 'title': group_name}
                                            deleted = self.groups_database[key].get('deleted_topics', []) or []
                                            if getattr(topic, 'id', None) and topic.id not in deleted:
                                                deleted.append(topic.id)
                                            self.groups_database[key]['deleted_topics'] = deleted
                                            # Save DB
                                            try:
                                                db_path = os.path.abspath('groups_database.json')
                                                with open(db_path, 'w', encoding='utf-8') as f:
                                                    json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                            except Exception:
                                                pass
                                        except Exception:
                                            pass
                                        # Mark the group temporarily blocked to avoid immediate retries
                                        try:
                                            self.mark_group_blocked(group_id, reason=f'topic_deleted:{topic_title}', block_minutes=60)
                                            self.record_audit('BLOCK', group_id, f'topic_deleted:{topic_title}')
                                        except Exception:
                                            pass
                                        self.log_and_send(f"⚠️ Topic deleted: '{topic_title}' in {group_name} (ID: {group_id}) - recorded, group temporarily blocked", "WARN")
                                        continue
                                    # Otherwise log and continue
                                    if "TOPIC_CLOSED" not in terr:
                                        self.log_and_send(f"⚠️ Error in topic '{topic_title}': {topic_error}", "WARN")
                                    continue

                            # If no topics were sent, fall back to a general send
                            if topics_sent == 0:
                                try:
                                    await self._deliver_ad_to_target(group_id)
                                    topics_sent = 1
                                    self.log_and_send(f"   └ Sent to general topic in {group_name} (fallback)", "SEND")
                                except FloodWaitError as flood_error:
                                    raise flood_error
                        except FloodWaitError:
                            # bubble up to outer handler
                            raise
                        except Exception as forum_error:
                            # Fallback to regular send if forum API fails
                            try:
                                await self._deliver_ad_to_target(group_id)
                                topics_sent = 1
                            except Exception:
                                topics_sent = 0
                            
                    else:
                        # Regular group/supergroup - send normally
                        await self._deliver_ad_to_target(group_id)
                        topics_sent = 1
                    
                    self.message_count += topics_sent
                    self.stats['total_sent'] += topics_sent
                    successful_sends += topics_sent
                    
                    # Update group-specific stats
                    if str(group_id) not in self.stats['groups']:
                        self.stats['groups'][str(group_id)] = {'sent': 0, 'failed': 0}
                    self.stats['groups'][str(group_id)]['sent'] += topics_sent
                    
                    if is_forum and topics_sent > 1:
                        self.log_and_send(f"[{i}/{total_targets}] Sent to {topics_sent} topics in '{group_name}' (ID: {group_id})", "SEND")
                    else:
                        self.log_and_send(f"[{i}/{total_targets}] Successfully sent to '{group_name}' (ID: {group_id})", "SEND")
                    
                except FloodWaitError as e:
                    wait_time = e.seconds
                    # Handle long waits more intelligently
                    # Reload threshold from disk so we can change behavior at runtime
                    try:
                        with open(os.path.abspath('config.json'), 'r', encoding='utf-8') as cf:
                            cfg_disk = json.load(cf)
                        threshold = int(cfg_disk.get('long_wait_threshold', cfg_disk.get('long_wait_threshold', 1800)))
                    except Exception:
                        threshold = int(self.config.get('long_wait_threshold', 1800))

                    if wait_time > threshold:
                        # If a server requests a long wait, take action according to config ('tombstone' or 'delete')
                        action = 'tombstone'
                        try:
                            with open(os.path.abspath('config.json'), 'r', encoding='utf-8') as cf:
                                cfg_disk = json.load(cf)
                                action = cfg_disk.get('long_wait_action', action)
                        except Exception:
                            action = self.config.get('long_wait_action', action)

                        failed_sends += 1
                        # Update group-specific stats for failure
                        if str(group_id) not in self.stats['groups']:
                            self.stats['groups'][str(group_id)] = {'sent': 0, 'failed': 0}
                        self.stats['groups'][str(group_id)]['failed'] += 1

                        gid_key = str(group_id)
                        try:
                            if getattr(self, 'groups_database', None) and gid_key in self.groups_database:
                                self.record_audit('LONG_FLOOD_' + action.upper(), group_id, f'wait={wait_time}')
                                if action == 'delete':
                                    # Remove entry
                                    try:
                                        del self.groups_database[gid_key]
                                    except Exception:
                                        pass
                                else:
                                    # Tombstone: mark blocked with reason and expiry
                                    try:
                                        block_days = int(cfg_disk.get('long_wait_block_days', self.config.get('long_wait_block_days', 7)))
                                    except Exception:
                                        block_days = int(self.config.get('long_wait_block_days', 7))
                                    try:
                                        self.groups_database[gid_key]['blocked'] = True
                                        until = (datetime.now() + timedelta(days=block_days)).isoformat()
                                        self.groups_database[gid_key]['blocked_until'] = until
                                        self.groups_database[gid_key]['blocked_reason'] = f'long_flood:{wait_time}s'
                                    except Exception:
                                        pass

                                # persist DB
                                try:
                                    self._write_json_atomic('groups_database.json', self.groups_database)
                                except Exception:
                                    try:
                                        with open(os.path.abspath('groups_database.json'), 'w', encoding='utf-8') as f:
                                            json.dump(self.groups_database, f, ensure_ascii=False, indent=2)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    else:
                        self.log_and_send(f"⏳ FloodWait: {wait_time}s for group {group_id}", "WAIT")
                        await asyncio.sleep(wait_time)
                        # Retry after flood wait
                        try:
                            if is_forum:
                                # For forums, just send to general topic on retry
                                await self._deliver_ad_to_target(group_id)
                            else:
                                await self._deliver_ad_to_target(group_id)
                            successful_sends += 1
                            self.stats['total_sent'] += 1
                            self.log_and_send(f"Retry successful for group {group_id}", "SEND")
                        except Exception as retry_error:
                            failed_sends += 1
                            # Update group-specific stats for failure
                            if str(group_id) not in self.stats['groups']:
                                self.stats['groups'][str(group_id)] = {'sent': 0, 'failed': 0}
                            self.stats['groups'][str(group_id)]['failed'] += 1
                            self.log_and_send(f"Retry failed for group {group_id}: {retry_error}", "ERROR")
                            # If retry indicates we are banned or chat write forbidden, mark blocked and skip
                            rmsg = str(retry_error)
                            if ('CHAT_WRITE_FORBIDDEN' in rmsg or 'USER_BAN' in rmsg or 'TOPIC_CLOSED' in rmsg
                                    or "You can't write in this chat" in rmsg or 'USER_BANNED_IN_CHANNEL' in rmsg):
                                try:
                                    self.mark_group_blocked(group_id, reason=retry_error, block_minutes=60*24)
                                except Exception:
                                    pass
                    
                except Exception as e:
                    failed_sends += 1
                    # Update group-specific stats for failure
                    if str(group_id) not in self.stats['groups']:
                        self.stats['groups'][str(group_id)] = {'sent': 0, 'failed': 0}
                    self.stats['groups'][str(group_id)]['failed'] += 1
                    
                    # Special handling for forum-related errors
                    if "TOPIC_CLOSED" in str(e):
                        self.log_and_send(f"Forum topic closed for '{group_name}' (ID: {group_id})", "WARN")
                        self.log_and_send("Tip: Use Forums button to refresh and get accessible forums only", "INFO")
                    else:
                        self.log_and_send(f"Error sending to {group_id}: {e}", "ERROR")
                        # permanent errors -> mark blocked
                        emsg = str(e)
                        if ('CHAT_WRITE_FORBIDDEN' in emsg or 'USER_BANNED_IN_CHANNEL' in emsg or 'USER_BAN' in emsg or 'TOPIC_CLOSED' in emsg
                                or "You can't write in this chat" in emsg or 'ENTITY_MIGRATE' in emsg):
                            try:
                                self.mark_group_blocked(group_id, reason=e, block_minutes=60*24)
                            except Exception:
                                pass
                        else:
                            # Check if this is a channel and apply stricter auto-block policy
                            is_channel = False
                            try:
                                from telethon.tl.types import Channel
                                if isinstance(entity, Channel) and getattr(entity, 'broadcast', False):
                                    is_channel = True
                            except:
                                # Fallback: check from groups_database
                                try:
                                    gkey = str(group_id)
                                    if gkey in (self.groups_database or {}):
                                        gtype = (self.groups_database[gkey] or {}).get('type', '')
                                        is_channel = (gtype == 'channel')
                                except:
                                    pass
                            
                            if is_channel:
                                # For channels: auto-block permanently after 2 failures
                                try:
                                    current_failures = self.stats['groups'][str(group_id)].get('failed', 0)
                                    if current_failures >= 2:
                                        # Permanently block channel
                                        self.mark_group_blocked(group_id, reason=f'channel_auto_blocked_after_{current_failures}_failures', block_minutes=60*24*365*10)  # 10 years = permanent
                                        self.log_and_send(f"🚫 Channel PERMANENTLY blocked after {current_failures} failures: {group_name} (ID: {group_id})", "WARN")
                                        self.record_audit('CHANNEL_AUTO_BLOCK', group_id, f'failures={current_failures}')
                                except Exception:
                                    pass
                            else:
                                # Non-permanent error for groups; increment failure counter and auto-skip if threshold reached
                                try:
                                    skipped = self.increment_group_failure(group_id)
                                    if skipped:
                                        self.log_and_send(f"⚠️ Group auto-skipped after repeated failures: {group_id}", "WARN")
                                except Exception:
                                    pass
                
                # Rate limiting delay only
                await asyncio.sleep(self.config.get('rate_limit_delay', 5))
            
            # Cycle summary
            console.print(f"\n[bold cyan]{'─' * 60}[/bold cyan]")
            console.print(f"[bold white]CYCLE #{cycle_count} COMPLETE[/bold white]")
            console.print(f"[bold cyan]{'─' * 60}[/bold cyan]")
            console.print(f"[green]Successful: {successful_sends}[/green]")
            console.print(f"[red]Failed: {failed_sends}[/red]")
            console.print(f"[cyan]Total Sent: {self.message_count}[/cyan]")
            console.print(f"[bold cyan]{'─' * 60}[/bold cyan]\n")
            
            # Save stats after each cycle
            self.save_stats()
            
            if self.is_sending:
                # If manually started via admin button, use a shorter manual_cycle_delay to avoid 300s default
                if getattr(self, 'manual_mode', False):
                    manual_delay = int(self.config.get('manual_cycle_delay', 5))
                    self.log_and_send(f"Manual mode waiting {manual_delay}s before next cycle...", "WAIT")
                    await asyncio.sleep(manual_delay)
                else:
                    self.log_and_send(f"Waiting {self.config['cycle_delay']}s before next cycle...", "WAIT")
                    await asyncio.sleep(self.config['cycle_delay'])
        
        console.print(f"\n[bold red]{'=' * 60}[/bold red]")
        console.print(f"[bold white]SENDING STOPPED[/bold white]")
        console.print(f"[bold red]{'=' * 60}[/bold red]")
        console.print(f"[cyan]Total Cycles: {cycle_count}[/cyan]")
        console.print(f"[cyan]Total Messages: {self.message_count}[/cyan]")
        console.print(f"[bold red]{'=' * 60}[/bold red]\n")
        self.save_stats()

    async def send_everywhere(self):
        """Continuously send the ad message to every group in the groups_database (no filtering).
        This will run until `self.is_sending_everywhere` is set to False.
        Use with caution - make sure you have permission to send to these groups.
        """
        self.log_and_send("Starting EVERYWHERE sending mode", "INFO")
        try:
            active_minutes = int(self.config.get('active_cycle_minutes', 30))
            rest_minutes = int(self.config.get('rest_cycle_minutes', 10))
            active_seconds = max(10, active_minutes * 60)
            rest_seconds = max(10, rest_minutes * 60)

            self.log_and_send(f"EVERYWHERE mode: active {active_minutes}m / rest {rest_minutes}m", "INFO")

            # Continuous cycle: active -> rest -> repeat
            while getattr(self, 'is_sending_everywhere', False):
                start_ts = datetime.now()
                end_active = start_ts.timestamp() + active_seconds

                # Active phase: send messages until time expires or toggle turned off
                while datetime.now().timestamp() < end_active and getattr(self, 'is_sending_everywhere', False):
                    # Respect manual pause
                    if getattr(self, 'is_paused', False) or not getattr(self, 'is_sending', True):
                        await asyncio.sleep(1)
                        continue

                    # Choose source of group targets: prefer normalized groups_database, fall back to config targets
                    targets_iterable = None
                    try:
                        if self.groups_database and len(self.groups_database) > 0:
                            targets_iterable = [(k, v) for k, v in self.groups_database.items() if not self.is_group_blocked(k)]
                        else:
                          cfg_targets = self.config.get('target_groups', [])
                          # convert plain list of ids into (id, {}) pairs to match expected loop and filter blocked
                          targets_iterable = [(str(t), {}) for t in cfg_targets if not self.is_group_blocked(t)]
                    except Exception:
                        targets_iterable = []

                    for gid, gdata in targets_iterable:
                        if not getattr(self, 'is_sending_everywhere', False):
                            break
                        try:
                            group_id = gdata.get('id') if isinstance(gdata, dict) and gdata.get('id') else gid
                            group_id = self.normalize_group_id(group_id)
                            # Pre-resolve the entity to detect missing/invalid targets early
                            try:
                                _entity = await self.user_client.get_entity(group_id)
                            except Exception as resolve_err:
                                msg = str(resolve_err)
                                # If it's a connection/closed error, attempt reconnect
                                try:
                                    txtlow = msg.lower()
                                    if 'server closed the connection' in txtlow or '0 bytes read' in txtlow or 'connection reset by peer' in txtlow:
                                        ok = await self.ensure_client_connected(self.user_client)
                                        if ok:
                                            # retry resolving once
                                            try:
                                                _entity = await self.user_client.get_entity(group_id)
                                            except Exception:
                                                pass
                                except Exception:
                                    pass

                                # Skip unrecoverable resolution errors quickly
                                if 'Cannot find any entity' in msg or 'ENTITY_MIGRATE' in msg:
                                    self.log_and_send(f"EVERYWHERE skip: cannot resolve {group_id}: {resolve_err}", "WARN")
                                    continue
                                else:
                                    self.log_and_send(f"EVERYWHERE resolve error for {group_id}: {resolve_err}", "WARN")
                                    continue

                            # Use the resilient send wrapper
                            try:
                                await self._deliver_ad_to_target(group_id)
                                self.log_and_send(f"EVERYWHERE: Sent to {group_id}", "SEND")
                                try:
                                    self.record_audit('SEND', group_id, f'sent_to_everywhere')
                                except Exception:
                                    pass
                            except FloodWaitError as e:
                                self.log_and_send(f"EVERYWHERE FloodWait {e.seconds}s for {gid}", "WAIT")
                                await asyncio.sleep(min(e.seconds, 60))
                            except Exception as e:
                                # If the send raised an unrecoverable Telethon error (TOPIC_CLOSED etc), skip quickly
                                msg = str(e)
                                if ('TOPIC_CLOSED' in msg or 'Cannot find any entity' in msg or 'ENTITY_MIGRATE' in msg):
                                    self.log_and_send(f"EVERYWHERE unrecoverable send error for {gid}: {e}; skipping", "WARN")
                                    continue
                                # If writing is forbidden, mark and skip to avoid future retries
                                if ("You can't write in this chat" in msg or 'CHAT_WRITE_FORBIDDEN' in msg
                                        or 'USER_BANNED_IN_CHANNEL' in msg or 'USER_BAN' in msg):
                                    try:
                                        self.mark_group_blocked(group_id, reason=msg, block_minutes=60*24)
                                    except Exception:
                                        pass
                                    self.log_and_send(f"EVERYWHERE write-forbidden for {gid}: {e}; marked blocked", "WARN")
                                    continue
                                self.log_and_send(f"EVERYWHERE error sending to {gid}: {e}", "ERROR")
                                try:
                                    skipped = self.increment_group_failure(group_id)
                                    if skipped:
                                        self.log_and_send(f"EVERYWHERE auto-skipped group after repeated failures: {group_id}", "WARN")
                                except Exception:
                                    pass

                            # yield between sends to avoid blocking the outer loop
                            await asyncio.sleep(self.config.get('rate_limit_delay', 5))
                        except Exception as e:
                            self.log_and_send(f"EVERYWHERE inner loop error for {gid}: {e}", "ERROR")

                # Active phase complete; enter rest
                if not getattr(self, 'is_sending_everywhere', False):
                    break
                self.log_and_send(f"EVERYWHERE active phase complete — resting for {rest_minutes} minutes", "INFO")
                rest_end = datetime.now().timestamp() + rest_seconds
                while datetime.now().timestamp() < rest_end and getattr(self, 'is_sending_everywhere', False):
                    await asyncio.sleep(1)

        finally:
            self.log_and_send("Stopped EVERYWHERE sending mode", "INFO")
    
    async def get_status(self):
        """Get current status with unlimited mode info"""
        status = "🟢 RUNNING (UNLIMITED)" if self.is_sending else "🔴 STOPPED"
        scraping = " (SCRAPING...)" if self.is_scraping else ""
        
        uptime = datetime.now() - self.session_start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        log_status = "✅ Enabled" if self.config.get('log_channel_id') else "❌ Not Set"
        
        return (
            f"🤖 **AD SENDER STATUS (UNLIMITED MODE)**\n\n"
            f"Status: {status}{scraping}\n"
            f"Messages Sent: {self.message_count}\n"
            f"Target Groups: {len(self.config['target_groups'])}\n"
            f"Rate Delay: {self.config.get('rate_limit_delay', 5)}s\n"
            f"Cycle Delay: {self.config['cycle_delay']}s\n"
            f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
            f"Log Channel: {log_status}\n\n"
            f"**Current Message:**\n{self.config['ad_message'][:100]}..."
        )

async def main():
    bot = HybridAdBot()
    # Remove all channels from targets and database on startup
    bot.filter_targets_to_groups()
    # Auto-clean duplicates on startup
    bot.auto_clean_duplicates()
    # /setowner logic removed; owner ID is now hardcoded in config
    """Main function"""
    # Set up exception handling for asyncio tasks
    def exception_handler(loop, context):
        exception = context.get('exception')
        if isinstance(exception, QueryIdInvalidError):
            print("⚠️ Callback query expired (handled)")
        else:
            print(f"❌ Unhandled exception: {context}")
    
    # Get the current event loop and set exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    
    bot = HybridAdBot()
    # Show a short startup animation and header
    try:
        await startup_animation('STARTING HYBRID AD BOT', credit='MRNOL', duration=1.2)
    except Exception:
        # fallback to simple header if animation fails
        print(term_header('STARTING HYBRID AD BOT', credit='MRNOL'))
    
    # Get credentials from CSV
    api_id, api_hash, session_name = bot.get_telegram_credentials()
    if not api_id or not api_hash:
        console.print("[bold yellow]Credentials missing — starting interactive first-time setup...[/bold yellow]")
        ok = await bot.interactive_setup_and_authorize()
        if not ok:
            console.print("[bold red]Interactive setup failed or was cancelled. Exiting.[/bold red]")
            return

        # reload credentials and try again
        api_id, api_hash, session_name = bot.get_telegram_credentials()
        if not api_id or not api_hash:
            console.print("[bold red]Credentials still missing after setup. Exiting.[/bold red]")
            return
    
    # Initialize or reuse user client for operations with fresh session
    user_client = None
    # If interactive setup created and set a user_client, prefer that one
    if hasattr(bot, 'user_client') and bot.user_client:
        try:
            if await bot.user_client.is_user_authorized():
                user_client = bot.user_client
        except Exception:
            user_client = None

    if not user_client:
        user_client = TelegramClient(
            session_name or 'pure_user_session',  # Use session from CSV or default
            api_id=api_id,
            api_hash=api_hash,
            connection_retries=5,
            retry_delay=3,
            timeout=30,
            request_retries=5
        )
        bot.user_client = user_client
    
    # Start user client with retry logic
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            await user_client.start()

            # Check if authorized as user
            if not await user_client.is_user_authorized():
                print("User authentication required...")
                phone = input("Enter your phone number (with country code): ")
                await user_client.send_code_request(phone)
                code = input("Enter the OTP code: ")

                try:
                    await user_client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = input("Enter your 2FA password: ")
                    await user_client.sign_in(password=password)

            me = await user_client.get_me()
            
            # Display user info with clean formatting
            console.print(f"\n[bold cyan]{'─' * 60}[/bold cyan]")
            console.print(f"[cyan]User Client:[/cyan] {me.first_name} | @{me.username or 'No username'} (@{session_name or 'user'})")
            console.print(f"[cyan]Phone:[/cyan] {me.phone}")
            
            # Update user bio if configured
            try:
                success, info = await bot.set_user_bio(user_client)
                if success:
                    console.print(f"[green]Bio updated successfully[/green]")
                else:
                    console.print(f"[yellow]Bio update: {info}[/yellow]")
            except Exception as e:
                console.print(f"[red]Bio update failed: {e}[/red]")

            # Verify user permissions
            try:
                dialogs_count = 0
                async for dialog in user_client.iter_dialogs(limit=5):
                    dialogs_count += 1
                console.print(f"[green]User permissions verified - can access {dialogs_count} dialogs[/green]")
            except Exception as e:
                console.print(f"[red]User permission test failed: {e}[/red]")
            
            console.print(f"[bold cyan]{'─' * 60}[/bold cyan]\n")
            
            break  # Success, exit retry loop

        except TimeoutError as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"⚠️ Connection timeout (attempt {retry_count}/{max_retries}). Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                print(f"❌ Failed to connect after {max_retries} attempts. Please check your internet connection.")
                return
        except Exception as e:
            print(f"User client error: {e}")
            return
    
    # Get bot token from CSV or config
    bot_token = bot.get_bot_token()
    if not bot_token:
        bot_token = input("Enter your bot token (from @BotFather): ")
        bot.config['bot_token'] = bot_token
        bot.save_config()
        bot.save_config()
    
    # Initialize bot client for commands
    bot_client = TelegramClient(
        'hybrid_bot',
        api_id=api_id,
        api_hash=api_hash,
        connection_retries=5,
        retry_delay=3,
        timeout=30,
        request_retries=5
    )
    bot.bot_client = bot_client
    
    # Start bot client with retry logic
    max_retries = 3
    retry_count = 0
    bot_me = None
    while retry_count < max_retries:
        try:
            await bot_client.start(bot_token=bot_token)
            bot_me = await bot_client.get_me()
            break  # Success, exit retry loop
        except TimeoutError as e:
            retry_count += 1
            if retry_count < max_retries:
                console.print(f"[yellow]Bot connection timeout (attempt {retry_count}/{max_retries}). Retrying in 5 seconds...[/yellow]")
                await asyncio.sleep(5)
            else:
                console.print(f"[bold red]Failed to connect bot after {max_retries} attempts. Please check your internet connection.[/bold red]")
                return
        except Exception as e:
            console.print(f"[bold red]Bot client error: {e}[/bold red]")
            return

    # Test ping/latency
    try:
        import time
        start_time = time.time()
        await user_client.get_me()
        ping_ms = int((time.time() - start_time) * 1000)
    except Exception:
        ping_ms = 0

    # Display clean status
    console.print(f"\n[bold green]{'=' * 60}[/bold green]")
    console.print(f"[bold white]BOT STATUS[/bold white]")
    console.print(f"[bold green]{'=' * 60}[/bold green]")
    console.print(f"[cyan]Bot:[/cyan] @{bot_me.username}")
    console.print(f"[cyan]User:[/cyan] {me.first_name} (@{me.username or 'unknown'})")
    console.print(f"[cyan]Ping:[/cyan] {ping_ms}ms")
    console.print(f"[cyan]Mode:[/cyan] UNLIMITED")
    console.print(f"[cyan]Rate Delay:[/cyan] {bot.config.get('rate_limit_delay', 5)}s")
    console.print(f"[green]Status:[/green] Online & Ready")
    console.print(f"[bold green]{'=' * 60}[/bold green]\n")

    # Send notification silently
    try:
        await bot_client.send_message(me.id,
            f"UNLIMITED AD SENDER STARTED\n\n"
            f"User: {me.first_name}\n"
            f"Bot: @{bot_me.username}\n"
            f"Mode: UNLIMITED\n"
            f"Ping: {ping_ms}ms\n"
            f"Rate Delay: {bot.config.get('rate_limit_delay', 5)}s\n\n"
            f"Send /start to @{bot_me.username} to control!"
        )
        # Attempt to send a startup image if one exists in the project folder.
        # The file should be named `start_image.jpg` and placed in the bot project directory.
        try:
            start_img_path = os.path.abspath('start_image.jpg')
            if os.path.exists(start_img_path):
                send_target = None
                # Prefer the configured log channel, otherwise fallback to the owner
                if bot.config.get('log_channel_id'):
                    send_target = bot.config.get('log_channel_id')
                elif bot.config.get('owner_chat_id'):
                    send_target = bot.config.get('owner_chat_id')

                if send_target:
                    caption = bot.config.get('start_image_caption', f"{bot_me.first_name or bot_me.username} is online 🚀")
                    try:
                        await bot_client.send_file(send_target, start_img_path, caption=caption)
                        console.print(f"[green]Startup image sent to {send_target}[/green]")
                    except Exception as e:
                        console.print(f"[yellow]Failed to send startup image: {e}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Startup image check failed: {e}[/yellow]")

        # Flush any buffered logs now that clients are available
        try:
            await bot.flush_log_buffer()
        except Exception:
            pass
        # Start background enforcers (bio enforcement)
        try:
            asyncio.create_task(bot.enforce_bio_loop())
        except Exception:
            pass

    except Exception as e:
        console.print(f"[yellow]Could not send startup message: {e}[/yellow]")
    
    # Bot command handlers
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def cmd_start(event):
        status = await bot.get_status()
        buttons = [
            [Button.inline("🚀 Send Ads", b"send_ads")],
            [Button.inline("⏹️ Stop", b"stop"), Button.inline("⏸️ Pause", b"pause")],
            [Button.inline("⚙️ Settings", b"settings"), Button.inline("🔍 Scrape", b"scrape")],
            [Button.inline("📱 Help", b"help"), Button.inline("🔄 Refresh", b"refresh")]
        ]
        await event.respond(status, buttons=buttons)
    
    @bot_client.on(events.CallbackQuery())
    async def handle_callback(event):
        try:
            # Decode callback data safely
            try:
                data = event.data.decode() if event.data else None
            except Exception:
                data = None

            # Debug receipt (safe access to possible missing attributes)
            msg = getattr(event, 'message', None)
            msg_id = getattr(msg, 'id', None) if msg else None
            print(f"[DEBUG] Callback received - data={data} sender={getattr(event, 'sender_id', None)} chat_id={getattr(event, 'chat_id', None)} message_id={msg_id}")

            # Acknowledge the callback immediately to prevent it expiring
            try:
                await event.answer()
            except Exception:
                pass

            if data == "start":
                # Unlimited sending has been disabled to avoid accidental mass sending.
                await bot.safe_callback_answer(event, "⚠️ Unlimited sending mode is disabled.")

            elif data == "send_ads":
                # Admin-protected explicit start for sending ads
                try:
                    sender = getattr(event, 'sender_id', None)
                    # Reload admin list from config.json on each request so changes take effect
                    try:
                        cfg_path = os.path.abspath('config.json')
                        with open(cfg_path, 'r', encoding='utf-8') as cf:
                            cfg_disk = json.load(cf)
                        admins = cfg_disk.get('admin_users', []) or []
                    except Exception:
                        admins = bot.config.get('admin_users', []) or []

                    if sender not in admins:
                        await bot.safe_callback_answer(event, "❌ Admin only command!")
                    else:
                        if getattr(bot, 'is_sending', False):
                            await bot.safe_callback_answer(event, "Already sending")
                        else:
                            await bot.safe_callback_answer(event, "🚀 Starting send loop...")
                            try:
                                # enable manual mode to reduce cycle delay
                                try:
                                    bot.manual_mode = True
                                except Exception:
                                    pass
                                asyncio.create_task(bot.send_to_groups())
                            except Exception as _e:
                                await bot.safe_callback_answer(event, "⚠️ Failed to start send loop")
                except Exception:
                    # Fallback acknowledgement
                    try:
                        await bot.safe_callback_answer(event, "⚠️ Could not process request")
                    except Exception:
                        pass

            elif data == "stop":
                bot.is_sending = False
                await bot.safe_callback_answer(event, "Stopped")

            elif data == "scrape":
                if not bot.is_scraping:
                    await bot.safe_callback_answer(event, "Starting scraping...")
                    asyncio.create_task(bot.handle_scraping_task(event))
                else:
                    await bot.safe_callback_answer(event, "Already scraping")

            elif data == "pause":
                bot.is_paused = True
                bot.is_sending = False
                await bot.safe_callback_answer(event, "Paused sending")

            elif data == "quicksetup":
                # Provide quick setup instructions
                text = (
                    "QUICK SETUP\n\n"
                    "1) /setmsg [text] - set ad message\n"
                    "2) /setrate [seconds] - set rate delay\n"
                    "3) /setlog [ID] - set log channel\n"
                    "4) /addgroup [ID] - add target group\n\n"
                    "Use the above commands to configure quickly."
                )
                await bot.safe_callback_answer(event, edit_text=text)

            elif data == "dashboard":
                status = await bot.get_status()
                await bot.safe_callback_answer(event, edit_text=status)

            elif data == "settings":
                cfg = bot.config
                log_id = cfg.get('log_channel_id') or 'Not set'
                text = (
                    f"SETTINGS\n\nRate delay: {cfg.get('rate_limit_delay')}s\n"
                    f"Cycle delay: {cfg.get('cycle_delay')}s\n"
                    f"Min members: {cfg.get('min_members')}\n"
                    f"Max members: {cfg.get('max_members')}\n"
                    f"Log channel: {log_id}\n"
                    f"Owner chat ID: {cfg.get('owner_chat_id', 'Not set')}\n\n"
                    "Commands:\n/setrate [s]\n/setlog [ID]\n/setadurl (reply to a message or t.me/c/xxxx/yyyy)"
                )
                await bot.safe_callback_answer(event, edit_text=text)

            elif data == "help":
                help_text = (
                    "HELP\n\nCommands available:\n"
                    "/start - Start the bot\n"
                    "/stop - Stop the bot\n"
                    "/pause - Pause sending\n"
                    "/scrape - Scrape groups\n"
                    "/settings - View settings\n"
                    "/help - Show this help message"
                )
                await bot.safe_callback_answer(event, edit_text=help_text)

        except Exception as e:
            # Log and attempt to notify the user/admin about the error
            print(f"Error in callback handler: {e}")
            try:
                await bot.safe_callback_answer(event, edit_text="⚠️ An internal error occurred while handling your action.")
            except Exception:
                pass

    # Text commands
    @bot_client.on(events.NewMessage(pattern='/settopic'))
    async def cmd_set_topic(event):
        """Set target topic name for forums"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
            
        try:
            topic_name = event.text.replace('/settopic', '', 1).strip()
            if topic_name:
                bot.config['target_topic_name'] = topic_name
                bot.save_config()
                await event.reply(f"✅ Target topic set to: **{topic_name}**\n\nForums will now target topics containing this name.")
            else:
                current_topic = bot.config.get('target_topic_name', 'instagram')
                await event.reply(f"📝 Current target topic: **{current_topic}**\n\n❌ Usage: /settopic instagram\n\nThis will target topics named 'instagram' or containing 'instagram' in forums.")
        except Exception as e:
            await event.reply(f"❌ Failed to set topic: {e}")
    
    @bot_client.on(events.NewMessage(pattern='/addgroup'))
    async def cmd_add_group(event):
        try:
            group_id = int(event.text.split()[1])
            if group_id not in bot.config['target_groups']:
                bot.config['target_groups'].append(group_id)
                bot.save_config()
                await event.reply(f"✅ Added group `{group_id}` to targets!")
            else:
                await event.reply("❌ Group already in list!")
        except:
            await event.reply("❌ Usage: /addgroup -1001234567890")
    
    @bot_client.on(events.NewMessage(pattern='/setmsg'))
    async def cmd_set_message(event):
        msg = event.text.replace('/setmsg', '', 1).strip()
        if msg:
            bot.config['ad_message'] = msg
            # Clear any previous ad forward config
            bot.config.pop('ad_forward_from_chat', None)
            bot.config.pop('ad_forward_message_id', None)
            bot.save_config()
            await event.reply("✅ Message updated!")
        else:
            await event.reply("❌ Usage: /setmsg Your ad message here")

    @bot_client.on(events.NewMessage(pattern='/setadurl'))
    async def cmd_set_ad_url(event):
        """
        Set the ad to forward by replying to a message or providing a t.me/c/xxxx/yyyy URL.
        Usage:
        1. Reply to a message with /setadurl
        2. /setadurl https://t.me/c/xxxx/yyyy
        """
        # Debug: log invocation so we can confirm handler is triggered
        try:
            console.print(f"[blue][DEBUG][/blue] /setadurl triggered by sender={getattr(event,'sender_id',None)} is_reply={getattr(event,'is_reply',False)} text={getattr(event,'text','')[:200]}")
        except Exception:
            print(f"DEBUG: /setadurl triggered by sender={getattr(event,'sender_id',None)}")

        # Helper to extract a usable chat_id from a Telethon Message
        def _chat_id_from_message(reply_msg):
            # Prefer explicit chat_id
            if getattr(reply_msg, 'chat_id', None):
                return reply_msg.chat_id
            # Try to extract channel id and convert to -100... format
            to_id = getattr(reply_msg, 'to_id', None)
            if to_id:
                cid = getattr(to_id, 'channel_id', None)
                if cid:
                    return int(f"-100{cid}")
            peer = getattr(reply_msg, 'peer_id', None)
            if peer:
                cid = getattr(peer, 'channel_id', None)
                if cid:
                    return int(f"-100{cid}")
                cid = getattr(peer, 'chat_id', None)
                if cid:
                    return cid
            # Fallback to sender (user) id
            if getattr(reply_msg, 'sender_id', None):
                return reply_msg.sender_id
            return None

        # If the command is a reply to a message, use that
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            chat_id = _chat_id_from_message(reply_msg)
            if chat_id is None:
                await event.reply("❌ Could not determine chat ID from the replied message.")
                return
            bot.config['ad_forward_from_chat'] = chat_id
            bot.config['ad_forward_message_id'] = reply_msg.id
            bot.save_config()
            await event.reply(f"✅ Ad post set from replied message (chat_id={chat_id}, message_id={reply_msg.id})!")
            return
        # If a URL is provided, parse it
        url = event.text.replace('/setadurl', '', 1).strip()
        import re
        # Accept forms like: https://t.me/c/1234567890/123 or t.me/c/123/123
        # Accept either numeric /c/ URLs or username URLs like t.me/username/123
        m = re.search(r'(?:https?://)?(?:www\.)?t\.me/(?:c/)?([^/]+)/([0-9]+)', url)
        if m:
            raw_chat = m.group(1)
            msg_id = int(m.group(2))
            # If raw_chat is purely digits (from /c/ links), convert to -100<id>
            if raw_chat.isdigit():
                try:
                    chat_id = int(f"-100{raw_chat}")
                except Exception:
                    await event.reply("❌ Failed to parse numeric chat id from URL.")
                    return
                bot.config['ad_forward_from_chat'] = chat_id
                bot.config['ad_forward_message_id'] = msg_id
                bot.save_config()
                await event.reply(f"✅ Ad post set from URL (chat_id={chat_id}, message_id={msg_id})!")
                return

            # Otherwise treat raw_chat as a username; store the username and message id
            username = raw_chat.lstrip('@')
            bot.config['ad_forward_from_chat'] = username
            bot.config['ad_forward_message_id'] = msg_id
            bot.save_config()
            await event.reply(f"✅ Ad post set from username URL (username={username}, message_id={msg_id})!")
            return

        await event.reply("❌ Usage: /setadurl (reply to a message or provide t.me/c/xxxx/yyyy URL)")
    
    @bot_client.on(events.NewMessage(pattern='/setlog'))
    async def cmd_set_log(event):
        try:
            channel_id = int(event.text.split()[1])
            bot.config['log_channel_id'] = channel_id
            bot.save_config()
            
            # Test log message
            await bot.log_to_channel("🎯 Log channel successfully configured!", "SUCCESS")
            await event.reply(f"✅ Log channel set to: `{channel_id}`\nTest message sent!")
        except:
            await event.reply("❌ Usage: /setlog -1001234567890\n(Use channel/group ID)")
    
    @bot_client.on(events.NewMessage(pattern='/setrate'))
    async def cmd_set_rate(event):
        try:
            delay = int(event.text.split()[1])
            bot.config['rate_limit_delay'] = delay
            bot.save_config()
            await event.reply(f"✅ Rate limit delay set to {delay} seconds")
        except:
            await event.reply("❌ Usage: /setrate 5")
    
    @bot_client.on(events.NewMessage(pattern='/listgroups'))
    async def cmd_list_groups(event):
        targets = bot.config['target_groups']
        if targets:
            text = f"🎯 **Target Groups ({len(targets)}):**\n\n"
            for i, gid in enumerate(targets, 1):
                try:
                    entity = await user_client.get_entity(gid)
                    text += f"{i}. {entity.title} (`{gid}`)\n"
                except:
                    text += f"{i}. `{gid}` (Can't get name)\n"
                    
                if i >= 20:  # Show only first 20
                    text += f"\n... and {len(targets) - 20} more groups"
                    break
            await event.reply(text)
        else:
            await event.reply("❌ No target groups. Use /addgroup [ID] to add.")
    
    @bot_client.on(events.NewMessage(pattern='/credentials'))
    async def credentials_status(event):
        """Show credential status"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        text = "🔐 **Credential Status:**\n\n"
        
        # Show loaded credentials
        for cred_type, creds in bot.credentials.items():
            desc = creds.get('description', 'No description')
            session = creds.get('session_name', 'N/A')
            text += f"✅ **{cred_type}**: {desc}\n"
            text += f"   Session: `{session}`\n\n"
        
        if not bot.credentials:
            text += "❌ No credentials loaded from CSV file"
        
        await event.reply(text)
    
    @bot_client.on(events.NewMessage(pattern='/help'))
    async def help_command(event):
        """Show all available commands"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        text = "🤖 **Hybrid Telegram Bot Commands**\n\n"
        
        text += "**🎯 Targeting Commands:**\n"
        text += "/autopopulate - Auto-populate with priority targeting\n"
        text += "/supergroups - Target only supergroups (no flood waits)\n"
        text += "/addgroup [ID] - Add group to targets manually\n"
        text += "/listgroups - Show current target groups\n\n"
        
        text += "**📊 Statistics & Info:**\n"
        text += "/groupstats - Show groups database with type breakdown\n"
        text += "/resetstats - Reset sending statistics\n"
        text += "/credentials - Show loaded API credentials\n\n"
        
        text += "**⚙️ Configuration:**\n"
        text += "/setmsg [text] - Change advertisement message\n"
        text += "/settopic [name] - Set target topic name for forums\n"
        text += "/setlog [ID] - Set log channel for notifications\n"
        text += "/setrate [seconds] - Set rate limiting delay\n\n"
        
        text += "**🔍 Group Types:**\n"
        text += "🏛️ Forums - Targets specific topic name (default: 'instagram')\n"
        text += "🏢 Supergroups - Large groups with high engagement\n"
        text += "👥 Regular Groups - Standard Telegram groups\n\n"
        
        text += "**💡 Pro Tips:**\n"
        text += "• Use /settopic to change forum target topic\n"
        text += "• Forums target only matching topic names\n"
        text += "• Supergroups for flood-free sending"
        
        await event.reply(text)
    
    @bot_client.on(events.NewMessage(pattern='/autopopulate'))
    async def auto_populate_command(event):
        """Auto-populate target groups prioritizing forums and supergroups"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        stats = bot.get_groups_stats()
        text = f"📊 **Groups Database Stats:**\n\n"
        text += f"📁 **Total:** {stats['total']}\n"
        text += f"🏛️ **Forums:** {stats['forums']} ({stats['suitable_forums']} suitable)\n"
        text += f"🏢 **Supergroups:** {stats['supergroups']} ({stats['suitable_supergroups']} suitable)\n"
        text += f"👥 **Regular Groups:** {stats['regular_groups']} ({stats['suitable_regular_groups']} suitable)\n"
        text += f"📢 **Channels:** {stats['channels']} (excluded)\n\n"
        
        populated = bot.auto_populate_target_groups(prefer_forums_supergroups=True)
        if populated > 0:
            text += f"✅ **Auto-populated {populated} target groups!**\n"
            text += f"**Priority:** Forums → Supergroups → Regular Groups\n"
            text += f"**Filter:** {bot.config['min_members']}-{bot.config['max_members']:,} members"
        else:
            text += "❌ No suitable groups found for auto-population"
        
        await event.reply(text)
    
    @bot_client.on(events.NewMessage(pattern='/supergroups'))
    async def supergroups_targeting_command(event):
        """Target only supergroups (avoid forum flood waits)"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        stats = bot.get_groups_stats()
        
        # Get supergroup-only targets
        supergroup_targets = []
        for group_data in bot.groups_database.values():
            if (group_data.get('type') == 'group' and 
                bot.config['min_members'] <= group_data.get('participant_count', 0) <= bot.config['max_members'] and
                group_data.get('group_type') == 'supergroup'):
                supergroup_targets.append(group_data['id'])
        
        # Update target groups with supergroups only
        bot.config['target_groups'] = supergroup_targets
        bot.save_config()
        text = f"🏢 **Supergroups Targeting Activated!**\n\n"
        text += f"📊 **Available Supergroups:** {stats['supergroups']}\n"
        text += f"✅ **Selected:** {len(supergroup_targets)} supergroups\n\n"
        text += f"**Benefits:**\n"
        text += f"• Reliable delivery (no forum flood waits)\n"
        text += f"• Large audiences\n"
        text += f"• High engagement\n"
        text += f"• Filter: {bot.config['min_members']}-{bot.config['max_members']:,} members"
        
        await event.reply(text)
    
    @bot_client.on(events.NewMessage(pattern='/groupstats'))
    async def group_stats_command(event):
        """Show groups database statistics with forum/supergroup breakdown"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        stats = bot.get_groups_stats()
        configured_targets = len(bot.config.get('target_groups', []))
        
        text = f"📊 **Groups Database Statistics:**\n\n"
        text += f"📁 **Total Scraped:** {stats['total']}\n"
        text += f"🏛️ **Forums:** {stats['forums']} ({stats['suitable_forums']} suitable)\n"
        text += f"🏢 **Supergroups:** {stats['supergroups']} ({stats['suitable_supergroups']} suitable)\n"
        text += f"👥 **Regular Groups:** {stats['regular_groups']} ({stats['suitable_regular_groups']} suitable)\n"
        text += f"📢 **Channels:** {stats['channels']} (excluded from targeting)\n"
        text += f"📌 **Configured Targets:** {configured_targets}\n\n"
        
        text += f"**Targeting Priority:**\n"
        text += f"1. 🏛️ Forums (premium group type)\n"
        text += f"2. 🏢 Supergroups (high engagement)\n"
        text += f"3. 👥 Regular Groups (standard)\n\n"
        
        text += f"**Filters Applied:**\n"
        text += f"• Type: Groups only (no channels)\n"
        text += f"• Members: {bot.config['min_members']}-{bot.config['max_members']:,}\n\n"
        
        text += f"**Commands:**\n"
        text += f"/autopopulate - Auto-populate with priority targeting\n"
        text += f"/listgroups - Show current target groups"
        
        await event.reply(text)
    
    @bot_client.on(events.NewMessage(pattern='/resetstats'))
    async def reset_stats_command(event):
        """Reset sending statistics"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        
        bot.reset_stats()
        await event.reply("✅ **Statistics Reset!**\n\nAll sending stats have been cleared:\n• Total sent: 0\n• Group stats cleared\n• Message count reset")

    @bot_client.on(events.NewMessage(pattern='/setbioenforce'))
    async def cmd_set_bio_enforce(event):
        """Toggle bio enforcement on/off (admin only)"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return

        try:
            parts = event.text.split()
            if len(parts) < 2:
                await event.reply(
                    f"✅ Current enforce_bio: {bot.config.get('enforce_bio')}\nUsage: /setbioenforce on|off"
                )
                return

            val = parts[1].lower()
            if val in ('on', 'true', '1'):
                bot.config['enforce_bio'] = True
            else:
                bot.config['enforce_bio'] = False
            bot.save_config()
            await event.reply(f"✅ enforce_bio set to: {bot.config['enforce_bio']}")
        except Exception as e:
            await event.reply(f"❌ Error toggling enforce_bio: {e}")

    @bot_client.on(events.NewMessage(pattern='/setautobio'))
    async def cmd_set_auto_bio(event):
        """Set the auto_bio text (admin only)"""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return

        try:
            new_bio = event.text.replace('/setautobio', '', 1).strip()
            if not new_bio:
                await event.reply("❌ Usage: /setautobio Your new bio text here")
                return
            bot.config['auto_bio'] = new_bio
            bot.save_config()
            await event.reply("✅ auto_bio updated!")
            # Try to apply immediately to user client and report result
            try:
                if bot.user_client:
                    success, info = await bot.set_user_bio(bot.user_client)
                    if success:
                        await event.reply(f"✅ auto_bio applied to user (info={info})")
                    else:
                        await event.reply(f"⚠️ auto_bio applied but failed: {info}")
            except Exception:
                pass
        except Exception as e:
            await event.reply(f"❌ Error setting auto_bio: {e}")

    @bot_client.on(events.NewMessage(pattern='/forcebio'))
    async def cmd_force_bio(event):
        """Force immediate bio update using the user client (admin only)."""
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return

        if not bot.user_client:
            await event.reply("❌ No user client available to set bio")
            return

        try:
            success, info = await bot.set_user_bio(bot.user_client)
            if success:
                await event.reply(f"✅ Bio updated successfully (info={info})")
            else:
                await event.reply(f"⚠️ Bio update failed or no change: {info}")
        except Exception as e:
            await event.reply(f"❌ Error forcing bio update: {e}")

    @bot_client.on(events.NewMessage(pattern='/reenablebio'))
    async def cmd_reenable_bio(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        bot.config['enforce_bio'] = True
        bot.save_config()
        await event.reply("✅ Bio enforcement re-enabled")

    @bot_client.on(events.NewMessage(pattern='/biostatus'))
    async def cmd_bio_status(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        status = {
            'enforce_bio': bot.config.get('enforce_bio'),
            'auto_bio': bot.config.get('auto_bio'),
            'bio_enforce_interval_minutes': bot.config.get('bio_enforce_interval_minutes'),
            'bio_enforce_max_failures': bot.config.get('bio_enforce_max_failures'),
        }
        await event.reply(f"✅ Bio Status: {status}")

    @bot_client.on(events.NewMessage(pattern='/setbioconsent'))
    async def cmd_set_bio_consent(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        parts = event.text.split()
        if len(parts) < 2:
            await event.reply(
                f"✅ Current bio_consent_given: {bot.config.get('bio_consent_given')}\nUsage: /setbioconsent on|off"
            )
            return
        val = parts[1].lower()
        bot.config['bio_consent_given'] = val in ('on', 'true', '1', 'yes')
        bot.save_config()
        await event.reply(f"✅ bio_consent_given set to: {bot.config['bio_consent_given']}")
    
    # Register admin helpers: listblocked, unblock, listtopicfails, cleartopicfails
    @bot_client.on(events.NewMessage(pattern='/listblocked'))
    async def cmd_listblocked(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        await bot._handle_listblocked(event)

    @bot_client.on(events.NewMessage(pattern='/unblock'))
    async def cmd_unblock(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        await bot._handle_unblock(event)

    @bot_client.on(events.NewMessage(pattern='/listtopicfails'))
    async def cmd_listtopicfails(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        await bot._handle_listtopicfails(event)

    @bot_client.on(events.NewMessage(pattern='/cleartopicfails'))
    async def cmd_cleartopicfails(event):
        if event.sender_id not in bot.config.get('admin_users', []):
            await event.reply("❌ Admin only command!")
            return
        await bot._handle_cleartopicfails(event)
    
    # Handlers registered, start running
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())

    pass

    pass
