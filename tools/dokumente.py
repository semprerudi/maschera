"""Dokumente einlesen — Text, Mail, PDF, DOCX.

Eine Stelle für alles, was aus einer Datei reinen Text macht. Benutzt von
`filter_document.py` und `eval_documents.py`.

**Grundsatz: lieber zuviel Text als zuwenig.** Was hier verlorengeht, kann der
Filter nicht maskieren, weil er es nie sieht. Deshalb kommen bei einer Mail
auch die Kopfzeilen mit — gerade dort stehen die Personendaten. Wo doch etwas
ausgelassen wird, sagt es ein Hinweis: eine stille Auslassung wäre eine
Leckquelle mit leerem Befund.

Keine neuen Abhängigkeiten ausser für PDF: `.txt`, `.md`, `.eml`, `.mbox` und
`.docx` laufen über die Standardbibliothek — ein `.docx` ist ein ZIP mit XML
darin. PDF braucht `pymupdf`.
"""

from __future__ import annotations

import email
import email.policy
import html as html_mod
import re
from dataclasses import dataclass
from email.header import decode_header, make_header
from pathlib import Path

from core.hinweise import Abbruch, hinweis

# Die deutschen Namen der Word-Teile, die nicht gelesen werden. Sie stehen
# hier fuer `hinweis(..., text=...)`; die vier uebrigen Sprachen stehen
# unter denselben Schluesseln in `maschera.js`.
TEIL_NAMEN = {
    "t_kopfzeilen": "Kopfzeilen",
    "t_fusszeilen": "Fusszeilen",
    "t_kommentare": "Kommentare",
    "t_fussnoten": "Fussnoten",
}

TEXTENDUNGEN = {".txt", ".md", ".log", ".text", ".csv", ".json", ""}
MAILENDUNGEN = {".eml", ".msg"}

# ⚠️ Die Signatur eines OLE2-Verbunddokuments. Outlook `.msg`, altes
# `.doc`, `.xls` und `.ppt` tragen sie alle. Geprueft wird sie und nicht
# die Endung — eine Datei mit falschem Namen bleibt, was sie ist.
OLE2 = bytes.fromhex("d0cf11e0a1b11ae1")
PDFENDUNGEN = {".pdf"}
DOCXENDUNGEN = {".docx"}
SAMMELENDUNGEN = {".mbox"}

# ⚠️ `.doc` ist das alte binaere Word-Format und steht NICHT in `ALLE`. Ohne
# diesen Eintrag fiele es in die Textendungen — `entschluessle` faende
# irgendeine Kodierung, die nie scheitert (cp1252 nimmt jedes Byte an), und
# der Filter arbeitete auf Binaermuell. Ein leerer Befund saehe dann aus wie
# «nichts gefunden» und hiesse «nichts gelesen».
ALTE_WORDENDUNGEN = {".doc", ".dot"}

ALLE = (TEXTENDUNGEN | MAILENDUNGEN | PDFENDUNGEN | DOCXENDUNGEN
        | SAMMELENDUNGEN)

# Reihenfolge zaehlt: utf-8-sig vor utf-8, sonst bleibt die Byte-Order-Mark als
# unsichtbares Zeichen am Textanfang stehen und verschiebt alle Offsets um eins.
KODIERUNGEN = ("utf-8-sig", "utf-8", "cp1252", "iso-8859-1")


@dataclass
class Dokument:
    text: str
    kennung: str          # eindeutiger Name, auch bei Mails aus einer mbox
    format: str           # text | eml | pdf | mbox
    hinweise: list[dict]  # was beim Lesen aufgefallen ist, s. `core.hinweise`


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def entschluessle(roh: bytes) -> tuple[str, str]:
    """Bytes zu Text, mit erkannter Kodierung.

    UTF-8 anzunehmen ist im Schweizer Schriftverkehr falsch: Altsysteme und
    Windows-Ausgaben liefern cp1252. Ein Absturz beim Einlesen ist harmlos,
    ein still ersetztes Zeichen nicht — `Müller` als `M?ller` waere ein Name,
    den weder Regex noch Modell wiedererkennt.
    """
    for k in KODIERUNGEN:
        try:
            return roh.decode(k), k
        except UnicodeDecodeError:
            continue
    # Letzter Ausweg: nichts wegwerfen, aber deutlich melden.
    return roh.decode("utf-8", errors="replace"), "utf-8 (mit Ersatzzeichen)"


