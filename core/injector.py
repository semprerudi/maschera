"""Injektor: Vorlage + Nomenklatur -> Trainingsbeispiel mit Spannen (SPEC §8).

Slot-Grammatik in den Vorlagen:

    {FULLNAME}      echte Entitaet, wird getaggt
    {@address}      Makro, gekoppelte Gruppe aus macros.yaml
    {~amount}       **Decoy**: sieht aus wie eine Entitaet, bleibt aber O

Der Decoy-Mechanismus ist der Kern von SPEC §8. Ein Modell, das nur echte
Entitaeten sieht, lernt "Zahl mit CHF davor = AMOUNT". Es muss aber lernen
"Zahl mit CHF davor UND ohne Freibetrags-Kontext = AMOUNT". Dafuer braucht es
Gegenbeispiele im selben Satzbau.

**Round-Trip (SPEC §11):** Nach dem Fuellen wird fuer jede Spanne geprueft, ob
der Text an dieser Stelle exakt der eingesetzte Wert ist. Schlaegt das fehl,
ist das Beispiel unbrauchbar und wird verworfen statt stillschweigend mit
falschen Labels ins Training zu wandern. Das ist die einzige Absicherung
dagegen, dass ein Modell auf systematisch verschobene Spannen trainiert wird.
"""

from __future__ import annotations

import datetime
import json
import hashlib
import random
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from core.masking import Span
from packs.ch.generators.identifiers import GENERATORS

PACK_DIR = Path(__file__).resolve().parent.parent / "packs" / "ch"
DIST = PACK_DIR / "nomenclatures" / "dist"

SLOT_RE = re.compile(r"\{(~?@?)([A-Za-z0-9_]+)\}")
# Ziffern muessen erlaubt sein — sonst wird {AHVN13} nie ersetzt und
# steht als Literal im Trainingstext. Faellt nur bei Sichtpruefung auf.


@dataclass
class Example:
    text: str
    spans: list[Span]
    template_id: str
    lang: str
    decoys: list[tuple[int, int, str]] = field(default_factory=list)

    def to_bio(self, tokenizer=None) -> list[tuple[str, str]]:
        """Wortweise BIO-Labels. Nur fuer Sichtpruefung — das echte Training
        arbeitet auf Subword-Ebene mit den Zeichenspannen."""
        tokens: list[tuple[str, str]] = []
        for m in re.finditer(r"\S+", self.text):
            label = "O"
            for s in self.spans:
                if m.start() >= s.start and m.end() <= s.end:
                    label = ("B-" if m.start() == s.start else "I-") + s.tag
                    break
            tokens.append((m.group(0), label))
        return tokens


# ---------------------------------------------------------------------------
# Wertquellen
# ---------------------------------------------------------------------------

# Notvorrat, damit der Injektor OHNE heruntergeladene Nomenklaturen laeuft und
# testbar bleibt. Bewusst divers besetzt: waere hier nur Mueller/Meier/Schmid,
# wuerde ein Test gegen diesen Vorrat genau die Blindstelle verbergen, um die
# es bei Namen geht.
SEED = {
    "FULLNAME": ["Meier", "Da Silva", "Yilmaz", "Rajasingam", "Dupont",
                 "Rossi", "de Weck", "Meier-Schmid", "Oezdemir", "Brunner"],
    "GIVENNAME": ["Hans", "Rita", "Mehmet", "Chantal", "Jean-Pierre",
                  "Giuseppe", "Ana", "Fatima", "Sandro", "Nadia"],
    "STREET": ["Marktgasse", "Bahnhofstrasse", "Rue du Midi", "Via Nassa",
               "Chemin des Vignes", "Untere Zaeune", "Sonnenweg"],
    "CITY": ["Bern", "Geneve", "Lugano", "St. Gallen", "Sion", "Chur"],
    "ZIPCODE": ["3011", "1204", "6900", "9000", "1950", "7000"],
    "BUILDINGNUM": ["12", "4a", "27", "108", "3"],
    "PLACE_OF_ORIGIN": ["Hautemorges VD", "Biel/Bienne BE", "Tinizong GR",
                        "Sant'Antonino TI", "Zug ZG", "Rue FR"],
    "ORG": ["Alpin Treuhand AG", "Limmat Bau GmbH", "Cordier Transport SA",
            "Bundesamt für Statistik", "Steueramt Köniz",
            "Ufficio dello stato civile", "Office de l'état civil"],
    "HEALTHCARE_ORG": ["Klinik Sonnenberg", "Hopital du Jura"],
    "CANTON": ["BE", "VD", "TI", "ZH", "VS", "GR"],
    "COUNTRY": ["Schweiz", "Portugal", "Tuerkei", "Italien", "Kosovo"],
    "SEX": ["maennlich", "weiblich"],
    "MARITALSTATUS": ["ledig", "verheiratet", "geschieden", "verwitwet"],
    "NATIONALITY": ["Schweizer", "portugiesisch", "italienisch"],
    "RELIGION": ["roemisch-katholisch", "evangelisch-reformiert", "konfessionslos"],
    "PERMIT_TYPE": ["Ausweis B", "Ausweis C", "permis C"],
    "RESIDENCE_STATUS": ["Niederlassung", "Aufenthalt"],
    "VOTING_RIGHTS": ["stimmberechtigt", "nicht stimmberechtigt",
                      "in Gemeindeangelegenheiten stimmberechtigt"],
    "SOCIAL_INSURANCE": ["IV-Fall 4.271.883", "Kassennummer 1348",
                         "IV-Fall 9.112.004", "Kassennummer 1.234.5",
                         "Policennr. 88.221.4"],
    # Behoerde und Nummer getrennt: eine einzige Spanne ueber Behoerde, Stadt
    # UND Nummer waeren drei Tags in einem.
    "INSURANCE_POLICY": ["POL-8842119", "V-2024-77310", "748.221.909"],
    "PATIENT_ID": ["P-2024-0815", "PAT-99127", "KL-2023-4471"],
    # Benutzernamen wie in Firmen- und Behoerdennetzen ueblich: Initial plus
    # Nachname, punktgetrennt, mit Praefix der Stelle, oder rein numerisch.
    "USERNAME": ["mmueller", "a.rossi", "ktzh-hmeier", "u284471",
                 "schmidlin_l", "adasilva", "CORP\\myilmaz", "p.dupont",
                 "grossi_m", "n.oezdemir"],
}


