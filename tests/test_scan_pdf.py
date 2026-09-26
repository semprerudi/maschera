"""Ein gescanntes PDF ohne Textebene — der stille Nullbefund.

    python3 tests/test_scan_pdf.py

⚠️ **Der gefaehrlichste Befund ist ein leerer.** Ein Scan ohne Textebene
liefert null Zeichen. Ohne Auskunft sieht das aus wie «nichts gefunden, alles
in Ordnung» — dabei heisst es «nichts gelesen». Der Anwender laedt eine
Verfuegung hoch, sieht keine Fundstellen und schliesst daraus, das Dokument
enthalte keine Personendaten.

`dokumente.pdf_zu_text` formuliert die richtige Warnung, und sie muss bis
zur Oberflaeche durchkommen — nicht als «Der Text ist leer.», das die
Datei fuer kaputt statt unlesbar haelt. Diese Pruefung haelt den Weg vom
Leser bis zur Oberflaeche fest.

Braucht `pymupdf`. Fehlt es, meldet sie sich als uebersprungen — sie prueft
dann NICHTS.
"""
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "app"))
sys.path.insert(0, str(WURZEL / "tools"))

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        print("UEBERSPRUNGEN: pymupdf nicht installiert.")
        raise SystemExit(0)

try:
    import flask  # noqa: F401
except ImportError:
    print("UEBERSPRUNGEN: Flask nicht installiert.")
    raise SystemExit(0)

from app import baue_mit_oberflaeche  # noqa: E402
from dokumente import lies  # noqa: E402
from serve import Zustand  # noqa: E402

failures: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="maschera-scan-"))


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def scan_pdf(name: str, seiten: int = 1) -> Path:
    """Ein PDF mit Strichen statt Text — wie ein Scan ohne Texterkennung."""
    pfad = TMP / name
    d = pymupdf.open()
    for _ in range(seiten):
        s = d.new_page()
        s.draw_rect(pymupdf.Rect(60, 60, 400, 300), color=(0, 0, 0), width=1)
        s.draw_line(pymupdf.Point(80, 120), pymupdf.Point(380, 120))
    d.save(pfad)
    d.close()
    return pfad


def text_pdf(name: str, inhalt: str) -> Path:
    pfad = TMP / name
    d = pymupdf.open()
    s = d.new_page()
    s.insert_text(pymupdf.Point(72, 100), inhalt, fontsize=11)
    d.save(pfad)
    d.close()
    return pfad


print("1. Der Leser meldet den leeren Scan")
dok = lies(scan_pdf("scan.pdf"))[0]
check(dok.text.strip() == "", f"unerwarteter Text: {dok.text[:60]!r}")
check(any(h["schluessel"] == "pdf_ohne_text" for h in dok.hinweise),
      f"keine Warnung, nur: {dok.hinweise}")
check(any("Scan" in h["text"] or "OCR" in h["text"]
          for h in dok.hinweise),
      "die Warnung nennt den Grund nicht")
print("   OK   " + dok.hinweise[0]["text"][:58] + " …")

print("2. Ein PDF MIT Textebene wird normal gelesen")
# Gegenprobe: die Warnung darf nicht immer kommen.
dok2 = lies(text_pdf("mittext.pdf", "Frau Brulhart, 3011 Bern"))[0]
check("Brulhart" in dok2.text, f"Text nicht gelesen: {dok2.text!r}")
check(not any(h["schluessel"] == "pdf_ohne_text"
              for h in dok2.hinweise),
      f"warnt ohne Grund: {dok2.hinweise}")
print("   OK   gelesen, keine Warnung")

print("3. Der Endpunkt reicht die Warnung durch, statt sie zu ersetzen")
# ⚠️ Der eigentliche Befund: der Grund kommt an, nicht «Der Text ist
# leer.» — sonst ginge mit ihm die Aussage verloren, dass ein leerer Befund
# keine Entwarnung ist.
ORDNER = tempfile.TemporaryDirectory()
z = Zustand("ch", regeln_pfad=str(Path(ORDNER.name) / "regeln.yaml"))
c = baue_mit_oberflaeche(z).test_client()
with scan_pdf("scan2.pdf").open("rb") as f:
    r = c.post("/api/anonymisieren",
               data={"datei": (f, "scan2.pdf")},
               content_type="multipart/form-data")
check(r.status_code == 400, f"Status {r.status_code} statt 400")
d = r.get_json()
check("NICHT" in (d.get("fehler") or ""),
      f"die Meldung nennt den Grund nicht: {d.get('fehler')!r}")
check(d.get("fehler") != "Der Text ist leer.",
      "die Warnung des Lesers wurde durch die kurze Fassung ersetzt")
check(isinstance(d.get("hinweise"), list) and d["hinweise"],
      "keine Hinweise im Fehlerkoerper")
if not failures:
    print("   OK   " + (d.get("fehler") or "")[:58] + " …")

print("4. Ein lesbares PDF laeuft normal durch")
with text_pdf("mittext2.pdf", "AHV 756.1234.5678.97 am 14.03.2026").open("rb") as f:
    r = c.post("/api/anonymisieren",
               data={"datei": (f, "mittext2.pdf")},
               content_type="multipart/form-data")
check(r.status_code == 200, f"Status {r.status_code}: {r.get_json()}")
d = r.get_json()
check("756.1234.5678.97" not in d["maskiert"], "AHV-Nummer nicht maskiert")
tags = {s["tag"] for s in d["spans"]}
check("AHVN13" in tags, f"gefunden: {sorted(tags)}")
print(f"   OK   {len(d['spans'])} Fundstellen: {', '.join(sorted(tags))}")

print("5. Die Oberflaeche zeigt den Grund, nicht nur den Status")
js = c.get("/maschera.js").get_data(as_text=True)
check("e.hinweise" in js,
      "maschera.js liest die Hinweise aus dem Fehlerkoerper nicht")
check("hinweise = d.hinweise" in js.replace(" ", "").replace("\n", "")
      or "d.hinweise" in js,
      "maschera.js kennt das Feld `hinweise` im Fehlerfall nicht")
print("   OK   Hinweise werden ausgewertet")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Gescanntes PDF: der Nullbefund ist nicht mehr stumm.")