# ---------------------------------------------------------------------------
# Mail
# ---------------------------------------------------------------------------

_BLOCK = re.compile(r"(?i)</(p|div|tr|li|h[1-6]|table|blockquote)>")
_TAG = re.compile(r"(?s)<[^>]+>")
_SKRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")


def html_zu_text(roh: str) -> str:
    """Sehr einfache HTML-Entkleidung. Bewusst grob.

    Blockenden werden zu Zeilenumbruechen, damit nicht zwei Woerter
    zusammenkleben (`Meier</td><td>Bern` -> `MeierBern` waere ein Wort, das
    keine Erkennung findet).
    """
    s = _SKRIPT.sub(" ", roh)
    s = _BLOCK.sub("\n", s)
    s = _TAG.sub(" ", s)
    s = html_mod.unescape(s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


# WO TEXT AUFHOERT UND BINAERES ANFAENGT.
#
# Eine `.eml` aus Outlook kann nach dem Text einen Binaerteil tragen; im
# Mailprogramm endet sie nach «Liebe Gruesse», eingelesen folgten sonst
# seitenweise Steuerzeichen.
#
# `cp1252` UND `iso-8859-1` DECODIEREN JEDES BYTE. Sie werfen nie, und das
# ist bei echtem Text genau richtig — `entschluessle()` gibt es, damit
# `Müller` nicht zu `M?ller` wird. Bei Binaerem heisst dieselbe Eigenschaft:
# aus einem Bild wird klaglos «Text», und kein Fehler faellt an.
#
# Was hier zaehlt, ist nicht die Kodierung, sondern die LESBARKEIT.
_UNLESBAR = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]")

# Ein Block, ueber den geurteilt wird, und ab welchem Anteil er als
# unlesbar gilt. 200 Zeichen sind lang genug, dass ein einzelnes
# Sonderzeichen nichts ausmacht, und kurz genug, dass der Schnitt nahe an
# der Stelle sitzt, an der der Text wirklich aufhoert.
_BLOCKLAENGE = 200
_UNLESBAR_ANTEIL = 0.2
# Wie weit vor dem Schnitt noch nach dem Anfang der Zone gesucht wird.
_RUECKBLICK = 120


def text_bis_binaer(roh: str) -> tuple[str, int]:
    """Text bis zur ersten binaeren Stelle. Gibt Text und Rest zurueck.

    ⚠️ ABGESCHNITTEN, NICHT VERWORFEN. Wer eine Mail einliest, deren
    zweite Haelfte Binaeres ist, will die erste Haelfte — und er will
    WISSEN, dass etwas fehlt. Beides zu verschweigen waere der Fall, gegen
    den in diesem Projekt der Satz steht: ein leerer Befund ist keine
    Entwarnung.

    ⚠️ Und es wird NICHT gefiltert, sondern GESCHNITTEN. Einzelne
    Steuerzeichen aus einem Text zu entfernen aendert Textstellen, und
    Textstellen sind das, worueber die ganze Kette rechnet.
    """
    if not roh:
        return roh, 0
    for anfang in range(0, len(roh), _BLOCKLAENGE):
        block = roh[anfang:anfang + _BLOCKLAENGE]
        if len(_UNLESBAR.findall(block)) / len(block) <= _UNLESBAR_ANTEIL:
            continue
        # ⚠️ Geschnitten wird am ERSTEN unlesbaren Zeichen des Blocks, nicht
        # am Blockanfang. Sonst faellt der lesbare Text, der im selben Block
        # noch davor steht, mit weg — und genau der ist der Grund, warum
        # jemand die Mail einliest.
        erstes = _UNLESBAR.search(block)
        schnitt = anfang + (erstes.start() if erstes else 0)
        # Nicht zurueck bis zum letzten Zeilenumbruch — der liegt oft im
        # Binaeren: ein Bild enthaelt das Byte 0x0a so gut wie jedes andere.
        #
        # Aber zurueck bis zum Anfang der schmutzigen Zone. Der Block, der
        # anschlaegt, ist selten der erste mit Binaerem: davor steht meist schon
        # ein Stueck, das fuer sich allein unter der Schwelle blieb (ein PNG-Kopf
        # hat viel druckbares ASCII).
        #
        # Zwei unlesbare Zeichen im Fenster, nicht eines: ein einzelnes
        # Steuerzeichen kommt in echtem Text vor und soll den Schnitt nicht
        # hundert Zeichen weiter nach vorne ziehen.
        while schnitt > 0:
            fenster = max(0, schnitt - _RUECKBLICK)
            treffer = _UNLESBAR.findall(roh, fenster, schnitt)
            if len(treffer) < 2:
                break
            schnitt = _UNLESBAR.search(roh, fenster, schnitt).start()
        return roh[:schnitt].rstrip(), len(roh) - schnitt
    return roh, 0