@lru_cache(maxsize=1)
def _nomenclatures() -> dict[str, list[dict]]:
    """dist/ lesen, falls vorhanden. Sonst leer -> SEED greift."""
    out: dict[str, list[dict]] = {}
    if not DIST.exists():
        return out
    mapping = {
        "nachnamen": "FULLNAME",
        "vornamen": "GIVENNAME",
        "strassen": "STREET",
        "ortschaften": "CITY",
        "gemeinden": "CITY",
        "heimatorte": "PLACE_OF_ORIGIN",
        "organisationen": "ORG",
        "behoerden": "behoerden",
        "merkmale": "merkmale",
    }
    for path in DIST.glob("*.json"):
        tag = mapping.get(path.stem)
        if not tag:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        records = [
            e if isinstance(e, dict) else {"name": e, "weight": 1}
            for e in data["entries"]
        ]
        out.setdefault(tag, []).extend(records)
        if path.stem == "ortschaften":
            pairs = [r for r in records if r.get("plz")]
            if pairs:
                out.setdefault("_LOCALITY", []).extend(pairs)
        if path.stem in ("merkmale", "behoerden"):
            # Format TAG|lang|wert. Die geschlossenen Listen aus dem Amtlichen
            # Katalog der Merkmale werden SPRACHRICHTIG gezogen — eine deutsche
            # Auspraegung in einer franzoesischen Vorlage lehrt eine Sprachmischung,
            # die in echten Dokumenten nicht vorkommt.
            out.pop(path.stem, None)
            for r in records:
                teile = r["name"].split("|", 2)
                if len(teile) != 3:
                    continue
                merkmal, sprache, wert = teile
                out.setdefault(f"{merkmal}@{sprache}", []).append(
                    {"name": wert, "weight": 1})
            continue
        if path.stem == "strassen":
            full = [r for r in records if r.get("plz") and r.get("city")]
            if full:
                out["_ADDRESS"] = full
    return out


# Notvorrat als PAARE, damit PLZ und Ort auch ohne Nomenklatur zusammenpassen.
SEED_LOCALITY = [("3011", "Bern"), ("1204", "Geneve"), ("6900", "Lugano"),
                 ("9000", "St. Gallen"), ("7000", "Chur"), ("4051", "Basel"),
                 ("6600", "Locarno"), ("1950", "Sion")]


def _pick_locality(rng: random.Random) -> tuple[str, str]:
    """Ein zusammengehoeriges Paar (PLZ, Ort)."""
    pairs = _nomenclatures().get("_LOCALITY")
    if pairs:
        r = rng.choice(pairs)
        return r["plz"], r["name"]
    return rng.choice(SEED_LOCALITY)


def _pick_address(rng: random.Random) -> dict | None:
    """Strasse, PLZ und Ort aus EINEM Datensatz — sie gehoeren zusammen."""
    records = _nomenclatures().get("_ADDRESS")
    if not records:
        return None
    return rng.choice(records)


@lru_cache(maxsize=32)
def _weighted(tag: str) -> tuple[list, list]:
    """Datensaetze und KUMULIERTE Gewichte je Tag — einmal berechnet.

    Die Gewichtungsliste bei jedem Namensgriff neu aufzubauen, ueber alle
    rund 220 000 Nachnamen, kostet bei Hunderttausenden Spannen Milliarden
    ueberfluessige Operationen. Ein O(n)-Aufruf in einer heissen Schleife
    faellt bei einem Notvorrat von zehn Namen nicht auf und explodiert mit
    echten Daten.
    """
    records = _nomenclatures().get(tag) or []
    records = _zone(tag, records)
    total = 0
    cumulative = []
    for r in records:
        # Wurzel daempft die Verteilung: haeufige Namen bleiben haeufig, aber
        # die Top-20 erdruecken nicht den ganzen Rest.
        total += max(1, int(r.get("weight", 1) ** 0.5))
        cumulative.append(total)
    return records, cumulative


# --- Rauschen: echte Dokumente sind nicht sauber ----------------------------
#
# Ein Name mit vertauschten Buchstaben («Pasuqale») steht in keiner
# Nomenklatur und damit in keinem einzigen Trainingsbeispiel. Ein Modell,
# das nur saubere Nomenklaturwerte sieht, lernt Namen aus einer Liste
# WIEDERZUERKENNEN statt sie an ihrer Form zu erkennen — ein Woerterbuch
# statt einer Sprache.
#
# Die Fehlerarten sind aus echten Dokumenten abgeleitet, nicht erfunden:
# Vertauschung (Tippfehler), fehlender Buchstabe, doppelter Buchstabe,
# aufgeloester Umlaut (Systeme, die Umlaute strippen), Versalien
# (Formulare in Grossschrift).
_UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
            "à": "a", "é": "e", "è": "e", "ê": "e", "î": "i", "ô": "o",
            "û": "u", "ç": "c"}


