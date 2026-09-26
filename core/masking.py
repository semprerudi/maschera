"""Maskierung, Wörterbuch und Rückführung (SPEC §10).

Platzhalterformat:  [Bezeichnung_Nummer]      z.B. [FULLNAME_5], [AHVN13_5]

Drei Eigenschaften, die zusammengehören:

1. **Eine Spanne pro Entität, Trennzeichen inklusive.** `756.9217.0769.85` wird
   zu einem einzigen `[AHVN13_5]`, nicht zu vier Platzhaltern mit Punkten
   dazwischen.

2. **Koreferenz ist sichtbar.** Alle Vorkommen derselben Person teilen dieselbe
   Nummer. Kommt derselbe Name in verschiedenen Oberflächenformen vor
   (`Hans Meier`, später nur `Meier`), erhalten die Varianten einen
   Buchstabenzusatz: `[FULLNAME_5]` und `[FULLNAME_5b]`. Das Sprachmodell
   sieht damit, dass es dieselbe Person ist, und die Rückführung bleibt exakt.

3. **Die Rückführung ist verlustfrei.** `restore(mask(t)) == t` gilt zeichengenau.
   Das ist testbar und wird getestet.

Dieses Modul persistiert nichts. Das Wörterbuch ist ein Rückgabewert; wer es
aufbewahrt, entscheidet die Anwendung — auf einem Server gilt: zum Client
ausliefern, serverseitig sofort verwerfen.
"""

from __future__ import annotations

import bisect
import json
import re
from dataclasses import dataclass, field

__all__ = ["Span", "MaskResult", "mask", "restore", "propagate"]

# Der Namensteil darf UNTERSTRICHE enthalten, die Nummer steht am Schluss.
# Die Platzhalter tragen die englischen Tagnamen (`[PLACE_OF_ORIGIN_1]`),
# damit keine Oberflaeche sie mituebersetzen muss.
#
# `[^\W\d]` als erstes Zeichen: ein Buchstabe, kein Unterstrich, keine
# Ziffer. Sonst passte `[_1]` oder `[123_1]` ebenfalls.
#
# Der Namensteil erlaubt auch Kleinbuchstaben — wegen der Benutzerregeln.
# Sie vergeben ihren Platzhalter frei (`Dossier` -> `[Dossier_1]`), und ein
# Muster nur fuer Grossbuchstaben haette genau die Werte nicht mehr
# zurueckgewandelt, die der Anwender selbst als schuetzenswert benannt hat.
PLACEHOLDER_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9_]*)_(\d+[a-z]*)\]")

# Tags, deren Werte durchs ganze Dokument weiterverfolgt werden (SPEC §10).
PROPAGATE_TAGS = frozenset(
    {"FULLNAME", "GIVENNAME", "ORG", "HEALTHCARE_ORG", "STREET"}
)
# BUILDINGNUM bewusst NICHT: "12" wuerde jede 12 im Dokument einsammeln.

# Namensbestandteile unter dieser Länge werden nicht einzeln weiterverfolgt.
MIN_PART_LEN = 3


@dataclass(frozen=True)
class Span:
    tag: str
    start: int
    end: int
    canonical: str | None = None  # Wert, zu dem diese Spanne koreferent ist
    source: str = "model"  # model | regex | propagation

    def value(self, text: str) -> str:
        return text[self.start : self.end]


@dataclass
class MaskResult:
    text: str
    dictionary: dict[str, str] = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)

    def to_json(self, **kw) -> str:
        return json.dumps(self.dictionary, ensure_ascii=False, **kw)


# ---------------------------------------------------------------------------
# Überlappungen auflösen
# ---------------------------------------------------------------------------

