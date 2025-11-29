---
date: 2025-11-28
author: Henry.Correa
status: ready
type: feature
priority: high
estimated_effort: 4-6 hours
---

# Plan: Implementación Completa del Proyecto WhatsApp Migration

## Contexto

Basándose en la investigación exhaustiva realizada en `docs/research/2025-11-28-investigacion-proyecto-migracion-whatsapp.md`, se implementará desde cero el proyecto de migración de WhatsApp Android → iOS con arquitectura modular, manejo robusto de errores, y documentación completa.

**Estado actual:**
- ✅ Script monolítico `main.py` funcional (267 líneas)
- ❌ Componente crítico `migrate.py` NO existe
- ❌ Sin manejo de errores ni logging
- ❌ Archivos `.github/` de otro proyecto (Green-POS)
- ❌ Documentación incompleta

**Objetivo:**
Crear proyecto profesional listo para producción con:
- Arquitectura modular (separación de responsabilidades)
- Manejo completo de errores y rollback
- Logging estructurado
- Documentación exhaustiva
- Script `migrate.py` implementado con mapeo de esquemas SQLite

---

## Fases de Implementación

### Fase 1: Estructura de Proyecto y Documentación

**Objetivo:** Crear estructura de directorios y archivos de documentación.

**Cambios:**

1. **Crear estructura de directorios:**
```
Whatsapp_AndroidToIphone/
├── src/                        # Código fuente
├── bin/                        # Binarios externos (ADB, DLLs)
│   └── README.md
├── apk/                        # APKs legacy
│   └── README.md
├── backups/                    # Backups de seguridad
├── logs/                       # Archivos de log
├── tests/                      # Tests unitarios
└── docs/
    ├── research/              # Ya existe
    ├── SETUP.md
    ├── USAGE.md
    └── ARCHITECTURE.md
```

2. **Crear README.md principal:**
   - Descripción del proyecto
   - Requisitos y dependencias
   - Instalación rápida
   - Links a documentación detallada

3. **Crear bin/README.md:**
   - Instrucciones para descargar ADB
   - Links a Android SDK Platform Tools
   - Checklist de archivos requeridos

4. **Crear apk/README.md:**
   - Instrucciones para obtener APKs legacy
   - Versiones recomendadas
   - Links a APKMirror
   - Advertencias legales

**Criterios de Éxito:**
- [ ] Estructura de directorios creada
- [ ] README.md completo con badges y secciones
- [ ] bin/README.md con instrucciones de descarga ADB
- [ ] apk/README.md con instrucciones de APKs legacy
- [ ] .gitignore actualizado (tmp/, out/, logs/, backups/)

---

### Fase 2: Implementación de migrate.py

**Objetivo:** Implementar el componente crítico de migración de bases de datos SQLite.

**Archivo:** `src/migrate.py`

**Funcionalidad:**

1. **Parser de argumentos CLI:**
```python
import argparse
parser = argparse.ArgumentParser(description='Migrate WhatsApp chats Android → iOS')
parser.add_argument('-adb', required=True, help='Android database path')
parser.add_argument('-idb', required=True, help='iOS database path')
parser.add_argument('-u', required=True, help='Phone number with country code')
parser.add_argument('-o', default='out/out.db', help='Output database path')
```

2. **Conexión a bases de datos con manejo de errores:**
```python
try:
    android_conn = sqlite3.connect(android_db_path)
    ios_conn = sqlite3.connect(ios_db_path)
    output_conn = sqlite3.connect(output_db_path)
except sqlite3.Error as e:
    logger.error(f"Database connection error: {e}")
    sys.exit(1)
```

3. **Mapeo de esquemas:**
   - Analizar estructura de `msgstore.db` (Android)
   - Analizar estructura de `ChatStorage.sqlite` (iOS)
   - Crear mapeo de tablas:
     * `messages` → `ZWAMESSAGE`
     * `chat` → `ZWACHATSESSION`
     * `message_media` → `ZWAMEDIAITEM`
     * `jid` → `ZWACHATSESSION.ZCONTACTJID`

4. **Conversión de timestamps:**
```python
def android_to_ios_timestamp(android_ts):
    """Convierte Unix ms (1970) a Apple sec (2001)"""
    unix_sec = android_ts / 1000
    apple_sec = unix_sec - 978307200  # Diferencia 1970-2001
    return apple_sec
```

5. **Fusión de datos:**
   - Copiar esquema completo de iOS a output
   - Insertar mensajes de Android que no existan en iOS
   - Detectar duplicados por: `(timestamp, jid, message_text)`
   - Generar nuevos IDs compatibles con Core Data (Z_PK)

6. **Logging de progreso:**
   - Total de chats procesados
   - Total de mensajes migrados
   - Duplicados detectados
   - Errores encontrados

