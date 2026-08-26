"""Página de Simulador — backtest walk-forward vs línea base aleatoria."""

import streamlit as st
import numpy as np
from scipy.stats import hypergeom

from core.simulator import walk_forward_simulate, simulate_since
from core.models import DrawHistory
from core.ingest import ingest_file


st.set_page_config(page_title="SuperKino — Simulador", page_icon:"🧪")
st.sidebar.title("⚙️ Configuración del simulador")

# ── Cargar historial ──────────────────────────────────────────────────
if "history" not in st.session_state or st.session_state.get("history_page") != "simulador":
    st.session_state.history = None
    st.session_state.sim_window = 100
    st.session_state.sim_n_combos = 25
    st.session_state.sim_temperature = 1.0

st.sidebar.markdown("### Datos base")
upd = st.sidebar.file_uploader("SuperKinoTV.txt", type="txt", key="simulador_upload")
if upd is not None:
    text = upd.getvalue().decode("utf-8")
    lines = text.splitlines()
    from core.ingest import ingest_file as ingest_h
    st.session_state.history, _ = ingest_h(lines)
    st.session_state.sim_window = 100
    st.sidebar.success(f"{st.session_state.history.count} sorteos cargados")

window = st.sidebar.slider("Ventana W (sorteos previos)", 10, 300, 100, key="sim_window")
n_combos = st.sidebar.number_input("Combinaciones por sorteo (1-100)", 1, 100, 25, key="sim_n_combos")
temperature = st.sidebar.slider("Temperatura", 0.1, 3.0, 1.0, 0.1, key="sim_temperature")
rng_seed = st.sidebar.number_input("Semilla (opcional)", value=0, step=1, key="sim_seed")

if st.session_state.history is not None:
    st.title("🧪 SuperKino — Simulador Walk-Forward")

    if st.button("Ejecutar simulación", type="primary"):
        with st.spinner("Ejecutando backtest walk-forward..."):
            result = walk_forward_simulate(
                st.session_state.history,
                window=window,
                n_combinations=n_combos,
                temperature=temperature,
                rng_seed=int(rng_seed) if rng_seed else None,
            )

        if "mensaje" in result:
            st.info(result["mensaje"])
        else:
            st.success("Simulación completada")

            # Métricas clave alineadas
            c1, c2, c3 = st.columns(3)
            c1.metric("% Sorteos ≥5 aciertos (usuario)", f"{result['porcentaje_hit5']}%")
            c2.metric("% Sorteos ≥7 aciertos (usuario)", f"{result['porcentaje_hit7']}%")
            c3.metric("% Sorteos 10 aciertos (usuario)", f"{result['porcentaje_hit10']}%")

            c1, c2, c3 = st.columns(3)
            c1.metric("% Sorteos ≥5 aciertos (azar)", f"{result['linea_base_hit5']}%")
            c2.metric("% Sorteos ≥7 aciertos (azar)", f"{result['linea_base_hit7']}%")

            st.subheader("Tabla hipergeométrica (referencia teórica)")
            for k, v in result["tabla_hipergeometrica"].items():
                st.write(f"P({k} aciertos) = {v:.4f}")

            st.subheader("Distribución de mejores aciertos")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"≥5 aciertos: {result['distribucion_mayor_5']} de {result['total_sorteos_analizados']} sorteos")
            with col2:
                st.write(f"≥7 aciertos: {result['distribucion_mayor_7']} de {result['total_sorteos_analizados']} sorteos")

            st.write(f"Exacto 10 aciertos: {result['distribucion_10']} de {result['total_sorteos_analizados']} sorteos")

            st.write("**Línea base vs usuario:**")
            st.write(f"- Usuario ≥5: {result['porcentaje_hit5']}% | Azar ≥5: {result['linea_base_hit5']}%")
            st.write(f"- Usuario ≥7: {result['porcentaje_hit7']}% | Azar ≥7: {result['linea_base_hit7']}%")

            # Detalle por sorteo expandible
            with st.expander("Ver detalle por sorteo"):
                for r in result["detalle_por_sorteo"][:5]:  # primeros 5 para no saturar
                    st.write(f"Sorteo {r['sorteo_idx']} ({r['sorteo_date']}): mejor acierto {r['mejor_acierto']} "
                              f"(usuario), base ≥5: {max(r['linea_base_aciertos'])}, base ≥7: {max(r['linea_base_aciertos']) > 6}")