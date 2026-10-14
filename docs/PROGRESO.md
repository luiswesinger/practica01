# SmartCampus · Informe de progreso

**Asignatura:** Proyecto Big Data I · Taller evaluable 01
**Repositorio:** https://github.com/luiswesinger/practica01
**Última actualización:** 14 de octubre de 2026
**Estado global:** Reto A completado y verificado · Retos B, C y D en curso

---

## 1. Resumen del estado

| Reto | Descripción | Responsable | Estado |
|---|---|---|---|
| **A** | Infraestructura con Docker Compose | Equipo (infraestructura) | ✅ **Completado y verificado** |
| **B** | Carga, almacenamiento y análisis (pandas + SQLAlchemy) | Pendiente de asignar | ⬜ No iniciado |
| **C** | API de datos con Flask | Parcialmente cubierto por el Reto A | 🟡 En curso |
| **D** | Demostración de extremo a extremo | Depende del Reto B | ⬜ No iniciado |
| — | Evidencias (capturas) | Equipo | ⬜ No iniciado |
| — | Memoria de uso de IA | Equipo | ⬜ No iniciado |

---

## 2. Qué se ha hecho: Reto A · Infraestructura

Se ha implementado el entorno completo de tres servicios descrito en el enunciado.
Todo el sistema se levanta con **un solo comando**:

```bash
docker compose up --build
```

### 2.1 Servicios definidos

| Servicio | Imagen | Contenedor | Puerto en el host | Publica |
|---|---|---|---|---|
| `db` | Propia (`postgres:16-alpine`) | `smartcampus_db` | — | ❌ No |
| `api` | Propia (`python:3.13-slim`) | `smartcampus_api` | `5000` | ✅ Sí |
| `jupyter` | Propia (`quay.io/jupyter/minimal-notebook`) | `smartcampus_jupyter` | `8888` | ✅ Sí |

### 2.2 Qué aporta cada servicio

**`db` — PostgreSQL 16**

- Imagen propia (`db/Dockerfile`) que **copia** `db/init.sql` a
  `/docker-entrypoint-initdb.d/`, siguiendo el patrón de la asignatura: el
  esquema inicial forma parte de la imagen y no depende de una ruta del host.
- Esa carpeta solo se ejecuta **cuando el contenedor inicializa un volumen
  vacío**, es decir, la primera vez. `COPY` solo copia el fichero durante el
  build: la ejecución del SQL ocurre en el runtime.
- La tabla `lecturas` incluye los cinco campos del CSV más un `id` autoincremental,
  y dos índices de apoyo (`edificio` y `fecha_hora`).
- Los datos se guardan en el volumen con nombre `postgres_data`, por lo que
  sobreviven a `docker compose down` y a la recreación de los contenedores.
- **No publica el puerto 5432 al host**: solo lo consumen `api` y `jupyter` a
  través de la red interna de Compose. Así el puerto del equipo anfitrión no
  puede entrar en conflicto con otros proyectos.

**`api` — API Flask**

Implementa los tres endpoints obligatorios del Reto C:

| Método y ruta | Comportamiento | Código |
|---|---|---|
| `GET /health` | Comprueba el servicio **y** el acceso real a la base de datos | `200` si todo va bien · `503` si la base no responde |
| `GET /lecturas` | Devuelve las lecturas almacenadas, leídas de PostgreSQL | `200` |
| `POST /lecturas` | Valida los cinco campos obligatorios e inserta la lectura | `201` · `400` si faltan campos |

Detalles de implementación que conviene conocer:

- `GET /health` **no devuelve un 200 fijo**: ejecuta un `SELECT 1` contra
  PostgreSQL. Si la base no responde, devuelve `503` en lugar de un `200`
  engañoso. El enunciado pide comprobar «que puede acceder a la base de datos»,
  así que un 200 incondicional no cumpliría el requisito.
