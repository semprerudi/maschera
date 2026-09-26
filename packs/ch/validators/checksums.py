"""Prüfsummen für Schweizer Identifikatoren (SPEC §5).

Grundsatz: Diese Funktionen sind die Precision-Garantie des Systems. Eine
gültige Prüfsumme maskiert auch dann, wenn das Modell schweigt; eine ungültige
verwirft auch dann, wenn das Modell anschlägt.

Sie arbeiten auf normalisierten Zeichenketten. Die Normalisierung ist bewusst
von der Prüfung getrennt: der Recognizer muss die ORIGINALE Zeichenspanne
behalten (Punkte, Bindestriche, Leerzeichen gehören zur Entität), auch wenn die
Mathematik sie nicht sieht.
"""

from __future__ import annotations

import re

__all__ = [
    "normalize_digits",
    "ean13",
    "is_valid_ahvn13",
    "is_valid_gln",
    "is_valid_uid",
    "is_valid_iban",
    "is_valid_qr_reference",
    "is_valid_creditcard",
    "VALIDATORS",
]

_NON_DIGIT = re.compile(r"[^0-9]")
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]")


def normalize_digits(value: str) -> str:
    """Alles ausser Ziffern entfernen. `756.9217.0769.85` -> `7569217076985`."""
    return _NON_DIGIT.sub("", value)


# ---------------------------------------------------------------------------
# EAN-13  ->  AHVN13, GLN
# ---------------------------------------------------------------------------

def ean13(first12: str) -> int:
    """Prüfziffer nach EAN-13. Gewichte 1,3,1,3,... von links über 12 Stellen."""
    if len(first12) != 12 or not first12.isdigit():
        raise ValueError("EAN-13 erwartet genau 12 Ziffern")
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(first12))
    return (10 - total % 10) % 10


def is_valid_ahvn13(value: str) -> bool:
    """AHV-Nummer: 13 Ziffern, Präfix 756, EAN-13-Prüfziffer."""
    d = normalize_digits(value)
    if len(d) != 13 or not d.startswith("756"):
        return False
    return ean13(d[:12]) == int(d[12])


def is_valid_gln(value: str) -> bool:
    """GLN: 13 Ziffern, EAN-13-Prüfziffer, kein Präfixzwang."""
    d = normalize_digits(value)
    if len(d) != 13:
        return False
    return ean13(d[:12]) == int(d[12])


# ---------------------------------------------------------------------------
# Modulo 11  ->  UID
# ---------------------------------------------------------------------------

_UID_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4)


def uid_check_digit(first8: str) -> int | None:
    """Prüfziffer der UID. None = Ergebnis 10, solche Nummern werden nie vergeben."""
    if len(first8) != 8 or not first8.isdigit():
        raise ValueError("UID erwartet genau 8 Ziffern vor der Prüfziffer")
    total = sum(int(d) * w for d, w in zip(first8, _UID_WEIGHTS))
    check = 11 - (total % 11)
    if check == 10:
        return None
    return 0 if check == 11 else check


def is_valid_uid(value: str) -> bool:
    """UID: CHE + 8 Ziffern + Prüfziffer, Modulo 11."""
    cleaned = _NON_ALNUM.sub("", value).upper()
    # Suffixe MWST / TVA / IVA gehören zur Entität, nicht zur Zahl
    for suffix in ("MWST", "TVA", "IVA", "HR"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    if not cleaned.startswith("CHE"):
        return False
    digits = cleaned[3:]
    if len(digits) != 9 or not digits.isdigit():
        return False
    expected = uid_check_digit(digits[:8])
    return expected is not None and expected == int(digits[8])


# ---------------------------------------------------------------------------
# Modulo 97  ->  IBAN  (ISO 13616)
# ---------------------------------------------------------------------------

def is_valid_iban(value: str, countries: tuple[str, ...] = ("CH", "LI")) -> bool:
    """IBAN nach ISO 13616. Standardmässig auf CH/LI beschränkt (21 Zeichen)."""
    iban = _NON_ALNUM.sub("", value).upper()
    if len(iban) < 15 or len(iban) > 34:
        return False
    if not iban[:2].isalpha() or not iban[2:4].isdigit():
        return False
    if countries and iban[:2] not in countries:
        return False
    if iban[:2] in ("CH", "LI") and len(iban) != 21:
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(
        str(ord(c) - 55) if c.isalpha() else c for c in rearranged
    )
    if not numeric.isdigit():
        return False
    return int(numeric) % 97 == 1


# ---------------------------------------------------------------------------
# Modulo 10 rekursiv  ->  QR-Referenz / ESR
# ---------------------------------------------------------------------------

_MOD10_TABLE = (
    (0, 9, 4, 6, 8, 2, 7, 1, 3, 5),
    (9, 4, 6, 8, 2, 7, 1, 3, 5, 0),
    (4, 6, 8, 2, 7, 1, 3, 5, 0, 9),
    (6, 8, 2, 7, 1, 3, 5, 0, 9, 4),
    (8, 2, 7, 1, 3, 5, 0, 9, 4, 6),
    (2, 7, 1, 3, 5, 0, 9, 4, 6, 8),
    (7, 1, 3, 5, 0, 9, 4, 6, 8, 2),
    (1, 3, 5, 0, 9, 4, 6, 8, 2, 7),
    (3, 5, 0, 9, 4, 6, 8, 2, 7, 1),
    (5, 0, 9, 4, 6, 8, 2, 7, 1, 3),
)


def mod10_recursive(digits: str) -> int:
    """Prüfziffer nach Modulo 10 rekursiv (Tabellenverfahren)."""
    if not digits.isdigit():
        raise ValueError("Modulo 10 rekursiv erwartet nur Ziffern")
    carry = 0
    for d in digits:
        carry = _MOD10_TABLE[carry][int(d)]
    return (10 - carry) % 10


def is_valid_qr_reference(value: str) -> bool:
    """QR-Referenz: 27 Stellen, letzte ist die Prüfziffer."""
    d = normalize_digits(value)
    if len(d) != 27:
        return False
    return mod10_recursive(d[:26]) == int(d[26])


# ---------------------------------------------------------------------------
# Luhn  ->  Kreditkarte
# ---------------------------------------------------------------------------

def luhn_check_digit(payload: str) -> int:
    """Prüfziffer nach Luhn für die Stellen ohne Prüfziffer."""
    if not payload.isdigit():
        raise ValueError("Luhn erwartet nur Ziffern")
    total = 0
    for i, ch in enumerate(reversed(payload)):
        n = int(ch)
        if i % 2 == 0:  # Position der künftigen Prüfziffer ist ungerade
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - total % 10) % 10


def is_valid_creditcard(value: str) -> bool:
    """Kreditkarte: 12-19 Ziffern, Luhn."""
    d = normalize_digits(value)
    if not 12 <= len(d) <= 19:
        return False
    return luhn_check_digit(d[:-1]) == int(d[-1])


# ---------------------------------------------------------------------------
# Registrierung: Tag -> Validator (wird von den Recognizern konsumiert)
# ---------------------------------------------------------------------------

VALIDATORS = {
    "AHVN13": is_valid_ahvn13,
    "GLN": is_valid_gln,
    "UID": is_valid_uid,
    "IBAN": is_valid_iban,
    "QR_REFERENCE": is_valid_qr_reference,
    "CREDITCARD": is_valid_creditcard,
}
