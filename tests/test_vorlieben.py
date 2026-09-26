"""Klartext-Vorlieben: Wachen und getrennte Ausweisung.

Tag-Filter und `prefs.json`, mit zwei Wachen — beide werden hier
geprueft:

  1. Besonders schuetzenswerte Personendaten brauchen `--auch-bspd`.
  2. Ein abgeschaltetes Tag verschwindet NICHT aus der Auswertung, sondern
     wird getrennt ausgewiesen. Sonst verbessert sich die Leckrate, indem
     man abschaltet, was leckt.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# XDG umbiegen, BEVOR das Modul den Pfad berechnet — sonst schriebe der Test
# in die echte Konfiguration des Anwenders.
_TMP = tempfile.mkdtemp(prefix="maschera-vorlieben-")
os.environ["XDG_CONFIG_HOME"] = _TMP

from core import vorlieben  # noqa: E402
from core.evaluate import evaluate, format_report  # noqa: E402
from core.masking import Span  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")
failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


print("1. Der Pfad zeigt nicht ins Projekt")
check(str(vorlieben.PFAD).startswith(_TMP),
      f"schreibt ausserhalb von XDG_CONFIG_HOME: {vorlieben.PFAD}")
check("MASCHERA" not in str(Path(__file__).parent.parent / "packs"
                             ) or "packs" not in str(vorlieben.PFAD),
      "Vorlieben liegen im Projektbaum — sie wuerden ueber Git und rsync "
      "auf jede Maschine wandern")
print(f"   OK   {vorlieben.PFAD}")

print("\n2. Unbekannte Tags werden abgelehnt, nicht ignoriert")
# Ein Tippfehler waere sonst wirkungslos, und der Anwender glaubte, das
# Datum bleibe im Klartext.
try:
    vorlieben.pruefe({"DATUM"}, PACK)
    check(False, "'DATUM' (Tippfehler) wurde angenommen")
except vorlieben.Abgelehnt as e:
    check("DATUM" in str(e), "Meldung nennt das falsche Tag nicht")
    print("   OK   Tippfehler abgewiesen")

print("\n3. bspd-Tags brauchen --auch-bspd")
heikel = sorted(t.tag for t in PACK.get_tags() if t.bspd)
check(len(heikel) >= 3, f"zu wenige bspd-Tags in der Taxonomie: {heikel}")
try:
    vorlieben.pruefe({heikel[0]}, PACK)
    check(False, f"{heikel[0]} ohne --auch-bspd angenommen")
except vorlieben.Abgelehnt:
    print(f"   OK   {heikel[0]} ohne Bestaetigung abgewiesen")
check(vorlieben.pruefe({heikel[0]}, PACK, auch_bspd=True) == {heikel[0]},
      "mit --auch-bspd muss es durchgehen")
print(f"   OK   mit --auch-bspd erlaubt ({len(heikel)} heikle Tags)")

print("\n4. Speichern und Laden")
vorlieben.speichere({"DATE", "ORG"}, PACK)
check(vorlieben.lade() == {"DATE", "ORG"}, f"gelesen: {vorlieben.lade()}")
print("   OK   DATE, ORG")

print("\n5. Ein abgeschaltetes Tag verschwindet NICHT aus der Auswertung")
# Der Missbrauchsfall: abschalten, was leckt. Ohne getrennte Ausweisung
# faellt die Leckrate auf 0 und niemand sieht warum. Ein Mass, das sich
# durch eine Einstellung verbessern laesst, misst die Einstellung.
text = "Andrea Bruelhart aus Lugano."
gold = [Span("GIVENNAME", 0, 6), Span("FULLNAME", 7, 16), Span("CITY", 21, 27)]
pred = gold[:2]                                   # CITY leckt

offen = evaluate([(text, gold, pred)], PACK)
check(offen.leak_rate > 0, "ohne Ausschluss muss CITY als Leck zaehlen")

still = evaluate([(text, gold, pred)], PACK, excluded={"CITY"})
check(still.leak_rate == 0.0, "ein bewusst offenes Tag ist kein Leck")
check(("CITY", "Lugano") in still.im_klartext,
      f"der Wert fehlt in im_klartext: {still.im_klartext}")
check(still.klartext_tags == ("CITY",), f"Tags fehlen: {still.klartext_tags}")

bericht = format_report(still, top=5)
check("BEWUSST IM KLARTEXT" in bericht and "CITY" in bericht,
      "der Bericht verschweigt, dass ein Tag abgeschaltet ist")
print(f"   OK   Leckrate {100*offen.leak_rate:.1f} % -> "
      f"{100*still.leak_rate:.1f} %, aber 'Lugano' steht namentlich im Bericht")

print("\n6. Ein bewusst offenes Tag ist keine Uebermaskierung")
# Beim ersten Lauf mit `--ohne DATE,ORG` blieb die Zahl bei 36 statt zu
# fallen: die Leckseite war getrennt, die Uebermaskierungsseite vergessen.
# Ein Tag, das nichts ersetzt, kann nichts uebermaskieren.
t2 = "Andrea Bruelhart, Bundesamt fuer Statistik, in Lugano."
g2 = [Span("GIVENNAME", 0, 6), Span("FULLNAME", 7, 16)]
p2 = g2 + [Span("ORG", 18, 41), Span("CITY", 46, 52)]

voll = evaluate([(t2, g2, p2)], PACK)
ohne_org = evaluate([(t2, g2, p2)], PACK, excluded={"ORG"})
check(len(voll.over) == 2, f"erwartet 2 Uebermaskierungen: {voll.over}")
check(len(ohne_org.over) == 1,
      f"ORG offen -> nur CITY darf uebrig bleiben: {ohne_org.over}")
check(ohne_org.over[0][0] == "CITY", f"falsches Tag: {ohne_org.over}")
print(f"   OK   {len(voll.over)} -> {len(ohne_org.over)}, nur CITY bleibt")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
