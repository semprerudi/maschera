#!/usr/bin/env python3
"""Das Nachladen des Modells — ohne Netz, ohne Fenster, ohne 1,2 GB.

    python3 tests/test_modell.py

⚠️ **Die Quelle ist ein eigener Server auf 127.0.0.1.** Gegen Hugging Face
zu pruefen hiesse, bei jedem Lauf ein Gigabyte zu ziehen und beim
Ausbleiben der Verbindung rot zu werden — eine Wache, die vom Netz
abhaengt, meldet Netzausfaelle und keine Fehler.

⚠️ **Die wichtigsten Punkte sind die, in denen es SCHIEFGEHT.** Ein
Holweg, der bei gutem Wetter funktioniert, ist die Haelfte; die andere
ist, dass eine falsche Datei nicht liegen bleibt und wie ein fertiges
Modell aussieht.
"""
import hashlib
import http.server
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from core import modell                                        # noqa: E402
from core.modell import PFLICHT, Abgelehnt                     # noqa: E402

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


TMP = Path(tempfile.mkdtemp(prefix="maschera-modell-"))
INHALT = {n: (f"inhalt von {n} ".encode() * 40) for n in PFLICHT}

# --- Ein Server, der genau diese fuenf Dateien ausliefert -------------------
QUELLE = TMP / "quelle"
QUELLE.mkdir()
for _n, _b in INHALT.items():
    (QUELLE / _n).write_bytes(_b)


class Stille(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


_srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0),
    lambda *a, **k: Stille(*a, directory=str(QUELLE), **k))
threading.Thread(target=_srv.serve_forever, daemon=True).start()
PORT = _srv.server_address[1]


def manifest(kaputt: str | None = None) -> dict:
    """Ein Manifest ueber die fuenf Proben. `kaputt` verfaelscht eine Summe."""
    dateien = {}
    for n, b in INHALT.items():
        summe = hashlib.sha256(b).hexdigest()
        if n == kaputt:
            summe = "0" * 64
        dateien[n] = {"bytes": len(b), "sha256": summe}
    return {"name": "probe",
            "quelle": f"http://127.0.0.1:{PORT}/{{datei}}",
            "bytes": sum(len(b) for b in INHALT.values()),
            "dateien": dateien}


print("1. Ein vollstaendiges Modell wird gefunden, ein halbes nicht")
_ort = TMP / "halb"
_ort.mkdir()
check(not modell.vollstaendig(_ort), "ein LEERES Verzeichnis gilt als Modell")
for _n in PFLICHT[:-1]:
    (_ort / _n).write_bytes(b"x")
check(not modell.vollstaendig(_ort),
      "vier von fuenf Dateien gelten als vollstaendiges Modell — dann "
      "startet das Werkzeug in ein Modell hinein, das es nicht gibt")
(_ort / PFLICHT[-1]).write_bytes(b"x")
check(modell.vollstaendig(_ort), "fuenf von fuenf gelten NICHT als Modell")
print("   OK   leer nein, vier nein, fuenf ja")

print("\n2. Geholt wird nur auf Befehl — und dann vollstaendig")
_ziel = TMP / "geholt"
_gesehen = []
_ergebnis = modell.hole(manifest(), _ziel,
                        melde=lambda n, a, b: _gesehen.append(n))
check(modell.vollstaendig(_ergebnis), "nach dem Holen fehlt etwas")
for _n in PFLICHT:
    check((_ziel / _n).read_bytes() == INHALT[_n],
          f"{_n} kam anders an, als es abgeschickt wurde")
check(set(_gesehen) == set(PFLICHT),
      f"die Anzeige sah nicht alle Dateien: {sorted(set(_gesehen))}")
print(f"   OK   {len(PFLICHT)} Dateien, Inhalt gleich, Anzeige vollstaendig")

