"""Eigene Regeln des Anwenders — branchenspezifische Bezeichner.

Jede Stelle hat Identifikatoren, die nur bei ihr vorkommen: die Dossiernummer
einer Kanzlei, die Kundennummer einer Firma, die Fallnummer einer
Fachanwendung, das Kuerzel eines Registers. Keine davon gehoert in die Taxonomie — es gibt
zu viele, sie aendern sich, und sie sind nicht schweizweit einheitlich.

**Warum das ohne Neutraining geht.** Der Labelvertrag deckt nur ab, was das
MODELL vorhersagt. Eine Benutzerregel laeuft wie ein Packmuster der
Stufe 2, rein deterministisch, und beruehrt weder BIO-Labels noch
Checkpoint (Architekturprinzip 1: Erkennen und Maskieren sind zwei Achsen).

**Warum diese Tags nie ins Training gelangen koennen.** Sie heissen `X_<id>`
und stehen in keiner `taxonomy.yaml`. Geriete eine je in einen
Trainingssatz, wirft `align()` einen `KeyError` — lauter Fehler statt
stillem Labelverlust. Das ist keine Absicht, die man vergessen kann,
sondern die Bauweise.

Drei Arten, absteigend nach Sicherheit:

  wordlist    feste Zeichenketten, Wortgrenzen zwingend. Kein Regex.
  label       Etikett + Wertform. Der Anwender fuellt Felder aus, die Engine
              baut das verankerte Muster — inklusive Umlaut- und
              Diakritikavarianten.
  regex       eigenes Muster. Wird beim Laden auf Laufzeit geprueft.

## Ablageort

Vorgabe `~/.config/maschera/regeln.yaml`, ueberschreibbar ueber
`MASCHERA_REGELN` oder `--regeln`. Ausserhalb des Repositoriums — die Datei
enthaelt betriebsinterne Bezeichner und geht niemanden sonst etwas an.

## Format

**Die Schluessel sind englisch**, weil diese Datei der Anwender schreibt und
die Schweiz mehrsprachig ist. Der restliche Quelltext bleibt deutsch. Die
WERTE bleiben in der Sprache des Dokuments: `labels` sind die Etiketten,
wie sie im Text stehen, und eine Regel darf mehrere Sprachen zugleich
fuehren.

```yaml
version: 1
rules:
  - id: dossier
    name: Dossier number
    placeholder: Dossier
    type: label
    labels: ["Dossier-Nr.", "Dossier Nr.", "No de dossier",
             "N. dossier", "Dossiernummer"]
    value_form: digits_grouped
    min: 6
    max: 14

  - id: case_number
    name: Case number
    placeholder: Case
    type: label
    labels: ["Fall-Nr.", "No de cas", "N. caso", "Case no."]
    value_form: digits
    min: 3
    max: 8

  - id: project_names
    name: internal project names
    placeholder: Project
    type: wordlist
    words: ["Seerose", "Kirschbaum", "Nordwind"]
```

**Die Felder:**

| | |
|---|---|
| `id` | Kleinbuchstaben, Ziffern, Unterstrich. Wird zu `X_<id>` |
| `name` | wie die Regel in der Oberflaeche heisst |
| `placeholder` | landet als `[<placeholder>_1]` im Text |
| `type` | `label`, `wordlist` oder `regex` |
| `labels` | die Etiketten im Text — bei `label` noetig |
| `value_form` | `digits`, `digits_grouped`, `alphanumeric`, `letter_digits`, `to_end_of_line` |
| `min` / `max` | Laenge des Wertes |
| `words` | bei `wordlist` — mindestens drei Zeichen je Wort |
| `ignore_case` | Gross- und Kleinschreibung egal |
| `pattern` | bei `regex` — eigenes Muster |
| `window` | wie weit das Etikett entfernt stehen darf. Vorgabe 40 |
| `same_line` | Etikett auf derselben Zeile. Vorgabe `true` |
| `max_distance` | hoechstens so viele Woerter dazwischen. Vorgabe 3 |
| `not_after` | Woerter, nach denen NICHT gegriffen wird |

Deutsche Schluessel (`regeln`, `art`, `woerter` …) und das Feld `stage`
werden gelesen, aber nicht still: `GET /api/regeln` meldet jeden davon.
Alle Regeln laufen wie Stufe 2; eine Stufenwahl gibt es nicht.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from core.masking import Span
from core.recognizers import Recognizer, anchor_variants

from core import pfade
from core.hinweise import Abbruch

VORGABE = pfade.konfig("regeln.yaml")

# Das Regelformat ist englisch — diese Datei schreibt der Anwender, und in
# der Schweiz sind das vier Sprachen.
#
# Deutsche Schluessel werden weiter gelesen, aber nicht still: die Datei
# kommt zurueck, dazu eine Warnung, die jeden Schluessel beim Namen nennt.
# Ein hartes Abweisen legte eine laufende Einrichtung lahm; ein stilles
# Annehmen liesse zwei Formate nebeneinander stehen.
DEUTSCH = {
    "rules": "regeln",
    "name": "bezeichnung",
    "placeholder": "platzhalter",
    "type": "art",
    "words": "woerter",
    "ignore_case": "ohne_gross",
    "labels": "etiketten",
    "value_form": "wertform",
    "pattern": "muster",
    "window": "fenster",
    "same_line": "gleiche_zeile",
    "max_distance": "hoechstabstand",
    "not_after": "nicht_nach",
}

# Die Arten und die Wertformen tragen ebenfalls englische Namen — ein
# englischer Schluessel mit deutschem Wert waere eine halbe Umstellung.
ARTEN_DEUTSCH = {"wordlist": "wortliste", "label": "etikett", "regex": "regex"}

# Wertformen. Der Anwender waehlt aus dieser Liste, statt Regex zu schreiben —
# ein falsch geschriebenes Muster ist eine Fehlerquelle, die man ihm nicht
# aufhalsen sollte.
WERTFORMEN = {
    "digits": r"\d{{{min},{max}}}",
    "digits_grouped": r"\d[\d.\s'-]{{{min},{max}}}\d",
    "alphanumeric": r"[A-Za-z0-9][A-Za-z0-9.\-]{{{min},{max}}}",
    "letter_digits": r"[A-Za-z]{{1,3}}[-.\s]?\d{{{min},{max}}}",
    "to_end_of_line": r"[^\n]{{{min},{max}}}",
}
WERTFORMEN_DEUTSCH = {
    "digits": "ziffern",
    "digits_grouped": "ziffern_gruppiert",
    "alphanumeric": "alphanumerisch",
    "letter_digits": "buchstabe_ziffern",
    "to_end_of_line": "bis_zeilenende",
}


def _feld(spec: dict, name: str, vorgabe=None, altlasten=None):
    """Ein Feld der Regel — englisch, sonst deutsch, sonst die Vorgabe.

    ⚠️ `in` und nicht `get(...) or`: ein ausdrueckliches `false` oder eine
    leere Liste ist eine Angabe des Anwenders und keine fehlende. Bei
    `same_line: false` haette `or` die Vorgabe `true` zurueckgegeben und
    die Regel still anders wirken lassen, als sie dasteht.
    """
    if name in spec:
        return spec[name]
    deutsch = DEUTSCH.get(name)
    if deutsch and deutsch in spec:
        if altlasten is not None:
            altlasten.add(f"{deutsch} → {name}")
        return spec[deutsch]
    return vorgabe

# Ein Platzhalter unter drei Zeichen ist fast immer ein Fehler: «AG», «Bern»,
# «Wil» in einer Wortliste zerlegen jeden Text. Dieselbe Lehre wie bei den
# 23 Heimatorten mit zwei Zeichen (`Au`, `Rue`, `Sur`).
MIN_WORTLAENGE = 3

# Zeitschranke fuer eigene Regex. Ein unglueklich geschachtelter Ausdruck
# ((a+)+b) laeuft exponentiell und legt die App still lahm.
REGEX_BUDGET = 0.25
PROBE = ("Musterstrasse 12, 3011 Bern, Dossier 2024-1234567890 " * 200)


@dataclass(frozen=True)
class Regel:
    id: str
    bezeichnung: str
    platzhalter: str
    tag: str
    recognizer: Recognizer


def _pruefe_regex(muster: re.Pattern, id: str) -> None:
    beginn = time.perf_counter()
    muster.findall(PROBE)
    dauer = time.perf_counter() - beginn
    if dauer > REGEX_BUDGET:
        raise Abbruch(
            f"Regel {id!r}: das Muster braucht {dauer:.2f} s auf einer "
            f"Probezeile von {len(PROBE)} Zeichen. Das ist zu langsam und "
            f"deutet auf katastrophales Backtracking hin — meist geschachtelte "
            f"Quantoren wie (a+)+. Regel abgelehnt.",
            schluessel="regel_zu_langsam", id=id, dauer=f"{dauer:.2f}")


def _baue(spec: dict, altlasten: set | None = None) -> Regel:
    if not isinstance(spec, dict) or "id" not in spec:
        raise Abbruch("Eine Regel hat keine Kennung (`id`).",
                      schluessel="regel_ohne_kennung")
    id = str(spec["id"]).strip()
    if not re.fullmatch(r"[a-z0-9_]{2,32}", id):
        raise Abbruch(
            f"Regel-Kennung {id!r}: nur Kleinbuchstaben, Ziffern und "
            f"Unterstrich, 2 bis 32 Zeichen.",
            schluessel="regel_kennung", id=id)

    platzhalter = str(_feld(spec, "placeholder", altlasten=altlasten)
                      or id).strip()
    if not re.fullmatch(r"[A-Za-z0-9]{2,20}", platzhalter):
        raise Abbruch(
            f"Regel {id!r}: Platzhalter {platzhalter!r} muss alphanumerisch "
            f"sein, 2 bis 20 Zeichen — er landet als [{platzhalter}_1] im Text.",
            schluessel="regel_platzhalter", id=id, platzhalter=platzhalter)

    art = _feld(spec, "type", "label", altlasten)
    # Eine deutsche Art bei englischem Schluessel wird ebenfalls gemeldet.
    for engl, dtsch in ARTEN_DEUTSCH.items():
        if art == dtsch and dtsch != engl:
            if altlasten is not None:
                altlasten.add(f"{dtsch} → {engl}")
            art = engl
    # `stage` wird gelesen, uebergangen und gemeldet. Eine Stufenwahl fuer
    # eigene Regeln hat keine Wirkung: `merge` holt die Stufe aus der
    # Taxonomie des Packs, und `X_<id>` steht dort nicht. Nicht abweisen —
    # eine Regeldatei mit `stage` legte sonst die ganze Einrichtung lahm; und
    # nicht still uebergehen — sonst glaubte der Anwender an einen Vorrang,
    # den es nicht gibt.
    for _alt in ("stage", "stufe"):
        if _alt in spec and altlasten is not None:
            altlasten.add(f"{_alt} → ✕")
    stufe = 2
    etiketten: tuple[str, ...] = ()
    verlangt = False

    if art == "wordlist":
        woerter = [str(w) for w in _feld(spec, "words", [], altlasten)
                   if str(w).strip()]
        if not woerter:
            raise Abbruch(f"Regel {id!r}: `words` ist leer.",
                          schluessel="regel_woerter_leer", id=id)
        kurz = [w for w in woerter if len(w) < MIN_WORTLAENGE]
        if kurz:
            raise Abbruch(
                f"Regel {id!r}: zu kurze Eintraege {kurz}. Unter "
                f"{MIN_WORTLAENGE} Zeichen zerlegt eine Wortliste den ganzen "
                f"Text — «AG», «Wil» und «Au» kommen als Silbe ueberall vor.",
                schluessel="regel_woerter_kurz", id=id,
                kurz=", ".join(kurz), min=MIN_WORTLAENGE)
        # Laengste zuerst, sonst gewinnt das kuerzere Teilwort.
        alternativen = "|".join(
            re.escape(w) for w in sorted(woerter, key=len, reverse=True))
        muster = re.compile(rf"\b(?:{alternativen})\b",
                            re.IGNORECASE
                            if _feld(spec, "ignore_case", False, altlasten)
                            else 0)

    elif art == "label":
        etiketten = tuple(str(e)
                          for e in _feld(spec, "labels", [], altlasten)
                          if str(e))
        if not etiketten:
            raise Abbruch(
                f"Regel {id!r}: `labels` ist leer. Ohne Etikett wuerde die "
                f"Wertform jede beliebige Zahl im Dokument treffen.",
                schluessel="regel_etiketten_leer", id=id)
        form = _feld(spec, "value_form", "digits", altlasten)
        for engl, dtsch in WERTFORMEN_DEUTSCH.items():
            if form == dtsch and dtsch != engl:
                if altlasten is not None:
                    altlasten.add(f"{dtsch} → {engl}")
                form = engl
        if form not in WERTFORMEN:
            raise Abbruch(
                f"Regel {id!r}: Wertform {form!r} unbekannt. "
                f"Moeglich: {', '.join(sorted(WERTFORMEN))}",
                schluessel="regel_wertform", id=id, form=str(form),
                moeglich=", ".join(sorted(WERTFORMEN)))
        mn, mx = int(spec.get("min", 1)), int(spec.get("max", 20))
        if not 1 <= mn <= mx <= 200:
            raise Abbruch(f"Regel {id!r}: min/max unplausibel ({mn}/{mx}).",
                          schluessel="regel_min_max", id=id, min=mn, max=mx)
        # Bei den gruppierten Formen zaehlen die Randziffern separat.
        if form in ("digits_grouped", "letter_digits"):
            mn, mx = max(0, mn - 2), max(0, mx - 2)
        muster = re.compile(WERTFORMEN[form].format(min=mn, max=mx))
        verlangt = True

    elif art == "regex":
        roh = _feld(spec, "pattern", altlasten=altlasten)
        if not roh:
            raise Abbruch(f"Regel {id!r}: `pattern` fehlt.",
                          schluessel="regel_muster_fehlt", id=id)
        try:
            muster = re.compile(roh)
        except re.error as fehler:
            # Die Stelle ist uebersetzbar, der Text von `re` nicht.
            raise Abbruch(f"Regel {id!r}: ungueltiges Muster — {fehler}",
                          schluessel="regel_muster_ungueltig", id=id,
                          stelle=(fehler.pos or 0) + 1)
        _pruefe_regex(muster, id)
        etiketten = tuple(str(e)
                          for e in _feld(spec, "labels", [], altlasten)
                          if str(e))
        verlangt = bool(etiketten)

    else:
        raise Abbruch(
            f"Regel {id!r}: Art {art!r} unbekannt. "
            f"Moeglich: {', '.join(sorted(ARTEN_DEUTSCH))}",
            schluessel="regel_art", id=id, art=str(art),
            moeglich=", ".join(sorted(ARTEN_DEUTSCH)))

    rec = Recognizer(
        tag=f"X_{id}",
        stage=stufe,
        regex=muster,
        validator=None,
        anchor_words=tuple(sorted(
            {v for w in etiketten for v in anchor_variants(w)})),
        anchor_required=verlangt,
        anchor_window=int(_feld(spec, "window", 40, altlasten)),
        anchor_after=False,
        anchor_same_line=bool(_feld(spec, "same_line", True, altlasten)),
        anchor_max_distance=_feld(spec, "max_distance", 3, altlasten),
        anchor_not=tuple(sorted(
            {v for w in _feld(spec, "not_after", (), altlasten)
             for v in anchor_variants(w)})),
    )
    return Regel(id=id,
                 bezeichnung=str(_feld(spec, "name", altlasten=altlasten)
                                 or id),
                 platzhalter=platzhalter, tag=f"X_{id}", recognizer=rec)


def lade(pfad: str | Path | None = None, pack=None,
         altlasten: set | None = None) -> list[Regel]:
    """Regeln aus der YAML-Datei. Fehlt sie, ist das kein Fehler.

    `altlasten` ist eine Menge, in die veraltete Schluessel eingetragen
    werden — deutsche und `stage`. Ein Ausgabefeld und kein Rueckgabewert:
    `lade()` hat vier Aufrufer, und nur einer interessiert sich dafuer.
    """
    if pfad is None:
        pfad = (os.environ.get("MASCHERA_REGELN")
                or pfade.konfig("regeln.yaml"))
    pfad = Path(pfad)
    if not pfad.is_file():
        return []

    try:
        daten = yaml.safe_load(pfad.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as fehler:
        # Die Zeile ist uebersetzbar, der Text des YAML-Lesers nicht.
        marke = getattr(fehler, "problem_mark", None)
        zeile = marke.line + 1 if marke is not None else 0
        raise Abbruch(f"Regeldatei ist kein gueltiges YAML: {fehler}",
                      schluessel="regeln_kein_yaml", zeile=zeile)
    liste = _feld(daten, "rules", [], altlasten)
    regeln = [_baue(s, altlasten) for s in liste]

    kennungen = [r.id for r in regeln]
    doppelt = {k for k in kennungen if kennungen.count(k) > 1}
    if doppelt:
        raise Abbruch(f"Doppelte Regel-Kennungen: {sorted(doppelt)}",
                      schluessel="regeln_doppelt",
                      kennungen=", ".join(sorted(doppelt)))

    # Der Platzhalter-Namensraum darf nicht mit dem Pack kollidieren, sonst
    # zeigt [Name_1] auf zwei verschiedene Werte und die Rueckfuehrung ist
    # kaputt — ein Fehler, den man erst beim Zurueckschreiben bemerkt.
    if pack is not None:
        belegt = {t.placeholder for t in pack.get_tags() if t.placeholder}
        kollision = {r.platzhalter for r in regeln} & belegt
        if kollision:
            raise Abbruch(
                f"Platzhalter {sorted(kollision)} sind im Pack bereits "
                f"vergeben. Anderen Namen waehlen — sonst zeigt derselbe "
                f"Platzhalter auf zwei verschiedene Werte.",
                schluessel="regel_platzhalter_vergeben",
                platzhalter=", ".join(sorted(kollision)))
    return regeln


def erkenne(text: str, regeln: list[Regel]) -> list[Span]:
    """Treffer der Benutzerregeln. Quelle `benutzer`, damit sie im Bericht
    von Modell- und Packtreffern unterscheidbar sind."""
    out: list[Span] = []
    for regel in regeln:
        rec = regel.recognizer
        for m in rec.regex.finditer(text):
            start, end = m.start(), m.end()
            if rec.anchor_words:
                start = rec.trim_to_anchor(text, start, end)
            if rec.blocked(text, start, end):
                continue
            if rec.anchor_required and not rec.has_anchor(text, start, end):
                continue
            out.append(Span(regel.tag, start, end, source="benutzer"))
    return out


def aktionen(regeln: list[Regel]) -> dict[str, str]:
    return {r.tag: "mask" for r in regeln}


def platzhalter(regeln: list[Regel]) -> dict[str, str]:
    return {r.tag: r.platzhalter for r in regeln}


def stufen(regeln: list[Regel]) -> dict[str, int]:
    return {r.tag: r.recognizer.stage for r in regeln}
