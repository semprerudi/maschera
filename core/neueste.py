"""Nach der neuesten Fassung fragen — nur auf Klick, nur bei GitHub.

⚠️ DIE ZWEITE TUER NACH AUSSEN. Der Grundsatz heisst «kein Nachladen von
aussen»; dieser Weg ist eine benannte Ausnahme davon, und er ist so eng wie
moeglich gebaut:

- Er laeuft **nur**, wenn der Anwender im Burgermenue «Nach Updates suchen»
  waehlt. Kein Start, kein Zeitgeber, kein Hintergrund fragt hier.
- Er fragt **eine** feste Adresse. Die Oberflaeche schickt keine Adresse mit;
  der Server baut sie nicht aus der Anfrage. Sonst waere dieser Endpunkt ein
  Weg, den lokalen Server Adressen eigener Wahl abrufen zu lassen.
- Er schickt **nichts** mit ausser dem, was jede HTTP-Anfrage traegt. Kein
  Dokument, keine Einstellung, keine Kennung.
- Aus der Antwort wird **nur** die Fassungsnummer gelesen, und nur, wenn sie
  wie eine aussieht. Die Download-Adresse kommt nicht aus der Antwort, sondern
  aus `app/static/adressen.json`.

Die Oberflaeche selbst bleibt dabei bei `connect-src 'self'`: gefragt wird
ueber den eigenen Server, nicht aus dem Fenster.
"""
from __future__ import annotations

import json
import re
import urllib.request

# Das oeffentliche Repository. `tests/test_api.py` prueft, dass der Eintrag
# «Nach Updates suchen» in `adressen.json` auf dasselbe zeigt.
REPO = "semprerudi/maschera"
ADRESSE = f"https://api.github.com/repos/{REPO}/releases/latest"

# Die Antwort ist ein paar Kilobyte; mehr wird nicht gelesen.
HOECHSTENS = 1024 * 1024
WARTEN_S = 8

_FASSUNG = re.compile(r"v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})")


class NichtErreichbar(Exception):
    """GitHub antwortet nicht — kein Netz, Docker ohne Ausgang, Sperre."""


class Unlesbar(Exception):
    """GitHub antwortet, aber nicht mit einer Fassungsnummer."""


def zerlegen(fassung: str) -> tuple[int, int, int] | None:
    """`2.3.10` oder `v2.3.10` → (2, 3, 10). Alles andere → None."""
    m = _FASSUNG.fullmatch((fassung or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def _holen(adresse: str) -> bytes:
    anfrage = urllib.request.Request(adresse, headers={
        "Accept": "application/vnd.github+json",
        # GitHub weist Anfragen ohne User-Agent ab. Ohne Fassung: die Frage
        # soll nicht verraten, was hier laeuft.
        "User-Agent": "MASCHERA",
    })
    with urllib.request.urlopen(anfrage, timeout=WARTEN_S) as antwort:
        return antwort.read(HOECHSTENS + 1)


def nachsehen(holen=_holen) -> str:
    """Die neueste veroeffentlichte Fassung, z. B. `2.3.10`.

    `holen` ist austauschbar, damit die Pruefung ohne Netz laeuft.
    """
    try:
        roh = holen(ADRESSE)
    except Exception as e:  # jede Art, nicht anzukommen
        raise NichtErreichbar(type(e).__name__) from e
    if len(roh) > HOECHSTENS:
        raise Unlesbar("Antwort zu gross")
    try:
        daten = json.loads(roh)
    except ValueError as e:
        raise Unlesbar("kein JSON") from e
    marke = daten.get("tag_name") if isinstance(daten, dict) else None
    teile = zerlegen(marke) if isinstance(marke, str) else None
    if teile is None:
        raise Unlesbar("keine Fassungsnummer")
    return ".".join(str(x) for x in teile)


def ist_neuer(neueste: str, aktuell: str) -> bool:
    """Liegt `neueste` hinter `aktuell`? Unlesbares zaehlt als «nein»."""
    a, b = zerlegen(neueste), zerlegen(aktuell)
    return bool(a and b and a > b)
