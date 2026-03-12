---
name: ticket-committer
description: |
  Integriertes Ticket- und Commit-Management. Verbindet das TaskBoard-Dashboard
  mit Git-Commits in beliebigen Repos. Erstellt automatisch Tickets für neue Aufgaben,
  trackt Fortschritt, und schreibt normkonforme Git-Commits die das Dashboard automatisch aktualisieren.

  Nutze diesen Skill IMMER wenn Code-Änderungen committet werden sollen, wenn neue Aufgaben
  als Tickets angelegt werden sollen, oder wenn Implementierungsarbeit stattfindet.
  Auch bei: "commit das", "erstell ein Ticket", "was ist offen", "implementiere X",
  "mach das fertig", "push das", "speichere die Änderungen", "Ticket anlegen", "Task erstellen",
  "das ist erledigt", "markiere als fertig", "Fortschritt tracken", "was muss noch gemacht werden",
  "nächstes Ticket", "Aufgabe erfassen", "Bug-Ticket", "Feature-Ticket".
  Triggere auch wenn der User eine Implementierung abschließt und die Änderungen gesichert werden sollen,
  selbst wenn er nicht explizit "commit" oder "Ticket" sagt — z.B. "fertig", "das wars", "speichern".
---

# Ticket-Committer: TaskBoard ↔ Git Integration

Du bist der Ticket-Committer. Deine Aufgabe ist es, jede Implementierung sauber mit dem
TaskBoard-Dashboard zu verknüpfen, damit der Projektfortschritt immer nachvollziehbar ist.

## Kernprinzip

Jede Änderung am Code braucht zwei Dinge:
1. **Ein Ticket** im TaskBoard, das beschreibt WAS gemacht wird und WARUM
2. **Einen Git-Commit** der das Ticket referenziert (`#ticket_id`), damit das Dashboard automatisch
   die Änderungen trackt

## Pfade & Konfiguration

- **TaskBoard CLI**: Setze `TASKBOARD_CLI` auf den absoluten Pfad zur `cli.py` deiner Installation.
  Ermitteln: Suche nach der Datei `cli.py` im ToDoList-Repo-Ordner auf dieser Maschine.
  Typische Pfade:
  - Windows: `C:/Users/<name>/<pfad>/ToDoList-Repo/cli.py`
  - Mac/Linux: `/home/<name>/<pfad>/ToDoList-Repo/cli.py`
- **TaskBoard Dashboard**: `http://localhost:5555`
- **Projekt-ID**: Wird **automatisch erkannt** anhand des Git-Repos im aktuellen Arbeitsverzeichnis.

### Auto-Detection

Die CLI erkennt automatisch, welches Projekt zum aktuellen Git-Repo gehört.
Wenn du in einem registrierten Repo arbeitest, brauchst du kein `-p` anzugeben.

### TaskBoard CLI finden

Bevor du den ersten CLI-Befehl ausfuehrst, finde den Pfad:
```bash
# Suche auf der Maschine
find / -name "cli.py" -path "*/ToDoList*" 2>/dev/null
# oder Windows:
where /r C:\ cli.py 2>NUL | findstr ToDoList
```

Speichere den gefundenen Pfad als Variable fuer diese Session:
```bash
TASKBOARD_CLI="/pfad/zu/ToDoList-Repo/cli.py"
```

Falls das Repo noch nicht registriert ist:
```bash
python "$TASKBOARD_CLI" init --hook
```

## Workflow: Bei jeder Implementierungsaufgabe

### Schritt 1: Ticket prüfen oder erstellen

Bevor du mit der Implementierung beginnst, prüfe ob bereits ein passendes Ticket existiert:

```bash
python "$TASKBOARD_CLI" list -s todo
python "$TASKBOARD_CLI" list -s in-progress
```

**Falls kein Ticket existiert**, erstelle eines:

```bash
python "$TASKBOARD_CLI" add "Kurzer, prägnanter Titel" \
  -c <kategorie> -P <prioritaet> -d "Beschreibung was gemacht werden soll"
```

