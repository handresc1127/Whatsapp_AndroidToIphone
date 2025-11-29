# Puntos Críticos del Proceso de Migración WhatsApp Android → iOS

**Fecha de análisis:** 28 de noviembre de 2025  
**Archivo analizado:** main.py  
**Tipo de documento:** Identificación de riesgos operacionales

---

## 1. Validaciones Implementadas

### Validación de Archivos Requeridos (Línea 12-17)
**Exit Code:** `1`  
**Archivos validados:**
- `bin/adb.exe`
- `bin/AdbWinApi.dll`
- `bin/AdbWinUsbApi.dll`
- `bin/LegacyWhatsApp.apk`
- `./migrate.py`

**Consecuencia de fallo:** Terminación inmediata del script antes de iniciar proceso.

### Validación de Directorio de Backup iOS (Línea 112-116)
**Exit Code:** `2`  
**Rutas verificadas (en orden):**
1. `%APPDATA%\Apple Computer\MobileSync\Backup`
2. `%USERPROFILE%\Apple\MobileSync\Backup`
3. `%USERPROFILE%\Apple\MobileSync`

**Consecuencia de fallo:** No se encuentra ninguna ubicación de backup de iTunes.

### Validación de Backups Disponibles (Línea 118-125)
**Exit Code:** `3`  
**Condición:** Directorio de backups vacío.  
**Consecuencia de fallo:** No hay backups de iPhone para procesar.

### Validación de Manifest.db (Línea 127-130)
**Exit Code:** `4`  
**Archivo crítico:** `<backup_folder>/Manifest.db`  
**Consecuencia de fallo:** Backup iOS corrupto o incompleto.

### Validación de Datos de WhatsApp en iOS (Línea 134-137)
**Exit Code:** `5`  
**Query SQL:** `SELECT fileID FROM Files WHERE relativePath='ChatStorage.sqlite' AND domain='AppDomainGroup-group.net.whatsapp.WhatsApp.shared'`  
**Condición:** Debe retornar exactamente 1 resultado.  
**Consecuencia de fallo:** 
- WhatsApp no instalado en iPhone
- Backup no contiene datos de WhatsApp
- Múltiples instancias de WhatsApp (inesperado)

### Validación de Base de Datos Android (Línea 85-89)
**Exit Code:** `1`  
**Archivo crítico:** `tmp\apps\com.whatsapp\db\msgstore.db` (o `com.whatsapp.w4b`)  
**Consecuencia de fallo:** Backup Android incompleto o corrupto.

---

## 2. Intervenciones Manuales del Usuario

### 2.1. Pre-Proceso Android

#### Confirmación de Backup Manual de Chats (Línea 44-47)
```
***********************************************
Please backup all your whatsapp chats before proceeding.
***********************************************
Do you want to continue?[y/n]:
```
**Acción requerida:** Usuario debe confirmar que realizó backup manual en WhatsApp Android.  
**Riesgo:** No hay validación de que el backup se haya hecho realmente.

### 2.2. Durante Proceso Android

#### Confirmación de Backup ADB (Línea 57)
```
Please confirm the backup operation is complete and tmp/whatsapp.ab is present.
Press Enter to continue after backup is complete...
```
**Acción requerida en dispositivo Android:**
1. Aparece diálogo de confirmación de backup
2. Usuario debe tocar "BACKUP MY DATA"
3. Esperar a que se complete (sin indicador de progreso en script)

**Validación manual:** Usuario debe verificar que `tmp\whatsapp.ab` existe antes de continuar.

#### Operación de Backup Sin Contraseña (Línea 53-54)
```
Nota: No pongas ninguna contraseña.
adb backup -f tmp\whatsapp.ab {package}
```
**Acción crítica:** Si usuario pone contraseña, el backup será encriptado y NO PROCESABLE.

### 2.3. Pre-Proceso iOS

