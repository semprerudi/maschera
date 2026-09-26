"""DOCX einlesen — ohne neue Abhaengigkeit, ohne Word, ohne Beispieldatei.

Die Probedateien entstehen hier im Test. Das ist Absicht: eine mitgelieferte
`.docx` waere entweder erfunden und damit wertlos, oder aus einem echten
Dokument und gehoerte dann nicht ins Repository.

⚠️ Der wichtigste Fall ist Nummer 3. Word-Tabellen sind in Schweizer
Formularen der Normalfall — Etikett links, Wert rechts. Wer sie absatzweise
liest, setzt das Etikett eine Zeile ueber den Wert, und `anchor_same_line`
verliert ihn. Beim Lesen laesst sich das vermeiden statt spaeter im Muster.
"""
import sys
import tempfile
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

from dokumente import ALLE, ALTE_WORDENDUNGEN, docx_zu_text, lies  # noqa: E402

failures: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="maschera-docx-"))


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def baue(name: str, koerper: str, extra: dict | None = None) -> Path:
    """Eine minimale, aber echte .docx — ZIP mit word/document.xml."""
    pfad = TMP / name
    xml = (f'<?xml version="1.0"?><w:document {NS}>'
           f'<w:body>{koerper}</w:body></w:document>')
    with zipfile.ZipFile(pfad, "w") as z:
        z.writestr("word/document.xml", xml)
        for n, inhalt in (extra or {}).items():
            z.writestr(n, inhalt)
    return pfad


def p(*laeufe: str) -> str:
    return "<w:p>" + "".join(f"<w:r><w:t>{t}</w:t></w:r>"
                             for t in laeufe) + "</w:p>"


print("1. Endung ist angemeldet, .doc ausdruecklich nicht")
check(".docx" in ALLE, ".docx fehlt in ALLE")
check(".doc" not in ALLE, ".doc steht in ALLE — landete im Textzweig")
check(".doc" in ALTE_WORDENDUNGEN, ".doc fehlt bei den alten Endungen")
print("   OK   .docx in ALLE, .doc getrennt")

print("2. Laeufe werden zusammengezogen, nicht zerschnitten")
# Word teilt einen Namen bei jeder Formatwechsel-Stelle. Wer je Lauf eine
# Zeile schreibt, macht aus «Bruelhart» zwei Woerter — dann erkennt weder
# Regex noch Modell den Namen wieder.
d = baue("laeufe.docx", p("Sehr geehrte Frau ", "Br", "ülhart"))
text, _ = docx_zu_text(d)
check(text == "Sehr geehrte Frau Brülhart", f"Laeufe zerschnitten: {text!r}")
print("   OK   Brülhart bleibt ein Wort")

print("3. Tabellenzeilen behalten Etikett und Wert auf EINER Zeile")
tbl = ("<w:tbl>"
       "<w:tr><w:tc>" + p("AHV-Nr.") + "</w:tc>"
       "<w:tc>" + p("756.1234.5678.97") + "</w:tc></w:tr>"
       "<w:tr><w:tc>" + p("Wohnort") + "</w:tc>"
       "<w:tc>" + p("3011 Bern") + "</w:tc></w:tr>"
       "</w:tbl>")
d = baue("tabelle.docx", tbl)
text, hinweise = docx_zu_text(d)
zeilen = text.split("\n")
check(len(zeilen) == 2, f"2 Zeilen erwartet, {len(zeilen)}: {zeilen!r}")
check(zeilen[0] == "AHV-Nr.\t756.1234.5678.97",
      f"Etikett und Wert getrennt: {zeilen[0]!r}")
check("756.1234.5678.97" in zeilen[0].split("\t")[-1],
      "Wert nicht in derselben Zeile wie der Anker")
check(any(h["schluessel"] == "tabellen" for h in hinweise),
      "Tabellen nicht gemeldet")
print("   OK   AHV-Nr.\\t756.1234.5678.97")

print("4. Umbruch und Tabulator im Absatz bleiben erhalten")
d = baue("umbruch.docx",
         "<w:p><w:r><w:t>Zeile eins</w:t></w:r><w:br/>"
         "<w:r><w:t>Zeile zwei</w:t></w:r></w:p>")
