"""Nur EIN MASCHERA. Ein zweiter Start zeigt das laufende Fenster.

    from core import einmalig
    if einmalig.laeuft_schon():
        return 0                       # der andere zeigt sich selbst
    einmalig.horche(zeigen_verlangt)   # im laufenden Programm

Dass der Port belegt ist, genuegt nicht als Antwort: es geht nicht darum,
OB er belegt ist, sondern WER ihn haelt. Wer daraus «dann nimm einen
anderen» folgert, oeffnet bei jedem Klick auf das Startsymbol ein
weiteres Fenster.

Warum ein eigener Sockel und nicht der Port: der Port nimmt keine
Anweisung entgegen, und einen Endpunkt «zeig dich» soll es nicht geben —
die HTTP-Flaeche bleibt so klein wie moeglich. Ein Unix-Sockel im
Laufzeitverzeichnis ist ausserdem an den Anwender gebunden: zwei Anwender
auf derselben Maschine stoeren sich nicht.

Der Sockel liegt nicht in `~/.config/maschera/`. Dort stehen die
Einstellungen; ein Sockel gehoert ins Laufzeitverzeichnis, wo das
Betriebssystem ihn beim Neustart selbst wegraeumt.
"""
from __future__ import annotations

import os
import socket
import threading
from pathlib import Path

# Was der zweite Start hinueberschickt. Ein Wort, kein Format — es gibt
# genau eine Nachricht, und ein Protokoll fuer eine Nachricht waere
# Aufwand fuer nichts.
ZEIGEN = b"zeigen\n"


# Zwei Wege, weil es unter Windows keinen Unix-Sockel gibt (`os.getuid()`
# und `socket.AF_UNIX` fehlen dort). Der Zweck bleibt derselbe: genau ein
# MASCHERA, und ein zweiter Start sagt dem ersten, er moege sich zeigen.
#
#   POSIX     ein Unix-Sockel. Er traegt Dateirechte, also gehoert er dem
#             Anwender, und er verschwindet mit dem Laufzeitverzeichnis.
#   Windows   eine Datei mit einer PORTNUMMER darin, dazu ein Horcher auf
#             127.0.0.1. Der zweite Start liest die Nummer und verbindet.
#
# Der Windows-Weg ist schwaecher: ein Horcher auf 127.0.0.1 ist fuer jeden
# Prozess derselben Maschine erreichbar. Entgegengenommen wird allerdings
# genau ein Wort — «zeigen» —, und die einzige Wirkung ist, dass ein Fenster
# nach vorne kommt. Kein Text, kein Woerterbuch, keine Einstellung.
#
# Die Portnummer wird nicht festgelegt: `bind(("127.0.0.1", 0))` laesst das
# System eine freie waehlen. Eine feste Nummer waere irgendwann belegt.
WINDOWS = os.name == "nt"


def sockelpfad() -> Path:
    """Wo der Sockel liegt. An den Anwender gebunden, nicht an das Projekt."""
    if WINDOWS:
        # `LOCALAPPDATA` und nicht `APPDATA`: die Datei ist maschinengebunden
        # und hat in einem wandernden Profil nichts verloren.
        basis = os.environ.get("LOCALAPPDATA") or str(Path.home())
        return Path(basis) / "maschera" / "maschera.port"
    lauf = os.environ.get("XDG_RUNTIME_DIR")
    if lauf and Path(lauf).is_dir():
        return Path(lauf) / "maschera.sock"
    # Rueckfall mit der Benutzerkennung im Namen. Ein fester Name unter
    # `/tmp` waere auf einer Maschine mit zwei Anwendern der Sockel des
    # jeweils anderen.
    return Path("/tmp") / f"maschera-{os.getuid()}.sock"


def _verbinde(pfad: Path, windows: bool | None = None):
    """Zur laufenden Fassung verbinden. `None`, wenn keine da ist.

    `windows` ist ausdruecklich uebergebbar, damit die Pruefung den
    Windows-Weg auch auf Linux durchlaufen kann.
    """
    windows = WINDOWS if windows is None else windows
    try:
        if windows:
            port = int(pfad.read_text(encoding="utf-8").strip())
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(("127.0.0.1", port))
        else:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(str(pfad))
        return s
    except (OSError, ValueError, socket.timeout):
        return None


def _horche_auf(pfad: Path, windows: bool | None = None):
    """Den Horcher aufmachen. Wirft `OSError`, wenn es nicht geht."""
    windows = WINDOWS if windows is None else windows
    pfad.parent.mkdir(parents=True, exist_ok=True)
    if windows:
        horcher = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        horcher.bind(("127.0.0.1", 0))
        horcher.listen(4)
        # Erst binden, dann die Nummer hinschreiben. Andersherum stuende eine
        # Nummer da, auf der noch niemand horcht.
        pfad.write_text(str(horcher.getsockname()[1]), encoding="utf-8")
        return horcher
    horcher = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    horcher.bind(str(pfad))
    horcher.listen(4)
    return horcher


def laeuft_schon(pfad: Path | None = None,
                 windows: bool | None = None) -> bool:
    """Laeuft schon eine? Dann bekommt sie Bescheid, sich zu zeigen.

    Gefragt wird durch VERBINDEN, nicht durch Nachsehen, ob die Datei da
    ist. Ein Sockel ueberlebt einen Absturz; die Datei sagt also «laeuft», wo
    nichts mehr laeuft.
    """
    pfad = pfad or sockelpfad()
    s = _verbinde(pfad, windows)
    if s is None:
        # Niemand da. Eine Leiche wegraeumen, damit `horche()` binden kann.
        # Unter Windows ist die Leiche eine Datei mit einer Portnummer, auf der
        # niemand mehr horcht — aus demselben Grund weg.
        try:
            pfad.unlink()
        except OSError:
            pass
        return False
    finally_gesendet = False
    try:
        s.sendall(ZEIGEN)
        finally_gesendet = True
    except OSError:
        pass
    finally:
        s.close()
    return finally_gesendet


def horche(bei_zeigen, pfad: Path | None = None,
           windows: bool | None = None) -> threading.Thread | None:
    """Auf zweite Starts horchen. `bei_zeigen()` laeuft im HORCHFADEN.

    Der Rueckruf laeuft nicht im Qt-Faden. Wer von hier aus ein Fenster
    anfasst, greift aus einem fremden Faden in die Anzeigeschicht. Deshalb
    setzt der Rueckruf nur ein Zeichen; das Fenster sieht in seinem eigenen
    Takt nach.
    """
    pfad = pfad or sockelpfad()
    try:
        pfad.unlink()
    except OSError:
        pass
    try:
        horcher = _horche_auf(pfad, windows)
    except OSError as e:
        # Kein Abbruch, aber nicht still: ohne Sockel gehen wieder mehrere
        # Fenster auf, und niemand wuesste warum.
        print(f"  ⚠ Einmal-Start nicht gesichert ({type(e).__name__}: {e})")
        return None

    def schleife():
        while True:
            try:
                verbindung, _ = horcher.accept()
            except OSError:
                return
            try:
                if ZEIGEN.strip() in verbindung.recv(64):
                    bei_zeigen()
            except OSError:
                pass
            finally:
                verbindung.close()

    faden = threading.Thread(target=schleife, daemon=True)
    faden.start()
    return faden