def _kopfzeile(nachricht, feld: str) -> str:
    roh = nachricht.get(feld)
    if not roh:
        return ""
    try:
        return str(make_header(decode_header(str(roh))))
    except Exception:
        return str(roh)


KOPFFELDER = ("Date", "From", "To", "Cc", "Subject")


def mail_zu_text(nachricht) -> tuple[str, list[str]]:
    """Mail zu Text: die tragenden Kopfzeilen, dann der Rumpf.

    `From`, `To` und `Cc` sind bei einem Support-Ticket die dichteste Stelle
    fuer Personendaten ueberhaupt — Name und Adresse zusammen. Sie wegzulassen
    hiesse, den Filter genau dort blind zu machen.

    Die uebrigen Kopfzeilen (Received, Message-ID, DKIM …) bleiben draussen:
    Sie enthalten Rechnernamen und Zufallszeichenfolgen, die das Modell mit
    Fallnummern verwechseln wuerde, und in einem ausgedruckten Mailverlauf
    stehen sie ohnehin nicht.
    """
    hinweise: list[dict] = []
    zeilen = []
    for feld in KOPFFELDER:
        wert = _kopfzeile(nachricht, feld)
        if wert:
            zeilen.append(f"{feld}: {wert}")
    kopf = "\n".join(zeilen)

    rumpf, art = "", None
    if nachricht.is_multipart():
        for teil in nachricht.walk():
            if teil.get_content_maintype() == "multipart":
                continue
            if teil.get_filename():
                hinweise.append(hinweis(
                    "anhang_uebersprungen",
                    f"Anhang übersprungen: {teil.get_filename()}",
                    name=teil.get_filename()))
                continue
            typ = teil.get_content_type()
            if typ == "text/plain" and not rumpf:
                rumpf, art = _teil_text(teil), "text/plain"
            elif typ == "text/html" and art is None:
                rumpf, art = html_zu_text(_teil_text(teil)), "text/html"
    else:
        # ⚠️ NUR `text/*`. Hier stand vorher «alles andere gilt als
        # text/plain» — und damit wurde bei einer einteiligen Mail auch
        # ein Bild oder ein Datenstrom klaglos zu «Text». `cp1252`
        # decodiert jedes Byte, also fiel kein Fehler an.
        typ = nachricht.get_content_type()
        if typ == "text/html":
            rumpf, art = html_zu_text(_teil_text(nachricht)), "text/html"
        elif nachricht.get_content_maintype() == "text":
            rumpf, art = _teil_text(nachricht), "text/plain"
        else:
            hinweise.append(hinweis(
                "kein_textteil",
                f"Die Mail hat keinen Textteil, nur {typ}.", art=typ))

    if art == "text/html":
        hinweise.append(hinweis("nur_html",
                                "nur HTML-Teil vorhanden, grob entkleidet"))

    # Und dann der Schnitt am Binaeren. Er sitzt HIER und nicht in
    # `entschluessle()`: dort geht es um die Kodierung, und `cp1252` fuer
    # echten Text ist richtig. Die Frage nach der LESBARKEIT ist eine andere
    # und gehoert an die Stelle, an der ein Rumpf entsteht.
    rumpf, weggelassen = text_bis_binaer(rumpf)
    if weggelassen:
        hinweise.append(hinweis(
            "binaer_abgeschnitten",
            f"{weggelassen} Zeichen nach dem Textende sahen aus wie "
            f"Binärdaten und wurden weggelassen.", zeichen=weggelassen))

    if not rumpf.strip():
        hinweise.append(hinweis("kein_rumpf", "kein Textrumpf gefunden"))

    return (kopf + "\n\n" + rumpf).strip(), hinweise


