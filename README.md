# WhatsApp Android → iOS Migration Tool

Migrate your WhatsApp chat history from Android to iOS devices with complete message preservation and timestamp accuracy.

---

## 🚀 Quick Start

```powershell
# 1. Setup dependencies (see docs/SETUP.md)
# - Install Python 3.8+
# - Download ADB binaries to bin/
# - Download legacy WhatsApp APK to apk/

# 2. Connect devices
# - Connect Android via USB (USB debugging enabled)
# - Create iOS backup via iTunes/Finder (unencrypted)

# 3. Run migration
python main.py

# 4. Follow interactive prompts
# 5. Restore modified iOS backup
```

**⚠️ Warning:** This tool modifies iOS backups and downgrades Android WhatsApp. **Use at your own risk.** Always create manual backups first.

---

## 📋 Features

### ✅ What Gets Migrated

- ✅ **Message text** (sent and received)
- ✅ **Timestamps** (accurate to the second)
- ✅ **Contact names and phone numbers**
- ✅ **Group chats** with participants
- ✅ **Message status** (delivered, read)
- ✅ **Quoted/reply messages** (best effort)
- ✅ **Chronological order** preserved

### ❌ What Doesn't Get Migrated

- ❌ Media files (photos, videos, voice messages, documents)
- ❌ Stickers and GIFs
- ❌ Group admin permissions
- ❌ Muted chat settings
- ❌ Wallpapers and chat colors
- ❌ Starred messages
- ❌ Archived chats status
- ❌ Status updates
- ❌ Call history

---

## 📖 Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| **[SETUP.md](docs/SETUP.md)** | Installation and dependencies | All users |
| **[USAGE.md](docs/USAGE.md)** | Step-by-step migration guide | All users |
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Technical deep-dive | Developers |

---

## 🛠️ Requirements

### System Requirements

- **Python:** 3.8 or higher (uses standard library only)
- **OS:** Windows 10/11 (primary), macOS 10.15+ (partial support), Linux (advanced)
- **Storage:** 5GB free space minimum
- **USB Ports:** 2 available (1 for Android, 1 for iOS)

### External Dependencies

**Must be downloaded separately (not included in repository):**

