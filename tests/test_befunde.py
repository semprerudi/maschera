"""Zwei gemessene Befunde: Gesetzesdatum und die `&`-Spanne.

    python3 tests/test_befunde.py

⚠️ **Diese Pruefung misst Stufe 2, nicht die ganze Kette.** `recognize()`
liefert nur Muster und Pruefsummen. Was hier gruen ist, kann in der vollen
Kette trotzdem maskiert werden — das Modell auf Stufe 3 liefert dieselbe
Spanne noch einmal, und ein Muster, das SCHWEIGT, verhindert nichts. Die
Rueckblicke im `DATE`-Muster greifen nachweislich (`--ohne-modell` laesst
«25. September 2020» im Klartext), aber Stufe 2 kann HINZUFUEGEN, nicht
VERBIETEN.

⚠️ Beide Richtungen zaehlen, aber nicht gleich viel.

Ein Gesetzesdatum, das maskiert wird, ist **Uebermaskierung**: der Text wird
fuer das Sprachmodell schlechter lesbar, es geht aber nichts hinaus. Ein
echtes Datum, das NICHT maskiert wird, ist ein **Leck** — und Geburtsdaten
gehoeren zu den empfindlichsten Daten ueberhaupt.

Die Pruefungen unter «LECK» wiegen deshalb schwerer als die unter
«Uebermaskierung». Wer die Rueckblicke erweitert, muss zuerst hier
nachsehen: jeder zusaetzliche Rueckblick kann ein echtes Datum treffen.

Laeuft ohne Modell — Stufe 2 ist reine Mustererkennung.
"""
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from core.recognizers import recognize  # noqa: E402

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def tags(text: str, tag: str) -> list[str]:
    return [text[s.start:s.end] for s in recognize(text, "ch") if s.tag == tag]


# ---------------------------------------------------------------------------
print("1. Gesetzesdaten: Stufe 2 schweigt — TEILWEISE behoben")
# «Bundesgesetz vom 19. Juni 1992» ist der Name des Gesetzes, kein
# Personendatum.
#
# ⚠️ Was hier gruen ist, heisst NUR: das Muster liefert die Spanne nicht.
# In der vollen Kette setzt das Modell sie trotzdem. Gemessen an allen drei
# Amtssprachen in `edoeb-berichtigung-*`:
#
#     des Bundesgesetzes vom [DATE_2] ueber den Datenschutz
#     de la loi federale du [DATE_2] sur la protection
#     della legge sulla protezione dei dati del [DATE_2]
#
# Vollstaendig geloest wird das nur im Training — Vorlagen mit
# Gesetzeszitierungen, in denen das Datum NICHT markiert ist. Ein
# Verbotsmechanismus in `merge` waere der andere Weg, aber ein Eingriff in
# den empfindlichsten Teil der Kette fuer eine Uebermaskierung ist das
# falsche Risiko.
#
# Wirksam ist der Rueckblick heute: in `--ohne-modell` und ueberall, wo das
# Modell die Stelle nicht selbst findet.
STEHEN = [
    "Bundesgesetz vom 19. Juni 1992 über den Datenschutz",
    "Verordnung vom 31. August 2022 über die Datenbearbeitung",
    "Beschluss vom 12.05.2021 des Gerichts",
    "Datenschutzgesetz vom 25. September 2020",
    "Loi fédérale du 25 septembre 2020 sur la protection",
    "Ordonnance du 31 août 2022 sur la protection",
    "Legge federale del 25 settembre 2020 sulla protezione",
    "Ordinanza del 31 agosto 2022",
]
for t in STEHEN:
    g = tags(t, "DATE")
    check(not g, f"Gesetzesdatum maskiert: {g} in {t[:44]!r}")
print(f"   OK   {len(STEHEN)} Zitierungen, vier Sprachen")

# ---------------------------------------------------------------------------
print("2. Echte Daten werden maskiert — hier waere ein Ausfall ein LECK")
# ⚠️ Die drei mittleren tragen dasselbe «vom» / «du» wie eine Gesetzes-
# zitierung. Genau daran scheitert ein zu breiter Negativanker.
LECK = [
    ("Gemäss DSG hat Frau Müller am 14.03.2026 verlangt", "14.03.2026"),
    ("Ihr Geburtsdatum ist der 03.11.1981.", "03.11.1981"),
    ("Das Gesetz gilt. Am 14.03.2026 kam die Anfrage", "14.03.2026"),
    ("Ihr Schreiben vom 14. März 2026 haben wir erhalten", "14. März 2026"),
    ("Der Vertrag vom 01.02.2024 wurde gekündigt", "01.02.2024"),
    ("La lettre du 14.03.2026 nous est parvenue", "14.03.2026"),
    ("Nato il 03.11.1981 a Lugano", "03.11.1981"),
    ("Gemäss Art. 8 des Bundesgesetzes über den Datenschutz "
     "hat sie am 14.03.2026 geschrieben", "14.03.2026"),
]
for t, erwartet in LECK:
    g = tags(t, "DATE")
    check(erwartet in g, f"LECK — {erwartet!r} nicht gefunden in {t[:44]!r}")
print(f"   OK   {len(LECK)} echte Daten, keines unterdrueckt")

