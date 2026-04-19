"""Punto de entrada Streamlit — Trading Platform."""

import streamlit as st

st.set_page_config(
    page_title="Trading Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Trading Platform")
st.markdown(
    """
    Bienvenido a tu plataforma de análisis técnico personal.

    **Flujo recomendado:**
    1. **📋 Watchlist** — selecciona mercado y acciones
    2. **📈 Análisis** — ejecuta el análisis técnico
    3. **🔬 Backtesting** — evalúa estrategias históricas
    4. **⚙️ Configuración** — ajusta parámetros
    """
)

st.info("Usa el menú lateral para navegar entre secciones.")

with st.sidebar:
    st.markdown("---")
    st.caption("v2.0.0 · Solo fines informativos")
