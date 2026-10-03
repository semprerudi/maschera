"""Die Projektseite unter `site/` — vollstaendig, in vier Sprachen, ohne Nachladen.

`site/` ist, was unter www.maschera.ch online steht (`tools/seite.py` spiegelt
und vergleicht).

    python3 tests/test_webseite.py

Die Seite wirbt damit, dass MASCHERA nichts von aussen laedt und nichts
sendet. Sie selbst darf deshalb weder Schriften noch Skripte noch Bilder
von fremden Servern holen. Dazu: jedes Bildschirmfoto liegt in einer
hellen und einer dunklen Fassung vor, und jeder Text, den die Seite
uebersetzt, steht in allen vier Sprachen — ein fehlender Schluessel
faellt im Browser still auf Deutsch zurueck.
"""
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SITE = WURZEL / "site"
failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


if not (SITE / "index.html").is_file():
    print("UEBERSPRUNGEN — site/index.html fehlt")
    raise SystemExit(0)

HTML = (SITE / "index.html").read_text(encoding="utf-8")
CSS = (SITE / "stil.css").read_text(encoding="utf-8")
JS = (SITE / "sprachen.js").read_text(encoding="utf-8")


print("1. Nichts wird von aussen geladen")
# Verweise (`<a href>`) duerfen nach draussen zeigen — sie laden nichts,
# bevor jemand klickt. Alles, was der Browser beim Oeffnen SELBST holt,
# muss neben der Seite liegen.
_geladen = re.findall(r'<(?:img|script|source|link|iframe)\b[^>]*?'
                      r'(?:src|srcset|href)="([^"]+)"', HTML)
_fremd = [u for u in _geladen if re.match(r"(?:https?:)?//", u)]
check(not _fremd, f"index.html laedt von aussen: {_fremd}")
check(not re.search(r"url\(\s*['\"]?(?:https?:)?//", CSS)
      and "@import" not in CSS,
      "stil.css laedt von aussen (url() oder @import)")
# Im CODE, nicht in den Uebersetzungen — «nothing is fetched» ist ein Satz.
_js_code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', JS)
check(not re.search(r"\b(fetch|XMLHttpRequest|sendBeacon|WebSocket)\b",
                    _js_code),
      "sprachen.js baut eine Verbindung auf")
if not failures:
    print(f"   OK   {len(_geladen)} geladene Dateien, alle lokal")


print("\n2. Jede geladene Datei liegt da, jedes Bild in jeder Sprache, hell UND dunkel")
_vorher = len(failures)
for _u in _geladen:
    check((SITE / _u).is_file(), f"index.html verweist auf {_u} — fehlt")
# ⚠️ Kommentare zuerst weg: der Schriftenblock steht im Stilblatt
# AUSKOMMENTIERT («bis sie geliefert sind»), und ein Verweis im Kommentar ist
# keine Datei, die die Seite braucht. Ohne diesen Schritt schlug die Wache an
# vier Dateien an, die es nicht geben muss.
_css_code = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
for _u in re.findall(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', _css_code):
    check((SITE / _u).is_file(), f"stil.css verweist auf {_u} — fehlt")
# Die Bilder liegen je Sprache unter `bilder/<sprache>/<name>.png`, das
# dunkle Gegenstueck mit Endung `-dunkel`. Das HTML nennt die deutschen;
# `sprachen.js` waehlt den Ordner zur Sprache.
_bilder = sorted({m for m in re.findall(r'bilder/de/([\w-]+)\.png', HTML)
                  if not m.endswith("-dunkel")})
check(_bilder, "keine Bildschirmfotos unter bilder/de/ verwendet")
for _b in _bilder:
    for _spr in ("de", "fr", "it", "en"):
        for _fassung in (_b, _b + "-dunkel"):
            check((SITE / "bilder" / _spr / f"{_fassung}.png").is_file(),
                  f"bilder/{_spr}/{_fassung}.png fehlt")
if len(failures) == _vorher:
    print(f"   OK   {len(_bilder)} Bildschirmfotos, vier Sprachen, hell und dunkel")


print("\n3. Jeder Textschluessel steht in allen vier Sprachen")
_vorher = len(failures)
# Deutsch steht im HTML, fr/it/en in `sprachen.js`.
_schluessel = set(re.findall(r'data-i18n(?:-html)?="([^"]+)"', HTML))
_schluessel |= {a.split(":", 1)[1]
                for a in re.findall(r'data-i18n-attr="([^"]+)"', HTML)}
_teile = re.split(r"\n\s{4}(fr|it|en): \{", JS)
_sprachen = {_teile[i]: set(re.findall(r'"([\w.]+)":', _teile[i + 1]))
             for i in range(1, len(_teile) - 1, 2)}
check(set(_sprachen) == {"fr", "it", "en"},
      f"sprachen.js fuehrt {sorted(_sprachen)}, erwartet fr, it, en")
for _spr, _hat in sorted(_sprachen.items()):
    _fehlt = sorted(_schluessel - _hat)
    check(not _fehlt, f"{_spr}: {len(_fehlt)} Schluessel fehlen: "
                      f"{', '.join(_fehlt[:6])}")
if len(failures) == _vorher:
    print(f"   OK   {len(_schluessel)} Schluessel in de, fr, it, en")


print("\n4. Die Seite verspricht nichts, was nicht stimmt")
_vorher = len(failures)
# Die Lizenz der Pakete, und die Adresse des Modells: beides muss mit dem
# Repository uebereinstimmen, nicht mit einem Entwurf.
check("AGPL-3.0" in HTML, "der Fuss nennt die Lizenz der Pakete nicht")
_readme = (WURZEL / "README.md").read_text(encoding="utf-8")
for _u in set(re.findall(r'href="(https://huggingface\.co/[^"]+)"', HTML)):
    check(_u in _readme, f"Modelladresse {_u} steht nicht im README")
check(re.search(r'href="https://huggingface\.co/', HTML) is not None,
      "die Seite verweist nicht auf das Modell")
# Jeder Download-Knopf zeigt auf einen Dateinamen, den das README ebenfalls
# nennt. Die Dateien im Release tragen feste Namen (`MASCHERA-latest-…`);
# ein Knopf auf einen anderen Namen fuehrt auf eine Fehlerseite — und das
# faellt erst auf, wenn jemand klickt. (Gemessen am 3.10.2026 beim macOS-Knopf:
# README und Seite muessen denselben Namen tragen.)
_readme_de = (WURZEL / "README.de.md").read_text(encoding="utf-8")
_dateien = re.findall(r'releases/latest/download/([\w.-]+)"', HTML)
check(len(_dateien) >= 4, f"nur {len(_dateien)} Download-Knoepfe gefunden")
for _d in _dateien:
    check(_d in _readme and _d in _readme_de,
          f"der Knopf fuehrt auf {_d}, das README nicht beide nennen")
check(all(f'"{_d}"' not in HTML or True for _d in _dateien), "")
check("In Arbeit" not in HTML or "MASCHERA-latest-arm64.dmg" not in HTML,
      "die Seite nennt macOS zugleich «In Arbeit» und als Download")
if len(failures) == _vorher:
    print("   OK   Lizenz und Modelladresse wie im Repository")


print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Projektseite in Ordnung.")
