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
import urllib.error
import urllib.request

# Das oeffentliche Repository. `tests/test_api.py` prueft, dass der Eintrag
# «Nach Updates suchen» in `adressen.json` auf dasselbe zeigt.
REPO = "semprerudi/maschera"
ADRESSE = f"https://api.github.com/repos/{REPO}/releases/latest"

# Die Antwort ist ein paar Kilobyte; mehr wird nicht gelesen.
HOECHSTENS = 1024 * 1024
WARTEN_S = 8

# Mit optionalem Vorabteil (`2.0.0-test.1`, seit 18.10.2026 fuer die
# Teststufe). Eine Vorabfassung ist AELTER als dieselbe Nummer ohne Zusatz —
# wie bei SemVer: wer `2.0.0-test.3` faehrt, bekommt `2.0.0` angeboten.
_FASSUNG = re.compile(
    r"v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})(?:-([0-9A-Za-z][0-9A-Za-z.]{0,30}))?")


class NichtErreichbar(Exception):
    """GitHub antwortet nicht — kein Netz, Docker ohne Ausgang, Sperre."""


class Begrenzt(Exception):
    """GitHub antwortet, aber begrenzt gerade (Abfragelimit erschoepft).

    Gemessen am 17.10.2026: ohne Anmeldung erlaubt GitHub 60 Abfragen je
    Stunde und Adresse, fuer das ganze Heimnetz zusammen. Danach kommt 403
    mit `X-RateLimit-Remaining: 0`. Bis 1.1 hiess das in der App «nicht
    erreichbar» — falsch, das Netz ging.
    """


class Unlesbar(Exception):
    """GitHub antwortet, aber nicht mit einer Fassungsnummer."""


def zerlegen(fassung: str) -> tuple[int, int, int] | None:
    """`8.7.60`, `v8.7.60` oder `8.7.60-test.1` → (8, 7, 60). Sonst None."""
    m = _FASSUNG.fullmatch((fassung or "").strip())
    return tuple(int(x) for x in m.groups()[:3]) if m else None


def _rang(fassung: str) -> tuple[int, int, int, int] | None:
    """Zum Vergleichen: die drei Zahlen und 1 fuer eine fertige Fassung,
    0 fuer eine Vorabfassung — so liegt `3.1.4-test.2` vor `3.1.4`."""
    m = _FASSUNG.fullmatch((fassung or "").strip())
    if not m:
        return None
    return (*(int(x) for x in m.groups()[:3]), 0 if m.group(4) else 1)


def _normal(fassung: str) -> str | None:
    """`v3.1.4-test.2` → `3.1.4-test.2`; der Vorabteil bleibt stehen."""
    m = _FASSUNG.fullmatch((fassung or "").strip())
    if not m:
        return None
    zahl = ".".join(str(int(x)) for x in m.groups()[:3])
    return zahl + (f"-{m.group(4)}" if m.group(4) else "")


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
    """Die neueste veroeffentlichte Fassung, z. B. `8.7.60`.

    `holen` ist austauschbar, damit die Pruefung ohne Netz laeuft.
    """
    try:
        roh = holen(ADRESSE)
    except urllib.error.HTTPError as e:
        # 403/429 mit erschoepftem Limit ist eine ANTWORT, kein Netzfehler.
        rest = (e.headers or {}).get("X-RateLimit-Remaining") if hasattr(e, "headers") else None
        if e.code in (403, 429) and (rest == "0" or e.code == 429):
            raise Begrenzt(f"HTTP {e.code}") from e
        raise NichtErreichbar(f"HTTP {e.code}") from e
    except Exception as e:  # jede andere Art, nicht anzukommen
        raise NichtErreichbar(type(e).__name__) from e
    if len(roh) > HOECHSTENS:
        raise Unlesbar("Antwort zu gross")
    try:
        daten = json.loads(roh)
    except ValueError as e:
        raise Unlesbar("kein JSON") from e
    marke = daten.get("tag_name") if isinstance(daten, dict) else None
    fassung = _normal(marke) if isinstance(marke, str) else None
    if fassung is None:
        raise Unlesbar("keine Fassungsnummer")
    return fassung


def ist_neuer(neueste: str, aktuell: str) -> bool:
    """Liegt `neueste` hinter `aktuell`? Unlesbares zaehlt als «nein»."""
    a, b = _rang(neueste), _rang(aktuell)
    return bool(a and b and a > b)
