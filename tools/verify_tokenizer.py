#!/usr/bin/env python3
"""Prueft die Annahmen ueber den echten Tokenizer (SPEC §11).

    pip install transformers --break-system-packages   # ~50 MB, KEIN torch
    python3 tools/verify_tokenizer.py
    python3 tools/verify_tokenizer.py --model jhu-clsp/mmBERT-base --n 500

Warum es dieses Skript gibt: `core/alignment.py` ist bewusst tokenizer-
unabhaengig und wurde gegen synthetische Offsets getestet. Damit ist die LOGIK
geprueft, nicht das Zusammenspiel mit dem echten Tokenizer. Vier Annahmen
bleiben offen, und dieses Skript prueft genau die:

  1. Gibt es einen schnellen Tokenizer? Ohne ihn kein offset_mapping.
  2. Schliessen die Offsets fuehrende Leerzeichen ein? (SentencePiece: ja)
  3. Ueberleben die Zeichenspannen die echte Subword-Zerlegung?
  4. Passen die Vorlagen in max_length, oder verlieren wir Beispiele?

Braucht weder GPU noch torch. Laeuft in unter einer Minute.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.alignment import align, decode  # noqa: E402
from core.injector import generate  # noqa: E402
from packs import load_pack  # noqa: E402

# Zeichen und Formen, bei denen es erfahrungsgemaess knirscht
TRICKY = [
    ("AHV-Nummer", "756.9217.0769.85"),
    ("UID", "CHE-116.281.710"),
    ("IBAN", "CH93 0076 2011 6238 5295 7"),
    ("QR-Referenz", "21 00000 00003 13947 14300 09017"),
    ("punktloses i", "Yılmaz"),
    ("Apostroph", "Sant'Antonino"),
    ("Schraegstrich", "Biel/Bienne"),
    ("Umlaut", "Grundstück Zürich Öhningen"),
    ("Accent", "Genève Épalinges"),
    ("Klammer verschachtelt", "Ursy (Montet (Glâne)) FR"),
    ("Tausenderapostroph", "CHF 1'250.00"),
    ("Bindestrichname", "Meier-Schmid"),
    ("Partikel", "de Weck / Da Silva"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="jhu-clsp/mmBERT-base")
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--max-length", type=int, default=512)
    args = ap.parse_args()

    try:
        from transformers import AutoTokenizer
    except ImportError:
        raise SystemExit(
            "transformers fehlt.\n"
            "  pip install transformers --break-system-packages\n"
            "torch wird NICHT gebraucht."
        )

    print(f"Modell: {args.model}")
    try:
        tok = AutoTokenizer.from_pretrained(args.model)
    except Exception as exc:
        raise SystemExit(
            f"Tokenizer nicht ladbar: {exc}\n\n"
            "Falls der Name nicht stimmt: auf huggingface.co suchen und mit "
            "--model uebergeben. Der Rest des Packs haengt nicht am Modellnamen."
        )

    problems: list[str] = []

    # --- 1. Schneller Tokenizer? -------------------------------------------
    print(f"\n1. Schneller Tokenizer:  {tok.is_fast}")
    if not tok.is_fast:
        problems.append(
            "KEIN schneller Tokenizer — ohne offset_mapping ist keine "
            "Ausrichtung moeglich. Anderes Modell noetig."
        )
    print(f"   Vokabular:            {tok.vocab_size}")
    print(f"   Modell-Maximallaenge: {getattr(tok, 'model_max_length', '?')}")

    # --- 2. Offset-Semantik -------------------------------------------------
    print("\n2. Schliessen Offsets fuehrende Leerzeichen ein?")
    probe = "Hans Meier wohnt hier"
    enc = tok(probe, return_offsets_mapping=True)
    leading = sum(
        1 for a, b in enc["offset_mapping"]
        if b > a and probe[a].isspace()
    )
    print(f"   {leading} von {len(enc['offset_mapping'])} Token beginnen mit "
          f"Leerzeichen")
    print(f"   -> _trim in core/alignment.py "
          f"{'wird gebraucht' if leading else 'laeuft leer, schadet aber nicht'}")

    # --- 3. Schwierige Zeichenketten ---------------------------------------
    print("\n3. Zerlegung heikler Zeichenketten")
    for label, text in TRICKY:
        pieces = tok.tokenize(text)
        unk = sum(1 for p in pieces if p == getattr(tok, "unk_token", "[UNK]"))
        flag = "  <- UNK!" if unk else ""
        print(f"   {label:<22} {len(pieces):>3} Stueck{flag}")
        print(f"   {'':<22} {pieces}")
        if unk:
            problems.append(f"{label}: {unk} unbekannte Token in {text!r}")

    # --- 4. Round-Trip ueber echte Beispiele -------------------------------
    print(f"\n4. Round-Trip mit echten Offsets, {args.n} Beispiele")
    pack = load_pack("ch")
    labels = list(pack.get_labels())
    examples = generate(args.n, seed=31337)

    bad, conflicts, dropped, weiter = 0, 0, 0, 0
    lengths: list[int] = []
    lost_tags: Counter = Counter()

    for e in examples:
        enc = tok(e.text, truncation=True, max_length=args.max_length,
                  return_offsets_mapping=True)
        offsets = enc["offset_mapping"]
        lengths.append(len(offsets))
        a = align(e.text, e.spans, offsets, labels)
        conflicts += a.boundary_conflicts
        if a.unlabelled_spans:
            dropped += 1
            for s in a.unlabelled_spans:
                lost_tags[s.tag] += 1
            continue
        back = decode(offsets, a.labels, e.text)
        want = sorted((s.tag, e.text[s.start:s.end].strip()) for s in e.spans)
        got = sorted((s.tag, e.text[s.start:s.end].strip()) for s in back)
        if want != got:
            # Die RICHTUNG entscheidet, ob das ein Problem ist.
            #
            # Deckt die zurueckgelesene Spanne den Sollwert vollstaendig ab und ist
            # nur laenger, wurde ZUVIEL maskiert — ein Satzpunkt, der im Platzhalter
            # verschwindet. Haesslich, aber kein Leck: im Zweifel MEHR maskieren.
            #
            # Fehlt dagegen ein Zeichen oder stimmt der Inhalt nicht, bleibt etwas im
            # Klartext stehen — ein Platzhalter, der Vollstaendigkeit vortaeuscht.
            paare = [(w, g) for w, g in zip(want, got) if w != g]
            inhalt = [
                (w, g) for w, g in paare
                if not (w[0] == g[0] and w[1] in g[1] and len(g[1]) > len(w[1]))
            ]
            if inhalt:
                bad += 1
                if bad <= 3:
                    print(f"   Abweichung in {e.template_id}: {inhalt[:3]}")
            else:
                weiter += 1
                if weiter <= 3:
                    print(f"   Nur ausgedehnt in {e.template_id}: {paare[:3]}")

    ok = len(examples) - bad - dropped
    print(f"   {ok}/{len(examples)} sauber, {bad} Abweichungen, "
          f"{dropped} wegen Abschneidung verworfen")
    if weiter:
        print(f"   {weiter} Spannen nur AUSGEDEHNT (zuviel maskiert, kein Leck)")
    print(f"   {conflicts} Grenzkonflikte")
    if bad:
        problems.append(f"{bad} Beispiele mit Round-Trip-Abweichung")

    # --- 5. Tokenbudget -----------------------------------------------------
    lengths.sort()
    p50 = lengths[len(lengths) // 2]
    p95 = lengths[int(len(lengths) * 0.95)]
    print(f"\n5. Tokenlaenge: Median {p50}, 95. Perzentil {p95}, "
          f"Maximum {lengths[-1]}")
    if lengths[-1] >= args.max_length:
        share = 100 * sum(1 for l in lengths if l >= args.max_length) / len(lengths)
        print(f"   {share:.1f} % stossen an max_length={args.max_length}")
        problems.append(
            f"{share:.1f} % der Beispiele werden abgeschnitten — "
            f"max_length erhoehen oder Vorlagen kuerzen"
        )
    else:
        print(f"   Alles unter max_length={args.max_length}. Kein Verlust.")
    if lost_tags:
        print(f"   Durch Abschneidung verlorene Tags: {dict(lost_tags)}")

    # ------------------------------------------------------------------------
    print()
    if problems:
        print(f"BEFUNDE — {len(problems)}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Alle Annahmen bestaetigt. core/alignment.py passt zum echten "
          "Tokenizer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
