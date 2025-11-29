"""
Tests para migrate.py

Suite de tests unitarios para WhatsAppMigrator y conversión de timestamps.
"""

import unittest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.migrate import WhatsAppMigrator, TIMESTAMP_OFFSET


class TestTimestampConversion(unittest.TestCase):
    """Tests para conversión de timestamps Android → iOS."""
    
    def setUp(self):
        """Setup para cada test."""
        # Crear DBs temporales dummy
        self.android_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.ios_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        
        # Cerrar archivos para evitar PermissionError en Windows
        self.android_db.close()
        self.ios_db.close()
        
        # Crear migrador
        self.migrator = WhatsAppMigrator(
            self.android_db.name,
            self.ios_db.name,
            '1234567890'
        )
    
    def tearDown(self):
        """Cleanup después de cada test."""
        try:
            if os.path.exists(self.android_db.name):
                os.unlink(self.android_db.name)
        except PermissionError:
            pass  # Ignorar en Windows si archivo está en uso
        
        try:
            if os.path.exists(self.ios_db.name):
                os.unlink(self.ios_db.name)
        except PermissionError:
            pass  # Ignorar en Windows si archivo está en uso
    
    def test_timestamp_conversion_known_value(self):
        """Test conversión con valor conocido."""
        # Test caso: 2023-11-15 00:00:00 UTC
        # Unix timestamp: 1700000000000 ms
        # Apple timestamp: 721692800.0 s
        android_ms = 1700000000000
        expected_ios = 721692800.0
        
        result = self.migrator.convert_timestamp(android_ms)
        
        # Permitir diferencia de 1 segundo por redondeo
        self.assertAlmostEqual(result, expected_ios, places=1)
    
    def test_timestamp_conversion_null(self):
        """Test conversión con timestamp null."""
        result = self.migrator.convert_timestamp(None)
        
        # Debe devolver timestamp actual (> 0)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
    
    def test_timestamp_conversion_zero(self):
        """Test conversión con timestamp en cero."""
        result = self.migrator.convert_timestamp(0)
        
        # Debe devolver timestamp actual
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
    
    def test_timestamp_conversion_out_of_range_high(self):
        """Test conversión con timestamp fuera de rango (muy alto)."""
        # Timestamp muy en el futuro (año 2100)
        android_ms = 4102444800000  # 2100-01-01
        
        result = self.migrator.convert_timestamp(android_ms)
        
        # Debe devolver timestamp actual como fallback
        self.assertIsInstance(result, float)
        # Debe estar en rango razonable (no en 2100)
        self.assertLess(result, 2000000000)  # Antes de 2064
    
    def test_timestamp_conversion_out_of_range_low(self):
        """Test conversión con timestamp fuera de rango (muy bajo)."""
        # Timestamp antes de 2001 (negativo en Apple epoch)
        android_ms = 946684800000  # 2000-01-01
        
        result = self.migrator.convert_timestamp(android_ms)
        
        # Debe devolver timestamp actual como fallback
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
    
    def test_timestamp_offset_constant(self):
        """Test que la constante TIMESTAMP_OFFSET es correcta."""
        # Offset debe ser 978307200 segundos
        self.assertEqual(TIMESTAMP_OFFSET, 978307200)
        
        # Verificar que corresponde a diferencia entre 1970 y 2001
        # 31 años * 365.25 días/año * 86400 seg/día ≈ 978307200
        expected = 31 * 365.25 * 86400
        self.assertAlmostEqual(TIMESTAMP_OFFSET, expected, delta=86400)  # ±1 día


