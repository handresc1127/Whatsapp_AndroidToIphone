# Tecnologías iOS y SQLite - WhatsApp Migration

## 1. iTunes/Finder Backup (iOS)

### Estructura de Directorios
```
{GUID}/                           # ID único del dispositivo iOS
├── Manifest.db                   # Base de datos con índice de archivos
├── Manifest.plist               # Metadata del backup
├── Info.plist                   # Información del dispositivo
├── Status.plist                 # Estado del backup
└── {2chars}/                    # Subdirectorios de 2 caracteres
    └── {fileID_completo}        # Archivo real (40 caracteres SHA-1)
```

**Ejemplo real:**
```
/Users/nombre/Library/Application Support/MobileSync/Backup/00008030-001E34CC3662802E/
├── Manifest.db
├── 7c/
│   └── 7c7fba66680ef796b916b067077cc246adacf01d
├── b8/
│   └── b8548dc30aa1030df0ce18ef08b882cf7ab5212f
└── 1b/
    └── 1b432994e958845fffe8e2f190f26d1511534088
```

### Manifest.db

**Propósito:**
- Base de datos SQLite que actúa como índice/catálogo de todos los archivos del backup
- Mapea rutas lógicas de apps a hashes SHA-1 físicos
- Permite localizar archivos sin conocer su ubicación física

**Tabla `Files` (principal):**
```sql
CREATE TABLE Files (
    fileID TEXT PRIMARY KEY,          -- Hash SHA-1 (40 chars) del archivo
    domain TEXT,                       -- Dominio de la app (ej: AppDomainGroup-group.net.whatsapp...)
    relativePath TEXT,                 -- Ruta original en el dispositivo
    flags INTEGER,                     -- Tipo: 1=archivo, 2=directorio
    file BLOB                          -- Metadata en formato bplist
);
```

**Query SQL usada en el proyecto:**
```sql
SELECT fileID 
FROM Files 
WHERE relativePath = 'ChatStorage.sqlite' 
  AND domain = 'AppDomainGroup-group.net.whatsapp.WhatsApp.shared'
```

**Explicación:**
- `relativePath`: Nombre del archivo en el contenedor de la app (ChatStorage.sqlite)
- `domain`: Identifica el grupo de contenedor compartido de WhatsApp
- `fileID`: Devuelve el hash SHA-1 que se usa para ubicar el archivo físico

**IDs de archivos WhatsApp (constantes):**
```python
# WhatsApp estándar
MESSAGE_DB   = "7c7fba66680ef796b916b067077cc246adacf01d"  # ChatStorage.sqlite
CONTACT_DB   = "b8548dc30aa1030df0ce18ef08b882cf7ab5212f"  # ContactsV2.sqlite
CALL_DB      = "1b432994e958845fffe8e2f190f26d1511534088"  # CallHistory.sqlite
DOMAIN       = "AppDomainGroup-group.net.whatsapp.WhatsApp.shared"

# WhatsApp Business
MESSAGE_DB   = "724bd3b98b18518b455a87c1f3ac3a0d189c4466"
CONTACT_DB   = "d7246a707f51ddf8b17ee2dddabd9e0a4da5c552"
CALL_DB      = "b463f7c4365eefc5a8723930d97928d4e907c603"
DOMAIN       = "AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared"
```

### Organización de Archivos (Subdirectorios de 2 caracteres)

**Razón técnica:**
- Sistema de archivos tiene límites de archivos por directorio (~32K en HFS+)
- Backup puede contener 100K+ archivos (apps, fotos, mensajes)
- Distribución en 256 subdirectorios (00-FF en hex) = ~390 archivos por carpeta
- Mejora rendimiento de búsqueda/acceso al evitar directorios enormes

**Cómo funciona:**
1. Calcular SHA-1 del archivo → `7c7fba66680ef796b916b067077cc246adacf01d`
2. Tomar primeros 2 caracteres → `7c`
3. Crear/usar subdirectorio `7c/`
4. Guardar archivo como `7c/7c7fba66680ef796b916b067077cc246adacf01d`

