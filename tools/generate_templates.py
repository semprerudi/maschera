#!/usr/bin/env python3
"""Vorlagen von einem lokalen LLM erzeugen lassen — «LLM author, code labeler».

    python3 tools/generate_templates.py --probe
    python3 tools/generate_templates.py --lang fr --domaene mietvertrag \\
        --tags MARITALSTATUS,CITY,STREET --anzahl 3 --trocken
    python3 tools/generate_templates.py --lang it --domaene arbeitszeugnis \\
        --anzahl 4 --out packs/ch/templates/it/arbeit_neu.yaml

Das Prinzip: **Das LLM schreibt ausschliesslich
Prosa mit Slots und sieht nie einen echten Wert.** Der Code injiziert die Werte
und erzeugt die BIO-Labels aus den Einsetzpositionen.

Daraus folgt der zweite Teil des Grundsatzes, und der ist hier der wichtigere:
**dem Autor wird nicht geglaubt.** Jede erzeugte Vorlage laeuft durch dieselben
Wachen wie eine von Hand geschriebene, plus drei zusaetzliche:

  1. Nur bekannte Slots. Erfindet das Modell `{NAME}` statt `{FULLNAME}` oder
     `{@adresse}` statt `{@address}`, wird die Vorlage verworfen — ein
     unbekanntes Tag laesst `align()` spaeter mit `KeyError` abstuerzen.
  2. Keine echten Werte im Text. Geprueft mit dem EIGENEN Erkenner: schlaegt
     ein Stufe-1- oder Stufe-2-Muster auf dem Vorlagentext an, hat das Modell
     einen Wert hingeschrieben statt einen Slot. Sprachmodelle tun das
     staendig, weil ein ausgefuelltes Beispiel «hilfreicher» aussieht.
  3. Die verlangten Tags muessen vorkommen. Sonst erzeugt man 40 Vorlagen und
     hat die Luecke, die man schliessen wollte, immer noch.

Dazu die bestehenden: `check_template()` (benachbarte Slots mit gleichem Tag,
`\\n` als Literal) und `pruefe_decoy_stellung()` (Etikett vor Phrasen-Decoy).

**Kein Netzzugang ausser zum eigenen Endpunkt.** Keine neuen Abhaengigkeiten —
`urllib` aus der Standardbibliothek genuegt fuer eine OpenAI-kompatible
Schnittstelle.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))

from core.injector import DECOYS, check_template, pruefe_decoy_stellung  # noqa: E402
from core.recognizers import recognize  # noqa: E402
from packs import load_pack  # noqa: E402

import yaml  # noqa: E402

VORGABE_ENDPUNKT = (os.environ.get("MASCHERA_LLM")
                    or "http://127.0.0.1:1234/v1")
VORGABE_MODELL = "google/gemma-4-26b-a4b-qat"

SPRACHNAME = {"de": "Deutsch", "fr": "Französisch", "it": "Italienisch",
              "en": "Englisch"}

SLOT = re.compile(r"\{([^}]*)\}")


# ---------------------------------------------------------------------------
# Endpunkt
# ---------------------------------------------------------------------------

def frage(endpunkt: str, modell: str, system: str, nutzer: str,
          temperatur: float = 0.8, max_tokens: int = 6000,
          roh_zeigen: bool = False) -> str:
    """Eine Frage an den Endpunkt. Gibt den Textinhalt zurueck.

    **Modelle mit Denkschritt legen das Ergebnis nicht immer in `content`.**
    Geht das Token-Budget vollstaendig fuer den Denkschritt drauf, bleibt
    `content` leer. `finish_reason` sagt es (`length` statt `stop`), aber nur,
    wenn man hinschaut. Deshalb schaut dieses Werkzeug hin.
    """
    daten = json.dumps({
        "model": modell,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": nutzer}],
        "temperature": temperatur,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    anfrage = urllib.request.Request(
        f"{endpunkt}/chat/completions", data=daten,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(anfrage, timeout=900) as antwort:
            roh = json.loads(antwort.read().decode("utf-8"))
    except urllib.error.URLError as fehler:
        raise SystemExit(
            f"Endpunkt {endpunkt} nicht erreichbar: {fehler}\n"
            f"Pruefen: curl -s --max-time 5 {endpunkt}/models")

    if roh_zeigen:
        print(json.dumps(roh, ensure_ascii=False, indent=2)[:4000])

    wahl = (roh.get("choices") or [{}])[0]
    nachricht = wahl.get("message") or {}
    grund = wahl.get("finish_reason")

    # `content` zuerst, dann die ueblichen Felder fuer den Denkschritt.
    inhalt = nachricht.get("content") or ""
    if not inhalt.strip():
        for feld in ("reasoning_content", "reasoning", "thinking"):
            if nachricht.get(feld):
                inhalt = nachricht[feld]
                print(f"  HINWEIS Antwort stand in `{feld}`, nicht in "
                      f"`content`.")
                break

    if not inhalt.strip():
        verbrauch = roh.get("usage", {})
        raise SystemExit(
            f"Das Modell hat KEINEN Text geliefert.\n"
            f"  finish_reason : {grund}\n"
            f"  Felder        : {sorted(nachricht)}\n"
            f"  Verbrauch     : {verbrauch}\n\n"
            + ("  `length` heisst: das Token-Budget war aufgebraucht, bevor\n"
               "  die Antwort begann — bei Modellen mit Denkschritt geht es\n"
               "  dafuer drauf. Mit --max-tokens hoeher ansetzen.\n"
               if grund == "length" else
               "  Mit --roh nochmal aufrufen, dann steht die vollstaendige\n"
               "  Antwort des Endpunkts da.\n"))
    return inhalt


# ---------------------------------------------------------------------------
# Auftrag formulieren
# ---------------------------------------------------------------------------

def bekannte_slots(pack) -> tuple[set[str], set[str], set[str]]:
    tags = {t.tag for t in pack.get_tags()}
    makros = set()
    pfad = HIER.parent / "packs" / "ch" / "macros.yaml"
    if pfad.is_file():
        daten = yaml.safe_load(pfad.read_text(encoding="utf-8")) or {}
        makros = set(daten.get("macros", {}))
    decoys = set(DECOYS)
    return tags, makros, decoys


def systemauftrag(pack, lang: str) -> str:
    tags, makros, decoys = bekannte_slots(pack)
    verfuegbar = sorted(tags)
    return f"""Du schreibst Vorlagen für ein Trainingskorpus zur Erkennung von