class TestWhatsAppMigrator(unittest.TestCase):
    """Tests para WhatsAppMigrator class."""
    
    def test_migrator_initialization(self):
        """Test inicialización de WhatsAppMigrator."""
        android_db = 'test_android.db'
        ios_db = 'test_ios.db'
        phone = '573001234567'
        
        migrator = WhatsAppMigrator(android_db, ios_db, phone)
        
        self.assertEqual(str(migrator.android_db_path), android_db)
        self.assertEqual(str(migrator.ios_db_path), ios_db)
        self.assertEqual(migrator.phone_number, phone)
        self.assertIsNone(migrator.schema_version)
    
    def test_detect_schema_version_modern(self):
        """Test detección de esquema moderno."""
        # Crear DB temporal con esquema moderno
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            android_db = f.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            ios_db = f.name
        
        try:
            # Crear tablas modernas
            conn = sqlite3.connect(android_db)
            conn.execute("CREATE TABLE messages (_id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE message_quoted (_id INTEGER PRIMARY KEY)")  # Indicador moderno
            conn.commit()
            conn.close()
            
            # Crear iOS DB básico
            conn = sqlite3.connect(ios_db)
            conn.execute("CREATE TABLE ZWAMESSAGE (Z_PK INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            
            # Crear migrador y conectar
            migrator = WhatsAppMigrator(android_db, ios_db, '1234567890')
            migrator.connect_databases()
            
            # Detectar esquema
            schema = migrator.detect_schema_version()
            
            self.assertEqual(schema, 'modern')
            
            # Cerrar conexiones
            migrator.android_conn.close()
            migrator.ios_conn.close()
            
        finally:
            if os.path.exists(android_db):
                os.unlink(android_db)
            if os.path.exists(ios_db):
                os.unlink(ios_db)
    
    def test_detect_schema_version_legacy(self):
        """Test detección de esquema legacy."""
        # Crear DB temporal con esquema legacy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            android_db = f.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            ios_db = f.name
        
        try:
            # Crear solo tablas básicas (sin modernas)
            conn = sqlite3.connect(android_db)
            conn.execute("CREATE TABLE messages (_id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE chat (_id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            
            # Crear iOS DB básico
            conn = sqlite3.connect(ios_db)
            conn.execute("CREATE TABLE ZWAMESSAGE (Z_PK INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            
            # Crear migrador y conectar
            migrator = WhatsAppMigrator(android_db, ios_db, '1234567890')
            migrator.connect_databases()
            
            # Detectar esquema
            schema = migrator.detect_schema_version()
            
            self.assertEqual(schema, 'legacy')
            
            # Cerrar conexiones
            migrator.android_conn.close()
            migrator.ios_conn.close()
            
        finally:
            if os.path.exists(android_db):
                os.unlink(android_db)
            if os.path.exists(ios_db):
                os.unlink(ios_db)


class TestTimestampEdgeCases(unittest.TestCase):
    """Tests para casos edge de timestamps."""
    
    def setUp(self):
        """Setup para cada test."""
        android_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        ios_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        
        # Cerrar archivos inmediatamente para evitar PermissionError
        android_db.close()
        ios_db.close()
        
        self.migrator = WhatsAppMigrator(
            android_db.name,
            ios_db.name,
            '1234567890'
        )
        
        self.android_db = android_db
        self.ios_db = ios_db
    
    def tearDown(self):
        """Cleanup."""
        try:
            if os.path.exists(self.android_db.name):
                os.unlink(self.android_db.name)
        except (PermissionError, FileNotFoundError):
            pass
        
        try:
            if os.path.exists(self.ios_db.name):
                os.unlink(self.ios_db.name)
        except (PermissionError, FileNotFoundError):
            pass
    
    def test_timestamp_epoch_start(self):
        """Test timestamp en inicio de época Unix (1970-01-01)."""
        android_ms = 0
        result = self.migrator.convert_timestamp(android_ms)
        
        # 0 debe tratarse como caso especial (timestamp actual)
        self.assertGreater(result, 0)
    
    def test_timestamp_apple_epoch_start(self):
        """Test timestamp en inicio de época Apple (2001-01-01)."""
        # 2001-01-01 00:00:00 UTC = 978307200000 ms desde Unix epoch
        android_ms = TIMESTAMP_OFFSET * 1000
        result = self.migrator.convert_timestamp(android_ms)
        
        # Debe resultar en 0 (inicio Apple epoch)
        self.assertAlmostEqual(result, 0.0, places=1)
    
    def test_timestamp_current_time(self):
        """Test timestamp de tiempo actual."""
        import time
        
        # Timestamp actual en ms
        android_ms = int(time.time() * 1000)
        result = self.migrator.convert_timestamp(android_ms)
        
        # Resultado debe ser positivo y razonable
        self.assertGreater(result, 0)
        # Debe ser menor que 60 años desde 2001 (aproximadamente 2061)
        self.assertLess(result, 60 * 365.25 * 86400)
    
    def test_timestamp_negative_android(self):
        """Test timestamp Android negativo (antes de 1970)."""
        android_ms = -1000000000  # Antes de 1970
        result = self.migrator.convert_timestamp(android_ms)
        
        # Debe manejar gracefully (usar timestamp actual)
        self.assertIsInstance(result, float)


if __name__ == '__main__':
    # Ejecutar tests con verbosidad
    unittest.main(verbosity=2)