text, _ = docx_zu_text(d)
check(text == "Zeile eins\nZeile zwei", f"Umbruch verloren: {text!r}")
print("   OK   Umbruch bleibt")

print("5. Kopf- und Fusszeilen werden GEMELDET, nicht verschwiegen")
# ⚠️ Der Absender eines Briefs steht bei Word regelmaessig in header1.xml.
# Eine stille Auslassung waere genau die Leckquelle mit leerem Befund, vor der
# der Grundsatz dieser Datei warnt.
d = baue("kopf.docx", p("Text"),
         {"word/header1.xml": "<x/>", "word/footer1.xml": "<x/>"})
_, hinweise = docx_zu_text(d)
gemeldet = " ".join(h["text"] for h in hinweise)
check("Kopfzeilen" in gemeldet, f"Kopfzeilen nicht gemeldet: {hinweise!r}")
check("Fusszeilen" in gemeldet, f"Fusszeilen nicht gemeldet: {hinweise!r}")
check("NICHT gelesen" in gemeldet, "Auslassung nicht als solche benannt")
print("   OK   NICHT gelesen: Kopfzeilen, Fusszeilen")

print("6. Ohne Kopfzeilen keine Warnung")
d = baue("schlicht.docx", p("Text"))
_, hinweise = docx_zu_text(d)
check(not any(h["schluessel"] == "nicht_gelesen" for h in hinweise),
      f"warnt ohne Grund: {hinweise!r}")
print("   OK   still")

print("7. Leeres Dokument sagt, dass es leer ist")
# Ein leerer Befund darf nicht wie «nichts gefunden» aussehen.
d = baue("leer.docx", "")
text, hinweise = docx_zu_text(d)
check(text.strip() == "", f"unerwarteter Text: {text!r}")
check(any(h["schluessel"] == "docx_leer" for h in hinweise),
      f"leeres Dokument schweigt: {hinweise!r}")
print("   OK   gemeldet")

print("8. Kaputte Datei bricht ab statt zu raten")
kaputt = TMP / "kaputt.docx"
kaputt.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 kein ZIP")
try:
    docx_zu_text(kaputt)
    check(False, "kaputte .docx wurde stillschweigend gelesen")
except SystemExit as e:
    check(".doc" in str(e), f"Meldung nennt das alte Format nicht: {e}")
print("   OK   Abbruch mit Hinweis auf .doc")

print("9. ZIP ohne document.xml wird erkannt")
falsch = TMP / "falsch.docx"
with zipfile.ZipFile(falsch, "w") as z:
    z.writestr("content.xml", "<x/>")      # so sieht eine .odt aus
try:
    docx_zu_text(falsch)
    check(False, "ZIP ohne word/document.xml wurde gelesen")
except SystemExit:
    pass
print("   OK   Abbruch")

print("10. .doc wird vor dem Textzweig abgefangen")
# ⚠️ Ohne diese Wache faende `entschluessle` eine Kodierung — cp1252 nimmt
# jedes Byte an — und der Filter liefe auf Binaermuell.
alt = TMP / "alt.doc"
alt.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00\x01" * 200)
try:
    lies(alt)
    check(False, ".doc wurde als Text gelesen")
except SystemExit as e:
    check("docx" in str(e).lower(), f"Meldung nennt den Ausweg nicht: {e}")
print("   OK   Abbruch mit Umwandlungshinweis")

print("11. lies() liefert format 'docx' und die Hinweise")
d = baue("ganz.docx", p("Frau Brülhart, 3011 Bern"))
doks = lies(d)
check(len(doks) == 1, f"{len(doks)} Dokumente statt 1")
check(doks[0].format == "docx", f"format {doks[0].format!r}")
check("Brülhart" in doks[0].text, "Text kam nicht durch")
check(doks[0].kennung == "ganz.docx", f"kennung {doks[0].kennung!r}")
print("   OK   docx")

