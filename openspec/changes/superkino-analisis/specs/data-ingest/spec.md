# Delta Spec: data-ingest

## Purpose

Ingestar, validar y persistir el historial de sorteos de SuperKinoTV como fuente única y confiable de datos para todos los análisis, con control de calidad por línea y exportación al formato original.

## ADDED Requirements

### Requirement: Carga de archivo de historial
El sistema DEBE (MUST) permitir cargar un archivo de texto donde cada línea tiene el formato `DD/MM/AAAA,n1,n2,...,n20` (fecha seguida de los 20 números del sorteo separados por comas, en orden ascendente).

#### Scenario: Carga exitosa
- **WHEN** el usuario carga un archivo con líneas válidas
- **THEN** el sistema muestra la cantidad de sorteos importados y el rango de fechas cubierto

### Requirement: Validación estricta por línea
El sistema DEBE (MUST) validar cada línea antes de incorporarla: fecha válida, exactamente 20 valores numéricos, todos distintos entre sí, y cada uno entero en el rango 1–80. Las líneas inválidas NO DEBEN (MUST NOT) incorporarse al historial.

#### Scenario: Número repetido dentro de una línea
- **WHEN** una línea contiene un número repetido (ej. "23" dos veces)
- **THEN** la línea es rechazada e identificada con su fecha y el motivo del rechazo

#### Scenario: Número fuera de rango
- **WHEN** una línea contiene un número menor que 1 o mayor que 80
- **THEN** la línea es rechazada e identificada con su fecha y el motivo del rechazo

#### Scenario: Cantidad incorrecta de números
- **WHEN** una línea contiene más o menos de 20 números
- **THEN** la línea es rechazada e identificada con su fecha y el motivo del rechazo

#### Scenario: Fecha inválida
- **WHEN** una línea tiene una fecha inexistente o mal formateada
- **THEN** la línea es rechazada e identificada con el motivo del rechazo

### Requirement: Reporte de calidad de datos
El sistema DEBE (MUST) presentar tras cada carga un resumen de calidad: líneas aceptadas, líneas rechazadas con su motivo, y huecos de fechas dentro del rango cargado (días sin sorteo registrado), listados como advertencia sin invalidar el resto.

#### Scenario: Hueco de fechas
- **WHEN** faltan uno o más días dentro del rango de fechas cargado
- **THEN** el sistema lista las fechas faltantes como advertencia y conserva los sorteos válidos

### Requirement: Persistencia entre sesiones
El sistema DEBE (MUST) almacenar localmente los sorteos validados de forma que sobrevivan al cierre o reinicio de la aplicación, sin necesidad de recargar los archivos.

#### Scenario: Reinicio de la aplicación
- **WHEN** la aplicación se reinicia después de haber cargado o agregado sorteos
- **THEN** el historial completo sigue disponible para análisis

### Requirement: Sin duplicados por fecha
El sistema NO DEBE (MUST NOT) almacenar dos sorteos con la misma fecha; ante un intento de duplicado DEBE (MUST) conservar el existente e informar la omisión.

#### Scenario: Re-carga del mismo archivo
- **WHEN** se carga nuevamente un archivo con fechas ya almacenadas
- **THEN** los sorteos con fecha existente se omiten y se informa cuántos fueron omitidos

### Requirement: Alta manual de sorteo
El sistema DEBE (MUST) permitir agregar un sorteo individual escribiendo o pegando una línea con el mismo formato del archivo, aplicando exactamente las mismas validaciones.

#### Scenario: Alta manual válida
- **WHEN** el usuario pega una línea válida correspondiente a un sorteo nuevo
- **THEN** el sorteo se agrega al historial y queda disponible para todos los análisis

### Requirement: Exportación a txt
El sistema DEBE (MUST) permitir descargar el historial completo en el mismo formato de entrada, con una línea por sorteo ordenadas por fecha ascendente.

#### Scenario: Exportación completa
- **WHEN** el usuario solicita exportar el historial
- **THEN** descarga un archivo txt con todas las líneas en formato `DD/MM/AAAA,n1,...,n20` ordenadas por fecha
