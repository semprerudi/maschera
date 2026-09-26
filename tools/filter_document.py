#!/usr/bin/env python3
"""Ein echtes Dokument durch die volle Kette schicken und lesbar berichten.

    python3 tools/filter_document.py --model runs/ch-v63b brief.txt
    python3 tools/filter_document.py --model runs/ch-v63b /pfad/zu/dokumenten/ --klartext
    python3 tools/filter_document.py brief.txt --ohne-modell
    python3 tools/filter_document.py --model runs/ch-v63b /pfad/zu/dokumenten/ \\
        --bericht /tmp/bericht.json --woerterbuch /tmp/dict.json

Der Unterschied zu `evaluate_model.py`: dort braucht es Gold-Spannen, und es
faellt eine Zahl heraus. Hier gibt es kein Gold — es faellt ein TEXT heraus,
den ein Mensch liest. Genau dort stehen die Fehler, die keine Kennzahl zeigt.

Drei Abschnitte:

  1. Der maskierte Text. Das ist der eigentliche Befund.
  2. Fundstellen — was wurde erkannt, von welcher Stufe, mit welchem Vertrauen.
  3. Verworfen — was hat die Kette weggeworfen und WARUM. Ohne diese Liste
     ist nicht nachvollziehbar, weshalb etwas durchging.

Dazu optional `--verdacht`: ein grobes Netz ueber alles, was NICHT maskiert
wurde und trotzdem nach Personendatum aussieht — die einzige Hilfe gegen die
Blindstelle eines Laufs ohne Gold.

**Formate:** `.txt`, `.md`, `.eml`, `.mbox` und `.pdf`. Ein Verzeichnis wird
im Stapel gelesen, eine `.mbox` ergibt eine Mail je Nachricht. PDF braucht
`pymupdf`; bei einem Scan ohne Textebene kommt nichts heraus, und ein leerer
Befund heisst dort NICHT, dass nichts drin ist.

**Klartext.** Standardmaessig enthaelt der Bericht keine Originalwerte, nur
Tag, Position und Laenge. Damit ist er weitergabefaehig. `--klartext` nimmt
die Werte auf; dann enthaelt die Berichtsdatei dieselben Personendaten wie
das Dokument und gehoert genauso behandelt.
"""

from __future__ import annotations

import argparse
import json
import bisect
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))

from core.inference import Scored, filter_text  # noqa: E402
from core import vorlieben  # noqa: E402
from dokumente import ALLE, lies, sammle  # noqa: E402
from packs import load_pack  # noqa: E402


# ---------------------------------------------------------------------------
# Der Laeufer merkt sich die Vertrauenswerte
# ---------------------------------------------------------------------------

