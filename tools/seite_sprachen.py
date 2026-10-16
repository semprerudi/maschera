#!/usr/bin/env python3
"""Die Sprachseiten der Projektseite: site/fr/, site/it/, site/en/.

    mpy tools/seite_sprachen.py            erzeugen (und den FAQ-Block der
                                           deutschen Seite nachfuehren)
    mpy tools/seite_sprachen.py --pruefen  nur vergleichen; 1, wenn veraltet

Seit 12.10.2026. Vorher setzte `sprachen.js` die Texte erst im Browser: eine
Adresse, vier Sprachen. Eine Suchmaschine sah davon eine einzige — und
welche, entschied die Browsersprache ihres Crawlers. Jetzt hat jede Sprache
ihre eigene Seite mit eigenem Titel, eigener Beschreibung und hreflang.

Es bleibt EINE Quelle: Deutsch steht in `site/index.html`, fr/it/en stehen
in `sprachen.js` (`T`, `titel`, `beschreibung`). Die Sprachseiten sind
Erzeugnisse und werden nie von Hand bearbeitet; `tests/test_webseite.py`
schlaegt an, wenn sie nicht mehr zur Quelle passen.

`T` liest Node aus `sprachen.js` (die Datei ist JavaScript, kein JSON). Das
HTML geht durch den Parser der Standardbibliothek: jedes Element mit
`data-i18n` bekommt seinen Text, mit `data-i18n-html` sein HTML, mit
`data-i18n-attr` sein Attribut — dieselben drei Regeln, die vorher
`sprachen.js` im Browser anwandte.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SITE = WURZEL / "site"
HAUPT = "https://www.maschera.ch/"
SPRACHEN = ("fr", "it", "en")
LOCALE = {"de": "de_CH", "fr": "fr_CH", "it": "it_CH", "en": "en_GB"}
LEER = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
# Die Fragen und Antworten, die als FAQPage in die strukturierten Daten
# gehen — dieselben Schluessel, die der Abschnitt «Fragen» sichtbar zeigt.
FRAGEN = [(f"faq.f{i}", f"faq.a{i}") for i in range(1, 8)]
FAQ_AUF, FAQ_ZU = "<!-- faq-ld -->", "<!-- /faq-ld -->"


def texte_lesen() -> dict:
    """`T`, `titel` und `beschreibung` aus sprachen.js, per Node ausgewertet."""
    js = (SITE / "sprachen.js").read_text(encoding="utf-8")
    anfang, ende = js.index("var T = "), js.index("\n  var hier = ")
    code = js[anfang:ende]
    skript = ("const vm=require('vm');let c='';process.stdin.on('data',d=>c+=d)"
              ".on('end',()=>{const r=vm.runInNewContext(c+"
              "'\\n;({T:T,titel:titel,beschreibung:beschreibung})');"
              "process.stdout.write(JSON.stringify(r));});")
    aus = subprocess.run(["node", "-e", skript], input=code, text=True,
                         capture_output=True)
    if aus.returncode:
        raise SystemExit(f"sprachen.js laesst sich nicht auswerten:\n{aus.stderr}")
    return json.loads(aus.stdout)


def _ist_relativ(url: str) -> bool:
    return not re.match(r"(?:[a-z]+:|//|#|/)", url)


class _Sammler(HTMLParser):
    """Der Text jedes `data-i18n`-Elements — fuer die deutschen Fragen."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.texte: dict[str, str] = {}
        self._schluessel: str | None = None
        self._tiefe = 0

    def handle_starttag(self, tag, attrs):
        if self._schluessel:
            if tag not in LEER:
                self._tiefe += 1
            return
        k = dict(attrs).get("data-i18n")
        if k and tag not in LEER:
            self._schluessel, self._tiefe = k, 1
            self.texte[k] = ""

    def handle_endtag(self, tag):
        if self._schluessel and tag not in LEER:
            self._tiefe -= 1
            if self._tiefe == 0:
                self._schluessel = None

    def handle_data(self, data):
        if self._schluessel:
            self.texte[self._schluessel] += data


