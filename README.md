# SmartCampus · Proyecto Big Data I

Prototipo de servicio de datos para consultar y registrar las lecturas de los
sensores ambientales de un campus universitario.

Tres servicios orquestados con **Docker Compose**: un entorno **Jupyter** para
el análisis, una base de datos **PostgreSQL** para el almacenamiento y una
**API Flask** para consultar y registrar lecturas desde otros sistemas.

> **Taller evaluable 01** · Proyecto Big Data I · Grado en Ciencia de Datos ·
> Universidad Europea de Valencia

---

## Índice

1. [Equipo y objetivo](#1-equipo-y-objetivo)
2. [Arquitectura y tecnologías](#2-arquitectura-y-tecnologías)
3. [Requisitos previos](#3-requisitos-previos)
4. [Preparación y puesta en marcha](#4-preparación-y-puesta-en-marcha)
5. [Notebook y análisis de datos](#5-notebook-y-análisis-de-datos)
6. [API y pruebas](#6-api-y-pruebas)
7. [Prueba de extremo a extremo](#7-prueba-de-extremo-a-extremo)
8. [Bonus opcionales](#8-bonus-opcionales)
9. [Evidencias](#9-evidencias)
10. [Uso de IA](#10-uso-de-ia)
11. [Parada y limpieza](#11-parada-y-limpieza)
12. [Problemas frecuentes](#12-problemas-frecuentes)

---

## 1. Equipo y objetivo

| | |
|---|---|
| **Integrantes** | Luis Wesinger · Yiao Tang |
| **Repositorio** | https://github.com/luiswesinger/practica01 |
| **Asignatura** | Proyecto Big Data I · Taller evaluable 01 |

**Objetivo.** Una empresa de gestión de edificios universitarios registra
mediciones ambientales en un fichero CSV y necesita dejar de depender de un
fichero aislado. Este prototipo permite:

- almacenar las lecturas en una base de datos relacional,
- analizarlas desde un notebook con pandas y SQLAlchemy,
- **cambiar de motor de base de datos** (PostgreSQL o SQLite) modificando
  únicamente la conexión, sin reescribir la lógica de análisis,
- y consultar o registrar lecturas nuevas a través de una API REST.

No incluye interfaz gráfica: no forma parte del encargo.

---

## 2. Arquitectura y tecnologías

### 2.1 Los tres servicios

```text
        EQUIPO ANFITRIÓN
        ┌──────────────────────────────────────────────┐
        │   :8888                      :5000           │
        │     │                          │             │
        └─────┼──────────────────────────┼─────────────┘
              │                          │
    ┌─────────▼─────────┐      ┌─────────▼─────────┐
    │  jupyter          │      │  api              │
    │  quay.io/jupyter/ │      │  python:3.13-slim │
    │  minimal-notebook │      │  Flask 3          │
    │  pandas           │      │  GET  /health     │
    │  SQLAlchemy       │      │  GET  /lecturas   │
    │  psycopg2         │      │  POST /lecturas   │
    │  requests         │      │                   │
    └─────────┬─────────┘      └─────────┬─────────┘
              │                          │
              │    red interna           │
              │   smartcampus_net        │
              └────────────┬─────────────┘
                           │  hostname: db
                  ┌────────▼─────────┐
                  │  db              │
                  │  postgres:16     │
                  │  tabla lecturas  │
                  │  volumen:        │
                  │  postgres_data   │
                  └──────────────────┘
```

| Servicio | Imagen | Contenedor | Puerto en el host | Publica |
|---|---|---|---|---|
| `db` | propia sobre `postgres:16-alpine` | `smartcampus_db` | — | ❌ No |
| `api` | propia sobre `python:3.13-slim` | `smartcampus_api` | `5000` | ✅ Sí |
| `jupyter` | propia sobre `quay.io/jupyter/minimal-notebook` | `smartcampus_jupyter` | `8888` | ✅ Sí |

### 2.2 Comunicación entre contenedores

Los tres servicios comparten la red `smartcampus_net`. **Cada servicio se
resuelve por su nombre**, no por una dirección IP:

```text
Jupyter  ──►  db:5432      (PostgreSQL)
Jupyter  ──►  api:5000     (API Flask)
API      ──►  db:5432      (PostgreSQL)
```

> ⚠️ **`localhost` no sirve para comunicar contenedores.** Dentro de un
> contenedor, `localhost` apunta a ese mismo contenedor, no a los demás. Por eso
> las cadenas de conexión usan `db` y `api`, que son los nombres de servicio
> definidos en `docker-compose.yml`.

**El puerto de PostgreSQL no se publica al equipo anfitrión.** Solo lo consumen
`api` y `jupyter` a través de la red interna. No publicarlo evita conflictos con
otros PostgreSQL ya instalados en la máquina. Para inspeccionar la base se usa
`docker compose exec db psql …` (véase el apartado 6.4).

### 2.3 Papel de cada componente

| Componente | Papel |
|---|---|
| **PostgreSQL** | Almacén principal. Contiene la tabla `lecturas` y sobrevive a los reinicios gracias al volumen `postgres_data`. |
| **SQLite** | **No es un servicio de Compose**: es una base de datos de fichero. Se usa para demostrar que la misma lógica sirve para otro motor. |
| **Flask** | Expone las lecturas y acepta lecturas nuevas mediante HTTP/JSON. Escribe en la misma tabla `lecturas`. |
| **Jupyter** | Entorno de análisis. Lee el CSV, carga en los dos motores, obtiene los análisis y ejecuta la prueba de integración de extremo a extremo. |

### 2.4 Estructura del repositorio

```text
practica01/
├── docker-compose.yml            los tres servicios, la red y el volumen
├── .env.example                  plantilla de variables de entorno
├── .dockerignore                 reduce el contexto de build
├── api/
│   ├── Dockerfile
│   ├── requirements.txt          Flask + psycopg2-binary
│   └── app.py                    los tres endpoints
├── db/
│   ├── Dockerfile                copia init.sql dentro de la imagen
│   └── init.sql                  esquema inicial de 'lecturas'
├── jupyter/
│   ├── Dockerfile
│   └── requirements.txt
├── datos/
│   └── sensores.csv              el CSV que se copia en la imagen
├── notebooks/
│   └── analyse_data.ipynb        Retos B y D
├── evidencias/                   capturas de la entrega
├── docs/                         documentación técnica del proyecto
└── README.md                     este fichero
```

---

## 3. Requisitos previos

### 3.1 Software necesario

| Requisito | Versión probada | Notas |
|---|---|---|
| Docker Engine o Docker Desktop | 29.1.2 | Debe estar **en ejecución** |
| Docker Compose | v2 (plugin `docker compose`) | Se usa la sintaxis `docker compose`, no `docker-compose` |
| Conexión a Internet | — | Solo para el primer arranque: hay que descargar las imágenes base (unos 3,2 GB) |

> **No hace falta instalar nada más en el equipo.** Ni Python, ni PostgreSQL,
> ni Jupyter: todo se ejecuta dentro de los contenedores.

### 3.2 Puertos utilizados

| Puerto | Servicio | ¿Se puede cambiar? |
|---|---|---|
| **8888** | Jupyter | Sí, con `JUPYTER_PORT` |
| **5000** | API Flask | Sí, con `API_PORT` |
| *5432* | *PostgreSQL* | **No se publica**, así que no puede entrar en conflicto |

Si alguno de esos puertos está ocupado, véase el apartado 4.3.

### 3.3 Variables de entorno

Todas tienen un valor por defecto en `docker-compose.yml`, de modo que el
proyecto **funciona sin crear ningún fichero**. Para personalizarlas se copia la
plantilla:

```bash
cp .env.example .env
```

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `POSTGRES_DB` | `smartcampus` | Nombre de la base de datos |
| `POSTGRES_USER` | `smartcampus` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | *(definido en `.env.example`)* | Contraseña de PostgreSQL |
| `JUPYTER_PORT` | `8888` | Puerto de Jupyter en el host |
| `API_PORT` | `5000` | Puerto de la API en el host |

> 🔒 El fichero `.env` está excluido por `.gitignore` y **nunca se sube al
> repositorio**. Las credenciales de este proyecto son deliberadamente simples
> porque el entorno es local y de prácticas. **No son credenciales reales.**

---

## 4. Preparación y puesta en marcha

### 4.1 Arrancar el entorno completo

```bash
git clone https://github.com/luiswesinger/practica01.git
cd practica01
docker compose up --build
```

**El primer arranque tarda entre 10 y 20 minutos** porque descarga las imágenes
base y instala las dependencias de Python durante el build. Los arranques
posteriores son mucho más rápidos, ya que Docker reutiliza las capas en caché.

Cuando termine, debe verse algo así:

```text
 Container smartcampus_db  Healthy
 Container smartcampus_api  Started
 Container smartcampus_jupyter  Started
```

> 💡 Para dejarlo corriendo en segundo plano y recuperar el control de la
> terminal, añádase `-d`: `docker compose up -d --build`.

### 4.2 Comprobar que los tres servicios están activos

```bash
docker compose ps
```

Resultado esperado (los puertos publicados son los de vuestro `.env`; aquí se
muestra la ejecución verificada, con `API_PORT=5001` y `JUPYTER_PORT=8889`):

```text
NAME                  SERVICE   STATUS                        PORTS
smartcampus_api       api       Up                            0.0.0.0:5001->5000/tcp
smartcampus_db        db        Up (healthy)                  5432/tcp
smartcampus_jupyter   jupyter   Up (healthy)                  0.0.0.0:8889->8888/tcp
```

Qué hay que comprobar en esa salida:

- **Los tres servicios aparecen**, y ninguno figura como `Exited` ni `Restarting`.
- **`db` figura como `(healthy)`**: su `healthcheck` con `pg_isready` pasa.
- **`db` muestra solo `5432/tcp`**, sin mapeo al equipo anfitrión. Es deliberado:
  la base de datos no se publica y solo la consumen `api` y `jupyter` por la red
  interna de Compose.
- **`api` no tiene columna de estado de salud** porque no define `healthcheck`
  propio. Eso no significa que esté mal: se comprueba con `GET /health`, que sí
  consulta la base de datos (véase el apartado 6).

> 💡 Los nombres de las columnas pueden variar ligeramente entre versiones de
> Compose. Lo importante es el **estado** de cada servicio y los **puertos**
> publicados, no el formato exacto de la tabla.

### 4.3 Si un puerto está ocupado

**En macOS el puerto 5000 suele estar ocupado por el sistema**: lo usa el
«Receptor de AirPlay» (Centro de Control). Hay dos salidas:

**Opción A — cambiar el puerto publicado.** Cópiese la plantilla y edítese:

```bash
cp .env.example .env
```

```env
JUPYTER_PORT=8889
API_PORT=5001
```

> ⚠️ **Cambiad solo el lado izquierdo** del mapeo. El puerto de la derecha es el
> que usa el proceso **dentro** del contenedor (8888 para Jupyter, 5000 para
> Flask) y no debe modificarse.

**Opción B — liberar el puerto.** En macOS: *Ajustes del Sistema → General →
AirPlay y Handoff* → desactivar el receptor de AirPlay.

### 4.4 Abrir Jupyter

```text
http://localhost:8888
```

**No se pide token ni contraseña.** El servidor arranca con
`--ServerApp.token=''` y `--ServerApp.password=''`, de modo que cualquiera que
llegue al puerto entra directamente en el entorno.

> ⚠️ **Aviso de seguridad.** Los puertos se publican sobre **todas las
> interfaces de red** (`0.0.0.0`), no solo sobre `127.0.0.1`. En la práctica
> esto significa que **cualquier equipo de la misma red puede abrir Jupyter y
> leer o modificar los notebooks sin autenticarse**, y puede consultar la API.
>
> Esto es aceptable en el contexto del taller —entorno local de prácticas, sin
> datos personales— pero conviene saberlo:
>
> - **No lo dejéis levantado en redes públicas** (una wifi de biblioteca, un
>   aeropuerto, una red compartida).
> - Para restringirlo a la máquina local, añadid `127.0.0.1:` delante del
>   puerto en el `docker-compose.yml`:
>
>   ```yaml
>   ports:
>     - "127.0.0.1:${JUPYTER_PORT:-8888}:8888"   # solo el equipo local
>     - "127.0.0.1:${API_PORT:-5000}:5000"
>   ```
>
>   ⚠️ Con ese cambio, **otros equipos de la red ya no podrán acceder** a
>   Jupyter ni a la API. Es justo lo contrario de lo que hace falta si alguien
>   del grupo quiere probar el entorno desde su propia máquina.

> 💡 **Sobre el estado `(healthy)` de Jupyter.** El `docker-compose.yml` no le
> define un `healthcheck` propio: el que aparece proviene de la imagen base
> (`/etc/jupyter/docker_healthcheck.py`). Funciona, pero es una dependencia
> implícita del tag `latest` de la imagen. Si algún día se fija la imagen por
> versión o por digest, conviene declarar el `healthcheck` de forma explícita.

---

## 5. Notebook y análisis de datos

El notebook está en **`notebooks/analyse_data.ipynb`**.

> 📌 La carpeta `notebooks/` está **montada** dentro del contenedor en
> `/home/jovyan/work`. Todo lo que se edite ahí se guarda directamente en el
> equipo anfitrión: no hay que copiar ni reconstruir nada.

### 5.1 Cómo ejecutarlo

Abrir el notebook en Jupyter y ejecutar **las celdas en orden, de arriba abajo**
(*Kernel → Restart Kernel and Run All Cells*). No requiere ningún paso manual
previo: las dependencias ya están instaladas en la imagen.

El notebook tarda unos pocos segundos. Es **repetible**: puede ejecutarse varias
veces sin acumular datos duplicados.

### 5.2 El fichero de datos

`sensores.csv` contiene **192 lecturas** de 4 edificios (A, B, C y D), 48 por
edificio, tomadas cada 15 minutos a lo largo de una jornada.

| Columna | Significado | Tipo |
|---|---|---|
| `edificio` | Identificador del edificio | Texto |
| `fecha_hora` | Instante de la lectura | Fecha y hora |
| `temperatura` | Temperatura ambiente | Numérico, °C |
| `humedad` | Humedad relativa | Numérico, % |
| `co2_ppm` | Concentración de CO₂ | Entero, ppm |

Dentro del contenedor el CSV está en **`/home/jovyan/datos/sensores.csv`**. Viaja
**dentro de la imagen** (se copia en el build), de modo que el notebook no
depende de lo que haya en el equipo de cada persona.

### 5.3 Qué hace el notebook

1. Lee el CSV con pandas y convierte `fecha_hora` a tipo fecha.
2. Comprueba la calidad de los datos: valores ausentes, duplicados y rangos.
3. Crea el engine de SQLAlchemy y carga las lecturas en PostgreSQL.
4. Obtiene los dos análisis obligatorios:
   - **temperatura media por edificio**, agregando en SQL (`GROUP BY` + `AVG`),
   - **edificio con mayor CO₂ medio**, agregando en pandas.
5. Repite la carga y el análisis **en SQLite**, cambiando solo el engine.
6. Ejecuta la función común `cargar_y_resumir(engine, data)` contra **los dos
   motores** y comprueba que los resultados coinciden.
7. Ejecuta la prueba de integración de extremo a extremo (apartado 7).

### 5.4 El punto clave: una sola lógica para dos motores

El requisito central del taller es **no duplicar la lógica**. Todo el flujo está
encapsulado en **una única función** cuyo único elemento variable es el engine:

```python
def cargar_y_resumir(engine, data: pd.DataFrame) -> dict:
    """Función agnóstica del fabricante de la base de datos."""
    ...
```

**Dentro de esa función no hay ninguna bifurcación según el motor**: no existe
un `if` que pregunte si se trata de PostgreSQL o de SQLite. Se limita a recibir
un engine y trabajar. Esa es la diferencia entre los dos fragmentos siguientes:

```python
# ❌ Lógica duplicada: un bloque para cada motor
pg_engine = create_engine(PG_URI)
df.to_sql("lecturas", pg_engine, if_exists="append", index=False)
resumen_pg = pd.read_sql("SELECT ...", pg_engine)

sqlite_engine = create_engine(SQLITE_URI)
df.to_sql("lecturas", sqlite_engine, if_exists="append", index=False)   # repetido
resumen_sqlite = pd.read_sql("SELECT ...", sqlite_engine)               # repetido

# ✅ Una sola función, invocada dos veces
res_pg     = cargar_y_resumir(pg_engine,     df)
res_sqlite = cargar_y_resumir(sqlite_engine, df)
```

### 5.5 Resultados que deben obtenerse

| Edificio | Temperatura media | CO₂ medio |
|---|---|---|
| A | 22,63 °C | 822,4 ppm |
| B | 23,68 °C | 1002,9 ppm |
| **C** | **24,44 °C** ← la más alta | 1202,4 ppm |
| **D** | 23,08 °C | **1349,3 ppm** ← el más alto |

- **Temperatura media por edificio:** el C es el más cálido y el A el más frío.
- **Edificio con mayor CO₂ medio:** el **D**, con 1349,3 ppm.

> 📎 **Nota sobre el edificio A.** Su media exacta es 22,625, justo en la mitad
> de una centésima. PostgreSQL (`ROUND` sobre `numeric`) redondea a **22,63**,
> mientras que `round()` de Python y pandas aplican redondeo bancario y dan
> **22,62**. La diferencia de 0,01 es una diferencia de **regla de redondeo**,
> no un error de cálculo. Los otros tres edificios no caen en ese punto exacto.

Al final, el notebook muestra que **los dos motores devuelven exactamente los
mismos resultados** y cuenta los registros cargados en cada uno.

---

## 6. API y pruebas

La API está implementada en `api/app.py` y escucha en el puerto **5000** dentro
de la red de Compose (publicado en el host según `API_PORT`).

### 6.1 Endpoints

| Método y ruta | Qué hace | Respuesta |
|---|---|---|
| `GET /health` | Comprueba que el servicio responde **y** que puede acceder a la base de datos | `200` si todo va bien · `503` si la base no responde |
| `GET /lecturas` | Devuelve las lecturas almacenadas, leídas de PostgreSQL | `200` + colección JSON |
| `POST /lecturas` | Recibe una lectura en JSON y la guarda en PostgreSQL | `201` + confirmación · `400` si faltan campos |

### 6.2 Ejemplos de uso

Sustitúyase `5000` por el valor de `API_PORT` si se ha cambiado.

**Comprobar el estado:**

```bash
curl http://localhost:5000/health
```

```json
{"database": "ok", "status": "ok"}
```

**Consultar las lecturas:**

```bash
curl http://localhost:5000/lecturas
```

```json
{
  "total": 192,
  "lecturas": [
    {
      "id": 1,
      "edificio": "A",
      "fecha_hora": "2026-10-14 08:00:00",
      "temperatura": 21.9,
      "humedad": 43.7,
      "co2_ppm": 762
    }
  ]
}
```

**Registrar una lectura nueva:**

```bash
curl -X POST http://localhost:5000/lecturas \
     -H "Content-Type: application/json" \
     --data @04_Ejemplos_pruebas/01_lectura_valida.json
```

```json
{
  "mensaje": "Lectura almacenada correctamente.",
  "lectura": {
    "id": 193,
    "edificio": "A",
    "fecha_hora": "2026-10-15 12:34:56",
    "temperatura": 23.7,
    "humedad": 51.0,
    "co2_ppm": 1375
  }
}
```

**Comprobar la validación** (falta `co2_ppm`):

```bash
curl -X POST http://localhost:5000/lecturas \
     -H "Content-Type: application/json" \
     --data @04_Ejemplos_pruebas/02_lectura_incompleta_HTTP400.json
```

```json
{
  "error": "Faltan campos obligatorios.",
  "campos_ausentes": ["co2_ppm"],
  "campos_requeridos": ["edificio", "fecha_hora", "temperatura", "humedad", "co2_ppm"]
}
```

> El repositorio incluye tres cuerpos JSON de ejemplo en
> `04_Ejemplos_pruebas/`: uno válido, uno incompleto (que debe devolver `400`) y
> uno con humedad fuera de rango (pensado para el bonus de validación avanzada).

### 6.3 Los cinco campos son obligatorios

El cuerpo del `POST` debe contener **los mismos cinco campos del CSV**:

```json
{
  "edificio": "A",
  "fecha_hora": "2026-10-15 12:34:56",
  "temperatura": 23.7,
  "humedad": 51.0,
  "co2_ppm": 1375
}
```

Si falta alguno, la API responde `400` e indica cuáles faltan. **El registro no
se guarda.**

### 6.4 Consultar la base de datos directamente

Como el puerto de PostgreSQL no se publica, se accede a través del contenedor:

```bash
docker compose exec db psql -U smartcampus -d smartcampus
```

Dentro de `psql`:

```sql
\dt                              -- listar tablas
\d lecturas                      -- ver la estructura
SELECT count(*) FROM lecturas;
SELECT * FROM lecturas ORDER BY id DESC LIMIT 5;
\q                               -- salir
```

### 6.5 Esquema de la tabla

La tabla `lecturas` **no la crea el notebook**: la define `db/init.sql`, que se
copia dentro de la imagen de PostgreSQL y se ejecuta automáticamente la primera
vez que el contenedor inicializa un volumen vacío.

```sql
CREATE TABLE lecturas (
    id           SERIAL PRIMARY KEY,
    edificio     VARCHAR(10)  NOT NULL,
    fecha_hora   TIMESTAMP    NOT NULL,
    temperatura  NUMERIC(5,2) NOT NULL,
    humedad      NUMERIC(5,2) NOT NULL,
    co2_ppm      INTEGER      NOT NULL
);
```

Además se crean dos índices: `idx_lecturas_edificio` e `idx_lecturas_fecha_hora`.

> ⚠️ **Por este motivo el notebook usa `if_exists="append"` y no `"replace"`.**
> `replace` eliminaría y recrearía la tabla, y con ella se perderían los tipos
> definidos (`NUMERIC(5,2)`, `TIMESTAMP`) y los dos índices. Para que el notebook
> siga siendo repetible, antes de cargar se vacía la tabla con un `DELETE`.

---

## 7. Prueba de extremo a extremo

Es el núcleo del taller: demuestra que **los tres servicios están realmente
conectados**. Está en la última sección de `notebooks/analyse_data.ipynb`.

### 7.1 Qué hace

```text
   Jupyter                        api                        db
  ┌────────┐   POST /lecturas   ┌────────┐   INSERT INTO   ┌──────────┐
  │requests├───────────────────►│ Flask  ├────────────────►│ lecturas │
  │        │◄───────────────────┤        │                 │          │
  └───┬────┘   HTTP 201 + JSON  └────────┘                 └────┬─────┘
      │                                                        │
      │              SELECT ... (SQLAlchemy)                    │
      └────────────────────────────────────────────────────────┘
             comprobar que el registro está persistido
```

1. Comprueba `GET /health`, para no empezar la prueba sin saber si la API y su
   acceso a la base de datos están operativos.
2. Cuenta las filas existentes en PostgreSQL **antes** de la prueba, usando
   SQLAlchemy y no la API: así la comprobación es independiente del servicio que
   se está evaluando.
3. Envía con `requests` un `POST /lecturas` con una medición **nueva y
   reconocible** (edificio D, `2026-10-15 03:30:00`, `co2_ppm` 1450).
4. Comprueba que la API devuelve **HTTP 201** y recupera el `id` asignado.
5. **Vuelve a consultar PostgreSQL con SQLAlchemy** y busca ese `id` concreto.

### 7.2 Cómo verificarlo

Al ejecutar el notebook debe verse:

```text
Registros en PostgreSQL antes : 192
Registros en PostgreSQL despues: 193

Lectura recuperada de la base de datos (id=...):
  edificio    : D
  fecha_hora  : 2026-10-15 03:30:00
  temperatura : 19.90
  humedad     : 62.50
  co2_ppm     : 1450

OK: la peticion POST ha quedado persistida en PostgreSQL.
```

> ⚠️ **Enseñar la respuesta JSON de la API no es suficiente.** Una captura del
> JSON sin persistencia efectiva no demuestra que la integración funcione. Por
> eso la prueba **vuelve a leer la base de datos** con SQLAlchemy y compara los
> valores. Si el registro no se hubiera guardado, el notebook fallaría con una
> aserción en lugar de dar un resultado engañoso.

### 7.3 Sin abrir el notebook

La misma prueba puede hacerse desde la terminal:

```bash
# Filas antes
docker compose exec db psql -U smartcampus -d smartcampus -c "SELECT count(*) FROM lecturas;"

# POST
curl -X POST http://localhost:5000/lecturas \
     -H "Content-Type: application/json" \
     --data '{"edificio":"D","fecha_hora":"2026-10-15 03:30:00","temperatura":19.9,"humedad":62.5,"co2_ppm":1450}'

# Filas después
docker compose exec db psql -U smartcampus -d smartcampus -c "SELECT count(*) FROM lecturas;"
```

---

## 8. Bonus opcionales

**No realizados.**

Los cinco bonus (`GET /resumen`, filtrado de lecturas, alertas de CO₂,
validación avanzada del POST y pruebas automáticas) no se han implementado. El
enunciado indica expresamente que no son necesarios para obtener la máxima
calificación de la práctica.

---

## 9. Evidencias

Las capturas están en la carpeta **`evidencias/`**:

| Fichero | Qué muestra |
|---|---|
| `01_servicios_compose.png` | Los tres servicios en ejecución (`docker compose ps`) |
| `02_bbdd_postgresql_sqlite.png` | Recuentos y análisis en PostgreSQL **y** SQLite |
| `03_api_endpoints.png` | Respuesta de `GET /lecturas` y `POST /lecturas` correcto |
| `04_integracion_e2e.png` | POST desde Jupyter y verificación del registro en PostgreSQL |

---

## 10. Uso de IA

Esta práctica es de **nivel AMARILLO**: la IA está permitida, pero exige
trazabilidad completa y validación propia.

La memoria de uso de IA se entrega en **`evidencias/memoria_uso_IA.md`**, e
incluye las herramientas utilizadas, las capturas de **todos** los prompts
enviados —también los que no funcionaron—, qué se corrigió, cómo se validó y un
balance final.

Todo el código y los resultados entregados han sido **ejecutados y verificados**
por el equipo sobre Docker real: los resultados del apartado 5.5 y de los
apartados 6 y 7 son salidas reales, no ejemplos teóricos.

---

## 11. Parada y limpieza

### 11.1 Parar los contenedores conservando los datos

```bash
docker compose down
```

Los servicios y la red se eliminan, pero **el volumen `postgres_data` se
conserva**. Al volver a arrancar, las lecturas siguen ahí.

### 11.2 Parar y borrar también los datos

```bash
docker compose down -v
```

> ⚠️ El modificador `-v` **elimina el volumen** y con él todas las lecturas
> guardadas. La próxima vez que se arranque, PostgreSQL inicializará un volumen
> vacío y volverá a ejecutar `init.sql`, recreando la tabla.

### 11.3 Borrar también la base de datos SQLite

SQLite es un fichero dentro de `notebooks/`, no un contenedor:

```bash
rm -rf notebooks/data/
```

El notebook lo vuelve a crear en la siguiente ejecución.

### 11.4 Limpieza completa de recursos del proyecto

```bash
docker compose down -v --rmi local
```

Elimina además las imágenes construidas por el proyecto.

---

## 12. Problemas frecuentes

| Problema | Causa | Solución |
|---|---|---|
| `port is already allocated` | El puerto 8888 o 5000 está ocupado | Cambiar `JUPYTER_PORT` o `API_PORT` en el fichero `.env` |
| En macOS, el puerto 5000 siempre ocupado | Lo usa el «Receptor de AirPlay» del sistema | Usar `API_PORT=5001` o desactivar AirPlay |
| `relation "lecturas" does not exist` | El volumen no estaba vacío, así que `init.sql` no se ejecutó | `docker compose down -v` y volver a arrancar |
| `could not translate host name "db"` | Se cambió `DB_HOST` o el servicio no está en la red | No modificar `DB_HOST`: debe ser `db` |
| La API devuelve **503** en `/health` | La API no consigue conectar con PostgreSQL | `docker compose logs api` y comprobar que `db` está `healthy` |
| `NameError: name 'Path' is not defined` | Falta el import en el notebook | Debe estar `from pathlib import Path` |
| El notebook falla al conectar con PostgreSQL | La URI usa `localhost` en lugar de `db` | El host debe ser `db` |
| Los recuentos no cuadran (384 en vez de 192) | Se ejecutó la carga varias veces sin vaciar la tabla | El notebook ya hace `DELETE` antes de cargar; reiniciar el kernel y ejecutar todo |
| `no such table: lecturas` en SQLite | El fichero SQLite es nuevo y está vacío | Ejecutar el notebook completo de arriba abajo |
| El primer build falla | Problema de red al descargar imágenes o paquetes | Revisar la conexión y repetir `docker compose up --build` |
| En Windows el entorno va muy lento | El proyecto está en `/mnt/c/…` | Moverlo al sistema de ficheros de WSL (`/home/…`) |

### Diagnóstico

```bash
docker compose ps                     # estado de los servicios
docker compose logs api               # salida de la API
docker compose logs db | tail -50     # inicialización de PostgreSQL
docker compose exec db psql -U smartcampus -d smartcampus -c "\dt"
```

---

## Notas

- La documentación técnica del proyecto está en `docs/`.
- El enunciado oficial de la práctica prevalece sobre cualquier indicación
  recogida en este README.
