# Peticiones de ejemplo para SmartCampus

Los JSON incluidos son **cuerpos de ejemplo** para probar el endpoint `POST /lecturas`. No incluyen código de la API ni la implementación de la conexión a la base de datos.

- `01_lectura_valida.json`: petición completa. Debe aceptarse y quedar almacenada, según el reto C.
- `02_lectura_incompleta_HTTP400.json`: falta `co2_ppm`; debe rechazarse con HTTP 400, requisito obligatorio.
- `03_bonus_lectura_invalida_humedad.json`: el campo `humedad` está fuera del intervalo 0–100. Es **solo para el bonus de validación avanzada**.

Podéis enviar estas peticiones desde Postman o mediante `requests` desde Jupyter. Comprobad siempre los códigos de estado, el contenido JSON de la respuesta y, cuando corresponda, la persistencia real en PostgreSQL.

**Atención:** El registro completo es un ejemplo para pruebas y puede repetirse al ejecutar varias veces el sistema. Elegid cómo identificar vuestras inserciones durante la demostración final. Para enviar los JSON utilizad cabecera `Content-Type: application/json`.
