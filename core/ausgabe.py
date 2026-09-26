"""Die Ausgabe ueberlebt einen weggebrochenen Leser.

    from core import ausgabe
    ausgabe.sichern()          # einmal, ganz am Anfang

Manche Starter (etwa Gearlever beim Einrichten einer AppImage) haengen
eine Pipe an die Ausgabe und beenden sich, waehrend das Modell noch
laedt. Der naechste `print` wirft dann `BrokenPipeError` — und ein
voll funktionsfaehiges Werkzeug meldete Versagen, nur weil niemand mehr
zuhoerte.

    Leser da   -> print geht durch
    Leser weg  -> BrokenPipeError: [Errno 32] Broken pipe

Verschluckt wird NUR das Schreiben, nicht der Fehler dahinter. Wo eine
Ausgabe nicht ankommt, ist nichts zu retten und nichts zu melden. Dies ist
kein allgemeiner `except`, sondern einer um genau eine Zeile.
"""
from __future__ import annotations

import sys

# Was ein toter Ausgang wirft. `ValueError` steht dabei fuer den
# geschlossenen Datenstrom («I/O operation on closed file»), `OSError` fuer
# alles, was das Betriebssystem sonst noch zurueckgibt — `BrokenPipeError`
# ist selbst ein `OSError` und steht nur der Deutlichkeit halber da.
TOT = (BrokenPipeError, OSError, ValueError)


class Robust:
    """Ein Ausgang, dem ein weggebrochener Leser nichts anhaben kann."""

    def __init__(self, echt):
        self._echt = echt

    def write(self, text):
        try:
            return self._echt.write(text)
        except TOT:
            # Es gibt niemanden mehr, der es liest. Die Laenge zu melden
            # haelt `print` bei seiner Zusage, ohne etwas zu erfinden.
            return len(text)

    def flush(self):
        try:
            self._echt.flush()
        except TOT:
            pass

    # Alles Uebrige durchreichen. Ein Ausgang, der nur `write` und
    # `flush` kann, bricht an der naechsten Stelle, die `isatty()` oder
    # `fileno()` fragt — und das tun Bibliotheken oefter, als man denkt.
    def __getattr__(self, name):
        return getattr(self._echt, name)


def sichern() -> None:
    """`sys.stdout` und `sys.stderr` gegen einen toten Leser absichern.

    Mehrfach aufrufbar: ein schon gesicherter Ausgang bleibt, wie er ist.
    """
    if not isinstance(sys.stdout, Robust):
        sys.stdout = Robust(sys.stdout)
    if not isinstance(sys.stderr, Robust):
        sys.stderr = Robust(sys.stderr)
