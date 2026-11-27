"""Versionshinweise fuer das Burgermenue fuehren.

Die App zeigt unter «Versionshinweise» denselben Text wie die Releases auf
GitHub. Er reist in `app/static/versionshinweise.json` mit dem Paket; die App
holt nichts von aussen.

Quellen: `tools/paket/RELEASE-NOTES.md` (oben Englisch, nach
`<!-- UNTEN -->` und `---` Deutsch; das ist der Text auf GitHub) und fuer die
App allein `RELEASE-NOTES.fr.md` und `RELEASE-NOTES.it.md` (je ein Kopf
`# MASCHERA X.Y.Z`, darunter der Text). Alle drei tragen nur die aktuelle
Fassung und werden bei jedem Release ueberschrieben. Deshalb sammelt dieses
Werkzeug: vor jedem Release einmal aufrufen, es setzt die Fassung aus der
Datei ein oder ersetzt sie.

    mpy tools/versionshinweise.py                 aktuelle Fassung uebernehmen
    mpy tools/versionshinweise.py --aus ORDNER    Releasetexte vX.Y.Z.md einlesen
    mpy tools/versionshinweise.py --pruefen X.Y.Z Abbruch, wenn sie fehlt

Was nur auf GitHub einen Sinn hat, faellt weg: Downloads, Lizenz, «Fehler
gefunden?», Tabellen, Codebloecke, Pruefsummen und der Verweis auf das
CHANGELOG.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "tools" / "paket" / "RELEASE-NOTES.md"
# Nur fuer die App: GitHub zeigt Englisch und Deutsch.
UEBERSETZT = {s: WURZEL / "tools" / "paket" / f"RELEASE-NOTES.{s}.md"
              for s in ("fr", "it")}
SPRACHEN = ("de", "fr", "it", "en")
ZIEL = WURZEL / "app" / "static" / "versionshinweise.json"

KOPF = re.compile(r"^# MASCHERA (\d+\.\d+\.\d+)\s*$")
# Abschnitte, die nur auf der Release-Seite einen Sinn haben.
WEG_ABSCHNITTE = ("downloads", "licence", "license", "found a problem?")
# Absaetze mit diesen Stellen sind Hinweise zum Herunterladen oder Melden.
WEG_ABSATZ = ("SHA256SUMS", "LIZENZ.md", "/issues", "CHANGELOG.md",
              "Website:", "Webseite:")


def _absaetze(text: str) -> list[str]:
    return [a for a in re.split(r"\n\s*\n", text.strip()) if a.strip()]


def saeubern(teil: str) -> str:
    """Einen Sprachteil ohne Titel und ohne Release-Beiwerk."""
    zeilen = teil.strip().splitlines()
    if zeilen and KOPF.match(zeilen[0]):
        zeilen = zeilen[1:]
    # Codebloecke zuerst, sie koennen Leerzeilen tragen.
    ohne_code, im_code = [], False
    for z in zeilen:
        if z.strip().startswith("```"):
            im_code = not im_code
            continue
        if not im_code:
            ohne_code.append(z)
    raus, weg = [], False
    for a in _absaetze("\n".join(ohne_code)):
        erste = a.lstrip().splitlines()[0]
        if erste.startswith("## "):
            weg = erste[3:].strip().lower() in WEG_ABSCHNITTE
            if weg:
                continue
        elif weg:
            continue
        if a.lstrip().startswith("|"):
            continue
        if any(s in a for s in WEG_ABSATZ):
            continue
        raus.append(a.rstrip())
    # Ein Abschnittstitel ohne Inhalt bleibt nicht stehen.
    while raus and raus[-1].lstrip().startswith("## "):
        raus.pop()
    return "\n\n".join(raus)


def zerlegen(text: str) -> tuple[str, str, str]:
    """(fassung, en, de) aus einem Releasetext oder RELEASE-NOTES.md."""
    text = text.replace("\r\n", "\n").replace("<!-- UNTEN -->", "")
    koepfe = [m for m in re.finditer(r"^# MASCHERA (\d+\.\d+\.\d+)\s*$",
                                     text, re.M)]
    if len(koepfe) != 2:
        raise ValueError(f"zwei Koepfe «# MASCHERA X.Y.Z» erwartet, "
                         f"gefunden {len(koepfe)}")
    fassung = koepfe[0].group(1)
    if koepfe[1].group(1) != fassung:
        raise ValueError(f"Englisch {fassung}, Deutsch {koepfe[1].group(1)}")
    en = text[koepfe[0].start():koepfe[1].start()]
    en = re.sub(r"\n---\s*$", "", en.rstrip())
    de = text[koepfe[1].start():]
    return fassung, saeubern(en), saeubern(de)


def einsprachig(text: str, fassung: str) -> str:
    """Eine Uebersetzung: Kopf muss zur Fassung passen."""
    zeilen = text.replace("\r\n", "\n").strip().splitlines()
    m = KOPF.match(zeilen[0]) if zeilen else None
    if not m or m.group(1) != fassung:
        raise ValueError(f"Kopf «# MASCHERA {fassung}» erwartet, "
                         f"gefunden «{zeilen[0] if zeilen else ''}»")
    return saeubern("\n".join(zeilen))


def _schluessel(f: str) -> tuple[int, ...]:
    return tuple(int(x) for x in f.split("."))


def lesen() -> list[dict]:
    if not ZIEL.exists():
        return []
    return json.loads(ZIEL.read_text(encoding="utf-8"))["fassungen"]


def schreiben(fassungen: list[dict]) -> None:
    fassungen = sorted(fassungen, key=lambda e: _schluessel(e["fassung"]),
                       reverse=True)
    daten = {
        "_kommentar": [
            "Versionshinweise fuer das Burgermenue, neueste zuerst.",
            "Gefuehrt von tools/versionshinweise.py aus den Releasetexten,",
            "nicht von Hand. Markdown in einer kleinen Teilmenge:",
            "## Titel, - Aufzaehlung, **fett**, `code`, [Text](Adresse).",
        ],
        "fassungen": fassungen,
    }
    ZIEL.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")


def einsetzen(fassungen: list[dict], neu: dict) -> list[dict]:
    alt = {e["fassung"]: e for e in fassungen}
    # Das Datum bleibt beim ersten Eintrag: ein zweiter Lauf vor dem
    # Release aendert den Text, nicht den Tag.
    if neu["fassung"] in alt and "datum" in alt[neu["fassung"]]:
        neu["datum"] = alt[neu["fassung"]]["datum"]
    alt[neu["fassung"]] = neu
    return list(alt.values())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--aus", type=Path,
                   help="Ordner mit Releasetexten vX.Y.Z.md (einmalig)")
    p.add_argument("--pruefen", metavar="FASSUNG",
                   help="nur pruefen, ob diese Fassung eingetragen ist")
    a = p.parse_args()

    if a.pruefen:
        e = next((e for e in lesen() if e["fassung"] == a.pruefen), None)
        fehlt = [s for s in SPRACHEN if not (e or {}).get(s)]
        if fehlt:
            print(f"versionshinweise.json: {a.pruefen} fehlt in "
                  f"{', '.join(fehlt)}. RELEASE-NOTES(.fr/.it).md nachfuehren, "
                  f"dann: mpy tools/versionshinweise.py", file=sys.stderr)
        return 1 if fehlt else 0

    fassungen = lesen()
    if a.aus:
        # Einmalig: Releasetexte von GitHub (nur en und de).
        for datei in sorted(a.aus.glob("v*.md")):
            f, en, de = zerlegen(datei.read_text(encoding="utf-8"))
            fassungen = einsetzen(fassungen, {"fassung": f, "en": en, "de": de})
            print(f"  {f}")
    else:
        f, en, de = zerlegen(QUELLE.read_text(encoding="utf-8"))
        neu = {"fassung": f, "datum": dt.date.today().isoformat(), "de": de}
        for s, datei in UEBERSETZT.items():
            neu[s] = einsprachig(datei.read_text(encoding="utf-8"), f)
        neu["en"] = en
        fassungen = einsetzen(fassungen, neu)
        print(f"  {f} uebernommen")
    schreiben(fassungen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