#### Instrucciones Manuales (Línea 96-101)
```
1. Login into whatsapp with the same number in your iphone.
   If already logged in, script will preserve iphone chats also.
2. Disable 'Find My iPhone' option in your iphone.
3. Create an unencrypted local backup using iTunes.
```

**Acción 1:** Login en WhatsApp iOS  
**Acción 2:** Desactivar "Buscar mi iPhone" en Ajustes → [Nombre] → Buscar → Buscar mi iPhone  
**Acción 3:** Crear backup NO ENCRIPTADO en iTunes

**CRÍTICO:** Si el backup está encriptado, `Manifest.db` no será accesible.

#### Pausa para Configuración iOS (Línea 102)
```
Press enter to continue...
```
**Tiempo estimado:** 5-15 minutos (login WhatsApp + backup iTunes completo).

### 2.4. Durante Migración

#### Input de Número Telefónico (Línea 141)
```
Enter phone number with country code, eg: 9185XXXXXXXX:
```
**Formato requerido:** Solo dígitos, con código de país, SIN símbolos (+, -, espacios).  
**Sin validación:** El script NO valida el formato del número.

### 2.5. Selección WhatsApp/Business (Línea 29-30)
```
¿Quieres migrar WhatsApp estándar o WhatsApp Business?
1. WhatsApp estándar
2. WhatsApp Business
Selecciona 1 o 2:
```
**Validación:** Solo verifica si input == '2', cualquier otra entrada → WhatsApp estándar.  
**Riesgo:** Input inválido (3, 'a', etc.) procesará como WhatsApp estándar sin advertencia.

---

## 3. Operaciones Destructivas

### 3.1. Desinstalación de WhatsApp Android (Línea 59)
```bash
bin\adb.exe shell pm uninstall -k {wa_package}
```
**Qué se elimina:**
- Aplicación WhatsApp (APK)
- **Datos de aplicación PERMANECEN** (flag `-k` = keep data)

**Punto de no retorno:** Parcial - se puede reinstalar pero requiere APK.

### 3.2. Eliminación de Directorio Temporal (Línea 92)
```python
shutil.rmtree('tmp')
```
**Qué se elimina:**
- `tmp\whatsapp.ab` (backup ADB original)
- `tmp\whatsapp.tar` (versión extraída)
- `tmp\apps\com.whatsapp\db\msgstore.db` (base de datos Android original)
- Toda la estructura de carpetas extraída

**Punto de no retorno:** TOTAL - No hay rollback después de esta línea.  
**CRÍTICO:** Si falla el proceso iOS después, NO HAY backup Android recuperable.

### 3.3. Sobrescritura de ChatStorage.sqlite iOS (Línea 150)
```python
shutil.copyfile('out\\out.db', chatstorage_path)
```
**Qué se sobrescribe:**
- `<backup_iOS>/<hash[:2]>/<hash>` (ChatStorage.sqlite original del iPhone)

**Punto de no retorno:** TOTAL  
**CRÍTICO:** Los chats iOS originales se pierden sin backup adicional.  
**Mitigación existente:** Se copia a `out\ios.db` (línea 139) pero se elimina después (línea 151).

### 3.4. Eliminación de Directorio de Salida (Línea 151)
```python
shutil.rmtree('out')
```
**Qué se elimina:**
- `out\android.db` (copia de base de datos Android)
- `out\ios.db` (copia de base de datos iOS ORIGINAL)
- `out\out.db` (base de datos migrada antes de sobrescribir)

**Consecuencia:** No quedan copias de seguridad locales después del proceso.

---

## 4. Dependencias de Configuración

### Android:

**Hardware/Software:**
- Dispositivo Android conectado por USB
- Drivers ADB instalados
- Modo depuración USB activado
- Autorización de depuración USB confirmada

**WhatsApp:**
- WhatsApp instalado (estándar o Business)
- Sesión activa (número verificado)
- Backup manual de chats recomendado (Google Drive/local)

**Sistema:**
- Windows con PowerShell
- Permisos para instalar/desinstalar aplicaciones vía ADB

