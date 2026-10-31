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
import io
import subprocess
import sys
import tempfile
import zlib
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

print("6. Brotli erreicht MuPDF nicht: die rohe Datei")
# ⚠️ Die Proben tragen kaputte Daten und keinen Angriff. Ein kaputter
# Brotli-Strom laesst MuPDF aber haengen, deshalb laeuft der ganze Weg in
# eigenen Prozessen: gibt die Wache nach, wird die Pruefung rot und bleibt
# nicht stehen.
from dokumente import (inhalt_brotli_verdacht, pdf_entschaerfen,  # noqa: E402
                       pdf_verdeckter_filter)

for _probe in (b"<</Filter/BrotliDecode>>", b"<</Filter/Br>>", b"<</F/Br>>",
               b"<</Filter/Brotli#44ecode>>", b"<</Filter/B#72>>",
               b"<</Filter[/Fl/Br]>>", b"<</X/F/Filter/Br>>",
               b"<</T(100%)/Filter %c\n/Br>>", b"5 0 obj /Br endobj"):
    _neu = pdf_entschaerfen(_probe)
    check(len(_neu) == len(_probe), f"Laenge geaendert: {_probe!r}")
    check(b"/~b" in _neu, f"nicht ueberschrieben: {_probe!r}")
for _probe in (b"<</Filter 5 0 R>>", b"<</Filter[5 0 R]>>",
               b"<</Filter[/Fl 5 0 R]>>", b"<</Filter %c\n 5 0 R>>",
               b"<</F 5 0 R>>"):
    check(pdf_verdeckter_filter(_probe), f"nicht erkannt: {_probe!r}")
print("   OK   jede gemessene Schreibweise")

print("7. Gewoehnliche PDF fallen nicht durch")
for _probe in (b"<</Font<</F1 5 0 R/F2 6 0 R>>>>", b"<</Type/Annot/F 4>>",
               b"<</Filter/FlateDecode>>", b"<</Filter[/A85/Fl]>>",
               b"<</Filter /FlateDecode /Length 7 0 R>>",
               b"<</F /Xy /Length 7 0 R>>",
               b"<</F 5 0 R>>\n5 0 obj\n<</F(a.pdf)>>\nendobj"):
    check(not pdf_verdeckter_filter(_probe), f"zu Unrecht: {_probe!r}")
check(pdf_entschaerfen(b"/Brot /Bruch /Xy /Filter") == b"/Brot /Bruch /Xy /Filter",
      "aehnliche Namen werden ueberschrieben")
_rand = bytes(i * 37 % 251 for i in range(4096)) * 500
check(pdf_entschaerfen(_rand) == _rand, "Binaerdaten werden veraendert")
check(not pdf_verdeckter_filter(_rand), "Binaerdaten loesen die Wache aus")
check(not inhalt_brotli_verdacht(b"BI /W 1 /Xb0 1 ID x EI"),
      "ein Name, der mit /Xb beginnt, loest aus")
check(not inhalt_brotli_verdacht(b"<a>BI</a><b>x</Br><c>ID</c>"),
      "XML in einem Anhang loest aus")
check(not inhalt_brotli_verdacht(b"BT (a /Br) Tj ET BI /W 1 /F /Fl ID x EI"),
      "Text oder Flate loest aus")
for _probe in (b"q BI /W 1 /F /Br ID x EI Q", b"BI/F/BrotliDecode ID x EI",
               b"BI /(ID) /F /B#72 ID x EI", b"(a)BI /ID 1 /F /Br ID x EI",
               b"BI /F /Br ID x", b"BI /X (EI ) /F /Br ID x EI",
               b"BI /X 1 % EI\n /F /Br ID x EI", b"BI\n/F /~b ID x EI"):
    check(inhalt_brotli_verdacht(_probe), f"nicht erkannt: {_probe!r}")
print("   OK   Schriften, Anmerkungen, Flate, Anhaenge, Binaerdaten")

