"""
WhatsApp Android to iOS Migration Tool

Módulo central de migración de bases de datos SQLite.
Convierte esquema Android (msgstore.db) a esquema iOS (ChatStorage.sqlite).
"""

import argparse
import logging
import os
import sqlite3
import sys
from typing import Dict, List, Tuple, Optional

# Constante de conversión de timestamps
# Unix Epoch (1970-01-01) a Apple Epoch (2001-01-01)
TIMESTAMP_OFFSET = 978307200  # segundos entre 1970 y 2001


class WhatsAppMigrator:
    """Migrador de bases de datos WhatsApp Android → iOS."""
    
    def __init__(self, android_db_path: str, ios_db_path: str, phone_number: str):
        """
        Inicializa el migrador.
        
        Args:
            android_db_path: Ruta a msgstore.db (Android)
            ios_db_path: Ruta a ChatStorage.sqlite (iOS)
            phone_number: Número de teléfono con código de país
        """
        self.android_db_path = android_db_path
        self.ios_db_path = ios_db_path
        self.phone_number = phone_number
        self.logger = logging.getLogger('whatsapp_migration.migrate')
        
        self.android_conn: Optional[sqlite3.Connection] = None
        self.ios_conn: Optional[sqlite3.Connection] = None
        self.output_conn: Optional[sqlite3.Connection] = None
        self.schema_version: Optional[str] = None
    
    def detect_schema_version(self) -> str:
        """
        Detecta la versión del esquema de la base de datos Android.
        
        Returns:
            'legacy' para WhatsApp 2.11.x, 'modern' para 2.20.x+
        """
        try:
            cursor = self.android_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            # Tablas que solo existen en versiones modernas
            modern_indicators = [
                'message_quoted',
                'message_ephemeral',
                'message_poll',
                'message_view_once'
            ]
            
            for indicator in modern_indicators:
                if indicator in tables:
                    self.logger.info(f"Detected modern schema (found table: {indicator})")
                    return 'modern'
            
            self.logger.info("Detected legacy schema")
            return 'legacy'
        except Exception as e:
            self.logger.error(f"Error detecting schema version: {e}")
            # Default to modern for safety
            return 'modern'
    
    def connect_databases(self) -> None:
        """Conecta a las bases de datos Android e iOS."""
        try:
            self.logger.info(f"Connecting to Android DB: {self.android_db_path}")
            self.android_conn = sqlite3.connect(self.android_db_path)
            self.android_conn.row_factory = sqlite3.Row
            
            self.logger.info(f"Connecting to iOS DB: {self.ios_db_path}")
            self.ios_conn = sqlite3.connect(self.ios_db_path)
            self.ios_conn.row_factory = sqlite3.Row
            
            self.logger.info("Database connections successful")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise RuntimeError(f"Failed to connect to databases: {e}")
    
    def analyze_android_schema(self) -> Dict[str, List[str]]:
        """
        Analiza el esquema de la base de datos Android.
        
        Returns:
            Diccionario con nombres de tablas y sus columnas
        """
        schema = {}
        try:
            cursor = self.android_conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.logger.info(f"Android DB tables found: {', '.join(tables)}")
            
            # Obtener columnas de cada tabla
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema[table] = columns
                self.logger.debug(f"Table {table}: {len(columns)} columns")
            
            return schema
            
        except sqlite3.Error as e:
            self.logger.error(f"Error analyzing Android schema: {e}")
            raise
    
    def analyze_ios_schema(self) -> Dict[str, List[str]]:
        """
        Analiza el esquema de la base de datos iOS.
        
        Returns:
            Diccionario con nombres de tablas y sus columnas
        """
        schema = {}
        try:
            cursor = self.ios_conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'Z_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.logger.info(f"iOS DB tables found: {', '.join(tables)}")
            
            # Obtener columnas de cada tabla
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema[table] = columns
                self.logger.debug(f"Table {table}: {len(columns)} columns")
            
            return schema
            
        except sqlite3.Error as e:
            self.logger.error(f"Error analyzing iOS schema: {e}")
            raise
    
    def convert_timestamp(self, android_timestamp: int) -> float:
        """
        Convierte timestamp de Android (Unix ms) a iOS (Apple sec).
        
        Android: Milisegundos desde 1970-01-01 00:00:00 UTC
        iOS: Segundos desde 2001-01-01 00:00:00 UTC
        
        Args:
            android_timestamp: Timestamp en formato Android (milisegundos)
        
        Returns:
            Timestamp en formato iOS (segundos desde 2001)
        """
        if android_timestamp is None or android_timestamp == 0:
            # Usar timestamp actual como fallback
            import time
            return time.time() - TIMESTAMP_OFFSET
        
        # Convertir milisegundos a segundos
        unix_seconds = android_timestamp / 1000.0
        
        # Restar offset para convertir a Apple Epoch
        apple_seconds = unix_seconds - TIMESTAMP_OFFSET
        
        # Validar rango (2001-01-01 a 2060-01-01)
        MIN_TIMESTAMP = 0
        MAX_TIMESTAMP = 1893456000
        
        if not (MIN_TIMESTAMP <= apple_seconds <= MAX_TIMESTAMP):
            self.logger.warning(f"Timestamp out of range: {apple_seconds}, using current time")
            import time
            return time.time() - TIMESTAMP_OFFSET
        
        return apple_seconds
    
    def get_android_messages_count(self) -> int:
        """Obtiene el conteo total de mensajes en Android DB."""
        try:
            cursor = self.android_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            self.logger.info(f"Android messages count: {count}")
            return count
        except sqlite3.Error as e:
            self.logger.error(f"Error counting Android messages: {e}")
            return 0
    
    def get_ios_messages_count(self) -> int:
        """Obtiene el conteo total de mensajes en iOS DB."""
        try:
            cursor = self.ios_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ZWAMESSAGE")
            count = cursor.fetchone()[0]
            self.logger.info(f"iOS messages count: {count}")
            return count
        except sqlite3.Error as e:
            self.logger.error(f"Error counting iOS messages: {e}")
            return 0
    
    def copy_ios_schema_to_output(self, output_path: str) -> None:
        """
        Copia el esquema completo de iOS a la base de datos de salida.
        
        Args:
            output_path: Ruta de la base de datos de salida
        """
        try:
            self.logger.info(f"Creating output database: {output_path}")
            
            # Si el archivo existe, eliminarlo
            if os.path.exists(output_path):
                os.remove(output_path)
                self.logger.debug(f"Removed existing output file")
            
            # Copiar archivo completo de iOS
            import shutil
            shutil.copy2(self.ios_db_path, output_path)
            
            self.logger.info("iOS database copied to output successfully")
            
            # Conectar a la base de datos de salida
            self.output_conn = sqlite3.connect(output_path)
            self.output_conn.row_factory = sqlite3.Row
            
        except Exception as e:
            self.logger.error(f"Error copying iOS schema: {e}")
            raise
    
    def _migrate_modern_schema(self) -> Tuple[int, int]:
        """
        Migra mensajes desde esquema moderno (WhatsApp 2.20.x+).
        
        Returns:
            Tupla (mensajes_migrados, duplicados_omitidos)
        """
        migrated = 0
        duplicates = 0
        
        try:
            self.logger.info("Starting modern schema migration...")
            
            # Obtener siguiente Z_PK disponible en iOS
            cursor = self.output_conn.execute("SELECT IFNULL(MAX(Z_PK), 0) FROM ZWAMESSAGE")
            next_pk = cursor.fetchone()[0] + 1
            
            # Leer mensajes de Android (solo campos base para compatibilidad)
            android_cursor = self.android_conn.execute("""
                SELECT 
                    m._id,
                    m.key_remote_jid,
                    m.key_from_me,
                    m.data,
                    m.timestamp,
                    m.status,
                    COALESCE(m.media_wa_type, 0) as media_type,
                    COALESCE(m.starred, 0) as starred
                FROM messages m
                WHERE m.data IS NOT NULL
                ORDER BY m.timestamp ASC
            """)
            
            total_messages = 0
            for row in android_cursor:
                total_messages += 1
            
            self.logger.info(f"Found {total_messages} messages to migrate")
            
            # Reiniciar cursor para migración
            android_cursor = self.android_conn.execute("""
                SELECT 
                    m._id,
                    m.key_remote_jid,
                    m.key_from_me,
                    m.data,
                    m.timestamp,
                    m.status,
                    COALESCE(m.media_wa_type, 0) as media_type,
                    COALESCE(m.starred, 0) as starred
                FROM messages m
                WHERE m.data IS NOT NULL
                ORDER BY m.timestamp ASC
            """)
            
            for row in android_cursor:
                android_id, remote_jid, from_me, text, timestamp, status, media_type, starred = row
                
                # Convertir timestamp
                ios_timestamp = self.convert_timestamp(timestamp)
                
                # Determinar JIDs según dirección
                if from_me:
                    to_jid = remote_jid
                    from_jid = self.phone_number
                else:
                    to_jid = None
                    from_jid = remote_jid
                
                # Mapear tipo de mensaje (simplificado)
                ios_message_type = 0 if media_type == 0 else media_type
                
                # Mapear status (simplificado, iOS usa 0-5)
                ios_status = min(status if status else 0, 5)
                
                # Insertar en iOS
                self.output_conn.execute("""
                    INSERT INTO ZWAMESSAGE (
                        Z_PK, Z_ENT, Z_OPT,
                        ZISFROMME, ZMESSAGESTATUS, ZMESSAGETYPE, ZISSTARRED,
                        ZTEXT, ZMESSAGEDATE, ZSENTDATE, ZRECEIVEDDATE,
                        ZTOJID, ZFROMJID
                    ) VALUES (?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    next_pk,
                    from_me,
                    ios_status,
                    ios_message_type,
                    starred,
                    text,
                    ios_timestamp,
                    ios_timestamp,
                    ios_timestamp,
                    to_jid,
                    from_jid
                ))
                
                next_pk += 1
                migrated += 1
                
                # Progress logging cada 1000 mensajes
                if migrated % 1000 == 0:
                    self.logger.info(f"Migrated {migrated}/{total_messages} messages...")
                    print(f"\rProgress: {migrated}/{total_messages} messages migrated", end='', flush=True)
            
            if migrated > 0:
                print()  # Newline después de progress
            
            self.output_conn.commit()
            self.logger.info(f"Modern schema migration completed: {migrated} messages")
            
            return migrated, duplicates
            
        except Exception as e:
            self.logger.error(f"Error in modern schema migration: {e}")
            self.output_conn.rollback()
            raise
    
    def _migrate_legacy_schema(self) -> Tuple[int, int]:
        """
        Migra mensajes desde esquema legacy (WhatsApp 2.11.x).
        
        Returns:
            Tupla (mensajes_migrados, duplicados_omitidos)
        """
        self.logger.warning("Legacy schema migration not yet implemented")
        raise NotImplementedError(
            "Legacy schema (WhatsApp 2.11.x) migration is not yet implemented. "
            "Please use a modern version of WhatsApp or request this feature."
        )
    
    def migrate_messages(self) -> Tuple[int, int]:
        """
        Migra mensajes de Android a iOS.
        
        Esta es una implementación simplificada que copia datos básicos.
        En producción, se requiere mapeo completo de todos los campos.
        
        Returns:
            Tupla (mensajes_migrados, duplicados_omitidos)
        """
        migrated = 0
        duplicates = 0
        
        try:
            self.logger.info("Starting message migration...")
            
            # Obtener mensajes de Android
            android_cursor = self.android_conn.cursor()
            android_cursor.execute("""
                SELECT 
                    m._id,
                    m.key_remote_jid,
                    m.key_from_me,
                    m.key_id,
                    m.status,
                    m.data,
                    m.timestamp,
                    m.media_url,
                    m.media_mime_type,
                    m.media_size
                FROM messages m
                ORDER BY m.timestamp ASC
            """)
            
            android_messages = android_cursor.fetchall()
            total_messages = len(android_messages)
            self.logger.info(f"Found {total_messages} messages in Android DB")
            
            # Obtener contador actual de Z_PK en iOS
            ios_cursor = self.output_conn.cursor()
            ios_cursor.execute("SELECT MAX(Z_PK) FROM ZWAMESSAGE")
            max_pk = ios_cursor.fetchone()[0] or 0
            next_pk = max_pk + 1
            
            self.logger.info(f"Starting Z_PK from: {next_pk}")
            
            # Insertar mensajes
            for idx, msg in enumerate(android_messages, 1):
                try:
                    # Convertir timestamp
                    ios_timestamp = self.convert_timestamp(msg['timestamp'])
                    
                    # Verificar si el mensaje ya existe (duplicado)
                    ios_cursor.execute("""
                        SELECT COUNT(*) FROM ZWAMESSAGE 
                        WHERE ZMESSAGEDATE = ? AND ZTEXT = ?
                    """, (ios_timestamp, msg['data']))
                    
                    if ios_cursor.fetchone()[0] > 0:
                        duplicates += 1
                        continue
                    
                    # Insertar mensaje en formato iOS
                    # NOTA: Esta es una versión SIMPLIFICADA
                    # En producción se requieren más campos y validaciones
                    ios_cursor.execute("""
                        INSERT INTO ZWAMESSAGE (
                            Z_PK, Z_ENT, Z_OPT,
                            ZMESSAGEDATE, ZTEXT, ZISFROMME,
                            ZGROUPEVENTTYPE, ZMESSAGETYPE
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        next_pk,
                        2,  # Z_ENT para mensajes
                        1,  # Z_OPT (versión)
                        ios_timestamp,
                        msg['data'],
                        1 if msg['key_from_me'] else 0,
                        0,  # No es evento de grupo
                        0   # Mensaje de texto
                    ))
                    
                    migrated += 1
                    next_pk += 1
                    
                    # Log de progreso cada 100 mensajes
                    if idx % 100 == 0:
                        self.logger.info(f"Progress: {idx}/{total_messages} messages processed")
                
                except sqlite3.Error as e:
                    self.logger.warning(f"Failed to migrate message {msg['_id']}: {e}")
                    continue
            
            self.output_conn.commit()
            self.logger.info(f"Migration complete: {migrated} migrated, {duplicates} duplicates skipped")
            
            return migrated, duplicates
            
        except Exception as e:
            self.logger.error(f"Error during message migration: {e}")
            if self.output_conn:
                self.output_conn.rollback()
            raise
    
    def run_migration(self, output_path: str) -> Dict[str, int]:
        """
        Ejecuta el proceso completo de migración.
        
        Args:
            output_path: Ruta de la base de datos de salida
        
        Returns:
            Diccionario con estadísticas de la migración
            
        Raises:
            NotImplementedError: Si el esquema detectado no está soportado
        """
        stats = {
            'android_messages': 0,
            'ios_messages_before': 0,
            'ios_messages_after': 0,
            'migrated': 0,
            'duplicates': 0,
            'contacts': 0,
            'groups': 0
        }
        
        try:
            # Conectar a bases de datos
            self.connect_databases()
            
            # Detectar versión de esquema
            self.schema_version = self.detect_schema_version()
            self.logger.info(f"Detected schema version: {self.schema_version}")
            print(f"\n[INFO] Database schema: {self.schema_version}")
            
            # Analizar esquemas
            self.logger.info("Analyzing database schemas...")
            android_schema = self.analyze_android_schema()
            ios_schema = self.analyze_ios_schema()
            
            # Conteo inicial
            stats['android_messages'] = self.get_android_messages_count()
            stats['ios_messages_before'] = self.get_ios_messages_count()
            
            # Copiar esquema iOS a output
            self.copy_ios_schema_to_output(output_path)
            
            # Migrar mensajes según esquema
            print(f"\n[INFO] Starting migration with {self.schema_version} schema...")
            if self.schema_version == 'modern':
                migrated, duplicates = self._migrate_modern_schema()
            else:
                migrated, duplicates = self._migrate_legacy_schema()
            
            stats['migrated'] = migrated
            stats['duplicates'] = duplicates
            
            # TODO: Migrar contactos y grupos (futuro)
            stats['contacts'] = 0
            stats['groups'] = 0
            
            # Conteo final
            cursor = self.output_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ZWAMESSAGE")
            stats['ios_messages_after'] = cursor.fetchone()[0]
            
            self.logger.info("Migration summary:")
            self.logger.info(f"  Android messages: {stats['android_messages']}")
            self.logger.info(f"  iOS messages (before): {stats['ios_messages_before']}")
            self.logger.info(f"  Migrated: {stats['migrated']}")
            self.logger.info(f"  Duplicates skipped: {stats['duplicates']}")
            self.logger.info(f"  iOS messages (after): {stats['ios_messages_after']}")
            
            return stats
            
        finally:
            # Cerrar conexiones
            if self.android_conn:
                self.android_conn.close()
            if self.ios_conn:
                self.ios_conn.close()
            if self.output_conn:
                self.output_conn.close()


