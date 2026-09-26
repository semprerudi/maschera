"""Regressionen: bekannte Fehlerklassen von PII-Erkennern.

    python3 tests/test_regressionen.py

Jeder Abschnitt haelt eine Fehlerklasse fest, die ein Erkenner dieser Art
typischerweise hat und die hier nicht wieder auftreten darf.
"""
from __future__ import annotations

import datetime
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.detectors import IBAN_LENGTHS  # noqa: E402
from core.injector import check_template, pruefe_decoys, generate, load_templates, normalize_template  # noqa: E402
from core.recognizers import recognize  # noqa: E402

failures = []
def check(c, m):
    if not c: failures.append(m)

ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def make_iban(country, rng):
    n = IBAN_LENGTHS[country]
    body = "".join(rng.choice(ALNUM) for _ in range(n - 4))
    rear = body + country + "00"
    num = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rear)
    return f"{country}{98 - int(num) % 97:02d}{body}"


print("IBAN in Gruppen geschrieben, auch auslaendische\n")

rng = random.Random(99)
total = miss = partial = 0
for country in IBAN_LENGTHS:
    for _ in range(3):
        iban = make_iban(country, rng)
        for k in (0, 2, 3, 4, 5, 6, 7):
            written = iban if k == 0 else " ".join(
                iban[i:i + k] for i in range(0, len(iban), k))
            text = f"Zahlung an die Firma auf {written} bis Ende Monat."
            total += 1
            hits = [text[s.start:s.end] for s in recognize(text) if s.tag == "IBAN"]
            if not hits:
                miss += 1
            elif "".join(c for c in hits[0] if c.isalnum()) != iban:
                partial += 1

check(miss == 0, f"{miss} IBAN nicht gefunden")
check(partial == 0, f"{partial} IBAN nur teilweise erfasst — der gefaehrliche Fall")
print(f"   {total} Faelle, {len(IBAN_LENGTHS)} Laender x 7 Schreibweisen")
print(f"   nicht gefunden {miss}, teilweise {partial}, "
      f"vollstaendig {100*(total-miss-partial)/total:.1f} %")

prosa = ["Gestuetzt auf Art. 6 Abs. 1 Bst. i RHG (SR 431.02) wird verfuegt.",
         "Die Parzelle 1234 in der Gemeinde AG 4711 wurde vermessen.",
         "Formular AB12 CD34 EF56 ist beizulegen.",
         "Kontrollschild ZH 123456, Fahrzeug BE 9911",
         "Der Betrag CHF 1'250.00 ist bis SO 31.12.2026 faellig."]
fp = sum(len([s for s in recognize(t) if s.tag == "IBAN"]) for t in prosa * 200)
check(fp == 0, f"{fp} Falsch-Positive auf Prosa")
print(f"   Falsch-Positive auf 1000 Prosazeilen: {fp}")

print("\nDaten eines Dokuments sind nicht unabhaengig")
print("   Vor der Korrektur: 53 % der Dokumente mit Daten in falscher Reihenfolge.\n")

def parse(v):
    for f in ("%d.%m.%Y", "%Y-%m-%d"):
        try: return datetime.datetime.strptime(v, f).date()
        except ValueError: pass
    return None

rueck = docs = 0
birth_years = []
for e in generate(800, seed=5):
    ordinary = []
    for s in e.spans:
        if s.tag != "DATE":
            continue
        d = parse(e.text[s.start:s.end])
        if not d:
            continue
        before = e.text[max(0, s.start - 30):s.start].lower()
        # Muss dieselben Marker kennen wie _BIRTH_MARKERS im Injektor.
        # Nach der Umstellung auf sprachspezifische Makros erschienen "né le"
        # und "nato il" — der Test kannte sie nicht und zaehlte Geburtsdaten
        # als gewoehnliche Daten, die dann natuerlich rueckwaerts standen.
        if any(w in before for w in ("geboren", "geburtsdatum", "naissance",
                                     "né le", "ne le", "nato il", "nata il",
                                     "nascita", "birth", "born on")):
            birth_years.append(d.year)
        else:
            ordinary.append(d)
    if len(ordinary) >= 2:
        docs += 1
        if ordinary != sorted(ordinary):
            rueck += 1

check(rueck == 0, f"{rueck} von {docs} Dokumenten haben Daten in falscher Reihenfolge")
check(all(y < 2010 for y in birth_years),
      f"unplausible Geburtsjahre: {[y for y in birth_years if y >= 2010][:5]}")
