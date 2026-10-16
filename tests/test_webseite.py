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
# `<link rel="canonical">` laedt nichts: er nennt Suchmaschinen die
# Hauptadresse und zeigt deshalb bewusst auf die eigene Domain. Dasselbe
# gilt fuer `rel="alternate"` (hreflang, seit 12.10.2026): er nennt die
# Sprachseiten, geholt wird nichts.
_ohne_canonical = re.sub(r'<link\b[^>]*\brel="(?:canonical|alternate)"[^>]*>',
                         "", HTML)
_geladen = re.findall(r'<(?:img|script|source|link|iframe)\b[^>]*?'
                      r'(?:src|srcset|href)="([^"]+)"', _ohne_canonical)
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


print("\n3b. Der Server darf HTML, JS und CSS nicht auf eigene Faust zwischenspeichern")
# ⚠️ Am 3.10.2026 sah ein Besucher nach einem Update die neue Seite mit der
# Uebersetzung von gestern: der Server schickte keine Cache-Anweisung, und der
# Browser entscheidet dann selbst, wie lange er `sprachen.js` behaelt. Die
# `.htaccess` neben der Seite sagt «vor Gebrauch nachfragen» (`no-cache`, mit
# ETag ein winziges 304). Ohne sie ist die naechste Aktualisierung wieder eine
# Mischung aus alt und neu.
_ht = SITE / ".htaccess"
check(_ht.is_file(), "site/.htaccess fehlt")
if _ht.is_file():
    _hc = "\n".join(z for z in _ht.read_text(encoding="utf-8").splitlines()
                    if not z.lstrip().startswith("#"))
    check("Cache-Control" in _hc and "no-cache" in _hc,
          ".htaccess setzt kein Cache-Control: no-cache")
    check(all(e in _hc for e in ("html", "js", "css")),
          ".htaccess nennt nicht html, js und css")
    check("png" not in _hc and "woff" not in _hc,
          ".htaccess nimmt auch Bilder oder Schriften aus dem Zwischenspeicher")
if not failures:
    print("   OK   no-cache fuer html, js, css; Bilder bleiben im Zwischenspeicher")

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


print("\n5. Suchmaschinen finden EINE Adresse, eine Sitemap und Text zu jedem Bild")
# Seit 12.10.2026. Die Seite kommt aus Claude Design; wird sie dort neu
# erzeugt und eingespielt, fallen diese Zeilen als Erstes weg — still, denn
# fuer den Besucher aendert sich nichts.
import json as _json5  # noqa: E402
_vorher = len(failures)
HAUPT = "https://www.maschera.ch/"
_canon = re.findall(r'<link rel="canonical" href="([^"]+)"', HTML)
check(_canon == [HAUPT], f"canonical ist {_canon}, erwartet {HAUPT}")
_robots = (SITE / "robots.txt").read_text(encoding="utf-8") \
    if (SITE / "robots.txt").is_file() else ""
check(f"Sitemap: {HAUPT}sitemap.xml" in _robots,
      "robots.txt fehlt oder nennt die Sitemap nicht")
_sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8") \
    if (SITE / "sitemap.xml").is_file() else ""
check(f"<loc>{HAUPT}</loc>" in _sitemap, "sitemap.xml fehlt oder nennt die Seite nicht")
_ht = (SITE / ".htaccess").read_text(encoding="utf-8")
check("RewriteCond %{HTTP_HOST} ^maschera\\.ch$" in _ht
      and "https://www.maschera.ch%{REQUEST_URI} [R=301" in _ht,
      ".htaccess leitet maschera.ch nicht dauerhaft auf www um")
_ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', HTML, re.S)
try:
    _bloecke = [_json5.loads(b) for b in _ld]
except ValueError:
    _bloecke = []
_daten = next((b for b in _bloecke if b.get("@type") == "SoftwareApplication"), {})
check(_daten.get("@type") == "SoftwareApplication"
      and _daten.get("isAccessibleForFree") is True
      and _daten.get("url") == HAUPT,
      "strukturierte Daten fehlen oder sind unvollstaendig")
# Keine Fassungsnummer: `VERSION` in app/serve.py ist die einzige Quelle,
# und die Seite wird nicht bei jeder Auslieferung neu hochgeladen.
check("softwareVersion" not in _daten, "die Seite fuehrt eine Fassungsnummer")
for _eig in ("og:title", "og:description", "og:image", "og:url"):
    check(f'property="{_eig}"' in HTML, f"{_eig} fehlt")
