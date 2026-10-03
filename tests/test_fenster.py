"""Das eigene Fenster: Adresse, Port und dass die Wahl bleibt.

    python3 tests/test_fenster.py

`app/fenster.py` nimmt Adresse und Port aus
`~/.config/maschera/einstellungen.json` — derselben Datei, die die
Oberflaeche aendert. Zwei Wege zu derselben Einstellung, von denen einer
den anderen nicht kennt, waeren die Fehlerklasse «eine Datei, zwei
Verwalter». Dazu kommen die Verpackungen, das Ablagefach und der Start.

⚠️ **Diese Pruefung schreibt NIE nach `~/.config/maschera/`.** Sie lenkt
`XDG_CONFIG_HOME` in ein temporaeres Verzeichnis um, BEVOR `core.pfade`
geladen wird. Dort liegen Regeln und Vorlagen des Anwenders, und die
gehen eine Pruefung nichts an.
"""
import os
import re as _re
import socket
import sys
import threading
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# ⚠️ VOR jedem Import aus `core`. `core/pfade.py` liest `XDG_CONFIG_HOME`
# beim Aufruf, aber `core.einstellungen` bestimmt `PFAD` beim IMPORT.
# Wird die Umlenkung danach gesetzt, schreibt die Pruefung in die Datei
# des Anwenders — genau das, was sie nicht darf.
_temp = tempfile.TemporaryDirectory()
os.environ["XDG_CONFIG_HOME"] = _temp.name

sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))
sys.path.insert(0, str(WURZEL / "app"))

failures: list[str] = []


def ohne_kommentare(text: str) -> str:
    """Quelltext ohne Kommentare und ohne Doku-Zeichenketten.

    Eine Wache, die eine Zeichenkette im Quelltext sucht, trifft sonst die
    Kommentarzeile, die erklaert, warum sie dort nicht stehen darf — und
    verbietet ihre eigene Begruendung.
    """
    import re as _r
    t = _r.sub(r'"""[\s\S]*?"""', "", text)
    t = _r.sub(r"\'\'\'[\s\S]*?\'\'\'", "", t)
    return _r.sub(r"(?m)\s#.*$|^\s*#.*$", "", t)


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "fenster", WURZEL / "app" / "fenster.py")
fenster = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fenster)

from core import einstellungen as est  # noqa: E402

check(str(est.PFAD).startswith(_temp.name),
      f"die Pruefung zeigt auf {est.PFAD} — das ist NICHT das temporaere "
      f"Verzeichnis. Abbruch, bevor etwas geschrieben wird.")
if failures:
    raise SystemExit(1)


print("1. `belegt` prueft BINDEN, nicht Antworten")
# ⚠️ «Antwortet dort jemand» waere die falsche Frage: ein Port kann von
# einem Dienst gehalten werden, der nicht antwortet — und dann scheitert
# der Start trotzdem. Deshalb wird hier ein Port belegt, aber NICHT
# gelauscht: `bind` ohne `listen`. Ein Verbindungsversuch liefe ins Leere,
# `bind` schlaegt fehl.
halter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
halter.bind(("127.0.0.1", 0))
BELEGT = halter.getsockname()[1]

grund = fenster.belegt("127.0.0.1", BELEGT)
check(grund is not None,
      f"Port {BELEGT} ist gebunden und gilt trotzdem als frei")
check(grund is None or "use" in grund.lower() or "addr" in grund.lower(),
      f"der Grund ist unbrauchbar: {grund!r}")
print(f"   OK   {BELEGT} belegt: {grund}")


print("\n2. `naechster_freier` ueberspringt den belegten")
vorschlag = fenster.naechster_freier("127.0.0.1", BELEGT - 1)
check(vorschlag is not None, "kein freier Port in 50 Schritten gefunden")
check(vorschlag != BELEGT,
      f"der Vorschlag {vorschlag} ist genau der belegte Port")
check(vorschlag is None or vorschlag > BELEGT - 1,
      f"der Vorschlag {vorschlag} liegt nicht oberhalb")
check(fenster.belegt("127.0.0.1", vorschlag) is None,
      f"der Vorschlag {vorschlag} ist selbst nicht frei")
print(f"   OK   ab {BELEGT - 1} vorgeschlagen: {vorschlag}")
halter.close()

# ⚠️ Und `main()` NIMMT ihn, ohne Dialog. Der Qt-Dialog, der vorher
# fragte, war nur deutsch — und unter Windows gibt es kein Qt: dort brach
# der Start bei belegtem Port wortlos ab. Geprueft wird die Quelle von
# `main()`: bei belegtem Port kein Qt, sondern `naechster_freier`, und die
# Wahl wird gesichert.
import inspect as _insp  # noqa: E402
_main = _insp.getsource(fenster.main)
_zweig = _main[_main.index("grund = belegt(wirt, port)"):]
_zweig = _zweig[:_zweig.index('adresse = f"http://')]
check("naechster_freier(wirt, port)" in _zweig and "qtpy" not in _zweig
      and "QDialog" not in _zweig,
      "bei belegtem Port fragt main() wieder einen Dialog")
check("est.speichere(" in _zweig,
      "der ausgewichene Port wird nicht gesichert")
check(not hasattr(fenster, "frage_nach_adresse"),
      "der deutsche Qt-Dialog fuer den Port ist wieder da")


print("\n3. Die Wahl ueberlebt die Sitzung")
# ⚠️ Das ist der Punkt, um den es geht. Ein Dialog, der jedes Mal
# dieselbe Frage stellt, ist keine Einstellung, sondern eine Belaestigung.
vorher = est.lade()
check(vorher["port"] == 4141 and vorher["adresse"] == "127.0.0.1",
      f"die Vorgabe ist nicht 127.0.0.1:4141, sondern "
      f"{vorher['adresse']}:{vorher['port']}")
est.speichere({**vorher, "adresse": "127.0.0.1", "port": 5099})
nachher = est.lade()
check(nachher["port"] == 5099,
      f"nach dem Sichern steht {nachher['port']}, erwartet 5099")
check(nachher["adresse"] == "127.0.0.1",
      f"die Adresse ging verloren: {nachher['adresse']}")
# Die uebrigen Felder duerfen nicht verlorengehen — `speichere` schreibt
# die GANZE Datei, nicht nur zwei Felder.
check(nachher.get("dienste") == vorher.get("dienste"),
      "beim Sichern von Adresse und Port sind die Dienste verschwunden")
print(f"   OK   4141 -> 5099, gesichert und wieder gelesen")


print("\n4. Ein unmoeglicher Port wird abgewiesen")
# Der Dreher im Dialog ist auf 1-65535 begrenzt, aber die Datei laesst
# sich von Hand aendern. `pruefe` muss halten.
for schlecht in (0, 65536, -1, "abc", None):
    try:
        est.speichere({**vorher, "port": schlecht})
        check(False, f"Port {schlecht!r} wurde angenommen")
    except (est.Abgelehnt, TypeError, ValueError):
        pass
print("   OK   5 unmoegliche Werte abgewiesen")


print("\n5. Das Fenster nimmt keinen Zufallsport")
# ⚠️ Quelltextpruefung, weil der Fehler genau so aussah: eine Funktion,
# die sich einen Port GIBT, statt den eingestellten zu NEHMEN.
QUELLE = (WURZEL / "app" / "fenster.py").read_text(encoding="utf-8")
check("einstellungen" in QUELLE,
      "fenster.py liest die gespeicherten Einstellungen nicht")
check("bind((\"127.0.0.1\", 0))" not in QUELLE
      and "bind(('127.0.0.1', 0))" not in QUELLE,
      "fenster.py laesst sich noch einen zufaelligen Port geben — dann "
      "horcht der Dienst jedes Mal woanders, und die Einstellung des "
      "Anwenders bewirkt nichts")
check("speichere" in QUELLE,
      "die im Dialog gewaehlte Adresse wird nicht gesichert — dann fragt "
      "das Werkzeug bei jedem Start dasselbe")
print("   OK   liest die Einstellungen, sichert die Wahl")


print("\n6. Der Vorgabeport hat GENAU EINEN Verwalter")
# Die Zahl steht an genau einer Stelle. Wer den Vorgabeport aendern
# will, soll nicht neun Fundstellen suchen muessen — und solange er nicht
# geaendert wird, sieht neunfach dasselbe aus wie einmal.
#
# ⚠️ ZWEI Faelle, und sie brauchen zwei verschiedene Regeln:
#
#   Quelltext (py/js/html)  darf die Zahl NICHT ausfuehrbar enthalten.
#                           Er kann `VORGABE_PORT` lesen.
#   Verpackung (Dockerfile, EXPOSE und Portabbildungen brauchen eine
#   compose, AppRun)        Zahl — Docker kennt kein Python. Sie duerfen
#                           sie tragen, muessen aber die AKTUELLE sein.
import re  # noqa: E402

QUELLE_DATEI = WURZEL / "core" / "einstellungen.py"
PORT = est.VORGABE_PORT


def ohne_erklaerung(text: str, py: bool) -> list[tuple[int, str]]:
    """Zeilen ohne Kommentare und ohne Zeichenkettenbloecke."""
    zeilen, im_block, marke = [], False, ""
    for nr, roh in enumerate(text.splitlines(), 1):
        z = roh.strip()
        if py:
            if im_block:
                if marke in z:
                    im_block = False
                continue
            for m in ('"""', "'''"):
                if z.startswith(m):
                    if z.count(m) == 1:
                        im_block, marke = True, m
                    z = ""
                    break
        if z.startswith(("#", "//", "*", "<!--")):
            continue
        if z:
            zeilen.append((nr, z))
    return zeilen


suender = []
for ort in ("app", "core"):
    for pfad in sorted((WURZEL / ort).rglob("*")):
        if (not pfad.is_file() or pfad == QUELLE_DATEI
                or "__pycache__" in str(pfad)
                or pfad.suffix not in {".py", ".js", ".html"}):
            continue
        for nr, z in ohne_erklaerung(pfad.read_text(encoding="utf-8"),
                                     pfad.suffix == ".py"):
            if re.search(rf"\b{PORT}\b", z):
                suender.append(f"{pfad.relative_to(WURZEL)}:{nr}  {z[:55]}")

check(not suender,
      f"der Vorgabeport {PORT} steht ausfuehrbar an {len(suender)} "
      f"Stellen im Quelltext. Er gehoert aus "
      f"`core.einstellungen.VORGABE_PORT` gelesen:\n      "
      + "\n      ".join(suender[:6]))

