"""Ist `dist/` aelter als der Bauplan, der es erzeugt hat?

    python3 tests/test_dist_frisch.py

**Eine Korrektur am Generator wirkt erst, wenn das Erzeugte neu gebaut
wird.** Aendert sich `packs/ch/nomenclatures/build.py` und bleibt
`dist/` stehen, laeuft jede Messung gegen die alte Nomenklatur weiter —
ohne dass irgendetwas rot wird. Ein Filter raeumt nicht nach, und ein
Generator baut nicht rueckwirkend.

Ein Beispiel dafuer steht in Punkt 3: Behoerdennamen tragen keinen
Ortsnamen, weil das Muster ohne Ort erkennt und jeder Wert mit Ort sonst
nur teilweise erfasst wuerde:

    Gold   'Betreibungsamt Bern'    <- Nomenklaturwert, eine Spanne
    Regex  'Betreibungsamt'         <- Muster ohne Ortsnamen

Diese Wache kostet einen Dateizugriff.
"""
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

BAUPLAN = WURZEL / "packs" / "ch" / "nomenclatures" / "build.py"
DIST = WURZEL / "packs" / "ch" / "nomenclatures" / "dist"

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


print("1. Ist der Bauplan da?")
check(BAUPLAN.is_file(), f"fehlt: {BAUPLAN}")
if not BAUPLAN.is_file():
    raise SystemExit(1)
print(f"   OK   {BAUPLAN.name}")

print("\n2. Passt der Fingerabdruck zu den Dateien in dist/?")
# NICHT der Zeitstempel. Eine Wache, die bei jeder Aenderung an
# `build.py` anschlaegt — auch an einem Kommentar —, wird weggeklickt, und
# dann nuetzt auch der Teil nichts mehr, der stimmt. Deshalb vergleicht sie
# die ERZEUGTEN WERTE mit dem, was `build.py` beim letzten Lauf abgelegt
# hat.
import hashlib  # noqa: E402
import json  # noqa: E402

FINGER = DIST / "_fingerabdruck.json"
# Ausnahme an der KONVENTION, nicht am Dateinamen: Unterstrich am Anfang
# heisst «keine Nomenklatur». Dieser Test importiert `build.py` bewusst
# nicht — er behandelt den Bauplan als Datei, nicht als Modul —, deshalb
# steht die Regel hier ein zweites Mal. Die Quelle ist
# `build.nomenklaturdateien()`.
gebaut = sorted(p for p in DIST.glob("*.json")
                if not p.name.startswith("_")) \
    if DIST.is_dir() else []

if not gebaut:
    # Kein Fehler: Wer den Pack frisch klont, hat `dist/` noch nicht. Ein
    # Test, der dann rot ist, wird als "geht halt nicht" abgetan.
    print("   —    dist/ ist leer. Bauen mit:")
    print("        python3 packs/ch/nomenclatures/build.py --build")
elif not FINGER.is_file():
    print("   —    kein Fingerabdruck. Einmal neu bauen:")
    print("        python3 packs/ch/nomenclatures/build.py --build")
else:
    erwartet = json.loads(FINGER.read_text(encoding="utf-8"))["werte"]
    abweichend = []
    for pfad in gebaut:
        name = pfad.stem
        ist = hashlib.sha256(pfad.read_bytes()).hexdigest()[:16]
        if name in erwartet and erwartet[name] != ist:
            abweichend.append(name)
    check(not abweichend,
          "dist/ wurde nach dem Bauen veraendert: "
          f"{', '.join(abweichend)}\n"
          "        python3 packs/ch/nomenclatures/build.py --build")
    if not abweichend:
        print(f"   OK   {len(gebaut)} Datei(en) unveraendert seit dem Bauen")

print("\n3. Behoerdennamen ohne Ortsnamen")
# Nicht die Zeitstempel, sondern der INHALT. Ein Zeitstempel laesst sich
# durch `touch` heilen, ohne dass sich etwas geaendert haette.
beh = DIST / "behoerden.json"
if not beh.is_file():
    print("   —    behoerden.json noch nicht gebaut")
else:
    text = beh.read_text(encoding="utf-8")
    # Orte aus der geloeschten `_BEH_ORTE`-Liste, die es dort nie geben darf.
    spuren = [o for o in ("Vals", "Biel/Bienne", "Köniz", "Aarau")
              if o in text]
    check(not spuren,
          f"Ortsnamen in den Behoerdenwerten: {', '.join(spuren)}\n"
          "        Der Ortsname gehoert in einen eigenen {CITY}-Slot.\n"
          "        Sonst erfasst das Muster nur den Teil ohne Ort, und jeder\n"
          "        Wert wird zum Teiltreffer.")
    if not spuren:
        print(f"   OK   {beh.stat().st_size // 1024} kB, keine Ortsnamen")

print("\n4. Vertragen die Werkzeuge, die dist/ durchgehen, den Inhalt?")
# Werkzeuge, die `dist/*.json` lesen, muessen `_fingerabdruck.json`
# auslassen — es traegt `gebaut`/`werte` statt `entries`. Nimmt eines die
# Dateien pauschal, bricht es mit `KeyError: 'entries'` ab, und weil diese
# Werkzeuge von Hand aufgerufen werden, saehe es keine andere Pruefung.
if not gebaut:
    print("   —    dist/ ist leer")
else:
    unterstrich = [x.name for x in DIST.glob("*.json")
                   if x.name.startswith("_")]
    ohne_entries = []
    for x in gebaut:
        o = json.loads(x.read_text(encoding="utf-8"))
        if "entries" not in o or "meta" not in o:
            ohne_entries.append(x.name)
    check(not ohne_entries,
          f"Nomenklatur ohne meta/entries: {', '.join(ohne_entries)}\n"
          "        Traegt eine Datei den Vertrag nicht, gehoert sie nicht\n"
          "        nach dist/ oder braucht einen Unterstrich.")
    if not ohne_entries:
        # ⚠️ Das Wort «uebersprungen» ist hier frei: der Laeufer erkennt ein
        # Selbstauslassen nur an der Marke `UEBERSPRUNGEN` am Zeilenanfang.
        print(f"   OK   {len(gebaut)} Nomenklatur(en) mit meta/entries, "
              f"{len(unterstrich)} mit Unterstrich ausgenommen")

    # Der Befehl selbst, nicht nur seine Voraussetzung. Er liest nur und
    # braucht kein Netz.
    import subprocess  # noqa: E402
    r = subprocess.run(
        [sys.executable, str(BAUPLAN), "--verify"],
        capture_output=True, text=True)
    check(r.returncode == 0,
          "build.py --verify scheitert:\n        "
          + (r.stderr.strip().splitlines() or ["(keine Meldung)"])[-1])
    if r.returncode == 0:
        print("   OK   build.py --verify laeuft durch")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