print(f"   {docs} Dokumente mit mehreren Daten, {rueck} rueckwaerts")
print(f"   {len(birth_years)} Geburtsdaten, Jahre "
      f"{min(birth_years)}-{max(birth_years)}" if birth_years else "")

print("\nZwei benachbarte Slots verschmelzen die Entitaeten")
# Auf GLEICHE Tags eingegrenzt: `B-AGE` neben `B-SEX` ist in BIO
# eindeutig, und «Gesendet: {DATE} {TIME}» steht so in jeder Mailkopfzeile.
# Eine Warnung, die man immer wegklickt, ist schlimmer als keine.
adj = check_template({"id": "t", "text": "Person: {FULLNAME} {FULLNAME} hier"})
check(adj, "benachbarte Slots mit gleichem Tag muessten gemeldet werden")
ok = check_template({"id": "t", "text": "Gesendet: {DATE} {TIME}"})
check(not ok, "verschiedene Tags nebeneinander sind KEIN Befund")
check(not check_template({"id": "t", "text": "Person: {AGE} Jahre, {SEX}"}),
      "Slots mit Trenntext duerfen nicht gemeldet werden")
real = [t["id"] for t in load_templates() if check_template(t)]
check(not real, f"eigene Vorlagen verletzen die Regel: {real}")
print(f"   Wache greift, eigene Vorlagenbank sauber ({len(load_templates())} Vorlagen)")

print("\nLiterale Escapes zerstoeren die BIO-Labels")
broken = {"id": "t", "text": "Zeile eins" + chr(92) + "nGeboren am {DATE}"}
check(check_template(broken), "literaler Escape muesste gemeldet werden")
fixed = normalize_template(broken)
check(not check_template(fixed), "Normalisierung behebt es nicht")
check("\n" in fixed["text"], "Normalisierung erzeugt keinen echten Umbruch")
print("   Wache greift, Normalisierung repariert statt zu verwerfen")

print("\nZerstueckelung laesst Zeichen im Klartext")
print("   Original: '12/06/2025' -> '[DATE_1][DATE_2]2[DATE_3]'.")
print("   Ohne diesen Erkenner zerfallen Daten in Teil-Platzhalter.\n")

from core.inference import Scored, filter_text  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")


class Fragmenting:
    """Modell, das lange Entitaeten in zwei Spannen zerlegt und ein Zeichen
    dazwischen auslaesst. """

    def __init__(self, example):
        self.example = example

    def score(self, text):
        out = []
        for s in self.example.spans:
            if s.tag in ("DATE", "CASE_ID") and s.end - s.start > 6:
                mid = s.start + (s.end - s.start) // 2
                out.append(Scored(s.tag, s.start, mid, 0.9))
                out.append(Scored(s.tag, mid + 1, s.end, 0.9))
            else:
                out.append(Scored(s.tag, s.start, s.end, 0.9))
        return out


PLACEHOLDER = re.compile(r"\[[A-Za-z0-9]+_\d+[a-z]*\]")
stuck = []
for e in generate(200, seed=3):
    r = filter_text(e.text, PACK, scorer=Fragmenting(e))
    for m in PLACEHOLDER.finditer(r.masked):
        before = r.masked[m.start() - 1:m.start()]
        after = r.masked[m.end():m.end() + 1]
        if (before and before.isalnum()) or (after and after.isalnum()):
            stuck.append(r.masked[max(0, m.start() - 12):m.end() + 12])

check(not stuck, f"{len(stuck)} Platzhalter kleben an einem Wortzeichen: "
                 f"{stuck[:3]}")
print(f"   {len(stuck)} Teil-Platzhalter bei zerstueckelndem Modell")
print("   Die Zusicherung ist unabhaengig vom Modell-Recall: sie verlangt nicht,")
print("   dass eine Entitaet erkannt wird, sondern dass die Ersetzung ganze")
print("   Woerter abdeckt, WENN sie erkannt wird.")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures: print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")


# --- Decoy-Familie einheitlich ----------------------------------------------
print("\nDecoy-Familie `amount` — Nominalphrasen, keine Saetze")
befunde = pruefe_decoys()
check(not befunde, f"amount-Decoys nicht einheitlich: {befunde}")
print("   OK   alle amount-Decoys sind Nominalphrasen")

if failures:
    print(f"\nFEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
