"""Test der Ausrichtung Zeichenspanne <-> BIO (SPEC §11).

    python3 tests/test_alignment.py

Kein echter Tokenizer noetig: die Ausrichtung arbeitet auf `offset_mapping`,
und das laesst sich synthetisch erzeugen. Der Test simuliert bewusst
unangenehme Tokenisierungen — Subword-Schnitte mitten in Zahlen, Sonderzeichen,
Leerraum-Offsets — weil genau dort die stillen Fehler sitzen.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.alignment import IGNORE_INDEX, align, decode, verify_roundtrip  # noqa: E402
from core.injector import generate  # noqa: E402
from core.masking import Span  # noqa: E402
from packs import load_pack  # noqa: E402

PACK = load_pack("ch")
LABELS = PACK.get_labels()
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def fake_tokenize(text: str, rng: random.Random, subword: bool = True):
    """Offsets wie ein WordPiece-Tokenizer: Woerter, teils in Stuecke zerlegt.

    Beginnt und endet mit einem Sonderzeichen-Offset (0, 0), wie [CLS]/[SEP].
    """
    offsets: list[tuple[int, int]] = [(0, 0)]
    # Echte WordPiece- und SentencePiece-Tokenizer trennen Satzzeichen ab.
    # Ein Tokenizer, der auf \S+ splittet, ist unrealistisch grob und wuerde
    # Fehler zeigen, die im Betrieb nie auftreten.
    previous_end = 0
    # Der Schraegstrich gehoert NICHT in den Wortzusammenhalt: der echte
    # mmBERT-Tokenizer trennt ihn ab ('▁Biel', '/', 'B', 'ienne'). Klebte er
    # ihn an, entstuende bei "/home/{USERNAME}/" ein Token "home/p.dupont",
    # das ueber die Entitaetsgrenze ragt — ein Fehler, den es im Betrieb nicht
    # gibt, der aber den Test rot faerbt.
    for m in re.finditer(r"\w+(?:[.'’-]\w+)*|[^\w\s]", text, re.UNICODE):
        a, b = m.start(), m.end()
        # SentencePiece gibt Leerraum als eigenes Token aus. Ohne das findet
        # dieser Test die Fehlerklasse nicht, die 368 von 400 Beispielen
        # zerlegt hat.
        if a > previous_end and rng.random() < 0.5:
            offsets.append((previous_end, a))
        previous_end = b
        if subword and b - a > 3 and rng.random() < 0.6:
            cuts = sorted(rng.sample(range(a + 1, b), k=min(2, b - a - 1)))
            prev = a
            for c in cuts:
                offsets.append((prev, c))
                prev = c
            offsets.append((prev, b))
        else:
            offsets.append((a, b))
    offsets.append((0, 0))
    return offsets


# ---------------------------------------------------------------------------
print("1. Grundfall")

text = "Hans Meier wohnt in Bern."
spans = [Span("GIVENNAME", 0, 4), Span("FULLNAME", 5, 10), Span("CITY", 20, 24)]
offsets = [(0, 0), (0, 4), (5, 10), (11, 16), (17, 19), (20, 24), (24, 25), (0, 0)]
a = align(text, spans, offsets, LABELS)
print("   ", list(zip([text[s:e] for s, e in offsets], a.labels)))
check(a.labels[1] == "B-GIVENNAME", "erstes Token falsch")
check(a.labels[2] == "B-FULLNAME", "zweites Token falsch")
check(a.ids[0] == IGNORE_INDEX and a.ids[-1] == IGNORE_INDEX,
      "Sonderzeichen muessen -100 bekommen, nicht O")
check(not a.unlabelled_spans, "Spanne ohne Token")
ok, problems = verify_roundtrip(text, spans, offsets, LABELS)
check(ok, f"Round-Trip Grundfall: {problems}")
print(f"    OK   Sonderzeichen -> {IGNORE_INDEX}, Round-Trip sauber")

# ---------------------------------------------------------------------------
print("\n2. Subword-Schnitt mitten in einer Entitaet")

text = "Versichertennummer 756.9217.0769.85 lautet so."
span = Span("AHVN13", 19, 35)
check(text[19:35] == "756.9217.0769.85", "Testaufbau falsch")
# Tokenizer zerschneidet die Nummer in fuenf Stuecke
offsets = [(0, 0), (0, 18), (19, 22), (22, 27), (27, 32), (32, 35),
           (36, 42), (43, 45), (45, 46), (0, 0)]
a = align(text, [span], offsets, LABELS)
inside = [l for l in a.labels if l.endswith("AHVN13")]
check(inside == ["B-AHVN13", "I-AHVN13", "I-AHVN13", "I-AHVN13"],
      f"BIO-Folge falsch: {inside}")
back = decode(offsets, a.labels)
check(len(back) == 1 and text[back[0].start:back[0].end] == "756.9217.0769.85",
      f"Decode liefert {[text[s.start:s.end] for s in back]}")
print(f"    OK   4 Teilstuecke -> B,I,I,I -> zurueck zu einer Spanne")

# ---------------------------------------------------------------------------
print("\n3. Grenzkonflikt wird gezaehlt, nicht verschwiegen")

text = "BetragCHF500 steht da."
span = Span("AMOUNT", 6, 12)  # "CHF500" ohne Leerzeichen davor
offsets = [(0, 0), (0, 12), (13, 18), (19, 21), (21, 22), (0, 0)]
a = align(text, [span], offsets, LABELS)
check(a.boundary_conflicts == 1,
      f"Grenzkonflikt nicht erkannt: {a.boundary_conflicts}")
print(f"    OK   {a.boundary_conflicts} Konflikt gemeldet statt still aufgeloest")

# ---------------------------------------------------------------------------
print("\n4. Zwei gleiche Tags nebeneinander bleiben getrennt")

text = "Meier Brunner sind zwei."
spans = [Span("FULLNAME", 0, 5), Span("FULLNAME", 6, 13)]
offsets = [(0, 0), (0, 5), (6, 13), (14, 18), (19, 23), (23, 24), (0, 0)]
a = align(text, spans, offsets, LABELS)
check(a.labels[1] == "B-FULLNAME" and a.labels[2] == "B-FULLNAME",
      f"zwei Entitaeten verschmolzen: {a.labels[1:3]}")
check(len(decode(offsets, a.labels)) == 2, "Decode verschmilzt sie wieder")
print("    OK   B-FULLNAME B-FULLNAME, decode liefert zwei")

# ---------------------------------------------------------------------------
print("\n5. Unbekanntes Tag wird laut, nicht still")

try:
    align("x", [Span("GIBTESNICHT", 0, 1)], [(0, 1)], LABELS)
    check(False, "unbekanntes Tag muesste KeyError werfen")
    loud = False
except KeyError:
    loud = True
print(f"    {'OK  ' if loud else 'FEHL'} KeyError statt stiller Verlust")

# ---------------------------------------------------------------------------
print("\n6. SentencePiece-Muster: Leerraum als eigenes Token")
# Am echten mmBERT-Tokenizer beobachtet:
#   "CHF 1'250.00" -> ['▁CHF', '▁', '1', "'", '2', '5', '0', '.', '0', '0']
# Das nackte '▁' traegt nur das Trennzeichen. Wird es 'O', zerfaellt der Betrag
# in zwei Spannen. 368 von 400 Beispielen waren betroffen, und der
# Wortgrenzen-Tokenizer aus diesem Test konnte es nicht zeigen — er erzeugt
# ueberhaupt keine reinen Leerraum-Token.

text = "Betrag CHF 1'250.00 faellig"
span = Span("AMOUNT", 7, 19)
check(text[7:19] == "CHF 1'250.00", "Testaufbau falsch")
sp_offsets = [(0, 0), (0, 6), (6, 10), (10, 11), (11, 12), (12, 13), (13, 14),
              (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 27), (0, 0)]
a = align(text, [span], sp_offsets, LABELS)
inner = [l for l in a.labels if l.endswith("AMOUNT")]
check(inner[0] == "B-AMOUNT" and all(l == "I-AMOUNT" for l in inner[1:]),
      f"Leerraum-Token bricht die Entitaet: {inner}")
back = decode(sp_offsets, a.labels, text)
check(len(back) == 1 and text[back[0].start:back[0].end] == "CHF 1'250.00",
      f"Betrag zerfaellt: {[text[s.start:s.end] for s in back]}")
print(f"    OK   {len(inner)} Token, davon 1x B und {len(inner)-1}x I -> eine Spanne")

# Gegenprobe: Leerraum ZWISCHEN Entitaeten muss O bleiben
text2 = "Meier Brunner sind zwei"
spans2 = [Span("FULLNAME", 0, 5), Span("FULLNAME", 6, 13)]
off2 = [(0, 0), (0, 5), (5, 6), (6, 13), (13, 14), (14, 18), (18, 19), (19, 23), (0, 0)]
a2 = align(text2, spans2, off2, LABELS)
check(a2.labels[2] == "O", f"Leerraum zwischen Entitaeten muesste O sein: {a2.labels[2]}")
check(len(decode(off2, a2.labels, text2)) == 2, "zwei Namen verschmolzen")
print("    OK   Leerraum ZWISCHEN Entitaeten bleibt O")

# ---------------------------------------------------------------------------
print("\n6b. Echte Zefix-Namensformen")
# Firmennamen aus dem Handelsregister tragen Anfuehrungszeichen, Klammern und
# Abkuerzungspunkte. '_tighten' schnitt das schliessende Anfuehrungszeichen ab
# und hinterliess [Firma_1]" — ein Zeichen im Klartext unter einem Platzhalter,
# der Vollstaendigkeit vortaeuscht. 37 von 500 Beispielen betroffen.
ZEFIX = [
    'Studio "Zen"',
    '"Der Bauer" Pius Henke',
    '"Heidi\'s Bluemenchischtli" H. Milz',
    "Muster AG (in Liquidation)",
    "Gebr. Meier-Schmid",
    "Uetli Energie & Co.",
]
for name in ZEFIX:
    probe = f"Firma: {name} eingetragen"
    s_span = Span("ORG", 7, 7 + len(name))
    check(probe[7:7 + len(name)] == name, "Testaufbau falsch")
    offs = [(0, 0), (0, 6), (6, 7)] + [
        (7 + i, 8 + i) for i in range(len(name))
    ] + [(7 + len(name), len(probe)), (0, 0)]
    a = align(probe, [s_span], offs, LABELS)
    back = decode(offs, a.labels, probe)
    ok = len(back) == 1 and probe[back[0].start:back[0].end] == name
    check(ok, f"Zefix-Name verstuemmelt: {name!r} -> "
              f"{[probe[x.start:x.end] for x in back]}")
print(f"    OK   {len(ZEFIX)} Firmennamen mit Anfuehrungszeichen, Klammern, "
      f"Abkuerzungspunkten")

# ---------------------------------------------------------------------------
print("\n7. Round-Trip ueber das echte Trainingsset")

rng = random.Random(4711)
examples = generate(400, seed=7)
bad, conflicts, tokens = 0, 0, 0
for e in examples:
    offsets = fake_tokenize(e.text, rng)
    tokens += len(offsets)
    a = align(e.text, e.spans, offsets, LABELS)
    conflicts += a.boundary_conflicts
    ok, probleme = verify_roundtrip(e.text, e.spans, offsets, LABELS)
    if not ok:
        bad += 1
        if bad <= 2:
            print(f"    {e.template_id}: {probleme[0][:160]}")
check(bad == 0, f"{bad} von {len(examples)} Beispielen scheitern am Round-Trip")
print(f"    {'OK  ' if bad == 0 else 'FEHL'} {len(examples) - bad}/{len(examples)} "
      f"Beispiele, {tokens} Token, {conflicts} Grenzkonflikte")

# ---------------------------------------------------------------------------
print("\n8. Wortweise Tokenisierung (ohne Subwords) als Gegenprobe")

bad2 = 0
for e in examples[:200]:
    offsets = fake_tokenize(e.text, rng, subword=False)
    ok, probleme = verify_roundtrip(e.text, e.spans, offsets, LABELS)
    if not ok:
        bad2 += 1
        if bad2 <= 2:
            print(f"    {e.template_id}: {probleme[0][:160]}")
check(bad2 == 0, f"{bad2} Beispiele scheitern bei wortweiser Tokenisierung")
print(f"    {'OK  ' if bad2 == 0 else 'FEHL'} {200 - bad2}/200")

print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)} Problem(e):")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