def verrausche(wert: str, rng: random.Random) -> str:
    """Einen Wert leicht beschaedigen — wie ein Mensch oder ein Altsystem."""
    if len(wert) < 4:
        return wert
    art = rng.choice(("tausch", "fehlt", "doppelt", "umlaut", "versal"))

    if art == "umlaut":
        ersetzt = "".join(_UMLAUTE.get(z, z) for z in wert)
        # Nur melden, wenn sich wirklich etwas geaendert hat — sonst waere
        # jeder fuenfte Rauschgriff wirkungslos und die Rate gelogen.
        return ersetzt if ersetzt != wert else wert
    if art == "versal":
        return wert.upper()

    # Position im Wortinneren: der erste Buchstabe traegt zu viel Signal,
    # ihn zu beschaedigen macht den Namen unkenntlich statt tippfehlerhaft.
    i = rng.randrange(1, len(wert) - 1)
    if art == "tausch":
        return wert[:i] + wert[i + 1] + wert[i] + wert[i + 2:]
    if art == "fehlt":
        return wert[:i] + wert[i + 1:]
    return wert[:i] + wert[i] + wert[i:]


# Tags, bei denen Rauschen sinnvoll ist. NICHT bei Pruefsummen-Tags: eine
# beschaedigte AHV-Nummer ist keine AHV-Nummer mehr, Stufe 1 verwirft sie
# zu Recht, und das Beispiel lehrt nichts ausser einem Widerspruch.
VERRAUSCHBAR = {"FULLNAME", "GIVENNAME", "STREET", "CITY", "ORG",
                "PLACE_OF_ORIGIN"}


# --- Haltezone: trennt Erkennen von Auswendiglernen ------------------------
#
# Ziehen Trainings- und Auswertungssatz aus DERSELBEN Nomenklatur, ist «das
# Modell erkennt Namen» nicht von «das Modell hat die Nachnamenliste
# auswendig gelernt» zu unterscheiden.
#
# Ein Zehntel der Werte wird deshalb deterministisch zurueckgehalten. Der
# Trainingssatz sieht sie NIE, der Auswertungssatz NUR sie. Faellt der Wert
# dort ab, hat das Modell die Liste gelernt und nicht die Form.
#
# Deterministisch ueber den Wert selbst, nicht ueber den Index: baut sich die
# Nomenklatur neu und aendert die Reihenfolge, bleibt die Trennung dieselbe.
HALTEZONE = 10          # jeder zehnte Wert
_zonenmodus: str | None = None      # None | "training" | "halten"


def setze_zone(modus: str | None) -> None:
    """None = alle Werte, 'training' = neun Zehntel, 'halten' = ein Zehntel."""
    global _zonenmodus
    if modus not in (None, "training", "halten"):
        raise ValueError(f"Unbekannter Zonenmodus: {modus}")
    _zonenmodus = modus
    _weighted.cache_clear()


def _in_haltezone(name: str) -> bool:
    return int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16) \
        % HALTEZONE == 0


def _zone(tag: str, records: list) -> list:
    if _zonenmodus is None or not records:
        return records
    # Den Sprachzusatz abschneiden. `_weighted` wird auch mit "ORG@de"
    # aufgerufen, und "ORG@de" steht nicht in VERRAUSCHBAR. Ohne diese Zeile
    # hielte die Haltezone Firmennamen zurueck und Behoerdennamen nicht — ein
    # Filter, der nichts filtert, sieht von aussen aus wie einer, der nichts zu
    # tun hat.
    tag = tag.split("@", 1)[0]
    # Nur bei den Tags, um die es geht. Bei einer Liste von acht Zivilstaenden
    # wuerde ein Zehntel Rueckhalt die Vorlage unbrauchbar machen.
    if tag not in VERRAUSCHBAR:
        return records
    halten = _zonenmodus == "halten"
    gefiltert = [r for r in records if _in_haltezone(r["name"]) == halten]
    return gefiltert or records


def _pick(tag: str, rng: random.Random, lang: str = "de") -> str:
    """Einen Wert fuer ein Tag ziehen. Nomenklatur schlaegt Notvorrat.

    `lang` zaehlt nur fuer die geschlossenen Listen aus dem Amtlichen Katalog
    der Merkmale (`MARITALSTATUS`, `SEX`, `RELIGION`, `RESIDENCE_STATUS`,
    `VOTING_RIGHTS`, `PERMIT_TYPE`). Namen und Orte sind sprachneutral —
    ein Tessiner Nachname steht auch in einer deutschen Vorlage.
    """
    wert = _pick_roh(tag, rng, lang)
    if _rauschrate and tag in VERRAUSCHBAR and rng.random() < _rauschrate:
        return verrausche(wert, rng)
    return wert


_rauschrate = 0.0


# Tags, bei denen die Sprachliste die allgemeine Liste NICHT verdeckt,
# sondern sich mit ihr teilt — und zu welchem Anteil sie zum Zug kommt.
#
# Der Vorrang der Sprachliste in `_pick_roh` ist fuer GESCHLOSSENE Kataloge
# gebaut: bei `MARITALSTATUS`, `SEX`, `RELIGION`, `RESIDENCE_STATUS`,
# `VOTING_RIGHTS` und `PERMIT_TYPE` waere eine deutsche Auspraegung in einer
# franzoesischen Vorlage schlicht falsch, und eine allgemeine Liste gibt es
# dort nicht.
#
# `ORG` ist anders: `behoerden.json` liefert rund 190 Eintraege je Sprache
# (`ORG@de` …), `organisationen.json` rund 20 000 Firmennamen. Verdeckte die
# Sprachliste die allgemeine, saehe das Modell als `ORG` nur Bundesaemter —
# und hielte `Šarić & Partner GmbH` fuer einen Personennamen.
#
# 0.5 und nicht mehr: Post von Behoerden kommt in echten Dokumenten
# haeufig vor und soll es in den Trainingsdaten bleiben. Ueber die
# Haelfte der `ORG`-Slots in den Vorlagen steht aber in
# Firmenzusammenhaengen.
GETEILT = {"ORG": 0.5}


