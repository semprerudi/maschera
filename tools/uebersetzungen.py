#!/usr/bin/env python3
"""Alle Uebersetzungen in EINE Tabelle — zum Lesen und Korrigieren.

    python3 tools/uebersetzungen.py --nach uebersetzungen.csv

Die Saetze stehen in drei Dateien, und jede hat ihren Grund:

    app/static/maschera.js   `I18N` — Beschriftung, Meldungen, Hinweise
    app/fenster.py           `START_SAETZE` — der Startbildschirm, der steht,
                             bevor die Oberflaeche geladen ist; dazu
                             `TRAY_WORTE` und `SPEICHERN_UNTER`
    app/static/seiten.js     Hilfe und Impressum

Die Tabelle ist eine ANSICHT, keine Quelle: korrigiert wird im Code, die
Tabelle wird danach neu erzeugt. Eine Tabelle, aus der zurueckgeschrieben
wuerde, waere ein vierter Verwalter derselben Saetze.

Spalten: Ort, Schluessel, de, fr, it, en. Trennzeichen `;` und eine
Byte-Order-Mark, damit Excel und LibreOffice mit Schweizer Einstellung die
Umlaute und Spalten ohne Nachfrage richtig lesen.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SPRACHEN = ("de", "fr", "it", "en")

# Holt `I18N` aus `maschera.js`, ohne die Datei auszufuehren — sie braucht
# einen Browser. Ausgeschnitten wird der Block von `const I18N = {` bis zur
# ersten Zeile `};` und als Ausdruck ausgewertet.
_NODE = r"""
const fs = require("fs"), vm = require("vm"), path = require("path");
const w = process.argv[1];
const js = fs.readFileSync(path.join(w, "app/static/maschera.js"), "utf8");
const a = js.indexOf("const I18N = {");
const b = js.indexOf("\n};", a);
if (a < 0 || b < 0) { console.error("I18N nicht gefunden"); process.exit(1); }
const i18n = vm.runInNewContext("(" + js.slice(a + "const I18N = ".length, b + 2) + ")");
require(path.join(w, "app/static/seiten.js"));
process.stdout.write(JSON.stringify({ i18n, seiten: globalThis.MASCHERA_SEITEN }));
"""


def flach(wert, vorsatz: str, aus: dict) -> None:
    """Verschachtelte Tabellen zu `a.b.c` — Listen mit ihrer Nummer."""
    if isinstance(wert, dict):
        for k, v in wert.items():
            flach(v, f"{vorsatz}.{k}" if vorsatz else str(k), aus)
    elif isinstance(wert, list):
        for i, v in enumerate(wert):
            flach(v, f"{vorsatz}.{i}", aus)
    elif wert is not None:
        aus[vorsatz] = str(wert)


def stueck(inhalt) -> str:
    """Ein Inhalt der Hilfe zu Text: Stuecke aneinander, Fett als **…**."""
    if isinstance(inhalt, str):
        return inhalt
    if isinstance(inhalt, list) and len(inhalt) == 2 and inhalt[0] == "b":
        return f"**{inhalt[1]}**"
    if isinstance(inhalt, list):
        return "".join(stueck(s) for s in inhalt)
    return str(inhalt)


def seite(bloecke: list) -> dict:
    """Hilfe oder Impressum zu nummerierten Zeilen."""
    aus: dict = {}
    for i, (art, inhalt) in enumerate(bloecke):
        if art in ("h", "p"):
            aus[f"{i:02d}.{art}"] = stueck(inhalt)
        elif art == "ul":
            for j, punkt in enumerate(inhalt):
                aus[f"{i:02d}.ul.{j}"] = stueck(punkt)
        elif art == "tab":
            for j, (links, rechts) in enumerate(inhalt):
                aus[f"{i:02d}.tab.{j}.links"] = stueck(links)
                aus[f"{i:02d}.tab.{j}.rechts"] = stueck(rechts)
        else:
            aus[f"{i:02d}.{art}"] = stueck(inhalt)
    return aus


def zeilen() -> list[list[str]]:
    roh = subprocess.run(["node", "-e", _NODE, str(WURZEL)], check=True,
                         capture_output=True, text=True).stdout
    daten = json.loads(roh)

    tabellen: list[tuple[str, dict]] = []
    # 1. Oberflaeche
    je = {}
    for s in SPRACHEN:
        je[s] = {}
        flach(daten["i18n"][s], "", je[s])
    tabellen.append(("oberflaeche", je))
    # 2. Startbildschirm
    sys.path[:0] = [str(WURZEL), str(WURZEL / "app"), str(WURZEL / "tools")]
    import fenster  # noqa: E402
    je = {}
    for s in SPRACHEN:
        je[s] = {}
        flach(fenster.START_SAETZE[s], "", je[s])
    tabellen.append(("startbildschirm", je))
    # Infobereich und Speicherdialog — je ein kleines Woerterbuch
    tabellen.append(("infobereich", {
        s: {"beenden": fenster.TRAY_WORTE[s][0],
            "fenster_zeigen": fenster.TRAY_WORTE[s][1]} for s in SPRACHEN}))
    tabellen.append(("speicherdialog", {
        s: {"titel": fenster.SPEICHERN_UNTER[s]} for s in SPRACHEN}))
    # 3. Hilfe und Impressum
    for name in ("hilfe", "impressum"):
        tabellen.append((name, {s: seite(daten["seiten"][name][s])
                                for s in SPRACHEN}))

    aus = []
    for ort, je in tabellen:
        # Reihenfolge der deutschen Fassung; was nur anderswo steht, danach
        schluessel = list(je["de"])
        for s in SPRACHEN[1:]:
            schluessel += [k for k in je[s] if k not in schluessel]
        for k in schluessel:
            aus.append([ort, k] + [je[s].get(k, "⚠ FEHLT") for s in SPRACHEN])
    return aus


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nach", required=True, help="Ziel, eine .csv-Datei")
    args = ap.parse_args()
    liste = zeilen()
    with open(args.nach, "w", encoding="utf-8-sig", newline="") as f:
        schreiber = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        schreiber.writerow(["Ort", "Schluessel"] + list(SPRACHEN))
        schreiber.writerows(liste)
    fehlt = sum(1 for z in liste if "⚠ FEHLT" in z)
    print(f"{len(liste)} Zeilen nach {args.nach}"
          + (f" — {fehlt} mit fehlender Sprache" if fehlt else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
