"""Rauschen und Haltezone — zwei Lehren aus der Auswertung.

BEFUND 1, Rauschen:

    GIVENNAME  'Pasuqale'      <- Leck

«Pasquale» mit vertauschten Buchstaben, wie er in einem echten Dokument
stehen kann. Der Name steht in keiner Vornamenliste und damit in KEINEM
Trainingsbeispiel. Ein Modell, das nur saubere Nomenklaturwerte sieht,
lernt, Namen aus einer Liste wiederzuerkennen — nicht, sie an ihrer Form
zu erkennen. **Ein Injektor, der nur saubere Nomenklaturwerte einsetzt,
lehrt ein Woerterbuch statt eine Sprache.**

BEFUND 2, Haltezone. Ziehen Trainings- und Auswertungssatz aus DERSELBEN
Nomenklatur, ist eine hohe Genauigkeit mit «erkennt Namen» UND mit «hat
die Nachnamenliste auswendig» vereinbar — die Zahl unterscheidet die
beiden nicht. **Ein Mass, das zwei Erklaerungen gleich gut passt, misst
keine von beiden.**
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import injector as inj  # noqa: E402

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


print("1. Rauschen erzeugt echte Tippfehlerarten")
r = random.Random(11)
formen = {inj.verrausche("Pasquale", r) for _ in range(300)}
check("Pasquale" not in formen or len(formen) > 5,
      f"zu wenig Vielfalt: {sorted(formen)[:5]}")
check(any(f == "Pasqaule" for f in formen),
      "die gemessene Vertauschung 'Pasqaule' kommt nicht vor")
check("PASQUALE" in formen, "Versalien fehlen (Formulare in Grossschrift)")
umlaut = {inj.verrausche("Brülhart", r) for _ in range(300)}
check("Bruelhart" in umlaut,
      f"aufgeloester Umlaut fehlt: {sorted(umlaut)[:6]}")
print(f"   OK   {len(formen)} Formen, u.a. Pasqaule, PASQUALE, Bruelhart")

print("\n2. Der erste Buchstabe bleibt unangetastet")
# Ihn zu beschaedigen macht den Namen unkenntlich statt tippfehlerhaft —
# und ein unkenntlicher Name ist kein Trainingsbeispiel, sondern Rauschen
# im Wortsinn.
for wort in ("Pasquale", "Sonnenbergstrasse", "Bernasconi"):
    kaputt = {inj.verrausche(wort, r) for _ in range(200)}
    fremd = [k for k in kaputt if k and k[0] != wort[0] and not k.isupper()]
    check(not fremd, f"{wort}: Anfangsbuchstabe veraendert -> {fremd[:3]}")
print("   OK   Anfangsbuchstabe bleibt (ausser bei Versalien)")

print("\n3. Kurze Werte bleiben unberuehrt")
# «B» als PERMIT_TYPE oder «w» als SEX darf nicht verrauscht werden — daraus
# entstuende ein Wert, den die geschlossene Liste nicht kennt.
for kurz in ("B", "w", "AG", "Ins"):
    check(inj.verrausche(kurz, r) == kurz, f"{kurz!r} wurde veraendert")
print("   OK   unter 4 Zeichen unveraendert")

print("\n4. Pruefsummen-Tags werden NICHT verrauscht")
# Eine beschaedigte AHV-Nummer ist keine AHV-Nummer. Stufe 1 verwirft sie zu
# Recht, und das Beispiel lehrt nichts ausser einem Widerspruch.
for tag in ("AHVN13", "IBAN", "UID", "QR_REFERENCE", "CREDITCARD", "GLN"):
    check(tag not in inj.VERRAUSCHBAR, f"{tag} steht in VERRAUSCHBAR")
print(f"   OK   verrauschbar sind nur {len(inj.VERRAUSCHBAR)} Text-Tags")

print("\n5. Halterzone: Training und Auswertung teilen keinen Wert")
namen = [{"name": f"Name{i:04d}"} for i in range(2000)]
inj.setze_zone("training")
tr = {r["name"] for r in inj._zone("FULLNAME", namen)}
inj.setze_zone("halten")
ha = {r["name"] for r in inj._zone("FULLNAME", namen)}
inj.setze_zone(None)

check(not (tr & ha), f"Ueberschneidung: {sorted(tr & ha)[:5]}")
check(tr | ha == {r["name"] for r in namen}, "zusammen nicht vollstaendig")
check(0.05 < len(ha) / len(namen) < 0.15,
      f"Halterzone ist {100*len(ha)/len(namen):.0f} %, erwartet rund 10 %")
print(f"   OK   {len(tr)} Training, {len(ha)} gehalten, Schnittmenge leer")

# ⚠️ Auch die Schluesselform MIT Sprachzusatz.
#
# `_weighted` ruft `_zone` auch mit "ORG@de" auf. Pruefte diese Stelle nur
# die FUNKTION mit erfundenen Datensaetzen und nie eine AUFRUFSTELLE,
# liefe der Filter fuer "ORG@de" ins Leere: alle Behoerdennamen laegen in
# BEIDEN Zonen, waehrend die Pruefung gruen waere — bei dem Mechanismus,
# der Erkennen von Auswendiglernen trennen soll.
inj.setze_zone("training")
tr_l = {r["name"] for r in inj._zone("ORG@de", namen)}
inj.setze_zone("halten")
ha_l = {r["name"] for r in inj._zone("ORG@de", namen)}
inj.setze_zone(None)
check(not (tr_l & ha_l),
      f"'ORG@de' wird nicht geteilt — Sprachzusatz nicht abgeschnitten? "
      f"Ueberschneidung: {len(tr_l & ha_l)}")
check(tr_l and ha_l, "'ORG@de' liefert eine leere Zone")
print(f"   OK   'ORG@de' ebenso geteilt: {len(tr_l)} / {len(ha_l)}")

# Und die Probe aufs Ganze: echte Ziehungen, nicht nur die Filterfunktion.
import random as _random  # noqa: E402

def _zieh(zone, n=1500):
    inj.setze_zone(zone)
    werte = set()
    for lang in ("de", "fr", "it", "en"):
        rng = _random.Random(7)
        for _ in range(n // 4):
            werte.add(inj._pick("ORG", rng, lang))
    return werte

# ⚠️⚠️ DIE BEDINGUNG FRAGT DIE NOMENKLATUR, NICHT DIE ERGEBNISMENGEN.
#
# Ohne `dist/` greift der Notvorrat, und der ist fuer 1500 Ziehungen zu
# klein: es gibt dann zwangslaeufig geteilte Werte. Der Notvorrat LIEFERT
# aber Werte, die Ergebnismengen sind also nie leer — eine Bedingung
# `if not _tr or not _ha` wuerde den Sprung nie nehmen, und die Wache
# stuende rot ueber einer Eigenschaft, die in Ordnung ist.
#
# ⚠️ Gefragt wird nach dem, WOVON es abhaengt. Eine Bedingung, die das
# Ergebnis abfragt statt die Voraussetzung, ist im guten Fall gruen aus dem
# falschen Grund — oder rot aus dem falschen Grund.
_org = [k for k in inj._nomenclatures()
        if k == "ORG" or k.startswith("ORG@")]
if not _org:
    inj.setze_zone(None)
    print("   —    keine Nomenklatur gebaut (packs/ch/nomenclatures/dist/) "
          "— die Ziehprobe braucht sie, der Notvorrat ist zu klein")
else:
    _tr, _ha = _zieh("training"), _zieh("halten")
    inj.setze_zone(None)
    check(not (_tr & _ha),
          f"ORG-Ziehungen teilen {len(_tr & _ha)} Wert(e) ueber die Zonen")
    print(f"   OK   ORG gezogen: {len(_tr)} / {len(_ha)}, Schnittmenge leer")

print("\n6. Geschlossene Listen bleiben ganz")
# Bei acht Zivilstaenden wuerde ein Zehntel Rueckhalt die Vorlage unbrauchbar
# machen — der Wert fehlte dann im Auswertungssatz vollstaendig.
inj.setze_zone("halten")
for tag in ("MARITALSTATUS", "SEX", "RELIGION", "PERMIT_TYPE"):
    check(len(inj._zone(tag, namen)) == len(namen),
          f"{tag} wurde aufgeteilt")
inj.setze_zone(None)
print("   OK   MARITALSTATUS, SEX, RELIGION, PERMIT_TYPE ungeteilt")

print("\n7. Die Trennung ist reproduzierbar")
# Deterministisch ueber den WERT, nicht ueber den Index: Baut sich die
# Nomenklatur neu und aendert die Reihenfolge, bliebe die Trennung sonst
# nicht dieselbe — und zwei Laeufe waeren nicht vergleichbar.
gemischt = list(reversed(namen))
inj.setze_zone("halten")
ha2 = {r["name"] for r in inj._zone("FULLNAME", gemischt)}
inj.setze_zone(None)
check(ha == ha2, "andere Reihenfolge ergibt eine andere Halterzone")
print("   OK   umgekehrte Reihenfolge, gleiche Halterzone")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
