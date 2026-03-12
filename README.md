# TaskBoard Dashboard

Farbenfrohes Kanban-Board mit CLI, Git-Integration und automatischem Change-Tracking.
Funktioniert mit beliebig vielen Projekten — erkennt automatisch das aktuelle Repo.

## Setup

```bash
git clone https://github.com/Sternenstaubfee2/ToDoList.git
cd ToDoList
pip install flask
```

Optional: Umgebungsvariable setzen fuer bequemeren Zugriff:
```bash
# Bash (.bashrc / .zshrc)
export TASKBOARD="$(pwd)/cli.py"
alias tb="python $TASKBOARD"

# PowerShell ($PROFILE)
$env:TASKBOARD = "C:\pfad\zu\ToDoList\cli.py"
function tb { python $env:TASKBOARD @args }
```

## Setup auf neuem Rechner

Wenn du das TaskBoard auf einem anderen Rechner (z.B. Arbeitsrechner) nutzen willst:

### 1. Repo clonen und Abhaengigkeiten installieren

```bash
git clone https://github.com/Sternenstaubfee2/ToDoList.git
cd ToDoList
pip install flask
```

### 2. Claude Skill installieren (fuer Claude Code Integration)

Den `ticket-committer` Skill aus dem Repo in das Claude-Skill-Verzeichnis kopieren:

```bash
# Windows (PowerShell)
xcopy /E /I skills\ticket-committer $env:USERPROFILE\.claude\skills\ticket-committer

# Windows (Git Bash)
cp -r skills/ticket-committer ~/.claude/skills/

# Mac/Linux
cp -r skills/ticket-committer ~/.claude/skills/
```

### 3. Arbeitsprojekt registrieren

Im Verzeichnis des Arbeitsprojekts:
```bash
cd /pfad/zum/arbeitsprojekt
python /pfad/zu/ToDoList/cli.py init -l "Mein Arbeitsprojekt" --hook
```

Das registriert das Repo fuer Auto-Detection und installiert den Git-Hook.
Ab sofort funktioniert alles automatisch:
- `cli.py list` erkennt das Projekt anhand des Repos
- Commits mit `#ticket_id` werden automatisch getrackt
- Der `ticket-committer` Skill in Claude Code greift nahtlos

### 4. Optional: Bestehende TODO.md importieren

Falls das Projekt eine TODO.md hat:
```bash
python /pfad/zu/ToDoList/importer.py TODO.md mein_projekt "Mein Projekt" .
```

### 5. Dashboard starten

```bash
cd /pfad/zu/ToDoList && python app.py
# -> http://localhost:5555 — zeigt alle registrierten Projekte
```

### Hinweis: data/ ist maschinenspezifisch

Das `data/`-Verzeichnis ist in `.gitignore` und wird NICHT synchronisiert.
Jeder Rechner hat seine eigenen Projekt-Registrierungen (mit lokalen Repo-Pfaden).
Die Tickets selbst leben lokal — fuer projektuebergreifendes Tracking nutze die
TODO.md-Sync-Funktion, die ins jeweilige Projekt-Repo schreibt.

## Dashboard starten

```bash
python app.py
# -> http://localhost:5555
```

## Schnellstart: Neues Projekt registrieren

### Variante 1: Aus einem Git-Repo (empfohlen)

Im Repo-Verzeichnis:
```bash
cd /pfad/zum/repo
python /pfad/zu/ToDoList-Repo/cli.py init --hook
```

Oder mit expliziten Angaben:
```bash
python cli.py init -r /pfad/zum/repo --id mein_projekt -l "Mein Projekt" --hook
```

Das erstellt das Projekt mit Standard-Kategorien (Bugs, Features, Ops, Docs),
registriert das Repo fuer Auto-Detection und installiert optional den Git-Hook.

### Variante 2: Aus einer bestehenden TODO.md

```bash
python importer.py pfad/TODO.md mein_projekt "Mein Projekt" /pfad/zum/repo
```

### Variante 3: Leeres Projekt via CLI

```bash
python cli.py -p mein_projekt add "Erstes Ticket" -c feature -P 2
```

## CLI-Befehle