# Die Verpackung: jede Portzahl darin MUSS die aktuelle sein.
MUSTER = (
    r"EXPOSE\s+(\d+)",
    r"127\.0\.0\.1:(\d+):(\d+)",
    r"server\.port=(\d+)",
    r'"--port",\s*"(\d+)"',
    r"127\.0\.0\.1:(\d+)/api",
)
falsch, gefunden = [], 0
for pfad in sorted((WURZEL / "tools" / "paket").rglob("*")):
    if not pfad.is_file():
        continue
    if pfad.suffix not in {".yaml", ".yml"} and pfad.name not in {
            "Dockerfile", "AppRun"}:
        continue
    text = pfad.read_text(encoding="utf-8")
    for nr, z in enumerate(text.splitlines(), 1):
        if z.strip().startswith("#"):
            continue
        for muster in MUSTER:
            for treffer in re.finditer(muster, z):
                for zahl in treffer.groups():
                    gefunden += 1
                    if int(zahl) != PORT:
                        falsch.append(
                            f"{pfad.relative_to(WURZEL)}:{nr}  {zahl} "
                            f"statt {PORT}")

check(gefunden > 0,
      "in tools/paket/ wurde KEINE Portangabe gefunden — die Muster "
      "greifen nicht mehr, und dann prueft dieser Punkt nichts")
check(not falsch,
      f"die Verpackung nennt einen anderen Port als "
      f"`VORGABE_PORT` ({PORT}):\n      " + "\n      ".join(falsch[:6]))
if not suender and not falsch:
    print(f"   OK   {PORT} nur in core/einstellungen.py, "
          f"{gefunden} Portangaben in tools/paket/ stimmen ueberein")


print("\n7. Die Fassungsnummer hat GENAU EINEN Verwalter")
# Dieselbe Frage wie beim Vorgabeport: die Nummer steht in
# `app/serve.py`, und die Bauskripte lesen sie dort mit
# `tools/paket/fassung.fish`. Jede zweite Stelle faellt erst auf, wenn
# jemand die Nummer erhoeht.
QUELLE_V = WURZEL / "app" / "serve.py"
import re as _re  # noqa: E402

_t = QUELLE_V.read_text(encoding="utf-8")
_m = _re.search(r'^VERSION = "([^"]+)"', _t, _re.M)
check(_m is not None, "keine VERSION in app/serve.py")
FASSUNG = _m.group(1) if _m else ""

fund = []
for ort in ("app", "core", "tools", "tests", "docs"):
    for pfad in sorted((WURZEL / ort).rglob("*")):
        if (not pfad.is_file() or pfad == QUELLE_V
                or "__pycache__" in str(pfad)
                or pfad.suffix not in {".py", ".js", ".html", ".yaml",
                                       ".yml", ".fish", ".md"}
                and pfad.name not in {"Dockerfile", "AppRun"}):
            continue
        for nr, z in enumerate(
                pfad.read_text(encoding="utf-8").splitlines(), 1):
            if FASSUNG in z and not z.strip().startswith(("#", "//", "*")):
                fund.append(f"{pfad.relative_to(WURZEL)}:{nr}  {z.strip()[:50]}")

check(not fund,
      f"die Fassung {FASSUNG} steht ausfuehrbar an {len(fund)} weiteren "
      f"Stellen. Die Bauskripte lesen sie mit "
      f"`tools/paket/fassung.fish`:\n      " + "\n      ".join(fund[:5]))
if not fund:
    print(f"   OK   {FASSUNG} nur in app/serve.py")



print("\n8. Beide Bauwege sehen nach, dass torch die CPU-Fassung ist")
# `--extra-index-url …/whl/cpu` ERGAENZT PyPI, es ersetzt es nicht —
# die CUDA-Raeder bleiben waehlbar. `--index-url` statt dessen ginge nicht:
# auf dem CPU-Index gibt es Flask und die uebrigen Pakete nicht. Dass
# `+cpu` gewinnt, haengt an der Sortierung der Versionen, nicht an einer
# Zusage.
#
# ⚠️ Und ein Fehlgriff waere UNSICHTBAR: die CUDA-Fassung laeuft. Sie
# bringt nur ueber 2 GB Bibliotheken mit, die keine GPU je benutzt.
#
# Geprueft wird die BEZIEHUNG und nicht ein Wortlaut: jeder Bauweg, der
# `requirements` einliest, muss danach `+cpu` nachsehen.
for _datei in ("appimage_bauen.fish", "Dockerfile"):
    _q = (WURZEL / "tools" / "paket" / _datei).read_text(encoding="utf-8")
    _code = ohne_kommentare(_q)
    check("+cpu" in _code,
          f"{_datei} sieht nicht nach, ob torch die CPU-Fassung ist — "
          f"ein Fehlgriff waere unsichtbar, weil CUDA-torch laeuft und "
          f"nur 2 GB schwerer ist")
    check("torch.__version__" in _code,
          f"{_datei} liest `torch.__version__` nicht — dann prueft es "
          f"etwas anderes als die eingebaute Fassung")
if not failures:
    print("   OK   AppImage und Abbild brechen ohne `+cpu` ab")

print("\n9. Qt wird ueber `qtpy` geholt, nie direkt")
# `requirements-appimage.txt` legt die Bindung mit `QT_API=pyqt6` fest,
# damit die Wahl nicht von der Reihenfolge abhaengt. Ein direktes
# `from PyQt6` uebergeht diese Wahl: liefe die Anwendung auf PySide6,
# stuerzten genau die Stellen ab, die direkt importieren — und das sind
# typischerweise die Dialoge, also das, was im Fehlerfall erscheint.
#
# Geprueft wird die EIGENSCHAFT ueber `app/`, nicht einzelne Stellen.
_qt_direkt = []
for _p in sorted((WURZEL / "app").glob("*.py")):
    for _nr, _z in enumerate(_p.read_text(encoding="utf-8").splitlines(), 1):
        if _z.lstrip().startswith("#"):
            continue
        if _re.search(r"^\s*(from|import)\s+(PyQt6|PySide6)\b", _z):
            _qt_direkt.append(f"{_p.name}:{_nr}")
check(not _qt_direkt,
      f"Qt wird direkt geholt statt ueber `qtpy`: {', '.join(_qt_direkt)} — "
      f"damit haengt die Bindung an dieser Zeile und nicht an QT_API, und "
      f"die Anwendung laeuft teils auf der einen, teils auf der anderen")
if not failures:
    _ueber = sum(z.count("from qtpy")
                 for z in (WURZEL / "app" / "fenster.py")
                 .read_text(encoding="utf-8").splitlines()
                 if not z.lstrip().startswith("#"))
    print(f"   OK   {_ueber} Zugriffe, alle ueber qtpy")

print("\n10. Kein Name wird vor seinem Import im selben Rumpf benutzt")
# Ein Import IRGENDWO im Rumpf macht den Namen fuer die GANZE Funktion
# lokal — auch fuer die Zeilen davor. Die Folge ist ein
# `UnboundLocalError`, und zwar erst zur Laufzeit und nur in dem Zweig,
# der die Zeile erreicht. Liegt der Zweig im ersten Start ohne Modell,
# sieht ihn keine Pruefung, die mit Modell laeuft.
#
# Geprueft wird die KLASSE: in `app/` und `core/` muss ueberall dort, wo
# eine Funktion selbst importiert, der Import VOR jeder Benutzung stehen.
# Diese Dateien importieren absichtlich spaet — `serve` zieht torch nach,
# der Startbildschirm soll vorher dastehen —, also ist das Muster hier
# haeufig.
import ast as _ast                                              # noqa: E402


def _eigener_rumpf(knoten):
    """Alle Knoten der Funktion OHNE verschachtelte Funktionen/Klassen."""
    for kind in _ast.iter_child_nodes(knoten):
        if isinstance(kind, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                             _ast.ClassDef)):
            continue
        yield kind
        yield from _eigener_rumpf(kind)


_zu_frueh = []
for _d in sorted(list((WURZEL / "app").glob("*.py"))
                 + list((WURZEL / "core").glob("*.py"))):
    _baum = _ast.parse(_d.read_text(encoding="utf-8"))
    for _f in [n for n in _ast.walk(_baum)
               if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]:
        _importiert = {}
        _benutzt = {}
        for _k in _eigener_rumpf(_f):
            if isinstance(_k, (_ast.Import, _ast.ImportFrom)):
                for _a in _k.names:
                    if _a.name == "*":
                        continue
                    _n = (_a.asname or _a.name).split(".")[0]
                    _importiert.setdefault(_n, _k.lineno)
            elif isinstance(_k, _ast.Name) and isinstance(_k.ctx, _ast.Load):
                _benutzt.setdefault(_k.id, _k.lineno)
        for _n, _zeile in _importiert.items():
            if _n in _benutzt and _benutzt[_n] < _zeile:
                _zu_frueh.append(
                    f"{_d.name}:{_benutzt[_n]} benutzt {_n!r}, "
                    f"importiert erst in Zeile {_zeile} ({_f.name})")
check(not _zu_frueh,
      "hier wird ein Name vor seinem Import im selben Rumpf benutzt — das "
      "ist ein UnboundLocalError, und zwar erst zur Laufzeit und nur in "
      f"dem Zweig, der ihn erreicht: {'; '.join(_zu_frueh[:4])}")
if not failures:
    print("   OK   app/ und core/ durchgesehen, kein Name vor seinem Import")

print("\n11. Der Prozess heisst maschera und nicht python")
# Heisst der Prozess `python`, laesst er sich nur mit `killall python`
# beenden — und das trifft jedes andere Python auf der Maschine mit. Bei
# einem Werkzeug im Ablagefach, dessen X nur versteckt, ist das der
# naheliegende Weg.
#
# ⚠️ GEPRUEFT WIRD DAS ERGEBNIS, nicht die Absicht: der Kernname aus
# `/proc/PID/comm` NACH dem Aufruf. Ein Test, der nur nachsieht, ob
# `benenne()` aufgerufen wird, meldete gruen, auch wenn `prctl` scheitert.
#
# ⚠️ Und er prueft ihn im UNTERPROZESS. Im Laeufer selbst waere der Name
# danach dauerhaft geaendert.
import subprocess as _sp7f                                      # noqa: E402
_r7f = _sp7f.run(
    [sys.executable, "-c",
     "import sys; sys.path.insert(0, %r);"
     "from core import prozess;"
     "print(prozess.benenne(), prozess.kernname())" % str(WURZEL)],
    capture_output=True, text=True, cwd=str(WURZEL))
check(_r7f.returncode == 0, f"benenne() bricht ab: {_r7f.stderr.strip()[:120]}")
_teile = _r7f.stdout.split()
if sys.platform.startswith("linux"):
    check(len(_teile) == 2 and _teile[1] == "maschera",
          f"der Kernname ist {_teile[1:] or ['?']}, erwartet 'maschera' — "
          f"`killall maschera` findet den Prozess sonst nicht")
    check(_teile[0] != "nichts",
          "benenne() konnte gar nichts setzen")
else:
    print("   --   kein Linux, `/proc` gibt es nicht")

