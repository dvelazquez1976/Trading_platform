"""Página de configuración — ajuste de parámetros de la plataforma."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import streamlit as st

st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")

CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    st.success("Configuración guardada.")


st.title("⚙️ Configuración")
cfg = _load_config()

tab_data, tab_proc, tab_prov, tab_ui = st.tabs(["Datos", "Procesamiento", "Proveedores", "Interfaz"])

with tab_data:
    st.subheader("Datos históricos")
    data_cfg = cfg.get("data", {})
    analysis_days = st.slider("Período de análisis (días)", 90, 1825, data_cfg.get("analysis_period_days", 730), 30)
    cache_enabled = st.checkbox("Caché habilitado", data_cfg.get("cache_enabled", True))
    cache_ttl = st.number_input("TTL de caché (horas)", 1, 48, data_cfg.get("cache_ttl_hours", 4))

    cfg.setdefault("data", {})
    cfg["data"]["analysis_period_days"] = analysis_days
    cfg["data"]["cache_enabled"] = cache_enabled
    cfg["data"]["cache_ttl_hours"] = int(cache_ttl)

with tab_proc:
    st.subheader("Procesamiento")
    proc_cfg = cfg.get("processing", {})
    parallel = st.checkbox("Procesamiento paralelo", proc_cfg.get("parallel_processing", False))
    workers = st.slider("Workers máximos", 1, 16, proc_cfg.get("max_workers", 4))

    cfg.setdefault("processing", {})
    cfg["processing"]["parallel_processing"] = parallel
    cfg["processing"]["max_workers"] = workers

    st.subheader("Indicadores avanzados")
    ind_cfg = cfg.get("indicators", {})
    adv_enabled = st.checkbox("Habilitar indicadores avanzados", ind_cfg.get("advanced_enabled", False))
    cfg.setdefault("indicators", {})
    cfg["indicators"]["advanced_enabled"] = adv_enabled

with tab_prov:
    st.subheader("Proveedores de datos")
    prov_cfg = cfg.get("providers", {})

    st.info(
        "**Stooq** (primario) — gratuito, sin API key, buena cobertura europea.\n\n"
        "**yfinance** (fallback) — gratuito, amplia cobertura global.\n\n"
        "Proveedores de pago (Alpha Vantage, Polygon, etc.) se pueden añadir en el futuro sin modificar el código."
    )

    primary = st.selectbox("Proveedor primario", ["stooq", "yfinance"],
                            index=["stooq", "yfinance"].index(prov_cfg.get("primary", "stooq")))
    cfg.setdefault("providers", {})
    cfg["providers"]["primary"] = primary

    st.markdown("---")
    st.subheader("API Keys (proveedores de pago)")
    st.caption("Las claves se guardan en config.json. Para mayor seguridad usa variables de entorno (.env).")

    api_keys = prov_cfg.get("api_keys", {})
    av_key = st.text_input("Alpha Vantage API Key", value=api_keys.get("alpha_vantage", ""),
                            type="password", placeholder="Tu clave aquí")
    if av_key:
        cfg["providers"]["api_keys"]["alpha_vantage"] = av_key

with tab_ui:
    st.subheader("Interfaz")
    ui_cfg = cfg.get("ui", {})

    theme = st.selectbox("Tema de gráficos", ["light", "dark"],
                          index=["light", "dark"].index(ui_cfg.get("theme", "light")))
    chart_months = st.slider("Meses de histórico en gráficos", 3, 60, ui_cfg.get("chart_months", 24))

    default_market = st.selectbox(
        "Mercado por defecto",
        ["ibex35", "sp500_sample", "nasdaq100", "dax40", "cac40", "eurostoxx50", "ftse100", "nikkei225_sample"],
        index=0 if ui_cfg.get("default_market", "ibex35") not in
              ["ibex35", "sp500_sample", "nasdaq100", "dax40", "cac40", "eurostoxx50", "ftse100", "nikkei225_sample"]
        else ["ibex35", "sp500_sample", "nasdaq100", "dax40", "cac40", "eurostoxx50", "ftse100", "nikkei225_sample"]
              .index(ui_cfg.get("default_market", "ibex35"))
    )

    cfg.setdefault("ui", {})
    cfg["ui"]["theme"] = theme
    cfg["ui"]["chart_months"] = chart_months
    cfg["ui"]["default_market"] = default_market

st.markdown("---")
if st.button("💾 Guardar configuración", type="primary"):
    _save_config(cfg)

with st.expander("Ver configuración actual (JSON)"):
    st.json(cfg)
