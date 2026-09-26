"""Der Einstieg der Windows-Fassung.

PyInstaller friert nur diese Datei ein. Der Quellcode von MASCHERA liegt
unveraendert als Daten neben ihr (`maschera/app`, `core`, `packs`, `tools`,
`runs`) und wird von dort ausgefuehrt — genau wie in der AppImage. Damit
stimmen alle Pfade, die `app/fenster.py` und `app/serve.py` aus ihrem
eigenen Ort ableiten, und Windows fuehrt denselben Code aus wie Linux.

`_importe` nennt jede Bibliothek, die der Quellcode importiert; das
Bauskript erzeugt die Liste. Der Import steht hinter einer Bedingung, die
zur Laufzeit nie zutrifft: PyInstaller sieht ihn und packt alles ein, der
Start laedt dagegen nichts vorab — der Startbildschirm soll stehen, bevor
torch geladen ist.
"""
import os
import runpy
import sys
from pathlib import Path

if len(sys.argv) < 0:  # nur fuer die Analyse von PyInstaller
    import _importe  # noqa: F401

# Ohne Konsole setzt PyInstaller die Ausgaben auf None. Nicht in eine Datei
# umlenken: ein Protokoll waere eine Datei mit Dokumentinhalt, und
# MASCHERA schreibt keine.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

BASIS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) \
    / "maschera"
EINSTIEG = BASIS / "app" / "fenster.py"
sys.argv[0] = str(EINSTIEG)
runpy.run_path(str(EINSTIEG), run_name="__main__")
