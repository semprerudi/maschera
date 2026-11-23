#!/usr/bin/env python3
"""Jede Programmdatei eines .app-Buendels: richtige Architektur, Minimum eingehalten.

    python3 tools/paket/macho_pruefen.py dist/macos-bau/dist/MASCHERA.app \\
        --arch x86_64 --minimum 13.0

Liest den Mach-O-Kopf selbst (64 Bit und fette Dateien), ohne `otool`, damit
es auf jedem Rechner laeuft. Das Minimum steht in `LC_BUILD_VERSION` (minos)
oder bei aelteren Dateien in `LC_VERSION_MIN_MACOSX`.

Warum es das braucht (Messung 23.11.2026 am DMG 2.3.3): 23 von 108 Dateien
verlangten macOS 14, die Info.plist nannte kein Minimum, das README sagte
«M1 oder neuer». Ein Mac mit macOS 11 bis 13 haette die App wortlos nicht
gestartet. Das Minimum haengt an den Raedern, nicht an einer Einstellung;
deshalb wird es nach dem Bau gemessen und nicht vorher angenommen.

Rueckgabe 0, wenn alles passt, sonst 1 mit den Dateien, die abweichen.
"""
from __future__ import annotations

import argparse
import collections
import plistlib
import struct
import sys
from pathlib import Path

CPU = {0x01000007: "x86_64", 0x0100000C: "arm64"}
LC_BUILD_VERSION = 0x32
LC_VERSION_MIN_MACOSX = 0x24
MH_MAGIC_64 = 0xFEEDFACF
FAT_MAGIC = 0xCAFEBABE


def _fassung(v: int) -> tuple[int, int]:
    return (v >> 16, (v >> 8) & 0xFF)


def _teil(roh: bytes, ab: int) -> tuple[str, tuple[int, int] | None] | None:
    """Architektur und Minimum eines 64-Bit-Mach-O ab `ab`, sonst None."""
    if len(roh) < ab + 32 or struct.unpack_from("<I", roh, ab)[0] != MH_MAGIC_64:
        return None
    _, cpu, _, _, ncmds, groesse, _, _ = struct.unpack_from("<IiIIIIII", roh, ab)
    p, ende, minos = ab + 32, ab + 32 + groesse, None
    for _ in range(ncmds):
        if p + 8 > ende:
            break
        cmd, cs = struct.unpack_from("<II", roh, p)
        if cmd == LC_BUILD_VERSION:
            minos = _fassung(struct.unpack_from("<I", roh, p + 12)[0])
        elif cmd == LC_VERSION_MIN_MACOSX:
            minos = _fassung(struct.unpack_from("<I", roh, p + 8)[0])
        p += max(cs, 8)
    return CPU.get(cpu & 0xFFFFFFFF, hex(cpu & 0xFFFFFFFF)), minos


def teile(pfad: Path) -> list[tuple[str, tuple[int, int] | None]]:
    """Alle Mach-O-Teile einer Datei; leer, wenn es keine Programmdatei ist."""
    with open(pfad, "rb") as f:
        kopf = f.read(8)
        if len(kopf) < 4:
            return []
        if struct.unpack(">I", kopf[:4])[0] == FAT_MAGIC:
            anzahl = struct.unpack(">I", kopf[4:8])[0]
            f.seek(0)
            roh = f.read()
            ergebnis = []
            for i in range(anzahl):
                _, _, ab, _, _ = struct.unpack_from(">iIIII", roh, 8 + 20 * i)
                t = _teil(roh, ab)
                if t:
                    ergebnis.append(t)
            return ergebnis
        if struct.unpack("<I", kopf[:4])[0] != MH_MAGIC_64:
            return []
        f.seek(0)
        t = _teil(f.read(), 0)
        return [t] if t else []


def pruefe(app: Path, arch: str, minimum: str) -> list[str]:
    """Die Abweichungen als Saetze; leer heisst: passt."""
    soll = tuple(int(x) for x in minimum.split("."))[:2]
    fehler, zaehlung = [], collections.Counter()
    for pfad in sorted(app.rglob("*")):
        if pfad.is_symlink() or not pfad.is_file():
            continue
        for a, minos in teile(pfad):
            zaehlung[a] += 1
            name = pfad.relative_to(app)
            if a != arch:
                fehler.append(f"{name}: Architektur {a}, erwartet {arch}")
            if minos is None:
                fehler.append(f"{name}: kein Minimum eingetragen")
            elif minos > soll:
                fehler.append(f"{name}: verlangt macOS {minos[0]}.{minos[1]}, "
                              f"Ziel {minimum}")
    if not zaehlung:
        fehler.append("keine Programmdatei gefunden")
    plist = app / "Contents" / "Info.plist"
    if plist.is_file():
        eingetragen = plistlib.loads(plist.read_bytes()).get("LSMinimumSystemVersion")
        if eingetragen != minimum:
            fehler.append(f"Info.plist: LSMinimumSystemVersion {eingetragen!r}, "
                          f"erwartet {minimum!r}")
    else:
        fehler.append("Info.plist fehlt")
    print(f"   {sum(zaehlung.values())} Mach-O-Teile: {dict(zaehlung)}")
    return fehler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("app", type=Path)
    ap.add_argument("--arch", required=True, choices=sorted(set(CPU.values())))
    ap.add_argument("--minimum", required=True)
    a = ap.parse_args()
    fehler = pruefe(a.app, a.arch, a.minimum)
    for f in fehler[:40]:
        print(f"   FEHLER {f}")
    if len(fehler) > 40:
        print(f"   … und {len(fehler) - 40} weitere")
    if fehler:
        return 1
    print(f"   OK   alles {a.arch}, nichts verlangt mehr als macOS {a.minimum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