```bash
# Tasks verwalten
python cli.py list                              # Alle Tasks anzeigen
python cli.py list -s todo                      # Nur offene Tasks
python cli.py list -s in-progress               # Nur laufende Tasks
python cli.py done <id>                         # Task als erledigt markieren
python cli.py progress <id>                     # Task auf "In Arbeit" setzen
python cli.py todo <id>                         # Task zurueck auf "Offen"
python cli.py add "Titel" -c feature -P 2       # Neuer Task
python cli.py add "Titel" -d "Beschreibung"     # Neuer Task mit Beschreibung
python cli.py note <id> "Notiz-Text"            # Notiz an Task anhaengen

# Change-Tracking
python cli.py track <id> -r <repo-pfad>         # Letzten Commit ins Ticket tracken
python cli.py track <id> -c <commit-hash>       # Bestimmten Commit tracken

# Projekt-Verwaltung
python cli.py init                              # Aktuelles Repo als Projekt registrieren
python cli.py init -r /pfad --hook              # Mit Git-Hook
python cli.py install-hook <repo-pfad>          # Post-commit Hook installieren
python cli.py projects                          # Alle Projekte auflisten
```

### Auto-Detection

Die CLI erkennt automatisch, welches Projekt zum aktuellen Git-Repo gehoert.
Wenn du dich im registrierten Repo befindest, brauchst du kein `-p`.

Manuell ein anderes Projekt waehlen:
```bash
python cli.py -p anderes_projekt list
```

## Features

### Kanban-Board (Web)
- 3 Spalten: Offen / In Arbeit / Erledigt
- Tasks farbcodiert nach Kategorie (frei konfigurierbar pro Projekt)
- Drag & Drop zwischen Spalten
- Doppelklick zum Bearbeiten
- Aufwand-Badges (Minor/Medium/Major/Epic)
- Zeitschaetzung (Freitext: 2h, 1d, 1w)
- Personen-Zuweisung mit Initialen-Avatar
- Multi-Projekt-Navigation in der Navbar

### TODO.md Sync
Jede Aenderung (GUI, CLI, API) schreibt automatisch die TODO.md im Projekt-Ordner zurueck.
Format:
```markdown
- [ ] **Titel** *(in Arbeit)* [Major, 2d, @Julia]
```

### Git Sync
Button im Dashboard scannt Commits nach Keywords (`done:`, `closes #`, `fixes #`)
und markiert passende Tasks als erledigt.

## Change-Tracking

Commits werden automatisch in Tickets dokumentiert. Drei Wege:

### 1. Automatisch per Git Hook

Post-commit Hook installieren (einmalig pro Repo):
```bash
python cli.py install-hook /pfad/zum/repo
```

Danach: Ticket-ID mit `#` in der Commit-Message referenzieren:
```bash
git commit -m "Login-Bug gefixt #a1b2c3d4"
```

Der Hook liest den Diff und schreibt automatisch eine Zusammenfassung in die Ticket-Notizen:
```
--- Commit a3f7b2c (2026-03-12 14:30) ---
Login-Bug gefixt

  Geaenderte Dateien (2):
    ~ auth/login.py
    ~ tests/test_login.py
  Gesamt: 2 Dateien betroffen
  2 files changed, 15 insertions(+), 3 deletions(-)
```

### 2. Manuell per CLI

Von einer anderen Claude-Instanz oder aus einem anderen Verzeichnis:
```bash
python /pfad/zu/ToDoList-Repo/cli.py track <ticket_id> -r .
```

### 3. Per API

Wenn das Dashboard laeuft:
```bash
curl -X POST http://localhost:5555/api/<projekt>/tasks/<id>/track
```

## Aufwand-Stufen

| Stufe  | Bedeutung                           | Farbe  |
|--------|-------------------------------------|--------|
| Minor  | Kleiner Fix, unter 1 Stunde         | Gruen  |
| Medium | Feature-Teil, ein paar Stunden      | Orange |
| Major  | Tagewerk, mehrere Dateien           | Rot    |
| Epic   | Mehrtaegig, architektonische Arbeit  | Lila   |

## Claude-Integration (ticket-committer Skill)

Der `ticket-committer` Skill verbindet Claude Code mit dem TaskBoard.
Er wird automatisch getriggert bei Commits, Ticket-Erstellung und Implementierungsarbeit.

### Skill installieren

Kopiere den Skill in dein Claude-Skill-Verzeichnis:
```bash
cp -r skills/ticket-committer ~/.claude/skills/
```

Passe den Pfad zur CLI in `SKILL.md` an deine Maschine an (Zeile `TASKBOARD_CLI`).

### Workflow

1. Claude prueft offene Tickets oder erstellt ein neues
2. Setzt das Ticket auf "In Arbeit"
3. Implementiert die Aenderung
4. Committed mit `#ticket_id` in der Message
5. Trackt den Commit ins Ticket
6. Markiert das Ticket als erledigt

Der Skill funktioniert projektuebergreifend dank Auto-Detection.