print("8. Der ganze Weg: echtes MuPDF, je Fall ein Prozess")
_KURZ = (
    "import sys; sys.path[:0] = ['.', 'tools']\n"
    "from pathlib import Path\n"
    "from core.hinweise import Abbruch\n"
    "from dokumente import pdf_zu_text\n"
    "try:\n    print('GELESEN', pdf_zu_text(Path(sys.argv[1]))[0][:40])\n"
    "except Abbruch as e:\n    print(e.schluessel)\n")


def _pdf(objekte):
    b = b"%PDF-1.7\n"
    orte = []
    for i, o in enumerate(objekte, 1):
        orte.append(len(b))
        b += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    a = len(b)
    b += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objekte) + 1)
    for o in orte:
        b += b"%010d 00000 n \n" % o
    return b + (b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objekte) + 1, a))


def _strom(d, c):
    return b"<<" + d + b"/Length %d>>\nstream\n" % len(c) + c + b"\nendstream"


_KAPUTT = b"\x1b\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
_KOPF = [b"<</Type/Catalog/Pages 2 0 R>>",
         b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
         b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R"
         b"/Resources<</Font<</F1 <</Type/Font/Subtype/Type1"
         b"/BaseFont/Helvetica>>>>>>>>"]
_TEXT = b"BT /F1 14 Tf 10 50 Td (Gesund) Tj ET"


def _inline(name):
    return _TEXT + b" q 9 0 0 9 0 0 cm BI /W 4 /H 4 /BPC 8 /CS /G /F /" + name \
        + b" ID " + _KAPUTT + b" EI Q"


def _mit_objektstrom():
    """Stream 4 -> /F 5 0 R -> [6 0 R] -> /Br, versteckt in Objektstrom 7."""
    kopf, wert = b"6 0 ", b"/Br"
    teile = _KOPF + [_strom(b"/F 5 0 R", _KAPUTT), b"[6 0 R]",
                     None,
                     _strom(b"/Type/ObjStm/N 1/First %d/Filter/FlateDecode"
                            % len(kopf), zlib.compress(kopf + wert))]
    b = b"%PDF-1.7\n"
    orte = {}
    for i, o in enumerate(teile, 1):
        if o is not None:
            orte[i] = len(b)
            b += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    ab = len(b)
    orte[8] = ab
    zeilen = b"\0\0\0\0\0\0"
    for i in range(1, 9):
        if i == 6:
            zeilen += b"\2" + (7).to_bytes(4, "big") + b"\0"
        else:
            zeilen += b"\1" + orte[i].to_bytes(4, "big") + b"\0"
    b += b"8 0 obj\n" + _strom(b"/Type/XRef/Size 9/W[1 4 1]/Root 1 0 R",
                               zeilen) + b"\nendobj\n"
    return b + b"startxref\n%d\n%%%%EOF\n" % ab


def _katalog_hinter_verweis(schluessel, zusatz=b"", art=b"/Type/ObjStm"):
    """Katalog in Objektstrom 5, dessen Filter auf /Br in Objektstrom 8 zeigt."""
    kopf, wert = b"7 0 ", b"/Br"
    teile = {2: _KOPF[1], 3: _KOPF[2], 4: _strom(b"", _TEXT),
             5: _strom(art + b"/N 1/First 4" + schluessel, _KAPUTT),
             8: _strom(b"/Type/ObjStm/N 1/First %d/Filter/FlateDecode"
                       % len(kopf), zlib.compress(kopf + wert))}
    b = b"%PDF-1.7\n" + zusatz
    orte = {}
    for i, o in teile.items():
        orte[i] = len(b)
        b += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    ab = len(b)
    orte[9] = ab
    zeilen = b"\0\0\0\0\0\0" + b"\2" + (5).to_bytes(4, "big") + b"\0"
    for i in (2, 3, 4, 5):
        zeilen += b"\1" + orte[i].to_bytes(4, "big") + b"\0"
    zeilen += b"\0\0\0\0\0\0" + b"\2" + (8).to_bytes(4, "big") + b"\0"
    zeilen += b"\1" + orte[8].to_bytes(4, "big") + b"\0"
    zeilen += b"\1" + orte[9].to_bytes(4, "big") + b"\0"
    b += b"9 0 obj\n" + _strom(b"/Type/XRef/Size 10/W[1 4 1]/Root 1 0 R",
                               zeilen) + b"\nendobj\n"
    return b + b"startxref\n%d\n%%%%EOF\n" % ab


