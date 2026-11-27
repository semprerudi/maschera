"""Der Labelvertrag ist EINGEFROREN.

    python3 tests/test_labelvertrag_eingefroren.py

WAS EINGEFROREN IST UND WAS NICHT
=================================

Eingefroren:  **Tagliste und ihre Reihenfolge.** Daraus entstehen die 91
              BIO-Labels und der Hash, gegen den jedes Modell geprueft wird.

NICHT eingefroren, jederzeit aenderbar:
              `action` (mask/tag_only), Schwellen, Budgets, Platzhalter,
              Muster, Vorlagen, Nomenklaturen, Benutzerregeln.

Der Unterschied ist mechanisch: Eine neue Tagliste macht **jedes bisher
trainierte Modell unbrauchbar**, weil der Ausgabekopf eine andere Groesse
hat. Alles andere laesst sich ohne Training aendern.

WARUM EINGEFROREN
=================

Golddokumente in vier Sprachen (de/fr/it/en) und vier Dokumenttypen
(gesuch, mailverlauf, formular, Support-Ticket): **kein einziges
Personendatum brauchte ein Tag, das es nicht gibt.**

Zwei Auffaelligkeiten sind keine Luecke im Vertrag:

  PERMIT_TYPE   existiert, ist aber in den Vorlagen kaum belegt — ein
                Vorlagen-, kein Vertragsproblem.
  X_dossier     bewusst AUSSERHALB des Vertrags. Solche Kennungen kennt nur
                eine einzelne Stelle; der Vertrag beschreibt, was das
                MODELL vorhersagt, und das Modell soll allen dienen. Der
                Praefix `X_` markiert genau diese Grenze — solche Kennungen
                gehoeren in eigene Regeln (`core/user_rules.py`).

⚠️ WAS DAS EINFRIEREN NICHT BEHAUPTET
=====================================

Nicht: «Die Tagliste ist richtig.» Sondern: «Die Golddokumente haben keine
Luecke gezeigt, und eine Aenderung kostet ein Neutraining.»

Zeigt ein spaeteres Golddokument ein fehlendes Tag, wird aufgetaut — mit
Begruendung und einem neuen Hash hier. **Eine eingefrorene Zahl, die
niemand mehr aendern darf, waere keine Wache, sondern ein Denkmal.**
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packs import load_pack  # noqa: E402

# Aendern NUR zusammen mit einer Begruendung, die die Luecke nennt, und
# einem neu trainierten Modell.
#
# Aufgetaut am 24.11.2026 fuer JOBTITLE (Tag 46). Die Luecke: Berufs- und
# Funktionsbezeichnungen hatten kein Tag und wurden teils als ORG erkannt,
# obwohl eine Funktion keine Stelle ist (ORG-Entscheid vom 7.8.2026).
# Am 25.11.2026 zusaetzlich FAMILYROLE (Tag 47): Verwandtschaft, Partnerschaft,
# Beistand und Vormund hatten kein Tag. Beide im selben Vertrag, damit es
# nur einen Wechsel und ein Neutraining gibt.
# Angehaengt, nicht eingefuegt: Punkt 5 haelt fest, dass jeder fruehere
# Vertrag ein Praefix des heutigen ist.
HASH = "6abcddcc90e672691e0a53c0acc6138c9fb3df5b40daf54aeff19ddb06a463c4"
TAGS = 47
LABELS = 95
# Jeder fruehere Vertrag muss ein PRAEFIX des heutigen sein (Laenge, Hash).
VORGAENGER = [(91, "b7a96dc99b05c6150302fc11943e0a357c7078b593e7382b4b06390245cceeee"),
              (93, "047939a48135b0a826d00d0bf92ee3f7feb282854784e3a959c6226043351442")]

PACK = load_pack("ch")
failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


print("1. Der Hash des Labelvertrags")
ist = PACK.get_label_hash()
check(ist == HASH,
      "Der Labelvertrag hat sich geaendert.\n"
      f"        eingefroren: {HASH}\n"
      f"        jetzt:       {ist}\n"
      "        Damit ist JEDES bisher trainierte Modell unbrauchbar —\n"
      "        der Ausgabekopf hat eine andere Groesse.\n"
      "        War das Absicht? Dann den Grund festhalten, das Modell neu\n"
      "        trainieren und den Hash HIER nachfuehren.")
if ist == HASH:
    print(f"   OK   {HASH[:16]}…")

print("\n2. Umfang")
check(len(PACK.get_tags()) == TAGS,
      f"{len(PACK.get_tags())} Tags statt {TAGS}")
check(len(PACK.get_labels()) == LABELS,
      f"{len(PACK.get_labels())} Labels statt {LABELS}")
print(f"   OK   {TAGS} Tags, {LABELS} BIO-Labels")

print("\n3. Was NICHT eingefroren ist, bleibt aenderbar")
# Diese Pruefung ist kein Formalismus: Sie haelt fest, dass das Einfrieren
# NUR die Tagliste betrifft. Waere es mehr, waere jede Kalibrierung und jede
# Musterkorrektur ein Vertragsbruch — und in den letzten Tagen wurden
# Schwellen, Muster, Vorlagen und Nomenklaturen mehrfach geaendert.
import yaml as _yaml  # noqa: E402
TAXO_TABELLE = _yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "packs" / "ch"
     / "taxonomy.yaml").read_text(encoding="utf-8"))["thresholds"]
schwellen = PACK.get_thresholds()
# ⚠️ Schwellen gehoeren NICHT zum eingefrorenen Vertrag. Eine Wache, die
# «darf sich bewegen» prueft, indem sie einen Wert festnagelt, prueft das
# Gegenteil von dem, was sie sagt. Deshalb strukturell: jedes Tag traegt
# eine Schwelle, und die kommt aus der Budgettabelle, nicht aus dem
# Vertragshash.
# ⚠️ NICHT 45. Die sechs Stufe-1-Tags tragen `budget: None` — dort
# entscheidet die Pruefsumme.
mit_budget = {t.tag for t in PACK.get_tags() if t.budget is not None}
check(mit_budget <= set(schwellen),
      f"Tag mit Budget, aber ohne Schwelle: "
      f"{sorted(mit_budget - set(schwellen))}")
check(set(schwellen.values()) <= set(TAXO_TABELLE.values()),
      "eine Schwelle stammt weder aus einem Budget noch aus einer "
      "eingetragenen Ausnahme")
aktionen = PACK.get_actions()
check(aktionen.get("CANTON") == "tag_only",
      "CANTON ist tag_only — auch `action` ist nicht eingefroren")
print("   OK   Schwellen, action, Muster, Vorlagen bleiben frei")

print("\n4. Benutzerspezifische Tags stehen AUSSERHALB")
# Ein Benutzertag wie `X_dossier` kann als Goldspanne vorkommen, gehoert aber
# nicht in den Vertrag: solche Kennungen kennt nur die eigene Stelle.
namen = {t.tag for t in PACK.get_tags()}
fremd = sorted(t for t in namen if t.startswith("X_"))
check(not fremd, f"X_-Tags im Labelvertrag: {fremd}")
print(f"   OK   kein X_-Tag unter den {len(namen)}")

print("\n5. Neue Tags sind ANGEHAENGT, nicht eingefuegt")
# Die Taxonomie verlangt es im Kopf; hier wird es geprueft. Waere ein Tag
# eingefuegt worden, verschoeben sich die Indizes aller folgenden Labels, und
# ein altes Modell laese still falsche Klassen. Der Hash der ersten n Labels
# muss deshalb jeder frueheren Fassung gleichen.
import hashlib  # noqa: E402
labels = PACK.get_labels()
for n, alt in VORGAENGER:
    ist_praefix = hashlib.sha256("\n".join(labels[:n]).encode("utf-8")).hexdigest()
    check(ist_praefix == alt,
          f"die ersten {n} Labels sind nicht mehr der Vertrag {alt[:8]}: "
          "ein Tag wurde eingefuegt, umsortiert oder umbenannt")
    if ist_praefix == alt:
        print(f"   OK   die ersten {n} Labels = Vertrag {alt[:8]}")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
