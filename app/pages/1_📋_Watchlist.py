"""Página de gestión de Watchlist — selección de mercado y acciones."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Watchlist", page_icon="📋", layout="wide")

from components.theme import apply_theme, export_csv_es
from trading_platform.storage.watchlist_manager import (
    list_watchlists,
    load_watchlist,
    save_watchlist,
    delete_watchlist,
)

apply_theme()

MARKETS_DIR = Path(__file__).parent.parent.parent / "data" / "markets"

MARKET_FILES = {
    "IBEX 35": "ibex35.csv",
    "S&P 500 (muestra)": "sp500_sample.csv",
    "NASDAQ 100": "nasdaq100.csv",
    "DAX 40": "dax40.csv",
    "CAC 40": "cac40.csv",
    "EuroStoxx 50": "eurostoxx50.csv",
    "FTSE 100": "ftse100.csv",
    "Nikkei 225 (muestra)": "nikkei225_sample.csv",
}

# ── Inicializar estado ────────────────────────────────────────
if "watchlist" not in st.session_state:
    records = load_watchlist("default.csv")
    st.session_state["watchlist"] = records or []


def _load_market(filename: str) -> pd.DataFrame:
    path = MARKETS_DIR / filename
    if not path.exists():
        return pd.DataFrame(columns=["ticker", "name", "sector"])
    return pd.read_csv(path)


# ── Título + barra de watchlists guardadas ────────────────────
st.title("📋 Watchlist")
st.caption("Selecciona un mercado, elige acciones y añádelas a tu watchlist.")

# Panel lateral: gestión de watchlists guardadas
with st.sidebar:
    st.subheader("Mis watchlists")
    saved = list_watchlists()

    if saved:
        for wl in saved:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                label = f"**{wl['display_name']}** ({wl['tickers']} tickers)"
                if st.button(label, key=f"load_{wl['filename']}", use_container_width=True):
                    records = load_watchlist(wl["filename"])
                    if records is not None:
                        st.session_state["watchlist"] = records
                        st.session_state["_loaded_wl"] = wl["display_name"]
                        st.rerun()
            with col_b:
                if st.button("🗑", key=f"del_{wl['filename']}", help="Eliminar esta watchlist"):
                    delete_watchlist(wl["filename"])
                    st.rerun()
    else:
        st.caption("No hay watchlists guardadas todavía.")

    if "_loaded_wl" in st.session_state:
        st.success(f"Cargada: {st.session_state.pop('_loaded_wl')}")

# ── Columnas principales ──────────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("Mercado")
    market_label = st.selectbox("Mercado", list(MARKET_FILES.keys()))
    df_market = _load_market(MARKET_FILES[market_label])

    if df_market.empty:
        st.warning("Archivo de mercado no encontrado.")
    else:
        sectors = ["Todos"] + sorted(df_market["sector"].unique().tolist())
        sector_filter = st.selectbox("Filtrar por sector", sectors)

        df_filtered = df_market if sector_filter == "Todos" else df_market[df_market["sector"] == sector_filter]

        display = df_filtered[["ticker", "name", "sector"]].copy()
        display.insert(0, "✓", False)

        st.markdown("**Acciones disponibles** — marca las que quieres añadir:")
        edited = st.data_editor(
            display.reset_index(drop=True),
            column_config={
                "✓": st.column_config.CheckboxColumn("Añadir", default=False),
                "ticker": st.column_config.TextColumn("Ticker", disabled=True),
                "name": st.column_config.TextColumn("Empresa", disabled=True),
                "sector": st.column_config.TextColumn("Sector", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            height=400,
        )

        if st.button("➕ Añadir selección a Watchlist", type="primary"):
            selected = edited[edited["✓"] == True]
            existing_tickers = {r["ticker"] for r in st.session_state["watchlist"]}
            added = 0
            for _, row in selected.iterrows():
                if row["ticker"] not in existing_tickers:
                    st.session_state["watchlist"].append({
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "sector": row["sector"],
                    })
                    added += 1
            if added:
                st.success(f"{added} acciones añadidas.")
            else:
                st.info("Todas las acciones seleccionadas ya estaban en la watchlist.")

        st.markdown("---")
        st.caption("¿Tu ticker no está en la lista? Añádelo manualmente:")
        manual_col1, manual_col2 = st.columns([1, 2])
        with manual_col1:
            manual_ticker = st.text_input("Ticker", placeholder="AAPL")
        with manual_col2:
            manual_name = st.text_input("Nombre", placeholder="Apple Inc.")
        if st.button("Añadir manualmente"):
            if manual_ticker:
                t = manual_ticker.upper().strip()
                existing = {r["ticker"] for r in st.session_state["watchlist"]}
                if t not in existing:
                    st.session_state["watchlist"].append({"ticker": t, "name": manual_name or t, "sector": "—"})
                    st.success(f"{t} añadido.")
                else:
                    st.info(f"{t} ya está en la watchlist.")

with col_right:
    st.subheader(f"Mi Watchlist ({len(st.session_state['watchlist'])} tickers)")

    if not st.session_state["watchlist"]:
        st.info("Tu watchlist está vacía. Selecciona acciones del panel izquierdo.")
    else:
        df_watch = pd.DataFrame(st.session_state["watchlist"])
        df_watch.insert(0, "🗑", False)

        edited_watch = st.data_editor(
            df_watch,
            column_config={
                "🗑": st.column_config.CheckboxColumn("Eliminar", default=False),
                "ticker": "Ticker",
                "name": "Empresa",
                "sector": "Sector",
            },
            hide_index=True,
            use_container_width=True,
            height=350,
        )

        # ── Botones de acción ─────────────────────────────────
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("🗑 Eliminar selección"):
                to_remove = edited_watch[edited_watch["🗑"] == True]["ticker"].tolist()
                st.session_state["watchlist"] = [
                    r for r in st.session_state["watchlist"] if r["ticker"] not in to_remove
                ]
                st.rerun()
        with btn_col2:
            if st.button("🧹 Vaciar"):
                st.session_state["watchlist"] = []
                st.rerun()
        with btn_col3:
            csv_bytes = export_csv_es(df_watch.drop(columns=["🗑"]))
            st.download_button(
                "⬇ Exportar CSV",
                data=csv_bytes,
                file_name="watchlist.csv",
                mime="text/csv",
                help="Formato europeo (';' separador, ',' decimal)",
            )

        # ── Guardar con nombre ────────────────────────────────
        st.markdown("---")
        st.markdown("**Guardar watchlist**")
        save_col1, save_col2 = st.columns([2, 1])
        with save_col1:
            wl_name = st.text_input(
                "Nombre de la watchlist",
                value="default",
                label_visibility="collapsed",
                placeholder="Ej: IBEX favoritas",
                key="wl_save_name",
            )
        with save_col2:
            if st.button("💾 Guardar", type="primary", use_container_width=True):
                if st.session_state["watchlist"]:
                    save_watchlist(st.session_state["watchlist"], wl_name or "default")
                    st.success(f"Watchlist '{wl_name}' guardada.")
                    st.rerun()
                else:
                    st.warning("La watchlist está vacía.")

    st.markdown("---")
    n = len(st.session_state.get("watchlist", []))
    if n > 0:
        st.info(f"**{n} tickers** listos para análisis.\n\nVe a **📈 Análisis** y pulsa **[RUN]**.")
