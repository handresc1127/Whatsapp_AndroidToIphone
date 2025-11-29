# WhatsApp Android → iOS Migration Tool - Copilot Instructions

## 📋 Project Overview

This is a **Python tool** for migrating WhatsApp chat history from Android to iOS devices. The project uses **only Python standard library** modules (no external dependencies for core functionality).

**Key Objective:** Preserve message text, timestamps, contacts, and group chats during cross-platform migration.

---

## 🏗️ Project Architecture

### Modular Design (5 Core Modules)

```
src/
├── main.py              # Entry point, orchestration, user interaction
├── migrate.py           # Core migration engine (schema conversion)
├── android_backup.py    # ADB operations, .ab file extraction
├── ios_backup.py        # iTunes backup manipulation
└── utils.py             # Logging, validation, ADB commands
```

### External Dependencies (Not Python Packages)

1. **ADB (Android Debug Bridge):** `bin/adb.exe` + 2 DLLs
2. **Legacy WhatsApp APK:** `apk/WhatsApp_2.11.431.apk` (versions 2.11.431-2.11.498)
3. **iTunes/Finder:** For iOS device backups

---

## 🎯 Technology Stack

- **Python Version:** 3.8+ (type hints, pathlib, modern features)
- **Standard Library Modules:**
  - `sqlite3` - Database manipulation
  - `subprocess` - ADB command execution
  - `pathlib` - Cross-platform paths
  - `logging` - Structured logging
  - `json` - Manifest.db parsing
  - `shutil` - File operations
  - `datetime` - Timestamp conversions
  - `hashlib` - iOS backup file hashing
  
- **No External Dependencies:** Project uses ONLY Python stdlib

---

## 🔧 Coding Standards

### Python Code Style

**PEP 8 Compliance:**
- 4 spaces indentation
- Max line length: 88 characters (Black formatter)
- Snake_case for functions/variables
- PascalCase for classes

**Type Hints (Mandatory):**
```python
def convert_timestamp(android_ms: int) -> float:
    """Convert Android timestamp to iOS format."""
    APPLE_EPOCH_OFFSET = 978307200
    return (android_ms / 1000) - APPLE_EPOCH_OFFSET
```

**Docstrings (Google Style):**
```python
def run_migration(android_db: str, ios_db: str) -> Dict[str, int]:
    """Execute complete database migration.
    
    Args:
        android_db: Path to msgstore.db (Android)
        ios_db: Path to ChatStorage.sqlite (iOS)
        
    Returns:
        Dictionary with migration statistics:
        - messages: int (count of messages migrated)
        - contacts: int (count of contacts migrated)
        - groups: int (count of groups migrated)
        
    Raises:
        sqlite3.DatabaseError: If database access fails
        FileNotFoundError: If input files don't exist
    """
```

**Error Handling (Always with Rollback):**
```python
try:
    conn.execute("BEGIN TRANSACTION")
    # ... database operations
    conn.commit()
except Exception as e:
    conn.rollback()
    logger.error(f"Migration failed: {e}")
    raise
finally:
    conn.close()
```

**Logging (Structured):**
```python
import logging

# Setup in main
logger = logging.getLogger(__name__)

# Usage
logger.info("Starting migration...")
logger.warning("Large database detected")
logger.error(f"Failed to connect: {error}")
logger.debug(f"Query result: {result}")  # Verbose mode only
```

---

## 📊 Database Schemas

### Android msgstore.db (SQLite)

**Key Tables:**
```sql
messages (
    _id INTEGER PRIMARY KEY,
    key_remote_jid TEXT,        -- Contact/group identifier
    key_from_me INTEGER,        -- 1=sent, 0=received
    data TEXT,                  -- Message text content
    timestamp INTEGER,          -- Unix epoch milliseconds
    status INTEGER,             -- Delivery status
    media_wa_type INTEGER,      -- 0=text, 1=image, etc.
    starred INTEGER,            -- 1=starred
    quoted_row_id INTEGER       -- Reply to message ID
)

chat (
    _id INTEGER PRIMARY KEY,
    jid TEXT UNIQUE,            -- Chat identifier
    subject TEXT,               -- Group name (if group)
    created_timestamp INTEGER
)

jid (
    _id INTEGER PRIMARY KEY,
    raw_string TEXT UNIQUE,     -- Full JID (e.g., "1234567890@s.whatsapp.net")
    type INTEGER                -- 0=contact, 1=group
)

group_participants (
    _id INTEGER PRIMARY KEY,
    gjid TEXT,                  -- Group JID
    jid TEXT,                   -- Member JID
    admin INTEGER               -- 1=admin, 0=member
)
```

