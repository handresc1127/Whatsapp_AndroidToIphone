"""
WhatsApp Android to iOS Migration Tool - Setup Script

Este script descarga y configura automáticamente las dependencias necesarias:
- APK legacy de WhatsApp (versión 2.11.431)
- Verifica la instalación de ADB

Ejecutar ANTES de main.py:
    python setup.py
"""

import os
import sys
import urllib.request
import subprocess
from pathlib import Path


def print_banner():
    """Imprime banner del setup."""
    print("\n" + "="*80)
    print("WhatsApp Android → iOS Migration Tool - SETUP")
    print("="*80 + "\n")


def check_adb():
    """Verifica que ADB esté disponible."""
    print("Checking ADB availability...")
    
    # Verificar bin/adb.exe
    if os.path.exists('bin/adb.exe'):
        print("  ✓ ADB found: bin/adb.exe")
        return True
    
    # Verificar ADB del sistema
    try:
        result = subprocess.run(
            ['adb', 'version'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            print("  ✓ ADB found in system PATH")
            for line in result.stdout.split('\n'):
                if 'Installed as' in line:
                    print(f"    Location: {line.split('Installed as')[1].strip()}")
                    break
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("\n  ✗ ADB not found!")
    print("\n  Please install Android Platform Tools:")
    print("  1. Download: https://developer.android.com/tools/releases/platform-tools")
    print("  2. Extract and add to PATH, OR")
    print("  3. Copy adb.exe, AdbWinApi.dll, AdbWinUsbApi.dll to bin/")
    print("\n  See bin/README.md for detailed instructions.\n")
    return False


def download_legacy_apk():
    """Descarga el APK legacy de WhatsApp."""
    print("\nDownloading WhatsApp Legacy APK...")
    
    apk_dir = Path('apk')
    apk_dir.mkdir(exist_ok=True)
    
    apk_path = apk_dir / 'LegacyWhatsApp.apk'
    
    # Verificar si ya existe
    if apk_path.exists():
        size_mb = apk_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ APK already exists: {apk_path} ({size_mb:.2f} MB)")
        
        response = input("\n  Do you want to re-download it? [y/N]: ").strip().upper()
        if response != 'Y':
            return True
    
    print("\n" + "="*80)
    print("IMPORTANT: APK Download Information")
    print("="*80)
    print("\nWhatsApp Legacy APK (v2.11.431) is required for unencrypted backups.")
    print("\nDue to copyright restrictions, this script CANNOT download it automatically.")
    print("\nPlease follow these manual steps:")
    print("\n1. Visit: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/")
    print("\n2. Search for version: 2.11.431 (August 2014)")
    print("\n3. Download the APK file")
    print("\n4. Save it as: apk/LegacyWhatsApp.apk")
    print("\n5. Come back and run this setup again")
    print("\n" + "="*80)
    print("\nWhy version 2.11.431?")
    print("  - Last version WITHOUT AES-256 encryption")
    print("  - Allows extraction of msgstore.db from backups")
    print("  - Versions 2.12+ use encrypted backups (won't work)")
    print("\n" + "="*80)
    
    response = input("\nHave you already downloaded the APK? [y/N]: ").strip().upper()
    if response == 'Y':
        print("\nGreat! Verifying APK location...")
        if apk_path.exists():
            size_mb = apk_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ APK found: {apk_path} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"  ✗ APK not found at: {apk_path}")
            print(f"\n  Common issues:")
            print(f"    - Wrong filename (must be exactly 'LegacyWhatsApp.apk')")
            print(f"    - Wrong location (must be in 'apk/' folder)")
            print(f"    - File still downloading")
            print(f"\n  Current apk/ directory contents:")
            if apk_dir.exists():
                files = list(apk_dir.iterdir())
                if files:
                    for f in files:
                        print(f"    - {f.name}")
                else:
                    print(f"    (empty)")
            print(f"\n  Please move/rename the APK to: apk\\LegacyWhatsApp.apk")
            return False
    
    print("\n  Please download the APK first, then run setup again.")
    return False


def check_migrate_script():
    """Verifica que migrate.py exista."""
    print("\nChecking migration script...")
    
    # Buscar en src/migrate.py (proyecto modular)
    if os.path.exists('src/migrate.py'):
        print("  ✓ src/migrate.py found")
        return True
    
    # Buscar en raíz (proyecto legacy)
    if os.path.exists('migrate.py'):
        print("  ✓ migrate.py found")
        return True
    
    print("  ✗ migrate.py not found!")
    print("    Expected location: src/migrate.py")
    print("    This is a required component for the migration process.")
    return False


def create_directories():
    """Crea directorios necesarios."""
    print("\nCreating required directories...")
    
    dirs = ['apk', 'bin', 'logs', 'backups']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"  ✓ {dir_name}/")
    
    return True


def print_summary(adb_ok, apk_ok, migrate_ok):
    """Imprime resumen del setup."""
    print("\n" + "="*80)
    print("SETUP SUMMARY")
    print("="*80)
    
    print(f"\n  ADB Available:           {'✓ YES' if adb_ok else '✗ NO'}")
    print(f"  WhatsApp Legacy APK:     {'✓ YES' if apk_ok else '✗ NO'}")
    print(f"  Migration Script:        {'✓ YES' if migrate_ok else '✗ NO'}")
    
    print("\n" + "="*80)
    
    if adb_ok and apk_ok and migrate_ok:
        print("✓ SETUP COMPLETE - Ready to run migration!")
        print("\nNext steps:")
        print("  1. Connect your Android device via USB")
        print("  2. Enable USB debugging on Android")
        print("  3. Run: python main.py")
        print("\n" + "="*80 + "\n")
        return True
    else:
        print("✗ SETUP INCOMPLETE - Please fix the issues above")
        
        if not apk_ok:
            print("\nTo fix APK issue:")
            print("  1. Download from: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/")
            print("  2. Version: 2.11.431")
            print("  3. Rename to: LegacyWhatsApp.apk")
            print("  4. Move to: apk\\")
            print("  5. Run setup again: python setup.py")
        
        if not adb_ok:
            print("\nTo fix ADB issue:")
            print("  See: bin\\README.md")
        
        print("\n" + "="*80 + "\n")
        return False


def main():
    """Función principal del setup."""
    print_banner()
    
    # Crear directorios
    create_directories()
    
    # Verificar componentes
    adb_ok = check_adb()
    apk_ok = download_legacy_apk()
    migrate_ok = check_migrate_script()
    
    # Resumen
    success = print_summary(adb_ok, apk_ok, migrate_ok)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nSetup failed with error: {e}")
        sys.exit(1)
