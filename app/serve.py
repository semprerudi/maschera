#!/usr/bin/env python3
"""Der Flask-Kern. Die bestehende Kette hinter den Endpunkten aus
`docs/API_OBERFLAECHE.md`.

    python3 app/serve.py --model runs/ch-v63b
    python3 app/serve.py --onnx release/ch-v63b --port 4141
    python3 app/serve.py --ohne-modell            # nur Stufe 1 und 2

Dies ist derselbe Kern, den das eigene Fenster (`app/fenster.py`) benutzt —
ohne Browser, ohne Fenster. `app/app.py` legt die Auslieferung der
Oberflaeche darum; die Endpunkte sind dieselben.

⚠️ GRUNDSAETZE, die im Code stehen und nicht in einer Konfiguration:

  1. **Nur 127.0.0.1 — und nur unter dem eigenen Namen.** Wer
     `--host 0.0.0.0` setzt, macht ein Werkzeug, das Personendaten
     verarbeitet, im Netz auf. Das ist moeglich — der Serverbetrieb hinter
     einem Reverse Proxy mit Anmeldung braucht es —, aber es ist eine
     bewusste Handlung mit einer Warnung, kein Standardwert.

     Die Adresse allein genuegt nicht: ein fremder `Host:`-Kopf bekommt
     403. Sonst waere «nur lokal» eine Aussage ueber die Adresse und keine
     ueber den Namen, und DNS-Rebinding fuehrt am CORS-Schutz des Browsers
     vorbei. Siehe `erlaubte_wirte()` weiter unten.

  2. **Nichts wird geschrieben.** Kein Zugriffsprotokoll mit Text, keine
     Zwischendatei, kein Zwischenspeicher. Was hier durchlaeuft, existiert
     nur im Arbeitsspeicher. Genauer: nichts wird geschrieben ausser den
     EINSTELLUNGEN des Anwenders — `PUT /api/regeln`, `/api/vorlieben`,
     `/api/vorlagen`, `/api/einstellungen` —, alle nach
     `~/.config/maschera/`, alle nur auf ausdruecklichen Befehl. Kein
     Dokumentinhalt, kein Woerterbuch, kein Protokoll.

  3. **Ein Dokument zur Zeit.** Der Laeufer ist nicht wiedereintrittsfaehig
     — der `Mitschreiber` merkt sich die Vertrauenswerte des letzten Laufs.
     Zwei gleichzeitige Anfragen wuerden ihre Werte vermischen und
     Vertrauenswerte des einen Dokuments am anderen anzeigen. Deshalb eine
     Sperre um die ganze Kette. `/api/zustand` bleibt daneben erreichbar.

  4. **Ohne Modell ist kein Betriebszustand.** `--ohne-modell` laeuft, aber
     jede Antwort traegt den Hinweis, dass Namen, Daten und Adressen im
     Klartext bleiben. Ein Server, der still ohne Modell laeuft, ist eine
     Leckquelle mit gruener Anzeige.
"""

from __future__ import annotations

import bisect
import time

import argparse
import os
import sys
import tempfile
import threading
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

from flask import Flask, jsonify, request  # noqa: E402

from core import einstellungen, user_rules, vorlagen  # noqa: E402
from core import vorlieben  # noqa: E402
from core.hinweise import Abgelehnt, hinweis  # noqa: E402
from core.inference import filter_text  # noqa: E402
from core.masking import PLACEHOLDER_RE, restore  # noqa: E402
from packs import load_pack  # noqa: E402

from dokumente import ALLE, lies  # noqa: E402
from filter_document import Mitschreiber  # noqa: E402

# Die Versionsnummer der Anwendung, unabhaengig von der Modellfassung.
#
# Die einzige Quelle: sie steht in `/api/zustand`, in der Oberflaeche, im
# Namen der AppImage und in der Docker-Marke, und die Bauskripte lesen sie
# hier heraus. `tests/test_fenster.py` Punkt 7 prueft, dass es bei dieser
# einen Stelle bleibt. In einem Fehlerbericht sagt sie, welcher Stand
# gemeint ist.
VERSION = "1.0.2"

# Mehr nimmt der Server nicht an. Ein Dokument ist laut Messung 1500 bis 4500
# Zeichen; 10 MB fangen auch ein PDF mit Bildern ab, ohne dass ein
# versehentlich abgelegtes Archiv den Speicher fuellt.
MAX_UPLOAD = 10 * 1024 * 1024

# ---------------------------------------------------------------------------
# Unter welchem Namen dieser Dienst antwortet
# ---------------------------------------------------------------------------
#
# «Nur lokal» ist eine Aussage ueber die ADRESSE und keine ueber den
# NAMEN. Ein Angreifer laesst seinen eigenen Namen auf 127.0.0.1 zeigen
# (DNS-Rebinding); die vom Anwender besuchte Seite ruft dann
# `http://boese.example:4141/…` — fuer den Browser derselbe Ursprung, also
# ohne jede CORS-Schranke, und die Antwort ist lesbar. Zu holen gaebe es
# `GET /api/vorlagen` (Prompts, koennen Personendaten tragen) und
# `GET /api/regeln` (die Regeldatei im Rohtext).
#
# Die Schranke ist deshalb der NAME: ein Wirt, der nicht in dieser Liste
# steht, bekommt 403. Der Browser schickt den Namen mit, den er meint.
#
# Hinter einem Reverse Proxy setzt der Betreiber `MASCHERA_WIRT` auf den
# Namen, unter dem der Dienst erreichbar ist. `MASCHERA_WIRT=*` schaltet
# die Pruefung ab — ausdruecklich, mit einem Zeichen, das kein Wirtsname
# sein kann, nicht als Nebenwirkung einer leeren Variablen.
WIRTE_LOKAL = ("127.0.0.1", "localhost", "::1", "0.0.0.0")


def erlaubte_wirte() -> set[str] | None:
    """Die Namen, unter denen geantwortet wird. `None` heisst: jeder."""
    gesetzt = (os.environ.get("MASCHERA_WIRT") or "").strip()
    if gesetzt == "*":
        return None
    namen = set(WIRTE_LOKAL)
    namen.update(w.strip().lower() for w in gesetzt.split(",") if w.strip())
    return namen


