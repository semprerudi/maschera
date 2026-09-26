"""Dauerhafte Klartext-Vorlieben — welche Tags erkannt, aber nicht ersetzt werden.

    from core import vorlieben
    tags = vorlieben.lade()              # {"DATE", "ORG"}
    vorlieben.speichere({"DATE"}, pack)  # prueft gegen die Taxonomie

Aufbewahrt in `~/.config/maschera/klartext.json` — nicht im Projektbaum.
Es ist eine Einstellung des Anwenders, keine Eigenschaft des Werkzeugs:
laege sie im Projekt, wanderte sie mit jeder Kopie mit, und ein Entscheid
fuer EIN Dokument gaelte stillschweigend fuer alle.

Zwei Wachen gehen ueber ein einfaches Abschalten hinaus — beide unter
`WACHEN` unten begruendet.
"""
from __future__ import annotations

import json
from pathlib import Path

# Ort nach XDG, nie im Projektverzeichnis — siehe `core/pfade.py`.
from core import hinweise, pfade

PFAD = pfade.konfig("klartext.json")


class Abgelehnt(hinweise.Abgelehnt):
    """Eine Vorliebe, die so nicht gesetzt werden darf."""


def _bspd_tags(pack) -> set[str]:
    return {t.tag for t in pack.get_tags() if t.bspd}


def _alle_tags(pack) -> set[str]:
    return {t.tag for t in pack.get_tags()}


def pruefe(tags: set[str], pack, auch_bspd: bool = False) -> set[str]:
    """WACHEN — was `--ohne` nicht darf.

    1. **Unbekannte Tags werden abgelehnt, nicht ignoriert.** Ein Tippfehler
       («DATUM» statt «DATE») wuerde sonst stillschweigend nichts bewirken,
       und der Anwender glaubte, das Datum bleibe im Klartext.

    2. **Besonders schuetzenswerte Personendaten brauchen `auch_bspd`.**
       `NATIONALITY`, `RELIGION` und die uebrigen `bspd`-Tags lassen sich
       abschalten, aber nicht beilaeufig. Bei einem Gesetzesdatum kostet ein
       Fehlgriff Lesbarkeit; bei der Religionszugehoerigkeit kostet er den
       Zweck des ganzen Werkzeugs. Die Abstufung des revDSG ist hier der
       richtige Massstab.
    """
    bekannt = _alle_tags(pack)
    unbekannt = sorted(t for t in tags if t not in bekannt)
    if unbekannt:
        raise Abgelehnt(
            f"Unbekannte Tags: {', '.join(unbekannt)}\n"
            f"Bekannt sind: {', '.join(sorted(bekannt))}",
            schluessel="vorliebe_tags_unbekannt",
            tags=", ".join(unbekannt),
            bekannt=", ".join(sorted(bekannt)))

    if not auch_bspd:
        heikel = sorted(tags & _bspd_tags(pack))
        if heikel:
            raise Abgelehnt(
                f"Besonders schuetzenswerte Personendaten: {', '.join(heikel)}\n"
                "Diese Tags bleiben nur mit --auch-bspd im Klartext.\n"
                "Bei einem Datum kostet ein Fehlgriff Lesbarkeit; hier kostet\n"
                "er den Zweck des Werkzeugs.",
                schluessel="vorliebe_bspd",
                tags=", ".join(heikel))
    return set(tags)


def lade() -> set[str]:
    """Gespeicherte Vorlieben. Fehlt oder kaputt -> leere Menge.

    Gelesen wird von `PFAD`, demselben Ort, an den `speichere` schreibt.
    """
    try:
        roh = json.loads(PFAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return set(roh.get("klartext", []))


def speichere(tags: set[str], pack, auch_bspd: bool = False) -> Path:
    tags = pruefe(set(tags), pack, auch_bspd)
    PFAD.parent.mkdir(parents=True, exist_ok=True)
    PFAD.write_text(
        json.dumps({"klartext": sorted(tags)}, ensure_ascii=False, indent=2)
        + "\n", encoding="utf-8")
    return PFAD


def legende(pack) -> str:
    """Welche Tags es gibt, was sie bedeuten, welche heikel sind.

    Ohne solche Liste ist `--ohne` unbenutzbar: man muesste die Tagnamen
    raten.
    """
    z = ["Tags dieses Packs. `--ohne TAG` laesst eines im KLARTEXT —",
         "erkannt wird es weiterhin, nur nicht ersetzt.", ""]
    z.append(f"{'Tag':<20}{'St':>3}{'Aktion':>10}{'Budget':>8}  bspd")
    for t in pack.get_tags():
        marke = "  ⚠ besonders schuetzenswert" if t.bspd else ""
        z.append(f"{t.tag:<20}{t.stage:>3}{t.action:>10}"
                 f"{(t.budget or '—'):>8}{marke}")
    z.append("")
    z.append("⚠ markierte Tags brauchen zusaetzlich --auch-bspd.")
    z.append(f"Dauerhaft merken: --klartext-merken. Datei: {PFAD}")
    return "\n".join(z)
