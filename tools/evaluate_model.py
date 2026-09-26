#!/usr/bin/env python3
"""Trainiertes Modell auswerten (SPEC §4, §11).

    python3 tools/evaluate_model.py --model runs/ch-v63b --data eval.jsonl
    python3 tools/evaluate_model.py --model runs/ch-v63b --data eval.jsonl --show 5

Misst die **Leckrate** — den gewichteten Anteil der Personendaten, die
unmaskiert ans Frontier-Modell durchgehen. Micro-F1 steht daneben, ist aber
nicht die Zielgroesse: ein Modell mit F1 0.98 kann untauglich sein, wenn die
fehlenden zwei Prozent AHV-Nummern sind.

Ausgewertet wird die VOLLE Kette: Modell plus Regex plus Pruefsummen-Override,
also das, was der Anwender tatsaechlich bekommt — nicht die nackte
Modellleistung. Mit --no-rules laesst sich der Modellanteil isolieren.

**Was diese Zahl NICHT sagt:** Der Auswertungssatz stammt aus denselben
Vorlagen wie das Training, nur mit anderem Zufallsstartwert. Er misst, ob das
Modell ueber WERTE verallgemeinert — nicht ueber Dokumentarten. Ein Dokument,
dessen Satzbau in keiner Vorlage vorkommt, ist damit nicht geprueft. Dafuer
braucht es das Dokument-Testset aus echten Unterlagen (SPEC §11).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.evaluate import evaluate, format_report  # noqa: E402
from core import user_rules  # noqa: E402
from core.inference import Scored, merge  # noqa: E402
from core.masking import Span, mask  # noqa: E402
from packs import load_pack  # noqa: E402


class TorchScorer:
    """Modell aus einem Trainingsordner. Braucht torch nur hier."""

    def __init__(self, model_dir: str, max_length: int = 512,
                 stride: int = 128):
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        self.torch = torch
        path = Path(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForTokenClassification.from_pretrained(path)
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.max_length = max_length
        self.stride = stride

        contract = path / "pack.json"
        self.labels = (
            json.loads(contract.read_text(encoding="utf-8"))["labels"]
            if contract.exists()
            else [self.model.config.id2label[i]
                  for i in range(len(self.model.config.id2label))]
        )
        self.label_hash = (
            json.loads(contract.read_text(encoding="utf-8")).get("label_hash")
            if contract.exists() else None
        )

    def check_contract(self, pack) -> None:
        if self.label_hash and self.label_hash != pack.get_label_hash():
            raise SystemExit(
                "ABBRUCH: Labelvertrag des Modells passt nicht zum Pack.\n"
                f"  Modell: {self.label_hash}\n  Pack:   {pack.get_label_hash()}\n"
                "Der Datensatz wurde mit einer anderen Taxonomie erzeugt."
            )

    def score(self, text: str) -> list[Scored]:
        from core.alignment import decode

        torch = self.torch

        # Lange Dokumente in ueberlappende Fenster schneiden.
        #
        # Mit `truncation=True` saehe das Modell alles ab Token 512 nie — und am
        # Ende einer Mail stehen die Signaturbloecke: Name, Firma, Strasse, Ort.
        # Dieselbe Fensterung wie im `OnnxScorer`: zwei Laeufer, ein Verhalten.
        #
        # `add_special_tokens=False` gilt nur fuer die OFFSETS.
        #
        #   OnnxScorer  Tokenizer.encode()       23 Token  [2, …] … […, 1]
        #   Training    hf(text) (Vorgabe)       23 Token  [2, …] … […, 1]
        #   ohne Sondertoken                     21 Token
        #
        # Ohne die Sondertoken je Fenster bekaeme das Modell eine Eingabeform, die
        # es im Training nie gesehen hat — und das kostet Lecks.
        #
        # Die Offsets bleiben ohne Sondertoken — sie haben keine Stelle im Text. Sie
        # kommen je FENSTER dazu, und die Logit-Indizes verschieben sich deshalb um
        # eins.
        cls_id = self.tokenizer.cls_token_id
        sep_id = self.tokenizer.sep_token_id
        if cls_id is None or sep_id is None:
            raise SystemExit(
                "ABBRUCH: Tokenizer ohne [CLS]/[SEP].\n"
                "  Das Modell wurde mit beiden trainiert. Ohne sie ist\n"
                "  jede Vorhersage auf einer fremden Eingabeform.")

        enc = self.tokenizer(text, return_offsets_mapping=True,
                             add_special_tokens=False)
        ids = enc["input_ids"]
        offsets = enc["offset_mapping"]

        results: dict[tuple[int, int], tuple[str, float]] = {}
        nutz = self.max_length - 2          # Platz fuer [CLS] und [SEP]
        step = max(1, nutz - self.stride)
        # ⚠️ Die Zahl der Fenster steht VOR der Rechnung fest. Das ist der
        # Grund, warum die Oberflaeche einen echten Balken zeigen kann und
        # keinen gefuehlten. `melde` bleibt None, wenn niemand zusieht —
        # auf der Kommandozeile und in den Messungen kostet das nichts.
        from core.inference import fensterzahl

        fenster = fensterzahl(len(ids), nutz, step)
        melde = getattr(self, "melde", None)
        for nr, begin in enumerate(range(0, max(1, len(ids)), step), start=1):
            if melde is not None:
                melde(nr, fenster)
            chunk_ids = ids[begin:begin + nutz]
            chunk_off = offsets[begin:begin + nutz]
            if not chunk_ids:
                break
            arr = torch.tensor([[cls_id] + chunk_ids + [sep_id]],
                               device=self.device)
            with torch.no_grad():
                logits = self.model(
                    input_ids=arr,
                    attention_mask=torch.ones_like(arr),
                ).logits[0]
            probs = torch.softmax(logits, dim=-1)
            best = probs.argmax(dim=-1).tolist()
            conf = probs.max(dim=-1).values.tolist()
            for i, (a, b) in enumerate(chunk_off):
                if b <= a:
                    continue
                j = i + 1                   # [CLS] steht davor
                # Bei Ueberlappung gewinnt die sicherere Vorhersage.
                prev = results.get((a, b))
                if prev is None or conf[j] > prev[1]:
                    results[(a, b)] = (self.labels[best[j]], conf[j])
            if begin + nutz >= len(ids):
                break

        ordered = sorted(results.items())
        offsets = [k for k, _ in ordered]
        labels = [v[0] for _, v in ordered]
        confidence = {k: v[1] for k, v in ordered}

        out: list[Scored] = []
        for span in decode(offsets, labels, text):
        # Vertrauen aus allen Token, die sich mit der Spanne UEBERSCHNEIDEN —
        # nicht nur aus den vollstaendig enthaltenen.
        #
        # SentencePiece haengt das fuehrende Leerzeichen an das Token: aus
        # " Schweiz" wird ein Token mit Offset (a, b), wobei a VOR dem
        # Entitaetsbeginn liegt. Verlangte man Enthaltensein, faende man bei einer
        # Entitaet aus genau einem Wort-Token gar kein Token, das Vertrauen waere
        # 0.0, und die Schwelle wuerfe die Entitaet weg — obwohl das Modell auf
        # Tokenebene richtig lag.
            überlappend = [
                confidence[(a, b)] for (a, b) in offsets
                if b > a and a < span.end and span.start < b
            ]
            out.append(Scored(span.tag, span.start, span.end,
                              min(überlappend) if überlappend else 0.0))
        return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--regeln", default=None,
                    help="eigene Regeln, Vorgabe ~/.config/maschera/regeln.yaml")
    ap.add_argument("--limit", type=int, default=0, help="0 = alle")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--no-rules", action="store_true",
                    help="nur das Modell, ohne Regex und Pruefsummen")
    ap.add_argument("--show", type=int, default=0,
                    help="so viele maskierte Beispiele ausgeben")
    args = ap.parse_args()

    pack = load_pack(args.pack)
    # Dieselbe Kette messen, die im Betrieb laeuft — inklusive Benutzerregeln.
    regeln = user_rules.lade(args.regeln, pack)
    if regeln:
        print(f"Eigene Regeln ({len(regeln)}): "
              + ", ".join(r.bezeichnung for r in regeln))

    rows = []
    with open(args.data, encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            if "_meta" in obj:
                if obj["_meta"].get("label_hash") not in (None, pack.get_label_hash()):
                    raise SystemExit(
                        "ABBRUCH: Labelvertrag des Datensatzes passt nicht zum Pack."
                    )
                continue
            rows.append(obj)
    if args.limit:
        rows = rows[:args.limit]

    print(f"Modell laden: {args.model}")
    scorer = TorchScorer(args.model, args.max_length)
    scorer.check_contract(pack)
    print(f"Geraet: {scorer.device}, {len(rows)} Beispiele\n")

    cases = []
    for i, row in enumerate(rows):
        if i and i % 200 == 0:
            print(f"  {i}/{len(rows)} …")
        text = row["text"]
        gold = [Span(s["tag"], s["start"], s["end"]) for s in row["spans"]]
        model_spans = scorer.score(text)
        if args.no_rules:
            thresholds = pack.get_thresholds()
            pred = [
                Span(s.tag, s.start, s.end, source="model")
                for s in model_spans
                if s.score >= thresholds.get(s.tag, 0.0)
            ]
        else:
            pred, _ = merge(text, model_spans, pack,
                        user_spans=user_rules.erkenne(text, regeln))
        cases.append((text, gold, pred))

    report = evaluate(cases, pack)
    print()
    print("Kette:", "nur Modell" if args.no_rules else "Modell + Regex + Pruefsummen")
    print(format_report(report, top=10))

    for text, gold, pred in cases[:args.show]:
        print("\n" + "-" * 68)
        print(mask(text, pred, pack).text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
