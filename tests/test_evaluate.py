"""Test der Auswertung (SPEC §4, §11).

    python3 tests/test_evaluate.py

Prueft, dass die Leckrate das misst, was sie messen soll: ein verpasster
Identifikator muss schwerer wiegen als ein verpasstes Kontexttag.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.evaluate import evaluate, format_report  # noqa: E402
from core.injector import generate  # noqa: E402
from core.masking import Span  # noqa: E402
from core.recognizers import recognize  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")
failures: list[str] = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


text = "Hans Meier, AHV 756.9217.0769.85, Kanton BE"
gold = [Span("GIVENNAME", 0, 4), Span("FULLNAME", 5, 10),
        Span("AHVN13", 16, 32), Span("CANTON", 41, 43)]

print("1. Perfekte Vorhersage")
r = evaluate([(text, gold, list(gold))], PACK)
check(r.leak_rate == 0.0, f"Leckrate muesste 0 sein: {r.leak_rate}")
check(r.micro_f1 == 1.0, f"F1 muesste 1 sein: {r.micro_f1}")
print(f"   OK   Leckrate {100*r.leak_rate:.2f} %, F1 {r.micro_f1:.3f}")

print("\n2. Gewichtung: AHV-Nummer verpasst vs. Kanton verpasst")
ohne_ahv = evaluate([(text, gold, [g for g in gold if g.tag != "AHVN13"])], PACK)
ohne_kanton = evaluate([(text, gold, [g for g in gold if g.tag != "CANTON"])], PACK)
check(ohne_ahv.leak_rate > 0.3, f"AHV-Leck zu leicht gewichtet: {ohne_ahv.leak_rate}")
check(ohne_kanton.leak_rate == 0.0,
      f"CANTON ist tag_only und kann gar nicht lecken: {ohne_kanton.leak_rate}")
print(f"   OK   AHVN13 fehlt  -> Leckrate {100*ohne_ahv.leak_rate:5.1f} %, "
      f"F1 {ohne_ahv.micro_f1:.3f}")
print(f"   OK   CANTON fehlt  -> Leckrate {100*ohne_kanton.leak_rate:5.1f} %, "
      f"F1 {ohne_kanton.micro_f1:.3f}")
print("   -> Gleicher F1-Verlust, voellig verschiedene Tragweite.")

print("\n3. Teiltreffer schuetzt teilweise")
kurz = [Span("AHVN13", 16, 28)] + [g for g in gold if g.tag != "AHVN13"]
r3 = evaluate([(text, gold, kurz)], PACK)
check(0 < r3.leak_rate < ohne_ahv.leak_rate,
      f"Teiltreffer muesste zwischen 0 und Vollverlust liegen: {r3.leak_rate}")
print(f"   OK   4 von 16 Zeichen ungeschuetzt -> Leckrate {100*r3.leak_rate:.1f} %")

print("\n3b. Umetikettierung ist KEIN Leck")
# "KL-2023-4471" als CASE_ID statt PATIENT_ID erkannt: der Wert ist maskiert,
# nur das Etikett stimmt nicht. Das ist kein Leck — ein Mass, das solche
# Faelle als Leck zaehlt, weist eine zu hohe Rate aus.
falsch_etikettiert = [Span("CASE_ID", 16, 32)] + [g for g in gold if g.tag != "AHVN13"]
r3b = evaluate([(text, gold, falsch_etikettiert)], PACK)
check(r3b.leak_rate == 0.0,
      f"Umetikettierung darf nicht als Leck zaehlen: {r3b.leak_rate}")
check(r3b.per_tag["AHVN13"].recall == 0.0,
      "Tagtreue muss trotzdem als Fehler in Precision/Recall erscheinen")
print(f"   OK   Leckrate {100*r3b.leak_rate:.1f} %, "
      f"AHVN13-Recall {r3b.per_tag['AHVN13'].recall:.3f} — Wert geschuetzt, "
      f"Etikett falsch")

print("\n4. Uebermaskierung wird getrennt ausgewiesen")
zuviel = list(gold) + [Span("CITY", 34, 40)]
r4 = evaluate([(text, gold, zuviel)], PACK)
check(r4.leak_rate == 0.0, "Uebermaskierung darf die Leckrate nicht erhoehen")
check(len(r4.over) == 1, f"Uebermaskierung nicht gezaehlt: {r4.over}")
print(f"   OK   Leckrate {100*r4.leak_rate:.1f} %, {len(r4.over)} Uebermaskierung")

print("\n5. Grundlinie: nur Regex, ohne Modell, auf 300 Beispielen")
cases = [(e.text, e.spans, recognize(e.text)) for e in generate(300, seed=11)]
r5 = evaluate(cases, PACK)
print()
print(format_report(r5, top=5))
check(r5.leak_rate < 1.0, "Leckrate muss zwischen 0 und 1 liegen")
check(r5.per_tag["AHVN13"].recall > 0.95,
      f"Regex muesste AHVN13 fast vollstaendig finden: {r5.per_tag['AHVN13'].recall}")

print("\n6. Je Dokument: die Gesamtzahl verdeckt den Einzelfall")
# Waechst ein Testset um leichtere Dokumente, steigt der Micro-F1 und
# faellt die Leckrate, ohne dass sich etwas verbessert hat — dieselben Lecks
# verteilen sich auf mehr Text. Deshalb werden Dokumente einzeln und nach
# Sprache und Typ ausgewiesen.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from eval_documents import je_dokument, _kennzahlen  # noqa: E402

leicht_t = "Adresse: Bahnhofstrasse 4, 3011 Bern"
leicht_g = [Span("STREET", 9, 24), Span("BUILDINGNUM", 25, 26),
            Span("ZIPCODE", 28, 32), Span("CITY", 33, 36)]
schwer_t = "Gruss von Andrea Bruelhart aus Lugano"
schwer_g = [Span("GIVENNAME", 10, 16), Span("FULLNAME", 17, 26),
            Span("CITY", 31, 37)]
schwer_p = schwer_g[:2]          # CITY leckt

nur_schwer = [(schwer_t, schwer_g, schwer_p)]
mit_leicht = nur_schwer + [(leicht_t, leicht_g, list(leicht_g))]

_, rate_allein, _, lecks_allein, _ = _kennzahlen(nur_schwer, PACK)
_, rate_gemischt, _, lecks_gemischt, _ = _kennzahlen(mit_leicht, PACK)

check(lecks_allein == lecks_gemischt == 1,
      f"Leckzahl darf sich nicht aendern: {lecks_allein} vs {lecks_gemischt}")
check(rate_gemischt < rate_allein,
      "ein leichtes Dokument muss die Leckrate verduennen — sonst misst "
      "dieser Test nicht, was er soll")
print(f"   OK   dasselbe eine Leck: {100*rate_allein:.1f} % allein, "
      f"{100*rate_gemischt:.1f} % mit einem leichten Dokument daneben")

meta = [("schwer-001", "it", "mailverlauf", len(schwer_t)),
        ("leicht-002", "de", "gesuch", len(leicht_t))]
tabelle = je_dokument(mit_leicht, meta, PACK)
check("schwer-001" in tabelle and "leicht-002" in tabelle,
      "je_dokument nennt nicht beide Dokumente")
check("NACH SPRACHE" in tabelle and "NACH DOKUMENTTYP" in tabelle,
      "Gruppierungen fehlen")
# Die Spalten duerfen nicht aneinanderkleben (16-Zeichen-Typ neben Sprache).
for zeile in tabelle.splitlines():
    check("  it it_support" not in zeile.replace("\t", " "),
          f"Spaltenkollision: {zeile!r}")
print("   OK   Tabelle je Dokument, nach Sprache und nach Dokumenttyp")

print("\n7. Schwellen: Budget als Vorgabe, Tag als begruendete Ausnahme")
# Schwellen stehen pro Budget (R/A/P) UND koennen pro Tag ueberschrieben
# werden. Nur pro Budget waere es zu grob: eine Kalibrierung pro TAG, etwa
# fuer `ORG`, liesse sich sonst nicht eintragen, ohne ZIPCODE, AMOUNT, URL,
# IPADDRESS, COUNTRY und CANTON mitzunehmen.
import yaml  # noqa: E402

TAXO = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "packs" / "ch" / "taxonomy.yaml"
     ).read_text(encoding="utf-8"))
tabelle = TAXO["thresholds"]
budgets = {"R", "A", "P"}
ausnahmen = sorted(k for k in tabelle if k not in budgets)
schwellen = PACK.get_thresholds()

check(budgets <= set(tabelle), "die drei Budgets muessen gesetzt bleiben")
check(schwellen["ZIPCODE"] == tabelle["P"],
      "ein P-Tag muss den Budgetwert tragen")

# ⚠️ Die Wache prueft die REGEL statt eines Beispiels — sonst haelt sie
# eine Zahl fest, die die naechste Messung widerlegen darf. Was sie
# sichert: Ausnahmen bleiben begruendet, wenige, und wirksam. Die
# Begruendung einer Ausnahme steht in `taxonomy.yaml`.
for tag in ausnahmen:
    budget = {t.tag: t.budget for t in PACK.get_tags()}.get(tag)
    check(budget is None or tabelle[tag] != tabelle.get(budget),
          f"Ausnahme {tag} = {tabelle[tag]} ist identisch mit Budget "
          f"{budget}. Eine Ausnahme, die nichts aendert, ist keine — "
          f"streichen statt eintragen.")
print(f"   OK   ZIPCODE {schwellen['ZIPCODE']} (Budget P), "
      f"{len(ausnahmen)} Ausnahme(n)")

# Die REGEL: jede Ausnahme braucht eine Begruendung mit Messung, und die
# steht als Kommentar neben dem Wert in `taxonomy.yaml`. Ohne sie hoehlt
# sich die Vereinfachung aus, bis wieder 39 ungepruefte Zahlen dastehen und
# niemand weiss, welche gemessen und welche geraten sind.
#
# Geprueft wird die Form der Begruendung: ein Kommentarblock, der das Tag
# mit seinem Wert nennt und eine Messreihe mit Lecks traegt.
_tax = (Path(__file__).resolve().parent.parent / "packs" / "ch"
        / "taxonomy.yaml").read_text(encoding="utf-8")
_kommentare = "\n".join(z.strip() for z in _tax.split("\n")
                        if z.strip().startswith("#"))
for tag in ausnahmen:
    check(f"{tag}: {tabelle[tag]:.2f}" in _kommentare and "Lecks" in _kommentare,
          f"Schwellen-Ausnahme {tag} ist in taxonomy.yaml nicht mit einer "
          "Messung begruendet")
check(len(ausnahmen) <= 5,
      f"{len(ausnahmen)} Ausnahmen — ab hier ist das Budget keine "
      "Vereinfachung mehr, sondern eine Liste")
if ausnahmen:
    print(f"   OK   {len(ausnahmen)} Ausnahme(n), alle in taxonomy.yaml "
          f"begruendet: {', '.join(ausnahmen)}")
else:
    # ⚠️ Ein leerer Befund ist keine Entwarnung — auch hier nicht.
    #
    # Ohne eine einzige Ausnahme laeuft die Schleife oben ueber nichts. Der
    # Ueberschreibmechanismus in `adapter.get_thresholds()` hat damit kein
    # Beispiel, an dem er geprueft waere: ginge er kaputt, bliebe diese
    # Pruefung gruen. Das gehoert hier hingeschrieben, nicht verschwiegen.
    print("   —    keine Ausnahme eingetragen. Die Regeln oben laufen")
    print("        damit ueber nichts; der Ueberschreibweg ist ungeprueft.")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
