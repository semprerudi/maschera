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
import re
import runpy
import sys
from pathlib import Path

if len(sys.argv) < 0:  # nur fuer die Analyse von PyInstaller
    import _importe  # noqa: F401

# Der Hilfsprozess der Standardbibliothek. `multiprocessing` startet den
# «resource_tracker» (er raeumt Semaphoren auf) ueber die eigene
# Programmdatei mit `-B -S -I -c "from multiprocessing.resource_tracker import
# main;main(<fd>)"`. In einem eingefrorenen Programm kommen diese Argumente bei
# `fenster.py` an, das sie nicht kennt: unter macOS stand beim Start eine
# Fehlerzeile von argparse, und der Tracker lief nie.
#
# ⚠️ Es wird NICHT der Text aus `argv` ausgefuehrt. Erkannt wird genau dieser
# eine Aufruf der Standardbibliothek (mit einer Zahl), und DER wird aufgerufen.
# Alles andere geht den normalen Weg weiter. Wer die Programmdatei mit anderem
# Code in `-c` startet, bekommt ihn nicht ausgefuehrt — das waere ein Weg, den
# Namen und die Rechte dieser App zu borgen.
_TRACKER = re.compile(r"from multiprocessing\.resource_tracker import main;main\((\d+)\)")


def hilfsprozess(argv, tracker=None) -> bool:
    """Ist das der Hilfsprozess der Standardbibliothek? Dann laeuft er hier."""
    if len(argv) != 6 or argv[1:5] != ["-B", "-S", "-I", "-c"]:
        return False
    treffer = _TRACKER.fullmatch(argv[5])
    if not treffer:
        return False
    if tracker is None:
        from multiprocessing import resource_tracker
        tracker = resource_tracker.main
    tracker(int(treffer.group(1)))
    return True


# Ohne Konsole setzt PyInstaller die Ausgaben auf None. Nicht in eine Datei
# umlenken: ein Protokoll waere eine Datei mit Dokumentinhalt, und
# MASCHERA schreibt keine.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

def main() -> None:
    if hilfsprozess(sys.argv):
        return
    basis = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) \
        / "maschera"
    einstieg = basis / "app" / "fenster.py"
    sys.argv[0] = str(einstieg)
    runpy.run_path(str(einstieg), run_name="__main__")


# Der Einstieg laeuft als Hauptprogramm — auch eingefroren. Die Bedingung
# erlaubt `tests/test_fenster.py`, die Datei zu laden, ohne das Fenster zu starten.
if __name__ == "__main__" or getattr(sys, "frozen", False):
    main()