# ⚠️ Und JEDER Einstieg muss ihn rufen. Drei Einstiege, drei Prozesse:
# das Fenster, die Oberflaeche und der nackte Kern. Wer einen vergisst,
# hat auf genau dem Weg wieder ein `python`.
for _e in ("fenster.py", "app.py", "serve.py"):
    _q = (WURZEL / "app" / _e).read_text(encoding="utf-8")
    _code = ohne_kommentare(_q)
    check("prozess.benenne()" in _code,
          f"app/{_e} benennt den Prozess nicht — auf diesem Weg heisst er "
          f"weiter `python`, und `killall python` trifft alles andere mit")
if not failures:
    print("   OK   Kernname 'maschera', drei Einstiege rufen es")

print("\n12. Jede Verpackung nimmt dieselben tools/-Dateien mit")
# `evaluate_model` wird erst IM RUMPF von `Zustand.__init__` geholt, wenn
# ein Modell gesetzt ist. Nach einem blossen `import serve` steht es nicht
# in `sys.modules` — wer die noetigen Dateien so ermittelt, findet zwei
# von drei. Der Fehler faellt dann nicht beim Bauen auf, sondern beim
# ersten Start.
#
# Geprueft wird STATISCH und ueber ALLE Verpackungen: jeder Import aus
# `tools/` in `app/*.py`, auch der verzoegerte, muss in jeder Verpackung
# stehen.
import ast as _ast7g                                            # noqa: E402
_tools = {_p.stem for _p in (WURZEL / "tools").glob("*.py")}
_noetig = set()
for _d in sorted((WURZEL / "app").glob("*.py")):
    for _k in _ast7g.walk(_ast7g.parse(_d.read_text(encoding="utf-8"))):
        if isinstance(_k, _ast7g.ImportFrom) and _k.module and _k.level == 0:
            _n = _k.module.split(".")[0]
            if _n in _tools:
                _noetig.add(_n + ".py")
        elif isinstance(_k, _ast7g.Import):
            for _a in _k.names:
                _n = _a.name.split(".")[0]
                if _n in _tools:
                    _noetig.add(_n + ".py")
check(len(_noetig) >= 3,
      f"nur {sorted(_noetig)} aus tools/ gefunden — die Ableitung greift "
      f"nicht mehr")
# Jede Verpackung kopiert ihre eigene Auswahl aus `tools/` und kann sie
# einzeln verlieren. Die AppImage steht nicht dabei — sie packt den ganzen
# Baum ein. Das Arch-Paket wird geprueft, wo es vorliegt. Windows nimmt
# seit 0.9.58 ebenfalls nur noch die Auswahl mit (`WERKZEUGE`).
_verpackungen = ["Dockerfile", "ch.maschera.Maschera.yml",
                 "windows_bauen.py"]
if (WURZEL / "tools" / "paket" / "PKGBUILD").is_file():
    _verpackungen.append("PKGBUILD")
for _verpackung in _verpackungen:
    _q = (WURZEL / "tools" / "paket" / _verpackung).read_text(encoding="utf-8")
    _code = ohne_kommentare(_q)
    _fehlt = sorted(n for n in _noetig if n not in _code)
    check(not _fehlt,
          f"{_verpackung} nimmt {_fehlt} nicht mit — das faellt nicht beim "
          f"Bauen auf, sondern beim ersten Start")

# Und was draussen bleibt. Die Liste steht EINMAL, in
# `tools/paket/draussen.txt`. Bis 0.9.58 trug jede Verpackung ihre eigene:
# der Server liess alles weg, Flatpak und Arch nahmen Vorlagen und `eval/`
# mit, Windows alles samt 52 Werkzeugen.
_draussen = [_z.strip() for _z in (WURZEL / "tools/paket/draussen.txt")
             .read_text(encoding="utf-8").splitlines()
             if _z.strip() and not _z.strip().startswith("#")]
check(len(_draussen) >= 7,
      f"draussen.txt fuehrt nur {len(_draussen)} Eintraege — geleert?")
# Windows liest die Liste selbst — also AUSFUEHREN und nachsehen, was im
# Zwischenstand liegt. Ein Blick in den Quelltext saehe nur, dass die
# Liste genannt wird, nicht dass sie wirkt (Gegenprobe gemacht).
import importlib.util as _ilu  # noqa: E402
import tempfile as _tf  # noqa: E402
_spec = _ilu.spec_from_file_location(
    "_windows_bauen", WURZEL / "tools/paket/windows_bauen.py")
_wbm = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_wbm)
with _tf.TemporaryDirectory() as _tmp:
    _ziel = Path(_tmp) / "maschera"
    _wbm.zusammenstellen(_ziel)
    _drin = [_e for _e in _draussen if list(_ziel.glob(_e))]
    check(not _drin, f"der Windows-Zwischenstand enthaelt {_drin}")
    _werkzeuge = sorted(_p.name for _p in (_ziel / "tools").iterdir())
    check(_werkzeuge == sorted(_noetig),
          f"Windows nimmt aus tools/ {_werkzeuge} mit, noetig {sorted(_noetig)}")
    _cache = [str(_p) for _p in _ziel.rglob("__pycache__")]
    check(not _cache, f"Bytecode im Windows-Zwischenstand: {_cache[:2]}")
_hand = ["appimage_bauen.fish", "ch.maschera.Maschera.yml", "../../.dockerignore"]
if (WURZEL / "tools/paket/PKGBUILD").is_file():
    _hand.append("PKGBUILD")
for _verpackung in _hand:
    _code = ohne_kommentare((WURZEL / "tools/paket" / _verpackung)
                            .read_text(encoding="utf-8"))
    # Der Eintrag ohne das Pack-Muster: `packs/*/eval` steht in jeder
    # Verpackung mit anderem Vorsatz, aber immer mit `/*/eval`. Als ganzes
    # Wort — «eval» steckt sonst schon in `evaluate_model.py`.
    _fehlt = [_e for _e in _draussen
              if not re.search(r"(?<![\w.])" + re.escape(_e.split("*/")[-1])
                               + r"(?![\w])", _code)]
    check(not _fehlt, f"{Path(_verpackung).name} laesst {_fehlt} nicht weg "
          "— Werkstattdateien fahren zum Anwender (siehe draussen.txt)")

# Und die Lizenztexte fahren mit. Das gebaute Paket steht unter AGPL-3.0;
# bis 0.9.65 trug nur Arch den Text, Flatpak nur MIT, AppImage, Windows
# und Docker keinen.
for _verpackung in ("appimage_bauen.fish", "ch.maschera.Maschera.yml",
                    "Dockerfile", "maschera.iss") + (
        ("PKGBUILD",) if (WURZEL / "tools/paket/PKGBUILD").is_file() else ()):
    _code = ohne_kommentare((WURZEL / "tools/paket" / _verpackung)
                            .read_text(encoding="utf-8"))
    if _verpackung == "maschera.iss":
        _code = re.sub(r"(?m)^\s*;.*$", "", _code)
    _fehlt = [n for n in ("LICENSE-AGPL-3.0.txt", "LIZENZ.md")
              if n not in _code]
    check(not _fehlt, f"{_verpackung} liefert {_fehlt} nicht mit")

# ⚠️ Jede Fassung, die eine Verpackung nennt, ist die aus
# `app/serve.py`. `<release version=…>` in der metainfo ist fuer Flathub
# der Ort, an dem der Anwender die Fassung SIEHT.
#
# Gesucht wird nach ZUWEISUNGEN (`pkgver=…`, `version="…"`), nicht nach
# der Zahl im Fliesstext. Arch vertraegt keinen Bindestrich in `pkgver`,
# dort gilt dieselbe Zahl ohne ihn.
#
# ⚠️ NUR VERFOLGTE DATEIEN. `tools/paket/.env` gehoert dem Anwender und
# ist ignoriert; sie mitzupruefen hiesse, auf einer fremden Maschine rot
# zu werden.
import subprocess as _sp7g                                   # noqa: E402
_verfolgt = _sp7g.run(["git", "ls-files"], cwd=WURZEL,
                      capture_output=True, text=True,
                      check=True).stdout.split()
_v = (WURZEL / "app" / "serve.py").read_text(encoding="utf-8")
_soll = _re.search(r'^VERSION = "([^"]+)"', _v, _re.M).group(1)
_verkuendet = 0
for _rel in _verfolgt:
    if not _rel.startswith("tools/paket/"):
        continue
    # ⚠️ DIE ERSTE ANGABE JE DATEI, NICHT JEDE. Eine AppStream-Datei
    # fuehrt zu Recht eine Geschichte: `<releases>` listet die frueheren
    # Fassungen, neueste zuerst. Geprueft gehoert, was eine Datei als IHRE
    # EIGENE Fassung angibt — die erste.
    for _z in (WURZEL / _rel).read_text(
            encoding="utf-8", errors="replace").splitlines():
        _mv = _re.search(r'(?:^\s*\w*ver(?:sion)?=|version=")'
                         r'"?(\d+\.\d+\.\d+-?[A-Za-z]*)', _z)
        if not _mv:
            continue
        _verkuendet += 1
        check(_mv.group(1).replace("-", "") == _soll.replace("-", ""),
              f"{_rel} nennt sich in der ERSTEN Fassungsangabe "
              f"{_mv.group(1)}, app/serve.py sagt {_soll} — zwei "
              f"Fassungen fuer ein Paket")
        break
check(_verkuendet >= 1,
      "keine Fassungsangabe in tools/paket/ gefunden — metainfo.xml traegt "
      "eine, die Suche greift nicht mehr")
if not failures:
    print(f"   OK   {len(_noetig)} tools/-Dateien in "
          f"{len(_verpackungen)} Verpackungen, "
          f"{_verkuendet} Fassungsangaben gleich {_soll}")

print("\n13. Wer aus der Maske ein Symbol macht, legt sie aufs Quadrat")
# `maske.svg` ist 1278x1506. Ein Symbolthema rechnet mit einem Quadrat,
# und eine nicht quadrierte Maske steht verzogen in Leiste und
# Ablagefach — ein Fehler, den niemand meldet, weil nichts abstuerzt.
#
# Geprueft wird als EIGENSCHAFT ueber den ganzen Baum: was die Maske
# anfasst UND daraus ein Symbol macht, muss quadrieren. Ausgenommen sind
# `app/static/` und `tests/` — dort wird sie als Bild eingebettet
# beziehungsweise nur besprochen.
_symbol = []
for _rel in _verfolgt:
    if _rel.startswith(("app/static/", "tests/")):
        continue
    _q = (WURZEL / _rel).read_text(encoding="utf-8", errors="replace")
    if "maske.svg" not in _q:
        continue
    _symbol.append(_rel)
    # Drei Wege, alle quadratisch: die gemeinsame Rechnung, das Werkzeug
    # darueber, oder eine ausdruecklich quadratische Zielflaeche beim
    # Rendern.
    _eckig = ("quadratisch" in _q
              or "symbol_quadrat" in _q
              or _re.search(r"--page-width (\S+) --page-height \1", _q)
              or _re.search(r"-extent \{?(\S+?)\}?x\{?\1\}?", _q))
    check(bool(_eckig),
          f"{_rel} macht aus maske.svg ein Symbol, legt sie aber nicht "
          f"aufs Quadrat — es wird in der Leiste verzogen, und das "
          f"meldet niemand als Fehler")
