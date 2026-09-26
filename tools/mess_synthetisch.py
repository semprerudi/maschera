#!/usr/bin/env python3
"""Dokument-Testset aus der Haltezone — ein Messgeraet mit Aufloesung.

    python3 tools/mess_synthetisch.py --model runs/ch-v63b --n 300

WOZU
----
Ein kleines Golddokument-Testset loest nur grobe Unterschiede auf:
mehrere Auswertungen desselben Modellstands streuen dort um mehrere
Hundertstel Micro-F1. Dieses Werkzeug hebt die Aufloesung, indem es die
Zahl der Spannen um zwei Groessenordnungen erhoeht. Die Werte stammen aus
der HALTEZONE, dem zurueckgehaltenen Zehntel: das Modell hat sie nie
gesehen. Erzeuger, Keim und Code-Stand genuegen, um die Zahl
nachzurechnen.

WAS ES NICHT IST
----------------
**Kein Ersatz fuer die Golddokumente.** Es teilt die blinden Flecken des
Generators — was in keiner Vorlage steht, prueft es nicht. Ein Tag, das
nur in einem einzigen Satzrahmen vorkommt, wird hier glaenzend bewertet,
waehrend es an echten Dokumenten versagen kann.

    synthetisch  = misst genau, sieht nur die eigene Welt
    Golddokument = misst grob, sieht die Wirklichkeit

Beide, nicht eines.

Die Kette ist dieselbe wie in `eval_documents.py` — `merge`, `evaluate`,
`format_report`, dieselben Benutzerregeln, dieselben Vorlieben. Ein
zweites Messverfahren daneben ergaebe zwei Zahlen aus zwei Testsets.

Leckwerte werden hier im Klartext ausgegeben: die Dokumente sind
erzeugt, es gibt kein Personendatum darin.
"""
import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import user_rules, vorlieben  # noqa: E402
from core.evaluate import evaluate, format_report  # noqa: E402
from core.inference import merge  # noqa: E402
from core.injector import generate  # noqa: E402
from packs import load_pack  # noqa: E402

from eval_documents import _scorer  # noqa: E402


def baue_faelle(scorer, pack, n=300, seed=99, rauschen=0.08, lang=None,
                regeln=None, melde=None):
    """Faelle (Text, Gold, Vorhersage) aus der Haltezone erzeugen.

    Ausgelagert, damit `build_release.py --verify` DIESELBE Rechnung
    benutzt statt einer dritten daneben. Zwei Zahlen aus zwei Testsets
    sind in diesem Projekt schon zweimal teuer geworden.
    """
    bsp = generate(n, seed=seed, rauschen=rauschen, zone="halten", lang=lang)
    cases, meta = [], []
    for i, e in enumerate(bsp, 1):
        model_spans = scorer.score(e.text) if scorer else []
        pred, _ = merge(e.text, model_spans, pack,
                        user_spans=user_rules.erkenne(e.text, regeln or []))
        cases.append((e.text, e.spans, pred))
        meta.append((e.lang, e.template_id))
        if melde and i % 50 == 0:
            melde(i, len(bsp))
    return cases, meta


def _kennzahlen(teil_cases, pack, ohne):
    r = evaluate(teil_cases, pack, excluded=ohne)
    gold = sum(t.gold for t in r.per_tag.values())
    return gold, r.leak_rate, r.micro_f1, len(r.leaked), len(r.over)


