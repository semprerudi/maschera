#!/usr/bin/env python3
"""MASCHERA.app und .dmg bauen — das Gegenstueck zu `windows_bauen.py`.

    python3 tools/paket/macos_bauen.py

Auf einem Mac, im Projektstamm, in einer Umgebung mit
`requirements-paket.txt`, `pywebview` und `pyinstaller`; das Modell liegt
unter `runs/ch-v63b` (oder wird vorher geholt, siehe `.github/workflows/`).

Ergebnis: `dist/MASCHERA-<fassung>-<arch>.dmg`, `<arch>` ist `arm64` oder
`x86_64` — das sind zwei Pakete (`MACOS.md` Abschnitt 2).

⚠️ **Dieser Bau ist neu und auf einem Mac noch nicht gemessen.** Er teilt
alles Teilbare mit `windows_bauen.py` — dieselben Listen (`DATEN`,
`WERKZEUGE`, `draussen.txt`), dieselbe Zusammenstellung, dieselbe
Importliste, dieselbe Pickle-Sperre im Modellordner —, damit die zwei
Verpackungen nicht auseinanderlaufen. Was nur hier steht: PyInstaller als
`.app` statt als Ordner und `hdiutil` statt Inno Setup. Die drei Punkte in
`MACOS.md` Abschnitt 6 («Zu messen») sind damit nicht beantwortet.

Unsigniert: `MACOS.md` Abschnitt 7 beschreibt, was Gatekeeper dazu sagt.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Die gemeinsamen Teile kommen aus dem Windows-Bau — nicht abgeschrieben,
# denn eine zweite Liste bliebe beim naechsten Aendern zurueck.
_spec = importlib.util.spec_from_file_location(
    "_windows_bauen", Path(__file__).with_name("windows_bauen.py"))
wb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wb)

WURZEL = wb.WURZEL
BAU = WURZEL / "dist" / "macos-bau"
MODELL = wb.MODELL


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("Dieses Skript baut unter macOS.")
    zahl = wb.fassung()
    arch = platform.machine()
    print(f"MASCHERA {zahl} ({arch})")
    # Anders als unter Windows gibt es hier keine CUDA-Rader: PyPI liefert
    # fuer macOS nur die CPU-Fassung, ohne den Zusatz `+cpu`. Die Fassung
    # wird gemeldet, nicht verlangt.
    import torch
    print(f"   torch {torch.__version__}")
    if not (WURZEL / "runs" / MODELL / "model.safetensors").is_file():
        raise SystemExit(f"Das Modell fehlt unter runs/{MODELL}.")

    if BAU.exists():
        shutil.rmtree(BAU)
    BAU.mkdir(parents=True)
    liste = wb.importe()
    (BAU / "_importe.py").write_text(
        "".join(f"import {n}\n" for n in liste), encoding="utf-8")
    print(f"   {len(liste)} Importe fuer die Analyse")
    shutil.copy2(Path(__file__).with_name("windows_start.py"),
                 BAU / "windows_start.py")

    zwischen = BAU / "maschera"
    wb.zusammenstellen(zwischen)
    modell = BAU / "modell" / MODELL
    wb.modell_zusammenstellen(modell)

    trenner = os.pathsep
    argumente = [
        str(BAU / "windows_start.py"), "--noconfirm", "--windowed",
        "--name", "MASCHERA",
        "--osx-bundle-identifier", "ch.maschera.Maschera",
        "--paths", str(BAU),
        "--distpath", str(BAU / "dist"),
        "--workpath", str(BAU / "arbeit"),
        "--specpath", str(BAU),
    ]
    for teil in (*wb.DATEN, "tools"):
        argumente += ["--add-data",
                      f"{zwischen / teil}{trenner}maschera/{teil}"]
    argumente += ["--add-data",
                  f"{modell}{trenner}maschera/runs/{MODELL}"]
    import PyInstaller.__main__
    PyInstaller.__main__.run(argumente)

    app = BAU / "dist" / "MASCHERA.app"
    if not app.is_dir():
        raise SystemExit("MASCHERA.app ist nicht entstanden")
    ziel = WURZEL / "dist"
    ziel.mkdir(exist_ok=True)
    dmg = ziel / f"MASCHERA-{zahl}-{arch}.dmg"
    dmg.unlink(missing_ok=True)
    # `hdiutil` ist Teil von macOS — kein zusaetzliches Werkzeug noetig.
    subprocess.run(["hdiutil", "create", "-volname", "MASCHERA",
                    "-srcfolder", str(app), "-ov", "-format", "UDZO",
                    str(dmg)], check=True)
    print(f"FERTIG: {dmg}  ({dmg.stat().st_size / 1e9:.2f} GB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
