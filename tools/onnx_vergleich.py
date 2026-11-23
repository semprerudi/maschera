#!/usr/bin/env python3
"""torch gegen ONNX: rohe Logits und Vertrauenswerte an den Schwellen.

    python3 tools/onnx_vergleich.py --torch runs/ch-v63b \\
        --onnx release/ch-v63b-fp32 [--onnx release/ch-v63b] [--streng]

Warum es das braucht (23.11.2026): Das Mac-Paket fuer Intel rechnet mit
onnxruntime statt torch, weil es fuer x86_64 kein aktuelles torch mehr gibt.
Dieselben Gewichte sollen dasselbe Ergebnis geben. `build_release.py --verify`
misst die ganze Kette; hier steht, WIE NAH die beiden Laeufer beieinander
liegen, und vor allem: ob ein Vertrauenswert ueber oder unter seine Schwelle
kippt. Nur das aendert, was maskiert wird.

Gemessen auf erfundenen Texten in de/fr/it/en, kurz und lang (mehrere
Fenster), nie auf Golddaten. Der Workflow ruft es nach dem Export mit
`--streng` auf: dann ist jeder Kipper und jede fehlende Spanne ein Abbruch.

Kennzahlen:
  Logits   groesste absolute Differenz, Anteil Token mit anderem argmax
  Spannen  gleiche (Tag, Anfang, Ende), nur auf einer Seite, groesste
           Differenz im Vertrauenswert
  Kipper   Spannen, die auf der einen Seite die Schwelle ihres Tags
           erreichen und auf der anderen nicht
  Knapp    Spannen, deren Wert weniger als 0,05 von der Schwelle liegt
           (ORG mit 0,90 eingeschlossen) — sie kippen zuerst
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

# Erfunden. Namen, Nummern und Adressen gibt es so nicht; die AHV-Nummer ist
# die bekannte Beispielnummer mit gueltiger Pruefziffer.
TEXTE = {
    "de": ("Sehr geehrte Frau Petra Muster-Brunner\n"
           "Wir bestätigen Ihren Termin vom 12. März 2026 an der Bahnhofstrasse 14 "
           "in 4600 Olten. Ihre AHV-Nummer lautet 756.1234.5678.97, Ihre Telefonnummer "
           "+41 62 555 01 23. Bei Fragen wenden Sie sich an Daniel Fiktiv, "
           "Sozialversicherungsanstalt Kanton Solothurn, daniel.fiktiv@example.ch.\n"
           "Freundliche Grüsse\n"),
    "fr": ("Madame Chiara Rossi-Probe\n"
           "Nous confirmons votre rendez-vous du 3 avril 2026 à la rue du Lac 3, "
           "1950 Sion. Votre numéro AVS est 756.1234.5678.97. Pour toute question, "
           "contactez Luc Exemple, Office cantonal des assurances, au 027 555 44 33.\n"),
    "it": ("Gentile signor Marco Esempio\n"
           "Confermiamo l'appuntamento del 7 maggio 2026 in via Nassa 21, 6900 Lugano. "
           "Il suo numero AVS è 756.1234.5678.97. Per domande si rivolga a Anna Prova, "
           "Ufficio delle assicurazioni sociali, telefono 091 555 22 11.\n"),
    "en": ("Dear Mr Reto Sample\n"
           "We confirm your appointment on 21 June 2026 at Seestrasse 8, 8002 Zurich. "
           "Your AHV number is 756.1234.5678.97. If you have questions, contact "
           "Lea Placeholder at the Cantonal Office, lea.placeholder@example.org.\n"),
}


def texte() -> list[tuple[str, str]]:
    """Jede Sprache einmal kurz und einmal lang (rund 3000 Token, mehrere Fenster)."""
    aus = []
    for spr, t in TEXTE.items():
        aus.append((f"{spr}-kurz", t))
        aus.append((f"{spr}-lang", "\n".join(t for _ in range(18))))
    return aus


def logits_vergleich(torch_dir: str, onnx_dir: str, max_length: int) -> tuple[float, float, int]:
    """Rohe Logits fuer dieselben Token-IDs; je Text das erste Fenster."""
    import numpy as np
    import onnxruntime as ort
    import torch
    from tokenizers import Tokenizer
    from transformers import AutoModelForTokenClassification

    tok = Tokenizer.from_file(str(Path(onnx_dir) / "tokenizer.json"))
    tok.no_truncation()
    modell = AutoModelForTokenClassification.from_pretrained(
        torch_dir, use_safetensors=True)
    modell.eval()
    opt = ort.SessionOptions()
    sitzung = ort.InferenceSession(str(Path(onnx_dir) / "model.onnx"), opt,
                                   providers=["CPUExecutionProvider"])
    groesste, anders, gesamt = 0.0, 0, 0
    for _, t in texte():
        ids = tok.encode(t).ids[:max_length]
        x = np.array([ids], dtype=np.int64)
        m = np.ones_like(x)
        with torch.no_grad():
            a = modell(input_ids=torch.from_numpy(x),
                       attention_mask=torch.from_numpy(m)).logits.numpy()[0]
        b = sitzung.run(["logits"], {"input_ids": x, "attention_mask": m})[0][0]
        groesste = max(groesste, float(np.abs(a - b).max()))
        anders += int((a.argmax(-1) != b.argmax(-1)).sum())
        gesamt += len(ids)
    return groesste, anders / max(gesamt, 1), gesamt


def spannen_vergleich(torch_dir: str, onnx_dir: str, max_length: int) -> dict:
    from core.inference import OnnxScorer
    from evaluate_model import TorchScorer
    from packs import load_pack

    pack = load_pack("ch")
    schwellen = pack.get_thresholds()
    links = TorchScorer(torch_dir, max_length)
    rechts = OnnxScorer(onnx_dir, max_length)
    for s in (links, rechts):
        s.check_contract(pack)
    gleich = nur_links = nur_rechts = 0
    groesste = 0.0
    kipper, knapp = [], []
    for name, t in texte():
        a = {(s.tag, s.start, s.end): s.score for s in links.score(t)}
        b = {(s.tag, s.start, s.end): s.score for s in rechts.score(t)}
        for k in a.keys() | b.keys():
            thr = schwellen.get(k[0])
            if k in a and k in b:
                gleich += 1
                groesste = max(groesste, abs(a[k] - b[k]))
                if thr is not None:
                    if (a[k] >= thr) != (b[k] >= thr):
                        kipper.append((name, k[0], a[k], b[k], thr))
                    elif min(abs(a[k] - thr), abs(b[k] - thr)) < 0.05:
                        knapp.append((name, k[0], a[k], b[k], thr))
            elif k in a:
                nur_links += 1
                if thr is None or a[k] >= thr:
                    kipper.append((name, k[0], a[k], None, thr))
            else:
                nur_rechts += 1
                if thr is None or b[k] >= thr:
                    kipper.append((name, k[0], None, b[k], thr))
    return {"gleich": gleich, "nur_torch": nur_links, "nur_onnx": nur_rechts,
            "groesste": groesste, "kipper": kipper, "knapp": knapp}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--torch", required=True)
    ap.add_argument("--onnx", action="append", required=True)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--streng", action="store_true",
                    help="jeder Kipper und jede einseitige Spanne ist ein Abbruch")
    a = ap.parse_args()
    fehler = 0
    for onnx_dir in a.onnx:
        print(f"\n== torch {a.torch}  gegen  ONNX {onnx_dir}")
        g, anteil, n = logits_vergleich(a.torch, onnx_dir, a.max_length)
        print(f"   Logits: groesste Differenz {g:.2e}, anderes argmax "
              f"{100 * anteil:.3f} % von {n} Token")
        r = spannen_vergleich(a.torch, onnx_dir, a.max_length)
        print(f"   Spannen: {r['gleich']} gleich, {r['nur_torch']} nur torch, "
              f"{r['nur_onnx']} nur ONNX, groesste Wertdifferenz {r['groesste']:.2e}")
        print(f"   Kipper an der Schwelle: {len(r['kipper'])}")
        for name, tag, x, y, thr in r["kipper"]:
            print(f"      {name:<9} {tag:<14} torch {x}  ONNX {y}  Schwelle {thr}")
        print(f"   Knapp an der Schwelle (< 0,05): {len(r['knapp'])}")
        for name, tag, x, y, thr in r["knapp"]:
            print(f"      {name:<9} {tag:<14} torch {x:.4f}  ONNX {y:.4f}  "
                  f"Schwelle {thr}  Differenz {abs(x - y):.2e}")
        if a.streng and (r["kipper"] or r["nur_torch"] or r["nur_onnx"]):
            fehler += 1
    if a.streng:
        print("\nOK   keine Abweichung, die etwas an der Maskierung aendert"
              if not fehler else "\nABBRUCH: ONNX weicht ab")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
