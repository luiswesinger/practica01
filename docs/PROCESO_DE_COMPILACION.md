# SmartCampus · Proceso de compilación e infraestructura

**Asignatura:** Proyecto Big Data I · Taller evaluable 01
**Ámbito de este documento:** Reto A (infraestructura). Describe **cómo se
construyen las imágenes, en qué orden y por qué**, y deja constancia de que los
Dockerfiles siguen el patrón trabajado en clase.
**Última actualización:** 14 de octubre de 2026

---

## 1. Idea previa: build no es lo mismo que runtime

Todo este documento gira alrededor de una distinción que la asignatura repite
constantemente y que conviene tener clara antes de leer nada más:

| Momento | Qué ocurre | Qué produce |
|---|---|---|
| **BUILD** (`docker compose build`) | Se ejecutan las instrucciones del Dockerfile: `FROM`, `COPY`, `RUN`, `WORKDIR`, `EXPOSE` | Una **imagen** (plantilla de solo lectura) |
| **RUNTIME** (`docker compose up`) | Se crea un **contenedor** a partir de la imagen y se arranca su proceso | Un **contenedor** en ejecución |

Consecuencias prácticas en este proyecto:

- `RUN pip install` pertenece al **build**: las dependencias quedan dentro de la
  imagen y el contenedor arranca ya listo, sin `pip install` manual.
- `COPY db/init.sql` pertenece al **build** y **solo copia el fichero, no lo
  ejecuta**. El SQL se ejecuta en el **runtime**, cuando el entrypoint oficial
  de PostgreSQL detecta que el directorio de datos está vacío.
- Por eso `EXPOSE` no publica nada: solo documenta el puerto. La publicación
  real se decide en `docker-compose.yml` con `ports:`.

---

## 2. Correspondencia con los ejemplos de la asignatura

Los Dockerfiles de este proyecto siguen los ejemplos canónicos vistos en clase.
Esta tabla deja constancia de la correspondencia y de las diferencias, todas
ellas deliberadas y justificadas.

### 2.1 Dockerfile de Jupyter

**Ejemplo de la asignatura** (guía *Dockerfile: Jupyter + PostgreSQL*, pág. 5):

```dockerfile
FROM jupyter/minimal-notebook:latest
WORKDIR /home/jovyan/work
COPY --chown=jovyan:users requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=jovyan:users datos/ ./datos/
COPY --chown=jovyan:users train_model.py ./train_model.py
RUN python train_model.py
COPY --chown=jovyan:users notebooks/ ./notebooks/
EXPOSE 8888
```

**Implementación en este proyecto** (`jupyter/Dockerfile`):

```dockerfile
FROM quay.io/jupyter/minimal-notebook:latest
COPY --chown=jovyan:users jupyter/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY --chown=jovyan:users datos /home/jovyan/datos
WORKDIR /home/jovyan/work
EXPOSE 8888
```

| Elemento | Ejemplo de clase | Este proyecto | ¿Coincide? |
|---|---|---|---|
| Imagen base | `jupyter/minimal-notebook:latest` | `quay.io/jupyter/minimal-notebook:latest` | ✅ Es la misma imagen; se usa la ruta completa de `quay.io`, que es la que emplean los materiales del módulo 1 y la que funciona de forma fiable en Apple Silicon y en arquitecturas `amd64` |
| `WORKDIR /home/jovyan/work` | Presente | Presente | ✅ Mismo directorio (`/home/jovyan/work`) |
| `COPY` de `requirements.txt` | A `./requirements.txt` | A `/tmp/requirements.txt` | 🟡 Misma instrucción, distinto destino. Se copia a `/tmp` para que el fichero **no acabe dentro del espacio de trabajo montado** desde el host y no aparezca como ruido en Jupyter |
| `RUN pip install --no-cache-dir -r …` | Presente | Presente | ✅ Idéntico, incluido `--no-cache-dir` |
| `COPY --chown=jovyan:users` | Presente | Presente | ✅ Se respeta la cesión de propiedad, que además evita un fallo real de build (véase el apartado 6.1) |
<<<<<<< HEAD
| `COPY` de los datos | `datos/` → `./datos/` | `datos` → `/home/jovyan/datos` | 🟡 Misma idea. Se copia **fuera** de `/home/jovyan/work` a propósito: así los datos vienen siempre de la imagen y no del bind mount |
=======
| `COPY` de los datos | `datos/` → `./datos/` | `datos` → `/home/jovyan/datos` | 🟡 Misma idea. Se copia **fuera** de `/home/jovyan/work` a propósito: así los datos provienen siempre de la imagen y no del directorio de notebooks montado desde el host |
>>>>>>> 8b2b0b98cd6283ba28341bb39ba1ed52204fd55a
| `EXPOSE 8888` | Presente | Presente | ✅ Idéntico |
| `RUN python train_model.py` | Presente (entrenaba un modelo en el build) | **No aplica** | ⚪ Ese ejemplo pertenecía al taller de Dockerfile, que generaba un artefacto de Machine Learning durante el build. SmartCampus no requiere ningún modelo |

