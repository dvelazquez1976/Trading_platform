# 📈 Plan de Mejora — Trading Platform (v2, enfoque amateur)

**Versión:** 2.0  
**Fecha:** 2026-04-19  
**Contexto:** aplicación personal, uso amateur, **coste operativo = 0 €**. Arquitectura preparada para incorporar providers de pago en el futuro sin refactor. UI moderna con flujo interactivo.

---

## 1. Objetivos del plan

1. **Mantener coste 0 €** hoy: solo fuentes de datos gratuitas (Stooq, yfinance, FRED).
2. **Arquitectura extensible**: añadir un proveedor de pago en el futuro debe ser conectar un módulo, no reescribir la aplicación.
3. **Experiencia de uso moderna**: flujo visual
   ```
   [Mercado ▼] → [Tickers ▼ multi] → [+Añadir a lista] → [Tabla watchlist] → [▶ RUN]
   ```
4. **Solidez técnica**: resolver bugs detectados, limpiar estructura, preparar el terreno para crecer.
5. **Valor financiero real**: aunque sea amateur, el backtesting y las señales tienen que dar información honesta (no inflada por ausencia de costes/slippage).

---

## 2. Fuentes de datos — estrategia 100% gratuita

### 2.1 Selección final (coste 0 €)

| Proveedor | Uso | Cobertura IBEX | Cobertura global | Notas |
|-----------|-----|----------------|------------------|-------|
| **Stooq** ⭐ primario | OHLCV histórico EOD | ✅ Excelente (`.ES` suffix) | ✅ Global | Sin API key, CSV directo, sin rate limits prácticos |
| **yfinance** fallback | OHLCV, info empresa | 🟡 Aceptable | ✅ Excelente | Frágil pero útil para metadata (`longName`, sector) |
| **FMP Free** opcional | Fundamentales básicos (P/E, market cap) | 🟡 | ✅ Buena | 250 req/día — solo al pulsar "ver fundamentales" |
| **Finnhub Free** opcional | Earnings calendar, news US | — | ✅ US | 60 req/min; EU requiere pago, así que solo para tickers US |
| **FRED** opcional | Macro: tipos, VIX, inflación | — | — | Sin límite, gratis siempre. Contexto macro. |

**Regla operativa:** la app arranca y funciona con Stooq + yfinance solamente. Los demás son opt-in, activables rellenando una API key en un ajuste (vacío por defecto).

### 2.2 Índices de mercado soportados (listas bundled)

Se distribuyen con el repo como CSV estáticos (`data/markets/*.csv`), actualizables manualmente 1-2 veces al año:

- 🇪🇸 **IBEX 35** (`ibex35.csv`) — ya disponible en `tickers.txt` actual.
- 🇺🇸 **S&P 500** (`sp500.csv`).
- 🇺🇸 **NASDAQ 100** (`nasdaq100.csv`).
- 🇪🇺 **EuroStoxx 50** (`eurostoxx50.csv`).
- 🇩🇪 **DAX 40** (`dax40.csv`).
- 🇫🇷 **CAC 40** (`cac40.csv`).
- 🇬🇧 **FTSE 100** (`ftse100.csv`).
- 🇯🇵 **Nikkei 225** (`nikkei225.csv`).
- 📋 **Watchlist personal** (`custom.csv`) — editable por el usuario.

**Formato CSV** por mercado:
```csv
ticker,name,sector
BBVA.MC,Banco Bilbao Vizcaya Argentaria,Banca
SAN.MC,Banco Santander,Banca
IBE.MC,Iberdrola,Utilities
...
```

---

## 3. Arquitectura propuesta (preparada para el futuro)

### 3.1 Patrón DataProvider

El corazón de la extensibilidad. Una interfaz, múltiples implementaciones, orquestador con fallback.

```python
# src/trading_platform/providers/base.py
from typing import Protocol
import pandas as pd

class DataProvider(Protocol):
    """Contrato que todo proveedor debe cumplir."""
    name: str
    is_free: bool
    requires_api_key: bool
    
    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> pd.DataFrame: ...
    def fetch_company_info(self, ticker: str) -> dict | None: ...
    def supports_market(self, market_code: str) -> bool: ...  # "IBEX", "SP500"...
```

**Implementaciones v1 (gratuitas):**
- `StooqProvider` — primario para EOD.
- `YFinanceProvider` — fallback + company info.

**Preparadas para futuro (stubs vacíos que lanzan `NotImplementedError`):**
- `FMPProvider` (plan pagado → fundamentales premium).
- `EODHDProvider` (plan pagado → tick data, opciones).
- `PolygonProvider` (plan pagado → real-time US).

Activarlas en el futuro = rellenar métodos + añadir API key en settings. **Cero cambios en el código que consume datos.**

### 3.2 Orchestrator con fallback automático

```python
# src/trading_platform/providers/orchestrator.py
class DataOrchestrator:
    def __init__(self, providers: list[DataProvider]):
        self.providers = providers  # en orden de preferencia
    
    def fetch_ohlcv(self, ticker, start, end):
        for p in self.providers:
            if not p.supports_market(detect_market(ticker)):
                continue
            try:
                df = p.fetch_ohlcv(ticker, start, end)
                if df is not None and not df.empty:
                    log.info(f"{ticker} resuelto por {p.name}")
                    return df
            except ProviderError as e:
                log.warning(f"{p.name} falló para {ticker}: {e}")
        raise AllProvidersFailed(ticker)
```

