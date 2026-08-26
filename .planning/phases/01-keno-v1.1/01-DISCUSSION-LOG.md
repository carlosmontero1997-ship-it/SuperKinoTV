# Discussion Log — Phase 1: Data Ingestion & Controls

**Date:** 2026-08-26
**Mode:** Default (interactive)

---

## Area 1: Validation Strictness

**Q1:** Qué tan estricto debe ser el parser de datos?
- Options: Estricto | Leniente auto-fix | Leniente con advertencia
- **Selection:** Estricto — rechaza todo lo que no sea formato perfecto
- **Follow-up:** Debe informar dónde está la línea de error, no solo ignorar

**Q2:** Cuando una línea falla validación, ¿qué pasa con el resto?
- Options: Continuar con válidos | Bloquear todo si hay errores
- **Selection:** Bloquear todo — el usuario debe corregir antes de continuar

---

## Area 2: Error Feedback UX

**Q1:** ¿Cómo se muestran los errores de parseo?
- Options: Lista expandible | Inline en text area | Alerta en sidebar
- **Selection:** Lista expandible con errores numerados

---

## Area 3: Band Distribution Behavior

**Q1:** Cuando el usuario cambia el tamaño del pool, ¿qué pasa con la distribución?
- Options: Recalcular automático | Mantener y advertir | Forzar a Equilibrada
- **Selection:** Recalcular automático proporcionalmente

**Q2:** En modo Personalizada, si la suma no coincide con pool size
- Options: Bloquear generación | Ajustar último campo | Permitir con warning
- **Selection:** Bloquear generación hasta que la suma coincida

**Q3:** ¿Qué preset debe ser el predeterminado?
- Options: Equilibrada Dinámica | 4-3-3 | Sin preset, forzar personalizada
- **Selection:** Sin preset, forzar personalizada — control total del usuario

**Q4:** ¿Cómo se muestra la distribución actual?
- Options: Métricas con colores | Barra de progreso | Solo números
- **Selection:** Métricas con colores por franja (Baja=azul, Media=amarillo, Alta=rojo)

---

## Area 4: Data Persistence Across Tabs

**Q1:** Cuando el usuario cambia de pestaña, ¿los datos persisten?
- Options: Persistir siempre | Recargar por pestaña | Persistir + refresh
- **Selection:** Persistir siempre en session state

**Q2:** ¿Qué pasa si el usuario sube un nuevo archivo?
- Options: Reemplazar con confirmación | Reemplazar silenciosamente | Acumular
- **Selection:** Reemplazar con confirmación

**Q3:** Si hay archivo Y text area con datos
- Options: Combinar ambos | Priorizar archivo | Priorizar text area
- **Selection:** Detectar ambas fuentes, preguntar cuál usar, combinar si elige ambas

---

## Deferred Ideas

- Walk-forward backtesting simulator — v2
- Heatmap visualization — v2
- Lift/co-occurrence analysis — v2
- Temperature-controlled generation — v2