print("11b. Zwei Bomben werden abgewiesen, nicht ausgepackt")
# ⚠️⚠️ Zwei Wege, den Dienst lahmzulegen — beide GEMESSEN und nicht der
# Dokumentation entnommen:
#
#   ENTITY   `ET.fromstring` loest interne Entities auf. 209 Byte
#            Quelltext ergeben 10 000 Zeichen bei vier Ebenen; jede
#            weitere nimmt das Zehnfache, zwei mehr sind ein Gigabyte.
#            Die Groessengrenze faengt es NICHT — die Quelle bleibt winzig.
#
#   ZIP      `z.read()` packt aus, so weit der Inhalt reicht. DEFLATE
#            schafft 1 : 1026 (50 MB in 48 KB), aus dem 10-MB-Limit des
#            Servers wuerden also rund 10 GB im Arbeitsspeicher.
#
# Beide legen den Dienst still lahm; auslaufen wuerde nichts. Genau deshalb
# steht die Wache hier: ein Fehler ohne Datenverlust bekommt sonst nie einen
# Verwalter.
#
# ⚠️ Die Bombe wird KLEIN gebaut. Ein echter Ausbau waere der Fehler, den
# die Wache verhindern soll — sie wuerde den Laeufer selbst umbringen.
_bombe = TMP / "entity.docx"
with zipfile.ZipFile(_bombe, "w") as z:
    z.writestr("word/document.xml",
               '<?xml version="1.0"?>\n'
               '<!DOCTYPE w:document [\n'
               '<!ENTITY a "AAAAAAAAAA">\n'
               '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">\n'
               ']>\n'
               f'<w:document {NS}><w:body><w:p><w:r><w:t>&b;</w:t>'
               '</w:r></w:p></w:body></w:document>')
try:
    docx_zu_text(_bombe)
    check(False, "eine DTD im Dokumentteil wird gelesen statt abgewiesen")
except SystemExit as e:
    check("DTD" in str(e), f"abgewiesen, aber mit falschem Grund: {e}")

# ⚠️ NICHT wirklich 64 MB schreiben. Geprueft wird die Entscheidung, und
# die faellt an `file_size` aus dem ZIP-Verzeichnis — also wird die
# Grenze fuer diesen einen Aufruf heruntergesetzt. Eine 65-MB-Probedatei
# haette den Laeufer eine Minute lang beschaeftigt, um dasselbe zu sagen.
import dokumente as _dok  # noqa: E402
_gross = baue("gross.docx", p("Nur ein Satz, aber ueber der Grenze."))
_alt = _dok.DOCX_HOECHSTENS
_dok.DOCX_HOECHSTENS = 10
try:
    docx_zu_text(_gross)
    check(False, "die Groessengrenze wirkt nicht")
except SystemExit as e:
    check("MB" in str(e), f"abgewiesen, aber mit falschem Grund: {e}")
finally:
    _dok.DOCX_HOECHSTENS = _alt

# Gegenprobe: eine gewoehnliche Datei geht weiter durch. Eine Wache, die
# alles abweist, ist keine.
_text, _ = docx_zu_text(_gross)
check("Nur ein Satz" in _text, "die Wache weist auch gewoehnliche ab")
print("   OK   Entity-Bombe und Groessengrenze, gewoehnliche Datei laeuft")

print("12. Echte Word-Dateien in beispiele/, falls vorhanden")
# ⚠️ Die elf Pruefungen oben bauen ihre .docx selbst. Sie pruefen damit
# Annahmen ueber Word, nicht Word. Die kritischen Fehler kommen aus echten
# Dokumenten, nicht aus synthetischen: eine Datei, die wirklich aus Word
# oder LibreOffice kam, sagt mehr als alle elf zusammen.
echte = sorted((WURZEL / "beispiele").glob("*.docx"))
if not echte:
    print("   --   keine in beispiele/ — die Pruefungen oben sind synthetisch")
for d in echte:
    text, hinweise = docx_zu_text(d)
    check(text.strip() != "", f"{d.name}: nichts gelesen")
    check("\x00" not in text, f"{d.name}: Nullbytes im Text — falsch gelesen")
    doks = lies(d)
    check(doks[0].format == "docx", f"{d.name}: format {doks[0].format!r}")
    print(f"   OK   {d.name}: {len(text)} Zeichen"
          + (f" · {'; '.join(h['text'] for h in hinweise)}" if hinweise else ""))

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("DOCX-Leser in Ordnung.")