check(len(_symbol) >= 5,
      f"nur {len(_symbol)} Stelle(n) gefunden, die aus der Maske ein "
      f"Symbol machen — erwartet sind mindestens fuenf; die Suche greift "
      f"nicht mehr")
if not failures:
    print(f"   OK   {len(_symbol)} Stellen, alle aufs Quadrat gelegt")

print("\n14. Kein Bauskript ueberschreibt die Einstellungen des Anwenders")
# Die Datei `.env` traegt Wirtsnamen und Middlewares, die der Anwender
# eingetragen hat. Ein Bauskript, das sie mit `>` neu schreibt, loescht
# das — und meldet dabei «geschrieben». Ein Werkzeug, das etwas zerstoert
# und OK meldet, ist schlimmer als eines, das abbricht.
import re as _re2  # noqa: E402

_gefahr = []
for _p in sorted((WURZEL / "tools" / "paket").glob("*.fish")):
    for _nr, _z in enumerate(
            _p.read_text(encoding="utf-8").splitlines(), 1):
        if _z.strip().startswith("#"):
            continue
        # `>` auf eine .env, aber nicht auf eine Zwischendatei wie
        # `.env.neu` — die wird gleich darauf umbenannt und ist der
        # richtige Weg.
        if _re2.search(r">\s*\S*\.env\s*$", _z):
            _gefahr.append(f"{_p.name}:{_nr}  {_z.strip()[:60]}")

check(not _gefahr,
      "ein Bauskript schreibt mit `>` direkt auf eine .env und loescht "
      "damit, was der Anwender dort eingetragen hat:\n      "
      + "\n      ".join(_gefahr))
if not _gefahr:
    print("   OK   keine .env wird ueberschrieben")


print("\n15. Die Zwischenablage toetet das Fenster nicht mehr")
# pywebview uebergibt `setFeaturePermission` eine Zahl, PyQt6 verlangt
# eine Aufzaehlung — der Prozess stirbt dann beim Kopieren mit
# `TypeError`, ohne Dialog. `fenster.berechtigungen_richten()` ersetzt
# die Methode. Diese Pruefung braucht KEIN Fenster: sie ersetzt die
# Methode wie beim Start und ruft sie an einer Attrappe auf.
#
# ⚠️ Die Attrappe ist streng — sie merkt sich, was ankommt, und die
# Pruefung sieht nach. Eine grosszuegige Attrappe verschluckte genau
# diesen Fehler.
try:
    import webview  # noqa: F401
    from webview.platforms import qt as _schicht
    from qtpy.QtWebEngineCore import QWebEnginePage as _Seite
except ImportError as e:
    print(f"   uebersprungen — keine Qt-Schicht ({e})")
else:
    _vorher = len(failures)
    _meldung = fenster.berechtigungen_richten()
    check("erlaubt" in _meldung, f"nichts gerichtet: {_meldung}")

    class _Attrappe:
        def __init__(self):
            self.gesehen = []

        def setFeaturePermission(self, url, merkmal, regel):
            self.gesehen.append((merkmal, regel))

    _a = _Attrappe()
    _fn = _schicht.BrowserView.WebPage.onFeaturePermissionRequested
    for _merkmal in (_Seite.Feature.ClipboardReadWrite,
                     _Seite.Feature.MediaVideoCapture,
                     _Seite.Feature.MediaAudioCapture,
                     _Seite.Feature.Geolocation):
        _fn(_a, None, _merkmal)

    check(len(_a.gesehen) == 4, f"nur {len(_a.gesehen)} Antworten")
    for _merkmal, _regel in _a.gesehen:
        # DER Punkt: keine Zahl.
        check(isinstance(_regel, _Seite.PermissionPolicy),
              f"{_merkmal} bekommt {type(_regel).__name__}, keine "
              f"Aufzaehlung — daran stirbt der Prozess beim Kopieren")
        check(not isinstance(_regel, int) or hasattr(_regel, "name"),
              f"{_merkmal} bekommt eine nackte Zahl")

    _regeln = dict(_a.gesehen)
    check(_regeln[_Seite.Feature.ClipboardReadWrite]
          is _Seite.PermissionPolicy.PermissionGrantedByUser,
          "die Zwischenablage ist verweigert — dann scheitert `writeText` "
          "still, und der Anwender fuegt nichts ein")
    # ⚠️ Bewusste Abweichung von pywebview, das Kamera und Mikrofon von
    # sich aus ERLAUBT. Ein Werkzeug, das nichts sendet, hat dort nichts
    # zu suchen.
    for _merkmal in (_Seite.Feature.MediaVideoCapture,
                     _Seite.Feature.MediaAudioCapture,
                     _Seite.Feature.Geolocation):
        check(_regeln[_merkmal]
              is _Seite.PermissionPolicy.PermissionDeniedByUser,
              f"{_merkmal} ist erlaubt — Kamera, Mikrofon und Ort "
              f"gehoeren verweigert")
    # Das OK nur, wenn wirklich nichts anschlug.
    if len(failures) == _vorher:
        print("   OK   Zwischenablage erlaubt, Kamera/Mikrofon/Ort "
              "verweigert, keine nackte Zahl")





print("\n16. Das Herunterladen tut im eigenen Fenster etwas")
# Dieselbe Klasse wie beim vorigen Punkt: pywebview ruft eine
# Qt5-Schnittstelle auf.
#
#     download.setPath(path)      ->  gibt es in Qt6 nicht
#     setDownloadDirectory/Name   ->  gibt es
#
# Ohne den Eingriff tut «Herunterladen» im eigenen Fenster nichts, im
# Browser schon.
#
# ⚠️ Auch diese Pruefung braucht KEIN Fenster. Die Attrappe ist streng:
# was sie nicht kennt, wirft — und `setPath` kennt sie ausdruecklich
# NICHT, denn genau der Aufruf ist der Fehler.
try:
    from webview.platforms import qt as _schicht2  # noqa: F401
except ImportError as e:
    print(f"   uebersprungen — keine Qt-Schicht ({e})")
else:
    from qtpy.QtWebEngineCore import QWebEngineDownloadRequest as _Anfrage

    # 1. Die Schnittstelle selbst — bevor irgendetwas gerichtet wird.
    check(not hasattr(_Anfrage, "setPath"),
          "Qt kennt `setPath` wieder — dann ist der Eingriff zu pruefen")
    for _name in ("setDownloadDirectory", "setDownloadFileName",
                  "downloadFileName", "accept", "cancel"):
        check(hasattr(_Anfrage, _name),
              f"Qt kennt `{_name}` nicht mehr — der Eingriff ist ueberholt")

    _meldung2 = fenster.downloads_richten()
    check("setPath" in _meldung2, f"nichts gerichtet: {_meldung2}")

    class _AnfrageAttrappe:
        def __init__(self, name):
            self._name = name
            self.ordner = None
            self.datei = None
            self.zustand = None

        def downloadFileName(self):
            return self._name

        # ⚠️ ABSICHTLICH NICHT DA: `setPath`. Ruft es jemand wieder auf,
        # wirft diese Attrappe — statt es zu verschlucken.
        def setDownloadDirectory(self, o):
            self.ordner = o

        def setDownloadFileName(self, d):
            self.datei = d

        def accept(self):
            self.zustand = "angenommen"

        def cancel(self):
            self.zustand = "abgebrochen"

    _fn2 = _schicht2.BrowserView.on_download_requested

    class _DialogAttrappe:
        """Der Dateidialog, ohne Anzeige. `antwort` steuert ihn."""
        antwort = ""

        @staticmethod
        def getSaveFileName(eltern, titel, vorschlag):
            _DialogAttrappe.gesehen = (titel, vorschlag)
            return (_DialogAttrappe.antwort, "")

    import qtpy.QtWidgets as _widgets
    _echt = _widgets.QFileDialog
    _widgets.QFileDialog = _DialogAttrappe
    try:
        # a) Der Anwender waehlt einen Ort.
        _DialogAttrappe.antwort = "/tmp/irgendwo/mein-vokabular.json"
        _a2 = _AnfrageAttrappe("maschera-vokabular-klartext-2026-09-01.json")
        _fn2(None, _a2)
        check(_a2.zustand == "angenommen",
              f"der Download wurde nicht angenommen: {_a2.zustand}")
        check(_a2.ordner == "/tmp/irgendwo",
              f"falsches Verzeichnis: {_a2.ordner}")
        check(_a2.datei == "mein-vokabular.json",
              f"falscher Dateiname: {_a2.datei}")

        # ⚠️ DER NAMENSVORSCHLAG kommt aus `downloadFileName()` und NICHT
        # aus dem Verweis. Die Oberflaeche laedt ueber `blob:`, und dessen
        # Pfad ist eine nackte UUID — der Anwender haette die angeboten
        # bekommen.
        _titel, _vorschlag = _DialogAttrappe.gesehen
        check(_vorschlag.endswith("maschera-vokabular-klartext-"
                                  "2026-09-01.json"),
              f"der Vorschlag traegt nicht den echten Namen: {_vorschlag}")
        check(_titel in fenster.SPEICHERN_UNTER.values(),
              f"der Dialogtitel steht in keiner der vier Sprachen: {_titel}")

        # b) Der Anwender bricht ab — dann ABBRECHEN, nicht haengen lassen.
        _DialogAttrappe.antwort = ""
        _a3 = _AnfrageAttrappe("egal.txt")
        _fn2(None, _a3)
        check(_a3.zustand == "abgebrochen",
              f"abgebrochen wurde nicht abgebrochen: {_a3.zustand}")
        check(_a3.ordner is None and _a3.datei is None,
              "trotz Abbruch wurde ein Ziel gesetzt")
    finally:
        _widgets.QFileDialog = _echt

    # ⚠️ Die vier Sprachen, wie ueberall.
    check(set(fenster.SPEICHERN_UNTER) == {"de", "fr", "it", "en"},
          "der Speicherdialog kennt nicht die vier Bediensprachen")

print("   OK   Ziel ueber Verzeichnis und Name, Abbruch bricht ab")


