# Requirements: SuperKinoTV v1.2

**Defined:** 2026-08-27
**Core Value:** Deterministic combinatorial analysis and wheeling-based ticket generation from historical Keno 20/80 data

## v1.2 Requirements

### Backtesting

- [x] **BT-01**: Simulación walk-forward: entrenar en N sorteos, probar en el siguiente sorteo, deslizar hacia adelante — validated in Phase 6
- [x] **BT-02**: Rastrear rendimiento de la estrategia del usuario en todos los períodos de prueba — validated in Phase 6
- [x] **BT-03**: Comparar contra línea base aleatoria (distribución hipergeométrica + Monte Carlo) — validated in Phase 6
- [x] **BT-04**: Parámetro de temperatura T controla exploración vs explotación — validated in Phase 6
- [x] **BT-05**: Visualizar resultados: aciertos acumulados, tasa de acierto, comparación de ROI — validated in Phase 6
- [x] **BT-06**: Análisis predictivo para optimizar selección de números con distribuciones sugeridas y análisis inteligente

### Distribución de Bandas por Boleto

- [x] **BAND-01**: Usuario puede seleccionar esquema de distribución de bandas por boleto (ej: 4-3-3, 3-4-3, 1-4-4-1) — validated in Phase 5
- [x] **BAND-02**: Algoritmo de wheeling respeta la distribución de bandas seleccionada por boleto — validated in Phase 5
- [x] **BAND-03**: Mostrar información de distribución de bandas en resumen de boletos y volantes — validated in Phase 5

### Matriz Intermedia

- [ ] **MATX-03**: Matriz intermedia muestra S1 como el sorteo más reciente (fila superior)
- [ ] **MATX-04**: Siempre tomar los 100 sorteos más recientes disponibles para generar la matriz

## Out of Scope

| Feature | Razón |
|---------|-------|
| Predicción con ML/AI | Solo algoritmos deterministas |
| Datos en tiempo real | Análisis offline |
| App móvil | Solo Streamlit web |

## Traceability

| Requirement | Fase | Estado |
|-------------|------|--------|
| BT-01 | Phase 6 | Completo |
| BT-02 | Phase 6 | Completo |
| BT-03 | Phase 6 | Completo |
| BT-04 | Phase 6 | Completo |
| BT-05 | Phase 6 | Completo |
| BT-06 | Phase 7 | Completo |
| BAND-01 | Phase 5 | Completo |
| BAND-02 | Phase 5 | Completo |
| BAND-03 | Phase 5 | Completo |
| MATX-03 | Phase 4 | Pendiente |
| MATX-04 | Phase 4 | Pendiente |

**Cobertura:**
- v1.2 requirements: 11 total
- Mapeados a fases: 11
- Completados: 8 (BT-01 through BT-05, BAND-01 through BAND-03)
- Pendientes: 3 (BT-06, MATX-03, MATX-04)
- Sin mapear: 0 ✓

---
*Requirements actualizados: 2026-08-27 after Phase 6 completion*
