# WhatsApp Migration Tool - Usage Guide

Step-by-step instructions for migrating WhatsApp data from Android to iOS.

---

## Table of Contents

1. [Before You Begin](#before-you-begin)
2. [Migration Process Overview](#migration-process-overview)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Command Line Options](#command-line-options)
5. [Understanding the Process](#understanding-the-process)
6. [Common Issues](#common-issues)
7. [Data Validation](#data-validation)
8. [Rollback and Recovery](#rollback-and-recovery)

---

## Before You Begin

### ⚠️ Critical Warnings

1. **BACKUP EVERYTHING:**
   - Create manual Android WhatsApp backup (Settings → Chats → Chat backup)
   - Create full iOS device backup via iTunes/Finder
   - This tool creates automatic backups, but manual backups are extra insurance

2. **RISKS:**
   - iOS backup modification is irreversible once restored
   - Data loss is possible if process is interrupted
   - **USE AT YOUR OWN RISK**

3. **REQUIREMENTS:**
   - Android device must be unlocked and screen ON during extraction
   - WhatsApp must have storage permissions enabled
   - iOS device must be disconnected during backup modification
   - Stable USB connections (no hubs/extenders recommended)
   - At least 15-30 minutes uninterrupted time

4. **NOT SUPPORTED:**
   - Media files (photos, videos, audio) - only message text and metadata
   - Stickers and custom emojis
   - Group permissions and admin roles
   - Call history
   - Status updates

### Prerequisites Checklist

Before starting migration, verify:

- [ ] Setup completed ([SETUP.md](SETUP.md))
- [ ] Python 3.8+ installed
- [ ] ADB binaries in `bin/` folder
- [ ] Android device connected and authorized (`adb devices` shows device)
- [ ] WhatsApp has storage permissions enabled on Android
- [ ] iOS device has recent unencrypted backup
- [ ] At least 5GB free disk space
- [ ] Manual backups created for both devices
- [ ] Read and understood warnings above

---

## Migration Process Overview

The migration involves **5 main steps**:

```
Step 1: Validate Dependencies
  ↓
Step 2: Select WhatsApp Type
  ↓
Step 3: Direct Database Extraction (Android)
  ↓
Step 4: Migrate Database (Android → iOS)
  ↓
Step 5: Update iOS Backup
```

**Estimated Time:** 10-20 minutes  
**Requires User Interaction:** Yes (confirmations at each step)

**Note:** If direct extraction fails, a legacy backup method is available as fallback (requires legacy APK download).

---

## Step-by-Step Migration

### Starting the Migration

**Open PowerShell/Terminal in project directory:**

```powershell
cd d:\path\to\Whatsapp_AndroidToIphone
python main.py
```

The script will guide you through each step with prompts.

---

### Step 1: Dependency Validation

**What happens:**
- Checks Python version (≥3.8)
- Verifies ADB executable exists
- Tests Android device connection
- Locates iTunes backup directory
- Verifies iOS backup availability
- *(Optional)* Checks if legacy APK is present (only for fallback)

**Expected Output:**
```
[INFO] Step 1/5: Validating dependencies...
✅ Python 3.11.5 detected
✅ ADB found: bin\adb.exe (version 35.0.1)
✅ Android device connected: ABC123XYZ (model: SM-G991B)
✅ iOS backup directory: C:\Users\...\MobileSync\Backup\
✅ Found iOS backup: a1b2c3d4e5f6... (modified: 2025-11-27 14:30)

[INFO] Legacy APK directory not found (optional)
       Only direct extraction method will be available
       This is fine for most users
```

**If Errors Occur:**
- Missing ADB: See [SETUP.md - ADB Installation](SETUP.md#adb-installation)
- Device not detected: Enable USB debugging, try different cable
- No iOS backup: Create backup via iTunes/Finder

**User Action:** Review output, confirm to proceed

---

### Step 2: Select WhatsApp Type

**What happens:**
- Script asks which WhatsApp to migrate
- Options: Standard or Business

**Expected Output:**
```
[INFO] Step 2/5: Select WhatsApp Type

Which WhatsApp do you want to migrate?
  1. WhatsApp (Standard)
  2. WhatsApp Business

Select option (1 or 2): 1
```

**User Action:** Enter `1` for Standard or `2` for Business

---

### Step 3: Direct Database Extraction

**What happens:**
- Extracts msgstore.db directly from `/sdcard/Android/media/com.whatsapp/`
- No downgrade needed
- No backup file creation
- Works with current WhatsApp version

**Expected Output:**
```
[INFO] Step 3/5: Android Database Extraction

This will extract WhatsApp database directly from your device.

METHOD:
  - Direct extraction from /sdcard/ (no backup needed)
  - Works with current WhatsApp version (no downgrade)
  - Requires storage permissions granted to WhatsApp
  - Fast extraction (usually < 1 minute)

REQUIREMENTS:
  - WhatsApp installed with active chats
  - Storage permissions enabled for WhatsApp
  - USB debugging enabled

Do you want to continue? (yes/no): yes

[INFO] Attempting direct database extraction...
[INFO] Trying: /sdcard/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db
[OK] Database extracted successfully (125.4 MB)

[OK] Database validated successfully
     Schema: modern
     Messages: 15,234
     Size: 125.40 MB

You can now safely disconnect your Android device.
```

**User Actions:**
1. Ensure WhatsApp has **storage permissions** enabled:
   - Settings → Apps → WhatsApp → Permissions → Storage → Allow
2. Confirm to proceed
3. Wait for extraction (usually 10-30 seconds)

**Troubleshooting:**
- **"Could not access database file":**
  - Grant storage permissions to WhatsApp
  - Open WhatsApp to ensure it has created database
  - Try alternative: Settings → Storage → Manage Space → "Export database"

- **"Database validation failed":**
  - Database may be encrypted (rare on modern Android)
  - Try legacy backup method (will prompt automatically)

**If Direct Extraction Fails:**

The script will show detailed error messages with manual solutions:

```
[WARNING] Direct extraction failed.

This can happen if:
  - WhatsApp doesn't have storage permissions
  - Database file is in non-standard location
  - WhatsApp is not installed or has no data
  - Custom ROM with different file structure

Recommended solutions:
  1. Grant storage permissions: Settings → Apps → WhatsApp → Permissions → Storage
  2. Copy database manually via USB to out/android.db
  3. Use Android file manager to locate and export msgstore.db
  4. Try WhatsApp cloud backup and download from Google Drive

Note: This tool no longer supports legacy APK downgrade method.
      If direct extraction doesn't work, manual file transfer is required.
```

**Manual Database Transfer Steps:**

1. **On Android Device:**
   - Install a file manager app (e.g., Files by Google, Solid Explorer)
   - Enable "Show hidden files" in file manager settings
   - Navigate to one of these locations:
     - `/sdcard/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db`
     - `/sdcard/WhatsApp/Databases/msgstore.db`
   - Copy `msgstore.db` to `/sdcard/Download/`

2. **Transfer to Computer:**
   - Connect Android via USB
   - Open device in File Explorer (Windows) or Finder (macOS)
   - Navigate to `Internal Storage → Download`
   - Copy `msgstore.db` to your computer

3. **Place in Migration Tool:**
   - In project folder, create `out/` directory if it doesn't exist
   - Rename file to `android.db` and place in `out/` folder
   - Resume migration from Step 4

---

### Step 4: Migrate Database

**What happens:**
- Extracts iOS ChatStorage.sqlite from backup
- Detects Android database schema (modern vs legacy)
- Converts Android schema to iOS schema
- Migrates messages, contacts, groups
- Converts timestamps (Unix 1970 → Apple 2001 epoch)

**Expected Output:**
```
[INFO] Step 4/5: Data Migration

Please enter your phone number with country code
Example: 573001234567 (for Colombia)
Phone number: 573001234567

[INFO] Starting database migration...
[INFO] This may take several minutes depending on chat history size...

[INFO] Database schema: modern
[INFO] Analyzing database schemas...
[OK] Android DB: 15,234 messages
[OK] iOS DB: 0 messages (fresh)

[INFO] Starting migration with modern schema...
Progress: 15234/15234 messages migrated

================================================================================
MIGRATION STATISTICS
================================================================================
Android messages:      15,234
iOS messages (before): 0
Messages migrated:     15,234
Contacts migrated:     0
Groups migrated:       0
iOS messages (after):  15,234
================================================================================
```

**What Gets Migrated:**

✅ **Included:**
- Message text (sent/received)
- Timestamps (accurate to the second)
- Contact identifiers (JIDs)
- Message status (delivered, read)
- From/To information

❌ **Not Included:**
- Media files (photos, videos, voice messages, documents)
- Stickers and GIFs
- Group admin permissions
- Contact names (synced from iOS contacts separately)
- Muted chats settings
- Wallpapers and chat colors
- Archived chats status

**User Action:** 
1. Enter phone number with country code
2. Wait for migration (1-5 minutes depending on message count)
3. Review statistics

**Troubleshooting:**
- **"Schema not implemented":** Database too old, try legacy method
- **"Migration failed":** Check logs in `logs/` folder
- **Message count mismatch:** Some system messages may be filtered

---

### Step 5: Update iOS Backup

**What happens:**
- Backs up original iOS ChatStorage.sqlite
- Replaces iOS database with migrated database
- Updates iOS backup Manifest.db with new file hash
- Validates backup integrity

**Expected Output:**
```
[INFO] Step 5/5: Update iTunes Backup

This step will modify your iTunes backup with the migrated data.
A safety backup will be created before overwriting.

Do you want to update the iTunes backup? (yes/no): yes

[INFO] Backing up original iOS database...
[OK] Backup saved: backups/ChatStorage_original_20251129_143530.sqlite

[INFO] Updating iOS backup...
[OK] Database replaced successfully
[OK] Manifest.db updated
[OK] Backup integrity verified

================================================================================
MIGRATION COMPLETE!
================================================================================

Final Steps:
  1. Connect your iPhone to iTunes/Finder
  2. Restore from the updated backup
  3. Open WhatsApp on your iPhone
  4. Verify that all chats from Android are present

NOTE: If you experience issues:
  - Backup WhatsApp to iCloud
  - Reinstall WhatsApp
  - Restore from iCloud
================================================================================
```

**User Action:**
1. Confirm backup update
2. Review completion message
3. Proceed to manual iOS restore

---

### Step 6: Restore iOS Backup (Manual)

**This step is MANUAL - done via iTunes/Finder:**

#### Windows (iTunes):

1. **Disconnect Android device**
2. **Connect iOS device** via USB
3. **Open iTunes**
4. **Click device icon** (top left)
5. **Summary tab** → **Backups section**
6. **Click "Restore Backup..."**
7. **Select the modified backup** (check timestamp - should be recent)
8. **Click "Restore"**
9. **Wait for completion** (10-30 minutes depending on backup size)
10. **Device will restart** automatically

#### macOS (Finder):

1. **Disconnect Android device**
2. **Connect iOS device** via USB
3. **Open Finder**
4. **Select device** in sidebar
5. **General tab** → **Backups section**
6. **Click "Restore Backup..."**
7. **Select the modified backup** (check date - should match migration date)
8. **Click "Restore"**
9. **Wait for completion**
10. **Device will restart**

**During Restore:**
- Progress bar may appear stuck - be patient
- Device screen will show Apple logo and progress bar
- Do not disconnect device or close iTunes/Finder
- Device will restart multiple times

**After Restore:**

1. **Unlock iOS device**
2. **Complete setup wizard** (if any)
3. **Open WhatsApp**
4. **Verify phone number** (SMS/call)
5. **Wait for chats to load** (1-5 minutes)

**Expected Result:**
- All messages appear in chronological order
- Contacts show correct names
- Groups show correct participants
- Timestamps are accurate
- **Media files will NOT be present** (photos/videos show placeholder)

---

## Command Line Options

### Basic Usage

```powershell
# Interactive mode (recommended)
python main.py

# With specific iOS backup
python main.py --ios-backup "a1b2c3d4e5f6..."

# Dry run (check dependencies only)
python main.py --check-dependencies

# Enable verbose logging
python main.py --verbose

# Skip backups (NOT RECOMMENDED)
python main.py --no-backup
```

### Advanced Options

```powershell
# Custom ADB path
python main.py --adb-path "C:\platform-tools\adb.exe"

# Custom legacy APK
python main.py --legacy-apk "apk\WhatsApp_2.11.498.apk"

# Custom output directory
python main.py --output-dir "D:\WhatsApp_Migration\"

# Force overwrite existing files
python main.py --force

# Non-interactive mode (use defaults)
python main.py --yes
```

### Help

```powershell
python main.py --help
```

---

## Understanding the Process

### Direct Extraction Method

**How It Works:**

Modern Android (8.0+) with Scoped Storage allows direct file access to WhatsApp databases:

1. **Database Location:**
   - Primary: `/sdcard/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db`
   - Fallback: `/sdcard/WhatsApp/Databases/msgstore.db`

2. **Permissions Required:**
   - WhatsApp must have "Storage" permission enabled
   - ADB file access (provided by USB debugging)

3. **Advantages:**
   - ⚡ 20x faster than legacy method (seconds vs minutes)
   - ✅ Works with current WhatsApp version (no downgrade)
   - ✅ Compatible with Android 11+ (where `adb backup` is deprecated)
   - ✅ No phone number re-verification needed

**When Direct Extraction Fails:**

Legacy backup method is available as fallback:
- Requires legacy APK (2.11.431-2.11.498)
- Downgrades WhatsApp temporarily
- Uses `adb backup` to create encrypted backup
- Takes 15-30 minutes additional time
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details

### Timestamp Conversion

Android and iOS use different epoch timestamps:

| Platform | Epoch Start | Units | Example |
|----------|-------------|-------|---------|
| Android  | 1970-01-01  | Milliseconds | `1700000000000` |
| iOS      | 2001-01-01  | Seconds | `721170000` |

**Conversion Formula:**
```python
# Android → iOS
ios_timestamp = (android_timestamp_ms / 1000) - 978307200

# iOS → Android
android_timestamp_ms = (ios_timestamp + 978307200) * 1000
```

**Offset Constant:** `978307200` seconds between epochs

### Database Schema Mapping

| Android Table | iOS Entity | Notes |
|---------------|------------|-------|
| `messages` | `ZWAMESSAGE` | Message text, timestamps, status |
| `chat` | `ZWACHATSESSION` | Chat metadata |
| `jid` | `ZWACHATSESSION.ZCONTACTJID` | Contact identifiers |
| `group_participants` | `ZWAGROUPMEMBER` | Group membership |
| `media_refs` | `ZWAMEDIAITEM` | Media metadata (files not copied) |

**Core Data Complexity:**
iOS uses Core Data framework with complex relationships. The migration script creates simplified schema compatible with WhatsApp's expected structure.

### What Happens to Media?

**Media files are NOT migrated** because:

1. **Storage Location:** Android stores media in `/sdcard/WhatsApp/Media/`, iOS in complex app container
2. **File Format:** Different naming conventions and encryption
3. **Database References:** Complex Core Data relationships for media items
4. **Backup Size:** Would make backups massive (gigabytes)

**Result:**
- Messages show placeholders: "📷 Photo", "🎥 Video", "🎤 Voice message"
- Clicking placeholder shows "Media not available"
- To preserve media: manually export important photos/videos before migration

---

## Common Issues

### Direct Extraction Fails

**Symptom:** `Could not access database file` or extraction returns empty/corrupted file

**Causes:**
1. Storage permissions not granted to WhatsApp
2. Database in non-standard location
3. WhatsApp not installed or never opened
4. Custom ROM with different file structure

**Solutions:**
1. **Grant Storage Permissions:**
   - Settings → Apps → WhatsApp → Permissions → Storage → Allow
   - Open WhatsApp to ensure database is created

2. **Try Alternative Paths:**
   - Script automatically tries multiple common locations
   - Check manually: Use file manager app to locate `msgstore.db`

3. **Use Legacy Method:**
   - Download legacy APK to `apk/` folder
   - Retry migration - script will offer legacy method
   - Requires phone number re-verification

4. **Manual Export:**
   - WhatsApp → Settings → Chats → Chat backup → Export
   - Copy msgstore.db manually via USB
   - Place in `out/android.db`
   - Resume migration from Step 4

### iOS Backup Not Found

**Symptom:** Script reports "No iOS backups found"

**Causes:**
1. Backup directory doesn't exist (iTunes not installed)
2. Backups encrypted (script can't modify)
3. No recent backups

**Solutions:**
1. Install iTunes (Windows) or update macOS
2. Create new **unencrypted** backup:
   - iTunes: Uncheck "Encrypt local backup"
   - Finder: Uncheck "Encrypt local backup"
3. Create backup: iTunes/Finder → Back Up Now

### Migration Completes But Chats Don't Appear on iOS

**Symptom:** WhatsApp opens on iOS but shows no chats or "Restoring..." indefinitely

**Causes:**
1. Wrong iOS backup restored
2. Phone number verification failed
3. iOS WhatsApp version incompatible
4. Database corruption during migration

**Solutions:**
1. Verify restored backup timestamp matches migration date
2. Re-verify phone number (Settings → Account → Delete Account → re-verify)
3. Update iOS WhatsApp to latest version
4. Restore original iOS backup and retry migration

### Partial Message Migration

**Symptom:** Only some messages appear, or recent chats missing

**Causes:**
1. Android backup incomplete
2. Media-only messages filtered out
3. Database schema mismatch

**Solutions:**
1. Create fresh Android backup (ensure all chats loaded)
2. Media messages show as placeholders (expected behavior)
3. Check Android WhatsApp version (must be 2.11.431-2.11.498)

### Timestamps Incorrect

**Symptom:** Messages show wrong dates/times (e.g., year 2001 or 1970)

**Causes:**
1. Timestamp conversion error
2. Timezone not preserved
3. Database corruption

**Solutions:**
1. Check migration logs: `logs/migration.log`
2. Verify timestamps in Android database: `SELECT timestamp FROM messages LIMIT 10;`
3. Manual fix: Edit `src/migrate.py` timestamp conversion logic

---

## Data Validation

After iOS restore, validate migration success:

### Message Count Validation

**Android (before migration):**
```powershell
# Count total messages in Android backup
python -c "import sqlite3; conn = sqlite3.connect('tmp/apps/com.whatsapp/db/msgstore.db'); print(conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0])"
```

**iOS (after migration):**
- Open WhatsApp on iOS
- Settings → Storage and Data → Manage Storage
- Check total messages count

**Expected:** Counts should match (±5% due to system messages)

### Sample Chat Validation

**Manually verify:**

1. **Open a personal chat**
   - Check oldest message date
   - Check most recent message date
   - Verify message text accuracy
   - Check sender/receiver correct

2. **Open a group chat**
   - Verify all participants present
   - Check group name correct
   - Verify admin status (may be lost)
   - Check message chronology

3. **Check contact names**
   - Verify contact names display correctly
   - Check phone numbers match
   - Profile photos will NOT migrate (expected)

### Expected Differences

| Feature | Android | iOS | Notes |
|---------|---------|-----|-------|
| Message text | ✅ | ✅ | Identical |
| Timestamps | ✅ | ✅ | Converted but accurate |
| Media files | ✅ | ❌ | Only placeholders on iOS |
| Contact names | ✅ | ✅ | May need re-sync from contacts |
| Group names | ✅ | ✅ | Identical |
| Group admins | ✅ | ⚠️ | May be lost |
| Starred messages | ✅ | ❌ | Not migrated |
| Archived chats | ✅ | ❌ | Not migrated |

---

## Rollback and Recovery

### If Migration Fails

**Option 1: Restore Original iOS Backup**

1. Open iTunes/Finder
2. Restore Backup → Select backup from BEFORE migration
3. Wait for restore
4. WhatsApp will return to pre-migration state

**Original backup location:**
- Windows: `%APPDATA%\Apple Computer\MobileSync\Backup\`
- macOS: `~/Library/Application Support/MobileSync/Backup/`

**Option 2: Use Automated Backup**

Script creates backup: `backups/ChatStorage_original_YYYYMMDD_HHMMSS.sqlite`

**Manual restore:**
1. Locate iOS backup folder (UUID format)
2. Find file: `7c7fba66680ef796b916b067077cc246adacf01d`
3. Replace with backup: `Copy-Item backups\ChatStorage_original_*.sqlite` to iOS backup folder
4. Restore backup via iTunes/Finder

### If Android WhatsApp Broken

**Option 1: Reinstall from Backup**

```powershell
# Uninstall legacy WhatsApp
.\bin\adb.exe uninstall com.whatsapp

# Reinstall from backup
.\bin\adb.exe install backups\WhatsApp_current_YYYYMMDD_HHMMSS.apk

# Restore data
.\bin\adb.exe push backups\WhatsApp_data_YYYYMMDD_HHMMSS.tar /sdcard/
# (Extract .tar on device using file manager or ADB shell)
```

**Option 2: Reinstall from Play Store**

1. Uninstall WhatsApp from Android
2. Reinstall from Google Play Store
3. Verify phone number
4. Restore from Google Drive backup (if available)

---

## Support and Troubleshooting

### Logs Location

All operations are logged to:
- **File:** `logs/migration_YYYYMMDD_HHMMSS.log`
- **Console:** Real-time progress

**Log Levels:**
- `[INFO]` - Normal operations
- `[WARN]` - Warnings (non-critical)
- `[ERROR]` - Errors (may cause failure)
- `[DEBUG]` - Verbose details (use `--verbose` flag)

### Interpreting Logs

**Example log snippet:**
```
2025-11-28 14:32:15 [INFO] Starting migration...
2025-11-28 14:32:16 [INFO] Android database: 15234 messages, 127 contacts, 23 groups
2025-11-28 14:32:17 [INFO] Migrating messages... [0%]
...
2025-11-28 14:35:42 [INFO] Migrating messages... [100%]
2025-11-28 14:35:43 [OK] Messages migrated successfully
```

**Check for errors:**
```powershell
# Windows
Select-String -Path "logs\migration_*.log" -Pattern "ERROR"

# macOS/Linux
grep "ERROR" logs/migration_*.log
```

### Getting Help

If you encounter issues:

1. **Check logs:** `logs/migration_*.log`
2. **Review this guide:** [USAGE.md](USAGE.md)
3. **Check setup:** [SETUP.md](SETUP.md)
4. **Review architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) (technical details)
5. **Search known issues** in this document

### Known Limitations

1. **Media files not migrated** (photos, videos, audio, documents)
2. **Stickers not migrated** (only text messages)
3. **Group admin status may be lost**
4. **Archived chats not preserved**
5. **Muted chats settings lost**
6. **Starred messages not migrated**
7. **Wallpapers and chat colors reset**
8. **Status updates not migrated**
9. **Call history not migrated**
10. **Broadcast lists not migrated**

---

## Best Practices

### Before Migration

1. ✅ Create manual backups (Android → Google Drive, iOS → iTunes/Finder)
2. ✅ Export important media manually (Google Photos, iCloud, local storage)
3. ✅ Note group admins (will need to re-assign on iOS)
4. ✅ Screenshot starred messages (cannot be migrated)
5. ✅ Inform contacts of number change (if applicable)

### During Migration

1. ✅ Keep devices connected and unlocked
2. ✅ Don't use devices during process
3. ✅ Monitor console output for errors
4. ✅ Confirm each step before proceeding
5. ✅ Have at least 1 hour uninterrupted time

### After Migration

1. ✅ Validate message counts
2. ✅ Check sample chats for accuracy
3. ✅ Re-sync contacts (Settings → Contacts → Refresh)
4. ✅ Re-join groups if admin status lost
5. ✅ Keep backups for at least 1 month
6. ✅ Inform contacts you're on iOS now (optional)

---

## FAQ

**Q: Will my contacts see that I switched to iOS?**  
A: No, your phone number remains the same. Contacts won't notice unless you tell them.

**Q: Can I migrate only specific chats?**  
A: No, the script migrates all chats. Manual selective migration would require custom script modifications.

**Q: Can I migrate from iOS to Android?**  
A: Not with this tool. The process is designed for Android → iOS only.

**Q: Will my media files (photos/videos) be migrated?**  
A: No, only message text and metadata. Export media manually before migration.

**Q: Can I use this tool multiple times?**  
A: Yes, but each run overwrites the previous migration. Not suitable for merging chat histories.

**Q: What if I have messages in both Android and iOS WhatsApp?**  
A: The migration REPLACES iOS data with Android data. Messages on iOS will be LOST. Backup iOS first if needed.

**Q: Is this tool safe?**  
A: The tool creates backups before destructive operations, but **use at your own risk**. Always create manual backups.

---

**Last Updated:** November 29, 2025  
**Version:** 1.1.0
