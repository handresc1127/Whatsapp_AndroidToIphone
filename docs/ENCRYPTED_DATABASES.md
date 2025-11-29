# Manejo de Bases de Datos Encriptadas de WhatsApp

## 🔐 Información General

Desde versión 2.17.x (2016), WhatsApp encripta automáticamente las bases de datos locales usando AES-256-GCM. Los archivos tienen extensión `.crypt14` o `.crypt15`.

**Ubicación típica:**
```
/sdcard/Android/media/com.whatsapp[.w4b]/WhatsApp/Databases/
├── msgstore.db.crypt14          # Backup más reciente
├── msgstore-2025-11-29.1.db.crypt14
├── msgstore-2025-11-28.1.db.crypt14
└── ...
```

---

## 🚀 Proceso Automático (Requiere Root)

La herramienta intenta desencriptar automáticamente:

```powershell
PS> python main.py

[OK] Found: msgstore.db.crypt14 (11.86 MB)
[INFO] Database is encrypted, attempting decryption...
[INFO] Extracting encryption key...

# Si dispositivo tiene root habilitado:
[OK] Encryption key extracted
[OK] Database decrypted successfully

# Si no tiene root:
[WARNING] Could not extract encryption key (root required)
```

---

## 📋 Proceso Manual (Sin Root)

### Paso 1: Extraer Archivos del Dispositivo

**Archivos necesarios:**
1. **Base de datos encriptada:** `msgstore.db.crypt14`
2. **Clave de encriptación:** `key` (archivo de 158 bytes)

**Ubicaciones:**
```
Base de datos (público - no requiere root):
/sdcard/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db.crypt14

Clave (privado - requiere root o herramienta):
/data/data/com.whatsapp/files/key
```

### Paso 2: Obtener la Clave de Encriptación

#### Opción A: WhatsApp Key Extractor (Recomendado - No Root)