- `GET /lecturas` lee siempre de la base de datos. El enunciado prohíbe
  explícitamente devolver una lista escrita a mano en Python.
- La configuración se recibe por **variables de entorno**; no hay credenciales
  escritas en el código.
- Las fechas se devuelven en **ISO 8601** (`2026-10-15 12:34:56`) y los números
  como números. psycopg2 devuelve `TIMESTAMP` como `datetime` y `NUMERIC` como
  `Decimal`, y su serialización por defecto producía una fecha en formato de
  cabecera HTTP y valores entrecomillados, incómodos de consumir desde el
  notebook. Se normalizan antes de responder.

**`jupyter` — Entorno de análisis**

- Imagen propia con las dependencias instaladas **durante el build**, de modo
  que el contenedor arranca ya preparado y no hay que ejecutar `pip install`
  después:

  | Paquete | Versión instalada | Para qué |
  |---|---|---|
  | pandas | 2.3.3 | Lectura del CSV y análisis |
  | numpy | 2.5.4 | Operaciones numéricas |
  | SQLAlchemy | 2.1.4 | Capa de acceso: mismo código para PostgreSQL y SQLite |
  | psycopg2-binary | 2.9.13 | Driver de PostgreSQL |
  | requests | 2.34.2 | Prueba de integración del Reto D |

- El CSV viaja **dentro de la imagen**, en `/home/jovyan/datos/sensores.csv`.
- Los notebooks se montan desde `./notebooks`, así que se editan en el host sin
  reconstruir la imagen.
- `sqlite3` está disponible (3.54.0) para el cambio de motor del Reto B.

### 2.3 Estructura de ficheros añadida

```
practica01/
├── docker-compose.yml          ← los tres servicios, la red y el volumen
├── .env.example                ← plantilla de variables de entorno
├── .dockerignore               ← reduce el contexto de build
├── api/
│   ├── Dockerfile
│   ├── requirements.txt        ← Flask + psycopg2-binary
│   └── app.py                  ← los tres endpoints
├── jupyter/
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   ├── Dockerfile              ← copia init.sql dentro de la imagen
│   └── init.sql                ← esquema inicial de 'lecturas'
├── datos/
│   └── sensores.csv            ← el CSV que se copia en la imagen
├── docs/
│   ├── PROGRESO.md             ← este documento
│   └── PROCESO_DE_COMPILACION.md ← cómo se construyen las imágenes y por qué
├── notebooks/                  ← (vacío; lo llenará el Reto B)
└── evidencias/                 ← (vacío; capturas de la entrega)
```

> 📄 El detalle del proceso de build —correspondencia con los ejemplos de la
> asignatura, caché de capas, orden de arranque e incidencias— está en
> **[`docs/PROCESO_DE_COMPILACION.md`](PROCESO_DE_COMPILACION.md)**.

---

## 3. Cómo levantarlo

### 3.1 Requisitos previos

- Docker Desktop (o Docker Engine + el plugin `docker compose`).
- Los puertos **8888** y **5000** libres en el equipo anfitrión.

> ⚠️ **En macOS el puerto 5000 suele estar ocupado** por el sistema: el
> «Receptor de AirPlay» (Centro de Control). Si `docker compose up` falla con
> un error de puerto en uso, hay dos salidas: desactivar AirPlay en
> *Ajustes del Sistema → General → AirPlay y Handoff*, o cambiar el puerto
> publicado (véase el punto 3.3).

### 3.2 Puesta en marcha

```bash
git clone https://github.com/luiswesinger/practica01.git
cd practica01
docker compose up --build
```

Una vez arrancado:

- **Jupyter** → http://localhost:8888 (sin token, es un entorno local de prácticas)
- **API** → http://localhost:5000/health

### 3.3 Cambiar puertos o credenciales

El fichero `.env.example` documenta todas las variables. Para personalizarlas:

```bash
cp .env.example .env
```

