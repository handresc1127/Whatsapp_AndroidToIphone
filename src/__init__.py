"""
WhatsApp Android to iOS Migration Tool

Herramienta para migrar chats de WhatsApp/WhatsApp Business desde Android hacia iOS.
"""

__version__ = '1.0.0'
__author__ = 'Henry.Correa'
__description__ = 'WhatsApp Android to iOS Migration Tool'

# Exportar clases principales
from .android_backup import AndroidBackupManager
from .ios_backup import IOSBackupManager
from .migrate import WhatsAppMigrator

__all__ = [
    'AndroidBackupManager',
    'IOSBackupManager',
    'WhatsAppMigrator',
]
