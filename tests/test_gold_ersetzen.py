"""Werte in Golddokumenten ersetzen — die Spannen muessen mitwandern.

    python3 tests/test_gold_ersetzen.py

Ein blosses Suchen-und-Ersetzen im Text bereinigte ein Golddokument und
zerstoerte still die Messgrundlage: jede Spanne nach der ersten Aenderung
zeigte danach um die Laengendifferenz daneben. Die Auswertung liefe weiter,
die Zahlen waeren Unsinn, und niemand saehe es.

Deshalb hier: laengengleiche und laengenverschiedene Ersetzung, Ersetzung
innerhalb einer Spanne, und der Abbruch bei halber Ueberlappung.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
WERKZEUG = WURZEL / "tools" / "gold_ersetzen.py"
TMP = Path(tempfile.mkdtemp(prefix="maschera-gold-"))

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def baue(name: str, text: str, spans: list[tuple[str, str]]) -> Path:
    """spans als (tag, teilstring) — die Positionen werden gesucht."""
    liste = []
    for tag, teil in spans:
        i = text.index(teil)
        liste.append({"tag": tag, "start": i, "end": i + len(teil)})
    p = TMP / name
    p.write_text(json.dumps({
        "id": p.stem, "lang": "de", "doctype": "ticket", "geprueft": True,
        "text": text, "spans": liste, "zu_pruefen": [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def lauf(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(WERKZEUG), *args],
                          capture_output=True, text=True, cwd=WURZEL)


def werte(p: Path) -> list[tuple[str, str]]:
    d = json.loads(p.read_text(encoding="utf-8"))
    return [(s["tag"], d["text"][s["start"]:s["end"]]) for s in d["spans"]]


TEXT = ("Sehr geehrte Frau Muster\n"
        "Ihre Anfrage an support@echtefirma.ch wurde weitergeleitet.\n"
        "Rueckfragen an m.muster@echtefirma.ch oder 031 322 11 22.\n")
SPANS = [("FULLNAME", "Muster"), ("EMAIL", "support@echtefirma.ch"),
         ("EMAIL", "m.muster@echtefirma.ch"), ("PHONE", "031 322 11 22")]

print("1. Laengengleiche Ersetzung laesst alle Spannen stehen")
p = baue("gleich.json", TEXT, SPANS)
r = lauf(str(p), "--ersetze", "@echtefirma.ch=@musterfirm.xy")
check(r.returncode == 0, f"Abbruch: {r.stderr.strip()}")
check(("PHONE", "031 322 11 22") in werte(p), "PHONE verschoben")
check(("FULLNAME", "Muster") in werte(p), "FULLNAME verschoben")
print("   OK   4 Spannen unversehrt")

print("2. Laengenverschiedene Ersetzung verschiebt korrekt")
# ⚠️ Der eigentliche Fall. +6 Zeichen, zweimal — die PHONE-Spanne am Ende
# laege ohne Nachfuehrung um 12 Zeichen daneben.
p = baue("laenger.json", TEXT, SPANS)
r = lauf(str(p), "--ersetze", "@echtefirma.ch=@musterfirma.example")
check(r.returncode == 0, f"Abbruch: {r.stderr.strip()}")
w = werte(p)
check(("PHONE", "031 322 11 22") in w, f"PHONE steht falsch: {w}")
check(("FULLNAME", "Muster") in w, f"FULLNAME steht falsch: {w}")
check(("EMAIL", "support@musterfirma.example") in w,
      f"EMAIL nicht mitgewachsen: {w}")
print("   OK   +12 Zeichen, PHONE und FULLNAME sitzen richtig")

print("3. Kuerzere Ersetzung ebenso")
p = baue("kuerzer.json", TEXT, SPANS)
r = lauf(str(p), "--ersetze", "@echtefirma.ch=@x.ch")
check(r.returncode == 0, f"Abbruch: {r.stderr.strip()}")
check(("PHONE", "031 322 11 22") in werte(p), "PHONE verschoben")
print("   OK   -18 Zeichen, PHONE sitzt richtig")

print("4. Halbe Ueberlappung bricht ab und schreibt nicht")
# Die Grenze der Spanne laege mitten im ersetzten Bereich — wo sie nachher
# hingehoert, ist nicht entscheidbar. Raten hiesse, eine Messgrundlage zu
# erfinden.
text2 = "Kontakt: Firma Meier AG, Bern\n"
p = baue("halb.json", text2, [("ORG", "Firma Meier AG")])
vorher = p.read_text(encoding="utf-8")
r = lauf(str(p), "--ersetze", "Meier AG, Bern=Muster AG, Thun")
check(r.returncode != 0, "halbe Ueberlappung wurde durchgelassen")
check("halb" in r.stderr, f"Meldung nennt den Grund nicht: {r.stderr!r}")
check(p.read_text(encoding="utf-8") == vorher,
      "Datei wurde trotz Abbruch geaendert")
print("   OK   Abbruch, Datei unveraendert")

print("5. --probe schreibt nicht")
p = baue("probe.json", TEXT, SPANS)
vorher = p.read_text(encoding="utf-8")
r = lauf(str(p), "--ersetze", "@echtefirma.ch=@y.ch", "--probe")
check(r.returncode == 0, f"Abbruch: {r.stderr.strip()}")
check(p.read_text(encoding="utf-8") == vorher, "--probe hat geschrieben")
print("   OK   unveraendert")

print("6. --zeigen-tag listet nur das gefragte Tag")
p = baue("zeigen.json", TEXT, SPANS)
r = lauf(str(p), "--zeigen-tag", "EMAIL")
check("echtefirma" in r.stdout, "EMAIL nicht gezeigt")
check("031 322" not in r.stdout, "PHONE mitgezeigt, obwohl nicht gefragt")
print("   OK   nur EMAIL")

print("7. Nicht gefundener Suchtext wird gemeldet, nicht verschwiegen")
p = baue("fehlt.json", TEXT, SPANS)
r = lauf(str(p), "--ersetze", "@gibtsnicht.ch=@x.ch", "--probe")
check(r.returncode == 0, f"Abbruch: {r.stderr.strip()}")
print("   OK   still uebergangen, Datei unberuehrt")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Gold-Ersetzung in Ordnung.")
