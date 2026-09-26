#!/usr/bin/env python3
"""Schwellen am Dokument-Testset kalibrieren.

    python3 tools/kalibriere_schwellen.py --model runs/ch-v63b
    python3 tools/kalibriere_schwellen.py --model runs/ch-v63b --tag GIVENNAME

WAS DIESES WERKZEUG TUT — UND WAS NICHT
=======================================

Es setzt KEINE Schwelle. Es zeigt fuer jedes Tag die Kurve: bei welcher
Schwelle wieviele Lecks entstehen und wieviel uebermaskiert wird.

Der Grund ist der Zielkonflikt. Eine niedrigere Schwelle laesst mehr
Modelltreffer durch:

    weniger Lecks          <- der Zweck des Werkzeugs
    mehr Uebermaskierung   <- kostet den Zweck des Dokuments

**Welcher Punkt der richtige ist, ist eine fachliche Entscheidung, keine
rechnerische.** Bei `RELIGION` wiegt ein Leck schwerer als bei `TIME`. Genau
dafuer gibt es die Budgets R/A/P in der Taxonomie — und genau deshalb schlaegt
dieses Werkzeug vor und setzt nicht.

WENIGE DOKUMENTE SIND WENIG
===========================

Manche Tags haben im Testset Dutzende Goldspannen, andere eine einzige.
Eine Schwelle, die auf einer einzigen Spanne kalibriert ist, ist geraten
und nicht gemessen. Das Werkzeug schreibt die Belegzahl deshalb in jede
Zeile und schweigt bei Tags mit zu wenig Belegen.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))

from core import pfade  # noqa: E402
from core import user_rules  # noqa: E402
from core.evaluate import evaluate  # noqa: E402
from core.inference import merge  # noqa: E402
from core.masking import Span  # noqa: E402
from packs import load_pack  # noqa: E402

# ⚠️ Hier stand dieselbe `EVAL_DIR`-Zeile wie in `eval_documents.py` und
# `gold_from_markup.py`. Siehe dort — der Pfad kommt aus `core/pfade.py`.
STUFEN = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
MINDESTBELEGE = 5
# Unter dieser Spanne an Uebermaskierungen ueber den ganzen
# Schwellenbereich hat die Schwelle keine messbare Wirkung.
MINDESTWIRKUNG = 3


def _scorer(modell: str, pack, max_length: int = 512):
    from evaluate_model import TorchScorer
    s = TorchScorer(modell, max_length)
    s.check_contract(pack)
    return s


def lade_faelle(pack, modell: str, regeln, packname: str = "ch"):
    """Einmal durch das Modell, danach nur noch rechnen.

    Die Modellspannen samt Vertrauenswerten werden EINMAL erzeugt und dann
    fuer jede Schwellenstufe wiederverwendet. Neun Stufen mal 39 Tags waeren
    sonst 351 Modelllaeufe fuer dasselbe Ergebnis.
    """
    import json
    eval_dir, hinweis = pfade.gold_lesen(packname, "real")
    if hinweis:
        print(f"⚠️  {hinweis}\n")

    # Lag nichts da, liefe die Kalibrierung ueber null Faelle und schluege
    # Schwellen vor, die auf nichts beruhen — ein leerer Befund als Entwarnung.
    # Dieselbe Meldung wie in `eval_documents.py`.
    dateien = sorted(eval_dir.glob("*.json"))
    if not dateien:
        raise SystemExit(
            f"Keine Dokumente in {eval_dir}.\n"
            f"Ohne Golddokumente laesst sich keine Schwelle kalibrieren. "
            f"Liegt das Testset woanders, MASCHERA_GOLD darauf setzen "
            f"(erwartet wird darunter <pack>/real/).")

    scorer = _scorer(modell, pack)
    faelle = []
    for pfad in dateien:
        obj = json.loads(pfad.read_text(encoding="utf-8"))
        if not obj.get("geprueft"):
            continue
        text = obj["text"]
        gold = [Span(s["tag"], s["start"], s["end"]) for s in obj["spans"]]
        roh = scorer.score(text)
        faelle.append((obj.get("id", pfad.stem), text, gold, roh))

    # Zweiter leerer Befund, andere Ursache: Dateien sind da, aber keine ist
    # `geprueft`. Ohne diese Meldung sieht das Ergebnis genauso aus wie ein
    # leeres Verzeichnis — und beide Male stuende «0 Lecks».
    if not faelle:
        raise SystemExit(
            f"{len(dateien)} Datei(en) in {eval_dir}, aber keine mit "
            f"`geprueft: true`. Ungeprueftes Gold ist kein Massstab.")
    return faelle


def lade_faelle_synthetisch(pack, modell, n, seed, rauschen):
    """Dieselbe Quelle wie `tools/mess_synthetisch.py`: die Haltezone.

    WARUM ES DIESE ZWEITE QUELLE GIBT
    =================================
    Ein kleines Golddokument-Testset loest feine Unterschiede nicht auf:
    ueber den ganzen Schwellenbereich kann dieselbe Leckzahl stehen. Eine
    Reihe konstanter Werte belegt aber keine Unempfindlichkeit, sondern ein
    Geraet, das nichts sieht. 2000 Haltezone-Dokumente geben Zehntausende
    Goldspannen — dort hat eine Kurve Form.

    Der Vorbehalt gehoert mitgelesen: synthetisch geprueft wird die
    Verteilung, aus der erzeugt wird. Fuer eine Schwelle — eine Zahl UEBER dem
    Modell, nicht im Modell — ist das der richtige Massstab. Fuer eine
    Aenderung an der Erzeugung waere es Partei.

    Die rohen Modellspannen werden gebraucht, vor `merge`, damit jede
    Schwellenstufe ohne neuen Modelllauf gerechnet werden kann. Deshalb nicht
    `baue_faelle` aus `mess_synthetisch.py` — das fuehrt schon zusammen.
    """
    from core.injector import generate

    scorer = _scorer(modell, pack)
    faelle = []
    for e in generate(n, seed=seed, rauschen=rauschen, zone="halten"):
        faelle.append((e.template_id, e.text, e.spans, scorer.score(e.text)))
    if not faelle:
        raise SystemExit("Keine Dokumente erzeugt — --synthetisch > 0?")
    return faelle


def messe(faelle, pack, schwellen, regeln) -> tuple[int, int]:
    """(Lecks, Uebermaskierungen) bei diesen Schwellen."""
    cases = []
    for _, text, gold, roh in faelle:
        eigene = user_rules.erkenne(text, regeln)
        final, _ = merge(text, roh, pack, thresholds=schwellen,
                         user_spans=eigene)
        cases.append((text, gold, final))
    r = evaluate(cases, pack)
    return len(r.leaked), len(r.over)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--tag", default=None, help="nur ein Tag")
    ap.add_argument("--regeln", default=None)
    ap.add_argument("--synthetisch", type=int, default=0, metavar="N",
                    help="N Dokumente aus der Haltezone statt der "
                         "Golddokumente. 2000 geben 29 497 Goldspannen "
                         "gegen 211 — die Golddokumente loesen nicht auf")
    ap.add_argument("--seed", type=int, default=99,
                    help="Keim der Erzeugung, nur mit --synthetisch")
    ap.add_argument("--rauschen", type=float, default=0.08)
    a = ap.parse_args()

    pack = load_pack(a.pack)
    regeln = user_rules.lade(a.regeln, pack)
    if not regeln:
        print("⚠ KEINE eigenen Regeln geladen — Zahlen nicht vergleichbar.")

    if a.synthetisch:
        faelle = lade_faelle_synthetisch(pack, a.model, a.synthetisch,
                                         a.seed, a.rauschen)
        quelle = f"Haltezone, Keim {a.seed}, Rauschen {a.rauschen}"
    else:
        faelle = lade_faelle(pack, a.model, regeln, a.pack)
        quelle = "Golddokumente"
    gold_gesamt = sum(len(g) for _, _, g, _ in faelle)
    print(f"{len(faelle)} Dokumente, {gold_gesamt} Goldspannen — {quelle}")
    print(f"Modell {a.model}\n")

    grund = dict(pack.get_thresholds())
    belege: dict[str, int] = {}
    for _, _, gold, _ in faelle:
        for g in gold:
            belege[g.tag] = belege.get(g.tag, 0) + 1

    lecks0, over0 = messe(faelle, pack, grund, regeln)
    print(f"Ausgangslage: {lecks0} Leck(s), {over0} Uebermaskierungen\n")

    budgets = {t.tag: t.budget for t in pack.get_tags()}
    tags = [a.tag] if a.tag else sorted(
        t for t in grund if belege.get(t, 0) >= MINDESTBELEGE)

    kopf = (f"{'Tag':<18}{'Bud':>4}{'Beleg':>6}{'jetzt':>7}  "
            + "".join(f"{s:>6.2f}" for s in STUFEN))
    print(kopf)
    print(f"{'':<18}{'':>4}{'':>6}{'':>7}  "
          + "".join(f"{'L/U':>6}" for _ in STUFEN))

    vorschlaege, flach = [], []
    for tag in tags:
        n = belege.get(tag, 0)
        zeile = f"{tag:<18}{budgets.get(tag) or '—':>4}{n:>6}{grund[tag]:>7.2f}  "
        beste = None
        kurve = []
        for stufe in STUFEN:
            s = dict(grund)
            s[tag] = stufe
            lecks, over = messe(faelle, pack, s, regeln)
            kurve.append((stufe, lecks, over))
            zeile += f"{lecks}/{over}".rjust(6)
            # Bei Gleichstand gewinnt die NIEDRIGERE Schwelle: `<`, nicht `<=`. Eine
            # hoehere Schwelle laesst WENIGER durch und ist gegenueber dem SCHUTZ die
            # riskantere Wahl.
            #
            # ZUERST wenige Lecks, DANN wenig Uebermaskierung. Die wenigsten
            # Uebermaskierungen unter allen Stufen zu nehmen, die die Leckzahl nicht
            # erhoehen, bevorzugte eine Stufe mit WENIGER Lecks nie — und kehrte einen
            # Grundsatz um, der nicht verhandelbar ist: «Uebermaskierung ist kein Leck —
            # ein unterdruecktes Datum ist teurer als eines zuviel.»
            if beste is None or (lecks, over) < (beste[3], beste[2]):
                beste = (tag, stufe, over, lecks)

        # Erste Stufe, bei der ein zusaetzliches Leck entsteht — die Zahl,
        # die man beim Entscheiden braucht. Ein Optimum ohne Kippstelle
        # sagt nicht, wieviel Luft dahinter ist.
        kipp = next((st for st, lk, _ in kurve if lk > lecks0), None)
        zeile += f"   kippt {kipp:.2f}" if kipp else "   kippt —"
        print(zeile)

        # Flache Kurve = keine Aussage. Aendert sich die Uebermaskierung
        # ueber den ganzen Bereich kaum, filtert die Schwelle dieses Tag
        # gar nicht — es kommt fast vollstaendig aus Stufe 1 und 2. Ein
        # Werkzeug, das daraus eine Empfehlung ableitet, empfiehlt Rauschen.
        spanne = max(o for _, _, o in kurve) - min(o for _, _, o in kurve)
        if spanne < MINDESTWIRKUNG:
            flach.append((tag, spanne))
        else:
            # Nur bei GEMESSENER Verbesserung vorschlagen, nicht bei Gleichstand. Eine
            # andere Zahl mit denselben Lecks und derselben Uebermaskierung ist kein
            # Befund, und eine Ausnahme ist begruendungspflichtig: «drei Regler statt
            # Einzelzahlen».
            jetzt = next(((lk, o) for st, lk, o in kurve
                          if abs(st - grund[tag]) < 1e-9), None)
            if beste and (jetzt is None
                          or (beste[3], beste[2]) < jetzt):
                vorschlaege.append(beste)

    print("\n  L = Lecks gesamt, U = Uebermaskierungen gesamt, je Schwellenwert.")
    print("  kippt = erste Schwelle, bei der ein zusaetzliches Leck entsteht.")
    print(f"  Tags mit weniger als {MINDESTBELEGE} Goldspannen sind weggelassen —")
    print("  eine Schwelle auf einer Handvoll Belege ist geraten, nicht gemessen.")

    if flach:
        print("\nOHNE AUSSAGE — die Schwelle wirkt bei diesen Tags nicht:")
        for tag, spanne in flach:
            print(f"  {tag:<18}Uebermaskierung schwankt um {spanne} ueber den"
                  " ganzen Bereich")
        print("  Diese Tags kommen fast vollstaendig aus Stufe 1 und 2.")
        print("  Fuer sie ist die Modellschwelle bedeutungslos — das ist")
        print("  selbst ein Befund und kein Grund, eine Zahl zu setzen.")

    if vorschlaege:
        print("\nVORSCHLAEGE (keine Aenderung wird geschrieben):")
        for tag, stufe, over, lecks in vorschlaege:
            print(f"  {tag:<18}{grund[tag]:.2f} -> {stufe:.2f}   "
                  f"{lecks} Leck(s), {over} Uebermaskierungen")
        print("\n  Eintragen als AUSNAHME in packs/ch/taxonomy.yaml:")
        for tag, stufe, _, _ in vorschlaege:
            print(f"      {tag}: {stufe:.2f}")
        print()
        print("  Die Schwellen stehen pro BUDGET (R/A/P), nicht pro Tag —")
        print("  drei Regler fuer 39 Tags. Ein Tagname in derselben Tabelle")
        print("  ist eine Ausnahme und ueberschreibt das Budget.")
        print()
        print("  ⚠ REGEL: Eine Ausnahme braucht eine Messung, festgehalten")
        print("    neben dem Wert in taxonomy.yaml. `test_evaluate.py` Punkt 7")
        print("    prueft das und wird rot, wenn die Begruendung fehlt.")
        print("  ⚠ Das Budget mitlesen: Bei R wiegt ein Leck schwerer als")
        print("    bei P. Diese Abwaegung trifft kein Werkzeug.")
    else:
        # ⚠️ Die Quelle nennen, nicht «sieben Dokumente» annehmen.
        # Mit --synthetisch sind es 2000, und dann heisst «kein
        # Vorschlag» etwas voellig anderes: nicht «zu klein», sondern
        # «die Schwelle wirkt nicht».
        print(f"\nKein Vorschlag — die Vorgaben sind auf {quelle} "
              f"({len(faelle)} Dokumente,")
        print(f"{gold_gesamt} Goldspannen) nicht zu verbessern.")
        if a.synthetisch:
            print("Bei dieser Belegzahl heisst eine flache Kurve, dass die")
            print("Schwelle WIRKLICH nicht wirkt — nicht, dass das Testset")
            print("zu klein ist.")
        else:
            print("Das heisst NICHT, dass sie richtig sind; es heisst, dass")
            print("dieses Testset zu klein ist, um einen Unterschied zu")
            print("zeigen. Mit --synthetisch 2000 hat die Frage Aufloesung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
