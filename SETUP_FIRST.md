# ⚙️ Setup Instructions - READ THIS FIRST

**IMPORTANTE: Ejecuta el setup ANTES de usar el script de migración.**

## 🚀 Inicio Rápido

### Paso 1: Ejecutar Setup

```powershell
python setup.py
```

El script de setup verificará automáticamente:
- ✅ ADB (Android Debug Bridge) - Local o del sistema
- ✅ APK Legacy de WhatsApp - Te guiará para descargarlo
- ✅ Script de migración (migrate.py)
- ✅ Directorios necesarios

### Paso 2: Seguir Instrucciones

Si falta algún componente, el setup te mostrará instrucciones claras para instalarlo.

### Paso 3: Ejecutar Migración

Una vez que el setup esté completo:

```powershell
python main.py
```

---

## 📋 Componentes Requeridos

### 1. ADB (Android Debug Bridge)

**Opción A: Local al proyecto (Recomendado)**
- Descarga: https://developer.android.com/tools/releases/platform-tools
- Extrae: `adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll`
- Copia a: `bin/`

**Opción B: Del sistema (PATH)**
- Instala Android Platform Tools
- Agrega al PATH de Windows
- El script lo detectará automáticamente

### 2. WhatsApp Legacy APK (v2.11.431)

**POR QUÉ ES NECESARIO:**
- Versiones modernas (2.12+) cifran backups con AES-256
- Versión 2.11.431 NO cifra → permite extraer msgstore.db
- Es temporal: solo se usa para crear el backup

**CÓMO OBTENERLO:**
1. Visita: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/
2. Busca: WhatsApp 2.11.431 (Agosto 2014)
3. Descarga el APK
4. Renombra a: `LegacyWhatsApp.apk`
5. Guarda en: `apk/`

⚠️ **ADVERTENCIA LEGAL:**
- WhatsApp es marca registrada de Meta Platforms, Inc.
- Solo para uso personal conforme a términos de servicio
- NO redistribuir el APK

### 3. migrate.py

Debe estar en la raíz del proyecto (ya incluido).

---

## ✅ Verificación Manual

Si prefieres verificar manualmente:

```powershell
# 1. Verificar ADB
.\bin\adb.exe version
# O si está en PATH:
adb version

# 2. Verificar APK
Test-Path apk\LegacyWhatsApp.apk

# 3. Verificar script de migración
Test-Path migrate.py

# 4. Listar estructura
tree /F
```

---

## 🆘 Solución de Problemas

### "ADB not found"
- Descarga Platform Tools
- Ver: `bin/README.md`

### "APK not found"
- Descarga de APKMirror (v2.11.431)
- Verifica el nombre: `LegacyWhatsApp.apk`
- Ubicación correcta: `apk/`

### "migrate.py not found"
- Verifica que estás en el directorio correcto del proyecto
- Clona nuevamente el repositorio si falta

---

## 📂 Estructura Esperada

Después del setup:

```
Whatsapp_AndroidToIphone/
├── apk/
│   └── LegacyWhatsApp.apk    ← Descargado manualmente
├── bin/
│   ├── adb.exe               ← Descargado (o en PATH)
│   ├── AdbWinApi.dll
│   └── AdbWinUsbApi.dll
├── logs/                     ← Creado por setup
├── backups/                  ← Creado por setup
├── setup.py                  ← Script de setup
├── main.py                   ← Script principal
└── migrate.py                ← Script de migración
```

---

## 🎯 Siguiente Paso

Una vez completado el setup:

**Ver:** `docs/USAGE.md` para instrucciones completas de migración.

---

**Fecha de actualización:** Noviembre 28, 2025
