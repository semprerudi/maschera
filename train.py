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


def _lehrer_trainer(Trainer, torch):
    """Trainer mit Distillation der alten Labels (siehe --lehrer)."""
    F = torch.nn.functional

    class LehrerTrainer(Trainer):
        def __init__(self, *a, lehrer=None, n_alt=0, gewicht=1.0,
                     frei_erwartet=False, frei_labels=None, **k):
            super().__init__(*a, **k)
            self.lehrer, self.n_alt, self.gewicht = lehrer, n_alt, gewicht
            # Nur diese Label-Ids sind in freien Beispielen ohne Lehrer; None =
            # das ganze Beispiel.
            self.frei_labels = frei_labels
            self.frei_erwartet, self.frei_gesehen = frei_erwartet, 0
            self._lehrer_ort = None

        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            # 1 = fuer dieses Beispiel keine Distillation (--lehrer-frei).
            frei = inputs.pop("lehrer_frei", None)
            # Laut abbrechen statt still mit Lehrer ueberall weiterlernen.
            if self.frei_erwartet and model.training and frei is None:
                raise SystemExit("ABBRUCH: --lehrer-frei gesetzt, aber das Feld "
                                 "lehrer_frei kommt im Training nicht an")
            if frei is not None and model.training:
                self.frei_gesehen += int(frei.sum())
            out = model(**inputs)
            verlust = out.loss
            if self._lehrer_ort != out.logits.device:
                self.lehrer.to(out.logits.device)
                self._lehrer_ort = out.logits.device
            with torch.no_grad():
                t = self.lehrer(input_ids=inputs["input_ids"],
                                attention_mask=inputs["attention_mask"]).logits
            s = out.logits[..., :self.n_alt]
            kl = F.kl_div(F.log_softmax(s.float(), dim=-1),
                          F.softmax(t.float(), dim=-1),
                          reduction="none").sum(-1)
            maske = inputs["attention_mask"].float()
            if frei is not None:
                f = frei.float().to(maske.device).unsqueeze(-1).expand_as(maske)
                if self.frei_labels is not None:
                    # Nur die Token, deren Gold eines der genannten Tags ist
                    # (ch-v71d: ganz frei faerbte auf andere Dokumente ab).
                    ids = torch.tensor(self.frei_labels, device=maske.device)
                    f = f * torch.isin(inputs["labels"].to(maske.device), ids).float()
                maske = maske * (1 - f)
            kl = (kl * maske).sum() / maske.sum().clamp(min=1)
            verlust = verlust + self.gewicht * kl
            return (verlust, out) if return_outputs else verlust

    return LehrerTrainer


def _nur_neue_zeilen(model, pfad: str) -> None:
    """Alles einfrieren ausser den NEUEN Zeilen des Ausgabekopfs.

    Gewicht und Bias des Kopfs bleiben trainierbar, aber ein Haken setzt den
    Gradienten der uebernommenen Zeilen auf null. Weight decay ist fuer diesen
    Fall aus (siehe `weight_decay` unten), sonst schrumpften sie trotzdem.
    """
    alt = len(json.loads((Path(pfad) / "pack.json").read_text(
        encoding="utf-8"))["labels"])
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("classifier.")

    def maske(grad):
        grad = grad.clone()
        grad[:alt] = 0
        return grad
    model.classifier.weight.register_hook(maske)
    if model.classifier.bias is not None:
        model.classifier.bias.register_hook(maske)
    n = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Nur Kopf:   {alt} alte Zeilen eingefroren, {n} Parameter "
          "trainierbar (davon wirksam nur die neuen Zeilen)")


