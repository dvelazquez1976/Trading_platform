"""Página de análisis técnico — ejecuta el pipeline sobre la watchlist."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Análisis", page_icon="📈", layout="wide")

import json as _json

from components.theme import apply_theme, sparkline, export_csv_es
from trading_platform.pipeline.runner import TradingPlatform
from trading_platform.core.constants import REPORTS_DIR
from trading_platform.alerts.telegram import from_config as _telegram_from_config

apply_theme()


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
        h_col, spark_col, p_col = st.columns([3, 2, 1])
        with h_col:
            st.markdown(f"### {icon} {ticker} — :{color}[{resumen}]")
            st.caption(item.get("company_name", ""))
        with spark_col:
            # Sparkline: últimos 30 sesiones de precio cierre
            if "cierre" in df.columns and len(df) >= 5:
                serie = df["cierre"].dropna().tail(30)
                spark_color = "#16a34a" if resumen == "COMPRA" else ("#dc2626" if resumen == "VENTA" else "#64748b")
                st.plotly_chart(
                    sparkline(serie, color=spark_color),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"spark_{ticker}",
                )
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


def _results_to_df(results: list) -> pd.DataFrame:
    """Tabla resumen de resultados para exportar."""
    rows = []
    for item in results:
        res = item["resultado_analisis"]
        df = item["datos_con_indicadores"]
        last = df.iloc[-1] if not df.empty else {}
        rows.append({
            "Ticker": res.get("ticker", ""),
            "Empresa": item.get("company_name", ""),
            "Señal": res.get("resumen", "N/A"),
            "Precio cierre": res.get("precio_cierre", 0),
            "RSI": round(float(last.get("RSI", 0) or 0), 2),
            "Williams %R": round(float(last.get("WILLR", 0) or 0), 2),
            "MACD": round(float(last.get("MACD", 0) or 0), 4),
        })
    return pd.DataFrame(rows)


# ── Título ───────────────────────────────────────────────────
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
    with st.spinner(f"Analizando {len(tickers)} tickers…"):
        platform = TradingPlatform()
        results = platform.run_tickers(tickers, analysis_days=days)
        st.session_state["last_results"] = results

    # ── Alertas Telegram (si configuradas y habilitadas) ──────
    _cfg_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    try:
        _app_cfg = _json.loads(_cfg_path.read_text(encoding="utf-8"))
    except Exception:
        _app_cfg = {}
    if _app_cfg.get("alerts", {}).get("enabled", False):
        _alerter = _telegram_from_config(_app_cfg)
        if _alerter:
            _mode = _app_cfg["alerts"].get("mode", "both")
            _sent = _alerter.alert_signals(results, min_signal=_mode)
            if _sent:
                st.toast("Alerta Telegram enviada.", icon="🔔")
            else:
                st.toast("Alerta configurada pero no se pudo enviar.", icon="⚠️")

if "last_results" in st.session_state and st.session_state["last_results"]:
    results = st.session_state["last_results"]

    buys  = [r for r in results if r["resultado_analisis"].get("resumen") == "COMPRA"]
    sells = [r for r in results if r["resultado_analisis"].get("resumen") == "VENTA"]
    holds = [r for r in results if r["resultado_analisis"].get("resumen") not in ("COMPRA", "VENTA")]

    # ── KPIs ─────────────────────────────────────────────────
    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Tickers analizados", len(results))
    kc2.metric("📈 Compra", len(buys))
    kc3.metric("📉 Venta", len(sells))
    kc4.metric("━ Neutral", len(holds))

    # ── Filtros ───────────────────────────────────────────────
    st.markdown("---")
    f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
    with f_col1:
        filter_signals = st.multiselect(
            "Filtrar por señal",
            ["COMPRA", "VENTA", "NEUTRAL"],
            default=["COMPRA", "VENTA", "NEUTRAL"],
            key="filter_signals",
        )
    with f_col2:
        search_ticker = st.text_input("Buscar ticker / empresa", placeholder="AAPL, Apple…", key="search_ticker")
    with f_col3:
        sort_by = st.selectbox("Ordenar por", ["Señal", "Ticker", "RSI", "Volatilidad"], key="sort_by")

    def _matches(item: dict) -> bool:
        res = item["resultado_analisis"]
        sig = res.get("resumen", "NEUTRAL")
        sig_norm = sig if sig in ("COMPRA", "VENTA") else "NEUTRAL"
        if sig_norm not in filter_signals:
            return False
        if search_ticker:
            q = search_ticker.lower()
            if q not in res.get("ticker", "").lower() and q not in item.get("company_name", "").lower():
                return False
        return True

    filtered = [r for r in results if _matches(r)]

    if sort_by == "Ticker":
        filtered.sort(key=lambda r: r["resultado_analisis"].get("ticker", ""))
    elif sort_by == "RSI":
        filtered.sort(key=lambda r: float(r["datos_con_indicadores"].iloc[-1].get("RSI", 0) or 0))
    elif sort_by == "Volatilidad":
        filtered.sort(
            key=lambda r: r["datos_con_indicadores"]["cierre"].pct_change().std(),
            reverse=True,
        )
    else:  # Señal
        _order = {"COMPRA": 0, "VENTA": 1}
        filtered.sort(key=lambda r: _order.get(r["resultado_analisis"].get("resumen", ""), 2))

    st.caption(f"Mostrando **{len(filtered)}** de {len(results)} resultados")

    # ── Export CSV ────────────────────────────────────────────
    summary_df = _results_to_df(filtered)
    exp_col1, exp_col2 = st.columns([1, 5])
    with exp_col1:
        st.download_button(
            "⬇ Exportar CSV",
            data=export_csv_es(summary_df),
            file_name="analisis_resultados.csv",
            mime="text/csv",
            help="Formato europeo: separador ';', decimal ','",
        )

    dash_file = REPORTS_DIR / "dashboard_consolidado.html"
    if dash_file.exists():
        with open(dash_file, "r", encoding="utf-8") as f:
            dash_html = f.read()
        with exp_col2:
            st.download_button(
                "⬇ Descargar Dashboard consolidado",
                data=dash_html,
                file_name="dashboard_consolidado.html",
                mime="text/html",
            )

    # ── Resultados por pestaña ────────────────────────────────
    st.markdown("---")
    f_buys  = [r for r in filtered if r["resultado_analisis"].get("resumen") == "COMPRA"]
    f_sells = [r for r in filtered if r["resultado_analisis"].get("resumen") == "VENTA"]
    f_holds = [r for r in filtered if r["resultado_analisis"].get("resumen") not in ("COMPRA", "VENTA")]

    tab_buy, tab_sell, tab_hold, tab_tabla = st.tabs([
        f"📈 Compra ({len(f_buys)})",
        f"📉 Venta ({len(f_sells)})",
        f"━ Neutral ({len(f_holds)})",
        "📋 Tabla resumen",
    ])

    with tab_buy:
        if f_buys:
            for item in f_buys:
                _render_result_card(item)
        else:
            st.info("Ninguna señal de compra en los resultados filtrados.")

    with tab_sell:
        if f_sells:
            for item in f_sells:
                _render_result_card(item)
        else:
            st.info("Ninguna señal de venta en los resultados filtrados.")

    with tab_hold:
        if f_holds:
            for item in f_holds:
                _render_result_card(item)
        else:
            st.info("Ninguna señal neutral.")

    with tab_tabla:
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
