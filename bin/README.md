# Binarios Externos Requeridos

Este directorio debe contener los binarios de **Android SDK Platform Tools** necesarios para la comunicación con dispositivos Android.

## Archivos Requeridos

```
bin/
├── adb.exe           # Android Debug Bridge ejecutable
├── AdbWinApi.dll     # Librería API de Windows
└── AdbWinUsbApi.dll  # Librería USB de Windows
```

## Descarga

### Opción 1: Android SDK Platform Tools (Recomendado)

1. Visita: https://developer.android.com/studio/releases/platform-tools
2. Descarga **SDK Platform-Tools for Windows**
3. Extrae el archivo ZIP
4. Copia los siguientes archivos a este directorio (`bin/`):
   - `platform-tools/adb.exe`
   - `platform-tools/AdbWinApi.dll`
   - `platform-tools/AdbWinUsbApi.dll`

### Opción 2: Instalación de Android Studio

Si ya tienes Android Studio instalado:

1. Los archivos están en: `C:\Users\{TuUsuario}\AppData\Local\Android\Sdk\platform-tools\`
2. Copia `adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll` a este directorio

## Verificación

Ejecuta en PowerShell:

```powershell
.\bin\adb.exe version
```

Deberías ver algo como:

```
Android Debug Bridge version 1.0.41
Version 34.0.5-10900879
```

## Notas

- **Tamaño aproximado**: ~10 MB total
- **Licencia**: Apache License 2.0 (Google)
- **Sistema**: Solo Windows (usa .exe y .dll)
- **Versión mínima**: ADB 1.0.40+

## Troubleshooting

### "adb.exe no se reconoce como comando"

Asegúrate de que los archivos estén en el directorio `bin/` dentro del proyecto.

### "No se puede cargar AdbWinApi.dll"

Verifica que las 3 DLLs estén en el mismo directorio que `adb.exe`.

### "device unauthorized"

En tu dispositivo Android:
1. Ve a Configuración → Opciones de Desarrollador
2. Revoca autorizaciones USB
3. Reconecta el dispositivo y autoriza la computadora

---

**No incluimos los archivos por:**
- Tamaño (~10MB)
- Licenciamiento (redistribución de binarios de Google)
- Actualizaciones frecuentes (mejor descargar la última versión)