Y editar el `.env`. **Cambiad solo el lado izquierdo** del mapeo de puertos: el
derecho es el que usa el proceso dentro del contenedor y no debe modificarse.

```env
JUPYTER_PORT=8889    # si el 8888 está ocupado
API_PORT=5001        # si el 5000 lo ocupa AirPlay en macOS
```

El fichero `.env` está excluido por `.gitignore` y **nunca se sube al
repositorio**.

### 3.4 Comandos útiles

```bash
docker compose ps                  # estado de los tres servicios
docker compose logs -f api         # seguir los logs de la API
docker compose exec db psql -U smartcampus -d smartcampus
docker compose exec jupyter bash   # entrar en el contenedor de Jupyter
docker compose down                # parar (CONSERVA los datos)
docker compose down -v             # parar y BORRAR los datos del volumen
```

### 3.5 Comprobar los endpoints manualmente

```bash
# Estado del servicio y de la base de datos
curl http://localhost:5000/health

# Lecturas almacenadas
curl http://localhost:5000/lecturas

# Insertar una lectura (cuerpo de ejemplo incluido en el repositorio)
curl -X POST http://localhost:5000/lecturas \
     -H "Content-Type: application/json" \
     --data @04_Ejemplos_pruebas/01_lectura_valida.json
```

---

## 4. Verificación realizada

Todo lo siguiente se ejecutó sobre el entorno real y estos son los resultados
obtenidos. Sirve como base para las capturas de evidencia del apartado 04 del
enunciado.

| # | Comprobación | Resultado |
|---|---|---|
| 1 | `docker compose ps` | Los tres servicios en ejecución; `db` y `jupyter` en estado `healthy` |
| 2 | Esquema en PostgreSQL (`\d lecturas`) | 6 columnas + clave primaria + 2 índices |
| 3 | `GET /health` | `200` · `{"status":"ok","database":"ok"}` |
| 4 | `GET /lecturas` (base vacía) | `200` · `{"lecturas":[],"total":0}` |
| 5 | `POST /lecturas` con el JSON válido de ejemplo | `201` · registro insertado con `id: 1` |
| 6 | `POST /lecturas` sin `co2_ppm` | `400` · `{"error":"Faltan campos obligatorios.","campos_ausentes":["co2_ppm"]}` |
| 7 | `POST /lecturas` con cuerpo vacío `{}` | `400` · lista los cinco campos ausentes |
| 8 | Persistencia tras `docker compose restart` | Los 2 registros siguen presentes |
| 9 | Conexión desde Jupyter a `db` por nombre de servicio | Correcta; consulta `SELECT count(*) FROM lecturas` |
| 10 | Red interna | `db` no publica puerto al host; `api` y `jupyter` lo alcanzan por el nombre `db` |

---

## 5. Decisiones de diseño y su justificación

Esta sección recoge el *porqué* de las decisiones, porque la guía advierte de
que cualquier miembro del equipo debe poder defender cada línea.

### 5.1 El contexto de build es la raíz del repositorio

```yaml
build:
  context: .
  dockerfile: jupyter/Dockerfile
```

Podría parecer más natural usar `context: ./jupyter`, pero el Dockerfile de
Jupyter necesita copiar `datos/`, que está **fuera** de esa carpeta. Con el
contexto en la raíz, el `.dockerignore` de la raíz mantiene el contexto pequeño
(28 kB) excluyendo el enunciado, las plantillas y los ejemplos de pruebas.

### 5.2 `db` es el hostname, no `localhost`

Dentro de la red de Compose cada servicio se resuelve por **su nombre**. Desde
el contenedor de la API, `localhost` apuntaría a la propia API, no a
PostgreSQL. Por eso las variables de entorno usan `DB_HOST=db`.

Los `container_name` (`smartcampus_db`, etc.) sirven para identificar los
contenedores con `docker ps`, pero **no** se usan como hostname: Compose
resuelve por nombre de servicio.