print("\n17. Das Ablagefach — und was ohne Ablagefach passiert")
# Ablagefach, X versteckt statt schliesst, Widget-Modus.
#
# ⚠️ DER GEFAEHRLICHE TEIL IST NICHT DAS ABLAGEFACH, SONDERN SEIN FEHLEN.
# Unter GNOME gibt es ohne AppIndicator-Erweiterung keines. Versteckt sich
# die App dorthin, wo kein Symbol erscheint, ist sie WEG. Deshalb prueft
# dieser Punkt vor allem den Fall «kein Ablagefach».
from core import einstellungen as _E  # noqa: E402

# Seit 0.9.58 sind Ablagefach und Widget vorgabemaessig AN (Wunsch des
# Anwenders: sie sollen ab dem ersten Start wirken). Das ist nur deshalb
# vertretbar, weil `beim_schliessen` ohne Symbol das Schliessen freigibt —
# das prueft der Rest dieses Punkts.
check(_E.VORGABE["tray"] is True,
      "das Ablagefach ist vorgabemaessig aus")
check(_E.VORGABE["fenstermodus"] == "widget",
      "das schmale Fenster ist nicht die Vorgabe")
check(_E.FENSTERMODI == ("voll", "widget"),
      f"unerwartete Fenstermodi: {_E.FENSTERMODI}")
# ⚠️ 380 px. Unter etwa 340 passt in Maschera kein lesbarer Satz — das
# Werkzeug lebt von Textfeldern, und 150 px waeren eine Attrappe.
check(_E.WIDGET_BREITE >= 340,
      f"der Widget-Modus ist zu schmal fuer einen Satz: {_E.WIDGET_BREITE}")
# ⚠️ UND ER MUSS DIE GEMESSENE GRENZE HALTEN. 378 ist die kleinste Breite
# ohne waagrechten Rollbalken, am laufenden Dienst gemessen.
check(_E.WIDGET_BREITE >= _E.GEMESSENE_MINDESTBREITE,
      f"der Widget-Modus oeffnet mit {_E.WIDGET_BREITE}, gemessen braucht "
      f"die Oberflaeche {_E.GEMESSENE_MINDESTBREITE}")
# ⚠️ UND DER RAHMEN GEHOERT DAZU. Die gemessene Zahl ist die des
# INHALTS, `create_window` bekommt die des FENSTERS. Ohne Rahmen und
# Rollbalken bliebe der Inhalt unter der gemessenen Breite.
check(_E.WIDGET_RAHMEN > 0,
      "der Widget-Modus rechnet Rahmen und Rollbalken nicht mit — dann ist "
      "der Inhalt schmaler als gemessen")
check(_E.WIDGET_BREITE == _E.GEMESSENE_MINDESTBREITE + _E.WIDGET_RAHMEN,
      f"{_E.WIDGET_BREITE} ist nicht die Summe aus "
      f"{_E.GEMESSENE_MINDESTBREITE} und {_E.WIDGET_RAHMEN} — eine dritte "
      "Zahl ist die, die man beim naechsten Mal vergisst")
# ⚠️ Die Untergrenze des Fensters darf nicht unter die Oeffnungsbreite
# fallen — sonst laesst es sich unter die gemessene Grenze ziehen.
_m_widget = _re.search(r"breite = einstellungen\.WIDGET_BREITE(.*?)on_top=True",
                       (WURZEL / "app" / "fenster.py").read_text(
                           encoding="utf-8"), _re.S)
check(_m_widget is not None, "der Widget-Zweig ist nicht mehr zu finden")
if _m_widget:
    _mg = _re.search(r"min_size=\((\w+|\d+),", _m_widget.group(1))
    check(_mg is not None, "der Widget-Modus setzt keine Untergrenze")
    if _mg:
        _wert = _mg.group(1)
        _zahl = int(_wert) if _wert.isdigit() else _E.WIDGET_BREITE
        check(not _wert.isdigit() or _zahl >= _E.WIDGET_BREITE,
              f"das Widget-Fenster laesst sich auf {_zahl} ziehen, obwohl "
              f"es mit {_E.WIDGET_BREITE} oeffnet — darunter kommt der "
              "waagrechte Rollbalken")

check(set(fenster.TRAY_WORTE) == {"de", "fr", "it", "en"},
      "das Ablagefach kennt nicht die vier Bediensprachen")

# ⚠️ Ohne QApplication gibt es kein Ablagefach — und `tray_moeglich()`
# muss das SAGEN und nicht werfen. Diese Pruefung laeuft ohne Anzeige,
# also ist genau das hier der Normalfall.
check(fenster.tray_moeglich() is False,
      "tray_moeglich() meldet ein Ablagefach ohne QApplication")

# ⚠️ ZWEI WOERTER JE SPRACHE, und BEIDE beschriften etwas: «Beenden» und
# «Fenster zeigen».
#
# Geprueft wird nicht die ZAHL allein, sondern dass jedes Wort auch
# gesetzt wird. Woerter zu fuehren, die nichts beschriften, ist dieselbe
# Klasse wie eine Zusage im Kommentar.
_quelle_f = (WURZEL / "app" / "fenster.py").read_text(encoding="utf-8")
for _spr, _worte in fenster.TRAY_WORTE.items():
    check(len(_worte) == 2,
          f"TRAY_WORTE[{_spr}] fuehrt {len(_worte)} Woerter — erwartet "
          "sind Beenden und Fenster zeigen")
    for _w in _worte:
        check(_w.strip(), f"TRAY_WORTE[{_spr}] traegt ein leeres Wort")

# ⚠️ UND BEIDE WERDEN GESETZT. Ein gefuehrtes Wort, das nichts
# beschriftet, sieht nach Pflege aus und ist keine.
check("menu.addAction(zeigen_wort, umschalten)" in _quelle_f,
      "«Fenster zeigen» steht in TRAY_WORTE und beschriftet nichts")
check("menu.addAction(beenden_wort, beenden)" in _quelle_f,
      "«Beenden» steht in TRAY_WORTE und beschriftet nichts")

# ⚠️ UND DER EINTRAG STEHT UEBERALL. Ihn nur dort zu setzen, wo der
# Klick das Fenster nicht hervorholt, hiesse, den Schreibtisch ueber
# `XDG_CURRENT_DESKTOP` zu erraten. Liegt die Vermutung falsch, ist die
# App unerreichbar. Ein Eintrag, den man nicht anklickt, kostet eine
# Zeile.
check("XDG_CURRENT_DESKTOP" not in ohne_kommentare(_quelle_f),
      "das Ablagefach raet wieder am Schreibtisch herum — der Eintrag "
      "steht ueberall, dann braucht es keine Erkennung")

# Das X: mit Ablagefach versteckt es, ohne schliesst es. Nachgebaut, weil
# der echte Weg ein Fenster braeuchte.
#
# ⚠️ DREI FAELLE, NICHT ZWEI. Am selben Behandler haengt auch «Beenden».
# Ein Nachbau, der nur den Ausloeser «X» kennt, bliebe gruen ueber einem
# Behandler, der JEDES Schliessen abbricht — die App liesse sich dann nur
# noch ueber den Prozessmanager beenden.
_versteckt = []

def _beim_schliessen(hat_fach, beenden_gewuenscht=False):
    """Derselbe Entscheid wie in `main()` — hier ohne Fenster."""
    if beenden_gewuenscht:
        return True
    if not hat_fach:
        return True
    _versteckt.append(True)
    return False

check(_beim_schliessen(False) is True,
      "ohne Ablagefach wird das Schliessen abgefangen — dann ist die App "
      "weg, ohne Fenster und ohne Symbol")
check(_beim_schliessen(True) is False and _versteckt,
      "mit Ablagefach schliesst das X trotzdem")
check(_beim_schliessen(True, True) is True,
      "«Beenden» aus dem Ablagefach wird abgefangen — die App laesst sich "
      "dann nur ueber den Prozessmanager loswerden")

# ⚠️ Und dass `main()` diesen Entscheid WIRKLICH so faellt, statt ihn nur
# hier nachzubauen: eine Pruefung, die ihre eigene Nachbildung prueft,
# ist keine. Deshalb der Blick in den Quelltext.
_quelle = (WURZEL / "app" / "fenster.py").read_text(encoding="utf-8")
_m_schliessen = _re.search(r"def beim_schliessen\(\):(.*?)fenster\.events",
                           _quelle, _re.S)
check(_m_schliessen is not None, "`main()` haengt nichts an `closing`")
if _m_schliessen:
    _rumpf = _m_schliessen.group(1)
    check("tray_moeglich()" in _rumpf,
          "`main()` fragt beim Schliessen nicht, ob es ein Ablagefach gibt")
    check("return True" in _rumpf,
          "ohne Ablagefach gibt `main()` das Schliessen nicht frei")
    # ⚠️ VERSTECKEN, nicht minimieren. Ein minimiertes Fenster kommt unter
    # Wayland ueber das Ablagefach nicht zuverlaessig zurueck; ein
    # verstecktes schon. Ein Fenster, das zurueckkommt, ist mehr wert als
    # eines, das seine Stelle behaelt.
    check("hide()" in _rumpf, "`main()` versteckt das Fenster nicht")
    # ⚠️ Und ZUERST. Steht die Abfrage hinter dem Verstecken, ist sie
    # wirkungslos — der Behandler hat dann schon `False` gegeben.
    check("BEENDEN.is_set()" in _rumpf,
          "`main()` fragt den Beendenwunsch nicht ab — «Beenden» versteckt "
          "das Fenster dann nur")
    check(_rumpf.index("BEENDEN.is_set()") < _rumpf.index("hide()"),
          "der Beendenwunsch wird erst nach dem Verstecken gefragt")

# ⚠️ DER MENUEEINTRAG DARF NICHT MEHR AUF `self.close` ZEIGEN. Genau das
# war die Falle: `close()` laeuft in den Behandler, der abbricht.
_m_tray = _re.search(
    r"def tray_richten\(.*?def __init__\(self, fenster\):(.*?)sicht\.__init__ =",
    _quelle, _re.S)
check(_m_tray is not None, "`tray_richten()` richtet kein __init__ mehr ein")
if _m_tray:
    _rt = _m_tray.group(1)
    check("BEENDEN.set()" in _rt,
          "der Beenden-Eintrag merkt den Wunsch nicht vor")
    # ⚠️ Der DRITTE Parameter von `tray_bauen` ist der Beenden-Rueckruf.
    # Er muss der eigene Weg sein, nicht `self.close` — das liefe in den
    # Behandler und versteckte nur.
    #
    # Geprueft ueber die ARGUMENTE und nicht ueber einen Textausschnitt: der
    # Aufruf traegt selbst eine Klammer (`fenster_umschalten(self)`), an der
    # ein einfaches `[^)]*`-Muster abbricht und gruen meldet.
    _m_aufruf = _re.search(r"tray_bauen\((.*?)\)\s*$", _rt, _re.S | _re.M)
    check(_m_aufruf is not None, "`tray_bauen` wird nicht mehr aufgerufen")
    if _m_aufruf:
        _args = [a.strip() for a in _re.split(r",(?![^(]*\))",
                                              _m_aufruf.group(1))]
        check(len(_args) == 4,
              f"`tray_bauen` bekommt {len(_args)} Argumente statt vier: "
              f"{_args}")
        check(len(_args) == 4 and _args[2] == "beenden",
              "der Beenden-Rueckruf ist "
              f"{_args[2] if len(_args) > 2 else '?'} statt `beenden` — "
              "zeigt er auf `self.close`, laeuft er in den Behandler und "
              "versteckt nur")