print("\n3. Eine falsche Pruefsumme bleibt NICHT liegen")
# ⚠️⚠️ DER WICHTIGSTE PUNKT DIESER DATEI. Bliebe die falsche Datei am
# richtigen Platz, saehe `vollstaendig()` sie beim naechsten Start und
# meldete ein fertiges Modell. Der Anwender bekaeme eine Erkennung, die
# auf etwas laeuft, das niemand geprueft hat — und die Anzeige waere
# gruen. Genau die Bauart, vor der «ein leerer Befund ist keine
# Entwarnung» warnt, nur schlimmer: hier ist der Befund nicht leer,
# sondern falsch.
_ziel3 = TMP / "kaputt"
try:
    modell.hole(manifest(kaputt="tokenizer.json"), _ziel3)
    check(False, "eine falsche Pruefsumme wurde angenommen")
except Abgelehnt as e:
    check("Pruefsumme" in str(e), f"abgewiesen, aber mit falschem Grund: {e}")
check(not (_ziel3 / "tokenizer.json").is_file(),
      "die verworfene Datei liegt trotzdem da")
check(not list(_ziel3.glob("*.teil")),
      "eine `.teil`-Datei ist liegengeblieben")
check(not modell.vollstaendig(_ziel3),
      "das halbe Verzeichnis gilt als fertiges Modell — beim naechsten "
      "Start liefe die Erkennung darauf los")
print("   OK   abgewiesen, verworfen, kein Rest, gilt nicht als Modell")

print("\n4. Eine fehlende Quelle bricht ab, statt Leeres abzulegen")
_m = manifest()
_m["quelle"] = f"http://127.0.0.1:{PORT}/gibtesnicht-{{datei}}"
_ziel4 = TMP / "leer"
try:
    modell.hole(_m, _ziel4)
    check(False, "eine unerreichbare Quelle wurde nicht gemeldet")
except Abgelehnt:
    pass
check(not list(_ziel4.glob("*.teil")), "`.teil` liegengeblieben")
check(not modell.vollstaendig(_ziel4), "leeres Verzeichnis gilt als Modell")
print("   OK   Abbruch ohne Rest")

print("\n5. Ein Abbruch mittendrin laesst nichts Halbes zurueck")
# ⚠️ Der Anwender darf jederzeit abbrechen — das steht so in der
# Forderung an den Dialog. Wichtig ist nicht, DASS es abbricht, sondern
# was danach auf der Platte liegt.
_ziel5 = TMP / "abbruch"
try:
    modell.hole(manifest(), _ziel5, abbruch=lambda: True)
    check(False, "der Abbruch wurde nicht beachtet")
except Abgelehnt as e:
    check("abgebrochen" in str(e), f"anderer Grund als Abbruch: {e}")
check(not list(_ziel5.glob("*.teil")), "`.teil` nach Abbruch liegengeblieben")
check(not modell.vollstaendig(_ziel5), "nach Abbruch gilt es als Modell")
print("   OK   abgebrochen, nichts Halbes zurueck")

print("\n6. Ein zweiter Anlauf holt nur, was fehlt")
# ⚠️ 1,2 GB zweimal ueber Mobilfunk sind genau der Schaden, den die Frage
# vor dem Laden verhindern soll. Wer nach einem Abbruch neu anfaengt, soll
# die fertigen Dateien behalten.
_ziel6 = TMP / "zweiter"
modell.hole(manifest(), _ziel6)
(_ziel6 / "tokenizer.json").unlink()
_nochmal = []
modell.hole(manifest(), _ziel6, melde=lambda n, a, b: _nochmal.append(n))
check(modell.vollstaendig(_ziel6), "der zweite Anlauf blieb unvollstaendig")
check(_nochmal.count("model.safetensors") <= 1,
      "die grosse Datei wurde ein zweites Mal geholt, obwohl sie stimmte")
print("   OK   die vorhandenen bleiben, die fehlende kommt")

print("\n7. `pruefe()` findet eine veraenderte Datei")
_schaeden = modell.pruefe(_ziel6, manifest())
check(not _schaeden, f"ein sauberes Modell wird bemaengelt: {_schaeden}")
(_ziel6 / "config.json").write_bytes(b"etwas anderes")
_schaeden = modell.pruefe(_ziel6, manifest())
check(any("config.json" in s for s in _schaeden),
      "eine veraenderte Datei faellt nicht auf")
