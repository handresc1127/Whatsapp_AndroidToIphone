# APKs Legacy de WhatsApp

Este directorio debe contener las versiones **legacy** (antiguas) de WhatsApp que NO cifran los backups con AES-256.

## Archivos Requeridos

```
apk/
├── LegacyWhatsApp.apk          # WhatsApp estándar ~v2.11.431
└── LegacyWhatsAppBusiness.apk  # WhatsApp Business legacy (opcional)
```

## ¿Por Qué Versiones Legacy?

Las versiones modernas de WhatsApp (v2.12+) cifran los backups de Android con **AES-256-GCM**, haciendo imposible extraer `msgstore.db` sin la clave de cifrado.

Las versiones legacy (~2.11.x):
- ✅ Generan backups SIN cifrar
- ✅ Permiten extracción de `msgstore.db`
- ✅ Compatibles con `adb backup`
- ⚠️ Requieren downgrade temporal

## Descarga

### WhatsApp Estándar Legacy

**Versión recomendada**: 2.11.431 (Agosto 2014)

1. Visita: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp/
2. Busca versión **2.11.431** o similar (2.11.x)
3. Descarga el APK
4. Renombra a `LegacyWhatsApp.apk`
5. Coloca en este directorio (`apk/`)

### WhatsApp Business Legacy

**Versión recomendada**: Similar a estándar (versiones tempranas)

1. Visita: https://www.apkmirror.com/apk/whatsapp-inc/whatsapp-business/
2. Busca versiones tempranas (pre-cifrado)
3. Descarga el APK
4. Renombra a `LegacyWhatsAppBusiness.apk`
5. Coloca en este directorio (`apk/`)

## ⚠️ Advertencias Legales

### Derechos de Autor

- WhatsApp y WhatsApp Business son **marcas registradas** de Meta Platforms, Inc.
- Los APKs son **propiedad de Meta** y están sujetos a sus términos de servicio
- **NO redistribuyas** los APKs descargados
- Solo para uso personal conforme a los términos de WhatsApp

### Seguridad

- ⚠️ Descarga SOLO de fuentes confiables (APKMirror, APKPure verificados)
- ⚠️ Verifica checksums SHA-256 cuando estén disponibles
- ⚠️ Escanea con antivirus antes de usar
- ⚠️ El downgrade temporal puede tener riesgos

### Proceso de Migración

El script:
1. **Desinstala** WhatsApp actual (mantiene datos con `-k`)
2. **Instala** versión legacy temporal
3. **Extrae** backup sin cifrar
4. **NO reinstala** la versión moderna (hazlo manualmente después)

## Verificación

Para verificar la versión del APK descargado, puedes usar:

```powershell
# Extraer información del APK (requiere aapt de Android SDK)
aapt dump badging LegacyWhatsApp.apk | Select-String "versionName"
```

Deberías ver algo como: `versionName='2.11.431'`

## Alternativas

### Si no puedes encontrar versiones legacy:

1. **Método de transferencia oficial**: WhatsApp ofrece migración Android→iOS en algunos países
2. **Herramientas comerciales**: Existen soluciones de pago (WazzapMigrator, Dr.Fone)
3. **Backup local cifrado**: Requiere conocer la contraseña de cifrado (64 caracteres)

## Notas Técnicas

### Cifrado en Versiones Modernas

- **Algoritmo**: AES-256-GCM
- **Key Derivation**: PBKDF2 con salt único
- **Resultado**: Archivo `.crypt14` o `.crypt15` en lugar de `.db`
- **Solución**: Versiones legacy NO usan cifrado end-to-end para backups

### Compatibilidad de Versiones

| Versión WhatsApp | Cifrado Backup | Compatible ADB |
|------------------|----------------|----------------|
| 2.11.x (Legacy)  | ❌ No          | ✅ Sí          |
| 2.12.x - 2.16.x  | ⚠️ Parcial     | ⚠️ Parcial     |
| 2.17.x+          | ✅ AES-256     | ❌ No          |

---

**No incluimos los APKs por:**
- Tamaño (~20-25MB cada uno)
- Derechos de autor (Meta Platforms, Inc.)
- Términos de servicio de WhatsApp
- Actualizaciones de seguridad
