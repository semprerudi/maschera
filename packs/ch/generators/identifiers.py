"""Generatoren für Schweizer Identifikatoren (SPEC §6).

Identifikatoren werden generiert, nicht gelistet. Jeder Generator erzeugt
ausschliesslich Werte, die den zugehörigen Validator bestehen — das ist die
Voraussetzung für den Round-Trip aus SPEC §11.

Ausgabe erfolgt in der ÜBLICHEN SCHREIBWEISE mit Trennzeichen, weil genau die
im Dokument steht und vom Modell gelernt werden muss.
"""

from __future__ import annotations

import random

from packs.ch.validators.checksums import (
    ean13,
    luhn_check_digit,
    mod10_recursive,
    uid_check_digit,
)

__all__ = [
    "gen_ahvn13",
    "gen_gln",
    "gen_uid",
    "gen_iban",
    "gen_qr_reference",
    "gen_creditcard",
    "GENERATORS",
]

# OFFENER PUNKT: Bankleitzahlen aus dem SIX-Bankenstamm ziehen. Ohne das
# entstehen gültige Prüfsummen mit nicht existierenden Banken (SPEC §6).
_PLACEHOLDER_CLEARING = ("00700", "00243", "09000", "00779", "08390")


def gen_ahvn13(rng: random.Random | None = None, formatted: bool = True) -> str:
    rng = rng or random
    body = "756" + "".join(str(rng.randint(0, 9)) for _ in range(9))
    full = body + str(ean13(body))
    if not formatted:
        return full
    return f"{full[0:3]}.{full[3:7]}.{full[7:11]}.{full[11:13]}"


def gen_gln(rng: random.Random | None = None, formatted: bool = True) -> str:
    """GLN einer Medizinalperson. Präfix 76 = Schweizer GS1-Bereich."""
    rng = rng or random
    body = "76" + "".join(str(rng.randint(0, 9)) for _ in range(10))
    # GLN hat keine übliche Trennschreibweise, `formatted` nur für API-Symmetrie
    return body + str(ean13(body))


def gen_uid(rng: random.Random | None = None, formatted: bool = True) -> str:
    rng = rng or random
    while True:
        body = "".join(str(rng.randint(0, 9)) for _ in range(8))
        check = uid_check_digit(body)
        if check is not None:  # 10 wird nie vergeben, neu würfeln
            break
    digits = body + str(check)
    if not formatted:
        return "CHE" + digits
    return f"CHE-{digits[0:3]}.{digits[3:6]}.{digits[6:9]}"


def gen_iban(
    rng: random.Random | None = None,
    country: str = "CH",
    formatted: bool = True,
) -> str:
    """CH/LI-IBAN: 2 Land + 2 Prüf + 5 Clearing + 12 Kontoteil = 21 Zeichen."""
    rng = rng or random
    clearing = rng.choice(_PLACEHOLDER_CLEARING)
    account = "".join(str(rng.randint(0, 9)) for _ in range(12))
    bban = clearing + account
    rearranged = bban + country + "00"
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    check = 98 - int(numeric) % 97
    iban = f"{country}{check:02d}{bban}"
    if not formatted:
        return iban
    return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))


def gen_qr_reference(rng: random.Random | None = None, formatted: bool = True) -> str:
    rng = rng or random
    body = "".join(str(rng.randint(0, 9)) for _ in range(26))
    full = body + str(mod10_recursive(body))
    if not formatted:
        return full
    # Übliche Gruppierung: 2 + 5x5, von rechts gelesen
    return f"{full[0:2]} {full[2:7]} {full[7:12]} {full[12:17]} {full[17:22]} {full[22:27]}"


def gen_creditcard(rng: random.Random | None = None, formatted: bool = True) -> str:
    rng = rng or random
    prefix = rng.choice(("4", "51", "52", "53", "54", "55"))
    length = 16
    body = prefix + "".join(
        str(rng.randint(0, 9)) for _ in range(length - len(prefix) - 1)
    )
    full = body + str(luhn_check_digit(body))
    if not formatted:
        return full
    return " ".join(full[i : i + 4] for i in range(0, len(full), 4))


GENERATORS = {
    "AHVN13": gen_ahvn13,
    "GLN": gen_gln,
    "UID": gen_uid,
    "IBAN": gen_iban,
    "QR_REFERENCE": gen_qr_reference,
    "CREDITCARD": gen_creditcard,
}