Configuración en `config.json`:
```json
"data_providers": {
  "ohlcv_chain": ["stooq", "yfinance"],
  "fundamentals_chain": ["yfinance"],
  "api_keys": {
    "fmp": "",
    "finnhub": "",
    "eodhd": ""
  }
}
```

### 3.3 Reorganización completa de la estructura de directorios

Este apartado es **prioritario y se ejecuta en la Fase 0**. La raíz actual mezcla código fuente, configuración, secretos, datos de entrada, datos de salida, logs, bases de datos, entornos virtuales duplicados, documentos, ficheros temporales y copias de seguridad ad-hoc. Esto provoca: (a) `.gitignore` lleno de reglas puntuales que se siguen escapando, (b) riesgo de commit accidental de datos sensibles o pesados, (c) imposibilidad de distinguir entradas (`tickers.txt`) de salidas (`Salida.txt`), (d) proyecto no empaquetable.

#### 3.3.1 Diagnóstico del desorden actual

Inventario real de la raíz (42 entradas en el nivel superior):

```
Trading_platform/
├── .claude/              ← config Claude (mantener pero gitignored)
├── .git/                 ← ok
├── .gitignore            ← ok, se renovará
├── .venv/                ← ❌ venv en raíz
├── API_Key/              ← ❌ secretos trackeados (Alpha_Vantage.txt)
├── DOCUMENTACION_TECNICA.md
├── LastQuotes.txt        ← ❌ artefacto de ejecución
├── README.md
├── SSL_PROBLEMA_Y_SOLUCIONES.md  ← ❌ nota de troubleshooting suelta
├── Salida.txt            ← ❌ salida de ejecución (55 KB)
├── __pycache__/          ← ❌ ya gitignored pero presente en disco
├── _ul                   ← ❌ ¿qué es esto? (112 bytes, sin extensión)
├── advanced_indicators.py    ← código
├── advanced_signals.py       ← código
├── backtesting_engine.py     ← código
├── cache_manager.py          ← código
├── certs/                ← ❌ cacert.pem (283 KB) para fix SSL
├── cli.py                    ← código
├── config.json           ← configuración
├── config_manager.py         ← código
├── constants.py              ← código
├── control.txt           ← ❌ log de ejecución (283 KB!)
├── csv_formatter.py          ← código
├── dashboard_generator.py    ← código
├── data_acquisition.py       ← código
├── data_storage.py           ← código
├── generar_dashboard.py      ← ❌ script suelto aparentemente redundante
├── indicator_calculator.py   ← código
├── logger_config.py          ← código
├── main.py                   ← código
├── mejoras.md                ← doc (este plan)
├── parallel_processor.py     ← código
├── plataforma_trading.db ← ❌ SQLite (4.3 MB) en raíz
├── requirements.txt      ← será pyproject.toml
├── run_with_ssl_fix.py   ← ❌ workaround SSL antiguo
├── salidas/              ← ❌ 40 HTMLs + CSVs generados, en raíz
├── signal_generator.py       ← código
├── tests/                ← ok
├── tickers - copia.txt   ← ❌ BASURA evidente (duplicado manual)
├── tickers.txt           ← entrada del usuario
├── utils.py                  ← código
├── venv_clean/           ← ❌ SEGUNDO venv duplicado
└── visualizer.py             ← código
```

**Diagnóstico resumido:**
- 16 módulos Python sueltos en raíz — deberían ir bajo un paquete.
- 2 entornos virtuales (`.venv/` + `venv_clean/`) — deja uno, borra el otro.
- Secretos en `API_Key/Alpha_Vantage.txt` trackeados en git.
- Ficheros generados (`control.txt` 283 KB, `Salida.txt` 55 KB, `LastQuotes.txt`, `plataforma_trading.db` 4.3 MB, `salidas/` 10+ MB de HTMLs).
- Basura (`tickers - copia.txt`, `_ul`, `generar_dashboard.py` posiblemente redundante con `dashboard_generator.py`).
- Docs sueltos de troubleshooting (`SSL_PROBLEMA_Y_SOLUCIONES.md`) mezclados con código.

#### 3.3.2 Estructura objetivo — limpia y autoexplicativa

