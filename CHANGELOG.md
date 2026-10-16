# Änderungen

## 1.0.5 – 2026-10-16

### Neu
- **Entfernen im Vokabular:** jede Zeile hat ein rotes ×. Ein Klick nimmt den
  Platzhalter im ganzen Dokument zurück — bei langen Dokumenten mit viel
  Übermaskierung schneller als über das Klappmenü im Text.
- **«Nach Updates suchen»** im Menü: fragt GitHub einmal nach der neuesten
  Fassungsnummer, nur auf Klick, über den eigenen Server. Mitgeschickt wird
  nichts. Im Docker-Betrieb (ohne Netz nach aussen) sagt es das und zeigt den
  Weg zur Download-Seite.

### Geändert
- Schmale Fenster: die Trennlinien zwischen den Bereichen sind deutlich
  dicker; nebeneinander bleiben sie dünn.

### Sicherheit (Prüfung mit einem lokalen Modell, am Code nachgeprüft)
- Das Modell wird von einem festen Commit auf Hugging Face geholt, nicht
  von `main`.
- Der Name einer hochgeladenen Datei wird nie zum Pfad (unter Windows sind
  `con.txt` oder `aux.pdf` Geräte).
- Laute Warnung beim Start, wenn `MASCHERA_WIRT=*` die Namensprüfung abschaltet.
- Kein `exec`/`eval` mehr im Projekt, mit einer Wache dagegen.

### Behoben
- Ein Zeichen ohne eigene Grössenregel stand leer da; jedes Zeichen hat jetzt
  eine Grundgrösse.

### Bekannt
- Der Windows-Installer und die macOS-App sind weiter **nicht signiert**.

## 1.0.4 – 2026-10-11

### Sicherheit
- Werkzeug ≥ 3.1.9 (CVE-2026-102598): unter **Windows** liess sich eine
  Anfrage mit einem Gerätenamen wie `NUL:` endlos hängen (lokaler DoS). Linux,
  macOS und Docker waren nicht betroffen.
- Die Bauten holen jetzt jedes Mal das neueste Python 3.13: Docker mit
  `--pull`, das AppImage mit `uv python upgrade`. Das AppImage 1.0.3 lief noch
  auf 3.13.15; 3.13.16 behebt eine Lücke in `zipfile` (CVE-2026-15310), das
  beim Lesen von Word-Dateien gebraucht wird.

### Geändert
- Was sich nicht als Datei ablegen lässt — etwa eine Nachricht direkt aus
  Apple Mail —, meldet sich jetzt in vier Sprachen, statt still nichts zu tun:
  zuerst auf den Schreibtisch ziehen, dann hierher.
- Der Windows-Installer wird jetzt wie das macOS-Paket auf GitHub gebaut
  (`.github/workflows/pakete.yml`), aus einer frischen Umgebung.

### Bestätigt
- macOS: «Kopieren und … öffnen» öffnet den Dienst auch in der App (getestet
  mit 1.0.3 am 4.10.2026).

## 1.0.3 – 2026-10-04

### Behoben
- macOS (und Windows): «Kopieren und … öffnen» öffnet den Dienst jetzt wie ein
  Link im Burgermenü. Die Anwendung startet das Kopieren, klickt im selben Zug
  einen echten Verweis an und wartet erst danach. Die Brücke zur Anwendung aus
  1.0.2 half nicht und ist wieder weg. Linux und der Browser bleiben, wie sie
  waren.
- macOS: die Fehlzeile zu `multiprocessing.resource_tracker` beim Start ist weg.
  Erkannt und aufgerufen wird genau dieser eine Aufruf der Standardbibliothek;
  Text aus den Startargumenten wird nie ausgeführt.

### Bekannt
- macOS, in der App: ob «Kopieren und … öffnen» den Dienst öffnet, ist auch
  mit dieser Änderung **nicht bestätigt** (im Server-/Browserbetrieb geht es). Der
  Text liegt in jedem Fall in der Zwischenablage; der Dienst lässt sich von Hand
  öffnen.

### Geändert
- Die Dienste stehen alphabetisch (ChatGPT, Claude, Copilot, Gemini, Mistral),
  im Pulldown und in den Einstellungen. **Mistral** ist neu in der Vorgabe.
  Gewählt bleibt Claude. Wer schon eine eigene Liste gespeichert hat, behält sie;
  angezeigt wird sie ebenfalls alphabetisch.

## 1.0.2 – 2026-10-03

Gefunden beim ersten Test auf macOS und durch CodeQL.

