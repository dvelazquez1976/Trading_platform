# 📈 Plataforma de Trading - Análisis Técnico Automatizado

**Versión 2.0.0** - Sistema profesional de análisis técnico para mercados financieros

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Características Principales

✅ **Análisis Multi-Ticker**: Procesa múltiples activos simultáneamente
✅ **20+ Indicadores Técnicos**: Básicos y avanzados
✅ **Procesamiento Paralelo**: Análisis rápido con multi-threading
✅ **Backtesting Integrado**: Prueba estrategias con datos históricos
✅ **Sistema de Caché**: Reduce tiempos de ejecución
✅ **Visualización Interactiva**: Gráficos HTML con Plotly
✅ **Exportación Flexible**: CSV, tablas, y gráficos
✅ **CLI Completa**: Interfaz de línea de comandos poderosa
✅ **Logging Detallado**: Seguimiento completo de ejecución

---

## 📋 Tabla de Contenidos

- [Instalación](#instalación)
- [Inicio Rápido](#inicio-rápido)
- [Uso de la CLI](#uso-de-la-cli)
- [Configuración](#configuración)
- [Indicadores Técnicos](#indicadores-técnicos)
- [Backtesting](#backtesting)
- [Archivos de Salida](#archivos-de-salida)
- [Documentación Técnica](#documentación-técnica)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Conexión a Internet (para descargar datos de Yahoo Finance)

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/Trading_platform.git
cd Trading_platform

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## ⚡ Inicio Rápido

### Ejecución Básica

1. **Configurar tickers** (archivo `tickers.txt`):
```
AAPL
GOOGL
MSFT
TSLA
```

2. **Ejecutar análisis**:
```bash
python main.py
```

3. **Ver resultados**:
- `control.txt` - Logs de ejecución
- `salida.txt` - Tablas de resultados
- `salidas/` - Gráficos HTML y CSVs

---

## 💻 Uso de la CLI

La plataforma incluye una interfaz de línea de comandos completa:

### Ejemplos de Uso

```bash
# Análisis básico
python cli.py

# Con archivo de tickers personalizado
python cli.py --tickers mis_tickers.txt

# Análisis de 1 año (365 días)
python cli.py --days 365

# Modo paralelo con 8 workers
python cli.py --parallel --workers 8

# Habilitar indicadores avanzados
python cli.py --advanced

# Limpiar caché antes de ejecutar
python cli.py --clear-cache

# Ver estadísticas de caché
python cli.py --cache-stats

# Modo backtesting
python cli.py --backtest --strategy ma_crossover --capital 10000

# Combinación de opciones
python cli.py --parallel --workers 6 --advanced --days 500
```

### Opciones Disponibles

#### Configuración de Datos
- `--tickers, -t` - Archivo con lista de tickers (default: tickers.txt)
- `--days, -d` - Número de días de histórico a analizar

#### Procesamiento
- `--parallel, -p` - Activar procesamiento paralelo
- `--workers, -w` - Número de workers (default: 4)

#### Indicadores
- `--advanced, -a` - Habilitar indicadores técnicos avanzados

#### Gestión de Caché
- `--clear-cache` - Limpiar todo el caché
- `--clear-cache-ticker TICKER` - Limpiar caché de un ticker específico
- `--cache-stats` - Mostrar estadísticas del caché
- `--no-cache` - Desactivar uso de caché

#### Backtesting
- `--backtest, -b` - Ejecutar modo backtesting
- `--strategy` - Estrategia: `ma_crossover`, `rsi_threshold`, `macd_signal`, `multi_indicator`
- `--capital` - Capital inicial (default: 10000)

#### Salida
- `--output-dir, -o` - Directorio de salida (default: salidas)
- `--no-html` - No generar gráficos HTML
- `--no-csv` - No generar archivos CSV

#### Otras
- `--verbose, -v` - Modo verbose (más detalles)
- `--version` - Mostrar versión

---

## ⚙️ Configuración

### Archivo `config.json`

El archivo de configuración permite personalizar todos los parámetros:

```json
{
  "data": {
    "analysis_period_days": 730
  },
  "processing": {
    "parallel_processing": false,
    "max_workers": 4
  },
  "indicators": {
    "sma_periods": [30, 60, 90],
    "rsi_period": 14,
    "macd_params": {"fast": 12, "slow": 26, "signal": 9}
  },
  "signals": {
    "rsi_oversold": 30,
    "rsi_overbought": 70
  },
  "advanced_indicators": {
    "enabled": false
  }
}
```

### Parámetros Importantes

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `analysis_period_days` | Días de histórico a analizar | 730 (2 años) |
| `parallel_processing` | Activar procesamiento paralelo | false |
| `max_workers` | Workers para procesamiento paralelo | 4 |
| `rsi_oversold` | Umbral RSI sobreventa | 30 |
| `rsi_overbought` | Umbral RSI sobrecompra | 70 |
| `advanced_indicators.enabled` | Habilitar indicadores avanzados | false |

---

## 📊 Indicadores Técnicos

### Indicadores Básicos (siempre incluidos)

| Indicador | Descripción | Parámetros |
|-----------|-------------|------------|
| **SMA** | Medias Móviles Simples | 30, 60, 90 días |
| **RSI** | Relative Strength Index | 14 períodos |
| **Estocástico** | Oscilador de momentum | K=14, D=3 |
| **MACD** | Moving Average Convergence Divergence | 12, 26, 9 |
| **Bandas Bollinger** | Bandas de volatilidad | 20, 2σ |
| **CCI** | Commodity Channel Index | 20 períodos |
| **ADX** | Average Directional Index | 14 períodos |
| **MFI** | Money Flow Index | 14 períodos |
| **Williams %R** | Oscilador de momentum | 14 períodos |
| **AO** | Awesome Oscillator | 5, 34 |
| **ROC** | Rate of Change | 12 períodos |

### Indicadores Avanzados (opcionales)

Activar con `--advanced` o `config.json`:

| Indicador | Descripción |
|-----------|-------------|
| **Stochastic RSI** | RSI con estocástico para mejor timing |
| **TSI** | True Strength Index - oscilador suavizado |
| **Ultimate Oscillator** | Combina múltiples timeframes |
| **Chaikin Oscillator** | Divergencias precio-volumen |
| **Aroon Oscillator** | Identifica tendencias emergentes |
| **TRIX** | Triple EMA suavizada |
| **Volume RSI** | RSI aplicado al volumen |
| **DPO** | Detrended Price Oscillator |

---

## 🔬 Backtesting

### Estrategias Disponibles

#### 1. MA Crossover (Cruce de Medias Móviles)
```bash
python cli.py --backtest --strategy ma_crossover --capital 10000
```
- **Señal COMPRA**: SMA_30 cruza sobre SMA_60
- **Señal VENTA**: SMA_30 cruza bajo SMA_60

#### 2. RSI Threshold (Umbrales RSI)
```bash
python cli.py --backtest --strategy rsi_threshold --capital 10000
```
- **Señal COMPRA**: RSI < 30 (sobreventa)
- **Señal VENTA**: RSI > 70 (sobrecompra)

#### 3. MACD Signal
```bash
python cli.py --backtest --strategy macd_signal --capital 10000
```
- **Señal COMPRA**: MACD cruza sobre línea de señal
- **Señal VENTA**: MACD cruza bajo línea de señal

#### 4. Multi Indicator (Votación de Indicadores)
```bash
python cli.py --backtest --strategy multi_indicator --capital 10000
```
- Combina RSI, MACD y SMAs
- Decisión por mayoría de votos

### Métricas de Backtesting

El sistema calcula automáticamente:
- Capital final
- Retorno total (%)
- Número de operaciones
- Operaciones ganadoras/perdedoras
- Win rate (%)
- Ganancia/pérdida promedio
- Mayor ganancia/pérdida

---

## 📁 Archivos de Salida

### `control.txt` - Log de Ejecución
```
2025-01-15 10:30:15 | INFO | main | load_tickers:82 | Cargados 5 tickers
2025-01-15 10:30:16 | INFO | data_acquisition | descargar_datos:85 | Descargando AAPL
2025-01-15 10:30:17 | INFO | indicator_calculator | calcular_indicadores:78 | Calculando indicadores
...
```

### `salida.txt` - Tablas de Resultados

Contiene 3-5 tablas según configuración:
1. **Resumen General**: Ticker, Empresa, Fecha, Precio, Recomendación
2. **Señales Básicas**: Señal de cada indicador básico
3. **Valores Básicos**: Valores numéricos de indicadores
4. **Señales Avanzadas** (si habilitado)
5. **Valores Avanzados** (si habilitado)

### Carpeta `salidas/`

#### Gráficos HTML Interactivos
- `{TICKER}_analisis.html` - Gráfico Plotly interactivo con:
  - Candlestick + SMAs
  - Volumen
  - RSI
  - Williams %R

#### Archivos CSV
- `open_data.csv` - Precios de apertura
- `high_data.csv` - Precios máximos
- `low_data.csv` - Precios mínimos
- `close_data.csv` - Precios de cierre
- `volume_data.csv` - Volúmenes

**Formato**: Delimitador `;`, decimal `,` (compatible con Excel español)

---

## 📚 Documentación Técnica

Para documentación técnica completa, ver:
- **`DOCUMENTACION_TECNICA.md`** - Guía técnica detallada (1,200+ líneas)

Incluye:
- Arquitectura del sistema
- Flujo de ejecución paso a paso
- Explicación de cada módulo
- Estructuras de datos
- Diagramas de flujo
- Guía de mantenimiento
- Cómo añadir indicadores
- Glosario de términos

---

## 🐛 Troubleshooting

### Error: "No se encontró el archivo de tickers"
**Solución**: Crear archivo `tickers.txt` en la raíz del proyecto con un ticker por línea

### Error: "All values are NaN"
**Solución**:
- Verificar que el ticker es válido (ej: AAPL, no Apple)
- Verificar rango de fechas (no puede ser futuro)
- Probar con otro ticker conocido

### Tablas vacías en salida.txt
**Solución**:
- Revisar `control.txt` para ver errores específicos
- Verificar conexión a Internet
- Verificar que tickers.txt tiene símbolos válidos

### Gráficos HTML no se generan
**Solución**:
- Verificar permisos de escritura en carpeta `salidas/`
- Reinstalar plotly: `pip install --upgrade plotly`

### Procesamiento muy lento
**Solución**:
- Activar procesamiento paralelo: `--parallel --workers 6`
- Reducir días de análisis: `--days 365`
- Usar caché (activado por defecto)

---

## 🔧 Desarrollo

### Ejecutar Tests
```bash
# Instalar pytest si no está instalado
pip install pytest pytest-cov

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_data_acquisition.py
```

### Estructura del Proyecto

```
Trading_platform/
├── main.py                    # Orquestador principal
├── cli.py                     # Interfaz CLI
├── data_acquisition.py        # Descarga de datos
├── data_storage.py            # Base de datos
├── indicator_calculator.py    # Indicadores básicos
├── advanced_indicators.py     # Indicadores avanzados
├── signal_generator.py        # Generación de señales
├── visualizer.py              # Gráficos HTML
├── parallel_processor.py      # Procesamiento paralelo
├── cache_manager.py           # Sistema de caché
├── backtesting_engine.py      # Motor de backtesting
├── logger_config.py           # Sistema de logging
├── config_manager.py          # Gestor de configuración
├── constants.py               # Constantes
├── utils.py                   # Utilidades
├── config.json                # Configuración
├── tickers.txt                # Lista de tickers
├── requirements.txt           # Dependencias
├── README.md                  # Este archivo
├── DOCUMENTACION_TECNICA.md   # Documentación técnica
└── tests/                     # Pruebas unitarias
    ├── test_data_acquisition.py
    ├── test_indicators.py
    └── test_signals.py
```

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📧 Contacto

- **Repositorio**: [https://github.com/tu-usuario/Trading_platform](https://github.com/tu-usuario/Trading_platform)
- **Issues**: [https://github.com/tu-usuario/Trading_platform/issues](https://github.com/tu-usuario/Trading_platform/issues)

---

## 🌟 Agradecimientos

- [yfinance](https://github.com/ranaroussi/yfinance) - Datos de Yahoo Finance
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Indicadores técnicos
- [Plotly](https://plotly.com/python/) - Visualizaciones interactivas

---

**¿Te gusta este proyecto? Dale una ⭐ en GitHub!**