```
Trading_platform/
│
├── 📱 app/                          # Interfaz de usuario (Streamlit)
│   ├── main.py                      # entrypoint: `streamlit run app/main.py`
│   ├── pages/
│   │   ├── 1_📊_Watchlist.py        # mercado → tickers → lista → RUN
│   │   ├── 2_📈_Análisis.py         # detalle por ticker
│   │   ├── 3_🔬_Backtesting.py      # UI de backtests
│   │   └── 4_⚙️_Settings.py         # config editable
│   └── components/
│       ├── ticker_picker.py
│       ├── watchlist_table.py
│       └── run_button.py
│
├── 📦 src/trading_platform/         # Código fuente (paquete instalable)
│   ├── __init__.py
│   ├── providers/                   # fuentes de datos pluggables
│   │   ├── __init__.py
│   │   ├── base.py                  # interfaz DataProvider
│   │   ├── orchestrator.py          # fallback chain
│   │   ├── stooq.py                 # gratis, primario
│   │   ├── yfinance_provider.py     # gratis, fallback
│   │   └── _stubs.py                # FMP/EODHD/Polygon (futuro)
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── basic.py                 # ← indicator_calculator.py
│   │   └── advanced.py              # ← advanced_indicators.py
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── generator.py             # ← signal_generator.py
│   │   └── advanced.py              # ← advanced_signals.py
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── engine.py                # ← backtesting_engine.py
│   │   ├── costs.py                 # modelo de costes (nuevo)
│   │   └── metrics.py               # Sharpe, MaxDD, CAGR (nuevo)
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py              # ← data_storage.py
│   │   └── cache.py                 # ← cache_manager.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── charts.py                # ← visualizer.py
│   │   ├── dashboard.py             # ← dashboard_generator.py
│   │   ├── theme.py                 # tokens light+dark (nuevo)
│   │   └── templates/               # Jinja2 si aplica
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── runner.py                # ← main.py / TradingPlatform class
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # ← config_manager.py
│   │   ├── constants.py             # ← constants.py
│   │   ├── logging.py               # ← logger_config.py
│   │   └── utils.py                 # ← utils.py
│   └── cli.py                       # ← cli.py (CLI separada)
│
├── 📥 data/                         # Entradas + salidas de ejecución
│   ├── markets/                     # 📘 ENTRADAS — índices bundled (versionados)
│   │   ├── ibex35.csv
│   │   ├── sp500.csv
│   │   ├── nasdaq100.csv
│   │   ├── dax40.csv
│   │   ├── cac40.csv
│   │   ├── eurostoxx50.csv
│   │   ├── ftse100.csv
│   │   └── nikkei225.csv
│   ├── watchlists/                  # 📘 ENTRADAS — watchlists del usuario
│   │   ├── default.csv              # era `tickers.txt`
│   │   └── *.csv                    # watchlists guardadas desde la UI
│   ├── cache/                       # 📕 DATOS DERIVADOS (gitignored)
│   │   └── *.parquet
│   ├── db/                          # 📕 BASE DE DATOS (gitignored)
│   │   └── plataforma_trading.db
│   └── outputs/                     # 📕 SALIDAS (gitignored)
│       ├── reports/                 # era `salidas/` HTMLs
│       ├── csv/                     # era CSVs de `salidas/`
│       └── logs/                    # era control.txt, salida.txt
│
├── 📝 config/                       # Configuración
│   ├── config.json                  # parámetros indicadores/señales/costes
│   └── logging.yaml                 # opcional: config estructurada de logs
│
├── 🧪 tests/                        # Tests (mantener)
│   ├── conftest.py
│   ├── test_providers.py            # nuevo: tests de cada provider
│   ├── test_indicators.py
│   ├── test_signals.py
│   ├── test_backtesting.py
│   └── fixtures/                    # datos sintéticos de test
│
├── 📚 docs/                         # Documentación
│   ├── DOCUMENTACION_TECNICA.md     # movido desde raíz
│   ├── troubleshooting/
│   │   └── ssl.md                   # era `SSL_PROBLEMA_Y_SOLUCIONES.md`
│   └── screenshots/                 # capturas de la UI para README
│
├── 🔒 .env.example                  # template de variables de entorno
├── 🔒 .env                          # (gitignored) secretos reales
├── .gitignore                       # renovado (ver §3.3.5)
├── .python-version                  # pin de versión (para pyenv/uv)
├── pyproject.toml                   # reemplaza requirements.txt
├── README.md                        # reescrito, apuntando a docs/
└── mejoras.md                       # este documento
```

**Principio rector:** cuatro categorías claramente separadas en carpetas distintas.

| Categoría | Carpeta | Ejemplos | Versionado en git |
|-----------|---------|----------|-------------------|
| 💻 **Código** | `src/`, `app/`, `tests/` | `.py` | ✅ Sí |
| ⚙️ **Configuración** | `config/` | `config.json` | ✅ Sí (sin secretos) |
| 📘 **Entradas del usuario** | `data/markets/`, `data/watchlists/` | listados, CSVs de índices | ✅ Sí |
| 📕 **Datos derivados/salidas** | `data/cache/`, `data/db/`, `data/outputs/` | HTML, parquet, SQLite, logs | ❌ No (gitignored) |

La regla es simple: **si lo genera la aplicación, no va a git; si lo edita el usuario, sí**.

#### 3.3.3 Inventario: qué hacer con cada archivo/carpeta actual