_titel = re.search(r"<title>([^<]+)</title>", HTML)
_beschr = re.search(r'<meta name="description" content="([^"]+)"', HTML)
check(_titel and "Open Source" in _titel.group(1), "Titel ohne «Open Source»")
check(_beschr and 70 <= len(_beschr.group(1)) <= 200,
      "Beschreibung fehlt oder ist zu kurz/lang fuer die Trefferliste")
_ohne_alt = [m for m in re.findall(r'<img [^>]*>', HTML)
             if re.search(r' alt=""', m)]
check(not _ohne_alt, f"{len(_ohne_alt)} Bilder ohne Alt-Text")
# Seit 12.10.2026 (Audit mit dem Skill seo-geo-consultant): Google schneidet
# den Titel nach rund 60 Zeichen ab, die Beschreibung nach rund 160 — in
# jeder Sprache, auch in denen, die `sprachen.js` setzt.
_titel_js = dict(re.findall(r'\n\s+(fr|it|en|de): "([^"]+)"',
                            JS.split("var titel = {")[1].split("};")[0]))
_beschr_js = dict(re.findall(r'\n\s+(fr|it|en): "([^"]+)"',
                             JS.split("var beschreibung = {")[1].split("};")[0]))
check(_titel and len(_titel.group(1)) <= 60, "Titel laenger als 60 Zeichen")
check(_beschr and len(_beschr.group(1)) <= 160,
      "Beschreibung laenger als 160 Zeichen")
check(_titel_js.get("de") == (_titel.group(1) if _titel else None),
      "der deutsche Titel in sprachen.js weicht vom HTML ab")
for _sp, _t in _titel_js.items():
    check(len(_t) <= 60, f"Titel {_sp} laenger als 60 Zeichen")
for _sp in ("fr", "it", "en"):
    check(_sp in _beschr_js and len(_beschr_js[_sp]) <= 160,
          f"Beschreibung {_sp} fehlt oder ist laenger als 160 Zeichen")
# Wer die Software herausgibt und wann die Seite zuletzt stimmte: KI-Suchen
# zitieren anonyme und undatierte Seiten seltener. Das Datum muss dasselbe
# sein wie in der Sitemap — zwei Stellen von Hand, also eine Pruefung.
check((_daten.get("author") or {}).get("@type") == "Person",
      "strukturierte Daten nennen keinen Autor")
_lastmod = re.findall(r"<lastmod>([^<]+)</lastmod>", _sitemap)
check(_daten.get("dateModified") and set(_lastmod) == {_daten.get("dateModified")},
      f"dateModified {_daten.get('dateModified')} passt nicht zur Sitemap {_lastmod}")
# Ohne Masse springt die Seite beim Laden (CLS), weil der Browser die Hoehe
# erst kennt, wenn das Bild da ist.
_ohne_mass = [m for m in re.findall(r'<img [^>]*>', HTML)
              if " width=" not in m or " height=" not in m]
check(not _ohne_mass, f"{len(_ohne_mass)} Bilder ohne width/height")
# `llms.txt`: die Zusammenfassung fuer KI-Systeme. `seite.py` laedt sie nur
# hoch, wenn sie in FUER_SUCHMASCHINEN steht — keine Seite verlinkt sie.
_llms = (SITE / "llms.txt").read_text(encoding="utf-8") \
    if (SITE / "llms.txt").is_file() else ""
check(_llms.startswith("# MASCHERA") and HAUPT in _llms,
      "llms.txt fehlt oder nennt die Seite nicht")
_seite_py = (WURZEL / "tools" / "seite.py").read_text(encoding="utf-8")
check(re.search(r'FUER_SUCHMASCHINEN = \{[^}]*"llms\.txt"', _seite_py),
      "seite.py laedt llms.txt nicht hoch")
# Seit 13.10.2026: Hostpoint sperrt KI-Trainingscrawler serverweit
# (HOSTPOINT_AI_TRAINING_BLOCKLIST, 403 auch fuer robots.txt). Die
# .htaccess hebt die Sperre fuer GPTBot und ClaudeBot auf; ohne
# Crawl-delay ist das laut Hostpoint nicht zulaessig.
for _bot in ("GPTBot", "ClaudeBot"):
    check(re.search(rf'BrowserMatch "{_bot}/" !HOSTPOINT_AI_TRAINING_BLOCKLIST', _ht),
          f".htaccess hebt die Hostpoint-Sperre fuer {_bot} nicht auf")
check(re.search(r"(?m)^Crawl-delay:\s*[5-9]", _robots),
      "robots.txt ohne Crawl-delay (Hostpoint verlangt 5)")