**Limitaciones:**
- Backup ADB NO funciona en Android 11+ (limitación de OS)
- Requiere versión legacy de WhatsApp APK

### iOS:

**Hardware/Software:**
- iPhone con WhatsApp instalado
- iTunes instalado en Windows
- Cable USB conectado
- "Buscar mi iPhone" DESACTIVADO

**WhatsApp:**
- Sesión iniciada con el MISMO número que Android
- Puede tener chats existentes (se preservarán si script funciona)

**iTunes:**
- Backup NO ENCRIPTADO (requisito absoluto)
- Backup completo reciente
- Suficiente espacio en disco para backup

**Sistema:**
- Ubicación de backups en una de las rutas:
  - `%APPDATA%\Apple Computer\MobileSync\Backup`
  - `%USERPROFILE%\Apple\MobileSync\Backup`
  - `%USERPROFILE%\Apple\MobileSync`

**Limitaciones:**
- Un solo backup en directorio (o input manual de ruta)
- Backup debe contener Manifest.db legible
- ChatStorage.sqlite debe existir en backup

---

## 5. Análisis de Manejo de Errores

### Errores Capturados:

1. **Archivos requeridos faltantes** (exit 1)
2. **Directorio de backup iOS no existe** (exit 2)
3. **No hay backups iOS** (exit 3)
4. **Manifest.db faltante** (exit 4)
5. **ChatStorage.sqlite no encontrado o múltiple** (exit 5)
6. **msgstore.db Android faltante** (exit 1)
7. **Usuario cancela confirmación inicial** (exit sin código)

### Errores NO Capturados (Posibles Fallos Sin Try-Catch):

#### Operaciones ADB (Líneas 41-54):
- `adb kill-server` falla
- `adb start-server` falla
- `adb wait-for-device` timeout infinito
- `pm uninstall` falla (app no instalada)
- `adb install` falla (APK corrupto, incompatible)
- `adb backup` falla (permisos denegados, almacenamiento lleno)

**Consecuencia:** Script continúa sin validar éxito de comandos.

#### Operaciones de Archivos (Líneas 61-77):
- `open('tmp/whatsapp.ab', 'rb')` - FileNotFoundError si backup no se creó
- `tarfile.open('tmp\\whatsapp.tar')` - tarfile.ReadError si archivo corrupto
- `tp.extractall()` - PermissionError, DiskFullError

**Consecuencia:** Crash con traceback Python.

#### Operaciones de Base de Datos (Línea 132):
- `sqlite3.connect(manifest_db_path)` - Corrupted database
- Query SQL falla - Tabla "Files" no existe

**Consecuencia:** Crash con traceback Python.

#### Operaciones de Migración (Línea 143):
- `os.system('python migrate.py ...')` - migrate.py falla
- Archivo de salida `out\out.db` no se genera

**Consecuencia:** Sobrescritura en línea 150 con archivo inexistente → FileNotFoundError.

#### Operaciones de Limpieza (Líneas 92, 151):
- `shutil.rmtree()` - PermissionError (archivo abierto en otro proceso)
- `shutil.rmtree()` - Directorio no existe (si `out` no se creó)

**Consecuencia:** Crash, pero datos ya procesados.

### Falta de Validación Post-Operación:

- No verifica que `tmp\whatsapp.ab` existe después de backup
- No valida tamaño de archivo backup > 0 bytes
- No valida que `out\android.db` se copió correctamente
- No valida que migrate.py retornó exitosamente
- No valida que `out\out.db` fue creado por migrate.py
- No valida integridad de bases de datos SQLite

---

## 6. Puntos de No Retorno