def _von_modell(pfad: str, labels: list[str], Auto, torch):
    """Ein fertiges Modell laden und seinen Ausgabekopf auf `labels` erweitern.

    Bricht ab, wenn die alten Labels kein Praefix der neuen sind: dann waeren
    Indizes verschoben, und das alte Wissen laege unter falschen Labels.
    """
    alt = json.loads((Path(pfad) / "pack.json").read_text(encoding="utf-8"))
    alte = list(alt["labels"])
    if labels[:len(alte)] != alte:
        raise SystemExit(
            f"ABBRUCH: die {len(alte)} Labels von {pfad} sind kein Praefix des "
            "heutigen Vertrags. Weitertrainieren geht nur bei angehaengten Tags.")
    model = Auto.from_pretrained(pfad)
    kopf = model.classifier
    neu = torch.nn.Linear(kopf.in_features, len(labels),
                          bias=kopf.bias is not None)
    with torch.no_grad():
        neu.weight[:len(alte)] = kopf.weight
        if kopf.bias is not None:
            neu.bias[:len(alte)] = kopf.bias
            # Neue Labels starten mit dem kleinsten alten Bias: sie sollen
            # nicht vom ersten Schritt an Tokens an sich ziehen.
            neu.bias[len(alte):] = kopf.bias.min()
    model.classifier = neu
    model.num_labels = len(labels)
    model.config.num_labels = len(labels)
    model.config.id2label = {i: l for i, l in enumerate(labels)}
    model.config.label2id = {l: i for i, l in enumerate(labels)}
    print(f"Start von:  {pfad} ({len(alte)} Labels uebernommen, "
          f"{len(labels) - len(alte)} neu)")
    return model


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
    # Seit 25.11.2026: von einem fertigen Modell aus weitertrainieren statt vom
    # Basismodell. Gedacht fuer einen ANGEHAENGTEN Labelvertrag: die Labels des
    # alten Modells muessen ein Praefix der neuen sein (die Taxonomie verlangt
    # Anhaengen). Ihre Zeilen im Ausgabekopf werden exakt uebernommen, die
    # neuen zufaellig angelegt. Anlass: frische Laeufe ab mmBERT-base erreichten
    # die Leckzahl von ch-v63b nicht (7 bis 12 statt 6, auch ohne neues Tag).
    ap.add_argument("--start-von", default=None, metavar="MODELL",
                    help="fertiges Modell mit Praefix-Labelvertrag als Start")
    # Mit --start-von: Rumpf und die uebernommenen Zeilen des Ausgabekopfs
    # einfrieren, nur die neuen Labels lernen. Die Werte der alten Labels
    # bleiben dann genau die des Startmodells. Anlass 25.11.2026: auch eine
    # Epoche mit kleiner Lernrate verschob ch-v63b (8 statt 6 Lecks).
    # Mit --start-von: ganzes Modell trainieren, aber die alten Labels per
    # Distillation an ein Lehrermodell binden (KL zwischen den Softmax-
    # Verteilungen ueber die alten Labels, Token fuer Token). Der Rumpf lernt
    # die neuen Tags, ohne zu vergessen, was der Lehrer bei den alten konnte.
    # Anlass 25.11.2026: --nur-kopf lernte JOBTITLE nur mit Precision 0.36,
    # weil die eingefrorenen Merkmale Berufe nicht von anderen Nomen trennen.
    ap.add_argument("--lehrer", default=None, metavar="MODELL",
                    help="Lehrer fuer die alten Labels (meist = --start-von)")
    ap.add_argument("--lehrer-gewicht", type=float, default=1.0)
    # Seit 25.11.2026 (Feedback Test 2): Beispiele aus Vorlagen, deren Kennung
    # dieses Stueck enthaelt, lernen die ALTEN Labels frei, ohne Lehrer. So
    # duerfen Namen in Protokollkoepfen von ORG zu FULLNAME umlernen, waehrend
    # der Lehrer ueberall sonst das alte Verhalten festhaelt (mit schwachem
    # Lehrer kamen im echten Testset neue Lecks).
    ap.add_argument("--lehrer-frei", default=None, metavar="MUSTER",
                    help="Vorlagenkennungen mit diesem Stueck ohne Lehrer")
    ap.add_argument("--lehrer-frei-tags", default=None, metavar="TAGS",
                    help="nur Token dieser Tags (z. B. GIVENNAME,FULLNAME) ohne Lehrer")
    ap.add_argument("--nur-kopf", action="store_true",
                    help="nur die neuen Zeilen des Ausgabekopfs trainieren")
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
        def __init__(self, encoded, label_ids, keep, frei=None):
            self.encoded, self.labels, self.keep = encoded, label_ids, keep
            self.frei = frei

        def __len__(self):
            return len(self.keep)

        def __getitem__(self, i):
            j = self.keep[i]
            return {
                "input_ids": self.encoded["input_ids"][j],
                "attention_mask": self.encoded["attention_mask"][j],
                "labels": self.labels[i],
                **({"lehrer_frei": self.frei[j]} if self.frei is not None else {}),
            }

    frei = None
    if args.lehrer_frei:
        frei = [int(args.lehrer_frei in str(r.get("template", ""))) for r in rows]
        print(f"Lehrer frei: {sum(frei)} Beispiele mit '{args.lehrer_frei}'")
    train_ds = TokenDataset(enc, lab, keep, frei)

    eval_ds = None
    if args.eval_data:
        print("Auswertungsdaten:")
        erows, emeta = load_dataset(Path(args.eval_data))
        check_contract(emeta, pack)
        eenc, elab, ekeep = build_features(erows, tokenizer, labels,
                                           args.max_length)
        eval_ds = TokenDataset(eenc, elab, ekeep)

    if args.nur_kopf and not args.start_von:
        raise SystemExit("--nur-kopf geht nur zusammen mit --start-von")
    if args.start_von:
        model = _von_modell(args.start_von, labels,
                            AutoModelForTokenClassification, torch)
        if args.nur_kopf:
            _nur_neue_zeilen(model, args.start_von)
    else:
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

    # Aufwaermen ueber 10 % der Schritte. transformers 5 kennt `warmup_ratio`
    # nicht mehr und nimmt den Bruchteil in `warmup_steps` (eine Zahl unter 1
    # gilt als Anteil). Bemerkt am 24.11.2026 beim ersten Training seit 4.x.
    import inspect
    if "warmup_ratio" in inspect.signature(TrainingArguments).parameters:
        aufwaermen = {"warmup_ratio": 0.1}
    else:
        aufwaermen = {"warmup_steps": 0.1}

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        **aufwaermen,
        weight_decay=0.01 if not args.nur_kopf else 0.0,
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
        # ⚠️ Mit `True` (Vorgabe) wirft der Trainer bei einem eigenen Datensatz
        # jedes Feld weg, das `model.forward` nicht kennt, OHNE Meldung. So kam
        # `lehrer_frei` nie an, und ch-v71c (25.11.2026) trainierte mit Lehrer
        # ueberall. Die Datensatzklasse liefert ohnehin nur, was gebraucht wird.
        remove_unused_columns=False,
    )

    Klasse = Trainer
    extra = {}
    if args.lehrer:
        if not args.start_von or args.nur_kopf:
            raise SystemExit("--lehrer braucht --start-von und geht nicht "
                             "mit --nur-kopf")
        Klasse = _lehrer_trainer(Trainer, torch)
        lehrer = AutoModelForTokenClassification.from_pretrained(
            args.lehrer, use_safetensors=True)
        lehrer.eval()
        for q in lehrer.parameters():
            q.requires_grad = False
        n_alt = lehrer.config.num_labels
        if labels[:n_alt] != [lehrer.config.id2label[i] for i in range(n_alt)]:
            raise SystemExit("ABBRUCH: die Labels des Lehrers sind kein "
                             "Praefix des heutigen Vertrags")
        extra = {"lehrer": lehrer, "n_alt": n_alt,
                 "gewicht": args.lehrer_gewicht,
                 "frei_erwartet": bool(args.lehrer_frei),
                 "frei_labels": ([i for i, l in enumerate(labels) if l != "O"
                                  and l.split("-", 1)[1] in args.lehrer_frei_tags.split(",")]
                                 if args.lehrer_frei_tags else None)}
        if extra["frei_labels"] is not None:
            print(f"Lehrer frei nur fuer: {args.lehrer_frei_tags} "
                  f"({len(extra['frei_labels'])} Labels)")
        print(f"Lehrer:     {args.lehrer} ({n_alt} Labels, Gewicht "
              f"{args.lehrer_gewicht})")

    trainer = Klasse(
        **extra,
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics if eval_ds else None,
    )
    trainer.train()
    if extra.get("frei_erwartet"):
        print(f"Lehrer frei: {trainer.frei_gesehen} Beispiele ohne Lehrer gesehen")
        if not trainer.frei_gesehen:
            raise SystemExit("ABBRUCH: kein Beispiel ohne Lehrer gesehen")

    out = Path(args.out)
    trainer.save_model(out)
    tokenizer.save_pretrained(out)

    # Labelvertrag zum Checkpoint legen. Wird beim Laden geprueft.
    vertrag = {
        "pack": args.pack,
        "label_hash": pack.get_label_hash(),
        "labels": labels,
        "base_model": args.start_von or args.model,
    }
    if args.nur_kopf or args.lehrer:
        # Die Laeufer entscheiden die alten Labels dann getrennt von den neuen
        # (`core.inference.kopf_paesse`). Mit --nur-kopf verhalten sich die
        # alten Tags genau wie im Startmodell, mit --lehrer annaehernd (die
        # Distillation haelt sie fest, ohne sie einzufrieren).
        vertrag["kopf_alt"] = len(json.loads(
            (Path(args.start_von) / "pack.json").read_text(
                encoding="utf-8"))["labels"])
    (out / "pack.json").write_text(json.dumps(
        vertrag, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nModell und Labelvertrag in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
