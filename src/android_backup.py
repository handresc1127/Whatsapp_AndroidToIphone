"""
WhatsApp Android to iOS Migration Tool

Módulo para gestión de backups de Android via ADB.
"""

import logging
import os
import tarfile
from typing import Optional

from .utils import run_adb_command, ensure_directory, clean_directory, print_step, get_adb_command


class AndroidBackupManager:
    """Gestor de backups de WhatsApp en Android."""
    
    # Configuración de paquetes
    WHATSAPP_STANDARD = {
        'package': 'com.whatsapp',
        'apk': 'LegacyWhatsApp.apk',
        'db_path': 'tmp/apps/com.whatsapp/db/msgstore.db'
    }
    
    WHATSAPP_BUSINESS = {
        'package': 'com.whatsapp.w4b',
        'apk': 'LegacyWhatsAppBusiness.apk',
        'db_path': 'tmp/apps/com.whatsapp.w4b/db/msgstore.db'
    }
    
    def __init__(self, whatsapp_type: str = 'standard'):
        """
        Inicializa el gestor de backups de Android.
        
        Args:
            whatsapp_type: 'standard' o 'business'
        """
        self.logger = logging.getLogger('whatsapp_migration.android_backup')
        
        if whatsapp_type == 'business':
            self.config = self.WHATSAPP_BUSINESS
        else:
            self.config = self.WHATSAPP_STANDARD
        
        # Detectar comando ADB disponible
        self.adb_cmd = get_adb_command()
        
        self.logger.info(f"Initialized for {whatsapp_type} WhatsApp")
        self.logger.info(f"Package: {self.config['package']}")
        self.logger.info(f"Using ADB: {self.adb_cmd}")
    
    def start_adb_server(self) -> bool:
        """
        Inicia el servidor ADB.
        
        Returns:
            True si el servidor inició correctamente
        """
        try:
            self.logger.info("Stopping ADB server...")
            run_adb_command([self.adb_cmd, 'kill-server'], check=False)
            
            self.logger.info("Starting ADB server...")
            run_adb_command([self.adb_cmd, 'start-server'])
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to start ADB server: {e}")
            return False
    
    def wait_for_device(self, timeout: int = 60) -> bool:
        """
        Espera a que un dispositivo Android se conecte.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
        
        Returns:
            True si el dispositivo se conectó
        """
        try:
            self.logger.info(f"Waiting for Android device (timeout: {timeout}s)...")
            print("\nPlease connect your Android device via USB...")
            print("Make sure USB debugging is enabled.")
            
            run_adb_command([self.adb_cmd, 'wait-for-device'], timeout=timeout)
            
            # Verificar dispositivo
            result = run_adb_command([self.adb_cmd, 'devices'])
            self.logger.info(f"ADB devices output:\n{result.stdout}")
            
            print("\n[OK] Android device connected!")
            return True
            
        except Exception as e:
            self.logger.error(f"Device connection failed: {e}")
            return False
    
    def uninstall_whatsapp(self, keep_data: bool = True) -> bool:
        """
        Desinstala WhatsApp del dispositivo.
        
        Args:
            keep_data: Si True, mantiene los datos de la app (-k flag)
        
        Returns:
            True si la desinstalación fue exitosa
        """
        try:
            self.logger.info(f"Uninstalling {self.config['package']}...")
            
            cmd = [self.adb_cmd, 'shell', 'pm', 'uninstall']
            if keep_data:
                cmd.append('-k')
            cmd.append(self.config['package'])
            
            result = run_adb_command(cmd, check=False)
            
            if 'Success' in result.stdout or result.returncode == 0:
                self.logger.info("WhatsApp uninstalled successfully")
                return True
            else:
                self.logger.warning(f"Uninstall result: {result.stdout}")
                return True  # Puede no estar instalado, continuar
                
        except Exception as e:
            self.logger.error(f"Failed to uninstall WhatsApp: {e}")
            return False
    
    def install_legacy_apk(self) -> bool:
        """
        Instala el APK legacy de WhatsApp.
        
        Returns:
            True si la instalación fue exitosa
        """
        try:
            apk_path = f"apk/{self.config['apk']}"
            
            if not os.path.exists(apk_path):
                self.logger.error(f"APK not found: {apk_path}")
                print(f"\n[ERROR] APK file not found: {apk_path}")
                print("Please download the legacy APK. See apk/README.md for instructions.")
                return False
            
            self.logger.info(f"Installing legacy APK: {apk_path}")
            print(f"\nInstalling legacy WhatsApp APK...")
            
            # -r: replace existing, -d: allow downgrade
            result = run_adb_command([
                self.adb_cmd, 'install', '-r', '-d', apk_path
            ], timeout=120)
            
            if 'Success' in result.stdout:
                self.logger.info("Legacy APK installed successfully")
                print("[OK] Legacy WhatsApp installed!")
                print("\nIMPORTANT: Please open WhatsApp and verify your phone number.")
                print("           This is required before creating the backup.")
                input("Press Enter once WhatsApp is verified and ready...")
                return True
            else:
                self.logger.error(f"Installation failed: {result.stdout}")
                print(f"\n[ERROR] Failed to install legacy APK")
                print(f"Reason: {result.stdout}")
                
                # Check for common errors
                if 'INSTALL_FAILED_VERSION_DOWNGRADE' in result.stdout:
                    print("\nThe app data is preventing downgrade.")
                    print("Please manually uninstall WhatsApp completely from Android settings,")
                    print("then run this script again.")
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install legacy APK: {e}")
            return False
    
    def create_backup(self, output_file: str = 'tmp/whatsapp.ab') -> bool:
        """
        Crea backup de WhatsApp sin cifrar.
        
        Args:
            output_file: Ruta del archivo de backup
        
        Returns:
            True si el backup se creó exitosamente
        """
        try:
            ensure_directory('tmp')
            
            self.logger.info(f"Creating Android backup: {output_file}")
            print("\n" + "="*80)
            print("CREATING ANDROID BACKUP")
            print("="*80)
            print("\nIMPORTANT:")
            print("1. A backup prompt will appear on your Android device")
            print("2. DO NOT set a password - leave it empty")
            print("3. Tap 'BACK UP MY DATA'")
            print("4. Wait for the backup to complete (may take several minutes)")
            print("\nStarting backup...")
            
            result = run_adb_command([
                self.adb_cmd, 'backup', '-f', output_file, self.config['package']
            ], timeout=600)  # 10 minutos de timeout
            
            # Validar que el archivo se creó
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                self.logger.info(f"Backup created: {size_mb:.2f} MB")
                print(f"\n[OK] Backup created successfully ({size_mb:.2f} MB)")
                return True
            else:
                self.logger.error("Backup file was not created or is empty")
                print("\n[ERROR] Backup failed. Please check if you authorized the backup on your device.")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def extract_ab_to_tar(self, ab_file: str, tar_file: str) -> bool:
        """
        Convierte archivo .ab (Android Backup) a .tar.
        
        El formato .ab tiene un header de 24 bytes seguido de datos zlib.
        Los reemplazamos con un header gzip para crear un .tar válido.
        
        Args:
            ab_file: Ruta del archivo .ab
            tar_file: Ruta del archivo .tar de salida
        
        Returns:
            True si la conversión fue exitosa
        """
        try:
            self.logger.info(f"Converting .ab to .tar: {ab_file} → {tar_file}")
            
            with open(ab_file, 'rb') as inp:
                with open(tar_file, 'wb') as out:
                    # Escribir header gzip
                    out.write(b'\x1f\x8b\x08\x00\x00\x00\x00\x00')
                    
                    # Saltar header .ab (24 bytes)
                    inp.read(24)
                    
                    # Copiar datos zlib
                    while True:
                        chunk = inp.read(4096)
                        if not chunk:
                            break
                        out.write(chunk)
            
            self.logger.info("Conversion successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to convert .ab to .tar: {e}")
            return False
    
    def extract_msgstore_db(self, tar_file: str, output_dir: str = 'out') -> Optional[str]:
        """
        Extrae msgstore.db del archivo tar.
        
        Args:
            tar_file: Ruta del archivo .tar
            output_dir: Directorio de salida
        
        Returns:
            Ruta del archivo msgstore.db extraído, None si falla
        """
        try:
            self.logger.info(f"Extracting tar file: {tar_file}")
            ensure_directory('tmp')
            ensure_directory(output_dir)
            
            # Extraer tar completo a tmp/
            with tarfile.open(tar_file) as tar:
                tar.extractall(path='tmp')
            
            self.logger.info("Tar extracted successfully")
            
            # Buscar msgstore.db
            db_path = self.config['db_path']
            
            if os.path.exists(db_path):
                output_path = f"{output_dir}/android.db"
                
                import shutil
                shutil.copy2(db_path, output_path)
                
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.logger.info(f"msgstore.db extracted: {size_mb:.2f} MB")
                print(f"\n[OK] Android database extracted ({size_mb:.2f} MB)")
                
                return output_path
            else:
                self.logger.error(f"msgstore.db not found at expected path: {db_path}")
                print(f"\n[ERROR] Database not found in backup at: {db_path}")
                print("The backup may be incomplete or corrupted.")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract msgstore.db: {e}")
            return False
    
    def cleanup(self) -> None:
        """Limpia archivos temporales y detiene ADB."""
        try:
            self.logger.info("Cleaning up Android backup process...")
            
            if os.path.exists('tmp'):
                clean_directory('tmp', self.logger)
            
            # Detener servidor ADB
            run_adb_command([self.adb_cmd, 'kill-server'], check=False)
            self.logger.info("ADB server stopped")
            
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    def extract_database_directly(self) -> Optional[str]:
        """
        Intenta extraer msgstore.db directamente desde /sdcard/WhatsApp/Databases/
        Maneja tanto bases de datos planas (.db) como encriptadas (.crypt14).
        
        Returns:
            Ruta del archivo msgstore.db desencriptado, None si falla
        """
        try:
            self.logger.info("Attempting direct database extraction...")
            ensure_directory('out')
            ensure_directory('tmp')
            
            # Rutas base según tipo de WhatsApp
            if self.config['package'] == 'com.whatsapp.w4b':
                db_dir = '/sdcard/Android/media/com.whatsapp.w4b/WhatsApp Business/Databases'
                alt_db_dir = '/sdcard/WhatsApp Business/Databases'
                key_path = f"/data/data/{self.config['package']}/files/key"
            else:
                db_dir = '/sdcard/Android/media/com.whatsapp/WhatsApp/Databases'
                alt_db_dir = '/sdcard/WhatsApp/Databases'
                key_path = f"/data/data/{self.config['package']}/files/key"
            
            # Intentar diferentes versiones de archivos
            db_files_to_try = [
                # Archivos encriptados (más común)
                ('msgstore.db.crypt14', f"{db_dir}/msgstore.db.crypt14"),
                ('msgstore.db.crypt15', f"{db_dir}/msgstore.db.crypt15"),
                ('msgstore.db.crypt12', f"{db_dir}/msgstore.db.crypt12"),
                # Archivo plano (legacy)
                ('msgstore.db', f"{db_dir}/msgstore.db"),
                # Alternativas
                ('msgstore.db.crypt14', f"{alt_db_dir}/msgstore.db.crypt14"),
                ('msgstore.db', f"{alt_db_dir}/msgstore.db"),
            ]
            
            extracted_file = None
            is_encrypted = False
            
            print(f"\n[INFO] Searching for WhatsApp database on device...")
            
            # Intentar extraer cada archivo
            for filename, remote_path in db_files_to_try:
                self.logger.debug(f"Trying: {remote_path}")
                local_temp = f'tmp/{filename}'
                
                result = run_adb_command([
                    self.adb_cmd, 'pull', remote_path, local_temp
                ], check=False, timeout=60)
                
                if result.returncode == 0 and os.path.exists(local_temp) and os.path.getsize(local_temp) > 0:
                    extracted_file = local_temp
                    is_encrypted = '.crypt' in filename
                    size_mb = os.path.getsize(local_temp) / (1024 * 1024)
                    print(f"[OK] Found: {filename} ({size_mb:.2f} MB)")
                    self.logger.info(f"Extracted: {remote_path} ({size_mb:.2f} MB)")
                    break
            
            if not extracted_file:
                self.logger.error("No database file found on device")
                print("\n[ERROR] Could not find WhatsApp database on device.")
                self._print_manual_extraction_help()
                return None
            
            # Si está encriptado, desencriptar
            if is_encrypted:
                print(f"\n[INFO] Database is encrypted, attempting decryption...")
                decrypted_db = self._decrypt_database(extracted_file, key_path)
                if not decrypted_db:
                    return None
                return decrypted_db
            else:
                # Mover archivo plano a ubicación final
                final_path = 'out/android.db'
                import shutil
                shutil.move(extracted_file, final_path)
                print(f"\n[OK] Database extracted successfully (unencrypted)")
                return final_path
                
        except Exception as e:
            self.logger.error(f"Direct extraction failed: {e}")
            print(f"\n[ERROR] Extraction failed: {e}")
            self._print_manual_extraction_help()
            return None
    
    def _print_manual_extraction_help(self) -> None:
        """Imprime instrucciones para extracción manual."""
        print("\nPossible causes:")
        print("  - WhatsApp doesn't have storage permissions enabled")
        print("  - Database is in a non-standard location (custom ROM)")
        print("  - Device requires root access for encrypted databases")
        print("\nManual solutions:")
        print("  1. Grant storage permissions: Settings → Apps → WhatsApp → Permissions → Storage → Allow")
        print("  2. Use file manager to navigate to:")
        print("     /sdcard/Android/media/com.whatsapp[.w4b]/WhatsApp/Databases/")
        print("  3. Copy msgstore.db.crypt14 (or latest backup) to computer")
        print("  4. Place in tmp/ folder and we'll try to decrypt it")
        print("  5. For encrypted databases, you may need WhatsApp Key Extractor tool")
    
    def _decrypt_database(self, encrypted_file: str, key_path: str) -> Optional[str]:
        """Desencripta base de datos de WhatsApp.
        
        Args:
            encrypted_file: Ruta al archivo .cryptXX
            key_path: Ruta a la clave de encriptación en el dispositivo
            
        Returns:
            Ruta al archivo desencriptado, None si falla
        """
        try:
            # Intentar extraer clave de encriptación
            print(f"[INFO] Extracting encryption key...")
            local_key = 'tmp/key'
            
            # Requiere root o adb root
            result = run_adb_command([
                self.adb_cmd, 'root'
            ], check=False, timeout=10)
            
            if result.returncode == 0:
                # Dispositivo con root habilitado
                result = run_adb_command([
                    self.adb_cmd, 'pull', key_path, local_key
                ], check=False, timeout=30)
                
                if result.returncode == 0 and os.path.exists(local_key):
                    print(f"[OK] Encryption key extracted")
                    self.logger.info("Encryption key extracted successfully")
                    
                    # Desencriptar usando la clave
                    decrypted_path = 'out/android.db'
                    if self._decrypt_with_key(encrypted_file, local_key, decrypted_path):
                        print(f"[OK] Database decrypted successfully")
                        return decrypted_path
                    else:
                        print(f"[ERROR] Decryption failed")
                        return None
                else:
                    self.logger.warning("Could not extract encryption key - device may not have root")
            
            # Fallback: intentar sin root (archivos más antiguos)
            print(f"\n[WARNING] Could not extract encryption key (root required)")
            print(f"\nFor encrypted databases (.crypt14), you need:")
            print(f"  1. Rooted Android device OR")
            print(f"  2. WhatsApp Key Extractor tool (search GitHub)")
            print(f"  3. Extract 'key' file manually and place in tmp/key")
            print(f"\nAlternatively, try:")
            print(f"  - Use an older backup if available (some may be unencrypted)")
            print(f"  - Use WhatsApp's official 'Export Chat' feature (limited)")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            print(f"\n[ERROR] Decryption failed: {e}")
            return None
    
    def _decrypt_with_key(self, encrypted_file: str, key_file: str, output_file: str) -> bool:
        """Desencripta archivo usando clave extraída.
        
        Args:
            encrypted_file: Archivo .cryptXX
            key_file: Archivo de clave
            output_file: Archivo de salida .db
            
        Returns:
            True si desencriptación exitosa
        """
        try:
            # Determinar versión de encriptación
            if '.crypt14' in encrypted_file:
                crypt_version = 14
            elif '.crypt15' in encrypted_file:
                crypt_version = 15
            elif '.crypt12' in encrypted_file:
                crypt_version = 12
            else:
                crypt_version = 14  # Default
            
            self.logger.info(f"Decrypting using crypt version {crypt_version}")
            print(f"[INFO] Using decryption method for crypt{crypt_version}...")
            
            # Leer clave
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            # Verificar tamaño de clave
            if len(key_data) != 158:  # Tamaño esperado para crypt14/15
                self.logger.warning(f"Unexpected key size: {len(key_data)} bytes")
            
            # Leer archivo encriptado
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Desencriptar (implementación básica para crypt14)
            # Nota: La desencriptación completa requiere AES-GCM con parámetros específicos
            # Para versión completa, se recomienda usar herramientas especializadas
            
            # Por ahora, informar al usuario que use herramienta externa
            print(f"\n[INFO] Encryption key and database extracted.")
            print(f"\nFor decryption, please use WhatsApp Viewer or similar tool:")
            print(f"  - Encrypted file: {encrypted_file}")
            print(f"  - Key file: {key_file}")
            print(f"  - Output should be: {output_file}")
            print(f"\nRecommended tools:")
            print(f"  - WhatsApp Viewer (GitHub)")
            print(f"  - wa-crypt-tools (GitHub)")
            print(f"  - Online: https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter")
            
            # TODO: Implementar desencriptación nativa
            # Requiere: pycryptodome o cryptography library
            # Por ahora retornamos False para que usuario use herramienta externa
            
            return False
            
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            return False
    
    def validate_database(self, db_path: str) -> bool:
        """
        Valida que la base de datos extraída sea válida y procesable.
        
        Args:
            db_path: Ruta del archivo de base de datos
        
        Returns:
            True si la DB es válida, False en caso contrario
        """
        try:
            import sqlite3
            from .utils import confirm_action
            
            self.logger.info(f"Validating database: {db_path}")
            
            # 1. Verificar que el archivo existe y no está vacío
            if not os.path.exists(db_path):
                self.logger.error("Database file does not exist")
                return False
            
            file_size = os.path.getsize(db_path)
            if file_size == 0:
                self.logger.error("Database file is empty")
                return False
            
            # 2. Verificar header SQLite
            with open(db_path, 'rb') as f:
                header = f.read(16)
            
            if not header.startswith(b'SQLite format 3'):
                self.logger.error("Not a valid SQLite database")
                print("\n[ERROR] Database file is corrupted or encrypted")
                print("The file does not have a valid SQLite header.")
                return False
            
            # 3. Intentar conectar y verificar tablas
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            # Verificar tablas mínimas requeridas
            required_tables = ['messages', 'chat']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                self.logger.error(f"Missing required tables: {missing_tables}")
                print(f"\n[ERROR] Database is missing required tables: {', '.join(missing_tables)}")
                conn.close()
                return False
            
            # 4. Verificar que hay datos
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            
            if message_count == 0:
                self.logger.warning("Database has no messages")
                print("\n[WARNING] Database is empty (no messages found)")
                if not confirm_action("Continue anyway?", default=False):
                    conn.close()
                    return False
            
            # 5. Detectar esquema (legacy vs moderno)
            if 'message_quoted' in tables or 'message_ephemeral' in tables:
                schema_version = 'modern'
            else:
                schema_version = 'legacy'
            
            self.logger.info(f"Database schema: {schema_version}")
            self.logger.info(f"Messages: {message_count:,}")
            self.logger.info(f"Tables: {len(tables)}")
            
            print(f"\n[OK] Database validated successfully")
            print(f"     Schema: {schema_version}")
            print(f"     Messages: {message_count:,}")
            print(f"     Size: {file_size / (1024 * 1024):.2f} MB")
            
            conn.close()
            return True
            
        except sqlite3.DatabaseError as e:
            self.logger.error(f"Database validation failed: {e}")
            print(f"\n[ERROR] Database validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            return False
    
    def legacy_backup_process(self) -> Optional[str]:
        """
        Ejecuta el proceso completo de backup legacy (downgrade + adb backup).
        
        ⚠️ DEPRECATED - NO LONGER USED ⚠️
        
        This method is preserved for reference only. Modern Android versions
        (8.0+) prevent APK downgrade without factory reset, making this
        approach non-viable.
        
        Current migration flow uses direct extraction only. If that fails,
        users must manually transfer the database file.
        
        NEVER call this method from the main migration flow.
        
        Returns:
            Ruta del archivo msgstore.db extraído, None si falla
        """
        raise NotImplementedError(
            "Legacy backup method is no longer supported. "
            "APK downgrade is not possible on modern Android versions. "
            "Use direct extraction or manual file transfer instead."
        )
        try:
            from .utils import confirm_action
            
            self.logger.info("Starting legacy backup process...")
            print("\n" + "="*80)
            print("LEGACY BACKUP PROCESS")
            print("="*80)
            print()
            print("WARNING: This will temporarily downgrade WhatsApp to version 2.11.x")
            print()
            print("Steps:")
            print("  1. Uninstall current WhatsApp (data preserved)")
            print("  2. Install legacy WhatsApp APK")
            print("  3. Create unencrypted backup via adb")
            print("  4. Extract msgstore.db")
            print()
            print("IMPORTANT:")
            print("  - You will need to verify your phone number again")
            print("  - This takes 5-15 minutes")
            print("  - Legacy APK must be available in apk/ folder")
            print("="*80)
            
            if not confirm_action("\nProceed with legacy backup?", default=False):
                self.logger.info("User cancelled legacy backup")
                return None
            
            # Desinstalar WhatsApp actual
            if not self.uninstall_whatsapp(keep_data=True):
                self.logger.error("Failed to uninstall current WhatsApp")
                return None
            
            # Instalar APK legacy
            if not self.install_legacy_apk():
                self.logger.error("Failed to install legacy APK")
                return None
            
            # Crear backup
            if not self.create_backup():
                self.logger.error("Failed to create backup")
                return None
            
            input("\nPress Enter once the backup is complete...")
            
            # Convertir .ab a .tar
            if not self.extract_ab_to_tar('tmp/whatsapp.ab', 'tmp/whatsapp.tar'):
                self.logger.error("Failed to convert .ab to .tar")
                return None
            
            # Extraer msgstore.db
            android_db = self.extract_msgstore_db('tmp/whatsapp.tar')
            if not android_db:
                self.logger.error("Failed to extract msgstore.db")
                return None
            
            # Cleanup
            self.cleanup()
            
            print("\n[OK] Legacy backup process completed")
            print(f"[OK] Database: {android_db}")
            
            return android_db
            
        except Exception as e:
            self.logger.error(f"Legacy backup process failed: {e}")
            return None