# ---------------------------------------------------------------------------
# Outlook `.msg` — OLE2, nicht MIME
# ---------------------------------------------------------------------------

# ⚠️ Die Stroeme, in denen ein `.msg` seinen Inhalt fuehrt. Der Name kodiert
# die Eigenschaft und ihren Typ: `001F` ist UTF-16LE, `001E` eine
# 8-Bit-Kodierung. Beide koennen vorkommen; welche, entscheidet Outlook.
#
#   3007  Erstellungszeit        0037  Betreff
#   0C1A  Absendername           0E04  An
#   0E03  Kopie                  1000  Rumpf
MSG_FELDER = (
    ("Date", "3007"), ("From", "0C1A"), ("To", "0E04"),
    ("Cc", "0E03"), ("Subject", "0037"),
)
MSG_RUMPF = "1000"
# ⚠️ Nur der reine Textrumpf. Ein `.msg` fuehrt daneben oft eine
# RTF-Fassung (`10090102`, komprimiert) und eine HTML-Fassung — die
# RTF-Entpackung braeuchte ein weiteres Paket, und HTML liegt meist auch
# als Text vor. Fehlt der Textrumpf, wird das GESAGT und nichts geraten.


def _msg_strom(ole, kennung: str) -> str:
    """Eine Eigenschaft aus dem `.msg` holen. Leer, wenn es sie nicht gibt."""
    for endung, kodierung in (("001F", "utf-16-le"), ("001E", None)):
        name = f"__substg1.0_{kennung}{endung}"
        if not ole.exists(name):
            continue
        roh = ole.openstream(name).read()
        if kodierung:
            return roh.decode(kodierung, errors="replace").rstrip("\x00")
        return entschluessle(roh)[0].rstrip("\x00")
    return ""


