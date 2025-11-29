#!/usr/bin/env python3
"""
WhatsApp Database Decryption Helper

Este script simplifica el proceso de desencriptación para usuarios sin root.
Guía paso a paso con verificaciones automáticas.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Imprime encabezado formateado."""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")

def print_step(number, title):
    """Imprime paso numerado."""
    print(f"\n{'='*80}")
    print(f"STEP {number}: {title}")
    print(f"{'='*80}\n")

def check_file_exists(path, description):
    """Verifica si un archivo existe."""
    if Path(path).exists():
        size = Path(path).stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"✅ {description} found: {path} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ {description} NOT found: {path}")
        return False

def run_command(cmd, description):
    """Ejecuta comando y muestra resultado."""
    print(f"\n[INFO] {description}...")
    print(f"[CMD]  {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {cmd[0]}")
        return False

def main():
    print_header("WhatsApp Database Decryption Helper")
    
    print("This script will guide you through decrypting your WhatsApp database.")
    print("Prerequisites: Python 3.8+, git, pip")
    
    # Verificar archivos necesarios
    print_step(1, "Verify Files")
    
    # Buscar archivo encriptado
    encrypted_files = list(Path('tmp').glob('msgstore*.crypt*'))
    
    if not encrypted_files:
        print("❌ No encrypted database found in tmp/ folder")
        print("\nPlease run 'python main.py' first to extract the database.")
        sys.exit(1)
    
    encrypted_file = encrypted_files[0]
    print(f"✅ Encrypted database found: {encrypted_file}")
    
    # Verificar si ya existe clave
    key_file = Path('tmp/key')
    has_key = check_file_exists(key_file, "Encryption key")
    
    if not has_key:
        print_step(2, "Extract Encryption Key")
        print("Your device doesn't have root, so we'll use WhatsApp Key Extractor.")
        print("\n🔧 Installing WhatsApp Key Extractor...")
        
        extractor_dir = Path('WhatsApp-Key-Database-Extractor')
        
        if not extractor_dir.exists():
            print("\n[INFO] Cloning WhatsApp Key Extractor from GitHub...")
            if not run_command([
                'git', 'clone', 
                'https://github.com/YuvrajRaghuvanshiS/WhatsApp-Key-Database-Extractor.git'
            ], "Downloading tool"):
                print("\n❌ Failed to download tool.")
                print("Please download manually from:")
                print("https://github.com/YuvrajRaghuvanshiS/WhatsApp-Key-Database-Extractor")
                sys.exit(1)
        else:
            print("✅ WhatsApp Key Extractor already downloaded")
        
        print("\n" + "=" * 80)
        print("MANUAL STEP REQUIRED")
        print("=" * 80)
        print("\n📱 Please run the key extractor manually:")
        print("\n1. Open a new terminal/command prompt")
        print("2. Navigate to: WhatsApp-Key-Database-Extractor")
        print("3. Run: python wa_kdbe.py")
        print("4. Follow the on-screen instructions:")
        print("   - Confirm backup on Android device")
        print("   - Wait for extraction to complete")
        print("5. Copy extracted 'key' file to: tmp/key")
        print("\n6. Then press ENTER here to continue...")
        
        input()
        
        # Verificar si ahora existe la clave
        if not check_file_exists(key_file, "Encryption key"):
            print("\n❌ Key file still not found. Please extract it manually.")
            print("Extraction location: WhatsApp-Key-Database-Extractor/extracted/key")
            print(f"Destination: {key_file.absolute()}")
            sys.exit(1)
    
    # Verificar e instalar dependencias de desencriptación
    print_step(3, "Install Decryption Tool")
    
    print("[INFO] Installing pycryptodome...")
    if not run_command([
        sys.executable, '-m', 'pip', 'install', 'pycryptodome'
    ], "Installing cryptography library"):
        print("⚠️  Warning: pycryptodome installation failed")
        print("You may need to install it manually: pip install pycryptodome")
    
    decrypter_dir = Path('WhatsApp-Crypt14-Decrypter')
    
    if not decrypter_dir.exists():
        print("\n[INFO] Cloning WhatsApp Crypt14 Decrypter from GitHub...")
        if not run_command([
            'git', 'clone',
            'https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter.git'
        ], "Downloading decryption tool"):
            print("\n❌ Failed to download decryption tool.")
            print("Please download manually from:")
            print("https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter")
            sys.exit(1)
    else:
        print("✅ Decryption tool already downloaded")
    
    # Desencriptar base de datos
    print_step(4, "Decrypt Database")
    
    output_file = Path('out/android.db')
    output_file.parent.mkdir(exist_ok=True)
    
    # Determinar script de desencriptación según versión
    if '.crypt15' in encrypted_file.name:
        decrypt_script = decrypter_dir / 'decrypt15.py'
    elif '.crypt14' in encrypted_file.name:
        decrypt_script = decrypter_dir / 'decrypt14.py'
    else:
        decrypt_script = decrypter_dir / 'decrypt14.py'  # Default
    
    print(f"[INFO] Using decryption script: {decrypt_script}")
    print(f"[INFO] Input:  {encrypted_file}")
    print(f"[INFO] Key:    {key_file}")
    print(f"[INFO] Output: {output_file}")
    
    if run_command([
        sys.executable,
        str(decrypt_script),
        str(key_file),
        str(encrypted_file),
        str(output_file)
    ], "Decrypting database"):
        print("\n✅ DATABASE DECRYPTED SUCCESSFULLY!")
        
        # Verificar archivo de salida
        if check_file_exists(output_file, "Decrypted database"):
            print_step(5, "Continue Migration")
            print("✅ Decrypted database is ready!")
            print(f"   Location: {output_file.absolute()}")
            print("\n📍 Next steps:")
            print("   1. Run: python main.py")
            print("   2. Script will detect the decrypted database")
            print("   3. Migration will continue automatically")
            print("\n" + "=" * 80)
        else:
            print("\n❌ Decryption completed but output file not found")
    else:
        print("\n❌ DECRYPTION FAILED")
        print("\nPossible causes:")
        print("  - Key doesn't match this database")
        print("  - Corrupted encrypted file")
        print("  - Wrong decryption script version")
        print("\nTry:")
        print("  - Re-extract key from device")
        print("  - Use different backup file")
        print("  - Check docs/ENCRYPTED_DATABASES.md for troubleshooting")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
