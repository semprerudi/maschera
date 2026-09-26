"""Lange Dokumente: das Modell muss den SCHLUSS sehen, nicht nur den Kopf.

    python3 tests/test_langes_dokument.py

`release/*/tokenizer.json` traegt aus dem Training
`truncation: {max_length: 512}`. Ruft ein Laeufer
`tokenizer.encode(text)` ohne die Abschneidung abzuschalten, schneidet
der Tokenizer auf 512 Token ab, BEVOR die Fensterschleife anfaengt — die
Schleife ist dann toter Code. Das Ergebnis: der Kopf eines langen
Dokuments sauber maskiert, und ab etwa der Haelfte stehen alle Namen,
Firmen und Orte im Klartext. Was weiter funktioniert, sind nur die
Stufe-2-Treffer (URL, Datum, Postleitzahl).

    14 000 Zeichen -> 512 Token   (abgeschnitten)
    ohne Abschneidung -> 3603 Token

⚠️ Es gibt ZWEI Laeufer — torch fuer Messungen, ONNX beim Anwender —,
und beide muessen es koennen. Eine Pruefung nur ueber torch saehe den
Weg nicht, den der Anwender geht.

⚠️ Ein Testset aus kurzen Golddokumenten (unter 512 Token) kann diesen
Fehler STRUKTURELL nicht sehen. Diese Pruefung stellt den Fall deshalb
selbst her — sie baut ein Dokument, das lang genug ist.
"""
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

failures: list[str] = []
uebersprungen: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


# Ein Dokument, das sicher ueber mehrere Fenster geht. Der Name steht drei
# Mal: am Anfang, in der Mitte und GANZ AM SCHLUSS — der letzte ist der,
# der bei Abschneidung verlorengeht, und bei einer Mail steht dort die
# Signatur.
FUELL = ("Der Standort ueberzeugt durch seine zentrale Lage und "
         "hervorragende Verkehrsanbindung sowie eine moderne "
         "Lernumgebung, die Zusammenarbeit und Innovation foerdert. ")
NAME = "Mathias Ramseyer und Toni La Rosa haben reagiert."
TEXT = NAME + " " + FUELL * 10 + " " + NAME + " " + FUELL * 40 + " " + NAME
STELLEN = [0, TEXT.index(NAME, 100), TEXT.rindex(NAME)]

MODELL = WURZEL / "release" / "ch-v63b"
TRAINING = WURZEL / "runs" / "ch-v63b"


print("1. Der Quelltext schaltet die Abschneidung ab")
# ⚠️ Diese Pruefung braucht KEIN Modell und laeuft deshalb auf jeder
# Maschine. Sie haette den Fehler gefangen: `no_truncation()` fehlte.
QUELLE = (WURZEL / "core" / "inference.py").read_text(encoding="utf-8")
anfang = QUELLE.index("class OnnxScorer")
klasse = QUELLE[anfang:]

check("self.tokenizer.no_truncation()" in klasse,
      "OnnxScorer schaltet die Abschneidung des Tokenizers nicht ab — "
      "alles ab Token 512 sieht das Modell nie")
check(re.search(r"encode\(\s*text\s*,\s*add_special_tokens=False",
                klasse) is not None,
      "OnnxScorer holt die Offsets MIT Sondertoken — dann zeigen sie auf "
      "Stellen, die es im Text nicht gibt")
check("[self.cls_id]" in klasse and "[self.sep_id]" in klasse,
      "OnnxScorer setzt die Sondertoken nicht je FENSTER. Werden sie "
      "einmal fuer den ganzen Text gesetzt und danach geschnitten, "
      "bekommt jedes Fenster ausser dem ersten eine Eingabeform, die das "
      "Modell im Training nie gesehen hat")
if not failures:
    print("   OK   no_truncation, Offsets ohne Sondertoken, cls/sep je Fenster")


print("\n2. Der Tokenizer schneidet den Text nicht mehr ab")
if not (MODELL / "tokenizer.json").is_file():
    uebersprungen.append(f"{MODELL}/tokenizer.json fehlt")
    print(f"   ⚠ NICHT GELAUFEN — {MODELL}/tokenizer.json fehlt.")