| Actual (raíz) | Acción | Destino / motivo |
|---------------|--------|------------------|
| `.claude/` | 🟰 Mantener | gitignored (config local Claude) |
| `.git/` | 🟰 Mantener | — |
| `.gitignore` | 🔄 Reescribir | ver §3.3.5 |
| `.venv/` | 🟰 Mantener | entorno virtual único |
| `venv_clean/` | ❌ Borrar | duplicado con `.venv/` |
| `API_Key/Alpha_Vantage.txt` | 🔒 Mover + gitignorar | → `.env` con `ALPHA_VANTAGE_KEY=...`; purgar del historial con `git filter-repo` |
| `DOCUMENTACION_TECNICA.md` | 📁 Mover | → `docs/DOCUMENTACION_TECNICA.md` |
| `LastQuotes.txt` | ❌ Borrar | artefacto de ejecución antigua |
| `README.md` | ✏️ Reescribir | en raíz, apuntando a nueva estructura y docs/ |
| `SSL_PROBLEMA_Y_SOLUCIONES.md` | 📁 Mover | → `docs/troubleshooting/ssl.md` |
| `Salida.txt` | ❌ Borrar + gitignorar | generado en `data/outputs/logs/salida.txt` |
| `__pycache__/` | ❌ Borrar | gitignored ya |
| `_ul` | ❌ Borrar | archivo anónimo de 112 B sin función identificable |
| `advanced_indicators.py` | 📁 Mover | → `src/trading_platform/indicators/advanced.py` |
| `advanced_signals.py` | 📁 Mover | → `src/trading_platform/signals/advanced.py` |
| `backtesting_engine.py` | 📁 Mover | → `src/trading_platform/backtesting/engine.py` |
| `cache_manager.py` | 📁 Mover | → `src/trading_platform/storage/cache.py` |
| `certs/cacert.pem` | 🔒 Evaluar | Si sigue siendo necesario, mover a `config/certs/` y documentar por qué. Si no, **borrar**. |
| `cli.py` | 📁 Mover | → `src/trading_platform/cli.py` |
| `config.json` | 📁 Mover | → `config/config.json` |
| `config_manager.py` | 📁 Mover | → `src/trading_platform/core/config.py` |
| `constants.py` | 📁 Mover | → `src/trading_platform/core/constants.py` |
| `control.txt` | ❌ Borrar + gitignorar | log de ejecución, se regenera en `data/outputs/logs/` |
| `csv_formatter.py` | 📁 Mover | → `src/trading_platform/core/utils.py` (fusionar o módulo aparte) |
| `dashboard_generator.py` | 📁 Mover | → `src/trading_platform/visualization/dashboard.py` |
| `data_acquisition.py` | ♻️ Refactor | Dividir en `providers/stooq.py`, `providers/yfinance_provider.py`, `providers/orchestrator.py` |
| `data_storage.py` | 📁 Mover | → `src/trading_platform/storage/database.py` |
| `generar_dashboard.py` | ⚠️ Analizar | Revisar si duplica `dashboard_generator.py`. Si sí → borrar. Si es wrapper → eliminar tras migrar a UI Streamlit. |
| `indicator_calculator.py` | 📁 Mover | → `src/trading_platform/indicators/basic.py` |
| `logger_config.py` | 📁 Mover | → `src/trading_platform/core/logging.py` |
| `main.py` | 📁 Mover + refactor | → `src/trading_platform/pipeline/runner.py` |
| `parallel_processor.py` | 📁 Mover | → `src/trading_platform/pipeline/parallel.py` |
| `plataforma_trading.db` | ❌ Borrar + gitignorar | se regenera en `data/db/` |
| `requirements.txt` | 🔄 Reemplazar | por `pyproject.toml` (uv/poetry) |
| `run_with_ssl_fix.py` | ❌ Borrar | workaround obsoleto — si es aún necesario, integrar fix en `providers/` |
| `salidas/` | ❌ Borrar + gitignorar | se regenera en `data/outputs/reports/` y `/csv/` |
| `signal_generator.py` | 📁 Mover | → `src/trading_platform/signals/generator.py` |
| `tests/` | 📁 Actualizar imports | Mantener la carpeta, actualizar paths de `from xxx import` |
| `tickers - copia.txt` | ❌ Borrar | **basura evidente** (duplicado manual) |
| `tickers.txt` | 📁 Renombrar + mover | → `data/watchlists/default.csv` (formato CSV con `ticker,name,sector`) |
| `utils.py` | 📁 Mover | → `src/trading_platform/core/utils.py` |
| `visualizer.py` | 📁 Mover | → `src/trading_platform/visualization/charts.py` |

**Resumen numérico:** de 42 entradas en la raíz → **~10 entradas** tras la limpieza (código bajo `src/`, datos bajo `data/`, docs bajo `docs/`, config bajo `config/`, más 5-6 ficheros de metadatos en raíz).

#### 3.3.4 Plan de migración con preservación de historial git

**Objetivo:** mover archivos con `git mv` para que `git log --follow <archivo>` siga funcionando tras la migración.

