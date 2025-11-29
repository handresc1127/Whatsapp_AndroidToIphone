"""
WhatsApp Android to iOS Migration Tool

Módulo para gestión de backups de Android via ADB.
"""

import logging
import os
import tarfile
from typing import Optional

from utils import run_adb_command, ensure_directory, clean_directory, print_step, get_adb_command


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
                return True
            else:
                self.logger.error(f"Installation failed: {result.stdout}")
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
