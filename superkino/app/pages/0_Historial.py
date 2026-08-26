"""Página principal: Historial — ingesta, validación, reporte y exportación."""

import streamlit as st

from core.ingest import ingest_file, ingest_lines
from core.models import DrawHistory


st.set_page_config(page_title="SuperKino — Historial", page_icon=":lottery_box:")

st.title("📊 SuperKino — Historial de sorteos")

st.markdown(
    "Sube tu archivo `SuperKinoTV.txt` o pega las líneas directamente. "
    "El formato esperado es una línea por sorteo: `DD/MM/AAAA,n1,n2,...,n20`"
)

# ── Session state inicial ────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = None  # DrawHistory | None
    st.session_state.problemas = []  # list[(idx, motivo)]
    st.session_state.carga_exitosa = False

# ── Área: Cargar archivo ──────────────────────────────────────────────

st.subheader("1. Cargar archivo de sorteos")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Arrastra y suelta tu archivo .txt", type="txt")
with col2:
    st.caption("Formato: `DD/MM/AAAA,n1,...,n20`")

# También permitir pegar texto directamente
st.caption("O pega las líneas aquí:")
texto_directo = st.text_area("Texto", height=150, placeholder="21/04/2026,1,5,6,14,30,...")

# Botón para procesar
if st.button("Procesar datos", type="primary") or (
    uploaded_file is not None or texto_directo.strip()
):
    lines_to_process: List[str] = []

    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        text_data = bytes_data.decode("utf-8")
        lines_to_process = text_data.splitlines()
    if texto_directo.strip():
        lines_to_process.extend(texto_directo.strip().splitlines())

    if lines_to_process:
        with st.spinner("Validando y parseando..."):
            st.session_state.history, st.session_state.problemas = ingest_lines(
                lines_to_process, reject_duplicates=True,
            )
        st.session_state.carga_exitosa = True
        st.success(f"Procesado: {st.session_state.history.count} sorteos válidos cargados.")
    else:
        st.warning("No hay líneas para procesar.")

# ── Mostrar reporte de calidad ────────────────────────────────────────

if st.session_state.carga_exitosa and st.session_state.problemas:
    st.subheader("2. Reporte de calidad")
    st.write(f"Líneas rechazadas: {len(st.session_state.problemas)}")

    with st.expander("Ver detalles de líneas rechazadas"):
        for idx, motivo in st.session_state.problemas:
            st.write(f"**Línea {idx + 1}:** {motivo}")

    # Detectar huecos de fechas
    if st.session_state.history is not None:
        fechas = st.session_state.history.dates
        from core.analysis import detect_gaps
        huecos = detect_gaps(fechas)

        if huecos:
            st.warning(f"Se detectaron {len(huecos)} día(s) sin sorteo registrado en el rango:")
            for h in huecos[:10]:  # mostrar los primeros 10
                st.write(f"- {h}")
            if len(huecos) > 10:
                st.write(f"... y {len(huecos) - 10} más.")
        else:
            st.success("No se detectaron huecos de fechas en el rango cargado.")

# ── Mostrar tabla de sorteos ───────────────────────────────────────────

if st.session_state.history is not None and st.session_state.carga_exitosa:
    st.subheader("3. Tabla de sorteos cargados")

    df_data = []
    for d in st.session_state.history._draws:
        nums_str = ",".join(str(n) for n in d.numbers)
        df_data.append({"Fecha": d.date_iso, "Sorteo": nums_str})

    import pandas as pd
    st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=300)

    # Botón de exportación
    st.download_button(
        label="Exportar historial a txt",
        data=st.session_state.history.to_file_path_returns_data(),
        file_name="SuperKino_exportado.txt",
        mime="text/plain",
    )
# Corregimos el método to_file_path - necesita devolver los datos
# Actually, let's just have the download button call the method differently
# For now, let's simplify: we'll just export the data directly

# ── Si aún no hay datos, mostrar instrucción ──────────────────────────

if not st.session_state.carga_exitosa:
    st.info("Carga un archivo .txt o pega las líneas para comenzar el análisis.")
    st.markdown(
        "Tu archivo actual de referencia tiene 120 sorteos (21/04/2026 – 19/08/2026). "
        "El primer registro tiene el número 23 duplicado, que será rechazado automáticamente."
    )


# Extensión del método en models.py - necesario para el download button
# Agreguemos este método a models.py después


def to_file_path_returns_data(self, path: str = "SuperKino_exportado.txt") -> bytes:
    """Escribir el historial y devolver los bytes para el download button."""
    lines = []
    for d in self._draws:
        nums_str = ",".join(str(n) for n in d.numbers)
        lines.append(f"{d.date_iso},{nums_str}")
    content = "\n".join(lines)
    return content.encode("utf-8")


# Attach to the class
import types
DrawHistory.to_file_path_returns_data = types.MethodType(to_file_path_returns_data, DrawHistory)