print("   OK   sauber still, veraendert gemeldet")

print("\n8. Das Manifest im Pack ist lesbar und deckt alle Pflichtdateien")
_m8 = modell.manifest("ch")
check(_m8["dateien"].keys() >= set(PFLICHT),
      f"das Manifest kennt nicht alle Pflichtdateien: {sorted(_m8['dateien'])}")
check("{datei}" in _m8["quelle"],
      f"die Quelle hat keine Stelle fuer den Dateinamen: {_m8['quelle']}")
check(modell.groesse(_m8) > 1_000_000_000,
      f"das Manifest meldet {modell.groesse(_m8)} Bytes — das ist kein "
      f"Modell dieser Bauart")
print(f"   OK   {modell.groesse(_m8) / 1e9:.2f} GB aus packs/ch/modell.json")

print("\n9. Der Ort ist NICHT ~/.config/")
# ⚠️ «Nichts wird geschrieben ausser den Einstellungen» — ein Modell ist
# keine Einstellung. Es gehoert unter XDG_DATA_HOME, damit es beim
# Sichern des Heimatverzeichnisses nicht mitfaehrt und beim Loeschen
# nichts kostet.
from core import pfade                                          # noqa: E402
_ort9 = str(pfade.modell("probe"))
check(".config" not in _ort9,
      f"das Modell landet unter .config: {_ort9}")
check("share" in _ort9 or os.environ.get("XDG_DATA_HOME"),
      f"das Modell landet nicht im Datenverzeichnis: {_ort9}")
print(f"   OK   {_ort9}")

print("\n9b. Ein Netzfehler sagt, wo zu suchen ist")
# ⚠️⚠️ Hugging Face antwortet mit 401 AUCH auf ein Repositorium, das es
# nicht gibt oder das nicht oeffentlich ist — es will dessen Existenz nicht
# verraten. «config.json nicht erreichbar: HTTP Error 401» liest sich wie
# ein Anmeldeproblem; wer die Meldung woertlich nimmt, sucht nach einem
# Zugangsschluessel, den es nicht braucht.
#
# Eine Fehlermeldung ist ein Befund ueber die ANTWORT und nicht ueber die
# URSACHE.
import urllib.error as _ue                                      # noqa: E402
from core.modell import _grund                                  # noqa: E402

_faelle = [
    (401, "Repositorium", "401 muss die haeufigste Ursache nennen"),
    (403, "Repositorium", "403 ist derselbe Fall wie 401"),
    (404, "Manifest", "404 muss auf Zweig oder Dateinamen zeigen"),
    (503, "Gegenstelle", "5xx muss sagen, dass es nicht am Anwender liegt"),
]
for _code, _wort, _warum in _faelle:
    _satz = _grund(_ue.HTTPError("u", _code, "x", None, None))
    check(_wort in _satz, f"{_warum}: {_satz!r}")
    check(str(_code) in _satz, f"HTTP {_code} steht nicht im Satz: {_satz!r}")
check("Verbindung" in _grund(_ue.URLError("kein DNS")),
      "ein Ausfall ohne HTTP-Antwort wird nicht als solcher benannt")

# Gegenprobe: die Wache darf nicht bei JEDEM Satz zufrieden sein.
check("Repositorium" not in _grund(_ue.HTTPError("u", 404, "x", None, None)),
      "404 bekommt denselben Satz wie 401 — dann sagt er nichts")
print("   OK   401/403, 404, 5xx und Ausfall bekommen eigene Saetze")

print("\n9c. Jeder geworfene Schluessel steht in allen vier Sprachen")
# ⚠️⚠️ `core/modell.py` spricht eine Sprache, das Onboarding vier. Ein
# fertiger deutscher Satz von hier waere dort ein Fremdkoerper. Deshalb
# traegt `Abgelehnt` einen SCHLUESSEL, und die Saetze stehen in
# `app/fenster.py` in `START_SAETZE` — dieselbe Bauart wie
# `core/hinweise.py` fuer den Server.
#
# ⚠️ Damit gibt es zwei Orte fuer eine Sache. Deshalb hier die Klammer:
# JEDER Schluessel, den dieses Modul wirft, muss in ALLEN VIER Sprachen
# einen Satz haben. Ein Schluessel ohne Satz zeigt dem Anwender nichts —
# die Seite fiele auf den deutschen Rohtext zurueck.
#
# ⚠️ Gelesen wird der QUELLTEXT und nicht eine Liste. Wer eine neue
# Absage einbaut, faellt hier auf, ohne dass jemand daran denkt.
import re as _re9c                                              # noqa: E402
sys.path.insert(0, str(WURZEL / "app"))
import fenster as _fen                                          # noqa: E402

