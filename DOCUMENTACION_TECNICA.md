# Plataforma de Trading - Documentación Técnica Completa

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura General](#arquitectura-general)
3. [Flujo de Ejecución Completo](#flujo-de-ejecución-completo)
4. [Módulos del Sistema](#módulos-del-sistema)
5. [Estructuras de Datos](#estructuras-de-datos)
6. [Configuración](#configuración)
7. [Archivos de Salida](#archivos-de-salida)
8. [Diagramas de Flujo](#diagramas-de-flujo)
9. [Guía de Mantenimiento](#guía-de-mantenimiento)

---

## Introducción

### ¿Qué es esta plataforma?

La **Plataforma de Trading** es un sistema automatizado de análisis técnico para activos financieros (acciones, ETFs, etc.). El sistema:

- Descarga datos históricos de múltiples activos desde Yahoo Finance
- Calcula más de 20 indicadores técnicos (básicos y avanzados)
- Genera señales de compra/venta basadas en el análisis técnico
- Crea visualizaciones interactivas en HTML
- Exporta resultados a CSV y tablas formateadas
- Almacena datos en base de datos SQLite para análisis histórico

### Características Principales

✅ **Análisis Multi-Ticker**: Procesa múltiples activos en paralelo o secuencialmente
✅ **Indicadores Completos**: 8 indicadores básicos + 8 indicadores avanzados opcionales
✅ **Visualización Interactiva**: Gráficos Plotly con candlesticks, volumen e indicadores
✅ **Exportación Flexible**: CSV formateado para Excel, tablas en formato texto
✅ **Logging Detallado**: Sistema de logging que separa mensajes de control y resultados
✅ **Configuración Flexible**: Archivo JSON para personalizar todos los parámetros

---

## Arquitectura General

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    PLATAFORMA DE TRADING                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │        main.py (Orquestador)            │
        │     Clase: TradingPlatform              │
        └─────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│  Adquisición Datos   │              │  Procesamiento       │
│  ─────────────────   │              │  ─────────────────   │
│ • data_acquisition   │              │ • parallel_processor │
│ • data_storage       │              │ • Modo secuencial    │
└──────────────────────┘              └──────────────────────┘
          │                                       │
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│  Análisis Técnico    │              │  Salida Resultados   │
│  ─────────────────   │              │  ─────────────────   │
│ • indicator_calc     │              │ • visualizer         │
│ • signal_generator   │              │ • csv_formatter      │
│ • advanced_*         │              │ • Tablas            │
└──────────────────────┘              └──────────────────────┘
          │                                       │
          └───────────────────┬───────────────────┘
                              ▼
              ┌──────────────────────────────┐
              │     Infraestructura          │
              │  ─────────────────────       │
              │  • config_manager            │
              │  • logger_config             │
              │  • constants                 │
              │  • utils                     │
              └──────────────────────────────┘
```

### Módulos y Responsabilidades

| Módulo | Responsabilidad | Archivo |
|--------|----------------|---------|
| **Orquestador Principal** | Coordina todo el flujo de ejecución | `main.py` |
| **Adquisición de Datos** | Descarga datos de Yahoo Finance | `data_acquisition.py` |
| **Almacenamiento** | Gestiona base de datos SQLite | `data_storage.py` |
| **Cálculo Indicadores** | Calcula indicadores técnicos básicos | `indicator_calculator.py` |
| **Indicadores Avanzados** | Calcula indicadores avanzados opcionales | `advanced_indicators.py` |
| **Generación de Señales** | Analiza indicadores y genera señales | `signal_generator.py` |
| **Señales Avanzadas** | Genera señales de indicadores avanzados | `advanced_signals.py` |
| **Visualización** | Crea gráficos HTML interactivos | `visualizer.py` |
| **Procesamiento Paralelo** | Gestiona ejecución multihilo | `parallel_processor.py` |
| **Formateo CSV** | Convierte CSV a formato Excel | `csv_formatter.py` |
| **Configuración** | Gestiona config.json | `config_manager.py` |
| **Logging** | Sistema centralizado de logs | `logger_config.py` |
| **Constantes** | Define constantes del sistema | `constants.py` |
| **Utilidades** | Funciones auxiliares comunes | `utils.py` |

---

## Flujo de Ejecución Completo

### Secuencia de Ejecución Paso a Paso

```
INICIO DEL PROGRAMA
    │
    ▼
[1] Inicialización de TradingPlatform
    │   • Crea instancia de la clase principal
    │   • Inicializa logger
    │   • Configura directorio de salidas
    │
    ▼
[2] Inicialización de Base de Datos
    │   • Verifica si existe plataforma_trading.db
    │   • Crea tabla precios_acciones si no existe
    │   • Estructura: (id, ticker, fecha, apertura, maximo, minimo, cierre, volumen)
    │
    ▼
[3] Carga de Tickers
    │   • Lee archivo tickers.txt
    │   • Filtra líneas vacías
    │   • Almacena lista de tickers a procesar
    │   • Registra en log cuántos tickers se cargaron
    │
    ▼
[4] Configuración de Rango de Fechas
    │   • Lee config.json -> data.analysis_period_days (default: 730)
    │   • fecha_fin = HOY
    │   • fecha_inicio = HOY - analysis_period_days
    │   • Registra rango en log
    │
    ▼
[5] Determinación del Modo de Procesamiento
    │   • Lee config.json -> processing.parallel_processing
    │   • Lee config.json -> processing.max_workers
    │   • Si parallel_processing = true Y hay >1 ticker → MODO PARALELO
    │   • Si parallel_processing = false O hay 1 ticker → MODO SECUENCIAL
    │
    ├──────────────┬──────────────┐
    │              │              │
    ▼              ▼              ▼
MODO SECUENCIAL   MODO PARALELO
    │              │
    │              ├→ [6a] Crea ThreadPoolExecutor con max_workers
    │              │
    │              ├→ [6b] Envía todos los tickers al pool
    │              │
    └──────────────┴→ [6c] Para cada ticker (secuencial o paralelo):
                        │
                        ├→ Descarga datos históricos (yfinance)
                        │   • Llama a yf.download(ticker, start, end)
                        │   • Valida que los datos existan
                        │   • Convierte columnas a español
                        │   • Obtiene nombre de la empresa
                        │
                        ├→ Almacena en base de datos
                        │   • INSERT OR REPLACE INTO precios_acciones
                        │   • Evita duplicados por (ticker, fecha)
                        │
                        ├→ Calcula indicadores técnicos
                        │   • Convierte columnas a inglés para pandas_ta
                        │   • Calcula SMA (30, 60, 90)
                        │   • Calcula RSI (14)
                        │   • Calcula Estocástico (K=14, D=3)
                        │   • Calcula MACD (12, 26, 9)
                        │   • Calcula Bandas de Bollinger (20, 2)
                        │   • Calcula CCI (20)
                        │   • Calcula ADX (14)
                        │   • Calcula MFI (14)
                        │   • Calcula Williams %R (14)
                        │   • Calcula Awesome Oscillator (5, 34)
                        │   • Calcula ROC (12)
                        │   • Si advanced_indicators.enabled = true:
                        │       • Calcula Stochastic RSI
                        │       • Calcula TSI (True Strength Index)
                        │       • Calcula Ultimate Oscillator
                        │       • Calcula Chaikin Oscillator
                        │       • Calcula Aroon Oscillator
                        │       • Calcula TRIX
                        │       • Calcula Volume RSI
                        │       • Calcula DPO (Detrended Price Oscillator)
                        │   • Convierte columnas de vuelta a español
                        │   • Elimina filas con NaN
                        │
                        ├→ Genera señales de trading
                        │   • Obtiene últimas 2 filas de datos
                        │   • Para cada indicador básico:
                        │       ├─ Cruce_Medias: SMA_30 vs SMA_60
                        │       ├─ RSI: oversold(<30) / overbought(>70)
                        │       ├─ Estocastico: K vs D en zonas extremas
                        │       ├─ MACD: MACD vs Signal
                        │       ├─ Bandas_Bollinger: Precio vs BBL/BBU
                        │       ├─ Williams_R: oversold(<-80) / overbought(>-20)
                        │       ├─ Awesome_Oscillator: Cruce con 0
                        │       └─ ROC: bullish(>5) / bearish(<-5)
                        │   • Si advanced_indicators.enabled = true:
                        │       • Genera señales para cada indicador avanzado
                        │   • Calcula resumen:
                        │       • Cuenta señales de COMPRA vs VENTA
                        │       • Resumen = mayoría
                        │   • Construye resultado:
                        │       • ticker, fecha, precio_cierre
                        │       • señales (dict con todos los indicadores)
                        │       • resumen (COMPRA/VENTA/KEEP)
                        │
                        └→ Genera gráfico interactivo
                            • Crea figura Plotly con 4 subplots:
                                1. Candlestick + SMAs
                                2. Volumen
                                3. RSI con líneas 30/70
                                4. Williams %R con líneas -20/-80
                            • Guarda HTML en salidas/{ticker}_analisis.html
                        │
                        └→ Almacena resultado para tablas finales
    │
    ▼
[7] Exportación a CSV
    │   • Concatena todos los DataFrames históricos
    │   • Para cada tipo de dato (apertura, maximo, minimo, cierre, volumen):
    │       • Crea tabla pivote: ticker x fecha
    │       • Exporta a CSV: salidas/{tipo}_data.csv
    │       • Modifica formato:
    │           - Cambia delimitador ',' → ';'
    │           - Cambia decimal '.' → ','
    │           - Formato compatible con Excel español
    │
    ▼
[8] Generación de Tablas de Resultados
    │   • Captura output en StringIO para separar de logs
    │   • Genera 3 tablas básicas (siempre):
    │       ├─ TABLA 1: Resumen General
    │       │   • Ticker, Empresa, Fecha, Precio Cierre, Recomendación
    │       │
    │       ├─ TABLA 2: Señales de Indicadores Básicos
    │       │   • Ticker + señal de cada indicador
    │       │
    │       └─ TABLA 3: Valores de Indicadores Básicos
    │           • Ticker + valor numérico de cada indicador
    │
    │   • Si advanced_indicators.enabled = true:
    │       ├─ TABLA 4: Señales de Indicadores Avanzados
    │       └─ TABLA 5: Valores de Indicadores Avanzados
    │
    │   • Formatea con tabulate (formato grid)
    │
    ▼
[9] Guardado de Resultados
    │   • Escribe tablas en salida.txt
    │   • Todos los logs ya están en control.txt
    │
    ▼
[10] Resumen Final
    │   • Registra en log:
    │       • Número de tickers procesados
    │       • Ubicación de archivos generados:
    │           - control.txt (logs)
    │           - salida.txt (tablas)
    │           - salidas/*.csv (datos)
    │           - salidas/*.html (gráficos)
    │
    ▼
FIN DEL PROGRAMA
```

---

## Módulos del Sistema

### 1. main.py - Orquestador Principal

**Clase Principal**: `TradingPlatform`

**Atributos**:
- `tickers`: List[str] - Lista de símbolos a analizar
- `fecha_inicio`: date - Fecha de inicio del análisis
- `fecha_fin`: date - Fecha final del análisis
- `ticker_data_collection`: List[Dict] - Resultados de análisis
- `all_historical_data`: List[DataFrame] - Datos históricos de todos los tickers
- `salidas_dir`: str - Directorio de salidas

**Métodos Principales**:

#### `load_tickers(tickers_file='tickers.txt') -> bool`
```python
# Lee el archivo de tickers línea por línea
# Filtra líneas vacías
# Retorna True si carga exitosa, False si error
```

#### `setup_date_range(analysis_days=730)`
```python
# Calcula fecha_inicio = hoy - analysis_days
# fecha_fin = hoy
# Registra rango en logger
```

#### `process_ticker_sequential(ticker) -> bool`
```python
# PASO 1: Descarga datos históricos
datos, company = data_acquisition.descargar_datos(ticker, inicio, fin)

# PASO 2: Guarda en base de datos
data_storage.guardar_datos(datos, ticker)

# PASO 3: Calcula indicadores
datos_indicadores = indicator_calculator.calcular_indicadores(datos)

# PASO 4: Genera señales
resultado = signal_generator.generar_senales(datos_indicadores)

# PASO 5: Crea gráfico
visualizer.generar_grafico(datos_indicadores, resultado, ticker)

# PASO 6: Almacena resultado
self.ticker_data_collection.append(...)
```

#### `process_all_tickers_parallel(max_workers=4)`
```python
# Crea ThreadPoolExecutor
# Envía todos los tickers al pool
# Espera resultados y los procesa
```

#### `export_csv_data()`
```python
# Concatena todos los datos históricos
# Para cada tipo de dato (open, high, low, close, volume):
#   - Crea pivot table (ticker x fecha)
#   - Exporta a CSV
#   - Formatea para Excel (delimitador ; y decimal ,)
```

#### `generate_summary_tables() -> str`
```python
# Captura output en StringIO
# Genera tablas con tabulate:
#   - Tabla 1: Resumen General
#   - Tabla 2: Señales Básicas
#   - Tabla 3: Valores Básicos
#   - Tabla 4: Señales Avanzadas (si enabled)
#   - Tabla 5: Valores Avanzados (si enabled)
# Retorna string con todas las tablas
```

#### `run()`
```python
# Flujo completo de ejecución
# Ver diagrama de flujo arriba
```

---

### 2. data_acquisition.py - Descarga de Datos

**Función Principal**: `descargar_datos(ticker, fecha_inicio, fecha_fin)`

**Flujo Interno**:
```python
1. Validar ticker (no vacío, formato válido)
2. Validar fechas (formato YYYY-MM-DD válido)
3. Llamar a yfinance.download():
   - ticker: símbolo del activo
   - start: fecha_inicio
   - end: fecha_fin
   - auto_adjust=False (no ajustar por splits/dividendos)
   - progress=False (sin barra de progreso)
4. Verificar que datos no estén vacíos
5. Manejar MultiIndex si existe (yfinance a veces lo retorna)
6. Resetear índice (fecha pasa a ser columna)
7. Renombrar columnas de inglés a español:
   - Date → fecha
   - Open → apertura
   - High → maximo
   - Low → minimo
   - Close → cierre
   - Volume → volumen
8. Verificar columnas requeridas presentes
9. Convertir columna fecha a datetime
10. Validar que valores numéricos no sean todos NaN
11. Obtener nombre de empresa con get_company_name()
12. Retornar (DataFrame, nombre_empresa)
```

**Función Auxiliar**: `get_company_name(ticker)`
```python
1. Crear objeto yf.Ticker(ticker)
2. Obtener .info (metadatos del activo)
3. Extraer info.get('longName', ticker)
4. Si falla, retornar ticker como fallback
```

---

### 3. data_storage.py - Gestión de Base de Datos

**Base de Datos**: SQLite (`plataforma_trading.db`)

**Esquema de Tabla**:
```sql
CREATE TABLE IF NOT EXISTS precios_acciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    fecha DATE NOT NULL,
    apertura REAL NOT NULL,
    maximo REAL NOT NULL,
    minimo REAL NOT NULL,
    cierre REAL NOT NULL,
    volumen INTEGER NOT NULL,
    UNIQUE(ticker, fecha)  -- Evita duplicados
)
```

**Context Manager**: `get_db_connection()`
```python
# Gestiona conexión a DB automáticamente
# En caso de error, hace rollback
# Siempre cierra la conexión
with get_db_connection() as conn:
    # Operar con conn
    # Auto-commit al salir
```

**Función**: `crear_base_de_datos()`
```python
# Crea archivo .db si no existe
# Crea tabla precios_acciones con CREATE TABLE IF NOT EXISTS
# No borra datos existentes
```

**Función**: `guardar_datos(datos, ticker)`
```python
# Valida entrada (DataFrame no vacío, ticker válido)
# Para cada fila del DataFrame:
#   INSERT OR REPLACE INTO precios_acciones (...)
#   VALUES (ticker, fecha, apertura, maximo, minimo, cierre, volumen)
# INSERT OR REPLACE: si existe (ticker, fecha), actualiza; si no, inserta
```

**Función**: `leer_datos(ticker) -> DataFrame`
```python
# Ejecuta query:
SELECT fecha, apertura, maximo, minimo, cierre, volumen
FROM precios_acciones
WHERE ticker = ?
ORDER BY fecha

# Retorna DataFrame con parse_dates=['fecha']
```

---

### 4. indicator_calculator.py - Cálculo de Indicadores Técnicos

**Función Principal**: `calcular_indicadores(datos) -> DataFrame`

**Preparación**:
```python
1. Validar columnas requeridas (fecha, apertura, maximo, minimo, cierre, volumen)
2. Copiar DataFrame
3. Renombrar columnas a inglés para pandas_ta:
   - fecha → date
   - apertura → open
   - maximo → high
   - minimo → low
   - cierre → close
   - volumen → volume
```

**Indicadores Básicos Calculados**:

| Indicador | Fórmula/Librería | Parámetros Default | Columna Resultado |
|-----------|-----------------|-------------------|-------------------|
| **SMA** | ta.sma() | periods=[30, 60, 90] | SMA_30, SMA_60, SMA_90 |
| **RSI** | ta.rsi() | length=14 | RSI |
| **Estocástico** | ta.stoch() | k=14, d=3 | STOCHk_14_3_3, STOCHd_14_3_3 |
| **MACD** | ta.macd() | fast=12, slow=26, signal=9 | MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9 |
| **Bandas Bollinger** | ta.bbands() | length=20, std=2 | BBL_20_2, BBM_20_2, BBU_20_2 |
| **CCI** | ta.cci() | length=20 | CCI |
| **ADX** | ta.adx() | length=14 | ADX_14, DMP_14, DMN_14 |
| **MFI** | ta.mfi() | length=14 | MFI_14 |
| **Williams %R** | ta.willr() | length=14 | WILLR |
| **AO** | ta.ao() | fast=5, slow=34 | AO |
| **ROC** | ta.roc() | length=12 | ROC_12 |

**Indicadores Avanzados (si enabled)**:

Se llama a `advanced_indicators.calculate_all_advanced_indicators()` que calcula:
- Stochastic RSI
- TSI (True Strength Index)
- Ultimate Oscillator
- Chaikin Oscillator
- Aroon Oscillator
- TRIX
- Volume RSI
- DPO

**Finalización**:
```python
1. Renombrar columnas de vuelta a español
2. Retornar DataFrame con indicadores
```

---

### 5. signal_generator.py - Generación de Señales

**Función Principal**: `generar_senales(datos) -> Dict`

**Estructura del Flujo**:
```python
1. Obtener umbrales de config.json -> signals
2. Inicializar diccionario de señales:
   {
       "Cruce_Medias": "KEEP/NO SIGNAL",
       "RSI": "KEEP/NO SIGNAL",
       ...
   }
3. Obtener última y penúltima fila de datos
4. Para cada indicador, evaluar condiciones
5. Actualizar diccionario con señal (COMPRA/VENTA/KEEP)
6. Calcular resumen (mayoría de votos)
7. Construir resultado final
```

**Lógica de Cada Indicador**:

#### Cruce de Medias (SMA_30 vs SMA_60)
```python
if SMA_30_actual > SMA_60_actual AND SMA_30_anterior <= SMA_60_anterior:
    señal = "COMPRA"  # Cruce alcista
elif SMA_30_actual < SMA_60_actual AND SMA_30_anterior >= SMA_60_anterior:
    señal = "VENTA"   # Cruce bajista
else:
    señal = "KEEP/NO SIGNAL"
```

#### RSI
```python
if RSI < 30:
    señal = "COMPRA"  # Sobreventa
elif RSI > 70:
    señal = "VENTA"   # Sobrecompra
else:
    señal = "KEEP/NO SIGNAL"
```

#### Estocástico
```python
# En zona de sobreventa (<20)
if STOCHk < 20 AND STOCHd < 20:
    if STOCHk_actual > STOCHd_actual AND STOCHk_anterior <= STOCHd_anterior:
        señal = "COMPRA"  # Cruce alcista en sobreventa

# En zona de sobrecompra (>80)
elif STOCHk > 80 AND STOCHd > 80:
    if STOCHk_actual < STOCHd_actual AND STOCHk_anterior >= STOCHd_anterior:
        señal = "VENTA"  # Cruce bajista en sobrecompra
```

#### MACD
```python
if MACD_actual > Signal_actual AND MACD_anterior <= Signal_anterior:
    señal = "COMPRA"  # Cruce alcista
elif MACD_actual < Signal_actual AND MACD_anterior >= Signal_anterior:
    señal = "VENTA"   # Cruce bajista
```

#### Bandas de Bollinger
```python
if precio_cierre < BBL (banda inferior):
    señal = "COMPRA"  # Precio toca banda inferior
elif precio_cierre > BBU (banda superior):
    señal = "VENTA"   # Precio toca banda superior
```

#### Williams %R
```python
if WILLR < -80:
    señal = "COMPRA"  # Sobreventa
elif WILLR > -20:
    señal = "VENTA"   # Sobrecompra
```

#### Awesome Oscillator
```python
if AO_actual > 0 AND AO_anterior <= 0:
    señal = "COMPRA"  # Cruce sobre cero
elif AO_actual < 0 AND AO_anterior >= 0:
    señal = "VENTA"   # Cruce bajo cero
```

#### ROC (Rate of Change)
```python
if ROC > 5:
    señal = "COMPRA"  # Momentum alcista fuerte
elif ROC < -5:
    señal = "VENTA"   # Momentum bajista fuerte
```

**Cálculo del Resumen**:
```python
compras = count(señales == "COMPRA")
ventas = count(señales == "VENTA")

if compras > ventas:
    resumen = "COMPRA"
elif ventas > compras:
    resumen = "VENTA"
else:
    resumen = "KEEP"
```

**Estructura del Resultado**:
```python
{
    "ticker": "AAPL",
    "fecha": "2025-01-15",
    "precio_cierre": 150.25,
    "señales": {
        "Cruce_Medias": "COMPRA",
        "RSI": "KEEP/NO SIGNAL",
        "Estocastico": "COMPRA",
        "MACD": "VENTA",
        ...
    },
    "resumen": "COMPRA"  # Mayoría
}
```

---

### 6. visualizer.py - Generación de Gráficos

**Función Principal**: `generar_grafico(datos, resultado, ticker, output_dir='salidas')`

**Estructura del Gráfico**:
```
┌──────────────────────────────────────────────────┐
│ Subplot 1 (60% altura): Candlestick + SMAs      │
│ - Velas japonesas (OHLC)                         │
│ - Línea azul: SMA 30                             │
│ - Línea naranja: SMA 60                          │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│ Subplot 2 (10% altura): Volumen                  │
│ - Barras de volumen                              │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│ Subplot 3 (15% altura): RSI                      │
│ - Línea morada: RSI                              │
│ - Línea roja punteada: 70 (sobrecompra)         │
│ - Línea verde punteada: 30 (sobreventa)         │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│ Subplot 4 (15% altura): Williams %R              │
│ - Línea teal: Williams %R                        │
│ - Línea roja punteada: -20 (sobrecompra)        │
│ - Línea verde punteada: -80 (sobreventa)        │
└──────────────────────────────────────────────────┘
```

**Creación del Gráfico**:
```python
1. Crear figura con make_subplots(rows=4, cols=1)
2. Configurar shared_xaxes=True (zoom sincronizado)
3. Configurar vertical_spacing=0.02
4. Configurar row_heights=[0.6, 0.1, 0.15, 0.15]

5. Agregar Candlestick (row=1):
   - x=fecha
   - open=apertura
   - high=maximo
   - low=minimo
   - close=cierre

6. Agregar SMAs (row=1):
   - SMA 30 (azul, width=1)
   - SMA 60 (naranja, width=1)

7. Agregar Volumen (row=2):
   - Barras con x=fecha, y=volumen

8. Agregar RSI (row=3):
   - Línea morada
   - Líneas horizontales en 70 y 30

9. Agregar Williams %R (row=4):
   - Línea teal
   - Líneas horizontales en -20 y -80

10. Configurar layout:
    - title=f"Análisis Técnico para {ticker}"
    - xaxis_rangeslider_visible=False
    - height=800px

11. Guardar HTML:
    - filepath = output_dir/{ticker}_analisis.html
    - fig.write_html(filepath)
```

---

### 7. parallel_processor.py - Procesamiento Paralelo

**Clase**: `ParallelProcessor`

**Atributos**:
- `max_workers`: int - Número de hilos paralelos
- `results`: List - Resultados exitosos
- `errors`: List - Errores encontrados
- `lock`: threading.Lock - Para acceso thread-safe a listas

**Método**: `process_tickers_parallel(tickers, process_function, *args, **kwargs)`

**Flujo**:
```python
1. Inicializar ThreadPoolExecutor con max_workers hilos
2. Para cada ticker:
   - Enviar tarea al pool: executor.submit(process_ticker, ticker, ...)
   - Crear diccionario future_to_ticker para tracking
3. Conforme se completan las tareas:
   - future.result() obtiene el resultado
   - Si exitoso: agregar a self.results
   - Si error: agregar a self.errors
4. Al finalizar:
   - Registrar estadísticas (exitosos, errores, tiempo total)
   - Retornar self.results
```

**Función**: `process_single_ticker(ticker, fecha_inicio, fecha_fin, output_dir)`

Esta función replica el flujo de `process_ticker_sequential` pero de forma standalone para uso en threads:
```python
1. Descargar datos
2. Guardar en DB
3. Calcular indicadores
4. Generar señales
5. Crear gráfico
6. Retornar diccionario con todos los resultados
```

---

### 8. config_manager.py - Gestión de Configuración

**Clase**: `ConfigManager`

**Patrón Singleton**: Solo existe una instancia global

**Archivo**: `config.json`

**Estructura del JSON**:
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
    "stoch_params": {"k": 14, "d": 3},
    "macd_params": {"fast": 12, "slow": 26, "signal": 9},
    "bollinger_params": {"length": 20, "std": 2},
    ...
  },
  "signals": {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    ...
  },
  "advanced_indicators": {
    "enabled": false,
    ...
  }
}
```

**Métodos**:
- `get(section, key=None, default=None)`: Obtiene valor de configuración
- `update(section, key, value)`: Actualiza configuración en memoria
- `save()`: Guarda configuración a archivo
- `get_indicator_params()`: Obtiene parámetros de indicadores
- `get_signal_thresholds()`: Obtiene umbrales de señales
- `get_data_config()`: Obtiene configuración de datos

---

### 9. logger_config.py - Sistema de Logging

**Clase**: `TradingLogger` (Singleton)

**Configuración**:
```python
Logger raíz: 'trading_platform'
Nivel: DEBUG

Handlers:
1. FileHandler → control.txt
   - Nivel: DEBUG
   - Formato: timestamp | nivel | módulo | función:línea | mensaje

2. StreamHandler → consola
   - Nivel: INFO
   - Formato: nivel: mensaje
```

**Uso**:
```python
from logger_config import get_logger

logger = get_logger(__name__)

logger.debug("Mensaje detallado")
logger.info("Mensaje informativo")
logger.warning("Advertencia")
logger.error("Error", exc_info=True)  # Incluye traceback
```

---

## Estructuras de Datos

### DataFrame de Datos Históricos

**Columnas**:
```
┌────────────┬──────────┬───────────┬────────┬──────────┬───────────┬─────────┐
│   fecha    │ apertura │  maximo   │ minimo │  cierre  │  volumen  │ ticker  │
├────────────┼──────────┼───────────┼────────┼──────────┼───────────┼─────────┤
│ 2024-01-15 │  150.20  │  152.50   │ 149.80 │  151.30  │ 50000000  │  AAPL   │
│ 2024-01-16 │  151.50  │  153.20   │ 150.90 │  152.80  │ 48000000  │  AAPL   │
│    ...     │   ...    │   ...     │  ...   │   ...    │    ...    │   ...   │
└────────────┴──────────┴───────────┴────────┴──────────┴───────────┴─────────┘

Tipos:
- fecha: datetime64
- apertura, maximo, minimo, cierre: float64
- volumen: int64
- ticker: object (string)
```

### DataFrame con Indicadores

**Columnas Adicionales** (además de las de datos históricos):
```
SMA_30, SMA_60, SMA_90
RSI
STOCHk_14_3_3, STOCHd_14_3_3
MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
BBL_20_2, BBM_20_2, BBU_20_2
CCI_20
ADX_14, DMP_14, DMN_14
MFI_14
WILLR_14
AO_5_34
ROC_12

+ Indicadores avanzados si enabled
```

### Diccionario de Resultado de Análisis

```python
{
    "ticker": str,              # "AAPL"
    "fecha": str,               # "2025-01-15"
    "precio_cierre": float,     # 150.25
    "señales": {                # Diccionario de señales
        "Cruce_Medias": str,           # "COMPRA" | "VENTA" | "KEEP/NO SIGNAL"
        "RSI": str,
        "Estocastico": str,
        "MACD": str,
        "Bandas_Bollinger": str,
        "Williams_R": str,
        "Awesome_Oscillator": str,
        "ROC": str,
        # + Señales avanzadas si enabled
    },
    "resumen": str              # "COMPRA" | "VENTA" | "KEEP"
}
```

---

## Configuración

### Archivo config.json

**Sección `data`**:
```json
{
  "analysis_period_days": 730  // Días de histórico a analizar
}
```

**Sección `processing`**:
```json
{
  "parallel_processing": false,  // true para paralelo, false para secuencial
  "max_workers": 4               // Número de hilos si parallel
}
```

**Sección `indicators`** - Parámetros de Indicadores Básicos:
```json
{
  "sma_periods": [30, 60, 90],   // Períodos de SMAs
  "rsi_period": 14,
  "stoch_params": {"k": 14, "d": 3},
  "macd_params": {"fast": 12, "slow": 26, "signal": 9},
  "bollinger_params": {"length": 20, "std": 2},
  "cci_period": 20,
  "adx_period": 14,
  "mfi_period": 14,
  "willr_period": 14,
  "ao_params": {"fast": 5, "slow": 34},
  "roc_period": 12
}
```

**Sección `signals`** - Umbrales de Señales Básicas:
```json
{
  "rsi_oversold": 30,      // RSI < 30 → COMPRA
  "rsi_overbought": 70,    // RSI > 70 → VENTA
  "stoch_oversold": 20,
  "stoch_overbought": 80,
  "willr_oversold": -80,
  "willr_overbought": -20,
  "roc_bullish": 5,
  "roc_bearish": -5
}
```

**Sección `advanced_indicators`** - Indicadores Avanzados:
```json
{
  "enabled": false,  // true para habilitar indicadores avanzados
  "stoch_rsi_rsi_period": 14,
  "stoch_rsi_stoch_period": 14,
  "tsi_long_period": 25,
  "tsi_short_period": 13,
  "uo_period1": 7,
  "uo_period2": 14,
  "uo_period3": 28,
  "chaikin_fast": 3,
  "chaikin_slow": 10,
  "aroon_period": 14,
  "trix_period": 14,
  "volume_rsi_period": 14,
  "dpo_period": 20
}
```

**Sección `advanced_signals`** - Umbrales de Señales Avanzadas:
```json
{
  "stoch_rsi_oversold": 20,
  "stoch_rsi_overbought": 80,
  "tsi_bullish": 5,
  "tsi_bearish": -5,
  "uo_oversold": 30,
  "uo_overbought": 70,
  "chaikin_bullish": 0,
  "aroon_osc_bullish": 50,
  "aroon_osc_bearish": -50,
  "trix_bullish": 0,
  "volume_rsi_oversold": 30,
  "volume_rsi_overbought": 70,
  "dpo_bullish": 0
}
```

---

## Archivos de Salida

### control.txt - Log de Ejecución

**Formato**:
```
2025-01-15 10:30:15 | INFO     | main | load_tickers:82 | Cargando tickers desde: D:\...\tickers.txt
2025-01-15 10:30:15 | INFO     | main | load_tickers:87 | Cargados 5 tickers: AAPL, GOOGL, MSFT, TSLA, AAL
2025-01-15 10:30:15 | INFO     | main | setup_date_range:108 | Rango de análisis configurado:
2025-01-15 10:30:15 | INFO     | main | setup_date_range:109 |   Fecha inicio: 2023-01-15
2025-01-15 10:30:15 | INFO     | main | setup_date_range:110 |   Fecha fin: 2025-01-15
...
```

**Contiene**:
- Timestamp de cada operación
- Nivel de log (DEBUG, INFO, WARNING, ERROR)
- Módulo y función que generó el log
- Número de línea
- Mensaje

### salida.txt - Tablas de Resultados

**Contenido**:
```
================================================================================
TABLA 1: RESUMEN GENERAL
================================================================================
+--------+-----------------+------------+---------------+----------------+
| Ticker | Empresa         | Fecha      | Precio Cierre | Recomendación  |
+========+=================+============+===============+================+
| AAPL   | Apple Inc.      | 2025-01-15 | 150.25        | COMPRA         |
| GOOGL  | Alphabet Inc.   | 2025-01-15 | 140.50        | VENTA          |
| ...    | ...             | ...        | ...           | ...            |
+--------+-----------------+------------+---------------+----------------+

================================================================================
TABLA 2: SEÑALES DE INDICADORES BÁSICOS
================================================================================
+--------+---------------+------+-------------+------+-------------------+...
| Ticker | Cruce_Medias  | RSI  | Estocastico | MACD | Bandas_Bollinger  |...
+========+===============+======+=============+======+===================+...
| AAPL   | COMPRA        | KEEP | COMPRA      | KEEP | KEEP/NO SIGNAL    |...
| ...    | ...           | ...  | ...         | ...  | ...               |...
+--------+---------------+------+-------------+------+-------------------+...

... (más tablas)
```

### Archivos CSV en salidas/

**Archivos Generados**:
- `open_data.csv` - Precios de apertura
- `high_data.csv` - Precios máximos
- `low_data.csv` - Precios mínimos
- `close_data.csv` - Precios de cierre
- `volume_data.csv` - Volúmenes

**Formato** (ejemplo close_data.csv):
```
;2025-01-01;2025-01-02;2025-01-03;...
AAPL;150,25;151,30;152,80;...
GOOGL;140,50;141,20;140,90;...
MSFT;380,75;382,10;383,50;...
```

**Características**:
- Delimitador: `;` (punto y coma)
- Decimal: `,` (coma)
- Formato compatible con Excel español
- Filas: Tickers
- Columnas: Fechas
- Valores: Precios o volúmenes

### Archivos HTML en salidas/

**Archivos Generados**:
- `{TICKER}_analisis.html` - Un archivo por cada ticker

**Contenido**:
- Gráfico interactivo Plotly
- 4 subplots (Candlestick, Volumen, RSI, Williams %R)
- Interactividad:
  - Zoom
  - Pan
  - Hover tooltips con valores exactos
  - Leyendas clickeables
  - Guardado de imagen

---

## Diagramas de Flujo

### Flujo de Procesamiento de un Ticker

```
┌─────────────────────┐
│  Ticker: AAPL       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  1. DESCARGA DE DATOS               │
│  ─────────────────────               │
│  • yfinance.download(AAPL, ...)     │
│  • Validaciones                     │
│  • Conversión de columnas           │
│  • Obtención nombre empresa         │
│  ────────────────────────────────   │
│  ✓ DataFrame con OHLCV              │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  2. ALMACENAMIENTO                  │
│  ──────────────                     │
│  • INSERT OR REPLACE INTO DB        │
│  • Evita duplicados (ticker, fecha) │
│  ────────────────────────────────   │
│  ✓ Datos persistidos                │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  3. CÁLCULO DE INDICADORES          │
│  ──────────────────────              │
│  • Conversión a inglés              │
│  • Cálculo con pandas_ta:           │
│    - SMA (30, 60, 90)               │
│    - RSI (14)                       │
│    - Estocástico (14, 3)            │
│    - MACD (12, 26, 9)               │
│    - Bollinger (20, 2)              │
│    - CCI (20)                       │
│    - ADX (14)                       │
│    - MFI (14)                       │
│    - Williams %R (14)               │
│    - AO (5, 34)                     │
│    - ROC (12)                       │
│  • Si advanced_enabled:             │
│    - 8 indicadores avanzados        │
│  • Conversión a español             │
│  • Limpieza de NaN                  │
│  ────────────────────────────────   │
│  ✓ DataFrame con ~30-40 columnas    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  4. GENERACIÓN DE SEÑALES           │
│  ─────────────────────               │
│  • Obtener últimas 2 filas          │
│  • Para cada indicador:             │
│    - Evaluar condiciones            │
│    - Generar señal:                 │
│      * COMPRA                       │
│      * VENTA                        │
│      * KEEP/NO SIGNAL               │
│  • Calcular resumen (mayoría)       │
│  ────────────────────────────────   │
│  ✓ Diccionario con señales          │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  5. VISUALIZACIÓN                   │
│  ─────────────                      │
│  • Crear figura Plotly              │
│  • 4 subplots:                      │
│    1. Candlestick + SMAs            │
│    2. Volumen                       │
│    3. RSI                           │
│    4. Williams %R                   │
│  • Guardar HTML interactivo         │
│  ────────────────────────────────   │
│  ✓ salidas/AAPL_analisis.html       │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  TICKER PROCESADO EXITOSAMENTE      │
└─────────────────────────────────────┘
```

### Flujo de Decisión: Modo Secuencial vs Paralelo

```
                  INICIO
                    │
                    ▼
        ┌───────────────────────┐
        │ ¿parallel_processing  │
        │   = true EN CONFIG?   │
        └───────────┬───────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
       NO                      SÍ
        │                       │
        │                       ▼
        │           ┌────────────────────┐
        │           │ ¿Hay más de 1      │
        │           │   ticker?          │
        │           └────────┬───────────┘
        │                    │
        │           ┌────────┴────────┐
        │           │                 │
        │          NO                SÍ
        │           │                 │
        ▼           ▼                 ▼
┌──────────────────────┐    ┌────────────────────┐
│  MODO SECUENCIAL     │    │  MODO PARALELO     │
│  ────────────────    │    │  ──────────────    │
│  • Procesa 1 a 1     │    │  • ThreadPool      │
│  • Orden garantizado │    │  • max_workers     │
│  • Más fácil debug   │    │  • Más rápido      │
└──────────────────────┘    └────────────────────┘
        │                            │
        └────────────┬───────────────┘
                     ▼
        ┌───────────────────────┐
        │  PROCESAMIENTO        │
        │  DE TODOS LOS TICKERS │
        └───────────────────────┘
```

---

## Guía de Mantenimiento

### Añadir un Nuevo Indicador Básico

**Paso 1**: Añadir en `constants.py`
```python
AVAILABLE_INDICATORS.append("Nuevo_Indicador")
INDICATOR_RESULT_COLUMNS.append("NUEVO_INDIC_VALOR")
```

**Paso 2**: Añadir en `config.json`
```json
{
  "indicators": {
    ...
    "nuevo_indicador_period": 20
  },
  "signals": {
    ...
    "nuevo_indicador_umbral": 50
  }
}
```

**Paso 3**: Calcular en `indicator_calculator.py`
```python
def calcular_indicadores(datos):
    ...
    params = config_manager.get_indicator_params()
    df_ta['NUEVO_INDIC'] = ta.nuevo_indicador(
        df_ta['close'],
        length=params.get('nuevo_indicador_period', 20)
    )
    ...
```

**Paso 4**: Generar señal en `signal_generator.py`
```python
def generar_senales(datos):
    ...
    senales["Nuevo_Indicador"] = _evaluar_condicion(
        ultimo_dato['NUEVO_INDIC'],
        thresholds.get('nuevo_indicador_umbral', 50)
    )
    ...
```

### Modificar Umbrales de Señales

**Editar** `config.json`:
```json
{
  "signals": {
    "rsi_oversold": 25,      // Cambiar de 30 a 25
    "rsi_overbought": 75,    // Cambiar de 70 a 75
    ...
  }
}
```

No es necesario modificar código, el sistema lee los valores del JSON.

### Cambiar Período de Análisis

**Opción 1 - Permanente**: Editar `config.json`
```json
{
  "data": {
    "analysis_period_days": 365  // Cambiar de 730 a 365 (1 año)
  }
}
```

**Opción 2 - Temporal**: Modificar llamada en código
```python
platform.setup_date_range(analysis_days=365)
```

### Activar/Desactivar Modo Paralelo

**Editar** `config.json`:
```json
{
  "processing": {
    "parallel_processing": true,   // false para secuencial
    "max_workers": 8               // Ajustar según CPU
  }
}
```

**Recomendaciones**:
- CPU con 4 cores → max_workers: 4
- CPU con 8 cores → max_workers: 6-8
- No exceder número de cores físicos

### Habilitar Indicadores Avanzados

**Editar** `config.json`:
```json
{
  "advanced_indicators": {
    "enabled": true  // Cambiar de false a true
  }
}
```

Esto añade:
- 8 indicadores adicionales
- Tabla 4: Señales Avanzadas
- Tabla 5: Valores Avanzados

**Advertencia**: Aumenta tiempo de procesamiento ~20-30%

### Solución de Problemas Comunes

#### Error: "No se encontró el archivo de tickers"
**Causa**: Archivo `tickers.txt` no existe o ruta incorrecta
**Solución**:
1. Verificar que `tickers.txt` está en la raíz del proyecto
2. Revisar permisos de lectura del archivo

#### Error: "Error al descargar datos para {ticker}"
**Causa**: Ticker inválido o problemas de conexión
**Solución**:
1. Verificar que el símbolo es correcto (ej: AAPL, no Apple)
2. Verificar conexión a internet
3. Verificar que Yahoo Finance está accesible
4. Revisar logs en `control.txt` para detalles

#### Error: "All values are NaN"
**Causa**: Datos descargados están vacíos o corruptos
**Solución**:
1. Verificar rango de fechas (no puede ser futuro)
2. Verificar que el ticker tiene datos en ese rango
3. Intentar con rango de fechas diferente

#### Tablas vacías en salida.txt
**Causa**: No se procesó ningún ticker exitosamente
**Solución**:
1. Revisar `control.txt` para ver errores
2. Verificar que `tickers.txt` tiene símbolos válidos
3. Verificar conexión a internet

#### Gráficos HTML no se generan
**Causa**: Error en visualizer o permisos de carpeta
**Solución**:
1. Verificar que carpeta `salidas/` tiene permisos de escritura
2. Revisar logs en `control.txt`
3. Verificar que plotly está instalado

---

## Apéndice

### Dependencias del Proyecto

```
yfinance==0.2.28          # Descarga de datos financieros
pandas==2.1.0             # Manipulación de datos
pandas_ta==0.3.14b        # Indicadores técnicos
plotly==5.17.0            # Visualización interactiva
tabulate==0.9.0           # Formateo de tablas
numpy==1.24.3             # Cálculos numéricos
```

### Estructura de Directorios

```
Trading_platform/
├── main.py                        # Orquestador principal
├── data_acquisition.py            # Descarga de datos
├── data_storage.py                # Base de datos
├── indicator_calculator.py        # Indicadores básicos
├── advanced_indicators.py         # Indicadores avanzados
├── signal_generator.py            # Señales básicas
├── advanced_signals.py            # Señales avanzadas
├── visualizer.py                  # Gráficos HTML
├── parallel_processor.py          # Procesamiento paralelo
├── csv_formatter.py               # Formateo CSV
├── config_manager.py              # Gestión configuración
├── logger_config.py               # Sistema de logging
├── constants.py                   # Constantes
├── utils.py                       # Utilidades
├── config.json                    # Archivo de configuración
├── tickers.txt                    # Lista de tickers a analizar
├── plataforma_trading.db          # Base de datos SQLite
├── control.txt                    # Log de ejecución (generado)
├── salida.txt                     # Tablas de resultados (generado)
├── DOCUMENTACION_TECNICA.md       # Este documento
└── salidas/                       # Carpeta de salidas (generada)
    ├── AAPL_analisis.html         # Gráfico interactivo por ticker
    ├── GOOGL_analisis.html
    ├── ...
    ├── open_data.csv              # CSV de precios de apertura
    ├── high_data.csv              # CSV de precios máximos
    ├── low_data.csv               # CSV de precios mínimos
    ├── close_data.csv             # CSV de precios de cierre
    └── volume_data.csv            # CSV de volúmenes
```

---

## Glosario de Términos

**Ticker**: Símbolo único que identifica un activo financiero (ej: AAPL = Apple)

**OHLCV**: Open, High, Low, Close, Volume - Datos básicos de precio y volumen

**SMA**: Simple Moving Average - Media móvil simple

**RSI**: Relative Strength Index - Índice de fuerza relativa

**MACD**: Moving Average Convergence Divergence

**Estocástico**: Oscilador que compara precio de cierre con rango de precios

**Bandas de Bollinger**: Bandas de volatilidad basadas en desviación estándar

**Williams %R**: Oscilador de momentum

**Señal COMPRA**: Indicador sugiere comprar el activo

**Señal VENTA**: Indicador sugiere vender el activo

**Señal KEEP/NO SIGNAL**: No hay señal clara, mantener posición

**Sobreventa**: Condición donde el precio ha bajado demasiado y podría rebotar

**Sobrecompra**: Condición donde el precio ha subido demasiado y podría corregir

**Candlestick**: Gráfico de velas japonesas que muestra OHLC

**Thread Pool**: Conjunto de hilos para procesamiento paralelo

**Singleton**: Patrón de diseño donde solo existe una instancia de una clase

---

**Fin de la Documentación Técnica**

Para más información o soporte, consulte los comentarios en el código fuente o revise los logs en `control.txt`.
