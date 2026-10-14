# ---------------------------------------------------------------------------
# Imagen de Jupyter para SmartCampus
#
# IMPORTANTE · contexto de build
#   El contexto es la RAÍZ del repositorio, no esta carpeta:
#       docker build -f jupyter/Dockerfile .
#   Por ese motivo las rutas de COPY empiezan por 'jupyter/'.
#   Se hace así porque la imagen necesita copiar 'datos/', que está fuera.
#
# Objetivo: que el contenedor arranque ya listo. Todas las dependencias se
# instalan durante el BUILD, no después, y el CSV viaja dentro de la imagen
# para que el notebook no dependa de lo que haya en el host.
# ---------------------------------------------------------------------------
FROM quay.io/jupyter/minimal-notebook:latest

# Dependencias primero, para que un cambio en el código no invalide
# la caché de esta capa.
#
# --chown=jovyan:users es necesario por dos motivos:
#   1. La imagen base ejecuta los comandos como el usuario 'jovyan', no como
#      root, así que un fichero copiado como root:root con modo 600 sería
#      ilegible para pip.
#   2. COPY conserva los permisos del fichero original en el host, de modo que
#      un fichero con modo 600 en una máquina rompería el build en esa máquina
#      y no en otra.
# Cediendo la propiedad a 'jovyan' el fichero queda legible siempre.
COPY --chown=jovyan:users jupyter/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Datos de entrada: quedan FUERA del punto de montaje de ./notebooks,
# así siempre provienen de la imagen y no del host.
COPY --chown=jovyan:users datos /home/jovyan/datos

WORKDIR /home/jovyan/work

# Documenta el puerto del servidor Jupyter (no lo publica por sí solo).
EXPOSE 8888
