# Tasks: SuperKino Análisis

## 1. Setup del proyecto

- [ ] 1.1 Crear estructura (`superkino/core/`, `superkino/app/pages/`, `tests/`), entorno virtual y `requirements.txt` con versiones fijadas (streamlit, pandas, numpy, scipy, plotly; dev: pytest, ruff). Verificar: `pip install -r requirements.txt` termina sin errores y `python -c "import pandas, numpy, scipy, plotly"` funciona.
- [ ] 1.2 Configurar `pyproject.toml` (ruff lint+format, pytest con path de tests). Verificar: `ruff check .` y `pytest` ejecutan limpios sobre la suite vacía.

## 2. Modelos e ingesta (core)

- [ ] 2.1 Implementar `superkino/core/models.py`: dataclass `Draw` (fecha ISO + 20 números) y `DrawHistory` (ordenado por fecha, acceso por índice/fecha). Verificar: test unitario construye un historial desde fixture pequeño y consulta por fecha.
- [ ] 2.2 Implementar parser+validador en `ingest.py` (regex estructural → fecha válida → 20 enteros → rango 1–80 → unicidad; resultado aceptada/rechazada-con-motivo). Verificar: tests con línea válida, la línea real del 16/06/2026 (23 duplicado) como fixture, número fuera de rango, cantidad ≠ 20 y fecha inválida — cada rechazo con su motivo.
- [ ] 2.3 Implementar detector de huecos de fechas sobre el rango [mín, máx] cargado. Verificar: test con fixture que omite el 04/07/2026 reporta exactamente esa fecha como advertencia.
- [ ] 2.4 Implementar `storage.py` (SQLite: esquema `draws(date PK, numbers JSON)`, carga completa, `INSERT OR IGNORE` con conteo de omitidos, `is_empty`). Verificar: tests de persistencia entre conexiones y de re-inserción del mismo archivo (omitidos informados, sin duplicados).
- [ ] 2.5 Implementar exportación a txt (líneas `DD/MM/AAAA,n1,...,n20` ordenadas por fecha ascendente). Verificar: test de ida y vuelta — importar `SuperKinoTV.txt` (sin la línea inválida), exportar, re-importar produce el mismo conjunto de sorteos.

## 3. Análisis matricial (core)

- [ ] 3.1 Implementar matriz de presencia `P ∈ {0,1}^{W×80}`, frecuencias y piso esperado `W·20/80`. Verificar: test contra fixture pequeño calculado a mano.
- [ ] 3.2 Implementar cálculo de atrasos (cerdos finales por columna; ausente en ventana ⇒ atraso = W). Verificar: test con fixture donde un número nunca aparece en la ventana.
- [ ] 3.3 Implementar matriz posicional `X ∈ ℕ^{W×20}` con estadísticas empíricas por posición, media teórica `j·81/21` y posición teórica por número `1 + 19(n−1)/79`. Verificar: test de fórmulas teóricas contra valores calculados a mano y de consistencia X ordenada ascendente por fila.
- [ ] 3.4 Implementar suma total, paridad y decenas por sorteo con agregados de ventana. Verificar: test contra fixture pequeño calculado a mano.
- [ ] 3.5 Implementar lift de pares (`C = PᵀP − diag`, esperado `W·(20/80)(19/79)`). Verificar: test de simetría de C, diagonal cero y lift conocido en fixture.

## 4. Scoring y generador (core)

- [ ] 4.1 Implementar score individual ponderado en `scoring.py` (min-max de frecuencia, atraso/W, densidad posicional en banda teórica; pesos renormalizados a suma 1). Verificar: tests de renormalización y de componentes nulos al poner peso 0.
- [ ] 4.2 Implementar afinidad de conjuntos (promedio de lifts de pares del subconjunto). Verificar: test con subconjunto pequeño contra lift calculado en 3.5.
- [ ] 4.3 Implementar `generator.py`: softmax con temperatura T∈[0.05,2.0], muestreo sin reemplazo de 10 números, unicidad de boletos por regeneración, semilla explícita, score total con desglose. Verificar: tests de propiedad — todo boleto tiene 10 únicos en 1–80, N boletos son distintos, misma semilla reproduce salida idéntica, T mínima concentra solapamiento alto con el top-10.

## 5. Simulador walk-forward (core)

- [ ] 5.1 Implementar bucle walk-forward en `simulator.py`: para cada sorteo con ≥W previos, ventana estrictamente anterior a D, genera N boletos del modelo + N aleatorios uniformes, calcula aciertos. Verificar: test de propiedad de no-lookahead (ninguna fecha usada es ≥ D) y conteo correcto de aciertos contra sorteo simulado a mano.
- [ ] 5.2 Implementar agregados (% sorteos con mejor acierto ≥5/≥7/=10, distribución, mejor fecha) y tabla hipergeométrica de referencia con `scipy.stats.hypergeom(M=80, n=20, N=10)`. Verificar: test de agregados contra caso sintético conocido y de P(k aciertos) contra valores hipergeométricos publicados (media 2.5).

## 6. App Streamlit

- [ ] 6.1 Construir página **Historial** (`Home.py`): upload/pegado con reporte de calidad (aceptadas/rechazadas/huecos), alta manual, tabla paginada, botón de exportación y siembra automática desde `SuperKinoTV.txt` si la BD está vacía. Verificar: `streamlit run superkino/app/Home.py` localmente — cargar el txt real muestra 119 aceptadas, 1 rechazada (23 duplicado) y hueco 04/07/2026; reiniciar la app conserva el historial.
- [ ] 6.2 Construir página **Análisis**: slider de ventana W (default 100) y tabs plotly — heatmap presencia, ranking frecuencias con piso esperado, atrasos, mapa posicional empírico vs teórico, histograma de sumas, top pares por lift con observado/esperado. Verificar: en vivo, cada gráfica responde a hover/zoom y se recalcula al mover W.
- [ ] 6.3 Construir página **Combinaciones**: sliders de pesos (recalculo en vivo), temperatura, N∈[1,100]; tabla rankeada con detalle expandible (desglose por componente y posición probable por número); selección de boletos hacia `st.session_state`. Verificar: mover pesos actualiza el ranking sin recargar; generar 25 boletos produce 25 distintos con desglose visible.
- [ ] 6.4 Construir página **Simulador**: rango de fechas, N tomado de las combinaciones seleccionadas (o elegido), ejecución walk-forward, resultados usuario vs base aleatoria lado a lado, distribución, mejor fecha y tabla hipergeométrica; mensaje claro si no hay sorteos elegibles. Verificar: simulación sobre el historial real completa en segundos y muestra ambas columnas comparativas.

## 7. Integración y despliegue

- [ ] 7.1 Test E2E de integración: pipeline completo sobre el archivo real (parse → validar → persistir → analizar → generar → simular). Verificar: `pytest tests/test_e2e.py` verde con los conteos esperados (120 líneas leídas, 1 rechazada, 1 hueco).
- [ ] 7.2 Pulir repo: `.gitignore` (incluye `data/*.db`), README con instrucciones de deploy y sección de expectativas honestas (qué puede y qué no puede decir el análisis), `requirements.txt` final. Verificar: `ruff check .` y `pytest` verdes; README revisado.
- [ ] 7.3 Publicar: push a GitHub y conectar Streamlit Community Cloud (main: `superkino/app/Home.py`). Verificar: URL pública carga, las 4 páginas funcionan y la BD se siembra sola desde el txt del repo tras un redeploy.
