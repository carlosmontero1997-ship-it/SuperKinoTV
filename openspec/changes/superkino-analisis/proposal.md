# Proposal: SuperKino Análisis

## Why

El usuario juega SuperKinoTV (lotería dominicana tipo Keno: se sortean 20 números de 1–80 diariamente y el jugador elige 10; hay premios por acertar 5–10 números) y hoy analiza su historial de sorteos a mano en un archivo txt. Necesita una herramienta que transforme ese historial en análisis visual, generación paramétrica de combinaciones y validación empírica de estrategias contra sorteos reales pasados.

Nota de expectativa (parte del propósito del producto): los sorteos son eventos independientes; la app ofrece análisis descriptivo y candidatos explicables con backtest honesto contra azar puro, no predicción garantizada.

## What Changes

- Crear una webapp Streamlit (publicable gratis en Streamlit Community Cloud) con cálculos en Python (`pandas`, `numpy`, `scipy`, `plotly`).
- **Ingesta de historial**: carga del archivo txt existente (formato `DD/MM/AAAA,n1,...,n20`), validación estricta por línea (20 números únicos en rango 1–80, fecha válida, detección de huecos de fechas y duplicados — el archivo actual tiene una línea con "23" repetido), persistencia local (SQLite) y exportación a txt.
- **Análisis matricial doble** sobre una ventana configurable (por defecto últimos 100 sorteos):
  - Matriz de presencia 100×80 (sorteos × números) → frecuencias, calientes/fríos, atrasos, heatmap.
  - Matriz posicional 100×20 (números ordenados por sorteo) → distribución por posición, comparación empírico vs teórico (estadísticas de orden).
  - Gráficas interactivas: frecuencias, atraso, heatmap presencia, mapa posicional, suma del sorteo, paridad/decenas, lift de pares.
- **Generador de combinaciones**: score individual por número (frecuencia + atraso + posicional, pesos ajustables vía sliders), score de conjuntos (pares hasta grupos de 10 vía lift/co-ocurrencia), y generación de entre 1 y 100 boletos de 10 números mediante muestreo ponderado con temperatura ajustable; cada combinación con su score explicable.
- **Simulador walk-forward**: para cada sorteo histórico con ≥100 sorteos previos, entrena el modelo solo con datos anteriores, genera las N combinaciones elegidas y mide % de acierto (≥5, ≥7, 10 aciertos), comparando siempre contra N boletos aleatorios como línea base justa.
- Datos iniciales: `SuperKinoTV.txt` (120 sorteos, 21/04/2026–19/08/2026).

## Capabilities

### New Capabilities
- `data-ingest`: Carga, validación, persistencia y exportación del historial de sorteos.
- `matrix-analysis`: Análisis matricial (presencia y posicional) con visualizaciones interactivas sobre ventana configurable.
- `combination-generator`: Scoring de números individuales y conjuntos, y generación paramétrica de 1–100 combinaciones de 10 números.
- `simulator`: Backtest walk-forward de combinaciones contra sorteos históricos con línea base aleatoria.

### Modified Capabilities

N/A (proyecto nuevo, no existen specs previas)

## Impact

- **Código**: proyecto Python nuevo desde cero en este repositorio (app Streamlit + módulos de análisis).
- **Dependencias**: `streamlit`, `pandas`, `numpy`, `scipy`, `plotly` (se instalarán al iniciar la implementación, en entorno virtual dedicado).
- **Datos**: `SuperKinoTV.txt` como dataset inicial; base SQLite local generada por la app (no versionada).
- **Despliegue**: Streamlit Community Cloud (gratis, app pública; los datos son públicos así que sin riesgo de privacidad).
- **Sin breaking changes** (no existe sistema previo).