class Belegung:
    """Belegte Stellen eines Textes — verschmolzen und nach Anfang sortiert.

    Die Frage «ist [a,b) belegt?» wird fuer jede Fundstelle gestellt. Gegen
    alle bisher belegten Stellen gefragt, waechst der Aufwand quadratisch mit
    der Textlaenge — bei 124 000 Zeichen Minuten statt Sekunden. Liegen die
    Stellen verschmolzen und sortiert, sind auch ihre ENDEN sortiert, und die
    Frage wird zu einer Suche mit `bisect`.

    VERSCHMOLZEN, nicht bloss sortiert: die hereinkommenden Spannen duerfen
    sich ueberlappen, und ohne Verschmelzen waere «die Enden sind sortiert»
    falsch — die Suche griffe still daneben. Fuer diese Frage ist das
    Verschmelzen verlustfrei: WELCHE Spanne belegt, spielt keine Rolle, nur
    DASS belegt ist.

    Eine Klasse, damit `tests/test_masking.py` Punkt 8 dasselbe prueft, was
    laeuft.
    """

    __slots__ = ("_anf", "_end")

    def __init__(self, spannen=()) -> None:
        self._anf: list[int] = []
        self._end: list[int] = []
        for a, b in spannen:
            self.belegen(a, b)

    def belegen(self, a: int, b: int) -> None:
        """[a,b) belegen und mit den Nachbarn verschmelzen."""
        i = bisect.bisect_left(self._end, a)
        j = bisect.bisect_right(self._anf, b)
        if i < j:                                # beruehrt Vorhandenes
            a = min(a, self._anf[i])
            b = max(b, self._end[j - 1])
            del self._anf[i:j]
            del self._end[i:j]
        self._anf.insert(i, a)
        self._end.insert(i, b)

    def frei(self, a: int, b: int) -> bool:
        """Ist zwischen `a` und `b` nichts belegt?"""
        # Erste Stelle, die hinter `a` endet. Faengt sie vor `b` an, ueberlappt sie.
        i = bisect.bisect_right(self._end, a)
        return i >= len(self._anf) or self._anf[i] >= b


def _priority(span: Span, stages: dict[str, int]) -> tuple[int, int]:
    """Kleiner ist besser: Stufe 1 schlägt Stufe 2 schlägt Stufe 3, dann Länge."""
    return (stages.get(span.tag, 9), -(span.end - span.start))


def resolve_overlaps(spans: list[Span], stages: dict[str, int]) -> list[Span]:
    # Dieselbe Frage wie in `propagate()`: `Belegung` beantwortet sie mit
    # einer Suche statt mit einem Durchlauf ueber alles bisher Behaltene. Das
    # Verschmelzen ist hier folgenlos — was behalten wird, ueberlappt sich per
    # Konstruktion nicht.
    behalten: list[Span] = []
    belegt = Belegung()
    for span in sorted(spans, key=lambda s: _priority(s, stages)):
        if not belegt.frei(span.start, span.end):
            continue
        belegt.belegen(span.start, span.end)
        behalten.append(span)
    return sorted(behalten, key=lambda s: s.start)


# ---------------------------------------------------------------------------
# Dokument-Propagation
# ---------------------------------------------------------------------------

def _occurrences(text: str, needle: str) -> list[tuple[int, int]]:
    """Vorkommen an Wortgrenzen. Zeilenumbrüche im Wert werden toleriert."""
    if not needle.strip():
        return []
    pattern = r"\s+".join(re.escape(part) for part in needle.split())
    return [
        (m.start(), m.end())
        for m in re.finditer(rf"(?<!\w){pattern}(?!\w)", text)
    ]


def propagate(text: str, spans: list[Span]) -> list[Span]:
    """Jeden erkannten Namen im ganzen Dokument weiterverfolgen (SPEC §10).

    Grösster einzelner Recall-Gewinn: Anreden kommen einmal vor, der Name
    viermal — in Tabellen, Unterschriftenblöcken, Verteilern, Kopfzeilen.
    """
    belegt = Belegung((sp.start, sp.end) for sp in spans)
    free = belegt.frei
    belegen = belegt.belegen
    added: list[Span] = []

    # Je Nadel nur einmal suchen. Je Fundstelle gibt es einen Seed, und
    # derselbe Name kommt oft zwanzigmal vor; `_occurrences` haengt nur an
    # `text` und `needle`, und `text` steht hier fest.
    fundstellen: dict[str, list[tuple[int, int]]] = {}

    def wo(needle: str) -> list[tuple[int, int]]:
        treffer = fundstellen.get(needle)
        if treffer is None:
            treffer = _occurrences(text, needle)
            fundstellen[needle] = treffer
        return treffer

    seeds = [s for s in spans if s.tag in PROPAGATE_TAGS]

    # 1. Der vollständige Wert an anderen Stellen
    for seed in seeds:
        value = seed.value(text)
        for a, b in wo(value):
            if free(a, b):
                belegen(a, b)
                added.append(
                    Span(seed.tag, a, b, canonical=value, source="propagation")
                )

    # 2. Einzelne Namensbestandteile — das nackte "Meier"
    for seed in seeds:
        if seed.tag not in ("FULLNAME", "ORG", "HEALTHCARE_ORG"):
            continue
        value = seed.value(text)
        parts = [p for p in re.split(r"[\s\-]+", value) if len(p) >= MIN_PART_LEN]
        if len(parts) < 2:
            continue  # einteiliger Wert, nichts zu zerlegen
        for part in parts:
            if not part[0].isupper():
                continue
            for a, b in wo(part):
                if free(a, b):
                    belegen(a, b)
                    added.append(
                        Span(seed.tag, a, b, canonical=value, source="propagation")
                    )

    return sorted(spans + added, key=lambda s: s.start)


