"""Página de Análisis — matrices presencia y posicional, frecuencias, atrasos, lift, sumas."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.analysis import analyze_window, format_freq_table, format_gap_table
from core.models import DrawHistory


st.set_page_config(page_title="SuperKino — Análisis", page_icon=":chart_with_upwards_trend:")
st.sidebar.title("⚙️ Filtros de análisis")

# ── Cargar historial si no está en session_state ──────────────────────
if "history" not in st.session_state or st.session_state.get("history_page") != "analisis":
    st.session_state.history = None
    st.session_state.analisis_window = 100

st.sidebar.markdown("### Cargar datos")
upd = st.sidebar.file_uploader("SuperKinoTV.txt", type="txt", key="analisis_upload")
if upd is not None:
    text = upd.getvalue().decode("utf-8")
    lines = text.splitlines()
    from core.ingest import ingest_lines
    st.session_state.history, _ = ingest_lines(lines)
    st.session_state.analisis_window = 100
    st.sidebar.success(f"{st.session_state.history.count} sorteos cargados")

window = st.sidebar.slider("Ventana de sorteos (W)", min_value=20, max_value=300, value=100)

if st.session_state.history is not None:
    result = analyze_window(st.session_state.history, window)

    st.title("📊 SuperKino — Análisis Matricial")

    # --- Pestañas ---
    tabs = st.tabs(["🔥 Frecuencias y Atrasos", "📍 Posicional", "📈 Sumas y Paridad", "🔗 Lift de Pares"])

    # Tab 1: Frecuencias y Atrasos
    with tabs[0]:
        st.subheader("Frecuencias (calientes/frías)")
        freq_data = format_freq_table(st.session_state.history, window)
        P = result["presence_matrix"]
        df_heat = pd.DataFrame(P, index=[f"S{i+1}" for i in range(len(P))],
                               columns=[f"N{n}" for n in range(1, 81)])
        st.plotly_chart(px.imshow(df_heat, aspect="color", title="Heatmap Presencia (W×80)"),
                        use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top 10 números calientes**")
            for num, freq in freq_data["hot_numbers"]:
                st.write(f"N{num}: {freq}")
        with col2:
            st.write("**Top 10 números fríos**")
            for num, freq in freq_data["cold_numbers"]:
                st.write(f"N{num}: {freq}")

        st.subheader("Atrasos (sorteos desde última aparición)")
        gap_data = format_gap_table(st.session_state.history, window)
        top_gaps = gap_data["gaps"][:15]
        for num, gap in top_gaps:
            st.write(f"N{num}: ausencia de {gap} sorteo(s)")

    # Tab 2: Posicional
    with tabs[1]:
        st.subheader("Distribución posicional")
        pos = format_positional_summary(st.session_state.history, window)
        df_pos = pd.DataFrame({
            "Posición": list(range(1, 21)),
            "Empírica": pos["empirical_means"],
            "Teórica": pos["theoretical_means"],
        })
        fig = px.line(df_pos, x="Posición", y=["Empírica", "Teórica"],
                      title="Media por posición: empírica vs teórica (j·81/21)")
        st.plotly_chart(fig, use_container_width=True)

        st.write("**Posición teórica esperada para cada número:**")
        per_num = pos["per_number_theoretical"]
        ejemplo = list(per_num.items())[:5]
        for n, pos in ejemplo:
            st.write(f"N{n}: posición esperada ≈ {pos:.1f}")

    # Tab 3: Sumas y Paridad
    with tabs[2]:
        st.subheader("Suma total del sorteo")
        st.write(f"**Promedio de suma:** {result['sum_avg']:.1f}")
        fig2 = px.histogram(x=result["sums"], nbins=30,
                           title="Distribución de sumas de los 20 números")
        st.plotly_chart(fig2, use_container_width=True)

        st.write("**Paridad por sorteo**")
        parity_counts = result["parity_counts"]
        parity_df = pd.DataFrame(parity_counts, columns=["Impares", "Pares"],
                                  index=[f"S{i+1}" for i in range(len(parity_counts))])
        st.dataframe(parity_df.head(10))

        st.write("**Distribución por decenas** (1–10, 11–20, …, 71–80)")
        dec = result["decade_counts"]
        dec_total = pd.Series(dec).sum()
        st.bar_chart(dec_total)

    # Tab 4: Lift de pares
    with tabs[3]:
        st.subheader("Lift de co-ocurrencia de pares")
        st.write(
            "Lift = co-aplicación observada / esperada por azar. "
            "Valores > 1 indican que el par sale juntos más de lo esperado."
        )
        # Calcular lift y mostrar top/bottom
        from core.analysis import compute_pair_lift
        P = result["presence_matrix"]
        observed, lift = compute_pair_lift(P, window)
        # Formatear a dataframe los 20 pares con lift más alto y más bajo
        n = 80
        pairs_list = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs_list.append(((i + 1, j + 1), lift[i, j]))
        pairs_df = pd.DataFrame(pairs_list, columns=["Par", "Lift"])
        top_20_high = pairs_df.nlargest(20, "Lift")
        top_20_low = pairs_df.nsmallest(20, "Lift")

        st.write("**Pares con mayor lift**")
        for _, row in top_20_high.iterrows():
            st.write(f"N{row['Par'][0]}-N{row['Par'][1]}: lift {row['Lift']:.2f}")

        st.write("**Pares con menor lift**")
        for _, row in top_20_low.iterrows():
            st.write(f"N{row['Par'][0]}-N{row['Par'][1]}: lift {row['Lift']:.2f}")