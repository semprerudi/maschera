"""Der Mail-Einleser: nur der Textinhalt, und nichts, was nur so aussieht.

    python3 tests/test_mail.py

Eine Mail endet im Mailprogramm nach der Grussformel; im eingelesenen Text
duerfen danach keine Anhaenge als Steuerzeichen folgen. Diese Datei
prueft, was der Einleser koennen soll: `.eml`, `.msg` und `.mbox` stehen
auf der Liste der lesbaren Formate, und jedes davon braucht eine
Pruefung.

⚠️ **Alle Mails hier sind ERFUNDEN.** Keine Zeile stammt aus einem echten
Postfach; die Namen sind Kunstfiguren. Eine Pruefung mit einer echten
Mail waere ein Personendatum im Repository.
"""
import os
import sys
from email import message_from_bytes, policy
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))

from dokumente import (entschluessle, lies, mail_zu_text,  # noqa: E402
                       text_bis_binaer)

failures: list[str] = []
# ⚠️ Was NICHT lief, wird gemeldet. Ein wortloser Sprung meldet
# Bereitschaft.
uebersprungen: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def schluessel(hinweise) -> set:
    return {h.get("schluessel") if isinstance(h, dict) else str(h)
            for h in hinweise}


RUMPF = ("Sehr geehrte Damen und Herren\n\n"
         "Danke fuer Ihre Nachricht und die uebermittelten Unterlagen.\n\n"
         "Liebe Gruesse\nDomi\n")


print("1. Eine gewoehnliche Mail: Kopf und Rumpf, sonst nichts")
_einfach = (
    b"From: Domi Aebischer <domi@example.ch>\r\n"
    b"To: Support <support@example.ch>\r\n"
    b"Subject: Rueckfrage zum Dossier\r\n"
    b"Date: Tue, 2 Sep 2026 09:00:00 +0200\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
    + RUMPF.encode("utf-8"))
_text, _hin = mail_zu_text(message_from_bytes(_einfach,
                                              policy=policy.default))
check("Domi Aebischer" in _text, "der Absender fehlt im Text")
check("Rueckfrage zum Dossier" in _text, "der Betreff fehlt im Text")
check("Liebe Gruesse" in _text, "der Rumpf fehlt im Text")
# ⚠️ Received, Message-ID und DKIM bleiben draussen: Rechnernamen und
# Zufallsfolgen, die das Modell mit Fallnummern verwechselt.
check("Message-ID" not in _text, "technische Kopfzeilen stehen im Text")
check(not schluessel(_hin), f"unerwartete Hinweise: {schluessel(_hin)}")
if not failures:
    print("   OK   fuenf Kopffelder, Rumpf, keine Technik")


print("\n2. ⚠️ Binaeres nach dem Textende wird abgeschnitten UND gemeldet")
# ⚠️ DER GEMELDETE FALL. Eine einteilige Mail, deren Rumpf nach dem
# Gruss in Binaeres uebergeht — so kam sie beim Anwender an.
#
# ⚠️ Und warum kein Fehler anfiel: `cp1252` und `iso-8859-1` decodieren
# JEDES Byte. Sie werfen nie. Bei echtem Text ist das genau richtig; bei
# einem Bild heisst dieselbe Eigenschaft, dass daraus klaglos «Text»
# wird.
_mist = RUMPF + entschluessle(b"\x89PNG\r\n\x1a\n" + os.urandom(4000))[0]
_roh = (b"From: Domi <domi@example.ch>\r\n"
        b"Subject: Mit Anhang im Rumpf\r\n"
        b"Content-Type: text/plain; charset=iso-8859-1\r\n\r\n"
        + _mist.encode("iso-8859-1", errors="replace"))
_text2, _hin2 = mail_zu_text(message_from_bytes(_roh, policy=policy.default))
check("Liebe Gruesse" in _text2 and "Domi" in _text2,
      "der lesbare Teil ist mit weggefallen")
check("PNG" not in _text2,
      f"der Binaerteil steht noch im Text: {_text2[-120:]!r}")
check("binaer_abgeschnitten" in schluessel(_hin2),
      "es wurde abgeschnitten, aber nicht gemeldet — ein leerer Befund "
      "ist keine Entwarnung")
check(len(_text2) < 400,
      f"es blieben {len(_text2)} Zeichen stehen, erwartet unter 400")
