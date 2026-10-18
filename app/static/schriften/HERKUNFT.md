# Schriften

**IBM Plex Sans** und **IBM Plex Mono** fuer Oberflaeche und Texte (seit 2.0,
Entwurf des UX-Architekten). Copyright © 2017 IBM Corp., Reserved Font Name
«Plex» — <https://github.com/IBM/plex>. Plex Sans ist eine stufenlose Datei
(Gewicht 100–700), Plex Mono in 400 und 500. Die Dateien sind die
`latin`- und `latin-ext`-Teilmengen, wie Google Fonts sie ausliefert;
uebernommen aus dem Entwurf, nicht aus dem Netz geladen.

**Barlow Condensed** nur noch fuer die Wortmarke MAS**CH**ERA, gestaltet von
Jeremy Tribby. Copyright 2017 The Barlow Project Authors —
<https://github.com/jpt/barlow>. Barlow (die Textschrift bis 1.1) ist
entfernt.

Lizenz aller drei: **SIL Open Font License 1.1**, vollstaendiger Text in
`OFL.txt`.

## Warum sie hier liegen und nicht geladen werden

Ein Werkzeug, das damit wirbt, dass der Text das Gerät nicht verlässt, darf
beim Öffnen keine Verbindung nach aussen aufbauen. Schon der Abruf einer
Schrift von einem fremden Server verrät, dass und wann jemand MASCHERA
benutzt — ohne dass ein Zeichen des Dokuments übertragen würde.

`tests/test_app.py` prüft jede ausgelieferte Datei darauf.

## Welche Teilmengen und warum

Zehn Dateien, je in den Teilmengen `latin` und `latin-ext`: Plex Sans
(stufenlos), Plex Mono 400 und 500, Barlow Condensed 400 und 600.
Zusammen rund 200 KB.

⚠️ **Vietnamesisch fehlt absichtlich.** Seit dem 11.11.2024 gilt in den
Schweizer Personenregistern ein einheitlicher Zeichensatz: **ISO 8859-1 +
Latin Extended-A** (Bundesratsentscheid vom 12.5.2021, seit dem 11.11.2024
in Kraft). Was in einem Schweizer Namen stehen kann, ist damit amtlich
festgelegt: `U+0020–U+00FF` und `U+0100–U+017F`. Die beiden gewählten
Teilmengen decken genau das ab. Vietnamesisch liegt ausserhalb und hätte
37 KB für nichts gekostet.

## Abdeckung des amtlichen Zeichensatzes

Gemessen am 18.10.2026: IBM Plex Sans und Plex Mono decken **alle 319**
druckbaren Zeichen ab. Barlow Condensed 310 von 319 — das betrifft nur die
Wortmarke, keinen Personennamen. Die Luecken stehen je Schrift in
`tests/test_schriften.py`; die Pruefung schlaegt an, sobald sich etwas
aendert.
