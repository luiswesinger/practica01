# Consultas técnicas · Docker y GitHub

**Proyecto:** SmartCampus · Proyecto Big Data I · Taller evaluable 01
**Repositorio:** https://github.com/luiswesinger/practica01

---

## Para qué sirve este documento

Recoge las **preguntas técnicas** que el equipo consultó sobre la infraestructura Docker,
sobre GitHub y sobre la reproducción del entorno en otras máquinas, con las respuestas
obtenidas. Todas se formularon **con la configuración real del proyecto**, para que las
respuestas se ajusten a este caso y sirvan para defender la solución en el coloquio.

> **Nota de alcance.** Este documento es material de estudio del equipo. No sustituye a la
> memoria de uso de IA de la entrega.

---

## Bloque 1 · Docker y Git

### 1. ¿Qué aporta `condition: service_healthy` frente a `depends_on` a secas?

`depends_on` por sí solo **solo ordena el arranque y la parada**: Compose inicia `db` antes
que `api` y `jupyter`, y los detiene en orden inverso. «Arrancado» significa que el proceso
principal se ha lanzado, **no** que el servicio esté listo.

`condition: service_healthy` añade una **barrera real**: Compose no crea el contenedor
dependiente hasta que `db` reporte `healthy`.

**Por qué importa en este proyecto.** En su primera inicialización PostgreSQL hace `initdb`,
arranca un servidor **temporal solo por socket Unix**, ejecuta
`/docker-entrypoint-initdb.d/01-init.sql`, lo apaga y arranca el servidor definitivo con
TCP. Ese hueco dura entre 2 y 15 segundos. Sin la barrera, la API arranca antes y falla con
`connection refused`.

**Detalle que conviene conocer:** la barrera la implementa **la CLI de Compose, no el
daemon**. Con `docker run` directo, o al reiniciar contenedores por `restart:`, la garantía
desaparece.

---

### 2. Si ya está `EXPOSE 5000` en el Dockerfile, ¿por qué hace falta `ports:`?

`EXPOSE` es **solo metadato**: queda en `Config.ExposedPorts` y no abre nada ni toca
`iptables`. Sirve para documentar y para `docker run -P`.

Con `EXPOSE` y sin `ports:`:

- **Desde el equipo anfitrión no se llega** (`curl localhost:5000` → connection refused, y la
  columna PORTS de `docker ps` sale vacía).
- **Entre contenedores sí funciona**, por cualquier puerto: en una red bridge de usuario no
  hay aislamiento por puerto.

Por eso el navegador —que está fuera de la red Docker— necesita `ports:`, que crea reglas
`iptables` de NAT y un proceso `docker-proxy`.

> Los valores del mapeo **deben ir entre comillas** (`"5000:5000"`): sin ellas, YAML
> interpreta `22:22` como sexagesimal.

---

### 3. ¿Qué diferencia hay entre `docker compose down` y `down -v`?

- **`down`** elimina contenedores y la red del proyecto, y **conserva** el volumen
  `postgres_data`, las imágenes y los bind mounts.
- **`down -v`** **destruye** `postgres_data`. Al volver a levantar, PostgreSQL encuentra el
  directorio vacío, rehace `initdb` y **vuelve a ejecutar `01-init.sql`**.

**Consecuencia práctica.** Editar `db/init.sql` y hacer `up --build` **no aplica los
cambios**: el entrypoint imprime *«Skipping initialization»* porque el volumen no está
vacío. Hay que hacer `down -v` o aplicar el SQL a mano con `psql`.

**Ojo con el fichero SQLite:** `notebooks/data/smartcampus.db` **no es un volumen Docker**,
es un fichero del anfitrión. Sobrevive a `down` y a `down -v`; solo desaparece borrándolo a
mano.

---

### 4. ¿Por qué PostgreSQL usa un volumen con nombre y los notebooks un bind mount?