**Ventajas:**
- **Balance de carga:** Distribución uniforme (SHA-1 es hash aleatorio)
- **Escalabilidad:** Agregar millones de archivos sin degradación
- **Compatibilidad:** Funciona en FAT32, NTFS, HFS+, APFS
- **Simplicidad:** Evita estructuras jerárquicas complejas

---

## 2. ChatStorage.sqlite (iOS)

### Contenido
Base de datos Core Data (framework de persistencia de Apple) que almacena:
- **Mensajes:** Texto, multimedia, ubicaciones, contactos, documentos
- **Conversaciones:** Chats individuales y grupales
- **Contactos:** Información de participantes con JID (Jabber ID)
- **Medios:** Referencias a archivos multimedia con rutas locales
- **Estado de mensajes:** Enviado, entregado, leído, estrellado, eliminado

### Estructura de Tablas (Prefijo `ZWA`)

**Core Data usa prefijos automáticos:**
- `Z_` → Tablas de metadata de Core Data
- `ZWA` → Entidades de WhatsApp (WhatsApp prefijo `WA`)

**Tablas principales:**

#### `ZWAMESSAGE` (Mensajes)
```sql
-- Campos principales
Z_PK                INTEGER PRIMARY KEY,      -- ID único del mensaje
ZCHATSESSION        INTEGER,                  -- FK a ZWACHATSESSION
ZFROMJID            TEXT,                     -- JID del remitente
ZMESSAGEDATE        REAL,                     -- Timestamp (Apple epoch: 2001-01-01)
ZTEXT               TEXT,                     -- Contenido del mensaje
ZMESSAGETYPE        INTEGER,                  -- 0=texto, 1=imagen, 2=audio, etc.
ZISFROMME           INTEGER,                  -- 1=enviado, 0=recibido
ZISFORWARDED        INTEGER,                  -- 1=reenviado
ZSTARRED            INTEGER,                  -- 1=destacado
ZGROUPMEMBER        TEXT,                     -- JID del miembro en grupos
ZMEDIAITEM          INTEGER                   -- FK a ZWAMEDIAITEM
```

**Tipos de mensaje (`ZMESSAGETYPE`):**
- 0 = Texto
- 1 = Imagen
- 2 = Audio
- 3 = Video
- 4 = Contacto
- 5 = Ubicación
- 6 = Documento
- 7 = Sticker
- 8 = GIF
- 15 = Mensaje eliminado

#### `ZWACHATSESSION` (Conversaciones)
```sql
Z_PK                INTEGER PRIMARY KEY,
ZCONTACTJID         TEXT,                     -- JID del chat (usuario o grupo)
ZPARTNERNAME        TEXT,                     -- Nombre del contacto
ZLASTMESSAGEDATE    REAL,                     -- Fecha del último mensaje
ZMESSAGECOUNTER     INTEGER,                  -- Total de mensajes
ZUNREADCOUNT        INTEGER,                  -- Mensajes no leídos
ZARCHIVED           INTEGER,                  -- 1=archivado
ZGROUPINFO          INTEGER                   -- FK a ZWAGROUPINFO (si es grupo)
```

#### `ZWAMEDIAITEM` (Archivos Multimedia)
```sql
Z_PK                INTEGER PRIMARY KEY,
ZMESSAGE            INTEGER,                  -- FK a ZWAMESSAGE
ZMEDIALOCALPATH     TEXT,                     -- Ruta local en dispositivo
ZMEDIAURL           TEXT,                     -- URL del servidor WhatsApp
ZFILESIZE           INTEGER,                  -- Tamaño en bytes
ZMEDIAKEY           BLOB,                     -- Clave de encriptación E2E
ZVCARDSTRING        TEXT,                     -- Para contactos vCard
ZLATITUDE           REAL,                     -- Para ubicaciones
ZLONGITUDE          REAL
```

#### `ZWAGROUPINFO` (Información de Grupos)
```sql
Z_PK                INTEGER PRIMARY KEY,
ZNAME               TEXT,                     -- Nombre del grupo
ZCREATORJID         TEXT,                     -- JID del creador
ZPICTUREID          TEXT,                     -- ID de la foto del grupo
ZSUBJECT            TEXT                      -- Descripción del grupo
```