### Punto de No Retorno #1: Eliminación de `tmp\` (Línea 92)
**Momento:** Después de copiar `android.db` a `out\`  
**Qué se pierde:**
- `tmp\whatsapp.ab` - Backup ADB original
- `tmp\whatsapp.tar` - Versión extraída
- `tmp\apps\...\msgstore.db` - Base de datos Android en formato original

**Rollback posible:** NO  
**Mitigación:** Se preserva copia en `out\android.db` hasta línea 151.

### Punto de No Retorno #2: Sobrescritura de ChatStorage iOS (Línea 150)
**Momento:** Después de ejecutar migrate.py exitosamente  
**Qué se pierde:**
- ChatStorage.sqlite original del iPhone
- Chats iOS previos (si no fueron integrados correctamente por migrate.py)

**Rollback posible:** NO (a menos que iTunes haya creado versiones anteriores)  
**Mitigación:** Se copió a `out\ios.db` (línea 139) pero se elimina en línea 151.

### Punto de No Retorno #3: Eliminación de `out\` (Línea 151)
**Momento:** Final del proceso  
**Qué se pierde:**
- `out\android.db` - Única copia de base de datos Android
- `out\ios.db` - Única copia de base de datos iOS ORIGINAL
- `out\out.db` - Única copia de base de datos migrada

**Rollback posible:** NO  
**Consecuencia:** Si restauración de iTunes falla, NO HAY backups disponibles.

### Línea de Fallo Crítico

```
Línea 57:  Usuario confirma backup → Puede continuar sin backup real
Línea 92:  rmtree('tmp') → PIERDE backup Android original
Línea 150: copyfile a iOS → PIERDE chats iOS originales
Línea 151: rmtree('out') → PIERDE todas las copias de seguridad
```

**Si el proceso falla entre líneas 150-151:** iPhone tiene datos migrados pero no hay copias locales.  
**Si el proceso falla después de línea 151:** No hay forma de recuperar datos ni Android ni iOS.

---

## 7. Archivos Temporales y Limpieza

### Archivos Creados Durante el Proceso:

#### Directorio `tmp\` (creado línea 51, eliminado línea 92):
```
tmp\
├── whatsapp.ab          # Backup ADB (tamaño: 100MB-2GB típicamente)
├── whatsapp.tar         # Versión extraída (tamaño similar)
└── apps\
    └── com.whatsapp\    # (o com.whatsapp.w4b)
        ├── db\
        │   └── msgstore.db      # Base de datos de chats
        ├── f\                   # Archivos multimedia (fotos, videos)
        └── [otras carpetas]
