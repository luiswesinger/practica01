# SmartCampus · Diccionario de datos

El archivo `sensores.csv` contiene lecturas ambientales **sintéticas**, preparadas para esta práctica. No son datos reales de personas ni de edificios concretos.

| Columna | Contenido | Ejemplo | Tipo esperado |
|---|---|---|---|
| `edificio` | Código del edificio | `A` | Texto |
| `fecha_hora` | Fecha y hora de la lectura | `2026-10-14 08:00:00` | Fecha-hora |
| `temperatura` | Temperatura ambiente | `23.1` | Numérico, °C |
| `humedad` | Humedad relativa | `51.2` | Numérico, % |
| `co2_ppm` | Concentración de dióxido de carbono | `1080` | Entero, ppm |

**Detalles:** CSV separado por comas, codificación UTF-8, encabezado en la primera fila y punto como separador decimal. Incluye lecturas de los edificios A, B, C y D a lo largo de una jornada. Los campos siguen exactamente el enunciado.

**Importante:** El archivo constituye la entrada a procesar; no representa una base de datos ya creada ni una solución al taller. La estructura de la tabla y la lógica de ingestión las debe implementar el equipo.
