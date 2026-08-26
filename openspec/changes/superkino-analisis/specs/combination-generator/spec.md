# Delta Spec: combination-generator

## Purpose

Generar combinaciones elegibles de 10 números a partir de scores individuales ponderados (frecuencia, atraso, posición) y de afinidad entre números (lift de co-ocurrencia), con parámetros ajustables en vivo y explicabilidad de cada boleto.

## ADDED Requirements

### Requirement: Score individual ponderado
El sistema DEBE (MUST) asignar a cada número del 1 al 80 un score individual que combine frecuencia, atraso y probabilidad posicional, con pesos visibles y ajustables por el usuario. Al cambiar un peso, el ranking DEBE (MUST) recalcularse sin recargar la página.

#### Scenario: Ajuste de pesos en vivo
- **WHEN** el usuario modifica el peso de cualquiera de los componentes
- **THEN** el ranking de números y su score se recalculan y se muestran al instante

### Requirement: Score de conjuntos
El sistema DEBE (MUST) evaluar la afinidad entre números mediante el lift de co-ocurrencia observado en la ventana de análisis, aplicable desde pares hasta conjuntos crecientes de hasta 10 números, y usarla al construir los boletos.

#### Scenario: Afinidad entre dos números
- **WHEN** el usuario consulta dos números específicos
- **THEN** el sistema muestra su lift de co-ocurrencia en la ventana actual con sus apariciones observadas y esperadas

### Requirement: Generación paramétrica de combinaciones
El sistema DEBE (MUST) generar entre 1 y 100 combinaciones según lo indique el usuario; cada combinación DEBE (MUST) contener exactamente 10 números únicos en el rango 1–80, y todas las combinaciones generadas DEBEN (MUST) ser distintas entre sí. La diversidad entre combinaciones DEBE (MUST) controlarse mediante un parámetro de temperatura ajustable.

#### Scenario: Generación de N combinaciones
- **WHEN** el usuario solicita generar N combinaciones (1 ≤ N ≤ 100)
- **THEN** el sistema produce exactamente N boletos, cada uno con 10 números únicos en rango, sin duplicados entre sí

#### Scenario: Temperatura baja
- **WHEN** el usuario genera combinaciones con temperatura mínima
- **THEN** los boletos resultantes son muy similares entre sí, concentrados en los números de mayor score

#### Scenario: Temperatura alta
- **WHEN** el usuario genera combinaciones con temperatura máxima
- **THEN** los boletos resultantes presentan mayor variedad de números manteniendo el sesgo hacia mayores scores

### Requirement: Explicabilidad de cada combinación
CADA combinación generada DEBE (MUST) mostrar su score total y el desglose por componente (frecuencia, atraso, posicional, afinidad de conjunto) para que el usuario entienda por qué fue elegida.

#### Scenario: Detalle de un boleto
- **WHEN** el usuario selecciona una combinación generada
- **THEN** ve su score total, el desglose por componente y la posición probable de cada número según el análisis posicional

### Requirement: Selección para simulación
El sistema DEBE (MUST) permitir al usuario seleccionar cualquier subconjunto de las combinaciones generadas (o todas) y enviarlas al simulador como boletos a evaluar.

#### Scenario: Envío al simulador
- **WHEN** el usuario selecciona una o más combinaciones y confirma
- **THEN** esas combinaciones quedan configuradas como boletos del simulador