# ---------------------------------------------------------------------------
# Maskieren
# ---------------------------------------------------------------------------

def mask(
    text: str,
    spans: list[Span],
    pack,
    do_propagate: bool = True,
    excluded: set[str] | None = None,
    mapping_enabled: bool = True,
    extra: dict | None = None,
) -> MaskResult:
    """Spannen durch Platzhalter ersetzen und das Woerterbuch aufbauen.

    `excluded` — Tags, die ERKANNT, aber nicht ersetzt werden. Zweck:
    Kontext behalten, den das Sprachmodell fuer eine brauchbare Antwort
    braucht. Eine grosse Behoerde oder Firma identifiziert niemanden, eine kleine
    Stelle unter Umstaenden eine Person. Die Grenze ist fachlich und gehoert
    deshalb dem Anwender, nicht dem Code.

    `mapping_enabled=False` — endgueltige Anonymisierung. Die Platzhalter
    werden weiterhin durchnummeriert, sagen also weiterhin, dass zwei
    Vorkommen dieselbe Person sind; das Woerterbuch bleibt aber leer, und
    damit ist der Wert nicht rekonstruierbar.
    """
    actions = dict(pack.get_actions())
    # `extra` traegt die Tags der Benutzerregeln (`X_<id>`). Sie stehen in
    # keiner taxonomy.yaml und duerfen dort auch nicht stehen — der
    # Labelvertrag beschreibt, was das MODELL vorhersagt.
    extra = extra or {}
    actions.update(extra.get("actions", {}))
    for tag in (excluded or ()):
        actions[tag] = "tag_only"
    labels = dict(pack.get_placeholders())
    labels.update(extra.get("placeholders", {}))
    stages = {t.tag: t.stage for t in pack.get_tags()}
    stages.update(extra.get("stages", {}))

    spans = resolve_overlaps(list(spans), stages)
    if do_propagate:
        spans = propagate(text, spans)
        spans = resolve_overlaps(spans, stages)

    masked = [s for s in spans if actions.get(s.tag) == "mask"]

    # Durchgang 1: Gruppen bilden, Reihenfolge des ersten Auftretens merken
    order: list[tuple[str, str]] = []
    members: dict[tuple[str, str], list[str]] = {}
    for span in masked:
        value = span.value(text)
        key = (span.tag, span.canonical or value)
        if key not in members:
            members[key] = []
            order.append(key)
        if value not in members[key]:
            members[key].append(value)

    # Durchgang 2: Platzhalter vergeben. Die kanonische Form erhaelt die
    # Basisnummer, Varianten den Buchstabenzusatz — unabhaengig davon, welche
    # Form zufaellig zuerst im Dokument steht.
    counter: dict[str, int] = {}
    assigned: dict[tuple[str, str], dict[str, str]] = {}
    dictionary: dict[str, str] = {}
    for key in order:
        tag, canonical = key
        counter[tag] = counter.get(tag, 0) + 1
        values = members[key]
        if canonical in values:
            values = [canonical] + [v for v in values if v != canonical]
        assigned[key] = {}
        for i, value in enumerate(values):
            suffix = "" if i == 0 else chr(ord("a") + i - 1)
            placeholder = f"[{labels[tag]}_{counter[tag]}{suffix}]"
            assigned[key][value] = placeholder
            if mapping_enabled:
                dictionary[placeholder] = value

    # Durchgang 3: ersetzen, von hinten nach vorne
    replacements: list[tuple[int, int, str]] = []
    for span in masked:
        value = span.value(text)
        key = (span.tag, span.canonical or value)
        replacements.append((span.start, span.end, assigned[key][value]))

    out = text
    for start, end, placeholder in sorted(replacements, reverse=True):
        out = out[:start] + placeholder + out[end:]

    return MaskResult(text=out, dictionary=dictionary, spans=spans)


# ---------------------------------------------------------------------------
# Rückführen
# ---------------------------------------------------------------------------

def restore(text: str, dictionary: dict[str, str], strict: bool = False) -> str:
    """Platzhalter durch die Originalwerte ersetzen.

    strict=True wirft, wenn ein Platzhalter im Text steht, der nicht im
    Wörterbuch ist — das passiert, wenn das Sprachmodell einen erfindet.
    """
    unknown: list[str] = []

    def sub(m: re.Match) -> str:
        ph = m.group(0)
        if ph in dictionary:
            return dictionary[ph]
        unknown.append(ph)
        return ph

    out = PLACEHOLDER_RE.sub(sub, text)
    if strict and unknown:
        raise ValueError(f"unbekannte Platzhalter: {sorted(set(unknown))}")
    return out
