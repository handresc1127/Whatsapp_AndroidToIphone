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
Step 2: Direct Database Extraction (Android)
  ↓
Step 3: Validate Database
  ↓
Step 4: Extract and Migrate Database
  ↓
Step 5: Inject into iOS Backup
  ↓
Step 6: Restore iOS Backup
```

**Estimated Time:** 10-20 minutes  
**Requires User Interaction:** Yes (confirmations at each step)

**Note:** If direct extraction fails, a legacy backup method is available as fallback.

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
- Confirms legacy APK is present
- Locates iTunes backup directory
- Tests Android device connection
- Verifies iOS backup availability

**Expected Output:**
```
[INFO] Step 1/6: Validating dependencies...
✅ Python 3.11.5 detected
✅ ADB found: bin\adb.exe (version 35.0.1)
✅ Legacy WhatsApp APK found: apk\WhatsApp_2.11.431.apk
✅ Android device connected: ABC123XYZ (model: SM-G991B)
✅ iOS backup directory: C:\Users\...\MobileSync\Backup\
✅ Found iOS backup: a1b2c3d4e5f6... (modified: 2025-11-27 14:30)
```

**If Errors Occur:**
- Missing ADB: See [SETUP.md - ADB Installation](SETUP.md#adb-installation)
- Device not detected: Enable USB debugging, try different cable
- No iOS backup: Create backup via iTunes/Finder
- Missing APK: Download legacy WhatsApp (see [SETUP.md](SETUP.md#legacy-whatsapp-apk))

**User Action:** Review output, confirm to proceed

---

### Step 2: Backup Current Android WhatsApp

**What happens:**
- Creates backup of current WhatsApp APK
- Creates backup of `/sdcard/WhatsApp/` folder
- Stores backups in `backups/` folder with timestamp

**Expected Output:**
```
[INFO] Step 2/6: Backing up current WhatsApp...
[INFO] Creating backup of WhatsApp APK...
[OK] APK backup saved: backups/WhatsApp_current_20251128_143022.apk
[INFO] Creating backup of WhatsApp data folder...
[OK] Data backup saved: backups/WhatsApp_data_20251128_143022.tar
[OK] Backup completed successfully
```

**Backup Locations:**
- APK: `backups/WhatsApp_current_YYYYMMDD_HHMMSS.apk`
- Data: `backups/WhatsApp_data_YYYYMMDD_HHMMSS.tar`

**User Action:** Confirm backup success before proceeding

**⚠️ IMPORTANT:** Keep these backups until you've verified iOS migration success. You'll need them to restore Android if something goes wrong.

---

### Step 3: Downgrade to Legacy WhatsApp

**What happens:**
- Uninstalls current WhatsApp (with `-k` flag to keep data)
- Installs legacy WhatsApp APK (version 2.11.431-2.11.498)
- Prompts you to open WhatsApp and verify phone number

**Expected Output:**
```
[INFO] Step 3/6: Downgrading WhatsApp to legacy version...
[INFO] Uninstalling current WhatsApp (keeping data)...
[OK] Current WhatsApp uninstalled
[INFO] Installing legacy WhatsApp: apk\WhatsApp_2.11.431.apk
[OK] Legacy WhatsApp installed successfully

⚠️  MANUAL STEP REQUIRED:
1. Unlock your Android device
2. Open WhatsApp (green icon)
3. Verify your phone number
4. Skip backup restoration (if prompted)
5. Wait for chats to load completely

Press Enter when WhatsApp is ready...
```

**User Actions:**

1. **Unlock Android device**
2. **Open WhatsApp** from app drawer
3. **Verify phone number** (will receive SMS/call)
4. **IMPORTANT:** If asked to restore from Google Drive → **SKIP** or **Cancel**
5. Wait for chats to appear (may take 1-2 minutes)
6. Return to computer and **press Enter**

**Troubleshooting:**
- **"App not installed" error:** Uninstall manually first: Settings → Apps → WhatsApp → Uninstall
- **Phone verification fails:** Check SIM card, mobile data/WiFi, try SMS instead of call
- **Chats don't load:** Wait 5 minutes, restart WhatsApp, check `/sdcard/WhatsApp/` exists

---

### Step 4: Create Android Backup (.ab file)

**What happens:**
- Uses ADB to create backup of WhatsApp data
- Creates `.ab` (Android Backup) file
- **IMPORTANT:** Requires manual confirmation on Android device

**Expected Output:**
```
[INFO] Step 4/6: Creating Android backup...
[INFO] Executing: adb backup -f tmp/whatsapp.ab -noapk com.whatsapp

⚠️  LOOK AT YOUR ANDROID DEVICE NOW!
A prompt will appear asking to confirm backup.

1. Unlock your Android device
2. You should see "Backup my data" screen
3. DO NOT set a password (leave blank)
4. Tap "BACK UP MY DATA" button
5. Wait for confirmation...

