---
status: investigating
slug: importerror-styler-background
trigger: |
  ImportError: `Import matplotlib` failed. Styler.background_gradient requires matplotlib.
  Use pip or conda to install the matplotlib package.

  Raising at app.py:2594 in render_tab_predictive -> st.dataframe(subset_cooc.style.background_gradient(cmap="YlOrRd"))
created: 2026-08-27T17:03:13Z
updated: 2026-08-27T17:03:13Z
---

## Symptoms

- **Expected behavior**: The co-occurrence heatmap in the "Analisis Predictivo" tab renders with a YlOrRd color gradient.
- **Actual behavior**: Streamlit throws `ImportError: Styler.background_gradient requires matplotlib` and the app crashes on that dataframe.
- **Error message**: `ImportError: \`Import matplotlib\` failed. Styler.background_gradient requires matplotlib. Use pip or conda to install the matplotlib package.` (full traceback at app.py:2594 -> subset_cooc.style.background_gradient(cmap="YlOrRd"))
- **Timeline**: Appears now on the Predictive tab after expanding "Matriz de co-ocurrencia". Did not appear in earlier tab versions.
- **Reproduction**: Load data, open "Analisis Predictivo" tab, expand "Matriz de co-ocurrencia (top 20 numeros)" expander.

## Current Focus

hypothesis: |
  The code calls `pandas Styler.background_gradient()` which requires the `matplotlib` optional dependency. `matplotlib` is NOT installed in the venv and NOT listed in requirements.txt. The app imports cleanly (numpy/scipy/plotly present) but styling needs matplotlib.
next_action: |
  Verify matplotlib absence in venv, then fix. Best fix: add matplotlib to requirements.txt (deployment) AND install in venv (local). Optionally wrap the styler in a try/except to degrade gracefully if matplotlib unavailable.