```

**Persistencia:** Eliminado completamente en línea 92.

#### Directorio `out\` (creado línea 80, eliminado línea 151):
```
out\
├── android.db    # Copia de msgstore.db (creado línea 86)
├── ios.db        # Copia de ChatStorage.sqlite (creado línea 139)
└── out.db        # Base de datos migrada (creado por migrate.py)
```

**Persistencia:** Eliminado completamente en línea 151.

### Archivos Persistentes:

**En sistema local:**
- `bin\LegacyWhatsApp.apk` - APK legacy (pre-existente)
- `migrate.py` - Script de migración (pre-existente)

**En dispositivo Android:**
- WhatsApp legacy instalado (si no se desinstala manualmente después)
- Datos de WhatsApp preservados (`-k` flag en uninstall)

**En backup de iTunes:**
- ChatStorage.sqlite **SOBRESCRITO** con datos migrados
- Resto de archivos del backup sin modificar

### Limpieza Post-Proceso:

**Automática:**
- Servidor ADB detenido (línea 93)
- Directorios temporales eliminados (líneas 92, 151)

**Manual requerida:**
- Reinstalar WhatsApp actualizado en Android (si se desea)
- Habilitar "Buscar mi iPhone" nuevamente
- Eliminar backup iTunes antiguo (opcional)

### Riesgos de Limpieza:

1. **shutil.rmtree() sin validación:** Si falla, deja archivos huérfanos.
2. **No hay logs persistentes:** Imposible auditar qué pasó en caso de fallo.
3. **Eliminación prematura:** Backups locales se eliminan antes de confirmar restauración exitosa en iPhone.

---

## 8. Dependencias Externas Sin Validación

### Comandos del Sistema (os.system):
- **ADB:** 7 llamadas sin captura de return code
- **Python:** 1 llamada a migrate.py sin validación de éxito

### Archivos Generados por Procesos Externos:
- `tmp\whatsapp.ab` - Generado por ADB, asumido que existe
- `out\out.db` - Generado por migrate.py, asumido que existe

### Interacción Usuario-Dispositivo:
- Confirmación de backup en pantalla Android (sin timeout)
- Login en WhatsApp iOS (sin validación)
- Creación de backup iTunes (sin validación de completitud)

---

## Resumen Ejecutivo de Riesgos

### Riesgos ALTOS:
1. **Pérdida de datos iOS:** Sobrescritura sin backup verificable (línea 150)
2. **Pérdida de datos Android:** Eliminación de backup original sin rollback (línea 92)
3. **Falta de validación de migrate.py:** Si falla, corrompe backup iOS

### Riesgos MEDIOS:
1. **Comandos ADB sin validación:** Proceso continúa aunque fallen
2. **Backup ADB con contraseña:** Usuario puede encriptar sin darse cuenta
3. **Múltiples backups iOS:** Si hay más de uno, requiere input manual

### Riesgos BAJOS:
1. **Selección WhatsApp/Business:** Input inválido procesa como estándar
2. **Formato de número telefónico:** Sin validación, puede causar error en migrate.py
3. **Permisos de archivos:** shutil.rmtree() puede fallar en limpieza

---

**Documento generado para:** Análisis de riesgos operacionales  
**Próximo paso sugerido:** Implementar validaciones y backups de seguridad  
**Disclaimer:** Este documento identifica riesgos existentes, NO propone soluciones.

---

## 9. Tecnologías Android

### 9.1. ADB - Android Debug Bridge

**Definición:**  
Herramienta de línea de comandos que permite comunicación entre un PC y dispositivos Android. Funciona en arquitectura cliente-servidor con tres componentes:
- **Cliente:** Ejecuta comandos desde terminal (adb.exe)
- **Daemon (adbd):** Proceso en segundo plano en el dispositivo Android
- **Servidor:** Proceso en background en PC que gestiona comunicación cliente-daemon

**Comandos Utilizados:**

#### `adb kill-server` (línea 41)
**Propósito:** Detiene el proceso del servidor ADB en el PC.  
**Uso en script:** Limpia cualquier sesión previa antes de iniciar proceso fresh.  
**Return code:** Ignorado (sin validación).

#### `adb start-server` (línea 42)
**Propósito:** Inicia el proceso del servidor ADB en el PC.  
**Uso en script:** Establece conexión entre PC y dispositivo Android.  
**Comportamiento:** Inicia automáticamente el daemon (adbd) en el dispositivo si es necesario.

#### `adb wait-for-device` (línea 43)
**Propósito:** Bloquea ejecución hasta que un dispositivo Android esté conectado y autorizado.  
**Uso en script:** Pausa el script hasta detectar dispositivo listo para comandos.  
**Timeout:** Infinito por defecto (sin límite de tiempo configurado en script).

#### `adb shell pm uninstall -k {package}` (línea 59)
**Propósito:** Desinstala una aplicación desde el dispositivo Android.  
**Flag `-k` (keep data):** Preserva datos de aplicación y caché.  
**Resultado:** 
- Elimina el APK (`/data/app/{package}`)
- **Mantiene** bases de datos (`/data/data/{package}/databases/`)
- **Mantiene** archivos multimedia (`/data/data/{package}/files/`)

**Uso crítico en script:** Permite desinstalar WhatsApp moderno sin perder chats, para instalar versión legacy.

#### `adb install -r -d {apk}` (línea 62)
**Propósito:** Instala un APK en el dispositivo Android.  
**Flag `-r` (replace):** Reinstala aplicación manteniendo datos (equivalente a actualización).  
**Flag `-d` (downgrade):** Permite instalar versión más antigua que la existente (normalmente bloqueado).  
**Resultado:** Instala `LegacyWhatsApp.apk` con versionCode menor que WhatsApp moderno.

**Uso crítico en script:** Necesario para forzar downgrade a versión legacy sin cifrado AES-256.

#### `adb backup -f {file} {package}` (línea 64)
**Propósito:** Crea backup completo de datos de aplicación en formato .ab (Android Backup).  
**Flag `-f {file}`:** Especifica ruta de archivo de salida (tmp\whatsapp.ab).  
**Argumento `{package}`:** Paquete específico a respaldar (com.whatsapp o com.whatsapp.w4b).  
**Formato generado:** Archivo .ab con estructura:
- Header Android (24 bytes)
- Datos comprimidos con zlib (contenido tar)
- **SIN cifrado** si usuario no pone contraseña en diálogo

**Interacción usuario:** Requiere confirmación manual en pantalla del dispositivo Android ("BACKUP MY DATA").

**Archivos Windows Requeridos:**

#### `bin\adb.exe` (validado línea 12-17)
**Propósito:** Ejecutable principal del cliente ADB para Windows.  
**Versión típica:** 1.0.39+ (necesaria compatibilidad con Android 5.0+)

#### `bin\AdbWinApi.dll`
**Propósito:** Librería de la API de Windows para comunicación USB con dispositivos Android.  
**Función:** Interfaz entre adb.exe y drivers USB del dispositivo.

#### `bin\AdbWinUsbApi.dll`
**Propósito:** Librería de drivers USB genéricos de Android para Windows.  
**Función:** Permite comunicación de bajo nivel con dispositivo Android vía USB sin drivers OEM específicos.

**Nota:** Estos DLLs son parte del Android SDK Platform Tools y deben estar en mismo directorio que adb.exe.

---

### 9.2. Formato Android Backup (.ab)

**Estructura del Archivo:**

#### Bytes 0-23: Header Android Backup
```
Byte 0-14:  "ANDROID BACKUP\n"     (cadena ASCII, 15 bytes)
Byte 15-16: Version number          (ej: "1\n" o "4\n", ASCII)
Byte 17-18: Compression flag        ("0\n" = sin compresión, "1\n" = comprimido)
Byte 19-23: Encryption type         ("none\n" = sin cifrado, "AES-256\n" = cifrado)
```

**Ejemplo real (hexadecimal):**
```
41 4E 44 52 4F 49 44 20 42 41 43 4B 55 50 0A  (ANDROID BACKUP\n)
34 0A                                         (4\n - versión)
31 0A                                         (1\n - comprimido)
6E 6F 6E 65 0A                                (none\n - sin cifrado)
```

#### Bytes 24+: Datos Comprimidos con zlib
**Formato:** Stream de datos zlib (RFC 1950) conteniendo archivo tar.  
**Contenido del tar:** Estructura de directorios de aplicación Android.

**¿Por qué la Conversión Manual a tar? (líneas 70-78)**

**Razón 1 - Formato Híbrido:**  
Python's `tarfile.open()` espera un archivo tar estándar, pero .ab es:
```
[Header Android de 24 bytes] + [Datos zlib del tar]
```
No es un tar directo, requiere extracción del stream zlib.

**Razón 2 - Header Incompatible:**  
El header de 24 bytes rompe la estructura tar esperada. `tarfile` busca header tar en byte 0, pero encuentra texto ASCII "ANDROID BACKUP".

**Razón 3 - Formato zlib vs gzip:**  
ADB genera compresión zlib (deflate), pero Python's `tarfile` espera gzip para archivos .tar.gz.

**Solución Implementada (líneas 70-78):**

```python
with open('tmp/whatsapp.ab','rb') as inp:
    with open('tmp/whatsapp.tar','wb') as out:
        # 1. Escribir header gzip manual (8 bytes)
        out.write(b'\x1f\x8b\x08\x00\x00\x00\x00\x00')
        
        # 2. Saltar header Android (24 bytes)
        inp.read(24)
        
        # 3. Copiar resto (datos zlib) que son compatibles con gzip
        while True:
            b = inp.read(512)
            if not b:
                break
            out.write(b)
