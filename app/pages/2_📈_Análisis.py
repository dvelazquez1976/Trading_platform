"""Página de análisis técnico — ejecuta el pipeline sobre la watchlist."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import streamlit as st

st.set_page_config(page_title="Análisis", page_icon="📈", layout="wide")

from trading_platform.pipeline.runner import TradingPlatform
from trading_platform.core.constants import REPORTS_DIR


def _render_result_card(item: dict):
    res = item["resultado_analisis"]
    ticker = res["ticker"]
    resumen = res.get("resumen", "N/A")
    precio = res.get("precio_cierre", 0)
    signals = res.get("señales", {})
    df = item["datos_con_indicadores"]

    color = {"COMPRA": "green", "VENTA": "red"}.get(resumen, "gray")
    icon = {"COMPRA": "📈", "VENTA": "📉"}.get(resumen, "━")

    with st.container(border=True):
        h_col, p_col = st.columns([3, 1])
        with h_col:
            st.markdown(f"### {icon} {ticker} — :{color}[{resumen}]")
            st.caption(item.get("company_name", ""))
        with p_col:
            st.metric("Precio cierre", f"${precio:.2f}")

        last = df.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("RSI", f"{last.get('RSI', 0):.1f}")
        m2.metric("Williams %R", f"{last.get('WILLR', 0):.1f}")
        m3.metric("MACD", f"{last.get('MACD', 0):.4f}")
        vol = df["cierre"].pct_change().std() * 100
        m4.metric("Volatilidad", f"{vol:.2f}%")

        with st.expander("Ver señales de indicadores"):
            for ind, sig in signals.items():
                sc = {"COMPRA": "🟢", "VENTA": "🔴"}.get(sig, "⚪")
                st.write(f"{sc} **{ind.replace('_',' ')}** → {sig}")

        report_file = REPORTS_DIR / f"{ticker}_analisis.html"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.download_button(
                f"⬇ Descargar informe {ticker}",
                data=html_content,
                file_name=f"{ticker}_analisis.html",
                mime="text/html",
                key=f"dl_{ticker}",
            )


st.title("📈 Análisis Técnico")

watchlist = st.session_state.get("watchlist", [])
tickers = [r["ticker"] for r in watchlist]

if not tickers:
    st.warning("Tu watchlist está vacía. Ve a **📋 Watchlist** y añade acciones primero.")
    st.stop()

st.info(f"Watchlist: **{', '.join(tickers)}**")

with st.sidebar:
    st.subheader("Parámetros")
    days = st.slider("Días de histórico", min_value=90, max_value=1825, value=730, step=30)
    parallel = st.checkbox("Procesamiento paralelo", value=False)

run_col, _ = st.columns([1, 4])
with run_col:
    run_clicked = st.button("▶ RUN", type="primary", use_container_width=True)

if run_clicked:
    results_placeholder = st.empty()
    with st.spinner(f"Analizando {len(tickers)} tickers…"):
        platform = TradingPlatform()
        results = platform.run_tickers(tickers, analysis_days=days)
        st.session_state["last_results"] = results

if "last_results" in st.session_state and st.session_state["last_results"]:
    results = st.session_state["last_results"]

    buys  = [r for r in results if r["resultado_analisis"].get("resumen") == "COMPRA"]
    sells = [r for r in results if r["resultado_analisis"].get("resumen") == "VENTA"]
    holds = [r for r in results if r["resultado_analisis"].get("resumen") not in ("COMPRA", "VENTA")]

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Tickers analizados", len(results))
    kc2.metric("📈 Compra", len(buys))
    kc3.metric("📉 Venta", len(sells))
    kc4.metric("━ Neutral", len(holds))

    dash_file = REPORTS_DIR / "dashboard_consolidado.html"
    if dash_file.exists():
        with open(dash_file, "r", encoding="utf-8") as f:
            dash_html = f.read()
        st.download_button(
            "⬇ Descargar Dashboard consolidado",
            data=dash_html,
            file_name="dashboard_consolidado.html",
            mime="text/html",
        )

    st.markdown("---")
    tab_buy, tab_sell, tab_hold = st.tabs([
        f"📈 Compra ({len(buys)})",
        f"📉 Venta ({len(sells)})",
        f"━ Neutral ({len(holds)})",
    ])

    with tab_buy:
        if buys:
            for item in buys:
                _render_result_card(item)
        else:
            st.info("Ninguna señal de compra en esta ejecución.")

    with tab_sell:
        if sells:
            for item in sells:
                _render_result_card(item)
        else:
            st.info("Ninguna señal de venta en esta ejecución.")

    with tab_hold:
        if holds:
            for item in holds:
                _render_result_card(item)
        else:
            st.info("Ninguna señal neutral.")
