#!/usr/bin/env python3
"""Den Windows-Installer bauen — das Gegenstueck zu `appimage_bauen.fish`.

    .venv\\Scripts\\python.exe tools\\paket\\windows_bauen.py

Auf einer Windows-Maschine, im Projektstamm, in einer Umgebung mit
`requirements-paket.txt`, `pywebview` und `pyinstaller` (siehe
`tools/paket/WINDOWS.md`). Das Modell liegt unter `runs/ch-v63b`.

Ergebnis: `dist/MASCHERA-<fassung>-x64-setup.exe`.

Drei Schritte:

1. **Die Fassung** kommt aus `app/serve.py` — die einzige Quelle. Sie geht
   in den Namen des Installers und an Inno Setup.
2. **PyInstaller** friert nur `windows_start.py` ein. Der Quellcode liegt
   unveraendert als Daten daneben. Damit PyInstaller trotzdem jede
   Bibliothek einpackt, sammelt dieses Skript alle Importe aus dem
   Quellcode und schreibt sie nach `_importe.py` — eine Liste, die mit dem
   Code mitwaechst, statt von Hand nachgefuehrt zu werden.
3. **Inno Setup** schnuert daraus einen Installer, der ohne
   Administratorrechte in den Benutzerordner installiert.

⚠️ torch muss die CPU-Fassung sein. Auf einer Maschine mit Grafikkarte
laeuft die CUDA-Fassung auch — und braechte ueber 2 GB mit, die niemand
braucht. Das Skript bricht ab, statt es zu glauben.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent
BAU = WURZEL / "dist" / "windows-bau"
MODELL = "ch-v63b"

# Was der Quellcode zur Laufzeit liest — als Daten, unveraendert.
DATEN = ("app", "core", "packs")
# DREI Dateien aus `tools/`, dieselbe Liste wie im `Dockerfile`.
WERKZEUGE = ("dokumente.py", "filter_document.py", "evaluate_model.py")
# Was nur zum Erzeugen und Messen da ist, steht in `draussen.txt` — der
# einen Quelle fuer alle Verpackungen.
DRAUSSEN = Path(__file__).with_name("draussen.txt")
# Was im Modellordner NICHT mitfaehrt: Zwischenstaende des Trainings und
# alles, was Pickle sein kann (`training_args.bin` ist eine). Die Dateien
# werden zur Laufzeit nicht gelesen (`core/modell.py`, `PFLICHT`), und eine
# Pickle-Datei in einem Paket kann beim Oeffnen Code ausfuehren. Dieselbe
# Liste steht in `.dockerignore` und `appimage_bauen.fish`;
# `tests/test_fenster.py` Punkt 25 haelt die drei zusammen.
MODELL_DRAUSSEN = ("checkpoint-*", "*.bin", "*.pt", "*.pth", "*.pkl",
                   "*.ckpt", "*.pickle")


def draussen() -> list[str]:
    zeilen = [z.strip() for z in DRAUSSEN.read_text(encoding="utf-8")
              .splitlines()]
    liste = [z for z in zeilen if z and not z.startswith("#")]
    if not liste:
        raise SystemExit(f"{DRAUSSEN.name} ist leer — Abbruch statt "
                         "eines Pakets mit allem")
    return liste

# Die eigenen Module. Sie werden nicht eingefroren, sondern als Quellcode
# mitgeliefert; in der Importliste haben sie deshalb nichts zu suchen.
EIGENE = {"app", "core", "packs", "tools", "serve", "fenster", "dokumente",
          "filter_document", "evaluate_model", "_importe"}


def fassung() -> str:
    text = (WURZEL / "app" / "serve.py").read_text(encoding="utf-8")
    m = re.search(r'^VERSION = "([^"]+)"', text, re.M)
    if not m:
        raise SystemExit("keine VERSION in app/serve.py")
    return m.group(1)


def torch_pruefen() -> None:
    import torch
    if "+cpu" not in torch.__version__:
        raise SystemExit(
            f"torch {torch.__version__} ist nicht die CPU-Fassung. Neu holen:\n"
            "  pip install torch --index-url "
            "https://download.pytorch.org/whl/cpu --force-reinstall")


def windows_pakete_pruefen() -> None:
    """`pystray` und `Pillow` bauen das Symbol im Infobereich. Fehlen sie,
    entstuende still ein Installer ohne — der Schalter stuende da und
    bewirkte nichts."""
    for name in ("pystray", "PIL"):
        if importlib.util.find_spec(name) is None:
            raise SystemExit(f"{name} fehlt: pip install pystray pillow")


def zusammenstellen(zwischen: Path) -> None:
    """Was der Anwender bekommt, in einen Zwischenstand — `--add-data`
    nimmt ein Verzeichnis ganz oder gar nicht. `tests/test_fenster.py`
    Punkt 12 ruft das auf Linux auf und sieht nach, was darin liegt."""
    kein_cache = shutil.ignore_patterns("__pycache__", "*.pyc")
    for teil in DATEN:
        shutil.copytree(WURZEL / teil, zwischen / teil, ignore=kein_cache)
    for muster in draussen():
        for treffer in zwischen.glob(muster):
            if treffer.is_dir():
                shutil.rmtree(treffer)
            else:
                treffer.unlink()
    (zwischen / "tools").mkdir()
    for name in WERKZEUGE:
        shutil.copy2(WURZEL / "tools" / name, zwischen / "tools" / name)


def modell_zusammenstellen(ziel: Path) -> None:
    """Den Modellordner ohne Trainingsartefakte nach `ziel` kopieren —
    `--add-data` nimmt ein Verzeichnis ganz oder gar nicht."""
    shutil.copytree(WURZEL / "runs" / MODELL, ziel,
                    ignore=shutil.ignore_patterns(*MODELL_DRAUSSEN))


def importe() -> list[str]:
    """Jeder Import aus dem Quellcode, der in dieser Umgebung aufloesbar ist."""
    dateien = [p for teil in ("app", "core", "packs")
               for p in (WURZEL / teil).rglob("*.py")]
    dateien += [WURZEL / "tools" / f"{n}.py"
                for n in ("dokumente", "filter_document", "evaluate_model")]
    namen: set[str] = set()
    for datei in dateien:
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for k in ast.walk(baum):
            if isinstance(k, ast.Import):
                namen.update(a.name for a in k.names)
            elif isinstance(k, ast.ImportFrom) and k.level == 0 and k.module:
                namen.add(k.module)
    gefunden = []
    for name in sorted(namen):
        if name.split(".")[0] in EIGENE:
            continue
        # Plattformfremdes (fcntl, gi, PyQt …) steht im Code hinter
        # Bedingungen und ist hier nicht installiert — dann nicht nennen.
        try:
            if importlib.util.find_spec(name) is None:
                continue
        except (ImportError, ValueError):
            continue
        gefunden.append(name)
    return gefunden


def iscc() -> Path:
    for ort in (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs"
                / "Inno Setup 6" / "ISCC.exe",
                Path(os.environ.get("ProgramFiles(x86)", ""))
                / "Inno Setup 6" / "ISCC.exe",
                Path(os.environ.get("ProgramFiles", ""))
                / "Inno Setup 6" / "ISCC.exe"):
        if ort.is_file():
            return ort
    raise SystemExit("Inno Setup (ISCC.exe) nicht gefunden")


def main() -> int:
    if os.name != "nt":
        raise SystemExit("Dieses Skript baut unter Windows.")
    zahl = fassung()
    print(f"MASCHERA {zahl}")
    torch_pruefen()
    windows_pakete_pruefen()
    if not (WURZEL / "runs" / MODELL / "model.safetensors").is_file():
        raise SystemExit(f"Das Modell fehlt unter runs/{MODELL}.")

    if BAU.exists():
        shutil.rmtree(BAU)
    BAU.mkdir(parents=True)
    liste = importe()
    (BAU / "_importe.py").write_text(
        "".join(f"import {n}\n" for n in liste), encoding="utf-8")
    print(f"   {len(liste)} Importe fuer die Analyse")
    shutil.copy2(Path(__file__).with_name("windows_start.py"),
                 BAU / "windows_start.py")

    zwischen = BAU / "maschera"
    zusammenstellen(zwischen)

    trenner = os.pathsep
    argumente = [
        str(BAU / "windows_start.py"), "--noconfirm", "--windowed",
        "--name", "MASCHERA",
        "--icon", str(WURZEL / "app" / "static" / "favicon.ico"),
        "--paths", str(BAU),
        "--distpath", str(BAU / "dist"),
        "--workpath", str(BAU / "arbeit"),
        "--specpath", str(BAU),
    ]
    for teil in (*DATEN, "tools"):
        argumente += ["--add-data",
                      f"{zwischen / teil}{trenner}maschera/{teil}"]
    modell = BAU / "modell" / MODELL
    modell_zusammenstellen(modell)
    argumente += ["--add-data",
                  f"{modell}{trenner}maschera/runs/{MODELL}"]
    import PyInstaller.__main__
    PyInstaller.__main__.run(argumente)

    ziel = WURZEL / "dist"
    subprocess.run([str(iscc()), f"/DFassung={zahl}",
                    f"/DQuelle={BAU / 'dist' / 'MASCHERA'}",
                    f"/O{ziel}", str(Path(__file__).with_name("maschera.iss"))],
                   check=True)
    installer = ziel / f"MASCHERA-{zahl}-x64-setup.exe"
    if not installer.is_file():
        raise SystemExit(f"{installer.name} ist nicht entstanden")
    print(f"FERTIG: {installer}  "
          f"({installer.stat().st_size / 1e9:.2f} GB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