def msg_zu_text(pfad: Path) -> tuple[str, list[str]]:
    """Ein Outlook-`.msg` zu Text: dieselben Kopffelder, dann der Rumpf.

    Outlook speichert `.msg` als OLE2-Verbunddokument — dasselbe Behaeltnis
    wie das alte `.doc`, nicht verwandt mit dem Textformat einer `.eml`.
    `email.message_from_bytes` findet darin keine Kopfzeilen und reichte den
    ganzen Binaerklumpen als Rumpf durch.

    `olefile` ist die zweite Ausnahme von «keine neuen Abhaengigkeiten ausser
    fuer PDF», und sie ist klein gewaehlt: eine einzelne Python-Datei, BSD,
    ohne eigene Abhaengigkeiten. `extract_msg` haette `compressed_rtf`,
    `beautifulsoup4` und `tzlocal` mitgebracht.

    Dieselben fuenf Kopffelder wie bei der `.eml`, aus demselben Grund:
    `From`, `To` und `Cc` sind die dichteste Stelle fuer Personendaten
    ueberhaupt.
    """
    try:
        import olefile
    except ImportError:
        raise Abbruch(
            "Fuer Outlook-Nachrichten (.msg) fehlt `olefile`.\n"
            "  pip install olefile\n"
            "  Oder in Outlook «Speichern unter» -> .eml waehlen.",
            schluessel="msg_ohne_olefile")

    hinweise: list[dict] = []
    try:
        ole = olefile.OleFileIO(str(pfad))
    except Exception as e:  # noqa: BLE001
        # ⚠️ Nicht nur `OSError`. `olefile` meldet einen kaputten Kopf mit
        # `ValueError` aus `struct` («bytes length not a multiple of item
        # size») — eine Meldung, die dem Anwender nichts sagt. Was er
        # braucht, ist der Ausweg.
        raise ValueError(
            f"Kein lesbares Outlook-.msg ({type(e).__name__}). "
            "In Outlook «Speichern unter» -> .eml waehlen, oder den Text "
            "von Hand einfuegen.")
    try:
        zeilen = []
        for feld, kennung in MSG_FELDER:
            wert = _msg_strom(ole, kennung).strip()
            if wert:
                zeilen.append(f"{feld}: {wert}")
        rumpf = _msg_strom(ole, MSG_RUMPF)
    finally:
        ole.close()

    if not rumpf.strip():
        # ⚠️ NICHT raten. Liegt der Rumpf nur als RTF oder HTML vor, ist
        # er nicht da, wo wir nachsehen — das zu verschweigen hiesse, eine
        # leere Maskierung als Entwarnung auszugeben.
        hinweise.append(hinweis(
            "msg_ohne_textrumpf",
            "Die .msg hat keinen reinen Textrumpf (nur RTF oder HTML). "
            "In Outlook «Speichern unter» -> .eml waehlen."))

    # ⚠️ Auch hier der Schnitt: ein `.msg` fuehrt Anhaenge im selben
    # Behaeltnis, und ein falsch benannter Strom brauchte nur einmal
    # durchzurutschen.
    rumpf, weggelassen = text_bis_binaer(rumpf)
    if weggelassen:
        hinweise.append(hinweis(
            "binaer_abgeschnitten",
            f"{weggelassen} Zeichen nach dem Textende sahen aus wie "
            f"Binärdaten und wurden weggelassen.", zeichen=weggelassen))

    kopf = "\n".join(zeilen)
    return (kopf + "\n\n" + rumpf).strip(), hinweise


def _teil_text(teil) -> str:
    roh = teil.get_payload(decode=True)
    if roh is None:
        return str(teil.get_payload())
    zeichensatz = teil.get_content_charset()
    if zeichensatz:
        try:
            return roh.decode(zeichensatz)
        except (UnicodeDecodeError, LookupError):
            pass
    return entschluessle(roh)[0]


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def pdf_zu_text(pfad: Path) -> tuple[str, list[str]]:
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf  # aeltere Paketnamen
        except ImportError:
            raise Abbruch(
                "PDF braucht pymupdf:\n"
                "  pip install pymupdf",
                schluessel="pdf_ohne_pymupdf")

    hinweise: list[dict] = []
    seiten = []
    with pymupdf.open(pfad) as dok:
        for n, seite in enumerate(dok, 1):
            seiten.append(seite.get_text())
    text = "\n\n".join(seiten)

    if not text.strip():
        hinweise.append(hinweis(
            "pdf_ohne_text",
            "kein Text im PDF — vermutlich ein Scan. Ohne OCR sieht der "
            "Filter nichts, und ein leerer Befund heisst hier NICHT, dass "
            "keine Personendaten drin sind."))
    else:
        hinweise.append(hinweis(
            "pdf_seiten",
            f"{len(seiten)} Seiten, Layout geht beim Auslesen verloren",
            anzahl=len(seiten)))
    return text, hinweise


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------
#
# ⚠️ Keine neue Abhaengigkeit. Ein `.docx` ist ein ZIP mit XML darin;
# `zipfile` und `xml.etree` liegen in der Standardbibliothek. `python-docx`
# waere MIT-lizenziert und lizenzrechtlich unbedenklich — es ist trotzdem die
# schlechtere Wahl, weil das README zusagt: «keine Abhaengigkeiten ausser
# PyYAML und Flask». Bei einem Datenschutzwerkzeug ist jede Bibliothek eine
# weitere Stelle, die den Text sieht.

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# ⚠️ Was `word/document.xml` AUSGEPACKT hoechstens wiegen darf.
#
# 64 MB und nicht das Zehnfache: ein Dokument ist laut Messung 1500 bis
# 4500 Zeichen, und selbst ein Buch mit tausend Seiten bleibt weit
# darunter. Die Zahl ist so gewaehlt, dass sie keine echte Datei trifft
# und trotzdem weit unter dem liegt, was ein praeparierter ZIP verspricht.
DOCX_HOECHSTENS = 64 * 1_000_000

