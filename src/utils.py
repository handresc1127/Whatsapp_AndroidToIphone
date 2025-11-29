"""
WhatsApp Android to iOS Migration Tool

Módulo de utilidades comunes compartidas entre todos los componentes.
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(log_file: str = 'logs/migration.log', level: int = logging.INFO) -> logging.Logger:
    """
    Configura logging a archivo y consola.
    
    Args:
        log_file: Ruta del archivo de log
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger configurado
    """
    # Crear directorio de logs si no existe
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Configurar logger root
    logger = logging.getLogger('whatsapp_migration')
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def validate_file_exists(filepath: str, description: str, logger: logging.Logger) -> None:
    """
    Valida que un archivo exista, termina con exit(1) si no.
    
    Args:
        filepath: Ruta del archivo a validar
        description: Descripción del archivo para mensaje de error
        logger: Logger para registrar errores
    """
    if not os.path.exists(filepath):
        logger.error(f"Missing required file: {description}")
        logger.error(f"Expected path: {filepath}")
        print(f"\n[ERROR] Missing: {filepath}")
        print(f"Description: {description}")
        sys.exit(1)
    logger.debug(f"Validated: {filepath}")


def validate_directory_exists(dirpath: str, description: str, logger: logging.Logger) -> None:
    """
    Valida que un directorio exista, termina con exit si no.
    
    Args:
        dirpath: Ruta del directorio a validar
        description: Descripción para mensaje de error
        logger: Logger para registrar errores
    """
    if not os.path.isdir(dirpath):
        logger.error(f"Missing required directory: {description}")
        logger.error(f"Expected path: {dirpath}")
        print(f"\n[ERROR] Directory not found: {dirpath}")
        print(f"Description: {description}")
        sys.exit(1)
    logger.debug(f"Validated directory: {dirpath}")


def create_backup(source: str, backup_dir: str = 'backups') -> Optional[str]:
    """
    Crea backup con timestamp de un archivo.
    
    Args:
        source: Ruta del archivo a respaldar
        backup_dir: Directorio donde guardar backup
    
    Returns:
        Ruta del archivo de backup creado, None si falla
    """
    logger = logging.getLogger('whatsapp_migration')
    
    if not os.path.exists(source):
        logger.warning(f"Cannot backup non-existent file: {source}")
        return None
    
    try:
        # Crear directorio de backups
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = Path(source).name
        backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
        
        # Copiar archivo
        shutil.copy2(source, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to create backup of {source}: {e}")
        return None


def run_adb_command(command: list, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Ejecuta comando ADB y valida return code.
    
    Args:
        command: Lista con comando ADB (ej: ['bin/adb.exe', 'devices'])
        check: Si True, lanza excepción si comando falla
        timeout: Timeout en segundos
    
    Returns:
        CompletedProcess con stdout, stderr y returncode
    
    Raises:
        RuntimeError: Si comando falla y check=True
    """
    logger = logging.getLogger('whatsapp_migration')
    
    try:
        logger.debug(f"Running ADB command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            logger.error(f"ADB command failed (exit {result.returncode})")
            logger.error(f"Command: {' '.join(command)}")
            logger.error(f"stderr: {result.stderr}")
            
            if check:
                raise RuntimeError(f"ADB command failed: {result.stderr}")
        
        logger.debug(f"ADB command successful (exit {result.returncode})")
        return result
        
    except subprocess.TimeoutExpired:
        logger.error(f"ADB command timed out after {timeout}s")
        if check:
            raise RuntimeError(f"ADB command timed out after {timeout}s")
        return subprocess.CompletedProcess(command, -1, '', f'Timeout after {timeout}s')
    except Exception as e:
        logger.error(f"ADB command exception: {e}")
        if check:
            raise
        return subprocess.CompletedProcess(command, -1, '', str(e))


def ensure_directory(dirpath: str) -> None:
    """
    Asegura que un directorio exista, créalo si no.
    
    Args:
        dirpath: Ruta del directorio
    """
    Path(dirpath).mkdir(parents=True, exist_ok=True)


def clean_directory(dirpath: str, logger: logging.Logger) -> None:
    """
    Elimina un directorio y todo su contenido de forma segura.
    
    Args:
        dirpath: Ruta del directorio a eliminar
        logger: Logger para registrar operación
    """
    if not os.path.exists(dirpath):
        logger.debug(f"Directory does not exist, nothing to clean: {dirpath}")
        return
    
    try:
        shutil.rmtree(dirpath)
        logger.info(f"Cleaned directory: {dirpath}")
    except Exception as e:
        logger.error(f"Failed to clean directory {dirpath}: {e}")
        raise


def validate_sqlite_database(db_path: str, expected_tables: list = None) -> bool:
    """
    Valida que un archivo sea una base de datos SQLite válida.
    
    Args:
        db_path: Ruta de la base de datos
        expected_tables: Lista opcional de tablas que deben existir
    
    Returns:
        True si la base de datos es válida
    """
    import sqlite3
    logger = logging.getLogger('whatsapp_migration')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test query básica
        cursor.execute("SELECT 1")
        
        # Validar tablas si se especificaron
        if expected_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            for table in expected_tables:
                if table not in existing_tables:
                    logger.error(f"Expected table '{table}' not found in {db_path}")
                    conn.close()
                    return False
        
        conn.close()
        logger.debug(f"SQLite database validated: {db_path}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Invalid SQLite database {db_path}: {e}")
        return False


def print_separator(char: str = '=', length: int = 80) -> None:
    """Imprime una línea separadora."""
    print(char * length)


def print_step(step_number: int, description: str) -> None:
    """Imprime un paso numerado del proceso."""
    print(f"\n{'='*80}")
    print(f"STEP {step_number}: {description}")
    print('='*80)


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Solicita confirmación del usuario.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto si usuario presiona Enter
    
    Returns:
        True si usuario confirma, False si no
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(prompt + suffix).strip().upper()
    
    if not response:
        return default
    
    return response in ['Y', 'YES', 'SI', 'S']