if not failures:
    print(f"   OK   {len(_text2)} Zeichen behalten, Rest gemeldet")


print("\n3. Ein Anhang wird uebersprungen, der Text bleibt")
_mehrteilig = (
    b"From: Domi <domi@example.ch>\r\n"
    b"Subject: Mit Beilage\r\n"
    b'Content-Type: multipart/mixed; boundary="GRENZE"\r\n\r\n'
    b"--GRENZE\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
    + RUMPF.encode("utf-8") + b"\r\n"
    b"--GRENZE\r\n"
    b"Content-Type: application/pdf\r\n"
    b'Content-Disposition: attachment; filename="beilage.pdf"\r\n'
    b"Content-Transfer-Encoding: base64\r\n\r\n"
    b"JVBERi0xLjQKJcOkw7zDtsOfCg==\r\n"
    b"--GRENZE--\r\n")
_text3, _hin3 = mail_zu_text(message_from_bytes(_mehrteilig,
                                                policy=policy.default))
check("Liebe Gruesse" in _text3, "der Textteil fehlt")
check("JVBERi" not in _text3 and "PDF-1.4" not in _text3,
      "der Anhang steht im Text")
check("anhang_uebersprungen" in schluessel(_hin3),
      "der uebersprungene Anhang wird nicht gemeldet")
if not failures:
    print("   OK   Text da, Anhang draussen und benannt")


print("\n4. HTML wird entkleidet und als solches gemeldet")
_html = (b"From: Domi <domi@example.ch>\r\n"
         b"Subject: Nur HTML\r\n"
         b"Content-Type: text/html; charset=utf-8\r\n\r\n"
         b"<html><body><p>Sehr geehrte Damen</p>"
         b"<p>Liebe Gr&uuml;sse</p></body></html>")
_text4, _hin4 = mail_zu_text(message_from_bytes(_html, policy=policy.default))
check("Sehr geehrte Damen" in _text4, "der HTML-Text fehlt")
check("Liebe Grüsse" in _text4, "die HTML-Entitaet wurde nicht aufgeloest")
check("<p>" not in _text4, "die Auszeichnung steht noch im Text")
check("nur_html" in schluessel(_hin4), "der HTML-Rueckfall wird nicht gemeldet")
if not failures:
    print("   OK   entkleidet, Entitaeten aufgeloest, gemeldet")


print("\n5. ⚠️ Eine Mail OHNE Textteil erfindet keinen")
# ⚠️ Nicht «alles andere gilt als text/plain»: sonst wird bei einer
# einteiligen Mail auch ein Bild klaglos zu «Text» — und weil `cp1252` nie
# wirft, saehe es niemand.
_bild = (b"From: Domi <domi@example.ch>\r\n"
         b"Subject: Nur ein Bild\r\n"
         b"Content-Type: image/png\r\n"
         b"Content-Transfer-Encoding: base64\r\n\r\n"
         b"iVBORw0KGgoAAAANSUhEUg==\r\n")
_text5, _hin5 = mail_zu_text(message_from_bytes(_bild, policy=policy.default))
check("kein_textteil" in schluessel(_hin5),
      f"eine Mail ohne Textteil wird nicht gemeldet: {schluessel(_hin5)}")
check("PNG" not in _text5 and "IHDR" not in _text5,
      f"aus einem Bild wurde Text: {_text5[:120]!r}")
check("kein_rumpf" in schluessel(_hin5),
      "der fehlende Rumpf wird nicht gemeldet")
if not failures:
    print("   OK   kein erfundener Text, zweimal gemeldet")


print("\n6. ⚠️ Ein Outlook-.msg wird als OLE2 erkannt und gelesen")
# ⚠️ Outlook speichert `.msg` als OLE2-Verbunddokument — Signatur
# D0CF11E0A1B11AE1, dasselbe Behaeltnis wie das alte `.doc`, nicht entfernt
# verwandt mit dem Textformat einer `.eml`. `email.message_from_bytes`
# findet darin keine Kopfzeilen und reicht den ganzen Klumpen als Rumpf
# durch: seitenweise Steuerzeichen oder, nach einem Binaerschnitt, zwei
# Zeichen «ÐÏ» — beides falsch, und beides ohne ein Wort darueber, was los
# ist.
#
# ⚠️ Geprueft wird die SIGNATUR, nicht die Endung: eine `.msg`, die `.eml`
# heisst, ist immer noch OLE2.
import tempfile  # noqa: E402