_quelle = (WURZEL / "core" / "modell.py").read_text(encoding="utf-8")
_geworfen = set(_re9c.findall(r'"(m_f_[a-z_]+)"', _quelle))
check(_geworfen, "core/modell.py wirft keine Schluessel mehr — dann steht "
                 "die Uebersetzung wieder still")
for _spr, _saetze in _fen.START_SAETZE.items():
    _fehlt = sorted(_geworfen - set(_saetze))
    check(not _fehlt,
          f"{_spr}: fuer {_fehlt} gibt es keinen Satz — der Anwender saehe "
          f"den deutschen Rohtext")

# ⚠️ Und die Gegenrichtung: ein Satz ohne Werfer ist tote Last, die beim
# naechsten Umbau niemand mehr zuordnen kann.
_uebrig = sorted({k for k in _fen.START_SAETZE["de"] if k.startswith("m_f_")}
                 - _geworfen)
check(not _uebrig,
      f"fuer {_uebrig} gibt es einen Satz, aber niemand wirft sie")

# ⚠️ `_grund()` und `_grund_schluessel()` muessen DIESELBEN Faelle
# unterscheiden. Zwei Einteilungen, die auseinanderlaufen, waeren ein
# Terminal, das etwas anderes sagt als das Fenster.
import urllib.error as _ue9c                                    # noqa: E402
from core.modell import _grund, _grund_schluessel                # noqa: E402
for _code, _erwartet in ((401, "m_f_nicht_berechtigt"),
                         (403, "m_f_nicht_berechtigt"),
                         (404, "m_f_nicht_gefunden"),
                         (503, "m_f_gegenstelle")):
    _f = _ue9c.HTTPError("u", _code, "x", None, None)
    _s, _w = _grund_schluessel(_f)
    check(_s == _erwartet, f"HTTP {_code} -> {_s}, erwartet {_erwartet}")
    check(str(_code) in _grund(_f),
          f"der deutsche Satz zu HTTP {_code} nennt die Zahl nicht")
print(f"   OK   {len(_geworfen)} Schluessel, vier Sprachen, keine tote Last")

print("\n10. Die Windows-Wege laufen — auf dieser Maschine nachgeprueft")
# ⚠️⚠️ WINDOWS-ZWEIGE, AUF LINUX GEPRUEFT. Zwei Stellen liessen das
# Fenster unter Windows gar nicht erst starten, eine dritte waere
# schlimmer, weil sie NICHT abstuerzt:
#
#   core/einmalig.py   `os.getuid()` ist «Availability: Unix», und
#                      `socket.AF_UNIX` gibt es dort nicht -> AttributeError
#                      beim Start, bevor irgendetwas anderes passiert.
#   core/pfade.py      `~/.config` LAESST sich unter Windows anlegen. Das
#                      Werkzeug schriebe also klaglos an einen Ort, an dem
#                      kein Windows-Programm etwas sucht und den keine
#                      Sicherung erfasst. Ein Fehler, der laut ist, kostet
#                      eine Stunde; einer, der leise ist, kostet die Datei.
#
# Beide Module nehmen `windows` als Schalter bzw. lesen die
# Umgebungsvariablen, also laesst sich der fremde Zweig hier durchlaufen.
# Ein Zweig, der nur auf einer Maschine laeuft, die im Testlauf niemand
# hat, waere ein ungeprueft ausgeliefertes Stueck.
import threading                                                # noqa: E402
from core import einmalig                                       # noqa: E402