**Criterios de Éxito:**
- [ ] Script acepta argumentos CLI correctamente
- [ ] Conecta a ambas bases de datos sin errores
- [ ] Mapea correctamente tablas Android → iOS
- [ ] Convierte timestamps correctamente (verificar con ejemplos)
- [ ] Fusiona datos sin duplicar mensajes
- [ ] Genera `out.db` válido que iTunes pueda restaurar
- [ ] Logging completo de operaciones
- [ ] Manejo de errores en cada etapa

---

### Fase 3: Módulos Especializados

**Objetivo:** Refactorizar `main.py` en módulos reutilizables.

**Archivos a crear:**

1. **src/utils.py** - Utilidades comunes:
```python
import logging
import os
from pathlib import Path

def setup_logging(log_file='logs/migration.log'):
    """Configura logging a archivo y consola"""
    
def validate_file_exists(filepath, description):
    """Valida que archivo exista, exit(1) si no"""
    
def create_backup(source, backup_dir='backups'):
    """Crea backup con timestamp de archivo"""
    
def run_adb_command(command, check=True):
    """Ejecuta comando ADB y valida return code"""
```

2. **src/android_backup.py** - Lógica de backup Android:
```python
class AndroidBackupManager:
    def __init__(self, package_name, apk_path):
        self.package = package_name
        self.apk = apk_path
        
    def start_adb_server(self):
        """Inicia servidor ADB con validación"""
        
    def wait_for_device(self, timeout=30):
        """Espera dispositivo con timeout"""
        
    def uninstall_whatsapp(self, keep_data=True):
        """Desinstala WhatsApp preservando datos"""
        
    def install_legacy_apk(self):
        """Instala APK legacy con downgrade"""
        
    def create_backup(self, output_file='tmp/whatsapp.ab'):
        """Crea backup sin cifrar"""
        
    def extract_ab_to_tar(self, ab_file, tar_file):
        """Convierte .ab a .tar"""
        
    def extract_msgstore_db(self, tar_file, output_dir='out'):
        """Extrae msgstore.db del tar"""
```

3. **src/ios_backup.py** - Lógica de backup iOS:
```python
class IOSBackupManager:
    BACKUP_LOCATIONS = [
        os.getenv('APPDATA') + '\\Apple Computer\\MobileSync\\Backup',
        os.getenv('USERPROFILE') + '\\Apple\\MobileSync\\Backup',
    ]
    
    def find_backup_directory(self):
        """Busca directorio de backups de iTunes"""
        
    def select_backup(self):
        """Selecciona backup si hay múltiples"""
        
    def extract_chatstorage(self, backup_path, output_file='out/ios.db'):
        """Extrae ChatStorage.sqlite del backup"""
        
    def update_backup(self, backup_path, new_db_file):
        """Sobrescribe ChatStorage en backup con validación"""
```

4. **src/main.py** - Script principal refactorizado:
```python
from utils import setup_logging, validate_file_exists, create_backup
from android_backup import AndroidBackupManager
from ios_backup import IOSBackupManager
import migrate

def main():
    # Setup logging
    logger = setup_logging()
    
    # Validar dependencias
    validate_dependencies()
    
    # Android backup
    android_mgr = AndroidBackupManager(...)
    android_db = android_mgr.run_backup_process()
    
    # iOS backup
    ios_mgr = IOSBackupManager()
    ios_db, backup_path = ios_mgr.extract_chatstorage()
    
    # Migración
    uid = input("Enter phone number: ")
    migrate.run(android_db, ios_db, uid, output='out/out.db')
    
    # Actualizar backup iOS
    create_backup(ios_db, 'backups')  # Backup de seguridad
    ios_mgr.update_backup(backup_path, 'out/out.db')
    
    logger.info("Migration complete!")
```

**Criterios de Éxito:**
- [ ] `utils.py` tiene funciones de logging, validación, backup
- [ ] `android_backup.py` encapsula toda lógica ADB
- [ ] `ios_backup.py` encapsula toda lógica iTunes
- [ ] `main.py` orquesta el flujo sin lógica de bajo nivel
- [ ] Cada módulo tiene manejo de errores
- [ ] Todas las operaciones destructivas tienen backup previo
- [ ] Logging en cada paso crítico

---

### Fase 4: Manejo de Errores y Rollback

**Objetivo:** Agregar manejo robusto de errores con posibilidad de rollback.

**Mejoras:**

1. **Try-catch en operaciones críticas:**
```python
try:
    # Operación destructiva
    shutil.rmtree('tmp')
except OSError as e:
    logger.error(f"Failed to remove tmp: {e}")
    # Continuar o abortar según criticidad
```