def main():
    """Función principal para ejecución desde CLI."""
    parser = argparse.ArgumentParser(
        description='Migrate WhatsApp chats from Android to iOS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py -adb out/android.db -idb out/ios.db -u 573001234567
  python migrate.py -adb out/android.db -idb out/ios.db -u 573001234567 -o out/output.db
        """
    )
    
    parser.add_argument(
        '-adb', '--android-db',
        required=True,
        help='Path to Android database (msgstore.db)'
    )
    
    parser.add_argument(
        '-idb', '--ios-db',
        required=True,
        help='Path to iOS database (ChatStorage.sqlite)'
    )
    
    parser.add_argument(
        '-u', '--uid',
        required=True,
        help='Phone number with country code (e.g., 573001234567)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='out/out.db',
        help='Output database path (default: out/out.db)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    from utils import setup_logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(level=log_level)
    
    logger.info("="*80)
    logger.info("WhatsApp Android → iOS Migration Tool")
    logger.info("="*80)
    
    # Validar archivos de entrada
    if not os.path.exists(args.android_db):
        logger.error(f"Android database not found: {args.android_db}")
        sys.exit(1)
    
    if not os.path.exists(args.ios_db):
        logger.error(f"iOS database not found: {args.ios_db}")
        sys.exit(1)
    
    # Crear migrador y ejecutar
    try:
        migrator = WhatsAppMigrator(args.android_db, args.ios_db, args.uid)
        stats = migrator.run_migration(args.output)
        
        print("\n" + "="*80)
        print("MIGRATION SUCCESSFUL")
        print("="*80)
        print(f"Android messages: {stats['android_messages']}")
        print(f"iOS messages (before): {stats['ios_messages_before']}")
        print(f"Messages migrated: {stats['migrated']}")
        print(f"Duplicates skipped: {stats['duplicates']}")
        print(f"iOS messages (after): {stats['ios_messages_after']}")
        print(f"\nOutput database: {args.output}")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
