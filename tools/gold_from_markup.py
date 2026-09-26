#!/usr/bin/env python3
"""Gold-Spannen aus markiertem Text erzeugen.

    # 1. Vormarkieren — die Kette schlaegt vor, du korrigierst
    python3 tools/gold_from_markup.py --vormarkieren /pfad/brief.txt \\
        --model runs/ch-v63b --out /pfad/brief.markiert.txt

    # 2. Im Editor: Tags korrigieren UND Werte ersetzen, in EINEM Durchgang

    # 3. Anlegen — die Spannen stimmen konstruktionsbedingt
    python3 tools/gold_from_markup.py --anlegen /pfad/brief.markiert.txt \\
        --id de-brief-003 --lang de --doctype mailverlauf

## Warum dieser Weg und nicht `eval_documents.py --anlegen`

Jener Weg verlangt **zwei** Durchgaenge: erst die Werte im Text ersetzen,
dann die vorgeschlagenen Spannen in einer JSON-Datei durchsehen — doppelte
Arbeit an derselben Entscheidung, und man hat Zeichenpositionen statt Text
vor sich.

**Wer ersetzt, weiss die Spannen.** Hier wird in einem Durchgang markiert
und ersetzt, und die Spannen ergeben sich aus den Einsetzpositionen.

## Markierung

    Von: [[FULLNAME:Hasli]] [[GIVENNAME:Leopold]] <[[EMAIL:l.h@example.ch]]>

Alles ausserhalb der Klammern ist `O`. Die Spannen ergeben sich aus den
Einsetzpositionen — dieselbe Mechanik wie beim Injektor, dieselbe Sicherheit.

## Die Wache gegen Uebersehenes

Vor dem Anlegen laeuft `restverdacht()` ueber den unmarkierten Text. Findet es
etwas, das nach einem Personendatum aussieht, bricht das Werkzeug ab statt es
still ins Testset zu schreiben. `--trotzdem` hebt das auf, wenn du geprueft
hast.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))

from core import pfade  # noqa: E402
from core import user_rules  # noqa: E402
from core.inference import merge  # noqa: E402
from dokumente import lies  # noqa: E402
from filter_document import restverdacht  # noqa: E402
from packs import load_pack  # noqa: E402

# ⚠️ Hier stand dieselbe `EVAL_DIR`-Zeile wie in `eval_documents.py` und
# `kalibriere_schwellen.py`. Siehe dort — der Pfad kommt aus `core/pfade.py`.

# [[TAG:wert]] — der Wert darf keine eckigen Klammern enthalten.
MARKE = re.compile(r"\[\[([A-Za-z_][A-Za-z0-9_]*):([^\[\]]*)\]\]")


def zerlege(markiert: str, erlaubte: set[str]) -> tuple[str, list[dict], list[str]]:
    """Markierten Text zu (Klartext, Spannen, Befunde)."""
    text_teile: list[str] = []
    spans: list[dict] = []
    befunde: list[str] = []
    pos = 0
    laenge = 0

    for m in MARKE.finditer(markiert):
        tag, wert = m.group(1), m.group(2)
        vorher = markiert[pos:m.start()]
        text_teile.append(vorher)
        laenge += len(vorher)

        if tag not in erlaubte:
            befunde.append(
                f"unbekanntes Tag {tag!r} bei {wert!r} — erlaubt sind die "
                f"Tags der Taxonomie und die Benutzerregeln (X_…)")
        if not wert:
            befunde.append(f"leere Markierung [[{tag}:]]")
        elif wert != wert.strip():
            befunde.append(
                f"Randleerzeichen in [[{tag}:{wert}]] — die Leerzeichen "
                f"gehoeren VOR die Klammer")

        spans.append({"tag": tag, "start": laenge, "end": laenge + len(wert),
                      "wert": wert})
        text_teile.append(wert)
        laenge += len(wert)
        pos = m.end()

    text_teile.append(markiert[pos:])
    text = "".join(text_teile)

    # Gegenprobe: jede Spanne muss den Wert zurueckliefern. Sitzt eine daneben,
    # ist die Zerlegung kaputt — lauter Fehler statt stiller Verschiebung.
    for s in spans:
        if text[s["start"]:s["end"]] != s["wert"]:
            befunde.append(
                f"Spanne {s['start']}-{s['end']} liefert "
                f"{text[s['start']:s['end']]!r} statt {s['wert']!r}")
    return text, spans, befunde


def vormarkieren(args, pack) -> int:
    quelle = Path(args.vormarkieren)
    dokumente = lies(quelle)
    if len(dokumente) > 1:
        raise SystemExit(f"{quelle} enthaelt {len(dokumente)} Nachrichten.")
    text = dokumente[0].text
    for h in dokumente[0].hinweise:
        print(f"  HINWEIS {h['text']}", file=sys.stderr)

    scorer = None
    if args.model:
        from evaluate_model import TorchScorer
        scorer = TorchScorer(args.model, args.max_length)
        scorer.check_contract(pack)
    regeln = user_rules.lade(args.regeln, pack)
    model_spans = scorer.score(text) if scorer else []
    spans, _ = merge(text, model_spans, pack,
                     user_spans=user_rules.erkenne(text, regeln))

    teile, pos = [], 0
    for s in sorted(spans, key=lambda s: s.start):
        if s.start < pos:
            continue
        teile.append(text[pos:s.start])
        teile.append(f"[[{s.tag}:{text[s.start:s.end]}]]")
        pos = s.end
    teile.append(text[pos:])
    markiert = "".join(teile)

    ziel = Path(args.out) if args.out else quelle.with_suffix(".markiert.txt")
    ziel.write_text(markiert, encoding="utf-8")
    print(f"-> {ziel}  ({len(spans)} Vorschlaege)", file=sys.stderr)
    print(file=sys.stderr)
    print("  Jetzt im Editor, in EINEM Durchgang:", file=sys.stderr)
    print("    1. falsche Markierungen entfernen (Klammern weg, Wert bleibt)",
          file=sys.stderr)
    print("    2. fehlende ergaenzen: [[FULLNAME:Meier]]", file=sys.stderr)
    print("    3. Tags korrigieren", file=sys.stderr)
    print("    4. **die Werte durch erfundene ersetzen**", file=sys.stderr)
    print(file=sys.stderr)
    print("  Die Vorschlaege sind ZIRKULAER — sie stammen aus derselben Kette,",
          file=sys.stderr)
    print("  die geprueft werden soll. Was sie uebersieht, fehlt auch hier.",
          file=sys.stderr)
    return 0


def anlegen(args, pack) -> int:
    quelle = Path(args.anlegen)
    markiert = quelle.read_text(encoding="utf-8")

    erlaubte = {t.tag for t in pack.get_tags()}
    erlaubte |= {r.tag for r in user_rules.lade(args.regeln, pack)}

    text, spans, befunde = zerlege(markiert, erlaubte)
    if befunde:
        print("Befunde in der Markierung:")
        for b in befunde:
            print(f"  {b}")
        return 1

    if not spans:
        raise SystemExit("Keine Markierungen gefunden. Format: [[TAG:wert]]")

    # --- Wache gegen Uebersehenes -------------------------------------------
    abgedeckt = bytearray(len(text))
    for s in spans:
        for i in range(s["start"], s["end"]):
            abgedeckt[i] = 1
    verdacht = restverdacht(text, abgedeckt)

    def offen(a: int, b: int) -> str:
        """Die BEDEUTSAMEN Zeichen, die unabgedeckt blieben.

        Nur auf Abdeckung zu pruefen genuegt nicht: «[[FULLNAME:Bossi]]
        [[GIVENNAME:Mario]]» laesst das Leerzeichen dazwischen unabgedeckt, und
        der Verdachtstreffer «Bossi Mario» spannt darueber. Ein Leerzeichen ist
        kein Personendatum.
        """
        return "".join(text[i] for i in range(a, b)
                       if not abgedeckt[i] and not text[i].isspace()
                       and text[i] not in ".,;:!?()<>-/")

    def offene_woerter(a: int, b: int) -> str:
        """Die WOERTER des Treffers, die unabgedeckte Zeichen enthalten.

        `offen()` liefert die blossen Zeichen und taugt als Filter, nicht zur
        Anzeige: aus 'Planzer Paket Logo' wird dort 'Logo', aus 'Haben Sie
        Fragen' wird 'HabenSieFragen'. Wer vor dem Abbruch sitzt, muss
        wissen, WELCHE Woerter offen sind.
        """
        teile: list[str] = []
        wort: list[str] = []
        wort_offen = False
        for i in range(a, b):
            if text[i].isspace():
                if wort and wort_offen:
                    teile.append("".join(wort))
                wort, wort_offen = [], False
                continue
            wort.append(text[i])
            if not abgedeckt[i]:
                wort_offen = True
        if wort and wort_offen:
            teile.append("".join(wort))
        return " ".join(teile)

    # Verengt wird NUR die Klasse, an der die Verengung gemessen wurde: ein
    # einzelnes grossgeschriebenes Wort ist im Deutschen der Normalfall und
    # kein Namensverdacht.
    #
    # Ausgeschlossen wird, was NICHT gezeigt werden soll — nicht aufgezaehlt,
    # was gezeigt wird. Eine Liste erlaubter Arten liesse `Ziffernfolge` und
    # `Pfad` wortlos herausfallen, und eine Sendungsnummer erreichte den
    # Abbruch nie.
    eng = [(a, s, e, w) for a, s, e, w in verdacht
           if offen(s, e)
           and not (a == "Grossschreibung" and len(w.split()) < 2)]
    if eng and not args.trotzdem:
        # ⚠️ Die Meldung sagt, was geprueft wurde, nicht was gefunden wurde.
        # `restverdacht()` ist ein grobes Netz mit vielen Fehlalarmen, und
        # das steht so in seinem eigenen Docstring — «sehen nach unersetzten
        # Personendaten aus» behauptete ein Urteil, das der Regex nicht
        # faellen kann.
        print(f"ABBRUCH: {len(eng)} unmarkierte Stellen. Grobes Netz, viele "
              f"Fehlalarme — bitte durchsehen:\n")
        for a, s, e, w in eng[:20]:
            rest = offene_woerter(s, e)
            # Nur anzeigen, wenn der Treffer mehr umfasst als das Offene.
            # 'Planzer Paket Logo' sah aus wie ein unmarkierter Firmenname
            # und war eine Spannengrenze — das hat eine Runde gekostet.
            zusatz = ("" if rest == " ".join(w.split())
                      else f"   -> offen: {rest!r}")
            print(f"  {s:6}  {a:16} {w!r}{zusatz}")
        if len(eng) > 20:
            print(f"  … {len(eng) - 20} weitere")
        print("\n  Entweder markieren (dann sind sie Gold) oder ersetzen.")
        print("  Sind alle geprueft und in Ordnung: --trotzdem")
        return 1

    kennung = args.id or quelle.stem.replace(".markiert", "")
    # Immer an den neuen Ort, nie in den Projektbaum — siehe `gold_schreiben()`.
    ordner = pfade.gold_schreiben(args.pack, "real")
    ziel = ordner / f"{kennung}.json"
    if ziel.is_file() and not args.ueberschreiben:
        alt = json.loads(ziel.read_text(encoding="utf-8"))
        zusatz = ("  ⚠️ Sie ist bereits GEPRUEFT — Handarbeit ginge verloren.\n"
                  if alt.get("geprueft") else "")
        raise SystemExit(f"{ziel} existiert bereits.\n{zusatz}"
                         f"  --ueberschreiben nutzen.")

    ordner.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps({
        "id": kennung,
        "lang": args.lang,
        "doctype": args.doctype,
        "herkunft": args.herkunft,
        # Konstruktionsbedingt geprueft: die Spannen stammen aus den
        # Markierungen, nicht aus einem Vorschlag der eigenen Kette.
        "geprueft": True,
        "quelle_markiert": str(quelle),
        "text": text,
        "spans": spans,
        "zu_pruefen": [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    je_tag: dict[str, int] = {}
    for s in spans:
        je_tag[s["tag"]] = je_tag.get(s["tag"], 0) + 1
    print(f"-> {ziel}")
    print(f"   {len(text)} Zeichen, {len(spans)} Spannen, geprueft: true")
    print("   " + ", ".join(f"{k} {v}" for k, v in
                            sorted(je_tag.items(), key=lambda kv: -kv[1])))
    if eng and args.trotzdem:
        # `eng`, NICHT `verdacht`: die Zahl steht hier als Rechenschaft darueber,
        # was der Mensch verantwortet. Sie muss dieselbe Liste zaehlen, die ihm
        # vorgelegt wurde.
        print(f"\n   {len(eng)} Verdachtsstellen uebergangen (--trotzdem)")
        print("   Genau die, die der Abbruch ohne --trotzdem gezeigt haette.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vormarkieren", default=None,
                    help="Textdatei -> markierte Fassung zum Bearbeiten")
    ap.add_argument("--anlegen", default=None,
                    help="markierte Fassung -> Golddokument")
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--regeln", default=None)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--id", default=None)
    ap.add_argument("--lang", default="de")
    ap.add_argument("--doctype", default="unbekannt")
    ap.add_argument("--herkunft", default="")
    ap.add_argument("--ueberschreiben", action="store_true")
    ap.add_argument("--trotzdem", action="store_true",
                    help="anlegen trotz Verdachtsstellen")
    args = ap.parse_args()

    pack = load_pack(args.pack)
    if args.vormarkieren:
        return vormarkieren(args, pack)
    if args.anlegen:
        return anlegen(args, pack)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
