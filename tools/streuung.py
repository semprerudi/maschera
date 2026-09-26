#!/usr/bin/env python3
"""Mehrere Laeufe je Bedingung messen — und die Streuung ausrechnen.

    python3 tools/streuung.py \\
        --bedingung "A=runs/lauf-a,runs/lauf-a-b" \\
        --bedingung "B=runs/lauf-b,runs/lauf-b-b" \\
        --einzeln runs/lauf-c

## Wozu

Wer Einzellaeufe vergleicht, liest jede Differenz als Wirkung. Derselbe
Datensatz mit zwei Keimen trainiert kann aber weiter auseinanderliegen
als zwei Bedingungen. Dieses Werkzeug beantwortet genau eine Frage:
**ist der Unterschied zwischen zwei Bedingungen groesser als das Rauschen
innerhalb einer?**

## Was es NICHT tut

Es druckt **keine Leckwerte**. `core/evaluate.py` fuehrt unter
`report.leaked` die ungeschuetzt gebliebenen Zeichenketten — und ein Leck
aus einem Golddokument IST das geschuetzte Datum. Hier zaehlen Lecks, sie
stehen nicht da.

## Zwei Laeufe sind keine Streuung

Bei n = 2 gibt es eine **Spanne**, keine Streuung, und das Werkzeug sagt
das auch so. Eine Standardabweichung aus zwei Werten sieht aus wie eine
Zahl und ist ein Wunsch. Ab n = 3 steht sie da, ab n = 4 traegt sie.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))

from core import user_rules  # noqa: E402
from core import vorlieben  # noqa: E402
from core.evaluate import evaluate  # noqa: E402
from core.inference import merge  # noqa: E402
from eval_documents import lade_gold  # noqa: E402
from packs import load_pack  # noqa: E402

# Das Laden der Golddokumente steht in `eval_documents.lade_gold()` und
# wird von dort geholt, nicht nachgebaut — zwei Kopien einer Ladelogik
# hiessen zwei verschiedene Testsets unter demselben Namen.
# `tests/test_goldpfad.py` Punkt 6 fuehrt dieses Werkzeug deshalb mit.

# Kleiner ist besser: bei diesen Groessen zeigt der Pfeil nach unten.
KLEINER_BESSER = {"Lecks", "Uebermask", "Leckrate %"}


def messe(modell: str, dokumente, pack, regeln, ohne, tags, max_length):
    """Ein Modell gegen das Testset. Gibt die Kennzahlen als dict."""
    from evaluate_model import TorchScorer

    scorer = TorchScorer(modell, max_length)
    scorer.check_contract(pack)

    cases = []
    for text, gold, _meta in dokumente:
        pred, _ = merge(text, scorer.score(text), pack,
                        user_spans=user_rules.erkenne(text, regeln))
        cases.append((text, gold, pred))

    r = evaluate(cases, pack, excluded=ohne)
    werte = {
        "Micro-F1": r.micro_f1,
        "Lecks": float(len(r.leaked)),
        "Uebermask": float(len(r.over)),
        "Leckrate %": 100 * r.leak_rate,
    }
    for tag in tags:
        s = r.per_tag.get(tag)
        werte[f"{tag} F1"] = s.f1 if s else 0.0

    # Das Modell wieder freigeben — acht Laeufe hintereinander passen sonst
    # nicht auf eine Karte mit 8 GB.
    del scorer
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    return werte


def urteil(d: float, sg: float) -> str:
    """Wie ein Unterschied `d` gegen eine Streuung `sg` zu lesen ist.

    Die Schwellen sind bewusst grob: unter einem σ heisst NICHT AUFGELOEST,
    nicht «kein Unterschied». Das Testset sieht es nicht — ueber die Sache
    selbst sagt das nichts.
    """
    if sg == 0:
        return "σ = 0 — zu wenige Laeufe, um etwas zu sagen"
    if d > 2 * sg:
        return f"Δ ist {d/sg:.1f}× σ — deutlich"
    if d > sg:
        return f"Δ ist {d/sg:.1f}× σ — schwach, nicht belegt"
    return (f"Δ ist {d/sg:.1f}× σ — NICHT AUFGELOEST, "
            f"das Testset sieht es nicht")


def _zeile(name: str, werte: dict, spalten, genau=False, breite=18) -> str:
    """Eine Tabellenzeile. `genau` gibt auch Lecks mit Nachkommastellen.

    Ein Mittel und ein σ ueber Lecks sind gebrochene Zahlen. Sie auf ganze
    zu runden, weil die Einzelwerte ganz sind, macht aus σ = 1.5 eine 2 —
    und genau diese Groesse entscheidet, ob ein Unterschied aufgeloest ist.
    """
    z = f"{name:<{breite}}"
    for s in spalten:
        v = werte[s]
        rund = genau or s in ("Micro-F1", "Leckrate %") or "F1" in s
        z += f"{v:>12.3f}" if rund else f"{v:>12.0f}"
    return z


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bedingung", action="append", default=[],
                    metavar="NAME=PFAD,PFAD",
                    help="Eine Bedingung mit ihren Laeufen. Mehrfach angebbar.")
    ap.add_argument("--einzeln", action="append", default=[], metavar="PFAD",
                    help="Ein Lauf ohne Bedingung — wird gegen die "
                         "Bedingungen gestellt.")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--tag", action="append", default=None, metavar="TAG",
                    help="Zusaetzliche Tag-F1 in der Tabelle. Vorgabe: ORG.")
    ap.add_argument("--regeln", default=None)
    ap.add_argument("--auch-ungeprueft", action="store_true")
    ap.add_argument("--ohne", action="append", default=None, metavar="TAG")
    ap.add_argument("--json", default=None,
                    help="Kennzahlen zusaetzlich hierhin schreiben.")
    args = ap.parse_args()

    if not args.bedingung and not args.einzeln:
        raise SystemExit("Nichts zu messen — --bedingung oder --einzeln.")

    tags = args.tag if args.tag is not None else ["ORG"]
    pack = load_pack(args.pack)
    dokumente, hinweis, uebersprungen = lade_gold(args.pack,
                                                  args.auch_ungeprueft)
    if hinweis:
        print(f"⚠️  {hinweis}\n")
    if uebersprungen:
        print(f"Uebersprungen, weil ungeprueft: {', '.join(uebersprungen)}\n")

    # Dieselbe Kette wie bei `eval_documents.py`, sonst sind die Zahlen nicht
    # vergleichbar. Fehlende Benutzerregeln LAUT melden — sonst fiele ein
    # Benutzertag auf einer anderen Maschine still auf 0.000, sichtbar nur an
    # einer fehlenden Zeile.
    regeln = user_rules.lade(args.regeln, pack)
    if regeln:
        print(f"Eigene Regeln ({len(regeln)}): "
              + ", ".join(r.bezeichnung for r in regeln))
    else:
        print(f"⚠ KEINE eigenen Regeln geladen ({user_rules.VORGABE}).")
        print("  Die Zahlen sind NICHT mit Laeufen vergleichbar, die welche")
        print("  hatten — X_-Tags koennen dann gar nicht entstehen.")

    ohne = (set(x for x in args.ohne if x) if args.ohne is not None
            else vorlieben.lade())
    if ohne:
        vorlieben.pruefe(ohne, pack, auch_bspd=True)

    gold = sum(len(g) for _t, g, _m in dokumente)
    print(f"{len(dokumente)} Dokumente, {gold} Goldspannen, "
          f"dasselbe Testset fuer alle Laeufe.\n")

    spalten = ["Micro-F1", "Lecks", "Uebermask", "Leckrate %"] \
        + [f"{t} F1" for t in tags]

    bedingungen: dict[str, list[str]] = {}
    for roh in args.bedingung:
        if "=" not in roh:
            raise SystemExit(f"--bedingung braucht NAME=PFAD,PFAD: {roh!r}")
        name, pfade_roh = roh.split("=", 1)
        bedingungen[name.strip()] = [p.strip() for p in pfade_roh.split(",")
                                     if p.strip()]

    ergebnis: dict[str, dict[str, dict]] = {}
    for name, laeufe in bedingungen.items():
        ergebnis[name] = {}
        for lauf in laeufe:
            print(f"  … {lauf}", flush=True)
            ergebnis[name][lauf] = messe(lauf, dokumente, pack, regeln, ohne,
                                         tags, args.max_length)
    einzeln = {}
    for lauf in args.einzeln:
        print(f"  … {lauf}", flush=True)
        einzeln[lauf] = messe(lauf, dokumente, pack, regeln, ohne, tags,
                              args.max_length)

    kopf = f"{'Lauf':<18}" + "".join(f"{s:>12}" for s in spalten)

    print("\nJE LAUF")
    print(kopf)
    for name, laeufe in ergebnis.items():
        for lauf, werte in laeufe.items():
            print(_zeile(Path(lauf).name, werte, spalten) + f"   [{name}]")
    for lauf, werte in einzeln.items():
        print(_zeile(Path(lauf).name, werte, spalten) + "   [einzeln]")

    print("\nJE BEDINGUNG")
    print(kopf)
    mittel: dict[str, dict[str, float]] = {}
    streuung: dict[str, dict[str, float]] = {}
    for name, laeufe in ergebnis.items():
        n = len(laeufe)
        mittel[name] = {s: statistics.fmean(w[s] for w in laeufe.values())
                        for s in spalten}
        print(_zeile(f"{name} (n={n})", mittel[name], spalten, genau=True)
              + "   Mittel")
        if n < 2:
            print(f"{'':<18}  ein Lauf — weder Mittel noch Streuung")
            continue
        streuung[name] = {s: statistics.stdev(w[s] for w in laeufe.values())
                          for s in spalten}
        print(_zeile("", streuung[name], spalten, genau=True) + "   σ")
        if n == 2:
            print(f"{'':<18}  ⚠ n=2 — σ aus zwei Werten ist |Δ|/√2 und damit\n                  eine SPANNE in anderer Schreibweise, keine Streuung.")

    if len(mittel) == 2:
        (a, b) = list(mittel)
        print(f"\nUNTERSCHIED  {a}  gegen  {b}")
        print(kopf)
        diff = {s: mittel[b][s] - mittel[a][s] for s in spalten}
        print(_zeile("Δ Mittel", diff, spalten, genau=True))
        if a in streuung and b in streuung:
            groesste = {s: max(streuung[a][s], streuung[b][s]) for s in spalten}
            print(_zeile("groesstes σ", groesste, spalten, genau=True))
            print()
            # Ein σ aus zwei Werten kann zufaellig winzig ausfallen, und dann wird
            # jedes Vielfache davon gross: bei 0.763 und 0.756 ist σ = 0.005, und
            # «+13σ» saehe aus wie ein Befund und waere ein Rundungsartefakt.
            if min(len(l) for l in ergebnis.values()) < 3:
                print("  ⚠ Mindestens eine Bedingung hat n < 3. Die "
                      "Vielfachen unten stehen auf einem σ,")
                print("    das selbst kaum bestimmt ist — als Richtung "
                      "lesbar, nicht als Mass.")
                print()
            for s in spalten:
                print(f"  {s:<14}{urteil(abs(diff[s]), groesste[s])}")

    # Auch dann, wenn nur eine Bedingung gemessen wird — ein Einzellauf
    # gegen eine fertige Bedingung ist ein haeufiger Fall.
    for lauf, werte in einzeln.items():
        if mittel:
            print(f"\n{Path(lauf).name} gegen die Bedingungen")
            for name in mittel:
                if name not in streuung:
                    print(f"  {name:<16}nur ein Lauf — kein Vergleich")
                    continue
                if len(ergebnis[name]) < 3:
                    # Hier NICHT bloss warnen, sondern schweigen: ein
                    # z-Wert gegen ein σ aus zwei Laeufen ist keine
                    # abgeschwaechte Aussage, sondern eine erfundene.
                    print(f"  {name:<16}n={len(ergebnis[name])} — kein "
                          f"belastbares σ, keine Vielfachen")
                    continue
                teile = []
                for s in spalten:
                    sg = streuung[name][s]
                    if sg == 0:
                        continue
                    z = (werte[s] - mittel[name][s]) / sg
                    teile.append(f"{s} {z:+.1f}σ")
                print(f"  {name:<16}" + "  ".join(teile))
            print("  Ein Einzellauf gegen ein Mittel ist ein Hinweis, kein")
            print("  Beleg — solange von ihm selbst nur ein Lauf vorliegt.")
            print("  Und ein σ aus vier Werten ist selbst noch unsicher:")
            print("  ein grosses Vielfaches heisst 'deutlich daneben',")
            print("  nicht 'um genau so viel daneben'.")

    if args.json:
        alles = {"testset": {"dokumente": len(dokumente), "goldspannen": gold},
                 "bedingungen": ergebnis, "einzeln": einzeln}
        Path(args.json).write_text(
            json.dumps(alles, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGeschrieben: {args.json}")

    print("\n  Kein Leckwert steht in dieser Ausgabe — nur Anzahlen. Wer die")
    print("  Werte braucht, nimmt `eval_documents.py` am Terminal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