- **`postgres_data` (volumen con nombre)** para la base de datos, por tres motivos:
  rendimiento y semántica POSIX nativos; **permisos**, porque `initdb` se niega a arrancar si
  el directorio no tiene el propietario y el modo correctos (el volumen se inicializa con el
  UID de la imagen, mientras un bind mount heredaría el UID del anfitrión); y portabilidad
  del ciclo de vida.
- **`./notebooks` (bind mount)** porque el anfitrión debe seguir siendo la fuente de verdad
  editable: se abre con el editor, se versiona con Git y los cambios se ven al instante.

El SQLite acaba en `./notebooks/data/smartcampus.db`. **No debe subirse al repositorio**: es
binario, se regenera desde `datos/sensores.csv` y provocaría conflictos de merge. Ya está
cubierto por `.gitignore` (`*.db`).

---

### 5. ¿Por qué los contenedores usan `db` y no `localhost`? ¿Sirve `container_name`?

Cada contenedor tiene su **propio espacio de nombres de red**: su propia interfaz de loopback
y su propia pila TCP/IP. `localhost` dentro de `api` es la `lo` **de la API**, donde no
escucha ningún PostgreSQL.

En una red bridge **definida por el usuario** (como `smartcampus_net`), Docker levanta un
**DNS embebido** que resuelve, dentro del espacio de nombres de cada contenedor, el nombre
del servicio (`db`), el `container_name` (`smartcampus_db`) y el nombre real del contenedor.

Sí funciona `smartcampus_db`, pero **es peor práctica**: es un nombre global que no se separa
por proyecto (puede chocar con otro y da
`Conflict. The container name ... is already in use`), impide usar `--scale` y no es el
contrato estable. Si el contenedor se renombra o se elimina, el alias desaparece y aparece
`Name or service not known`.

> En la red `bridge` **por defecto** no hay DNS embebido. Por eso este proyecto define su
> propia red.

---

### 6. ¿`git pull` o `git pull --rebase`?

- **`git pull`** = `fetch` + **merge**: crea un commit de fusión con dos padres.
- **`git pull --rebase`** = `fetch` + **rebase**: reaplica tus commits sobre la nueva punta,
  generando **SHAs nuevos** e historial lineal.

Si alguien ha reescrito el historial remoto, el `pull` normal **no da error de historias no
relacionadas**: produce commits duplicados con SHAs distintos, conflictos artificiales sobre
cambios idénticos, resurrección de contenido borrado y un commit de fusión ruidoso. El
`rebase` detecta los parches ya aplicados y los descarta, resolviendo el caso sin conflicto.

**Riesgos en ramas compartidas:** reescribir historial obliga a todo el equipo a rebasar;
conviene usar `--force-with-lease` en lugar de `--force` y avisar. Desde Git 2.27, un `pull`
sin política configurada falla y pide elegir explícitamente.

---

### 7. `.gitignore` tiene `*.db` pero `git status` sigue mostrando el fichero. ¿Por qué?

`.gitignore` **solo se aplica a ficheros no rastreados**. Si el `.db` ya está en el índice,
seguirá apareciendo como modificado para siempre.

Otros casos en que no se aplica: negaciones `!` posteriores, precedencia entre fuentes
(global, `.git/info/exclude`, directorios padre), rutas pasadas explícitamente, diferencias
de mayúsculas entre macOS y Linux, y patrones de ruta (`/*.db` no es lo mismo que `*.db`).

**Para dejar de rastrear un fichero:**

```bash
git rm --cached fichero.db     # --cached conserva el fichero en disco
git commit -m "deja de rastrear fichero.db"
```

> Sin `--cached`, el comando **borra también el fichero del disco**. Y esto no purga el
> historial: para eso haría falta `git filter-repo` o BFG y coordinarlo con el equipo.

---

### 8. ¿Qué debe incluir el README como mínimo?

**Imprescindible:**

- Qué es el proyecto y qué tres servicios lo componen.
- Requisitos **con versión** (Docker Engine / Desktop y el plugin `docker compose`), y la
  aclaración de que **no hace falta instalar Python, PostgreSQL ni Jupyter** en el equipo.
