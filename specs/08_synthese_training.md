# Synthese und Training

## Nomenklaturquellen

Die Nomenklaturen werden gebaut, nicht verteilt:
`packs/ch/nomenclatures/build.py` holt die offenen Verwaltungsdaten und
normalisiert sie; `raw/` und `dist/` stehen nicht im Repository.

| Bedarf | Quelle |
|---|---|
| `PLACE_OF_ORIGIN` | eCH-0135 Heimatortverzeichnis (BJ) |
| `CITY`, `ZIPCODE` | Amtliches Ortschaftenverzeichnis mit PLZ (swisstopo) |
| `STREET` | Amtliches Strassenverzeichnis (swisstopo) |
| `FULLNAME`, `GIVENNAME` | Nach- und Vornamen der ständigen Wohnbevölkerung (BFS) |
| `ORG` | Zefix über LINDAS (Handelsregister), dazu Behördennamen kombinatorisch |
| `NATIONALITY` u. a. | Amtlicher Katalog der Merkmale (BFS), viersprachig |

**eCH-0135**, Befunde, die den Generator prägen:

- Historisierte Namen stehen weiterhin in gültigen Pässen, **der
  Generator zieht sie mit.**
- Einträge in Klammerform (`Hautemorges (Apples)`) sind ein
  Registerartefakt → zwei Oberflächenformen, die zusammengesetzte verworfen.
- Namen, die in **mehreren Kantonen** vorkommen (`Buchs` in ZH/LU/SG/AG) →
  das Kantonskürzel gehört **in die Entitätsspanne**.
- Namen sind vielfach Alltagswörter: `Wald`, `Berg`, `Stein`, `Egg`, `Au`.
  → **Gazetteer nur zur Generierung, nie zur Erkennung. Kein Override.**
- Schrägstrich-Namen (`Breil/Brigels`) sind deutsch-romanische
  Doppelnamen. Rätoromanisch steht damit faktisch als fünfte Sprache in
  den Daten, ohne unterstützt zu sein.
- **Heimatortliste ≠ Gemeindeverzeichnis.** Zwei getrennte Nomenklaturen.

**Identifikatoren** werden **generiert**, mit gültigen Prüfsummen.

**Fairness:** Ohne italienische, portugiesische, balkanische, türkische
und tamilische Namen hätte das Modell den schlechtesten Recall bei genau
den Gruppen, die in Schweizer Dokumenten häufig vorkommen. Die Namenslisten
des BFS bilden die ständige Wohnbevölkerung ab.

**Englisch** ist keine Amtssprache und hat keine amtliche Nomenklatur.
Vorlagen komplett synthetisch, Identifikatoren bleiben schweizerisch.

## Vorlagenbank

**Nicht pro Dokumenttyp budgetieren, sondern pro Tag.** Seltene Tags
(`RELIGION`, `VOTING_RIGHTS`, `EWID`, `PLACE_OF_ORIGIN`, `PERMIT_TYPE`)
brauchen genug eigene Rahmen, sonst lernt das Modell sie nie.

**Deutsch bewusst überproportional.** In FR/IT/EN ist ein grossgeschriebenes
Wort mitten im Satz ein starkes Namenssignal, im Deutschen ist jedes
Substantiv gross. Qualität überträgt sich **nicht** von FR/IT/EN nach DE.

**Zeilen pro Vorlage begrenzen.** Zu wenige verschenken Wertvielfalt, zu
viele lehren das Modell den Rahmen statt der Entität.

Vorlagen werden von einem lokalen Sprachmodell geschrieben
(`tools/generate_templates.py`) oder von Hand, und jede läuft durch
dieselben Wachen (`core/injector.py`), vor dem Training trotzdem lesen:
die Wachen prüfen die Form, nicht den Sinn.

## Slot-Grammatik

```
{TAG}           echte Entität, wird getaggt
{@makro}        gekoppelte Gruppe aus macros.yaml
{~decoy}        sieht aus wie eine Entität, bleibt O
```

**Makros erzwingen Kohärenz.** `@address` zieht Strasse, Hausnummer, PLZ und
Ort aus EINEM Datensatz, sonst entsteht «Marktgasse 12, 6900 Bern», und das
Modell lernt, dass PLZ und Ort nichts miteinander zu tun haben.