import dokumente as _D  # noqa: E402

# ⚠️ AN DER SIGNATUR, NICHT AN DER ENDUNG. Genau so kam sie beim Anwender
# an: ein `.msg`, das `.eml` hiess. Ein kaputter Klumpen mit richtiger
# Signatur muss sauber abgewiesen werden — mit dem Ausweg im Satz.
for _name in ("nachricht.msg", "nachricht.eml"):
    with tempfile.TemporaryDirectory() as _ordner:
        _p = Path(_ordner) / _name
        _p.write_bytes(_D.OLE2 + b"\x00" * 4000)
        try:
            _D.lies(_p)
            check(False, f"{_name}: ein kaputtes OLE2 wurde gelesen")
        except ValueError as e:
            check(".eml" in str(e),
                  f"{_name}: die Absage sagt nicht, was zu tun ist: {e}")
        except Exception as e:  # noqa: BLE001
            check(False, f"{_name}: unerwartete Ausnahme {type(e).__name__}: {e}")

# ⚠️ UND DIE EXTRAKTION SELBST, gegen einen Doppelgaenger von
# `OleFileIO`. Ein echtes `.msg` hier zu erzeugen hiesse, einen
# CFB-SCHREIBER zu bauen — `olefile` liest nur. Was diese Pruefung
# deshalb NICHT abdeckt: dass `olefile` eine echte Outlook-Datei richtig
# aufschliesst. Das ist ehrlicher hinzuschreiben, als eine Zusage
# vorzutaeuschen.
#
# Was sie ABDECKT, ist unser Teil: welche Stroeme gelesen werden, welche
# Kodierung sie tragen, und dass der Rumpf gemeldet wird, wenn er fehlt.
class _OleDoppel:
    def __init__(self, stroeme):
        self.stroeme = stroeme
    def exists(self, name):
        return name in self.stroeme
    def openstream(self, name):
        import io
        return io.BytesIO(self.stroeme[name])
    def close(self):
        pass

_voll = _OleDoppel({
    "__substg1.0_0037001F": "Rueckfrage zum Dossier".encode("utf-16-le"),
    "__substg1.0_0C1A001F": "Domi Aebischer".encode("utf-16-le"),
    "__substg1.0_0E04001F": "Support".encode("utf-16-le"),
    "__substg1.0_1000001F": RUMPF.encode("utf-16-le"),
})
check(_D._msg_strom(_voll, "1000") == RUMPF,
      "der UTF-16-Rumpf kommt nicht zurueck")
check(_D._msg_strom(_voll, "0037") == "Rueckfrage zum Dossier",
      "der Betreff kommt nicht zurueck")
check(_D._msg_strom(_voll, "9999") == "",
      "eine fehlende Eigenschaft liefert nicht leer")

# ⚠️ Die 8-Bit-Fassung `001E` ist der andere Fall, den Outlook schreibt.
_acht = _OleDoppel({"__substg1.0_1000001E": "Grüezi Müller".encode("cp1252")})
check(_D._msg_strom(_acht, "1000") == "Grüezi Müller",
      f"die 8-Bit-Fassung kommt falsch zurueck: "
      f"{_D._msg_strom(_acht, '1000')!r}")

# ⚠️ UND DIE GANZE FUNKTION, indem `olefile.OleFileIO` fuer die Dauer der
# Pruefung durch den Doppelgaenger ersetzt wird. Damit laeuft `msg_zu_text`
# wirklich durch — Kopffelder, Rumpf, Hinweise — und nicht nur seine
# Bausteine.
# ⚠️ OHNE `olefile` WIRD DIESER PUNKT UEBERSPRUNGEN UND NICHT ROT. Es fehlt
# dann eine Abhaengigkeit, nichts ist kaputt, und `dokumente.py` sagt das
# dem Anwender auch («Fuer Outlook-Nachrichten (.msg) fehlt `olefile`»).
# Eine Pruefung, die eine fehlende Abhaengigkeit als Fehler meldet,
# schickt den Naechsten in den Code statt in `pip`.
#
# ⚠️ Aber NICHT still: der Sprung wird unten aufgezaehlt. Ein
# uebersprungener Punkt, den niemand sieht, ist schlimmer als ein roter.
try:
    import olefile as _olefile  # noqa: E402