### 2.2 Dockerfile de PostgreSQL

**Ejemplo de la asignatura** (misma guía, pág. 11):

```dockerfile
FROM postgres:16
COPY init.sql /opt/sql/init.sql
COPY init-db.sh /docker-entrypoint-initdb.d/01-init-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/01-init-db.sh
EXPOSE 5432
```

**Implementación en este proyecto** (`db/Dockerfile`):

```dockerfile
FROM postgres:16-alpine
COPY db/init.sql /docker-entrypoint-initdb.d/01-init.sql
EXPOSE 5432
```

| Elemento | Ejemplo de clase | Este proyecto | ¿Coincide? |
|---|---|---|---|
| Imagen base | `postgres:16` | `postgres:16-alpine` | 🟡 **Misma versión mayor (16)**. La variante `alpine` pesa unos 411 MB frente a 663 MB y no necesita herramientas extra |
| `COPY` a `/docker-entrypoint-initdb.d/` | Presente | Presente | ✅ Mismo mecanismo: es la carpeta que el entrypoint oficial ejecuta **solo** cuando inicializa un volumen vacío |
| Prefijo numérico `01-` | `01-init-db.sh` | `01-init.sql` | ✅ Se conserva el prefijo para fijar el orden si se añaden más scripts |
| `RUN chmod +x` | Presente | **No necesario** | ⚪ El ejemplo lo usaba porque copiaba un script **de shell** que debía ser ejecutable. Aquí se copia un `.sql`, que PostgreSQL lee, no ejecuta |
| `EXPOSE 5432` | Presente | Presente | ✅ Idéntico |

<<<<<<< HEAD
> **Cambio aplicado.** La primera versión de este proyecto montaba `db/init.sql`
> con un bind mount desde `docker-compose.yml`, en lugar de copiarlo en una
> imagen propia. El enunciado lo permitía (*«los Dockerfile o archivos de
> configuración necesarios»*), pero se ha alineado con el ejemplo de clase para
> que no haya duda: **el esquema inicial forma parte de la imagen** y no depende
> de que exista una ruta concreta en el equipo de cada compañero.
=======
**El esquema inicial viaja con la imagen.** El enunciado admite *«los Dockerfile
o archivos de configuración necesarios»*; al copiar `db/init.sql` en una imagen
propia, el esquema **forma parte de la imagen** y no depende de que exista una
ruta concreta en el equipo de cada compañero. La imagen queda autocontenida: se
puede reconstruir en cualquier máquina y, si se publicara en un registro, quien
la descargue obtiene exactamente el mismo esquema.
>>>>>>> 8b2b0b98cd6283ba28341bb39ba1ed52204fd55a

### 2.3 Dockerfile de la API

