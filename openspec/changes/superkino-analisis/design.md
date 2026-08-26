# Design: SuperKino Análisis

## Context

Proyecto verde (greenfield): no existe código previo. Existe el dataset inicial `SuperKinoTV.txt` (120 sorteos, formato `DD/MM/AAAA,n1,...,n20`) con dos defectos conocidos que motivan la validación estricta: la línea del 16/06/2026 repite el número 23, y falta el sorteo del 04/07/2026. El dominio del juego: sorteo diario de 20 números distintos de 1–80; el jugador arma boletos de 10; premios por acertar 5–10. Ver proposal.md para la motivación y los specs para los requisitos.

## Goals / Non-Goals

**Goals:**

- Núcleo analítico en Python puro, desacoplado de la UI, testeable sin Streamlit instalado.
- App local-first de un solo usuario, publicable gratis en Streamlit Community Cloud.
- Reproducibilidad total: toda estocasticidad pasa por semilla explícita.
- Honestidad estadística integrada al producto (piso teórico y línea base aleatoria siempre visibles).

**Non-Goals:**

- Sin cuentas/autenticación ni multiusuario.
- Sin scraping automático de resultados (la ingesta es manual en v1).
- Sin modelos de ML pesados (redes, etc.): scoring heurístico + estadística clásica.
- Sin gestión de dinero/premios económicos: solo conteo de aciertos.

## Decisions

### D1. Stack: Streamlit + librería científica estándar

**Elección**: Streamlit como vehículo de UI; `pandas`, `numpy`, `scipy` para cálculo; `plotly` para gráficas interactivas.

**Alternativas descartadas**: Dash (más control pero ~3x más código para el mismo resultado); FastAPI+React (doble stack injustificable para v1); Jupyter/Voilà (experiencia de webapp pobre).

### D2. Arquitectura en capas: núcleo separado de la UI

```
superkino/
├── core/                  # Python puro, PROHIBIDO importar streamlit
│   ├── models.py          # Draw, DrawHistory (dataclasses)
│   ├── ingest.py          # parser línea a línea + validador + detector de huecos
│   ├── storage.py         # persistencia SQLite (sqlite3 stdlib)
│   ├── analysis.py        # matrices presencia/posicional, frecuencias, atrasos,
│   │                      #   sumas/paridad/decenas, lift de pares
│   ├── scoring.py         # score individual ponderado + afinidad de conjuntos
│   ├── generator.py       # generación de combinaciones con temperatura
│   └── simulator.py       # backtest walk-forward + línea base aleatoria
├── app/                   # capa Streamlit (solo orquestación y visualización)
│   ├── Home.py            # Historial: ingesta, reporte de calidad, tabla, export
│   └── pages/
│       ├── 1_Analisis.py
│       ├── 2_Combinaciones.py
│       └── 3_Simulador.py
└── tests/                 # pytest sobre core/
```

**Rationale**: el valor del proyecto vive en `core/`; la UI es desechable/reemplazable. Permite tests unitarios rápidos y una futura migración de frontend sin tocar cálculos.

### D3. Persistencia: SQLite con esquema mínimo

```sql
CREATE TABLE draws (
    date    TEXT PRIMARY KEY,   -- 'YYYY-MM-DD' (orden lexicográfico = cronológico)
    numbers TEXT NOT NULL        -- JSON array de 20 enteros
);
```

**Elección**: `sqlite3` de stdlib, un archivo local (`data/superkino.db`, no versionado).

**Alternativas**: JSON/pickle (sin consultas ni integridad); CSV (sin clave primaria nativa); DuckDB (dependencia extra sin beneficio a esta escala). La fecha como PRIMARY KEY hace imposible el duplicado por fecha a nivel de almacenamiento (spec data-ingest). Los números van como JSON en una columna: flexible y suficiente; 20 columnas fijas sería rigidez innecesaria.

**Arranque en frío**: si la BD está vacía al iniciar la app, se siembra automáticamente desde `SuperKinoTV.txt` incluido en el repo. Esto resuelve el problema del filesystem efímero de Streamlit Cloud (ver R1).