### Neu
- **macOS** (nur Apple-Chip, M1 oder neuer): `MASCHERA-latest-arm64.dmg`, rund
  1,4 GB, das Modell fährt mit. Gebaut auf GitHub (`.github/workflows/macos.yml`),
  auf einem Mac von Hand getestet. Nicht signiert: nach dem Ziehen in
  «Programme» einmal `xattr -dr com.apple.quarantine /Applications/MASCHERA.app`
  im Terminal.
- Die Seite www.maschera.ch zeigt macOS als Download; `site/` im Repository
  ist der Stand der Seite, `tools/seite.py` vergleicht und lädt hoch.

### Nachträglich (3.10.2026)
- Das Docker-Abbild 1.0.2 ist mit cosign signiert; die README erklärt, wie man
  Prüfsummen und Signatur prüft.

### Behoben
- «Kopieren und … öffnen» tat unter macOS nichts: `window.open` verliert dort
  nach dem Kopieren die Nutzergeste, und pywebview baut kein Popup. Unter macOS
  und Windows öffnet jetzt die Anwendung die Adresse im Standardbrowser, und nur
  eine Adresse aus den eigenen Diensten. Linux und der Browser bleiben, wie sie
  waren.
- macOS: die App hat ein eigenes Symbol (vorher das allgemeine einer App).
- `MASCHERA_PORT` im AppImage: das Startskript gab `--port` an das Fenster
  weiter, das diese Option nicht kennt; wer die Variable setzte, bekam einen
  Abbruch. Jetzt gilt sie als Übersteuerung für diesen einen Start und wird
  nicht gespeichert.

### Sicherheit
- Antworten der lokalen Schnittstelle nennen den Text einer Bibliotheks-Ausnahme
  nicht mehr (CodeQL `py/stack-trace-exposure`). Bis 1.0.1 stand dort etwa der
  Pfad einer temporären Datei; bei der Docker-Fassung im Netz verriet das
  Serverpfade. Der Text steht im Protokoll des Servers.

### Bekannt
- macOS: die App ist nicht signiert. Unter neueren macOS-Fassungen genügt
  «Rechtsklick → Öffnen» nicht; es braucht in der Konsole
  `xattr -dr com.apple.quarantine /Applications/MASCHERA.app`.
- macOS: beim Start meldet ein Hilfsprozess eine Fehlerzeile zu
  `multiprocessing.resource_tracker`. Sie stört den Betrieb nicht.

## 1.0.1 – 2026-10-03

### Sicherheit
- Untergrenzen der Abhängigkeiten über bekannte Lücken angehoben: torch ≥ 2.13,
  transformers ≥ 5.10, Flask ≥ 3.1.3, Werkzeug ≥ 3.1.6, Jinja2 ≥ 3.1.6,
  gunicorn ≥ 22.0 (Entwicklung: onnx ≥ 1.22). Geprüft mit torch 2.14.1 (CPU),
  transformers 5.18.0 und Werkzeug 3.1.9; `pip-audit` meldet für diesen Stand
  keine bekannte Lücke.
- Das Modell wird ausschliesslich aus `model.safetensors` geladen, ohne
  stillen Rückgriff auf Pickle-Dateien.
- Trainingsartefakte (`training_args.bin`) fahren nicht mehr in AppImage,
  Windows-Paket und Docker-Abbild mit.
- Neu: `SECURITY.md` mit dem Meldeweg für Sicherheitslücken.

### Dokumentation
- Die Messtabelle in der README auf den heute reproduzierbaren Stand gebracht
  (synthetisch 13 Lecks bei 29 210 Spannen statt «0 Lecks»). Die alten Zahlen
  stammten aus einer Messung vom August; die Vorlagen und der Erzeuger haben
  sich seither geändert, und der Befehl in der README lieferte schon vor
  1.0.0 etwas anderes.
- Neu: Abschnitt «Wie es entstanden ist» (Claude Code) in beiden READMEs.

### Unverändert
- Modell `ch-v63b` und Labelvertrag `b7a96dc9`.
- Messung vor und nach dem Update identisch (CPU, torch 2.14.1): synthetisch
  13 Lecks bei 29 210 Spannen (0.02 %), Micro-F1 0.997, 84 Übermaskierungen;
  Golddokumente 6 Lecks bei 280 Spannen (1.27 %), Micro-F1 0.736,
  95 Übermaskierungen.

## 1.0.0 – 2026-09-26
- Erste öffentliche Fassung: Linux (AppImage, Flatpak), Windows, Docker.