**Herramienta:** [WhatsAppKeyDBExtract](https://github.com/YuvrajRaghuvanshiS/WhatsApp-Key-Database-Extractor)

**Requisitos:**
- Python 3.8+
- ADB configurado
- Android 4.0+
- WhatsApp instalado

**Pasos:**
```powershell
# 1. Descargar herramienta
git clone https://github.com/YuvrajRaghuvanshiS/WhatsApp-Key-Database-Extractor.git
cd WhatsApp-Key-Database-Extractor

# 2. Conectar Android (USB debugging habilitado)
adb devices

# 3. Ejecutar extractor
python wa_kdbe.py

# 4. Seguir instrucciones en pantalla
# - Confirmar backup temporal en Android
# - Esperar extracción automática

# 5. Archivos extraídos en:
extracted/
├── key                     # Clave de encriptación ✅
├── msgstore.db.crypt14     # Base de datos ✅
└── wa.db                   # Cache de contactos
```

#### Opción B: ADB Root (Solo Dispositivos Rooteados)

```powershell
# 1. Habilitar root en ADB
adb root

# 2. Extraer clave
adb pull /data/data/com.whatsapp/files/key key

# 3. Extraer base de datos
adb pull /sdcard/Android/media/com.whatsapp/WhatsApp/Databases/msgstore.db.crypt14 msgstore.db.crypt14
```

#### Opción C: Backup Completo (Android 4.0-9.0)

```powershell
# 1. Crear backup ADB (sin password)
adb backup -f whatsapp.ab com.whatsapp

# 2. Extraer .ab file usando herramienta online o:
# https://github.com/nelenkov/android-backup-extractor

# 3. Buscar key en:
apps/com.whatsapp/f/key
```

### Paso 3: Desencriptar Base de Datos

#### Método 1: wa-crypt-tools (Recomendado)

**Herramienta:** [WhatsApp-Crypt14-Decrypter](https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter)

**Instalación:**
```powershell
# Instalar dependencias
pip install pycryptodome

# Descargar herramienta
git clone https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter.git
cd WhatsApp-Crypt14-Decrypter
```

**Desencriptación:**
```powershell
# Para .crypt14
python decrypt14.py key msgstore.db.crypt14 msgstore.db

# Para .crypt15
python decrypt15.py key msgstore.db.crypt15 msgstore.db

# Salida:
# [OK] Database decrypted: msgstore.db
```

#### Método 2: WhatsApp Viewer (GUI)

**Herramienta:** [WhatsApp Viewer](https://github.com/andreas-mausch/whatsapp-viewer)

**Características:**
- Interfaz gráfica
- Visualización de mensajes
- Exportación a SQLite plano
- Soporta .crypt5 a .crypt14

**Pasos:**
1. Descargar WhatsApp Viewer
2. File → Open → Seleccionar `msgstore.db.crypt14`
3. Proporcionar archivo `key` cuando lo pida
4. File → Export → SQLite Database
5. Guardar como `msgstore.db`

#### Método 3: Script Python Custom

```python
# decrypt_wa.py
from Crypto.Cipher import AES
import sys

def decrypt_crypt14(key_file, encrypted_file, output_file):
    # Leer clave
    with open(key_file, 'rb') as f:
        key = f.read()
    
    # Verificar tamaño de clave
    if len(key) != 158:
        print(f"Warning: Expected 158 bytes, got {len(key)}")
    
    # Leer archivo encriptado
    with open(encrypted_file, 'rb') as f:
        data = f.read()
    
    # Extraer componentes (crypt14 format)
    # Primeros 67 bytes: header
    # Siguiente 32 bytes: IV
    # Resto: datos encriptados + tag
    
    iv = data[67:67+32]
    encrypted = data[67+32:-16]
    tag = data[-16:]
    
    # Desencriptar usando AES-256-GCM
    cipher = AES.new(key[:32], AES.MODE_GCM, nonce=iv)
    decrypted = cipher.decrypt_and_verify(encrypted, tag)
    
    # Guardar
    with open(output_file, 'wb') as f:
        f.write(decrypted)
    
    print(f"[OK] Decrypted: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python decrypt_wa.py <key> <input.crypt14> <output.db>")
        sys.exit(1)
    
    decrypt_crypt14(sys.argv[1], sys.argv[2], sys.argv[3])
```

**Uso:**
```powershell
python decrypt_wa.py key msgstore.db.crypt14 msgstore.db
```

### Paso 4: Usar Base de Datos Desencriptada

```powershell
# 1. Copiar archivo desencriptado a proyecto
copy msgstore.db C:\path\to\Whatsapp_AndroidToIphone\out\android.db

# 2. Continuar migración
cd C:\path\to\Whatsapp_AndroidToIphone
python main.py

# 3. Script detectará archivo y continuará desde Step 4 (Migrate Database)
```

---

## 🔍 Verificación de Archivos

### Verificar Tipo de Archivo

```powershell
# Ver primeros bytes del archivo
Get-Content msgstore.db.crypt14 -Encoding Byte -TotalCount 20 | Format-Hex

# Archivo .crypt14 comienza con:
# 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
# -----------------------------------------------
# (header específico de WhatsApp)

# Archivo .db (SQLite) comienza con:
# 53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00
# "SQLite format 3\0"
```

### Verificar Tamaño de Clave

```powershell
# Windows PowerShell
(Get-Item key).Length
# Debe retornar: 158

# Git Bash / Linux / macOS
ls -l key
# Debe mostrar: 158 bytes
```

### Verificar Base de Datos Desencriptada

```powershell
# Intentar abrir con SQLite
sqlite3 msgstore.db

# Comandos SQLite:
sqlite> .tables
# Debe mostrar: chat, message, jid, etc.

sqlite> SELECT COUNT(*) FROM messages;
# Debe retornar número de mensajes

sqlite> .quit
```

---

## ⚠️ Problemas Comunes

### Error: "Invalid key size"

**Causa:** Archivo `key` corrupto o incompleto

**Solución:**
```powershell
# Verificar tamaño
(Get-Item key).Length  # Debe ser 158 bytes

# Re-extraer con WhatsApp Key Extractor
# Verificar que no sea un archivo de texto con path (debe ser binario)
```

### Error: "MAC verification failed"

**Causa:** Clave no corresponde a esa base de datos

**Solución:**
- Verificar que `key` y `msgstore.db.crypt14` sean de la misma instalación de WhatsApp
- Verificar versión de encriptación (.crypt14 vs .crypt15)
- Extraer archivos nuevamente del mismo dispositivo

### Error: "Unsupported crypt version"

**Causa:** Versión de encriptación muy nueva

**Solución:**
```powershell
# Verificar versión
# .crypt15 (WhatsApp 2.22.x+) requiere herramientas actualizadas

# Actualizar wa-crypt-tools:
cd WhatsApp-Crypt14-Decrypter
git pull origin master

# Usar decrypt15.py para .crypt15:
python decrypt15.py key msgstore.db.crypt15 msgstore.db
```

### Error: "Database is encrypted" después de desencriptar

**Causa:** Desencriptación incompleta o fallida

**Verificación:**
```powershell
# Ver primeros bytes
Get-Content msgstore.db -Encoding Byte -TotalCount 16 | Format-Hex

# Debe comenzar con "SQLite format 3"
# Si no, la desencriptación falló
```

---

## 🛡️ Consideraciones de Seguridad

### Protección de la Clave

⚠️ **El archivo `key` es altamente sensible:**
- Permite desencriptar TODAS las conversaciones de WhatsApp
- Debe ser eliminado después de la migración
- No compartir ni subir a internet
- No guardar en repositorios públicos

**Buenas prácticas:**
```powershell
# Crear carpeta temporal protegida
New-Item -ItemType Directory -Path "C:\Temp\WhatsApp_Migration" -Force

# Copiar archivos sensibles aquí
copy key C:\Temp\WhatsApp_Migration\
copy msgstore.db.crypt14 C:\Temp\WhatsApp_Migration\

# Después de migración, eliminar de forma segura
Remove-Item C:\Temp\WhatsApp_Migration -Recurse -Force

# Windows: usar cipher para borrado seguro
cipher /w:C:\Temp\WhatsApp_Migration
```

### Privacidad

- ⚠️ **NUNCA usar servicios online de desencriptación**
  - Tus conversaciones privadas se subirían a servidores desconocidos
  - Alto riesgo de filtración de datos
  
- ✅ **Usar solo herramientas locales**
  - wa-crypt-tools (GitHub - código abierto)
  - WhatsApp Key Extractor (GitHub - código abierto)
  - WhatsApp Viewer (GitHub - código abierto)

---

## 📚 Referencias

### Herramientas Recomendadas

| Herramienta | Propósito | Requiere Root | URL |
|-------------|-----------|---------------|-----|
| **WhatsApp Key Extractor** | Extraer clave sin root | ❌ No | [GitHub](https://github.com/YuvrajRaghuvanshiS/WhatsApp-Key-Database-Extractor) |
| **WhatsApp Crypt14 Decrypter** | Desencriptar .crypt14/15 | ❌ No | [GitHub](https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter) |
| **WhatsApp Viewer** | GUI para ver/exportar | ❌ No | [GitHub](https://github.com/andreas-mausch/whatsapp-viewer) |
| **Android Backup Extractor** | Extraer .ab backups | ❌ No | [GitHub](https://github.com/nelenkov/android-backup-extractor) |

### Documentación Técnica

- [WhatsApp Encryption Format](https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter/wiki/Encryption-Format)
- [AES-GCM Documentation](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
- [Android Backup Format](https://nelenkov.blogspot.com/2012/06/unpacking-android-backups.html)

### Versiones de Encriptación

| Versión | Algoritmo | WhatsApp Version | Año |
|---------|-----------|------------------|-----|
| .crypt5 | AES-192-ECB | 2.11.x - 2.12.x | 2013-2014 |
| .crypt7 | AES-256-ECB | 2.12.x - 2.16.x | 2014-2015 |
| .crypt8 | AES-256-GCM | 2.16.x - 2.17.x | 2015-2016 |
| .crypt12 | AES-256-GCM (improved) | 2.17.x - 2.21.x | 2016-2021 |
| **.crypt14** | AES-256-GCM (current) | 2.21.x - 2.22.x | 2021-2023 |
| **.crypt15** | AES-256-GCM (latest) | 2.22.x+ | 2023+ |

---

## 🤝 Soporte

Para problemas con desencriptación:

1. **Verificar archivos:** Tamaños correctos (key=158 bytes, .crypt14>1MB)
2. **Verificar herramientas:** Versiones actualizadas de wa-crypt-tools
3. **Consultar documentación:** [USAGE.md](USAGE.md) - Troubleshooting
4. **Issues conocidos:** [GitHub Issues](https://github.com/EliteAndroidApps/WhatsApp-Crypt14-Decrypter/issues)

---

**Última actualización:** Noviembre 29, 2025  
**Versiones soportadas:** .crypt12, .crypt14, .crypt15