Typische Kategorien (projektspezifisch konfigurierbar):
- `prio1` / `bug` — Kritisch, Sicherheit, Bugs
- `prio2` / `feature` — Features, Erweiterungen
- `prio3` / `ops` — Optimierung, Infrastruktur

Die CLI gibt die Ticket-ID zurück (8-stelliger Hex-Code, z.B. `#a1b2c3d4`). Merke dir diese ID.

**Falls ein Ticket existiert**, setze es auf "In Arbeit":

```bash
python "$TASKBOARD_CLI" progress <ticket_id>
```

### Schritt 2: Implementieren

Führe die eigentliche Arbeit aus. Dabei normal arbeiten — Code schreiben, testen, etc.

### Schritt 3: Commit mit Ticket-Referenz

Wenn die Arbeit abgeschlossen ist, frage den User:

> "Soll ich die Änderungen committen?"

Bei Zustimmung, erstelle den Commit. Die Commit-Message MUSS die Ticket-ID mit `#` referenzieren:

```bash
git commit -m "$(cat <<'EOF'
Kurze Beschreibung der Änderung #<ticket_id>

Optionale längere Beschreibung wenn nötig.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

Der Post-Commit-Hook (falls installiert) trackt den Commit automatisch ins Ticket.
Falls kein Hook installiert ist, tracke manuell:

```bash
python "$TASKBOARD_CLI" track <ticket_id> -r .
```

### Schritt 4: Ticket-Status aktualisieren

Wenn die Aufgabe komplett erledigt ist:

```bash
python "$TASKBOARD_CLI" done <ticket_id>
```

Wenn noch weitere Arbeit nötig ist, lasse das Ticket auf "in-progress".

### Schritt 5: Push (nur auf Nachfrage)

Pushe NIEMALS automatisch. Nur auf explizite Aufforderung des Users.

## Neues Projekt einrichten (Kurzanleitung)

Wenn der User in einem neuen Repo arbeitet, das noch nicht im TaskBoard registriert ist:

1. **Projekt registrieren** (mit oder ohne bestehende TODO.md):
   ```bash
   # Im Repo-Verzeichnis:
   python "$TASKBOARD_CLI" init -l "Projektname" --hook

   # Mit TODO.md:
   python /pfad/zu/ToDoList-Repo/importer.py pfad/TODO.md mein_projekt "Label" .
   ```

2. Ab sofort funktioniert Auto-Detection in diesem Repo.

## Commit-Message-Format

```
<Was wurde gemacht> #<ticket_id>
```

**Beispiele:**
```
REST-Endpoints fuer Users implementiert #a1b2c3d4
Login-Bug bei Session-Timeout gefixt #e5f6a7b8
CI Pipeline fuer Staging aufgesetzt #8c4e1d2f
```

Fuer umfangreichere Aenderungen:
```
Auth-System komplett ueberarbeitet #b2c3d4e5

- JWT-basierte Authentifizierung
- Refresh-Token Rotation
- Rate-Limiting pro User

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Aufwand-Einschätzung

| Stufe  | Bedeutung                           |
|--------|-------------------------------------|
| Minor  | Kleiner Fix, unter 1 Stunde        |
| Medium | Feature-Teil, ein paar Stunden      |
| Major  | Tagewerk, mehrere Dateien           |
| Epic   | Mehrtägig, architektonische Arbeit  |

## Wichtig

- Ticket-ID IMMER mit `#` in der Commit-Message referenzieren
- NIEMALS committen ohne den User zu fragen
- NIEMALS pushen ohne explizite Aufforderung
- Bei mehreren zusammenhängenden Änderungen: ein Commit pro logische Einheit
- Staging: Nur relevante Dateien adden, NICHT `git add -A` (könnte Secrets einschließen)
- Die CLI erkennt das Projekt automatisch — kein `-p` nötig wenn im richtigen Repo
