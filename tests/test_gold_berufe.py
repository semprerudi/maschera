"""Nachmarkieren von Berufen im Testset (`tools/gold_berufe.py`).

    python3 tests/test_gold_berufe.py

Laeuft auf ERFUNDENEN Dokumenten in einem Wegwerfordner, nie auf dem
echten Testset. Die Antworten kommen aus einer Liste statt von der Tastatur.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from gold_berufe import eintragen, finde, markiere  # noqa: E402

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


FORMEN = {"projektleiterin", "amtschef", "müller"}
KOEDER = {"weber"}

print("1. Finden: laengste Form, ganze Woerter, Koeder, eigene Suche")
text = "Anna Weber, Projektleiterin. Der Amtschefin schrieb Herr Amtschef."
t = finde(text, FORMEN, KOEDER, suche=[r"Herr"])
werte = [(text[a:e], k) for a, e, k in t]
check(("Projektleiterin", False) in werte, f"Projektleiterin fehlt: {werte}")
check(("Weber", True) in werte, f"Weber nicht als Koeder: {werte}")
check(("Amtschefin", False) not in werte and ("Amtschef", False) in werte,
      f"«Amtschefin» darf nicht als «Amtschef» treffen: {werte}")
check(("Herr", False) in werte, f"--suche greift nicht: {werte}")
if not failures:
    print("   OK   vier Faelle")

print("\n2. Eintragen: neu, umtaggen, teilen, teilweise")
text = "Projektleiterin, Bundesamt für Justiz"
spans = [{"tag": "ORG", "start": 0, "end": len(text)}]
r = eintragen(spans, 0, 15, text)
tags = sorted((s["tag"], text[s["start"]:s["end"]]) for s in spans)
check(r.startswith("geteilt") and tags == [
    ("JOBTITLE", "Projektleiterin"), ("ORG", "Bundesamt für Justiz")],
    f"Teilen falsch: {r} {tags}")
spans = [{"tag": "ORG", "start": 0, "end": 15}]
check(eintragen(spans, 0, 15, text).startswith("umgetaggt")
      and spans[0]["tag"] == "JOBTITLE", "Umtaggen falsch")
spans = []
check(eintragen(spans, 0, 15, text) == "neu" and len(spans) == 1, "Neu falsch")
spans = [{"tag": "ORG", "start": 10, "end": 25}]
check(eintragen(spans, 0, 15, text).startswith("UEBERLAPPT")
      and spans[0]["tag"] == "ORG", "Teilweise Ueberlappung wurde veraendert")
print("   OK   vier Faelle") if not failures else None

print("\n3. Ganzer Durchgang: Sicherung, Schreiben, q, Koeder bleibt")
with tempfile.TemporaryDirectory() as tmp:
    ordner = Path(tmp)
    a = {"id": "a", "geprueft": True,
         "text": "Gruss\nAnna Weber\nProjektleiterin, Bundesamt für Justiz",
         "spans": [{"tag": "FULLNAME", "start": 11, "end": 16},
                   {"tag": "ORG", "start": 17, "end": 54}]}
    b = {"id": "b", "geprueft": True, "text": "Herr Amtschef meldet sich.",
         "spans": []}
    (ordner / "a.json").write_text(json.dumps(a), encoding="utf-8")
    (ordner / "b.json").write_text(json.dumps(b), encoding="utf-8")
    antworten = iter(["n", "j", "q"])   # Weber: n, Projektleiterin: j, b: q
    z = markiere(ordner, FORMEN, KOEDER, frage=lambda _: next(antworten),
                 ausgabe=lambda *_: None)
    neu_a = json.loads((ordner / "a.json").read_text(encoding="utf-8"))
    tags = sorted((s["tag"], neu_a["text"][s["start"]:s["end"]])
                  for s in neu_a["spans"])
    check(tags == [("FULLNAME", "Weber"), ("JOBTITLE", "Projektleiterin"),
                   ("ORG", "Bundesamt für Justiz")], f"a.json falsch: {tags}")
    check(neu_a["geprueft"] is True, "`geprueft` veraendert")
    sicherungen = list(ordner.glob(".sicherung-*/a.json"))
    check(len(sicherungen) == 1, "keine Sicherung von a.json")
    if sicherungen:
        alt = json.loads(sicherungen[0].read_text(encoding="utf-8"))
        check(alt == a, "Sicherung ist nicht der alte Stand")
    neu_b = json.loads((ordner / "b.json").read_text(encoding="utf-8"))
    check(neu_b["spans"] == [], "nach q wurde b.json trotzdem veraendert")
    check(z["geteilt"] == 1 and z["dateien"] == 1 and z["nein"] == 1,
          f"Zaehlung falsch: {z}")
if not failures:
    print("   OK   eine Datei geschrieben, gesichert, nach q nichts mehr")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
