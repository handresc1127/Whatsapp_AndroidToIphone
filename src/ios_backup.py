"""
WhatsApp Android to iOS Migration Tool

Módulo para gestión de backups de iOS via iTunes/Finder.
"""

import logging
import os
import shutil
import sqlite3
from typing import Optional, Tuple

from utils import ensure_directory, create_backup, validate_sqlite_database


class IOSBackupManager:
    """Gestor de backups de WhatsApp en iOS."""
    
    # Ubicaciones posibles de backups de iTunes
    BACKUP_LOCATIONS = [
        os.path.join(os.getenv('APPDATA', ''), 'Apple Computer', 'MobileSync', 'Backup'),
        os.path.join(os.getenv('USERPROFILE', ''), 'Apple', 'MobileSync', 'Backup'),
        os.path.join(os.getenv('USERPROFILE', ''), 'Apple', 'MobileSync'),
    ]
    
    def __init__(self):
        """Inicializa el gestor de backups de iOS."""
        self.logger = logging.getLogger('whatsapp_migration.ios_backup')
        self.backup_root = None
        self.backup_path = None
    
    def find_backup_directory(self) -> Optional[str]:
        """
        Busca el directorio raíz de backups de iTunes.
        
        Returns:
            Ruta del directorio de backups, None si no se encuentra
        """
        self.logger.info("Searching for iTunes backup directory...")
        
        for location in self.BACKUP_LOCATIONS:
            self.logger.debug(f"Checking: {location}")
            if os.path.exists(location) and os.path.isdir(location):
                self.logger.info(f"Found backup directory: {location}")
                self.backup_root = location
                return location
        
        self.logger.error("iTunes backup directory not found")
        print("\n[ERROR] iTunes backup directory not found.")
        print("\nSearched locations:")
        for loc in self.BACKUP_LOCATIONS:
            print(f"  - {loc}")
        print("\nPlease ensure you have created an iTunes backup of your iPhone.")
        return None
    
    def select_backup(self) -> Optional[str]:
        """
        Selecciona el backup de iPhone a usar.
        
        Si hay múltiples backups, solicita al usuario que seleccione uno.
        
        Returns:
            Ruta del backup seleccionado, None si falla
        """
        if not self.backup_root:
            if not self.find_backup_directory():
                return None
        
        try:
            # Listar directorios (cada uno es un backup)
            backups = [d for d in os.listdir(self.backup_root) 
                      if os.path.isdir(os.path.join(self.backup_root, d))]
            
            if len(backups) == 0:
                self.logger.error("No backups found")
                print("\n[ERROR] No iPhone backups found.")
                print(f"Expected location: {self.backup_root}")
                print("\nPlease create an unencrypted backup using iTunes/Finder.")
                return None
            
            elif len(backups) == 1:
                # Solo un backup, usarlo automáticamente
                backup_path = os.path.join(self.backup_root, backups[0])
                self.logger.info(f"Using backup: {backup_path}")
                self.backup_path = backup_path
                return backup_path
            
            else:
                # Múltiples backups, pedir al usuario
                self.logger.info(f"Found {len(backups)} backups")
                print(f"\n[INFO] Found {len(backups)} iPhone backups:")
                
                for idx, backup in enumerate(backups, 1):
                    backup_path = os.path.join(self.backup_root, backup)
                    info_plist = os.path.join(backup_path, 'Info.plist')
                    
                    # Intentar leer nombre del dispositivo
                    device_name = backup
                    if os.path.exists(info_plist):
                        try:
                            import plistlib
                            with open(info_plist, 'rb') as f:
                                info = plistlib.load(f)
                                device_name = info.get('Device Name', backup)
                        except:
                            pass
                    
                    print(f"  {idx}. {device_name}")
                    print(f"     Path: {backup_path}")
                
                # Solicitar selección
                while True:
                    try:
                        choice = input("\nSelect backup number (1-{}): ".format(len(backups)))
                        idx = int(choice) - 1
                        if 0 <= idx < len(backups):
                            backup_path = os.path.join(self.backup_root, backups[idx])
                            self.logger.info(f"User selected: {backup_path}")
                            self.backup_path = backup_path
                            return backup_path
                    except ValueError:
                        pass
                    print("Invalid selection. Please try again.")
                    
        except Exception as e:
            self.logger.error(f"Failed to select backup: {e}")
            return None
    
    def extract_chatstorage(self, output_file: str = 'out/ios.db') -> Optional[Tuple[str, str]]:
        """
        Extrae ChatStorage.sqlite del backup de iTunes.
        
        Args:
            output_file: Ruta del archivo de salida
        
        Returns:
            Tupla (output_path, chatstorage_path) si tiene éxito, None si falla
        """
        if not self.backup_path:
            if not self.select_backup():
                return None
        
        try:
            ensure_directory('out')
            
            # Conectar a Manifest.db
            manifest_path = os.path.join(self.backup_path, 'Manifest.db')
            
            if not os.path.exists(manifest_path):
                self.logger.error(f"Manifest.db not found in backup: {manifest_path}")
                print("\n[ERROR] Manifest.db not found.")
                print("The backup may be encrypted or corrupted.")
                print("\nPlease create an UNENCRYPTED backup in iTunes/Finder.")
                return None
            
            self.logger.info(f"Opening Manifest.db: {manifest_path}")
            
            conn = sqlite3.connect(manifest_path)
            cursor = conn.cursor()
            
            # Buscar ChatStorage.sqlite
            cursor.execute("""
                SELECT fileID FROM Files 
                WHERE relativePath = 'ChatStorage.sqlite' 
                AND domain = 'AppDomainGroup-group.net.whatsapp.WhatsApp.shared'
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            if len(results) != 1:
                self.logger.error(f"ChatStorage.sqlite not found in manifest (found {len(results)} matches)")
                print("\n[ERROR] WhatsApp data not found in iPhone backup.")
                print("\nPossible reasons:")
                print("  - WhatsApp is not installed on iPhone")
                print("  - WhatsApp backup is disabled")
                print("  - Backup is incomplete")
                return None
            
            file_id = results[0][0]
            self.logger.info(f"Found ChatStorage.sqlite with fileID: {file_id}")
            
            # Construir ruta del archivo
            # Estructura: {backup}/{primeros_2_chars}/{fileID_completo}
            chatstorage_path = os.path.join(
                self.backup_path,
                file_id[:2],
                file_id
            )
            
            if not os.path.exists(chatstorage_path):
                self.logger.error(f"ChatStorage file not found: {chatstorage_path}")
                return None
            
            # Copiar a directorio de salida
            shutil.copy2(chatstorage_path, output_file)
            
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            self.logger.info(f"ChatStorage.sqlite extracted: {size_mb:.2f} MB")
            print(f"\n[OK] iOS database extracted ({size_mb:.2f} MB)")
            
            # Validar que sea SQLite válido
            if not validate_sqlite_database(output_file, expected_tables=['ZWAMESSAGE']):
                self.logger.error("Extracted file is not a valid WhatsApp iOS database")
                return None
            
            return output_file, chatstorage_path
            
        except Exception as e:
            self.logger.error(f"Failed to extract ChatStorage.sqlite: {e}")
            return None
    
    def update_backup(self, new_db_file: str, backup_safety: bool = True) -> bool:
        """
        Actualiza el backup de iTunes con la nueva base de datos migrada.
        
        Args:
            new_db_file: Ruta de la nueva base de datos (out/out.db)
            backup_safety: Si True, crea backup antes de sobrescribir
        
        Returns:
            True si la actualización fue exitosa
        """
        try:
            if not self.backup_path:
                self.logger.error("No backup path set")
                return False
            
            # Buscar ChatStorage nuevamente para obtener ruta
            manifest_path = os.path.join(self.backup_path, 'Manifest.db')
            conn = sqlite3.connect(manifest_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fileID FROM Files 
                WHERE relativePath = 'ChatStorage.sqlite' 
                AND domain = 'AppDomainGroup-group.net.whatsapp.WhatsApp.shared'
            """)
            
            file_id = cursor.fetchone()[0]
            conn.close()
            
            chatstorage_path = os.path.join(self.backup_path, file_id[:2], file_id)
            
            # Crear backup de seguridad
            if backup_safety:
                backup_file = create_backup(chatstorage_path, 'backups')
                if backup_file:
                    self.logger.info(f"Safety backup created: {backup_file}")
                    print(f"\n[OK] Safety backup created: {backup_file}")
            
            # Validar archivo nuevo
            if not os.path.exists(new_db_file):
                self.logger.error(f"New database file not found: {new_db_file}")
                return False
            
            if not validate_sqlite_database(new_db_file, expected_tables=['ZWAMESSAGE']):
                self.logger.error("New database is invalid")
                return False
            
            # Sobrescribir ChatStorage en el backup
            self.logger.info(f"Updating iTunes backup: {chatstorage_path}")
            shutil.copy2(new_db_file, chatstorage_path)
            
            self.logger.info("iTunes backup updated successfully")
            print("\n[OK] iTunes backup updated successfully!")
            print("\nNext steps:")
            print("  1. Connect your iPhone to iTunes/Finder")
            print("  2. Restore from this backup")
            print("  3. Open WhatsApp and verify your chats")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update backup: {e}")
            
            # Intentar restaurar desde backup
            if backup_safety and backup_file:
                try:
                    self.logger.info("Attempting to restore from safety backup...")
                    shutil.copy2(backup_file, chatstorage_path)
                    self.logger.info("Restored from safety backup")
                    print("\n[INFO] Restored original file from safety backup")
                except:
                    pass
            
            return False
