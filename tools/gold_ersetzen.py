#!/usr/bin/env python3
"""Werte in einem Golddokument nachtraeglich ersetzen.

    # erst sehen, was drinsteht
    python3 tools/gold_ersetzen.py --zeigen $MASCHERA_GOLD/ch/real/de-brief-001.json
    python3 tools/gold_ersetzen.py --zeigen-tag EMAIL $MASCHERA_GOLD/ch/real/

    # dann ersetzen
    python3 tools/gold_ersetzen.py $MASCHERA_GOLD/ch/real/de-brief-001.json \\
        --ersetze "@firma-a.ch=@firma-b.ch" \\
        --ersetze "@amt-a.ch=@amt-b.ch"

⚠️ **Warum das nicht mit Suchen-und-Ersetzen geht.** Ein Golddokument
besteht aus `text` und `spans` mit `start`/`end` — Zeichenpositionen im Text.
Wird der Text auch nur um ein Zeichen kuerzer, zeigen alle nachfolgenden
Spannen ins Leere. Aus einer gepruegten Messgrundlage wuerde stillschweigend
eine falsche: die Auswertung liefe weiter, die Zahlen waeren Unsinn, und
niemand saehe es.

Dieses Werkzeug verschiebt die Spannen mit und prueft danach, dass jede
Spanne noch denselben Text umschliesst wie vorher.

⚠️ **Es ersetzt in `text`, nicht in `spans`.** Liegt der zu ersetzende Wert
INNERHALB einer Spanne — etwa die Domain in einer als EMAIL markierten
Adresse —, aendert sich der Inhalt der Spanne. Das ist gewollt, und der
Bericht sagt es. Faengt oder endet eine Spanne MITTEN im ersetzten Bereich,
bricht das Werkzeug ab: dann waere nicht mehr entscheidbar, wo sie hingehoert.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def lade(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def dateien(pfad: Path) -> list[Path]:
    if pfad.is_file():
        return [pfad]
    return sorted(p for p in pfad.glob("*.json"))


def zeigen(d: dict, nur_tag: str | None) -> None:
    text = d["text"]
    for s in d["spans"]:
        if nur_tag and s["tag"] != nur_tag:
            continue
        wert = text[s["start"]:s["end"]]
        print(f"  {s['start']:6} {s['tag']:<18} {wert!r}")


def ersetze(d: dict, paare: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """Ersetzen und alle Spannen mitverschieben."""
    text: str = d["text"]
    spans = [dict(s) for s in d["spans"]]
    # Was jede Spanne VOR der Aenderung umschloss — die Gegenprobe danach.
    vorher = [text[s["start"]:s["end"]] for s in spans]
    bericht: list[str] = []

    for alt, neu in paare:
        if alt not in text:
            bericht.append(f"nicht gefunden: {alt!r}")
            continue
        anzahl = text.count(alt)
        verschiebung = len(neu) - len(alt)

        # Von hinten nach vorne, damit die noch nicht bearbeiteten Stellen
        # ihre Positionen behalten.
        stellen = []
        pos = text.find(alt)
        while pos != -1:
            stellen.append(pos)
            pos = text.find(alt, pos + 1)

        for pos in reversed(stellen):
            ende = pos + len(alt)
            for s in spans:
                # ⚠️ Halb ueberlappend: die Spanne beginnt oder endet mitten
                # im ersetzten Bereich. Dann ist nicht entscheidbar, wo ihre
                # Grenze nachher liegen soll — und Raten hiesse, eine
                # Messgrundlage zu erfinden.
                halb = ((s["start"] < pos < s["end"] < ende)
                        or (pos < s["start"] < ende < s["end"]))
                if halb:
                    raise SystemExit(
                        f"ABBRUCH: Spanne {s['tag']} "
                        f"[{s['start']}:{s['end']}] ueberlappt die Stelle "
                        f"[{pos}:{ende}] nur halb.\n"
                        f"  Ersetzung von Hand vornehmen oder die Spanne "
                        f"anpassen.")
            for s in spans:
                if s["start"] >= ende:
                    s["start"] += verschiebung
                    s["end"] += verschiebung
                elif s["end"] > pos:            # Stelle liegt in der Spanne
                    s["end"] += verschiebung
            text = text[:pos] + neu + text[ende:]

        bericht.append(f"{alt!r} -> {neu!r}, {anzahl}x"
                       + (f", Verschiebung {verschiebung:+d}"
                          if verschiebung else ", laengengleich"))

    # Gegenprobe: jede Spanne muss noch dasselbe umschliessen wie vorher —
    # ausser sie enthielt einen ersetzten Wert.
    for s, alt_wert in zip(spans, vorher):
        neu_wert = text[s["start"]:s["end"]]
        if neu_wert == alt_wert:
            continue
        erwartet = alt_wert
        for a, n in paare:
            erwartet = erwartet.replace(a, n)
        if neu_wert != erwartet:
            raise SystemExit(
                f"ABBRUCH: Spanne {s['tag']} umschliesst nachher "
                f"{neu_wert!r}, erwartet war {erwartet!r}.\n"
                f"  Die Datei wurde NICHT geschrieben.")
        bericht.append(f"  in Spanne {s['tag']}: {alt_wert!r} -> {neu_wert!r}")

    d = dict(d)
    d["text"] = text
    d["spans"] = spans
    return d, bericht


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Werte in Golddokumenten ersetzen, Spannen mitfuehren.")
    ap.add_argument("pfad", help="Datei oder Verzeichnis")
    ap.add_argument("--zeigen", action="store_true",
                    help="alle Spannen mit ihrem Wert anzeigen")
    ap.add_argument("--zeigen-tag", default=None,
                    help="nur Spannen dieses Tags anzeigen, z.B. EMAIL")
    ap.add_argument("--ersetze", action="append", default=[],
                    metavar="ALT=NEU", help="mehrfach angebbar")
    ap.add_argument("--probe", action="store_true",
                    help="nur berichten, nichts schreiben")
    args = ap.parse_args()

    pfad = Path(args.pfad)
    if not pfad.exists():
        raise SystemExit(f"Nicht gefunden: {pfad}")

    paare = []
    for p in args.ersetze:
        if "=" not in p:
            raise SystemExit(f"Kein '=' in --ersetze {p!r}")
        alt, neu = p.split("=", 1)
        if not alt:
            raise SystemExit("Leerer Suchtext")
        paare.append((alt, neu))

    for datei in dateien(pfad):
        d = lade(datei)
        if args.zeigen or args.zeigen_tag:
            print(f"\n=== {datei.name}  ({d.get('lang')}, "
                  f"{len(d['spans'])} Spannen) ===")
            zeigen(d, args.zeigen_tag)
            continue
        if not paare:
            raise SystemExit("Nichts zu tun: --zeigen oder --ersetze angeben.")

        if not any(alt in d["text"] for alt, _ in paare):
            continue
        neu_d, bericht = ersetze(d, paare)
        print(f"\n=== {datei.name} ===")
        for z in bericht:
            print(f"  {z}")
        if args.probe:
            print("  (Probe — nichts geschrieben)")
            continue
        # Ueber eine Nebendatei, damit ein Abbruch mitten im Schreiben nicht
        # die Messgrundlage zerstoert.
        neben = datei.with_suffix(".json.neu")
        neben.write_text(json.dumps(neu_d, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        neben.replace(datei)
        print(f"  geschrieben: {len(neu_d['text'])} Zeichen, "
              f"{len(neu_d['spans'])} Spannen")

    if not args.zeigen and not args.zeigen_tag and not args.probe and paare:
        print("\n⚠️ Danach die Auswertung neu laufen lassen — fruehere Zahlen")
        print("   stammen aus dem Stand VOR dieser Aenderung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