for _modus, _name in ((False, "POSIX"), (True, "Windows")):
    _tmp = Path(tempfile.mkdtemp(prefix="maschera-einmal-"))
    _pfad = _tmp / ("maschera.port" if _modus else "maschera.sock")
    check(einmalig.laeuft_schon(_pfad, windows=_modus) is False,
          f"{_name}: es laeuft schon, bevor etwas horcht")
    _gesehen = threading.Event()
    _faden = einmalig.horche(_gesehen.set, _pfad, windows=_modus)
    check(_faden is not None, f"{_name}: der Horcher kam nicht auf")
    check(einmalig.laeuft_schon(_pfad, windows=_modus) is True,
          f"{_name}: der laufende Horcher wird nicht erkannt — dann gehen "
          f"zwei Fenster auf")
    check(_gesehen.wait(3.0),
          f"{_name}: das Zeichen kam nicht an — das erste Fenster kaeme "
          f"nicht nach vorne")
    if _modus:
        check(_pfad.read_text(encoding="utf-8").strip().isdigit(),
              "der Windows-Weg schreibt keine Portnummer hin")

# ⚠️ Und die Leiche. Eine Portdatei mit einer Nummer, auf der niemand mehr
# horcht, ist genauso irrefuehrend wie ein ueberlebender Unix-Sockel: sie
# sagt «laeuft», wo nichts laeuft. Gefragt wird durch VERBINDEN.
_leiche = Path(tempfile.mkdtemp()) / "maschera.port"
_leiche.write_text("1", encoding="utf-8")
check(einmalig.laeuft_schon(_leiche, windows=True) is False,
      "eine Portdatei ohne Horcher gilt als laufende Anwendung")
check(not _leiche.exists(), "die Leiche wurde nicht weggeraeumt — "
      "`horche()` koennte danach nicht binden")
print("   OK   beide Wege horchen, erkennen und raeumen die Leiche weg")

print("\n11. Die Orte stimmen auf beiden Plattformen")
from core import pfade as _pf                                   # noqa: E402
import importlib                                                # noqa: E402

_alt = {k: os.environ.get(k) for k in
        ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "APPDATA", "LOCALAPPDATA")}
try:
    for _k in _alt:
        os.environ.pop(_k, None)
    os.environ["APPDATA"] = r"C:\Users\probe\AppData\Roaming"
    os.environ["LOCALAPPDATA"] = r"C:\Users\probe\AppData\Local"
    _pf.WINDOWS = True
    check("Roaming" in str(_pf.konfig("regeln.yaml")),
          f"Windows: die Einstellungen landen nicht in APPDATA: "
          f"{_pf.konfig('regeln.yaml')}")
    check(".config" not in str(_pf.konfig("regeln.yaml")),
          "Windows: die Einstellungen landen in ~/.config — dort sucht "
          "kein Windows-Programm, und keine Sicherung erfasst es")
    # ⚠️ Und das Modell NICHT ins wandernde Profil. 1,2 GB, die bei jeder
    # Anmeldung durchs Netz gehen, waeren ein stiller Dauerschaden.
    check("Local" in str(_pf.modell("ch-v63b"))
          and "Roaming" not in str(_pf.modell("ch-v63b")),
          f"Windows: das Modell landet im wandernden Profil: "
          f"{_pf.modell('ch-v63b')}")
    # Eine gesetzte XDG-Variable gewinnt trotzdem — die Wachen lenken
    # damit die Einstellungen des Anwenders beiseite.
    os.environ["XDG_CONFIG_HOME"] = "/tmp/gelenkt"
    check(str(_pf.konfig("x")).startswith("/tmp/gelenkt"),
          "XDG_CONFIG_HOME wird unter Windows ignoriert — dann greift "
          "keine Wache mehr an den Einstellungen vorbei")
finally:
    _pf.WINDOWS = os.name == "nt"
    for _k, _v in _alt.items():
        os.environ.pop(_k, None)
        if _v is not None:
            os.environ[_k] = _v
print("   OK   APPDATA fuer Einstellungen, LOCALAPPDATA fuer das Modell")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Das Nachladen ist in Ordnung.")
