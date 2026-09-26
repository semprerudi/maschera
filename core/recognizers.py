"""Regex-Recognizer mit Kontextankern und Prüfsummen (SPEC §3, §5).

Rollenteilung aus Architekturprinzip 3: Das neuronale Modell ist die
Recall-Engine, die Regex die Precision-Garantie.

Zwei Stufen, zwei Verhaltensweisen:

  Stufe 1  Muster findet Kandidaten, die Prüfsumme entscheidet. Gültig ->
           maskieren, auch wenn das Modell schweigt. Ungültig -> verwerfen,
           auch wenn das Modell anschlägt.

  Stufe 2  Muster findet Kandidaten, der Kontextanker entscheidet. Kein
           Override — der Treffer geht als Vorschlag ins Zusammenführen mit
           den Modelltreffern.

Ein Anker ist ein Wort im Fenster VOR der Fundstelle (bei `anchor_after` auch
danach). Negativanker (`anchor_not`) verwerfen einen Treffer — das Gegenstück
zu den ~threshold-Decoys aus SPEC §8.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from core.detectors import DETECTORS
from core.masking import Span
from packs.ch.validators.checksums import VALIDATORS

__all__ = ["Recognizer", "load_recognizers", "recognize"]


# Umlautersatz ist im Schweizer Schriftverkehr allgegenwaertig: Altsysteme,
# ASCII-Exporte und OCR liefern "Gebuehr" statt "Gebühr", "Grundstueck" statt
# "Grundstück", "Identitaetskarte" statt "Identitätskarte". Ein Anker, der nur
# die Umlautform kennt, greift dort nicht — und ein NEGATIVanker, der nicht
# greift, laesst einen Falsch-Positiven durch.
_TRANSLIT = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
             "à": "a", "é": "e", "è": "e", "ê": "e", "î": "i",
             "ô": "o", "û": "u", "ç": "c", "’": "'"}


def anchor_variants(word: str) -> set[str]:
    """Schreibvarianten eines Ankerworts: Original, Umlautersatz, diakritikafrei.

    Bewusst am WORT und nicht am Text angewendet: faltete man den Text, wuerden
    sich die Zeichenpositionen verschieben (ue ist zwei Zeichen, ü eines) und
    die Spannen saessen daneben.
    """
    low = word.lower()
    out = {low}
    out.add("".join(_TRANSLIT.get(c, c) for c in low))
    stripped = unicodedata.normalize("NFD", low)
    out.add("".join(c for c in stripped if not unicodedata.combining(c)))
    return {v for v in out if v}


@dataclass(frozen=True)
class Recognizer:
    tag: str
    stage: int
    regex: re.Pattern
    validator: str | None
    anchor_words: tuple[str, ...]
    anchor_required: bool
    anchor_window: int
    anchor_after: bool
    anchor_same_line: bool
    anchor_max_distance: int | None
    anchor_not: tuple[str, ...]

    def trim_to_anchor(self, text: str, start: int, end: int) -> int:
        """Neuer Startpunkt hinter dem letzten Ankerwort INNERHALB des Treffers.

        Zwei Faelle, beide real:

          "Heimatort Biel/Bienne BE"     Muster verschluckt sein eigenes Etikett
          "Er ist von Hautemorges VD"    Satzanfang ist auch gross, also frisst
                                         das mehrwortfaehige Muster "Er ist von"
                                         gleich mit

        In beiden Faellen steht der Anker danach nicht mehr VOR der Fundstelle
        und die Pruefung schlaegt fehl — obwohl er da ist. Das Ankerwort gehoert
        ohnehin nie zur Entitaet, also wird davor abgeschnitten.

        Wortgrenzen sind zwingend: sonst schneidet "von" mitten in "Vonderweid".
        """
        if not self.anchor_words:
            return start
        span = text[start:end]
        low = span.lower()
        best = 0
        for w in self.anchor_words:
            pos = 0
            while (pos := low.find(w, pos)) != -1:
                left_ok = pos == 0 or not low[pos - 1].isalnum()
                right = pos + len(w)
                right_ok = right >= len(low) or not low[right].isalnum()
                if left_ok and right_ok:
                    best = max(best, right)
                pos = right
        if not best:
            return start
        while best < len(span) and not span[best].isalnum():
            best += 1
        return start + best if best < len(span) else start

    def anchor_distance(self, text: str, start: int, end: int) -> int | None:
        """Zeichenabstand zum naechsten Anker, None wenn keiner da ist.

        Das Fenster endet an der Absatzgrenze. Ohne diese Schranke greift ein
        Formularfeld auf das Etikett der vorherigen Zeile zu und "BFS-Nr. 351"
        wird zusaetzlich als EGID erkannt, weil zwei Zeilen darueber "EGID:"
        steht.
        """
        if not self.anchor_words:
            return 0

        window_start = max(0, start - self.anchor_window)
        before = text[window_start:start]
        cut = before.rfind("\n") if self.anchor_same_line else before.rfind("\n\n")
        if cut != -1:
            before = before[cut + (1 if self.anchor_same_line else 2) :]
        low = before.lower()
        best = None
        for w in self.anchor_words:
            pos = low.rfind(w)
            if pos != -1:
                dist = len(before) - (pos + len(w))
                best = dist if best is None else min(best, dist)

        if self.anchor_after:
            after = text[end : end + self.anchor_window]
            cut = after.find("\n\n")
            if cut != -1:
                after = after[:cut]
            low = after.lower()
            for w in self.anchor_words:
                pos = low.find(w)
                if pos != -1:
                    best = pos if best is None else min(best, pos)

        return best

    def has_anchor(self, text: str, start: int, end: int) -> bool:
        distance = self.anchor_distance(text, start, end)
        if distance is None:
            return False
        # Manche Etiketten binden nur das UNMITTELBAR folgende Wort. Ohne
        # Hoechstabstand faengt "Login mmueller seit gestern" auch "seit" und
        # "gestern" ein — jedes Wort im Fenster wird zum Benutzernamen.
        if self.anchor_max_distance is not None:
            return distance <= self.anchor_max_distance
        return True

    def blocked(self, text: str, start: int, end: int) -> bool:
        if not self.anchor_not:
            return False
        window = text[
            max(0, start - self.anchor_window) : end + self.anchor_window
        ].lower()
        return any(w in window for w in self.anchor_not)


@lru_cache(maxsize=4)
def load_recognizers(pack: str = "ch") -> tuple[Recognizer, ...]:
    path = Path(__file__).resolve().parent.parent / "packs" / pack / "patterns.yaml"
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    out: list[Recognizer] = []
    for tag, spec in data["patterns"].items():
        flags = re.IGNORECASE if "i" in (spec.get("flags") or "") else 0
        anchor = spec.get("anchor") or {}
        out.append(
            Recognizer(
                # Ein Tag darf MEHRERE Muster haben. Der YAML-Schluessel muss
                # eindeutig sein, das Tag nicht — sonst braeuchte man kuenstliche
                # Tags wie USERNAME_LABELLED, die im Labelvertrag gar nicht
                # existieren und beim Ausrichten mit KeyError abstuerzen.
                tag=spec.get("tag", tag),
                stage=spec["stage"],
                regex=re.compile(spec["pattern"], flags),
                validator=spec.get("validator"),
                anchor_words=tuple(sorted(
                    {v for w in anchor.get("words", ()) for v in anchor_variants(w)}
                )),
                anchor_required=bool(anchor.get("required", False)),
                anchor_window=int(spec.get("anchor_window", 40)),
                anchor_after=bool(spec.get("anchor_after", False)),
                anchor_same_line=bool(spec.get("anchor_same_line", False)),
                anchor_max_distance=spec.get("anchor_max_distance"),
                anchor_not=tuple(sorted(
                    {v for w in spec.get("anchor_not", ()) for v in anchor_variants(w)}
                )),
            )
        )
    return tuple(out)


def recognize(text: str, pack: str = "ch") -> list[Span]:
    """Alle Regex-Treffer als Spannen. Überlappungen löst der Maskierer auf."""
    candidates: dict[tuple[int, int], list[tuple[int, str]]] = {}

    # Erkenner, die sich nicht als Regex ausdruecken lassen
    extra: list[Span] = []
    for detector in DETECTORS.values():
        extra.extend(detector(text))
    for rec in load_recognizers(pack):
        for m in rec.regex.finditer(text):
            start, end = m.start(), m.end()

            if rec.anchor_words:
                start = rec.trim_to_anchor(text, start, end)

            if rec.blocked(text, start, end):
                continue

            if rec.validator:
                # Stufe 1: die Mathematik entscheidet, kompromisslos
                if not VALIDATORS[rec.validator](m.group(0)):
                    continue
                # Anker zusätzlich, wo die Prüfsumme allein zu schwach ist
                if rec.anchor_required and not rec.has_anchor(text, start, end):
                    continue
            elif rec.anchor_required and not rec.has_anchor(text, start, end):
                continue

            dist = rec.anchor_distance(text, start, end)
            candidates.setdefault((start, end), []).append(
                (dist if dist is not None else 10**6, rec.tag)
            )

    # Treffen mehrere verankerte Muster exakt dieselbe Spanne, gewinnt das
    # Muster, dessen Anker am naechsten steht.
    spans: list[Span] = []
    for (start, end), hits in candidates.items():
        best = min(h[0] for h in hits)
        for dist, tag in hits:
            if dist == best:
                spans.append(Span(tag, start, end, source="regex"))

    return sorted(spans + extra, key=lambda s: (s.start, -(s.end - s.start)))