Personendaten in Schweizer Dokumenten. Sprache der Vorlagen: {SPRACHNAME[lang]}.

REGELN, alle zwingend:

1. Du schreibst NUR Fliesstext mit Platzhaltern. Du setzt NIEMALS einen
   konkreten Wert ein — keinen Namen, kein Datum, keine Nummer, keine Adresse,
   keinen Betrag, keine E-Mail. Statt «Hans Meier» schreibst du {{FULLNAME}}.
   Statt «3011 Bern» schreibst du {{ZIPCODE}} {{CITY}}.

2. Erlaubte Entitäts-Platzhalter, ausschliesslich diese:
   {', '.join('{' + t + '}' for t in verfuegbar)}

3. Erlaubte Makros (gekoppelte Gruppen, bevorzugt verwenden):
   {', '.join('{@' + m + '}' for m in sorted(makros))}

4. Erlaubte Ablenker — sehen aus wie Entitäten, sind aber keine:
   {', '.join('{~' + d + '}' for d in sorted(decoys))}
   Ablenker sind SATZTEILE, keine Werte. Schreibe «Erhoben wird {{~amount}}»,
   niemals «Gebühr: {{~amount}}».

5. Erfinde KEINE neuen Platzhalter. Kein {{NAME}}, kein {{ADRESSE}}, kein
   {{DATUM}}. Nur die oben genannten, exakt so geschrieben.

