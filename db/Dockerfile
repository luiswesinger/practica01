# ---------------------------------------------------------------------------
# Imagen de PostgreSQL para SmartCampus
#
<<<<<<< HEAD
# Sigue el patrón de la asignatura: en lugar de montar el SQL desde el host con
# un bind mount, se COPIAN los ficheros dentro de la imagen. Así el esquema
# inicial forma parte de la imagen y no depende de que exista una ruta
# concreta en la máquina de cada compañero.
#
# IMPORTANTE · build frente a runtime
#   COPY solo copia el fichero durante el BUILD: NO lo ejecuta.
#   El entrypoint oficial de PostgreSQL ejecuta los scripts de
=======
# Sigue el patrón de la asignatura: el SQL de inicialización se COPIA dentro de
# la imagen. Así el esquema inicial forma parte de la propia imagen y no
# depende de que exista una ruta concreta en la máquina de cada compañero.
#
# IMPORTANTE · build frente a runtime
#   COPY solo copia el fichero durante el BUILD: NO lo ejecuta.
#   El entrypoint de PostgreSQL ejecuta los scripts de
>>>>>>> 8b2b0b98cd6283ba28341bb39ba1ed52204fd55a
#   /docker-entrypoint-initdb.d/ cuando arranca el contenedor y encuentra el
#   directorio de datos VACÍO, es decir, la primera vez que se crea el volumen.
# ---------------------------------------------------------------------------
FROM postgres:16-alpine

<<<<<<< HEAD
# Esquema inicial. Se copia a la carpeta que la imagen oficial reserva para
# los scripts de inicialización y se numera el prefijo para fijar el orden de
=======
# Esquema inicial. Se copia a la carpeta que la imagen base reserva para los
# scripts de inicialización y se numera el prefijo para fijar el orden de
>>>>>>> 8b2b0b98cd6283ba28341bb39ba1ed52204fd55a
# ejecución si algún día se añaden más ficheros.
COPY db/init.sql /docker-entrypoint-initdb.d/01-init.sql

# Documenta el puerto de PostgreSQL (no lo publica por sí solo; publicarlo o no
# se decide en docker-compose.yml).
EXPOSE 5432
