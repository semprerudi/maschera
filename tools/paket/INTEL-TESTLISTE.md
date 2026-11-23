# MASCHERA auf einem Intel-Mac testen

Für einen Test von Hand auf echter Hardware. Der Bau auf GitHub prüft schon, dass das
Paket startet und vier erfundene Briefe richtig maskiert; was er nicht kann, steht hier.
Dauer: rund 20 Minuten.

**Bitte nie ein echtes Dokument und keine echten Namen verwenden.** Für den Test genügt
ein erfundener Brief, zum Beispiel: «Sehr geehrte Frau Petra Muster, Ihr Termin am
12. März 2026 an der Bahnhofstrasse 14 in 4600 Olten ist bestätigt.»

## Vorher notieren

- [ ] Mac-Modell und Jahr (Apple-Menü › *Über diesen Mac*)
- [ ] macOS-Fassung (dort ebenfalls)
- [ ] Prozessor: steht dort «Prozessor» mit Intel? Dann ist es der richtige Mac.

Am wertvollsten sind ein Mac mit **macOS 13 Ventura** (das älteste unterstützte) und
einer mit **macOS 26** (das neueste für Intel).

## Installieren

1. [ ] `MASCHERA-latest-x86_64.dmg` von der Release-Seite laden.
2. [ ] Prüfsumme: im *Terminal* `shasum -a 256 ~/Downloads/MASCHERA-latest-x86_64.dmg`
   und mit der Zeile in `SHA256SUMS` vergleichen.
3. [ ] Abbild öffnen, `MASCHERA` in *Programme* ziehen.
4. [ ] Einmal im *Terminal*:
   `xattr -dr com.apple.quarantine /Applications/MASCHERA.app`
5. [ ] Erster Start per Doppelklick. Notieren: Sekunden bis das Fenster steht und bis die
   Erkennung bereit ist.
6. [ ] Kommt eine Meldung, das Programm brauche ein neueres macOS? Dann ist das Minimum
   falsch: bitte macOS-Fassung melden.

## Bedienen

7. [ ] Den erfundenen Brief einfügen, «Maskieren». Werden Name, Datum, Strasse, PLZ und Ort
   ersetzt?
8. [ ] «Kopieren und … öffnen»: öffnet sich der Dienst im Standardbrowser, ist der Text in
   der Zwischenablage?
9. [ ] Ein PDF mit Textebene (selbst erstellt, aus Pages oder Word «Als PDF sichern») ins
   Fenster ziehen. Wird es gelesen?
10. [ ] Ein PDF ohne Textebene (ein Foto als PDF): erscheint der Hinweis, dass kein Text
    gefunden wurde?
11. [ ] Fenster breit ziehen: drei Spalten. Schmal ziehen: eine Spalte, Seitenleiste schmal.
12. [ ] Einstellungen ändern (Sprache, Schriftgrösse), MASCHERA beenden und neu starten.
    Bleiben sie?

## Was geschrieben und gesendet wird

13. [ ] Im *Terminal* `ls ~/.config/maschera/`: dort und nur dort liegen die Einstellungen.
14. [ ] `find ~ -newer /Applications/MASCHERA.app -name "*maschera*" 2>/dev/null` nach einem
    Lauf: nichts ausser `~/.config/maschera/` (und Einträgen von macOS selbst).
15. [ ] Kein Netzverkehr im Betrieb: in der *Aktivitätsanzeige* › *Netzwerk* den Prozess
    MASCHERA ansehen, während maskiert wird. Gesendet werden sollte 0 Byte. (Ausnahme nur
    «Nach Updates suchen», wenn man darauf klickt.)

## Messen

16. [ ] *Aktivitätsanzeige* › *Speicher*: Arbeitsspeicher von MASCHERA nach dem Maskieren.
    Erwartet unter 1 GB.
17. [ ] Zeit für das Maskieren eines längeren Textes, zum Beispiel den Brief zwanzigmal
    hintereinander eingefügt.

## Zurückmelden

Bitte die Nummern mit «ok» oder einer kurzen Beschreibung, dazu Mac-Modell, macOS-Fassung,
Startzeit, Speicher und Zeit aus 16 und 17. Fehler gern als
[Issue](https://github.com/semprerudi/maschera/issues), ohne echte Dokumente.
