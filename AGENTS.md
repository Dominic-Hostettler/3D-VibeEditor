# AGENTS.md — Workflow für AI-Agenten

Lokaler STL-Viewer + parametrische CAD-Modelle. Vollständiges Playbook:
`.devin/skills/3d-viewer/SKILL.md` — **immer zuerst lesen**, dort stehen
Details, die hier absichtlich nur skizziert sind.

## Projekt-Layout

- `model.py` → Starter-Template (Parameter oben im File; `model.stl` ist gitignored — Repo liefert kein Modell)
- `examples/*.py` → weitere Generatoren (z.B. `dragon.py` = implizites
  SDF-Modeling); aus dem Projekt-Root laufen lassen
- **Konvention: jeder Generator schreibt `model.stl`** (binär, mm,
  Z-up) — genau eine Output-Datei, wird überschrieben; „Neues Modell"
  im Viewer leert die Szene, kein separates File nötig
- `index.html` — Three.js Viewer; `serve.py` — Server auf :8000
- `preview.py` — rendert `_preview.png` eines STL zum Selbst-Check
- `.devin/skills/3d-viewer/chain_report.py` — löst Viewer-Element-IDs
  (P/E/F) aus der Zwischenablage auf

## Workflow

1. User schickt Element-IDs aus dem Viewer → **erst** `chain_report.py`
   laufen lassen (IDs verschieben sich nach jeder Regenerierung!)
2. Parameter in `model.py` (oder `examples/*.py`) ändern
3. Skript ausführen → Output muss **watertight** sein
4. Organisches Modell: zusätzlich `python preview.py` und das PNG
   ansehen, bevor dem User „fertig" gemeldet wird
5. Viewer lädt `model.stl` ~3 s nach Änderung selbst neu — kein
   manueller Reload nötig, Kamera bleibt

## Wichtigste Lektionen

- STL ist Z-up, Three.js Y-up → Viewer rotiert beim Laden (`rotateX`)
- CAD-Formen: cadquery; organische Formen: SDF-Feld + Marching Cubes
  (skimage). Signierte `smin`/`sdiff`-Helper stehen in `examples/dragon.py` —
  Vorzeichen nicht ändern, die sind so verifiziert
- Additive Teile müssen physisch im Volumen verankert sein, sonst
  schweben sie; Schnitte nicht durch den ganzen Querschnitt
- Feld-Debug: `(field < 0).sum()` je Stufe; detachierte Teile findet
  `mesh.split()`
- Installierte Pakete IMMER mit `pip install --user`
- Export nie über Browser-APIs mit Dateisystemzugriff — `serve.py`
  hat einen serverseitigen Save-Dialog (`POST /export`)

## Konventionen

- Antworten an den User: Deutsch; Code/Kommentare: Englisch
- Keine Kommentare löschen; kompakter Stil
- Kein `git config` anfassen; nicht pushen ohne explizite Anweisung
