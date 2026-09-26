"""Test der Regex-Recognizer (SPEC §3 Stufe 1 und 2).

    python3 tests/test_patterns.py

Drei Ebenen:
  1. Treffer in DE/FR/IT/EN
  2. Decoys und Negativanker — was NICHT anschlagen darf
  3. Falsch-Positiv-Messung: wie stark ist eine Prüfsumme wirklich?
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.recognizers import recognize  # noqa: E402
from packs.ch.validators.checksums import is_valid_gln, luhn_check_digit  # noqa: E402

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def tags(text: str) -> set[str]:
    return {s.tag for s in recognize(text)}


def values(text: str, tag: str) -> list[str]:
    return [text[s.start : s.end] for s in recognize(text) if s.tag == tag]


# ---------------------------------------------------------------------------
# 1. Positivfälle, vier Sprachen
# ---------------------------------------------------------------------------

print("1. Treffer in vier Sprachen")

POSITIVE = [
    ("de", "Versichertennummer 756.9217.0769.85", "AHVN13"),
    ("fr", "Numéro AVS: 756.9217.0769.85", "AHVN13"),
    ("de", "Firma eingetragen unter CHE-116.281.710 MWST", "UID"),
    ("it", "Iscritta con CHE-116.281.710 IVA", "UID"),
    ("de", "Konto CH93 0076 2011 6238 5295 7", "IBAN"),
    ("de", "EGID 1234567 des Gebäudeidentifikators", "EGID"),
    ("fr", "identificateur fédéral de bâtiment 1234567", "EGID"),
    ("it", "identificatore federale dell'edificio 1234567", "EGID"),
    ("en", "federal building identifier 1234567", "EGID"),
    ("de", "EWID 12", "EWID"),
    ("fr", "identificateur de logement 12", "EWID"),
    ("de", "BFS-Nr. 351 der Gemeinde", "MUNICIPALITY_ID"),
    ("fr", "numéro OFS 6621", "MUNICIPALITY_ID"),
    ("de", "Telefon +41 79 123 45 67", "PHONE"),
    ("de", "Telefon 044 123 45 67", "PHONE"),
    ("de", "Fahrzeug ZH 123456", "PLATE"),
    ("de", "wohnhaft in 3011 Bern", "ZIPCODE"),
    ("fr", "domicilié à 1204 Genève", "ZIPCODE"),
    ("de", "Der Betrag von CHF 1'250.00 ist geschuldet", "AMOUNT"),
    ("fr", "Le montant de 1250 francs est dû", "AMOUNT"),
    ("it", "L'importo di 1250 franchi è dovuto", "AMOUNT"),
    ("de", "Er besitzt Ausweis B", "PERMIT_TYPE"),
    ("fr", "Il détient le permis C", "PERMIT_TYPE"),
    ("it", "Titolare del permesso Ci", "PERMIT_TYPE"),
    ("de", "ZSR-Nr. A123456 der santésuisse", "ZSR_RCC"),
    ("de", "Patientennummer P-2024-0815", "PATIENT_ID"),
    ("fr", "numéro de patient P-2024-0815", "PATIENT_ID"),
    ("de", "Parzelle 1234 in der Gemeinde", "PARCEL"),
    ("fr", "parcelle 1234", "PARCEL"),
    ("de", "Kontakt: rita.bertschi@example.ch", "EMAIL"),
    ("de", "Siehe https://www.example.ch/formular", "URL"),
    ("de", "Server 192.168.1.186", "IPADDRESS"),
    ("de", "Reisepass X1234567 ausgestellt", "IDDOC"),
    ("de", "Versichertenkarte 80756123456789012345", "INSURANCE_CARD"),
    ("de", "Referenz 21 00000 00003 13947 14300 09017", "QR_REFERENCE"),
    ("de", "GLN der Medizinalperson: 7601003000009", "GLN"),
    ("de", "Hans Meier, von Hautemorges VD", "PLACE_OF_ORIGIN"),
    ("de", "Heimatort Biel/Bienne BE", "PLACE_OF_ORIGIN"),
    ("de", "Er ist von Hautemorges VD und wohnt hier.", "PLACE_OF_ORIGIN"),
    ("fr", "Il est originaire de Vaz/Obervaz GR", "PLACE_OF_ORIGIN"),
    ("it", "attinente di Sant'Antonino TI", "PLACE_OF_ORIGIN"),
    ("de", "Heimatort: Ursy (Montet (Glâne)) FR", "PLACE_OF_ORIGIN"),
]

missed = []
for lang, text, expected in POSITIVE:
    found = tags(text)
    ok = expected in found
    if not ok:
        missed.append((lang, expected, text))
    print(f"   {'OK  ' if ok else 'FEHL'} [{lang}] {expected:<16} {text[:46]}")

check(not missed, f"{len(missed)} Positivfaelle nicht erkannt: "
                  f"{[(m[0], m[1]) for m in missed]}")

# ---------------------------------------------------------------------------
# 2. Was NICHT anschlagen darf
# ---------------------------------------------------------------------------

print("\n2. Decoys und Negativanker")

NEGATIVE = [
    ("756.9217.0769.86", "AHVN13", "AHV-Nummer mit falscher Pruefziffer"),
    ("CHE-116.281.711", "UID", "UID mit falscher Pruefziffer"),
    ("CH93 0076 2011 6238 5296 0", "IBAN", "erfundene IBAN"),
    ("Der Vermögensfreibetrag von 4000 Franken", "AMOUNT", "Freibetrag = Decoy"),
    ("Die Gebühr beträgt CHF 50.00", "AMOUNT", "Gebuehr = Decoy"),
    ("Gestützt auf Art. 6 Abs. 1 Bst. i RHG", "PERMIT_TYPE", "Rechtsverweis"),
    ("Die Zahl 1234567 steht ohne Kontext", "EGID", "EGID ohne Anker"),
    ("Wohnung 12 im zweiten Stock", "EWID", "EWID ohne Anker"),
    ("Nummer 351 auf der Liste", "MUNICIPALITY_ID", "BFS-Nr ohne Anker"),
    ("Die Nummer A123456", "ZSR_RCC", "ZSR ohne Anker"),
    ("Grundstueck der Nachbarn", "PARCEL", "Parzelle ohne Zahl"),
    ("innert 30 Tagen seit Eröffnung", "AMOUNT", "Frist ist kein Betrag"),
    ("Version 2.1, Stand 01.2026", "IPADDRESS", "Versionsnummer"),
    ("7601003000009 steht ohne Kontext", "GLN", "GLN ohne Anker"),
    ("Die Firma hat ihren Sitz in Zug ZG", "PLACE_OF_ORIGIN", "Sitz ist kein Heimatort"),
    ("Er wohnt in Bern BE", "PLACE_OF_ORIGIN", "Wohnort ist kein Heimatort"),
    ("Die Muster Treuhand AG hat geantwortet", "PLACE_OF_ORIGIN",
     "Firma auf AG ist kein Heimatort — 'AG' ist auch ein Kantonskuerzel"),
]

# --- 2b. Das Behoerdenmuster darf nicht ueber den Namen hinausfressen -------
#
# Eine Fortsetzung, die beliebige Woerter aufnimmt, greift weiter, sobald
# {ORG} mitten in einem Satz steht statt in einer Signatur mit
# Zeilenumbruch. Eine Fortsetzung braucht eine Einschraenkung dessen, was
# ein Fortsetzungswort sein darf.
print("\n2b. Behoerdenmuster: der Name endet, wo der Satz weitergeht")

GRENZE = [
    ("Federal Office of Topography has approved the terms", "Federal Office of Topography"),
    ("Bundesamt fuer Migration hat die Unterlagen bereits", "Bundesamt fuer Migration"),
    ("Bundesamt für Statistik wurde bereits informiert", "Bundesamt für Statistik"),
    ("Office fédéral de la statistique ne peut pas confirmer", "Office fédéral de la statistique"),
    ("Ufficio federale di topografia non ha ancora risposto", "Ufficio federale di topografia"),
    # Positivfaelle: die vollstaendigen Namen muessen ganz erkannt bleiben.
    ("Office fédéral de la santé publique", "Office fédéral de la santé publique"),
    ("Département fédéral des finances", "Département fédéral des finances"),
    ("Ufficio federale della sanità pubblica", "Ufficio federale della sanità pubblica"),
    ("Dipartimento federale degli affari esteri", "Dipartimento federale degli affari esteri"),
    ("Federal Department of Home Affairs", "Federal Department of Home Affairs"),
    # Eine Mindestlaenge fuer kleingeschriebene Fortsetzungen genuegt nicht:
    # italienische und franzoesische VERBEN — «risultano», «essere» — bestehen
    # sie muehelos. Deshalb eine GESCHLOSSENE Sachgebietsliste, abgeleitet aus
    # `_BEH_SACH` in nomenclatures/build.py. Ein Verb steht dort nicht.
    ("presso Ufficio federale di statistica risultano essere",
     "Ufficio federale di statistica"),
    ("presso Ufficio delle contribuzioni risultano essere",
     "Ufficio delle contribuzioni"),
    ("Office fédéral de la statistique a rendu sa décision",
     "Office fédéral de la statistique"),
    # Der Punkt am Wortende ist ein SATZENDE, kein Namensteil. Er stand im
    # Zeichenvorrat, damit «St. Gallen» funktioniert — und nahm dafuer jeden
    # Schlusspunkt mit.
    ("Republik und Kanton Freiburg. Der Entscheid",
     "Republik und Kanton Freiburg"),
    ("Repubblica e Cantone Vallese. La decisione",
     "Repubblica e Cantone Vallese"),
    ("Staat und Kanton St. Gallen", "Staat und Kanton St. Gallen"),
    ("Republik und Kanton Appenzell Ausserrhoden",
     "Republik und Kanton Appenzell Ausserrhoden"),
]

# --- 2c. Firmennamen mit Bindeglied ----------------------------------------
#
# «Strub & Partner GmbH» — das Modell bricht gern am kaufmaennischen Und,
# und dahinter faengt nichts wieder an.
#
# Die NEIN-Faelle sind der eigentliche Test: ein Muster, das beliebig viele
# grossgeschriebene Woerter vor der Rechtsform zulaesst, frisst
# «Glaeubiger», «Zwischen», «Between» mit. Das Bindeglied an fester Stelle
# verhindert es.
GRENZE += [
    ("Die Strub & Partner GmbH hat geantwortet", "Strub & Partner GmbH"),
    ("Glaeubiger Strub & Partner GmbH", "Strub & Partner GmbH"),
    ("Rechnung der Müller&Sohn AG", "Müller&Sohn AG"),
    ("Contrat avec Dupont & Fils Sàrl", "Dupont & Fils Sàrl"),
    ("Beratung durch Meier und Partner AG", "Meier und Partner AG"),
]

print("\n2c. Firmenmuster greift nicht auf das Wort davor ueber")
OHNE_TREFFER = [
    "Zwischen Limmat Bau GmbH und dem Kunden",
    "Glaeubiger Alpin Treuhand AG",
    "Wir haben die Unterlagen an die AG geschickt",
    "Sehr geehrte Damen und Herren",
]
for text in OHNE_TREFFER:
    treffer = [text[h.start:h.end] for h in recognize(text) if h.tag == "ORG"]
    # Ein Behoerdenmuster darf hier greifen; das Firmenmuster nicht.
    zuviel = [t for t in treffer if "GmbH" in t or t.endswith(" AG")]
    check(not any(t.split()[0] in ("Zwischen", "Glaeubiger", "Wir", "Sehr")
                  for t in zuviel),
          f"Firmenmuster frisst das Wort davor: {zuviel} in {text!r}")
print(f"   OK   {len(OHNE_TREFFER)} Faelle ohne Uebergriff")

for text, soll in GRENZE:
    treffer = [h for h in recognize(text) if h.tag == "ORG"]
    gefunden = [text[h.start:h.end] for h in treffer]
    check(soll in gefunden,
          f"Behoerdenmuster: {soll!r} nicht sauber abgegrenzt -> {gefunden}")
    zuviel = [g for g in gefunden if g != soll and soll in g]
    check(not zuviel, f"Behoerdenmuster frisst weiter: {zuviel}")
print(f"   OK   {len(GRENZE)} Grenzfaelle sauber abgeschnitten")

for text, forbidden, why in NEGATIVE:
    found = tags(text)
    ok = forbidden not in found
    check(ok, f"{forbidden} faelschlich erkannt in {text!r} ({why})")
    print(f"   {'OK  ' if ok else 'FEHL'} {forbidden:<16} abgelehnt: {why}")

# ---------------------------------------------------------------------------
# 3. Wie stark ist eine Pruefsumme allein?
# ---------------------------------------------------------------------------

print("\n3. Falsch-Positiv-Rate der Pruefsummen auf Zufallsziffern")

rng = random.Random(4711)
N = 20000

gln_hits = sum(
    1 for _ in range(N)
    if is_valid_gln("".join(str(rng.randint(0, 9)) for _ in range(13)))
)
luhn_hits = 0
for _ in range(N):
    d = "".join(str(rng.randint(0, 9)) for _ in range(16))
    if luhn_check_digit(d[:-1]) == int(d[-1]):
        luhn_hits += 1

print(f"   EAN-13 auf 13 Zufallsziffern : {100*gln_hits/N:5.2f} %")
print(f"   Luhn auf 16 Zufallsziffern   : {100*luhn_hits/N:5.2f} %")
print("   -> Pruefsumme allein ist kein Beweis. GLN braucht deshalb einen")
print("      Anker, CREDITCARD eine echte Kartenkennung im Muster.")

check(8 < 100 * gln_hits / N < 12, "EAN-13-Trefferquote unerwartet")
check(8 < 100 * luhn_hits / N < 12, "Luhn-Trefferquote unerwartet")

# Gegenprobe: mit Kartenkennung im Muster faellt Zufall praktisch weg
random_digits = " ".join(
    "".join(str(rng.randint(0, 9)) for _ in range(16)) for _ in range(2000)
)
cc = len([s for s in recognize(random_digits) if s.tag == "CREDITCARD"])
print(f"   CREDITCARD auf 2000 Zufallszahlen mit Muster+Luhn: {cc} Treffer "
      f"({100*cc/2000:.2f} %)")

# ---------------------------------------------------------------------------
# USERNAME: Paarschreibweise — «username/password» ist ein Wortpaar, kein
# Etikett mit Wert.
# ---------------------------------------------------------------------------
print("\n9. USERNAME — Etikett gegen Paarschreibweise")

def _user(text):
    return [text[s.start:s.end] for s in recognize(text) if s.tag == "USERNAME"]

for text, erwartet in [
    ("Benutzername: a.bertschinger", ["a.bertschinger"]),
    ("Login mmueller seit gestern", ["mmueller"]),
    ("Anmeldename=p.dupont", ["p.dupont"]),
    ("Username\tk.steiner", ["k.steiner"]),
    ("Kontoname: rvonwil", ["rvonwil"]),
    # Der Befund: der Anker griff, "password" wurde zum Benutzernamen.
    ("ORA-01017: invalid username/password", []),
    # Und die Nachfolgefalle: ein Lookbehind nur gegen / verschob den Treffer
    # um ein Zeichen ("assword") — Teilmaskierung statt keiner Maskierung.
    ("nom d'utilisateur/mot de passe", []),
]:
    got = _user(text)
    check(got == erwartet, f"USERNAME {text!r} -> {got}, erwartet {erwartet}")
    print(f"   {text!r:<40} -> {got}")

# ---------------------------------------------------------------------------
# IPADDRESS: Uhrzeit ist keine IPv6. Die Kopfzeile `Date:` einer Mail darf
# nicht zu `[IP_1]` werden.
# ---------------------------------------------------------------------------
print("\n10. IPADDRESS — Uhrzeit gegen IPv6")

def _ip(text):
    return [text[s.start:s.end] for s in recognize(text) if s.tag == "IPADDRESS"]

for text, erwartet in [
    ("Verbindung zu 10.42.7.19 auf Port 1521", ["10.42.7.19"]),
    ("Server 2001:0db8:85a3:0000:0000:8a2e:0370:7334 erreichbar",
     ["2001:0db8:85a3:0000:0000:8a2e:0370:7334"]),
    ("Adresse fe80::1ff:fe23:4567:890a im Log", ["fe80::1ff:fe23:4567:890a"]),
    ("localhost ::1 antwortet", ["::1"]),
    # Der Befund und seine Geschwister:
    ("Date: Mon, 03 Aug 2026 08:12:00 +0200", []),
    ("Absturz um 14:30:59 protokolliert", []),
    ("Dauer 1:02:33 Stunden", []),
    ("Zeitraum 08:00-17:00", []),
]:
    got = _ip(text)
    check(got == erwartet, f"IPADDRESS {text!r} -> {got}, erwartet {erwartet}")
    print(f"   {text!r:<58} -> {got}")

# ---------------------------------------------------------------------------
# ORG: Behoerdennamen — Zefix ist das HANDELSregister, Behoerden stehen
# dort nicht.
# ---------------------------------------------------------------------------
print("\n11. ORG — Behoerdennamen viersprachig")

def _org(text):
    treffer = [text[s.start:s.end] for s in recognize(text) if s.tag == "ORG"]
    return max(treffer, key=len) if treffer else None

for text, erwartet in [
    ("Bundesamt für Gesundheit", "Bundesamt für Gesundheit"),
    ("Bildungs- und Kulturdepartement BKD",
     "Bildungs- und Kulturdepartement BKD"),
    ("Repubblica e Cantone Ticino", "Repubblica e Cantone Ticino"),
    ("Dipartimento delle Istituzioni", "Dipartimento delle Istituzioni"),
    ("Sezione della popolazione", "Sezione della popolazione"),
    ("Ufficio dello stato civile", "Ufficio dello stato civile"),
    ("Office des poursuites", "Office des poursuites"),
    ("Service de la population", "Service de la population"),
    ("Einwohnergemeinde", "Einwohnergemeinde"),
    ("Betreibungsamt", "Betreibungsamt"),
    # Der Ortsname gehoert NICHT dazu — er ist eine eigene CITY-Spanne.
    ("Controllo abitanti di Bern", "Controllo abitanti"),
    # Italienisch auch ohne Artikel, und mit einbuchstabigem «e»:
    ("Sezione popolazione", "Sezione popolazione"),
    ("Settore giuridico e vigilanza", "Settore giuridico e vigilanza"),
    ("Gemeindeverwaltung", "Gemeindeverwaltung"),
    # `-verwaltung` als Suffix war zu generisch:
    ("eine Schnittstelle zur Geschaeftsverwaltung oder", None),
    ("Die Vermoegensverwaltung kostet", None),
    # Falsch-Positiv-Kandidaten:
    ("Die Gesamtkosten betragen 500 Franken.", None),
    ("Der Beamte prüfte das Gesuch.", None),
    ("Er wohnt im Kanton Bern.", None),
]:
    got = _org(text)
    check(got == erwartet, f"ORG {text!r} -> {got!r}, erwartet {erwartet!r}")
    print(f"   {text!r:<54} -> {got!r}")

# ---------------------------------------------------------------------------
# Geschlossene Wertlisten aus dem Amtlichen Katalog der Merkmale (BFS).
# Verankert am Merkmalsnamen — ohne Anker traefe «ledig» in «lediglich».
# ---------------------------------------------------------------------------
print("\n12. Katalog der Merkmale — verankerte Auspraegungen")

for text, tag, erwartet in [
    ("Zivilstand: verheiratet", "MARITALSTATUS", "verheiratet"),
    ("État civil: célibataire", "MARITALSTATUS", "célibataire"),
    ("Stato civile: coniugato", "MARITALSTATUS", "coniugato"),
    ("Zivilstand: in eingetragener Partnerschaft", "MARITALSTATUS",
     "in eingetragener Partnerschaft"),
    ("Konfession: römisch-katholisch", "RELIGION", "römisch-katholisch"),
    ("Geschlecht: weiblich", "SEX", "weiblich"),
    # Formulare schreiben die Kurzform. Sicher nur durch die enge Bindung:
    ("Geschlecht: w", "SEX", "w"),
    ("Sesso: f", "SEX", "f"),
    ("Die Wohnung ist 80 m gross", "SEX", None),
    ("Siehe Anhang f und Beilage m", "SEX", None),
    ("Meldeverhältnis: Hauptwohnsitz", "RESIDENCE_STATUS", "Hauptwohnsitz"),
    # Ohne Anker darf NICHTS greifen:
    ("Die Gebuehr betraegt lediglich 50 Franken.", "MARITALSTATUS", None),
    ("Er ist ledig und wohnt in Bern.", "MARITALSTATUS", None),
]:
    treffer = [text[s.start:s.end] for s in recognize(text) if s.tag == tag]
    got = max(treffer, key=len) if treffer else None
    check(got == erwartet, f"{tag} {text!r} -> {got!r}, erwartet {erwartet!r}")
    print(f"   {text!r:<46} -> {got!r}")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Problem(e):")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