- Los comandos exactos y copiables, con el aviso de que el primer arranque tarda minutos.
- La **salida esperada** de `docker compose ps` y cómo interpretarla.
- Cómo verificar funcionalmente cada servicio (una petición a `/health`, abrir Jupyter).
- Tabla de variables y puertos, dejando claro que **solo se cambia el lado izquierdo** del
  mapeo.
- Diferencias de entorno y conflictos de puertos conocidos.
- Ciclo de vida: `down` frente a `down -v`, con la consecuencia escrita.
- Diagnóstico de los fallos más probables.

**No debe incluir:** credenciales reales, tokens, rutas absolutas personales, direcciones IP
privadas, ni comandos destructivos sin advertencia.

---

## Bloque 2 · Reproducción en otros equipos

### 9. El entorno se verificó en macOS. ¿Qué problemas aparecen en otros sistemas?

| Sistema | Puerto 5000 | Diagnóstico | Solución |
|---|---|---|---|
| **macOS** | Lo ocupa el **Receptor de AirPlay** del sistema | `lsof -nP -iTCP:5000 -sTCP:LISTEN` muestra `ControlCe` | `API_PORT=5001`, o desactivar AirPlay |
| **Windows** | Rangos **excluidos por Hyper-V/WSL2** | `netsh interface ipv4 show excludedportrange protocol=tcp` | Cambiar de puerto; `net stop winnat && net start winnat` como parche temporal |
| **Linux** | Puede haber un PostgreSQL nativo en 5432 | `sudo ss -ltnp` | Cambiar el **lado izquierdo** del mapeo |

**Regla general: se cambia solo el lado izquierdo.** El puerto de la derecha está fijado por
las URLs internas —el notebook llama literalmente a `http://api:5000`— y no debe tocarse.

En Windows, un puerto dentro de un rango excluido **falla sin que aparezca ningún proceso**
en `netstat`: no hay nada que matar, solo cambiar de puerto.

---

### 10. En Windows con WSL2, ¿por qué no conviene trabajar en `/mnt/c/...`?

`/mnt/c` **no es un disco local**: es un sistema de ficheros **remoto por 9P**, y cada
operación (`open`, `stat`, `readdir`) cruza la frontera de la máquina virtual. El coste se
nota sobre todo en metadatos y ficheros pequeños.

En este proyecto golpea los dos puntos sensibles: el **contexto de build es la raíz del
repositorio** y el **bind mount de `./notebooks`** sufre muchas operaciones pequeñas por el
fichero SQLite.

**Matiz que conviene no exagerar:** mover el proyecto a `~` **no acelera la descarga ni el
`pip install`** (las capas viven dentro de la máquina virtual de Docker). Lo que acelera es el
envío del contexto de build y la entrada/salida del bind mount.

---

### 11. ¿Qué diferencia hay en los permisos de un bind mount entre sistemas?

| Sistema | Comportamiento |
|---|---|
| **macOS / Windows** | El UID **se sintetiza**: el anfitrión ve `501:20` y el contenedor `1000:100` sobre el mismo directorio. Por eso allí **nunca falla** y nadie lo previene. |
| **Linux (Docker Engine nativo)** | El UID real pasa tal cual. Si no coincide con `jovyan` (`1000:100`), aparece `PermissionError [Errno 13]`. |

Es el único punto de fricción del proyecto, y afecta **solo al bind mount de `./notebooks`**:
el volumen de PostgreSQL nunca da problemas porque Docker lo inicializa con el UID de la
imagen.

**Soluciones:** alinear el usuario con `user: "${UID}:${GID}"` (preferible), o
`sudo chown -R 1000:100 notebooks`. En Fedora/RHEL el fallo no es de UID sino de **SELinux**,
y se resuelve añadiendo `:z` al montaje.

---

### 12. ¿Los finales de línea CRLF rompen algo?

**Rompe** (verificado en contenedor):

