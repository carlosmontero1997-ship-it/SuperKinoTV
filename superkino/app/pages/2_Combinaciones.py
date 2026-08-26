"""Página de Combinaciones — score individual, afinidad, generación con temperatura."""

import streamlit as st
import numpy as np

from core.scoring import individual_score, set_affinity_mean_lift, generate_combinations, ticket_explainer
from core.analysis import compute_positional_stats


st.set_page_config(page_title="SuperKino — Combinaciones", page_icon:"🎫")
st.sidebar.title("⚙️ Generador de combinaciones")

# ── Cargar historial ──────────────────────────────────────────────────
if "history" not in st.session_state or st.session_state.get("history_page") != "combinaciones":
    st.session_state.history = None
    st.session_state.combo_window = 100
    st.session_state.combo_temperature = 1.0
    st.session_state.combo_n = 25

st.sidebar.markdown("### Datos base")
upd = st.sidebar.file_uploader("SuperKinoTV.txt", type="txt", key="combo_upload")
if upd is not None:
    text = upd.getvalue().decode("utf-8")
    lines = text.splitlines()
    from core.ingest import ingest_lines
    st.session_state.history, _ = ingest_lines(lines)
    st.session_state.combo_window = 100
    st.sidebar.success(f"{st.session_state.history.count} sorteos cargados")

window = st.sidebar.slider("Ventana de análisis (W)", 20, 300, 100, key="combo_window")
temperature = st.sidebar.slider("Temperatura (diversidad)", 0.1, 3.0, 1.0, 0.1, key="combo_temperature")
n_combinations = st.sidebar.number_input("Número de combinaciones (1-100)", 1, 100, 25, 1)

if st.session_state.history is not None:
    # Calcular scores sobre la ventana
    from core.analysis import analyze_window
    result = analyze_window(st.session_state.history, window)
    scores = np.array(result["frequencies"])  # usamos frecuencia como base simple

    st.title("🎫 SuperKino — Generador de Combinaciones")

    st.markdown(
        f"**Scores individuales** (basados en frecuencia sobre W={window} sorteos). "
        "Usa los sliders para ajustar pesos en la implementación completa. "
        "Aquí mostramos el ranking simple."
    )

    # Ranking de números
    numbered = [(i + 1, s) for i, s in enumerate(scores)]
    numbered.sort(key=lambda x: x[1], reverse=True)
    st.write("**Ranking de números por score:**")
    for i, (num, score) in enumerate(numbered[:20]):
        st.write(f"N{num}: {score:.3f}")

    # Generar combinaciones
    if st.button("Generar combinaciones", type="primary"):
        with st.spinner("Generando combinaciones con temperatura..."):
            combos = generate_combinations(
                scores, temperature=temperature, n_combinations=n_combinations,
                rng_seed=42,
            )

        st.success(f"Generadas {len(combos)} combinaciones únicas de 10 números cada una.")

        # Mostrar cada combinación con explicación
        st.subheader("Tus combinaciones")
        for idx, (numbers, score_total) in enumerate(combos):
            with st.expander(f"Combinación {idx + 1} — Score: {score_total:.3f}"):
                explainer = ticket_explainer(numbers, scores)
                st.write(f"**Números:** {explainer['numbers']}")
                st.write(f"**Score total:** {explainer['score_total']:.3f}")
                st.write("**Desglose por número:**")
                for n in explainer["numbers"]:
                    st.caption(f"N{n}: score {explainer['component_breakdown'][list(explainer['numbers']).index(n)]['score']:.3f} "
                              f"(posición teórica ≈ {explainer['component_breakdown'][list(explainer['numbers']).index(n)]['position_theoretical']:.1f})")