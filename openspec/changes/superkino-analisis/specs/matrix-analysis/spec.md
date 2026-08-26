# Delta Spec: matrix-analysis

## Purpose

Analizar la ventana reciente de sorteos mediante la doble matriz (presencia sorteos×números y posicional sorteos×posiciones) y presentar estadísticas y visualizaciones interactivas que revelen frecuencias, atrasos, estructura posicional y afinidades entre números.

## ADDED Requirements

### Requirement: Ventana de análisis configurable
El sistema DEBE (MUST) analizar los últimos W sorteos del historial, donde W es ajustable por el usuario con valor por defecto 100. Si el historial contiene menos de W sorteos, DEBE (MUST) analizar todos los disponibles e indicarlo.

#### Scenario: Historial menor que la ventana
- **WHEN** el historial tiene menos sorteos que el valor de ventana configurado
- **THEN** el análisis se calcula sobre todo el historial disponible y se muestra un aviso con la cantidad real utilizada

### Requirement: Matriz de presencia
El sistema DEBE (MUST) construir la matriz de W sorteos × 80 números donde cada celda indica si el número salió en ese sorteo, y derivar de ella: la frecuencia de cada número (apariciones en la ventana) y el atraso de cada número (cantidad de sorteos consecutivos desde su última aparición; si nunca apareció en la ventana, su atraso es W).

#### Scenario: Frecuencia por número
- **WHEN** se visualiza el análisis de frecuencias
- **THEN** cada número del 1 al 80 muestra su cantidad de apariciones en la ventana, identificando los más frecuentes (calientes) y menos frecuentes (fríos)

#### Scenario: Atraso por número
- **WHEN** se visualiza el análisis de atrasos
- **THEN** cada número muestra cuántos sorteos lleva sin salir, permitiendo ordenarlos de mayor a menor atraso (números "vencidos")

### Requirement: Matriz posicional
El sistema DEBE (MUST) construir la matriz de W sorteos × 20 posiciones conteniendo los números de cada sorteo en orden ascendente, y calcular la distribución empírica de valores por posición, presentada junto a la referencia teórica de estadísticas de orden para un sorteo de 20 números de 1–80.

#### Scenario: Posición probable de un número
- **WHEN** el usuario consulta un número candidato
- **THEN** el sistema muestra la banda de posiciones donde ese número tiende a aparecer cuando sale, junto con la posición teórica esperada

### Requirement: Estadísticas complementarias del sorteo
El sistema DEBE (MUST) calcular por sorteo la suma total de sus 20 números, la cantidad de impares y pares, y la cantidad de números por decena (1–10, 11–20, ..., 71–80), junto con sus distribuciones agregadas sobre la ventana.

#### Scenario: Distribución de sumas
- **WHEN** se visualiza el análisis de sumas
- **THEN** se muestra el histograma de sumas de la ventana con su promedio y dispersión

### Requirement: Lift de co-ocurrencia de pares
El sistema DEBE (MUST) calcular, para cada par de números, su co-aparición observada en la ventana frente a la esperada por azar (lift), y destacar los pares con mayor y menor lift indicando que la muestra es pequeña y el valor orientativo.

#### Scenario: Pares destacados
- **WHEN** se visualiza el análisis de pares
- **THEN** se listan los pares con lift más alto y más bajo, cada uno con sus apariciones observadas y esperadas

### Requirement: Visualizaciones interactivas
El sistema DEBE (MUST) presentar como mínimo estas visualizaciones interactivas (con zoom y detalle al pasar el cursor): heatmap de la matriz de presencia, ranking de frecuencias, gráfico de atrasos, mapa posicional empírico vs teórico, histograma de sumas y ranking de pares por lift.

#### Scenario: Exploración del heatmap
- **WHEN** el usuario pasa el cursor sobre una celda del heatmap de presencia
- **THEN** se muestra el número, la fecha del sorteo y si el número salió o no

### Requirement: Piso estadístico visible
El sistema DEBE (MUST) mostrar siempre el piso estadístico de referencia: la cantidad esperada de apariciones por número en la ventana (aproximadamente W × 20 / 80) y la expectativa teórica de aciertos para un boleto de 10 números contra un sorteo de 20 de 80 (media 2.5), para contextualizar las desviaciones observadas.

#### Scenario: Contexto de frecuencias
- **WHEN** se muestra el ranking de frecuencias
- **THEN** la vista incluye la cantidad esperada de apariciones por número bajo uniformidad, como referencia de comparación