def _pick_roh(tag: str, rng: random.Random, lang: str = "de") -> str:
    if tag in GENERATORS:
        return GENERATORS[tag](rng)

    if _nomenclatures().get(f"{tag}@{lang}"):
        anteil = GETEILT.get(tag)
        # Kein Anteil = geschlossener Katalog = Sprachliste allein.
        if anteil is None or rng.random() < anteil:
            records, cumulative = _weighted(f"{tag}@{lang}")
            if records:
                return rng.choices(records,
                                   cum_weights=cumulative, k=1)[0]["name"]

    records, cumulative = _weighted(tag)
    if records:
        # PLACE_OF_ORIGIN braucht die UEBLICHE Schreibweise mit Kantonskuerzel:
        # "Hautemorges VD", nicht "Hautemorges". Das Kuerzel ist der Anker des
        # Stufe-2-Musters — ohne es wird der Heimatort nicht erkannt, und das
        # Trainingsset lehrt eine Form, die im Dokument nicht vorkommt.
        field = "written" if tag == "PLACE_OF_ORIGIN" else "name"
        chosen = rng.choices(records, cum_weights=cumulative, k=1)[0]
        return chosen.get(field) or chosen["name"]

    if tag in SEED:
        return rng.choice(SEED[tag])

    return _fallback(tag, rng)


# Tatsaechlich vergebene Vorwahlen. "045" gibt es nicht — erfundene Vorwahlen
# im Trainingsset lehren das Modell ein Muster, das in echten Dokumenten
# nie vorkommt.
_AREA = ["21", "22", "24", "26", "27", "31", "32", "33", "34", "41", "43",
         "44", "51", "52", "55", "56", "58", "61", "62", "71", "76", "77",
         "78", "79", "81", "91"]


def _fallback(tag: str, rng: random.Random) -> str:
    """Fuer Tags ohne Liste: aus dem Muster erzeugen."""
    if tag == "DATE":
        d, m, y = rng.randint(1, 28), rng.randint(1, 12), rng.randint(1950, 2026)
        return rng.choice([f"{d:02d}.{m:02d}.{y}", f"{d}. {['Januar','Februar','Maerz','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'][m-1]} {y}", f"{y}-{m:02d}-{d:02d}"])
    if tag == "TIME":
        return f"{rng.randint(7,18):02d}:{rng.choice(['00','15','30','45'])}"
    if tag == "PHONE":
        return rng.choice([
            f"+41 {rng.choice(_AREA)} {rng.randint(100,999)} {rng.randint(10,99)} {rng.randint(10,99)}",
            f"0{rng.choice(_AREA)} {rng.randint(100,999)} {rng.randint(10,99)} {rng.randint(10,99)}",
        ])
    if tag == "EMAIL":
        return f"{rng.choice(['info','kontakt','a.muster','m.beispiel'])}@{rng.choice(['example.ch','muster.ch','gemeinde.ch'])}"
    if tag == "AGE":
        return str(rng.randint(18, 92))
    if tag == "AMOUNT":
        return f"CHF {rng.randint(1,9)}'{rng.randint(0,999):03d}.{rng.choice(['00','50','--'])}"
    if tag == "EGID":
        return str(rng.randint(100000, 9999999))
    if tag == "EWID":
        return str(rng.randint(1, 120))
    if tag == "MUNICIPALITY_ID":
        return str(rng.randint(1, 6810))
    if tag == "PLATE":
        return f"{rng.choice(SEED['CANTON'])} {rng.randint(1, 999999)}"
    if tag == "CASE_ID":
        return f"{rng.choice(['EWK','SOZ','BAU','STA'])}-{rng.randint(2015,2026)}-{rng.randint(1,99999):05d}"
    if tag == "IDDOC":
        return f"{rng.choice('XSFCA')}{rng.randint(1000000,9999999)}"
    if tag == "PARCEL":
        return str(rng.randint(1, 4999))
    if tag == "URL":
        return f"https://www.{rng.choice(['example','muster','gemeinde'])}.ch/{rng.choice(['formular','dienste','a/b'])}"
    if tag == "ZSR_RCC":
        return f"{rng.choice('ABCDEFGHKLMNPRSTVWZ')}{rng.randint(100000, 999999)}"
    if tag == "INSURANCE_CARD":
        return "80756" + "".join(str(rng.randint(0, 9)) for _ in range(15))
    if tag == "IPADDRESS":
        return ".".join(str(rng.randint(1, 254)) for _ in range(4))
    return f"<{tag}>"


# ---------------------------------------------------------------------------
# Datumskohaerenz
# ---------------------------------------------------------------------------
# Zieht jeder {DATE}-Slot unabhaengig, entstehen Zeilen wie "Referenzperiode:
# vom 15.01.2003 bis 07.05.1964" — ein Zeitraum, der rueckwaerts laeuft. Die
# Labels bleiben korrekt, die Prosa ist unmoeglich, und ein unmoegliches
# Umfeld ist eines, das das Modell nie antreffen wird.
#
# Regel: Ein Dokument hat sein EIGENES Datum, aktuell (2019-2026). Die uebrigen
# Daten schreiten davon vorwaerts. Ausnahme sind Geburtsdaten, die Jahrzehnte
# davor liegen und am ANKUENDIGUNGSTEXT erkannt werden, nicht geraten.