class Mitschreiber:
    """Legt sich um einen Scorer und behaelt, was er geliefert hat.

    `filter_text` gibt Spannen ohne Vertrauen zurueck — das Vertrauen wird beim
    Zusammenfuehren verbraucht. Fuer den Bericht wird es aber gebraucht: eine
    Fundstelle mit 0.31 knapp ueber der Schwelle liest sich anders als eine mit
    0.99. Deshalb dieser Umweg statt einer Aenderung an `filter_text`.
    """

    def __init__(self, inner):
        self.inner = inner
        self.werte: dict[tuple[str, int, int], float] = {}
        # Nachschlagehilfe fuer `vertrauen_zu`, siehe dort. `None` heisst
        # «noch nicht gebaut»; `_stand` merkt sich, fuer wie viele Werte.
        self._nach_tag: dict[str, list[tuple[int, int, float]]] | None = None
        self._laengste: dict[str, int] = {}
        self._stand = -1

    def score(self, text: str) -> list[Scored]:
        out = self.inner.score(text)
        for s in out:
            self.werte[(s.tag, s.start, s.end)] = s.score
        return out

    def vertrauen_zu(self, span) -> float | None:
        """Vertrauen einer fertigen Fundstelle — nur fuer Modelltreffer.

        Die Werte liegen unter `(tag, start, end)`, und dieser Schluessel stimmt
        in zwei Faellen nicht:

        1. `auf_wortgrenzen` dehnt Modellspannen aus, BEVOR zusammengefuehrt wird.
           Danach passt der Schluessel nicht mehr — ausgerechnet bei den
           ausgedehnten, also den unsicheren Spannen.

        2. Finden Regex und Modell dieselbe Spanne, traefe der Schluessel
           zufaellig, und an einem deterministischen Treffer stuende eine
           Modellzahl. Laut `docs/API_OBERFLAECHE.md` ist `vertrauen` bei
           `regex` und `propagation` null.

        Deshalb: Quelle zuerst, dann der exakte Schluessel, dann die
        ueberlappende Modellspanne desselben Tags. Bei mehreren die UNSICHERSTE —
        die Ausdehnung hat Zeichen dazugenommen, ueber die das Modell nichts
        gesagt hat, und die Anzeige soll nicht sicherer wirken als der Befund.

        **Die einzige Stelle, die den Schluessel aufloest.** `filter_document.py`
        und `app/serve.py` rufen sie beide auf.
        """
        if getattr(span, "source", None) != "model":
            return None
        genau = self.werte.get((span.tag, span.start, span.end))
        if genau is not None:
            return genau

        # Die Werte einmal nach Tag geordnet und nach Anfang sortiert, dann findet
        # `bisect` den Einstieg. Ein Durchlauf ueber ALLE Modellwerte je Fundstelle
        # waechst bei langen Dokumenten quadratisch. `_laengste` je Tag sagt, wie
        # weit davor eine ueberlappende Spanne beginnen kann.
        eintraege = self._geordnet().get(span.tag)
        if not eintraege:
            return None
        weit = self._laengste.get(span.tag, 0)
        i = bisect.bisect_left(eintraege, (span.start - weit,))
        bester = None
        for a, b, w in eintraege[i:]:
            if a >= span.end:
                break
            if b > span.start and (bester is None or w < bester):
                bester = w
        return bester

    def _geordnet(self) -> dict[str, list[tuple[int, int, float]]]:
        """Die Modellwerte nach Tag, nach Anfang sortiert. Einmal je Lauf.

        ⚠️ `_stand` statt eines Schalters: `werte` wird zwischen den
        Durchgaengen geleert und neu gefuellt, und ein Gedaechtnis, das das
        nicht merkt, antwortet mit den Zahlen des VORIGEN Dokuments. Das
        waere schlimmer als langsam.
        """
        if self._nach_tag is not None and self._stand == len(self.werte):
            return self._nach_tag
        nach_tag: dict[str, list[tuple[int, int, float]]] = {}
        laengste: dict[str, int] = {}
        for (tag, a, b), w in self.werte.items():
            nach_tag.setdefault(tag, []).append((a, b, w))
            if b - a > laengste.get(tag, 0):
                laengste[tag] = b - a
        for liste in nach_tag.values():
            liste.sort()
        self._nach_tag = nach_tag
        self._laengste = laengste
        self._stand = len(self.werte)
        return nach_tag


