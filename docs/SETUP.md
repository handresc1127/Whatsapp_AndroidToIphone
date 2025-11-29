# WhatsApp Migration Tool - Setup Guide

Complete installation and setup instructions for migrating WhatsApp data from Android to iOS.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Setup](#python-setup)
3. [ADB Installation](#adb-installation)
4. [Legacy WhatsApp APK](#legacy-whatsapp-apk)
5. [iTunes/Finder Setup](#itunesfinder-setup)
6. [Project Setup](#project-setup)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Operating System
- **Windows 10/11** (recommended)
- **macOS 10.15+** (partial support - ADB manual setup required)
- **Linux** (advanced users - ADB via apt/yum)

### Hardware
- **USB Ports**: 2 available ports (1 for Android, 1 for iOS)
- **Storage**: At least 5GB free space for backups and temp files
- **RAM**: 4GB minimum, 8GB recommended

### Devices
- **Android Device**:
  - Android 4.0+ (Ice Cream Sandwich or newer)
  - WhatsApp installed with data to migrate
  - USB debugging enabled (Developer Options)
  - Screen unlocked during process
  
- **iOS Device**:
  - iOS 9.0+ (iPhone, iPad, iPod Touch)
  - WhatsApp installed (can be fresh install)
  - Trusted computer for iTunes backup
  - Find My iPhone disabled (optional, for safety)

---

## Python Setup

### 1. Check Python Version

This tool requires **Python 3.8 or higher**.

**Windows:**
```powershell
python --version
# Should output: Python 3.8.x or higher
```

**macOS/Linux:**
```bash
python3 --version
```

### 2. Install Python (if needed)

If Python is not installed or version is too old:

**Windows:**
1. Download from: https://www.python.org/downloads/
2. Run installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify: `python --version` in new terminal

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.11

# Verify
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3-pip

# Verify
python3 --version
```

### 3. Verify Standard Library Modules

This tool uses **ONLY** Python standard library modules. No `pip install` needed for core functionality.

**Verify:**
```powershell
python -c "import sqlite3, subprocess, pathlib, logging; print('✅ All modules available')"
```

Expected output:
```
✅ All modules available
```

---

## ADB Installation

Android Debug Bridge (ADB) is required to communicate with Android devices.

### Windows Setup (Recommended)

1. **Download Platform Tools:**
   - Visit: https://developer.android.com/tools/releases/platform-tools
   - Download: `platform-tools_r35.0.1-windows.zip` (or latest)
   - Extract to temporary folder

2. **Copy Required Files:**
   ```powershell
   # From extracted platform-tools/ folder, copy these 3 files to your project's bin/ folder:
   # - adb.exe
   # - AdbWinApi.dll
   # - AdbWinUsbApi.dll
   ```

3. **Verify Installation:**
   ```powershell
   cd d:\path\to\Whatsapp_AndroidToIphone
   .\bin\adb.exe version
   ```

   Expected output:
   ```
   Android Debug Bridge version 1.0.41
   Version 35.0.1-12345678
   ...
   ```

### macOS Setup

1. **Install via Homebrew:**
   ```bash
   brew install android-platform-tools
   ```

2. **Verify:**
   ```bash
   adb version
   ```

3. **Update Project Code:**
   - Edit `src/utils.py`
   - Change `ADB_PATH` from `'bin/adb.exe'` to `'adb'` (uses system PATH)

### Linux Setup

1. **Install via Package Manager:**
   ```bash
   # Ubuntu/Debian
   sudo apt install adb

   # Fedora/RHEL
   sudo yum install android-tools
   ```

2. **Verify:**
   ```bash
   adb version
   ```

3. **Update Project Code:**
   - Edit `src/utils.py`
   - Change `ADB_PATH` from `'bin/adb.exe'` to `'adb'`

---

## Legacy WhatsApp APK

Android backup requires downgrading WhatsApp to a legacy version (2.11.431 - 2.11.498) that supports unencrypted backups.

### ⚠️ Legal Disclaimer

**IMPORTANT:**
- Only download APKs from **trusted sources** (APKMirror, APKPure)
- Verify APK signatures before installation
- This is for **personal data migration** only
- Do NOT distribute APK files
- Use at your own risk

### 1. Download Legacy APK

**Recommended Source:** APKMirror

1. Visit: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/
2. Find version: **2.11.431** (or any version between 2.11.431 - 2.11.498)
3. Download APK file (usually ~20-30MB)
4. **Verify signature:** APKMirror shows verified signature badge

**Alternative:** APKPure
- Visit: https://apkpure.com/whatsapp-messenger/com.whatsapp
- Select "Old Versions"
- Download 2.11.431

### 2. Place APK in Project

```powershell
# Move downloaded APK to project's apk/ folder
Move-Item "Downloads\WhatsApp_2.11.431.apk" "d:\path\to\Whatsapp_AndroidToIphone\apk\"

# Verify
Get-ChildItem apk\
```

Expected output:
```
Directory: d:\path\to\Whatsapp_AndroidToIphone\apk

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          11/28/2025  10:30 AM      28645120 WhatsApp_2.11.431.apk
-a---          11/28/2025  09:00 AM            523 README.md
```

### 3. Verification

The migration script will automatically:
- Detect APK in `apk/` folder
- Verify it's a valid APK file
- Prompt before installation

---

## iTunes/Finder Setup

### Windows - iTunes Installation

1. **Download iTunes:**
   - Visit: https://www.apple.com/itunes/download/
   - Download Windows 64-bit version
   - Run installer

2. **Verify Installation:**
   - Open iTunes
   - Connect iPhone via USB
   - Trust computer on iPhone

3. **Locate Backup Directory:**
   - Default location: `%APPDATA%\Apple Computer\MobileSync\Backup\`
   - Example: `C:\Users\YourName\AppData\Roaming\Apple Computer\MobileSync\Backup\`

### macOS - Finder

No installation needed. macOS 10.15+ (Catalina and later) uses Finder instead of iTunes.

1. **Connect iPhone:**
   - Open Finder
   - Click iPhone in sidebar
   - Trust computer on iPhone

2. **Locate Backup Directory:**
   - Default location: `~/Library/Application Support/MobileSync/Backup/`

### Create Test Backup

Before migration, ensure you can create iOS backups:

1. Connect iPhone
2. iTunes (Windows) or Finder (macOS)
3. Select device
4. **✅ Uncheck "Encrypt local backup"** (critical!)
5. Click "Back Up Now"
6. Wait for completion

**Verify:**
- Backup appears in backup directory
- Contains `Manifest.db` file
- Contains `7c7fba66680ef796b916b067077cc246adacf01d` (ChatStorage.sqlite)

---

## Project Setup

### 1. Clone/Download Project

```powershell
# If using git
git clone <repository-url> Whatsapp_AndroidToIphone
cd Whatsapp_AndroidToIphone

# Or download ZIP and extract
```

### 2. Verify Directory Structure

```powershell
Get-ChildItem -Recurse -Depth 1
```

Expected structure:
```
Whatsapp_AndroidToIphone/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── migrate.py
│   ├── android_backup.py
│   ├── ios_backup.py
│   └── utils.py
├── bin/
│   ├── adb.exe              # ⚠️ You must download
│   ├── AdbWinApi.dll        # ⚠️ You must download
│   ├── AdbWinUsbApi.dll     # ⚠️ You must download
│   └── README.md
├── apk/
│   ├── WhatsApp_2.11.431.apk  # ⚠️ You must download
│   └── README.md
├── backups/                 # Created automatically
├── logs/                    # Created automatically
├── tests/                   # Optional
├── docs/
│   ├── SETUP.md            # ← You are here
│   ├── USAGE.md
│   └── ARCHITECTURE.md
├── main.py                  # Entry point
├── requirements.txt
├── README.md
└── .gitignore
```

### 3. Missing Files Check

The following files must be manually downloaded:

- [ ] `bin/adb.exe` (from Android SDK Platform Tools)
- [ ] `bin/AdbWinApi.dll` (from Android SDK Platform Tools)
- [ ] `bin/AdbWinUsbApi.dll` (from Android SDK Platform Tools)
- [ ] `apk/WhatsApp_2.11.431.apk` (or similar version 2.11.431-2.11.498)

---

## Verification

### Step 1: Verify Python Imports

```powershell
python -c "import src; print('✅ Python modules OK')"
```

### Step 2: Verify ADB

```powershell
.\bin\adb.exe version
```

Expected output:
```
Android Debug Bridge version 1.0.41
...
```

### Step 3: Verify ADB Device Connection

1. Connect Android device via USB
2. Enable USB debugging on Android:
   - Settings → About Phone → Tap "Build Number" 7 times (enables Developer Options)
   - Settings → Developer Options → Enable "USB Debugging"
3. Run:
   ```powershell
   .\bin\adb.exe devices
   ```

Expected output:
```
List of devices attached
ABC123XYZ       device
```

If shows `unauthorized`, unlock Android and tap "Allow" on USB debugging prompt.

### Step 4: Verify Legacy APK

```powershell
Test-Path apk\WhatsApp_2.11.431.apk
```

Expected output:
```
True
```

### Step 5: Verify iTunes Backup Directory

**Windows:**
```powershell
Test-Path "$env:APPDATA\Apple Computer\MobileSync\Backup\"
```

**macOS:**
```bash
ls ~/Library/Application\ Support/MobileSync/Backup/
```

Should list existing backup folders (UUIDs).

### Step 6: Full System Check

Run the migration script in dry-run mode:

```powershell
python main.py --check-dependencies
```

Expected output:
```
[INFO] Checking dependencies...
✅ Python 3.11.5 detected
✅ ADB found: bin\adb.exe (version 35.0.1)
✅ Legacy APK found: apk\WhatsApp_2.11.431.apk
✅ iTunes backup directory: C:\Users\...\MobileSync\Backup\
⚠️  Android device: Not connected (connect to verify)
⚠️  iOS device: No recent backup (create backup to verify)

Summary: 4/6 checks passed. Ready to proceed after connecting devices.
```

---

## Troubleshooting

### ADB Not Found

**Error:** `ADB executable not found at bin/adb.exe`

**Solution:**
1. Download Android SDK Platform Tools
2. Extract `adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll` to `bin/`
3. Verify: `.\bin\adb.exe version`

### ADB Device Unauthorized

**Error:** `List of devices attached: ABC123XYZ unauthorized`

**Solution:**
1. Unlock Android device
2. Look for USB debugging prompt
3. Tap "Allow" and check "Always allow from this computer"
4. Run `.\bin\adb.exe devices` again

### Python Module Import Error

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
1. Ensure you're in project root directory: `cd d:\path\to\Whatsapp_AndroidToIphone`
2. Verify `src/__init__.py` exists
3. Try: `python -c "import sys; print(sys.path)"`

### Legacy APK Not Found

**Error:** `No legacy WhatsApp APK found in apk/ folder`

**Solution:**
1. Download WhatsApp 2.11.431 from APKMirror
2. Move to `apk/` folder
3. Verify filename: `Get-ChildItem apk\`

### iTunes Backup Directory Not Found

**Error:** `iTunes backup directory not found`

**Solution Windows:**
1. Install iTunes from https://www.apple.com/itunes/
2. Restart computer
3. Check: `Test-Path "$env:APPDATA\Apple Computer\MobileSync\Backup\"`

**Solution macOS:**
1. Update to macOS 10.15+ (uses Finder)
2. Check: `ls ~/Library/Application\ Support/MobileSync/Backup/`

### Insufficient Storage

**Error:** `Insufficient disk space for backup`

**Solution:**
1. Free up at least 5GB on C:\ drive (Windows) or root partition (macOS/Linux)
2. Delete old backups from `backups/` folder
3. Empty Recycle Bin / Trash

### USB Connection Issues

**Error:** `Device not detected`

**Solution:**
1. Try different USB cable (some are charge-only)
2. Try different USB port (prefer USB 3.0)
3. Disable "Charge only" mode on Android (Settings → Developer Options → Select USB Configuration → MTP)
4. Restart ADB: `.\bin\adb.exe kill-server` then `.\bin\adb.exe start-server`

---

## Next Steps

Once setup is complete:

1. ✅ All dependencies installed
2. ✅ Android device connected and authorized
3. ✅ iOS device backup created
4. ✅ Legacy WhatsApp APK downloaded

Proceed to:
- **[USAGE.md](USAGE.md)** - Step-by-step migration guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical documentation (for developers)

---

## Support

If you encounter issues not covered here:

1. Check `logs/migration.log` for detailed error messages
2. Review [USAGE.md](USAGE.md) for common migration errors
3. Consult [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Last Updated:** November 28, 2025  
**Version:** 1.0.0