### iOS ChatStorage.sqlite (Core Data)

**Key Entities:**
```sql
ZWAMESSAGE (
    Z_PK INTEGER PRIMARY KEY,
    ZISFROMME INTEGER,          -- 1=sent, 0=received
    ZTEXT TEXT,                 -- Message text
    ZMESSAGEDATE REAL,          -- Apple epoch seconds (2001-01-01 base)
    ZMESSAGESTATUS INTEGER,
    ZMESSAGETYPE INTEGER,       -- 0=text, 1=image, etc.
    ZISSTARRED INTEGER,
    ZFROMJID TEXT,              -- Sender JID
    ZTOJID TEXT                 -- Recipient JID
)

ZWACHATSESSION (
    Z_PK INTEGER PRIMARY KEY,
    ZCONTACTJID TEXT,           -- Chat identifier
    ZPARTNERNAME TEXT,          -- Contact/group name
    ZLASTMESSAGEDATE REAL,
    ZUNREADCOUNT INTEGER,
    ZARCHIVED INTEGER
)

ZWAGROUPMEMBER (
    Z_PK INTEGER PRIMARY KEY,
    ZCONTACTJID TEXT,           -- Member JID
    ZMEMBERJID TEXT,
    ZISADMIN INTEGER,           -- 1=admin
    ZCHATSESSION INTEGER        -- FK to ZWACHATSESSION
)
```

---

## ⏱️ Timestamp Conversion (Critical)

### Epoch Difference

| Platform | Epoch Start | Units | Example |
|----------|-------------|-------|---------|
| Android  | 1970-01-01  | Milliseconds | `1700000000000` |
| iOS      | 2001-01-01  | Seconds | `721692800.0` |

**Offset Constant:** `978307200` seconds (time between 1970-01-01 and 2001-01-01)

### Conversion Formula

```python
def _convert_timestamp(android_timestamp_ms: int) -> float:
    """Convert Android Unix timestamp to iOS Apple timestamp.
    
    Formula: iOS = (Android / 1000) - 978307200
    
    Args:
        android_timestamp_ms: Unix epoch milliseconds (1970-01-01 base)
        
    Returns:
        Apple epoch seconds (2001-01-01 base)
    """
    APPLE_EPOCH_OFFSET = 978307200  # Seconds between epochs
    
    # Convert milliseconds to seconds
    android_sec = android_timestamp_ms / 1000
    
    # Subtract Apple epoch offset
    ios_timestamp = android_sec - APPLE_EPOCH_OFFSET
    
    return ios_timestamp
```

**Edge Cases:**
- **Null timestamps:** Use current time as fallback
- **Zero timestamps:** Use current time
- **Range validation:** Ensure result is between 0 (2001-01-01) and ~1893456000 (2060-01-01)

---

## 🔄 Migration Process Flow

### 6-Step Pipeline

```python
def run_migration_pipeline():
    """Execute complete migration process."""
    
    # Step 1: Validate Dependencies
    validate_dependencies()
    # - Check Python version (≥3.8)
    # - Verify ADB executable exists
    # - Confirm legacy APK present
    # - Locate iTunes backup directory
    # - Test Android device connection
    
    # Step 2: Backup Current Android WhatsApp
    backup_android_whatsapp()
    # - Save current WhatsApp APK
    # - Backup /sdcard/WhatsApp/ data folder
    # - Store in backups/ with timestamp
    
    # Step 3: Downgrade to Legacy WhatsApp
    downgrade_whatsapp()
    # - Uninstall current WhatsApp (keep data)
    # - Install legacy APK (2.11.431)
    # - Prompt user to verify phone number
    
    # Step 4: Create Android Backup
    create_android_backup()
    # - Execute: adb backup -f tmp/whatsapp.ab com.whatsapp
    # - User confirms on Android screen
    # - Extract .ab → tar → msgstore.db
    
    # Step 5: Migrate Database
    migrate_database()
    # - Read Android msgstore.db
    # - Convert schema: Android tables → iOS Core Data entities
    # - Convert timestamps: Unix ms → Apple seconds
    # - Migrate messages, contacts, groups
    # - Validate data integrity
    
    # Step 6: Inject into iOS Backup
    inject_ios_backup()
    # - Backup original ChatStorage.sqlite
    # - Replace with migrated database
    # - Update Manifest.db with new file hash
    # - Instruct user to restore via iTunes/Finder
```

