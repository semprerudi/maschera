#!/usr/bin/env python3
"""Baut die Nomenklaturen aus offiziellen Quellen (SPEC §6, §12 Falle 3).

Grundsatz: **Bauplan verteilen, nicht Daten.** Dieses Skript wird versioniert,
`raw/` und `dist/` stehen in `.gitignore`. Wer den Pack klont, baut sich die
Listen selbst — damit stellt sich die Frage nicht, ob Bundesdaten weiterverteilt
werden dürfen.

    python3 packs/ch/nomenclatures/build.py --list      # Quellen anzeigen
    python3 packs/ch/nomenclatures/build.py --fetch     # herunterladen
    python3 packs/ch/nomenclatures/build.py --build     # normalisieren
    python3 packs/ch/nomenclatures/build.py --verify    # dist/ prüfen

Die Downloads laufen auf der Arbeitsmaschine, nicht in der
Entwicklungsumgebung.
Fehlt eine Quelle, baut `--build` die übrigen und meldet die Lücke.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
DIST = HERE / "dist"

# Unterstrich am Anfang = KEINE Nomenklatur. `_fingerabdruck.json` liegt
# im selben Verzeichnis und traegt `gebaut`/`werte` statt `meta`/`entries`.
# Wer `dist/*.json` pauschal nimmt, stuerzt darueber mit
# `KeyError: 'entries'`.
FINGERABDRUCK = DIST / "_fingerabdruck.json"


def nomenklaturdateien(verzeichnis: Path | None = None) -> list[Path]:
    """Die echten Nomenklaturen in `dist/`. Ohne Dateien mit Unterstrich.

    Die eine Stelle, an der diese Konvention steht. Wer `dist/` durchgeht,
    ruft das hier — nicht `glob("*.json")`.
    """
    d = verzeichnis or DIST
    if not d.is_dir():
        return []
    return sorted(x for x in d.glob("*.json") if not x.name.startswith("_"))


@dataclass(frozen=True)
class Source:
    key: str
    tag: str
    title: str
    url: str
    filename: str
    licence: str
    note: str = ""

    @property
    def files(self) -> list[str]:
        """Einzelne Dateinamen. Eine Quelle kann aus mehreren bestehen."""
        return [f.strip() for f in self.filename.split("+")]

    def present(self) -> bool:
        """Vorhanden, sobald MINDESTENS eine der Dateien da ist.

        Bei den Vornamen sind es zwei Tabellen (maennlich, weiblich); eine
        davon allein ist bereits brauchbar, nur aermer.
        """
        return any((RAW / f).exists() for f in self.files)


# -----------------------------------------------------------------------------
# Quellen. URLs ändern sich — bei 404 auf der Portalseite nachschlagen, nicht
# raten. Alle vier sind offene Verwaltungsdaten ohne Registrierung.
# -----------------------------------------------------------------------------

SOURCES = [
    # HINWEIS: Ein eigenes Gemeindeverzeichnis ist NICHT noetig. Die CSV im
    # Ortschaftenverzeichnis (PLZO_CSV_LV95.csv) fuehrt Gemeindename und
    # BFS-Nummer bereits mit. Eine Quelle weniger zu pflegen.
    Source(
        key="ortschaften",
        tag="CITY / ZIPCODE",
        title="Amtliches Ortschaftenverzeichnis mit PLZ",
        url="https://www.swisstopo.admin.ch/de/amtliches-ortschaftenverzeichnis",
        filename="ortschaften.csv",
        licence="swisstopo, frei mit Quellenangabe",
        note=("ZIP herunterladen, darin PLZO_CSV_LV95.csv -> ortschaften.csv "
              "umbenennen. Fuehrt auch Gemeindename und BFS-Nr."),
    ),
    Source(
        key="strassen",
        tag="STREET",
        title="Amtliches Strassenverzeichnis der Schweiz",
        url="https://www.swisstopo.admin.ch/de/amtliche-geografische-verzeichnisse",
        filename="strassen.csv",
        licence="swisstopo, frei mit Quellenangabe",
        note="Alle Strassen, Wege, Gassen, Plaetze. Speist STREET viersprachig.",
    ),
    Source(
        key="heimatorte",
        tag="PLACE_OF_ORIGIN",
        title="Aktuelle Liste der Heimatorte (XML nach eCH-0135)",
        # ACHTUNG: ech.ch fuehrt nur den STANDARD (PDF + XSD), nicht die Daten.
        # Die tatsaechliche Liste liegt beim Bundesamt fuer Justiz:
        url="https://www.e-service.admin.ch/competency-app/wicket/bookmarkable/"
            "ch.glue.suis.competency.app.pages.CivilRegistryLinks",
        filename="heimatorte.xml",
        licence="frei verwendbar (BJ/EJPD)",
        note="Status quo, ~2x jaehrlich neu. Historische Namensformen enthalten.",
    ),
    Source(
        key="nachnamen",
        tag="FULLNAME",
        title="Nachnamen der staendigen Wohnbevoelkerung nach SPRACHREGION",
        url="https://opendata.swiss/de/dataset/"
            "nachnamen-der-standigen-wohnbevolkerung-nach-sprachregion1",
        filename="nachnamen.csv",
        licence="frei mit Quellenangabe (BFS Open Government Data)",
        note=("Sprachregion, NICHT Gemeinde — siehe build_nachnamen. "
              "Mehrfachzeilen je Name werden aufsummiert."),
    ),
    Source(
        key="vornamen",
        tag="GIVENNAME",
        title="Vornamen der Wohnbevoelkerung (BFS, m + w)",
        url="https://www.data.bfs.admin.ch",
        filename="vornamen_m.csv + vornamen_f.csv",
        licence="frei mit Quellenangabe (BFS Open Government Data)",
        note=("Zwei Tabellen, maennlich und weiblich. vornamen.opendata.ch ist "
              "nur eine Suchmaske ohne Download."),
    ),
    Source(
        key="zefix",
        tag="ORG",
        title="Zefix Handelsregister über LINDAS",
        url="https://lindas.admin.ch/query",
        filename="zefix.csv",
        licence="OFFEN — Klärung ausstehend (offener Punkt 4)",
        note="SPARQL. Bis zur Klärung baut --build synthetische Firmennamen.",
    ),
]


# -----------------------------------------------------------------------------
# Normalisierung
# -----------------------------------------------------------------------------

def norm(value: str) -> str:
    """Unicode NFC, Randleerzeichen weg, innere Leerzeichen vereinheitlicht."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def sortkey(value: str) -> str:
    """Diakritikafreier Sortierschlüssel — Zürich und Zurich landen zusammen."""
    d = unicodedata.normalize("NFD", value.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def write(name: str, entries: list, meta: dict) -> Path:
    """Eine Nomenklatur als JSON ablegen. Sortiert = reproduzierbar.

    `entries` sind entweder Zeichenketten oder Datensaetze (dict) mit
    mindestens dem Schluessel `name`.
    """
    if entries and isinstance(entries[0], dict):
        seen: dict[tuple, dict] = {}
        for e in entries:
            rec = {**e, "name": norm(e["name"])}
            if rec["name"]:
                seen[tuple(sorted(rec.items()))] = rec
        unique = sorted(seen.values(), key=lambda r: (sortkey(r["name"]), r["name"]))
        DIST.mkdir(parents=True, exist_ok=True)
        path = DIST / f"{name}.json"
        path.write_text(
            json.dumps({"meta": {**meta, "count": len(unique)},
                        "entries": unique}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        return path

    unique = sorted({norm(e) for e in entries if norm(e)}, key=sortkey)
    DIST.mkdir(parents=True, exist_ok=True)
    path = DIST / f"{name}.json"
    path.write_text(
        json.dumps(
            {"meta": {**meta, "count": len(unique)}, "entries": unique},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return path


def read_csv_column(path: Path, candidates: list[str]) -> list[str]:
    """Erste passende Spalte lesen. Trennzeichen und Kodierung werden geraten."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f"{path.name}: Kodierung nicht erkannt")

    sample = raw[:4096]
    delim = max(";,\t", key=lambda d: sample.count(d))
    rows = list(csv.DictReader(raw.splitlines(), delimiter=delim))
    if not rows:
        raise SystemExit(f"{path.name}: keine Datenzeilen")

    fields = {f.lower().strip(): f for f in rows[0] if f}
    for cand in candidates:
        if cand.lower() in fields:
            return [r[fields[cand.lower()]] or "" for r in rows]
    raise SystemExit(
        f"{path.name}: keine der Spalten {candidates} gefunden. "
        f"Vorhanden: {sorted(fields.values())}"
    )


# -----------------------------------------------------------------------------
# Erbauer je Quelle
# -----------------------------------------------------------------------------

def build_ortschaften() -> tuple[str, list[dict], dict] | None:
    """Ortschaften MIT PLZ als Paar.

    Der Injektor muss PLZ und Ort zusammen ziehen koennen, sonst entstehen
    Adressen wie "Marktgasse 12, 6900 Bern". Das Modell lernt daraus, dass die
    beiden nichts miteinander zu tun haben — und genau diese Kopplung ist der
    einzige Anker des ZIPCODE-Recognizers.
    """
    path = RAW / "ortschaften.csv"
    if not path.exists():
        return None
    names = read_csv_column(path, ["Ortschaftsname", "ORTNAME", "Ortschaft", "Name"])
    try:
        plz = read_csv_column(path, ["PLZ", "PLZ4", "Postleitzahl", "NPA", "ZIP"])
    except SystemExit:
        plz = [""] * len(names)
    records = [{"name": n, "plz": p.strip()} for n, p in zip(names, plz) if n]

    # Wache gegen verschmolzene Zeilen: traegt ein CSV-Feld einen
    # Zeilenumbruch oder ist ein Anfuehrungszeichen unpaarig, haengt der Leser
    # mehrere Zeilen zusammen, und es entstehen Werte wie «Solothurn, 4528
    # Zuchwil, 4562 Biberist» in einer einzigen CITY-Spanne.
    #
    # Ein Ortsname enthaelt nie eine Ziffer und nie ein Komma gefolgt von
    # einer Ziffer. «Sta. Maria Val Müstair» und «Heiligkreuz (Mels)» sind
    # gueltig, «Mels, 8888 Heiligkreuz (Mels)» nicht.
    kaputt = [r for r in records
              if re.search(r",\s*\d", r["name"]) or "\n" in r["name"]]
    if kaputt:
        raise SystemExit(
            f"ABBRUCH: {len(kaputt)} Ortsnamen enthalten mehrere Eintraege, "
            f"z.B. {kaputt[0]['name']!r}.\n"
            f"Das CSV wurde zeilenweise falsch gelesen — meist ein "
            f"Zeilenumbruch oder ein unpaariges Anfuehrungszeichen im Feld.\n"
            f"Betroffene Datei: {path}"
        )
    return "ortschaften", records, {"source": "swisstopo", "tag": "CITY"}


def build_heimatorte() -> tuple[str, list[dict], dict] | None:
    """eCH-0135 vom BJ. Schema gegen die echte Datei verifiziert (4335 Eintraege).

    Struktur:
        placeOfOriginNomenclature / placeOfOrigins / placeOfOrigin
            placeOfOriginId        Kennung, gruppiert Namensformen
            placeOfOriginName      der Name
            cantonAbbreviation     immer gesetzt
            validFrom / validTo    Gueltigkeit, optional
            historyMunicipalityId  historisierte BFS-Nummer, optional
            successorId            Nachfolger bei Fusion, optional

    Die Datei ist **kumulativ**, nicht nur eine Auslieferung des Aktuellen: sie
    zeigt den Status quo der Heimatortslandschaft in dem Sinn, dass fuer JEDEN
    je gefuehrten Heimatort drinsteht, ob er heute gilt oder nicht. Ungueltige
    behalten ein validTo und tragen ausnahmslos eine successorId. Aeltestes
    validTo in der Ausgabe vom August 2026: 1928.

    Praktische Folge fuer den Bauplan: Der Umfang waechst monoton. Ein spaeterer
    Bezug darf NICHT kleiner sein als ein frueherer — schrumpft die Zahl, ist
    etwas beim Download schiefgegangen, nicht in der Quelle. --verify prueft das.

    **Historisierte Namen werden bewusst BEHALTEN.** Rund ein Drittel der
    Eintraege traegt ein validTo — "Aeugst" wurde 1976 zu "Aeugst am Albis".
    Genau die alten Formen stehen in alten Dokumenten, und alte Dokumente sind
    der Anwendungsfall. Ein Verzeichnis nur mit aktuellen Namen wuerde das
    Modell auf Heimatorten blind machen, die es am haeufigsten sieht.
    """
    path = RAW / "heimatorte.xml"
    if not path.exists():
        return None
    import xml.etree.ElementTree as ET

    NS = "{http://www.ech.ch/xmlns/eCH-0135/1}"
    root = ET.parse(path).getroot()

    def text(el, tag):
        found = el.find(f"{NS}{tag}")
        return found.text if found is not None else None

    records = []
    for el in root.iter(f"{NS}placeOfOrigin"):
        name = text(el, "placeOfOriginName")
        if not name:
            continue
        records.append({
            "name": name,
            "canton": text(el, "cantonAbbreviation"),
            # Fuer die Templategenerierung: die uebliche Schreibweise im
            # Dokument ist "Hautemorges VD", nicht "Hautemorges".
            "written": f"{name} {text(el, 'cantonAbbreviation')}".strip(),
            "historical": text(el, "validTo") is not None,
        })

    if not records:
        tags = sorted({e.tag.rsplit("}", 1)[-1] for e in root.iter()})[:25]
        raise SystemExit(
            f"heimatorte.xml: kein placeOfOrigin gefunden. Elemente: {tags}"
        )
    return "heimatorte", records, {
        "source": "BJ, eCH-0135",
        "tag": "PLACE_OF_ORIGIN",
        "hinweis": "historisierte Namen absichtlich enthalten",
    }


def _read_name_weight(path: Path, name_cols: list[str]) -> list[dict]:
    """Namensspalte plus optionale Haeufigkeitsspalte lesen."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f"{path.name}: Kodierung nicht erkannt")

    delim = max(";,\t", key=lambda d: raw[:4096].count(d))
    rows = list(csv.DictReader(raw.splitlines(), delimiter=delim))
    if not rows:
        raise SystemExit(f"{path.name}: keine Datenzeilen")

    fields = {f.lower().strip(): f for f in rows[0] if f}
    name_col = next((fields[c.lower()] for c in name_cols if c.lower() in fields), None)
    if not name_col:
        raise SystemExit(
            f"{path.name}: keine der Spalten {name_cols} gefunden. "
            f"Vorhanden: {sorted(fields.values())}"
        )
    weight_col = next(
        (fields[c] for c in ("anzahl", "count", "nombre", "numero", "wert",
                             "value", "haeufigkeit", "häufigkeit", "total")
         if c in fields),
        None,
    )

    # Nur den juengsten Erhebungszeitpunkt behalten. Die BFS-Exporte tragen eine
    # Spalte TIME_PERIOD; enthaelt die Datei mehrere Jahrgaenge, wuerde das
    # Aufsummieren dieselbe Person mehrfach zaehlen und die Gewichte verfaelschen.
    period_col = next(
        (fields[c] for c in ("time_period", "jahr", "year", "annee", "anno",
                             "periode", "period")
         if c in fields),
        None,
    )
    if period_col:
        periods = {(r.get(period_col) or "").strip() for r in rows}
        periods.discard("")
        if len(periods) > 1:
            newest = max(periods)
            rows = [r for r in rows if (r.get(period_col) or "").strip() == newest]
            print(f"    {path.name}: {len(periods)} Jahrgaenge, nur {newest} verwendet")

    # Mehrfachzeilen je Name aufsummieren. Die BFS-Tabellen fuehren einen Namen
    # einmal pro Sprachregion bzw. pro Geburtsjahrgang; gebraucht wird die
    # Gesamthaeufigkeit ueber alle Zeilen desselben Namens.
    totals: dict[str, int] = {}
    for r in rows:
        name = (r.get(name_col) or "").strip()
        if not name:
            continue
        weight = 1
        if weight_col:
            raw_w = (r.get(weight_col) or "1").replace("'", "").replace("\u2019", "")
            raw_w = raw_w.replace(" ", "").replace("\u00a0", "")
            try:
                weight = max(1, int(float(raw_w)))
            except ValueError:
                weight = 1
        totals[name] = totals.get(name, 0) + weight
    return [{"name": n, "weight": w} for n, w in totals.items()]


def build_nachnamen() -> tuple[str, list[dict], dict] | None:
    """Nachnamen aus der BFS-Statistik der staendigen Wohnbevoelkerung.

    **Warum die gesamtschweizerische Tabelle und nicht die nach Gemeinde:**
    Ein seltener Name plus eine kleine Gemeinde ist selbst ein Personendatum.
    "Der einzige Traeger dieses Namens in einer Kleinstgemeinde" identifiziert
    eine Person, auch wenn in der Zeile kein Vorname steht. Fuer die
    Templategenerierung ist die Gemeindeaufteilung ohnehin wertlos — gebraucht wird die Namensvielfalt,
    nicht ihre geografische Verteilung. Also die Aggregatstabelle nehmen.

    **Warum Vielfalt hier kein Komfortmerkmal ist:** Die staendige Wohnbevoel-
    kerung traegt portugiesische, tuerkische, tamilische, albanische, italienische
    Namen. Ein Templateset nur mit Mueller, Meier und Schmid erzeugt ein Modell,
    das auf "Ferreira da Silva" oder "Rajasingam" schlechter anschlaegt als auf
    "Zimmermann". Die Folge waere nicht bloss schlechterer Recall, sondern ein
    Filter, der fremd klingende Namen haeufiger ans Frontier-Modell durchlaesst
    als deutschschweizerische. Das ist eine Diskriminierung im Ergebnis, egal wie
    unbeabsichtigt. Deshalb ist die vollstaendige Liste inklusive seltener Namen
    Pflicht, nicht Kuer.

    Die Haeufigkeit wandert als `weight` mit: der Generator soll haeufige Namen
    haeufiger einsetzen, damit die Verteilung realistisch bleibt — aber jeder
    Name muss vorkommen koennen.
    """
    path = RAW / "nachnamen.csv"
    if not path.exists():
        return None
    records = _read_name_weight(
        path,
        # LASTNAME ist der tatsaechliche Spaltenname im BFS-Export.
        ["LASTNAME", "Nachname", "Name", "Familienname", "Nom", "Cognome",
         "Last name"],
    )
    return "nachnamen", records, {"source": "BFS 2023", "tag": "FULLNAME"}


def build_vornamen() -> tuple[str, list[dict], dict] | None:
    """Vornamen aus den BFS-Tabellen. Maennlich und weiblich getrennt publiziert.

    Akzeptiert `vornamen.csv` (eine Datei) ODER `vornamen_m.csv` +
    `vornamen_f.csv`. Beim Zusammenfuehren wird das Geschlecht bewusst
    VERWORFEN: fuer die Namenserkennung ist es unerheblich, und das Modell soll
    keinen Zusammenhang zwischen Vorname und Geschlecht lernen.
    """
    candidates = [RAW / n for n in
                  ("vornamen.csv", "vornamen_m.csv", "vornamen_f.csv")]
    present = [p for p in candidates if p.exists()]
    if not present:
        return None
    # firstname ist der tatsaechliche Spaltenname im BFS-Export.
    cols = ["firstname", "Vorname", "Name", "Prénom", "Prenom", "Nome",
            "First name"]
    totals: dict[str, int] = {}
    for path in present:
        for r in _read_name_weight(path, cols):
            totals[r["name"]] = totals.get(r["name"], 0) + r["weight"]
    records = [{"name": n, "weight": w} for n, w in totals.items()]
    return "vornamen", records, {
        "source": "BFS",
        "tag": "GIVENNAME",
        "dateien": [p.name for p in present],
    }


# Firmennamen kombinatorisch, solange die Zefix-Lizenz offen ist. Kein Ersatz
# für echte Namen, aber genug Formvielfalt, damit das Modell die Struktur lernt.
_ORG_FORMS = ["AG", "GmbH", "SA", "Sàrl", "Sagl", "Genossenschaft", "Stiftung",
              "& Co.", "Holding AG", "Group AG"]
_ORG_STEMS = ["Alpin", "Aare", "Belmont", "Cordier", "Dufour", "Engadin",
              "Furka", "Gotthard", "Helvetia", "Jura", "Kappeler", "Limmat",
              "Matter", "Nidwald", "Oberland", "Pilatus", "Quadri", "Reuss",
              "Säntis", "Ticino", "Uetli", "Vallée", "Wyler", "Zähringer"]
_ORG_KINDS = ["Bau", "Treuhand", "Immobilien", "Transport", "Consulting",
              "Elektro", "Garage", "Logistik", "Pharma", "Textil", "Energie"]


def build_zefix() -> tuple[str, list[str], dict]:
    path = RAW / "zefix.csv"
    if path.exists():
        names = read_csv_column(path, ["name", "Firmenname", "companyName"])
        return "organisationen", names, {"source": "Zefix/LINDAS", "tag": "ORG"}

    names = [
        f"{stem} {kind} {form}"
        for stem in _ORG_STEMS
        for kind in _ORG_KINDS
        for form in _ORG_FORMS
    ] + [f"{stem} {form}" for stem in _ORG_STEMS for form in _ORG_FORMS]
    return "organisationen", names, {
        "source": "synthetisch",
        "tag": "ORG",
        "warnung": "Platzhalter bis zur Klaerung der Zefix-Lizenz",
    }


def build_strassen() -> tuple[str, list[dict], dict] | None:
    """Strassen MIT Ort und PLZ.

    Strassennamen sind ortsfest. Zieht man Strasse und Ort unabhaengig, entsteht
    "Rue des Sorbiers 108, 7543 Lavin" — eine franzoesische Strasse im
    Unterengadin. Das Verzeichnis fuehrt ZIP_LABEL und COM_NAME bereits mit;
    die Kopplung kostet nichts ausser dem Mitlesen zweier Spalten.
    """
    path = RAW / "strassen.csv"
    if not path.exists():
        return None
    names = read_csv_column(path, ["Strassenname", "STN_LABEL", "Strasse", "Name"])
    try:
        plz = read_csv_column(path, ["ZIP_LABEL", "PLZ", "PLZ4"])
    except SystemExit:
        plz = [""] * len(names)
    try:
        ort = read_csv_column(path, ["COM_NAME", "Gemeindename", "Ort"])
    except SystemExit:
        ort = [""] * len(names)
    # ZIP_LABEL ist "6809 Medeglia", also PLZ UND Ortschaft in einem Feld.
    # COM_NAME ist die politische Gemeinde ("Monteceneri"). In einer Schweizer
    # Adresse steht die POSTALISCHE Ortschaft: "8844 Euthal", nicht
    # "8844 Einsiedeln". Also aus ZIP_LABEL beides herausloesen und COM_NAME
    # nur als Zusatzangabe mitfuehren.
    #
    # ZIP_LABEL kann MEHRERE Paare tragen — eine Strasse, die ueber
    # Gemeindegrenzen laeuft, steht dort als
    #
    #     "4500 Solothurn, 4528 Zuchwil, 4562 Biberist"
    #
    # Die erste PLZ und den ganzen Rest als Ortsnamen zu nehmen, lehrte das
    # Modell, dass ein Ortsname beliebig lang sein und Ziffern enthalten kann.
    # Richtig ist ein Datensatz JE PAAR: die Strasse existiert tatsaechlich in
    # allen genannten Ortschaften.
    paare = re.compile(r"(\d{4})\s+([^,;]+?)(?=\s*[,;]\s*\d{4}|\s*$)")
    records = []
    for n, z, o in zip(names, plz, ort):
        if not n:
            continue
        treffer = paare.findall(z or "")
        if not treffer:
            treffer = [((z or "").strip(), (o or "").strip())]
        for postleitzahl, ortschaft in treffer:
            records.append({
                "name": n,
                "plz": postleitzahl.strip(),
                "city": ortschaft.strip(),
                "municipality": (o or "").strip(),
            })

    # Dieselbe Wache wie bei den Ortschaften: ein Ortsname enthaelt nie ein
    # Komma gefolgt von einer Ziffer.
    kaputt = [r for r in records if re.search(r",\s*\d", r["city"])]
    if kaputt:
        raise SystemExit(
            f"ABBRUCH: {len(kaputt)} Strassen tragen mehrere Ortschaften in "
            f"einem city-Feld, z.B. {kaputt[0]['city']!r}. ZIP_LABEL wurde "
            f"nicht sauber zerlegt.")
    return "strassen", records, {"source": "swisstopo", "tag": "STREET"}


# ---------------------------------------------------------------------------
# Behoerdennamen — viersprachig, kombinatorisch
# ---------------------------------------------------------------------------
# `ORG` speist sich aus **Zefix**, dem Handelsregister — und Schweizer
# Behoerden stehen nicht im Handelsregister. Ohne diese Liste haette das
# Modell Namen wie `Ufficio dello stato civile`, `Repubblica e Cantone
# Ticino`, `Dipartimento delle Istituzioni` oder `Einwohnergemeinde` nie
# gesehen, obwohl Post von Behoerden in vielen Dokumenten vorkommt —
# bei Privaten und Firmen genauso wie in Verwaltungen.
#
# Warum das ein Personendatum sein kann: bei einer kleinen Stelle verraet
# der Name mehr als der Vorgang — dasselbe Argument wie bei
# `HEALTHCARE_ORG`.
#
# Keine feste Liste noetig: Behoerdennamen sind regelmaessig gebaut, anders
# als Firmennamen. Kopf + Sachgebiet.

# Das Sachgebiet traegt die Praeposition SAMT ARTIKEL: «Ufficio federale
# della sanità», nicht «di sanità». Artikelkongruenz ist nicht einsetzbar
# (SPEC §9).
_BEH_BUND = {
    "de": ["Bundesamt {}", "Staatssekretariat {}",
           "Eidgenössisches Departement {}"],
    "fr": ["Office fédéral {}", "Secrétariat d'État {}",
           "Département fédéral {}"],
    "it": ["Ufficio federale {}", "Segreteria di Stato {}",
           "Dipartimento federale {}"],
    "en": ["Federal Office {}", "Federal Department {}"],
}
_BEH_SACH = {
    "de": ["für Justiz", "für Polizei", "für Statistik", "für Migration",
           "für Gesundheit", "für Sozialversicherungen",
           "für Landestopografie", "für Umwelt", "für Kultur",
           "für Energie", "für Verkehr", "für Wohnungswesen",
           "für Zivildienst"],
    "fr": ["de la justice", "de la police", "de la statistique",
           "des migrations", "de la santé publique",
           "des assurances sociales", "de la culture",
           "de l'environnement", "de l'énergie", "des transports"],
    "it": ["di giustizia", "di polizia", "di statistica",
           "della migrazione", "della sanità pubblica",
           "delle assicurazioni sociali", "della cultura",
           "dell'ambiente", "dell'energia", "dei trasporti"],
    "en": ["of Justice", "of Police", "of Statistics", "of Migration",
           "of Public Health", "of Culture", "of Energy", "of Transport"],
}
# Kantonale und kommunale Stellen — hier steckt das eigentliche Personendatum,
# weil die Stelle klein ist.
_BEH_AMT = {
    "de": ["Zivilstandsamt", "Betreibungsamt", "Grundbuchamt", "Steueramt",
           "Migrationsamt", "Einwohnerdienste", "Einwohnergemeinde",
           "Gemeindeverwaltung", "Sozialdienst", "Kindes- und "
           "Erwachsenenschutzbehörde", "Regionalgericht", "Bezirksgericht",
           "Kreisbüro", "Amt für Migration", "Amt für Wirtschaft"],
    "fr": ["Office de l'état civil", "Office des poursuites",
           "Registre foncier", "Service des contributions",
           "Service de la population", "Contrôle des habitants",
           "Administration communale", "Service social",
           "Autorité de protection de l'enfant et de l'adulte"],
    "it": ["Ufficio dello stato civile", "Ufficio esecuzione e fallimenti",
           "Registro fondiario", "Ufficio delle contribuzioni",
           "Sezione della popolazione", "Controllo abitanti",
           "Amministrazione comunale", "Servizio sociale",
           "Dipartimento delle istituzioni", "Dipartimento istituzioni"],
    "en": ["Civil Registry Office", "Debt Enforcement Office",
           "Land Registry", "Tax Administration", "Residents' Registration"],
}
# Nur die AMTLICHEN Doppelformen. «Kanton Bern» allein ist Kontext, kein
# Organisationsname — dieselbe Ueberlegung, mit der `ORG_BEHOERDE_KANTON`
# schon im Muster auf diese Formen beschraenkt ist. «Staatskanzlei des
# Kantons Aargau» faellt aus demselben Grund weg wie «Betreibungsamt Bern»:
# Der Ort gehoert in einen eigenen Slot.
_BEH_KANTON = {
    "de": ["Republik und Kanton {}", "Staat und Kanton {}"],
    "fr": ["République et Canton de {}"],
    "it": ["Repubblica e Cantone {}"],
    "en": [],
}
# Kantonsnamen sind NICHT dieselbe Liste wie Ortsnamen: «Repubblica e Cantone
# Ticino» — Ticino ist kein Ort im Ortschaftenverzeichnis.
_BEH_KANTONSNAMEN = {
    "de": ["Bern", "Zürich", "Wallis", "Tessin", "Graubünden", "Aargau",
           "Luzern", "Freiburg", "Solothurn", "Thurgau", "Waadt", "Genf"],
    "fr": ["Vaud", "Genève", "Fribourg", "Valais", "Neuchâtel", "Jura",
           "Berne"],
    "it": ["Ticino", "Grigioni", "Vallese", "Berna"],
    "en": ["Bern", "Zurich", "Ticino", "Valais", "Geneva"],
}


def build_behoerden() -> tuple[str, list[str], dict]:
    # Format ORG|lang|name. Ohne Sprachtrennung stuende «Land Registry Bern»
    # in einem italienischen Dokument.
    namen: list[str] = []
    for sprache in ("de", "fr", "it", "en"):
        eintraege: list[str] = []
        for muster in _BEH_BUND[sprache]:
            for sach in _BEH_SACH[sprache]:
                eintraege.append(muster.format(sach))
        # **Ohne Ortsnamen.** Das Behoerdenmuster erkennt «Betreibungsamt», nicht
        # «Betreibungsamt Bern». Truegen die Nomenklaturwerte den Ort mit, waere
        # jeder davon im Training eine Spanne, die das Muster nur zur Haelfte
        # trifft — ein Teiltreffer und ein Precision-Verlust je Wert.
        #
        # Der Ortsname gehoert in einen eigenen `{CITY}`-Slot. Am Schutz aendert
        # das nichts — beide Tags maskieren —, aber Muster, Nomenklatur und
        # Vorlagen sagen dasselbe.
        for amt in _BEH_AMT[sprache]:
            eintraege.append(amt)
        for muster in _BEH_KANTON[sprache]:
            for kanton in _BEH_KANTONSNAMEN[sprache]:
                eintraege.append(muster.format(kanton))
        namen.extend(f"ORG|{sprache}|{e}" for e in eintraege)
    namen = sorted(dict.fromkeys(namen))
    return "behoerden", namen, {
        "source": "kombinatorisch",
        "tag": "ORG",
        "hinweis": "Behoerdennamen fehlen in Zefix",
    }


# ---------------------------------------------------------------------------
# Geschlossene Wertlisten aus dem Amtlichen Katalog der Merkmale (BFS)
# ---------------------------------------------------------------------------
# Quelle: «Die Harmonisierung amtlicher Personenregister — Amtlicher Katalog
# der Merkmale», BFS. Die deutschen Wortlaute sind woertlich uebernommen.
#
# Ein Modell, das «in eingetragener Partnerschaft» und «aufgelöste
# Partnerschaft» nie gesehen hat, erkennt sie nicht; und `nubile` oder
# `célibataire` schon gar nicht. Deshalb die vollstaendigen Listen in allen
# Sprachen.
#
# ⚠️ DE ist woertlich aus dem Katalog. FR und IT sind die amtlichen
# Entsprechungen aus dem Amtsgebrauch und **gehoeren gegengelesen**.
# Genau die Falle aus SPEC §9: uebersetztes Deutsch ist kein Franzoesisch.

_MERKMALE: dict[str, dict[str, list[str]]] = {
    # 341 Zivilstand — sieben Auspraegungen, nicht vier.
    "MARITALSTATUS": {
        "de": ["ledig", "verheiratet", "verwitwet", "geschieden",
               "unverheiratet", "in eingetragener Partnerschaft",
               "aufgelöste Partnerschaft", "gerichtlich getrennt",
               "freiwillig getrennt"],
        "fr": ["célibataire", "marié", "mariée", "veuf", "veuve", "divorcé",
               "divorcée", "non marié", "non mariée", "lié par un partenariat "
               "enregistré", "partenariat dissous", "séparé judiciairement"],
        "it": ["celibe", "nubile", "coniugato", "coniugata", "vedovo",
               "vedova", "divorziato", "divorziata", "non coniugato",
               "in unione domestica registrata", "unione domestica sciolta",
               "separato giudizialmente"],
        "en": ["single", "married", "widowed", "divorced",
               "in a registered partnership", "dissolved partnership"],
    },
    # 33 Geschlecht
    "SEX": {
        "de": ["männlich", "weiblich", "m", "w"],
        "fr": ["masculin", "féminin", "m", "f"],
        "it": ["maschile", "femminile", "m", "f"],
        "en": ["male", "female", "m", "f"],
    },
    # 71 Konfessionszugehoerigkeit — die amtlichen Bezeichnungen.
    "RELIGION": {
        "de": ["evangelisch-reformiert", "Evangelisch-Reformierte Kirche",
               "protestantisch", "römisch-katholisch",
               "Römisch-katholische Kirche", "christkatholisch",
               "Christkatholische Kirche", "altkatholisch",
               "israelitische Gemeinschaft", "jüdische Glaubensgemeinschaft",
               "konfessionslos", "ohne Konfession"],
        "fr": ["évangélique réformée", "Église évangélique réformée",
               "protestante", "catholique romaine", "Église catholique "
               "romaine", "catholique chrétienne", "communauté israélite",
               "sans confession", "sans appartenance religieuse"],
        "it": ["evangelica riformata", "Chiesa evangelica riformata",
               "protestante", "cattolica romana", "Chiesa cattolica romana",
               "cattolica cristiana", "comunità israelitica",
               "senza confessione"],
        "en": ["Protestant Reformed", "Roman Catholic", "Christian Catholic",
               "Jewish community", "no religious affiliation"],
    },
    # 52 Meldeverhaeltnis
    "RESIDENCE_STATUS": {
        "de": ["Niederlassung", "Aufenthalt", "Hauptwohnsitz",
               "Nebenwohnsitz", "niedergelassen", "Wochenaufenthalt"],
        "fr": ["établissement", "séjour", "domicile principal",
               "domicile secondaire", "résidence principale",
               "résidence secondaire"],
        "it": ["domicilio", "dimora", "domicilio principale",
               "domicilio secondario", "residenza principale"],
        "en": ["permanent residence", "temporary residence",
               "main residence", "secondary residence"],
    },
    # 72 Stimm- und Wahlrecht
    "VOTING_RIGHTS": {
        "de": ["stimmberechtigt", "nicht stimmberechtigt",
               "stimm- und wahlberechtigt", "passives Wahlrecht",
               "Stimmrecht auf Bundesebene", "Stimmrecht auf Kantonsebene",
               "Stimmrecht auf Gemeindeebene"],
        "fr": ["ayant droit de vote", "sans droit de vote",
               "droit de vote et d'éligibilité", "éligibilité",
               "droit de vote au niveau fédéral",
               "droit de vote au niveau communal"],
        "it": ["avente diritto di voto", "senza diritto di voto",
               "diritto di voto ed eleggibilità", "eleggibilità",
               "diritto di voto a livello federale"],
        "en": ["entitled to vote", "not entitled to vote", "eligibility"],
    },
    # 41 Staatsangehoerigkeiten, je Sprache — «Cittadinanza: portugiesisch»
    # waere eine Sprachmischung.
    #
    # Bewusst die HAEUFIGSTEN Staatsangehoerigkeiten der staendigen
    # Wohnbevoelkerung — Vielfalt ist hier kein Komfortmerkmal, sondern
    # dasselbe Fairness-Argument wie bei den Nachnamen.
    "NATIONALITY": {
        "de": ["Schweiz", "Deutschland", "Italien", "Portugal", "Frankreich",
               "Kosovo", "Spanien", "Türkei", "Nordmazedonien", "Serbien",
               "Österreich", "Sri Lanka", "Brasilien", "Eritrea", "Polen",
               "Vereinigtes Königreich", "Bosnien und Herzegowina",
               "schweizerisch", "deutsch", "italienisch", "portugiesisch"],
        "fr": ["Suisse", "Allemagne", "Italie", "Portugal", "France",
               "Kosovo", "Espagne", "Turquie", "Macédoine du Nord", "Serbie",
               "Autriche", "Sri Lanka", "Brésil", "Érythrée", "Pologne",
               "Royaume-Uni", "Bosnie-Herzégovine",
               "suisse", "allemande", "italienne", "portugaise"],
        "it": ["Svizzera", "Germania", "Italia", "Portogallo", "Francia",
               "Kosovo", "Spagna", "Turchia", "Macedonia del Nord", "Serbia",
               "Austria", "Sri Lanka", "Brasile", "Eritrea", "Polonia",
               "Regno Unito", "Bosnia ed Erzegovina",
               "svizzera", "tedesca", "italiana", "portoghese"],
        "en": ["Switzerland", "Germany", "Italy", "Portugal", "France",
               "Kosovo", "Spain", "Türkiye", "North Macedonia", "Serbia",
               "Austria", "Sri Lanka", "Brazil", "Eritrea", "Poland",
               "United Kingdom", "Bosnia and Herzegovina",
               "Swiss", "German", "Italian", "Portuguese"],
    },
    # 43 Auslaenderkategorie — die Ausweisarten im Klartext.
    "PERMIT_TYPE": {
        "de": ["Ausweis B", "Ausweis C", "Ausweis Ci", "Ausweis L",
               "Ausweis G", "Ausweis F", "Ausweis N", "Ausweis S",
               "Aufenthaltsbewilligung B", "Niederlassungsbewilligung C",
               "Grenzgängerbewilligung G", "Kurzaufenthaltsbewilligung L"],
        "fr": ["permis B", "permis C", "permis Ci", "permis L", "permis G",
               "permis F", "permis N", "permis S",
               "autorisation de séjour B", "autorisation d'établissement C",
               "autorisation frontalière G"],
        "it": ["permesso B", "permesso C", "permesso Ci", "permesso L",
               "permesso G", "permesso F", "permesso N", "permesso S",
               "permesso di dimora B", "permesso di domicilio C"],
        "en": ["permit B", "permit C", "permit L", "permit G", "permit F"],
    },
}


def build_merkmale() -> tuple[str, list[str], dict]:
    """Geschlossene Wertlisten je Tag, viersprachig.

    Format `TAG|lang|wert`, damit der Injektor sprachrichtig ziehen kann —
    dieselbe Lehre wie bei den Decoys: eine deutsche Auspraegung in einer
    franzoesischen Vorlage ist doppelt schaedlich.
    """
    zeilen: list[str] = []
    for tag, je_sprache in _MERKMALE.items():
        for sprache, werte in je_sprache.items():
            for wert in werte:
                zeilen.append(f"{tag}|{sprache}|{wert}")
    return "merkmale", sorted(dict.fromkeys(zeilen)), {
        "source": "Amtlicher Katalog der Merkmale (BFS), RHG Art. 6",
        "lizenz": "frei mit Quellenangabe",
        "hinweis": "DE woertlich aus dem Katalog, FR/IT gegenlesen",
    }


BUILDERS = [build_ortschaften, build_strassen, build_heimatorte,
            build_nachnamen, build_vornamen, build_zefix,
            build_behoerden, build_merkmale]


# -----------------------------------------------------------------------------

def cmd_list() -> int:
    print("Quellen fuer den Country Pack CH\n")
    for s in SOURCES:
        vorhanden = [f for f in s.files if (RAW / f).exists()]
        if not vorhanden:
            have = "FEHLT"
        elif len(vorhanden) == len(s.files):
            have = "vorhanden"
        else:
            have = f"teilweise ({len(vorhanden)}/{len(s.files)})"
        print(f"  {s.key:<12} [{have}]  {s.title}")
        print(f"  {'':<12} Tag:     {s.tag}")
        print(f"  {'':<12} Lizenz:  {s.licence}")
        print(f"  {'':<12} Quelle:  {s.url}")
        print(f"  {'':<12} Datei:   raw/{s.filename}")
        if s.note:
            print(f"  {'':<12} Hinweis: {s.note}")
        print()
    print(f"Zielverzeichnis: {RAW}")
    return 0


def cmd_fetch() -> int:
    """Absichtlich manuell: alle vier Portale liefern über Auswahlmasken oder
    SPARQL, nicht über stabile Direktlinks. Automatisieren hiesse raten."""
    RAW.mkdir(parents=True, exist_ok=True)
    print("Herunterladen und unter diesen Namen in raw/ ablegen:\n")
    for s in SOURCES:
        for f in s.files:
            mark = "OK " if (RAW / f).exists() else "-> "
            print(f"  {mark} {f:<22} {s.url}")
    print(f"\nZielverzeichnis: {RAW}")
    print("Danach: python3 packs/ch/nomenclatures/build.py --build")
    return 0


def cmd_build() -> int:
    built, missing = [], []
    for builder in BUILDERS:
        result = builder()
        if result is None:
            missing.append(builder.__name__.replace("build_", ""))
            continue
        name, entries, meta = result
        path = write(name, entries, meta)
        data = json.loads(path.read_text(encoding="utf-8"))
        flag = " (synthetisch)" if data["meta"].get("source") == "synthetisch" else ""
        print(f"  {data['meta']['count']:>6} Eintraege -> dist/{path.name}{flag}")
        built.append(name)

    if missing:
        print(f"\n  uebersprungen (raw/ fehlt): {', '.join(missing)}")

    # Fingerabdruck ueber die ERZEUGTEN WERTE, nicht ueber den Bauplan.
    #
    # Die Frage ist nicht «ist die Datei neuer?», sondern «waere das Ergebnis
    # anders?». Ein Vergleich von Zeitstempeln schluege schon bei einem
    # geaenderten Kommentar an, und eine Wache, die bei jedem Update anschlaegt,
    # wird weggeklickt.
    stempel = {}
    for name in built:
        pfad = DIST / f"{name}.json"
        stempel[name] = hashlib.sha256(pfad.read_bytes()).hexdigest()[:16]
    FINGERABDRUCK.write_text(
        json.dumps({"gebaut": datetime.now().isoformat(timespec="seconds"),
                    "werte": stempel}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    print(f"\n{len(built)} Nomenklatur(en) gebaut.")
    return 0


# Kumulative Quellen duerfen nie schrumpfen. Der Zaehler der letzten Ausgabe
# steht in dist/.watermark und wird bei jedem --verify fortgeschrieben.
MONOTONIC = {"heimatorte"}


def cmd_verify() -> int:
    dateien = nomenklaturdateien()
    if not dateien:
        print("dist/ ist leer — zuerst --build")
        return 1
    problems = []
    wm_path = DIST / ".watermark"
    marks = json.loads(wm_path.read_text()) if wm_path.exists() else {}
    for path in dateien:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["entries"]
        meta = data["meta"]
        structured = bool(entries) and isinstance(entries[0], dict)
        keys = [e["name"] for e in entries] if structured else entries
        if len(entries) != meta["count"]:
            problems.append(f"{path.name}: Zaehler stimmt nicht")
        if not structured and len(set(entries)) != len(entries):
            problems.append(f"{path.name}: Duplikate")
        if keys != sorted(keys, key=sortkey):
            problems.append(f"{path.name}: nicht sortiert -> nicht reproduzierbar")
        short = [k for k in keys if len(k) < 2]
        if short:
            problems.append(f"{path.name}: {len(short)} zu kurze Eintraege")
        stem = path.stem
        if stem in MONOTONIC:
            previous = marks.get(stem)
            if previous is not None and len(entries) < previous:
                problems.append(
                    f"{path.name}: {len(entries)} < {previous} beim letzten Mal. "
                    f"Diese Quelle ist kumulativ und darf nicht schrumpfen — "
                    f"vermutlich ein unvollstaendiger Download."
                )
            marks[stem] = max(len(entries), previous or 0)

        sample = entries[len(entries) // 2]
        print(f"  {path.name:<24} {len(entries):>6} Eintraege   "
              f"z.B. {(sample['written'] if structured and 'written' in sample else sample)!r}")
    if problems:
        print("\nPROBLEME:")
        for p in problems:
            print(f"  - {p}")
        return 1
    wm_path.write_text(json.dumps(marks, indent=1), encoding="utf-8")
    print("\ndist/ konsistent.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.list:
        return cmd_list()
    if args.fetch:
        return cmd_fetch()
    if args.build:
        return cmd_build()
    if args.verify:
        return cmd_verify()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