```

**Header Manual: `\x1f\x8b\x08\x00\x00\x00\x00\x00` (8 bytes)**

Explicación byte por byte:
```
\x1f\x8b    - Magic number gzip (identificador de formato)
\x08        - Compression method (08 = DEFLATE, mismo que zlib)
\x00        - Flags (sin flags especiales)
\x00\x00\x00\x00 - Timestamp (epoch 0 = 1970-01-01, placeholder)
```

**¿Por qué se saltan 24 bytes del .ab original?**

Porque contienen metadata de Android que NO es parte del tar:
- Firma del formato ("ANDROID BACKUP")
- Versión del formato de backup
- Flags de compresión/cifrado
- Metadata que `tarfile` no puede procesar

Después de saltar 24 bytes, el resto del .ab es un stream zlib puro que, con el header gzip agregado manualmente, se convierte en un archivo .tar.gz válido que `tarfile.open()` puede leer.

**Contenido del tar Extraído:**

```
tmp/apps/{package}/                 # com.whatsapp o com.whatsapp.w4b
├── db/
│   ├── msgstore.db                 # BASE DE DATOS DE CHATS (objetivo crítico)
│   ├── msgstore.db-wal             # Write-Ahead Log (SQLite)
│   ├── wa.db                       # Base de datos de contactos
│   ├── axolotl.db                  # Base de datos de cifrado E2E
│   └── [otros archivos .db]
├── f/                              # Carpeta de archivos (files)
│   ├── Media/
│   │   ├── WhatsApp Images/        # Fotos enviadas/recibidas
│   │   ├── WhatsApp Video/         # Videos
│   │   ├── WhatsApp Audio/         # Audios y notas de voz
│   │   ├── WhatsApp Documents/     # PDFs, documentos
│   │   └── WhatsApp Stickers/      # Stickers
│   ├── Avatars/                    # Fotos de perfil de contactos
│   └── Backups/                    # Backups locales de chats
├── sp/                             # SharedPreferences (configuración)
│   └── com.whatsapp_preferences.xml
└── [otros archivos de cache y temp]
```

**Archivo crítico:** `msgstore.db` (línea 85)  
**Ruta completa:** `tmp\apps\com.whatsapp\db\msgstore.db`  
**Copiado a:** `out\android.db` (línea 86)  
**Uso:** Base de datos SQLite con esquema de chats de Android que migrate.py convierte a formato iOS.

---

### 9.3. APK Legacy de WhatsApp

**Versión Aproximada de "Legacy":**  
WhatsApp 2.11.x a 2.12.x (circa 2014-2015)

**Versión exacta recomendada:**  
- WhatsApp: **2.11.431** (última versión antes de cifrado obligatorio)
- WhatsApp Business: **2.18.x** (primeras versiones sin cifrado de backup)

**¿Por qué las Versiones Modernas NO Sirven?**

#### Problema 1: Cifrado AES-256 en Backups (desde WhatsApp 2.12.556+)

**Versiones modernas (2.12.556+):**
```
adb backup -f whatsapp.ab com.whatsapp
```
Genera:
```
[ANDROID BACKUP Header]
Version: 4
Compressed: 1
Encryption: AES-256        <--- PROBLEMA
[Salt de 64 bytes]
[Checksum PBKDF2]
[Datos cifrados con AES-256-CBC]
```

**Contraseña requerida:** Si usuario pone contraseña en diálogo, datos son cifrados.  
**Consecuencia:** Sin contraseña correcta, datos son **ilegibles**.  
**Problema crítico:** Script NO soporta descifrado (no solicita contraseña, asume backup sin cifrar).

**Versiones legacy (2.11.x):**
```
adb backup -f whatsapp.ab com.whatsapp
```
Genera:
```
[ANDROID BACKUP Header]
Version: 1
Compressed: 1
Encryption: none           <--- SOLUCIÓN
[Datos zlib directos, sin cifrado]
```

**Incluso sin contraseña:** Backup es procesable porque aplicación legacy NO implementa cifrado en backups.

#### Problema 2: Restricciones de Android 11+ (API Level 30+)

**Android 11+:**  
`adb backup` está **deprecado** y muchos fabricantes lo deshabilitan.

**Workaround con APK legacy:**  
Versiones antiguas de WhatsApp tienen `android:allowBackup="true"` sin restricciones adicionales en AndroidManifest.xml.

**Versiones modernas:**  
Pueden tener `android:fullBackupOnly="true"` o `android:allowBackup="false"`, bloqueando `adb backup` completamente.

#### Problema 3: Cambios en Esquema de Base de Datos

**Versiones modernas:**  
Esquema de `msgstore.db` ha cambiado significativamente:
- Nuevas tablas (message_media, message_quoted, etc.)
- Cambios en estructura de columnas
- Mensajes cifrados E2E con referencias a `axolotl.db`

**Script migrate.py:**  
Espera esquema antiguo de WhatsApp 2.11.x con estructura compatible con ChatStorage.sqlite de iOS.

**Versiones legacy:**  
Esquema simple y estable que migrate.py puede mapear directamente a formato iOS.

#### Diferencia en Cifrado de Backups

**Tabla Comparativa:**

| Aspecto | WhatsApp Legacy (2.11.x) | WhatsApp Moderno (2.20.x+) |
|---------|---------------------------|----------------------------|
| **Cifrado de backup** | Ninguno (opcional con contraseña) | AES-256 obligatorio si hay contraseña |
| **Algoritmo de derivación** | N/A | PBKDF2-HMAC-SHA1 (10,000 iteraciones) |
| **Salt** | N/A | 64 bytes aleatorios |
| **IV (Vector de Inicialización)** | N/A | 16 bytes aleatorios por bloque |
| **Modo de cifrado** | N/A | AES-256-CBC |
| **Checksum** | CRC32 (tar) | HMAC-SHA1 del contenido cifrado |
| **Backup sin contraseña** | Procesable (sin cifrado) | **Procesable** (encryption: none) |
| **Backup con contraseña** | Cifrado básico | Cifrado AES-256 robusto |

**Por qué el script requiere "No pongas ninguna contraseña" (línea 53):**

**Si usuario pone contraseña:**
```python
# Línea 70-78 intenta esto:
with open('tmp/whatsapp.ab','rb') as inp:
    inp.read(24)  # Salta header
    # Pero siguiente contenido NO es zlib, es:
    # [Salt 64 bytes][Checksum][Datos AES cifrados]
    # out.write() copia datos cifrados
    
