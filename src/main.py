"""
WhatsApp Android to iOS Migration Tool - Main Script

Script principal refactorizado con arquitectura modular, manejo robusto de errores,
logging estructurado y backups automáticos de seguridad.

Usage:
    python src/main.py
"""

import os
import sys

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import (
    setup_logging, validate_file_exists, validate_directory_exists,
    print_step, print_separator, confirm_action, clean_directory,
    ensure_directory
)
from src.android_backup import AndroidBackupManager
from src.ios_backup import IOSBackupManager
from src.migrate import WhatsAppMigrator


def validate_dependencies(logger):
    """
    Valida que todas las dependencias externas existan.
    
    Args:
        logger: Logger para registrar resultados
    """
    print_step(1, "Validating Dependencies")
    
    required_files = {
        'bin/adb.exe': 'Android Debug Bridge executable',
        'bin/AdbWinApi.dll': 'ADB Windows API library',
        'bin/AdbWinUsbApi.dll': 'ADB Windows USB library',
    }
    
    # Validar archivos bin/
    for filepath, description in required_files.items():
        validate_file_exists(filepath, description, logger)
    
    # Validar directorios
    validate_directory_exists('apk', 'APK directory for legacy WhatsApp files', logger)
    
    # Informar sobre APKs (no son obligatorios hasta que se seleccione el tipo)
    print("\n[OK] Core dependencies validated")
    print("\nNOTE: Legacy WhatsApp APKs are required but will be validated when needed.")
    print("      See apk/README.md for download instructions.\n")
    
    logger.info("All core dependencies validated successfully")


def select_whatsapp_type():
    """
    Solicita al usuario que seleccione el tipo de WhatsApp.
    
    Returns:
        'standard' o 'business'
    """
    print_step(2, "Select WhatsApp Type")
    
    print("\nWhich WhatsApp do you want to migrate?")
    print("  1. WhatsApp (Standard)")
    print("  2. WhatsApp Business")
    
    while True:
        choice = input("\nSelect option (1 or 2): ").strip()
        if choice == '1':
            return 'standard'
        elif choice == '2':
            return 'business'
        else:
            print("Invalid option. Please enter 1 or 2.")


def android_backup_process(whatsapp_type, logger):
    """
    Ejecuta el proceso completo de backup de Android.
    
    Args:
        whatsapp_type: 'standard' o 'business'
        logger: Logger para registrar proceso
    
    Returns:
        Ruta del archivo android.db extraído, None si falla
    """
    print_step(3, "Android Backup Process")
    
    # Verificar si ya existe backup
    if os.path.exists('out/android.db'):
        print("\n[INFO] Android backup file already exists: out/android.db")
        if confirm_action("Do you want to use the existing backup?", default=True):
            logger.info("Using existing Android backup")
            return 'out/android.db'
        else:
            logger.info("User chose to create new backup")
    
    # Crear gestor de backup
    android_mgr = AndroidBackupManager(whatsapp_type)
    
    try:
        # Iniciar ADB
        if not android_mgr.start_adb_server():
            logger.error("Failed to start ADB server")
            return None
        
        # Esperar dispositivo
        if not android_mgr.wait_for_device():
            logger.error("Android device not connected")
            return None
        
        # Confirmar proceso
        print("\n" + "="*80)
        print("WARNING: This process will:")
        print("  1. Uninstall current WhatsApp (data will be preserved)")
        print("  2. Install legacy WhatsApp version")
        print("  3. Create unencrypted backup")
        print("="*80)
        
        if not confirm_action("\nDo you want to continue?"):
            logger.info("User cancelled Android backup process")
            return None
        
        # Desinstalar WhatsApp actual
        if not android_mgr.uninstall_whatsapp(keep_data=True):
            logger.error("Failed to uninstall WhatsApp")
            return None
        
        # Instalar APK legacy
        if not android_mgr.install_legacy_apk():
            logger.error("Failed to install legacy APK")
            return None
        
        # Crear backup
        if not android_mgr.create_backup():
            logger.error("Failed to create Android backup")
            return None
        
        input("\nPress Enter once the backup is complete...")
        
        # Convertir .ab a .tar
        if not android_mgr.extract_ab_to_tar('tmp/whatsapp.ab', 'tmp/whatsapp.tar'):
            logger.error("Failed to convert .ab to .tar")
            return None
        
        # Extraer msgstore.db
        android_db = android_mgr.extract_msgstore_db('tmp/whatsapp.tar')
        if not android_db:
            logger.error("Failed to extract msgstore.db")
            return None
        
        # Cleanup
        android_mgr.cleanup()
        
        print("\n[OK] Android backup process complete")
        print(f"[OK] Database saved to: {android_db}")
        print("\nYou can now safely remove your Android device.")
        
        return android_db
        
    except Exception as e:
        logger.error(f"Android backup process failed: {e}")
        android_mgr.cleanup()
        return None


def ios_backup_process(logger):
    """
    Ejecuta el proceso de extracción de backup de iOS.
    
    Args:
        logger: Logger para registrar proceso
    
    Returns:
        Tupla (ios_db_path, chatstorage_original_path) si tiene éxito, None si falla
    """
    print_step(4, "iOS Backup Process")
    
    print("\nBefore continuing, please ensure:")
    print("  1. You have logged into WhatsApp on your iPhone")
    print("  2. 'Find My iPhone' is DISABLED")
    print("  3. You have created an UNENCRYPTED backup in iTunes/Finder")
    
    input("\nPress Enter to continue...")
    
    # Crear gestor de backup iOS
    ios_mgr = IOSBackupManager()
    
    try:
        # Extraer ChatStorage.sqlite
        result = ios_mgr.extract_chatstorage()
        if not result:
            logger.error("Failed to extract iOS ChatStorage")
            return None
        
        ios_db, chatstorage_path = result
        
        print(f"\n[OK] iOS database extracted")
        print(f"[OK] Saved to: {ios_db}")
        
        return ios_db, chatstorage_path, ios_mgr
        
    except Exception as e:
        logger.error(f"iOS backup process failed: {e}")
        return None


