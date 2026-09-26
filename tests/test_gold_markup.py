#!/usr/bin/env python3
"""Gold aus markiertem Text — Schritt 12."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from gold_from_markup import zerlege
from packs import load_pack

failures: list[str] = []
def check(ok, msg):
    if not ok:
        failures.append(msg); print(f"   FEHL {msg}")

pack = load_pack("ch")
erlaubt = {t.tag for t in pack.get_tags()} | {"X_dossier"}

print("1. Zerlegung: Spannen aus Markierungen")
M = "Von: [[FULLNAME:Meier]] [[GIVENNAME:Hans]] <[[EMAIL:h.m@x.ch]]>"
text, spans, befunde = zerlege(M, erlaubt)
check(not befunde, f"unerwartete Befunde: {befunde}")
check(text == "Von: Meier Hans <h.m@x.ch>", f"Text falsch: {text!r}")
check(len(spans) == 3, f"3 Spannen erwartet, {len(spans)}")
for s in spans:
    check(text[s["start"]:s["end"]] == s["wert"],
          f"Spanne sitzt daneben: {s}")
print(f"   {text!r}")
for s in spans:
    print(f"     {s['start']:3} {s['end']:3}  {s['tag']:12} {s['wert']!r}")

print("\n2. Wachen gegen Fehler in der Markierung")
for markup, grund in [
    ("[[NAME:Meier]]", "unbekanntes Tag"),
    ("[[FULLNAME:]]", "leere Markierung"),
    ("[[FULLNAME: Meier]]", "Randleerzeichen"),
]:
    _, _, b = zerlege(markup, erlaubt)
    check(b, f"haette melden muessen: {grund}")
    if b:
        print(f"   OK   {grund}: {b[0][:60]}")

print("\n3. Text ohne Markierung ergibt keine Spannen")
t, sp, b = zerlege("Nur Fliesstext ohne alles.", erlaubt)
check(sp == [], "unerwartete Spannen")
check(t == "Nur Fliesstext ohne alles.", "Text veraendert")
print("   OK")

print("\n4. Die Verdachtswache greift nicht ueber Zeilenumbrueche")
# Ein Vor- und ein Nachname stehen auf derselben Zeile; was ueber einen
# Umbruch reicht, ist zufaellige Nachbarschaft — 'Sophia\n\n\nVon' ist
# kein Namensverdacht. Das Muster fuer Grossschreibung benutzt deshalb
# kein `\s+`.
from filter_document import restverdacht  # noqa: E402

def gross(text: str) -> list[str]:
    frei = bytearray(len(text))
    return [w for art, _, _, w in restverdacht(text, frei) if art == "Grossschreibung"]

ueber_umbruch = gross("Sophia\n\n\nVon Meier Anna")
check(not any("\n" in w for w in ueber_umbruch),
      f"Verdacht spannt ueber Zeilenumbruch: {ueber_umbruch}")
print(f"   OK   ueber Umbruch keine Spanne: {ueber_umbruch}")

auf_zeile = gross("Kontakt Meier Anna heute")
check(any("Meier Anna" in w for w in auf_zeile),
      f"Name auf einer Zeile nicht mehr gefunden: {auf_zeile}")
print(f"   OK   auf derselben Zeile weiterhin: {auf_zeile}")

# Der Tabulator ist eine SPALTENGRENZE, kein Abstand. In Formularen
# steht er zwischen Feldname und Wert: 'Name\tAndrea Brülhart',
# 'Adresse\tSonnenbergstrasse'. Nimmt das Muster ihn mit, reicht der
# Verdacht vom Feldnamen in den bereits markierten Wert.
#
# Merksatz: Ein Test, der eine Annahme festschreibt, schuetzt sie auch vor
# der Korrektur. Er muss dieselbe Pruefung durchlaufen wie der Code.
mit_tab = gross("Adresse\tSonnenbergstrasse")
check(not any("\t" in w for w in mit_tab),
      f"Verdacht spannt ueber Tabulator: {mit_tab}")
print(f"   OK   Tabulator trennt wie ein Umbruch: {mit_tab}")

satzanfang = gross("Beim Umzug im Maerz wurde die Nummer vertauscht")
check(not any(w.startswith("Beim") for w in satzanfang),
      f"Deutscher Satzanfang als Namensverdacht: {satzanfang}")
print(f"   OK   'Beim Umzug' ist kein Namensverdacht")

print("\n5. Gruss- und Anredeformeln loesen keinen Namensverdacht aus")
# `HARMLOS` braucht alle Beugungen einer Formel — "Herzlichen" (Dank)
# und "Herzliche" (Gruesse). Der Kommentar an `HARMLOS` sagt, warum das
# zaehlt: «Eine Wache, die man wegklickt, ist keine.»
#
# Diese Liste ist der Massstab. Wer eine Formel vermisst, traegt sie hier
# ein — dann faellt die fehlende Beugung hier auf und nicht am Gold.
FORMELN = [
    "Herzliche Grüsse", "Herzlichen Dank", "Herzlichst Ihre",
    "Freundliche Grüsse", "Freundlicher Gruss", "Liebe Grüsse",
    "Lieben Gruss", "Beste Grüsse", "Bester Gruss", "Besten Dank",
    "Viele Grüsse", "Vielen Dank", "Schöne Grüsse", "Sonnige Grüsse",
    "Warme Grüsse", "Liebste Grüsse", "Guten Tag", "Werte Damen",
    "Sehr geehrte Damen", "Geschätzte Kundin",
    "Meilleures salutations", "Cordiales salutations", "Bien cordialement",
    "Cordiali saluti", "Distinti saluti", "Molti saluti",
    "Kind regards", "Best regards", "Many thanks", "Warm regards",
]
durch = []
for f in FORMELN:
    t = "Ein Satz davor. " + f + " und weiter."
    if any(f.split()[0] in w for w in gross(t)):
        durch.append(f)
check(not durch, f"Formeln kommen durch die Wache: {durch}")
if not durch:
    print(f"   OK   {len(FORMELN)} Formeln in vier Sprachen, "
          f"keine durchgekommen")

# Verben am Anfang einer Frage sind dieselbe Klasse.
FRAGEN = ["Haben Sie Fragen", "Können Sie das", "Möchten Sie mehr",
          "Benötigen Sie Hilfe", "Melden Sie sich"]
durch = [f for f in FRAGEN
         if any(f.split()[0] in w
                for w in gross("Ein Satz davor. " + f + "?"))]
check(not durch, f"Frageanfaenge kommen durch: {durch}")
if not durch:
    print(f"   OK   {len(FRAGEN)} Frageanfaenge, keine durchgekommen")

print("\n6. Ein echter Name wird davon NICHT verschluckt")
# Die Gegenprobe zu Punkt 5. Eine Wache, die alles durchlaesst, besteht
# jede Formelpruefung — deshalb muss dieselbe Mechanik hier anschlagen.
for name in ["Kontakt Meier Anna heute", "Sachbearbeiter Hans Brülhart hier",
             "zustaendig Andrea Rossi meldet"]:
    check(gross(name), f"Name nicht mehr gefunden: {name!r}")
print("   OK   drei Namen weiterhin gefunden")

print("\n7. HARMLOS traegt keine Doppelten")
# Die Liste waechst von Hand. Doppelte sind harmlos, weil es ein `set`
# ist — aber sie zeigen, dass sie ohne Pruefung waechst.
import re as _re
from collections import Counter as _Counter
_quelle = (Path(__file__).resolve().parent.parent
           / "tools" / "filter_document.py").read_text(encoding="utf-8")
_block = _re.search(r"HARMLOS = \{(.*?)\n\}", _quelle, _re.S).group(1)
_code = [z for z in _block.splitlines() if not z.strip().startswith("#")]
_woerter = _re.findall(r'"([^"]+)"', "\n".join(_code))
_dopp = sorted(w for w, n in _Counter(_woerter).items() if n > 1)
check(not _dopp, f"Doppelte in HARMLOS: {_dopp}")
if not _dopp:
    print(f"   OK   {len(_woerter)} Eintraege, keine doppelt")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures: print("  -", f)
    sys.exit(1)
print("Alle Pruefungen bestanden.")
