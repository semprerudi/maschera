"""Adapter fuer den Country Pack CH.

Implementiert das Interface aus SPEC §12. Die gesamte Laenderlogik steckt
in den YAML-Dateien des Packs (`taxonomy.yaml`, `patterns.yaml`,
`macros.yaml`, `bezeichnungen.yaml`), nicht hier.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

PACK_DIR = Path(__file__).parent
VALID_STAGES = {1, 2, 3}
VALID_ACTIONS = {"mask", "tag_only"}
VALID_BUDGETS = {"R", "A", "P"}


@dataclass(frozen=True)
class Tag:
    tag: str
    stage: int
    action: str
    budget: str | None
    bspd: bool
    override: str | None
    note: str | None
    placeholder: str | None  # lesbare Bezeichnung, nur bei action == mask
    index: int  # 1-basierte Position im eingefrorenen Labelvertrag


@lru_cache(maxsize=1)
def _load_taxonomy() -> dict:
    with (PACK_DIR / "taxonomy.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def get_tags() -> tuple[Tag, ...]:
    """Alle Tags in der eingefrorenen Reihenfolge."""
    raw = _load_taxonomy()["tags"]
    return tuple(
        Tag(
            tag=entry["tag"],
            stage=entry["stage"],
            action=entry["action"],
            budget=entry.get("budget"),
            bspd=entry.get("bspd", False),
            override=entry.get("override"),
            note=entry.get("note"),
            placeholder=entry.get("placeholder"),
            index=i,
        )
        for i, entry in enumerate(raw, start=1)
    )


@lru_cache(maxsize=1)
def get_labels() -> tuple[str, ...]:
    """BIO-Liste in stabiler Reihenfolge: O, B-/I- je Tag.

    Diese Reihenfolge ist Vertrag. Siehe Kopf von taxonomy.yaml.
    """
    labels = ["O"]
    for tag in get_tags():
        labels.append(f"B-{tag.tag}")
        labels.append(f"I-{tag.tag}")
    return tuple(labels)


def get_label_hash() -> str:
    """Fingerabdruck der Labelliste, wandert in jeden Checkpoint (SPEC §12)."""
    joined = "\n".join(get_labels()).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


SPRACHEN = ("de", "fr", "it", "en")


@lru_cache(maxsize=1)
def _bezeichnungen() -> dict:
    pfad = PACK_DIR / "bezeichnungen.yaml"
    if not pfad.is_file():
        return {}
    with pfad.open(encoding="utf-8") as fh:
        return dict((yaml.safe_load(fh) or {}).get("bezeichnungen", {}))


def get_bezeichnungen(sprache: str = "de") -> dict[str, str]:
    """Tag -> Bezeichnung in dieser Sprache. Fuer Legende und Kontextmenue.

    Bewusst NICHT Teil des Labelvertrags: wie ein Tag heisst, darf sich
    aendern, ohne dass ein Checkpoint ungueltig wird.

    **Kein Rueckfall auf Deutsch bei fehlender Uebersetzung.** Eine
    franzoesische Oberflaeche mit einzelnen deutschen Menueeintraegen sieht
    aus wie ein Versehen, ein leerer Eintrag wie ein Fehler — und nur der
    Fehler wird gemeldet. `check_taxonomy.py` prueft deshalb auf
    Vollstaendigkeit in ALLEN vier Sprachen.
    """
    if sprache not in SPRACHEN:
        raise ValueError(f"unbekannte Sprache {sprache!r}, verfuegbar: {SPRACHEN}")
    return {tag: eintrag.get(sprache)
            for tag, eintrag in _bezeichnungen().items()
            if eintrag.get(sprache)}


def get_actions() -> dict[str, str]:
    """ACTION_MAP: maskieren oder nur taggen. Ohne Neutraining änderbar."""
    return {t.tag: t.action for t in get_tags()}


def get_thresholds() -> dict[str, float]:
    """Entscheidungsschwelle je Tag: Budget als Vorgabe, Tag als Ausnahme.

    Die drei Budgets R/A/P sind der Normalfall und eine echte Vereinfachung —
    sie zwingen dazu, ueber SCHUTZKLASSEN nachzudenken statt ueber 39
    Einzelzahlen. Ein Tagname in der Schwellentabelle ueberschreibt sein
    Budget.

    **Eine Ausnahme braucht eine Messung**, festgehalten neben dem Wert in
    `taxonomy.yaml`. Jede Ausnahme hoehlt die Vereinfachung ein Stueck aus;
    nach zehn Ausnahmen hat man wieder 39 Zahlen, und niemand weiss mehr,
    welche gemessen und welche geraten sind.
    """
    table = _load_taxonomy()["thresholds"]
    werte = {}
    for t in get_tags():
        if t.tag in table:                    # Ausnahme je Tag
            werte[t.tag] = float(table[t.tag])
        elif t.budget is not None:            # Vorgabe ueber das Budget
            werte[t.tag] = float(table[t.budget])
    return werte


def get_placeholders() -> dict[str, str]:
    """Tag -> lesbare Platzhalterbezeichnung. Nur für maskierte Tags."""
    return {t.tag: t.placeholder for t in get_tags() if t.placeholder}


def validate() -> list[str]:
    """Prüft den Labelvertrag. Leere Liste = alles in Ordnung."""
    problems: list[str] = []
    tags = get_tags()
    names = [t.tag for t in tags]

    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        problems.append(f"doppelte Tags: {sorted(duplicates)}")

    for t in tags:
        if t.stage not in VALID_STAGES:
            problems.append(f"{t.tag}: unbekannte Stufe {t.stage}")
        if t.action not in VALID_ACTIONS:
            problems.append(f"{t.tag}: unbekannte Aktion {t.action!r}")
        if t.stage == 1:
            if t.budget is not None:
                problems.append(f"{t.tag}: Stufe 1 darf kein Budget tragen")
            if t.override != "checksum":
                problems.append(f"{t.tag}: Stufe 1 verlangt override=checksum")
        else:
            if t.budget not in VALID_BUDGETS:
                problems.append(f"{t.tag}: unbekanntes Budget {t.budget!r}")
            if t.override is not None:
                problems.append(f"{t.tag}: Override nur auf Stufe 1 zulässig")

    seen_ph: dict[str, str] = {}
    for t in tags:
        if t.action == "mask":
            if not t.placeholder:
                problems.append(f"{t.tag}: maskiertes Tag ohne Platzhalter")
                continue
            ph = t.placeholder
            # ASCII, Grossbuchstaben, Ziffern und Unterstrich.
            #
            # Die Platzhalter tragen die englischen TAGNAMEN (`[QR_REFERENCE_1]`),
            # damit sie bei einer franzoesischen oder italienischen Oberflaeche nicht
            # mituebersetzt werden muessen.
            #
            # Keine Leerzeichen, keine Umlaute, keine Satzzeichen: der Platzhalter muss
            # ein Wort bleiben, das ein Sprachmodell unveraendert zurueckgibt und die
            # Rueckwandlung wiederfindet.
            if not ph.isascii() or not ph.replace("_", "").isalnum():
                problems.append(
                    f"{t.tag}: Platzhalter {ph!r} muss ASCII, alphanumerisch "
                    "oder Unterstrich sein"
                )
            if ph != ph.upper():
                problems.append(
                    f"{t.tag}: Platzhalter {ph!r} muss GROSS geschrieben sein — "
                    "sonst faellt er im Text nicht auf"
                )
            if ph != t.tag:
                problems.append(
                    f"{t.tag}: Platzhalter {ph!r} weicht vom Tagnamen ab. "
                    "Sie sind gleich, damit die Oberflaeche "
                    "uebersetzbar bleibt, ohne die Platzhalter zu aendern."
                )
            if ph in seen_ph:
                problems.append(
                    f"{t.tag}: Platzhalter {ph!r} bereits von {seen_ph[ph]} belegt"
                )
            seen_ph[ph] = t.tag
        elif t.placeholder:
            problems.append(f"{t.tag}: tag_only darf keinen Platzhalter tragen")

    labels = get_labels()
    if len(labels) != 2 * len(tags) + 1:
        problems.append(f"Labelzahl {len(labels)} passt nicht zu {len(tags)} Tags")
    if len(set(labels)) != len(labels):
        problems.append("Labelliste enthält Duplikate")

    return problems
