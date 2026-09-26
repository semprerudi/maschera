"""Wie der Prozess heisst — damit man ihn findet und beenden kann.

    from core import prozess
    prozess.benenne()          # so frueh wie moeglich im Start

Ohne Namen heisst MASCHERA `python`, und der einzige Weg, ein haengendes
Fenster sicher zu beenden, waere `killall python` — das trifft jedes
andere Python auf der Maschine mit. Bei einem Werkzeug, das im
Ablagefach sitzt und dessen X nur minimiert, ist das keine Kleinigkeit.

Drei Plattformen, drei Antworten:

  Linux     `prctl(PR_SET_NAME)` setzt den Kernnamen in
            `/proc/PID/comm`. Genau danach suchen `killall` und `pgrep`
            OHNE `-f`. Hoechstens 15 Zeichen; «maschera» sind acht.

  macOS     kennt kein `prctl`. Dort zaehlt der Name der ausfuehrbaren
            Datei; im gebauten `.app`-Buendel ist es `MASCHERA` — die
            Verpackung loest es, nicht der Code.

  Windows   dasselbe: der Prozessname ist der Dateiname, im gebauten
            Installer `MASCHERA.exe`.

`setproctitle` wird benutzt, wenn es da ist, aber nicht verlangt. Es
aendert zusaetzlich die Kommandozeile (`ps aux`, `pkill -f`), ist aber
ein C-Erweiterungsmodul, und jede Abhaengigkeit zaehlt. Der Kernname ueber
`ctypes` kostet nichts und leistet das Wichtigste.

Es faellt nie mit einem Fehler aus: ein Werkzeug, das nicht startet, weil
es sich nicht umbenennen konnte, waere die schlechteste aller Fassungen.
"""
from __future__ import annotations

import os
import sys

NAME = "maschera"

# `prctl(2)`, Option 15. Der Kern kuerzt auf 16 Byte einschliesslich der
# abschliessenden Null — deshalb 15 nutzbare Zeichen.
PR_SET_NAME = 15
KERNNAME_MAX = 15


def benenne(name: str = NAME) -> str:
    """Den Prozess benennen. Gibt zurueck, was tatsaechlich gelang.

    Rueckgabe ist eine Beschreibung fuer Menschen — `"prctl"`,
    `"setproctitle"`, `"beides"` oder `"nichts"`. Sie wird nicht
    ausgegeben; wer sie braucht, fragt danach.
    """
    gelungen = []

    # Zuerst `setproctitle`, weil es mehr kann. Kernname und Kommandozeile
    # sind zwei verschiedene Dinge: `killall` liest das eine, `pkill -f` das
    # andere.
    try:
        import setproctitle
        setproctitle.setproctitle(name)
        gelungen.append("setproctitle")
    except Exception:  # noqa: BLE001
        pass

    if sys.platform.startswith("linux"):
        try:
            import ctypes
            kurz = name.encode("utf-8")[:KERNNAME_MAX]
            libc = ctypes.CDLL(None, use_errno=True)
            if libc.prctl(PR_SET_NAME, ctypes.c_char_p(kurz), 0, 0, 0) == 0:
                gelungen.append("prctl")
        except Exception:  # noqa: BLE001
            pass

    if len(gelungen) == 2:
        return "beides"
    return gelungen[0] if gelungen else "nichts"


def kernname() -> str:
    """Wie der Kern den Prozess gerade nennt. Leer, wo es das nicht gibt.

    Nur zum Nachsehen — die Pruefung benutzt es, damit sie das Ergebnis
    prueft und nicht die Absicht. Ohne `/proc` gibt es nichts zu lesen, und
    das ist kein Fehler.
    """
    try:
        with open(f"/proc/{os.getpid()}/comm", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""
