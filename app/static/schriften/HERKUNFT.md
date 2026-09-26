# Schriften

**Barlow** und **Barlow Condensed**, gestaltet von Jeremy Tribby.
Copyright 2017 The Barlow Project Authors — <https://github.com/jpt/barlow>

Lizenz: **SIL Open Font License 1.1**, vollständiger Text in `OFL.txt`.

## Warum sie hier liegen und nicht geladen werden

Ein Werkzeug, das damit wirbt, dass der Text das Gerät nicht verlässt, darf
beim Öffnen keine Verbindung nach aussen aufbauen. Schon der Abruf einer
Schrift von einem fremden Server verrät, dass und wann jemand MASCHERA
benutzt — ohne dass ein Zeichen des Dokuments übertragen würde.

`tests/test_app.py` prüft jede ausgelieferte Datei darauf.

## Welche Teilmengen und warum

Zehn Dateien: fünf Schnitte (Barlow 400/500/700, Barlow Condensed 400/600)
mal zwei Teilmengen (`latin`, `latin-ext`). Zusammen 178 KB.

⚠️ **Vietnamesisch fehlt absichtlich.** Seit dem 11.11.2024 gilt in den
Schweizer Personenregistern ein einheitlicher Zeichensatz: **ISO 8859-1 +
Latin Extended-A** (Bundesratsentscheid vom 12.5.2021, seit dem 11.11.2024
in Kraft). Was in einem Schweizer Namen stehen kann, ist damit amtlich
festgelegt: `U+0020–U+00FF` und `U+0100–U+017F`. Die beiden gewählten
Teilmengen decken genau das ab. Vietnamesisch liegt ausserhalb und hätte
37 KB für nichts gekostet.

## Was Barlow nicht abdeckt

310 der 319 druckbaren Zeichen. Die neun Lücken stehen mit Begründung in
`tests/test_schriften.py`; die Prüfung schlägt an, sobald eine zehnte
dazukommt.

Zwei davon haben Namensbezug: `Ĳ` (niederländische Ligatur, gross) und `Ŀ`
(katalanisches L mit Mittelpunkt, gross). Die Kleinformen `ĳ` und `ŀ` sind
vorhanden — es fehlen ausgerechnet die, die am Anfang eines Nachnamens
stünden. Der Browser fällt dort zeichenweise auf eine Systemschrift zurück.
