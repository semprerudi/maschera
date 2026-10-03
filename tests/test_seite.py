#!/usr/bin/env python3
"""Das Upload-Werkzeug der Projektseite haelt seine Zusagen — als Pruefung.

    python3 tests/test_seite.py

`tools/seite.py` laedt auf einen fremden Server und hat dafuer ein Passwort.
Geprueft wird, ohne Netz und ohne Zugangsdaten, was an diesem Werkzeug am
teuersten waere:

  1. nur verschluesselt — kein Rueckfall auf Klartext-FTP,
  2. kein Passwort im Quelltext, nur aus `~/.netrc`,
  3. nichts wird geloescht,
  4. nur im festen Ordner,
  5. ohne `--ja` wird nichts hochgeladen, nicht einmal angemeldet,
  6. `index.html` kommt zuletzt, und Kommentare im CSS zaehlen nicht als Datei.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "tools"))

import seite  # noqa: E402

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def ohne_kommentare(text: str) -> str:
    text = re.sub(r'""".*?"""', "", text, flags=re.S)
    return "\n".join(z for z in text.splitlines()
                     if not z.lstrip().startswith("#"))


QUELLE = (WURZEL / "tools" / "seite.py").read_text(encoding="utf-8")
CODE = ohne_kommentare(QUELLE)

print("1. Nur verschluesselt, nie Klartext")
check("ftplib.FTP_TLS(" in CODE, "seite.py benutzt FTP_TLS nicht")
check(".auth()" in CODE and ".prot_p()" in CODE,
      "seite.py verschluesselt Anmeldung oder Datenkanal nicht")
check(not re.search(r"ftplib\.FTP\(", CODE),
      "seite.py kennt Klartext-FTP (ftplib.FTP)")
check("create_default_context" in CODE, "keine Zertifikatspruefung")
check("check_hostname = False" not in CODE and "CERT_NONE" not in CODE,
      "die Zertifikatspruefung ist abgeschaltet")
# Scheitert TLS, bricht es ab — der Satz steht im Code, nicht nur im Kommentar.
check("NICHT unverschluesselt" in QUELLE, "kein Abbruch bei fehlendem TLS")
if not failures:
    print("   OK   FTPS, Datenkanal geschuetzt, Zertifikat geprueft")

print("\n2. Kein Passwort im Quelltext")
_vorher = len(failures)
check("netrc.netrc()" in CODE, "seite.py liest ~/.netrc nicht")
check(not re.search(r"(?i)\b(passwort|password|passwd)\s*=\s*[\"']", CODE),
      "seite.py traegt ein Passwort im Quelltext")
with tempfile.TemporaryDirectory() as _heim:
    _alt = os.environ.get("HOME")
    os.environ["HOME"] = _heim            # leer: keine ~/.netrc
    try:
        seite.verbinden()
        check(False, "verbinden() lief ohne ~/.netrc weiter")
    except SystemExit as e:
        check("~/.netrc" in str(e), f"Meldung ohne Hinweis auf ~/.netrc: {e}")
    finally:
        if _alt is not None:
            os.environ["HOME"] = _alt
if len(failures) == _vorher:
    print("   OK   Zugangsdaten nur aus ~/.netrc, ohne sie bricht es ab")

print("\n3. Nichts wird geloescht")
_vorher = len(failures)
for _verboten in (".delete(", ".rmd(", "DELE ", "RMD ", "os.remove(",
                  "unlink(", "rmtree("):
    # `unlink`/`rmtree` gibt es im Spiegeln (lokal, in site/); der Server
    # darf nie damit gemeint sein — `ftps` steht dann in derselben Zeile.
    for _z in CODE.splitlines():
        if _verboten in _z and ("ftps" in _z or "ftp" in _z.lower()):
            check(False, f"seite.py loescht auf dem Server: {_z.strip()}")
check(".delete(" not in CODE and ".rmd(" not in CODE,
      "seite.py ruft einen Loeschbefehl des Servers auf")
if len(failures) == _vorher:
    print("   OK   kein Loeschbefehl fuer den Server")

print("\n4. Nur der feste Ordner")
check(seite.FTP_ORDNER == "/www/maschera",
      f"FTP_ORDNER ist {seite.FTP_ORDNER}, erwartet /www/maschera")
check(CODE.count("ftps.cwd(FTP_ORDNER)") >= 1, "cwd nicht auf FTP_ORDNER")
if not failures:
    print("   OK   /www/maschera")

print("\n5. Ohne --ja wird nichts hochgeladen, nicht einmal angemeldet")
_vorher = len(failures)


class _Args:
    nach = "unbenutzt"
    ja = False


_gerufen = []
_orig = (seite.verbinden, seite.live_stand, seite.lokal_stand)
seite.verbinden = lambda: _gerufen.append("verbinden") or (_ for _ in ()).throw(
    AssertionError("angemeldet"))
seite.live_stand = lambda: {"index.html": b"alt"}
seite.lokal_stand = lambda ordner: {"index.html": b"neu", "x.css": b"1"}
try:
    _rc = seite.cmd_hochladen(_Args())
    check(_rc == 0, f"Trockenlauf meldet {_rc}")
    check(not _gerufen, "der Trockenlauf meldet sich am Server an")
finally:
    seite.verbinden, seite.live_stand, seite.lokal_stand = _orig
check(re.search(r'"--ja",\s*action="store_true"', CODE) is not None,
      "--ja ist nicht als Schalter mit Vorgabe aus gebaut")
if len(failures) == _vorher:
    print("   OK   Trockenlauf bleibt lokal, --ja ist Pflicht")

print("\n6. index.html zuletzt, Kommentare sind keine Dateien")
_vorher = len(failures)
check(seite._reihenfolge(["index.html", "a.css", "bilder/x.png"])[-1]
      == "index.html", "index.html kommt nicht zuletzt")
_html = ('<link href="stil.css"><script src="zoom.js"></script>'
         '<img src="bilder/de/hero.png"><a href="https://x.ch/">x</a>'
         '<!-- <img src="bilder/de/kommentar.png"> -->')
_css = ('/* @font-face { src:url("schriften/barlow-400.woff2"); } */'
        ' .a { background:url("bilder/favicon.png"); }')
_e = seite.entdecke(_html, _css, "")
check("schriften/barlow-400.woff2" not in _e,
      "eine Datei aus einem CSS-Kommentar gilt als noetig")
check("bilder/de/kommentar.png" not in _e,
      "eine Datei aus einem HTML-Kommentar gilt als noetig")
check({"index.html", "stil.css", "zoom.js", "bilder/favicon.png",
       "bilder/de/hero.png", "bilder/fr/hero.png", "bilder/it/hero.png",
       "bilder/en/hero.png"} <= _e, f"Entdecken unvollstaendig: {sorted(_e)}")
check(not any(p.startswith("https:") for p in _e), "Fremdverweis als Datei")
_neu, _anders, _gleich, _nur = seite.vergleiche(
    {"a": b"1", "b": b"2", "c": b"3"}, {"a": b"1", "b": b"X", "z": b"9"})
check((_neu, _anders, _gleich, _nur) == (["c"], ["b"], ["a"], ["z"]),
      f"vergleiche() falsch: {(_neu, _anders, _gleich, _nur)}")
if len(failures) == _vorher:
    print("   OK   Reihenfolge, Kommentare, Vergleich")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Das Upload-Werkzeug haelt seine Zusagen.")
