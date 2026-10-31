# Regeln

## Wie geprüft wird

```
python3 tools/run_tests.py
```

Keine Abhängigkeiten ausser PyYAML und Flask für den Grossteil. Kein Modell,
keine GPU, keine Downloads nötig. Einige Erfahrungen stecken in der Art, wie
hier geprüft wird:

**Grosszügige Attrappen verschlucken Fehler.** Eine DOM-Attrappe, die für
alles ein Objekt liefert und `remove()` zur leeren Funktion macht, lässt
einen Absturz, der jeden Knopf lahmlegt, unsichtbar. Die Attrappe in
`tests/test_oberflaeche.js` ist deshalb **streng**: nicht vorhanden heisst
`null`, und jeder Zugriff darauf wirft.

**Eine Zusage im Kommentar ist keine Prüfung.** Die Frage, die am Anfang
steht: *welche Zusage steht in einem Kommentar und in keiner Prüfung?*

**Eine übersprungene Prüfung ist kein Erfolg.** Fehlt eine Abhängigkeit,
meldet die Prüfung `UEBERSPRUNGEN` am Zeilenanfang, und der Läufer zählt sie
nicht als bestanden, ein Skript, das sich selbst überspringt, gibt sonst 0
zurück.

**Der Einzelfall ist selten der Fall.** Dieselbe Sache mit mehreren
Verwaltern, ein Wert an mehreren Stellen, eine Liste in mehreren Dateien,
ist das häufigste Fehlermuster. Viele Prüfungen halten deshalb nicht einen
Wert fest, sondern die **Beziehung** zwischen den Stellen, die ihn tragen.
Die Frage gehört an den Anfang einer Fehlersuche: *welche anderen Stellen
haben dasselbe Muster?*

## Grundsätze, die nicht verhandelbar sind

| Grundsatz | Inhalt |
|---|---|
| Nichts wird geschrieben | Ausser Regeln, Vorlieben, Vorlagen und Einstellungen, alle nur auf ausdrücklichen Befehl. Kein Dokumentinhalt, kein Wörterbuch, kein Protokoll |
| `/api/senden` gibt es nicht | Kopieren und Dienst öffnen, eingefügt wird von Hand |
| Nie `innerHTML` mit Serverdaten | Ausnahmslos |
| Keine Erkennung im Browser | Die Kette läuft im Dienst |
| Kein Nachladen von aussen | Benannte Ausnahmen stehen in [13 Sicherheit](13_sicherheit.md) |
| Ein leerer Befund ist keine Entwarnung | Scan ohne Textebene ergibt 400 mit Begründung |
| Übermaskierung ist kein Leck | Ein unterdrücktes Datum ist teurer als eines zuviel |
| Der Labelvertrag ist eingefroren | Nicht ohne Messung ändern |
| Das Modell ist notwendig | `--ohne-modell` ist kein Betriebszustand |
| Eine Form je Sprache | Unbekannte Sprache ergibt 400, kein stiller Rückfall auf Deutsch |

## Oberfläche

- Alle Grössen in `rem`, gebunden an `--skala`. Feste Pixel nur für Kanten bis
  2 px.
- Jede Beschriftung in vier Sprachen, ein Schlüssel je Sprache genau einmal.
- `hidden` verliert gegen `display`: Jedes Element, dessen `hidden` das Skript
  setzt, braucht eine Gegenregel im CSS.
- Jede Bedienung bekommt ein Zeichen.
- Keine Gedankenstriche in Texten für Menschen. Eine Erklärung sagt zuerst, was
  man tun kann.
- Anrede in der Du-Form (fr `tu`, it `tu`).
- Die Kennung im Namen heisst **CH**, im Schriftzug MAS·CH·ERA.
- Unterstützt werden Deutsch, Französisch, Italienisch und Englisch. Rätoromanisch
  fehlt, und so steht es auch überall nach aussen.

## Fassungen

- `VERSION` in `app/serve.py` ist die einzige Quelle. Alle anderen Stellen lesen
  sie dort.
- Jede Auslieferung erhöht die dritte Stelle. Auslieferung heisst: Ein Bau
  verlässt die Maschine.
- Die Baunummer `vNNN` im Commit zählt Commits und steht nur dort.
- Vor einem Release laufen Rückmelderunden als `X.Y.Z-test.N`.

## Dokumentation

- Vor jedem Release wird die ganze Dokumentation nachgeführt, zuerst `specs/`.
- Ein neuer Prüfpunkt gehört zu einer Anforderung.
- Der Code gilt. Weicht der Katalog ab, wird er nachgezogen.

## Veröffentlichung

- Kein Name eines Entwicklers, kein Heimatpfad, kein Rechnername im öffentlichen
  Stand. Die Wache unterscheidet nicht nach Gross- und Kleinschreibung.
- Ein berechtigter Treffer wird als Ausnahme mit Begründung eingetragen, nie
  durch Streichen des Musters.
- Jeder öffentliche Commit nennt die Mitwirkung von Claude.

## Lehren aus Fehlern

- **Eine Regel braucht ein Merkmal.** Ein Satz wie «nicht bei jeder Änderung»
  sagt nicht, wann doch, und wird ausgelegt statt befolgt.
- **Eine Sperre braucht eine Begründung an der Sperre.** Eine Einordnung per
  Ähnlichkeit zum Nachbareintrag lässt sich später nicht überprüfen.
- **Eine Datei, zwei Verwalter.** Trat mehrmals auf: der Goldpfad an vier Orten,
  die Fassung an sechs, der Vorgabeport an neun. Dagegen hilft eine Quelle mit
  Prüfung.
- **Ein Abgleich darf nie überschreiben, was jemand getippt hat.** Mit `--update`
  und `--backup`, sonst verliert die zuletzt geschriebene Zeile.
- **Ein wortloser Sprung meldet Bereitschaft.** Was fehlt, muss sich melden.
- **Nach jeder Wache die Gegenprobe:** Fehler wieder einbauen, sonst ist
  unbekannt, ob die Prüfung prüft.
- **Grün heisst nur, was geprüft wurde.** Ein Hilfsprogramm kann ungeprüft Code
  mitbringen, wie die Telemetrie über eine Abhängigkeit zeigte: Laufzeitverbindungen
  gehören gemessen, nicht vermutet.
- **Eine Frage an die Daten geht vor der Vermutung.** Grösste offene Rätsel
  standen in vorhandenen Dateien, nur ungelesen.
