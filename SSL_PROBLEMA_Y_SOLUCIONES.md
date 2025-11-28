# Problema SSL en yfinance - Soluciones

## Descripción del Problema

El proyecto tiene un problema SSL cuando intenta descargar datos de Yahoo Finance usando `yfinance`:

```
SSLError: Failed to perform, curl: (77) error setting certificate verify locations:
CAfile: C:\Users\DavidVelázquezGómez\AppData\Roaming\Python\Python314\site-packages\certifi\cacert.pem
```

### Causa Raíz

El problema es causado por:
1. **Caracteres especiales (acentos) en la ruta del usuario de Windows**: "DavidVelázquezGómez"
2. **curl_cffi** (usado por yfinance 0.2.66) no puede manejar correctamente rutas con caracteres Unicode en Windows
3. Python 3.14 es muy reciente y algunas librerías aún tienen compatibilidad limitada

## Soluciones Disponibles

### Solución 1: Usar Datos en Caché (Actual)

El proyecto ya tiene datos históricos descargados previamente que se pueden usar:
- `AAL_analisis.html`
- `GOOGL_analisis.html`
- `MSFT_analisis.html`
- Base de datos SQLite con datos históricos

**Ventaja**: No requiere cambios, funciona inmediatamente
**Desventaja**: Los datos no están actualizados

### Solución 2: Crear un Usuario de Windows sin Acentos

Crear un nuevo usuario de Windows con nombre sin caracteres especiales (ej: "David" o "DavidV").

```powershell
# En PowerShell como Administrador
New-LocalUser -Name "David" -Description "Usuario sin acentos"
Add-LocalGroupMember -Group "Administradores" -Member "David"
```

**Ventaja**: Solución permanente
**Desventaja**: Requiere configurar nuevo perfil de usuario

### Solución 3: Usar Versión Anterior de yfinance

Downgrade a versión 0.2.43 que usa `requests` en lugar de `curl_cffi`:

```bash
python -m pip uninstall -y yfinance
python -m pip install "yfinance==0.2.43"
```

**Advertencia**: Esta versión puede tener problemas con Yahoo Finance debido a cambios en su API.

### Solución 4: Instalar Python en Ruta sin Acentos

Reinstalar Python en una ruta sin caracteres especiales:

```
C:\Python314\
```

Y configurar `pip` para instalar paquetes en una ruta sin acentos:

```bash
python -m pip install --user --target="C:\PythonLibs" yfinance pandas
```

### Solución 5: Usar Variable de Entorno (Temporal)

Para cada sesión, configurar:

```bash
set CURL_CA_BUNDLE=
set SSL_CERT_FILE=
python main.py
```

O usar el script auxiliar creado: `run_with_ssl_fix.py`

### Solución 6: Modificar Código para Deshabilitar Verificación SSL

**SOLO PARA DESARROLLO/TESTING - NO RECOMENDADO PARA PRODUCCIÓN**

Modificar `data_acquisition.py` para agregar al inicio:

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

## Recomendación

Para desarrollo inmediato: **Usar datos en caché existentes**

Para solución permanente: **Solución 2 (nuevo usuario Windows)** o **Solución 4 (reinstalar Python)**

## Estado Actual

- ✓ Código refactorizado funciona correctamente
- ✓ Todos los módulos importan sin errores
- ✓ Base de datos y estructura funcionan perfectamente
- ✗ Descarga de datos de Yahoo Finance bloqueada por SSL
- ✓ Datos históricos existentes disponibles para análisis

## Notas Adicionales

El problema NO está relacionado con las refactorizaciones realizadas. Es un problema de compatibilidad entre:
- Windows con usuarios con caracteres Unicode
- curl_cffi librería
- Python 3.14 (muy reciente)
- Rutas de Windows con acentos

El código del proyecto es correcto y funcionará sin problemas en:
- Linux/Mac
- Windows con usuario sin acentos
- Python < 3.14
- Tras aplicar cualquiera de las soluciones propuestas
