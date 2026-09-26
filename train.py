#!/usr/bin/env python3
"""Training des Token-Klassifikators (SPEC §3 Stufe 3, §12).

    python3 train.py --data dataset.jsonl --out runs/ch-stufe1
    python3 train.py --data dataset.jsonl --dry-run    # ohne GPU pruefbar

Laeuft NICHT in der Entwicklungsumgebung (kein torch, kein Zugriff auf
huggingface.co). Es braucht eine GPU: rund 8 GB VRAM reichen zum
Ausprobieren, fuer den richtigen Lauf sind 24 GB gemessen.

    pip install torch transformers datasets accelerate --break-system-packages

**Was hier NICHT passiert:** Es wird nichts an das Modell angepasst, was den
Labelvertrag betrifft. Die Labelreihenfolge kommt aus dem Pack, ihr Hash wandert
in den Checkpoint, und beim Laden wird er geprueft. Ohne diese Pruefung laedt man
irgendwann ein Modell mit falschem Mapping und bekommt Ausgaben, die plausibel
aussehen und falsch sind.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.alignment import IGNORE_INDEX, align  # noqa: E402
from core.masking import Span  # noqa: E402
from packs import load_pack  # noqa: E402

DEFAULT_MODEL = "jhu-clsp/mmBERT-base"


def load_dataset(path: Path) -> tuple[list[dict], dict]:
    """JSONL laden. Erste Zeile ist die Kopfzeile mit dem Labelvertrag-Hash."""
    meta: dict = {}
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            if "_meta" in obj:
                meta = obj["_meta"]
                continue
            rows.append(obj)
    return rows, meta


def check_contract(meta: dict, pack) -> None:
    """Datensatz und Pack muessen dieselbe Labelreihenfolge meinen."""
    have = pack.get_label_hash()
    want = meta.get("label_hash")
    if want and want != have:
        raise SystemExit(
            "ABBRUCH: Labelvertrag stimmt nicht ueberein.\n"
            f"  Datensatz: {want}\n"
            f"  Pack:      {have}\n"
            "Der Datensatz wurde mit einer anderen Taxonomie erzeugt. Neu "
            "generieren oder den passenden Pack-Stand auschecken — auf keinen "
            "Fall die Pruefung abschalten."
        )
    if meta.get("labels") and meta["labels"] != len(pack.get_labels()):
        raise SystemExit("ABBRUCH: Labelanzahl weicht ab.")


def build_features(rows, tokenizer, labels, max_length: int):
    """Texte tokenisieren und Zeichenspannen auf Tokenlabels abbilden."""
    texts = [r["text"] for r in rows]
    encoded = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        return_offsets_mapping=True,
        padding=False,
    )

    all_labels, conflicts, dropped = [], 0, 0
    keep = []
    for i, row in enumerate(rows):
        spans = [Span(s["tag"], s["start"], s["end"]) for s in row["spans"]]
        offsets = encoded["offset_mapping"][i]
        a = align(row["text"], spans, offsets, labels)
        conflicts += a.boundary_conflicts
        # Beispiele mit abgeschnittenen Entitaeten verwerfen statt mit
        # unvollstaendigen Labels trainieren
        if a.unlabelled_spans:
            dropped += 1
            continue
        keep.append(i)
        all_labels.append(a.ids)

    print(f"  {len(keep)}/{len(rows)} Beispiele verwendet, "
          f"{dropped} wegen Abschneidung verworfen, "
          f"{conflicts} Grenzkonflikte")
    return encoded, all_labels, keep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--eval-data", default=None)
    ap.add_argument("--out", default="runs/ch")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    # 512 als Vorgabe. `max_length` ist eine OBERGRENZE fuer das Abschneiden,
    # keine Fenstergroesse, die reserviert wird: `build_features` tokenisiert
    # mit `padding=False`, gepolstert wird je Stapel auf dessen laengste
    # Sequenz. 512 kostet also nichts. Mit 256 wuerden dagegen Beispiele
    # verworfen, deren Entitaet in den abgeschnittenen Teil faellt.
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--dry-run", action="store_true",
                    help="nur Datensatz und Labelvertrag pruefen")
    args = ap.parse_args()

    pack = load_pack(args.pack)
    labels = list(pack.get_labels())
    rows, meta = load_dataset(Path(args.data))
    check_contract(meta, pack)

    print(f"Pack:       {args.pack}")
    print(f"Labels:     {len(labels)}  Hash {pack.get_label_hash()[:16]}…")
    print(f"Beispiele:  {len(rows)}")

    if args.dry_run:
        from collections import Counter
        tags = Counter(s["tag"] for r in rows for s in r["spans"])
        fehlend = sorted({t.tag for t in pack.get_tags()} - set(tags))
        print(f"Sprachen:   {dict(Counter(r.get('lang','?') for r in rows))}")
        print(f"Tags ohne Beleg: {fehlend or 'keine'}")
        selten = sorted((n, t) for t, n in tags.items() if n < 30)[:8]
        if selten:
            print(f"Selten (<30): {[(t, n) for n, t in selten]}")
        print("\nTrockenlauf — Labelvertrag stimmt, kein Training gestartet.")
        return 0

    try:
        import numpy as np
        import torch
        from torch.utils.data import Dataset
        from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                                  DataCollatorForTokenClassification, Trainer,
                                  TrainingArguments)
    except ImportError as exc:
        raise SystemExit(
            f"{exc}\n\nFuer das Training:\n"
            "  pip install torch transformers datasets accelerate "
            "--break-system-packages\n"
            "Zum blossen Pruefen des Datensatzes: --dry-run"
        )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if not tokenizer.is_fast:
        raise SystemExit(
            "Es wird ein schneller Tokenizer gebraucht — nur der liefert "
            "offset_mapping, und ohne das ist keine Ausrichtung moeglich."
        )

    print("\nTrainingsdaten:")
    enc, lab, keep = build_features(rows, tokenizer, labels, args.max_length)

    class TokenDataset(Dataset):
        def __init__(self, encoded, label_ids, keep):
            self.encoded, self.labels, self.keep = encoded, label_ids, keep

        def __len__(self):
            return len(self.keep)

        def __getitem__(self, i):
            j = self.keep[i]
            return {
                "input_ids": self.encoded["input_ids"][j],
                "attention_mask": self.encoded["attention_mask"][j],
                "labels": self.labels[i],
            }

    train_ds = TokenDataset(enc, lab, keep)

    eval_ds = None
    if args.eval_data:
        print("Auswertungsdaten:")
        erows, emeta = load_dataset(Path(args.eval_data))
        check_contract(emeta, pack)
        eenc, elab, ekeep = build_features(erows, tokenizer, labels,
                                           args.max_length)
        eval_ds = TokenDataset(eenc, elab, ekeep)

    model = AutoModelForTokenClassification.from_pretrained(
        args.model,
        num_labels=len(labels),
        id2label={i: l for i, l in enumerate(labels)},
        label2id={l: i for i, l in enumerate(labels)},
    )

    def compute_metrics(pred):
        logits, gold = pred
        best = np.argmax(logits, axis=-1)
        mask = gold != IGNORE_INDEX
        correct = (best == gold) & mask
        # Nur zur Verlaufskontrolle. Die massgebliche Bewertung laeuft
        # entitaetsweise ueber core/evaluate.py — Tokengenauigkeit ist von
        # der O-Klasse dominiert und sieht immer gut aus.
        entity = mask & (gold != 0)
        return {
            "token_accuracy": float(correct.sum() / max(1, mask.sum())),
            "entity_token_accuracy": float(
                (correct & entity).sum() / max(1, entity.sum())
            ),
        }

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.1,
        weight_decay=0.01,
        logging_steps=50,
        # Bewusst "no". Mit "epoch" schriebe jeder Lauf Zwischenstaende zu je
        # 3,5 GB — Gewichte plus Optimiererzustand —, die nichts liest:
        # `load_best_model_at_end` ist nicht gesetzt, und das fertige Modell kommt
        # aus `trainer.save_model()` weiter unten.
        save_strategy="no",
        eval_strategy="epoch" if eval_ds else "no",
        seed=args.seed,
        bf16=torch.cuda.is_available(),
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics if eval_ds else None,
    )
    trainer.train()

    out = Path(args.out)
    trainer.save_model(out)
    tokenizer.save_pretrained(out)

    # Labelvertrag zum Checkpoint legen. Wird beim Laden geprueft.
    (out / "pack.json").write_text(json.dumps({
        "pack": args.pack,
        "label_hash": pack.get_label_hash(),
        "labels": labels,
        "base_model": args.model,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nModell und Labelvertrag in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