### D4. Ingesta y validación

Pipeline por línea: regex estructural `DD/MM/AAAA` + 20 tokens numéricos → fecha válida (día primero) → 20 enteros → rango 1–80 → unicidad. Resultado por línea: aceptada | rechazada(con motivo). Nunca silencioso.

Tras la carga: detección de huecos recorriendo el rango [mín, máx] de fechas cargadas y listando días ausentes como advertencia (un día sin registro no invalida datos; puede ser día sin sorteo o faltante — el usuario decide).

Duplicados por fecha: `INSERT OR IGNORE` + conteo de omitidos para el reporte.

### D5. Fórmulas de análisis (analysis.py)

Con ventana W (default 100):

- **Presencia**: matriz binaria `P ∈ {0,1}^{W×80}`, `P[i, n-1] = 1` si n salió en el sorteo i.
- **Frecuencia**: `f = P.sum(axis=0)`; esperado bajo uniformidad `E = W·20/80 = W/4`.
- **Atraso**: ceros finales consecutivos de cada columna de P; si el número no apareció en la ventana, atraso = W.
- **Posicional**: matriz `X ∈ ℕ^{W×20}` (valores ordenados ascendentes por fila). Media/cuartiles empíricos por posición vs media teórica de estadísticas de orden `E[X_(j)] = j·81/21`. Para un número n, su posición esperada cuando sale: `pos_teó(n) = 1 + 19·(n−1)/79` (los otros 19 sorteados son uniformes entre los 79 restantes); se compara con su histograma posicional empírico.
- **Suma/paridad/decenas**: sumas por fila de X; paridad por fila; decenas vía `bincount((X−1)//10)` sobre todo el bloque.
- **Lift de pares**: co-ocurrencia `C = PᵀP − diag(PᵀP)`; esperado por par `e = W·(20/80)·(19/79)`; `lift = C/e`. Cálculo vectorizado, costo trivial a esta escala.

Todo se calcula bajo demanda y se cachea (`st.cache_data`) con clave `(historial_hash, W)`.

### D6. Modelo de score individual (scoring.py)

```
score(n) = w_f·f_norm(n) + w_g·g_norm(n) + w_p·p_norm(n)
```

- `f_norm`: frecuencia min-max normalizada a [0,1] dentro de la ventana.
- `g_norm`: atraso / W.
- `p_norm`: densidad empírica de apariciones de n dentro de su banda posicional teórica, normalizada min-max entre números. **Nota honesta**: este componente discrimina débilmente entre números (bajo uniformidad todos aparecen igual); existe porque el usuario lo pidió explícitamente y su peso puede llevarse a 0.
- Pesos default `w_f=0.4, w_g=0.3, w_p=0.3`, ajustables con sliders; se renormalizan a suma 1 internamente.

**Afinidad de conjuntos**: score de un subconjunto S = promedio de lifts de sus pares. Se usa en el generador y se muestra en el detalle explicativo.

### D7. Generador de combinaciones con temperatura (generator.py)

1. Softmax sobre scores con temperatura T ajustable: `p_n ∝ exp(score(n)/T)`, T ∈ [0.05, 2.0]. T baja → concentración en el top (boletos casi idénticos); T alta → cercano a uniforme con leve sesgo.
2. Cada boleto: muestreo sin reemplazo de 10 números con probabilidades p (`numpy.random.Generator.choice(p=p, replace=False)`), semilla explícita (default fija, visible en UI avanzada).
3. Unicidad de boletos: regenerar con colisiones detectadas por conjunto de tuplas ordenadas hasta completar N (tope de intentos; con espacio de C(80,10)≈1.6×10⁹ las colisiones son raras salvo T mínima).
4. Score total del boleto = Σ score(número) + λ·afinidad_media(S), con λ fijo pequeño (0.1) en v1. Desglose por componente guardado para la vista explicativa.

### D8. Simulador walk-forward (simulator.py)