# Eine Dokumenttyp-Erklaerung am Anfang des Teils. Nur `re` noetig — die
# Erklaerung steht laut XML-Spezifikation im Prolog, also ganz vorne.
_DTD = re.compile(rb"<!DOCTYPE|<!ENTITY", re.IGNORECASE)


def _docx_absatz(p) -> str:
    """Ein `<w:p>` zu Text. Laeufe zusammenziehen, Umbrueche behalten.

    Word zerlegt einen Satz in beliebig viele `<w:r>`, sobald sich die
    Formatierung aendert — «Frau Br» und «uelhart» koennen getrennte Laeufe
    sein. Wer je Lauf eine Zeile schreibt, zerschneidet Namen mitten im Wort,
    und weder Regex noch Modell erkennen sie wieder.
    """
    stueck: list[str] = []
    for k in p.iter():
        if k.tag == W + "t" and k.text:
            stueck.append(k.text)
        elif k.tag in (W + "br", W + "cr"):
            stueck.append("\n")
        elif k.tag == W + "tab":
            stueck.append("\t")
    return "".join(stueck)


def docx_zu_text(pfad: Path) -> tuple[str, list[str]]:
    import xml.etree.ElementTree as ET
    import zipfile

    hinweise: list[dict] = []
    try:
        with zipfile.ZipFile(pfad) as z:
            namen = set(z.namelist())
            # Erst die angekuendigte Groesse, dann lesen. `z.read()` packt aus, so
            # weit der Inhalt reicht — die Datei selbst sagt darueber nichts. DEFLATE
            # schafft rund 1 : 1000 (50 MB Inhalt in 48 KB); aus dem 10-MB-Limit des
            # Servers wuerden sonst rund 10 GB im Arbeitsspeicher. Die Grenze steht VOR
            # dem Auspacken.
            gross = z.getinfo("word/document.xml").file_size
            if gross > DOCX_HOECHSTENS:
                raise Abbruch(
                    f"word/document.xml waere {gross / 1e6:.0f} MB gross: "
                    f"{pfad}\n"
                    f"  Hoechstens {DOCX_HOECHSTENS // 1_000_000} MB werden "
                    f"ausgepackt. Ein Dokument dieser Groesse gibt es nicht; "
                    f"ein ZIP, das es behauptet, schon.",
                    schluessel="docx_zu_gross",
                    mb=f"{gross / 1e6:.0f}",
                    hoechstens=DOCX_HOECHSTENS // 1_000_000)
            roh = z.read("word/document.xml")
    except zipfile.BadZipFile:
        raise Abbruch(
            f"Keine lesbare .docx-Datei: {pfad}\n"
            "  Aeltere .doc sind ein anderes, binaeres Format.",
            schluessel="docx_kaputt")
    except KeyError:
        raise Abbruch(
            f"ZIP ohne word/document.xml: {pfad}\n"
            "  Vermutlich .odt, .pptx oder .xlsx mit falscher Endung.",
            schluessel="docx_ohne_dokument")

    # ⚠️ KEINE DTD, KEINE ENTITIES. `xml.etree.ElementTree` loest interne
    # Entities auf — GEMESSEN, nicht aus der Dokumentation uebernommen:
    # 209 Byte Quelltext ergaben 10 000 Zeichen bei vier Ebenen, und jede
    # weitere Ebene nimmt das Zehnfache. Zwei mehr sind ein Gigabyte. Die
    # Groessengrenze oben faengt das NICHT: die Quelle bleibt winzig.
    #
    # ⚠️ Und es kostet keine echte Datei. ECMA-376 verbietet DTDs in den
    # Teilen eines OOXML-Pakets ausdruecklich — was hier anschlaegt, ist
    # keine Word-Datei, die Word geschrieben hat.
    #
    # ⚠️ Ohne neue Abhaengigkeit, wie der Kopf dieses Abschnitts zusagt.
    # `defusedxml` waere der uebliche Weg; bei einem Werkzeug, dessen
    # README «keine Abhaengigkeiten ausser PyYAML und Flask» sagt,
    # sind zwei Zeilen die bessere Wahl.
    if _DTD.search(roh[:4096]):
        raise Abbruch(
            f"word/document.xml erklaert eine DTD: {pfad}\n"
            "  OOXML kennt keine; ein solcher Teil wird nicht gelesen.",
            schluessel="docx_dtd")

    wurzel = ET.fromstring(roh)
    koerper = wurzel.find(W + "body")
    if koerper is None:
        return "", ["docx ohne Körper — nichts zu lesen"]

    zeilen: list[str] = []
    tabellen = 0
    for kind in koerper:
        if kind.tag == W + "p":
            zeilen.append(_docx_absatz(kind))
        elif kind.tag == W + "tbl":
            # Zeilenweise, Zellen mit Tabulator getrennt — NICHT je Zelle eine Zeile.
            # Sonst steht in einem Formular das Etikett eine Zeile ueber dem Wert:
            #
            #     AHV-Nr.
            #     756.1234.5678.97
            #
            # und `anchor_same_line` verliert ihn. Das laesst sich hier beim Lesen
            # vermeiden statt spaeter im Muster.
            tabellen += 1
            for tr in kind.iter(W + "tr"):
                zellen = [
                    " ".join(_docx_absatz(p) for p in tc.iter(W + "p")).strip()
                    for tc in tr.findall(W + "tc")
                ]
                zeilen.append("\t".join(zellen))

    text = "\n".join(zeilen)

    if tabellen:
        hinweise.append(hinweis(
            "tabellen", f"{tabellen} Tabellen, zeilenweise gelesen",
            anzahl=tabellen))

    # ⚠️ Was hier NICHT mitkommt, muss gesagt werden. Der Grundsatz dieser
    # Datei ist «lieber zuviel Text als zuwenig»; was verlorengeht, kann der
    # Filter nicht maskieren, weil er es nie sieht. Ein Briefkopf mit Absender
    # steht bei Word regelmaessig in `header1.xml` — also genau dort, wo die
    # Personendaten sind.
    # ⚠️ Die Teilnamen sind SCHLUESSEL, keine Woerter. Ein Feld in `werte`
    # gilt als Liste von Schluesseln und wird in der Oberflaeche selbst
    # uebersetzt — sonst stuenden vier deutsche Woerter mitten in einem
    # italienischen Satz. `TEIL_NAMEN` traegt die deutsche Fassung fuer
    # `text` und fuer die Kommandozeile.
    aussen = []
    if any(n.startswith("word/header") for n in namen):
        aussen.append("t_kopfzeilen")
    if any(n.startswith("word/footer") for n in namen):
        aussen.append("t_fusszeilen")
    if "word/comments.xml" in namen:
        aussen.append("t_kommentare")
    if "word/footnotes.xml" in namen:
        aussen.append("t_fussnoten")
    if aussen:
        deutsch = ", ".join(TEIL_NAMEN[k] for k in aussen)
        hinweise.append(hinweis(
            "nicht_gelesen",
            f"NICHT gelesen: {deutsch} — dort steht bei Briefen oft "
            f"der Absender",
            teile=aussen))

    if not text.strip():
        hinweise.append(hinweis(
            "docx_leer",
            "kein Text im Dokument. Ein leerer Befund heisst hier NICHT, dass "
            "keine Personendaten drin sind."))
    return text, hinweise


# ---------------------------------------------------------------------------
# Einstieg
# ---------------------------------------------------------------------------

def lies(pfad: Path) -> list[Dokument]:
    """Eine Datei zu einem oder mehreren Dokumenten. `.mbox` liefert viele."""
    endung = pfad.suffix.lower()

    if endung in SAMMELENDUNGEN:
        import mailbox
        out = []
        kasten = mailbox.mbox(str(pfad))
        for i, nachricht in enumerate(kasten, 1):
            text, hinweise = mail_zu_text(nachricht)
            betreff = _kopfzeile(nachricht, "Subject")[:40] or "ohne Betreff"
            out.append(Dokument(text, f"{pfad.stem}#{i:03d} {betreff}",
                                "mbox", hinweise))
        return out

    if endung in MAILENDUNGEN:
        roh = pfad.read_bytes()
        # Ein `.msg` ist keine MIME-Mail (siehe `_msg_zu_text`). Geprueft wird die
        # SIGNATUR und nicht die Endung — D0CF11E0A1B11AE1, der Kopf jedes
        # OLE2-Dokuments. Eine `.msg`, die `.eml` heisst, ist immer noch OLE2.
        if roh[:8] == OLE2:
            text, hinweise = msg_zu_text(pfad)
            return [Dokument(text, pfad.name, "msg", hinweise)]
        nachricht = email.message_from_bytes(roh, policy=email.policy.default)
        text, hinweise = mail_zu_text(nachricht)
        return [Dokument(text, pfad.name, "eml", hinweise)]

    if endung in PDFENDUNGEN:
        text, hinweise = pdf_zu_text(pfad)
        return [Dokument(text, pfad.name, "pdf", hinweise)]

    if endung in DOCXENDUNGEN:
        text, hinweise = docx_zu_text(pfad)
        return [Dokument(text, pfad.name, "docx", hinweise)]

    # ⚠️ Vor dem Textzweig abfangen, nicht danach. `entschluessle` scheitert
    # bei einer `.doc` nicht — cp1252 nimmt jedes Byte an —, und der Filter
    # liefe auf Binaermuell mit einem beruhigend leeren Befund.
    if endung in ALTE_WORDENDUNGEN:
        raise Abbruch(
            f"Altes Word-Format wird nicht gelesen: {pfad}\n"
            "  `.doc` ist binaer, nicht ZIP+XML wie `.docx`.\n"
            "  In Word oder LibreOffice als .docx speichern.",
            schluessel="word_alt")

    roh = pfad.read_bytes()
    text, kodierung = entschluessle(roh)
    hinweise = []
    # `utf-8-sig` steht in KODIERUNGEN vor `utf-8` und trifft auch auf eine
    # gewoehnliche UTF-8-Datei ohne BOM zu. Gemeldet wird deshalb nur, was
    # nicht UTF-8 ist — und die BOM getrennt, weil sie ihren eigenen Grund hat:
    # sie verschiebt die Offsets. Ein Hinweis, der immer erscheint, sagt
    # nichts.
    if kodierung not in ("utf-8", "utf-8-sig"):
        hinweise.append(hinweis("kodierung", f"Kodierung {kodierung}",
                                kodierung=kodierung))
    elif roh.startswith(b"\xef\xbb\xbf"):
        hinweise.append(hinweis("bom",
                                "Byte-Order-Mark am Textanfang, entfernt"))
    return [Dokument(text, pfad.name, "text", hinweise)]


def sammle(pfad: Path) -> list[Path]:
    """Eine Datei oder alle lesbaren Dateien eines Verzeichnisses."""
    if pfad.is_file():
        return [pfad]
    return sorted(
        p for p in pfad.rglob("*")
        if p.is_file() and p.suffix.lower() in ALLE and not p.name.startswith(".")
    )
