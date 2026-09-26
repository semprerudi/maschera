#!/usr/bin/env python3
"""Erzeugt das Trainingsset aus Vorlagen und Nomenklaturen.

    python3 tools/generate_dataset.py --n 20000 --out dataset.jsonl
    python3 tools/generate_dataset.py --n 20 --show

Ausgabeformat JSONL, eine Zeile je Beispiel:
    {"text": ..., "spans": [{"tag","start","end"}], "lang": ..., "template": ...}

Der Labelvertrag-Hash wandert in die Kopfzeile. Wer spaeter einen Checkpoint
laedt, kann pruefen, ob Modell und Datensatz dieselbe Labelreihenfolge meinen.
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.injector import generate  # noqa: E402
from packs import load_pack  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--lang", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--rauschen", type=float, default=0.0, metavar="ANTEIL",
                    help="Anteil der Namen und Orte mit Tippfehler, z.B. 0.08")
    ap.add_argument("--zone", default=None,
                    choices=["training", "halten"],
                    help="training = neun Zehntel der Werte, halten = das "
                         "zurueckgehaltene Zehntel (fuer den Auswertungssatz)")
    a = ap.parse_args()

    pack = load_pack("ch")
    examples = generate(a.n, seed=a.seed, rauschen=a.rauschen, zone=a.zone, lang=a.lang)

    if a.show:
        for e in examples[:3]:
            print(f"=== {e.template_id} [{e.lang}] ===")
            print(e.text)
            print("  ", [(s.tag, e.text[s.start:s.end]) for s in e.spans])
            print()

    tags = Counter(s.tag for e in examples for s in e.spans)
    langs = Counter(e.lang for e in examples)
    print(f"{len(examples)} Beispiele, {sum(tags.values())} Spannen")
    print(f"Sprachen: {dict(langs)}")
    print(f"Tags ohne Beleg: "
          f"{sorted({t.tag for t in pack.get_tags()} - set(tags))}")

    if a.out:
        # Laufend schreiben, nicht erst sammeln: 200'000 lange Zeilen als Python-Objekte sind ~1 GB, auf
        # einer ausgelasteten Maschine geht der Prozess in den Swap oder wird
        # abgeschossen — und die ganze Erzeugung ist verloren.
        path = Path(a.out)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "_meta": {"pack": "ch", "label_hash": pack.get_label_hash(),
                          "labels": len(pack.get_labels()), "seed": a.seed}
            }, ensure_ascii=False) + "\n")
            for e in examples:
                fh.write(json.dumps({
                    "text": e.text, "lang": e.lang, "template": e.template_id,
                    "spans": [{"tag": s.tag, "start": s.start, "end": s.end}
                              for s in e.spans],
                }, ensure_ascii=False) + "\n")
        print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