```bash
# --- PASO 0: Punto de partida seguro ---
git checkout -b refactor/estructura-limpia
git status                                    # debe estar limpio

# --- PASO 1: Crear esqueleto de directorios ---
mkdir -p src/trading_platform/{providers,indicators,signals,backtesting,storage,visualization,pipeline,core}
mkdir -p app/{pages,components}
mkdir -p data/{markets,watchlists,cache,db,outputs/{reports,csv,logs}}
mkdir -p config docs/troubleshooting tests/fixtures

# --- PASO 2: Marcadores __init__.py ---
touch src/trading_platform/__init__.py
touch src/trading_platform/{providers,indicators,signals,backtesting,storage,visualization,pipeline,core}/__init__.py
# ...igual en tests/ si falta

# --- PASO 3: Mover código con git mv (preserva historial) ---
git mv indicator_calculator.py     src/trading_platform/indicators/basic.py
git mv advanced_indicators.py      src/trading_platform/indicators/advanced.py
git mv signal_generator.py         src/trading_platform/signals/generator.py
git mv advanced_signals.py         src/trading_platform/signals/advanced.py
git mv backtesting_engine.py       src/trading_platform/backtesting/engine.py
git mv data_storage.py             src/trading_platform/storage/database.py
git mv cache_manager.py            src/trading_platform/storage/cache.py
git mv visualizer.py               src/trading_platform/visualization/charts.py
git mv dashboard_generator.py      src/trading_platform/visualization/dashboard.py
git mv parallel_processor.py      src/trading_platform/pipeline/parallel.py
git mv main.py                     src/trading_platform/pipeline/runner.py
git mv config_manager.py           src/trading_platform/core/config.py
git mv constants.py                src/trading_platform/core/constants.py
git mv logger_config.py            src/trading_platform/core/logging.py
git mv utils.py                    src/trading_platform/core/utils.py
git mv csv_formatter.py            src/trading_platform/core/csv_formatter.py
git mv cli.py                      src/trading_platform/cli.py
# data_acquisition.py → NO hacer git mv: se va a dividir en 3 archivos durante el refactor
git mv data_acquisition.py         src/trading_platform/providers/_legacy.py  # temporal

# --- PASO 4: Mover config, datos y docs ---
git mv config.json                 config/config.json
git mv tickers.txt                 data/watchlists/default.csv   # reformatear a CSV
git mv DOCUMENTACION_TECNICA.md    docs/
git mv SSL_PROBLEMA_Y_SOLUCIONES.md docs/troubleshooting/ssl.md

# --- PASO 5: Borrar basura y artefactos ---
git rm "tickers - copia.txt"
git rm -r -f salidas/ || true      # puede no estar trackeado
git rm -f Salida.txt control.txt LastQuotes.txt plataforma_trading.db _ul
git rm -f run_with_ssl_fix.py generar_dashboard.py  # tras confirmar redundancia
rm -rf venv_clean/ __pycache__/    # locales, no en git
# Evaluar certs/: si el fix SSL ya no hace falta, git rm -r certs/

# --- PASO 6: Purgar secretos del historial ---
# API_Key/Alpha_Vantage.txt nunca debería haber estado en git.
# Usar git-filter-repo (preferido sobre filter-branch):
pip install git-filter-repo
git filter-repo --path API_Key/ --invert-paths
# Nota: esto reescribe historia. Confirmar antes de push-force.

# --- PASO 7: Actualizar imports en TODOS los .py ---
# Imports cambian de:
#   import data_acquisition
#   from constants import STANDARD_COLUMNS
# A:
#   from trading_platform.providers import orchestrator as data_acquisition
#   from trading_platform.core.constants import STANDARD_COLUMNS
#
# Ejecutar búsqueda global y actualizar. Un ruff/rope automatiza parte.

# --- PASO 8: Actualizar tests/ y correr ---
pytest tests/ -v                   # todos deben pasar

# --- PASO 9: Commit por grupos lógicos ---
git commit -m "refactor: mover código fuente a src/trading_platform/"
git commit -m "refactor: separar data/ (entradas/salidas) del código"
git commit -m "refactor: consolidar docs/ y limpiar raíz"
git commit -m "chore: eliminar artefactos de ejecución y basura"
git commit -m "security: purgar API keys del historial git"
```

#### 3.3.5 `.gitignore` renovado

```gitignore
# ============================================
# Python
# ============================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# ============================================
# Entornos virtuales
# ============================================
.venv/
venv/
env/
ENV/

# ============================================
# IDE / Editores
# ============================================
.vscode/
.idea/
*.swp
*.swo
*~
.claude/

# ============================================
# Testing
# ============================================
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# ============================================
# Secretos (CRÍTICO)
# ============================================
.env
.env.local
.env.*.local
*.pem
*.key
*.crt
API_Key/          # legacy, por si reaparece

# ============================================
# Datos generados por la app (NO entradas)
# ============================================
data/cache/
data/db/
data/outputs/
# Se SÍ versionan: data/markets/ (índices bundled) y data/watchlists/ (config del usuario)

# ============================================
# OS
# ============================================
.DS_Store
Thumbs.db
desktop.ini
```

#### 3.3.6 Resultado esperado

Tras la limpieza, `ls` en la raíz muestra ~10 entradas en vez de 42:

```
Trading_platform/
├── app/              📱 UI
├── config/           ⚙️  configuración
├── data/             📦 datos (entradas versionadas, salidas ignoradas)
├── docs/             📚 documentación
├── src/              💻 código fuente
├── tests/            🧪 tests
├── .env.example      🔒 template de secretos
├── .gitignore
├── .python-version
├── mejoras.md
├── pyproject.toml
└── README.md
```

Cada carpeta tiene un propósito claro. Ningún fichero de ejecución (log, HTML, DB) en raíz. Ningún secreto trackeado. El usuario sabe de un vistazo **qué edita (config, watchlists, markets) y qué solo mira (outputs)**.

---

## 4. UI moderna — flujo mercado → tickers → lista → RUN

### 4.1 Stack recomendado: Streamlit