# ---------------------------------------------------------------------------
print("3. Beides im selben Text")
gemischt = ("Gemäss Art. 8 des Bundesgesetzes vom 19. Juni 1992 über den "
            "Datenschutz hat Frau Brülhart am 14.03.2026 Auskunft verlangt. "
            "Ihr Geburtsdatum ist der 03.11.1981.")
g = tags(gemischt, "DATE")
check(g == ["14.03.2026", "03.11.1981"],
      f"erwartet zwei echte Daten, gefunden {g}")
print(f"   OK   {g}")

# ---------------------------------------------------------------------------
print("4. `&` bricht die Firmenspanne nicht mehr")
# ⚠️ Das WAR ein Leck: das Modell brach am kaufmaennischen Und, und dahinter
# fing nichts wieder an — «Strub & Partner GmbH» hinterliess drei offene
# Woerter. `ORG_FIRMA` faengt es auf Stufe 2 ab, also ohne Modell.
FIRMEN = [
    ("Die Strub & Partner GmbH hat bestätigt", "Strub & Partner GmbH"),
    ("Meier und Partner AG in Bern", "Meier und Partner AG"),
    ("Rossi e Bianchi SA a Lugano", "Rossi e Bianchi SA"),
    ("Dupont et Fils Sàrl à Genève", "Dupont et Fils Sàrl"),
    ("Huber + Kern Treuhand AG", "Huber + Kern Treuhand AG"),
]
for t, erwartet in FIRMEN:
    g = tags(t, "ORG")
    check(erwartet in g, f"{erwartet!r} nicht gefunden, sondern {g}")
print(f"   OK   {len(FIRMEN)} Firmennamen mit Bindeglied")

print("5. Das Muster greift nicht ueber den Namen hinaus")
# ⚠️ Ein Muster, das systematisch ueber den Wert hinausgreift, erzeugt
# Teiltreffer statt Schutz. Im Deutschen ist JEDES vorangehende Substantiv
# grossgeschrieben — «Glaeubiger» laesst sich von «Strub» nicht
# unterscheiden. Das Bindeglied an fester Stelle loest es.
ZUVIEL = [
    ("Gläubiger Limmat Bau GmbH mahnt", "Gläubiger"),
    ("Zwischen Alpin Treuhand AG und der", "Zwischen"),
]
for t, darfnicht in ZUVIEL:
    g = tags(t, "ORG")
    check(not any(darfnicht in x for x in g),
          f"greift ueber den Namen hinaus: {g} in {t[:40]!r}")
print(f"   OK   {len(ZUVIEL)} Faelle ohne Uebergriff")

print("6. Firmen OHNE Bindeglied haengen weiter am Modell")
# Kein Fehler, sondern der dokumentierte Preis des engeren Schnitts. Diese
# Pruefung haelt fest, dass es so IST — damit niemand glaubt, Stufe 2 decke
# Firmennamen ab.
for t in ("Die Smart Service AG hat bestätigt",
          "Maschera Immobilien AG hat bestätigt"):
    g = tags(t, "ORG")
    check(not g, f"unerwartet doch von Stufe 2 gefunden: {g} — dann gehoert "
                 f"der Kommentar in patterns.yaml korrigiert")
print("   OK   2 Faelle, wie dokumentiert offen")

# ---------------------------------------------------------------------------
print("7. Ein Tag OHNE Schwelle bricht die Vertrauensliste nicht")
# Sechs Tags fuehren bewusst keine Schwelle: AHVN13, UID, IBAN,
# QR_REFERENCE, CREDITCARD, GLN. Dort entscheidet die Pruefsumme, und eine
# Schwelle waere falsch.
#
# ⚠️ `core/inference.py` filtert nur, wenn eine Schwelle DA ist. Ein
# schwellenloses Tag aus dem MODELL laeuft also ungefiltert durch — und
# die Zeile in `filter_document.py`, die genau das anzeigen sollte, warf
# `TypeError: unsupported format string passed to NoneType`. Sie riss den
# ganzen Lauf mitsamt Bericht mit, NACH dem Modelldurchgang.
#
# Ausgeloest hat es erst eine Probe mit erfundenen Nummern; in echten
# Dokumenten kamen diese sechs Tags immer aus Stufe 1. Ein Fehler, der
# jahrelang nur auf einen Eingang wartete.
from packs import load_pack as _lade  # noqa: E402

_pack = _lade("ch")
_schwellen = dict(_pack.get_thresholds())
_ohne = [t.tag for t in _pack.get_tags() if _schwellen.get(t.tag) is None]
check(_ohne, "kein einziges Tag ohne Schwelle — dann misst diese Pruefung "
             "nichts mehr und die Begruendung oben ist veraltet")
for _tag in _ohne + ["FULLNAME"]:
    _sch = _schwellen.get(_tag)
    # Wortgleich mit `filter_document.py`. Faellt die Zeile dort auseinander,
    # faellt sie hier zuerst.
    _spalte = "ohne" if _sch is None else f"{_sch:.2f}"
    try:
        f"    {_tag:<18}{_spalte:>6}{0.5:>8.2f}{0.5:>8.2f}{1:>6}"
    except TypeError as _e:
        check(False, f"Vertrauensliste bricht bei {_tag}: {_e}")
print(f"   OK   {len(_ohne)} Tags ohne Schwelle, Anzeige haelt")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Stufe 2 in Ordnung — Befund 1 vollstaendig, Befund 6 teilweise.")