def _katalog_im_brotli():
    """Der Dokumentkatalog in einem Objektstrom: `open()` braucht ihn sofort."""
    teile = {2: _KOPF[1], 3: _KOPF[2], 4: _strom(b"", _TEXT),
             5: _strom(b"/Type/ObjStm/N 1/First 4/Filter/Br", _KAPUTT)}
    b = b"%PDF-1.7\n"
    orte = {}
    for i, o in teile.items():
        orte[i] = len(b)
        b += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    ab = len(b)
    orte[6] = ab
    zeilen = b"\0\0\0\0\0\0" + b"\2" + (5).to_bytes(4, "big") + b"\0"
    for i in range(2, 7):
        zeilen += b"\1" + orte[i].to_bytes(4, "big") + b"\0"
    b += b"6 0 obj\n" + _strom(b"/Type/XRef/Size 7/W[1 4 1]/Root 1 0 R",
                               zeilen) + b"\nendobj\n"
    return b + b"startxref\n%d\n%%%%EOF\n" % ab


def _zwei_stroeme(c1, c2):
    seite = _KOPF[2].replace(b"/Contents 4 0 R", b"/Contents[4 0 R 5 0 R]")
    return _pdf(_KOPF[:2] + [seite,
                             _strom(b"/Filter/FlateDecode", zlib.compress(c1)),
                             _strom(b"/Filter/FlateDecode", zlib.compress(c2))])