def je_gruppe(cases, meta, pack, ohne) -> str:
    """Nach Sprache und Vorlage aufschluesseln.

    Dieselbe Lehre wie `je_dokument` in `eval_documents.py`: eine
    Gesamtzahl ueber Ungleiches misst die Mischung, nicht die Kette.
    Hier kommt sie billiger — die Mischung ist bekannt und steuerbar.
    """
    z = []
    for titel, stelle in (("NACH SPRACHE", 0), ("NACH VORLAGE", 1)):
        gruppen: dict[str, list] = defaultdict(list)
        for fall, m in zip(cases, meta):
            gruppen[m[stelle]].append(fall)
        if len(gruppen) < 2:
            continue
        z.append("")
        z.append(titel)
        z.append(f"{'':<28}{'n':>5}{'Gold':>7}{'Leck':>6}"
                 f"{'Leckrate':>10}{'F1':>8}{'Uebermask':>11}")
        for name, teil in sorted(gruppen.items()):
            gold, rate, f1, lecks, over = _kennzahlen(teil, pack, ohne)
            z.append(f"{name[:27]:<28}{len(teil):>5}{gold:>7}{lecks:>6}"
                     f"{100*rate:>9.2f} %{f1:>8.3f}{over:>11}")
    return "\n".join(z)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--onnx", default=None)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--n", type=int, default=300,
                    help="Zahl der erzeugten Dokumente")
    ap.add_argument("--seed", type=int, default=99,
                    help="Keim der Erzeugung. NICHT der Trainingskeim — "
                         "derselbe Wert gibt dasselbe Testset")
    ap.add_argument("--rauschen", type=float, default=0.08)
    ap.add_argument("--lang", default=None)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--regeln", default=None)
    ap.add_argument("--top", type=int, default=20,
                    help="Zahl der ausgegebenen Lecks")
    ap.add_argument("--ohne", action="append", default=None, metavar="TAG")
    ap.add_argument("--org-nur", choices=["firmen", "behoerden"],
                    default=None,
                    help="ORG nur aus einer der beiden Quellen ziehen. "
                         "`firmen` misst die Verallgemeinerung auf ECHTE, "
                         "nie gesehene Zefix-Namen; `behoerden` misst bei "
                         "Modellen, die alle Behoerdennamen gesehen haben, "
                         "auswendig Gelerntes")
    args = ap.parse_args()

    pack = load_pack(args.pack)

    if args.org_nur:
        # Warum es diesen Schalter gibt: `ORG` zieht je zur Haelfte aus der
        # Sprachliste (`behoerden.json`) und aus der allgemeinen Liste (Zefix).
        # Fuer ein Modell, das mit ALLEN Behoerdennamen trainiert wurde, misst die
        # ORG-Zahl auf der Behoerdenhaelfte Auswendiglernen, nicht Erkennen;
        # sauber ist dann nur die Firmenhaelfte.
        from core import injector
        injector.GETEILT = {"ORG": 0.0 if args.org_nur == "firmen" else 1.0}
        print(f"⚠ ORG nur aus: {args.org_nur}. Nicht mit Laeufen "
              "vergleichbar, die beide Quellen mischen.")

    scorer = _scorer(args, pack)
    if scorer is None:
        print("Kette: Stufe 1 + 2, OHNE Modell — Grundlinie.\n")

    regeln = user_rules.lade(args.regeln, pack)
    if regeln:
        print(f"Eigene Regeln ({len(regeln)}): "
              + ", ".join(r.bezeichnung for r in regeln))
    else:
        print(f"⚠ KEINE eigenen Regeln geladen ({user_rules.VORGABE}).")
        print("  Die Zahlen sind NICHT mit Laeufen vergleichbar, die "
              "welche hatten.")

    ohne = (set(x for x in args.ohne if x) if args.ohne is not None
            else vorlieben.lade())

    begonnen = time.time()
    # ⚠️ zone="halten" steckt in `baue_faelle` und ist nicht abschaltbar.
    # Ohne sie zoege das Testset aus derselben Nomenklatur wie das
    # Training, und das Ergebnis liesse sich mit «erkennt Namen» und mit
    # «hat sie auswendig» gleich gut erklaeren.
    cases, meta = baue_faelle(
        scorer, pack, n=args.n, seed=args.seed, rauschen=args.rauschen,
        lang=args.lang, regeln=regeln,
        melde=lambda i, n: print(f"  {i}/{n} …", file=sys.stderr))
    dauer = time.time() - begonnen

    gold = sum(len(c[1]) for c in cases)
    print(f"\n{len(cases)} erzeugte Dokumente, {gold} Goldspannen, "
          f"Keim {args.seed}, Rauschen {args.rauschen}")
    print(f"Haltezone — kein Wert stand im Training. {dauer:.0f} s\n")

    print(format_report(evaluate(cases, pack, excluded=ohne), top=args.top))
    print(je_gruppe(cases, meta, pack, ohne))
    print()
    print("  ⚠️ Synthetisch. Misst genau, sieht aber nur, was in den")
    print("     Vorlagen steht. Die Golddokumente bleiben die")
    print("     Wirklichkeitspruefung — beide, nicht eines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
