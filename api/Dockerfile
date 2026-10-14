# ---------------------------------------------------------------------------
# Imagen de la API Flask para SmartCampus
#
# IMPORTANTE · contexto de build
#   El contexto es la RAÍZ del repositorio, no esta carpeta:
#       docker build -f api/Dockerfile .
#   Por ese motivo las rutas de COPY empiezan por 'api/'.
#
# Imagen ligera: la API solo necesita Flask y el driver de PostgreSQL.
# Toda dependencia queda instalada en el BUILD, de forma que
# 'docker compose up' arranca el servicio sin pasos manuales.
# ---------------------------------------------------------------------------
FROM python:3.13-slim

# Evita que Python escriba ficheros .pyc y que bufferice la salida
# (así los logs de Flask aparecen en tiempo real en 'docker compose logs').
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias primero: la capa se reutiliza mientras no cambie el fichero.
COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY api/app.py .

# Documenta el puerto de Flask (no lo publica por sí solo).
EXPOSE 5000

# Se usa el servidor de desarrollo de Flask: el enunciado pide un prototipo
# funcional, no un despliegue de producción.
# host=0.0.0.0 es obligatorio para que el puerto sea alcanzable desde fuera
# del contenedor; con 127.0.0.1 solo respondería dentro del propio contenedor.
#
# --with-threads es necesario: sin él el servidor de desarrollo atiende una
# petición cada vez. GET /health consulta la base de datos, así que si
# PostgreSQL tarda o no responde, esa petición bloquea al único worker y TODAS
# las demás quedan en cola hasta agotar su tiempo de espera. Con hilos, el
# servicio sigue atendiendo el resto de peticiones mientras una está esperando
# a la base de datos. (En Flask 3 es el valor por defecto, pero se declara de
# forma explícita para que no dependa de la versión instalada.)
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000", "--with-threads"]