def wirt_von(roh: str) -> str:
    """Den Wirtsnamen aus einem `Host:`-Kopf holen, ohne Port.

    IPv6 steht in Klammern — `[::1]:4141`. Ein blosses `rsplit(":", 1)`
    machte daraus `[::1`, und die Wache erkennte den Rechner selbst nicht
    mehr.
    """
    roh = (roh or "").strip().lower()
    if roh.startswith("["):
        return roh[1:roh.index("]")] if "]" in roh else roh
    return roh.rsplit(":", 1)[0] if ":" in roh else roh


class Zustand:
    """Alles, was der Server zwischen den Anfragen behaelt.

    Bewusst ein Objekt und keine Modulvariablen: der Test baut sich damit
    eine eigene Anwendung ohne Modell, ohne globalen Zustand zu beruehren.
    """

    def __init__(self, pack_name: str = "ch", model: str | None = None,
                 onnx: str | None = None, max_length: int = 512,
                 regeln_pfad: str | None = None):
        self.pack = load_pack(pack_name)
        self.pack_name = pack_name
        self.max_length = max_length
        self.regeln_pfad = regeln_pfad
        self.sperre = threading.Lock()
        self.modellname: str | None = None
        self.scorer = None

        # Eigene Sperre, nicht `self.sperre`. Der Lauf haelt jene die ganze Zeit;
        # wer den Stand abfragt, wuerde bis zum Ende warten — und genau waehrend
        # des Laufs will ihn jemand wissen.
        self._standsperre = threading.Lock()
        self._stand = {"aktiv": False, "schritt": 0, "von": 0, "phase": ""}

        if onnx:
            from core.inference import OnnxScorer
            roh = OnnxScorer(onnx, max_length)
            roh.check_contract(self.pack)
            self.scorer = Mitschreiber(roh)
            self.modellname = onnx
        elif model:
            from evaluate_model import TorchScorer
            roh = TorchScorer(model, max_length)
            roh.check_contract(self.pack)
            self.scorer = Mitschreiber(roh)
            self.modellname = model

    # -- Fortschritt --------------------------------------------------------
    #
    # Nach dem Tokenisieren steht die Zahl der Fenster FEST, bevor gerechnet
    # wird. Ein Text ist damit nicht «irgendwie lang», sondern «31 Fenster»,
    # und der Balken zeigt etwas Gemessenes.
    #
    # Geschrieben wird nichts: der Stand lebt im Arbeitsspeicher und traegt
    # drei Zahlen und ein Wort — kein Dokumentinhalt, kein Platzhalter, kein
    # Wert.

    def melde(self, schritt: int, von: int, phase: str) -> None:
        with self._standsperre:
            self._stand = {"aktiv": True, "schritt": schritt, "von": von,
                           "phase": phase}

    def stand_aus(self) -> None:
        with self._standsperre:
            self._stand = {"aktiv": False, "schritt": 0, "von": 0, "phase": ""}

    def stand(self) -> dict:
        with self._standsperre:
            return dict(self._stand)

    # -- abgeleitete Tabellen, je Anfrage frisch, weil Regeln sich aendern --

    def regeln(self, anwenden: bool = True) -> list:
        if not anwenden:
            return []
        return user_rules.lade(self.regeln_pfad, self.pack)

    @property
    def ohne_modell(self) -> bool:
        return self.scorer is None


# Hinweise, die als Fehlertext taugen, wenn der Text leer bleibt.
# Gefragt wird der Schluessel, nicht der Satz — ein umformulierter Satz
# kann die Auswahl nicht aendern.
LEERER_BEFUND = {"pdf_ohne_text", "docx_leer"}


def _hinweise_ohne_modell() -> list[dict]:
    return [hinweis("ohne_modell",
                    "OHNE MODELL — nur Prüfsummen und Muster. Namen, Daten "
                    "und Adressen bleiben im KLARTEXT.")]


# ---------------------------------------------------------------------------
# Die Kette einmal durchlaufen und in die Form der API bringen
# ---------------------------------------------------------------------------

