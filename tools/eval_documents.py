#!/usr/bin/env python3
"""Auswertung gegen das Dokument-Testset — echte Unterlagen statt Vorlagen.

    python3 tools/eval_documents.py --anlegen /pfad/brief.txt --model runs/ch-v63b
    python3 tools/eval_documents.py --model runs/ch-v63b
    python3 tools/eval_documents.py --model runs/ch-v63b --zeige 3

Der Unterschied zu `evaluate_model.py`: dort stammt der Auswertungssatz aus
denselben Vorlagen wie das Training. Er misst Verallgemeinerung ueber WERTE.
Hier stammt der Satzbau aus einem echten Dokument, das keine Vorlage kennt —
das misst Verallgemeinerung ueber DOKUMENTARTEN.

## Dateiformat — `$MASCHERA_GOLD/<pack>/real/<id>.json`

    {
      "id":       "de-brief-001",
      "lang":     "de",
      "doctype":  "brief",
      "herkunft": "Werte durch Nomenklaturwerte ersetzt",
      "geprueft": false,
      "text":     "…",
      "spans":    [{"tag": "FULLNAME", "start": 42, "end": 54}]
    }

`geprueft` ist die wichtigste Zeile. `--anlegen` schlaegt Spannen vor, indem es
die Kette selbst laufen laesst — bequem, aber **zirkulaer**: das Gold erbt
damit genau die blinden Flecken, die es aufdecken soll. Solange `geprueft`
`false` ist, wertet dieses Werkzeug die Datei nicht. Erst wenn ein Mensch die
Spannen durchgesehen und ergaenzt hat, wird der Wert auf `true` gesetzt.

`--anlegen` laeuft deshalb mit `--verdacht`-Logik: die Vorschlagsdatei traegt
unter `zu_pruefen` alles ein, was unmaskiert blieb und nach Personendatum
aussieht. Das ist die Arbeitsliste beim Durchsehen.

## Keine Personendaten im Testset

Der empfohlene Weg: ein echtes Dokument nehmen, die Personendaten durch Werte
aus den eigenen Nomenklaturen ersetzen, DANN anlegen. Der Satzbau bleibt echt,
im Testset liegt kein Personendatum. Siehe `docs/GOLDDOKUMENTE.md`.

## Diese Dateien sind fuers Training gesperrt

Das Testset liegt ausserhalb des Projektbaums und wird vom Vorlagenlader
gar nicht erst gesehen. Zusaetzlich lehnt `load_templates()` jede Vorlage
mit `eval_only: true` ab. Waere ein Testdokument im Trainingssatz, pruefte
das Modell sich selbst.

Wo genau gelesen wird, entscheidet `core.pfade.gold_lesen()`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))

from core import pfade  # noqa: E402
from core import user_rules  # noqa: E402
from core import vorlieben  # noqa: E402
from core.evaluate import evaluate, format_report  # noqa: E402
from core.inference import merge  # noqa: E402
from core.masking import Span, mask  # noqa: E402
from dokumente import lies  # noqa: E402
from filter_document import restverdacht  # noqa: E402
from packs import load_pack  # noqa: E402

# ⚠️ Hier stand ein handgebautes `EVAL_DIR` — dieselbe Zeile wie in
# `gold_from_markup.py`, `kalibriere_schwellen.py` und (fuer die markierten
# Fassungen) `hole_musterbriefe.py`. Vier Verwalter fuer einen Pfad, und das
# Pack darin festverdrahtet, obwohl `--pack` daneben stand und nichts
# bewirkte. Der Pfad kommt jetzt aus `core/pfade.py`.
#
# `tests/test_goldpfad.py` Punkt 6 schlaegt an, wenn die fuenfte Kopie
# entsteht — die Wache liest den Quelltext, sie kann Kommentar nicht von Code
# unterscheiden. Deshalb steht die alte Zeile hier NICHT woertlich.


def lade_gold(pack_name: str, auch_ungeprueft: bool = False):
    """Die geprueften Golddokumente lesen — die EINE Stelle dafuer.

    Gibt `(dokumente, hinweis, uebersprungen)` zurueck. Ein Dokument ist
    `(text, gold, meta)` mit `meta = (kennung, sprache, doctype, zeichen)`.

    Auch `tools/streuung.py` laedt hier, samt der `geprueft`-Regel, die
    entscheidet, WELCHE Dokumente zaehlen. Zwei Kopien einer Ladelogik hiessen
    zwei verschiedene Testsets unter demselben Namen.
    """
    eval_dir, hinweis = pfade.gold_lesen(pack_name, "real")
    dateien = sorted(eval_dir.glob("*.json"))
    if not dateien:
        # Ein leerer Befund ist keine Entwarnung. Ein falsch aufgeloester Pfad ist
        # der wahrscheinliche Grund — deshalb steht er in der Meldung, samt der
        # Variablen, die ihn steuert.
        raise SystemExit(
            f"Keine Dokumente in {eval_dir}.\n"
            f"Liegt das Testset woanders, MASCHERA_GOLD darauf setzen "
            f"(erwartet wird darunter <pack>/real/).\n"
            "Mit --anlegen eine Vorschlagsdatei erzeugen.")

    dokumente, uebersprungen = [], []
    for pfad in dateien:
        obj = json.loads(pfad.read_text(encoding="utf-8"))
        kennung = obj.get("id", pfad.stem)
        # Vorgeschlagene Spannen sind zirkulaer und messen nichts.
        if not obj.get("geprueft") and not auch_ungeprueft:
            uebersprungen.append(kennung)
            continue
        text = obj["text"]
        gold = [Span(s["tag"], s["start"], s["end"]) for s in obj["spans"]]
        # Kennung, Sprache und Dokumenttyp mitfuehren — ohne sie ist die
        # Gesamtzahl ein Durchschnitt aus Ungleichem.
        dokumente.append((text, gold,
                          (kennung, obj.get("lang", "?"),
                           obj.get("doctype", "?"), len(text))))
    return dokumente, hinweis, uebersprungen


def _scorer(args, pack):
    if args.onnx:
        from core.inference import OnnxScorer
        s = OnnxScorer(args.onnx, args.max_length)
    elif args.model:
        from evaluate_model import TorchScorer
        s = TorchScorer(args.model, args.max_length)
    else:
        return None
    s.check_contract(pack)
    return s


def anlegen(args, pack) -> int:
    quelle = Path(args.anlegen)
    dokumente = lies(quelle)
    if len(dokumente) > 1:
        raise SystemExit(
            f"{quelle} enthaelt {len(dokumente)} Nachrichten. --anlegen "
            "erwartet EIN Dokument; eine mbox vorher auftrennen.")
    text = dokumente[0].text
    for h in dokumente[0].hinweise:
        print(f"  HINWEIS {h['text']}")
    scorer = _scorer(args, pack)

    # Die Auswertung muss DIESELBE Kette messen, die im Betrieb laeuft —
    # `merge()` mit `user_spans`, also mit den Benutzerregeln. Ohne sie fiele
    # ein Benutzertag auf Recall 0.000, und gemessen wuerde eine Kette, die es
    # so nicht gibt.
    regeln = user_rules.lade(args.regeln, pack)
    model_spans = scorer.score(text) if scorer else []
    spans, _ = merge(text, model_spans, pack,
                     user_spans=user_rules.erkenne(text, regeln))
    actions = pack.get_actions()

    abgedeckt = bytearray(len(text))
    for s in spans:
        if actions.get(s.tag) == "mask":
            for i in range(s.start, s.end):
                abgedeckt[i] = 1

    kennung = args.id or quelle.stem
    # Angelegt wird IMMER am neuen Ort, nie im Projektbaum — auch dann nicht,
    # wenn die Auswertung unten noch von dort liest. Sonst laegen die alten
    # Dokumente im Projekt und die neuen daneben, und keine Messung saehe beide.
    ordner = pfade.gold_schreiben(args.pack, "real")
    ziel = ordner / f"{kennung}.json"
    if ziel.exists() and not args.ueberschreiben:
        raise SystemExit(f"{ziel} existiert bereits — --ueberschreiben nutzen.")

    obj = {
        "id": kennung,
        "lang": args.lang,
        "doctype": args.doctype,
        "herkunft": args.herkunft,
        "geprueft": False,
        "text": text,
        "spans": [
            {"tag": s.tag, "start": s.start, "end": s.end,
             "wert": s.value(text)}
            for s in sorted(spans, key=lambda s: s.start)
        ],
        "zu_pruefen": [
            {"art": art, "start": a, "end": b, "wert": w}
            for art, a, b, w in restverdacht(text, abgedeckt)
        ],
    }
    ordner.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                    encoding="utf-8")

    print(f"Angelegt: {ziel}")
    print(f"  {len(obj['spans'])} vorgeschlagene Spannen")
    print(f"  {len(obj['zu_pruefen'])} Stellen unter `zu_pruefen`")
    print()
    print("  Die Vorschlaege stammen aus derselben Kette, die geprueft werden")
    print("  soll — sie sind ZIRKULAER. Was die Kette uebersieht, fehlt auch")
    print("  hier. Deshalb `zu_pruefen` durchgehen, fehlende Spannen von Hand")
    print("  ergaenzen, falsche entfernen, dann `geprueft` auf true setzen.")
    print()
    print("  Solange `geprueft: false` steht, wertet dieses Werkzeug die Datei")
    print("  nicht aus.")
    return 0


def _kennzahlen(teil_cases, pack, ohne=None) -> tuple[int, float, float, int, int]:
    """(Goldspannen, Leckrate, Micro-F1, Lecks, Uebermaskierungen)."""
    r = evaluate(teil_cases, pack, excluded=ohne)
    gold = sum(t.gold for t in r.per_tag.values())
    return gold, r.leak_rate, r.micro_f1, len(r.leaked), len(r.over)


def je_dokument(cases, meta, pack, ohne=None) -> str:
    """Eine Zeile je Dokument, dann nach Sprache und Dokumenttyp.

    Eine Gesamtzahl ueber Dokumente unterschiedlicher Schwierigkeit steigt,
    wenn ein leichtes dazukommt, und faellt, wenn ein schweres kommt. Sie
    misst dann die MISCHUNG des Testsets, nicht die Kette — dieselben drei
    Lecks verteilen sich bloss auf mehr Text.

    Und ein franzoesisches Leck, das ein deutscher Treffer ausgleicht, bliebe
    in einer Gesamtzahl unsichtbar.
    """
    z = []
    z.append("JE DOKUMENT")
    z.append(f"{'Dokument':<18}{'Spr':>4}{'Typ':>16}{'Zeich':>7}"
             f"{'Gold':>6}{'Leck':>6}{'Leckrate':>10}{'F1':>8}{'Uebermask':>11}")
    for fall, (kennung, lang, typ, zeichen) in zip(cases, meta):
        gold, rate, f1, lecks, over = _kennzahlen([fall], pack, ohne)
        z.append(f"{kennung:<18}{lang:>4}{typ[:15]:>16}{zeichen:>7}"
                 f"{gold:>6}{lecks:>6}{100*rate:>9.2f} %{f1:>8.3f}{over:>11}")

    for titel, stelle in (("NACH SPRACHE", 1), ("NACH DOKUMENTTYP", 2)):
        gruppen: dict[str, list] = {}
        for fall, m in zip(cases, meta):
            gruppen.setdefault(m[stelle], []).append(fall)
        if len(gruppen) < 2:
            continue
        z.append("")
        z.append(titel)
        z.append(f"{'':<18}{'n':>4}{'':>16}{'':>7}"
                 f"{'Gold':>6}{'Leck':>6}{'Leckrate':>10}{'F1':>8}{'Uebermask':>11}")
        for name, teil in sorted(gruppen.items()):
            gold, rate, f1, lecks, over = _kennzahlen(teil, pack, ohne)
            z.append(f"{name:<18}{len(teil):>4}{'':>16}{'':>7}"
                     f"{gold:>6}{lecks:>6}{100*rate:>9.2f} %{f1:>8.3f}{over:>11}")

    z.append("")
    z.append("  Die Gesamtzahlen oben sind ein Durchschnitt ueber Dokumente")
    z.append("  UNTERSCHIEDLICHER Schwierigkeit. Sie steigen, wenn ein leichtes")
    z.append("  Dokument dazukommt. Vergleichbar ueber die Zeit ist nur, was")
    z.append("  hier je Dokument steht.")
    return "\n".join(z)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--onnx", default=None)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--regeln", default=None,
                    help="eigene Regeln, Vorgabe ~/.config/maschera/regeln.yaml")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--zeige", type=int, default=0,
                    help="so viele maskierte Dokumente ausgeben")
    ap.add_argument("--auch-ungeprueft", action="store_true",
                    help="auch Dateien mit geprueft:false auswerten "
                         "(die Zahl ist dann wertlos)")
    # Anlegen
    ap.add_argument("--anlegen", default=None, help="Textdatei -> Vorschlagsdatei")
    ap.add_argument("--id", default=None)
    ap.add_argument("--lang", default="de")
    ap.add_argument("--doctype", default="unbekannt")
    ap.add_argument("--herkunft", default="")
    ap.add_argument("--ueberschreiben", action="store_true")
    # Die Auswertung muss mit derselben Einstellung laufen wie die Kette.
    # Vorgabe sind die gespeicherten Vorlieben — sonst misst man eine
    # Verarbeitung, die es so nicht gab.
    ap.add_argument("--ohne", action="append", default=None, metavar="TAG",
                    help="Tag bewusst im Klartext lassen. Vorgabe: die "
                         "gespeicherten Vorlieben. --ohne '' schaltet sie ab.")
    args = ap.parse_args()

    pack = load_pack(args.pack)

    if args.anlegen:
        return anlegen(args, pack)

    dokumente, hinweis, uebersprungen = lade_gold(args.pack,
                                                  args.auch_ungeprueft)
    if hinweis:
        print(f"⚠️  {hinweis}\n")

    scorer = _scorer(args, pack)
    regeln = user_rules.lade(args.regeln, pack)
    if regeln:
        print(f"Eigene Regeln ({len(regeln)}): "
              + ", ".join(r.bezeichnung for r in regeln))
    else:
        # LAUT melden, nicht stillschweigend weglassen. Fehlt `regeln.yaml` auf
        # einer Maschine, laeuft die Auswertung ohne die Benutzerregeln, und ein
        # Benutzertag faellt von 1.000 auf 0.000 — sichtbar nur daran, dass eine
        # Zeile FEHLT. Eine fehlende Zeile liest niemand.
        print(f"⚠ KEINE eigenen Regeln geladen ({user_rules.VORGABE}).")
        print("  Die Zahlen sind NICHT mit Laeufen vergleichbar, die welche")
        print("  hatten — X_-Tags koennen dann gar nicht entstehen.")
    if scorer is None:
        print("Kette: Stufe 1 + 2, OHNE Modell — Grundlinie.\n")

    cases, meta, benutzt = [], [], []
    for text, gold, m in dokumente:
        model_spans = scorer.score(text) if scorer else []
        pred, _ = merge(text, model_spans, pack,
                        user_spans=user_rules.erkenne(text, regeln))
        cases.append((text, gold, pred))
        meta.append(m)
        benutzt.append(f"{m[0]} [{m[1]}/{m[2]}]")

    if uebersprungen:
        print(f"Uebersprungen, weil ungeprueft: {', '.join(uebersprungen)}")
        print("  Vorgeschlagene Spannen sind zirkulaer und messen nichts.\n")
    if not cases:
        raise SystemExit("Kein geprueftes Dokument vorhanden.")

    print(f"{len(cases)} Dokumente: {', '.join(benutzt)}\n")
    ohne = (set(x for x in args.ohne if x) if args.ohne is not None
            else vorlieben.lade())
    if ohne:
        try:
            vorlieben.pruefe(ohne, pack, auch_bspd=True)
        except vorlieben.Abgelehnt as e:
            print(f"ABBRUCH: {e}", file=sys.stderr)
            return 2

    report = evaluate(cases, pack, excluded=ohne)
    print(format_report(report, top=20))
    print()
    print(je_dokument(cases, meta, pack, ohne))

    for text, gold, pred in cases[:args.zeige]:
        print("\n" + "-" * 74)
        print(mask(text, pred, pack).text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
