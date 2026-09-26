"""Test des Injektors (SPEC §8, §11).

    python3 tests/test_injector.py

Die entscheidende Prüfung ist der Round-Trip: die erzeugten Spannen müssen
zeichengenau sitzen. Sitzen sie systematisch daneben, trainiert das Modell auf
verschobene Labels und niemand merkt es, weil die Verlustkurve trotzdem sinkt.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.injector import generate, load_templates  # noqa: E402
from core.recognizers import recognize  # noqa: E402
from packs import load_pack  # noqa: E402
from packs.ch.validators.checksums import VALIDATORS  # noqa: E402

PACK = load_pack("ch")
N = 800
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


templates = load_templates()
examples = generate(N, seed=2026)
print(f"{len(templates)} Vorlagen, {len(examples)} Beispiele erzeugt\n")

# --- 1. Keine unersetzten Slots ---------------------------------------------
print("1. Vollstaendigkeit")
leftover = [(e.template_id, m.group(0))
            for e in examples for m in re.finditer(r"\{[^}]{1,30}\}", e.text)]
check(not leftover, f"unersetzte Slots: {sorted(set(leftover))[:5]}")
print(f"   {'OK  ' if not leftover else 'FEHL'} keine unersetzten Slots")

# --- 2. Round-Trip -----------------------------------------------------------
print("\n2. Round-Trip: sitzen die Spannen zeichengenau?")
bad = 0
for e in examples:
    for s in e.spans:
        v = e.text[s.start:s.end]
        if not v or v != v.strip() or "\n" in v and s.tag != "STREET":
            bad += 1
check(bad == 0, f"{bad} Spannen mit Rand- oder Leerzeichenfehler")
overlap = sum(1 for e in examples
              for i, a in enumerate(e.spans) for b in e.spans[i+1:]
              if a.start < b.end and b.start < a.end)
check(overlap == 0, f"{overlap} ueberlappende Spannen")
print(f"   {'OK  ' if bad == 0 else 'FEHL'} {sum(len(e.spans) for e in examples)} "
      f"Spannen sauber, {overlap} Ueberlappungen")

# --- 3. Decoys bleiben O -----------------------------------------------------
print("\n3. Decoys duerfen keine Spanne beruehren")
touched = sum(1 for e in examples for a, b, _ in e.decoys
              for s in e.spans if a < s.end and s.start < b)
check(touched == 0, f"{touched} Decoys ueberlappen mit Spannen")
n_decoys = sum(len(e.decoys) for e in examples)
with_decoy = sum(1 for e in examples if e.decoys)
check(with_decoy / len(examples) > 0.9,
      f"nur {100*with_decoy/len(examples):.0f} % der Beispiele haben Decoys")
print(f"   OK   {n_decoys} Decoys, {100*with_decoy/len(examples):.0f} % der "
      f"Beispiele enthalten mindestens einen")

# --- 4. Pruefsummen im Trainingsset muessen gueltig sein ---------------------
print("\n4. Erzeugte Identifikatoren bestehen ihre Pruefsumme")
for tag, validator in VALIDATORS.items():
    vals = [e.text[s.start:s.end] for e in examples for s in e.spans if s.tag == tag]
    if not vals:
        continue
    invalid = [v for v in vals if not validator(v)]
    check(not invalid, f"{tag}: {len(invalid)} ungueltige im Trainingsset")
    print(f"   {'OK  ' if not invalid else 'FEHL'} {tag:<14} {len(vals):>4} Stueck, "
          f"{len(invalid)} ungueltig")

# --- 5. PLZ und Ort passen zusammen -----------------------------------------
print("\n5. Kohaerenz von PLZ und Ort innerhalb einer Adresse")
# Gegen die TATSAECHLICH benutzte Wertquelle pruefen, nicht gegen den
# Notvorrat. Sind Nomenklaturen geladen, stammen die Paare von dort; ein Test,
# der stur den Notvorrat als Wahrheit nimmt, meldet dann Fehler, wo keine sind.
from core.injector import SEED_LOCALITY, _nomenclatures  # noqa: E402

lookup: dict[str, set] = {}
for plz, ort in SEED_LOCALITY:
    lookup.setdefault(plz, set()).add(ort)
for quelle in ("_LOCALITY", "_ADDRESS"):
    for r in _nomenclatures().get(quelle, []):
        if r.get("plz"):
            lookup.setdefault(r["plz"], set()).add(r.get("city") or r["name"])
echt = bool(_nomenclatures())

mismatch, geprueft = 0, 0
schlechte = []
for e in examples:
    for z in [s for s in e.spans if s.tag == "ZIPCODE"]:
        plz = e.text[z.start:z.end]
        nxt = [s for s in e.spans
               if s.tag == "CITY" and 0 <= s.start - z.end <= 2]
        if nxt and plz in lookup:
            geprueft += 1
            ort = e.text[nxt[0].start:nxt[0].end]
            if ort not in lookup[plz]:
                mismatch += 1
                if len(schlechte) < 3:
                    schlechte.append(f"{plz} {ort} (erwartet: {sorted(lookup[plz])[:3]})")
check(mismatch == 0,
      f"{mismatch} von {geprueft} Adressen mit unpassender PLZ/Ort-Kombination: "
      f"{schlechte}")
print(f"   {'OK  ' if mismatch == 0 else 'FEHL'} {mismatch} von {geprueft} "
      f"Fehlpaarungen ({'echte Nomenklaturen' if echt else 'Notvorrat'})")

# --- 6. Vielfalt -------------------------------------------------------------
print("\n6. Vielfalt der Namen")
names = [e.text[s.start:s.end] for e in examples for s in e.spans
         if s.tag == "FULLNAME"]
uniq = len(set(names))
top = Counter(names).most_common(1)
share = 100 * top[0][1] / len(names) if names else 0
check(uniq >= 8, f"nur {uniq} verschiedene Nachnamen")
check(share < 25, f"haeufigster Name macht {share:.0f} % aus")
print(f"   OK   {uniq} verschiedene Nachnamen, haeufigster {share:.0f} %")
# Vielfalt MESSEN, nicht gegen eine feste Namensliste pruefen. Der frueheren
# Fassung fehlte diese Unterscheidung: sie suchte nach den Namen des
# Notvorrats und meldete "0 nichtdeutschschweizerische Namen", sobald echte
# BFS-Daten geladen waren — also genau dann, wenn die Vielfalt am groessten war.
if _nomenclatures().get("FULLNAME"):
    check(uniq > 200,
          f"mit echten Nomenklaturen erwartet man viele Namen, gefunden: {uniq}")
    print(f"   OK   echte Nomenklaturen, {uniq} verschiedene Nachnamen")
else:
    vorrat = {"Da Silva", "Yilmaz", "Rajasingam", "Oezdemir", "Dupont", "Rossi"}
    nonde = len(vorrat & set(names))
    check(nonde >= 4,
          f"der Notvorrat muss divers besetzt bleiben, gefunden: {nonde}")
    print(f"   OK   Notvorrat, {nonde} nichtdeutschschweizerische Namen vertreten")

# --- 7. Regex findet, was der Injektor gesetzt hat ---------------------------
print("\n7. Gegenprobe: Recognizer gegen die Wahrheit des Injektors")
for tag in ("AHVN13", "UID", "IBAN", "PLACE_OF_ORIGIN"):
    truth = [(e, s) for e in examples for s in e.spans if s.tag == tag]
    if not truth:
        continue
    found = sum(1 for e, s in truth
                if any(r.tag == tag and r.start == s.start and r.end == s.end
                       for r in recognize(e.text)))
    rate = 100 * found / len(truth)
    fehlend = [e.text[s.start:s.end] for e, s in truth
               if not any(r.tag == tag and r.start == s.start and r.end == s.end
                          for r in recognize(e.text))][:3]
    check(rate > 90, f"{tag}: Recognizer findet nur {rate:.0f} % der gesetzten")
    if fehlend:
        print(f"        nicht gefunden, z.B.: {fehlend}")
    print(f"   {'OK  ' if rate > 90 else 'FEHL'} {tag:<16} {found}/{len(truth)} "
          f"({rate:5.1f} %)")

# --- 8. Falsch-Positive des Recognizers auf Decoys ---------------------------
print("\n8. Schlaegt der Recognizer auf Decoys an?")
fp = 0
for e in examples:
    hits = recognize(e.text)
    for a, b, kind in e.decoys:
        for h in hits:
            if a < h.end and h.start < b:
                fp += 1
print(f"   {fp} Regex-Treffer innerhalb von Decoys "
      f"({100*fp/max(1,n_decoys):.1f} % der Decoys)")
if fp:
    print("   -> Diese Faelle sind die Arbeitsliste fuer patterns.yaml.")

# --- 9. Namensreihenfolge ----------------------------------------------------
print("\n9. Beide Namensreihenfolgen kommen vor")
print("   Mailprogramme schreiben oft 'Nachname Vorname'. Schreibt keine")
print("   Vorlage die Register-Reihenfolge, lernt das Modell eine")
print("   Positionsregel: erstes Wort GIVENNAME, zweites FULLNAME.\n")

natuerlich = register = 0
for e in examples:
    paare = sorted(((sp.start, sp.end, sp.tag) for sp in e.spans
                    if sp.tag in ("GIVENNAME", "FULLNAME")))
    for (a1, e1, t1), (a2, _, t2) in zip(paare, paare[1:]):
        # Direkt benachbart: nur Trennzeichen dazwischen, kein Umbruch.
        zwischen = e.text[e1:a2]
        if len(zwischen) > 2 or "\n" in zwischen or t1 == t2:
            continue
        if t1 == "GIVENNAME":
            natuerlich += 1
        else:
            register += 1

anteil = register / max(1, natuerlich + register)
check(register > 0, "keine einzige Vorlage schreibt Register-Reihenfolge")
check(natuerlich > 0, "keine einzige Vorlage schreibt natuerliche Reihenfolge")
check(0.25 <= anteil <= 0.75,
      f"Reihenfolge zu einseitig: {100*anteil:.0f} % Register-Reihenfolge")
print(f"   OK   {natuerlich} natuerlich, {register} Register-Reihenfolge "
      f"({100*anteil:.0f} %)")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Problem(e):")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