6. Zwei Platzhalter mit demselben Tag dürfen nicht direkt nebeneinander
   stehen. {{GIVENNAME}} {{FULLNAME}} ist gut, {{FULLNAME}} {{FULLNAME}} nicht.

7. Schreibe echtes, idiomatisches {SPRACHNAME[lang]}. Übersetze nicht aus dem
   Deutschen — Wortstellung, Anrede und Formulierung sind sprachabhängig.

7b. Namensreihenfolge: Schreibe Namen abwechselnd natürlich
   ({{GIVENNAME}} {{FULLNAME}}) UND in Register-/Outlook-Reihenfolge
   ({{FULLNAME}} {{GIVENNAME}}). Mailkopfzeilen, Registerauszüge,
   Aktenrubren und Namenslisten setzen den Nachnamen zuerst. Beides muss
   in der Bank vorkommen, sonst lernt das Modell die Stellung statt den
   Namen. Für Formularfelder «Name, Vorname:» gibt es das Makro
   {{@person_feld}}.

7c. Register-, Anwendungs- und Systemnamen sind KEIN {{ORG}}: SAP, Sedex,
   EasyGov, ePortal gehören als Klartext in den Satz.
   {{ORG}} ist eine Stelle, der eine Person zugeordnet werden kann.

8. Länge: 8 bis 25 Zeilen. Realistischer Aufbau des Dokumenttyps, inklusive
   Kopf, Anrede und Abschluss, wo das dazugehört.

AUSGABEFORMAT: ausschliesslich JSON, keine Erklärung, keine Backticks.

{{"templates": [{{"id": "…", "doc_type": "…", "text": "…"}}]}}