#### `ZWAGROUPMEMBER` (Miembros de Grupos)
```sql
Z_PK                INTEGER PRIMARY KEY,
ZCHATSESSION        INTEGER,                  -- FK a ZWACHATSESSION
ZMEMBERJID          TEXT,                     -- JID del miembro
ZISADMIN            INTEGER                   -- 1=administrador
```

#### `ZWAPROFILEPUSHNAME` (Nombres de Perfil)
```sql
Z_PK                INTEGER PRIMARY KEY,
ZPUSHNAME           TEXT,                     -- Nombre mostrado en WhatsApp
ZJID                TEXT                      -- JID del contacto
```

### Formato de Datos Específico

**Timestamps (Apple Epoch):**
```python
# iOS usa segundos desde 2001-01-01 00:00:00 UTC
APPLE_TIME = 978307200  # Offset Unix Epoch → Apple Epoch
unix_timestamp = apple_timestamp + APPLE_TIME

# Ejemplo:
# Apple: 690566400 → Unix: 1668873600 (2022-11-19)
```

**JID (Jabber ID) - Identificador de Usuario:**
```
# Individual: {número}@s.whatsapp.net
573001234567@s.whatsapp.net

# Grupo: {id}-{timestamp}@g.us
120363012345678901@g.us

# Broadcast: {id}@broadcast
12345678901234@broadcast

# Status: status@broadcast
```

**Metadata BLOB (bplist):**
- Archivos multimedia incluyen metadata en formato Binary Property List
- Contiene: fecha de creación, modificación, tipo MIME, dimensiones

---

## 3. msgstore.db (Android)

### Contenido
Base de datos SQLite tradicional (sin ORM) que almacena:
- **Mensajes:** Similar a iOS pero con esquema diferente
- **Chats:** Lista de conversaciones activas
- **Referencias a medios:** Rutas a archivos en `/WhatsApp/Media/`
- **Información de contactos:** JIDs y nombres

### Estructura de Tablas Principales

#### `messages` (Mensajes)
```sql
-- Campos principales
_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
key_remote_jid      TEXT,                     -- JID del chat (individual/grupo)
key_from_me         INTEGER,                  -- 1=enviado, 0=recibido
key_id              TEXT,                     -- ID único del mensaje
status              INTEGER,                  -- 0=pendiente, 13=entregado, etc.
data                TEXT,                     -- Contenido del mensaje
timestamp           INTEGER,                  -- Unix timestamp (milisegundos)
media_url           TEXT,                     -- URL del archivo multimedia
media_mime_type     TEXT,                     -- image/jpeg, audio/mpeg, etc.
media_wa_type       INTEGER,                  -- 1=imagen, 2=audio, 3=video, etc.
media_size          INTEGER,                  -- Tamaño en bytes
media_name          TEXT,                     -- Nombre del archivo
media_caption       TEXT,                     -- Descripción de la imagen/video
latitude            REAL,                     -- Para ubicaciones
longitude           REAL,
quoted_row_id       INTEGER,                  -- FK a mensaje citado
message_type        INTEGER                   -- 0=texto, 1=imagen, etc.
```

**Estados de mensaje (`status`):**
- 0 = Pendiente de envío
- 4 = Enviado al servidor
- 5 = Entregado al destinatario
- 13 = Leído por el destinatario
- -1 = Error al enviar

#### `chat` (Conversaciones)
```sql
_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
jid_row_id          INTEGER,                  -- FK a tabla jid
hidden              INTEGER,                  -- 0=visible, 1=archivado
subject             TEXT,                     -- Nombre del chat/grupo
created_timestamp   INTEGER,                  -- Fecha de creación
display_message_row_id INTEGER,               -- Último mensaje visible
last_message_row_id INTEGER,                  -- FK al último mensaje
last_read_message_row_id INTEGER,
last_read_receipt_sent_message_row_id INTEGER,
archived            INTEGER,
sort_timestamp      INTEGER,
mod_tag             INTEGER,
gen                 INTEGER
```

#### `jid` (Jabber IDs)
```sql
_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
user                TEXT,                     -- Parte antes del @
server              TEXT,                     -- Parte después del @
agent               INTEGER,
device              INTEGER,
type                INTEGER,                  -- 0=individual, 1=grupo, etc.
raw_string          TEXT                      -- JID completo
```

