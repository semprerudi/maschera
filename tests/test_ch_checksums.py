"""Testsuite für die Prüfsummen (SPEC §5).

Drei Ebenen:
  1. Bekannte Vektoren — die zwei echten Nummern aus der Spec
  2. Round-Trip — 2000 generierte Nummern je Typ müssen validieren
  3. Mutation — eine geänderte Ziffer muss auffallen, sonst ist die Prüfsumme
     wertlos. Das ist der Test, der in der Spec fehlt.

    python3 tests/test_ch_checksums.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packs.ch.generators.identifiers import GENERATORS  # noqa: E402
from packs.ch.validators.checksums import (  # noqa: E402
    VALIDATORS,
    normalize_digits,
    uid_check_digit,
)

N = 2000
SEED = 20260801

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


# ---------------------------------------------------------------------------
# 1. Bekannte Vektoren
# ---------------------------------------------------------------------------

print("1. Bekannte Vektoren")

known_good = [
    ("AHVN13", "756.9217.0769.85"),
    ("AHVN13", "7569217076985"),
    ("UID", "CHE-116.281.710"),
    ("UID", "CHE116281710"),
    ("UID", "CHE-116.281.710 MWST"),
]
for tag, value in known_good:
    ok = VALIDATORS[tag](value)
    check(ok, f"{tag} {value!r} müsste gültig sein")
    print(f"   {'OK  ' if ok else 'FEHL'} {tag:<13} {value}")

known_bad = [
    ("AHVN13", "756.9217.0769.86", "falsche Prüfziffer"),
    ("AHVN13", "757.9217.0769.85", "falsches Präfix"),
    ("AHVN13", "756.9217.0769.8", "zu kurz"),
    ("UID", "CHE-116.281.711", "falsche Prüfziffer"),
    ("UID", "DEU-116.281.710", "falsches Präfix"),
    ("IBAN", "CH93 0076 2011 6238 5296 0", "erfundene Nummer"),
    ("QR_REFERENCE", "21 00000 00003 13947 14300 09018", "eine Ziffer gedreht"),
]
for tag, value, why in known_bad:
    ok = VALIDATORS[tag](value)
    check(not ok, f"{tag} {value!r} müsste ungültig sein ({why})")
    print(f"   {'OK  ' if not ok else 'FEHL'} {tag:<13} abgelehnt: {why}")

# UID-Sonderfall: Ergebnis 10 wird nie vergeben
tens = [
    body
    for body in (f"{i:08d}" for i in range(200000))
    if uid_check_digit(body) is None
]
check(len(tens) > 0, "kein einziger UID-Körper mit Prüfergebnis 10 gefunden")
print(f"   OK   UID           {len(tens)} von 200000 Körpern ergeben 10 -> nie vergeben")

# ---------------------------------------------------------------------------
# 2. Round-Trip
# ---------------------------------------------------------------------------

print(f"\n2. Round-Trip, {N} Nummern je Typ")

rng = random.Random(SEED)
for tag, gen in GENERATORS.items():
    validator = VALIDATORS[tag]
    bad = 0
    seen = set()
    for _ in range(N):
        value = gen(rng)
        seen.add(value)
        if not validator(value):
            bad += 1
    check(bad == 0, f"{tag}: {bad} von {N} generierten Nummern fielen durch")
    # Auch die unformatierte Schreibweise muss durchgehen
    unformatted_ok = True
    for _ in range(200):
        try:
            v = gen(rng, formatted=False)
        except TypeError:
            unformatted_ok = None
            break
        if not validator(v):
            unformatted_ok = False
            break
    fmt = {True: "auch roh", False: "ROH FEHLGESCHLAGEN", None: "kein roh-Modus"}[unformatted_ok]
    check(unformatted_ok is not False, f"{tag}: unformatierte Schreibweise fällt durch")
    print(f"   {'OK  ' if bad == 0 else 'FEHL'} {tag:<13} {N - bad}/{N} gültig, "
          f"{len(seen)} verschieden, {fmt}")

# ---------------------------------------------------------------------------
# 3. Mutation — der eigentliche Test
# ---------------------------------------------------------------------------

print(f"\n3. Mutation: eine Ziffer ändern, {N} Versuche je Typ")

rng = random.Random(SEED + 1)
for tag, gen in GENERATORS.items():
    validator = VALIDATORS[tag]
    missed = 0
    for _ in range(N):
        try:
            value = gen(rng, formatted=False)
        except TypeError:
            value = gen(rng)
        digits = normalize_digits(value)
        pos = rng.randrange(len(digits))
        new = str((int(digits[pos]) + rng.randint(1, 9)) % 10)
        mutated = digits[:pos] + new + digits[pos + 1 :]
        prefix = value[: len(value) - len(digits)]  # CHE / CH-Ländercode
        if validator(prefix + mutated):
            missed += 1
    rate = 100 * (N - missed) / N
    check(missed == 0, f"{tag}: {missed} von {N} Einzelziffer-Fehlern nicht erkannt")
    print(f"   {'OK  ' if missed == 0 else 'FEHL'} {tag:<13} {rate:6.2f} % der "
          f"Einzelziffer-Fehler erkannt")

# ---------------------------------------------------------------------------
# 4. Transposition — zwei Nachbarziffern vertauschen
# ---------------------------------------------------------------------------
# Kein Pass/Fail, sondern eine Messung. Kein Verfahren ausser Modulo 11 und
# Modulo 97 erkennt jede Vertauschung — das ist bekannte Mathematik, kein Fehler:
#
#   Modulo 11 (UID)          100 %   lückenlos
#   Modulo 97 (IBAN)         100 %   lückenlos in der Praxis
#   Modulo 10 rekursiv (QR)  ~98 %   blind bei 10 Ziffernpaaren, und auch dort
#                                    nur bei je einem bestimmten Übertragszustand
#                                    (03/30 bei Übertrag 4, 47/74 bei 0, ...)
#                                    = 10 von 450 Kombinationen
#   Luhn (Kreditkarte)       ~98 %   blind bei 09 <-> 90
#   EAN-13 (AHVN13, GLN)     ~90 %   blind bei allen Nachbarn mit Differenz 5,
#                                    also 05, 16, 27, 38, 49 — der schwächste Fall
#
# Praktische Folge für SPEC §5: Der Satz "Prüfsummen schlagen das Modell" gilt
# uneingeschränkt nur gegen Einzelziffer-Fehler (dort 100 % über alle Verfahren).
# Gegen Zahlendreher — genau das, was OCR produziert — ist ausgerechnet AHVN13
# das schwächste Glied. Der Override bleibt richtig; er beweist nur weniger, als
# der Wortlaut der Spec nahelegt.

print(f"4. Transposition: Nachbarziffern tauschen, {N} Versuche je Typ")

rng = random.Random(SEED + 2)
transposition = {}
for tag, gen in GENERATORS.items():
    validator = VALIDATORS[tag]
    attempts = missed = 0
    for _ in range(N):
        try:
            value = gen(rng, formatted=False)
        except TypeError:
            value = gen(rng)
        digits = normalize_digits(value)
        pos = rng.randrange(len(digits) - 1)
        if digits[pos] == digits[pos + 1]:
            continue  # Tausch ohne Wirkung
        attempts += 1
        swapped = (
            digits[:pos] + digits[pos + 1] + digits[pos] + digits[pos + 2 :]
        )
        prefix = value[: len(value) - len(digits)]
        if validator(prefix + swapped):
            missed += 1
    rate = 100 * (attempts - missed) / attempts if attempts else 0.0
    transposition[tag] = rate
    print(f"        {tag:<13} {rate:6.2f} % erkannt   ({missed} von {attempts} übersehen)")

check(
    transposition["UID"] == 100.0,
    "UID müsste alle Transpositionen erkennen (Modulo 11)",
)
check(
    transposition["IBAN"] == 100.0,
    "IBAN müsste alle Transpositionen erkennen (Modulo 97)",
)
check(
    transposition["QR_REFERENCE"] > 95.0,
    f"QR-Referenz unter Erwartung: {transposition['QR_REFERENCE']:.2f} %",
)
check(
    transposition["AHVN13"] > 85.0,
    f"AHVN13 unter Erwartung: {transposition['AHVN13']:.2f} %",
)

# ---------------------------------------------------------------------------

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Problem(e):")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)

print("Alle Prüfungen bestanden.")