except ImportError:
    _olefile = None
    uebersprungen.append(
        "Punkt 6 (.msg / OLE2): `olefile` fehlt — pip install olefile")
    print("   UEBERSPRUNGEN — `olefile` fehlt, .msg ungeprueft")

if _olefile is not None:

    _echt = _olefile.OleFileIO
    try:
        _olefile.OleFileIO = lambda _pfad: _voll
        with tempfile.TemporaryDirectory() as _o:
            _p = Path(_o) / "echt.msg"
            _p.write_bytes(_D.OLE2 + b"\x00" * 16)
            _t6, _h6 = _D.msg_zu_text(_p)
        check("Subject: Rueckfrage zum Dossier" in _t6,
              f"der Betreff steht nicht im Text: {_t6[:80]!r}")
        check("From: Domi Aebischer" in _t6, "der Absender fehlt")
        check("Liebe Gruesse" in _t6, "der Rumpf fehlt")
        check(not schluessel(_h6), f"unerwartete Hinweise: {schluessel(_h6)}")

        # ⚠️ Kein Textrumpf -> GESAGT, nicht geraten. Ein `.msg` fuehrt ihn oft
        # nur als komprimiertes RTF. Das zu verschweigen hiesse, eine leere
        # Maskierung als Entwarnung auszugeben.
        _olefile.OleFileIO = lambda _pfad: _OleDoppel(
            {"__substg1.0_0037001F": "Nur Betreff".encode("utf-16-le")})
        with tempfile.TemporaryDirectory() as _o:
            _p = Path(_o) / "ohne.msg"
            _p.write_bytes(_D.OLE2 + b"\x00" * 16)
            _t7, _h7 = _D.msg_zu_text(_p)
        check("msg_ohne_textrumpf" in schluessel(_h7),
              f"der fehlende Textrumpf wird nicht gemeldet: {schluessel(_h7)}")
        check("Nur Betreff" in _t7, "der Betreff ging mit verloren")
    finally:
        _olefile.OleFileIO = _echt

    # ⚠️ UND DIE ABSAGE MUSS IM DIENST ANKOMMEN. `SystemExit` ist KEINE
    # `Exception` — die Absagen aus `dokumente.py` (altes `.doc`, fehlendes
    # `pymupdf`, kaputtes ZIP) flogen am Behandler in `app/serve.py` vorbei
    # und wurden zur 500. Eine saubere Absage sah im Browser aus wie ein
    # Absturz des Dienstes. Deshalb hier `ValueError` und dort beide.
    _serve = (WURZEL / "app" / "serve.py").read_text(encoding="utf-8")
    check("except (Exception, SystemExit)" in _serve,
          "`serve.py` faengt `SystemExit` aus den Einlesern nicht — eine "
          "Absage wird dort zur 500")
    if not failures:
        print("   OK   Signatur erkannt, Stroeme gelesen, fehlender Rumpf gemeldet")

print("\n7. Echter Text wird NICHT angetastet")
# ⚠️ Die Gegenrichtung, und sie ist die wichtigere: eine Wache, die
# Binaeres wegschneidet, darf keinen Umlaut und keinen Tabulator fuer
# Binaeres halten. `Müller` als `M?ller` waere ein Name, den weder Regex
# noch Modell wiedererkennt.
for _probe, _was in [
        ("Grüezi Müller, Öl & Käse — 20 % à Fr. 5.–", "Umlaute und Zeichen"),
        ("Spalte\tWert\r\nZeile\tZwei\n", "Tabulatoren und CRLF"),
        ("Ein ganz normaler Satz. " * 400, "ein langer Text"),
        ("Café Zürich–Bern „Zitat“", "Sonderzeichen"),
        ("", "der leere Text")]:
    _t, _weg = text_bis_binaer(_probe)
    check(_weg == 0 and _t == _probe,
          f"{_was} wurde angetastet: {_weg} Zeichen weg")
if not failures:
    print("   OK   fuenf Proben unveraendert")


print("\n8. ⚠️ .mbox — das dritte Format auf der Liste, nie geprueft")
# ⚠️ `.mbox` laeuft durch dieselbe Funktion wie `.eml` — aber ueber
# `mailbox`, und deshalb braucht es einen eigenen Punkt. Jedes Format auf
# der Liste der lesbaren braucht einen.
import tempfile  # noqa: E402
_d = Path(tempfile.mkdtemp())

