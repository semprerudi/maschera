#!/usr/bin/env python3
"""Was `tools/streuung.py` zusagt — als Pruefung statt als Kommentar.

`streuung.py` macht drei Zusagen:

1. Es druckt **keine Leckwerte**. Ein Leck aus einem Golddokument IST das
   geschuetzte Personendatum; eine Uebersicht ueber acht Laeufe waere sonst
   ein bequemer Weg, echte Werte in einen Modellkontext zu tragen.
2. Bei **n < 3** gibt es keine σ-Vielfachen. σ aus zwei Werten ist
   zufaellig und ergaebe Angaben wie `Micro-F1 +13.0σ`.
3. Es liest die Golddokumente ueber `eval_documents.lade_gold()` und baut
   sich **keinen zweiten Lader**.

Eine Zusage im Kommentar ist keine Pruefung.

Punkt 1 und 3 sind Quelltextwachen — sie lesen die Datei, nicht ihre
Ausgabe. Das ist bewusst: um die Ausgabe zu pruefen, braeuchte es ein
Modell und echte Golddokumente, und dann pruefte die Pruefung mit genau
dem Material, vor dem sie schuetzen soll.
"""
import ast
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

QUELLE = (WURZEL / "tools" / "streuung.py").read_text(encoding="utf-8")

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


print("1. Die Schwellen des Urteils")
# Import erst hier: er zieht core/ mit, aber kein torch — `messe()` holt
# den Scorer absichtlich erst beim Aufruf.
from streuung import urteil  # noqa: E402

check("NICHT AUFGELOEST" in urteil(0.5, 1.0),
      "Δ unter σ gilt nicht als aufgeloest")
check("NICHT AUFGELOEST" in urteil(1.0, 1.0),
      "Δ genau auf σ gilt nicht als aufgeloest")
check("schwach" in urteil(1.5, 1.0),
      "Δ zwischen einem und zwei σ ist schwach")
check("deutlich" in urteil(2.5, 1.0),
      "Δ ueber zwei σ ist deutlich")
check("σ = 0" in urteil(1.0, 0.0),
      "σ = 0 darf keine Division ergeben, sondern eine Auskunft")
# ⚠️ Die Schwelle sagt "das Testset sieht es nicht" und NICHT "es gibt
# keinen Unterschied". Der Unterschied zwischen beiden Saetzen ist der
# ganze Grund fuer dieses Werkzeug.
check("kein Unterschied" not in urteil(0.5, 1.0),
      "ein unaufgeloester Unterschied darf nicht als 'kein Unterschied' "
      "ausgegeben werden")
if not failures:
    print("   OK   fuenf Schwellen, und keine Entwarnung bei Δ < σ")


print("\n2. Keine Leckwerte in der Ausgabe")
# `report.leaked` und `report.over` sind Listen von (Tag, WERT). Erlaubt
# ist nur, sie zu ZAEHLEN. Wer eines davon anders benutzt, traegt den Wert
# potenziell in die Ausgabe.
baum = ast.parse(QUELLE)
vorher = len(failures)
for knoten in ast.walk(baum):
    if not isinstance(knoten, ast.Attribute):
        continue
    if knoten.attr not in ("leaked", "over"):
        continue
    eltern = [n for n in ast.walk(baum)
              if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name) and n.func.id == "len"
              and knoten in n.args]
    check(bool(eltern),
          f"tools/streuung.py benutzt .{knoten.attr} in Zeile "
          f"{knoten.lineno} anders als in len() — Leckwerte koennten in "
          f"die Ausgabe geraten")
if len(failures) == vorher:
    print("   OK   .leaked und .over werden ausschliesslich gezaehlt")


print("\n3. Die Wache gegen σ-Vielfache bei zu wenigen Laeufen")
vorher = len(failures)
check("< 3" in QUELLE,
      "keine Schwelle n < 3 im Quelltext — die σ-Vielfachen sind "
      "ungeschuetzt")
check("keine Vielfachen" in QUELLE,
      "kein Zweig, der bei zu wenigen Laeufen auf die Vielfachen "
      "verzichtet")
if len(failures) == vorher:
    print("   OK   unter drei Laeufen keine Vielfachen")


print("\n4. Kein zweiter Lader fuer die Golddokumente")
vorher = len(failures)
check("from eval_documents import lade_gold" in QUELLE,
      "streuung.py holt die Golddokumente nicht ueber "
      "eval_documents.lade_gold()")
# ⚠️ Nicht auf das blosse Wort pruefen: `--auch-ungeprueft` REICHT die
# Entscheidung nur weiter und ist richtig hier. Gesucht ist, wer sie
# TRIFFT — der Griff in die Golddatei und das Absuchen des Verzeichnisses.
check('get("geprueft")' not in QUELLE,
      "streuung.py entscheidet selbst ueber `geprueft` — diese Regel "
      "gehoert in lade_gold() und nur dorthin")
check('glob("*.json")' not in QUELLE,
      "streuung.py sucht die Golddateien selbst zusammen statt ueber "
      "lade_gold()")
if len(failures) == vorher:
    print("   OK   ein Lader, eine `geprueft`-Regel")


print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Punkt(e)")
    raise SystemExit(1)
print("BESTANDEN — Streuungswerkzeug haelt seine Zusagen")