Para cada sorteo con fecha D que tenga ≥ W sorteos previos:

1. Ventana = W sorteos inmediatamente anteriores a D (nunca incluye D ni posteriores — propiedad testada).
2. Recalcular scores con los pesos actuales y generar N boletos (misma política de semilla/temperatura que el generador).
3. Aciertos por boleto = |boleto ∩ sorteo_real(D)|.
4. En paralelo, N boletos aleatorios uniformes (misma cantidad) como línea base.
5. Agregados: % de sorteos con mejor acierto ≥5 / ≥7 / =10, distribución de aciertos, mejor fecha; usuario vs azar lado a lado; tabla hipergeométrica de referencia (`scipy.stats.hypergeom(M=80, n=20, N=10)`).

Costo: con H sorteos hay H−W evaluaciones × 2N boletos; vectorizado en numpy es segundos incluso con miles de sorteos. Cache por `(historial_hash, W, pesos, T, N, seed)`.

### D9. UI Streamlit multipage (app/)

Cuatro páginas en español: **Historial** (upload/pegado, reporte de calidad, tabla paginada, export), **Análisis** (slider W + tabs de gráficas plotly), **Combinaciones** (sliders de pesos/temperatura/N, tabla rankeada, detalle expandible por boleto, selector para enviar al simulador), **Simulador** (rango de fechas, N, ejecutar, resultados vs base aleatoria + referencia teórica). Estado compartido vía `st.session_state` (combinaciones seleccionadas → simulador).

### D10. Calidad y reproducibilidad

- `pytest` sobre `core/`: casos del parser (incluida la línea del 23 duplicado como fixture real), validador, matemática de matrices contra fixtures pequeños calculados a mano, invariantes del generador (10 únicos en 1–80, N boletos distintos, monotonía de temperatura), y test de propiedad del simulador (ninguna ventana incluye fechas ≥ D).
- `requirements.txt` con versiones fijadas; Python ≥ 3.11; entorno virtual dedicado creado al inicio de la implementación.
- Formato de código: ruff (lint + format).

## Risks / Trade-offs

- **[R1] Streamlit Cloud tiene filesystem efímero: la SQLite se pierde en cada redeploy** → Estrategia de siembra desde el txt versionado en el repo (D3) + botón de exportación; documentar que los agregados manuales deben exportarse o incorporarse al txt del repo. BD externa queda fuera de alcance v1.
- **[R2] Lifts de pares ruidosos con ~100 sorteos (~7 co-apariciones esperadas por par)** → Mostrar siempre observado vs esperado junto al lift; etiqueta de "muestra pequeña"; el simulador arbitra con datos.
- **[R3] El componente posicional del score discrimina poco entre números** → Peso ajustable (puede ir a 0); framing descriptivo en la UI; documento de ayuda explica qué puede y qué no puede decir el análisis.
- **[R4] Datos corruptos contaminan todos los análisis** → Validación estricta con rechazo motivado (D4); el caso real del 23 duplicado es fixture de test permanente.
- **[R5] Expectativas del usuario sobre "predicción"** → Piso estadístico e hipergeométrica siempre visibles (specs matrix-analysis y simulator); comparación obligatoria contra azar.
- **[R6] Backtest débil con solo ~20 sorteos evaluables (120 totales − 100 de ventana)** → El ingestor ya soporta crecimiento; conseguir más historial es acción recomendada al usuario, no bloqueo técnico.

## Migration Plan

Greenfield: crear venv → instalar dependencias → implementar core con tests → construir app → push a GitHub → conectar Streamlit Community Cloud (main: `app/Home.py`). Rollback = borrar el deploy; sin datos previos que migrar.

## Open Questions

- ¿El juego oficialmente omite algún día (feriados)? Solo afecta el texto de la advertencia de huecos; decidible durante implementación sin cambiar specs.
- Montos/exactitud de premios por 5–9 aciertos: solo cosmético (etiquetas); el simulador mide aciertos, no dinero. Deferrable.