class _Uebersetzer(HTMLParser):
    """Schreibt die deutsche Seite in eine andere Sprache um, Zeichen fuer
    Zeichen sonst unveraendert."""

    def __init__(self, sprache: str, t: dict, titel: str, beschr: str) -> None:
        super().__init__(convert_charrefs=False)
        self.sp, self.t, self.titel, self.beschr = sprache, t, titel, beschr
        self.aus: list[str] = []
        self._tiefe = 0          # > 0: Inhalt des Elements wird ersetzt
        self.fehlt: list[str] = []

    # -- Hilfen
    def _attr(self, roh: str, name: str, wert: str) -> str:
        neu, n = re.subn(rf'(\s{re.escape(name)}=")[^"]*(")',
                         lambda m: m.group(1) + html.escape(wert) + m.group(2),
                         roh, count=1)
        return neu if n else roh

    def _umschreiben(self, tag: str, attrs: dict, roh: str) -> str:
        sp = self.sp
        if tag == "html":
            roh = self._attr(roh, "lang", sp)
        if tag == "meta":
            name = attrs.get("name") or attrs.get("property")
            ersatz = {
                "description": self.beschr,
                "og:title": self.titel,
                "og:description": self.beschr,
                "og:url": f"{HAUPT}{sp}/",
                "og:locale": LOCALE[sp],
                "og:image": f"{HAUPT}bilder/{sp}/hero.png",
            }
            if name in ersatz:
                roh = self._attr(roh, "content", ersatz[name])
            elif name == "og:locale:alternate" and attrs.get("content") == LOCALE[sp]:
                roh = self._attr(roh, "content", LOCALE["de"])
        if tag == "link" and attrs.get("rel") == "canonical":
            roh = self._attr(roh, "href", f"{HAUPT}{sp}/")
        if tag == "button" and "data-sprache" in attrs:
            roh = self._attr(roh, "aria-pressed",
                             "true" if attrs["data-sprache"] == sp else "false")
        for a in ("src", "href"):
            url = attrs.get(a)
            if url and _ist_relativ(url):
                url = re.sub(r"^bilder/de/", f"bilder/{sp}/", url)
                roh = self._attr(roh, a, "../" + url)
        regel = attrs.get("data-i18n-attr")
        if regel:
            name, k = regel.split(":", 1)
            if k in self.t:
                roh = self._attr(roh, name, self.t[k])
            else:
                self.fehlt.append(k)
        return roh

    # -- Parser
    def handle_starttag(self, tag, attrs):
        roh = self.get_starttag_text()
        if self._tiefe:
            if tag not in LEER:
                self._tiefe += 1
            return
        a = {k: (v or "") for k, v in attrs}
        self.aus.append(self._umschreiben(tag, a, roh))
        ersatz = None
        if tag == "title":
            ersatz = html.escape(self.titel, quote=False)
        elif "data-i18n" in a:
            k = a["data-i18n"]
            if k in self.t:
                ersatz = html.escape(self.t[k], quote=False)
            else:
                self.fehlt.append(k)
        elif "data-i18n-html" in a:
            k = a["data-i18n-html"]
            if k in self.t:
                ersatz = self.t[k]
            else:
                self.fehlt.append(k)
        if ersatz is not None and tag not in LEER:
            self.aus.append(ersatz)
            self._tiefe = 1

    def handle_startendtag(self, tag, attrs):
        if self._tiefe:
            return
        a = {k: (v or "") for k, v in attrs}
        self.aus.append(self._umschreiben(tag, a, self.get_starttag_text()))

    def handle_endtag(self, tag):
        if self._tiefe:
            if tag in LEER:
                return
            self._tiefe -= 1
            if self._tiefe:
                return
            # das Ende des ersetzten Elements selbst: es bleibt stehen
        self.aus.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._tiefe:
            self.aus.append(data)

    def handle_entityref(self, name):
        if not self._tiefe:
            self.aus.append(f"&{name};")

    def handle_charref(self, name):
        if not self._tiefe:
            self.aus.append(f"&#{name};")

    def handle_comment(self, data):
        if not self._tiefe:
            self.aus.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.aus.append(f"<!{decl}>")


def faq_block(sprache: str, texte: dict) -> str:
    """FAQPage als JSON-LD — `<` maskiert, damit nichts das Skript schliesst."""
    daten = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": sprache,
        "mainEntity": [
            {"@type": "Question", "name": texte[f],
             "acceptedAnswer": {"@type": "Answer", "text": texte[a]}}
            for f, a in FRAGEN
        ],
    }
    roh = json.dumps(daten, ensure_ascii=False, indent=1).replace("<", "\\u003c")
    return f'{FAQ_AUF}\n<script type="application/ld+json">\n{roh}\n</script>\n{FAQ_ZU}'


def _faq_einsetzen(seite: str, block: str) -> str:
    muster = re.compile(re.escape(FAQ_AUF) + r".*?" + re.escape(FAQ_ZU), re.S)
    if not muster.search(seite):
        raise SystemExit(f"{FAQ_AUF} … {FAQ_ZU} fehlt in site/index.html")
    return muster.sub(lambda _: block, seite, count=1)


def erzeuge() -> dict[Path, str]:
    """{Pfad: Inhalt} fuer die deutsche Seite und die drei Sprachseiten."""
    quelle = (SITE / "index.html").read_text(encoding="utf-8")
    daten = texte_lesen()
    sammler = _Sammler()
    sammler.feed(quelle)
    deutsch = sammler.texte
    fehlend = [k for f in FRAGEN for k in f if k not in deutsch]
    if fehlend:
        raise SystemExit(f"site/index.html: Fragen fehlen: {fehlend}")
    ergebnis = {SITE / "index.html": _faq_einsetzen(quelle, faq_block("de", deutsch))}
    for sp in SPRACHEN:
        t = daten["T"][sp]
        u = _Uebersetzer(sp, t, daten["titel"][sp], daten["beschreibung"][sp])
        u.feed(quelle)
        u.close()
        if u.fehlt:
            raise SystemExit(f"{sp}: Schluessel fehlen: {sorted(set(u.fehlt))}")
        seite = "".join(u.aus)
        texte = {k: html.unescape(re.sub(r"<[^>]+>", "", t[k]))
                 for f in FRAGEN for k in f}
        ergebnis[SITE / sp / "index.html"] = _faq_einsetzen(seite, faq_block(sp, texte))
    return ergebnis


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pruefen", action="store_true",
                    help="nichts schreiben; 1, wenn eine Seite veraltet ist")
    args = ap.parse_args()
    veraltet = []
    for pfad, inhalt in erzeuge().items():
        alt = pfad.read_text(encoding="utf-8") if pfad.is_file() else None
        if alt == inhalt:
            continue
        veraltet.append(pfad.relative_to(WURZEL))
        if not args.pruefen:
            pfad.parent.mkdir(parents=True, exist_ok=True)
            pfad.write_text(inhalt, encoding="utf-8")
    for p in veraltet:
        print(("veraltet: " if args.pruefen else "geschrieben: ") + str(p))
    if not veraltet:
        print("Sprachseiten aktuell.")
    return 1 if (args.pruefen and veraltet) else 0


if __name__ == "__main__":
    sys.exit(main())
