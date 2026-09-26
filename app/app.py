#!/usr/bin/env python3
"""Die Oberflaeche von MASCHERA.

    python3 app/app.py --ohne-modell
    python3 app/app.py --model runs/ch-v63b

**Kein zweiter Server.** `app.py` baut dieselbe Anwendung wie `serve.py`
und haengt die Auslieferung der Oberflaeche daran. Ein Codepfad, eine
Sperre, ein Laeufer — ein eigener Server mit eigener Kette waere eine
zweite Wahrheit darueber, was maskiert wird.

`serve.py` bleibt fuer sich lauffaehig: Serverbetrieb ohne Oberflaeche, und
`tests/test_api.py` prueft den nackten Kern.

## Was hier NICHT hineinkommt

**Nichts wird von aussen nachgeladen.** Kein Framework von einem CDN,
keine Schriften von Google. Ein Werkzeug, das damit wirbt, dass der Text
das Geraet nicht verlaesst, darf beim Oeffnen keine Verbindung nach aussen
aufbauen — schon der Abruf verraet einer fremden Stelle, dass und wann
jemand MASCHERA benutzt. `tests/test_app.py` prueft das an jeder
ausgelieferten Datei.

**Keine Erkennung im Browser.** Browserseitige Regexe als Rueckfall waeren
genau der Fall, vor dem `docs/API_OBERFLAECHE.md` bei `ohne_modell`
warnt: eine Maskierung mit gruener Anzeige, die keine ist.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "app"))
sys.path.insert(0, str(WURZEL / "tools"))

from flask import Flask, jsonify, send_from_directory  # noqa: E402

from core import einstellungen  # noqa: E402
from serve import VERSION, Zustand, baue  # noqa: E402

OBERFLAECHE = Path(__file__).resolve().parent / "static"


def baue_mit_oberflaeche(z: Zustand, statisch: Path | None = None) -> Flask:
    """Den Kern aus `serve.py`, dazu die Auslieferung der Oberflaeche."""
    app = baue(z)
    ordner = Path(statisch or OBERFLAECHE)

    @app.get("/")
    def wurzel():
        """Die Oberflaeche — mit dem gewaehlten Thema schon im `<html>`.

        Nicht einfach `send_from_directory`: die Farbwahl steht auf der Platte,
        und das Skript erfaehrt sie erst, wenn `GET /api/einstellungen` zurueck
        ist. Bis dahin stuende die Seite in der Systemfarbe, und wer «dunkel»
        gewaehlt hat, saehe den Startbildschirm hell aufblitzen.

        Kein zweiter Speicherort dafuer: `localStorage` waere eine Kopie der
        Einstellung, die niemand nachfuehrt. Die Datei bleibt die einzige
        Quelle; sie wird hier nur frueher gelesen.

        Ist das Thema «automatisch», wird nichts gesetzt — nur ohne Attribut
        greift `prefers-color-scheme` im Blatt.
        """
        roh = (ordner / "index.html").read_text(encoding="utf-8")
        try:
            thema = einstellungen.lade().get("thema", "automatisch")
        except Exception:
            thema = "automatisch"
        if thema in ("hell", "dunkel"):
            roh = roh.replace("<html lang=", f'<html data-thema="{thema}" lang=', 1)
        return app.response_class(roh, mimetype="text/html")

    @app.get("/<path:datei>")
    def statische_datei(datei: str):
        # `/api/…` gehoert NICHT hierher, auch nicht als 404. Diese Route nimmt
        # jeden Pfad an und ist auf GET beschraenkt; `POST /api/senden` passte damit
        # auf die Regel, aber nicht auf die Methode, und Flask antwortete mit 405
        # statt 404. 405 hiesse «es gibt ihn, nur nicht so» — den Endpunkt gibt es
        # aber nicht.
        if datei == "api" or datei.startswith("api/"):
            return jsonify({"fehler": f"Kein Endpunkt: /{datei}"}), 404
        # `send_from_directory` weist Pfade ausserhalb des Ordners ab —
        # `../../etc/passwd` kommt hier nicht durch. Selbst zusammensetzen
        # waere die haeufigste Art, genau das kaputtzumachen.
        return send_from_directory(ordner, datei)

    # Damit auch POST, PUT und DELETE auf unbekannte `/api/`-Pfade 404 geben
    # und nicht 405. Ohne diese Regel haengt die Antwort davon ab, ob die
    # Oberflaeche mitlaeuft — derselbe Aufruf, zwei Ergebnisse.
    @app.route("/api/<path:rest>",
               methods=["POST", "PUT", "DELETE", "PATCH"])
    def unbekannter_endpunkt(rest: str):
        return jsonify({"fehler": f"Kein Endpunkt: /api/{rest}"}), 404

    return app


def main() -> int:
    # So frueh wie moeglich: wer den Prozess sucht, sucht ihn meist, weil
    # etwas haengt — dann ist er womoeglich noch gar nicht fertig gestartet.
    from core import prozess
    prozess.benenne()

    ap = argparse.ArgumentParser(
        description="MASCHERA — Kern und Oberflaeche.")
    ap.add_argument("--model", default=None, help="Trainingsordner")
    ap.add_argument("--onnx", default=None,
                    help="Release-Ordner mit model.onnx")
    ap.add_argument("--ohne-modell", action="store_true",
                    help="nur Stufe 1 und 2 — Namen bleiben im Klartext")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--regeln", default=None,
                    help="eigene Regeln, Vorgabe ~/.config/maschera/regeln.yaml")
    ap.add_argument("--host", default="127.0.0.1")
    # Aus `core.einstellungen`, nicht als Zahl hier.
    ap.add_argument("--port", type=int, default=einstellungen.VORGABE_PORT)
    args = ap.parse_args()

    if not (args.model or args.onnx or args.ohne_modell):
        ap.error("Entweder --model, --onnx oder --ohne-modell angeben.")
    if not (OBERFLAECHE / "index.html").is_file():
        ap.error(f"Keine Oberflaeche unter {OBERFLAECHE}")

    z = Zustand(args.pack, args.model, args.onnx, args.max_length, args.regeln)
    app = baue_mit_oberflaeche(z)

    print(f"MASCHERA {VERSION} · Pack {args.pack} · "
          f"Labelvertrag {z.pack.get_label_hash()[:8]}")
    if z.ohne_modell:
        print("  ⚠ OHNE MODELL — Namen, Daten und Adressen bleiben im "
              "Klartext.")
    else:
        print(f"  Modell {z.modellname}")
    if args.host != "127.0.0.1":
        print(f"  ⚠ Erreichbar auf {args.host} — nicht nur lokal. Ein "
              f"Werkzeug, das Personendaten\n"
              f"    verarbeitet, gehoert hinter eine Anmeldung.")
        # Und der NAME gehoert dazu. Die Wirtspruefung laesst nur die Namen der
        # eigenen Maschine durch; wer unter einem anderen Namen ankommt, bekommt
        # 403. Das muss beim Start dastehen und nicht erst im Zugriffsprotokoll.
        if not (os.environ.get("MASCHERA_WIRT") or "").strip():
            print("    ⚠ MASCHERA_WIRT ist nicht gesetzt — unter einem "
                  "anderen Namen als\n"
                  "      127.0.0.1 antwortet der Dienst mit 403.")
    print(f"  http://{args.host}:{args.port}/")

    app.run(host=args.host, port=args.port, threaded=True, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
