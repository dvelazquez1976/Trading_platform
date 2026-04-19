# Trading Platform — Documentación Técnica v2.0

> Plataforma personal de análisis técnico de acciones. Arquitectura modular, UI Streamlit, múltiples mercados, sin costes de API.

---

## Índice

1. [Estructura del proyecto](#1-estructura-del-proyecto)
2. [Arquitectura](#2-arquitectura)
3. [Flujo de uso](#3-flujo-de-uso)
4. [Módulos del paquete](#4-módulos-del-paquete)
5. [Proveedores de datos](#5-proveedores-de-datos)
6. [Indicadores técnicos](#6-indicadores-técnicos)
7. [Señales y recomendaciones](#7-señales-y-recomendaciones)
8. [Backtesting](#8-backtesting)
9. [Visualización](#9-visualización)
10. [Configuración](#10-configuración)
11. [Instalación y arranque](#11-instalación-y-arranque)
12. [Bugs corregidos en v2.0](#12-bugs-corregidos-en-v20)
13. [Hoja de ruta](#13-hoja-de-ruta)

---

## 1. Estructura del proyecto

```
Trading_platform/
├── app/                        # Interfaz Streamlit
│   ├── main.py                 # Página de bienvenida
│   └── pages/
│       ├── 1_📋_Watchlist.py   # Selección de mercado + acciones
│       ├── 2_📈_Análisis.py    # Pipeline de análisis + botón RUN
│       ├── 3_🔬_Backtesting.py # Evaluación histórica de estrategias
│       └── 4_⚙️_Configuración.py
│
├── config/
│   └── config.json             # Configuración centralizada
│
├── data/
│   ├── markets/                # Índices bursátiles (CSV, versionados)
│   │   ├── ibex35.csv
│   │   ├── sp500_sample.csv
│   │   ├── nasdaq100.csv
│   │   ├── dax40.csv
│   │   ├── cac40.csv
│   │   ├── eurostoxx50.csv
│   │   ├── ftse100.csv
│   │   └── nikkei225_sample.csv
│   ├── watchlists/
│   │   └── default.csv         # Watchlist activa del usuario
│   ├── cache/                  # Caché JSON de datos descargados (gitignored)
│   ├── db/                     # Base de datos SQLite (gitignored)
│   └── outputs/                # Informes, CSV, logs (gitignored)
│       ├── reports/
│       ├── csv/
│       └── logs/
│
├── docs/
│   └── troubleshooting/
│       └── ssl.md              # Solución al problema SSL en Windows
│
├── src/
│   └── trading_platform/       # Paquete Python instalable
│       ├── core/               # Constantes, config, logging, utils
│       ├── providers/          # Stooq, yfinance, orquestador con fallback
│       ├── storage/            # SQLite + caché JSON
│       ├── indicators/         # Indicadores básicos y avanzados
│       ├── signals/            # Generador de señales de trading
│       ├── backtesting/        # Motor de backtesting + métricas
│       ├── visualization/      # Gráficos Plotly + dashboard HTML
│       ├── pipeline/           # Orquestador + procesamiento paralelo
│       └── cli.py              # Punto de entrada de línea de comandos
│
├── tests/                      # Tests (pytest)
├── .streamlit/config.toml      # Tema Streamlit
├── pyproject.toml              # Metadatos del proyecto y dependencias
├── .gitignore
└── .env.example                # Plantilla de variables de entorno
```

---

## 2. Arquitectura

```
Usuario
  │
  ▼
┌─────────────────────────────────────────────────────┐
│  Streamlit UI  (app/)                                │
│  Watchlist → [RUN] → resultados en pantalla          │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Pipeline (pipeline/runner.py)                       │
│  TradingPlatform.run_tickers()                       │
└──┬──────────┬───────────┬──────────────┬────────────┘
   │          │           │              │
   ▼          ▼           ▼              ▼
providers  indicators  signals    visualization
(datos)    (técnicos)  (señales)  (HTML + dashboard)
   │
   ├── Stooq (primario, gratis, sin API key)
   └── yfinance (fallback)
```

### Principio de extensibilidad de proveedores

Añadir un proveedor de pago (Alpha Vantage, Polygon…) requiere:
1. Crear `src/trading_platform/providers/nuevo_proveedor.py` implementando `DataProvider`.
2. Añadirlo a la lista en `orchestrator.py`.
3. Poner la API key en `.env`.

Sin tocar el resto del código.

---

## 3. Flujo de uso

### Interfaz Streamlit (recomendado)

```bash
cd Trading_platform
python -m streamlit run app/main.py
```

1. **📋 Watchlist**: Elige un mercado (IBEX 35, S&P 500, DAX 40…) → filtra por sector → marca acciones → "Añadir a Watchlist".
2. **📈 Análisis**: Ajusta parámetros (días de histórico) → pulsa **[RUN]** → ve resultados por tabs (Compra / Venta / Neutral) → descarga informes HTML.
3. **🔬 Backtesting**: Selecciona un ticker y estrategia → ajusta costes de transacción → pulsa "Ejecutar Backtest" → ve métricas y curva de capital.
4. **⚙️ Configuración**: Ajusta parámetros globales → "Guardar configuración".

### Línea de comandos

```bash
# Instalar en modo editable
pip install -e .

# Ejecutar análisis de tickers específicos
trading-platform --tickers SAN.MC BBVA.MC AAPL --days 365

# Ejecutar con la watchlist por defecto (data/watchlists/default.csv)
trading-platform
```

---

## 4. Módulos del paquete

### `core/`

| Archivo | Responsabilidad |
|---------|----------------|
| `constants.py` | `ROOT_DIR`, rutas de todos los directorios; mapas de columnas |
| `config.py` | `ConfigManager` — lee `config/config.json`, con valores por defecto |
| `logging.py` | `TradingLogger` singleton; escribe en `data/outputs/logs/control.txt` |
| `utils.py` | Renombrado de columnas, formateo CSV Excel, builders de filas de tabla |

### `providers/`

| Archivo | Responsabilidad |
|---------|----------------|
| `base.py` | Clase base `DataProvider` (Protocol) + excepciones |
| `stooq.py` | Descarga CSV de Stooq; mapea sufijos Yahoo→Stooq (`.MC`→`.es`) |
| `yfinance_provider.py` | `auto_adjust=True`; normaliza MultiIndex yfinance |
| `orchestrator.py` | Prueba proveedores en orden; alias `descargar_datos()` para retrocompatibilidad |

### `storage/`

| Archivo | Responsabilidad |
|---------|----------------|
| `database.py` | SQLite con `executemany()` — 10–50× más rápido que inserción fila a fila |
| `cache.py` | Caché JSON con TTL configurable; evita descargas repetidas |

### `indicators/`

| Archivo | Responsabilidad |
|---------|----------------|
| `basic.py` | RSI, MACD, Bollinger, SMA 30/60/90, Williams %R (columnas estandarizadas) |
| `advanced.py` | StochRSI, TSI, UO, Chaikin, Aroon, TRIX, VolumeRSI, DPO |

### `signals/`

| Archivo | Responsabilidad |
|---------|----------------|
| `generator.py` | Sistema de votación; devuelve `COMPRA / VENTA / KEEP/NO SIGNAL` por indicador + resumen |
| `advanced.py` | Señales para los indicadores avanzados |

### `backtesting/`

| Archivo | Responsabilidad |
|---------|----------------|
| `costs.py` | `TransactionCosts` — comisión porcentual + mínimo + slippage en bps |
| `metrics.py` | CAGR, Sharpe, Sortino, Max Drawdown, Profit Factor, Win Rate |
| `engine.py` | `BacktestingEngine.run()` — 4 estrategias: `sma_crossover`, `rsi_oversold`, `macd_signal`, `bollinger_reversion` |

### `visualization/`

| Archivo | Responsabilidad |
|---------|----------------|
| `theme.py` | Diccionarios de colores `light` / `dark` |
| `charts.py` | Gráfico Plotly de 5 paneles (velas, volumen, MACD, RSI, Williams) + tabla |
| `dashboard.py` | Dashboard HTML consolidado con gauge, heatmap, scatter y tabla filtrable |

### `pipeline/`

| Archivo | Responsabilidad |
|---------|----------------|
| `runner.py` | `TradingPlatform` — orquesta descarga→indicadores→señales→gráficos |
| `parallel.py` | `ParallelProcessor` con `ThreadPoolExecutor` + `process_single_ticker()` |

---

## 5. Proveedores de datos

### Stooq (primario)

- **Gratis**, sin registro, sin API key.
- Descarga CSVs directamente: `https://stooq.com/q/d/l/?s={ticker}&d1=YYYYMMDD&d2=YYYYMMDD&i=d`
- Buena cobertura para Europa (IBEX 35, DAX, CAC 40, FTSE 100) y mercados globales.
- **Mapeo de sufijos** Yahoo Finance → Stooq:

| Yahoo | Stooq | Mercado |
|-------|-------|---------|
| `.MC` | `.es` | España (BME) |
| `.DE` | `.de` | Alemania (XETRA) |
| `.PA` | `.fr` | Francia |
| `.L`  | `.uk` | Reino Unido |
| `.T`  | `.jp` | Japón |
| _(sin sufijo)_ | `.us` | EE.UU. |

### yfinance (fallback)

- Activado automáticamente si Stooq no devuelve datos.
- `auto_adjust=True` corrige precios históricos por dividendos y splits.
- **Problema SSL en Windows** con usuarios con acentos: resuelto usando Stooq como primario. Ver `docs/troubleshooting/ssl.md`.

---

## 6. Indicadores técnicos

### Básicos (siempre activos)

| Indicador | Columna(s) | Descripción |
|-----------|-----------|-------------|
| SMA 30 | `SMA_30` | Media móvil simple 30 días |
| SMA 60 | `SMA_60` | Media móvil simple 60 días |
| SMA 90 | `SMA_90` | Media móvil simple 90 días |
| RSI | `RSI` | Relative Strength Index (14 períodos) |
| MACD | `MACD`, `MACDs`, `MACDh` | MACD(12,26,9) — línea, señal, histograma |
| Bollinger | `BBU_BB`, `BBL_BB`, `BBM_BB` | Bandas de Bollinger (20, 2σ) |
| Williams %R | `WILLR` | Williams Percent Range (14 períodos) |

### Avanzados (opcionales, actívense en config)

StochRSI, TSI, Ultimate Oscillator, Chaikin Money Flow, Aroon, TRIX, Volume RSI, DPO.

---

## 7. Señales y recomendaciones

El sistema de votación en `signals/generator.py` evalúa cada indicador y produce:

| Señal | Descripción |
|-------|-------------|
| `COMPRA` | El indicador está en zona alcista |
| `VENTA` | El indicador está en zona bajista |
| `KEEP/NO SIGNAL` | Zona neutral |

**Resumen final**: mayoría de votos entre COMPRA y VENTA. Si hay empate → KEEP.

> **Aviso**: Las señales son indicativas. No constituyen asesoramiento financiero.

---

## 8. Backtesting

### Estrategias disponibles

| ID | Nombre | Lógica |
|----|--------|--------|
| `sma_crossover` | Cruce de medias | Compra cuando SMA30 > SMA90; vende cuando SMA30 < SMA90 |
| `rsi_oversold` | RSI sobrevendido | Compra cuando RSI < 30; vende cuando RSI > 70 |
| `macd_signal` | Cruce MACD | Compra cuando MACD cruza al alza la línea de señal |
| `bollinger_reversion` | Reversión Bollinger | Compra en banda inferior; vende en banda superior |

### Costes de transacción

```python
TransactionCosts(
    commission_pct = 0.002,   # 0.2% por operación
    min_commission = 1.0,     # mínimo 1€
    slippage_bps   = 5.0,     # 5 puntos básicos de slippage
)
```

### Métricas de salida

- **Total Return** — rentabilidad total del período
- **CAGR** — tasa de crecimiento anual compuesta
- **Sharpe Ratio** — rentabilidad ajustada al riesgo (rf=0)
- **Sortino Ratio** — como Sharpe pero sólo penaliza la volatilidad bajista
- **Max Drawdown** — caída máxima desde máximo histórico
- **Win Rate** — porcentaje de operaciones ganadoras
- **Profit Factor** — suma de ganancias / suma de pérdidas

---

## 9. Visualización

### Informe individual por ticker (`{ticker}_analisis.html`)

- **Panel 1**: Velas japonesas + SMA 30/60/90 + Bandas de Bollinger
- **Panel 2**: Volumen (coloreado: verde=subida, rojo=bajada)
- **Panel 3**: MACD + histograma + línea de señal
- **Panel 4**: RSI con zonas de sobrecompra/sobreventa
- **Panel 5**: Williams %R con zonas extremas
- Tabla con 10 sesiones recientes + tabla de señales por indicador

### Dashboard consolidado (`dashboard_consolidado.html`)

- KPIs: total tickers, señales compra/venta, sentimiento alcista
- Gauge de sentimiento de mercado (Plotly)
- Heatmap de volatilidad por ticker
- Tabla interactiva filtrable (buscar, filtrar por señal)
- Scatter RSI vs Williams %R (coloreado por señal)
- Clic en cualquier fila abre el informe individual del ticker

---

## 10. Configuración

`config/config.json` controla todos los parámetros:

```json
{
  "data": {
    "tickers_file": "data/watchlists/default.csv",
    "analysis_period_days": 730,
    "cache_enabled": true,
    "cache_ttl_hours": 4
  },
  "processing": {
    "parallel_processing": false,
    "max_workers": 4
  },
  "providers": {
    "primary": "stooq",
    "fallback": ["yfinance"]
  },
  "indicators": {
    "advanced_enabled": false
  },
  "backtesting": {
    "commission_pct": 0.002,
    "min_commission": 1.0,
    "slippage_bps": 5.0
  },
  "ui": {
    "theme": "light",
    "default_market": "ibex35",
    "chart_months": 24
  }
}
```

---

## 11. Instalación y arranque

### Prerrequisitos

- Python 3.10+
- pip

### Instalación

```bash
# Clonar repositorio
git clone <repo> && cd Trading_platform

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Instalar en modo editable (incluye dependencias)
pip install -e .

# (Opcional) crear variables de entorno
cp .env.example .env
```

### Arrancar la interfaz

```bash
python -m streamlit run app/main.py
# → http://localhost:8501
```

### Arrancar en modo CLI

```bash
trading-platform --tickers SAN.MC BBVA.MC AAPL
trading-platform --days 365 --output /ruta/salida
```

---

## 12. Bugs corregidos en v2.0

| ID | Descripción | Solución |
|----|-------------|---------|
| **B1** | MACD bug: `backtesting_engine.py` usaba `MACD_12_26_9` pero los indicadores generaban `MACD`/`MACDs` | Estandarizado a `MACD`/`MACDs`/`MACDh` en todo el código |
| **B2** | SQLite: inserción fila a fila (lento con 20 000+ registros) | `executemany()` con inserción en bloque |
| **B3** | Rutas hardcodeadas al directorio de trabajo (`CWD`) | `ROOT_DIR` via `pathlib.Path(__file__).parent` en `constants.py` |
| **B4** | API key de Alpha Vantage en texto plano versionado en git | Movida a `.env` (en `.gitignore`); plantilla en `.env.example` |
| **B5** | `auto_adjust=False` en yfinance distorsionaba históricos pre-split | Cambiado a `auto_adjust=True` |
| **B6** | SSL error con acentos en ruta de usuario Windows | Stooq como proveedor primario (no usa `curl_cffi`) |

---

## 13. Hoja de ruta

### Fase 1 — Completada (v2.0)
- [x] Estructura de directorios limpia
- [x] Arquitectura de proveedores extensible (Stooq + yfinance)
- [x] Corrección de todos los bugs conocidos
- [x] Interfaz Streamlit con flujo Watchlist → RUN
- [x] Backtesting con costes de transacción reales
- [x] 8 índices bursátiles en archivos CSV

### Fase 2 — Próximos pasos
- [ ] Tests unitarios para indicadores, señales y proveedores
- [ ] Proveedor FRED para datos macroeconómicos (gratis)
- [ ] Alertas por email cuando una señal cambia de estado
- [ ] Exportación a Excel con formato ES (separador `;`, decimal `,`)
- [ ] Comparación multi-ticker en el mismo gráfico

### Fase 3 — Futuro
- [ ] Soporte para Alpha Vantage / Polygon (con API key)
- [ ] Análisis de correlación entre activos
- [ ] Optimización automática de parámetros de estrategia
- [ ] Modo Docker para despliegue en servidor propio

---

*Documentación generada el 2026-04-19 · Trading Platform v2.0.0*