La asignatura **no incluye un ejemplo de imagen Flask**; el patrón que sí
aparece en el material es el de un Dockerfile genérico de aplicación Python
(deck *Containers and Docker*, pág. 19):

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY etl.py .
CMD ["python", "etl.py"]
```

**Implementación en este proyecto** (`api/Dockerfile`):

```dockerfile
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/app.py .
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
```

| Elemento | Patrón del material | Este proyecto | ¿Coincide? |
|---|---|---|---|
| Imagen base | `python:3.13-slim` | `python:3.13-slim` | ✅ Idéntica |
| `WORKDIR /app` | Presente | Presente | ✅ Idéntico |
| Orden `COPY requirements` → `RUN pip install` → `COPY código` | Presente | Presente | ✅ **Es el orden que aprovecha la caché de capas**: un cambio en el código no obliga a reinstalar dependencias |
| `--no-cache-dir` | Presente | Presente | ✅ Idéntico |
| Forma exec del `CMD` | `CMD ["python", "etl.py"]` | `CMD ["flask", …]` | ✅ Se usa la **forma exec JSON**, que es la recomendada para el manejo de señales |
| `ENV PYTHONDONTWRITEBYTECODE / PYTHONUNBUFFERED` | No aparece | Añadido | ⚪ Mejora: evita ficheros `.pyc` y hace que los logs de Flask salgan en tiempo real por `docker compose logs` |
| `EXPOSE 5000` | No aparece | Añadido | ✅ Documenta el puerto (Flask escucha en 5000) |

### 2.4 `requirements.txt`

El ejemplo de clase (guía del taller, pág. 3) fija versiones con intervalos:

```
pandas>=2.2,<3
SQLAlchemy>=2.0,<3
psycopg2-binary>=2.9,<3
```

Este proyecto sigue el mismo criterio de **fijar el rango** para evitar saltos
de versión mayor que rompan la reproducibilidad:

| Fichero | Contenido | Motivo frente al ejemplo |
|---|---|---|
| `jupyter/requirements.txt` | `pandas>=2.2,<3` · `numpy>=1.26,<3` · `SQLAlchemy>=2.0,<3` · `psycopg2-binary>=2.9,<3` · `requests>=2.32,<3` | Se añaden **numpy** y **requests**. El enunciado exige que Jupyter disponga de `requests` para la prueba de integración del Reto D, y numpy lo usa pandas |
| `api/requirements.txt` | `Flask>=3.0,<4` · `psycopg2-binary>=2.9,<3` | Se añade Flask, que el ejemplo del taller no necesitaba |

### 2.5 `.dockerignore`

El ejemplo de clase (guía del taller, pág. 6) excluye:

```
__pycache__/
*.pyc
.ipynb_checkpoints/
modelo_clientes.joblib
```

Este proyecto mantiene los tres primeros y añade el resto de ruido habitual
(metadatos del sistema, logs, entorno virtual, `.env`). La última línea del
ejemplo —excluir un artefacto generado durante el build— no aplica aquí.

---

## 3. Contexto de build: por qué es la raíz del repositorio

Los tres servicios construyen con **la raíz del repositorio como contexto**:

```yaml
db:      { context: ., dockerfile: db/Dockerfile }
api:     { context: ., dockerfile: api/Dockerfile }
jupyter: { context: ., dockerfile: jupyter/Dockerfile }
```

**Motivo:** el Dockerfile de Jupyter necesita copiar `datos/`, y el de la base de
datos necesita copiar `db/init.sql`. Ambas rutas están **fuera** de sus propias
carpetas, así que un contexto reducido a `./jupyter` o `./db` no las vería y el
build fallaría con `file not found in build context`.

**Contrapartida y cómo se controla:** un contexto en la raíz enviaría al daemon
todo el repositorio. Se evita con el `.dockerignore` de la raíz, que excluye el
enunciado, las plantillas, los ejemplos de pruebas, las evidencias y los
ficheros auxiliares. El contexto real que se envía es de **~29 kB**.

> Consecuencia sobre las rutas: como el contexto es la raíz, **las rutas de
> `COPY` son relativas a la raíz**, no a la carpeta del Dockerfile. Por eso se
> escribe `COPY api/app.py .` y no `COPY app.py .`.

---

## 4. El proceso de compilación, paso a paso

### 4.1 Comando único

```bash
docker compose up --build
```

Este comando hace, en este orden: **construir las tres imágenes → crear la red
y el volumen → arrancar los contenedores respetando las dependencias**.

### 4.2 Qué ocurre en cada imagen

**`practica01-db`** — la más rápida (2 instrucciones):

```
FROM postgres:16-alpine                              ← descarga la base (~411 MB)
COPY db/init.sql /docker-entrypoint-initdb.d/01-init.sql
EXPOSE 5432
```

No hay `RUN`: no se instala nada. El SQL **no se ejecuta aquí**.

**`practica01-api`** — imagen ligera (~232 MB):

```
FROM python:3.13-slim
ENV …                                                ← variables de Python
WORKDIR /app
COPY api/requirements.txt .                          ← primero las dependencias
RUN pip install --no-cache-dir -r requirements.txt   ← Flask + psycopg2-binary
COPY api/app.py .                                    ← después el código
EXPOSE 5000
CMD ["flask", …]
```

**`practica01-jupyter`** — la más pesada (~2,75 GB, casi toda la base):

```
FROM quay.io/jupyter/minimal-notebook:latest
COPY --chown=jovyan:users jupyter/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt   ← pandas, numpy, SQLAlchemy, psycopg2, requests
COPY --chown=jovyan:users datos /home/jovyan/datos        ← el CSV viaja en la imagen
WORKDIR /home/jovyan/work
EXPOSE 8888
```

### 4.3 Caché de capas: por qué el orden importa

Cada instrucción crea una **capa**. Docker reutiliza las capas cuya instrucción
y ficheros de entrada no han cambiado. Si una capa cambia, **se reconstruyen esa
y todas las siguientes**.

De ahí el orden elegido en las dos imágenes con dependencias:

```
COPY requirements.txt   ← capa 1
RUN pip install …       ← capa 2 (la cara: tarda minutos)
COPY código             ← capa 3 (la barata: cambia a menudo)
```

Si se copiara antes el código, **cualquier retoque en `app.py` invalidaría la
capa de `pip install`** y habría que reinstalar todo en cada build. Con este
orden, un cambio de código solo reconstruye la última capa, que es instantánea.

**Comprobación práctica:** ejecutar `docker compose build` dos veces seguidas.
La segunda debe terminar en segundos y mostrar `Using cache` en casi todas las
instrucciones.

### 4.4 Arranque: el orden lo decide `depends_on` + `healthcheck`

```yaml
api:
  depends_on:
    db:
      condition: service_healthy
