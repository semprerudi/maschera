#!/usr/bin/env python3
"""Metadaten aus einer Buerodatei entfernen.

    python3 tools/office_saeubern.py beispiele/musterbrief.docx

⚠️ **Warum das ein eigenes Werkzeug ist.** Eine `.docx` ist ein ZIP. Der
sichtbare Text steht in `word/document.xml` — daneben legt Word aber
`docProps/core.xml` und `docProps/app.xml` an, und darin stehen der Verfasser,
der zuletzt Speichernde, die Firma und der Bearbeitungsverlauf. Diese Angaben
sind im Dokument nicht zu sehen und ueberleben jedes «Speichern unter».

Fuer ein Werkzeug, dessen Zweck Datenschutz ist, waere ein Beispieldokument
mit dem Benutzernamen des Entwicklers darin die peinlichste Art von Leck —
und eine, die niemandem auffaellt, weil man sie nicht liest.

**Was entfernt wird:** `docProps/` vollstaendig, `word/comments.xml` samt
Verfassernamen, `word/people.xml`. Was bleibt: Text, Aufbau, Formatierung.

**Was das NICHT ist:** eine Anonymisierung des Inhalts. Steht ein echter Name
im Brief, steht er nachher immer noch drin. Dafuer ist der Filter da.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

# `docProps/` traegt Verfasser, Firma und Bearbeitungsverlauf.
# `people.xml` und `comments.xml` tragen die Namen der Kommentierenden.
# `meta.xml` ist das Gegenstueck bei OpenDocument.
WEG = ("docProps/", "word/comments.xml", "word/commentsExtended.xml",
       "word/commentsIds.xml", "word/people.xml", "meta.xml",
       "customXml/")

# Ohne diesen Verweis oeffnet Word die Datei zwar, meldet aber eine
# beschaedigte Struktur. Der Eintrag zeigt auf `docProps/`, das wir entfernen.
BEZUG = "_rels/.rels"


def saeubere(pfad: Path, ziel: Path | None = None) -> tuple[list[str], int]:
    ziel = ziel or pfad
    entfernt: list[str] = []
    behalten: list[tuple[str, bytes]] = []

    with zipfile.ZipFile(pfad) as z:
        for eintrag in z.infolist():
            name = eintrag.filename
            if any(name.startswith(w) or name == w for w in WEG):
                entfernt.append(name)
                continue
            roh = z.read(name)
            if name == BEZUG:
                roh = _rels_ohne_docprops(roh)
            behalten.append((name, roh))

    # Ueber eine Nebendatei schreiben, damit ein Abbruch mitten im Schreiben
    # nicht das Original zerstoert.
    neben = ziel.with_suffix(ziel.suffix + ".neu")
    with zipfile.ZipFile(neben, "w", zipfile.ZIP_DEFLATED) as z:
        for name, roh in behalten:
            z.writestr(name, roh)
    shutil.move(str(neben), str(ziel))
    return entfernt, len(behalten)


def _rels_ohne_docprops(roh: bytes) -> bytes:
    """Verweise auf `docProps/` aus `_rels/.rels` streichen."""
    import re
    text = roh.decode("utf-8", errors="replace")
    text = re.sub(r"<Relationship\b[^>]*Target=\"docProps/[^\"]*\"[^>]*/>",
                  "", text)
    return text.encode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Metadaten aus .docx/.xlsx/.pptx/.odt entfernen.")
    ap.add_argument("pfad", help="Datei, wird an Ort und Stelle geaendert")
    ap.add_argument("--nach", default=None,
                    help="stattdessen hierhin schreiben, Original bleibt")
    ap.add_argument("--zeigen", action="store_true",
                    help="nur anzeigen, was drinsteht, nichts aendern")
    args = ap.parse_args()

    pfad = Path(args.pfad)
    if not pfad.is_file():
        raise SystemExit(f"Nicht gefunden: {pfad}")

    if args.zeigen:
        with zipfile.ZipFile(pfad) as z:
            namen = z.namelist()
            gefunden = False
            for teil in ("docProps/core.xml", "docProps/app.xml", "meta.xml"):
                if teil in namen:
                    gefunden = True
                    print(f"--- {teil} ---")
                    print(z.read(teil).decode("utf-8", errors="replace"))
            for teil in ("word/comments.xml", "word/people.xml"):
                if teil in namen:
                    gefunden = True
                    print(f"--- {teil} vorhanden ---")
        if not gefunden:
            print("Keine Metadatenteile gefunden — die Datei ist bereits sauber.")
        return 0

    entfernt, geblieben = saeubere(pfad, Path(args.nach) if args.nach else None)
    ziel = args.nach or str(pfad)
    if entfernt:
        print(f"Entfernt aus {ziel}:")
        for n in entfernt:
            print(f"  {n}")
    else:
        print(f"{ziel}: nichts zu entfernen, war bereits sauber.")
    print(f"{geblieben} Teile behalten.")
    print()
    print("⚠️ Das saeubert die DATEI, nicht den INHALT. Steht ein echter Name")
    print("   im Brief, steht er nachher immer noch drin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
