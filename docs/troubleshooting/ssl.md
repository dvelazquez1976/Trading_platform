# Problema SSL en Windows — Solución

## Síntoma

```
SSLError: Failed to perform, curl: (77) error setting certificate verify locations:
CAfile: C:\Users\DavidVelázquezGómez\AppData\...
```

## Causa raíz

`curl_cffi` (usado por yfinance) no maneja rutas Windows con caracteres Unicode (acentos en el nombre de usuario).

## Solución definitiva (v2.0)

La plataforma usa **Stooq** como proveedor primario. Stooq descarga CSVs vía HTTP puro sin `curl_cffi`, eliminando el problema completamente. yfinance queda como fallback y sólo se activa si Stooq falla.

## Solución alternativa para yfinance

Si necesitas forzar yfinance, establece la variable de entorno antes de lanzar:

```bash
# En PowerShell
$env:CURL_CA_BUNDLE = "C:\ruta\sin\acentos\cacert.pem"
python -m streamlit run app/main.py

# O usa el script legado
python run_with_ssl_fix.py
```

## Ruta del certificado en el repositorio

El archivo `certs/cacert.pem` está en `.gitignore` por seguridad. Si lo necesitas, descárgalo de:
`https://curl.se/ca/cacert.pem`