**Tipos de JID (`type`):**
```python
class JidType:
    PM = 0              # Mensaje privado (individual)
    GROUP = 1           # Grupo
    SYSTEM_BROADCAST = 5 # Broadcast del sistema
    STATUS = 11         # Estados de WhatsApp
```

#### `message_media` (Referencias a Medios)
```sql
message_row_id      INTEGER PRIMARY KEY,      -- FK a messages
file_path           TEXT,                     -- Ruta local: Media/WhatsApp Images/...
file_size           INTEGER,
mime_type           TEXT,
media_key           BLOB,                     -- Clave de encriptación
file_hash           TEXT,                     -- SHA256 del archivo
media_key_timestamp INTEGER,
message_url         TEXT,                     -- URL del servidor
direct_path         TEXT,
media_enc_hash      TEXT,
media_duration      INTEGER                   -- Para audio/video
```

#### `message_quoted` (Mensajes Citados)
```sql
_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
key_remote_jid      TEXT,
key_from_me         INTEGER,
key_id              TEXT,
status              INTEGER,
needs_push          INTEGER,
data                TEXT,
timestamp           INTEGER,
media_caption       TEXT,
media_name          TEXT,
media_wa_type       INTEGER,
media_size          INTEGER,
media_url           TEXT,
media_mime_type     TEXT,
participant         TEXT
```

#### `group_participants` (Miembros de Grupos)
```sql
_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
gjid                TEXT,                     -- JID del grupo
jid                 TEXT,                     -- JID del miembro
admin               INTEGER,                  -- 0=miembro, 1=admin, 2=super admin
pending             INTEGER
```

### Formato de Datos Específico

**Timestamps (Unix):**
```python
# Android usa milisegundos desde 1970-01-01 00:00:00 UTC
unix_timestamp_ms = 1668873600000  # 2022-11-19
unix_timestamp_s = unix_timestamp_ms / 1000
```

**Rutas de archivos multimedia:**
```
# Estructura en Android
/sdcard/WhatsApp/Media/WhatsApp Images/IMG-20221119-WA0001.jpg
/sdcard/WhatsApp/Media/WhatsApp Audio/AUD-20221119-WA0001.opus
/sdcard/WhatsApp/Media/WhatsApp Video/VID-20221119-WA0001.mp4
/sdcard/WhatsApp/Media/WhatsApp Documents/DOC-20221119-WA0001.pdf
```

---

## 4. Compatibilidad entre Bases de Datos

### Diferencias Críticas

#### **1. Nombres de Tablas**
| Concepto          | iOS (Core Data)         | Android (SQLite)       |
|-------------------|-------------------------|------------------------|
| Mensajes          | `ZWAMESSAGE`            | `messages`             |
| Conversaciones    | `ZWACHATSESSION`        | `chat`                 |
| Multimedia        | `ZWAMEDIAITEM`          | `message_media`        |
| Grupos            | `ZWAGROUPINFO`          | Metadata en `chat`     |
| Miembros de grupo | `ZWAGROUPMEMBER`        | `group_participants`   |
| Contactos         | `ZWAPROFILEPUSHNAME`    | Metadata en `jid`      |

#### **2. IDs Internos (INCOMPATIBLES)**
```python
# iOS usa Z_PK (Primary Key de Core Data)
ios_message_id = 12345  # Secuencial en base de datos iOS

# Android usa _id con autoincrement
android_message_id = 67890  # Secuencial en base de datos Android

# ⚠️ NO SON INTERCAMBIABLES - Requieren remapeo completo
```

**Solución:** Crear tabla de mapeo `id_mapping`:
```sql
CREATE TABLE id_mapping (
    ios_table TEXT,
    ios_id INTEGER,
    android_table TEXT,
    android_id INTEGER,
    PRIMARY KEY (ios_table, ios_id)
);
```

#### **3. Timestamps (Formatos Diferentes)**
```python
# iOS: Segundos desde 2001-01-01 (Apple Epoch)
ios_timestamp = 690566400.0
APPLE_EPOCH = 978307200
unix_timestamp = ios_timestamp + APPLE_EPOCH  # 1668873600

# Android: Milisegundos desde 1970-01-01 (Unix Epoch)
android_timestamp = unix_timestamp * 1000  # 1668873600000

# Conversión:
def ios_to_android_timestamp(ios_ts):
    return int((ios_ts + 978307200) * 1000)

def android_to_ios_timestamp(android_ts):
    return (android_ts / 1000) - 978307200
```

