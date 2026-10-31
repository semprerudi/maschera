#!/usr/bin/env python3
"""Die gemessenen NFAs erneut messen und mit dem Sollwert vergleichen.

    python3 tools/mess_nfa.py --model runs/ch-v63b
    python3 tools/mess_nfa.py --model runs/ch-v63b --release v1.2.3

Text ist das erfundene Beispiel der Oberflaeche, nichts Echtes. Gerechnet wird
nur auf der CPU, wie im ausgelieferten Paket. Die Sollwerte stehen in
`specs/03_nichtfunktional.md`, hier steht keine zweite Zahl.

⚠️ Laufzeiten haengen vom Rechner ab. Eine Ueberschreitung auf einem kleinen
Rechner ist ein Hinweis, kein Fehler; deshalb laeuft dies nicht in
`tools/run_tests.py`. Die Paketgroessen sind dagegen hart.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

# Wie oft das Beispiel aneinandergehaengt wird. Die Laengen stehen so im Katalog.
LAEUFE = {"NFA-002": 1, "NFA-003": 10, "NFA-004": 50}
PAKETE = {"AppImage": "NFA-011", "setup.exe": "NFA-011", ".dmg": "NFA-011",
          ".flatpak": "NFA-012"}


def soll(kennung: str) -> float:
    """Der erste Wert «unter X» im Abschnitt der Anforderung."""
    text = (WURZEL / "specs/03_nichtfunktional.md").read_text(encoding="utf-8")
    abschnitt = re.search(rf"^### {kennung}\b.*?(?=^##|\Z)", text, re.S | re.M)
    wert = re.search(r"unter ([\d.]+) (?:s|GB)", abschnitt.group(0))
    return float(wert.group(1))


def beispiel() -> str:
    js = (WURZEL / "app/static/maschera.js").read_text(encoding="utf-8")
    t = re.search(r"^const BEISPIEL = \{.*?^\};", js, re.S | re.M)
    lauf = subprocess.run(
        ["node", "-e", t.group(0) + ";process.stdout.write(JSON.stringify(BEISPIEL))"],
        capture_output=True, text=True, encoding="utf-8", check=True)
    wert = json.loads(lauf.stdout)["de"]
    return wert if isinstance(wert, str) else wert["text"]


def zeile(kennung: str, was: str, ist: float, einheit: str) -> bool:
    grenze = soll(kennung)
    gut = ist < grenze
    print(f"   {'OK  ' if gut else 'ZU VIEL'} {kennung}  {was:<26} "
          f"{ist:7.2f} {einheit}  (unter {grenze:g})")
    return gut


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--release", default=None, help="Tag, misst die Pakete")
    ap.add_argument("--repo", default="semprerudi/maschera")
    args = ap.parse_args()
    gut = True

    if args.model:
        t0 = time.perf_counter()
        from evaluate_model import TorchScorer
        from core.inference import filter_text
        from packs import load_pack
        pack = load_pack("ch")
        scorer = TorchScorer(args.model, 512)
        gut &= zeile("NFA-001", "Modell laden", time.perf_counter() - t0, "s")
        text = beispiel()
        for kennung, mal in LAEUFE.items():
            dok = (text + "\n\n") * mal
            zeiten = []
            for _ in range(3):
                a = time.perf_counter()
                filter_text(dok, pack, scorer, propagate=True,
                            thresholds=pack.get_thresholds())
                zeiten.append(time.perf_counter() - a)
            gut &= zeile(kennung, f"{len(dok)} Zeichen",
                         statistics.median(zeiten), "s")
        spitze = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
        gut &= zeile("NFA-010", "Arbeitsspeicher", spitze, "GB")

    if args.release:
        lauf = subprocess.run(
            ["gh", "release", "view", args.release, "--repo", args.repo,
             "--json", "assets"], capture_output=True, text=True, check=True)
        for a in json.loads(lauf.stdout)["assets"]:
            for marke, kennung in PAKETE.items():
                if a["name"].endswith(marke) or marke in a["name"].split("-")[-1]:
                    if not a["name"].endswith(".zsync"):
                        gut &= zeile(kennung, a["name"][-26:],
                                     a["size"] / 1e9, "GB")
    return 0 if gut else 1


if __name__ == "__main__":
    sys.exit(main())