### Decoys: nie gelabelt

| Makro | Beispiel |
|---|---|
| `~legal_ref` | Art. 6 Abs. 1 Bst. i RHG (SR 431.02) |
| `~deadline` | innert 30 Tagen seit Eröffnung |
| `~threshold` | Vermögensfreibetrag von 4000 Franken |
| `~doc_meta` | Version 2.1, Stand 01.2026 |

Verwaltungstexte wimmeln von Zahlen, die keine Personendaten sind. Ohne
Decoys übertaggt das Modell. **Decoys sind das Precision-Werkzeug und
kosten nur Vorlagenzeilen.** Sie sind je Sprache getrennt: ein deutscher
Decoy in einer französischen Vorlage lehrt eine Sprachmischung, die in
echten Dokumenten nicht vorkommt.

## Makros

### Sprachregion koppelt Geografie

| Sprache | Pool |
|---|---|
| DE | Deutschschweiz |
| FR | Romandie |
| IT | Tessin + italienischsprachiges Graubünden |
| EN | alle, gewichtet nach Wirtschaftsräumen |

Dazu bewusst ein Anteil **Überkreuz**, ein Berner Verfahren mit Genfer
Gegenpartei ist normal. Ohne diesen Anteil wird das Modell überkonfident
auf Region.

### Wichtige Kopplungen

| Makro | Kopplungsregel |
|---|---|
| `@address` | PLZ ↔ Ort aus swisstopo |
| `@origin` | Heimatort mit dem Kanton, an den er in eCH-0135 gebunden ist |
| `@person` | Namensreihenfolge wechselt, auch Register-Reihenfolge «Nachname Vorname» |
| `@company` | Rechtsform sprachrichtig: AG/SA/SA, GmbH/Sàrl/Sagl |

**Jede Vorlage mit Heimatort enthält auch einen Wohnort.** Ohne dieses
Minimalpaar lernt das Modell die Unterscheidung *von* ↔ *wohnhaft in* nie,
und beide Orte werden verwechselt.

**Wortstellung ist sprachabhängig, nicht übersetzbar.** FR: «Rue du Marché
12» *oder* «12, rue du Marché». Makros einmal auf Deutsch definieren und
übersetzen ergibt Deutsch mit französischen Wörtern.

## Labeling-Vertrag

**Das Sprachmodell schreibt ausschliesslich Prosa mit Slots und sieht nie
einen echten Wert.** Der Code injiziert die Werte und erzeugt die
BIO-Labels aus den Einsetzpositionen.

1. Der Injektor merkt sich beim Einsetzen die Zeichen-Offsets.
2. Tokenisieren, BIO daran ausrichten (`core/alignment.py`).
3. **Round-Trip:** jeden gelabelten Span zurücklesen und mit dem
   eingesetzten Wert vergleichen.
4. Kein Match → **Zeile verwerfen**, nicht ins Training.

**Layout-Rauschen ist Pflicht**, weil der echte Input aus PDFs und Mails
kommt: Zeilenumbrüche in Entitäten, Tippfehler, aufgelöste Umlaute,
Versalien. Ein Zeilenumbruch mitten in einem Namen muss den Round-Trip
überleben.

**Haltezone:** ein Zehntel der Nomenklaturwerte wird deterministisch
zurückgehalten und nur in der Auswertung verwendet. Fällt der Wert dort
ab, hat das Modell die Liste gelernt und nicht die Form.

## Training

- **Backbone:** mmBERT-base. Nicht ohne Messung wechseln.
- **Sequenzlänge 512** im Training. Trainingsdaten sind satz- und
  absatzweise; lange Dokumente verarbeitet die Anwendung in überlappenden
  Fenstern, mit Sondertoken **je Fenster**.
- **bf16** setzt eine GPU ab Ampere voraus. Das Training braucht eine GPU,
  die Anwendung nicht.
- **Keine externe API in der Kette**, die Vorlagen entstehen an einem
  lokalen, OpenAI-kompatiblen Endpunkt.
- **Streuung messen.** Derselbe Datensatz mit verschiedenen Keimen kann
  weiter auseinanderliegen als zwei Bedingungen (`tools/streuung.py`).