#### **4. Estructura de Contactos**
**iOS (Relacional):**
```sql
-- Contacto en tabla separada
SELECT ZPUSHNAME 
FROM ZWAPROFILEPUSHNAME 
WHERE ZJID = '573001234567@s.whatsapp.net'
```

**Android (Desnormalizado):**
```sql
-- Información en tabla jid
SELECT user, server, raw_string 
FROM jid 
WHERE raw_string = '573001234567@s.whatsapp.net'
```

#### **5. Rutas de Archivos Multimedia**
```python
# iOS: Ruta relativa al contenedor de la app
ios_path = "Message/Media/IMG-20221119-WA0001.jpg"

# Android: Ruta absoluta en almacenamiento externo
android_path = "/sdcard/WhatsApp/Media/WhatsApp Images/IMG-20221119-WA0001.jpg"

# ⚠️ Los archivos deben copiarse y las rutas actualizarse
```

#### **6. Encriptación de Medios**
```python
# iOS: media_key en ZWAMEDIAITEM (BLOB)
# Android: media_key en message_media (BLOB)

# ✅ Formato compatible - Misma clave E2E de WhatsApp
# Puede reutilizarse si los archivos se copian correctamente
```

---

## Rol de `migrate.py`

### Tareas Críticas del Script

#### **1. Mapeo de Esquemas**
```python
def map_ios_to_android_schema():
    """
    Convierte estructura Core Data (iOS) a SQLite estándar (Android)
    """
    schema_mapping = {
        # Tablas
        'ZWAMESSAGE': 'messages',
        'ZWACHATSESSION': 'chat',
        'ZWAMEDIAITEM': 'message_media',
        
        # Campos de mensaje
        'ZTEXT': 'data',
        'ZMESSAGEDATE': 'timestamp',
        'ZFROMJID': 'key_remote_jid',
        'ZISFROMME': 'key_from_me',
        
        # Campos de chat
        'ZCONTACTJID': 'jid_row_id',  # Requiere lookup en jid
        'ZPARTNERNAME': 'subject',
        'ZLASTMESSAGEDATE': 'sort_timestamp',
    }
    return schema_mapping
```

#### **2. Conversión de Formatos**

**Timestamps:**
```python
def convert_timestamp(ios_timestamp):
    """
    iOS: Segundos desde 2001-01-01
    Android: Milisegundos desde 1970-01-01
    """
    APPLE_EPOCH = 978307200
    unix_seconds = ios_timestamp + APPLE_EPOCH
    return int(unix_seconds * 1000)
```

**JIDs:**
```python
def normalize_jid(jid_string):
    """
    Asegura formato correcto de JID para Android
    """
    # iOS puede tener variaciones
    if '@' not in jid_string:
        jid_string += '@s.whatsapp.net'
    
    # Crear entrada en tabla jid
    user, server = jid_string.split('@')
    jid_id = insert_jid(user, server, jid_string)
    return jid_id
```

**Tipos de Mensaje:**
```python
def map_message_type(ios_type, ios_media_type):
    """
    Mapea ZMESSAGETYPE (iOS) a message_type (Android)
    """
    type_mapping = {
        0: 0,   # Texto
        1: 1,   # Imagen
        2: 2,   # Audio
        3: 3,   # Video
        4: 4,   # Contacto
        5: 5,   # Ubicación
        6: 9,   # Documento
        7: 20,  # Sticker
        15: 0   # Eliminado (convertir a texto vacío)
    }
    return type_mapping.get(ios_type, 0)
```

#### **3. Fusión de Datos**