# ⚠️ DER LINKSKLICK. Ohne diese Verbindung hoert das Symbol auf keinen
# Klick, und die Attrappe bliebe daruber gruen.
_m_bauen = _re.search(r"def tray_bauen\(.*?\n    return tray", _quelle, _re.S)
check(_m_bauen is not None, "`tray_bauen()` nicht gefunden")
if _m_bauen:
    _rb = _m_bauen.group(0)
    check("tray.activated.connect" in _rb,
          "das Ablagefachsymbol hoert auf keinen Klick")
    check("ActivationReason.Trigger" in _rb,
          "der einfache Linksklick wird nicht ausgewertet")
    check("tray._geklickt" in _rb,
          "der Rueckruf ist nicht festgemacht — Python raeumt ihn ab, und "
          "die Verbindung stirbt lautlos mit ihm")
    # ⚠️ ZWEI EINTRAEGE IM MENUE: «Beenden» und «Fenster zeigen». Ein
    # dritter waere einer, den niemand braucht.
    check(_rb.count("menu.addAction") == 2,
          f"das Rechtsklickmenue kennt {_rb.count('menu.addAction')} "
          "Eintraege, erwartet sind Beenden und Fenster zeigen")

# Der Umschalter, ohne Qt geprueft — mit einer Attrappe statt eines Fensters.
class _FensterAttrappe:
    def __init__(self, sichtbar=True, klein=False):
        self.sichtbar, self.klein, self.getan = sichtbar, klein, []
        self.lage = None
    def saveGeometry(self):
        self.getan.append("saveGeometry")
        return b"LAGE"
    def restoreGeometry(self, roh):
        self.lage = roh
        self.getan.append("restoreGeometry")
    def isVisible(self):
        return self.sichtbar
    def isMinimized(self):
        return self.klein
    def hide(self):
        self.sichtbar = False
        self.getan.append("hide")
    def showMinimized(self):
        self.klein = True
        self.getan.append("showMinimized")
    def showNormal(self):
        self.sichtbar, self.klein = True, False
        self.getan.append("showNormal")
    # Die Attrappe kennt nur, was `fenster_umschalten` benutzen darf, und
    # wirft bei allem anderen. Eine, die jedem Zugriff ein Objekt liefert,
    # verschluckte einen Wechsel des Rueckwegs.
    def show(self):
        self.sichtbar, self.klein = True, False
        self.getan.append("show")
    def windowState(self):
        self.getan.append("windowState")
        return 0
    def setWindowState(self, wert):
        self.zustand = wert
        self.klein = False
        self.getan.append("setWindowState")
    def raise_(self):
        self.getan.append("raise_")
    def activateWindow(self):
        self.getan.append("activateWindow")

# ⚠️⚠️ VERSTECKEN — UND DIE FRAGE IST ABGESCHLOSSEN.
#
# `showMinimized()` kam unter Wayland nicht zurueck, auch nicht mit
# `windowState`. Andere Qt-Anwendungen mit Ablagefach verhalten sich
# dort genauso: es ist die Wayland-Sperre (xdg-activation), nicht dieser
# Code. Das Ablagefach ist deshalb ein Schalter fuer sichtbar/unsichtbar;
# das Verkleinern gehoert der Fensterleiste.
#
# ⚠️ DIESE WACHE HAELT DEN ENTSCHEID, NICHT NUR DAS VERHALTEN. Wer wieder
# auf `showMinimized()` geht, wird rot und liest hier, warum es nicht
# geht.
_w = _FensterAttrappe(sichtbar=True)
check(fenster.fenster_umschalten(_w) == "versteckt" and not _w.sichtbar,
      "ein sichtbares Fenster wird beim Klick nicht versteckt")
check("hide" in _w.getan and "showMinimized" not in _w.getan,
      "es wird minimiert statt versteckt — unter Wayland kommt ein "
      "minimiertes Fenster ueber das Ablagefach nicht zurueck")
check(fenster.fenster_umschalten(_w) == "gezeigt" and _w.sichtbar,
      "das versteckte Fenster kommt beim Klick nicht zurueck")
# ⚠️ Und es kommt NACH VORNE. Ohne das steht es hinter dem, was gerade
# vorne ist: der Anwender klickt, etwas passiert, und er sieht es nicht.
check("raise_" in _w.getan and "activateWindow" in _w.getan,
      "das Fenster kommt zurueck, aber nicht nach vorne")
# Minimiert zaehlt als «weg», nicht als «sichtbar».
_wk = _FensterAttrappe(sichtbar=True, klein=True)
check(fenster.fenster_umschalten(_wk) == "gezeigt",
      "ein minimiertes Fenster wird beim Klick noch weiter versteckt")

# ⚠️ DIE LAGE WIRD GEMERKT UND WIEDERHERGESTELLT. `hide()` nimmt die
# Flaeche weg, und beim naechsten `showNormal()` entscheidet der
# Fenstermanager neu — ohne gemerkte Lage steht das Fenster danach in
# der Bildschirmmitte.
#
# ⚠️ Geprueft wird, dass GEFRAGT und WIEDERHERGESTELLT wird — nicht, dass
# das Fenster danach an einer bestimmten Stelle steht. Unter Wayland
# entscheidet darueber der Fenstermanager, und eine Pruefung, die etwas
# zusichert, das das Protokoll nicht hergibt, waere eine falsche Zusage.
_wl = _FensterAttrappe(sichtbar=True)
fenster.fenster_umschalten(_wl)          # verstecken
check("saveGeometry" in _wl.getan,
      "die Lage wird vor dem Verstecken nicht gemerkt")
fenster.fenster_umschalten(_wl)          # zeigen
check("restoreGeometry" in _wl.getan,
      "die gemerkte Lage wird beim Zeigen nicht wiederhergestellt")
check(_wl.lage == b"LAGE", f"eine andere Lage kam zurueck: {_wl.lage!r}")
# ⚠️ Und in dieser Reihenfolge: auf ein unsichtbares Fenster wirkt
# `restoreGeometry` nicht.
check(_wl.getan.index("showNormal") < _wl.getan.index("restoreGeometry"),
      "die Lage wird gesetzt, bevor das Fenster wieder da ist")

# Das Symbol muss es geben — sonst steht ein leerer Fleck im Ablagefach.
check((WURZEL / "app" / "static" / "maske.svg").is_file(),
      "das Symbol des Ablagefachs fehlt")

print("   OK   aus als Vorgabe, vier Sprachen, X versteckt, Beenden beendet")


print("\n18. Die Ausgabe ueberlebt einen weggebrochenen Leser")
# Haengt ein Starter eine Pipe an die Ausgabe und geht, waehrend das
# Modell laedt, wirft der naechste `print` einen `BrokenPipeError`.
# `laden_und_starten()` faengt jede Ausnahme und zeigt sie als
# Fehlerseite — das Werkzeug stirbt dann, weil es nicht drucken kann.
#
# ⚠️ ECHT GEPRUEFT, nicht nachgebaut: ein eigener Prozess, dessen Leser
# wirklich weggeht. Eine Attrappe, die `BrokenPipeError` wirft, pruefte
# nur, dass wir `BrokenPipeError` abfangen — nicht, dass der Fall damit
# erledigt ist.
import subprocess  # noqa: E402
import textwrap  # noqa: E402

