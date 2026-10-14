"""
SmartCampus · API Flask
=======================

Versión mínima y funcional de los tres endpoints obligatorios del reto C:

    GET  /health     -> comprueba que el servicio responde y que la base de
                        datos es accesible.
    GET  /lecturas   -> devuelve las lecturas almacenadas en PostgreSQL.
    POST /lecturas   -> recibe una lectura en JSON y la guarda en PostgreSQL.

La configuración se recibe por variables de entorno (las define
docker-compose.yml), de modo que no hay credenciales escritas en el código.

Nota: este fichero cubre el mínimo verificable para poder construir y validar
los contenedores. La ampliación y el refactor corresponden al equipo.
"""

import os
from datetime import date, datetime
from decimal import Decimal

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Serialización de tipos
# ---------------------------------------------------------------------------
# psycopg2 devuelve los TIMESTAMP como datetime y los NUMERIC como Decimal.
# Al convertirlos a JSON, Python los serializa de formas poco útiles para un
# cliente: el datetime acaba en formato de cabecera HTTP
# ("Thu, 15 Oct 2026 12:34:56 GMT") y el Decimal, entre comillas como cadena.
# Se normalizan aquí para que la respuesta sea cómoda de consumir desde el
# notebook: fechas en ISO 8601 y números como números.
def normalizar(valor):
    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ")
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        # float() es suficiente para un prototipo de análisis; si se necesitara
        # precisión decimal exacta se devolvería como cadena.
        return float(valor)
    return valor


def normalizar_fila(fila):
    return {clave: normalizar(valor) for clave, valor in fila.items()}


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
# 'db' es el NOMBRE DEL SERVICIO en docker-compose.yml. Dentro de la red de
# Compose ese nombre se resuelve por DNS; 'localhost' apuntaría al propio
# contenedor de la API y la conexión fallaría.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "smartcampus"),
    "user": os.environ.get("DB_USER", "smartcampus"),
    "password": os.environ.get("DB_PASSWORD", "smartcampus_dev"),
}

TABLA = "lecturas"

# Campos obligatorios del POST: los mismos cinco del CSV.
CAMPOS_OBLIGATORIOS = ("edificio", "fecha_hora", "temperatura", "humedad", "co2_ppm")


def get_connection():
    """Abre una conexión nueva a PostgreSQL.

    Se abre una conexión por petición en lugar de compartir una global: es más
    simple y suficiente para un prototipo con el servidor de desarrollo.
    """
    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Comprueba el servicio Y el acceso a la base de datos.

    El enunciado pide comprobar que el servicio responde 'y que puede acceder
    a la base de datos', así que no basta con devolver un 200 fijo: hay que
    consultar de verdad.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return jsonify({"status": "ok", "database": "ok"}), 200
    except Exception as exc:  # noqa: BLE001 - se informa del error al cliente
        # Si la base de datos no responde, el servicio NO está sano:
        # se devuelve 503 (Service Unavailable) en lugar de un 200 engañoso.
        return jsonify({"status": "error", "database": "unreachable", "detail": str(exc)}), 503


# ---------------------------------------------------------------------------
# GET /lecturas
# ---------------------------------------------------------------------------
@app.route("/lecturas", methods=["GET"])
def listar_lecturas():
    """Devuelve las lecturas reales almacenadas en PostgreSQL.

    El enunciado prohíbe explícitamente devolver una lista escrita a mano en
    Python, así que los datos salen siempre de una consulta a la base.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"SELECT id, edificio, fecha_hora, temperatura, humedad, co2_ppm "
                f"FROM {TABLA} ORDER BY id;"
            )
            filas = cur.fetchall()

    return jsonify({"total": len(filas), "lecturas": [normalizar_fila(f) for f in filas]}), 200


# ---------------------------------------------------------------------------
# POST /lecturas
# ---------------------------------------------------------------------------
@app.route("/lecturas", methods=["POST"])
def crear_lectura():
    """Recibe una lectura en JSON y la inserta en la tabla 'lecturas'."""
    datos = request.get_json(silent=True)

    if datos is None:
        return jsonify({"error": "El cuerpo de la petición debe ser JSON válido."}), 400

    # Validación mínima obligatoria: todos los campos deben estar presentes.
    faltan = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in datos]
    if faltan:
        return (
            jsonify(
                {
                    "error": "Faltan campos obligatorios.",
                    "campos_ausentes": faltan,
                    "campos_requeridos": list(CAMPOS_OBLIGATORIOS),
                }
            ),
            400,
        )

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"INSERT INTO {TABLA} "
                f"(edificio, fecha_hora, temperatura, humedad, co2_ppm) "
                f"VALUES (%s, %s, %s, %s, %s) RETURNING *;",
                (
                    datos["edificio"],
                    datos["fecha_hora"],
                    datos["temperatura"],
                    datos["humedad"],
                    datos["co2_ppm"],
                ),
            )
            creada = cur.fetchone()
        conn.commit()

    return (
        jsonify(
            {
                "mensaje": "Lectura almacenada correctamente.",
                "lectura": normalizar_fila(creada),
            }
        ),
        201,
    )


if __name__ == "__main__":
    # host=0.0.0.0 es imprescindible dentro de un contenedor.
    app.run(host="0.0.0.0", port=5000, debug=True)
