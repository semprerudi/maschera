# MASCHERA: Anforderungskatalog

Dieser Ordner beschreibt das ganze System: was es leisten muss, wie es aufgebaut
ist, wie das Modell entsteht, wie die Oberfläche aussieht und wie alles geprüft
wird. Wer nur diesen Ordner und die Quellen im Abschnitt [Was von aussen nötig
ist](16_neubau.md) hat, soll MASCHERA neu bauen können.

MASCHERA pseudonymisiert Schweizer Dokumente lokal. Das ist **Pseudonymisierung,
nicht Anonymisierung**: Über das Wörterbuch lässt sich alles zurückholen.

## Lesereihenfolge

| Kapitel | Inhalt |
|---|---|
| [01 Ziele](01_ziele.md) | Zweck, Abgrenzung, Zielgruppen, Grundsätze |
| [02 Funktional](02_funktional.md) | Funktionale Anforderungen `FA-nnn` |
| [03 Nichtfunktional](03_nichtfunktional.md) | Nichtfunktionale Anforderungen `NFA-nnn` |
| [04 Architektur](04_architektur.md) | Komponenten und Datenfluss |
| [05 Abläufe](05_ablaeufe.md) | Abläufe als Diagramme |
| [06 Erkennung](06_erkennung.md) | Tags, Stufen, Prüfsummen, Labelvertrag |
| [07 API](07_api.md) | Vertrag der Endpunkte |
| [08 Synthese und Training](08_synthese_training.md) | Wie das Modell entsteht |
| [09 Evaluation](09_evaluation.md) | Fehlerbudgets und Messverfahren |
| [10 Oberfläche](10_oberflaeche.md) | Ansichten, Dialoge, Zustände, Tastatur |
| [11 Design](11_design.md) | Farben, Schriften, Raster, hell und dunkel |
| [12 Pakete und Release](12_pakete_release.md) | Paketformen, Bau, Signatur |
| [13 Sicherheit](13_sicherheit.md) | Bedrohungen, Datenschutz, Lieferkette |
| [14 Regeln](14_regeln.md) | Arbeits- und Codierregeln, Lehren aus Fehlern |
| [15 Entscheide](15_entscheide.md) | Entscheide `EN-nnn` samt Grund |
| [16 Neubau](16_neubau.md) | Reihenfolge eines Neubaus |

Aus dem Code erzeugt, nie von Hand geändert:

| Datei | Inhalt |
|---|---|
| [testkatalog.md](erzeugt/testkatalog.md) | Alle Prüfungen mit Punkten und Meldungen |
| [tags.md](erzeugt/tags.md) | Die Tags mit Index, Stufe, Budget |
| [erkennungsregeln.md](erzeugt/erkennungsregeln.md) | Die Muster und Anker |
| [endpunkte.md](erzeugt/endpunkte.md) | Die Endpunkte |
| [texte.md](erzeugt/texte.md) | Die Beschriftungen in vier Sprachen |
| [design.md](erzeugt/design.md) | Farben, Abstände, Abfragen |
| [elemente.md](erzeugt/elemente.md) | Alle Elemente der Oberfläche |
| [seiten.md](erzeugt/seiten.md) | Hilfe und Willkommen in vier Sprachen |
| [abhaengigkeiten.md](erzeugt/abhaengigkeiten.md) | Die Paketlisten |
| [rueckverfolgung.csv](erzeugt/rueckverfolgung.csv) | Anforderung zu Testfall |

## Regeln dieses Ordners

- **Kennungen:** `FA-nnn`, `NFA-nnn` und `EN-nnn` stehen als Überschrift und
  werden nie neu vergeben. Testfälle heissen `T-<DATEI>-<PUNKT>`, zum Beispiel
  `T-API-23`.
- **Rückverfolgung:** Jede Anforderung nennt ihre Testfälle oder trägt den
  Vermerk `ohne Prüfung`.
- **Status einer NFA:** `verbindlich` ist durch Prüfung oder Grundsatz
  festgelegt, `gemessen` ist ein aus einer Messung aufgerundeter Sollwert,
  `offen` wartet auf einen Entscheid.
- **Erzeugtes:** Nach einer Änderung an Prüfungen, Tags, Mustern, Endpunkten
  oder Beschriftungen läuft `python3 tools/specs_bauen.py`.
- **Leseansicht:** `python3 tools/specs_bauen.py --html` schreibt
  `specs/html/index.html` mit Navigation und Suche. Sie ist erzeugt und nicht in Git.
  Die Diagramme lädt sie von jsDelivr, ohne Netz stehen sie als Text da.
- **Wache:** `tests/test_specs.py` schlägt an, wenn etwas veraltet, doppelt
  oder ohne Ziel ist.
- **Rangfolge bei einem Widerspruch:** Der Code gilt. Der Katalog wird
  nachgezogen.
