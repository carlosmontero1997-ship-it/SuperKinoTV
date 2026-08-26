# Delta Spec: simulator

## Purpose

Validar empíricamente las combinaciones del usuario contra sorteos históricos reales mediante backtest walk-forward (sin acceso al futuro), con línea base aleatoria de igual tamaño para una comparación justa.

## ADDED Requirements

### Requirement: Backtest walk-forward sin sesgo de futuro
Para cada sorteo histórico que cuente con al menos W sorteos previos (W = tamaño de ventana configurado), el sistema DEBE (MUST) generar las combinaciones candidatas usando exclusivamente información de sorteos con fecha anterior a la del sorteo evaluado.

#### Scenario: Sin mirada al futuro
- **WHEN** el simulador evalúa el sorteo del día D
- **THEN** el modelo que genera las combinaciones solo utiliza sorteos con fecha estrictamente anterior a D

### Requirement: Evaluación de aciertos
El sistema DEBE (MUST) calcular, por sorteo simulado y por combinación jugada, la cantidad de aciertos (intersección entre la combinación y los 20 números realmente sorteados), y agregar los resultados en: porcentaje de sorteos cuyo mejor acierto fue ≥5, ≥7 y =10; distribución de aciertos; y mejor resultado por fecha.

#### Scenario: Resultados agregados
- **WHEN** termina la simulación sobre un rango de fechas
- **THEN** el sistema muestra el porcentaje de sorteos con mejor acierto ≥5, ≥7 y =10, la distribución de aciertos y el detalle del mejor día

### Requirement: Línea base aleatoria
El sistema DEBE (MUST) ejecutar la misma simulación con N boletos generados al azar (misma cantidad N que las combinaciones del usuario) y presentar ambos conjuntos de resultados lado a lado.

#### Scenario: Comparación justa
- **WHEN** se completa la simulación con las combinaciones del usuario
- **THEN** las métricas del usuario y las de la línea base aleatoria se muestran juntas, ambas calculadas con la misma cantidad de boletos por sorteo

### Requirement: Configuración de simulación
El sistema DEBE (MUST) permitir elegir el rango de fechas a simular y la cantidad de combinaciones (entre 1 y 100) a evaluar, e informar cuántos sorteos del rango son elegibles según el umbral mínimo de historia previa.

#### Scenario: Historial insuficiente
- **WHEN** ningún sorteo del rango elegido cuenta con al menos W sorteos previos
- **THEN** el sistema lo informa claramente y no ejecuta la simulación

### Requirement: Referencia teórica de aciertos
El sistema DEBE (MUST) mostrar la tabla de probabilidad teórica (distribución hipergeométrica) de acertar k números para un boleto de 10 contra un sorteo de 20 de 80, incluyendo la probabilidad del premio mayor (10 aciertos), como referencia del comportamiento esperado del azar puro.

#### Scenario: Consulta de referencia
- **WHEN** el usuario visualiza los resultados de la simulación
- **THEN** la vista incluye la tabla de probabilidades teóricas por cantidad de aciertos para contextualizar los resultados obtenidos
