#!/usr/bin/env python3
"""Berufe (JOBTITLE) und Familienbeziehungen (FAMILYROLE) im Testset nachmarkieren.

    python3 tools/gold_berufe.py                       # JOBTITLE (seit 24.11.2026)
    python3 tools/gold_berufe.py --tag FAMILYROLE      # seit 25.11.2026

    python3 tools/gold_berufe.py
    python3 tools/gold_berufe.py --suche Sachbearbeiterin --suche "Leiter \\w+"

Gedacht fuer DICH im eigenen Terminal, nicht fuer Claude Code: das Werkzeug
zeigt Ausschnitte aus `$MASCHERA_GOLD/<pack>/real/`, und die sind gesperrt.

Ablauf je Fundstelle: Ausschnitt mit etwas Text davor und danach, die
heutige Goldmarkierung, dann eine Taste.

    j   ist eine Berufs- oder Funktionsbezeichnung -> JOBTITLE
    n   nein, so lassen
    +   Spanne um ein Wort nach rechts verlaengern (danach erneut fragen)
    -   Spanne um ein Wort nach links verlaengern
    q   aufhoeren; was bis dahin entschieden ist, wird gespeichert

Gefunden wird mit den Formen aus `berufe.json` (ganze Woerter, laengste
zuerst) und mit `--suche` (regulaerer Ausdruck, ohne Gross/klein). Was beides
verfehlt, findet nur das Lesen: die Liste ist eine Untergrenze.

Was mit einer bestehenden Spanne geschieht, wenn du `j` drueckst:

    keine Spanne                 JOBTITLE wird neu eingetragen
    Spanne genau gleich          das Tag wird auf JOBTITLE gesetzt
    Spanne umschliesst sie       geteilt: die Funktion wird JOBTITLE, der Rest
                                 behaelt sein Tag («Projektleiterin, Bundesamt
                                 fuer Justiz» -> JOBTITLE + ORG); Komma und
                                 Leerzeichen am Rand fallen weg
    teilweise ueberlappend       nicht automatisch: wird gemeldet, von Hand

`(koeder)` heisst: dieselbe Zeichenfolge ist auch ein Nachname. Steht dort ein
Name, bleibt er FULLNAME (Vorgabe bei Enter: n).

Vor dem ersten Schreiben in eine Datei legt das Werkzeug eine Kopie unter
`real/.sicherung-<zeit>/` an. `geprueft` bleibt, wie es ist.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))

from core import pfade  # noqa: E402

WORT = re.compile(r"\w[\w\-’'.]*")
TRENNER = " ,;:\n\t"


LISTE = {"JOBTITLE": "berufe.json", "FAMILYROLE": "familie.json"}


def lade_formen(pack_dir: Path, tag: str = "JOBTITLE") -> tuple[set[str], set[str]]:
    """Formen des Tags und Koeder (Nachnamen) aus der Liste, klein."""
    pfad = pack_dir / "nomenclatures" / "dist" / LISTE[tag]
    if not pfad.exists():
        raise SystemExit(f"{pfad} fehlt. Zuerst: "
                         "python3 packs/ch/nomenclatures/build.py --build")
    formen, koeder = set(), set()
    for e in json.loads(pfad.read_text(encoding="utf-8"))["entries"]:
        art, _, wert = e["name"].split("|", 2)
        (formen if art == tag else koeder).add(wert.casefold())
    return formen, koeder


def finde(text: str, formen: set[str], koeder: set[str],
          suche: list[str] | None = None) -> list[tuple[int, int, bool]]:
    """Fundstellen als (start, ende, ist_koeder), nach Position, ohne Doppel."""
    treffer: list[tuple[int, int, bool]] = []
    woerter = [(m.start(), m.end()) for m in WORT.finditer(text)]
    i = 0
    while i < len(woerter):
        for n in range(min(8, len(woerter) - i), 0, -1):
            a, e = woerter[i][0], woerter[i + n - 1][1]
            kandidat = text[a:e].rstrip(".")
            k = kandidat.casefold()
            if k in formen or k in koeder:
                treffer.append((a, a + len(kandidat), k in koeder))
                i += n
                break
        else:
            i += 1
    for muster in suche or []:
        for m in re.finditer(rf"\b(?:{muster})\b", text, re.IGNORECASE):
            if m.end() > m.start() and not any(
                    a < m.end() and m.start() < e for a, e, _ in treffer):
                treffer.append((m.start(), m.end(), False))
    return sorted(treffer)


def _ausschnitt(text: str, a: int, e: int, rand: int = 70) -> str:
    vor = text[max(0, a - rand):a].replace("\n", " ⏎ ")
    nach = text[e:e + rand].replace("\n", " ⏎ ")
    return f"…{vor}\033[1;43m{text[a:e]}\033[0m{nach}…"


def _wortgrenze(text: str, a: int, e: int, richtung: int) -> tuple[int, int]:
    if richtung > 0:
        m = WORT.search(text, e)
        return (a, m.end()) if m else (a, e)
    davor = [m for m in WORT.finditer(text, 0, a)]
    return (davor[-1].start(), e) if davor else (a, e)


def eintragen(spans: list[dict], a: int, e: int, text: str,
              tag: str = "JOBTITLE") -> str:
    """`tag` fuer [a, e) eintragen. Gibt zurueck, was geschah."""
    ueber = [s for s in spans if s["start"] < e and a < s["end"]]
    if not ueber:
        spans.append({"tag": tag, "start": a, "end": e})
        return "neu"
    if len(ueber) == 1 and ueber[0]["start"] == a and ueber[0]["end"] == e:
        alt = ueber[0]["tag"]
        ueber[0]["tag"] = tag
        return f"umgetaggt ({alt})"
    if len(ueber) == 1 and ueber[0]["start"] <= a and e <= ueber[0]["end"]:
        s = ueber[0]
        rest = []
        for x, y in ((s["start"], a), (e, s["end"])):
            while x < y and text[x] in TRENNER:
                x += 1
            while y > x and text[y - 1] in TRENNER:
                y -= 1
            if x < y:
                rest.append({**s, "start": x, "end": y})
        spans.remove(s)
        spans.extend(rest)
        spans.append({"tag": tag, "start": a, "end": e})
        return f"geteilt ({s['tag']} behaelt {len(rest)} Teil(e))"
    return "UEBERLAPPT TEILWEISE: von Hand"


def markiere(ordner: Path, formen: set[str], koeder: set[str],
             tag: str = "JOBTITLE",
             suche: list[str] | None = None, frage=input,
             ausgabe=print) -> dict[str, int]:
    """Alle Dokumente durchgehen. Gibt die Zaehlung zurueck (ohne Werte)."""
    zaehl = {"gezeigt": 0, "neu": 0, "umgetaggt": 0, "geteilt": 0,
             "von_hand": 0, "nein": 0, "dateien": 0}
    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sicherung = ordner / f".sicherung-{stempel}"
    aufhoeren = False
    for pfad in sorted(ordner.glob("*.json")):
        obj = json.loads(pfad.read_text(encoding="utf-8"))
        text, spans = obj["text"], obj["spans"]
        geaendert = False
        for a, e, ist_koeder in finde(text, formen, koeder, suche):
            if any(s["tag"] == tag and s["start"] <= a and e <= s["end"]
                   for s in spans):
                continue
            while True:
                heute = next((s["tag"] for s in spans
                              if s["start"] < e and a < s["end"]), "O")
                zaehl["gezeigt"] += 1
                ausgabe(f"\n{obj.get('id', pfad.stem)}  {a}-{e}  "
                        f"Gold heute: {heute}"
                        f"{'  (koeder)' if ist_koeder else ''}")
                ausgabe("  " + _ausschnitt(text, a, e))
                antwort = frage(f"  {tag}? [j/n/+/-/q] ").strip().lower()
                if antwort in ("+", "-"):
                    a, e = _wortgrenze(text, a, e, 1 if antwort == "+" else -1)
                    zaehl["gezeigt"] -= 1
                    continue
                break
            if antwort == "q":
                aufhoeren = True
                break
            if antwort != "j":
                zaehl["nein"] += 1
                continue
            ergebnis = eintragen(spans, a, e, text, tag)
            ausgabe(f"  -> {ergebnis}")
            if ergebnis.startswith("UEBERLAPPT"):
                zaehl["von_hand"] += 1
                continue
            zaehl[ergebnis.split()[0]] += 1
            geaendert = True
        if geaendert:
            sicherung.mkdir(exist_ok=True)
            shutil.copy2(pfad, sicherung / pfad.name)
            spans.sort(key=lambda s: (s["start"], s["end"]))
            pfad.write_text(json.dumps(obj, ensure_ascii=False, indent=2)
                            + "\n", encoding="utf-8")
            zaehl["dateien"] += 1
        if aufhoeren:
            break
    return zaehl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--tag", default="JOBTITLE", choices=sorted(LISTE),
                    help="was nachmarkiert wird (Vorgabe JOBTITLE)")
    ap.add_argument("--suche", action="append", default=[], metavar="MUSTER",
                    help="zusaetzlich suchen (regulaerer Ausdruck)")
    args = ap.parse_args()
    ordner, hinweis = pfade.gold_lesen(args.pack, "real")
    if hinweis:
        raise SystemExit(hinweis)
    formen, koeder = lade_formen(HIER.parent / "packs" / args.pack, args.tag)
    z = markiere(ordner, formen, koeder, args.tag, args.suche)
    print(f"\nGezeigt {z['gezeigt']}, neu {z['neu']}, umgetaggt "
          f"{z['umgetaggt']}, geteilt {z['geteilt']}, von Hand "
          f"{z['von_hand']}, nein {z['nein']}; {z['dateien']} Datei(en) "
          "geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