- Un **shebang** con `\r`: `#!/bin/sh\r` → `exec /s.sh: no such file or directory`, porque el
  kernel busca el intérprete literal `/bin/sh\r`.
- Scripts interpretados: error de sintaxis por el `\r` final.
- Valores capturados con `$(...)`: el `\r` se cuela y la comparación **falla en silencio**,
  que es el caso más peligroso.

**No rompe** (y conviene desmentir el mito):

- `.env` en **Compose v2**: el `\r` se recorta al interpretar el valor.
- **Dockerfiles**: BuildKit normaliza.
- `db/init.sql`: `psql` tolera el `\r`.
- `pandas.read_csv`: tolera CRLF; el `sensores.csv` del repositorio está en CRLF y el notebook
  lee las 192 filas limpias.

**Quién propaga realmente el CRLF es Git, no el editor.** Sin `.gitattributes` y con
`core.autocrlf=false`, el repositorio guarda CRLF y quien esté en Linux lo recibe roto. Como
eso depende de la configuración local de cada persona, la garantía es declarar
`.gitattributes`, que en este proyecto ya está incluido.

---

### 13. ¿Y las diferencias de arquitectura?

Las tres imágenes base (`postgres:16-alpine`, `python:3.13-slim` y
`quay.io/jupyter/minimal-notebook`) son **multi-arquitectura**: en una máquina amd64 se
descarga la variante nativa sin hacer nada.

Las imágenes propias son de una sola arquitectura, pero **el proyecto se distribuye como
código con `build:`**, así que `up --build` las reconstruye nativas en destino. La emulación
solo entra si alguien escribe `--platform` explícitamente, y no compensa: las dependencias
tienen ruedas para ambas arquitecturas, así que reconstruir es nativo.

Donde sí falla es al **mover imágenes ya construidas** entre arquitecturas (`docker save` /
`load`) → `exec format error`.

> **Límite real de reproducibilidad:** los tags son mutables (`latest`, `16-alpine`,
> `3.13-slim`). Para una reproducibilidad exacta habría que fijar las imágenes por digest.

---

### 14. ¿Cambia algo al usar Docker Engine en Linux en lugar de Docker Desktop?

- **Permisos del socket:** en Linux pertenece a `root:docker`. Hay que añadir el usuario al
  grupo (`sudo usermod -aG docker $USER`) y **cerrar sesión o usar `newgrp docker`**. Si el
  README solo dice `usermod`, la persona sigue viendo `permission denied` y cree que las
  instrucciones están mal.
- **Pertenecer al grupo `docker` equivale a ser root.** Conviene decirlo sin dramatizar.
- **`host.docker.internal` no existe** en Engine nativo; requiere
  `extra_hosts: ["host.docker.internal:host-gateway"]`. **Este proyecto no lo necesita**: los
  servicios se hablan por nombre dentro de `smartcampus_net`.
- **La publicación de puertos funciona igual desde fuera**; cambia el mecanismo interno.

El `docker-compose.yml` **no necesita ninguna variante por plataforma**.

---

### 15. ¿Cuál es la comprobación mínima de extremo a extremo?

```bash
docker compose up -d --build
docker compose ps                                  # tres servicios; db (healthy)
curl -s http://localhost:5000/health               # {"database":"ok","status":"ok"}
```

Y para cerrar el circuito completo, **ejecutar el notebook de arriba abajo** desde el Jupyter
del contenedor: dentro llama a `http://api:5000`, un nombre que **solo resuelve dentro de la
red de Compose**.

> ⚠️ **No prometer un `id` concreto.** El `id` que devuelve el `POST` va muy por delante del
> número de filas (la secuencia `SERIAL` avanza aunque el notebook haga `DELETE` y recargue).
> Un README que prometa `id: 193` está mintiendo.

**Limpieza:**

```bash
docker compose down              # conserva los datos
docker compose down -v           # borra las lecturas
rm -rf notebooks/data/           # borra el SQLite (down -v NO lo elimina)
```
