#!/usr/bin/env python3
"""Prüft den Labelvertrag eines Packs und zeigt die Verteilung.

    python3 tools/check_taxonomy.py ch
    python3 tools/check_taxonomy.py ch --labels     # volle BIO-Liste
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packs import load_pack  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", nargs="?", default="ch")
    ap.add_argument("--labels", action="store_true", help="volle BIO-Liste ausgeben")
    args = ap.parse_args()

    pack = load_pack(args.pack)
    tags = pack.get_tags()
    labels = pack.get_labels()

    problems = pack.validate()
    if problems:
        print("FEHLER im Labelvertrag:")
        for p in problems:
            print(f"  - {p}")
        return 1

    by_stage = Counter(t.stage for t in tags)
    by_action = Counter(t.action for t in tags)
    by_budget = Counter(t.budget for t in tags if t.budget)

    print(f"Pack:            {args.pack}")
    print(f"Tags:            {len(tags)}")
    print(f"BIO-Labels:      {len(labels)}  (2 x {len(tags)} + 1)")
    print(f"Label-Hash:      {pack.get_label_hash()}")
    print()
    print("Stufen:          " + "  ".join(f"{s}: {by_stage[s]:>2}" for s in (1, 2, 3)))
    print(f"Aktion:          mask: {by_action['mask']:>2}   tag_only: {by_action['tag_only']:>2}")
    print("Budget:          " + "  ".join(f"{b}: {by_budget[b]:>2}" for b in "RAP"))
    print(f"bsPD:            {sum(t.bspd for t in tags)}")
    print()

    print("Nur getaggt, bleibt im Klartext:")
    for t in tags:
        if t.action == "tag_only":
            flag = " [bsPD]" if t.bspd else ""
            print(f"  {t.index:>2}  {t.tag:<18} Budget {t.budget}{flag}")
    print()

    print("Prüfsummen-Override (Stufe 1):")
    for t in tags:
        if t.stage == 1:
            print(f"  {t.index:>2}  {t.tag:<18} {t.note}")

    if args.labels:
        print()
        print("BIO-Labelliste (eingefrorene Reihenfolge):")
        for i, label in enumerate(labels):
            print(f"  {i:>3}  {label}")

    # Bezeichnungen sind kein Vertragsbestandteil — aber ein Tag ohne
    # Bezeichnung waere in der Oberflaeche ein leerer Menueeintrag, und das
    # faellt erst dort auf. Deshalb hier.
    sprachen = getattr(pack, "SPRACHEN", ("de",))
    if hasattr(pack, "get_bezeichnungen"):
        print()
        schlecht = False
        for sprache in sprachen:
            bez = pack.get_bezeichnungen(sprache)
            ohne = [t.tag for t in tags if not bez.get(t.tag)]
            zuviel = sorted(set(bez) - {t.tag for t in tags})
            if ohne:
                print(f"FEHLER {sprache}: ohne Bezeichnung ({len(ohne)}): "
                      f"{', '.join(ohne)}")
                schlecht = True
            if zuviel:
                print(f"FEHLER {sprache}: Bezeichnung ohne Tag: "
                      f"{', '.join(zuviel)}")
                schlecht = True
            if not ohne and not zuviel:
                print(f"Bezeichnungen {sprache}:  {len(bez)} von {len(tags)}")
        if schlecht:
            return 1

    print()
    print("OK — Labelvertrag konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