_mbox = _d / "post.mbox"
_mbox.write_text(
    "From alice@example.ch Mon Sep  1 10:00:00 2026\n"
    "From: Alice <alice@example.ch>\nTo: bob@example.ch\n"
    "Subject: Erste Nachricht\n\nHallo Bob, das ist die erste.\n\n"
    "From bob@example.ch Mon Sep  1 11:00:00 2026\n"
    "From: Bob <bob@example.ch>\nTo: alice@example.ch\n"
    "Subject: Zweite Nachricht\n\nUnd das die zweite.\n", encoding="utf-8")
_docs = lies(_mbox)
check(len(_docs) == 2, f"eine mbox mit zwei Nachrichten ergab {len(_docs)}")
if len(_docs) == 2:
    check(all(d.format == "mbox" for d in _docs), "das Format heisst nicht mbox")
    # ⚠️ Die Kennung muss die Nachrichten UNTERSCHEIDBAR machen. Zwei
    # Dokumente mit demselben Namen sind beim Auswerten nicht zuzuordnen —
    # dieselbe Begruendung wie beim Platzhaltervertrag.
    check(_docs[0].kennung != _docs[1].kennung,
          "beide Nachrichten tragen dieselbe Kennung")
    check("#001" in _docs[0].kennung and "#002" in _docs[1].kennung,
          f"die Nachrichten sind nicht durchnummeriert: {_docs[0].kennung!r}")
    check("Erste Nachricht" in _docs[0].kennung,
          "der Betreff steht nicht in der Kennung")
    check("erste" in _docs[0].text and "zweite" in _docs[1].text,
          "die Rumpftexte sind vertauscht oder fehlen")
    # Und der Kopf kommt mit, wie bei einer .eml — eine Absenderadresse
    # ist ein Personendatum und muss in den Text, nicht daran vorbei.
    check("alice@example.ch" in _docs[0].text,
          "die Absenderadresse fehlt im Text — sie waere unmaskierbar")

# ⚠️⚠️ NULL NACHRICHTEN IST EIN BEFUND. `mailbox.mbox` braucht die
# `From `-Trennzeile am Zeilenanfang. Eine leere Datei ergibt null — und
# eine `.eml`, die jemand `.mbox` genannt hat, EBENFALLS. Beide Faelle
# sahen aus wie «gelesen, nichts drin».
#
# Der Grundsatz des Projekts: ein leerer Befund ist keine Entwarnung.
_leer = _d / "leer.mbox"
_leer.write_text("", encoding="utf-8")
check(lies(_leer) == [], "eine leere mbox erfindet Nachrichten")

_falsch = _d / "falsch.mbox"
_falsch.write_text("From: a@b.ch\nSubject: Kein Trenner\n\nText hier.\n",
                   encoding="utf-8")
check(lies(_falsch) == [],
      "eine .eml unter .mbox-Namen wird stillschweigend gelesen — dann "
      "haengt das Ergebnis am Dateinamen statt am Inhalt")

# ⚠️ Und BEIDE Wege muessen es sagen: der Server (`datei_ohne_text`) und
# die Kommandozeile.
_ft = (WURZEL / "tools/filter_document.py").read_text(encoding="utf-8")
check("if not dokumente:" in _ft and "LEER:" in _ft,
      "filter_document laeuft ueber eine leere Sammeldatei wortlos hinweg")
_sv = (WURZEL / "app/serve.py").read_text(encoding="utf-8")
check('schluessel="datei_ohne_text"' in _sv,
      "der Server meldet eine textlose Datei nicht mehr")
if not failures:
    print("   OK   zwei Nachrichten getrennt, null Nachrichten gemeldet")


print()
if uebersprungen:
    # ⚠️ `UEBERSPRUNGEN` am Zeilenanfang — `run_tests.py` erkennt den
    # Sprung an dieser Marke und nicht am Wort irgendwo im Text. Die
    # Wortsuche hat zweimal die falsche Pruefung getroffen.
    print("UEBERSPRUNGEN — ⚠ NICHT VOLLSTAENDIG GELAUFEN:")
    for u in dict.fromkeys(uebersprungen):
        print(f"    {u}")
    print("  Die uebrigen Punkte liefen. `.msg` ist damit UNGEPRUEFT —")
    print("  das ist keine Entwarnung, sondern eine fehlende Messung.")
    print()

if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Mail-Einleser in Ordnung — nur Textinhalt.")