```

`depends_on` por sí solo espera a que el contenedor **arranque**, no a que
PostgreSQL esté **listo para aceptar conexiones**. El `healthcheck` con
`pg_isready` cubre ese hueco: sin él, la API podría intentar conectar antes de
que la base acepte peticiones y fallar de forma intermitente.

Secuencia real observada al arrancar:

```
db       → Starting → Waiting → Healthy
api      → (espera)  →         → Starting → Started
jupyter  → (espera)  →         → Starting → Started
```

### 4.5 Runtime de la base de datos: cuándo se crea la tabla

La tabla `lecturas` **no** se crea durante el build. Se crea cuando el
contenedor de PostgreSQL arranca y encuentra el directorio de datos **vacío**;
entonces el entrypoint oficial recorre `/docker-entrypoint-initdb.d/` y ejecuta
`01-init.sql`.

```
docker compose up
      ↓
contenedor db arranca
      ↓
¿/var/lib/postgresql/data está vacío?
      ├── SÍ  → ejecuta /docker-entrypoint-initdb.d/01-init.sql → crea 'lecturas'
      └── NO  → no ejecuta nada (los datos ya existen)
```

> ⚠️ **Consecuencia importante.** Si se modifica `db/init.sql` con un volumen ya
> creado, el cambio **no se aplica**, porque el directorio de datos ya no está
> vacío. Para reaplicarlo hay que borrar el volumen:
>
> ```bash
> docker compose down -v      # ⚠️ elimina también los datos guardados
> docker compose up --build
> ```

---

## 5. Verificación de la compilación

### 5.1 Comprobar que las imágenes se construyeron

```bash
docker images | grep practica01
```

Resultado esperado:

```
practica01-db        latest    ~411 MB
practica01-api       latest    ~232 MB
practica01-jupyter   latest    ~2,75 GB
```

### 5.2 Comprobar que las dependencias están dentro de la imagen

Esta es la comprobación que demuestra que **el build hizo su trabajo** y que el
contenedor no necesita instalar nada al arrancar:

```bash
docker run --rm --entrypoint python practica01-jupyter:latest -c \
  "import pandas, sqlalchemy, psycopg2, requests; print('dependencias OK')"

docker run --rm --entrypoint python practica01-api:latest -c \
  "import flask, psycopg2; print('dependencias OK')"
