#!/usr/bin/env python3
"""Vom trainierten Checkpoint zum auslieferbaren CPU-Modell (SPEC §12).

    python3 tools/build_release.py --checkpoint runs/ch-v63b --out release/ch-v63b --no-trim --verify

Drei Schritte:

  1. VOKABULAR BESCHNEIDEN  — ZURZEIT GESPERRT, `--no-trim` ist Pflicht.
     `kept_token_ids` landet in `pack.json` und wird von NIEMANDEM gelesen.
     Ohne Umbildung in `OnnxScorer` entstuende ein Modell, das laeuft und
     falsch liegt. Siehe die Sperre in `main()`.
     mmBERT nutzt den Gemma-2-Tokenizer mit 256'000 Token fuer 1833 Sprachen.
     Der Pack deckt vier ab; die Embedding-Matrix ist 64-70 % des Modells.
     Ein beschnittenes Vokabular machte einen Namen in fremder Schrift
     still unmaskierbar.

  2. NACH ONNX EXPORTIEREN
     Damit braucht der Anwender kein torch. onnxruntime + tokenizers sind
     zusammen ~60 MB statt ~2 GB.

  3. INT8-QUANTISIERUNG (dynamisch)
     Nochmals Faktor 4 kleiner und auf CPU schneller. Dynamisch, nicht
     statisch: kein Kalibrierdatensatz noetig. WIRD GEMESSEN, nicht
     angenommen — `--verify` laesst torch fp32, ONNX fp32 und ONNX int8
     gegen dieselben Haltezone-Dokumente laufen und stellt Micro-F1, Lecks
     und Uebermaskierungen nebeneinander.

Ergebnis in `out/`:
    model.onnx        INT8-quantisiert
    tokenizer.json
    pack.json         Labelvertrag, Hash, Basismodell
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from packs import load_pack  # noqa: E402


def _groesse(pfad: Path) -> int:
    """Groesse eines ONNX-Modells MITSAMT externer Gewichte.

    `stat().st_size` allein misst nur den Graphen und meldete fuer ein
    681-MB-Modell «0 MB».
    """
    return sum(x.stat().st_size for x in pfad.parent.glob(pfad.name + "*"))


def collect_used_tokens(tokenizer, texts, extra_words, keep_top=8000):
    """Alle Token-IDs, die tatsaechlich gebraucht werden."""
    used = set()
    for t in texts:
        used.update(tokenizer(t)["input_ids"])
    for w in extra_words:
        for variant in (w, " " + w, w.lower(), w.upper()):
            used.update(tokenizer(variant, add_special_tokens=False)["input_ids"])
    # Sonderzeichen und die haeufigsten Token als Puffer: unbekannte Eingaben
    # sollen nicht komplett auf [UNK] fallen.
    used.update(tokenizer.all_special_ids)
    used.update(range(keep_top))
    return sorted(used)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--out", default="release/ch")
    ap.add_argument("--data", default=None,
                    help="dataset.jsonl, bestimmt das beschnittene Vokabular")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--no-trim", action="store_true")
    ap.add_argument("--no-quantize", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="Genauigkeit vor/nach Quantisierung vergleichen")
    ap.add_argument("--verify-n", type=int, default=200,
                    help="Dokumente fuer --verify (Vorgabe 200)")
    a = ap.parse_args()

    try:
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            f"{exc}\n\nAuf der Trainingsmaschine:\n"
            "  pip install torch transformers onnx onnxruntime "
            "optimum[onnxruntime] --break-system-packages"
        )

    pack = load_pack(a.pack)
    ckpt, out = Path(a.checkpoint), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(ckpt)
    model = AutoModelForTokenClassification.from_pretrained(ckpt)
    before = sum(p.numel() for p in model.parameters())
    print(f"Checkpoint: {before/1e6:.0f}M Parameter, "
          f"Vokabular {model.config.vocab_size}")

    # Das Beschneiden ist gesperrt, bis `OnnxScorer` umbildet.
    #
    # `pack.json` traegt `kept_token_ids`, und NICHTS liest sie. Der
    # mitgelieferte Tokenizer hat 256 000 Eintraege, die beschnittene
    # Einbettungsmatrix rund 77 000 Zeilen. Weil `range(keep_top)` mitgenommen
    # wird, stimmen die IDs unter 8000 zufaellig — darueber zeigt jede Zerlegung
    # auf die falsche Zeile.
    #
    # Das Ergebnis waere kein Absturz, sondern ein Modell, das laeuft und
    # falsch liegt. Deshalb ABBRUCH statt Warnung.
    if not a.no_trim:
        raise SystemExit(
            "ABBRUCH: --no-trim ist zurzeit Pflicht.\n"
            "  Das beschnittene Vokabular braucht eine Umbildung der\n"
            "  Token-IDs in core/inference.py (OnnxScorer). Die gibt es\n"
            "  nicht — `kept_token_ids` wird geschrieben und nie gelesen.\n"
            "  Ohne sie entsteht ein Modell, das laeuft und falsch liegt.")

    kept_ids = None
    if False:
        texts = []
        if a.data:
            with open(a.data, encoding="utf-8") as fh:
                for line in fh:
                    o = json.loads(line)
                    if "text" in o:
                        texts.append(o["text"])
        words = []
        # Nicht glob("*.json") — `_fingerabdruck.json` hat kein `entries`. Die
        # Konvention steht in `nomenklaturdateien()`.
        from packs.ch.nomenclatures.build import nomenklaturdateien
        dist = (Path(__file__).resolve().parent.parent
                / f"packs/{a.pack}/nomenclatures/dist")
        for datei in nomenklaturdateien(dist):
            for e in json.loads(datei.read_text(encoding="utf-8"))["entries"]:
                words.append(e["name"] if isinstance(e, dict) else e)
        print(f"  Vokabularbasis: {len(texts)} Texte, {len(words)} Nomenklatureintraege")
        kept_ids = collect_used_tokens(tokenizer, texts, words)
        print(f"  behalten: {len(kept_ids)} von {model.config.vocab_size} Token")

        emb = model.get_input_embeddings().weight.data
        model.resize_token_embeddings(len(kept_ids))
        model.get_input_embeddings().weight.data.copy_(emb[kept_ids])
        after = sum(p.numel() for p in model.parameters())
        print(f"  {before/1e6:.0f}M -> {after/1e6:.0f}M Parameter "
              f"({100*(1-after/before):.0f} % kleiner)")

    onnx_path = out / "model.onnx"
    # Das Ziel steht VOR dem Export fest und wird nie umbenannt.
    #
    # Der torch-Exporter legt die Gewichte EXTERN ab: neben `x.onnx` entsteht
    # `x.onnx.data`, und der Verweis darauf steckt als Zeichenkette IM Graphen.
    # Ein `rename()` der .onnx-Datei bricht ihn, ohne dass etwas meldet, und
    # laesst die .data-Datei als Waise zurueck.
    fp32_path = out / "model.fp32.onnx"
    ziel = fp32_path if not a.no_quantize else onnx_path
    print(f"\nONNX-Export -> {ziel}")
    model.eval()
    dummy = torch.ones(1, 16, dtype=torch.long)
    # opset 18, nicht 17.
    #
    # Der Exporter kann nur >= 18 und warnt selbst, die Rueckumwandlung koenne
    # scheitern. Sie scheitert: mit 17 entsteht ein Split-Knoten mit dem
    # Attribut `num_outputs` aus opset 18, und onnxruntime weist den Graphen ab
    # — `InvalidGraph`.
    torch.onnx.export(
        model, (dummy, torch.ones_like(dummy)), str(ziel),
        input_names=["input_ids", "attention_mask"], output_names=["logits"],
        dynamic_axes={k: {0: "batch", 1: "seq"} for k in
                      ("input_ids", "attention_mask", "logits")},
        opset_version=18,
    )
    print(f"  fp32: {_groesse(ziel)/1e6:.0f} MB")

    if not a.no_quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic
        vorher = _groesse(fp32_path)
        quantize_dynamic(str(fp32_path), str(onnx_path),
                         weight_type=QuantType.QInt8)
        print(f"  INT8: {_groesse(onnx_path)/1e6:.0f} MB "
              f"(vorher {vorher/1e6:.0f} MB)")

    tokenizer.save_pretrained(out)
    (out / "pack.json").write_text(json.dumps({
        "pack": a.pack,
        "label_hash": pack.get_label_hash(),
        "labels": list(pack.get_labels()),
        "trimmed_vocab": kept_ids is not None,
        "vocab_size": len(kept_ids) if kept_ids else model.config.vocab_size,
        "kept_token_ids": kept_ids,
    }, ensure_ascii=False), encoding="utf-8")

    if a.verify:
        # Gemessen wird die KETTE, nicht die Logits: dieselben Faelle, dieselbe
        # Rechnung wie `mess_synthetisch.py` und `eval_documents.py`. Eine dritte
        # Zahl aus einem dritten Testset waere nicht vergleichbar.
        from core import user_rules, vorlieben
        from core.evaluate import evaluate
        from core.inference import OnnxScorer
        from evaluate_model import TorchScorer
        from mess_synthetisch import baue_faelle

        print(f"\n--verify: torch gegen INT8, {a.verify_n} Dokumente "
              "aus der Haltezone")
        regeln = user_rules.lade(None, pack)
        ohne = vorlieben.lade()
        zeilen = []
        # DREI Punkte, nicht zwei.
        #
        # torch fp32 direkt gegen ONNX int8 misst zwei Unterschiede auf einmal: die
        # Zahlendarstellung UND zwei getrennte Laeufer mit eigener Fensterung und
        # eigener Rueckbildung von Subwort auf Zeichen. Die quantisierte Fassung
        # kann dabei sogar besser herauskommen — was Quantisierung nicht leisten
        # kann.
        #
        #   torch fp32  ->  ONNX fp32   isoliert Export und Laeufer
        #   ONNX fp32   ->  ONNX int8   isoliert die Quantisierung
        punkte = [("torch fp32", TorchScorer(str(ckpt), 512))]
        if fp32_path.is_file():
            punkte.append(("ONNX fp32", OnnxScorer(str(out), 512,
                                                   datei=fp32_path.name)))
        punkte.append(("ONNX int8", OnnxScorer(str(out), 512)))
        for name, scorer in punkte:
            scorer.check_contract(pack)
            faelle, _ = baue_faelle(scorer, pack, n=a.verify_n,
                                    regeln=regeln)
            r = evaluate(faelle, pack, excluded=ohne)
            gold = sum(s.gold for s in r.per_tag.values())
            zeilen.append((name, r.micro_f1, len(r.leaked), len(r.over),
                           gold))

        print(f"\n  {'':<14}{'Micro-F1':>10}{'Lecks':>8}"
              f"{'Uebermask':>11}")
        for name, f1, lecks, over, gold in zeilen:
            print(f"  {name:<14}{f1:>10.4f}{lecks:>8}{over:>11}")
        for a_, b_ in zip(zeilen, zeilen[1:]):
            print(f"  {'  ' + a_[0] + ' -> ' + b_[0]:<14}"
                  f"{b_[1] - a_[1]:>+10.4f}{b_[2] - a_[2]:>+8}"
                  f"{b_[3] - a_[3]:>+11}")
        print(f"\n  {zeilen[0][4]} Goldspannen. "
              "Mehr Lecks nach der Quantisierung sind ein Rueckschritt,\n"
              "  mehr Uebermaskierungen sind es nicht — "
              "ein unterdruecktes Datum\n  ist billiger als eines zuviel.")

    # Die fp32-Fassung samt externer Gewichte raeumen — sonst blieben
    # Hunderte MB Waisen im Ausgabeverzeichnis.
    for teil in sorted(out.glob("model.fp32.onnx*")):
        teil.unlink()

    print(f"\nFertig: {out}")
    print("Anwenderseitig genuegt:  pip install onnxruntime tokenizers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