This may take 2-5 minutes depending on chat history size.
```

**User Actions:**

1. **Unlock Android device immediately**
2. **Look for "Backup my data" prompt** (appears within 10 seconds)
3. **Password field:** Leave **EMPTY** (critical!)
4. **Tap "BACK UP MY DATA"** button
5. **Wait patiently** (progress bar may not move smoothly)

**Expected Wait Time:**
- Small chats (<1000 messages): 1-2 minutes
- Medium chats (1000-10000 messages): 2-5 minutes
- Large chats (>10000 messages): 5-15 minutes

**Troubleshooting:**
- **Prompt doesn't appear:** Check Android screen is unlocked, try `adb backup` command again
- **"Backup failed":** Ensure legacy WhatsApp is running, phone is unlocked
- **"Password required":** You set a password - must restart and leave blank
- **Stuck at 0%:** Be patient, progress bar often jumps to 100% near end

**When Complete:**
```
[OK] Android backup created: tmp/whatsapp.ab (125.4 MB)
[INFO] Extracting backup archive...
[OK] Backup extracted to: tmp/apps/com.whatsapp/
```

---

### Step 5: Extract and Migrate Database

**What happens:**
- Extracts msgstore.db from Android backup
- Validates database integrity
- Converts Android schema to iOS schema
- Migrates messages, contacts, groups
- Converts timestamps (Unix 1970 → Apple 2001 epoch)

**Expected Output:**
```
[INFO] Step 5/6: Migrating database...
[INFO] Extracting msgstore.db from backup...
[OK] Android database: tmp/apps/com.whatsapp/db/msgstore.db

[INFO] Locating iOS ChatStorage.sqlite...
[OK] iOS database: C:\Users\...\MobileSync\Backup\a1b2c3d4e5f6...\7c7fba66680ef796b916b067077cc246adacf01d

[INFO] Starting migration...
[INFO] Analyzing Android database schema...
[OK] Found 4 tables: messages, contacts, groups, media
[OK] Total messages: 15,234
[OK] Total contacts: 127
[OK] Total groups: 23

[INFO] Creating iOS database schema...
[OK] Core Data model created

[INFO] Migrating messages...
Progress: [████████████████████████████████] 100% (15234/15234)
[OK] Messages migrated: 15,234

[INFO] Migrating contacts...
[OK] Contacts migrated: 127

[INFO] Migrating groups...
[OK] Groups migrated: 23

[INFO] Converting timestamps...
[OK] Timestamps converted (Unix epoch → Apple epoch)

[INFO] Finalizing migration...
[OK] Database integrity check passed
[OK] Migration completed successfully
```

**What Gets Migrated:**

✅ **Included:**
- Message text (sent/received)
- Timestamps (accurate to the second)
- Contact names and phone numbers
- Group names and participants
- Message read status
- Message delivery status
- Quoted/reply messages (best effort)

❌ **Not Included:**
- Media files (photos, videos, voice messages, documents)
- Stickers and GIFs
- Group admin permissions
- Muted chats settings
- Wallpapers and chat colors
- Archived chats status

**User Action:** Monitor progress, confirm completion

**Troubleshooting:**
- **"msgstore.db not found":** Android backup incomplete, restart from Step 4
- **"Database corrupted":** Try creating new Android backup
- **"Schema mismatch":** iOS WhatsApp version too new, update script or use older iOS backup

---

### Step 6: Inject into iOS Backup

**What happens:**
- Backs up original iOS ChatStorage.sqlite
- Replaces iOS database with migrated database
- Updates iOS backup Manifest.db with new file hash
- Validates backup integrity

**Expected Output:**
```
[INFO] Step 6/6: Updating iOS backup...

⚠️  CRITICAL: This will MODIFY your iOS backup
Original ChatStorage.sqlite will be backed up to:
backups/ChatStorage_original_20251128_143530.sqlite

Do you want to proceed? (yes/no): yes

[INFO] Backing up original iOS database...
[OK] Backup saved: backups/ChatStorage_original_20251128_143530.sqlite

[INFO] Replacing iOS database...
[OK] Migrated database copied to iOS backup

[INFO] Updating Manifest.db...
[OK] File hash updated in Manifest
[OK] Backup modified successfully

✅ MIGRATION COMPLETED!

Summary:
- Messages migrated: 15,234
- Contacts migrated: 127
- Groups migrated: 23
- Backups created: 3
- iOS backup ready for restore

NEXT STEPS:
1. Disconnect Android device
2. Connect iOS device to iTunes/Finder
3. Select "Restore Backup"
4. Choose the modified backup (timestamp: 2025-11-27 14:30)
5. Wait for restore to complete (10-30 minutes)
6. Open WhatsApp on iOS
7. Verify your phone number
8. Check that chats have been restored

⚠️  DO NOT create new iOS backup until you've verified migration!
```

**User Action:**
1. **Read summary carefully**
2. **Verify message counts** match expectations
3. **Note backup locations** for potential rollback
4. **Confirm understanding** of next steps

---

### Step 7: Restore iOS Backup (Manual)

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

### Why Downgrade WhatsApp?

Modern WhatsApp versions (2.12.x+) use **encrypted backups** by default. The encryption key is stored in Google Drive and cannot be extracted.

Legacy versions (2.11.431-2.11.498) create **unencrypted local backups** that can be read and modified.

**Timeline:**
- **2.11.431 (2014):** Last version with easy unencrypted backups
- **2.12.x (2015):** Introduced encrypted backups
- **Current:** Encryption mandatory, no workaround

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

### Android Backup Fails

**Symptom:** `adb backup` command hangs or returns empty file

**Causes:**
1. Screen locked during backup
2. Password set for backup (must be blank)
3. WhatsApp not running
4. USB debugging disabled mid-process

**Solutions:**
1. Unlock screen and keep awake
2. Restart from Step 4, leave password blank
3. Open WhatsApp, wait for chats to load
4. Re-enable USB debugging: Settings → Developer Options

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

**Q: Can I migrate between different phone numbers?**  
A: No, phone number must remain the same. Changing numbers requires WhatsApp's official "Change Number" feature separately.

---

**Last Updated:** November 28, 2025  
**Version:** 1.0.0
