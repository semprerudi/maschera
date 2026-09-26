#!/usr/bin/env python3
"""WSGI-Einstieg fuer den Betrieb hinter einem richtigen Server.

    gunicorn --workers 1 --threads 8 --bind 0.0.0.0:4141 app.wsgi:anwendung

`app/app.py` startet den Flask-Entwicklungsserver, und der ist fuer einen
Betrieb im Netz nicht gedacht. Hinter einem Reverse Proxy laeuft
MASCHERA deshalb unter gunicorn.

EIN Arbeiter, nicht mehr. Die Kette traegt eine Sperre um sich selbst —
`Zustand.sperre` —, weil der `Mitschreiber` sich die Vertrauenswerte des
letzten Laufs merkt. Zwei PROZESSE haetten jeder ihre eigene Sperre und
ihr eigenes Modell: doppelter Speicher, und die Sperre schuetzte nicht
mehr, wozu sie da ist. Faeden statt Prozesse.

Die Einstellungen kommen aus der Umgebung, weil gunicorn keine eigenen
Argumente durchreicht. Fehlt `MASCHERA_MODELL`, bricht es ab — ein
Server, der still ohne Modell laeuft, ist eine Leckquelle mit gruener
Anzeige.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# `app.app`, nicht `app`. `app/` liegt auf dem Suchpfad UND ist als
# Namensraumpaket importierbar — `from app import …` ist damit zweideutig
# und trifft je nach Umgebung die falsche Seite:
#
#     ImportError: cannot import name 'baue_mit_oberflaeche' from 'app'
#
# Ein `__init__.py` daneben machte es schlimmer: dann waere `app` sicher
# das Paket und `app/app.py` nur noch ueber `app.app` erreichbar.
from app.app import baue_mit_oberflaeche  # noqa: E402
from serve import VERSION, Zustand  # noqa: E402

_modell = os.environ.get("MASCHERA_MODELL")
_onnx = os.environ.get("MASCHERA_ONNX")
_ohne = os.environ.get("MASCHERA_OHNE_MODELL") == "1"

if not (_modell or _onnx or _ohne):
    raise SystemExit(
        "ABBRUCH: keine der Umgebungsvariablen MASCHERA_MODELL, "
        "MASCHERA_ONNX oder MASCHERA_OHNE_MODELL=1 gesetzt.\n"
        "  Ohne Modell leckt jeder Name. Das ist kein Betriebszustand.")

_zustand = Zustand(
    os.environ.get("MASCHERA_PACK", "ch"),
    _modell, _onnx,
    int(os.environ.get("MASCHERA_MAX_LENGTH", "512")),
    os.environ.get("MASCHERA_REGELN") or None,
)
anwendung = baue_mit_oberflaeche(_zustand)

print(f"MASCHERA {VERSION} unter gunicorn · "
      f"Modell {_zustand.modellname or 'KEINES'}", file=sys.stderr)
if _zustand.ohne_modell:
    print("  ⚠ OHNE MODELL — Namen, Daten und Adressen bleiben im Klartext.",
          file=sys.stderr)
