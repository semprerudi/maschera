"""Das Modell finden — und wenn es fehlt, es holen. Auf Befehl, nie von selbst.

    from core import modell
    ort = modell.suche("ch-v63b")          # None, wenn es fehlt
    m   = modell.manifest("ch")            # woher, wie gross, welche Pruefsumme
    modell.hole(m, ziel, melde=...)        # holt und prueft

Es gibt zwei Zuschnitte, und sie unterscheiden sich nur hier:

  fett     Die Gewichte liegen im Paket, neben dem Code (`runs/<name>`).
           So faehrt die AppImage und so faehrt das Docker-Abbild.

  schlank  Das Paket bringt nur den Code. Beim ersten Start fehlt das
           Modell, und der Anwender wird GEFRAGT.

Nach dem Holen sind beide gleich: im Betrieb geht nichts nach aussen.

**Der erste Start fragt — er laedt nicht.** 1,2 GB ueber ein Datenabo
sind ein echter Schaden. Ein Programm, das das ungefragt anrichtet, hat
sein Vertrauen verspielt — bei einem Datenschutzwerkzeug doppelt.

**Kein schlankes Paket ohne Fenster.** Ohne Anzeige kann die Frage nicht
gestellt werden. Auf einem Server heisst die Antwort Docker, und dort
faehrt das Modell mit. `suche()` und `hole()` wissen trotzdem nichts von
Fenstern, damit die Pruefung sie ohne Anzeige testen kann.

**Halb geholt ist nicht geholt.** Jede Datei wandert unter einem
Arbeitsnamen herunter, wird geprueft und erst dann an ihren Platz
umbenannt. Bricht es ab, bleibt nichts Halbes liegen, das beim naechsten
Start wie ein fertiges Modell aussieht.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from core import pfade

WURZEL = Path(__file__).resolve().parent.parent

# Was ein brauchbares Modellverzeichnis enthalten MUSS. `training_args.bin`
# steht bewusst nicht darin: die Datei sagt, wie trainiert wurde, und wird
# beim Erkennen nicht angefasst.
PFLICHT = ("config.json", "model.safetensors", "tokenizer.json",
           "tokenizer_config.json", "pack.json")

# Wie gross ein Stueck ist, das am Stueck gelesen wird. 1 MB: gross genug,
# dass der Aufwand je Stueck verschwindet, klein genug, dass die Anzeige
# sich bewegt und ein Abbruch schnell greift.
BROCKEN = 1024 * 1024


class Abgelehnt(Exception):
    """Das Modell laesst sich so nicht holen oder nicht glauben.

    Traegt einen Schluessel wie die Hinweise in `core/hinweise.py`: das
    Onboarding spricht vier Sprachen, dieses Modul eine. Der Schluessel
    wandert, nicht der Satz. Der deutsche Text bleibt als `str(...)` fuer die
    Kommandozeile.
    """

    def __init__(self, text: str, schluessel: str = "", **werte):
        super().__init__(text)
        self.schluessel = schluessel
        self.werte = {k: str(v) for k, v in werte.items()}


# ---------------------------------------------------------------------------
# Finden
# ---------------------------------------------------------------------------

def vollstaendig(ort: Path) -> bool:
    """Liegt dort ein Modell, dem man ansieht, dass es fertig ist?

    Geprueft wird auf die Pflichtdateien und nicht darauf, ob das Verzeichnis
    existiert. Ein leeres Modellverzeichnis entsteht beim ersten Anlauf und
    saehe sonst aus wie ein Modell.
    """
    return ort.is_dir() and all((ort / d).is_file() for d in PFLICHT)


def suche(name: str) -> Path | None:
    """Wo das Modell liegt — oder `None`.

    Zwei Orte, in dieser Reihenfolge:

      1. `runs/<name>` neben dem Code. Das fette Paket.
      2. `~/.local/share/maschera/modelle/<name>`. Das nachgeholte.

    Das Paket zuerst: wer eine AppImage benutzt, soll nicht eine nachgeholte
    Fassung von irgendwann bekommen, nur weil sie auch daliegt.
    """
    for ort in (WURZEL / "runs" / name, pfade.modell(name)):
        if vollstaendig(ort):
            return ort
    return None


# ---------------------------------------------------------------------------
# Das Manifest
# ---------------------------------------------------------------------------

def modell_ziel(name: str) -> Path:
    """Wohin ein nachgeholtes Modell gehoert.

    Eine eigene Funktion, damit der Aufrufer nicht `pfade` importieren muss,
    um den Ort zu kennen.
    """
    return pfade.modell(name)


def manifest(pack: str = "ch") -> dict:
    """Woher das Modell kommt, wie gross es ist, welche Pruefsummen gelten.

    Das steht im Pack und nicht hier: das Modell gehoert zum Pack, und ein
    zweiter Pack braeuchte ein anderes.
    """
    datei = WURZEL / "packs" / pack / "modell.json"
    if not datei.is_file():
        raise Abgelehnt(
            f"Kein Modell-Manifest fuer Pack {pack!r} ({datei}). "
            f"`python3 tools/modell_manifest.py --pack {pack} "
            f"--aus runs/<name>` erzeugt es.")
    m = json.loads(datei.read_text(encoding="utf-8"))
    fehlend = [d for d in PFLICHT if d not in m.get("dateien", {})]
    if fehlend:
        raise Abgelehnt(
            f"Das Manifest kennt {fehlend} nicht — ohne sie laeuft die "
            f"Erkennung nicht, und ein halbes Modell zu holen waere "
            f"schlimmer als keines.")
    return m


def groesse(m: dict) -> int:
    """Wieviele Bytes zu holen sind. Fuer die Frage VOR dem Holen."""
    return sum(int(d["bytes"]) for d in m["dateien"].values())


# ---------------------------------------------------------------------------
# Holen
# ---------------------------------------------------------------------------

def _pruefsumme(pfad: Path) -> str:
    h = hashlib.sha256()
    with pfad.open("rb") as fh:
        while brocken := fh.read(BROCKEN):
            h.update(brocken)
    return h.hexdigest()


def _grund(fehler: Exception) -> str:
    """Aus einem Netzfehler einen Satz machen, der ans richtige Ende schickt.

    Hugging Face antwortet mit 401 auch auf ein Repositorium, das es nicht
    gibt oder das nicht oeffentlich ist, weil es dessen Existenz nicht
    verraten will. Wer «401 Unauthorized» woertlich nimmt, sucht nach einem
    Zugangsschluessel, den es nicht braucht. Eine Fehlermeldung ist ein
    Befund ueber die ANTWORT, nicht ueber die URSACHE; die Ursache wird
    danebengeschrieben, wo sie bekannt ist.

    Der Rohtext bleibt drin — ergaenzt wird, nicht ersetzt.
    """
    if isinstance(fehler, urllib.error.HTTPError):
        code = fehler.code
        if code in (401, 403):
            return (f"HTTP {code} — «nicht berechtigt». Das heisst bei "
                    f"Hugging Face AUCH: es gibt das Repositorium noch "
                    f"nicht, oder es ist privat. Ein Zugangsschluessel "
                    f"hilft dann nicht.")
        if code == 404:
            return (f"HTTP {code} — die Datei gibt es unter dieser Adresse "
                    f"nicht. Meist stimmt der Zweig oder der Dateiname im "
                    f"Manifest nicht.")
        if 500 <= code < 600:
            return (f"HTTP {code} — die Gegenstelle hat ein Problem, nicht "
                    f"du. Spaeter nochmals.")
        return f"HTTP {code}"
    grund = getattr(fehler, "reason", fehler)
    return f"keine Verbindung ({grund})"


def _grund_schluessel(fehler: Exception) -> tuple[str, dict]:
    """Derselbe Befund wie `_grund()`, aber als Schluessel und Werte.

    Zwei Funktionen, eine Einteilung: `_grund()` schreibt den deutschen Satz
    fuer die Kommandozeile, diese hier den Schluessel fuer die Oberflaeche.
    Sie muessen dieselben Faelle unterscheiden; `tests/test_modell.py` haelt
    das zusammen.
    """
    if isinstance(fehler, urllib.error.HTTPError):
        code = fehler.code
        if code in (401, 403):
            return "m_f_nicht_berechtigt", {"code": code}
        if code == 404:
            return "m_f_nicht_gefunden", {"code": code}
        if 500 <= code < 600:
            return "m_f_gegenstelle", {"code": code}
        return "m_f_http", {"code": code}
    # Ohne den Rohtext des Netzes: «[Errno 11001] getaddrinfo failed» ist
    # englisch und hilft niemandem, der italienisch liest. Die Kommandozeile
    # behaelt ihn ueber `_grund()`.
    return "m_f_keine_verbindung", {}


def _hole_datei(url: str, ziel: Path, erwartet: str, bytes_soll: int,
                melde=None, abbruch=None) -> None:
    """Eine Datei holen, pruefen, erst dann an ihren Platz legen.

    Die Pruefsumme wird WAEHREND des Ladens gebildet, nicht danach aus der
    Datei gelesen — sonst gingen 1,2 GB zweimal durch den Speicher.
    """
    arbeit = ziel.with_name(ziel.name + ".teil")
    h = hashlib.sha256()
    geholt = 0
    try:
        with urllib.request.urlopen(url, timeout=60) as antwort, \
                arbeit.open("wb") as fh:
            while brocken := antwort.read(BROCKEN):
                if abbruch is not None and abbruch():
                    raise Abgelehnt("abgebrochen", "m_f_abgebrochen")
                fh.write(brocken)
                h.update(brocken)
                geholt += len(brocken)
                if melde is not None:
                    melde(ziel.name, geholt, bytes_soll)
    except urllib.error.URLError as e:
        arbeit.unlink(missing_ok=True)
        _s, _w = _grund_schluessel(e)
        raise Abgelehnt(f"{ziel.name}: {_grund(e)}", _s,
                        datei=ziel.name, **_w) from e
    except Abgelehnt:
        arbeit.unlink(missing_ok=True)
        raise
    except OSError as e:
        arbeit.unlink(missing_ok=True)
        raise Abgelehnt(f"{ziel.name} nicht schreibbar: {e}",
                        "m_f_nicht_schreibbar", datei=ziel.name) from e

    # Zuerst die Pruefsumme, dann umbenennen. Andersherum laege eine falsche
    # Datei am richtigen Platz, und `vollstaendig()` naehme sie beim naechsten
    # Start fuer bare Muenze.
    ist = h.hexdigest()
    if ist != erwartet:
        arbeit.unlink(missing_ok=True)
        raise Abgelehnt(
            f"{ziel.name}: Pruefsumme stimmt nicht.\n"
            f"  erwartet {erwartet}\n  bekommen {ist}\n"
            f"  Die Datei wurde verworfen. Was nicht stimmt, wird nicht "
            f"geflickt.",
            "m_f_pruefsumme", datei=ziel.name)
    if geholt != bytes_soll:
        arbeit.unlink(missing_ok=True)
        raise Abgelehnt(
            f"{ziel.name}: {geholt} Bytes statt {bytes_soll}.",
            "m_f_groesse", datei=ziel.name)
    arbeit.replace(ziel)


def hole(m: dict, ziel: Path, melde=None, abbruch=None) -> Path:
    """Das ganze Modell holen. Wirft `Abgelehnt`, wenn etwas nicht stimmt.

    `melde(name, geholt, soll)` treibt die Anzeige, `abbruch()` bricht ab.
    Beide duerfen fehlen — dann laeuft es still bis zum Ende durch.

    Gibt den Ort zurueck, an dem das Modell liegt.
    """
    ziel.mkdir(parents=True, exist_ok=True)
    for name in PFLICHT:
        eintrag = m["dateien"][name]
        fertig = ziel / name
        # Schon da und richtig? Dann nicht nochmal. Ein abgebrochener Lauf soll
        # beim zweiten Anlauf nicht wieder bei null anfangen.
        if fertig.is_file() and _pruefsumme(fertig) == eintrag["sha256"]:
            if melde is not None:
                melde(name, int(eintrag["bytes"]), int(eintrag["bytes"]))
            continue
        _hole_datei(m["quelle"].format(datei=name), fertig,
                    eintrag["sha256"], int(eintrag["bytes"]),
                    melde=melde, abbruch=abbruch)
    if not vollstaendig(ziel):
        raise Abgelehnt(f"{ziel} ist nach dem Holen unvollstaendig.",
                        "m_f_unvollstaendig")
    return ziel


def pruefe(ort: Path, m: dict) -> list[str]:
    """Was an einem vorhandenen Modell nicht stimmt. Leere Liste = alles gut.

    Nicht beim Start aufgerufen: 1,2 GB zu hashen dauert Sekunden. Gedacht
    fuer die Pruefung und fuer den Fall, dass jemand einen Verdacht hat.
    """
    schaeden = []
    for name in PFLICHT:
        pfad = ort / name
        if not pfad.is_file():
            schaeden.append(f"{name} fehlt")
            continue
        ist = _pruefsumme(pfad)
        soll = m["dateien"][name]["sha256"]
        if ist != soll:
            schaeden.append(f"{name}: {ist[:12]}… statt {soll[:12]}…")
    return schaeden