**Por qué Streamlit y no otra cosa:**
- Python puro, cero JavaScript.
- Widgets reactivos nativos (`selectbox`, `multiselect`, `dataframe`).
- Hot-reload al guardar.
- Despliegue gratis en Streamlit Community Cloud si algún día quieres compartirlo.
- Estética moderna por defecto, theming sencillo (light/dark).

**Alternativas consideradas y descartadas:**
- *Dash*: más potente pero más verboso, overkill para app personal.
- *Gradio*: orientado a ML, no a dashboards financieros.
- *NiceGUI*: prometedor pero comunidad más pequeña.

### 4.2 Página principal — Watchlist Builder

**Diseño del flujo exacto que has pedido:**

```
┌──────────────────────────────────────────────────────────┐
│  📊 Trading Platform — Watchlist Builder                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Paso 1 · Elige mercado                                  │
│  ┌────────────────────────────────────┐                 │
│  │ 🇪🇸 IBEX 35                    ▼  │                 │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Paso 2 · Selecciona acciones                            │
│  ┌────────────────────────────────────┐                 │
│  │ [Buscar / multi-select]         ▼  │                 │
│  │  ☑ BBVA — Banco Bilbao Vizcaya     │                 │
│  │  ☑ SAN — Banco Santander           │                 │
│  │  ☐ IBE — Iberdrola                 │                 │
│  │  ...                               │                 │
│  └────────────────────────────────────┘                 │
│  [ + Añadir a watchlist ]                                │
│                                                          │
│  Paso 3 · Tu watchlist (5)                               │
│  ┌────────┬─────────────────┬──────────┬───────┐        │
│  │ Ticker │ Empresa         │ Sector   │  🗑   │        │
│  ├────────┼─────────────────┼──────────┼───────┤        │
│  │ BBVA.MC│ BBVA            │ Banca    │  ✕    │        │
│  │ SAN.MC │ Santander       │ Banca    │  ✕    │        │
│  │ AAPL   │ Apple Inc.      │ Tech     │  ✕    │        │
│  └────────┴─────────────────┴──────────┴───────┘        │
│                                                          │
│  [💾 Guardar lista] [📂 Cargar lista]                    │
│                                                          │
│  ════════════════════════════════════════════════        │
│                                                          │
│              ┌───────────────────────────┐              │
│              │   ▶  RUN  ANÁLISIS       │  ← botón      │
│              │   5 tickers · ~12 seg     │    grande     │
│              └───────────────────────────┘              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Implementación resumida (Streamlit real, no pseudocódigo):**

```python
# app/pages/1_📊_Watchlist.py
import streamlit as st
from trading_platform.markets import load_market
from trading_platform.pipeline import run_analysis

st.title("📊 Watchlist Builder")

# Inicializar estado
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

# Paso 1: Mercado
market = st.selectbox(
    "🌍 Elige mercado",
    ["IBEX 35", "S&P 500", "NASDAQ 100", "DAX 40", "CAC 40",
     "EuroStoxx 50", "FTSE 100", "Nikkei 225", "Personalizado"]
)
tickers_df = load_market(market)  # lee CSV bundled

# Paso 2: Multi-select con autocomplete
seleccion = st.multiselect(
    "📈 Selecciona acciones",
    options=tickers_df["ticker"].tolist(),
    format_func=lambda t: f"{t} — {tickers_df.loc[tickers_df.ticker==t, 'name'].iloc[0]}"
)
if st.button("➕ Añadir a watchlist"):
    for t in seleccion:
        if t not in [w["ticker"] for w in st.session_state.watchlist]:
            row = tickers_df[tickers_df.ticker == t].iloc[0]
            st.session_state.watchlist.append(row.to_dict())

# Paso 3: Tabla watchlist con botones de borrar
st.subheader(f"📋 Tu watchlist ({len(st.session_state.watchlist)})")
st.dataframe(st.session_state.watchlist, use_container_width=True)

col1, col2 = st.columns(2)
if col1.button("💾 Guardar"):
    save_watchlist(st.session_state.watchlist)
if col2.button("📂 Cargar"):
    st.session_state.watchlist = load_watchlist()

st.divider()

# Botón RUN
if st.button("▶  RUN ANÁLISIS", type="primary", use_container_width=True):
    if not st.session_state.watchlist:
        st.error("Añade al menos un ticker a la watchlist")
    else:
        tickers = [w["ticker"] for w in st.session_state.watchlist]
        with st.status("Analizando...", expanded=True) as status:
            for i, ticker in enumerate(tickers):
                st.write(f"Procesando {ticker}...")
                run_analysis([ticker])
            status.update(label="✅ Completado", state="complete")
        st.switch_page("pages/2_📈_Análisis.py")