Die `id` beginnt mit «{lang}_» und ist kleingeschrieben mit Unterstrichen.
Zeilenumbrüche im `text` als \\n."""


def nutzerauftrag(domaene: str, tags: list[str], anzahl: int) -> str:
    teile = [f"Erzeuge {anzahl} verschiedene Vorlagen für den Dokumenttyp: "
             f"{domaene}."]
    if tags:
        teile.append(
            "Jede Vorlage MUSS diese Platzhalter enthalten: "
            + ", ".join("{" + t + "}" for t in tags) + ".")
    teile.append("Die Vorlagen sollen sich im Satzbau deutlich unterscheiden, "
                 "nicht nur in den Wörtern.")
    return "\n".join(teile)


# ---------------------------------------------------------------------------
# Pruefung
# ---------------------------------------------------------------------------

def pruefe(t: dict, pack, lang: str, tags: list[str]) -> list[str]:
    text = t.get("text", "")
    befunde: list[str] = []
    bekannte_tags, makros, decoys = bekannte_slots(pack)

    if not text.strip():
        return ["leerer Text"]

    # 1. Nur bekannte Slots
    for inhalt in SLOT.findall(text):
        if inhalt.startswith("@"):
            if inhalt[1:].split(":")[0] not in makros:
                befunde.append(f"unbekanntes Makro {{{inhalt}}}")
        elif inhalt.startswith("~"):
            familie = inhalt[1:]
            if familie not in decoys:
                befunde.append(f"unbekannte Ablenkerfamilie {{{inhalt}}}")
            elif lang not in DECOYS[familie]:
                befunde.append(f"{{{inhalt}}} hat keine {lang}-Variante")
        else:
            basis = inhalt.split(":")[0].split("|")[0].split(".")[0]
            if basis not in bekannte_tags:
                befunde.append(f"unbekanntes Tag {{{inhalt}}}")

    # 2. Keine echten Werte — mit dem EIGENEN Erkenner geprueft.
    #    Schlaegt ein Muster auf dem Vorlagentext an, steht dort ein Wert statt
    #    eines Slots. Sprachmodelle tun das staendig, weil ein ausgefuelltes
    #    Beispiel «hilfreicher» aussieht.
    for span in recognize(text):
        wert = text[span.start:span.end]
        if "{" in wert or "}" in wert:
            continue
        befunde.append(f"echter Wert im Text: {span.tag} {wert!r} — "
                       f"gehoert in einen Slot")

    # 3. Verlangte Tags vorhanden
    vorhanden = {i.split(":")[0].split("|")[0].split(".")[0]
                 for i in SLOT.findall(text)}
    fehlend = [t for t in tags if t not in vorhanden]
    if fehlend:
        befunde.append(f"verlangte Tags fehlen: {fehlend}")

    # 4. Die bestehenden Wachen
    befunde.extend(check_template({"id": t.get("id", "?"), "text": text}))
    problem = pruefe_decoy_stellung(text, t.get("id", "?"))
    if problem:
        befunde.append(problem)

    # 5. Laenge
    zeilen = text.strip().splitlines()
    if len(zeilen) < 4:
        befunde.append(f"nur {len(zeilen)} Zeilen — zu kurz fuer ein Dokument")
    if len(zeilen) > 40:
        befunde.append(f"{len(zeilen)} Zeilen — zu lang, das Modell lernt "
                       f"den Rahmen statt der Entitaet")

    return befunde


def hole_json(antwort: str) -> dict:
    """JSON aus der Antwort schaelen. Modelle setzen gern Backticks davor."""
    text = antwort.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < 0:
        raise SystemExit(
            f"Kein JSON in der Antwort ({len(antwort)} Zeichen):\n"
            f"{antwort[:800] if antwort.strip() else '  <leer>'}\n\n"
            f"  Bei leerer Antwort: --roh zeigt, was der Endpunkt wirklich\n"
            f"  geschickt hat. Bei Text ohne JSON: --temperatur 0.3 setzen.")
    try:
        return json.loads(text[a:b + 1])
    except json.JSONDecodeError as fehler:
        raise SystemExit(
            f"JSON unvollstaendig — {fehler}\n"
            f"  Meist abgeschnitten, weil das Token-Budget nicht reichte.\n"
            f"  --max-tokens erhoehen oder --anzahl senken.")


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpunkt", default=VORGABE_ENDPUNKT)
    ap.add_argument("--modell", default=VORGABE_MODELL)
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--lang", default="de", choices=list(SPRACHNAME))
    ap.add_argument("--domaene", default=None,
                    help="Dokumenttyp, z.B. mietvertrag, arbeitszeugnis")
    ap.add_argument("--tags", default="",
                    help="Tags, die vorkommen MUESSEN, kommagetrennt")
    ap.add_argument("--anzahl", type=int, default=3)
    ap.add_argument("--temperatur", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=6000,
                    help="Token-Budget. Modelle mit Denkschritt brauchen "
                         "deutlich mehr, als die Antwort lang ist.")
    ap.add_argument("--roh", action="store_true",
                    help="vollstaendige Antwort des Endpunkts anzeigen")
    ap.add_argument("--out", default=None, help="Zieldatei, YAML")
    ap.add_argument("--trocken", action="store_true",
                    help="nur anzeigen, nichts schreiben")
    ap.add_argument("--probe", action="store_true",
                    help="Endpunkt und Modell pruefen, sonst nichts")
    ap.add_argument("--antwort", default=None,
                    help="Antwort aus Datei lesen statt fragen (zum Pruefen "
                         "der Wachen ohne Endpunkt)")
    args = ap.parse_args()

    pack = load_pack(args.pack)

    if args.probe:
        try:
            with urllib.request.urlopen(f"{args.endpunkt}/models",
                                        timeout=10) as a:
                modelle = json.loads(a.read().decode("utf-8"))
        except urllib.error.URLError as fehler:
            raise SystemExit(f"Nicht erreichbar: {fehler}")
        print(f"Endpunkt {args.endpunkt} antwortet. Modelle:")
        for m in modelle.get("data", []):
            marke = " <- gewaehlt" if m["id"] == args.modell else ""
            print(f"  {m['id']}{marke}")
        # Budget bewusst grosszuegig: bei einem Modell mit Denkschritt geht
        # das meiste dafuer drauf, und eine Probe mit 20 Token schlaegt
        # zuverlaessig fehl, ohne dass man den Grund sieht.
        antwort = frage(args.endpunkt, args.modell,
                        "Antworte kurz und ohne Vorrede.",
                        "Sag: bereit", temperatur=0,
                        max_tokens=args.max_tokens, roh_zeigen=args.roh)
        print(f"\nAntwort auf Testfrage: {antwort.strip()[:200]!r}")
        return 0

    if not args.domaene:
        raise SystemExit("--domaene angeben, z.B. --domaene mietvertrag")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    unbekannt = set(tags) - {t.tag for t in pack.get_tags()}
    if unbekannt:
        raise SystemExit(f"Unbekannte Tags: {sorted(unbekannt)}")

    if args.antwort:
        roh = Path(args.antwort).read_text(encoding="utf-8")
    else:
        print(f"Frage {args.modell} nach {args.anzahl} Vorlagen "
              f"({args.lang}, {args.domaene}) …")
        roh = frage(args.endpunkt, args.modell,
                    systemauftrag(pack, args.lang),
                    nutzerauftrag(args.domaene, tags, args.anzahl),
                    temperatur=args.temperatur,
                    max_tokens=args.max_tokens, roh_zeigen=args.roh)

    daten = hole_json(roh)
    vorlagen = daten.get("templates", [])
    print(f"{len(vorlagen)} Vorlagen erhalten.\n")

    gut, schlecht = [], []
    for t in vorlagen:
        t.setdefault("doc_type", args.domaene)
        t.setdefault("id", f"{args.lang}_{args.domaene}")
        befunde = pruefe(t, pack, args.lang, tags)
        if befunde:
            schlecht.append((t, befunde))
        else:
            gut.append(t)

    for t, befunde in schlecht:
        print(f"--- VERWORFEN {t.get('id')}")
        for b in befunde:
            print(f"    {b}")
        print()

    for t in gut:
        print(f"=== {t['id']} [{args.lang}] " + "=" * 30)
        print(t["text"])
        print()

    print(f"{len(gut)} angenommen, {len(schlecht)} verworfen.")
    if schlecht:
        print("\n  Verworfene Vorlagen sind normal. Ein Sprachmodell setzt "
              "gern\n  echte Werte ein, weil ein ausgefuelltes Beispiel "
              "hilfreicher aussieht.\n  Genau dafuer sind die Wachen da — "
              "einfach nochmal laufen lassen.")

    if args.out and gut and not args.trocken:
        ziel = Path(args.out)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        bestehend = []
        if ziel.is_file():
            alt = yaml.safe_load(ziel.read_text(encoding="utf-8")) or {}
            bestehend = alt.get("templates", [])
        # Kennungen eindeutig machen
        belegt = {t["id"] for t in bestehend}
        for i, t in enumerate(gut, 1):
            basis = t["id"]
            n = i
            while t["id"] in belegt:
                t["id"] = f"{basis}_{n:02d}"
                n += 1
            belegt.add(t["id"])
        ziel.write_text(
            "# Erzeugt mit tools/generate_templates.py.\n"
            "# Jede Vorlage hat die Wachen bestanden — VOR dem Training\n"
            "# trotzdem lesen. Die Wachen pruefen die Form, nicht den Sinn.\n\n"
            + yaml.safe_dump({"templates": bestehend + gut},
                             allow_unicode=True, sort_keys=False,
                             default_flow_style=False, width=100),
            encoding="utf-8")
        print(f"\n-> {ziel} ({len(bestehend) + len(gut)} Vorlagen)")
        print("   Vor dem Training LESEN. Die Wachen pruefen die Form, "
              "nicht den Sinn.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