2. **Validación de comandos ADB:**
```python
def run_adb_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"ADB command failed: {result.stderr}")
        raise RuntimeError(f"ADB error: {result.stderr}")
    return result.stdout
```

3. **Backups antes de operaciones destructivas:**
```python
# Antes de sobrescribir ChatStorage
backup_file = create_backup(chatstorage_path, 'backups')
logger.info(f"Backup created: {backup_file}")

try:
    shutil.copyfile('out/out.db', chatstorage_path)
except Exception as e:
    logger.error(f"Failed to update backup: {e}")
    # Restaurar desde backup
    shutil.copyfile(backup_file, chatstorage_path)
    raise
```

4. **Validación de archivos generados:**
```python
if not os.path.exists('out/out.db'):
    logger.error("migrate.py did not generate output file")
    sys.exit(1)

# Validar que sea SQLite válido
try:
    conn = sqlite3.connect('out/out.db')
    conn.execute("SELECT 1 FROM ZWAMESSAGE LIMIT 1")
    conn.close()
except sqlite3.Error as e:
    logger.error(f"Invalid output database: {e}")
    sys.exit(1)
```

**Criterios de Éxito:**
- [ ] Try-catch en todas las operaciones de archivo
- [ ] Validación de return codes de ADB
- [ ] Backups automáticos antes de sobrescribir archivos
- [ ] Validación de archivos generados (existencia + integridad)
- [ ] Mensajes de error descriptivos
- [ ] Rollback automático si falla actualización de backup iOS

---

### Fase 5: Documentación Completa

**Objetivo:** Crear documentación exhaustiva para usuarios y desarrolladores.

**Archivos:**

1. **docs/SETUP.md:**
```markdown
# Guía de Instalación

## Requisitos
- Windows 10/11
- Python 3.8+
- Dispositivo Android con USB debugging
- iPhone con backup de iTunes sin cifrar

## Instalación de Dependencias

### 1. Android SDK Platform Tools
[Instrucciones detalladas...]

### 2. APKs Legacy de WhatsApp
[Instrucciones detalladas...]

### 3. Instalar proyecto
pip install -r requirements.txt

## Verificación
python src/main.py --check-dependencies
```

2. **docs/USAGE.md:**
```markdown
# Guía de Uso

## Proceso Completo Paso a Paso

### Preparación Android
1. Habilitar USB debugging
2. Conectar dispositivo
3. Autorizar computadora

### Preparación iOS
1. Desactivar "Find My iPhone"
2. Crear backup sin cifrar en iTunes
3. Cerrar iTunes

### Ejecutar Migración
python src/main.py

[Instrucciones detalladas de cada paso...]
```

3. **docs/ARCHITECTURE.md:**
```markdown
# Arquitectura del Proyecto

## Módulos

### src/main.py
Orquestador principal del flujo de migración.

### src/migrate.py
Núcleo de conversión de esquemas SQLite Android ↔ iOS.
[Diagramas de flujo, mapeo de tablas...]

### src/android_backup.py
[Documentación técnica...]

### src/ios_backup.py
[Documentación técnica...]

## Flujo de Datos
[Diagramas...]

## Manejo de Errores
[Estrategias...]
```

4. **Actualizar README.md principal:**
```markdown
# WhatsApp Android → iOS Migration Tool

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)]
[![License](https://img.shields.io/badge/license-MIT-green.svg)]

Herramienta para migrar chats de WhatsApp/WhatsApp Business desde Android hacia iOS.

## Características

✅ Migración completa de chats y grupos
✅ Soporte WhatsApp y WhatsApp Business
✅ Preserva chats existentes en iOS
✅ Backups automáticos de seguridad
✅ Logging detallado
✅ Manejo robusto de errores

## Instalación Rápida

[Instrucciones...]

## Documentación

- [Guía de Instalación](docs/SETUP.md)
- [Guía de Uso](docs/USAGE.md)
- [Arquitectura](docs/ARCHITECTURE.md)
- [Investigación Técnica](docs/research/2025-11-28-investigacion-proyecto-migracion-whatsapp.md)

## Advertencias

⚠️ Este proceso modifica backups de iTunes. Siempre haz backup antes.
⚠️ Requiere APK legacy de WhatsApp (no incluido por derechos de autor).
⚠️ Solo Windows por ahora (usa adb.exe).
```

**Criterios de Éxito:**
- [ ] SETUP.md completo con instrucciones de instalación
- [ ] USAGE.md con guía paso a paso ilustrada
- [ ] ARCHITECTURE.md con diagramas y explicaciones técnicas
- [ ] README.md actualizado con badges y estructura clara
- [ ] Todos los links funcionan correctamente

---

### Fase 6: Limpieza de .github/