1. **ADB (Android Debug Bridge):**
   - Download: [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
   - Extract to: `bin/adb.exe`, `bin/AdbWinApi.dll`, `bin/AdbWinUsbApi.dll`
   - See: [bin/README.md](bin/README.md)

2. **Legacy WhatsApp APK:**
   - Version: 2.11.431 - 2.11.498 (required for unencrypted backups)
   - Download from: [APKMirror](https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/) (legal sources only)
   - Place in: `apk/WhatsApp_2.11.431.apk`
   - See: [apk/README.md](apk/README.md)
   - **⚠️ Legal Warning:** Only for personal data migration

3. **iTunes (Windows) or Finder (macOS):**
   - For iOS device backups
   - Download: [Apple iTunes](https://www.apple.com/itunes/)

### Device Requirements

**Android:**
- Android 4.0+ (Ice Cream Sandwich or newer)
- USB debugging enabled
- WhatsApp installed with data to migrate

**iOS:**
- iOS 9.0+ (iPhone, iPad, iPod Touch)
- WhatsApp installed (can be fresh install)
- Unencrypted backup created

---

## 🏗️ Project Structure

```
Whatsapp_AndroidToIphone/
├── src/                        # Python package (core code)
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Entry point and orchestration
│   ├── migrate.py             # Core migration engine
│   ├── android_backup.py      # Android backup operations
│   ├── ios_backup.py          # iOS backup operations
│   └── utils.py               # Common utilities
├── bin/                        # ADB binaries (download separately)
│   ├── adb.exe                # ⚠️ Not included - download required
│   ├── AdbWinApi.dll          # ⚠️ Not included - download required
│   └── AdbWinUsbApi.dll       # ⚠️ Not included - download required
├── apk/                        # Legacy WhatsApp APKs (download separately)
│   └── WhatsApp_2.11.431.apk  # ⚠️ Not included - download required
├── backups/                    # Automatic backups (created at runtime)
├── logs/                       # Migration logs (created at runtime)
├── tmp/                        # Temporary files (created at runtime)
├── docs/                       # Documentation
│   ├── SETUP.md               # Installation guide
│   ├── USAGE.md               # User manual
│   ├── ARCHITECTURE.md        # Technical documentation
│   └── research/              # Research notes
├── main.py                     # Legacy entry point
├── requirements.txt            # Python dependencies (stdlib only)
├── README.md                   # This file
└── .gitignore                  # Git exclusions
```

---

## 🔄 How It Works

### Migration Process (6 Steps)

```
1. Validate Dependencies
   ├─ Check Python, ADB, legacy APK
   ├─ Verify Android device connection
   └─ Locate iOS backup directory
   ↓
2. Backup Current Android WhatsApp
   ├─ Save current WhatsApp APK
   └─ Backup /sdcard/WhatsApp/ data
   ↓
3. Downgrade to Legacy WhatsApp
   ├─ Uninstall current WhatsApp (keep data)
   ├─ Install legacy APK (2.11.431)
   └─ User verifies phone number
   ↓
4. Create Android Backup
   ├─ Execute: adb backup com.whatsapp
   ├─ User confirms on Android screen
   └─ Extract msgstore.db from .ab file
   ↓
5. Extract and Migrate Database
   ├─ Read Android msgstore.db
   ├─ Convert Android schema → iOS schema
   ├─ Convert timestamps (Unix 1970 → Apple 2001 epoch)
   ├─ Migrate messages, contacts, groups
   └─ Validate data integrity
   ↓
6. Inject into iOS Backup
   ├─ Backup original iOS ChatStorage.sqlite
   ├─ Replace with migrated database
   ├─ Update iOS backup Manifest.db
   └─ Restore iOS backup via iTunes/Finder (manual)
```

### Technical Details

**Timestamp Conversion:**
- Android: Unix epoch (1970-01-01) in milliseconds
- iOS: Apple epoch (2001-01-01) in seconds
- Formula: `ios_timestamp = (android_ms / 1000) - 978307200`

**Database Schemas:**
- Android: SQLite (`msgstore.db`) with `messages`, `chat`, `jid` tables
- iOS: Core Data (`ChatStorage.sqlite`) with `ZWAMESSAGE`, `ZWACHATSESSION` entities

**Backup Formats:**
- Android: `.ab` file (custom format with ZLIB compressed TAR)
- iOS: Directory with hashed files and `Manifest.db` index

For full technical details, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📊 Usage Example

### Interactive Mode (Recommended)

```powershell
PS> python main.py

WhatsApp Android → iOS Migration Tool
======================================

[INFO] Step 1/6: Validating dependencies...
✅ Python 3.11.5 detected
✅ ADB found: bin\adb.exe (version 35.0.1)
✅ Legacy WhatsApp APK found: apk\WhatsApp_2.11.431.apk
✅ Android device connected: ABC123XYZ (model: SM-G991B)
✅ iOS backup directory: C:\Users\...\MobileSync\Backup\
✅ Found iOS backup: a1b2c3d4e5f6... (modified: 2025-11-27 14:30)

Press Enter to continue or Ctrl+C to cancel...

[INFO] Step 2/6: Backing up current WhatsApp...
[OK] APK backup saved: backups/WhatsApp_current_20251128_143022.apk
[OK] Data backup saved: backups/WhatsApp_data_20251128_143022.tar

[INFO] Step 3/6: Downgrading WhatsApp to legacy version...
⚠️  MANUAL STEP: Open WhatsApp on Android and verify phone number
Press Enter when ready...

[INFO] Step 4/6: Creating Android backup...
⚠️  MANUAL STEP: Confirm backup on Android screen (no password)
[OK] Android backup created: tmp/whatsapp.ab (125.4 MB)

[INFO] Step 5/6: Migrating database...
[OK] Messages migrated: 15,234
[OK] Contacts migrated: 127
[OK] Groups migrated: 23

[INFO] Step 6/6: Updating iOS backup...
✅ MIGRATION COMPLETED!

Summary:
- Messages migrated: 15,234
- Contacts migrated: 127
- Groups migrated: 23
- Backups created: 3

NEXT STEPS:
1. Open iTunes/Finder
2. Restore modified backup to iOS device
3. Open WhatsApp and verify phone number
```

### Command Line Options

```powershell
# Dry run (check dependencies only)
python main.py --check-dependencies

# Verbose logging
python main.py --verbose

# Custom iOS backup
python main.py --ios-backup "a1b2c3d4e5f6..."

# Non-interactive mode
python main.py --yes

# Help
python main.py --help
```

---

## ⚠️ Important Warnings

### Data Loss Risks

1. **Android:**
   - Downgrading WhatsApp may cause compatibility issues
   - Backup current version before proceeding

2. **iOS:**
   - Modified backup replaces ALL WhatsApp data
   - Original iOS messages will be LOST
   - Create manual iTunes/Finder backup first

3. **Media:**
   - Photos, videos, audio NOT migrated
   - Export manually to Google Photos/iCloud before migration

### Security Considerations

- **Unencrypted backups:** Sensitive data readable by anyone with file access
- **Legacy WhatsApp:** Version 2.11.x has known security vulnerabilities (upgrade immediately after migration)
- **Backup storage:** Keep backups encrypted (BitLocker, FileVault)
- **Cleanup:** Delete backups and temp files after successful migration

### Legal Considerations

- **APK download:** Only from legal sources (APKMirror, APKPure)
- **Personal use only:** Do not distribute APK files
- **WhatsApp ToS:** May violate Terms of Service (use at your own risk)

---

## 🐛 Troubleshooting

### Common Issues

**ADB device not found:**
```powershell
# Solution 1: Enable USB debugging
Settings → About Phone → Tap "Build Number" 7 times
Settings → Developer Options → Enable "USB Debugging"

# Solution 2: Restart ADB
.\bin\adb.exe kill-server
.\bin\adb.exe start-server
.\bin\adb.exe devices
```

**Android backup fails:**
```powershell
# Ensure screen is unlocked
# Confirm "Backup my data" prompt on Android
# Leave password field BLANK (critical!)
# Be patient - progress bar may appear stuck
```

**iOS backup not found:**
```powershell
# Windows: Install iTunes from Apple
# macOS: Update to 10.15+ (uses Finder)
# Create new UNENCRYPTED backup
```

**Migration completes but chats don't appear on iOS:**
```powershell
# Verify correct backup restored (check timestamp)
# Re-verify phone number on iOS WhatsApp
# Wait 5 minutes for chats to load
# Check WhatsApp → Settings → Storage (message count)
```

For more issues, see [USAGE.md - Common Issues](docs/USAGE.md#common-issues).

---

## 📚 Resources

### Documentation

- [Installation Guide](docs/SETUP.md) - Complete setup instructions
- [User Manual](docs/USAGE.md) - Step-by-step migration guide
- [Technical Docs](docs/ARCHITECTURE.md) - Architecture and implementation details

### External Resources

- [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) - ADB download
- [APKMirror WhatsApp](https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/) - Legacy APK source
- [iTunes Download](https://www.apple.com/itunes/) - iOS backup tool (Windows)

### Research

- [Project Investigation](docs/research/2025-11-28-investigacion-proyecto-migracion-whatsapp.md) - Initial research and analysis

---

## 🤝 Contributing

Contributions welcome! Please read [ARCHITECTURE.md - Contributing](docs/ARCHITECTURE.md#contributing) for:

- Development setup
- Code style guidelines
- Testing strategy
- Pull request process

---

## 📝 License

**Educational/Personal Use Only**

This tool is provided as-is for **personal data migration** only. The authors are not responsible for:
- Data loss or corruption
- Violations of WhatsApp Terms of Service
- Security vulnerabilities from legacy WhatsApp usage
- Legal issues from APK downloads

**Use at your own risk.**

---

## 🙏 Acknowledgments

- WhatsApp Inc. (database schemas reverse-engineered from publicly available information)
- Android Open Source Project (ADB tools)
- Apple Inc. (iOS backup format)
- Community contributions to WhatsApp migration research

---

## 📞 Support

For issues and questions:

1. **Check documentation:**
   - [SETUP.md](docs/SETUP.md) - Installation problems
   - [USAGE.md](docs/USAGE.md) - Migration errors
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical details

2. **Check logs:** `logs/migration_YYYYMMDD_HHMMSS.log`

3. **Search known issues** in [USAGE.md - Common Issues](docs/USAGE.md#common-issues)

4. **Open an issue** with:
   - Error message
   - Log file excerpt
   - Android/iOS device models
   - WhatsApp versions

---

**Version:** 1.0.0  
**Last Updated:** November 28, 2025  
**Status:** Production Ready
Migracion de android to iphone