### 5.3 No se publica el puerto de PostgreSQL

El enunciado pide exponer «los puertos necesarios para acceder a Jupyter y a la
API». PostgreSQL no necesita estar accesible desde el host: solo lo consumen
`api` y `jupyter`, que están en la misma red. No publicarlo evita conflictos de
puerto (por ejemplo con otro PostgreSQL ya instalado) y reduce la superficie
expuesta. Para inspeccionar la base se usa `docker compose exec db psql …`.

### 5.4 Los servicios esperan a que la base esté *sana*

```yaml
depends_on:
  db:
    condition: service_healthy
```

`depends_on` por sí solo espera a que el contenedor **arranque**, no a que
PostgreSQL esté **listo para aceptar conexiones**. El `healthcheck` con
`pg_isready` cubre ese hueco: sin él, la API podría intentar conectar antes de
que la base acepte peticiones y fallar de forma intermitente.

### 5.5 El esquema se crea en `init.sql`, pero el notebook podrá recrearlo

La tabla `lecturas` se crea en la inicialización de PostgreSQL para que la API
sea funcional desde el primer arranque, **sin depender de que alguien haya
ejecutado antes el notebook**. Esto además hace que el `GET /health` sea
significativo desde el principio.

> ⚠️ **Consecuencia importante:** el entrypoint solo ejecuta
> `/docker-entrypoint-initdb.d/` cuando el volumen de datos está **vacío**. Si
> se modifica `db/init.sql` con un volumen ya existente, el cambio **no se
> aplica**. Para reaplicarlo hay que borrar el volumen con
> `docker compose down -v`, lo que elimina los datos.

Esta decisión **no limita** al Reto B: el notebook puede usar
`if_exists="replace"` o `"append"` sobre la misma tabla, tal como se vio en
clase.

### 5.6 `COPY --chown=jovyan:users` en la imagen de Jupyter

Este detalle costó un fallo de build y conviene documentarlo:

- La imagen base de Jupyter **no ejecuta los comandos como root**, sino como el
  usuario `jovyan`.
- La instrucción `COPY` **conserva los permisos del fichero original** en el
  host. Un `requirements.txt` con modo `600` llegaba a la imagen como
  `600 root:root` e `pip` no podía leerlo → `Permission denied`.
- Añadir `--chown=jovyan:users` cede la propiedad del fichero al usuario que
  ejecuta `pip`, de modo que el build funciona **independientemente del modo
  con que esté el fichero en cada máquina**.

Este es un buen ejemplo de fallo que solo aparece en algunas máquinas: es
exactamente el tipo de problema que Docker pretende eliminar.

---

## 6. Problemas encontrados y solución

| Problema | Causa | Solución aplicada |
|---|---|---|
| `pip install` fallaba con `Permission denied: '/tmp/requirements.txt'` | `COPY` conservó el modo `600` del fichero en el host y la imagen base ejecuta como `jovyan`, no como root | `COPY --chown=jovyan:users` |
| `chmod` fallaba con `Operation not permitted` | El `RUN` se ejecuta como `jovyan`, que no es propietario de un fichero copiado como `root` | Se sustituyó por `--chown` en el `COPY` |
| `COPY failed: stat datos: file does not exist` | El contexto de build era `./jupyter` y `datos/` está en la raíz | Contexto movido a la raíz del repositorio |
| `COPY failed: stat api/requirements.txt` | El `.dockerignore` de la raíz excluía `api/`, que sí se necesita al usar la raíz como contexto | Eliminada esa exclusión |
| Puerto 5000 ocupado en macOS | Lo usa el «Receptor de AirPlay» del sistema | Documentado en `.env.example`; se usa `API_PORT` |
| Fechas y números poco útiles en el JSON | psycopg2 serializa `datetime` en formato de cabecera HTTP y `Decimal` como cadena | Normalización a ISO 8601 y a `float` antes de responder |