def _durchlauf(z: Zustand, text: str, ohne: set[str], woerterbuch: bool,
               regelsatz: list, hinweise: list[dict]) -> dict:
    """Ein Dokument durch die Kette. Erwartet, dass `z.sperre` gehalten wird."""
    plaetze = {t.tag: t.placeholder for t in z.pack.get_tags()}
    plaetze.update({r.tag: r.platzhalter for r in regelsatz})
    actions = dict(z.pack.get_actions())
    actions.update({r.tag: "mask" for r in regelsatz})
    for tag in ohne:
        actions[tag] = "tag_only"
    budgets = {t.tag: t.budget for t in z.pack.get_tags()}
    bspd = {t.tag: t.bspd for t in z.pack.get_tags()}
    schwellen = z.pack.get_thresholds()

    if z.scorer is not None:
        z.scorer.werte.clear()

    # Der Melder haengt am ROHEN Laeufer (`inner`), nicht am `Mitschreiber`:
    # die Fensterschleife liegt eine Ebene tiefer, und der Mitschreiber reicht
    # `score()` nur weiter.
    roh = z.scorer
    while roh is not None and not hasattr(roh, "labels"):
        roh = getattr(roh, "inner", None)
    if roh is not None:
        # Nach dem letzten Fenster kommt noch Arbeit: Schwellen, Ueberlappungen,
        # Propagation, Ersetzen. Deshalb wechselt die Phase beim letzten Fenster
        # auf «maskieren» — sonst stuende der Balken auf 100 %, und es ginge
        # trotzdem weiter.
        roh.melde = lambda nr, von: z.melde(
            nr, von, "modell" if nr < von else "maskieren")
    t0 = time.monotonic()
    try:
        ergebnis = filter_text(
            text, z.pack, z.scorer,
            propagate=True,
            thresholds=schwellen,
            excluded=ohne,
            mapping_enabled=woerterbuch,
            rules=regelsatz,
        )
    finally:
        # In `finally`: bricht die Kette ab, bliebe die Anzeige sonst ewig
        # «laeuft» stehen.
        if roh is not None:
            roh.melde = None
        z.stand_aus()
    dauer_ms = int((time.monotonic() - t0) * 1000)
    # Die Aufloesung des Vertrauens steht bei `Mitschreiber.vertrauen_zu` in
    # `tools/filter_document.py`, dort, wo die Werte abgelegt werden — eine
    # Stelle fuer Oberflaeche und Kommandozeile. Nicht hierher kopieren.
    def vertrauen_zu(s) -> float | None:
        return z.scorer.vertrauen_zu(s) if z.scorer else None

    if len(text) > z.max_length * 3:
        hinweise.append(hinweis(
            "fenster",
            f"Länger als ein Fenster ({z.max_length} Token). "
            f"Wird überlappend verarbeitet.",
            token=z.max_length))
    if ergebnis.erweitert:
        hinweise.append(hinweis(
            "wortgrenzen",
            f"{ergebnis.erweitert} Modellspannen lagen mitten in einem Wort "
            f"und wurden auf Wortgrenzen gezogen.",
            anzahl=ergebnis.erweitert))

    # Der Platzhalter laesst sich NICHT ueber den Wert allein nachschlagen:
    # derselbe Nachname kann einmal FULLNAME und einmal GIVENNAME sein, und
    # im Rueckwaertsindex gewaenne der zuletzt eingetragene. Deshalb ueber
    # Wert UND Praefix — dieselbe Loesung wie in `filter_document.py`.
    # Einmal umgedreht statt je Spanne durchsucht; `setdefault` haelt den
    # ersten Treffer.
    rueckwaerts: dict[tuple[str, str], str] = {}
    for ph, v in ergebnis.dictionary.items():
        rueckwaerts.setdefault((ph[1:].rsplit("_", 1)[0], v), ph)

    def platzhalter(tag: str, wert: str) -> str | None:
        praefix = plaetze.get(tag)
        if not praefix or actions.get(tag) != "mask":
            return None
        return rueckwaerts.get((praefix, wert))

    # Die Umbrueche stehen einmal da, und `bisect` findet die Zeile. Von vorne
    # zu zaehlen hiesse je Spanne einmal durch den halben Text.
    # `tests/test_api.py` vergleicht beide Wege ueber tausend Stellen — sonst
    # zeigt ein Befund auf die falsche Zeile.
    _umbrueche = [i for i, ch in enumerate(text) if ch == "\n"]

    def zeile_von(pos: int) -> int:
        return bisect.bisect_left(_umbrueche, pos) + 1

    spans = []
    maskierte_zeichen = 0
    for s in ergebnis.spans:
        wert = s.value(text)
        if actions.get(s.tag) == "mask":
            maskierte_zeichen += s.end - s.start
        spans.append({
            "tag": s.tag,
            "start": s.start,
            "end": s.end,
            "platzhalter": platzhalter(s.tag, wert),
            "quelle": s.source,
            "vertrauen": vertrauen_zu(s),
            "bspd": bool(bspd.get(s.tag, False)),
            "budget": budgets.get(s.tag),
            "zeile": zeile_von(s.start),
        })

    verworfen = []
    for tag, wert, grund in ergebnis.dropped:
        verworfen.append({"tag": tag, "text": wert, "grund": grund})

    return {
        "maskiert": ergebnis.masked,
        "original": text,
        "spans": spans,
        "woerterbuch": ergebnis.dictionary,
        "verworfen": verworfen,
        "hinweise": hinweise,
        "kennzahlen": {
            "zeichen": len(text),
            "maskiert": maskierte_zeichen,
            "anteil": round(maskierte_zeichen / max(1, len(text)), 3),
            "fundstellen": len(spans),
            "woerterbucheintraege": len(ergebnis.dictionary),
            # Gemessen, nicht geschaetzt: die Dauer steht in der Antwort und damit
            # in einem Fehlerbericht.
            "dauer_ms": dauer_ms,
        },
    }


# ---------------------------------------------------------------------------

# Ein Dateiname aus dem Formular ist Eingabe wie jede andere. Was hier
# herauskommt, muss auf JEDEM Dateisystem anlegbar sein — mehr nicht.
#
# Es ist KEINE Bereinigung im Sinne von «unbedenklich machen». Der Ausbruch
# aus dem temporaeren Ordner ist schon durch `Path(...).name` erledigt;
# hier geht es allein darum, dass `open()` nicht wirft.
#
# 120 BYTES, nicht 120 Zeichen: die Grenze der Dateisysteme (255) zaehlt
# Bytes, und `Ähnliches.txt` traegt in UTF-8 mehr Bytes als Zeichen.
NAME_HOECHSTENS = 120


def _sicherer_name(name: str) -> str:
    """Einen anlegbaren Dateinamen daraus machen. Endung bleibt erhalten."""
    name = "".join(z for z in name if z.isprintable())
    if name in ("", ".", ".."):
        return "unbenannt"
    endung = Path(name).suffix
    if len(endung.encode("utf-8")) > NAME_HOECHSTENS:
        endung = ""
    stamm = name[:len(name) - len(endung)] if endung else name
    platz = NAME_HOECHSTENS - len(endung.encode("utf-8"))
    while len(stamm.encode("utf-8")) > platz:
        stamm = stamm[:-1]
    return (stamm + endung) or "unbenannt"


