"""Prompt-Vorlagen — benannte Prompts, die der Anwender wiederverwendet.

    from core import vorlagen
    liste = vorlagen.lade()          # [{"name": …, "text": …}, …]
    vorlagen.speichere(liste)        # prueft, bevor es schreibt

Aufbewahrt in `~/.config/maschera/vorlagen.json` — nicht im Projektbaum,
aus demselben Grund wie `klartext.json`.

⚠️ **Ein Prompt kann Personendaten enthalten.** «Fasse den Fall Brülhart
zusammen» ist eine Vorlage wie jede andere — und laege dann dauerhaft im
Klartext auf der Platte. Deshalb traegt jede Antwort des Endpunkts eine
`warnung`, und die Oberflaeche zeigt sie. Das Werkzeug kann es nicht
verhindern; es kann nur verhindern, dass es jemandem entgeht.
"""
from __future__ import annotations

import json
from pathlib import Path

from core import hinweise, pfade

PFAD = pfade.konfig("vorlagen.json")

# Grenzen. Nicht gegen Boesartigkeit — es ist die eigene Platte —, sondern
# damit eine versehentlich eingefuegte Datei nicht als Vorlage endet.
MAX_VORLAGEN = 50
MAX_NAME = 80
MAX_TEXT = 20_000


class Abgelehnt(hinweise.Abgelehnt):
    """Eine Vorlage, die so nicht gespeichert werden darf."""


def pruefe(roh) -> list[dict]:
    """WACHEN — was eine Vorlage nicht sein darf.

    1. **Ein leerer Name wird abgelehnt.** Eine namenlose Vorlage steht im
       Menue als leere Zeile; wer sie anklickt, ueberschreibt seinen Prompt
       mit etwas, das er nicht lesen konnte.

    2. **Namen sind einmalig.** Zwei gleichnamige Vorlagen sind im Menue
       nicht unterscheidbar — man waehlt die falsche und merkt es erst am
       fertigen Text.

    3. **Ganz oder gar nicht.** Eine kaputte Vorlage verwirft die ganze
       Anfrage. Sonst schriebe der Server eine andere Liste als die, die er
       bekommen hat, und meldete Erfolg.
    """
    if not isinstance(roh, list):
        raise Abgelehnt("Feld `vorlagen` fehlt oder ist keine Liste.",
                        schluessel="vorlagen_feld_fehlt")
    if len(roh) > MAX_VORLAGEN:
        raise Abgelehnt(f"Hoechstens {MAX_VORLAGEN} Vorlagen.",
                        schluessel="vorlagen_zu_viele", hoechstens=MAX_VORLAGEN)

    sauber: list[dict] = []
    gesehen: set[str] = set()
    for i, v in enumerate(roh, 1):
        if not isinstance(v, dict):
            raise Abgelehnt(f"Vorlage {i} ist kein Objekt.",
                            schluessel="vorlage_kein_objekt", nummer=i)
        name = v.get("name")
        text = v.get("text")
        if not isinstance(name, str) or not name.strip():
            raise Abgelehnt(f"Vorlage {i} hat keinen Namen.",
                            schluessel="vorlage_ohne_namen", nummer=i)
        if not isinstance(text, str) or not text.strip():
            raise Abgelehnt(f"Vorlage {i} ({name}) hat keinen Text.",
                            schluessel="vorlage_ohne_text", nummer=i, name=name)
        name = name.strip()
        if len(name) > MAX_NAME:
            raise Abgelehnt(
                f"Name laenger als {MAX_NAME} Zeichen: {name[:20]}…",
                schluessel="vorlage_name_zu_lang", hoechstens=MAX_NAME,
                name=name[:20] + "…")
        if len(text) > MAX_TEXT:
            raise Abgelehnt(
                f"Vorlage {name} laenger als {MAX_TEXT} Zeichen.",
                schluessel="vorlage_text_zu_lang", hoechstens=MAX_TEXT, name=name)
        schluessel = name.casefold()
        if schluessel in gesehen:
            raise Abgelehnt(f"Name zweimal vergeben: {name}",
                            schluessel="vorlage_name_doppelt", name=name)
        gesehen.add(schluessel)
        sauber.append({"name": name, "text": text})
    return sauber


def lade() -> list[dict]:
    """Gespeicherte Vorlagen. Fehlt oder kaputt -> leere Liste.

    Gelesen wird von `PFAD`, demselben Ort, an den `speichere` schreibt.
    """
    try:
        roh = json.loads(PFAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    try:
        return pruefe(roh.get("vorlagen", []))
    except Abgelehnt:
        # Eine von Hand verdorbene Datei macht das Werkzeug nicht
        # unbenutzbar — sie liefert keine Vorlagen, das ist alles.
        return []


def speichere(roh) -> Path:
    liste = pruefe(roh)
    PFAD.parent.mkdir(parents=True, exist_ok=True)
    PFAD.write_text(
        json.dumps({"vorlagen": liste}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return PFAD