# Línea 74-77: tarfile.open() falla
# Error: "not a gzip file" o "invalid tar header"
```

**Con versión legacy SIN contraseña:**
```python
# Después de saltar 24 bytes:
# [Datos zlib del tar] <- Directamente procesable
# tarfile.open() exitoso
```

**Consecuencia de usar versión moderna:**  
Incluso sin contraseña, si WhatsApp >= 2.12.556:
- Backup puede incluir metadata de cifrado opcional
- Estructura de carpetas puede cambiar (Google Drive backups integrados)
- migrate.py puede fallar por incompatibilidades de esquema

**Por qué `-d` (downgrade) es necesario (línea 62):**

Después de `pm uninstall -k com.whatsapp`:
- Datos quedan en `/data/data/com.whatsapp/`
- Metadata del sistema recuerda versionCode de APK anterior

Si intentas `adb install LegacyWhatsApp.apk` sin `-d`:
```
Error: INSTALL_FAILED_VERSION_DOWNGRADE
```

Con flag `-d`:
```bash
adb install -r -d bin/LegacyWhatsApp.apk
# -r: Reemplaza manteniendo datos
# -d: Permite downgrade de versionCode
```

Android acepta instalación y mapea datos existentes a aplicación legacy, permitiendo `adb backup` funcional.

---

**Fin de Documentación de Tecnologías Android**
