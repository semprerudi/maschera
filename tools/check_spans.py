#!/usr/bin/env python3
"""Erzeugte Spannen auf Unplausibilitaeten pruefen.

    python3 tools/check_spans.py --n 2000
    python3 tools/check_spans.py --n 2000 --lang it

Der Merksatz lautet: nach jeder Aenderung zwanzig Beispiele LESEN. Dieses
Werkzeug ersetzt das nicht — es faengt nur die Fehlerklassen ab, die sich
mechanisch beschreiben lassen, damit beim Lesen Zeit fuer die anderen bleibt.

Geprueft wird, was in echten Dokumenten NIE vorkommt:

  * Ein `CITY`- oder `FULLNAME`-Wert mit Komma oder Zeilenumbruch darin.
    Kommt dabei zweimal dieselbe PLZ vor, hat der Adressmakro zwei Instanzen
    ineinandergeschoben — genau der Fall «8400 Winterthur, 8406 Winterthur».
  * Spannen, die weit laenger sind als der laengste Nomenklatureintrag.
  * Randleerzeichen und Randsatzzeichen.
  * Ueberlappende Goldspannen.
  * Werte, die vollstaendig in einem Decoy liegen.

Alles davon ist ein Datenfehler, kein Modellfehler — und ein Datenfehler
kostet Trainingszeit, bevor ihn jemand bemerkt.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.injector import generate  # noqa: E402

# Tags, deren Wert ein einzelner Name ist. Ein Komma oder Umbruch darin heisst,
# dass zwei Werte in eine Spanne gerutscht sind.
EINWERTIG = {"CITY", "FULLNAME", "GIVENNAME", "STREET", "PLACE_OF_ORIGIN",
             "ZIPCODE", "BUILDINGNUM", "MUNICIPALITY_ID"}

# Ausnahmen: diese Formen tragen das Zeichen von Rechts wegen.
ERLAUBT = re.compile(r"^(?:[^,\n]+,\s?[A-ZÄÖÜ][^,\n]+)$")  # «Meier, Hans»


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--lang", default=None)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--zeige", type=int, default=6)
    args = ap.parse_args()

    befunde: dict[str, list[str]] = {}
    zaehler: Counter = Counter()

    def melde(art: str, text: str) -> None:
        befunde.setdefault(art, []).append(text)
        zaehler[art] += 1

    beispiele = list(generate(args.n, seed=args.seed, lang=args.lang))
    for ex in beispiele:
        spans = sorted(ex.spans, key=lambda s: s.start)
        for i, s in enumerate(spans):
            wert = ex.text[s.start:s.end]

            if s.tag in EINWERTIG and ("\n" in wert or
                                       ("," in wert and not ERLAUBT.match(wert))):
                melde("mehrere Werte in einer Spanne",
                      f"{ex.template_id} {s.tag} {wert!r}")

            if wert != wert.strip():
                melde("Randleerzeichen", f"{ex.template_id} {s.tag} {wert!r}")

            if wert[-1:] in ",;:" or wert[:1] in ",;:":
                melde("Randsatzzeichen", f"{ex.template_id} {s.tag} {wert!r}")

            if not wert:
                melde("leere Spanne", f"{ex.template_id} {s.tag}")

            if i + 1 < len(spans) and spans[i + 1].start < s.end:
                melde("ueberlappende Goldspannen",
                      f"{ex.template_id} {s.tag}/{spans[i+1].tag} {wert!r}")

            # Zwei PLZ in einem Wert: der Adressmakro hat zwei Instanzen
            # ineinandergeschoben.
            #
            # NUR fuer Ortsnamen. Der erste Versuch prüfte alle Tags und
            # meldete 332 Fehlalarme — eine AHV-Nummer «756.5761.6987.10» und
            # ein IBAN bestehen aus Vierergruppen. Fuenfter Fall in Folge, in
            # dem das Pruefmuster falsch war und nicht der Code; diesmal in
            # dem Werkzeug, das genau solche Faelle finden soll.
            plz = (re.findall(r"\b\d{4}\b", wert)
                   if s.tag in ("CITY", "STREET", "ORG") else [])
            if len(plz) > 1:
                melde("mehrere PLZ in einer Spanne",
                      f"{ex.template_id} {s.tag} {wert!r}")

    print(f"{len(beispiele)} Beispiele, "
          f"{sum(len(e.spans) for e in beispiele)} Spannen"
          + (f", Sprache {args.lang}" if args.lang else ""))
    print()
    if not befunde:
        print("Keine Unplausibilitaeten gefunden.")
        print()
        print("  Das heisst NICHT, dass die Daten gut sind — nur, dass die")
        print("  mechanisch pruefbaren Fehler weg sind. Der Rest steht im")
        print("  Text: python3 tools/generate_dataset.py --n 20 --show")
        return 0

    for art, liste in sorted(befunde.items(), key=lambda kv: -len(kv[1])):
        print(f"--- {art}: {len(liste)}")
        for zeile in liste[:args.zeige]:
            print(f"    {zeile}")
        if len(liste) > args.zeige:
            print(f"    … {len(liste) - args.zeige} weitere")
        print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