def _zeile(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _kontext(text: str, start: int, end: int, breite: int = 28) -> str:
    a, b = max(0, start - breite), min(len(text), end + breite)
    schnipsel = text[a:start] + "»" + text[start:end] + "«" + text[end:b]
    return schnipsel.replace("\n", "⏎")


# ---------------------------------------------------------------------------
# Restverdacht — das grobe Netz
# ---------------------------------------------------------------------------

VERDACHT = [
    ("Ziffernfolge", re.compile(r"\b\d[\d'.\- ]{3,}\d\b")),
    # NUR das Leerzeichen trennt, weder `\s` noch `\t`.
    #
    # `\s+` spannte ueber Zeilenumbrueche: 'Sophia\n\n\nVon' wurde ein
    # Namensverdacht. Und ein Tabulator ist eine Spaltengrenze, kein
    # Wortabstand: in Formularen wie 'Name\tAndrea Brülhart' reichte der
    # Verdacht sonst vom FELDNAMEN in den Wert hinein. Zwischen Vor- und
    # Nachnamen steht er nie.
    ("Grossschreibung", re.compile(
        r"\b[A-ZÄÖÜÀ-Þ][a-zäöüà-ÿ'’\-]{2,}(?: +[A-ZÄÖÜÀ-Þ][a-zäöüà-ÿ'’\-]{2,}){0,2}\b")),
    ("Adresszeichen", re.compile(r"\S+@\S+|https?://\S+|\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("Pfad", re.compile(r"(?:[A-Z]:\\|/)(?:[\w.\-]+[/\\]){1,}[\w.\-]*")),
]

# Wörter, die gross geschrieben sind und trotzdem nie ein Personendatum sind.
# Bewusst KURZ gehalten: das Netz soll zuviel fangen, nicht zuwenig.
HARMLOS = {
    "Der", "Die", "Das", "Ein", "Eine", "Sehr", "Mit", "Bei", "Von", "Für",
    "Herr", "Frau", "Guten", "Freundliche", "Grüsse", "Betreff", "Datum",
    "Le", "La", "Les", "Un", "Une", "Monsieur", "Madame", "Objet",
    "Il", "Lo", "Gli", "Signor", "Signora", "Oggetto",
    "The", "This", "Dear",
    # Im Deutschen wird JEDES Substantiv gross geschrieben. «Grossgeschriebenes
    # Wort neben grossgeschriebenem Wort» ist damit kein Namensverdacht,
    # sondern der Normalfall — «Vielen Dank», «Ihr Anliegen», «Diese
    # Beratungen». Deshalb diese Liste von Funktionswoertern am Anfang.
    #
    # Bei sechzehn Meldungen pro Dokument tippt man `--trotzdem` aus
    # Gewohnheit, und dann faengt die Wache nichts mehr. Eine Wache, die man
    # wegklickt, ist keine.
    "Vielen", "Viele", "Herzlichen", "Besten", "Ihr", "Ihre", "Ihrer", "Ihren",
    "Ihrem", "Unser", "Unsere", "Unserer", "Diese", "Dieser", "Dieses",
    "Sobald", "Falls", "Damit", "Dabei", "Zudem", "Ausserdem", "Weitere",
    "Liebe", "Lieber", "Geschätzte", "Hallo", "Beste", "Merci",
    "Votre", "Vos", "Notre", "Nos", "Cette", "Cordialement", "Veuillez",
    "Vostro", "Vostra", "Nostro", "Nostra", "Questa", "Questo", "Gentile",
    "Your", "Our", "These", "Kind", "Best", "Please", "Thank", "Thanks",
    # Weitere deutsche Satzanfaenge: Praepositionen und Konjunktionen am
    # Satzanfang sind grossgeschrieben und tragen nie einen Namen.
    "Beim", "Nach", "Vor", "Seit", "Aus", "Auf", "Ohne", "Gegen",
    "Wegen", "Aufgrund", "Gestützt", "Betreffend", "Zur", "Zum", "Als",
    "Sollte", "Sofern", "Nachdem", "Bevor", "Anbei", "Gerne", "Leider",
    "Subject", "Regards",
    # Anreden und Grussformeln: sie stehen am Zeilenanfang vor einem Namen.
    "Ciao", "Caro", "Cara", "Cari", "Salve", "Buongiorno",
    "Bonjour", "Chère", "Cher",
    "Meilleures", "Cordiali", "Caso", "Come", "Spero",
    # Gruss- und Anredeformeln in allen Beugungen — «Herzliche» (Gruesse)
    # neben «Herzlichen» (Dank), «Freundliche» neben «Freundlicher». Die Luecke
    # ist sonst keine Wortluecke, sondern eine Beugungsluecke.
    # `tests/test_gold_markup.py` Punkt 5 zaehlt die Formeln auf.
    "Herzliche", "Schöne", "Sonnige", "Werte", "Freundlicher", "Warme",
    "Liebste", "Bester", "Lieben", "Herzlichst",
    # Verben am Anfang einer Frage. Dieselbe Klasse wie die Praepositionen
    # daneben: im Deutschen grossgeschrieben, nie ein Name («Haben Sie
    # Fragen?»).
    "Haben", "Können", "Möchten", "Wollen", "Sollten", "Dürfen", "Müssen",
    "Sind", "Ist", "Wird", "Werden", "Wurde", "Wurden", "Brauchen",
    "Benötigen", "Melden", "Kontaktieren", "Antworten", "Klicken",
}


def restverdacht(text: str, abgedeckt: bytearray) -> list[tuple[str, int, int, str]]:
    """Alles, was unmaskiert blieb und nach Personendatum aussieht.

    Grobes Netz mit vielen Fehlalarmen — das ist Absicht. Ein Fehlalarm kostet
    eine Zeile Lesen, eine uebersehene Entitaet kostet ein Leck.
    """
    treffer: list[tuple[str, int, int, str]] = []
    for art, muster in VERDACHT:
        for m in muster.finditer(text):
            a, b = m.span()
            if all(abgedeckt[i] for i in range(a, b)):
                continue
            wert = m.group()
            if art == "Grossschreibung" and wert.split()[0] in HARMLOS:
                continue
            if art == "Grossschreibung" and len(wert.split()) == 1:
                # Einzelnes grossgeschriebenes Wort am Satzanfang ist Rauschen.
                davor = text[:a].rstrip()
                if not davor or davor[-1] in ".!?:\n":
                    continue
            treffer.append((art, a, b, wert))
    treffer.sort(key=lambda t: t[1])
    # Ueberlappende Verdachtsfaelle zusammenfassen
    knapp: list[tuple[str, int, int, str]] = []
    for t in treffer:
        if knapp and t[1] < knapp[-1][2]:
            continue
        knapp.append(t)
    return knapp


# ---------------------------------------------------------------------------

def verarbeite(dok, pack, scorer, args) -> dict:
    """Ein Dokument durch die Kette schicken und berichten."""
    text = dok.text
    # Benutzerregeln muessen HIER genauso eingemischt werden wie in `mask()`
    # — sonst zeigt der Bericht ihre Treffer als «nicht maskiert» an, obwohl
    # sie es sind, und die Deckungsrechnung unterschlaegt sie.
    stufen = {t.tag: t.stage for t in pack.get_tags()}
    stufen.update({r.tag: r.recognizer.stage for r in args.regelsatz})
    schwellen = args.schwellen
    actions = dict(pack.get_actions())
    actions.update({r.tag: "mask" for r in args.regelsatz})

    print("=" * 74)
    print(f"DOKUMENT  {dok.kennung}   [{dok.format}, {len(text)} Zeichen]")
    print("=" * 74)
    for h in dok.hinweise:
        print(f"  HINWEIS {h['text']}")
    if not text.strip():
        print("  leer — uebersprungen\n")
        return {"kennung": dok.kennung, "leer": True}
    if len(text) > args.max_length * 3:
        # Der Torch-Laeufer fenstert: das Modell sieht das ganze Dokument, nicht
        # nur die ersten 512 Token.
        print(f"  HINWEIS Laenger als ein Fenster ({args.max_length} Token). "
              f"Wird ueberlappend verarbeitet.")
    print()

    if scorer is not None:
        scorer.werte.clear()
    ergebnis = filter_text(text, pack, scorer,
                           propagate=not args.keine_propagation,
                           thresholds=args.schwellen,
                           excluded=set(args.ohne),
                           mapping_enabled=not args.ohne_woerterbuch,
                           rules=args.regelsatz)

    # --- 1. Der maskierte Text --------------------------------------------
    print("--- MASKIERTER TEXT " + "-" * 54)
    print(ergebnis.masked)
    print()

    abgedeckt = bytearray(len(text))
    for s in ergebnis.spans:
        if actions.get(s.tag) == "mask":
            for i in range(s.start, s.end):
                abgedeckt[i] = 1

    # --- 2. Fundstellen ----------------------------------------------------
    # Der Platzhalter laesst sich NICHT allein ueber den Wert nachschlagen:
    # derselbe Nachname kann an einer Stelle als FULLNAME und an einer anderen
    # als GIVENNAME erkannt worden sein, und dann gewaenne im Rueckwaertsindex
    # der zuletzt eingetragene — die Anzeige saehe nach vertauschten
    # Platzhaltern aus.
    plaetze = {t.tag: t.placeholder for t in pack.get_tags()}
    plaetze.update({r.tag: r.platzhalter for r in args.regelsatz})

    def platzhalter(tag: str, wert: str) -> str:
        praefix = plaetze.get(tag)
        if not praefix:
            return "—"
        treffer = [ph for ph, v in ergebnis.dictionary.items()
                   if v == wert and ph.startswith(f"[{praefix}_")]
        return treffer[0] if treffer else "?"

    if not args.knapp:
        print(f"--- FUNDSTELLEN ({len(ergebnis.spans)}) " + "-" * 48)
    kopf = (f"{'Zl':>4}  {'Tag':<18}{'St':>3}  {'Quelle':<11}{'Vert':>6}  "
            f"{'Platzhalter':<18}")
    if args.klartext:
        kopf += "Wert"
    if not args.knapp:
        print(kopf)

    fundstellen = []
    for s in ergebnis.spans:
        wert = s.value(text)
        v = scorer.vertrauen_zu(s) if scorer else None
        ph = platzhalter(s.tag, wert) if actions.get(s.tag) == "mask" else "—"
        zeile = f"{_zeile(text, s.start):>4}  {s.tag:<18}{stufen.get(s.tag,3):>3}  "
        zeile += f"{s.source:<11}"
        zeile += f"{v:>6.2f}  " if v is not None else f"{'—':>6}  "
        zeile += f"{ph:<18}"
        if args.klartext:
            zeile += repr(wert)
        if not args.knapp:
            print(zeile)
        eintrag = {
            "tag": s.tag, "stufe": stufen.get(s.tag, 3),
            "start": s.start, "end": s.end, "laenge": s.end - s.start,
            "zeile": _zeile(text, s.start), "quelle": s.source,
            "vertrauen": v, "platzhalter": ph,
            "maskiert": actions.get(s.tag) == "mask",
        }
        if args.klartext:
            eintrag["wert"] = wert
            eintrag["kontext"] = _kontext(text, s.start, s.end)
        fundstellen.append(eintrag)
    if not args.knapp:
        print()

    # --- 3. Verworfen ------------------------------------------------------
    if not args.knapp:
        print(f"--- VERWORFEN ({len(ergebnis.dropped)}) " + "-" * 50)
        if not ergebnis.dropped:
            print("  nichts")
        for tag, wert, grund in ergebnis.dropped:
            schwelle = schwellen.get(tag)
            zusatz = (f"  (Schwelle {schwelle:.2f})"
                      if schwelle is not None else "")
            gezeigt = repr(wert) if args.klartext else f"<{len(wert)} Zeichen>"
            print(f"  {tag:<18}{gezeigt:<28}{grund}{zusatz}")
        print()

    # --- Restverdacht ------------------------------------------------------
    verdachtsfaelle = []
    if args.verdacht and not args.knapp:
        faelle = restverdacht(text, abgedeckt)
        gezeigte = faelle if args.alle else faelle[:args.verdacht_max]
        print(f"--- RESTVERDACHT ({len(faelle)}, gezeigt {len(gezeigte)}) "
              + "-" * 36)
        print("  Unmaskiert und sieht nach Personendatum aus. Grobes Netz mit")
        print("  Fehlalarmen: einer kostet eine Zeile Lesen, eine uebersehene")
        print("  Entitaet kostet ein Leck.")
        if not faelle:
            print("  nichts")
        for art, a, b, wert in gezeigte:
            gezeigt = repr(wert) if args.klartext else f"<{len(wert)} Zeichen>"
            print(f"  Zl {_zeile(text, a):>4}  {art:<16}{gezeigt}")
            eintrag = {"art": art, "start": a, "end": b,
                       "zeile": _zeile(text, a)}
            if args.klartext:
                eintrag["wert"] = wert
                eintrag["kontext"] = _kontext(text, a, b)
            verdachtsfaelle.append(eintrag)
        if len(faelle) > len(gezeigte):
            print(f"  … {len(faelle) - len(gezeigte)} weitere. Vollstaendig "
                  f"mit --alle oder in --bericht.")
        print()

    je_tag: dict[str, int] = {}
    je_quelle: dict[str, int] = {}
    for s in ergebnis.spans:
        je_tag[s.tag] = je_tag.get(s.tag, 0) + 1
        je_quelle[s.source] = je_quelle.get(s.source, 0) + 1

    if ergebnis.erweitert:
        print(f"  {ergebnis.erweitert} Modellspannen lagen mitten in einem "
              f"Wort und wurden auf")
        print(f"  Wortgrenzen gezogen. Eine hohe Zahl heisst: das Modell sieht "
              f"Text,\n  den es nicht kennt.")
    print(f"  {len(text)} Zeichen, davon {sum(abgedeckt)} maskiert "
          f"({100 * sum(abgedeckt) / max(1, len(text)):.1f} %) · "
          f"{len(ergebnis.spans)} Fundstellen · "
          f"{len(ergebnis.dictionary)} Woerterbucheintraege")
    print(f"  Tags: " + ", ".join(f"{k} {v}" for k, v in
                                  sorted(je_tag.items(), key=lambda kv: -kv[1])))
    print()

    return {
        "kennung": dok.kennung,
        "format": dok.format,
        "hinweise": dok.hinweise,
        "zeichen": len(text),
        "maskierte_zeichen": sum(abgedeckt),
        "fundstellen": fundstellen,
        "verworfen": [
            {"tag": t, "grund": g,
             **({"wert": w} if args.klartext else {"laenge": len(w)})}
            for t, w, g in ergebnis.dropped
        ],
        "verdacht": verdachtsfaelle,
        "maskierter_text": ergebnis.masked,
        "woerterbuch": ergebnis.dictionary if args.klartext else {},
        "_dict": ergebnis.dictionary,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Dokumente durch die volle Kette schicken und berichten.")
    ap.add_argument("pfad", nargs="?", help="Datei oder Verzeichnis. "
                                 "txt, md, eml, mbox, pdf")
    ap.add_argument("--model", default=None,
                    help="Trainingsordner, z.B. runs/ch-v63b")
    ap.add_argument("--onnx", default=None,
                    help="Release-Ordner mit model.onnx statt --model")
    ap.add_argument("--ohne-modell", action="store_true",
                    help="nur Stufe 1 und 2 — Grundlinie ohne Modell")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--klartext", action="store_true",
                    help="Originalwerte in Bericht und Ausgabe aufnehmen "
                         "(dann enthalten sie Personendaten)")
    ap.add_argument("--verdacht", action="store_true",
                    help="unmaskierte Stellen listen, die nach PII aussehen")
    ap.add_argument("--bericht", default=None,
                    help="Bericht als JSON schreiben (bei mehreren Dokumenten "
                         "eine Datei mit allen)")
    ap.add_argument("--woerterbuch", default=None,
                    help="Woerterbuch als JSON schreiben (immer Klartext)")
    ap.add_argument("--knapp", action="store_true",
                    help="nur maskierter Text und Zusammenfassung")
    ap.add_argument("--alle", action="store_true",
                    help="Restverdacht vollstaendig statt gedeckelt")
    ap.add_argument("--verdacht-max", type=int, default=12,
                    help="hoechstens so viele Verdachtsfaelle je Dokument")
    ap.add_argument("--schwelle", action="append", default=[],
                    metavar="TAG=WERT",
                    help="Schwelle einzeln setzen, mehrfach erlaubt. "
                         "Auch R=, A=, P= fuer ein ganzes Budget.")
    ap.add_argument("--ohne", action="append", default=[], metavar="TAG",
                    help="Tag erkennen, aber NICHT ersetzen. Mehrfach erlaubt.")
    ap.add_argument("--ohne-woerterbuch", action="store_true",
                    help="endgueltig anonymisieren: Nummerierung bleibt, "
                         "Werte sind nicht rekonstruierbar")
    ap.add_argument("--auch-bspd", action="store_true",
                    help="erlaubt --ohne auch fuer besonders schuetzenswerte "
                         "Personendaten (NATIONALITY, RELIGION, HEALTH …)")
    ap.add_argument("--klartext-merken", action="store_true",
                    help="die --ohne-Auswahl dauerhaft speichern")
    ap.add_argument("--ohne-vorlieben", action="store_true",
                    help="gespeicherte Klartext-Vorlieben nicht laden")
    ap.add_argument("--tags", action="store_true",
                    help="Tagliste dieses Packs zeigen und beenden")
    ap.add_argument("--regeln", default=None,
                    help="eigene Regeln, Vorgabe ~/.config/maschera/regeln.yaml")
    ap.add_argument("--ohne-regeln", action="store_true",
                    help="eigene Regeln fuer diesen Lauf nicht laden")
    ap.add_argument("--keine-propagation", action="store_true")
    args = ap.parse_args()

    if args.tags:
        print(vorlieben.legende(load_pack(args.pack)))
        return 0
    if not args.pfad:
        ap.error("pfad fehlt")

    # Gespeicherte Vorlieben und die Schalter dieses Laufs zusammenfuehren.
    #
    # Warum die gespeicherten NICHT stillschweigend gelten: `--ohne` nimmt
    # Personendaten aus der Ersetzung. Eine Einstellung, die das dauerhaft
    # tut und dabei unsichtbar bleibt, ist genau die Art Wache, die man
    # wegklickt. Sie wird deshalb bei jedem Lauf ausgeschrieben.
    _pack = load_pack(args.pack)
    gemerkt = set() if args.ohne_vorlieben else vorlieben.lade()
    gewaehlt = set(args.ohne)
    try:
        vorlieben.pruefe(gewaehlt | gemerkt, _pack, args.auch_bspd)
    except vorlieben.Abgelehnt as e:
        print(f"ABBRUCH: {e}", file=sys.stderr)
        return 2
    if args.klartext_merken:
        print(f"Klartext-Vorlieben gespeichert: "
              f"{vorlieben.speichere(gewaehlt, _pack, args.auch_bspd)}")
    args.ohne = sorted(gewaehlt | gemerkt)
    if gemerkt - gewaehlt:
        print("Aus den gespeicherten Vorlieben im Klartext: "
              + ", ".join(sorted(gemerkt - gewaehlt)))

    pfad = Path(args.pfad)
    if not pfad.exists():
        raise SystemExit(f"Nicht gefunden: {pfad}")

    dateien = sammle(pfad)
    if not dateien:
        raise SystemExit(
            f"Keine lesbaren Dateien in {pfad}.\n"
            f"Unterstuetzt: {', '.join(sorted(e for e in ALLE if e))}")

    pack = load_pack(args.pack)

    # --- Schwellen, ggf. ueberschrieben ------------------------------------
    #
    # Zum Ausprobieren, ohne YAML zu editieren. Die Vorgaben stehen im Pack
    # und sind dort an den Golddokumenten kalibriert
    # (`tools/kalibriere_schwellen.py`).
    schwellen = dict(pack.get_thresholds())
    budgets = {t.tag: t.budget for t in pack.get_tags()}
    for eintrag in args.schwelle:
        if "=" not in eintrag:
            raise SystemExit(f"--schwelle braucht TAG=WERT, bekam {eintrag!r}")
        schluessel, wert = eintrag.split("=", 1)
        wert = float(wert)
        if schluessel in ("R", "A", "P"):
            treffer = [t for t, b in budgets.items() if b == schluessel]
            for t in treffer:
                schwellen[t] = wert
            print(f"Schwelle Budget {schluessel} = {wert:.2f} "
                  f"({len(treffer)} Tags)")
        else:
            if schluessel not in budgets:
                raise SystemExit(f"Unbekanntes Tag: {schluessel}")
            schwellen[schluessel] = wert
            print(f"Schwelle {schluessel} = {wert:.2f}")

    # --- Laeufer waehlen ---------------------------------------------------
    scorer = None
    if args.ohne_modell:
        print("Kette: Stufe 1 + 2 (Regex und Pruefsummen), OHNE Modell.")
        print("       Namen, Daten und Adressen bleiben im Klartext.")
    elif args.onnx:
        from core.inference import OnnxScorer
        roh = OnnxScorer(args.onnx, args.max_length)
        roh.check_contract(pack)
        scorer = Mitschreiber(roh)
        print(f"Kette: Modell (ONNX) + Regex + Pruefsummen — {args.onnx}")
    elif args.model:
        from evaluate_model import TorchScorer
        roh = TorchScorer(args.model, args.max_length)
        roh.check_contract(pack)
        scorer = Mitschreiber(roh)
        print(f"Kette: Modell + Regex + Pruefsummen — {args.model} "
              f"auf {roh.device}")
    else:
        raise SystemExit("Entweder --model, --onnx oder --ohne-modell angeben.")
    from core import user_rules
    args.regelsatz = [] if args.ohne_regeln else user_rules.lade(args.regeln, pack)
    if args.regelsatz:
        print(f"Eigene Regeln ({len(args.regelsatz)}): " + ", ".join(
            f"{r.bezeichnung} -> [{r.platzhalter}_n]" for r in args.regelsatz))
    args.schwellen = schwellen
    unbekannt = set(args.ohne) - {t.tag for t in pack.get_tags()}
    if unbekannt:
        raise SystemExit(f"Unbekannte Tags bei --ohne: {sorted(unbekannt)}")
    if args.ohne:
        print(f"Nicht ersetzt (nur erkannt): {', '.join(sorted(args.ohne))}")
    if args.ohne_woerterbuch:
        print("Endgueltige Anonymisierung — kein Woerterbuch, keine "
              "Rueckfuehrung moeglich.")
    print(f"{len(dateien)} Datei(en) unter {pfad}\n")

    # --- Durchlauf ---------------------------------------------------------
    berichte, woerterbuecher = [], {}
    for datei in dateien:
        try:
            dokumente = lies(datei)
        except SystemExit:
            raise
        except Exception as fehler:
            print(f"  FEHLER beim Lesen von {datei.name}: {fehler}\n")
            continue
        # NULL DOKUMENTE IST EIN BEFUND, KEINE RUHE.
        #
        # `mailbox.mbox` braucht die `From `-Trennzeile. Eine leere Datei ergibt
        # null Nachrichten — und eine `.eml`, die jemand `.mbox` genannt hat,
        # ebenfalls. Ohne diese Stelle liefen beide wortlos durch: kein Text, keine
        # Meldung, Rueckgabewert 0. Der Server meldet denselben Fall als
        # `datei_ohne_text`.
        if not dokumente:
            print(f"  LEER: {datei.name} ergab keine Nachricht. Bei einer "
                  f".mbox heisst das meist: die `From `-Trennzeile fehlt "
                  f"— es ist wohl eine einzelne Mail und gehoert auf "
                  f".eml.\n")
            continue
        for dok in dokumente:
            b = verarbeite(dok, pack, scorer, args)
            if b.get("leer"):
                berichte.append(b)
                continue
            woerterbuecher[b["kennung"]] = b.pop("_dict")
            berichte.append(b)

    # --- Sammeluebersicht --------------------------------------------------
    echte = [b for b in berichte if not b.get("leer")]
    if len(echte) > 1:
        print("=" * 74)
        print("UEBERSICHT")
        print("=" * 74)
        print(f"{'Dokument':<44}{'Zeichen':>9}{'mask %':>8}{'Funde':>7}"
              f"{'Verd.':>7}")
        for b in echte:
            anteil = 100 * b["maskierte_zeichen"] / max(1, b["zeichen"])
            print(f"{b['kennung'][:43]:<44}{b['zeichen']:>9}{anteil:>7.1f}%"
                  f"{len(b['fundstellen']):>7}{len(b['verdacht']):>7}")
        print()
        alle_tags: dict[str, int] = {}
        for b in echte:
            for f in b["fundstellen"]:
                alle_tags[f["tag"]] = alle_tags.get(f["tag"], 0) + 1
        print("  Tags insgesamt: " + ", ".join(
            f"{k} {v}" for k, v in sorted(alle_tags.items(),
                                          key=lambda kv: -kv[1])))

        # Wie sicher war das Modell? Ein Tag, dessen Treffer alle knapp ueber
        # der Schwelle liegen, ist ein Kandidat fuers Hochsetzen. Ohne diese
        # Spalte kalibriert man im Dunkeln.
        vertrauen_je_tag: dict[str, list[float]] = {}
        for b in echte:
            for f in b["fundstellen"]:
                if f["quelle"] == "model" and f["vertrauen"] is not None:
                    vertrauen_je_tag.setdefault(f["tag"], []).append(
                        f["vertrauen"])
        if vertrauen_je_tag:
            print()
            print("  Vertrauen der MODELL-Treffer je Tag "
                  "(Schwelle · Minimum · Median · Anzahl):")
            for tag, werte in sorted(vertrauen_je_tag.items(),
                                     key=lambda kv: min(kv[1])):
                werte = sorted(werte)
                med = werte[len(werte) // 2]
                sch = args.schwellen.get(tag)
                # ⚠️ `f"{a if b else f'{x:.2f}':>6}"` wendet `:>6` auf das
                # GANZE Bedingte an — bei `None` wirft das. Die Zeile lief
                # jahrelang, weil kein Dokument ein schwellenloses Tag aus
                # dem MODELL brachte; die sechs Pruefsummen-Tags kommen
                # sonst aus Stufe 1. Erst eine Probe mit erfundenen Nummern
                # hat es ausgeloest — und riss den ganzen Lauf mitsamt
                # Bericht mit, NACH dem Modell.
                #
                # `ohne` und nicht `—`: eine leere Zelle sieht aus wie ein
                # Anzeigefehler. Ein Tag ohne Schwelle wird NICHT gefiltert
                # (`core/inference.py`: `if limit is not None`), also faellt
                # jede Modellspanne durch, bei jedem Vertrauen. Das ist bei
                # den Pruefsummen-Tags richtig — die Mathematik entscheidet —
                # und es gehoert trotzdem sichtbar dagestanden.
                spalte = "ohne" if sch is None else f"{sch:.2f}"
                print(f"    {tag:<18}{spalte:>6}"
                      f"{min(werte):>8.2f}{med:>8.2f}{len(werte):>6}")
            print()
            print("  Aufsteigend nach Minimum: was oben steht, feuert am")
            print("  unsichersten. R/A/P = 0.30/0.50/0.70 sind Platzhalter —")
            print("  mit --schwelle R=0.9 laesst sich das ausprobieren.")
        fehlend = sorted({t.tag for t in pack.get_tags()} - set(alle_tags))
        print(f"\n  Nicht ein einziges Mal aufgetreten ({len(fehlend)}):")
        print("  " + ", ".join(fehlend))
        print("\n  Ein Tag ohne Treffer heisst nicht, dass es nicht vorkam.")
        print("  Genau das sagt nur der maskierte Text, gelesen.")
        print()

    print("  Diese Zahlen messen NICHTS. Ohne Gold-Spannen gibt es keine")
    print("  Leckrate. Der Befund steht im maskierten Text — gelesen,")
    print("  nicht gezaehlt.")

    # --- Dateien schreiben -------------------------------------------------
    if args.bericht:
        Path(args.bericht).write_text(json.dumps({
            "pfad": str(pfad),
            "pack": args.pack,
            "label_hash": pack.get_label_hash(),
            "modell": args.model or args.onnx or None,
            "klartext": args.klartext,
            "dokumente": berichte,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nBericht geschrieben: {args.bericht}")
        if args.klartext:
            print("  ACHTUNG Der Bericht enthaelt die Originalwerte. Er ist")
            print("          so schutzbeduerftig wie die Dokumente selbst.")

    if args.woerterbuch:
        inhalt = (woerterbuecher if len(woerterbuecher) > 1
                  else next(iter(woerterbuecher.values()), {}))
        Path(args.woerterbuch).write_text(
            json.dumps(inhalt, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Woerterbuch geschrieben: {args.woerterbuch}")
        print("  ACHTUNG Das Woerterbuch ist der Schluessel zum Klartext.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
