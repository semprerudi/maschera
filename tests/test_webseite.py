"""Die Projektseite unter `site/` — vollstaendig, in vier Sprachen, ohne Nachladen.

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


print("\n2. Jede geladene Datei liegt da, jedes Bild in hell UND dunkel")
_vorher = len(failures)
for _u in _geladen:
    check((SITE / _u).is_file(), f"index.html verweist auf {_u} — fehlt")
for _u in re.findall(r'url\("([^"]+)"\)', CSS):
    check((SITE / _u).is_file(), f"stil.css verweist auf {_u} — fehlt")
_hell = set(re.findall(r'src="bilder/hell/([^"]+)"', HTML))
_dunkel = set(re.findall(r'srcset="bilder/dunkel/([^"]+)"', HTML))
check(_hell, "keine Bildschirmfotos unter bilder/hell/ verwendet")
check(_hell == _dunkel,
      f"hell und dunkel ungleich: nur hell {sorted(_hell - _dunkel)}, "
      f"nur dunkel {sorted(_dunkel - _hell)}")
for _b in sorted(_hell):
    for _art in ("hell", "dunkel"):
        check((SITE / "bilder" / _art / _b).is_file(),
              f"bilder/{_art}/{_b} fehlt")
if len(failures) == _vorher:
    print(f"   OK   {len(_hell)} Bildschirmfotos in beiden Designs")


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
if len(failures) == _vorher:
    print("   OK   Lizenz und Modelladresse wie im Repository")


print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Projektseite in Ordnung.")