```

### 5.3 Comprobar que el CSV viaja dentro de la imagen

```bash
docker run --rm --entrypoint bash practica01-jupyter:latest -c \
  "ls -l /home/jovyan/datos && wc -l < /home/jovyan/datos/sensores.csv"
```

Resultado esperado: `sensores.csv` propiedad de `jovyan:users` y **193 líneas**
(192 lecturas + cabecera).

### 5.4 Comprobar que el esquema se crea en el runtime

```bash
docker compose exec db psql -U smartcampus -d smartcampus -c '\d lecturas'
```

Resultado esperado: la tabla con sus 6 columnas, la clave primaria y los dos
índices (`idx_lecturas_edificio`, `idx_lecturas_fecha_hora`).

### 5.5 Resultados obtenidos

| Comprobación | Resultado |
|---|---|
| Las tres imágenes se construyen | ✅ |
| `docker compose ps`: tres servicios activos | ✅ `db` y `jupyter` en estado `healthy` |
| Dependencias presentes en la imagen de Jupyter | ✅ pandas 2.3.3 · numpy 2.5.4 · SQLAlchemy 2.1.4 · psycopg2 2.9.13 · requests 2.34.2 |
| Dependencias presentes en la imagen de la API | ✅ Flask 3.1.3 · psycopg2 2.9.13 |
| CSV dentro de la imagen | ✅ `/home/jovyan/datos/sensores.csv`, 193 líneas |
| `init.sql` ejecutado en el runtime sobre volumen nuevo | ✅ tabla `lecturas` + 2 índices |
| `GET /health` | ✅ `200 {"status":"ok","database":"ok"}` |
| `POST /lecturas` | ✅ `201` y registro persistido |
| `POST /lecturas` sin un campo obligatorio | ✅ `400` con la lista de campos ausentes |
| Persistencia tras `docker compose restart` | ✅ los registros siguen presentes |

---

## 6. Incidencias reales durante la compilación

Se documentan porque son fallos que **solo aparecen en algunas máquinas**, que
es exactamente el problema que Docker pretende eliminar, y porque cualquier
miembro del equipo debe poder explicarlos.

### 6.1 `Permission denied: '/tmp/requirements.txt'`

**Síntoma.** El build de Jupyter fallaba en el `RUN pip install` con
`ERROR: Could not open requirements file: [Errno 13] Permission denied`.

**Causa.** Dos hechos que se combinan:

1. La imagen base de Jupyter **no ejecuta los comandos como `root`**, sino como
   el usuario `jovyan` (uid 1000).
2. La instrucción `COPY` **conserva los permisos del fichero original** en el
   host. El `requirements.txt` de esa máquina tenía modo `600`, de modo que
   llegaba a la imagen como `600 root:root` y `pip` no podía leerlo.

**Primer intento, fallido.** Añadir `RUN chmod 0644 /tmp/requirements.txt`
tampoco funcionó: devolvía `Operation not permitted`, porque el `RUN` también se
ejecuta como `jovyan` y `jovyan` no es el propietario de un fichero copiado como
`root`.

**Solución.** Ceder la propiedad en el propio `COPY`:

```dockerfile
COPY --chown=jovyan:users jupyter/requirements.txt /tmp/requirements.txt
```

Así el fichero es legible por quien ejecuta `pip`, **con independencia del modo
con que esté en cada máquina**. Es la misma instrucción que usa el ejemplo de
clase, y esta incidencia explica *por qué* el ejemplo la incluye.

### 6.2 `COPY failed: file not found in build context`

**Síntoma.** `stat datos: file does not exist` al construir Jupyter.

**Causa.** El contexto de build era `./jupyter`, y `datos/` está en la raíz del
repositorio. Docker solo puede copiar ficheros que estén **dentro del contexto**.

**Solución.** Mover el contexto a la raíz del repositorio y ajustar las rutas de
`COPY` (apartado 3).

### 6.3 `COPY failed: stat api/requirements.txt`

**Síntoma.** Al construir la API con el contexto ya en la raíz, el fichero
`api/requirements.txt` no se encontraba.

**Causa.** El `.dockerignore` de la raíz excluía la carpeta `api/` — una regla
que tenía sentido cuando la API se construía con su propio contexto `./api`,
pero que al pasar la raíz a ser el contexto **excluía justo lo que se quería
copiar**.

**Solución.** Eliminar esa exclusión del `.dockerignore`.

### 6.4 Fechas y números poco útiles en el JSON

**Síntoma.** `GET /lecturas` devolvía
`"fecha_hora": "Thu, 15 Oct 2026 12:34:56 GMT"` y `"temperatura": "23.70"`
(entre comillas).

**Causa.** No es un problema de Docker sino de serialización: `psycopg2`
devuelve los `TIMESTAMP` como `datetime` y los `NUMERIC` como `Decimal`, y la
conversión por defecto de Python a JSON produce una fecha en formato de cabecera
HTTP y números entrecomillados como cadenas.

**Solución.** Normalizar antes de responder, en `api/app.py`: fechas en ISO 8601
(`2026-10-15 12:34:56`) y números como números.

### 6.5 Puerto 5000 ocupado en macOS

**Síntoma.** El servicio `api` no arrancaba por puerto en uso.

**Causa.** En macOS el puerto 5000 lo ocupa el sistema: el «Receptor de AirPlay»
(Centro de Control).

**Solución.** Cambiar el puerto publicado, sin tocar el interno:

```env
API_PORT=5001
```

Documentado en `.env.example`. El puerto interno del contenedor sigue siendo
5000 y **no debe cambiarse**: es el que usa Flask dentro.

---

## 7. Referencia rápida

### 7.1 Comandos

```bash
# Construir todo y arrancar
docker compose up --build