def migration_process(android_db, ios_db, logger):
    """
    Ejecuta el proceso de migración de datos.
    
    Args:
        android_db: Ruta de la base de datos Android
        ios_db: Ruta de la base de datos iOS
        logger: Logger para registrar proceso
    
    Returns:
        Ruta del archivo out.db generado, None si falla
    """
    print_step(5, "Data Migration")
    
    # Solicitar número de teléfono
    print("\nPlease enter your phone number with country code")
    print("Example: 573001234567 (for Colombia)")
    uid = input("Phone number: ").strip()
    
    if not uid:
        logger.error("Phone number is required")
        print("[ERROR] Phone number cannot be empty")
        return None
    
    logger.info(f"Phone number provided: {uid}")
    
    try:
        # Crear migrador
        migrator = WhatsAppMigrator(android_db, ios_db, uid)
        
        # Ejecutar migración
        output_db = 'out/out.db'
        stats = migrator.run_migration(output_db)
        
        print("\n" + "="*80)
        print("MIGRATION STATISTICS")
        print("="*80)
        print(f"Android messages:      {stats['android_messages']:,}")
        print(f"iOS messages (before): {stats['ios_messages_before']:,}")
        print(f"Messages migrated:     {stats['migrated']:,}")
        print(f"Duplicates skipped:    {stats['duplicates']:,}")
        print(f"iOS messages (after):  {stats['ios_messages_after']:,}")
        print("="*80)
        
        return output_db
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        return None


def update_ios_backup(output_db, ios_mgr, logger):
    """
    Actualiza el backup de iTunes con la base de datos migrada.
    
    Args:
        output_db: Ruta de la base de datos migrada
        ios_mgr: Gestor de backups iOS
        logger: Logger para registrar proceso
    
    Returns:
        True si la actualización fue exitosa
    """
    print_step(6, "Update iTunes Backup")
    
    print("\nThis step will modify your iTunes backup with the migrated data.")
    print("A safety backup will be created before overwriting.")
    
    if not confirm_action("\nDo you want to update the iTunes backup?", default=True):
        logger.info("User chose not to update iTunes backup")
        print(f"\n[INFO] Migrated database saved at: {output_db}")
        print("You can manually replace ChatStorage.sqlite in your iTunes backup.")
        return False
    
    try:
        success = ios_mgr.update_backup(output_db, backup_safety=True)
        
        if success:
            print("\n" + "="*80)
            print("MIGRATION COMPLETE!")
            print("="*80)
            print("\nFinal Steps:")
            print("  1. Connect your iPhone to iTunes/Finder")
            print("  2. Restore from the updated backup")
            print("  3. Open WhatsApp on your iPhone")
            print("  4. Verify that all chats from Android are present")
            print("\nNOTE: If you experience issues:")
            print("  - Backup WhatsApp to iCloud")
            print("  - Reinstall WhatsApp")
            print("  - Restore from iCloud")
            print("="*80)
            
            return True
        else:
            logger.error("Failed to update iTunes backup")
            return False
            
    except Exception as e:
        logger.error(f"Error updating iTunes backup: {e}")
        return False


def cleanup(logger):
    """
    Limpia archivos temporales.
    
    Args:
        logger: Logger para registrar proceso
    """
    try:
        if os.path.exists('out'):
            clean_directory('out', logger)
            print("\n[OK] Temporary files cleaned")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


def main():
    """Función principal."""
    # Setup logging
    logger = setup_logging()
    
    print("="*80)
    print("WhatsApp Android → iOS Migration Tool v1.0.0")
    print("="*80)
    print()
    
    logger.info("="*80)
    logger.info("Migration process started")
    logger.info("="*80)
    
    try:
        # 1. Validar dependencias
        validate_dependencies(logger)
        
        # 2. Seleccionar tipo de WhatsApp
        whatsapp_type = select_whatsapp_type()
        logger.info(f"WhatsApp type selected: {whatsapp_type}")
        
        # 3. Backup de Android
        android_db = android_backup_process(whatsapp_type, logger)
        if not android_db:
            logger.error("Android backup process failed")
            sys.exit(1)
        
        # 4. Backup de iOS
        ios_result = ios_backup_process(logger)
        if not ios_result:
            logger.error("iOS backup process failed")
            sys.exit(1)
        
        ios_db, chatstorage_path, ios_mgr = ios_result
        
        # 5. Migración
        output_db = migration_process(android_db, ios_db, logger)
        if not output_db:
            logger.error("Migration process failed")
            sys.exit(1)
        
        # 6. Actualizar backup de iOS
        update_ios_backup(output_db, ios_mgr, logger)
        
        # 7. Cleanup (opcional)
        if confirm_action("\nDo you want to delete temporary files?", default=False):
            cleanup(logger)
        else:
            print(f"\n[INFO] Temporary files kept in: out/")
        
        logger.info("Migration process completed successfully")
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print("\n\n[CANCELLED] Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
