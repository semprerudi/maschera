#!/usr/bin/env python3
"""Alle Pruefungen nacheinander.  python3 tools/run_tests.py"""
import shutil
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = [
    ("Labelvertrag",  "tools/check_taxonomy.py"),
    ("Pruefsummen",   "tests/test_ch_checksums.py"),
    ("Maskierung",    "tests/test_masking.py"),
    ("Muster",        "tests/test_patterns.py"),
    ("Befunde 1 + 6", "tests/test_befunde.py"),
    ("Injektor",      "tests/test_injector.py"),
    ("Ausrichtung",   "tests/test_alignment.py"),
    ("Auswertung",    "tests/test_evaluate.py"),
    ("Inferenz",      "tests/test_inference.py"),
    ("Regressionen",  "tests/test_regressionen.py"),
    ("Eigene Regeln", "tests/test_user_rules.py"),
    ("Modell holen",  "tests/test_modell.py"),
    ("Goldpfad",      "tests/test_goldpfad.py"),
    ("Gold-Markierung", "tests/test_gold_markup.py"),
    ("Klartext-Vorlieben", "tests/test_vorlieben.py"),
    ("dist frisch",     "tests/test_dist_frisch.py"),
    ("Rauschen+Zone",   "tests/test_rauschen.py"),
    ("Vertrag gefroren", "tests/test_labelvertrag_eingefroren.py"),
    ("Veroeffentlichung", "tests/test_veroeffentlichung.py"),
    ("Vertrauen",       "tests/test_vertrauen.py"),
    ("DOCX",            "tests/test_dokumente_docx.py"),
    ("Mail",            "tests/test_mail.py"),
    ("Scan-PDF",        "tests/test_scan_pdf.py"),
    ("API-Endpunkte",   "tests/test_api.py"),
    ("Oberflaeche",     "tests/test_app.py"),
    ("Schriften",       "tests/test_schriften.py"),
    ("Gold-Ersetzung",  "tests/test_gold_ersetzen.py"),
    ("Streuung",        "tests/test_streuung.py"),
    ("Langes Dokument", "tests/test_langes_dokument.py"),
    ("Fenster",         "tests/test_fenster.py"),
    ("Projektseite",    "tests/test_webseite.py"),
    ("Oberflaechenlogik", "tests/test_oberflaeche.js"),
]

# Die Werkzeuge der eigenen Arbeitsumgebung (Server, Abgleich) werden
# nicht veroeffentlicht und ihre Pruefung auch nicht. Wo `tools/intern.txt`
# liegt, gehoert sie dazu — fehlt sie dort, schlaegt das an.
if (ROOT / "tools" / "intern.txt").is_file():
    SUITE.append(("Intern", "tests/test_intern.py"))

# Eine Pruefung, die sich selbst ueberspringt, gibt 0 zurueck und stuende
# sonst als `OK` in der Liste — «alle bestanden», waehrend eine fehlte.
# Erkannt wird es an der AUSGABE, nicht am Rueckgabewert, und zwar an einer
# eigenen Zeile: sie faengt mit `UEBERSPRUNGEN` an. Nach dem blossen Wort
# zu suchen traefe auch Pruefungen, die ueber das Ueberspringen SPRECHEN.
MARKER = "UEBERSPRUNGEN"


def uebersprungen(ausgabe: str) -> bool:
    """Hat sich die Pruefung selbst ausgelassen? Nur die Marke zaehlt."""
    return any(z.lstrip().startswith(MARKER) for z in ausgabe.splitlines())

# ⚠️ Spaltenbreite aus den Namen berechnen, nicht raten. Mit fest
# eingetragenen 14 Zeichen brach die Pfadspalte bei jedem laengeren Namen
# aus — «Klartext-Vorlieben», «Oberflaechenlogik», «Veroeffentlichung» —,
# und eine Liste, die man nicht senkrecht lesen kann, liest niemand.
BREITE = max(len(n) for n, _ in SUITE)
# «UEBER» statt «UEBERSPRUNGEN»: das lange Wort haette die Markenspalte auf
# 13 Zeichen aufgeblasen und alles nach rechts geschoben. Was uebersprungen
# wurde, steht ohnehin nochmals ausgeschrieben unter der Liste.
MARKE = 5

fails = []
sprung = []
for name, path in SUITE:
    # ⚠️ `.js` braucht node. Fehlt es, wird die Pruefung UEBERSPRUNGEN
    # gemeldet und nicht stillschweigend als OK gezaehlt.
    if path.endswith(".js"):
        if shutil.which("node") is None:
            print(f"  {'UEBER':<{MARKE}} {name:<{BREITE}} {path}")
            sprung.append((name, "node nicht installiert"))
            continue
        befehl = ["node", path]
    else:
        befehl = [sys.executable, path]
    r = subprocess.run(befehl, cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0
    weg = ok and uebersprungen(r.stdout)
    marke = "UEBER" if weg else ("OK" if ok else "FEHL")
    print(f"  {marke:<{MARKE}} {name:<{BREITE}} {path}")
    if weg:
        sprung.append((name, r.stdout.strip().splitlines()[0]))
    elif not ok:
        fails.append((name, r.stdout[-1500:] + r.stderr[-800:]))

print()
if sprung:
    for name, grund in sprung:
        print(f"  {name}: {grund}")
    print()
if fails:
    for name, out in fails:
        print(f"--- {name} ---\n{out}\n")
    print(f"{len(fails)} von {len(SUITE)} fehlgeschlagen.")
    raise SystemExit(1)
if sprung:
    print(f"{len(SUITE) - len(sprung)} von {len(SUITE)} Pruefungen bestanden, "
          f"{len(sprung)} uebersprungen.")
    print("Eine uebersprungene Pruefung hat NICHTS geprueft.")
    raise SystemExit(0)
print(f"Alle {len(SUITE)} Pruefungen bestanden.")
