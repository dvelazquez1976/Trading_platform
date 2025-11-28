"""
Script auxiliar para ejecutar main.py con configuración SSL corregida.
Este script soluciona el problema de caracteres especiales en la ruta de certificados.

SOLO PARA DESARROLLO/TESTING - NO USAR EN PRODUCCIÓN

Para producción, use certificados SSL válidos y verifique las conexiones.
Consulte SSL_PROBLEMA_Y_SOLUCIONES.md para más detalles.
"""

import os
import sys
import ssl
import warnings

# Verificar si estamos en modo desarrollo
DEV_MODE = os.environ.get('TRADING_PLATFORM_DEV', '1') == '1'

if not DEV_MODE:
    print("ERROR: Este script solo debe usarse en modo desarrollo.")
    print("Para modo producción, configure certificados SSL válidos.")
    sys.exit(1)

# Advertencia de seguridad
warnings.warn(
    "ADVERTENCIA DE SEGURIDAD: Verificación SSL deshabilitada. "
    "Solo usar en entorno de desarrollo/testing. "
    "NO USAR EN PRODUCCIÓN.",
    UserWarning,
    stacklevel=2
)

# Solución 1: Deshabilitar verificación SSL (solo para desarrollo/testing)
# ADVERTENCIA: Esto hace la conexión vulnerable a ataques MITM
ssl._create_default_https_context = ssl._create_unverified_context

# Solución 2: Configurar variables de entorno para curl
# Limpiar variables de certificados para evitar conflictos
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['SSL_CERT_FILE'] = ''

# Solución 3: Forzar uso de requests en lugar de curl_cffi
# requests maneja mejor los certificados en Windows
os.environ['YF_USE_REQUESTS'] = '1'

print("=" * 70)
print("MODO DESARROLLO - Configuración SSL ajustada")
print("ADVERTENCIA: Verificación SSL deshabilitada")
print("Vulnerable a ataques MITM - Solo usar en entorno controlado")
print("=" * 70)
print()
print("Para deshabilitar este modo, establezca: TRADING_PLATFORM_DEV=0")
print()

# Importar y ejecutar main
if __name__ == "__main__":
    # Importar el módulo main
    import main

    # Ejecutar la función main
    main.main()
