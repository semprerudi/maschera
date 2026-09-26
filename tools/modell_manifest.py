#!/usr/bin/env python3
"""Das Modell-Manifest erzeugen — woher, wie gross, welche Pruefsumme.

    python3 tools/modell_manifest.py --pack ch --aus runs/ch-v63b \
        --repo semprerudi/maschera-ch-v63b

⚠️ **WARUM ES DIESES WERKZEUG GIBT.** Die Pruefsummen im Manifest sind das
Einzige, was zwischen «das Modell ist da» und «irgendetwas ist da» steht.
Sie von Hand einzutragen hiesse, sie einmal abzuschreiben und danach nie
wieder — und beim naechsten Modell stuenden die alten drin, waehrend das
neue geladen wird. Die Wache dagegen ist die Erzeugung selbst.

⚠️ **ES SCHREIBT NICHT, WAS ES NICHT GEMESSEN HAT.** Das Manifest entsteht
aus einem Verzeichnis, das dawar — nicht aus einer Angabe. Wer die Zahlen
zu einem Modell braucht, das er nicht hat, hat keine Zahlen.

⚠️ **UND ES SAGT NICHT, DASS ES STIMMT.** Gemessen wird das Verzeichnis
auf DIESER Maschine. Ob dieselben Bytes unter der angegebenen Adresse
liegen, weiss es nicht — das zeigt erst der erste Lauf von
`core.modell.hole()` gegen die echte Quelle. Der Hinweis am Ende sagt das,
damit niemand ein ungeprueftes Manifest fuer eine Zusage haelt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from core.modell import PFLICHT, _pruefsumme                    # noqa: E402

# Die Adresse, unter der Hugging Face eine Datei eines Repositoriums
# ausliefert. `{datei}` fuellt `core.modell.hole()` ein.
VORLAGE = "https://huggingface.co/{repo}/resolve/main/{{datei}}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Modell-Manifest erzeugen.")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--aus", required=True,
                    help="Verzeichnis mit dem fertigen Modell")
    ap.add_argument("--repo", required=True,
                    help="z. B. benutzer/maschera-ch-v63b")
    ap.add_argument("--trocken", action="store_true",
                    help="nur anzeigen, nichts schreiben")
    args = ap.parse_args()

    quelle = Path(args.aus).resolve()
    if not quelle.is_dir():
        raise SystemExit(f"{quelle} ist kein Verzeichnis.")

    fehlend = [d for d in PFLICHT if not (quelle / d).is_file()]
    if fehlend:
        raise SystemExit(
            f"In {quelle} fehlen: {', '.join(fehlend)}\n"
            f"  Ein Manifest ueber ein unvollstaendiges Modell waere eine "
            f"Zusage ueber etwas, das es nicht gibt.")

    dateien = {}
    print(f"── {quelle.name}")
    for name in PFLICHT:
        pfad = quelle / name
        summe = _pruefsumme(pfad)
        gross = pfad.stat().st_size
        dateien[name] = {"bytes": gross, "sha256": summe}
        print(f"   {name:24} {gross / 1e6:9.1f} MB  {summe[:16]}…")

    manifest = {
        "name": quelle.name,
        "quelle": VORLAGE.format(repo=args.repo),
        "bytes": sum(d["bytes"] for d in dateien.values()),
        "dateien": dateien,
    }

    ziel = WURZEL / "packs" / args.pack / "modell.json"
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.trocken:
        print(f"\n(trocken — {ziel} bleibt, wie es ist)")
        return 0
    ziel.write_text(text, encoding="utf-8")
    print(f"\n{ziel}")
    print(f"   {manifest['bytes'] / 1e9:.2f} GB, {len(dateien)} Datei(en)")
    print()
    print("⚠️ GEMESSEN WURDE DAS VERZEICHNIS AUF DIESER MASCHINE.")
    print("   Ob unter der angegebenen Adresse dieselben Bytes liegen, sagt")
    print("   dieses Manifest NICHT. Das zeigt erst der erste echte Lauf.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
