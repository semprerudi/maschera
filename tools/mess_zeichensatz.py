#!/usr/bin/env python3
"""Misst, ob die Kette den amtlichen Zeichensatz traegt.

    python3 tools/mess_zeichensatz.py --proben /tmp/zeichensatz
    python3 tools/filter_document.py --model runs/ch-v63b \\
        --ohne-regeln --ohne-vorlieben --knapp \\
        --bericht /tmp/bericht.json /tmp/zeichensatz
    python3 tools/mess_zeichensatz.py --auswerten /tmp/bericht.json

In Schweizer Personenregistern gilt ISO 8859-1 + Latin Extended-A
(`docs/ZEICHENSATZ.md`). Stufe 2 traegt davon nicht alles: die
Grossbuchstaben aus Latin Extended-A am Wortanfang erkennen die
namentragenden Muster nicht. Die Frage, auf die es ankommt: **faengt
Stufe 3 das auf?** Das Modell erkennt Namen ohne Muster.

**Dieses Werkzeug entscheidet nichts.** Wie `kalibriere_schwellen.py`
zeigt es eine Kurve und schreibt nichts zurueck. `docs/ZEICHENSATZ.md`
verbietet ausdruecklich, die Muster auf Verdacht zu weiten: eine breitere
Zeichenklasse aendert das Messergebnis, und ohne vorherige Messung weiss
niemand in welche Richtung.

**Warum zwei Betriebsarten und nicht eine.** Der mittlere Schritt braucht
das Modell, die beiden aeusseren nicht. Damit laeuft das Werkzeug selbst
auf einer Maschine ohne `runs/` und bleibt dort pruefbar.

**Alle Namen und Nummern sind erfunden.** Die Proben enthalten keine
Personendaten, und der Bericht aus `filter_document.py` traegt ohne
`--klartext` ohnehin nur Tag, Stufe, Position und Vertrauen.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packs.ch.generators.identifiers import gen_ahvn13  # noqa: E402

# Der amtliche Satz laut docs/ZEICHENSATZ.md. Latin Extended-B ist NICHT
# dabei: das rumaenische `ș` (U+0219) liegt ausserhalb, das aehnlich
# aussehende `ş` mit Cedille (U+015F) darin. Wer die beiden verwechselt,
# misst am falschen Zeichen.
BEREICHE = ((0x0020, 0x007E), (0x00A0, 0x00FF), (0x0100, 0x017F))


def grossbuchstaben() -> list[str]:
    """Die Grossbuchstaben des Satzes — dort steht die enge Klasse.

    Im Wortinneren deckt `\\w` den ganzen Unicode ab; eine Messung dort faellt
    fuer jedes Zeichen gleich aus und sagt nichts.
    """
    return [chr(c) for a, b in BEREICHE for c in range(a, b + 1)
            if unicodedata.category(chr(c)) == "Lu"]


def block(z: str) -> str:
    return "Latin-1" if ord(z) < 0x0100 else "LatExt-A"


# Die Zuordnung Probe -> Sollspannen. Siehe `proben_schreiben` zur Endung.
ZUORDNUNG = "_erwartet.mess"


# --- Die Proben -------------------------------------------------------------
#
# Drei Zeilen je Datei, damit die drei Wege im selben Lauf vergleichbar
# sind. `{X}` ist der Anfangsbuchstabe, der durchgetauscht wird.
#
# Der Personenname ist die eigentliche Frage: FULLNAME hat KEIN
# Stufe-2-Muster (ein Muster fuer «Grossbuchstabe, dann Kleinbuchstaben»
# traefe in einem Amtsdokument alles), er haengt allein am Modell.
ZEILEN = (
    ("FULLNAME", "Sehr geehrter Herr {X}under, Ihre Anmeldung ist eingegangen."),
    ("ORG", "Rechnung der {X}trub & Partner GmbH vom 3.4.2025 liegt bei."),
    ("PLACE_OF_ORIGIN", "Heimatort: {X}urgen SG, wohnhaft in Bern."),
)

# Ohne Kontrollgruppe sagt ein Nullergebnis nicht, ob das ZEICHEN schuld
# ist oder der SATZ: ein untauglicher Satz scheitert auch mit schlichtem
# `e`. Die Kontrolle faengt genau das.
KONTROLLE = "M"


def proben_schreiben(ziel: Path) -> int:
    ziel.mkdir(parents=True, exist_ok=True)
    erwartet: list[dict] = []
    zeichen = grossbuchstaben() + [KONTROLLE]

    for z in zeichen:
        ist_kontrolle = z == KONTROLLE
        name = "kontrolle.txt" if ist_kontrolle else f"u{ord(z):04X}.txt"
        text, stellen = "", []
        for tag, vorlage in ZEILEN:
            # ⚠️ Erst die Stelle des Slots suchen, DANN einsetzen. Wer
            # einsetzt und hinterher `zeile.index(z)` fragt, findet das
            # erste Vorkommen im Satz und nicht den Slot: bei `R` ist das
            # «Rechnung», bei `S` das «Sehr». Die Sollspanne zeigt dann auf
            # ein festes Wort, und die Messung misst den Satz statt das
            # Zeichen. Aufgefallen im Trockenlauf, weil ORG bei genau einem
            # Latin-1-Zeichen durchfiel — bei `R`.
            i = vorlage.index("{X}")
            zeile = vorlage.replace("{X}", z)
            j = i
            while j < len(zeile) and not zeile[j].isspace() \
                    and zeile[j] not in ",.":
                j += 1
            stellen.append({"tag": tag,
                            "start": len(text) + i,
                            "end": len(text) + j})
            text += zeile + "\n"
        (ziel / name).write_text(text, encoding="utf-8")
        erwartet.append({
            "datei": name,
            "zeichen": z,
            "block": "Kontrolle" if ist_kontrolle else block(z),
            "spannen": stellen,
        })

    erwartet.extend(kennzahlproben_schreiben(ziel))
    # ⚠️ Endung `.mess` und NICHT `.json`. `tools/dokumente.py` fuehrt
    # `.json` — und `""` — in `TEXTENDUNGEN`: die Zuordnungsdatei wurde im
    # ersten echten Lauf selbst durch die Kette geschickt. 38 419 Zeichen,
    # 924 Fundstellen, Modellzeit fuer nichts, und die Zeile «Tags
    # insgesamt» zaehlte sie mit. Ein Werkzeug, das seine eigene
    # Buchhaltung als Messgegenstand einliest, misst sich selbst.
    (ziel / ZUORDNUNG).write_text(
        json.dumps(erwartet, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(erwartet)


# --- Die Kennzahlproben -----------------------------------------------------
#
# INSURANCE_CARD traegt das Muster `(?<!\d)80756\d{15}(?!\d)` und trifft
# damit NUR die ungetrennte Form. Auf der Versichertenkarte steht die
# Nummer gruppiert.
#
# Die Bindestrichform ist schlechter als ein Fehlschlag: sie erzeugt zwei
# CASE_ID-Spannen und sieht damit nach Erkennung aus. Ein falscher Treffer
# ist teurer als keiner, weil niemand nachsieht.
#
# AHVN13 im selben Bestand kann `[.\s]?` — dieselbe Sachfrage, zwei
# Antworten. Deshalb wird AHVN13 mitgemessen: als Vergleich, wie breit eine
# Kennnummer sein kann, ohne unsicher zu werden.
#
# Alle Nummern erfunden. Wo eine Pruefsumme gilt, kommt sie aus dem
# vorhandenen Generator — sonst scheitert Stufe 1 an einer ungueltigen
# Ziffer, und die Messung misst den Generator statt das Muster.
def _schreibweisen(ziffern: str, gruppen: tuple[int, ...]) -> dict[str, str]:
    """Dieselbe Ziffernfolge in den ueblichen Schreibweisen."""
    teile, i = [], 0
    for g in gruppen:
        teile.append(ziffern[i:i + g])
        i += g
    if i < len(ziffern):
        teile.append(ziffern[i:])
    return {
        "ungetrennt": ziffern,
        "leerzeichen": " ".join(teile),
        "punkt": ".".join(teile),
        "bindestrich": "-".join(teile),
        "apostroph": "’".join(teile),
    }


def kennzahlproben_schreiben(ziel: Path) -> list[dict]:
    # Fester Keim. `gen_ahvn13()` ohne rng zieht aus dem globalen Zufall — die
    # AHV-Nummer waere in jedem Probenlauf eine andere, und ein Vergleich zweier
    # Modelle verglich zwei verschiedene Nummern. Ein Rueckschritt der Probe
    # saehe dann aus wie ein Rueckschritt des Modells.
    ahv = gen_ahvn13(random.Random(2026), formatted=False)
    faelle = {
        "INSURANCE_CARD": ("Versichertenkarte Nr. {W} der Krankenkasse.",
                           _schreibweisen("80756" + "0155551234567890"[:15],
                                          (5, 4, 4, 4))),
        "AHVN13": ("Versichertennummer {W} im Dossier.",
                   _schreibweisen(ahv, (3, 4, 4))),
        "ZSR_RCC": ("ZSR-Nummer {W} der Praxis.",
                    {"ungetrennt": "L123456", "mit punkt": "L.123456"}),
        "PATIENT_ID": ("Patienten-Nr. {W} im Bericht.",
                       {"ungetrennt": "4711202699",
                        "bindestrich": "4711-2026",
                        "schraegstrich": "4711/2026"}),
    }
    erwartet = []
    for tag, (vorlage, formen) in faelle.items():
        for art, wert in formen.items():
            marke = art.replace(" ", "_")
            name = f"kz_{tag}_{marke}.txt"
            i = vorlage.index("{W}")
            zeile = vorlage.replace("{W}", wert)
            (ziel / name).write_text(zeile + "\n", encoding="utf-8")
            erwartet.append({
                "datei": name, "zeichen": None, "block": "Kennzahl",
                "kennzahl": {"tag": tag, "schreibweise": art},
                "spannen": [{"tag": tag, "start": i, "end": i + len(wert)}],
            })
    return erwartet


# --- Die Auswertung ---------------------------------------------------------
def _deckt(f: dict, soll: dict) -> bool:
    """Deckt eine Fundstelle die Sollspanne ganz?

    Bewusst grosszuegig bei den Raendern: eine Spanne, die den Namen
    mitsamt Anrede greift, ist erkannt.
    """
    return f["start"] <= soll["start"] and f["end"] >= soll["end"]


def _beruehrt(f: dict, soll: dict) -> bool:
    """Ueberlappt eine Fundstelle die Sollspanne ueberhaupt?"""
    return f["start"] < soll["end"] and f["end"] > soll["start"]


# Drei Ausgaenge und nicht zwei. «Nicht unter dem richtigen Tag gefunden»
# wirft zwei sehr verschiedene Faelle zusammen:
#
#   richtig           die Spanne ist da, unter dem erwarteten Tag
#   falsches Etikett  sie ist MASKIERT, aber unter einem anderen Tag.
#                     Kein Leck. Der Klartext ist weg, das Woerterbuch
#                     fuehrt ihn nur unter falschem Namen
#   LECK              nichts deckt die Stelle. Der Wert steht im Klartext
#
# Wer nur tagtreu zaehlt, meldet ein Vielfaches der echten Lecks.
def _urteil(fundstellen: list[dict], soll: dict) -> str:
    if any(f["tag"] == soll["tag"] and _deckt(f, soll) for f in fundstellen):
        return "richtig"
    if any(_beruehrt(f, soll) for f in fundstellen):
        return "etikett"
    return "leck"


def auswerten(bericht_pfad: Path) -> int:
    bericht = json.loads(bericht_pfad.read_text(encoding="utf-8"))
    proben_ordner = bericht_pfad.parent
    erwartet_datei = None
    # `_erwartet.json` bleibt als zweiter Kandidat: Berichte aus Laeufen vor
    # der Umbenennung sollen weiter auswertbar sein.
    for kandidat in (proben_ordner / ZUORDNUNG,
                     proben_ordner / "_erwartet.json"):
        if kandidat.is_file():
            erwartet_datei = kandidat
            break
    if erwartet_datei is None:
        print("FEHLER  `_erwartet.json` nicht gefunden.", file=sys.stderr)
        print(f"        `{ZUORDNUNG}` liegt im Probenordner aus `--proben`.",
              file=sys.stderr)
        print("        Entweder dorthin berichten lassen oder die Datei "
              "neben den Bericht legen.", file=sys.stderr)
        return 2

    erwartet = {e["datei"]: e
                for e in json.loads(erwartet_datei.read_text(encoding="utf-8"))}
    funde = {d["kennung"]: d.get("fundstellen", [])
             for d in bericht.get("dokumente", [])}

    fehlend = set(erwartet) - set(funde)
    if fehlend:
        print(f"⚠️  {len(fehlend)} Probe(n) fehlen im Bericht — "
              f"die Messung ist unvollstaendig.")
        for f in sorted(fehlend)[:5]:
            print(f"    {f}")
        print()

    # --- Zeichensatz ---
    tabelle: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"richtig": 0, "etikett": 0, "leck": 0})
    ersatz: dict[tuple[str, str], Counter] = defaultdict(Counter)
    # ⚠️ `quelle` und NICHT `stufe`. Das Feld `stufe` im Bericht traegt die
    # im Vertrag DEKLARIERTE Stufe des Tags, nicht die, die den Treffer
    # gefunden hat: `ORG` steht als Stufe 3 in der Taxonomie und wird vom
    # Stufe-2-Muster `ORG_FIRMA` erkannt. Wer `stufe` auswertet, liest
    # «Stufe 3» und meint, das Modell habe geliefert. Genau darum geht es
    # in dieser Messung — die Spalte waere die falsche Antwort auf die
    # einzige Frage, die offen ist.
    quellen: dict[tuple[str, str], set[str]] = defaultdict(set)
    kontrolle: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for datei, e in erwartet.items():
        if e["block"] == "Kennzahl" or datei not in funde:
            continue
        for soll in e["spannen"]:
            treffer = [f for f in funde[datei]
                       if f["tag"] == soll["tag"] and _deckt(f, soll)]
            ziel = kontrolle if e["block"] == "Kontrolle" else None
            if ziel is not None:
                ziel[soll["tag"]][1] += 1
                ziel[soll["tag"]][0] += bool(treffer)
                continue
            schl = (e["block"], soll["tag"])
            urteil = _urteil(funde[datei], soll)
            tabelle[schl][urteil] += 1
            if urteil == "richtig":
                quellen[schl].update(f.get("quelle", "?") for f in treffer)
            elif urteil == "etikett":
                ersatz[schl].update(f["tag"] for f in funde[datei]
                                    if _beruehrt(f, soll))

    print("=" * 66)
    print("KONTROLLE — dieselben Saetze mit ASCII-Namen")
    print("=" * 66)
    for tag, (ja, n) in kontrolle.items():
        marke = "ok" if ja == n else "⚠️ "
        print(f"  {marke} {tag:18s} {ja}/{n}")
    if any(ja == 0 for ja, _ in kontrolle.values()):
        print("\n  ⚠️  Ein Satz, den die Kette schon mit ASCII nicht traegt,")
        print("      misst nicht den Zeichensatz. Die Zeilen unten sind")
        print("      fuer dieses Tag NICHT auswertbar.")
    print()

    print("=" * 66)
    print("ZEICHENSATZ — erkannt je Block und Tag")
    print("=" * 66)
    print(f"  {'Block':10s} {'Tag':16s} {'richtig':>8s}"
          f"{'Etikett':>9s}{'LECK':>7s}   gefunden von")
    for (blk, tag) in sorted(tabelle):
        z = tabelle[(blk, tag)]
        q = ", ".join(sorted(quellen[(blk, tag)])) or "—"
        marke = " ⚠️" if z["leck"] else "  "
        print(f"{marke}{blk:10s} {tag:16s} {z['richtig']:>8}"
              f"{z['etikett']:>9}{z['leck']:>7}   {q}")
    print()
    for schl, c in sorted(ersatz.items()):
        if not c:
            continue
        wohin = ", ".join(f"{t} {n}" for t, n in c.most_common())
        print(f"  {schl[1]} in {schl[0]} stattdessen maskiert als: {wohin}")
    if ersatz:
        print("  Ein falsches Etikett ist KEIN Leck — der Klartext ist weg.")
        print("  Das Woerterbuch fuehrt ihn unter dem falschen Namen.")
        print()

    # --- Kennzahlen ---
    print("=" * 66)
    print("KENNNUMMERN — je Schreibweise")
    print("=" * 66)
    for datei, e in sorted(erwartet.items()):
        if e["block"] != "Kennzahl" or datei not in funde:
            continue
        kz, soll = e["kennzahl"], e["spannen"][0]
        richtig = [f for f in funde[datei]
                   if f["tag"] == kz["tag"] and _deckt(f, soll)]
        # ⚠️ Ein Treffer unter einem ANDEREN Tag ist kein Teilerfolg. Er
        # ist schlimmer als nichts: er sieht nach Erkennung aus.
        falsch = [f for f in funde[datei] if f["tag"] != kz["tag"]]
        if richtig:
            stand = "ok    " + ", ".join(
                sorted({f.get("quelle", "?") for f in richtig}))
        elif falsch:
            stand = "FALSCH " + ", ".join(sorted({f["tag"] for f in falsch}))
        else:
            stand = "nichts"
        print(f"  {kz['tag']:16s} {kz['schreibweise']:14s} {stand}")
    print()
    print("Dieses Werkzeug schlaegt nichts vor. Was mit einer Luecke")
    print("geschieht, ist ein fachlicher Entscheid — siehe docs/ZEICHENSATZ.md.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Proben erzeugen und einen Kettenbericht auswerten.")
    ap.add_argument("--proben", metavar="VERZEICHNIS",
                    help="Proben dorthin schreiben. Braucht kein Modell.")
    ap.add_argument("--auswerten", metavar="BERICHT.json",
                    help="Bericht aus filter_document.py auswerten.")
    args = ap.parse_args()

    if not args.proben and not args.auswerten:
        ap.print_help()
        return 1
    if args.proben:
        ziel = Path(args.proben)
        n = proben_schreiben(ziel)
        print(f"{n} Proben in {ziel}")
        print("Alle Namen und Nummern sind erfunden.")
        print()
        print("Naechster Schritt — dieser braucht das Modell:")
        print(f"  python3 tools/filter_document.py --model runs/ch-v63b \\")
        print(f"      --ohne-regeln --ohne-vorlieben --knapp \\")
        print(f"      --bericht {ziel}/bericht.json {ziel}")
    if args.auswerten:
        return auswerten(Path(args.auswerten))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
