#!/usr/bin/env python3
"""Das oeffentliche Paket bauen — was ins oeffentliche Repository geht und
was nicht.

    python3 tools/oeffentlich_paket.py --nach /tmp/maschera-public
    python3 tools/oeffentlich_paket.py --nach /tmp/x --pruefen

⚠️ **Warum ein Werkzeug und nicht `.gitignore`.** Ein `.gitignore`-Eintrag
greift nur bei UNVERFOLGTEN Dateien. Wer eine Datei einmal committet hat,
bevor der Eintrag entstand, hat sie fuer immer drin, und der Eintrag
suggeriert das Gegenteil. Der Ausschluss gehoert deshalb in ein Werkzeug,
das man laufen lassen und pruefen kann, nicht in eine Datei, die man
liest und glaubt.

⚠️ **Es schreibt in ein NEUES Verzeichnis.** Nichts wird an Ort und Stelle
geaendert, nichts geloescht. Was nicht ins Paket kommt, bleibt im
Arbeitsverzeichnis liegen — das Werkzeug nimmt nur mit, was mit darf.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Was NICHT mitkommt, und warum. Jede Zeile braucht einen Grund — ein
# Ausschluss ohne Begruendung ist beim naechsten Mal nicht von einem
# Versehen zu unterscheiden.
# ---------------------------------------------------------------------------
DRAUSSEN: dict[str, str] = {
    "HANDOVER.md": "Arbeitsjournal der Entwicklung",
    "GIT.md": "Abgleich zwischen den Entwicklungsmaschinen",
    "CLAUDE.md":
        "Arbeitsregeln fuer das Entwicklungswerkzeug — nennt die "
        "Verzeichnisse, in denen bei der Entwicklung Personendaten liegen",
    "UEBERGABE.md": "Uebergabe zwischen Arbeitssitzungen",
    "SITZUNG.md": "Uebergabe zwischen Arbeitssitzungen des Werkzeugs",
    "VERBOTEN_INTERN.txt":
        "die persoenliche Schicht der Veroeffentlichungswache — traegt "
        "genau die Namen, die sie schuetzt",
    "BETRIEB.md": "Maschinen und Betrieb der Entwicklungsumgebung",
    "tools/sync.fish":
        "Abgleich mit dem eigenen Server der Entwicklungsumgebung",
    "tools/start.fish": "Arbeitsablauf der Entwicklungsumgebung",
    "tools/feierabend.fish": "dito",
    "tools/desktop": "Ablagesymbole der Entwicklungsumgebung",
    "tools/schreibtisch.fish":
        "richtet die Ablagesymbole ein und ruft start.fish, "
        "feierabend.fish und appimage_holen.fish — alle zurueckgehalten",
    "tools/github_ordner.fish":
        "legt den GitHub-Ordner auf dem Abgleichserver ab — nennt ihn",
    "tools/appimage_holen.fish":
        "holt die AppImage ueber sync.fish vom Abgleichserver",
    "tools/schirmbilder.fish":
        "nimmt die Bilder der Projektseite auf und legt das ZIP im "
        "Ablageordner der Entwicklungsumgebung ab",
    "tools/im-terminal.fish":
        "der Starter der Ablagesymbole — ohne sie ohne Zweck",
    "tools/nachbessern_v55.py": "einmaliges Nachbesserungsskript",
    "tests/test_intern.py":
        "prueft die zurueckgehaltenen Werkzeuge der Arbeitsumgebung",
    "tools/intern.txt":
        "Liste der Arbeitsnotizen fuer die Abgleichwerkzeuge; ohne sie "
        "laeuft die Wache in der allgemeinen Schicht",
    "docs/WEBSEITE.md":
        "Gestaltungsvorgabe fuer die Projektseite, kein Teil des Werkzeugs",
    "tools/paket/auf_server.fish":
        "Aufbau auf dem Server der Entwicklungsumgebung — setzt Traefik, "
        "Authelia und den Abgleichserver voraus",
    "tools/paket/compose.traefik.yaml":
        "Anbindung an den Reverse Proxy der Entwicklungsumgebung",
    "tools/paket/config_sichern.fish":
        "sichert das Konfigurationsvolumen auf diesem Server",
    "tools/paket/PKGBUILD": "Arch-Paket, vorerst nicht veroeffentlicht",
    "tools/paket/arch_probe.fish": "Probelauf fuer das Arch-Paket",
    ".claude/settings.local.json":
        "Berechtigungen des Entwicklungswerkzeugs. Unverfolgt; der "
        "Eintrag faengt `git add -f`",
}

# Verzeichnisse, deren Inhalt nie mitkommt — Daten, keine Bausteine.
#
# ⚠️ Eigene Testsets liegen unter dem Goldpfad ausserhalb des Baums. Die
# Eintraege fuer `eval/real` und `eval/markup` bleiben trotzdem: sie kosten
# nichts und fangen einen Baum, in dem jemand Dokumente abgelegt hat. Eine
# Wache zu entfernen, weil sie gerade nichts faengt, ist der teure Fehler.
DATEN = (
    "packs/ch/eval/real",
    "packs/ch/eval/markup",
    "packs/ch/nomenclatures/raw",
    "runs",
    "dist",
    "release",
)

# Endungen, die nie mitkommen.
ENDUNGEN = {".pyc", ".jsonl", ".onnx", ".safetensors", ".bin", ".pt"}

# Die zwei Dateien, die aus einem DATEN-Verzeichnis trotzdem mitkommen: sie
# erklaeren den leeren Ordner und halten ihn in git.
#
# ⚠️ EIN NAME, ZWEI LESER. `tests/test_veroeffentlichung.py` importiert
# diese Zeile, weil seine Sperre und dieser Ausschluss dieselbe Frage
# beantworten muessen: WAS GEHT HINAUS. Stuenden die Namen getrennt da,
# koennte das Werkzeug eine Datei ins Paket nehmen, die die Wache nie
# angesehen hat.
ERKLAERER = ("README.md", ".gitkeep")


def verfolgte(wurzel: Path) -> list[str]:
    """Was Git kennt. Was Git nicht kennt, gehoert auch nicht ins Paket."""
    r = subprocess.run(["git", "-C", str(wurzel), "ls-files"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git ls-files fehlgeschlagen: {r.stderr.strip()}")
    return [z for z in r.stdout.split("\n") if z]


def draussen(pfad: str) -> str | None:
    """Grund, warum die Datei nicht mitkommt — oder None."""
    if pfad in DRAUSSEN:
        return DRAUSSEN[pfad]
    for ordner, grund in DRAUSSEN.items():
        if pfad.startswith(ordner + "/"):
            return grund
    for ordner in DATEN:
        if pfad == ordner or pfad.startswith(ordner + "/"):
            # README.md und .gitkeep erklaeren den leeren Ordner — die
            # duerfen mit, der Inhalt nicht.
            if Path(pfad).name in ERKLAERER:
                return None
            return f"Daten unter {ordner}/, nicht Bauplan"
    if Path(pfad).suffix in ENDUNGEN:
        return f"Endung {Path(pfad).suffix}"
    return None


def baue(ziel: Path) -> tuple[list[str], dict[str, str]]:
    dateien = verfolgte(WURZEL)
    mit, ohne = [], {}
    for f in dateien:
        grund = draussen(f)
        if grund:
            ohne[f] = grund
            continue
        quelle = WURZEL / f
        if not quelle.is_file():
            continue
        zielort = ziel / f
        zielort.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quelle, zielort)
        mit.append(f)
    return mit, ohne


def pruefe(ziel: Path) -> list[str]:
    """Das FERTIGE Paket pruefen, nicht die Absicht.

    ⚠️ Der Unterschied ist der ganze Punkt. `test_veroeffentlichung.py`
    prueft heute das Arbeitsverzeichnis; wenn es die Ausschluesse anders
    versteht als dieses Werkzeug, faellt das nicht auf. Hier wird geprueft,
    was tatsaechlich im Paket liegt.
    """
    fehler = []
    for name in DRAUSSEN:
        if (ziel / name).exists():
            fehler.append(f"{name} ist im Paket, obwohl ausgeschlossen")

    # ⚠️ Die zweite, UNABHAENGIGE Liste. `DRAUSSEN` oben gegen sich selbst zu
    # pruefen ist zirkulaer: wer einen Eintrag entfernt, dem sind Bauen und
    # Pruefen einig, und die Datei landet im Paket.
    #
    # `NUR_INTERN` steht in `tests/test_veroeffentlichung.py` und ist dort
    # aus einem anderen Grund gefuehrt: es sind die Dateien, die im
    # ARBEITSVERZEICHNIS Rechner- und Benutzernamen tragen duerfen. Zwei
    # Listen in zwei Dateien mit zwei Begruendungen — wer eine aendert,
    # faellt der anderen auf.
    try:
        raum: dict = {}
        quelle = (WURZEL / "tests" / "test_veroeffentlichung.py").read_text(
            encoding="utf-8")
        anfang = quelle.index("NUR_INTERN = {")
        ende = quelle.index("}", anfang) + 1
        exec(quelle[anfang:ende], raum)          # noqa: S102
        for name in raum.get("NUR_INTERN", {}):
            if (ziel / name).exists():
                fehler.append(
                    f"{name} ist im Paket — es traegt Rechner- oder "
                    f"Benutzernamen und steht in NUR_INTERN")
    except (OSError, ValueError, SyntaxError) as e:
        fehler.append(f"NUR_INTERN aus der Wache nicht lesbar: {e}")
    for ordner in DATEN:
        p = ziel / ordner
        if not p.is_dir():
            continue
        drin = [k.name for k in p.rglob("*")
                if k.is_file() and k.name not in ERKLAERER]
        if drin:
            fehler.append(f"{ordner}/ enthaelt {len(drin)} Datei(en): "
                          f"{', '.join(drin[:4])}")
    # ⚠️ Die Wache AUS DEM PAKET starten, nicht aus dem Arbeitsverzeichnis.
    # `test_veroeffentlichung.py` bestimmt seine Wurzel ueber `__file__` —
    # ein Aufruf der Fassung im Arbeitsverzeichnis prueft das
    # Arbeitsverzeichnis, egal welches `cwd` gesetzt ist.
    wache = ziel / "tests" / "test_veroeffentlichung.py"
    if not wache.is_file():
        fehler.append("test_veroeffentlichung.py fehlt im Paket — die "
                      "Wache kann dort nicht laufen")
    else:
        # ⚠️ `-B`: die Wache legt `core/pfade.py` auf den Suchpfad und
        # importiert `ARTEN` — Python schriebe dabei `core/__pycache__/*.pyc` INS
        # PAKET, NACH dem Kopieren, wo kein Ausschluss es mehr faengt.
        #
        # `PYTHONDONTWRITEBYTECODE` zusaetzlich, weil `-B` nur diesen Prozess
        # bindet — ein Unterprozess der Wache erbt die Fahne nicht, die
        # Umgebungsvariable schon.
        umgebung = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        r = subprocess.run([sys.executable, "-B", str(wache)],
                           capture_output=True, text=True, env=umgebung)
        if r.returncode != 0:
            fehler.append("test_veroeffentlichung.py schlaegt im Paket an:\n"
                          + r.stdout[-1200:])

    # ⚠️ Und danach nachsehen, statt es zu glauben. Eine Fahne, die wirkt,
    # und eine Wache, die es prueft, sind zwei verschiedene Dinge — hier
    # faellt jede kuenftige Quelle von Bytecode auf, nicht nur diese eine.
    uebrig = sorted(p.relative_to(ziel).as_posix()
                    for p in ziel.rglob("*")
                    if p.is_file() and p.suffix in ENDUNGEN)
    if uebrig:
        fehler.append(f"{len(uebrig)} Datei(en) mit ausgeschlossener Endung "
                      f"im Paket: {', '.join(uebrig[:6])}")
    return fehler


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Das oeffentliche Paket bauen.")
    ap.add_argument("--nach", required=True,
                    help="Zielverzeichnis, muss leer sein oder neu")
    ap.add_argument("--pruefen", action="store_true",
                    help="danach das fertige Paket pruefen")
    ap.add_argument("--ueberschreiben", action="store_true")
    args = ap.parse_args()

    ziel = Path(args.nach).resolve()
    if ziel.exists():
        if not args.ueberschreiben:
            raise SystemExit(f"{ziel} gibt es schon. --ueberschreiben "
                             f"oder anderes Ziel waehlen.")
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)

    mit, ohne = baue(ziel)
    print(f"{len(mit)} Datei(en) ins Paket, {len(ohne)} zurueckgehalten.\n")
    print("ZURUECKGEHALTEN")
    gruende: dict[str, list[str]] = {}
    for f, grund in sorted(ohne.items()):
        gruende.setdefault(grund, []).append(f)
    for grund, liste in sorted(gruende.items()):
        print(f"  {grund}")
        for f in liste[:6]:
            print(f"      {f}")
        if len(liste) > 6:
            print(f"      … und {len(liste) - 6} weitere")
    print(f"\nPaket: {ziel}")

    if args.pruefen:
        print("\nPRUEFUNG")
        fehler = pruefe(ziel)
        for f in fehler:
            print(f"  FEHL {f}")
        if fehler:
            print(f"\n{len(fehler)} Punkt(e) — das Paket ist NICHT bereit.")
            return 1
        print("  OK   nichts Zurueckgehaltenes im Paket")
        print("\nBereit fuer das oeffentliche Repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