def baue(z: Zustand) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    def begruendet(e: BaseException, vorsatz: str, *, schluessel: str):
        """Ein Abbruch, dessen Begruendung in die Oberflaeche darf.

        Traegt die Ausnahme einen eigenen Schluessel (`core.hinweise.Abbruch`),
        geht DER an die Oberflaeche, samt Werten — der Satz dazu steht in vier
        Sprachen in `maschera.js`. Sonst der allgemeine `schluessel` OHNE den
        Text der Ausnahme: der stammt aus einer Bibliothek oder vom
        Betriebssystem, ist englisch oder in der Sprache des Systems und traegt
        mitunter einen temporaeren Pfad.

        ⚠️ Bis 1.0.1 blieb dieser Text in `fehler` («fuer die Kommandozeile und
        die API»). Bei der Docker-Fassung im Netz verriet das Serverpfade an
        jeden Aufrufer; CodeQL meldete es (`py/stack-trace-exposure`). Jetzt
        steht er im Protokoll des Servers (Standardfehlerausgabe) und nicht
        mehr in der Antwort. Nur `Abbruch` mit eigenem Schluessel traegt
        seinen Satz weiter — der ist von uns geschrieben.
        """
        if getattr(e, "schluessel", None):
            return fehler(f"{vorsatz}: {e}", schluessel=e.schluessel,
                          **getattr(e, "werte", {}))
        print(f"{vorsatz}: {type(e).__name__}: {e}", file=sys.stderr,
              flush=True)
        return fehler(vorsatz, schluessel=schluessel)

    def fehler(nachricht: str, code: int = 400,
               hinweise: list[dict] | None = None,
               schluessel: str | None = None, **werte):
        """Fehlerantwort. `hinweise` traegt mit, was der Leser gemeldet hat.

        Ein gescanntes PDF ohne Textebene ergaebe sonst nur «Der Text ist leer.»
        — und wer die kurze Fassung liest, haelt die Datei fuer kaputt. Richtig
        ist: die Datei ist in Ordnung, MASCHERA sieht nur nichts davon, und ein
        leerer Befund heisst NICHT, dass keine Personendaten drin sind.

        `fehler` bleibt der deutsche Satz; daneben stehen `fehler_schluessel` und
        `fehler_werte` fuer den, der uebersetzen kann.
        """
        koerper = {"fehler": nachricht}
        if schluessel:
            koerper["fehler_schluessel"] = schluessel
            koerper["fehler_werte"] = werte
        if hinweise:
            koerper["hinweise"] = hinweise
        return jsonify(koerper), code

    def leer(hinweise: list[dict]):
        """Antwort auf einen leeren Text — mit dem Grund des Lesers.

        Die Meldung des Lesers wird weitergereicht, nicht ueberschrieben. Sie
        nennt den Grund — Scan ohne Textebene, leeres Dokument, ungelesene
        Kopfzeilen — und sagt ausdruecklich, dass ein leerer Befund keine
        Entwarnung ist. Eine Stelle fuer `/api/lesen` und `/api/anonymisieren`,
        und der Schluessel wandert mit, damit Hinweis und Fehlerzeile in
        derselben Sprache stehen.
        """
        h = next((h for h in hinweise
                  if h["schluessel"] in LEERER_BEFUND), None)
        if h:
            return fehler(h["text"], hinweise=hinweise,
                          schluessel=h["schluessel"], **h["werte"])
        return fehler("Der Text ist leer.", hinweise=hinweise,
                      schluessel="text_leer")

    def abgelehnt(e: Abgelehnt, code: int = 400):
        """Eine Ablehnung aus `core` zur Fehlerantwort machen — eine Stelle fuer
        alle schreibenden Endpunkte, damit keiner den Schluessel vergisst.
        """
        return fehler(str(e), code, schluessel=e.schluessel, **e.werte)

    def warnung(*, schluessel: str, text: str, **werte) -> dict:
        """Der Warnungsteil einer Antwort, zum Auffalten mit `**`.

        Eine Warnung steht NEBEN einem Fehler, nicht an seiner Stelle:
        `GET /api/regeln` schickt beides, wenn die gespeicherte Regeldatei kaputt
        ist. Deshalb `warnung_schluessel` und `fehler_schluessel` getrennt.
        """
        return {"warnung": text, "warnung_schluessel": schluessel,
                "warnung_werte": werte}

    # -- Wirtsname ----------------------------------------------------------

    @app.before_request
    def nur_bekannte_wirte():
        """Ein fremder Name kommt nicht durch. Siehe `erlaubte_wirte()`.

        VOR allen Endpunkten und ohne Ausnahme — auch `/api/zustand`, auch die
        Oberflaeche. Eine Liste von Endpunkten, die den Wirt pruefen, waere beim
        naechsten Endpunkt wieder unvollstaendig.

        Eine ABSAGE mit Grund, keine stille Umleitung: bei einer falsch gesetzten
        `MASCHERA_WIRT` soll der Betreiber lesen koennen, was los ist.
        """
        erlaubt = erlaubte_wirte()
        if erlaubt is None:
            return None
        wirt = wirt_von(request.host)
        if wirt in erlaubt:
            return None
        return fehler(
            f"Dieser Dienst antwortet nicht unter dem Namen «{wirt}». "
            f"Lokal ist er unter 127.0.0.1 erreichbar; hinter einem "
            f"Proxy gehoert der Name in MASCHERA_WIRT.",
            403, schluessel="wirt_unbekannt", wirt=wirt)

    # -- Sicherheitskopfzeilen --------------------------------------------

    # Die zweite Verteidigungslinie: eine Content-Security-Policy.
    #
    # Die erste ist der Code: in der Oberflaeche steht kein `innerHTML`, kein
    # `eval`, kein Inline-Skript, und Pruefungen passen darauf auf. Bringt eine
    # kuenftige Aenderung doch einen Weg herein, auf dem Text zu Code wird,
    # koennte dieser Code den Klartext per `fetch` an einen fremden Server
    # schicken. Die Policy verbietet das auf Ebene des Browsers, unabhaengig
    # davon, ob der Code sauber ist.
    #
    # `connect-src` kennt Loopback, und nur Loopback. Die Portpruefung in den
    # Einstellungen (`maschera.js`, markiert «nach-aussen-erlaubt») bleibt fuer
    # den LOKALEN Dienst erreichbar; eine Adresse im Heimnetz nicht — alles,
    # was die Maschine verlaesst, bleibt gesperrt.
    #
    # Auf JEDER Antwort, nicht nur auf der Seite. Das Startfenster kommt nicht
    # von hier (`html=` in `fenster.py`) und ist davon nicht betroffen.
    RICHTLINIE = "; ".join((
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self'",
        "font-src 'self'",
        "connect-src 'self' http://127.0.0.1:* http://localhost:*",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
    ))

    @app.after_request
    def sicherheitskopfzeilen(antwort):
        antwort.headers["Content-Security-Policy"] = RICHTLINIE
        # Kein Raten des Inhaltstyps: eine `.txt`-Antwort bleibt Text,
        # auch wenn sie wie HTML aussieht.
        antwort.headers["X-Content-Type-Options"] = "nosniff"
        # Wer aus dem Werkzeug einen KI-Dienst oeffnet, verraet ihm nicht
        # die lokale Adresse, von der er kommt.
        antwort.headers["Referrer-Policy"] = "no-referrer"
        return antwort

    # -- Zustand ------------------------------------------------------------

    @app.get("/api/zustand")
    def zustand():
        """Laeuft der Server, welches Modell, welcher Labelvertrag.

        Auch die Portpruefung der Oberflaeche haengt hier: Wer auf 4141
        antwortet, ist noch lange nicht MASCHERA.
        """
        return jsonify({
            "dienst": "maschera",   # maschinenlesbar, klein
            "version": VERSION,
            "pack": z.pack_name,
            "label_hash": z.pack.get_label_hash(),
            "tags": len(z.pack.get_tags()),
            "modell": z.modellname,
            "ohne_modell": z.ohne_modell,
            # Die Obergrenze gehoert in die Antwort, damit die Hilfe sie NENNEN kann,
            # ohne sie ein zweites Mal zu tragen.
            "max_mb": MAX_UPLOAD // (1024 * 1024),
            "hinweise": _hinweise_ohne_modell() if z.ohne_modell else [],
        })

    # -- Tags ---------------------------------------------------------------

    @app.get("/api/tags")
    def tags():
        # `?sprache=fr`. Eine unbekannte Sprache wird abgewiesen und nicht
        # stillschweigend auf Deutsch zurueckgesetzt: eine franzoesische
        # Oberflaeche, die unbemerkt deutsche Bezeichnungen zeigt, saehe aus wie
        # ein Uebersetzungsfehler statt wie ein Programmierfehler.
        sprache = request.args.get("sprache", "de")
        try:
            bez = z.pack.get_bezeichnungen(sprache)
        except ValueError as e:
            return fehler(str(e), schluessel="sprache_unbekannt",
                          sprache=sprache,
                          moeglich=", ".join(z.pack.SPRACHEN))
        schwellen = z.pack.get_thresholds()
        return jsonify({
            "label_hash": z.pack.get_label_hash(),
            "sprache": sprache,
            "sprachen": list(z.pack.SPRACHEN),
            "tags": [
                {
                    "tag": t.tag,
                    "bezeichnung": bez.get(t.tag),
                    "platzhalter": t.placeholder,
                    "stufe": t.stage,
                    "aktion": t.action,
                    "budget": t.budget,
                    "bspd": t.bspd,
                    "pruefsumme": t.override == "checksum",
                    "schwelle": schwellen.get(t.tag),
                }
                for t in z.pack.get_tags()
            ],
        })

    # -- Maskieren ----------------------------------------------------------

    def _datei_lesen(hinweise: list[dict]):
        """Die hochgeladene Datei zu Text machen. Gibt `(text, None)` oder
        `(None, fehlerantwort)` zurueck.

        Eine Quelle fuer `/api/lesen` und den Dateizweig von
        `/api/anonymisieren`: Formatliste, Mehrfachnachricht und die Meldung des
        Lesers haben so einen Verwalter.
        """
        datei = next(iter(request.files.values()))
        # `Path(...).name` streift das Verzeichnis ab — `x/../../y.txt` wird zu
        # `y.txt`, und der Ausbruch aus dem temporaeren Ordner ist erledigt.
        #
        # Bei `.` und `/` gibt `name` aber den LEEREN String, und dann zeigte
        # `pfad` auf das temporaere Verzeichnis selbst: `datei.save()` wuerfe
        # `IsADirectoryError` am Behandler vorbei, und der Aufrufer bekaeme eine
        # HTML-Seite statt der JSON-Absage. Das `or` steht deshalb HINTER `.name`.
        # `..` braucht eine eigene Zeile, weil `Path("..").name` nicht `""` ist,
        # sondern `".."`.
        #
        # Zwei weitere Faelle (`tests/test_api.py` Punkt 8a):
        #
        #   ein NUL-Byte im Namen   -> `ValueError: embedded null byte`
        #   300 Zeichen im Namen    -> `OSError: File name too long`
        #
        # Deshalb wird der Name zurechtgelegt und nicht bloss geprueft — er dient
        # ohnehin nur zwei Zwecken, der Endung und einem Pfad fuer `pymupdf` und
        # `mailbox`.
        name = _sicherer_name(Path(datei.filename or "").name)
        endung = Path(name).suffix.lower()
        if endung not in ALLE:
            return None, fehler(
                f"Format {endung or '(ohne Endung)'} wird nicht gelesen. "
                f"Möglich: {', '.join(sorted(e for e in ALLE if e))}",
                schluessel="format_unbekannt",
                endung=endung or "(ohne Endung)",
                moeglich=", ".join(sorted(e for e in ALLE if e)))
        # Auf die Platte, weil `pymupdf` und `mailbox` einen Pfad brauchen. In ein
        # temporaeres Verzeichnis, das der `with`-Block samt Inhalt wieder loescht —
        # die Datei enthaelt Personendaten.
        with tempfile.TemporaryDirectory() as ordner:
            pfad = Path(ordner) / name
            datei.save(pfad)
            try:
                dokumente = lies(pfad)
            # `SystemExit` gehoert dazu, und es ist KEINE `Exception`.
            # `tools/dokumente.py` meldet damit die Faelle, die es ausdruecklich nicht
            # liest: altes `.doc`, fehlendes `pymupdf`, kaputtes ZIP. Ohne diese Zeile
            # wuerde eine saubere Absage zur 500 und saehe aus wie ein Absturz.
            except (Exception, SystemExit) as e:  # noqa: BLE001
                return None, begruendet(e, "Datei nicht lesbar",
                                        schluessel="datei_unlesbar")
        if not dokumente:
            return None, fehler("Datei ergab keinen Text.",
                                schluessel="datei_ohne_text")
        if len(dokumente) > 1:
            hinweise.append(hinweis(
                "mehrere_nachrichten",
                f"{len(dokumente)} Nachrichten in der Datei — nur die erste "
                f"wird verarbeitet.",
                anzahl=len(dokumente)))
        dok = dokumente[0]
        hinweise.extend(dok.hinweise)
        return dok.text, None

    @app.post("/api/lesen")
    def lesen():
        """Eine Datei zu Text machen — und SONST NICHTS.

        Ablegen soll einlesen, nicht maskieren. Maskieren ist die Handlung, um
        die es in diesem Werkzeug geht; sie hat einen eigenen Knopf, weil sie
        eine Entscheidung ist. Etwas, das von selbst laeuft, weil eine Datei ins
        Fenster gezogen wurde, ist keine Entscheidung mehr.

        Gelesen wird trotzdem im SERVER, nicht im Browser: PDF und DOCX gehen
        dort ohnehin nicht, und der leere Befund — Scan ohne Textebene — muss aus
        derselben Quelle kommen wie sonst. Ein leerer Befund ist keine
        Entwarnung, und das darf beim Ablegen nicht still werden.

        Geschrieben wird nichts. Die Datei liegt fuer die Dauer des Lesens in
        einem temporaeren Verzeichnis und ist danach weg.
        """
        if not request.files:
            return fehler("Keine Datei erhalten.",
                          schluessel="keine_datei")
        hinweise: list[dict] = []
        text, fehlschlag = _datei_lesen(hinweise)
        if fehlschlag is not None:
            return fehlschlag
        if not text.strip():
            return leer(hinweise)
        antwort = {"original": text}
        if hinweise:
            antwort["hinweise"] = hinweise
        return jsonify(antwort)

    @app.post("/api/anonymisieren")
    def anonymisieren():
        hinweise: list[dict] = []
        if z.ohne_modell:
            hinweise.extend(_hinweise_ohne_modell())

        # Text kommt entweder als JSON oder als Datei. Eine Datei laeuft durch
        # `_datei_lesen` — dieselbe Stelle, die auch `/api/lesen` benutzt,
        # damit Mail, PDF und Kodierung nicht zweimal verschieden behandelt
        # werden.
        if request.files:
            daten = request.form
            text, fehlschlag = _datei_lesen(hinweise)
            if fehlschlag is not None:
                return fehlschlag
        else:
            daten = request.get_json(silent=True) or {}
            text = daten.get("text")
            if not isinstance(text, str):
                return fehler("Feld `text` fehlt oder ist kein Text.",
                              schluessel="feld_text")

        if not text.strip():
            return leer(hinweise)

        def flagge(schluessel: str, vorgabe: bool) -> bool:
            wert = daten.get(schluessel, vorgabe)
            if isinstance(wert, str):
                return wert.lower() not in ("false", "0", "nein", "")
            return bool(wert)

        woerterbuch = flagge("woerterbuch", True)
        regeln_an = flagge("regeln", True)
        auch_bspd = flagge("auch_bspd", False)

        # `ohne` fehlt ganz -> die gespeicherten Vorlieben gelten. Steht es da,
        # auch als leere Liste, gilt genau das und sonst nichts. Sonst waere
        # nicht ausdrueckbar: «diesmal alles maskieren».
        if "ohne" in daten:
            roh = daten.get("ohne") or []
            if isinstance(roh, str):
                roh = [x for x in roh.replace(",", " ").split() if x]
            ohne = set(roh)
        else:
            ohne = vorlieben.lade()
            if ohne:
                hinweise.append(hinweis(
                    "vorlieben",
                    "Aus den gespeicherten Vorlieben im Klartext: "
                    + ", ".join(sorted(ohne)),
                    tags=", ".join(sorted(ohne))))

        bekannt = {t.tag for t in z.pack.get_tags()}
        unbekannt = sorted(ohne - bekannt)
        if unbekannt:
            return fehler(f"Unbekannte Tags bei `ohne`: {unbekannt}",
                          schluessel="ohne_tags_unbekannt",
                          tags=", ".join(unbekannt))
        try:
            vorlieben.pruefe(ohne, z.pack, auch_bspd)
        except vorlieben.Abgelehnt as e:
            return abgelehnt(e)

        if not woerterbuch:
            hinweise.append(hinweis(
                "ohne_woerterbuch",
                "Ohne Wörterbuch — endgültig anonymisiert, keine "
                "Rückwandlung möglich."))

        try:
            regeln = z.regeln(regeln_an)
        except SystemExit as e:  # `user_rules` meldet Fehler so
            return begruendet(e, "Regeldatei fehlerhaft",
                              schluessel="regeldatei_fehlerhaft")
        if regeln:
            hinweise.append(hinweis(
                "eigene_regeln",
                f"Eigene Regeln angewendet ({len(regeln)}): "
                + ", ".join(r.bezeichnung for r in regeln),
                anzahl=len(regeln),
                namen=", ".join(r.bezeichnung for r in regeln)))

        with z.sperre:
            antwort = _durchlauf(z, text, ohne, woerterbuch, regeln,
                                 hinweise)
        return jsonify(antwort)

    # -- Fortschritt --------------------------------------------------------

    @app.get("/api/fortschritt")
    def fortschritt():
        """Wie weit ist der laufende Durchgang?

        Nimmt `z.sperre` NICHT: der Lauf haelt sie die ganze Zeit, und wer hier
        wartete, bekaeme die Antwort erst, wenn es nichts mehr zu melden gibt.
        Es steht nichts Vertrauliches darin: drei Zahlen und ein Wort.
        """
        return jsonify(z.stand())

    # -- Zurueckwandeln -----------------------------------------------------

    @app.post("/api/zurueckwandeln")
    def zurueckwandeln():
        daten = request.get_json(silent=True) or {}
        text = daten.get("text")
        wb = daten.get("woerterbuch")
        if not isinstance(text, str):
            return fehler("Feld `text` fehlt oder ist kein Text.",
                          schluessel="feld_text")
        if not isinstance(wb, dict):
            return fehler("Feld `woerterbuch` fehlt oder ist kein Objekt.",
                          schluessel="feld_woerterbuch")

        # Was NICHT zugeordnet werden konnte, ist der wichtige Teil: das
        # Sprachmodell schreibt Platzhalter um. Deshalb erst zaehlen, dann
        # ersetzen — `restore` schweigt darueber.
        gefunden = [m.group(0) for m in PLACEHOLDER_RE.finditer(text)]
        fehlend = sorted({p for p in gefunden if p not in wb})
        ersetzt = sum(1 for p in gefunden if p in wb)

        hinweise = []
        # Ein umgeschriebener Platzhalter unterscheidet sich meist nur in der
        # Gross-/Kleinschreibung — `[NAME_1]` statt `[Name_1]`. Das hier still
        # zu beheben waere falsch: dann ersetzt der Server etwas, das so nie
        # vergeben wurde. Gemeldet wird es trotzdem, sonst sucht der Anwender
        # an der falschen Stelle.
        klein = {k.lower(): k for k in wb}
        for p in fehlend:
            treffer = klein.get(p.lower())
            if treffer:
                hinweise.append(hinweis(
                    "schreibweise",
                    f"{p} unterscheidet sich von {treffer} nur in der "
                    f"Schreibweise — nicht ersetzt.",
                    platzhalter=p, treffer=treffer))

        return jsonify({
            "text": restore(text, wb),
            "ersetzt": ersetzt,
            "nicht_gefunden": fehlend,
            "hinweise": hinweise,
        })

    # -- Eigene Regeln ------------------------------------------------------

    @app.get("/api/regeln")
    def regeln_lesen():
        pfad = Path(z.regeln_pfad) if z.regeln_pfad else user_rules.VORGABE
        # Nicht ueber `z.regeln(True)`, weil dort die Altlasten nicht
        # durchkommen. Dieselbe Funktion mit einem Argument mehr — kein zweiter
        # Ladeweg.
        altlasten: set = set()
        try:
            regeln = user_rules.lade(z.regeln_pfad, z.pack, altlasten)
        except SystemExit as e:
            # Ein Fehler in einer Antwort mit Kennung 200: die gespeicherte
            # Regeldatei ist kaputt, der ROHTEXT wird trotzdem geliefert, damit die
            # Oberflaeche ihn zum Bearbeiten anzeigen kann. Deshalb kein
            # `fehler(...)`, aber dieselben drei Felder.
            #
            # Die Begruendung wie ueberall: der eigene Schluessel, wenn es einen
            # gibt, sonst der allgemeine — nie der Rohtext als `{grund}`.
            if getattr(e, "schluessel", None):
                schluessel, werte = e.schluessel, e.werte
            else:
                schluessel, werte = "regeldatei_fehlerhaft", {}
            return jsonify({"pfad": str(pfad), "yaml": _lies_roh(pfad),
                            "regeln": [],
                            # Nur der eigene Satz; der Text einer fremden
                            # Ausnahme gehoert nicht in die Antwort.
                            "fehler": (str(e) if getattr(e, "schluessel", None)
                                       else "Regeldatei fehlerhaft"),
                            "fehler_schluessel": schluessel,
                            "fehler_werte": werte})
        return jsonify({
            "pfad": str(pfad),
            "yaml": _lies_roh(pfad),
            "regeln": [
                {"id": r.id, "bezeichnung": r.bezeichnung,
                 "platzhalter": r.platzhalter, "tag": r.tag,
                 "stufe": r.recognizer.stage}
                for r in regeln
            ],
            # «Veraltet» und nicht «deutsch»: in `altlasten` steht auch `stage`, und
            # `stage` ist kein deutscher Schluessel.
            **(warnung(
                schluessel="regeln_veraltete_schluessel",
                text="Diese Regeldatei benutzt veraltete Schlüssel. "
                     "Sie werden weiter gelesen oder übergangen: "
                     + "; ".join(sorted(altlasten)),
                umbenennungen="; ".join(sorted(altlasten)))
               if altlasten else
               warnung(schluessel="regeln_gelesen",
                       text="Wer die Regeln ändert, ändert das "
                            "Messergebnis.")),
        })

    @app.put("/api/regeln")
    def regeln_schreiben():
        daten = request.get_json(silent=True) or {}
        roh = daten.get("yaml")
        if not isinstance(roh, str):
            return fehler("Feld `yaml` fehlt oder ist kein Text.",
                          schluessel="feld_yaml")

        # ⚠️ Erst pruefen, dann schreiben. Eine kaputte Regeldatei legt jeden
        # weiteren Lauf lahm — und zwar erst beim naechsten Dokument, nicht
        # beim Speichern. Geprueft wird gegen dieselbe Funktion, die spaeter
        # laedt, nicht gegen eine zweite Fassung davon.
        with tempfile.TemporaryDirectory() as ordner:
            probe = Path(ordner) / "regeln.yaml"
            probe.write_text(roh, encoding="utf-8")
            try:
                geprueft = user_rules.lade(probe, z.pack)
            except SystemExit as e:
                return begruendet(e, "Regeln abgelehnt",
                                  schluessel="regeln_abgelehnt")
            except Exception as e:  # noqa: BLE001
                return begruendet(e, "Regeln nicht lesbar",
                                  schluessel="regeln_unlesbar")

        pfad = Path(z.regeln_pfad) if z.regeln_pfad else user_rules.VORGABE
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(roh, encoding="utf-8")
        return jsonify({
            "pfad": str(pfad),
            "regeln": len(geprueft),
            **warnung(schluessel="regeln_gespeichert",
                      text="Gespeichert. Das Messergebnis ändert sich damit."),
        })

    # -- Klartext-Vorlieben -------------------------------------------------
    #
    # Lesen und schreiben, was ohne `ohne` gilt. Geschrieben wird nach
    # `~/.config/maschera/`, nur auf ausdruecklichen Befehl, nie beilaeufig
    # beim Maskieren.

    @app.get("/api/vorlieben")
    def vorlieben_lesen():
        gesetzt = vorlieben.lade()
        bspd = {t.tag for t in z.pack.get_tags() if t.bspd}
        # Was gespeichert ist, muss nicht mehr gueltig sein: ein Tag kann
        # zwischenzeitlich aus der Taxonomie verschwunden sein. Das gehoert
        # gemeldet, nicht stillschweigend gefiltert.
        bekannt = {t.tag for t in z.pack.get_tags()}
        unbekannt = sorted(gesetzt - bekannt)
        return jsonify({
            "klartext": sorted(gesetzt),
            "bspd": sorted(gesetzt & bspd),
            "unbekannt": unbekannt,
            "pfad": str(vorlieben.PFAD),
            **warnung(schluessel="klartext_gelesen",
                      text="Diese Tags bleiben dauerhaft im Klartext."),
        })

    @app.put("/api/vorlieben")
    def vorlieben_schreiben():
        daten = request.get_json(silent=True) or {}
        roh = daten.get("klartext")
        if not isinstance(roh, list) or any(not isinstance(t, str)
                                            for t in roh):
            return fehler("Feld `klartext` fehlt oder ist keine Tagliste.",
                          schluessel="feld_klartext")

        # Geprueft wird gegen dieselbe Funktion, die spaeter laedt —
        # `vorlieben.speichere` ruft `vorlieben.pruefe`. Unbekannte Tags werden
        # abgelehnt statt ignoriert, und besonders schuetzenswerte Tags verlangen
        # `auch_bspd`. Dasselbe verlangt `/api/anonymisieren` fuer `ohne`; waere es
        # hier anders, liesse sich die Wache umgehen, indem man den Tag dauerhaft
        # setzt statt ihn einmal mitzuschicken.
        try:
            vorlieben.speichere(set(roh), z.pack,
                                bool(daten.get("auch_bspd")))
        except vorlieben.Abgelehnt as e:
            return abgelehnt(e)
        except OSError as e:
            return begruendet(e, "Nicht gespeichert",
                              schluessel="nicht_gespeichert")

        gesetzt = vorlieben.lade()
        bspd = {t.tag for t in z.pack.get_tags() if t.bspd}
        return jsonify({
            "klartext": sorted(gesetzt),
            "bspd": sorted(gesetzt & bspd),
            "pfad": str(vorlieben.PFAD),
            **warnung(schluessel="klartext_gespeichert",
                      text="Gespeichert. Diese Tags bleiben dauerhaft im "
                           "Klartext — auch in künftigen Dokumenten."),
        })

    # -- Prompt-Vorlagen ----------------------------------------------------
    #
    # Dieselbe Bauart wie `/api/vorlieben`: geprueft wird gegen dieselbe
    # Funktion, die spaeter laedt, und eine abgelehnte Liste laesst die
    # bestehende Datei unberuehrt.
    #
    # Ein Prompt kann Personendaten enthalten. Verhindern laesst sich das
    # nicht — die Warnung in jeder Antwort ist das, was das Werkzeug tun kann.

    WARNUNG = ("Vorlagen liegen dauerhaft im Klartext auf der Platte. "
               "Keine Personendaten in eine Vorlage schreiben.")

    @app.get("/api/vorlagen")
    def vorlagen_lesen():
        return jsonify({
            "vorlagen": vorlagen.lade(),
            "pfad": str(vorlagen.PFAD),
            **warnung(schluessel="vorlagen_klartext", text=WARNUNG),
        })

    @app.put("/api/vorlagen")
    def vorlagen_schreiben():
        daten = request.get_json(silent=True) or {}
        try:
            vorlagen.speichere(daten.get("vorlagen"))
        except vorlagen.Abgelehnt as e:
            return abgelehnt(e)
        except OSError as e:
            return begruendet(e, "Nicht gespeichert",
                              schluessel="nicht_gespeichert")
        return jsonify({
            "vorlagen": vorlagen.lade(),
            "pfad": str(vorlagen.PFAD),
            **warnung(schluessel="vorlagen_klartext", text=WARNUNG),
        })

    # -- Einstellungen ------------------------------------------------------
    #
    # Adresse, Port, Dienste und die Fensterschalter — nichts, was ein
    # Geheimnis ist. Ein Feld fuer API-Schluessel gibt es nicht: MASCHERA
    # sendet nichts selbst.

    @app.get("/api/einstellungen")
    def einstellungen_lesen():
        return jsonify({**einstellungen.lade(),
                        "pfad": str(einstellungen.PFAD)})

    @app.put("/api/einstellungen")
    def einstellungen_schreiben():
        try:
            sauber = einstellungen.speichere(request.get_json(silent=True))
        except einstellungen.Abgelehnt as e:
            return abgelehnt(e)
        except OSError as e:
            return begruendet(e, "Nicht gespeichert",
                              schluessel="nicht_gespeichert")
        return jsonify({**sauber, "pfad": str(einstellungen.PFAD),
                        **warnung(schluessel="einstellungen_gespeichert",
                                  text="Gespeichert.")})

    @app.errorhandler(413)
    def zu_gross(_e):
        return fehler(f"Datei grösser als {MAX_UPLOAD // (1024 * 1024)} MB.",
                      413, schluessel="datei_zu_gross",
                      mb=MAX_UPLOAD // (1024 * 1024))

    return app


def _lies_roh(pfad: Path) -> str:
    try:
        return pfad.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------

def main() -> int:
    # So frueh wie moeglich: wer den Prozess sucht, sucht ihn meist, weil
    # etwas haengt — dann ist er womoeglich noch gar nicht fertig gestartet.
    from core import prozess
    prozess.benenne()

    ap = argparse.ArgumentParser(description="Flask-Kern von MASCHERA.")
    ap.add_argument("--model", default=None, help="Trainingsordner")
    ap.add_argument("--onnx", default=None, help="Release-Ordner mit model.onnx")
    ap.add_argument("--ohne-modell", action="store_true",
                    help="nur Stufe 1 und 2 — Namen bleiben im Klartext")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--regeln", default=None,
                    help="eigene Regeln, Vorgabe ~/.config/maschera/regeln.yaml")
    ap.add_argument("--host", default="127.0.0.1")
    # ⚠️ Aus `core.einstellungen`, nicht als Zahl hier. Siehe dort.
    ap.add_argument("--port", type=int, default=einstellungen.VORGABE_PORT)
    args = ap.parse_args()

    if not (args.model or args.onnx or args.ohne_modell):
        ap.error("Entweder --model, --onnx oder --ohne-modell angeben.")

    z = Zustand(args.pack, args.model, args.onnx, args.max_length, args.regeln)
    app = baue(z)

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
    print(f"  http://{args.host}:{args.port}/api/zustand")

    # `threaded=True`, damit `/api/zustand` waehrend eines Laufs antwortet.
    # Die Kette selbst ist durch `z.sperre` serialisiert.
    app.run(host=args.host, port=args.port, threaded=True, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