```

### 4.3 Otras páginas de la app

**Página Análisis (`2_📈_Análisis.py`)**
- Selector de ticker analizado.
- Gráfico Plotly (el actual reutilizable).
- Tarjeta de recomendación (COMPRA/VENTA/HOLD).
- Tabla de señales por indicador.
- Sparkline con últimos 30 días.
- Dashboard consolidado comparando todos los de la watchlist.

**Página Backtesting (`3_🔬_Backtesting.py`)**
- Selector de estrategia (dropdown).
- Capital inicial (slider).
- Rango de fechas (date picker).
- Botón "Ejecutar" → muestra equity curve, métricas, tabla de trades.
- Comparación side-by-side de dos estrategias.

**Página Settings (`4_⚙️_Settings.py`)**
- Tema: claro / oscuro / auto.
- API keys para providers de pago (vacías por defecto).
- Parámetros de indicadores (sliders que antes estaban en `config.json`).
- Modelo de costes de transacción para backtesting (comisión, slippage).

### 4.4 Theming moderno

- Fuente: **Inter** (ya la usas, bien).
- Paleta actual (Soft Fintech Light) se conserva pero extraída a `theme.py` con variante dark.
- Streamlit admite `.streamlit/config.toml` para tema:
  ```toml
  [theme]
  base = "light"
  primaryColor = "#0284c7"
  backgroundColor = "#f8fafc"
  secondaryBackgroundColor = "#ffffff"
  textColor = "#1e293b"
  font = "sans serif"
  ```
- Componentes custom con HTML/CSS inyectado donde Streamlit se quede corto.

---

## 5. Deudas técnicas prioritarias (bloqueantes)

Estas van primero porque pueden dar problemas reales al usuario y bloquean el resto del plan.

### 5.1 🔴 Bug crítico: MACD en backtesting nunca genera señales

**Dónde:** `backtesting_engine.py:141-151` referencia `MACD_12_26_9` y `MACDs_12_26_9`.  
**Realidad:** `indicator_calculator.py:80-82` estandariza a `MACD`, `MACDh`, `MACDs`.  
**Efecto:** la estrategia `macd_signal` devuelve siempre `HOLD`. El backtesting de esa estrategia siempre sale con 0 operaciones. Un cero silencioso.  
**Fix:** renombrar a los nombres estandarizados. Añadir test que ejecute cada estrategia sobre datos sintéticos y afirme `num_trades > 0`.

### 5.2 🔴 Ficheros sensibles en repo
- Mover `API_Key/` fuera del tracking de git.
- Añadir `.env.example` como template.
- Usar `python-dotenv` + `pydantic-settings` para cargar.

### 5.3 🔴 Limpieza estructural total (ver §3.3 con plan detallado)
La raíz actual tiene **42 entradas** mezclando código, datos, salidas, logs, secretos, entornos virtuales duplicados y basura (`tickers - copia.txt`, `_ul`). Esto hace inmantenible el proyecto y produce commits accidentales de datos pesados/sensibles. El objetivo es dejar la raíz con ~10 entradas y cuatro carpetas de propósito único:

- `src/` — código fuente (paquete `trading_platform`).
- `app/` — UI Streamlit.
- `data/` — entradas del usuario (versionadas: `markets/`, `watchlists/`) vs. salidas generadas (gitignored: `cache/`, `db/`, `outputs/`).
- `config/`, `docs/`, `tests/` — propósitos obvios.

Ver §3.3 para inventario archivo-a-archivo, plan de migración con `git mv` y `.gitignore` renovado.

### 5.4 🟡 Inserciones row-by-row en SQLite
`data_storage.py:152` itera con `INSERT OR REPLACE` fila a fila. Con 40 tickers × 500 días = 20.000 inserts por ejecución. Migrar a `executemany` o `to_sql` → **10-50× más rápido**.

### 5.5 🟢 Nombre inconsistente del fichero de salida
`config.json:46` dice `"output_file": "Salida.txt"` (mayúscula) pero `main.py:401` escribe `'salida.txt'` (minúscula). En Windows no importa, en Linux sí. Estandarizar a `salida.txt`.

---

## 6. Mejoras financieras mínimas (para que los resultados sean honestos)

Aun siendo amateur, estos cambios evitan que la app mienta al usuario:

### 6.1 Costes en backtesting (1 día)
Añadir configurable en `settings`:
```json
"transaction_costs": {
  "commission_pct": 0.002,     // 0.2% típico broker retail EU
  "min_commission_eur": 1.0,
  "slippage_bps": 5             // 5 basis points = 0.05%
}
```
Aplicar en apertura y cierre de cada `Trade`. Sin esto, los retornos de backtest están inflados.

### 6.2 Métricas de riesgo (1 día)
Añadir a la salida de backtesting:
- **CAGR**: `(1 + total_return) ** (365/days) - 1`.
- **Sharpe** (con risk-free = 2% anual hardcoded, editable en settings).
- **Max Drawdown**: pico de la equity curve y mayor caída.
- **Win rate**, **profit factor** (ya casi están).

### 6.3 Benchmark buy & hold (medio día)
Cuando corres un backtest sobre N tickers, descargar también `^IBEX` (o `^GSPC` si todo son US) y mostrar el buy & hold como línea de comparación.

### 6.4 Opcional: dividendos y splits
`yfinance` los expone por separado. Cambiar `auto_adjust=False` → `True` para que los precios vengan ajustados. Es una línea.

---

## 7. Roadmap por fases (coste 0 €)

| Fase | Tiempo part-time | Entregables | Prioridad |
|------|------------------|-------------|-----------|
| **F0 · Limpieza estructural + quick wins** | 3-4 días | Reorganización completa de directorios (§3.3), bug MACD, `.env`, `pyproject.toml`, purga de secretos del historial git | 🔴 |
| **F1 · Abstracción DataProvider** | 3-4 días | Interfaz + StooqProvider + YFProvider + Orchestrator + tests | 🔴 |
| **F2 · Datasets de mercados** | 1 día | CSVs bundled (IBEX, S&P, NASDAQ, DAX, CAC, EuroStoxx, FTSE) | 🔴 |
| **F3 · UI Streamlit base** | 4-5 días | App con 4 páginas, flujo mercado→tickers→watchlist→RUN | 🟡 |
| **F4 · Backtesting honesto** | 2-3 días | Costes, slippage, Sharpe, MaxDD, benchmark | 🟡 |
| **F5 · UI polish** | 2-3 días | Dark mode, sparklines, filtros, export CSV | 🟡 |
| **F6 · Watchlists persistentes** | 1-2 días | Guardar/cargar watchlists con nombre, historial | 🟢 |
| **F7 · Alertas opcionales** | 2-3 días | Telegram bot (gratis) cuando señal fuerte | 🟢 |
| **F8 · Stubs providers de pago** | 1 día | Esqueletos `FMPProvider`, `EODHDProvider` listos para rellenar cuando quieras pagar | 🟢 |

**Total estimado:** 18-25 días de trabajo part-time para tener todo. Las fases F0-F3 dan ya una app usable nueva en ~12 días.

---

## 8. Preparación para el futuro (cuando quieras pagar)

Cuando decidas invertir en datos de calidad, estos son los puntos de entrada ya diseñados:

### 8.1 Activar un proveedor de pago
1. Crear cuenta en el proveedor (FMP, EODHD...).
2. Copiar API key.
3. Abrir la app → Settings → pegar la key.
4. En `config.json` cambiar `"ohlcv_chain": ["stooq", "yfinance"]` por `["fmp", "stooq", "yfinance"]`.
5. Reiniciar → primer proveedor a consultar será FMP, fallback a los gratuitos.

**No tocas una línea de código**. Este es el valor de invertir 3-4 días en la abstracción `DataProvider` ahora.

### 8.2 Features que se desbloquearían con pago

| Feature | Requiere | Proveedor sugerido |
|---------|----------|-------------------|
| Fundamentales completos (ratios históricos, balance, cash-flow) | Plan pago | FMP Starter $22/mes |
| Dividendos IBEX 100% correctos, splits precisos | Plan pago | EODHD All-World $19.99/mes |
| Earnings calendar completo con estimaciones consensus | Plan pago | Finnhub Starter $59/mes |
| Real-time (no delay 15 min) | Plan pago | Polygon/Twelve Data $29/mes |
| Tick data, opciones | Plan pago | Polygon plans superiores |
| News con sentiment analysis | Plan pago | Finnhub |

### 8.3 Diseño que no se va a tirar
- Arquitectura modular: los providers pagados se enchufan.
- Streamlit escala: cuando la UI crezca, migras a FastAPI+React manteniendo la lógica en `src/trading_platform/`.
- SQLAlchemy-ready: cuando el volumen pase SQLite, cambias el URL de conexión.
- Config en JSON: fácilmente migrable a `pydantic-settings` con validación.

---

## 9. Siguientes pasos concretos

**Esta semana (orden propuesto):**

1. **Rama de refactor estructural.** `git checkout -b refactor/estructura-limpia` y ejecutar pasos 1-9 del plan de migración (§3.3.4). 1-2 días. Al final de esto la raíz tiene ~10 entradas en vez de 42.
2. **Validar el bug MACD.** Escribir un test que falle y luego el fix sobre la nueva estructura. 1 hora.
3. **Purga de secretos** (`git filter-repo` sobre `API_Key/`). Medio día, con backup previo del repo.
4. **Preparar los CSV de mercados** (§2.2). Manual, ~2 horas para 7 índices, viven en `data/markets/`.
5. **Construir `StooqProvider` mínimo** y comparar con yfinance sobre 5 tickers IBEX. Medio día.

**Próxima semana:**

5. **Orchestrator + tests** de la cadena Stooq → yfinance.
6. **Primer esqueleto de la app Streamlit** con solo la página Watchlist funcional.
7. **Conectar RUN** con el pipeline actual (`main.py` reutilizado como función).

**Después:**

8. Backtesting con costes.
9. Páginas restantes (Análisis detallado, Backtesting, Settings).
10. Dark mode + polish.

---

## 10. Principios de diseño que guían este plan

- **Simplicidad primero**: lo más sencillo que funciona. Si Streamlit basta, no montar FastAPI+React.
- **Extensible por defecto**: interfaces antes que implementaciones. Un proveedor nuevo debe costar ~100 líneas de código.
- **Honestidad de resultados**: un backtest sin costes es un backtest que miente. Preferible un número peor y real.
- **Coste 0 hoy, preparado para mañana**: los stubs vacíos de FMP/EODHD son inversión barata que ahorra un refactor doloroso futuro.
- **UI que invita a usar**: el flujo mercado → ticker → watchlist → RUN es el 80% del valor percibido. Todo lo demás es derivado.

---

*Fin del plan v2. Si algún punto no encaja con tu intención (prioridades, tiempos, stack), iteramos antes de escribir una línea de código.*
