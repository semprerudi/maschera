# Änderungen

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