**Mensajes:**
```python
def merge_messages(ios_db, android_db, id_map):
    """
    Combina mensajes de iOS con los existentes en Android
    """
    # 1. Leer mensajes de iOS
    ios_cursor = ios_db.execute("""
        SELECT Z_PK, ZCHATSESSION, ZTEXT, ZMESSAGEDATE, 
               ZFROMJID, ZISFROMME, ZMESSAGETYPE
        FROM ZWAMESSAGE
        ORDER BY ZMESSAGEDATE
    """)
    
    # 2. Para cada mensaje iOS
    for row in ios_cursor:
        # 3. Convertir timestamp
        android_timestamp = convert_timestamp(row['ZMESSAGEDATE'])
        
        # 4. Buscar chat correspondiente
        ios_chat_id = row['ZCHATSESSION']
        android_chat_id = id_map.get_android_id('chat', ios_chat_id)
        
        # 5. Verificar duplicados (por timestamp + JID)
        if not message_exists(android_db, android_timestamp, row['ZFROMJID']):
            # 6. Insertar en Android
            android_id = insert_message(
                android_db,
                key_remote_jid=get_jid_id(row['ZFROMJID']),
                key_from_me=row['ZISFROMME'],
                data=row['ZTEXT'],
                timestamp=android_timestamp,
                message_type=map_message_type(row['ZMESSAGETYPE']),
            )
            
            # 7. Guardar mapeo de IDs
            id_map.add_mapping('ZWAMESSAGE', row['Z_PK'], 'messages', android_id)
```

**Archivos Multimedia:**
```python
def copy_and_remap_media(ios_backup, android_media_dir, ios_db, android_db):
    """
    Copia archivos multimedia y actualiza referencias
    """
    # 1. Leer referencias de medios de iOS
    ios_cursor = ios_db.execute("""
        SELECT Z_PK, ZMESSAGE, ZMEDIALOCALPATH, ZFILESIZE, 
               ZMEDIAKEY, ZMEDIAURL
        FROM ZWAMEDIAITEM
    """)
    
    for row in ios_cursor:
        # 2. Localizar archivo en backup iOS
        ios_file_path = locate_media_in_backup(ios_backup, row['ZMEDIALOCALPATH'])
        
        # 3. Generar ruta Android
        android_file_path = generate_android_media_path(
            media_type=guess_media_type(row['ZMEDIALOCALPATH']),
            filename=extract_filename(row['ZMEDIALOCALPATH'])
        )
        
        # 4. Copiar archivo
        copy_file(ios_file_path, android_media_dir + android_file_path)
        
        # 5. Obtener android_message_id del mapeo
        ios_msg_id = row['ZMESSAGE']
        android_msg_id = id_map.get_android_id('messages', ios_msg_id)
        
        # 6. Insertar referencia en Android
        insert_media_reference(
            android_db,
            message_row_id=android_msg_id,
            file_path=android_file_path,
            file_size=row['ZFILESIZE'],
            media_key=row['ZMEDIAKEY'],
            message_url=row['ZMEDIAURL']
        )
```

**Chats/Conversaciones:**
```python
def merge_chats(ios_db, android_db):
    """
    Combina conversaciones de iOS con las de Android
    """
    ios_cursor = ios_db.execute("""
        SELECT Z_PK, ZCONTACTJID, ZPARTNERNAME, 
               ZLASTMESSAGEDATE, ZUNREADCOUNT, ZARCHIVED
        FROM ZWACHATSESSION
    """)
    
    for row in ios_cursor:
        # 1. Normalizar JID
        jid_id = normalize_jid(row['ZCONTACTJID'])
        
        # 2. Verificar si chat ya existe en Android
        existing_chat = android_db.execute("""
            SELECT _id FROM chat WHERE jid_row_id = ?
        """, (jid_id,)).fetchone()
        
        if existing_chat:
            # Actualizar solo si iOS tiene mensajes más recientes
            android_id = existing_chat['_id']
            update_chat_if_newer(android_db, android_id, row)
        else:
            # Crear nuevo chat
            android_id = insert_chat(
                android_db,
                jid_row_id=jid_id,
                subject=row['ZPARTNERNAME'],
                sort_timestamp=convert_timestamp(row['ZLASTMESSAGEDATE']),
                archived=row['ZARCHIVED']
            )
        
        # Guardar mapeo
        id_map.add_mapping('ZWACHATSESSION', row['Z_PK'], 'chat', android_id)
```