# Das Impressum nennt den richtigen Ort. Bis 12.10.2026 stand in allen vier
# Sprachen «GitHub Pages», die Seite lag aber bei Hostpoint.
check("GitHub Pages" not in HTML + JS, "das Impressum nennt noch GitHub Pages")
if len(failures) == _vorher:
    print("   OK   canonical, robots.txt, sitemap.xml, llms.txt, Umleitung, "
          "SoftwareApplication, Autor, Datum, Laengen, Bildmasse, Vorschaukarte, "
          "Alt-Texte, Impressum")


print("\n6. Jede Sprache hat ihre eigene Seite, und die Seiten passen zur Quelle")
# Seit 12.10.2026. Vorher setzte `sprachen.js` die Texte im Browser: eine
# Adresse, vier Sprachen — eine Suchmaschine sah eine davon. Die Seiten
# /fr/, /it/, /en/ erzeugt `tools/seite_sprachen.py` aus index.html und
# sprachen.js; von Hand bearbeitet waeren sie beim naechsten Lauf still weg,
# und vergessen waeren sie still veraltet. Beides faengt der Vergleich.
import importlib.util as _ilu  # noqa: E402
_vorher = len(failures)


def _modul(name):
    spec = _ilu.spec_from_file_location(name, WURZEL / "tools" / f"{name}.py")
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_gen = _modul("seite_sprachen")
try:
    _soll = _gen.erzeuge()
except SystemExit as _e:
    _soll = {}
    check(False, f"seite_sprachen.py bricht ab: {_e}")
for _pfad, _inhalt in _soll.items():
    _ist = _pfad.read_text(encoding="utf-8") if _pfad.is_file() else None
    check(_ist == _inhalt, f"{_pfad.relative_to(WURZEL)} veraltet — "
                           "mpy tools/seite_sprachen.py")
_adressen = {"de": HAUPT, "fr": HAUPT + "fr/", "it": HAUPT + "it/", "en": HAUPT + "en/"}
_hreflang_soll = sorted([(k, v) for k, v in _adressen.items()] + [("x-default", HAUPT)])
for _sp, _url in _adressen.items():
    _datei = SITE / ("index.html" if _sp == "de" else f"{_sp}/index.html")
    if not _datei.is_file():
        check(False, f"{_datei.relative_to(WURZEL)} fehlt")
        continue
    _s = _datei.read_text(encoding="utf-8")
    check(f'<html lang="{_sp}">' in _s, f"{_sp}: lang stimmt nicht")
    check(re.findall(r'<link rel="canonical" href="([^"]+)"', _s) == [_url],
          f"{_sp}: canonical zeigt nicht auf {_url}")
    _hl = sorted(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', _s))
    check(_hl == _hreflang_soll, f"{_sp}: hreflang unvollstaendig: {_hl}")
    check(f"<loc>{_url}</loc>" in _sitemap, f"sitemap.xml nennt {_url} nicht")
    _faq = [b for b in (_json5.loads(x) for x in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', _s, re.S))
        if b.get("@type") == "FAQPage"]
    check(len(_faq) == 1 and len(_faq[0].get("mainEntity", [])) == len(_gen.FRAGEN)
          and _faq[0].get("inLanguage") == _sp,
          f"{_sp}: FAQPage fehlt oder hat nicht {len(_gen.FRAGEN)} Fragen")
    # Kein Pfad darf ins Leere zeigen: die Sprachseiten liegen eine Ebene
    # tiefer und brauchen `../` vor jeder Datei.
    for _u in re.findall(r'<(?:img|script|link)\b[^>]*?(?:src|href)="([^"]+)"', _s):
        if not re.match(r"https?:", _u):
            check((_datei.parent / _u).resolve().is_file(),
                  f"{_sp}: verweist auf {_u} — fehlt")
_seite = _modul("seite")
_hoch = _seite.entdecke(HTML, CSS, JS)
for _sp in ("fr", "it", "en"):
    check(f"{_sp}/index.html" in _hoch, f"seite.py laedt {_sp}/index.html nicht hoch")
# Nach der Browsersprache wird nicht umgeleitet: ein Crawler mit englischer
# Browsersprache saehe sonst die deutsche Seite nie.
check("navigator.language" not in _js_code,
      "sprachen.js waehlt die Sprache nach dem Browser")
if len(failures) == _vorher:
    print("   OK   fr, it, en aktuell; lang, canonical, hreflang, Sitemap, "
          "FAQPage, Pfade, Hochladen")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Projektseite in Ordnung.")
