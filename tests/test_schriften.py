"""Schriften — vorhanden, lokal, und was sie abdecken.

    python3 tests/test_schriften.py

⚠️ **Der Massstab ist nicht Geschmack, sondern ein Bundesratsentscheid.**
In den Schweizer Personenregistern gilt ein einheitlicher Zeichensatz:
**ISO 8859-1 + Latin Extended-A**. Was in einem Schweizer Namen stehen
kann, ist damit amtlich festgelegt — `U+0020-U+00FF` und
`U+0100-U+017F`, zusammen 319 druckbare Zeichen.

Fuer ein Werkzeug, dessen Zweck das Behandeln von Namen ist, ist das die
richtige Messlatte: eine Schrift, die einen Buchstaben nicht hat, den ein
Zivilstandsamt eintragen darf, zeigt ihn in einer Ersatzschrift — kein
Kaestchen, aber sichtbar anders, mitten im Namen.

Geprueft wird ohne `fontTools`, wenn es fehlt: dann bleibt die
Abdeckungspruefung aus und sagt es. Die uebrigen Punkte laufen immer.
"""
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
STATIC = WURZEL / "app" / "static"
SCHRIFTEN = STATIC / "schriften"

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


# ISO 8859-1, druckbar (ohne C0- und C1-Steuerzeichen), plus Latin Extended-A.
AMTLICH = (set(range(0x20, 0x7F)) | set(range(0xA0, 0x100))
           | set(range(0x100, 0x180)))

# ⚠️ Bekannte Luecken von Barlow, jede mit Grund. Diese Liste ist der Zweck
# der Pruefung: sie darf nicht laenger werden, ohne dass jemand hinsieht.
# Wer eine Schrift austauscht oder eine Teilmenge weglaesst, merkt es hier.
LUECKEN = {
    0x0114: "E mit Breve — in Namen praktisch nicht vorkommend",
    0x0115: "e mit Breve — dito",
    0x012C: "I mit Breve — dito",
    0x014E: "O mit Breve — dito",
    0x0138: "groenlaendisches Kra — 1973 abgeschafft",
    0x0149: "'n als ein Zeichen — von Unicode als veraltet gefuehrt",
    0x017F: "langes s — historischer Satz",
    # ⚠️ Diese beiden koennen in einem Namen stehen. Die KLEINformen sind
    # vorhanden; es fehlen die Grossformen — also ausgerechnet die, die am
    # Anfang eines Nachnamens stuenden. Bewusst hingenommen, nicht uebersehen.
    0x0132: "IJ-Ligatur gross, niederlaendisch — kann in einem Namen stehen",
    0x013F: "L mit Mittelpunkt gross, katalanisch — kann in einem Namen stehen",
}

print("1. Die Schriftdateien liegen da")
dateien = sorted(SCHRIFTEN.glob("*.woff2"))
check(len(dateien) == 10, f"{len(dateien)} woff2 statt 10")
groesse = sum(d.stat().st_size for d in dateien)
check(groesse < 400 * 1024, f"{groesse/1024:.0f} KB — mehr als erwartet")
print(f"   OK   {len(dateien)} Dateien, {groesse/1024:.0f} KB")

print("2. Lizenz und Herkunft sind dabei")
# SIL OFL 1.1 verlangt, dass der Lizenztext mitgeliefert wird.
ofl = SCHRIFTEN / "OFL.txt"
check(ofl.is_file(), "OFL.txt fehlt — die Lizenz verlangt sie")
if ofl.is_file():
    text = ofl.read_text(encoding="utf-8")
    check("SIL OPEN FONT LICENSE" in text.upper(),
          "OFL.txt enthaelt nicht den Lizenztext")
check((SCHRIFTEN / "HERKUNFT.md").is_file(), "HERKUNFT.md fehlt")
print("   OK   OFL.txt, HERKUNFT.md")

print("3. Jede @font-face-Regel zeigt auf eine vorhandene Datei")
# Ein Tippfehler im Pfad faellt im Browser nur daran auf, dass die Schrift
# „irgendwie anders“ aussieht — und das sieht man erst, wenn man es weiss.
css = (STATIC / "maschera.css")
check(css.is_file(), "maschera.css fehlt")
inhalt = css.read_text(encoding="utf-8") if css.is_file() else ""
verweise = re.findall(r'src:\s*url\("([^"]+)"\)', inhalt)
check(len(verweise) == 10, f"{len(verweise)} @font-face-Regeln statt 10")
for v in verweise:
    check((STATIC / v).is_file(), f"@font-face zeigt ins Leere: {v}")
benutzt = {(STATIC / v).resolve() for v in verweise}
for d in dateien:
    check(d.resolve() in benutzt,
          f"{d.name} liegt herum, wird aber von keiner Regel benutzt")
print(f"   OK   {len(verweise)} Regeln, alle Dateien benutzt")

print("4. Kein Verweis nach aussen in der CSS")
check("fonts.googleapis" not in inhalt and "fonts.gstatic" not in inhalt,
      "maschera.css laedt Schriften von Google")
print("   OK   nur lokale Pfade")

print("5. Abdeckung des amtlichen Zeichensatzes")
try:
    import io

    from fontTools.ttLib import TTFont
except ImportError:
    print("   --   fontTools nicht installiert, Abdeckung ungeprueft")
    print("        pip install fonttools brotli")
else:
    je_familie: dict[str, set[int]] = {}
    for d in dateien:
        familie = d.name.split("-")[0]
        try:
            tf = TTFont(io.BytesIO(d.read_bytes()))
        except Exception as e:                        # noqa: BLE001
            check(False, f"{d.name} nicht lesbar: {e}")
            continue
        je_familie.setdefault(familie, set()).update(tf.getBestCmap().keys())

    for familie, cps in sorted(je_familie.items()):
        fehlt = AMTLICH - cps
        neu = fehlt - set(LUECKEN)
        for c in sorted(neu):
            check(False,
                  f"{familie}: U+{c:04X} {chr(c)!r} fehlt und steht nicht "
                  f"in LUECKEN — im amtlichen Zeichensatz seit 11.11.2024")
        # Gegenprobe: eine Luecke, die zugegangen ist, gehoert aus der Liste.
        # Sonst waechst sie zu einer Liste von Behauptungen.
        zu = set(LUECKEN) - fehlt
        for c in sorted(zu):
            check(False,
                  f"{familie}: U+{c:04X} {chr(c)!r} steht in LUECKEN, ist "
                  f"aber vorhanden — Eintrag streichen")
        print(f"   OK   {familie}: {len(AMTLICH) - len(fehlt)} von "
              f"{len(AMTLICH)} Zeichen")

print("\n6. Die vier Sprachen kommen vollstaendig durch")
# Eine Stichprobe mit echten Zeichen statt Codepunkten — sie faellt auf,
# wenn jemand sie liest.
PROBE = "äöüÄÖÜßéèàçÉÈÀÇìòùÌÒÙñõåøæþðÿŁłŠšŽžČčŘřĄąĘęŰűŐő"
# ⚠️ `je_familie` gibt es nur, wenn Punkt 5 fontTools gefunden hat. Fehlt
# es, faellt hier ein `NameError` an, und der ist die ganze Erkennung.
try:
    for familie, cps in sorted(je_familie.items()):
        fehlt = [z for z in PROBE if ord(z) not in cps]
        check(not fehlt, f"{familie} fehlen: {''.join(fehlt)}")
    print(f"   OK   {len(PROBE)} Probezeichen in allen Familien")
except NameError:
    print("   --   uebersprungen")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Schriften in Ordnung.")