---

## 7. Siguientes pasos

### 7.1 Reto B · Carga, almacenamiento y análisis (siguiente tarea)

El responsable de esta parte debe crear el notebook en `notebooks/`. Debe:

1. Leer `sensores.csv` con `pd.read_csv`, revisar columnas y tipos, y preparar
   los datos. **Atención:** la columna `fecha_hora` se lee como texto y hay que
   convertirla a fecha-hora antes de escribir en la base de datos.
2. Crear una conexión con SQLAlchemy y cargar las lecturas en la tabla
   `lecturas` de PostgreSQL, que **ya existe** (creada por `db/init.sql`).
3. **Reutilizar la misma lógica para SQLite cambiando solo el engine o la URI.**
   El enunciado y la rúbrica insisten en *«sin duplicar la lógica»*: conviene
   encapsular la carga y la consulta en funciones cuyo único parámetro variable
   sea el `engine`.
4. Mostrar cuántos registros se han cargado en cada motor y obtener:
   - temperatura media por edificio
   - edificio con mayor CO₂ medio

**Datos de referencia del CSV** (para contrastar los resultados):

- 192 filas, 4 edificios (A, B, C, D) × 48 lecturas cada uno.
- Sin valores ausentes ni duplicados. Rango: 2026-10-14 08:00 → 19:45.
- Temperatura media por edificio: A = 22.62 °C · B = 23.68 °C · C = 24.44 °C · D = 23.08 °C
- CO₂ medio por edificio: A = 822.4 · B = 1002.9 · C = 1202.4 · **D = 1349.3 ppm** ← el mayor

**URI de conexión para el notebook:**

```
postgresql+psycopg2://smartcampus:smartcampus_dev@db:5432/smartcampus
```

**URI para SQLite** (mismo código, distinto engine):

```
sqlite:////home/jovyan/work/data/smartcampus.db
```

### 7.2 Reto C · Ampliaciones pendientes de la API

La versión actual cubre el mínimo obligatorio. Queda por decidir si se amplía:

- `GET /resumen` (bonus 01) · filtros en `GET /lecturas` (bonus 02) ·
  `GET /alertas?umbral=` (bonus 03) · validación avanzada del POST (bonus 04) ·
  pruebas automáticas (bonus 05).

### 7.3 Reto D · Prueba de integración

Debe hacerse **desde el notebook**, con `requests`, contra el servicio `api`.
El flujo es: contar filas en PostgreSQL → enviar `POST /lecturas` con una
medición reconocible → comprobar el código de respuesta → verificar con
SQLAlchemy que la lectura está en la base de datos.

### 7.4 Entrega

- [ ] Capturas de las cuatro evidencias obligatorias en `evidencias/`
- [ ] `README.md` propio siguiendo `03_Plantillas/Plantilla_README_del_repositorio.md`
- [ ] Memoria de uso de IA con **todas** las capturas de prompts, incluidos los
      que no funcionaron, o declaración expresa de no uso
- [ ] Revisar que no se sube ninguna credencial real

---

## 8. Nota sobre el uso de IA

Esta práctica es de **nivel AMARILLO**: la IA está permitida, pero exige
trazabilidad completa y validación propia.

Todo el trabajo de infraestructura recogido en este documento ha sido
**ejecutado y verificado** sobre Docker real, no solo escrito: los resultados de
la tabla del apartado 4 son salidas obtenidas en ejecución, no ejemplos
teóricos.

**Pendiente:** recopilar las capturas de pantalla de todos los prompts
utilizados durante el desarrollo, en orden cronológico, e incorporarlas a la
memoria de IA del apartado 07 del enunciado. Se deben incluir también los
prompts que no sirvieron y las correcciones aplicadas.

---

*Documento de trabajo interno del equipo. No sustituye al enunciado oficial,
que prevalece sobre cualquier indicación recogida aquí.*