---

## 🛡️ Safety and Backup Strategy

### Automatic Backups Created

1. **Before Android downgrade:**
   - `backups/WhatsApp_current_YYYYMMDD_HHMMSS.apk`
   - `backups/WhatsApp_data_YYYYMMDD_HHMMSS.tar`

2. **Before iOS modification:**
   - `backups/ChatStorage_original_YYYYMMDD_HHMMSS.sqlite`

### Rollback Procedure

```python
def rollback_migration(stage: str):
    """Rollback migration if errors occur."""
    
    if stage == 'android_downgrade':
        # Reinstall original WhatsApp
        run_adb_command(['install', '-r', latest_apk_backup])
        
    elif stage == 'ios_modification':
        # Restore original ChatStorage.sqlite
        restore_file(
            source='backups/ChatStorage_original_*.sqlite',
            destination=ios_chatstorage_path
        )
        
        # Update Manifest.db
        update_manifest_hash(backup_dir, ios_chatstorage_path)
```

---

## 🚨 Critical Constraints

### SQLite Transactions (ALWAYS Required)

```python
# ✅ CORRECT: Always use try-except with rollback
try:
    conn.execute("BEGIN TRANSACTION")
    
    # ... database operations
    conn.execute("INSERT INTO ...")
    conn.execute("UPDATE ...")
    
    conn.commit()
    logger.info("Migration successful")
    
except Exception as e:
    conn.rollback()
    logger.error(f"Migration failed: {e}")
    raise
    
finally:
    conn.close()
```

```python
# ❌ INCORRECT: No error handling
conn.execute("INSERT INTO ...")  # If fails, leaves DB in bad state
conn.commit()
```

### Path Resolution (Cross-Platform)

```python
# ✅ CORRECT: Use pathlib for cross-platform paths
from pathlib import Path

project_root = Path(__file__).parent.parent
android_db_path = project_root / 'tmp' / 'msgstore.db'
ios_backup_dir = Path(os.getenv('APPDATA')) / 'Apple Computer' / 'MobileSync' / 'Backup'
```

```python
# ❌ INCORRECT: Hard-coded paths
android_db_path = 'd:\\tmp\\msgstore.db'  # Breaks on macOS/Linux
```

### ADB Command Execution

```python
# ✅ CORRECT: Use subprocess with error handling
import subprocess

def run_adb_command(args: list) -> str:
    """Execute ADB command with error handling."""
    
    adb_path = 'bin/adb.exe'  # Windows
    # adb_path = 'adb' for macOS/Linux (assumes in PATH)
    
    try:
        result = subprocess.run(
            [adb_path] + args,
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB command failed: {e.stderr}")
        raise
    except subprocess.TimeoutExpired:
        logger.error("ADB command timed out")
        raise
```

---

## 🔍 Known Limitations

### What Gets Migrated

✅ **Included:**
- Message text (sent/received)
- Timestamps (accurate to the second)
- Contact names and phone numbers
- Group names and participants
- Message delivery/read status
- Quoted/reply messages (best effort)

### What Doesn't Get Migrated

❌ **Not Included:**
- **Media files** (photos, videos, voice messages, documents)
- Stickers and GIFs
- Group admin permissions (iOS resets)
- Muted chat settings
- Wallpapers and chat colors
- Starred messages
- Archived chats status
- Status updates
- Call history
- Broadcast lists

**Reason for media exclusion:**
- Different storage locations (Android `/sdcard/` vs iOS app container)
- Different file naming and encryption
- Complex Core Data relationships
- Would make backups massive (gigabytes)

---

## 📁 File Locations and Hashes

### Android Backup Structure

```
tmp/
└── apps/com.whatsapp/
    ├── db/
    │   ├── msgstore.db           # Main message database ← TARGET
    │   ├── msgstore.db-wal       # Write-Ahead Log
    │   ├── msgstore.db-shm       # Shared memory
    │   ├── wa.db                 # Contact cache
    │   └── axolotl.db            # Encryption keys
    ├── f/
    │   └── <internal files>
    └── sp/
        └── com.whatsapp_preferences.xml
```

