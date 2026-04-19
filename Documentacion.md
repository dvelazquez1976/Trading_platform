# Trading Platform — Documentación Técnica v2.2

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
10. [Alertas Telegram](#10-alertas-telegram)
11. [Watchlists persistentes](#11-watchlists-persistentes)
12. [Configuración](#12-configuración)
13. [Instalación y arranque](#13-instalación-y-arranque)
14. [Bugs corregidos](#14-bugs-corregidos)
15. [Hoja de ruta](#15-hoja-de-ruta)

---

## 1. Estructura del proyecto

```
Trading_platform/
├── app/                        # Interfaz Streamlit
│   ├── main.py                 # Página de bienvenida
│   ├── components/             # Componentes reutilizables de la UI
│   │   └── theme.py            # CSS dark mode, sparkline helper, export CSV ES
│   └── pages/
│       ├── 1_📋_Watchlist.py   # Selección de mercado + gestión de watchlists
│       ├── 2_📈_Análisis.py    # Pipeline de análisis + RUN + alertas
│       ├── 3_🔬_Backtesting.py # Evaluación histórica de estrategias
│       └── 4_⚙️_Configuración.py # Config, API keys, alertas Telegram
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
│   ├── watchlists/             # Watchlists del usuario (versionadas)
│   │   ├── default.csv         # Watchlist que carga al inicio
│   │   └── *.csv               # Watchlists nombradas guardadas desde la UI
│   ├── cache/                  # Caché JSON de datos descargados (gitignored)
│   ├── db/                     # Base de datos SQLite (gitignored)
│   └── outputs/                # Informes, CSV, logs (gitignored)
│       ├── reports/
│       ├── csv/
│       └── logs/
│
├── docs/
│   └── troubleshooting/
│       └── ssl.md
│
├── src/
│   └── trading_platform/       # Paquete Python instalable
│       ├── core/               # Constantes, config, logging, utils
│       ├── providers/          # yfinance, Stooq, orquestador, stubs de pago
│       ├── storage/            # SQLite + caché JSON + watchlist manager
│       ├── indicators/         # Indicadores básicos y avanzados
│       ├── signals/            # Generador de señales de trading
│       ├── backtesting/        # Motor de backtesting + métricas
│       ├── alerts/             # Alertas Telegram
│       ├── visualization/      # Gráficos Plotly + dashboard HTML
│       └── pipeline/           # Orquestador + procesamiento paralelo
│
├── tests/                      # Tests (pytest)
├── .streamlit/config.toml      # Tema Streamlit (light por defecto)
├── pyproject.toml
├── .gitignore
└── .env.example
```

---

## 2. Arquitectura

```
Usuario
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  Streamlit UI  (app/)                                    │
│  Watchlist → [RUN] → resultados → alertas Telegram       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Pipeline (pipeline/runner.py)                           │
│  TradingPlatform.run_tickers()                           │
└──┬────────┬──────────┬──────────┬────────────┬──────────┘
   │        │          │          │            │
   ▼        ▼          ▼          ▼            ▼
providers indicators signals visualization  alerts
(datos)   (técnicos) (señales) (HTML)      (Telegram)
   │
   ├── yfinance (primario — gratuito, cobertura global)
   ├── Stooq (fallback — gratuito con API key)
   └── FMP / EODHD / Polygon / Finnhub (stubs — activar al contratar)
```

### Principio de extensibilidad de proveedores

Añadir un proveedor de pago requiere:
1. Implementar `fetch_ohlcv()` en la clase correspondiente de `providers/_stubs.py`.
2. Añadir su instancia al inicio de la lista en `orchestrator.py`.
3. Pegar la API key en ⚙️ Configuración → Proveedores.

Sin tocar el resto del código.

---

## 3. Flujo de uso

### Interfaz Streamlit (recomendado)

```bash
cd Trading_platform
python -m streamlit run app/main.py
# → http://localhost:8501
```

1. **📋 Watchlist** — Elige mercado → filtra sector → marca acciones → "Añadir a Watchlist". Guarda con nombre para reutilizar. Exporta a CSV formato europeo.
2. **📈 Análisis** — Ajusta parámetros → **[RUN]** → ve resultados por tabs (Compra/Venta/Neutral). Filtra por señal, busca ticker, ordena. Si las alertas Telegram están configuradas, recibe el resumen en Telegram automáticamente.
3. **🔬 Backtesting** — Selecciona ticker y estrategia → ajusta costes → "Ejecutar Backtest" → ve métricas, curva de capital y tabla de operaciones. Exporta a CSV.
4. **⚙️ Configuración** — Ajusta todos los parámetros globales, API keys, alertas Telegram.

### Línea de comandos

```bash
pip install -e .
trading-platform --tickers SAN.MC BBVA.MC AAPL --days 365
trading-platform   # usa la watchlist default
```

---

## 4. Módulos del paquete

### `core/`

| Archivo | Responsabilidad |
|---------|----------------|
| `constants.py` | `ROOT_DIR`, rutas de directorios; mapas de columnas OHLCV |
| `config.py` | `ConfigManager` — lee `config/config.json` |
| `logging.py` | Logger singleton; escribe en `data/outputs/logs/` |
| `utils.py` | Renombrado de columnas, formateo CSV, builders de tabla |

### `providers/`

| Archivo | Responsabilidad |
|---------|----------------|
| `base.py` | Clase base `DataProvider` + excepciones `ProviderError`, `AllProvidersFailed` |
| `yfinance_provider.py` | Proveedor primario; `auto_adjust=True`; normaliza MultiIndex |
| `stooq.py` | Fallback; mapeo de sufijos Yahoo→Stooq; detecta ausencia de API key |
| `orchestrator.py` | Prueba proveedores en orden; alias `descargar_datos()` |
| `_stubs.py` | Esqueletos listos para activar: `FMPProvider`, `EODHDProvider`, `PolygonProvider`, `FinnhubProvider` |

### `storage/`

| Archivo | Responsabilidad |
|---------|----------------|
| `database.py` | SQLite con `executemany()`; acepta `db_path` opcional para tests |
| `cache.py` | Caché JSON con TTL; `invalidate()` y `clear()`; acepta `cache_dir` opcional |
| `watchlist_manager.py` | CRUD de watchlists: `list_watchlists()`, `load_watchlist()`, `save_watchlist()`, `delete_watchlist()`, `rename_watchlist()` |

### `alerts/`

| Archivo | Responsabilidad |
|---------|----------------|
| `telegram.py` | `TelegramAlerter` — cliente Telegram Bot API sin dependencias externas; `send()`, `test_connection()`, `alert_signals()` |

### `indicators/`

| Archivo | Responsabilidad |
|---------|----------------|
| `basic.py` | RSI, MACD, Bollinger, SMA 30/60/90, Williams %R |
| `advanced.py` | StochRSI, TSI, UO, Chaikin, Aroon, TRIX, VolumeRSI, DPO |

### `signals/`

| Archivo | Responsabilidad |
|---------|----------------|
| `generator.py` | Sistema de votación; devuelve `COMPRA / VENTA / KEEP/NO SIGNAL` |
| `advanced.py` | Señales para indicadores avanzados |

### `backtesting/`

| Archivo | Responsabilidad |
|---------|----------------|
| `costs.py` | `TransactionCosts` — comisión % + mínimo + slippage bps |
| `metrics.py` | CAGR, Sharpe, Sortino, Max Drawdown, Profit Factor, Win Rate |
| `engine.py` | `BacktestingEngine`; `run(tickers)` y `run_on_df(df)`; 4 estrategias |

### `visualization/`

| Archivo | Responsabilidad |
|---------|----------------|
| `theme.py` | Diccionarios de colores `light` / `dark` |
| `charts.py` | Gráfico Plotly 5 paneles (velas, volumen, MACD, RSI, Williams) |
| `dashboard.py` | Dashboard HTML consolidado con gauge, heatmap, scatter y tabla filtrable |

### `pipeline/`

| Archivo | Responsabilidad |
|---------|----------------|
| `runner.py` | `TradingPlatform.run_tickers()` — orquesta todo el pipeline |
| `parallel.py` | `ParallelProcessor` con `ThreadPoolExecutor` |

### `app/components/`

| Archivo | Responsabilidad |
|---------|----------------|
| `theme.py` | `apply_theme()` inyecta CSS dark mode; `sparkline()` helper Plotly; `export_csv_es()` — CSV con separador `;` y decimal `,` |

---

## 5. Proveedores de datos

### yfinance (primario)

- Gratuito, sin API key, cobertura global.
- `auto_adjust=True` corrige dividendos y splits.
- Activo por defecto desde v2.1 (Stooq exige API key).

### Stooq (fallback)

- Gratuito con API key (registro en stooq.com).
- Excelente cobertura europea. Mapeo de sufijos:

| Yahoo | Stooq | Mercado |
|-------|-------|---------|
| `.MC` | `.es` | España |
| `.DE` | `.de` | Alemania |
| `.PA` | `.fr` | Francia |
| `.L`  | `.uk` | Reino Unido |
| `.T`  | `.jp` | Japón |

### Stubs de pago (listos para activar)

| Clase | Proveedor | Coste orientativo | Mejor uso |
|-------|-----------|-------------------|-----------|
| `FMPProvider` | Financial Modeling Prep | ~22 USD/mes | Fundamentales históricos, ratings |
| `EODHDProvider` | EOD Historical Data | ~20 USD/mes | OHLCV 70+ mercados, dividendos precisos |
| `PolygonProvider` | Polygon.io | ~29 USD/mes | Real-time US, opciones, cripto |
| `FinnhubProvider` | Finnhub | Free US / pago EU | Earnings calendar, news, sentimiento |

**Activar un stub:**
1. Obtener API key del proveedor.
2. Pegarla en ⚙️ Configuración → Proveedores.
3. Implementar `fetch_ohlcv()` en `providers/_stubs.py` siguiendo los comentarios TODO.
4. Añadir instancia al inicio de `DataOrchestrator.providers`.

---

## 6. Indicadores técnicos

### Básicos (siempre activos)

| Indicador | Columna(s) | Descripción |
|-----------|-----------|-------------|
| SMA 30/60/90 | `SMA_30`, `SMA_60`, `SMA_90` | Medias móviles simples |
| RSI | `RSI` | Relative Strength Index (14 períodos) |
| MACD | `MACD`, `MACDs`, `MACDh` | MACD(12,26,9) — línea, señal, histograma |
| Bollinger | `BBU_BB`, `BBL_BB`, `BBM_BB` | Bandas de Bollinger (20, 2σ) |
| Williams %R | `WILLR` | Williams Percent Range (14 períodos) |

### Avanzados (opcionales, activar en config)

StochRSI, TSI, Ultimate Oscillator, Chaikin Money Flow, Aroon, TRIX, Volume RSI, DPO.

---

## 7. Señales y recomendaciones

Sistema de votación en `signals/generator.py`:

| Señal | Descripción |
|-------|-------------|
| `COMPRA` | Indicador en zona alcista |
| `VENTA` | Indicador en zona bajista |
| `KEEP/NO SIGNAL` | Zona neutral |

Resumen final: mayoría de votos. Empate → KEEP.

> Las señales son indicativas. No constituyen asesoramiento financiero.

---

## 8. Backtesting

### Estrategias disponibles

| ID | Nombre | Lógica |
|----|--------|--------|
| `sma_crossover` | Cruce de medias | Compra SMA30 > SMA90; vende SMA30 < SMA90 |
| `rsi_oversold` | RSI sobrevendido | Compra RSI < 30; vende RSI > 70 |
| `macd_signal` | Cruce MACD | Compra al cruce alcista MACD/señal |
| `bollinger_reversion` | Reversión Bollinger | Compra en banda inferior; vende en banda superior |

### Costes de transacción (configurables)

```python
TransactionCosts(
    commission_pct = 0.002,   # 0.2% por operación
    min_commission = 1.0,     # mínimo 1€
    slippage_bps   = 5.0,     # 5 puntos básicos
)
```

### Métricas de salida

Total Return, CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor, número y detalle de operaciones.

---

## 9. Visualización

### Página Análisis

- **Sparklines**: gráfico de línea minimalista (últimas 30 sesiones) en cada tarjeta, coloreado en verde/rojo según la señal detectada.
- **Filtros**: por tipo de señal (COMPRA/VENTA/NEUTRAL), búsqueda por ticker o empresa, ordenación por señal/ticker/RSI/volatilidad.
- **Pestaña "Tabla resumen"**: vista tabular de todos los resultados filtrados.
- **Export CSV**: formato europeo (separador `;`, decimal `,`, BOM UTF-8 para Excel).

### Informe individual (`{ticker}_analisis.html`)

Velas + SMA/Bollinger, Volumen, MACD, RSI, Williams %R. Tabla de señales por indicador.

### Dashboard consolidado (`dashboard_consolidado.html`)

KPIs, gauge de sentimiento, heatmap de volatilidad, tabla interactiva, scatter RSI vs Williams %R.

### Dark mode

Toggle en ⚙️ Configuración → Interfaz. Se persiste en `config.json` y se aplica mediante inyección CSS al recargar cualquier página. El template de Plotly cambia dinámicamente entre `plotly_white` y `plotly_dark`.

---

## 10. Alertas Telegram

Recibe un resumen de señales detectadas en Telegram después de cada RUN.

### Configuración

1. Habla con [@BotFather](https://t.me/BotFather) → `/newbot` → copia el token.
2. Habla con [@userinfobot](https://t.me/userinfobot) para obtener tu `chat_id`.
3. En ⚙️ Configuración → Alertas: pega token, chat_id y elige el modo.
4. Pulsa "Enviar mensaje de prueba" para verificar.
5. Guarda la configuración.

### Modos de alerta

| Modo | Comportamiento |
|------|---------------|
| `both` | Envía alertas de COMPRA y VENTA |
| `buy` | Solo señales de COMPRA |
| `sell` | Solo señales de VENTA |

### Sin dependencias externas

El cliente Telegram usa únicamente `urllib` de la biblioteca estándar de Python. No requiere instalar `python-telegram-bot` ni ninguna otra librería.

---

## 11. Watchlists persistentes

Las watchlists se guardan como CSV en `data/watchlists/`.

### Operaciones disponibles

| Operación | Desde la UI | Desde código |
|-----------|-------------|-------------|
| Guardar con nombre | Campo de texto + botón "💾 Guardar" | `save_watchlist(records, name)` |
| Cargar | Sidebar → botón con nombre | `load_watchlist(filename)` |
| Borrar | Sidebar → botón 🗑 | `delete_watchlist(filename)` |
| Listar | Sidebar (automático) | `list_watchlists()` |
| Renombrar | — | `rename_watchlist(old, new)` |

### Formato del fichero

```csv
ticker,name,sector
BBVA.MC,Banco Bilbao Vizcaya Argentaria,Banca
SAN.MC,Banco Santander,Banca
AAPL,Apple Inc.,Tecnología
```

### Nombres de fichero

El nombre que introduce el usuario se convierte a slug seguro: `"IBEX favoritas"` → `ibex_favoritas.csv`.

---

## 12. Configuración

`config/config.json` — estructura completa:

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
    "primary": "yfinance",
    "fallback": ["stooq"],
    "api_keys": {
      "stooq": "",
      "fmp": "",
      "eodhd": "",
      "polygon": "",
      "finnhub": ""
    }
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
  },
  "alerts": {
    "enabled": false,
    "telegram_token": "",
    "telegram_chat_id": "",
    "mode": "both"
  }
}
```

---

## 13. Instalación y arranque

### Prerrequisitos

- Python 3.10+
- pip

### Instalación

```bash
git clone <repo> && cd Trading_platform
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
pip install -e .
cp .env.example .env            # opcional
```

### Arrancar la UI

```bash
python -m streamlit run app/main.py
# → http://localhost:8501
```

### Arrancar en modo CLI

```bash
trading-platform --tickers SAN.MC BBVA.MC AAPL
trading-platform   # usa data/watchlists/default.csv
```

---

## 14. Bugs corregidos

| ID | Versión | Descripción | Solución |
|----|---------|-------------|---------|
| B1 | v2.0 | MACD bug: columnas `MACD_12_26_9` vs `MACD` | Estandarizadas a `MACD`/`MACDs`/`MACDh` |
| B2 | v2.0 | SQLite inserción fila a fila (lento) | `executemany()` |
| B3 | v2.0 | Rutas hardcodeadas al CWD | `ROOT_DIR` via `pathlib` en `constants.py` |
| B4 | v2.0 | API key Alpha Vantage en git | Movida a `.env` |
| B5 | v2.0 | `auto_adjust=False` en yfinance | Cambiado a `True` |
| B6 | v2.0 | SSL error Windows con rutas con acentos | yfinance usa SSL estándar de Python |
| B7 | v2.1 | `SyntaxError` f-string `dashboard.py` Python 3.13 | `}}}` → `}}` en gauge Plotly |
| B8 | v2.1 | Nombres de estrategia incoherentes en backtesting | Unificados: `sma_crossover`, `rsi_oversold`, `macd_signal`, `bollinger_reversion` |
| B9 | v2.1 | Stooq cambió política: exige API key | Detectado; yfinance pasa a ser primario |
| B10 | v2.1 | Sortino `RuntimeWarning` divide-by-zero | `np.std([x])` = 0 → condición `len(neg_returns) > 1` |

---

## 15. Hoja de ruta

### Completado

| Fase | Versión | Contenido |
|------|---------|-----------|
| F0 · Limpieza estructural | v2.0 | Reorganización de directorios, purga de secretos, pyproject.toml |
| F1 · DataProvider abstraction | v2.0 | Stooq + yfinance + orchestrator con fallback |
| F2 · Market CSV datasets | v2.0 | 8 índices bursátiles en `data/markets/` |
| F3 · UI Streamlit base | v2.0 | 4 páginas, flujo Watchlist → RUN |
| F4 · Backtesting honesto | v2.0 | Costes, slippage, Sharpe, CAGR, Max Drawdown |
| F5 · UI polish | v2.2 | Dark mode, sparklines, filtros, export CSV ES |
| F6 · Watchlists persistentes | v2.2 | Guardar/cargar múltiples watchlists con nombre |
| F7 · Alertas Telegram | v2.2 | Bot sin dependencias externas; disparo automático tras RUN |
| F8 · Stubs providers de pago | v2.2 | FMP, EODHD, Polygon, Finnhub listos para activar |

### Posibles mejoras futuras

- Proveedor FRED para datos macroeconómicos (tipos, VIX, inflación) — gratuito.
- Comparación multi-ticker en el mismo gráfico.
- Análisis de correlación entre activos.
- Optimización automática de parámetros de estrategia (grid search).
- Modo Docker para despliegue en servidor propio.
- Benchmark buy & hold en gráfico de backtesting.

---

*Última actualización: 2026-04-19 · Trading Platform v2.2.0*