## Workflow: Neues Arbeitsprojekt von Null aufsetzen

Beispiel: Du startest ein neues Projekt auf der Arbeit.

### 1. Projekt registrieren

```bash
cd /arbeit/mein-api-projekt
python /pfad/zu/ToDoList-Repo/cli.py init -l "API Projekt" --hook
```

Output:
```
  + Projekt erstellt: API Projekt (mein_api_projekt)
    Repo: /arbeit/mein-api-projekt
  + Post-commit hook installiert
```

### 2. Tickets anlegen

```bash
python /pfad/zu/ToDoList-Repo/cli.py add "REST-Endpoints implementieren" -c feature -P 2
# → #a1b2c3d4

python /pfad/zu/ToDoList-Repo/cli.py add "Auth-Middleware einbauen" -c feature -P 1
# → #e5f6a7b8
```

### 3. Arbeit beginnen — Ticket auf "In Arbeit" setzen

```bash
python /pfad/zu/ToDoList-Repo/cli.py progress a1b2c3d4
```

### 4. Implementieren und committen

Normal arbeiten, dann committen mit `#ticket_id`:

```bash
git add routes.py models.py
git commit -m "REST-Endpoints fuer Users und Orders #a1b2c3d4"
```

Der Post-Commit-Hook schreibt automatisch eine Zusammenfassung ins Ticket:
welche Dateien geaendert, wieviele Zeilen, was der Commit macht.

### 5. Ticket abschliessen

```bash
python /pfad/zu/ToDoList-Repo/cli.py done a1b2c3d4
```

### 6. Dashboard anschauen

```bash
cd /pfad/zu/ToDoList-Repo && python app.py
# -> http://localhost:5555
```

Alle Projekte (privat + Arbeit) erscheinen in der Navigation.
Jedes Ticket zeigt die getrackten Commits in den Notizen.

### 7. Von Claude Code aus (mit ticket-committer Skill)

Wenn Claude Code im Repo arbeitet, triggert der `ticket-committer` Skill automatisch:

```
User: "Implementiere die Auth-Middleware"

Claude:
  1. Prueft offene Tickets → findet #e5f6a7b8
  2. Setzt es auf "In Arbeit"
  3. Implementiert die Aenderung
  4. Fragt: "Soll ich committen?"
  5. git commit -m "Auth-Middleware mit JWT implementiert #e5f6a7b8"
  6. Trackt den Commit → Ticket zeigt alle geaenderten Files
  7. Markiert Ticket als erledigt
```

Alles automatisch, kein manuelles Tracking noetig.

## API-Endpunkte

| Methode | Pfad                                | Beschreibung                |
|---------|-------------------------------------|-----------------------------|
| GET     | `/board/<project>`                  | Dashboard anzeigen          |
| GET     | `/api/<project>/tasks`              | Alle Tasks als JSON         |
| POST    | `/api/<project>/tasks`              | Neuen Task erstellen        |
| PUT     | `/api/<project>/tasks/<id>`         | Task aktualisieren          |
| DELETE  | `/api/<project>/tasks/<id>`         | Task loeschen               |
| POST    | `/api/<project>/tasks/<id>/track`   | Commit ins Ticket tracken   |
| GET     | `/api/<project>/members`            | Team-Mitglieder auflisten   |
| POST    | `/api/<project>/members`            | Mitglied hinzufuegen        |
| DELETE  | `/api/<project>/members/<name>`     | Mitglied entfernen          |
| POST    | `/api/<project>/git-sync`           | Git-Commits scannen         |

## Dateistruktur

```
ToDoList-Repo/
├── app.py              # Flask Server (Port 5555)
├── tasks.py            # Daten-Layer (JSON CRUD + TODO.md Export + Auto-Detection)
├── importer.py         # TODO.md Parser (Erst-Import)
├── tracker.py          # Git Change-Tracking (Hook + manuell)
├── git_sync.py         # Git-Commit Scanner (Keywords -> Status-Update)
├── cli.py              # Terminal-Tool (mit Auto-Detection)
├── requirements.txt    # Python-Abhaengigkeiten (nur flask)
├── skills/
│   └── ticket-committer/
│       └── SKILL.md    # Claude-Skill (kopieren nach ~/.claude/skills/)
├── data/               # (gitignored) Task-Daten pro Projekt
│   └── <project>.json
├── static/
│   ├── style.css       # Dashboard-Styling
│   └── app.js          # Frontend-Logik (Drag&Drop, Modal, API)
└── templates/
    └── board.html      # Kanban-Board Template
```