#### **4. Validación y Verificación**
```python
def verify_migration(ios_db, android_db, id_map):
    """
    Verifica integridad de la migración
    """
    # 1. Contar mensajes
    ios_msg_count = ios_db.execute("SELECT COUNT(*) FROM ZWAMESSAGE").fetchone()[0]
    android_msg_count = android_db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    
    print(f"Mensajes iOS: {ios_msg_count}")
    print(f"Mensajes Android: {android_msg_count}")
    
    # 2. Verificar mapeo completo
    mapped_count = id_map.count_mappings('ZWAMESSAGE')
    if mapped_count != ios_msg_count:
        print(f"⚠️ ADVERTENCIA: Solo {mapped_count}/{ios_msg_count} mensajes mapeados")
    
    # 3. Verificar archivos multimedia
    verify_media_files(android_media_dir)
    
    # 4. Validar integridad de FKs
    validate_foreign_keys(android_db)
```

---

## Resumen Técnico

### Flujo de Migración

```
1. EXTRAER iOS BACKUP
   ├─ Localizar Manifest.db
   ├─ Query para fileID de ChatStorage.sqlite
   ├─ Copiar {fileID[:2]}/{fileID} → ChatStorage.sqlite
   └─ Extraer archivos multimedia del backup

2. LEER BASES DE DATOS
   ├─ Abrir ChatStorage.sqlite (iOS) - Core Data
   ├─ Abrir msgstore.db (Android) - SQLite estándar
   └─ Crear id_mapping para relacionar IDs

3. MAPEO DE ESQUEMAS
   ├─ ZWAMESSAGE → messages
   ├─ ZWACHATSESSION → chat + jid
   ├─ ZWAMEDIAITEM → message_media
   └─ Convertir formatos de datos

4. CONVERSIÓN DE DATOS
   ├─ Timestamps: Apple Epoch → Unix milisegundos
   ├─ JIDs: Normalizar y crear entradas en tabla jid
   ├─ Tipos de mensaje: Mapear códigos iOS → Android
   └─ Rutas de archivos: Relativas iOS → Absolutas Android

5. FUSIÓN DE MENSAJES
   ├─ Detectar duplicados (timestamp + JID)
   ├─ Insertar mensajes únicos de iOS en Android
   ├─ Mantener orden cronológico
   └─ Guardar mapeo de IDs

6. COPIAR MULTIMEDIA
   ├─ Localizar archivos en backup iOS
   ├─ Copiar a estructura Android (/WhatsApp/Media/...)
   ├─ Actualizar rutas en message_media
   └─ Conservar claves de encriptación

7. ACTUALIZAR CONVERSACIONES
   ├─ Fusionar metadatos de chats
   ├─ Recalcular contadores (mensajes, no leídos)
   └─ Actualizar timestamp de último mensaje

8. VERIFICAR INTEGRIDAD
   ├─ Validar conteo de mensajes
   ├─ Verificar existencia de archivos multimedia
   ├─ Comprobar FKs (foreign keys)
   └─ Generar reporte de migración
```

### Desafíos Principales

1. **Incompatibilidad de ORM:** iOS usa Core Data (tablas con prefijo Z), Android usa SQLite puro
2. **Epochs diferentes:** Apple Epoch (2001) vs Unix Epoch (1970) + conversión segundos/milisegundos
3. **IDs no transferibles:** Requiere tabla de mapeo completa para relaciones
4. **Rutas de archivos:** Estructura de directorios completamente diferente
5. **Detección de duplicados:** Necesario para fusión incremental sin duplicar mensajes

### Criterios de Éxito

✅ **Migración exitosa cuando:**
- Total de mensajes iOS = Mensajes nuevos insertados en Android
- Todos los archivos multimedia copiados y accesibles
- Conversaciones ordenadas cronológicamente correctas
- Sin errores de FK (foreign key constraints)
- Medios descargados funcionan con claves de encriptación

---

**Referencias del código fuente analizado:**
- WhatsApp-Chat-Exporter: [ios_handler.py](https://github.com/KnugiHK/WhatsApp-Chat-Exporter)
- iOS Media Handler: [ios_media_handler.py](https://github.com/KnugiHK/WhatsApp-Chat-Exporter)
- Android Handler: [android_handler.py](https://github.com/KnugiHK/WhatsApp-Chat-Exporter)

**Documentado:** 28 de noviembre de 2025