### iOS Backup Structure

```
<UUID>/                          # Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
├── Manifest.db                  # Backup manifest (SQLite)
├── Manifest.plist
├── Info.plist
└── 7c/
    └── 7c7fba66680ef796b916b067077cc246adacf01d  # ChatStorage.sqlite ← TARGET
```

**ChatStorage.sqlite Hash:** `7c7fba66680ef796b916b067077cc246adacf01d`

**Calculation:**
```python
import hashlib

domain = "AppDomain-net.whatsapp.WhatsApp"
relative_path = "Library/ChatStorage.sqlite"
full_path = f"{domain}-{relative_path}"

file_hash = hashlib.sha1(full_path.encode('utf-8')).hexdigest()
# Result: "7c7fba66680ef796b916b067077cc246adacf01d"
```

---

## 🐛 Common Issues and Solutions

### Issue 1: ADB Device Not Found

**Symptom:** `adb devices` shows empty list

**Solutions:**
```python
# 1. Check USB debugging enabled
# Settings → Developer Options → USB Debugging

# 2. Restart ADB server
run_adb_command(['kill-server'])
run_adb_command(['start-server'])
run_adb_command(['devices'])

# 3. Check device authorization
# Unlock Android, tap "Allow" on USB debugging prompt
```

### Issue 2: Android Backup Fails

**Symptom:** `.ab` file is 0 bytes or backup hangs

**Solutions:**
```python
# 1. Ensure screen unlocked during backup
# 2. Confirm "Backup my data" prompt on Android
# 3. Leave password field BLANK (critical!)
# 4. Be patient - progress bar may appear stuck
```

### Issue 3: iOS Backup Not Found

**Symptom:** Script reports "No iOS backups found"

**Solutions:**
```python
# Windows: Install iTunes from Apple
# macOS: Update to 10.15+ (uses Finder instead of iTunes)

# Create new UNENCRYPTED backup:
# iTunes: Uncheck "Encrypt local backup"
# Finder: Uncheck "Encrypt local backup"
```

---

## 📚 Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `docs/SETUP.md` | Installation and dependencies | All users |
| `docs/USAGE.md` | Step-by-step migration guide | All users |
| `docs/ARCHITECTURE.md` | Technical deep-dive | Developers |
| `docs/research/2025-11-28-investigacion-proyecto-migracion-whatsapp.md` | Initial research | Developers |
| `README.md` | Project overview | All users |

---

## 🎨 Code Patterns and Examples

### Pattern 1: Database Migration Loop

```python
def migrate_messages(android_conn, ios_conn) -> int:
    """Migrate messages with timestamp conversion."""
    
    # Read Android messages
    android_cursor = android_conn.execute("""
        SELECT _id, key_remote_jid, key_from_me, data, timestamp, status
        FROM messages
        ORDER BY timestamp ASC
    """)
    
    # Get max iOS Z_PK for auto-increment continuation
    ios_max_pk = ios_conn.execute(
        "SELECT IFNULL(MAX(Z_PK), 0) FROM ZWAMESSAGE"
    ).fetchone()[0]
    
    next_pk = ios_max_pk + 1
    migrated = 0
    
    for row in android_cursor:
        android_id, jid, from_me, text, timestamp, status = row
        
        # Convert timestamp
        ios_timestamp = _convert_timestamp(timestamp)
        
        # Determine JID placement
        to_jid = jid if from_me else None
        from_jid = jid if not from_me else "me"
        
        # Insert into iOS
        ios_conn.execute("""
            INSERT INTO ZWAMESSAGE (
                Z_PK, Z_ENT, Z_OPT,
                ZISFROMME, ZTEXT, ZMESSAGEDATE,
                ZTOJID, ZFROMJID, ZMESSAGESTATUS
            ) VALUES (?, 1, 1, ?, ?, ?, ?, ?, ?)
        """, (next_pk, from_me, text, ios_timestamp, to_jid, from_jid, status))
        
        next_pk += 1
        migrated += 1
        
        # Progress logging
        if migrated % 1000 == 0:
            logger.info(f"Migrated {migrated} messages...")
    
    return migrated
```

