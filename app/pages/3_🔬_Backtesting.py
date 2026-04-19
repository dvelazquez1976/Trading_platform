"""Página de backtesting — evaluación histórica de estrategias."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Backtesting", page_icon="🔬", layout="wide")

from components.theme import apply_theme, export_csv_es
from trading_platform.providers import descargar_datos

apply_theme()
from trading_platform.indicators.basic import calcular_indicadores
from trading_platform.backtesting.engine import BacktestingEngine
from trading_platform.backtesting.costs import TransactionCosts


st.title("🔬 Backtesting")
st.caption("Evalúa el rendimiento histórico de estrategias sobre un ticker.")

with st.sidebar:
    st.subheader("Parámetros")
    ticker_input = st.text_input("Ticker", value="SAN.MC")
    days = st.slider("Días de histórico", 180, 1825, 730, 30)
    strategy = st.selectbox(
        "Estrategia",
        ["sma_crossover", "rsi_oversold", "macd_signal", "bollinger_reversion"],
        format_func=lambda s: {
            "sma_crossover": "Cruce de medias (SMA 30/90)",
            "rsi_oversold": "RSI sobrevendido (<30)",
            "macd_signal": "Cruce MACD/Señal",
            "bollinger_reversion": "Reversión a Bollinger",
        }.get(s, s),
    )
    st.markdown("---")
    st.subheader("Costes de transacción")
    commission = st.number_input("Comisión (%)", value=0.2, step=0.05, format="%.2f") / 100
    slippage = st.number_input("Slippage (bps)", value=5, step=1)
    min_comm = st.number_input("Comisión mínima (€)", value=1.0, step=0.5)

    run_bt = st.button("▶ Ejecutar Backtest", type="primary", use_container_width=True)

if run_bt:
    with st.spinner(f"Descargando datos de {ticker_input}…"):
        import datetime
        fecha_fin = datetime.date.today() + datetime.timedelta(days=1)
        fecha_inicio = fecha_fin - datetime.timedelta(days=days)
        datos, company_name = descargar_datos(
            ticker_input,
            fecha_inicio.strftime("%Y-%m-%d"),
            fecha_fin.strftime("%Y-%m-%d"),
        )

    if datos is None:
        st.error(f"No se pudieron obtener datos para {ticker_input}.")
        st.stop()

    with st.spinner("Calculando indicadores y ejecutando backtest…"):
        df = calcular_indicadores(datos.copy())
        df.dropna(inplace=True)

        costs = TransactionCosts(
            commission_pct=commission,
            min_commission=min_comm,
            slippage_bps=float(slippage),
        )
        engine = BacktestingEngine(strategy=strategy, transaction_costs=costs)
        result = engine.run_on_df(df)

    if result is None:
        st.error("El backtest no generó resultados. Revisa los datos.")
        st.stop()

    st.session_state["bt_result"] = result
    st.session_state["bt_df"] = df
    st.session_state["bt_ticker"] = ticker_input
    st.session_state["bt_company"] = company_name

if "bt_result" in st.session_state:
    result = st.session_state["bt_result"]
    df = st.session_state["bt_df"]
    ticker_label = st.session_state.get("bt_ticker", "")
    company_label = st.session_state.get("bt_company", "")

    metrics = result.get("metrics", {})
    trades = result.get("trades", [])
    equity = result.get("equity_curve", [])

    st.markdown(f"### {ticker_label} — {company_label}")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Retorno total", f"{metrics.get('total_return', 0)*100:.1f}%")
    m2.metric("CAGR", f"{metrics.get('cagr', 0)*100:.1f}%")
    m3.metric("Sharpe", f"{metrics.get('sharpe', 0):.2f}")
    m4.metric("Sortino", f"{metrics.get('sortino', 0):.2f}")
    m5.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0)*100:.1f}%")
    m6.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.1f}%")

    st.markdown("---")

    import json as _json
    _cfg_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    try:
        _theme = _json.loads(_cfg_path.read_text(encoding="utf-8")).get("ui", {}).get("theme", "light")
    except Exception:
        _theme = "light"
    plotly_template = "plotly_dark" if _theme == "dark" else "plotly_white"

    if equity:
        fig = go.Figure()
        eq_df = pd.DataFrame(equity)
        fig.add_trace(go.Scatter(
            x=eq_df["date"], y=eq_df["equity"],
            mode="lines", name="Equity",
            line=dict(color="#3b82f6", width=2),
            fill="tozeroy", fillcolor="rgba(59,130,246,.1)"
        ))
        fig.update_layout(
            title="Curva de capital",
            xaxis_title="Fecha", yaxis_title="Capital (€)",
            template=plotly_template, height=350,
            margin=dict(t=50, b=30, l=50, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    if trades:
        st.subheader(f"Operaciones ({len(trades)} totales)")
        df_trades = pd.DataFrame(trades)
        if "return_pct" in df_trades.columns:
            df_trades["retorno_%"] = df_trades["return_pct"] * 100
        tc1, tc2 = st.columns([1, 5])
        with tc1:
            st.download_button(
                "⬇ Exportar CSV",
                data=export_csv_es(df_trades),
                file_name=f"trades_{ticker_label}.csv",
                mime="text/csv",
                help="Formato europeo (';' separador, ',' decimal)",
            )
        st.dataframe(df_trades, use_container_width=True, height=300)
    else:
        st.info("La estrategia no generó operaciones en el período seleccionado.")
