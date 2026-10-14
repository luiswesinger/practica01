-- ---------------------------------------------------------------------------
-- SmartCampus · Esquema inicial de la base de datos
--
-- Este fichero se monta en /docker-entrypoint-initdb.d/ del contenedor de
-- PostgreSQL. La imagen oficial ejecuta los scripts de ese directorio
-- ÚNICAMENTE cuando inicializa un directorio de datos vacío, es decir, la
-- primera vez que se crea el volumen.
--
-- Consecuencia práctica: si más adelante se cambia este fichero, no se
-- volverá a aplicar sobre un volumen ya existente. Para reaplicarlo hay que
-- borrar el volumen (docker compose down -v), lo que elimina los datos.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lecturas (
    id           SERIAL PRIMARY KEY,
    edificio     VARCHAR(10)  NOT NULL,
    fecha_hora   TIMESTAMP    NOT NULL,
    temperatura  NUMERIC(5,2) NOT NULL,
    humedad      NUMERIC(5,2) NOT NULL,
    co2_ppm      INTEGER      NOT NULL
);

-- Índices de apoyo para las consultas del taller:
-- filtrado por edificio y búsqueda por rango temporal.
CREATE INDEX IF NOT EXISTS idx_lecturas_edificio   ON lecturas (edificio);
CREATE INDEX IF NOT EXISTS idx_lecturas_fecha_hora ON lecturas (fecha_hora);
