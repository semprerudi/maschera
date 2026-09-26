#!/usr/bin/env python3
"""Aus einem pip-Aufloesungsbericht das Flatpak-Modul mit den Raedern bauen.

    flatpak --filesystem=/tmp --user --devel --share=network \\
        --command=pip3 run org.kde.Sdk//6.11 \\
        install --dry-run --ignore-installed --report /tmp/pip-report.json \\
        -r requirements-flatpak.txt
    python3 tools/paket/flatpak_deps.py /tmp/pip-report.json

Warum nicht `flatpak-pip-generator`: der uebliche Weg holt Adresse und
Pruefsumme ueber `https://pypi.org/pypi/<name>/<version>/json` — und
`torch/2.14.0+cpu` gibt es dort nicht (404 fuer die CPU-Fassung, 200 fuer
`torch/2.14.0`). Ein Rad von `download.pytorch.org` ist fuer ihn
unsichtbar.

MASCHERA braucht aber genau dieses Rad: die CUDA-Fassung waere ueber 2 GB
schwerer, und im Sandkasten ist keine Grafikkarte.

pip selbst kennt beide Indexe. `--report` schreibt fuer jedes aufgeloeste
Paket Adresse UND Pruefsumme — aus dem Lauf, der den `--extra-index-url`
beachtet hat. Dieses Werkzeug uebersetzt das nur.

ES WIRD GEMESSEN, NICHT GETIPPT. Kein Name, keine Fassung und keine Summe
steht in dieser Datei.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
ZIEL = HIER / "flatpak-python-deps.json"


def _von_pypi(name: str, fassung: str) -> tuple[str, str] | None:
    """Adresse und Summe desselben Pakets bei PyPI — oder None.

    Der PyTorch-Index fuehrt Kopien fremder Pakete (etwa `Jinja2`,
    `MarkupSafe`) und liefert dort KEINE Pruefsumme mit. Ein Flatpak baut
    ohne Netz und braucht fuer jedes Rad eine Summe.
    """
    netz = f"https://pypi.org/pypi/{name}/{fassung}/json"
    try:
        with urllib.request.urlopen(netz, timeout=30) as a:
            daten = json.loads(a.read().decode("utf-8"))
    except Exception:
        return None
    # Ein Rad ohne Einschraenkung auf die Fassung von Python, sonst der
    # Quelltext. `py3-none-any` zuerst — das trifft die reinen
    # Python-Pakete, um die es hier geht.
    for bevorzugt in ("py3-none-any.whl", ".whl", ".tar.gz"):
        for d in daten.get("urls", []):
            if d["filename"].endswith(bevorzugt) and d["digests"].get("sha256"):
                return d["url"], d["digests"]["sha256"]
    return None


def _selbst_hashen(netz: str) -> str:
    """Notnagel: das Rad holen und die Summe aus den Bytes nehmen."""
    h = hashlib.sha256()
    with urllib.request.urlopen(netz, timeout=300) as a:
        for stueck in iter(lambda: a.read(1 << 20), b""):
            h.update(stueck)
    return h.hexdigest()


def main(bericht: Path) -> int:
    daten = json.loads(bericht.read_text(encoding="utf-8"))
    quellen: list[dict] = []
    nachgeholt: list[str] = []
    gehasht: list[str] = []

    for eintrag in daten["install"]:
        name = eintrag["metadata"]["name"]
        fassung = eintrag["metadata"]["version"]
        holen = eintrag["download_info"]
        netz = holen["url"]
        summe = holen.get("archive_info", {}).get("hashes", {}).get("sha256")

        if not summe:
            ersatz = _von_pypi(name, fassung)
            if ersatz:
                netz, summe = ersatz
                nachgeholt.append(f"{name} {fassung}")
            else:
                summe = _selbst_hashen(netz)
                gehasht.append(f"{name} {fassung}")

        # Der Name muss entziffert werden: Flatpak legt die Datei unter dem Namen
        # aus der ADRESSE ab, und dort steht das Plus als `%2B`. pip liest aus
        # `torch-2.14.0%2Bcpu-…whl` keine Fassung und meldet «No matching
        # distribution found for torch».
        datei = urllib.parse.unquote(netz.rsplit("/", 1)[-1])
        quelle = {"type": "file", "url": netz, "sha256": summe}
        if datei != netz.rsplit("/", 1)[-1]:
            quelle["dest-filename"] = datei
        quellen.append(quelle)

    # ⚠️ Sortiert nach Adresse, damit zwei Laeufe dieselbe Datei ergeben.
    # Sonst raschelt jeder Lauf durch `git diff`, und niemand sieht mehr,
    # WAS sich geaendert hat.
    quellen.sort(key=lambda q: q["url"])

    modul = {
        "name": "python-deps",
        "buildsystem": "simple",
        "build-commands": [
            # `--no-index` ist der Kern: gebaut wird aus den Dateien, die
            # Flatpak vorher geprueft hat, und aus keiner anderen Quelle.
            "pip3 install --no-index --find-links=. --prefix=${FLATPAK_DEST} "
            + " ".join(sorted(
                e["metadata"]["name"] for e in daten["install"])),
        ],
        "sources": quellen,
    }
    ZIEL.write_text(json.dumps(modul, indent=4) + "\n", encoding="utf-8")

    print(f"{ZIEL.name}: {len(quellen)} Raeder")
    if nachgeholt:
        print(f"  Summe bei PyPI nachgeholt: {', '.join(nachgeholt)}")
    if gehasht:
        print(f"  ⚠ selbst gehasht (PyPI kannte es nicht): "
              f"{', '.join(gehasht)}")

    # ⚠️ DIE PRUEFUNG, DIE DAS MANIFEST VERLANGT. Ohne sie waere die
    # CPU-Fassung eine Hoffnung: `2.14.0+cpu` sortiert heute hoeher als
    # `2.14.0`, und das ist die Reihenfolge der Fassungen, keine Zusage.
    cpu = [q for q in quellen if "%2Bcpu" in q["url"] or "+cpu" in q["url"]]
    if not cpu:
        print("\n⚠⚠ KEIN Rad mit +cpu. pip hat die CUDA-Fassung genommen;\n"
              "   das waeren ueber 2 GB fuer eine Grafikkarte, die im\n"
              "   Sandkasten nicht existiert. Siehe requirements-paket.txt.")
        return 1
    print(f"  +cpu bestaetigt an {len(cpu)} Rad/Raedern")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Aufruf: {Path(sys.argv[0]).name} <pip-report.json>")
    raise SystemExit(main(Path(sys.argv[1])))
