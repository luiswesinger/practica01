# Übergabe · Reto B (Notebook) — SmartCampus

**Projekt:** Proyecto Big Data I · Taller evaluable 01
**Repository:** https://github.com/luiswesinger/practica01
**Stand:** 14. Oktober 2026
**Verfasser dieser Übergabe:** tonyelos (Reto A — Infrastruktur)
**Empfänger:** verantwortliche Person für **Reto B** (Laden, Speichern und Analyse)

---

## 1. Kurzfassung: was zu tun ist

1. **Synchronisieren** — Achtung, die Historie wurde umgeschrieben (siehe § 3).
2. **Notebook erstellen** in `notebooks/` und nach `main` pushen.
3. **Dokumentation ergänzen** in `docs/PROGRESO.md` (Abschnitt „Reto B").
4. **Screenshots** für die Abgabe in `evidencias/` ablegen.
5. **KI-Nachweis** führen (Niveau GELB — verpflichtend, siehe § 8).

**Geschätzter Aufwand:** 35–40 Minuten (so sieht es der Zeitplan des Dozenten vor:
Minute 20–55 für den Datenblock).

---

## 2. Was bereits fertig ist (Reto A)

Die gesamte Infrastruktur läuft und ist verifiziert. **Bitte nichts davon neu bauen.**

| Dienst | Image | Container | Port |
|---|---|---|---|
| `db` | eigene Image auf `postgres:16-alpine` | `smartcampus_db` | nicht veröffentlicht |
| `api` | eigene Image auf `python:3.13-slim` | `smartcampus_api` | 5000 |
| `jupyter` | eigene Image auf `quay.io/jupyter/minimal-notebook` | `smartcampus_jupyter` | 8888 |

**Start mit einem einzigen Befehl:**

```bash
docker compose up --build
```

Anschließend:

- Jupyter → http://localhost:8888 (kein Token, lokale Übungsumgebung)
- API → http://localhost:5000/health

### 2.1 Wichtig: die Tabelle `lecturas` existiert schon

Das Schema wird beim ersten Start von PostgreSQL automatisch angelegt
(`db/init.sql`, per `COPY` in der Image). Verifiziert:

```
 Schema |   Name   | Type  |   Owner
--------+----------+-------+------------
 public | lecturas | table | smartcampus
```

Struktur:

| Spalte | Typ |
|---|---|
| `id` | `SERIAL PRIMARY KEY` |
| `edificio` | `VARCHAR(10) NOT NULL` |
| `fecha_hora` | `TIMESTAMP NOT NULL` |
| `temperatura` | `NUMERIC(5,2) NOT NULL` |
| `humedad` | `NUMERIC(5,2) NOT NULL` |
| `co2_ppm` | `INTEGER NOT NULL` |

Zusätzlich existieren zwei Indizes: `idx_lecturas_edificio` und
`idx_lecturas_fecha_hora`.

> **Das Notebook muss die Tabelle also nicht anlegen.** Es muss sie befüllen.

### 2.2 Die API ist funktionsfähig

Die drei Pflicht-Endpunkte aus Reto C sind implementiert und getestet:

| Endpunkt | Ergebnis im Test |
|---|---|
| `GET /health` | `200` · `{"status":"ok","database":"ok"}` |
| `GET /lecturas` | `200` · JSON-Auflistung |
| `POST /lecturas` | `201` · Datensatz wird persistiert |
| `POST` ohne Pflichtfeld | `400` · mit Liste der fehlenden Felder |

**Für Reto B reicht das aus.** Die API ist hier nur relevant, weil sie auf
**dieselbe Tabelle** `lecturas` schreibt, die das Notebook benutzt.

---

## 3. Schritt 1 — Repository synchronisieren

> ⚠️ **Wichtig:** Die Commit-Historie auf `main` wurde umgeschrieben
> (mehrere Commits wurden zu einem zusammengefasst). Ein normales `git pull`
> kann deshalb fehlschlagen.

### 3.1 Fall A: noch kein lokaler Klon vorhanden

```bash
git clone https://github.com/luiswesinger/practica01.git
cd practica01
```

### 3.2 Fall B: Repository bereits geklont, **keine** eigenen Änderungen

```bash
cd practica01
git fetch origin
git reset --hard origin/main
```

### 3.3 Fall C: Repository geklont **mit** eigenen, noch nicht committeten Änderungen

```bash
cd practica01
git stash                      # eigene Arbeit sichern
git fetch origin
git reset --hard origin/main
git stash pop                  # eigene Arbeit zurückholen
```

> Wenn `git stash pop` Konflikte meldet: Änderungen liegen meist in Dateien,
> die in dieser Übergabe neu sind. Dann die eigene Version prüfen und
> entscheiden, welche Fassung bleibt.

### 3.4 Git-Identität prüfen (wichtig für die Bewertung!)

Ein Commit wird GitHub nur dann dem eigenen Konto zugerechnet, wenn Name und
E-Mail stimmen. **Im Repository prüfen und bei Bedarf setzen:**

```bash
git config user.name
git config user.email
```

Falls leer oder falsch:

```bash
git config user.name  "DEIN_GITHUB_NAME"
git config user.email "DEINE_GITHUB_EMAIL"
```

> Der Autor von Reto A musste das ebenfalls lokal setzen, weil die globale
> Git-Konfiguration auf einen anderen Account zeigte.

---

## 4. Schritt 2 — Das Notebook erstellen (Reto B)

### 4.1 Ablageort und Dateiname

**Das Notebook gehört nach `notebooks/`.**

Dieser Ordner ist im Container auf `/home/jovyan/work` gemountet. Alles, was
dort liegt, ist sofort in Jupyter sichtbar und wird direkt im Repository
gespeichert — **kein Kopieren, kein Neubauen nötig.**

Vorschlag für den Dateinamen (der Dozent gibt keinen vor):

```
notebooks/smartcampus_analisis.ipynb
```

### 4.2 Verfügbare Pfade im Container

| Was | Pfad im Container | Herkunft |
|---|---|---|
| Der CSV-Datensatz | `/home/jovyan/datos/sensores.csv` | **in der Image** (per `COPY`) |
| Notebooks | `/home/jovyan/work/` | vom Host gemountet (`./notebooks`) |

> Beide Pfade sind bereits geprüft. Der Datensatz liegt **absichtlich außerhalb**
> des Mount-Punkts, damit er immer aus der Image kommt und nicht von dem, was
> zufällig auf dem Host liegt.

### 4.3 Verbindungs-URIs

**PostgreSQL** (der Hostname ist der **Dienstname** `db`, nicht `localhost`):

```
postgresql+psycopg2://smartcampus:smartcampus_dev@db:5432/smartcampus
```

**SQLite** (derselbe Code, nur ein anderer Engine — keine Server nötig):

```
sqlite:////home/jovyan/work/data/smartcampus.db
```

> Für SQLite vorher den Ordner anlegen, z. B. mit
> `Path("/home/jovyan/work/data").mkdir(exist_ok=True)`.
> Die Datei landet dann im gemounteten Ordner und ist im Repository sichtbar —
> sie ist aber über `.gitignore` ausgeschlossen, wird also **nicht** committet.
> Das ist beabsichtigt.

### 4.4 Die vier Pflichtaufgaben aus dem Enunciado

Das Notebook muss:

1. **Den CSV mit pandas einlesen** (`pd.read_csv`), Spalten und Typen prüfen und
   die Daten für die Speicherung vorbereiten.
2. **Eine Verbindung mit SQLAlchemy herstellen** und die Messwerte in die
   Tabelle `lecturas` in PostgreSQL laden.
3. **Dieselbe Lade- und Abfragelogik für SQLite wiederverwenden**, wobei
   **nur** der Engine bzw. die URI ausgetauscht wird. Die Logik lässt sich in
   Funktionen kapseln.
4. **Anzeigen, wie viele Datensätze pro Engine geladen wurden**, und mindestens
   zwei Ergebnisse liefern:
   - **Durchschnittstemperatur pro Gebäude**
   - **Gebäude mit dem höchsten CO₂-Durchschnitt**

### 4.5 Referenzwerte zum Abgleich

Damit die eigenen Ergebnisse geprüft werden können — das sind die tatsächlichen
Werte des Datensatzes:

| Gebäude | Ø Temperatur | Ø CO₂ |
|---|---|---|
| A | 22,62 °C | 822,4 ppm |
| B | 23,68 °C | 1002,9 ppm |
| C | **24,44 °C** ← höchste | 1202,4 ppm |
| D | 23,08 °C | **1349,3 ppm** ← höchster |

Weitere Eigenschaften des Datensatzes:

- **192 Zeilen**, 4 Gebäude (A, B, C, D) × 48 Messungen
- **keine fehlenden Werte, keine Duplikate**
- Zeitraum: 2026-10-14 08:00 → 19:45 (15-Minuten-Takt)

---

## 5. Fallstricke, die vermieden werden sollten

### 5.1 `fecha_hora` kommt als Text an ⚠️

`pd.read_csv` liest die Spalte `fecha_hora` **als Zeichenkette** (`str`), nicht
als Datum. Sie muss vor dem Schreiben in die Datenbank umgewandelt werden:

```python
df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
```

Ohne diese Umwandlung kann der Schreibvorgang in PostgreSQL bzw. SQLite
fehlschlagen oder ein falsches Format erzeugen.

### 5.2 Die Bewertung bestraft doppelte Logik ⚠️

In der Bewertungstabelle steht wörtlich:

> *„Carga de lecturas y análisis con pandas/SQLAlchemy en PostgreSQL y SQLite
> **sin duplicar la lógica**."* (2,0 Punkte)

**Falsch:**

```python
# Logik einmal für PostgreSQL …
pg_engine = create_engine(PG_URI)
df.to_sql("lecturas", pg_engine, if_exists="replace", index=False)
resumen_pg = pd.read_sql("SELECT ...", pg_engine)

# … und noch einmal kopiert für SQLite.
lite_engine = create_engine(LITE_URI)
df.to_sql("lecturas", lite_engine, if_exists="replace", index=False)
resumen_lite = pd.read_sql("SELECT ...", lite_engine)
```

**Richtig:** eine Funktion, die nur den Engine als Parameter bekommt:

```python
def cargar_y_resumir(engine, df):
    """Kennt den Datenbankhersteller nicht: bekommt nur einen Engine."""
    df.to_sql("lecturas", engine, if_exists="append", index=False)
    ...
    return resumen
```

Und dann für beide Engines mit derselben Funktion aufrufen. Genau das war der
Kernpunkt des SQLAlchemy-Labors: *„die Funktion kennt den Hersteller der
Datenbank nicht"*.

### 5.3 `if_exists="replace"` zerstört das Schema ⚠️

`if_exists="replace"` **löscht und erstellt die Tabelle neu** — und damit auch
die Spaltentypen, die `db/init.sql` definiert hat (z. B. `NUMERIC(5,2)` statt
automatisch abgeleiteter Typen). Außerdem gehen die zwei Indizes verloren.

Empfehlung: `if_exists="append"` verwenden, damit das vorgegebene Schema
erhalten bleibt.

> **Aber Achtung:** Beim erneuten Ausführen des Notebooks entstehen dann
> Duplikate. Zwei saubere Wege:
>
> - **Vorher leeren:** `DELETE FROM lecturas;` per
>   `connection.execute(text("DELETE FROM lecturas"))` — so bleibt das Notebook
>   wiederholbar ausführbar.
> - **Oder** nur einmal ausführen und die Zeilenzahl zur Kontrolle ausgeben.
>
> Die Zeilenzahl ist in beiden Fällen das, was der Dozent sehen will.

### 5.4 Die API schreibt in dieselbe Tabelle

`POST /lecturas` fügt Datensätze in **dieselbe** Tabelle `lecturas` ein. Wenn
das Notebook also eine Zeilenzahl ausgibt und parallel jemand die API benutzt,
kann die Zahl abweichen. Für die Beweisführung am besten die Zeilenzahl
**vor und nach** dem eigenen Test vergleichen.

### 5.5 `localhost` funktioniert nicht

Innerhalb des Jupyter-Containers zeigt `localhost` auf den Jupyter-Container
selbst — **nicht** auf die Datenbank. Der Hostname ist der **Dienstname** `db`.

---

## 6. Schritt 3 — Dokumentation ergänzen

In **`docs/PROGRESO.md`** existiert bereits ein Abschnitt
**„7.1 Reto B · Carga, almacenamiento y análisis (siguiente tarea)"**.

Dieser Abschnitt ist als Aufgabenbeschreibung geschrieben. **Bitte nach
Erledigung aktualisieren:**

1. Den Status in der Übersichtstabelle in § 1 von `⬜ No iniciado` auf
   `✅ Completado` setzen und den Namen der verantwortlichen Person eintragen.
2. Den Abschnitt 7.1 durch eine kurze Beschreibung des tatsächlich gebauten
   Notebooks ersetzen:
   - Dateiname und Ablageort
   - wie die Logik strukturiert wurde (welche Funktionen, welche Signatur)
   - **die erhaltenen Ergebnisse** (Tabelle mit Temperatur- und CO₂-Werten)
   - wie viele Datensätze in PostgreSQL und wie viele in SQLite geladen wurden
3. Den Abschnitt „Siguientes pasos" entsprechend kürzen.

### 6.1 Ebenfalls zu aktualisieren

- **`docs/PROCESO_DE_COMPILACION.md`** — nur falls sich am Build etwas ändert.
  Wenn keine neue Abhängigkeit nötig ist: **nichts zu tun**.
- Falls doch eine Bibliothek fehlt: `jupyter/requirements.txt` ergänzen und die
  Image neu bauen (`docker compose up --build`). Bitte dann im Commit erwähnen.

---

## 7. Schritt 4 — Screenshots für die Abgabe

Der Dozent verlangt **vier Pflichtnachweise**. Zwei davon betreffen Reto B:

| Nr. | Was zu sehen sein muss | Zuständig |
|---|---|---|
| 01 | Die drei laufenden Dienste (`docker compose ps`) | Reto A ✅ |
| **02** | **Notebook mit den Abfragen und Datensatzzahlen in PostgreSQL und SQLite** | **Reto B** |
| 03 | JSON-Antwort auf `GET /lecturas` und erfolgreicher `POST /lecturas` | Reto A ✅ |
| **04** | In Jupyter: `POST` ausgeführt und dieselbe Messung in PostgreSQL nachgewiesen | Reto D |

Die Screenshots gehören nach **`evidencias/`** (Ordner existiert bereits).
Sprechende Dateinamen verwenden, z. B.
`evidencias/02_bbdd_postgresql_sqlite.png`.

> 📌 Der Ordner `evidencias/` ist **nicht** von `.gitignore` ausgeschlossen —
> die Bilder werden also ganz normal mitcommittet. Das ist gewollt.

---

## 8. Schritt 5 — KI-Nachweis (Niveau GELB, verpflichtend)

Diese Übung ist als **Niveau GELB** eingestuft: KI ist erlaubt, aber die
Nachverfolgbarkeit ist **verpflichtend**.

**Was verlangt wird** (Enunciado, Abschnitt 07):

| Anforderung | Detail |
|---|---|
| Werkzeuge und Zweck | Welche Assistenten/Modelle, wofür (Docker, SQL, Flask, Debugging, Text), und **wer im Team** sie benutzt hat |
| **Screenshots ALLER Prompts** | Chronologisch geordnet, **auch Umformulierungen, Wiederholungen und Prompts, die nichts gebracht haben**. Die zugehörige Antwort bzw. der relevante Teil davon muss sichtbar sein. **Eine Auswahl nur der besten Prompts ist nicht zulässig.** |
| Was funktionierte, was nicht | Pro Interaktion: was beabsichtigt war, welcher Vorschlag brauchbar war, welche Antworten fehlerhaft waren oder nicht verwendet wurden |
| Korrekturen und Validierung | Was **ihr selbst** geändert habt und **wie ihr es geprüft habt** (Code ausgeführt, Fehler gefunden, SQL-Abfrage, HTTP-Antwort, Persistenz geprüft) |
| Abschlussbetrachtung | Kurze Reflexion über Nutzen und Grenzen von KI im Projekt: wo Zeit gespart wurde, wo Probleme entstanden, **welche Entscheidungen vom Team kamen** |

**Regeln:**

- 🕐 Screenshots **während der Arbeit** aufnehmen, **nicht** nachträglich eine
  idealisierte Unterhaltung rekonstruieren.
- 🔢 Nummerieren, damit sie dem Code bzw. der Aufgabe zugeordnet werden können.
- 🚫 **Keine Passwörter, Tokens oder personenbezogenen Daten** in die KI, ins
  Repository oder in die Screenshots. Diese Daten abdecken — aber **nicht** den
  Prompt selbst und nicht den fachlichen Nachweis.
- ⚖️ Auslassung, Ungenauigkeit oder Falschheit wird nach der KI-Regelung der
  Universität geahndet.

### 8.1 Vorlage

**`03_Plantillas/Plantilla_memoria_uso_IA_Amarillo.docx`** liegt im Repository
und gibt die Struktur vor (Prompts, Screenshots, Fehler, Validierung).

### 8.2 Falls keine KI verwendet wird

Dann ist eine ausdrückliche Erklärung einzureichen:

> „No se han utilizado herramientas de IA en esta práctica."

In diesem Fall sind keine Screenshots nötig.

> 💡 **Hinweis aus Reto A:** Dort wurde ein `PROMPTS.md` angelegt, das die
> Prompts dokumentiert. Für dieses Projekt reicht das **nicht** — es werden
> **Screenshots** verlangt.

---

## 9. Schritt 6 — Committen und Pushen

### 9.1 Vorgeschlagene Aufteilung

Kleine, thematisch getrennte Commits — der Dozent sieht daran den Arbeitsumfang:

```bash
# 1) Notebook
git add notebooks/smartcampus_analisis.ipynb
git commit -m "Reto B: notebook de carga y analisis con PostgreSQL y SQLite"

# 2) Dokumentation
git add docs/PROGRESO.md
git commit -m "docs: actualiza el estado del Reto B y los resultados obtenidos"

# 3) Evidencias
git add evidencias/
git commit -m "docs: anade capturas de evidencia de bases de datos"

# 4) Ggf. neue Abhaengigkeiten
git add jupyter/requirements.txt
git commit -m "build: anade <paquete> a las dependencias de Jupyter"
```

### 9.2 Vor dem Push prüfen

```bash
git status              # keine unerwarteten Dateien
git pull --rebase       # zuerst die Arbeit der anderen holen
git push origin main
```

> ⚠️ **Nicht committen:** `.env`, `*.db`, `*.sqlite`, `.ipynb_checkpoints/`,
> `__pycache__/`. Alles davon ist bereits über `.gitignore` ausgeschlossen —
> bitte nicht mit `git add -f` erzwingen.

---

## 10. Checkliste vor der Abgabe

- [ ] Repository synchronisiert, `git config user.name`/`user.email` korrekt
- [ ] Notebook liegt in `notebooks/` und läuft von oben nach unten durch
- [ ] `fecha_hora` wird vor dem Schreiben in ein Datum umgewandelt
- [ ] **Eine** gemeinsame Funktion für beide Engines — keine doppelte Logik
- [ ] Zeilenzahlen für PostgreSQL **und** SQLite werden ausgegeben
- [ ] Durchschnittstemperatur pro Gebäude ist zu sehen
- [ ] Gebäude mit dem höchsten CO₂-Durchschnitt ist zu sehen
- [ ] `docs/PROGRESO.md` ist aktualisiert (Status + Ergebnisse)
- [ ] Screenshot Nr. 02 liegt in `evidencias/`
- [ ] KI-Nachweis mit **allen** Prompt-Screenshots **oder** Nichtnutzungs-Erklärung
- [ ] Keine Passwörter oder Tokens in Repository oder Screenshots
- [ ] Push nach `main` erfolgt

---

## 11. Offene Punkte, die noch zu klären sind

| Punkt | Anmerkung |
|---|---|
| **Dateiname des Notebooks** | Der Dozent gibt keinen vor. Der Vorschlag `smartcampus_analisis.ipynb` ist nur ein Vorschlag — im Team abstimmen. |
| **Reto D (Ende-zu-Ende-Test)** | Ebenfalls aus dem Notebook heraus zu machen, mit `requests` gegen den Dienst `api`. Gehört nicht zu Reto B, schließt aber direkt daran an. Wer übernimmt das? |
| **Bonus-Aufgaben** | Fünf optionale Erweiterungen. Ausdrücklich **nicht** für die Höchstnote nötig. Erst nach den Pflichtteilen angehen. |

---

## 12. Ansprechpartner und Referenzen

| Thema | Datei |
|---|---|
| Aufgabenstellung, Bewertung, Bonus, KI-Regeln | `01_Enunciado/SmartCampus_Enunciado_Taller_UEV.pdf` |
| Datenstruktur des CSV | `02_Datos/DICCIONARIO_DE_DATOS.md` |
| Status des Projekts, Designentscheidungen, nächste Schritte | `docs/PROGRESO.md` |
| Wie die Images gebaut werden und warum | `docs/PROCESO_DE_COMPILACION.md` |
| Vorlage für die Projektdokumentation | `03_Plantillas/Plantilla_README_del_repositorio.md` |
| Vorlage für den KI-Nachweis | `03_Plantillas/Plantilla_memoria_uso_IA_Amarillo.docx` |
| Beispiel-JSON für Tests | `04_Ejemplos_pruebas/` |

**Bei Fragen zur Infrastruktur** (Compose, Images, Netzwerk, Ports): bei
tonyelos melden. **Bei Fragen zu Daten oder Analyse:** selbst entscheiden und
die Entscheidung dokumentieren — genau das verlangt die Bewertung.