# Construir sin arrancar
docker compose build

# Construir un solo servicio
docker compose build jupyter

# Construir sin usar la caché (build limpio)
docker compose build --no-cache

# Ver el estado de los tres servicios
docker compose ps

# Logs de un servicio
docker compose logs -f api

# Reconstruir y recrear un servicio concreto
docker compose up -d --build api

# Parar conservando los datos
docker compose down

# Parar y BORRAR los datos (fuerza la reejecución de init.sql)
docker compose down -v
```

### 7.2 Instrucciones empleadas

| Instrucción | Dónde | Qué hace |
|---|---|---|
| `FROM` | los tres Dockerfiles | Imagen base de la que se parte |
| `WORKDIR` | Jupyter, API | Directorio de trabajo para las instrucciones siguientes |
| `COPY` | los tres | Copia ficheros **del contexto de build** a la imagen (solo en el build) |
| `COPY --chown=usuario:grupo` | Jupyter | Copia y además cede la propiedad del fichero |
| `RUN` | Jupyter, API | Ejecuta un comando **durante el build** y genera una capa |
| `ENV` | API | Variable de entorno incluida en la imagen |
| `EXPOSE` | los tres | **Documenta** el puerto esperado; no lo publica |
| `CMD` | API | Proceso por defecto del contenedor (forma exec JSON) |
| `.dockerignore` | raíz, `api/`, `jupyter/` | Excluye ficheros del contexto de build |

### 7.3 Ruta de un fichero, de principio a fin

Ejemplo con el CSV, que ilustra build y runtime en una sola traza:

```
datos/sensores.csv                    (host, en el repositorio)
        │
        │  docker compose build   ← BUILD: COPY --chown=jovyan:users datos /home/jovyan/datos
        ▼
imagen practica01-jupyter
   └── /home/jovyan/datos/sensores.csv
        │
        │  docker compose up      ← RUNTIME: se crea el contenedor
        ▼
contenedor smartcampus_jupyter
   └── /home/jovyan/datos/sensores.csv   ← lo lee el notebook con pd.read_csv
```

Y el contraste con `init.sql`, que recorre un camino distinto:

```
db/init.sql                           (host)
        │
        │  docker compose build   ← BUILD: COPY … (solo copia, NO ejecuta)
        ▼
imagen practica01-db
   └── /docker-entrypoint-initdb.d/01-init.sql
        │
        │  docker compose up      ← RUNTIME: el entrypoint lo EJECUTA si el volumen está vacío
        ▼
contenedor smartcampus_db
   └── tabla 'lecturas' creada en el volumen postgres_data
```

---

*Documento de trabajo interno del equipo. El enunciado oficial prevalece sobre
cualquier indicación recogida aquí.*