else:
    from tokenizers import Tokenizer
    roh = Tokenizer.from_file(str(MODELL / "tokenizer.json"))
    # Ohne Zutun schneidet er ab — das ist die Vorgabe aus dem Training,
    # und genau deshalb muss OnnxScorer sie ausdruecklich abschalten.
    vorher = len(roh.encode(TEXT).ids)
    from core.inference import OnnxScorer
    if not (MODELL / "model.onnx").is_file():
        uebersprungen.append(f"{MODELL}/model.onnx fehlt")
        print(f"   ⚠ TEILWEISE — {MODELL}/model.onnx fehlt, "
              f"nur der rohe Tokenizer geprueft ({vorher} Token).")
    else:
        s = OnnxScorer(str(MODELL))
        nachher = len(s.tokenizer.encode(TEXT).ids)
        check(nachher > 512,
              f"der Tokenizer liefert {nachher} Token — abgeschnitten")
        check(nachher > vorher,
              f"roh {vorher}, im Scorer {nachher} — no_truncation wirkt nicht")
        print(f"   OK   roh {vorher} Token, im Scorer {nachher}")


print("\n3. Ein Name am SCHLUSS wird gefunden")
if not (MODELL / "model.onnx").is_file():
    uebersprungen.append(f"{MODELL}/model.onnx fehlt")
    print(f"   ⚠ NICHT GELAUFEN — {MODELL}/model.onnx fehlt.")
else:
    from core.inference import OnnxScorer
    s = OnnxScorer(str(MODELL))
    spannen = [x for x in s.score(TEXT)
               if x.tag in ("FULLNAME", "GIVENNAME")]
    getroffen = [p for p in STELLEN
                 if any(p <= x.start < p + len(NAME) for x in spannen)]
    check(STELLEN[-1] in getroffen,
          f"das Vorkommen bei Zeichen {STELLEN[-1]} wurde NICHT gefunden — "
          f"getroffen: {getroffen}. Genau hier steht bei einer Mail die "
          f"Signatur")
    check(len(getroffen) == 3,
          f"nur {len(getroffen)} von 3 Vorkommen gefunden")
    if not failures:
        print(f"   OK   3 von 3 Vorkommen, {len(spannen)} Namensspannen")


print("\n4. Beide Laeufer sehen dasselbe")
# ⚠️ «Zwei Laeufer, zwei Verhalten» ist in diesem Projekt dreimal
# aufgetreten: die Fensterung (3.8.), die Sondertoken (27.8.) und die
# Abschneidung (29.8.). Jedes Mal war der eine Weg gemessen und der andere
# ausgeliefert. Diese Pruefung vergleicht sie direkt.
if not (TRAINING / "model.safetensors").is_file():
    uebersprungen.append(f"{TRAINING} fehlt")
    print(f"   ⚠ NICHT GELAUFEN — {TRAINING} fehlt (nur Entwicklung).")
elif not (MODELL / "model.onnx").is_file():
    print("   ⚠ NICHT GELAUFEN — ohne ONNX kein Vergleich.")
else:
    try:
        from core.inference import OnnxScorer
        from evaluate_model import TorchScorer
        a = {(x.tag, x.start, x.end)
             for x in OnnxScorer(str(MODELL)).score(TEXT)}
        b = {(x.tag, x.start, x.end)
             for x in TorchScorer(str(TRAINING)).score(TEXT)}
        # Nicht Gleichheit verlangen: int8 gegen fp32 darf sich an
        # Grenzfaellen unterscheiden. Verlangt wird, dass keiner der
        # beiden am SCHLUSS blind ist.
        for name, menge in (("ONNX", a), ("torch", b)):
            check(any(STELLEN[-1] <= st < STELLEN[-1] + len(NAME)
                      for _, st, _ in menge),
                  f"{name} findet am Schluss nichts")
        gemeinsam = len(a & b)
        print(f"   OK   ONNX {len(a)}, torch {len(b)}, "
              f"{gemeinsam} deckungsgleich")
    except ImportError as e:
        uebersprungen.append(f"torch fehlt ({e})")
        print(f"   ⚠ NICHT GELAUFEN — torch fehlt.")


print()
if uebersprungen:
    # ⚠️ Ein wortloser Sprung meldet Bereitschaft. Was NICHT lief, steht
    # hier — sonst sieht ein Lauf ohne Modell aus wie ein gruener Lauf.
    print("UEBERSPRUNGEN — ⚠ NICHT VOLLSTAENDIG GELAUFEN:")
    for u in dict.fromkeys(uebersprungen):
        print(f"    {u}")
    print("  Punkt 1 laeuft immer und haette den Fehler vom 29.8. gefangen.")
    print("  Die Punkte 2 bis 4 messen — ohne Modell ist das KEINE Entwarnung.")
    print()

if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Lange Dokumente werden ganz gesehen.")