**Objetivo:** Eliminar archivos de Green-POS y crear estructura apropiada.

**Acciones:**

1. **Eliminar archivos no relacionados:**
```bash
# Eliminar
.github/agents/
.github/instructions/
.github/plans/2025-11-24-*.md
.github/plans/2025-11-25-*.md
.github/plans/2025-11-26-*.md
.github/copilot-instructions.md
```

2. **Crear nuevo copilot-instructions.md:**
```markdown
# Contexto del Proyecto WhatsApp Migration

## Stack Tecnológico
- Python 3.8+
- SQLite3
- ADB (Android Debug Bridge)
- iTunes Backup Format

## Patrones de Diseño
- Separación de responsabilidades (módulos especializados)
- Manejo de errores con try-catch
- Logging estructurado
- Backups antes de operaciones destructivas

[Documentación específica del proyecto...]
```

3. **Mantener:**
```
.github/
├── plans/
│   └── 2025-11-28-implementacion-completa-proyecto-whatsapp-migration.md
└── copilot-instructions.md  (nuevo)
```

**Criterios de Éxito:**
- [ ] Archivos de Green-POS eliminados
- [ ] Nuevo copilot-instructions.md creado
- [ ] Plan de implementación conservado
- [ ] Estructura .github/ limpia y relevante

---

### Fase 7: Configuración y Requirements

**Objetivo:** Crear archivos de configuración del proyecto.

**Archivos:**

1. **requirements.txt:**
```
# El proyecto usa solo librería estándar de Python
# No hay dependencias pip

# Para desarrollo/testing (opcional):
# pytest>=7.0.0
# pylint>=2.15.0
```

2. **Actualizar .gitignore:**
```gitignore
# WhatsApp Migration specifics
tmp/
out/
logs/
backups/
*.db
*.ab
*.tar

# APKs (no distribuir por copyright)
apk/*.apk

# Binarios (descargar por separado)
bin/adb.exe
bin/*.dll

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# IDEs
.vscode/
.idea/
```

3. **src/__init__.py:**
```python
"""
WhatsApp Android to iOS Migration Tool
"""
__version__ = '1.0.0'
__author__ = 'Henry.Correa'
```

**Criterios de Éxito:**
- [ ] requirements.txt creado (vacío con comentarios)
- [ ] .gitignore actualizado con rutas específicas
- [ ] src/__init__.py con metadata del proyecto

---

### Fase 8: Verificación Final

**Objetivo:** Validar que toda la implementación funcione correctamente.

**Checklist de Verificación:**

1. **Estructura de proyecto:**
   - [ ] Todos los directorios creados
   - [ ] Archivos en ubicaciones correctas
   - [ ] .gitignore funciona (tmp/, out/ ignorados)

2. **Código:**
   - [ ] `python src/main.py --help` funciona
   - [ ] Importaciones entre módulos correctas
   - [ ] No hay errores de sintaxis (pylint/flake8)

3. **Documentación:**
   - [ ] README.md se ve bien en GitHub
   - [ ] Links entre documentos funcionan
   - [ ] bin/README.md tiene instrucciones claras
   - [ ] apk/README.md tiene advertencias legales

4. **Testing manual (sin dispositivos):**
   - [ ] Script detecta dependencias faltantes correctamente
   - [ ] Mensajes de error son descriptivos
   - [ ] Logging a archivo funciona

**Criterios de Éxito:**
- [ ] Estructura completa creada
- [ ] Código sin errores de sintaxis
- [ ] Documentación completa y enlazada
- [ ] .github/ limpio de archivos irrelevantes
- [ ] Proyecto listo para usar (con dependencias externas)

---

## Notas de Implementación

### Prioridades
1. **Crítico:** migrate.py (sin él, el proyecto no funciona)
2. **Alto:** Manejo de errores y backups (seguridad)
3. **Medio:** Modularización (mantenibilidad)
4. **Bajo:** Documentación exhaustiva (usabilidad)

### Riesgos
- **migrate.py** es complejo: requiere entender esquemas SQLite de WhatsApp
- Esquemas de WhatsApp pueden cambiar entre versiones
- Testing real requiere dispositivos Android/iOS

### Dependencias Externas
No incluidas en el proyecto (copyright/tamaño):
- Android SDK Platform Tools (~10MB)
- LegacyWhatsApp.apk (~20MB)
- LegacyWhatsAppBusiness.apk (~25MB)

---

## Referencias

- [Investigación del Proyecto](../../docs/research/2025-11-28-investigacion-proyecto-migracion-whatsapp.md)
- [main.py Original](../../main.py)
- [Android Backup Format](https://nelenkov.blogspot.com/2012/06/unpacking-android-backups.html)
- [WhatsApp Encryption](https://www.whatsapp.com/security/)