_prog = textwrap.dedent(f"""
    import sys, time
    sys.path.insert(0, {str(WURZEL)!r})
    from core import ausgabe
    ausgabe.sichern()
    print("erste Zeile"); sys.stdout.flush()
    time.sleep(0.4)                      # der Leser geht
    print("zweite Zeile"); sys.stdout.flush()
    print("dritte Zeile"); sys.stdout.flush()
    sys.exit(0)
""")
_p = subprocess.Popen([sys.executable, "-c", _prog],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_p.stdout.close()
_p.wait(timeout=15)
_stderr = _p.stderr.read().decode(errors="replace")
_p.stderr.close()
check(_p.returncode == 0,
      f"der Prozess starb mit {_p.returncode}, obwohl nur die Ausgabe "
      f"weggebrochen ist:\n      {_stderr.strip()[:300]}")
check("BrokenPipeError" not in _stderr,
      f"BrokenPipeError kam trotzdem durch:\n      {_stderr.strip()[:300]}")

# Und die Gegenprobe im selben Lauf: OHNE die Sicherung muss es sterben.
_ohne = _prog.replace("ausgabe.sichern()", "pass")
_q = subprocess.Popen([sys.executable, "-c", _ohne],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_q.stdout.close()
_q.wait(timeout=15)
_qerr = _q.stderr.read().decode(errors="replace")
_q.stderr.close()
check(_q.returncode != 0 or "BrokenPipeError" in _qerr,
      "ohne `ausgabe.sichern()` laeuft es auch durch — dann prueft dieser "
      "Punkt nichts")

# ⚠️ Und `main()` muss sie ALS ERSTES rufen. Danach waere zu spaet: die
# ersten Zeilen sind genau die, die beim Laden gedruckt werden.
_m_main = _re.search(r"def main\(\) -> int:(.*?)args = ap\.parse_args\(\)",
                     _quelle, _re.S)
check(_m_main is not None, "`main()` nicht gefunden")
if _m_main:
    check("ausgabe.sichern()" in _m_main.group(1),
          "`main()` sichert die Ausgabe nicht, bevor es druckt")
if not failures:
    print("   OK   Leser weg, Prozess laeuft weiter (und ohne Sicherung nicht)")


print("\n19. Nur EIN MASCHERA")
# Ein Doppelklick mehr darf kein zweites Fenster oeffnen. Die
# Portpruefung allein genuegt nicht: sie merkt den vergebenen Port und
# folgert «nimm einen anderen» — jedes Fenster suchte sich dann seinen
# eigenen Port.
from core import einmalig  # noqa: E402

_sockel = Path(_temp.name) / "probe.sock"

check(einmalig.laeuft_schon(_sockel) is False,
      "ohne laufende App meldet `laeuft_schon()` trotzdem eine")

_gesehen = threading.Event()
_faden = einmalig.horche(_gesehen.set, _sockel)
check(_faden is not None, "der Horcher ist nicht gestartet")
check(einmalig.laeuft_schon(_sockel) is True,
      "mit laufendem Horcher wird die laufende App nicht erkannt")
check(_gesehen.wait(3.0),
      "der zweite Start hat sich gemeldet, das Fenster erfaehrt es nicht")

# ⚠️ EINE LEICHE DARF NICHT SPERREN. Der Sockel ueberlebt einen Absturz;
# waere schon die DATEI das Merkmal, liesse sich MASCHERA danach nie mehr
# starten. Deshalb wird verbunden und nicht nachgesehen — dieselbe
# Ueberlegung wie bei `belegt()`, das bindet statt anzuklopfen.
_tot = Path(_temp.name) / "leiche.sock"
_tot.touch()
check(einmalig.laeuft_schon(_tot) is False,
      "eine tote Sockeldatei gilt als laufende App — dann startet "
      "MASCHERA nach einem Absturz nie wieder")
check(not _tot.exists(), "die tote Sockeldatei wird nicht weggeraeumt")

# Und `main()` fragt VOR dem Modell.
if _m_main is not None:
    _vor_modell = _quelle[_quelle.index("def main() -> int:"):]
    check("laeuft_schon()" in _vor_modell,
          "`main()` fragt nicht, ob schon eine laeuft")
    check(_vor_modell.index("laeuft_schon()") < _vor_modell.index("belegt(wirt, port)"),
          "die Frage nach der laufenden App kommt erst nach der Portpruefung "
          "— dann fragt der Dialog wieder nach einem anderen Port")
if not failures:
    print("   OK   erkannt, gemeldet, Leiche raeumt sich weg")


print("\n20. Das Fenster traegt die Maske, nicht das W")
# «W» ist pywebviews eigenes Symbol; das Fenster soll die Maske tragen.
_m_symbol = _re.search(r"def symbol_richten\(\).*?return \"Maske als",
                       _quelle, _re.S)
check(_m_symbol is not None, "`symbol_richten()` fehlt")
if _m_symbol:
    _rs = _m_symbol.group(0)
    check("maske.svg" in _rs, "das Fenstersymbol kommt nicht aus der Maske")
    # ⚠️ BEIDES. Das eine traegt die Titelleiste, das andere die
    # Fensterliste; wer nur eines setzt, hat das «W» noch woanders.
    check("self.setWindowIcon" in _rs,
          "das Fenster selbst bekommt kein Symbol")
    check("anwendung.setWindowIcon" in _rs,
          "die Anwendung bekommt kein Symbol — in der Fensterliste steht "
          "weiter das W")
check("symbol_richten()" in _quelle.split("def symbol_richten")[0]
      or "symbol_richten())" in _quelle,
      "`symbol_richten()` wird nie gerufen")
if not failures:
    print("   OK   Maske am Fenster und an der Anwendung")

print("\n21. Der Startbildschirm kennt den Dunkelmodus")
# Dieser Bildschirm ist eigenes HTML in Python. Er wird weder von
# `maschera.css` gespeist noch von den Wachen in `test_oberflaeche.js`
# erfasst — die lesen das Blatt und das Skript. Ohne eigenen dunklen
# Zweig blitzt er weiss auf, bevor die dunkle Oberflaeche kommt.
_seite = fenster.startseite()
_stil = _seite[_seite.index("<style>"):_seite.index("</style>")]

check("prefers-color-scheme: dark" in _stil,
      "der Startbildschirm hat keinen dunklen Zweig — er blitzt weiss auf")
check(':root:not([data-thema="hell"])' in _stil,
      "die Systemwahl schlaegt hier die ausdrueckliche Wahl «hell»")
check(':root[data-thema="dunkel"]' in _stil,
      "«dunkel» laesst sich hier nicht erzwingen")

# ⚠️ ZWEI EINHAENGEPUNKTE, EINE LISTE — wie im Blatt. Zwei Listen waeren
# zwei Verwalter, und die eine bliebe beim naechsten Farbwechsel zurueck.
_marken = lambda t: set(_re.findall(r"(--[a-z]+):", t))
_i = _stil.index("prefers-color-scheme: dark")
_j = _stil.index(':root[data-thema="dunkel"]')
check(_marken(_stil[_i:_j]) == _marken(_stil[_j:]),
      "die zwei Einhaengepunkte des Startbildschirms tragen verschiedene "
      "Marken")

# ⚠️ Und KEINE Farbe ausserhalb der Markenschicht. Sonst bleibt beim
# naechsten Knopf wieder eine hell zurueck.
_ohne_marken = _re.sub(r"--[a-z]+:\s*#[0-9a-f]{3,6}", "", _stil)
_rest = _re.findall(r"#[0-9a-fA-F]{3,6}\b", _ohne_marken)
check(not _rest,
      f"{len(_rest)} Farbliteral(e) im Startbildschirm ausserhalb der "
      f"Marken: {sorted(set(_rest))[:4]}")

# Die helle Fassung ist unveraendert — das Aufraeumen sieht man nicht.
check("--grund:#fff" in _stil and "--schrift:#1d1f20" in _stil,
      "die hellen Werte des Startbildschirms haben sich verschoben")
if not failures:
    print("   OK   zwei Einhaengepunkte, eine Liste, keine Farbe daneben")










print("\n22. Flatpak und Abbild fuehren dieselben Pakete")
# `requirements-flatpak.txt` kann `requirements-paket.txt` nicht mit `-r`
# einbinden (der Bau im Sandkasten sieht die Datei nicht). Damit stehen die
# Pakete an zwei Orten. Erlaubt sind genau die Unterschiede, die die
# Flatpak-Datei selbst begruendet: `pywebview` OHNE `[qt]` und `qtpy`
# kommen dazu, PyQt kommt aus dem BaseApp und steht nirgends.


def _pakete(pfad: Path) -> dict[str, str]:
    """Name -> Schranke, ohne Kommentare, Extras und Index-Zeilen."""
    aus = {}
    for z in pfad.read_text(encoding="utf-8").splitlines():
        z = z.split("#", 1)[0].strip()
        if not z or z.startswith("-"):
            continue
        m = _re.match(r"([A-Za-z0-9_.-]+)(\[[^\]]*\])?\s*(.*)$", z)
        if m:
            aus[m.group(1).lower()] = m.group(3).replace(" ", "")
    return aus


def _indizes(pfad: Path) -> list[str]:
    return sorted(z.strip() for z in pfad.read_text(encoding="utf-8")
                  .splitlines() if z.strip().startswith("--"))


_paket_dir = WURZEL / "tools" / "paket"
_abbild = _pakete(_paket_dir / "requirements-paket.txt")
_flatpak = _pakete(_paket_dir / "requirements-flatpak.txt")
_nur_flatpak = {"pywebview", "qtpy"}
check(set(_flatpak) - _nur_flatpak == set(_abbild),
      f"andere Pakete: nur im Abbild "
      f"{sorted(set(_abbild) - set(_flatpak))}, nur im Flatpak "
      f"{sorted(set(_flatpak) - set(_abbild) - _nur_flatpak)}")
for _name, _schranke in _abbild.items():
    if _name in _flatpak:
        check(_flatpak[_name] == _schranke,
              f"{_name}: Abbild {_schranke!r}, Flatpak {_flatpak[_name]!r}")
check(not any(n.startswith("pyqt") for n in _flatpak),
      "PyQt steht in requirements-flatpak.txt — es kommt aus dem BaseApp, "
      "ein zweites waeren 525 MB doppelt")
check("[qt]" not in ohne_kommentare(
          (_paket_dir / "requirements-flatpak.txt").read_text(
              encoding="utf-8")),
      "pywebview[qt] im Flatpak zieht PyQt6 nach")
check(_indizes(_paket_dir / "requirements-paket.txt")
      == _indizes(_paket_dir / "requirements-flatpak.txt"),
      "die Index-Zeilen (CPU-torch) unterscheiden sich")
if not failures:
    print(f"   OK   {len(_abbild)} Pakete gleich, dazu {sorted(_nur_flatpak)}")


print("\n23. Die Bruecken zur Seite zeigen nur ihre Methoden")
# pywebview macht jedes oeffentliche Feld eines `js_api`-Objekts fuer die
# Seite erreichbar und steigt dafuer hinein. Ein oeffentliches Feld mit dem
# Fensterobjekt gaebe der Seite `load_url` und `evaluate_js` — und unter
# Windows (WinForms) laeuft das Hineinsteigen endlos
# (`native.AccessibilityObject.Bounds.Empty.Empty…`): das Fenster reagiert
# nicht mehr, und der Prozess waechst, bis der Speicher voll ist.
#
# Geprueft wird am echten Objekt, nicht am Quelltext: jedes Feld, das nicht
# mit `_` beginnt, ist ein Fehler — auch eines, das heute harmlos ist.
import threading as _th23                                          # noqa: E402
_b = fenster.Onboarding({}, Path(_temp.name), _th23.Event())
_b._fenster = object()
_offen = sorted(n for n in vars(_b) if not n.startswith("_"))
check(not _offen,
      f"die Bruecke traegt oeffentliche Felder: {_offen} — pywebview reicht "
      f"sie an die Seite weiter und steigt in sie hinein")
_methoden = sorted(n for n in dir(_b)
                   if not n.startswith("_") and callable(getattr(_b, n)))
check(_methoden == ["holen", "neustart", "spaeter", "sprache", "weiter"],
      f"die Bruecke bietet der Seite {_methoden} an, erwartet sind "
      f"holen, neustart, spaeter, sprache, weiter")
# Die kleine Bruecke der laufenden Oberflaeche: nur `neustart`.
_k = fenster.Bruecke()
_k._fenster = object()
check(not [n for n in vars(_k) if not n.startswith("_")],
      "die kleine Bruecke traegt oeffentliche Felder")
_km = sorted(n for n in dir(_k)
             if not n.startswith("_") and callable(getattr(_k, n)))
check(_km == ["neustart"], f"die kleine Bruecke bietet {_km} an")

# Der Nachfolger startet auf demselben Weg — und wartet auf den Vorgaenger.
_nb = fenster.neustart_befehl
check(_nb(["C:/m/fenster.py", "--x"], "C:/M/MASCHERA.exe", True, None, 7)
      == ["C:/M/MASCHERA.exe", "--x", "--nach-pid", "7"],
      "Windows startet nicht die .exe neu")
check(_nb(["/tmp/.mount_x/fenster.py", "--model", "/tmp/.mount_x/m", "--y"],
          "/tmp/.mount_x/python3", False, "/opt/M.AppImage", 8)
      == ["/opt/M.AppImage", "--y", "--nach-pid", "8"],
      "die AppImage startet das Python im verschwindenden Einhaengepunkt "
      "oder behaelt den alten Modellpfad")
check(_nb(["app/fenster.py", "--nach-pid", "3", "--z"], "/usr/bin/python3",
          False, None, 9)
      == ["/usr/bin/python3", "app/fenster.py", "--z", "--nach-pid", "9"],
      "ein alter --nach-pid wird weitergereicht")
_tot = subprocess.Popen([sys.executable, "-c", "pass"])
_tot.wait()
check(fenster.warte_auf_ende(_tot.pid, frist=2) is True,
      "warte_auf_ende erkennt einen beendeten Prozess nicht")
check(fenster.warte_auf_ende(os.getpid(), frist=0.5) is False,
      "warte_auf_ende haelt einen laufenden Prozess fuer beendet")
if not failures:
    print(f"   OK   {', '.join(_methoden)} und neustart — kein Feld; "
          "Nachfolger auf drei Wegen")


print("\n24. Unter Windows: Infobereich und Hervorholen ohne Qt")
# Unter Windows baut `pystray` das Symbol, und `zeigen_windows()` liest den
# Wunsch eines zweiten Starts. Geprueft an strengen Attrappen: `pystray`
# und `PIL` werden fuer diesen Punkt ersetzt, das Fenster merkt sich, was
# mit ihm geschah.
import time                                                     # noqa: E402
import types as _ty24                                              # noqa: E402


class _Fenster24:
    def __init__(self):
        self.getan = []

    def show(self):
        self.getan.append("show")

    def restore(self):
        self.getan.append("restore")

    def destroy(self):
        self.getan.append("destroy")


class _Icon24:
    def __init__(self, name, bild, titel, menu):
        self.menu, self.titel, self.gestoppt, self.laeuft = menu, titel, False, False

    def run_detached(self):
        self.laeuft = True

    def stop(self):
        self.gestoppt = True


_pystray = _ty24.SimpleNamespace(
    Icon=_Icon24,
    Menu=lambda *eintraege: list(eintraege),
    MenuItem=lambda wort, rueckruf, default=False: (wort, rueckruf, default))
_pil = _ty24.ModuleType("PIL")
_pil.Image = _ty24.SimpleNamespace(open=lambda pfad: ("bild", str(pfad)))
_vorher24 = {n: sys.modules.get(n) for n in ("pystray", "PIL")}
sys.modules["pystray"], sys.modules["PIL"] = _pystray, _pil
try:
    _f = _Fenster24()
    fenster.BEENDEN.clear()
    _icon = fenster.tray_windows_bauen(_f, "it")
    check(_icon.laeuft, "das Symbol laeuft nicht an (`run_detached` fehlt)")
    check(_icon.titel == fenster.TITEL, "das Symbol traegt nicht den Titel")
    _worte = [e[0] for e in _icon.menu]
    check(_worte == list(reversed(fenster.TRAY_WORTE["it"])),
          f"das Menue sagt {_worte}, erwartet «Fenster zeigen», «Beenden» "
          f"in der Bediensprache")
    check([e[2] for e in _icon.menu] == [True, False],
          "der Linksklick holt das Fenster nicht hervor")
    _icon.menu[0][1](_icon, None)
    check(_f.getan == ["show", "restore"],
          f"«Fenster zeigen» tut {_f.getan}")
    _icon.menu[1][1](_icon, None)
    check(fenster.BEENDEN.is_set(),
          "«Beenden» merkt den Wunsch nicht vor — der Schliessbehandler "
          "versteckte dann nur")
    check(_icon.gestoppt, "«Beenden» laesst das Symbol im Infobereich stehen")
    check(_f.getan[-1] == "destroy", "«Beenden» schliesst das Fenster nicht")

    # Ein zweiter Start holt das Fenster hervor.
    fenster.BEENDEN.clear()
    _g = _Fenster24()
    _faden = fenster.zeigen_windows(_g)
    fenster.ZEIGEN.set()
    for _ in range(40):
        if "show" in _g.getan:
            break
        time.sleep(0.05)
    check("show" in _g.getan,
          "ein zweiter Start holt das Fenster unter Windows nicht hervor")
    fenster.BEENDEN.set()
    _faden.join(timeout=2)
    check(not _faden.is_alive(), "der Horchfaden endet nicht mit dem Programm")
finally:
    for _n, _m in _vorher24.items():
        if _m is None:
            sys.modules.pop(_n, None)
        else:
            sys.modules[_n] = _m
    fenster.BEENDEN.clear()
    fenster.ZEIGEN.clear()
if not failures:
    print("   OK   Symbol, zwei Eintraege, Beenden beendet, zweiter Start holt hervor")

print("\n25. Kein Paket nimmt Pickle-Dateien aus dem Modellordner mit")
# ⚠️ `runs/ch-v63b/training_args.bin` ist eine Pickle-Datei. Docker
# (`COPY runs/ch-v63b/`), AppImage (`cp -a`) und Windows (`--add-data`)
# kopierten das ganze Verzeichnis; ausgeschlossen war nur `checkpoint-*`.
# Die Datei wird zur Laufzeit nicht gelesen (`core/modell.py`, `PFLICHT`),
# kann aber beim Oeffnen Code ausfuehren — im Paket hat sie nichts verloren.
#
# Wie Punkt 12: Windows wird AUSGEFUEHRT (auf einem kleinen Modellordner),
# die beiden anderen Verpackungen statisch gelesen — und zwar jede Endung
# einzeln, damit eine vergessene auffaellt.
_endungen25 = ["*.bin", "*.pt", "*.pth", "*.pkl", "*.ckpt", "*.pickle"]
check(all(_e in _wbm.MODELL_DRAUSSEN for _e in _endungen25)
      and "checkpoint-*" in _wbm.MODELL_DRAUSSEN,
      f"windows_bauen.MODELL_DRAUSSEN fuehrt nicht alle Endungen: "
      f"{_wbm.MODELL_DRAUSSEN}")
_docker25 = (WURZEL / ".dockerignore").read_text(encoding="utf-8")
_appimage25 = ohne_kommentare((WURZEL / "tools/paket/appimage_bauen.fish")
                              .read_text(encoding="utf-8"))
for _e in _endungen25:
    check(f"runs/ch-v63b/{_e}" in _docker25,
          f".dockerignore laesst {_e} im Modellordner nicht weg")
    check(f"-name '{_e}'" in _appimage25,
          f"appimage_bauen.fish loescht {_e} im Modellordner nicht")
with _tf.TemporaryDirectory() as _tmp25:
    _wurzel25 = Path(_tmp25) / "baum"
    _modell25 = _wurzel25 / "runs" / _wbm.MODELL
    (_modell25 / "checkpoint-100").mkdir(parents=True)
    for _n in ("config.json", "model.safetensors", "pack.json",
               "training_args.bin", "pytorch_model.bin", "x.pt", "x.pth",
               "x.pkl", "x.ckpt", "x.pickle", "checkpoint-100/optimizer.pt"):
        (_modell25 / _n).write_bytes(b"x")
    _alt25 = _wbm.WURZEL
    _wbm.WURZEL = _wurzel25
    try:
        _ziel25 = Path(_tmp25) / "modell"
        _wbm.modell_zusammenstellen(_ziel25)
    finally:
        _wbm.WURZEL = _alt25
    _drin25 = sorted(_p.name for _p in _ziel25.rglob("*") if _p.is_file())
    check(_drin25 == ["config.json", "model.safetensors", "pack.json"],
          f"der Windows-Modellordner enthaelt {_drin25}")
if not failures:
    print("   OK   Docker, AppImage und Windows lassen Pickle und Checkpoints weg")

print("\n26. Der macOS-Bau teilt die Listen mit Windows, die Workflows sind zahm")
# ⚠️ `macos_bauen.py` ist neu und auf einem Mac noch nicht gemessen. Was sich
# pruefen laesst, ohne einen Mac zu haben, ist die EIGENSCHAFT, an der ein
# Fehler am teuersten waere:
#   1. Der Bau benutzt die Zusammenstellung des Windows-Baus — dieselben
#      Listen, dieselbe Pickle-Sperre. Eine zweite, abgeschriebene Liste
#      bliebe beim naechsten Aendern zurueck (so war es bei den Paketen bis
#      0.9.58).
#   2. JEDER Workflow darf nur lesen, und jede Action ist auf einen Commit
#      festgenagelt. Eine Marke wie `@v4` laesst sich verschieben.
#   3. Der macOS-Workflow startet nur von Hand (er holt 1,2 GB und braucht
#      rund eine Stunde); der Testlauf nur bei Push und Pull Request — nie
#      `pull_request_target`, das Beitraegen von aussen Geheimnisse und
#      Schreibrechte liehe.
_mac = ohne_kommentare((WURZEL / "tools/paket/macos_bauen.py")
                       .read_text(encoding="utf-8"))
for _name in ("wb.zusammenstellen(", "wb.modell_zusammenstellen(",
              "wb.importe()", "wb.DATEN"):
    check(_name in _mac, f"macos_bauen.py benutzt {_name} nicht — dann "
          "laufen die Listen von Windows und macOS auseinander")
_wfs = sorted((WURZEL / ".github" / "workflows").glob("*.yml")) \
    if (WURZEL / ".github" / "workflows").is_dir() else []
if not _wfs:
    print("   HINWEIS kein .github/workflows/ — Punkt 26 prueft nur den Bau")
else:
    import yaml as _yaml26
    for _wf in _wfs:
        _w = _yaml26.safe_load(_wf.read_text(encoding="utf-8"))
        _aus = _w.get(True, _w.get("on"))   # YAML liest `on` als True
        _ausl = set(_aus if isinstance(_aus, (list, dict)) else [_aus])
        check(_w.get("permissions") == {"contents": "read"},
              f"{_wf.name} darf mehr als lesen: {_w.get('permissions')}")
        check("pull_request_target" not in _ausl,
              f"{_wf.name} nutzt pull_request_target — das liehe Beitraegen "
              "von aussen Geheimnisse und Schreibrechte")
        _text26 = _wf.read_text(encoding="utf-8")
        _uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", _text26, re.M)
        check(len(_uses) >= 2, f"{_wf.name}: nur {len(_uses)} Actions "
              "gefunden — die Wache sucht an der falschen Stelle")
        for _u in _uses:
            check(re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", _u) is not None,
                  f"{_wf.name}: Action nicht auf einen Commit festgenagelt: "
                  f"{_u}")
        if _wf.name == "macos.yml":
            check(_ausl == {"workflow_dispatch"},
                  f"der macOS-Workflow startet nicht nur von Hand: {_aus}")
        if _wf.name == "tests.yml":
            check(_ausl <= {"push", "pull_request"} and _ausl,
                  f"der Testlauf startet bei etwas anderem als Push und "
                  f"Pull Request: {_aus}")
if not failures:
    print(f"   OK   gemeinsame Listen; {len(_wfs)} Workflows: nur lesen, "
          "Actions gepinnt, richtige Ausloeser")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Fenster, Adresse, Port und Berechtigungen in Ordnung.")