## Der ausgelieferte Lauf

Das ausgelieferte Modell heisst `ch-v63b`. Die Gewichte selbst sind nicht Teil
dieses Katalogs; `packs/ch/modell.json` nennt Quelle, festen Commit, Grössen und
Prüfsummen. Die Werte unten stammen aus den Trainingsargumenten dieses Laufs.

| Parameter | Wert |
|---|---|
| Backbone | `jhu-clsp/mmBERT-base`, ModernBERT-Architektur |
| Kopf | Token-Klassifikation, 91 Labels |
| Epochen | 3 |
| Stapel | 8, Gradienten über 2 Stapel, effektiv 16 |
| Lernrate | 3e-5 |
| Aufwärmen | 10 % der Schritte |
| Gewichtsabnahme | 0.01 |
| Optimierer | Adam, Beta 0.9 und 0.999, Epsilon 1e-8 |
| Gradientenbegrenzung | 1.0 |
| Label Smoothing | keines |
| Rechengenauigkeit | bf16 |
| Keim Training | 4711 |
| Sequenzlänge | 512 |
| Zwischenstände | keine, `save_strategy="no"` |

Die Vorgaben von `train.py` entsprechen diesen Werten, ausser dem Keim (Vorgabe
2026).

### Daten und Befehle

Trainiert wird nur aus der Zone `training`, ausgewertet nur aus der Zone
`halten`. Ohne diese Trennung lässt sich nicht unterscheiden, ob das Modell
Namen erkennt oder Listen auswendig kann.

```fish
python3 packs/ch/nomenclatures/build.py
python3 tools/generate_dataset.py --n 40000 \
    --rauschen 0.08 --zone training --out dataset.jsonl
python3 tools/generate_dataset.py --n 2000 \
    --rauschen 0.08 --zone halten --seed 63 --out eval.jsonl
python3 train.py --data dataset.jsonl --eval-data eval.jsonl --dry-run
python3 train.py --data dataset.jsonl --eval-data eval.jsonl \
    --out runs/neu --max-length 512 --seed 4711
```

Am Datensatz gemessen: 40 000 Beispiele, längste Sequenz 285 Token, keine
Abschneidung bei 512. `max_length` ist eine Obergrenze und reserviert keinen
Speicher, weil je Stapel nur auf dessen längste Sequenz aufgefüllt wird.

Die Rechenzeit liegt für 2 Epochen bei rund 48 Minuten auf einer GPU mit 8 GB
Speicher. Die Anwendung braucht keine GPU.

### Was ein Neulauf liefert

⚠️ Ein Neulauf ergibt **nicht** dieselben Gewichte. Der ursprüngliche Datensatz
ist nicht veröffentlicht, Vorlagen und Erzeuger haben sich seither weiterbewegt,
und die Streuung zwischen zwei Keimen kann grösser sein als der Unterschied
zwischen zwei Bedingungen. `ch-v63b` war eine günstige Ziehung aus seiner
Bedingung, nicht ein typischer Lauf.

Daraus folgen die Anforderungen an ein neues Modell:

1. Mehrere Keime derselben Bedingung trainieren und `tools/streuung.py` zeigen
   lassen, ob ein Unterschied das Rauschen überragt.
2. Die Schwellen in `packs/ch/taxonomy.yaml` gehören zu einem Modell. Nach einem
   Wechsel neu kalibrieren, sonst wird ein Modell mit fremden Schwellen gemessen
   ([09 Evaluation](09_evaluation.md)).
3. Massgeblich ist die Zahl der Lecks, nicht Micro-F1
   ([06 Erkennung](06_erkennung.md)).
4. Der Modellordner trägt `pack.json` mit Labelliste und Hash. Der Dienst prüft
   beides beim Laden.
5. Nur `model.safetensors` ist zulässig, nie ein Pickle-Format. Trainingsartefakte
   wie `training_args.bin` fahren nicht im Paket mit.
6. Nach dem Wechsel `packs/ch/modell.json` mit `tools/modell_manifest.py`
   erneuern.
7. Die Anwendung nutzt die torch-Kette. ONNX int8 ist ein vorhandener Läufer,
   leckte aber mehr und wird nicht ausgeliefert ([EN-012](15_entscheide.md)).