_BILD = b"q 9 0 0 9 0 0 cm BI /W 1 /H 1 /BPC 8 /CS /G"
_FAELLE = {
    "katalog": _katalog_im_brotli(),
    "verweis_hex": _katalog_hinter_verweis(b"/Filt#65r 7 0 R"),
    "verweis_kurzhex": _katalog_hinter_verweis(b"/#46 7 0 R"),
    "verweis_null": _katalog_hinter_verweis(b"/Filter[null 7 0 R]"),
    "verweis_plus": _katalog_hinter_verweis(b"/Filter +7 0 R"),
    "verweis_koeder": _katalog_hinter_verweis(b"/F 7 0 R", b"%7 0 obj\n"),
    # Der Koeder steht im Klartext, nur das Lesen des Objektstroms faengt das.
    "verweis_string": _katalog_hinter_verweis(b"/F 7 0 R", b"(7 0 obj)\n", b""),
    "geteilt": _zwei_stroeme(_BILD, b"/F /Br ID " + _KAPUTT + b" EI Q"),
    "geteilt_nach_bi": _zwei_stroeme(b"q BI", b"/W 1 /H 1 /BPC 8 /CS /G "
                                     b"/F /BrotliDecode ID " + _KAPUTT + b" EI Q"),
    "geteilt_name": _zwei_stroeme(_BILD + b" /F /B",
                                  b"r ID " + _KAPUTT + b" EI Q"),
    "ei_im_string": _pdf(_KOPF + [_strom(
        b"/Filter/FlateDecode", zlib.compress(
            b"q BI /W 1 /H 1 /BPC 8 /CS /G /X (EI ) /F /Br ID " + _KAPUTT
            + b" EI Q"))]),
    "lang": _pdf(_KOPF + [_strom(b"/Filter/BrotliDecode", _KAPUTT)]),
    "kurz": _pdf(_KOPF + [_strom(b"/Filter/Br", _KAPUTT)]),
    "f": _pdf(_KOPF + [_strom(b"/F/Br", _KAPUTT)]),
    "hex": _pdf(_KOPF + [_strom(b"/Filter/B#72", _KAPUTT)]),
    "array": _pdf(_KOPF + [_strom(b"/Filter[/Br]", _KAPUTT)]),
    "schluessel": _pdf(_KOPF + [_strom(b"/X/F/Filter/Br", _KAPUTT)]),
    "kombiniert": _pdf(_KOPF + [_strom(b"/T(100%)/Filter %c\n/Br", _KAPUTT)]),
    "indirekt": _pdf(_KOPF + [_strom(b"/Filter 5 0 R", _KAPUTT), b"/Br"]),
    "f_weit": _pdf(_KOPF + [_strom(b"/F 5 0 R", _KAPUTT),
                            b" " * 600 + b"/Br"]),
    "objstrom": _mit_objektstrom(),
    "f_verdeckt": _pdf(_KOPF + [_strom(b"/F 9 0 R", _KAPUTT)]),
    "inline": _pdf(_KOPF + [_strom(b"/Filter/FlateDecode",
                                   zlib.compress(_inline(b"Br")))]),
    "inline_hex": _pdf(_KOPF + [_strom(b"/Filter/FlateDecode",
                                       zlib.compress(_inline(b"B#72")))]),
    "inline_bild": _pdf(_KOPF + [_strom(b"/Subtype/Image/Filter/FlateDecode",
                                        zlib.compress(_inline(b"Br")))]),
}
with tempfile.TemporaryDirectory() as _o:
    for _name, _b in _FAELLE.items():
        _p = Path(_o) / f"{_name}.pdf"
        _p.write_bytes(_b)
        try:
            _l = subprocess.run([sys.executable, "-c", _KURZ, str(_p)],
                                cwd=WURZEL, capture_output=True, text=True,
                                timeout=20)
            check("pdf_brotli" in _l.stdout,
                  f"{_name}: {(_l.stdout or _l.stderr)[-80:]!r}")
        except subprocess.TimeoutExpired:
            check(False, f"{_name} erreicht den Decoder: MuPDF haengt")
    _gesund = [_pdf(_KOPF + [_strom(b"", _TEXT)]),
               _pdf(_KOPF[:2] + [_KOPF[2], _strom(b"/Filter/FlateDecode",
                                                  zlib.compress(_TEXT))])]
    _echt = pymupdf.open()
    _echt.new_page().insert_text((72, 72), "Gesund")
    _echt.embfile_add("a.xml", b"<a>BI</a><b>x</Br><c>ID</c>")
    _gesund.append(_echt.tobytes(garbage=3, deflate=True))
    # Mehrere Inhaltsstroeme und eine Ressource, die mit /Xb beginnt.
    _gesund.append(_zwei_stroeme(_TEXT, b" q 9 0 0 9 0 0 cm BI /W 1 /H 1 /BPC 8 "
                                 b"/CS /G /Xb0 1 /Xb 1 ID x EI Q"))
    # Ein #-Paar in komprimierten Bytes darf gesunde Objektstroeme nicht stoeren.
    _hexdaten = _echt.tobytes(garbage=3, deflate=True, use_objstms=1)
    _gesund.append(_hexdaten)
    _gesund.append(_pdf(_KOPF + [_strom(b"/Xb 1/Xb0 2/Resources<</XObject"
                                        b"<</Xb 5 0 R>>>>", _TEXT)]))
    for _i, _b in enumerate(_gesund):
        _p = Path(_o) / f"gesund{_i}.pdf"
        _p.write_bytes(_b)
        _l = subprocess.run([sys.executable, "-c", _KURZ, str(_p)], cwd=WURZEL,
                            capture_output=True, text=True, timeout=20)
        check("GELESEN Gesund" in _l.stdout,
              f"gesundes PDF {_i}: {(_l.stdout or _l.stderr)[-80:]!r}")
_body = _FAELLE["kurz"]
r = c.post("/api/lesen", data={"datei": (io.BytesIO(_body), "b.pdf")},
           content_type="multipart/form-data")
check(r.status_code == 400, f"Status {r.status_code}")
check((r.get_json() or {}).get("fehler_schluessel") == "pdf_brotli",
      f"Antwort {r.get_json()}")
print(f"   OK   {len(_FAELLE)} Faelle abgewiesen, {len(_gesund)} gesunde gelesen")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Gescanntes PDF: der Nullbefund ist nicht mehr stumm.")
