# Golddokumente — ein eigenes Testset anlegen

Golddokumente sind echte Dokumente mit von Hand geprüften Spannen. Sie
messen, was synthetische Daten nicht messen können: ob die Kette mit
Dokumentarten zurechtkommt, die keine Vorlage kennt.

    synthetisch   = misst genau, sieht nur die eigene Welt
    Golddokument  = misst grob, sieht die Wirklichkeit

**Das Testset wird nicht mitgeliefert.** Auch mit ersetzten Werten bleibt
die Struktur eines echten Dokuments schützenswert. Wer an eigenen
Dokumenten messen will, legt sich ein eigenes Set an — die Werkzeuge dafür
sind hier beschrieben.

---

## Wo die Dokumente liegen

```
<gold>/<pack>/real/      die Golddokumente (JSON)
<gold>/<pack>/markup/    die markierten Fassungen (Text)
```

`<gold>` ist:

1. `MASCHERA_GOLD`, falls gesetzt.
2. Sonst der Datenordner des Programms: `~/.local/share/maschera/gold`
   (bzw. `$XDG_DATA_HOME/maschera/gold`, unter Windows `LOCALAPPDATA`).

Aufgelöst wird der Pfad in `core/pfade.py` (`gold_lesen()`,
`gold_schreiben()`) — kein Werkzeug baut ihn selbst.
`tests/test_goldpfad.py` hält das fest.

**Ausserhalb des Projektbaums, und das ist Absicht.** Alles, was über den
Baum geht — `git add -A`, ein Tar, ein zu weit gefasster Suchlauf —,
erreicht die Dokumente so strukturell nicht.

**Ein leerer Ort meldet sich.** Findet ein Werkzeug kein Testset, sagt es,
wo es gesucht hat. Eine Messung über ein leeres Verzeichnis, die «0 Lecks»
meldet, wäre der gefährlichste Befund überhaupt.

---

## `real/` — das Dateiformat

Eine Datei je Dokument, `<id>.json`:

| Feld | Bedeutung |
|---|---|
| `id` | Kennung, zugleich Dateiname, z. B. `de-brief-001` |
| `lang` | `de`, `fr`, `it`, `en` |
| `doctype` | z. B. `mailverlauf`, `formular` |
| `herkunft` | woher das Dokument stammt |
| `geprueft` | siehe unten |
| `text` | der volle Text |
| `spans` | `{tag, start, end, wert}` — die Goldspannen |
| `zu_pruefen` | Restverdacht aus `restverdacht()`, noch nicht entschieden |

**`geprueft: false` heisst: zählt nicht.** `tools/eval_documents.py`
überspringt solche Dateien, ausser mit `--auch-ungeprueft`. Ein Vorschlag
der eigenen Kette ist kein Massstab für dieselbe Kette — sonst prüfte das
Modell sich selbst.

`tools/kalibriere_schwellen.py` meldet beide leeren Fälle getrennt: keine
Datei, und Dateien-aber-keine-`geprueft`.

---

## `markup/` — die markierten Fassungen

`.txt`-Dateien, in denen die Spannen als Markierungen im Text stehen und die
Werte **bereits durch erfundene ersetzt sind**:

    Von: [[FULLNAME:Hasli]] [[GIVENNAME:Leopold]] <[[EMAIL:l.h@example.ch]]>

---

## Der Weg von einem Dokument zum Gold

**Wer ersetzt, weiss die Spannen.** Markieren und Ersetzen geschehen in
einem Durchgang; die Spannen ergeben sich aus den Einsetzpositionen.

```sh
# 1. Öffentliche Musterbriefe holen (EDÖB) — oder eigene Dokumente nehmen
python3 tools/hole_musterbriefe.py --liste
python3 tools/hole_musterbriefe.py --holen

# 2. Vormarkieren — die Kette schlägt vor
python3 tools/gold_from_markup.py --vormarkieren <datei> \
    --model runs/ch-v63b --out <datei>.markiert.txt

# 3. Im Editor, in EINEM Durchgang:
#    Tags korrigieren UND die Werte durch erfundene ersetzen

# 4. Anlegen — die Spannen stimmen konstruktionsbedingt
python3 tools/gold_from_markup.py --anlegen <datei>.markiert.txt \
    --id de-brief-001 --lang de --doctype mailverlauf

# 5. Messen
python3 tools/eval_documents.py --model runs/ch-v63b
```

Vor dem Anlegen läuft `restverdacht()` über den unmarkierten Text. Findet es
etwas, das nach einem Personendatum aussieht, bricht das Werkzeug ab, statt
es still ins Testset zu schreiben.

Werte nachträglich ersetzen: `tools/gold_ersetzen.py` — die Spannen wandern
mit.

Beim Ersetzen gilt: **erfundene, aber plausible Schweizer Werte.** Steht
Unsinn im Dokument, misst das Testset an etwas, das so nie vorkommt.

---

## Wie viel ein kleines Testset aussagt

Wenig Feines. Ein Testset aus einer Handvoll Dokumenten löst Unterschiede
von wenigen Hundertsteln Micro-F1 nicht auf, und eine Gesamtzahl über
verschieden schwere Dokumente misst auch die Mischung des Sets.
`tools/eval_documents.py` weist deshalb jedes Dokument einzeln und nach
Sprache und Dokumenttyp aus, und `tools/streuung.py` sagt, ob ein
Unterschied grösser ist als das Rauschen.

Golddokumente kommen aus der Welt oder sie taugen nicht — deshalb wächst
ein solches Set langsam und von Hand.
