"""Wo die Einstellungen des Anwenders, das Modell und die Golddokumente liegen.

Eine Stelle fuer alle drei Orte. Kein anderes Modul baut einen dieser Pfade
selbst — sonst gaebe es zwei Verwalter fuer denselben Ort, und einer
wuerde beim naechsten Umzug vergessen.
"""

from __future__ import annotations

import os
from pathlib import Path

NAME = "maschera"


# Windows hat kein `~/.config`. Es liesse sich dort anlegen, und das
# Werkzeug schriebe klaglos an einen Ort, an dem kein Windows-Programm
# etwas sucht und den keine Sicherung erfasst.
#
#   POSIX     XDG_CONFIG_HOME, sonst ~/.config
#   Windows   APPDATA (wandert mit dem Profil — Einstellungen sollen das)
#
# `XDG_CONFIG_HOME` gilt zuerst, auch unter Windows: wer sie setzt, meint
# es so, und die Pruefungen lenken damit die Einstellungen beiseite.
WINDOWS = os.name == "nt"


def _basis() -> Path:
    gesetzt = os.environ.get("XDG_CONFIG_HOME")
    if gesetzt:
        return Path(gesetzt)
    if WINDOWS:
        heim = os.environ.get("APPDATA")
        if heim:
            return Path(heim)
    return Path.home() / ".config"


def konfig(datei: str) -> Path:
    """Der Ort einer Einstellungsdatei des Anwenders."""
    return _basis() / NAME / datei


# --- Das Modell --------------------------------------------------------------
#
# Das Modell ist keine Einstellung, sondern Material des Programms: einmal
# geholt, danach unveraendert, jederzeit wieder zu holen. Deshalb
# `XDG_DATA_HOME` und nicht `XDG_CONFIG_HOME` — wer sein Heimatverzeichnis
# sichert, will 1,2 GB Gewichte nicht mit im Band haben.
#
# Und nicht ins Paketverzeichnis: `/usr/`, ein `.app`-Buendel und eine
# eingehaengte AppImage sind nur lesbar. Ein Werkzeug, das beim ersten
# Start nach root fragt, hat schon verloren.
#
# Die grossen Pakete legen das Modell weiter neben den Code (`runs/`).
# `suche()` in `core/modell.py` sieht an beiden Orten nach.


def daten(*teile: str) -> Path:
    """Der Ort fuer das, was das Programm sich selbst holt.

    Unter Windows `LOCALAPPDATA` und nicht `APPDATA`. Einstellungen
    duerfen mit einem wandernden Profil reisen, 1,2 GB Modellgewichte
    nicht — die sind maschinengebunden und jederzeit wieder zu holen. Wer
    sie ins wandernde Profil legt, schiebt sie bei jeder Anmeldung durchs
    Netz.
    """
    gesetzt = os.environ.get("XDG_DATA_HOME")
    if gesetzt:
        wurzel = Path(gesetzt)
    elif WINDOWS:
        heim = os.environ.get("LOCALAPPDATA")
        wurzel = Path(heim) if heim else Path.home() / ".local" / "share"
    else:
        wurzel = Path.home() / ".local" / "share"
    return wurzel.joinpath(NAME, *teile)


def modell(name: str) -> Path:
    """Wohin ein nachgeladenes Modell gehoert."""
    return daten("modelle", name)


# --- Golddokumente -----------------------------------------------------------
#
# Golddokumente sind echte Dokumente, und sie liegen AUSSERHALB des
# Projektbaums. Jede Operation, die ueber den Baum geht — `rglob`,
# `git add -A`, ein Tar, das Veroeffentlichungspaket —, erreicht sie so
# strukturell nicht.
#
# Der Ort:
#
#   1. `MASCHERA_GOLD`, falls gesetzt — ausdruecklich schlaegt vermutet.
#   2. Sonst der Datenordner des Programms (`daten("gold")`), derselbe
#      Grundort wie fuer ein nachgeholtes Modell.
#
# Fehlt das Verzeichnis, meldet `gold_lesen()` es. Ein stiller leerer Ort
# waere der gefaehrlichste Fall: eine Messung liefe ueber nichts und meldete
# «0 Lecks».

ARTEN = ("real", "markup")


def _gold_basis() -> Path:
    """Zur AUFRUFZEIT gelesen, nicht beim Import — sonst koennte die Pruefung
    `MASCHERA_GOLD` und `XDG_DATA_HOME` nicht setzen, ohne zu monkeypatchen.
    """
    gesetzt = os.environ.get("MASCHERA_GOLD")
    return Path(gesetzt) if gesetzt else daten("gold")


def gold_schreiben(pack: str, art: str) -> Path:
    """Der Ort, an den neue Golddokumente geschrieben werden."""
    if art not in ARTEN:
        raise ValueError(f"Art {art!r} gibt es nicht — {ARTEN}")
    return _gold_basis() / pack / art


def gold_lesen(pack: str, art: str) -> tuple[Path, str | None]:
    """Der Ort, von dem gelesen wird, und ein Hinweis, wenn dort nichts ist.

    Der Hinweis ist kein Schmuck: wer ihn nicht sieht, merkt erst an einer
    Messung ueber ein leeres Verzeichnis, dass der Pfad falsch war.
    """
    ort = gold_schreiben(pack, art)
    if ort.is_dir():
        return ort, None
    return ort, (f"Kein Testset unter {ort}. Liegt es woanders, "
                 f"MASCHERA_GOLD auf das Verzeichnis darueber setzen.")
