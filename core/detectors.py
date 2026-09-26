"""Erkenner, die sich nicht als Regex ausdruecken lassen.

Eine regexbasierte IBAN-Erkennung laesst den IBAN oft zum groessten Teil im
Klartext stehen, waehrend dem Anwender ein beruhigendes `[IBAN_1]` angezeigt
wird: das Muster hoert nach einer festen Zahl von Zeichen auf. Und ein Muster
nur fuer CH und LI uebersieht deutsche und italienische IBAN — in Schweizer
Rechnungen, Vertraegen und Grenzgaengerunterlagen Alltag.

Warum Regex hier nicht genuegt:

  Ein IBAN hat je Land eine FESTE Laenge (ISO 13616). Ein Muster, das
  "irgendwie 15 bis 34 Zeichen" nimmt, hoert entweder zu frueh auf — dann
  bleibt der Rest im Klartext — oder frisst den Nachbartext mit. Beides ist
  schlecht, und das erste ist gefaehrlich, weil es wie ein Erfolg aussieht.

  Der Erkenner liest deshalb das Laenderkuerzel, schlaegt die erwartete Laenge
  nach und konsumiert GENAU so viele alphanumerische Zeichen.
"""

from __future__ import annotations

import re

from core.masking import Span
from packs.ch.validators.checksums import is_valid_iban

# ISO 13616: Gesamtlaenge des IBAN je Land, Laenderkuerzel eingerechnet.
# Reine Daten — bei Aenderungen hier korrigieren, nicht im Code.
IBAN_LENGTHS = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BI": 27, "BR": 29, "BY": 28, "CH": 21, "CR": 22,
    "CY": 28, "CZ": 24, "DE": 22, "DJ": 27, "DK": 18, "DO": 28, "EE": 20,
    "EG": 29, "ES": 24, "FI": 18, "FK": 18, "FO": 18, "FR": 27, "GB": 22,
    "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28, "HN": 28, "HR": 21,
    "HU": 28, "IE": 22, "IL": 23, "IQ": 23, "IS": 26, "IT": 27, "JO": 30,
    "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21, "LT": 20, "LU": 20,
    "LV": 21, "LY": 25, "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MN": 20,
    "MR": 27, "MT": 31, "MU": 30, "NI": 28, "NL": 18, "NO": 15, "OM": 23,
    "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22,
    "RU": 33, "SA": 24, "SC": 31, "SD": 18, "SE": 24, "SI": 19, "SK": 24,
    "SM": 27, "SO": 23, "ST": 25, "SV": 28, "TL": 23, "TN": 24, "TR": 26,
    "UA": 29, "VA": 22, "VG": 24, "XK": 20,
}

# Nur die beiden LAENDERBUCHSTABEN als Anker, nicht Laenderkuerzel plus
# Pruefziffern. Sonst scheitert jede Gruppierung, die zwischen die vier
# fuehrenden Zeichen ein Trennzeichen setzt — bei 2er- und 3er-Gruppen also
# immer, und dann bleibt der ganze IBAN im Klartext. Ein Trennzeichen zwischen
# den beiden Buchstaben ist erlaubt; die Modulo-97-Pruefung faengt ab, was der
# lockere Anker zu viel einsammelt.
_START = re.compile(r"(?<![A-Za-z0-9])([A-Z])[ \t.\-]{0,2}([A-Z])")
_SEPARATOR = " \t-\u00a0\u2019'."


def _consume(text: str, start: int, needed: int) -> tuple[int, str] | None:
    """Ab `start` genau `needed` alphanumerische Zeichen einsammeln.

    Erlaubt Trennzeichen zwischen den Gruppen, hoechstens EINEN Zeilenumbruch.
    Verlangt gleichmaessige Gruppenlaengen — sonst laeuft der Erkenner in den
    Nachbartext oder liest eine Tabellenspalte als Code.
    """
    i = start
    collected: list[str] = []
    groups: list[int] = []
    current = 0
    newlines = 0

    while i < len(text) and len(collected) < needed:
        ch = text[i]
        if ch.isalnum():
            collected.append(ch.upper())
            current += 1
            i += 1
            continue
        if ch == "\n":
            newlines += 1
            if newlines > 1:
                return None
        elif ch not in _SEPARATOR:
            break
        # Trennzeichenfolge ueberspringen, aber nur eine
        if current:
            groups.append(current)
            current = 0
        i += 1
        while i < len(text) and text[i] in " \t":
            i += 1
        if i < len(text) and not text[i].isalnum():
            break

    if len(collected) != needed:
        return None
    if current:
        groups.append(current)

    # Kompaktform: eine Gruppe, immer zulaessig
    if len(groups) > 1:
        sizes = groups[:-1]
        if len(set(sizes)) != 1:
            return None
        if groups[-1] > sizes[0]:
            return None

    return i, "".join(collected)


def detect_iban(text: str) -> list[Span]:
    """IBAN in kompakter UND gruppierter Schreibweise, alle Laender."""
    found: list[tuple[int, int]] = []

    for m in _START.finditer(text):
        country = m.group(1) + m.group(2)
        needed = IBAN_LENGTHS.get(country)
        if not needed:
            continue
        got = _consume(text, m.start(), needed)
        if not got:
            continue
        end, compact = got
        if not is_valid_iban(compact, countries=()):
            continue
        # Nachgestellte Trennzeichen nicht mitnehmen
        while end > m.start() and not text[end - 1].isalnum():
            end -= 1
        found.append((m.start(), end))

    # Ueberlappende Kandidaten vereinigen. Einen davon zu verwerfen liesse ein
    # Stueck des anderen im Klartext stehen — unter einem beruhigenden
    # Platzhalter, was schlimmer ist als gar keine Maskierung.
    merged: list[tuple[int, int]] = []
    for a, b in sorted(found):
        if merged and a < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))

    return [Span("IBAN", a, b, source="regex") for a, b in merged]


DETECTORS = {"IBAN": detect_iban}