### Pattern 2: Backup with Timestamp

```python
from datetime import datetime
from pathlib import Path
import shutil

def create_backup(source_path: Path, backup_dir: Path = Path('backups')) -> Path:
    """Create timestamped backup of file."""
    
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(source_path, backup_path)
    logger.info(f"Backup created: {backup_path}")
    
    return backup_path
```

### Pattern 3: User Confirmation

```python
def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation."""
    
    prompt = f"{message} ({'Y/n' if default else 'y/N'}): "
    
    while True:
        response = input(prompt).strip().lower()
        
        if response == '':
            return default
        elif response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'yes' or 'no'")
```

---

## 🔐 Security Considerations

### Data Sensitivity

- **Phone numbers:** Stored in plain text in databases
- **Message content:** Unencrypted in backups
- **Encryption keys:** Present in axolotl.db (not migrated)

### Mitigation

1. **Local processing only:** No network transmission
2. **Backup encryption:** Recommend full disk encryption (BitLocker/FileVault)
3. **Temporary file cleanup:**
   ```python
   import atexit
   import shutil
   
   def cleanup_temp_files():
       if Path('tmp/').exists():
           shutil.rmtree('tmp/')
   
   atexit.register(cleanup_temp_files)
   ```
4. **Log sanitization:** Redact phone numbers in logs
   ```python
   def redact_phone(phone: str) -> str:
       return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]
   ```

---

## 🚀 Performance Optimization

### Batch Inserts (100x Faster)

```python
# ❌ SLOW: 1 transaction per message
for message in messages:
    conn.execute("INSERT INTO ... VALUES (?)", (message,))
    conn.commit()  # Disk write every iteration

# ✅ FAST: 1 transaction for all messages
conn.execute("BEGIN TRANSACTION")
for message in messages:
    conn.execute("INSERT INTO ... VALUES (?)", (message,))
conn.commit()  # Single disk write at end
```

### Progress Feedback

```python
def migrate_with_progress(messages, total):
    """Show progress bar during migration."""
    
    for i, message in enumerate(messages):
        # Migrate message...
        
        # Update progress every 100 messages
        if i % 100 == 0:
            percent = (i / total) * 100
            print(f"\rProgress: {percent:.1f}% ({i}/{total})", end='', flush=True)
    
    print()  # Newline after completion
```

---

## 🧪 Testing

### Unit Tests

```python
import unittest

class TestTimestampConversion(unittest.TestCase):
    
    def test_convert_timestamp(self):
        # Test case: 2023-11-15 00:00:00 UTC
        android_ms = 1700000000000
        expected_ios = 721692800.0
        
        result = _convert_timestamp(android_ms)
        
        self.assertAlmostEqual(result, expected_ios, places=1)
```

### Manual Testing Checklist

- [ ] ADB device detection works
- [ ] Legacy APK installation successful
- [ ] Android backup creates .ab file
- [ ] msgstore.db extracted correctly
- [ ] iOS backup located
- [ ] ChatStorage.sqlite extracted
- [ ] Migration completes without errors
- [ ] Message counts match
- [ ] Timestamps accurate (±1 second)
- [ ] Backups created successfully

---

## 📞 Support and Resources

### Documentation Priority

When user asks for help:

1. **Installation issues** → Point to [docs/SETUP.md](docs/SETUP.md)
2. **Migration errors** → Point to [docs/USAGE.md](docs/USAGE.md)
3. **Technical details** → Point to [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
4. **Code questions** → This file + source code

### External Resources

- [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) - ADB download
- [APKMirror WhatsApp](https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/) - Legacy APK source
- [iTunes Download](https://www.apple.com/itunes/) - iOS backup tool

---

## 📋 Checklist for New Features

Before adding new functionality:

- [ ] Read relevant documentation (SETUP, USAGE, ARCHITECTURE)
- [ ] Understand existing code patterns (this file)
- [ ] Follow coding standards (PEP 8, type hints, docstrings)
- [ ] Add error handling with rollback
- [ ] Create backups before destructive operations
- [ ] Add logging at appropriate levels
- [ ] Update documentation files
- [ ] Test with small database first
- [ ] Validate with real devices

---

**Version:** 1.0.0  
**Last Updated:** November 28, 2025  
**Project Status:** Production Ready