_BIRTH_MARKERS = (
    "geboren am", "geboren", "geburtsdatum", "geb.",
    "né le", "née le", "date de naissance", "naissance",
    "nato il", "nata il", "data di nascita",
    "born on", "date of birth",
)

# Marker in derselben Form wie das Suchfenster: Satzzeichen zu Leerraum.
_NORMALISED_MARKERS = tuple(
    " ".join(re.sub(r"[^\w\s]", " ", m).split()) for m in _BIRTH_MARKERS
)

# Monatsnamen je Sprache — "Decision dated 27. Oktober 2021" in einer
# englischen Vorlage waere eine Sprachmischung.
_MONTHS = {
    "de": ["Januar", "Februar", "Maerz", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
           "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}


def _announces_birth(tail: str) -> bool:
    """Steht unmittelbar vor dem Slot eine Geburtsankuendigung?

    ANKERT AM ENDE und ueberschreitet keine Satzgrenze. Sucht man in einem
    breiten Fenster, erwischt man die Ankuendigung des vorherigen Satzes: in
    "geboren am 29.08.1945. Ab {DATE}" wuerde auch das zweite Datum zu einer
    Geburt.
    """
    cut = max(tail.rfind("."), tail.rfind("\n"), tail.rfind(";"))
    # Satzzeichen zu Leerraum machen, dann an Wortgrenzen suchen. Im
    # Formularfeld steht "Geburtsdatum:", nicht "Geburtsdatum ".
    window = re.sub(r"[^\w\s]", " ", tail[cut + 1:][-40:].lower())
    return any(re.search(rf"\b{re.escape(m)}\b", window)
               for m in _NORMALISED_MARKERS)


def _format_date(d: datetime.date, rng: random.Random, lang: str = "de") -> str:
    month = _MONTHS.get(lang, _MONTHS["de"])[d.month - 1]
    written = {
        "de": f"{d.day}. {month} {d.year}",
        "fr": f"{d.day} {month} {d.year}",
        "it": f"{d.day} {month} {d.year}",
        "en": f"{d.day} {month} {d.year}",
    }[lang if lang in _MONTHS else "de"]
    numeric = (f"{d.year}-{d.month:02d}-{d.day:02d}" if lang == "en"
               else f"{d.day:02d}.{d.month:02d}.{d.year}")
    return rng.choice([f"{d.day:02d}.{d.month:02d}.{d.year}", written, numeric])


# Decoys: sehen aus wie Entitaeten, sind aber keine. Muessen O bleiben.
# Decoys je Sprache. Ein deutscher Decoy in einer franzoesischen Vorlage
# ("Paiement binnen 10 Arbeitstagen") ist doppelt schaedlich: das Modell lernt
# eine Sprachmischung, die in echten Dokumenten nicht vorkommt, und die
# franzoesische Vorlage verliert genau das Gegenbeispiel, fuer das sie da ist.
DECOYS = {
    "amount": {
        "de": ["der Vermoegensfreibetrag von 4000 Franken",
               "die Gebuehr von CHF 50.00",
               "der Grundbedarf von CHF 1'200.00",
               "eine Pauschale von CHF 300.00"],
        "fr": ["la franchise de 300 francs",
               "l'émolument de CHF 50.00",
               "le montant maximal de CHF 1'200.00",
               "un forfait de CHF 300.00"],
        "it": ["la franchigia di 300 franchi",
               "la tassa di CHF 50.00",
               "l'importo massimo di CHF 1'200.00",
               "un forfait di CHF 300.00"],
        "en": ["the tax-free allowance of CHF 4,000",
               "the fee of CHF 50.00",
               "a flat rate of CHF 300.00"],
    },
    "legal": {
        "de": ["Art. 6 Abs. 1 Bst. i RHG (SR 431.02)",
               "Art. 12 Abs. 3 DSG (SR 235.1)",
               "gestuetzt auf Art. 5 ZGB"],
        "fr": ["art. 6 al. 1 let. i LHR (RS 431.02)",
               "art. 12 al. 3 LPD (RS 235.1)",
               "fondé sur l'art. 5 CC"],
        "it": ["art. 6 cpv. 1 lett. i LArRa (RS 431.02)",
               "art. 12 cpv. 3 LPD (RS 235.1)",
               "fondato sull'art. 5 CC"],
        "en": ["Art. 6 para. 1 let. i RHA (SR 431.02)",
               "Art. 12 para. 3 FADP (SR 235.1)"],
    },
    "deadline": {
        "de": ["innert 30 Tagen", "binnen 10 Arbeitstagen",
               "innerhalb von 3 Monaten"],
        "fr": ["dans un délai de 30 jours", "sous 10 jours ouvrables",
               "dans les 3 mois"],
        "it": ["entro 30 giorni", "entro 10 giorni lavorativi",
               "entro 3 mesi"],
        "en": ["within 30 days", "within 10 working days",
               "within 3 months"],
    },
    "number": {
        "de": ["Version 2.1", "Seite 3 von 12", "Formular 1150",
               "Raum 204", "Postfach 3001"],
        "fr": ["version 2.1", "page 3 sur 12", "formulaire 1150",
               "bureau 204", "case postale 3001"],
        "it": ["versione 2.1", "pagina 3 di 12", "modulo 1150",
               "ufficio 204", "casella postale 3001"],
        "en": ["version 2.1", "page 3 of 12", "form 1150",
               "room 204", "P.O. Box 3001"],
    },
    # IT-Support ist der schwierigste Fall: Technik steht direkt neben
    # Personendaten, und vieles SIEHT aus wie ein Identifikator. Ohne diese
    # Gegenbeispiele lernt das Modell "Ziffernfolge mit Punkten = AHV-Nummer"
    # und maskiert Versionsnummern, Ports und Zeitstempel.
    "technical": {
        "de": ["Exit-Code 137", "Port 5432", "HTTP 502 Bad Gateway",
               "Build 2024.3.1-rc2", "PID 18442", "Commit a3f91c",
               "Speicherbedarf 4096 MB", "Timeout nach 30000 ms"],
        "fr": ["code de sortie 137", "port 5432", "HTTP 502 Bad Gateway",
               "build 2024.3.1-rc2", "PID 18442", "commit a3f91c",
               "délai dépassé après 30000 ms"],
        "it": ["codice di uscita 137", "porta 5432", "HTTP 502 Bad Gateway",
               "build 2024.3.1-rc2", "PID 18442", "commit a3f91c",
               "timeout dopo 30000 ms"],
        "en": ["exit code 137", "port 5432", "HTTP 502 Bad Gateway",
               "build 2024.3.1-rc2", "PID 18442", "commit a3f91c",
               "timed out after 30000 ms"],
    },
    "trace": {
        "de": ["at ch.example.registry.PersonService.load(PersonService.java:214)",
               "NullPointerException in Zeile 88",
               "java.sql.SQLException: ORA-01722: invalid number",
               "Stack: 0x00007ffce4a1b230"],
        "fr": ["at ch.example.registry.PersonService.load(PersonService.java:214)",
               "NullPointerException à la ligne 88",
               "java.sql.SQLException: ORA-01722: invalid number"],
        "it": ["at ch.example.registry.PersonService.load(PersonService.java:214)",
               "NullPointerException alla riga 88",
               "java.sql.SQLException: ORA-01722: invalid number"],
        "en": ["at ch.example.registry.PersonService.load(PersonService.java:214)",
               "NullPointerException at line 88",
               "java.sql.SQLException: ORA-01722: invalid number"],
    },
    "place": {
        "de": ["im Sinne von Art. 2", "gemaess Ziffer 4.2"],
        "fr": ["au sens de l'art. 2", "selon le chiffre 4.2"],
        "it": ["ai sensi dell'art. 2", "secondo la cifra 4.2"],
        "en": ["within the meaning of Art. 2", "under section 4.2"],
    },
}


def pick_decoy(kind: str, lang: str, rng: random.Random) -> str:
    pool = DECOYS.get(kind)
    if pool is None:
        raise KeyError(f"unbekannter Decoy ~{kind}")
    return rng.choice(pool.get(lang) or pool["de"])


# ---------------------------------------------------------------------------
# Injektion
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _macros() -> dict:
    with (PACK_DIR / "macros.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["macros"]


def _expand_macro(name: str, rng: random.Random, lang: str = "de") -> list:
    """Makro aufloesen. Varianten mit `lang` gelten nur fuer diese Sprache.

    Ohne den Filter landete ", geboren am " in franzoesischen Vorlagen.
    """
    macro = _macros().get(name)
    if not macro:
        raise KeyError(f"unbekanntes Makro @{name}")
    passend = [v for v in macro["variants"]
               if "lang" not in v or v["lang"] == lang]
    if not passend:
        passend = [v for v in macro["variants"] if "lang" not in v]
    # `weight` (Vorgabe 1) macht die Mischung zur Entscheidung statt zum
    # Nebenprodukt davon, wieviele Varianten jemand hingeschrieben hat. Beim
    # `person`-Makro haengt genau daran, wie oft das Modell die
    # Register-Reihenfolge sieht.
    gewichte = [v.get("weight", 1) for v in passend]
    return rng.choices(passend, weights=gewichte, k=1)[0]["parts"]


def inject(template: dict, rng: random.Random) -> Example | None:
    """Eine Vorlage fuellen. None, wenn der Round-Trip scheitert."""
    out: list[str] = []
    spans: list[Span] = []
    decoys: list[tuple[int, int, str]] = []
    pos = 0
    group: dict[str, str] = {}  # Makrogruppe -> kanonischer Wert

    def emit_literal(s: str) -> None:
        nonlocal pos
        out.append(s)
        pos += len(s)

    def emit_tag(tag: str, canonical: str | None) -> None:
        nonlocal pos
        if tag == "DATE":
            tail = "".join(out)
            if _announces_birth(tail):
                # Geburtsdatum: Jahrzehnte vor dem Dokument
                value = _format_date(
                    doc_date - datetime.timedelta(days=rng.randrange(6570, 32850)),
                    rng, lang,
                )
            else:
                if cursor["first"]:
                    cursor["first"] = False
                else:
                    cursor["date"] = cursor["date"] + datetime.timedelta(
                        days=rng.randrange(1, 400)
                    )
                value = _format_date(cursor["date"], rng, lang)
            out.append(value)
            spans.append(Span(tag, pos, pos + len(value), canonical=canonical))
            pos += len(value)
            return

        if tag in ("STREET", "ZIPCODE", "CITY") and canonical:
            if not context:
                # Ganze Adresse aus einem Datensatz. Nur wenn kein
                # Strassenverzeichnis da ist, faellt es auf getrennte Quellen
                # zurueck — dann stimmt die Kopplung nicht, aber es laeuft.
                address = _pick_address(rng)
                if address:
                    context["STREET"] = address["name"]
                    context["ZIPCODE"] = address["plz"]
                    context["CITY"] = address["city"]
                else:
                    plz, ort = _pick_locality(rng)
                    context["ZIPCODE"], context["CITY"] = plz, ort
                    context["STREET"] = _pick("STREET", rng)
            value = context.get(tag) or _pick(tag, rng, lang)
        else:
            value = _pick(tag, rng, lang)
        out.append(value)
        spans.append(Span(tag, pos, pos + len(value), canonical=canonical))
        pos += len(value)

    # Kohaerenzkontext einer Makroinstanz: PLZ und Ort muessen zusammenpassen.
    # Ohne das entsteht "Untere Zaeune 108, 6900 Lugano" — Strasse aus Bern,
    # PLZ aus Lugano. Das Modell lernt dann, dass PLZ und Ort nichts miteinander
    # zu tun haben, und der ZIPCODE-Recognizer verliert seinen einzigen Anker.
    context: dict[str, str] = {}
    lang = template.get("lang", "de")

    # Eigenes Datum des Dokuments. Alle uebrigen Daten schreiten davon vorwaerts.
    doc_date = datetime.date(2019, 1, 1) + datetime.timedelta(
        days=rng.randrange(0, 2600)
    )
    cursor = {"date": doc_date, "first": True}

    text = template["text"]
    last = 0
    for m in SLOT_RE.finditer(text):
        emit_literal(text[last:m.start()])
        prefix, name = m.group(1), m.group(2)

        if prefix == "~":
            value = pick_decoy(name, template.get("lang", "de"), rng)
            decoys.append((pos, pos + len(value), name))
            emit_literal(value)

        elif prefix == "@":
            parts = _expand_macro(name, rng, template.get("lang", "de"))
            # Alle Teile derselben Makroinstanz teilen eine Gruppenkennung,
            # damit die Propagation sie als Einheit behandelt (Adressleck).
            gid = f"@{name}:{len(spans)}"
            context.clear()  # jede Makroinstanz zieht ihren eigenen Ort
            for part in parts:
                if part.isupper() and part.isidentifier():
                    emit_tag(part, gid)
                else:
                    emit_literal(part)

        else:
            emit_tag(name, None)

        last = m.end()
    emit_literal(text[last:])

    final = "".join(out)

    # Kein Platzhalter der Form <TAG> darf durchrutschen. Er entsteht, wenn ein
    # Tag weder Generator noch Nomenklatur noch Notvorrat hat — und stuende dann
    # als Literal im Trainingstext, wo das Modell ihn brav mitlernt.
    if re.search(r"<[A-Z][A-Z0-9_]{2,}>", final):
        return None

    # --- Round-Trip: jede Spanne muss zeichengenau sitzen -------------------
    for s in spans:
        if not (0 <= s.start < s.end <= len(final)):
            return None
    if any(final[s.start:s.end].strip() == "" for s in spans):
        return None
    # Decoys duerfen sich nicht mit Spannen ueberlappen
    for a, b, _ in decoys:
        if any(a < s.end and s.start < b for s in spans):
            return None

    return Example(text=final, spans=spans,
                   template_id=template.get("id", "?"),
                   lang=template.get("lang", "de"), decoys=decoys)


# Wachen fuer die Vorlagenbank.
# Von Hand geschriebene Vorlagen verletzen das selten. Sobald die Bank von
# einem LLM erzeugt wird — wie in SPEC §8 vorgesehen — ist beides haeufig, und
# beide Fehler sind still: die Labels sehen richtig aus, das Ergebnis ist Schrott.

_ADJACENT = re.compile(r"\{[~@]?\w+\}[ \t]*\{[~@]?\w+\}")
_LITERAL_ESCAPE = re.compile(r"\\[nrt]")


def check_template(t: dict) -> list[str]:
    """Befunde zu einer Vorlage. Leere Liste = in Ordnung."""
    problems: list[str] = []
    text = t.get("text", "")

    # Zwei Slots nur durch Leerzeichen getrennt liefern benachbarte Entitaeten
    # ohne 'O' dazwischen. Bei GLEICHEM Tag sind sie in BIO nicht mehr von EINER
    # laengeren Entitaet zu unterscheiden.
    #
    # Bei VERSCHIEDENEN Tags ist das kein Problem — `B-DATE` neben `B-TIME` ist
    # eindeutig, und es kommt in echten Dokumenten laufend vor: «Gesendet:
    # Dienstag, 03.08.2026 08:12», «Zivilstandsamt, Köniz». Die Wache prueft
    # deshalb nur gleiche Tags; eine Warnung, die man immer wegklickt, ist
    # schlimmer als keine.
    for m in _ADJACENT.finditer(text):
        tags = re.findall(r"\{([@~]?\w+)[^}]*\}", m.group(0))
        if len(set(tags)) < len(tags):
            problems.append(
                f"benachbarte Slots MIT GLEICHEM TAG: {m.group(0)!r} — in BIO "
                f"nicht von einer laengeren Entitaet unterscheidbar")

    # Das Modell schreibt manchmal die zwei Zeichen '\' und 'n' statt eines
    # Zeilenumbruchs. Wird direkt danach ein Wert eingesetzt, klebt der
    # Tokenizer das 'n' an den Anfang der Entitaet ('\n09.06.1965' -> Token
    # 'n09'): dieses Token bleibt O, der Rest wird I-DATE. Eine BIO-Zeile mit
    # I- ohne B- verwirft das Training. Normalisiert statt verworfen — die
    # Vorlage ist sonst brauchbar.
    for m in _LITERAL_ESCAPE.finditer(text):
        problems.append(f"literaler Escape {m.group(0)!r} statt Zeilenumbruch")

    return problems


def normalize_template(t: dict) -> dict:
    """Literale Escapes in echte Zeichen wandeln."""
    text = t.get("text", "")
    text = text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")
    return {**t, "text": text}


# Decoys sind PHRASEN, keine Werte. Alle `amount`-Decoys sind Nominalphrasen
# mit Artikel («eine Pauschale von CHF 300.00»). Setzt eine Vorlage ein eigenes
# Etikett davor, entsteht kaputtes Deutsch:
#
#     Gebuehr: {~amount}   ->   «Gebuehr: eine Pauschale von CHF 300.00»
#
# Kein Label-Test kann das finden: die Labels sind korrekt, nur die Prosa
# ist unmoeglich.
_ETIKETT_VOR_DECOY = re.compile(
    r"(?i)\b(?:Geb(?:ü|ue)hr(?:enrahmen)?|Betrag|Kosten|Preis|Summe|Ansatz|"
    r"(?:é|e)molument|taxe|frais|montant|tassa|importo|spese|fee|amount)"
    r"\s*:?\s*\{~amount\}"
)


# Die `amount`-Familie muss EINHEITLICH aus Nominalphrasen bestehen. Mischt sie
# Phrasen und ganze Saetze, ist jede Vorlage entweder fuer die einen oder fuer
# die anderen falsch:
#
#     «Gebuehr {~amount}»          + Phrase  -> «Gebuehr eine Pauschale von …»
#     «Verrechnet wird {~amount}»  + Satz    -> «Verrechnet wird die Gebuehr
#                                                betraegt CHF 50.00»
#
# Eine Wache auf die Vorlagen allein genuegt also nicht — die DATEN muessen
# einheitlich sein.
_FINITES_VERB = re.compile(
    r"(?i)\b(?:betr(?:ae|ä)gt|bel(?:ae|ä)uft|ist|sind|s'élève|se monte|"
    r"ammonta|corrisponde|amounts?|equals)\b")


def pruefe_decoys() -> list[str]:
    """Jede `amount`-Ausprägung muss eine Nominalphrase sein, kein Satz."""
    problems = []
    for sprache, werte in DECOYS.get("amount", {}).items():
        for wert in werte:
            if _FINITES_VERB.search(wert):
                problems.append(
                    f"amount/{sprache}: {wert!r} ist ein SATZ, keine "
                    f"Nominalphrase. Die Familie muss einheitlich sein.")
    return problems


def pruefe_decoy_stellung(text: str, template_id: str) -> str | None:
    """Ein Etikett unmittelbar vor einem Phrasen-Decoy ergibt keinen Satz."""
    m = _ETIKETT_VOR_DECOY.search(text)
    if m:
        return (f"{template_id}: {m.group(0)!r} — `{{~amount}}` ist eine "
                f"PHRASE mit Artikel. Ein Etikett davor ergibt "
                f"«Gebuehr eine Pauschale von …». Etikett weglassen oder "
                f"ein Verb einsetzen («Erhoben wird {{~amount}}»).")
    return None


def load_templates(lang: str | None = None, strict: bool = False) -> list[dict]:
    out: list[dict] = []
    root = PACK_DIR / "templates"
    for path in sorted(root.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for t in data.get("templates", []):
            # Trainingssperre. Vorlagen und Dokumente des Testsets duerfen NIE
            # in den Trainingssatz. Waeren sie drin, pruefte das Modell sich
            # selbst und die Leckrate auf echten Dokumenten waere geschoent.
            # `packs/ch/eval/` liegt bereits ausserhalb von `templates/`; das
            # hier faengt den Fall ab, dass eine Datei verschoben wird.
            if t.get("eval_only") or data.get("eval_only"):
                raise SystemExit(
                    f"ABBRUCH: {path} traegt `eval_only` und liegt im "
                    f"Vorlagenbaum. Testdokumente gehoeren nach "
                    f"packs/ch/eval/, nicht nach packs/ch/templates/."
                )
            t.setdefault("lang", path.parent.name)
            problem = pruefe_decoy_stellung(t.get("text", ""),
                                            t.get("id", path.name))
            if problem:
                if strict:
                    raise SystemExit(f"ABBRUCH: {problem}")
                print(f"  WARNUNG {problem}")
            if lang is not None and t["lang"] != lang:
                continue
            t = normalize_template(t)
            problems = check_template(t)
            if problems:
                message = f"{t.get('id','?')}: " + "; ".join(problems)
                if strict:
                    raise SystemExit(f"Vorlage fehlerhaft — {message}")
                print(f"  WARNUNG Vorlage {message}")
                continue
            out.append(t)
    return out


def generate(n: int, seed: int = 0, lang: str | None = None,
             rauschen: float = 0.0, zone: str | None = None) -> list[Example]:
    """`rauschen` — Anteil der Namen und Orte mit einem Tippfehler (0.0–1.0).
    `zone` — None (alle Werte), "training" (neun Zehntel), "halten" (ein Zehntel).
    """
    global _rauschrate
    _rauschrate = rauschen
    setze_zone(zone)
    rng = random.Random(seed)
    templates = load_templates(lang)
    if not templates:
        raise SystemExit("keine Vorlagen gefunden")
    out, tries = [], 0
    while len(out) < n and tries < n * 10:
        tries += 1
        ex = inject(rng.choice(templates), rng)
        if ex:
            out.append(ex)
    return out
