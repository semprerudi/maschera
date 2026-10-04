#!/usr/bin/env python3
"""Die Endpunkte aus `docs/API_OBERFLAECHE.md`.

    python3 tests/test_api.py

Laeuft OHNE Modell — Stufe 1 und 2 genuegen, um die FORM der Antwort zu
pruefen. Was das Modell erkennt, misst `eval_documents.py` und nicht dieser
Test; hier geht es um den Vertrag zwischen Kern und Oberflaeche.

⚠️ Was hier besonders geprueft wird, weil es in der Oberflaeche NICHT
auffaellt:

  - `nicht_gefunden` bei der Rueckwandlung. Ein Sprachmodell schreibt
    Platzhalter um; wenn der Server das verschweigt, steht am Ende ein
    `[FULLNAME_1]` im Brief und niemand hat es bemerkt.
  - `PUT /api/regeln` mit kaputtem YAML. Eine abgelehnte Regeldatei darf die
    bestehende nicht ueberschreiben — sonst laeuft der naechste Lauf ohne
    Regeln, und das Messergebnis aendert sich still.
  - `bspd` ohne `auch_bspd`. Besonders schuetzenswerte Personendaten duerfen
    nicht ueber einen Schalter im Klartext landen, den man einmal umlegt.
"""
import io
import json
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "app"))

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


try:
    import flask  # noqa: F401
except ImportError:
    # Die Marke, an der `tools/run_tests.py` es erkennt.
    print("UEBERSPRUNGEN: Flask nicht installiert.")
    raise SystemExit(0)

from serve import Zustand, baue  # noqa: E402

# Eigene Regeldatei, damit der Test die des Anwenders nicht anfasst.
ORDNER = tempfile.TemporaryDirectory()
REGELN = Path(ORDNER.name) / "regeln.yaml"

z = Zustand("ch", regeln_pfad=str(REGELN))
app = baue(z)
c = app.test_client()

TEXT = (
    "Sehr geehrte Damen und Herren\n\n"
    "Betreffend Dossier 2024-77310 melde ich einen Wohnungswechsel.\n"
    "Meine AHV-Nummer lautet 756.1234.5678.97.\n"
    "Erreichbar bin ich unter andrea.bruelhart@example.ch, 031 322 11 22.\n"
    "Neue Adresse: Sonnenbergstrasse 14, 3011 Bern.\n"
    "Freundliche Gruesse, A. Brülhart\n"
)

print("1. Zustand")
r = c.get("/api/zustand")
check(r.status_code == 200, f"zustand {r.status_code}")
d = r.get_json()
check(d["dienst"] == "maschera", "Dienstname fehlt")
check(d["tags"] == 45, f"45 Tags erwartet, {d['tags']}")
check(len(d["label_hash"]) == 64, "Labelvertrag-Fingerabdruck fehlt")
check(d["ohne_modell"] is True, "ohne_modell nicht gemeldet")
check(d["hinweise"], "ohne Modell ohne Hinweis — das ist eine Leckquelle")
# ⚠️ Die Obergrenze kommt aus dem Endpunkt, nicht aus dem Hilfetext.
# Gegen `MAX_UPLOAD` gerechnet und nicht gegen eine abgeschriebene Zahl —
# sonst waere die Wache selbst der zweite Verwalter, den sie verhindern
# soll. Dieselbe Lehre wie bei der ORG-Schwelle sechs Zeilen tiefer.
from serve import MAX_UPLOAD as _max  # noqa: E402
check(d["max_mb"] == _max // (1024 * 1024),
      f"max_mb {d.get('max_mb')} passt nicht zu MAX_UPLOAD")
check(d["max_mb"] > 0, "die Hilfe bekaeme eine Null als Obergrenze")

print("2. Tags")
r = c.get("/api/tags")
d = r.get_json()
check(len(d["tags"]) == 45, f"45 Tags erwartet, {len(d['tags'])}")
eintraege = {t["tag"]: t for t in d["tags"]}
check(all(t["bezeichnung"] for t in d["tags"]),
      "Tag ohne Bezeichnung — leerer Menueeintrag in der Oberflaeche")
# ⚠️ Gegen den Pack pruefen, nicht gegen eine abgeschriebene Zahl: die
# Zeile prueft, dass die Oberflaeche dieselbe Schwelle sieht wie die
# Kette. Eine abgeschriebene Zahl wird rot, sobald sich die Schwelle durch
# eine Messung aendert, obwohl der Endpunkt richtig antwortet.
from packs import load_pack as _load_pack  # noqa: E402
_schwellen = _load_pack("ch").get_thresholds()
_ab = {tag: (e["schwelle"], _schwellen[tag]) for tag, e in eintraege.items()
       if tag in _schwellen and e["schwelle"] != _schwellen[tag]}
check(not _ab, f"Endpunkt und Pack uneins ueber die Schwelle: {_ab}")
check(eintraege["CANTON"]["aktion"] == "tag_only", "CANTON nicht tag_only")
check(eintraege["AHVN13"]["pruefsumme"] is True, "AHVN13 ohne Pruefsumme")
check(eintraege["NATIONALITY"]["bspd"] is True, "NATIONALITY nicht bspd")
check(d["sprache"] == "de", "Sprache fehlt in der Antwort")

# Vier Sprachen, jede vollstaendig. Eine Oberflaeche mit leeren
# Menueeintraegen ist der Grund, warum das hier geprueft wird.
for sprache, probe, erwartet in [("fr", "PLACE_OF_ORIGIN", "Lieu d'origine"),
                                 ("it", "PLACE_OF_ORIGIN", "Luogo di attinenza"),
                                 ("en", "PLACE_OF_ORIGIN", "Place of origin")]:
    ds = c.get(f"/api/tags?sprache={sprache}").get_json()
    check(len(ds["tags"]) == 45, f"{sprache}: 45 Tags erwartet")
    check(all(t["bezeichnung"] for t in ds["tags"]),
          f"{sprache}: Tag ohne Bezeichnung")
    treffer = {t["tag"]: t["bezeichnung"] for t in ds["tags"]}
    check(treffer[probe] == erwartet,
          f"{sprache}: {probe} ist {treffer[probe]!r}, erwartet {erwartet!r}")
check(c.get("/api/tags?sprache=rm").status_code == 400,
      "unbekannte Sprache nicht abgewiesen — sie faellt sonst still auf Deutsch")

print("3. Maskieren")
r = c.post("/api/anonymisieren", json={"text": TEXT})
check(r.status_code == 200, f"anonymisieren {r.status_code}")
d = r.get_json()
check(d["original"] == TEXT, "Original nicht unveraendert zurueck")
check("756.1234.5678.97" not in d["maskiert"], "AHV-Nummer nicht maskiert")
check("[AHVN13_1]" in d["maskiert"], "Platzhalter [AHVN13_1] fehlt")
check(d["kennzahlen"]["zeichen"] == len(TEXT), "Zeichenzahl falsch")
check(d["kennzahlen"]["fundstellen"] == len(d["spans"]), "Fundstellen != spans")
check(d["hinweise"], "Hinweis ohne Modell fehlt")

felder = {"tag", "start", "end", "platzhalter", "quelle", "vertrauen",
          "bspd", "budget", "zeile"}
check(all(felder <= set(s) for s in d["spans"]),
      "einer Fundstelle fehlen Felder aus API_OBERFLAECHE.md")
ahv = [s for s in d["spans"] if s["tag"] == "AHVN13"]
check(len(ahv) == 1, f"eine AHVN13 erwartet, {len(ahv)}")
if ahv:
    check(ahv[0]["quelle"] in ("regex", "checksum"),
          f"AHVN13 aus {ahv[0]['quelle']}")
    check(TEXT[ahv[0]["start"]:ahv[0]["end"]] == "756.1234.5678.97",
          "Positionen zeigen nicht ins ORIGINAL")
    check(ahv[0]["vertrauen"] is None, "Vertrauen bei Muster nicht null")

print("3b. Vertrauen wird richtig zugeordnet")
# Ein erfundener Laeufer, damit der Test ohne Modell prueft, was nur MIT
# Modell auffiel: eine ausgedehnte Spanne verliert ihren Schluessel, und ein
# Regextreffer erbt zufaellig eine Modellzahl.
from core.inference import Scored  # noqa: E402


class Probelaeufer:
    """Meldet eine halbe Spanne mitten im Wort und eine, die auf einem
    Regextreffer sitzt."""

    def __init__(self, treffer):
        self.treffer = treffer

    def score(self, text):
        return list(self.treffer)


TEXT2 = "Die Mitarbeiterin Bruelhart schrieb an a@b.ch."
i = TEXT2.index("Bruelhart")
j = TEXT2.index("a@b.ch")
from serve import Mitschreiber  # noqa: E402

z2 = Zustand("ch", regeln_pfad=str(Path(ORDNER.name) / "leer.yaml"))
z2.scorer = Mitschreiber(Probelaeufer([
    Scored("FULLNAME", i, i + 4, 0.42),      # halbes Wort -> wird ausgedehnt
    Scored("EMAIL", j, j + 6, 0.99),         # deckungsgleich mit der Regex
]))
z2.modellname = "probe"
c2 = baue(z2).test_client()
d8 = c2.post("/api/anonymisieren", json={"text": TEXT2}).get_json()
nach = {s["tag"]: s for s in d8["spans"]}
check(nach["FULLNAME"]["vertrauen"] == 0.42,
      f"ausgedehnte Modellspanne ohne Vertrauen: {nach['FULLNAME']}")
check(nach["EMAIL"]["quelle"] != "model" and nach["EMAIL"]["vertrauen"] is None,
      f"Regextreffer traegt eine Modellzahl: {nach['EMAIL']}")

print("4. Rueckwandeln")
wb = d["woerterbuch"]
check(wb, "Woerterbuch leer")
antwort = "Die Person mit [AHVN13_1] schreibt von [EMAIL_1] aus."
r = c.post("/api/zurueckwandeln", json={"text": antwort, "woerterbuch": wb})
d2 = r.get_json()
check("756.1234.5678.97" in d2["text"], "AHV-Nummer nicht zurueckgeschrieben")
check("example.ch" in d2["text"], "Mailadresse nicht zurueckgeschrieben")
check(d2["ersetzt"] >= 1, "nichts ersetzt")
check(d2["nicht_gefunden"] == [], f"unerwartet offen: {d2['nicht_gefunden']}")

# Der eigentliche Fall: das Sprachmodell hat den Platzhalter umgeschrieben.
r = c.post("/api/zurueckwandeln",
           json={"text": "Herr [FULLNAME_9] und [ahvn13_1].", "woerterbuch": wb})
d2 = r.get_json()
check("[FULLNAME_9]" in d2["nicht_gefunden"],
      "erfundener Platzhalter nicht gemeldet")
check("[FULLNAME_9]" in d2["text"], "erfundener Platzhalter still entfernt")
check(any(h["schluessel"] == "schreibweise" for h in d2["hinweise"]),
      "abweichende Schreibweise nicht gemeldet")

print("5. Ohne Woerterbuch — endgueltig")
r = c.post("/api/anonymisieren", json={"text": TEXT, "woerterbuch": False})
d3 = r.get_json()
check(d3["woerterbuch"] == {}, "Woerterbuch trotz woerterbuch=false gefuellt")
check("[AHVN13_1]" in d3["maskiert"], "Nummerierung fehlt trotzdem")
# ⚠️ «Rückwandlung» mit Umlaut. Die Hinweise sind SICHTBARER Text und
# tragen echte Umlaute; die Ersatzschreibung ist die Regel fuer
# Kommentare, nicht fuer die Oberflaeche.
check(any(h["schluessel"] == "ohne_woerterbuch" for h in d3["hinweise"]),
      "fehlende Umkehrbarkeit nicht gemeldet")

print("6. Klartext-Tags und bsPD")
r = c.post("/api/anonymisieren", json={"text": TEXT, "ohne": ["EMAIL"]})
d4 = r.get_json()
check("andrea.bruelhart@example.ch" in d4["maskiert"],
      "EMAIL trotz `ohne` maskiert")
mail = [s for s in d4["spans"] if s["tag"] == "EMAIL"]
check(mail and mail[0]["platzhalter"] is None,
      "nicht ersetztes Tag traegt einen Platzhalter")
r = c.post("/api/anonymisieren", json={"text": TEXT, "ohne": ["NATIONALITY"]})
check(r.status_code == 400,
      "bsPD im Klartext ohne auch_bspd durchgelassen")
r = c.post("/api/anonymisieren",
           json={"text": TEXT, "ohne": ["NATIONALITY"], "auch_bspd": True})
check(r.status_code == 200, "auch_bspd wirkt nicht")
r = c.post("/api/anonymisieren", json={"text": TEXT, "ohne": ["GIBTESNICHT"]})
check(r.status_code == 400, "unbekanntes Tag nicht abgewiesen")

print("7. Leerer und fehlender Text")
check(c.post("/api/anonymisieren", json={"text": "   "}).status_code == 400,
      "leerer Text nicht abgewiesen")
check(c.post("/api/anonymisieren", json={}).status_code == 400,
      "fehlender Text nicht abgewiesen")

print("8. Datei statt Text")
with tempfile.TemporaryDirectory() as ordner:
    p = Path(ordner) / "ticket.txt"
    p.write_bytes(TEXT.encode("cp1252"))  # Umlaut -> nicht als UTF-8 lesbar
    with p.open("rb") as fh:
        r = c.post("/api/anonymisieren", data={"datei": (fh, "ticket.txt")},
                   content_type="multipart/form-data")
    d5 = r.get_json()
    check(r.status_code == 200, f"Datei {r.status_code}")
    check("[AHVN13_1]" in d5["maskiert"], "Datei nicht maskiert")
    check(any(h["werte"].get("kodierung") == "cp1252"
              for h in d5["hinweise"]),
          f"Kodierung nicht gemeldet: {d5['hinweise']}")

    # Gegenprobe: eine gewoehnliche UTF-8-Datei darf KEINEN Kodierungshinweis
    # ausloesen — `utf-8-sig` trifft auch ohne BOM.
    p3 = Path(ordner) / "sauber.txt"
    p3.write_text(TEXT, encoding="utf-8")
    with p3.open("rb") as fh:
        r = c.post("/api/anonymisieren", data={"datei": (fh, "sauber.txt")},
                   content_type="multipart/form-data")
    check(not any(h["schluessel"] == "kodierung"
                  for h in r.get_json()["hinweise"]),
          "UTF-8 loest einen Kodierungshinweis aus")

    p2 = Path(ordner) / "bild.png"
    p2.write_bytes(b"\x89PNG")
    with p2.open("rb") as fh:
        r = c.post("/api/anonymisieren", data={"datei": (fh, "bild.png")},
                   content_type="multipart/form-data")
    check(r.status_code == 400, "unlesbares Format nicht abgewiesen")

print("8a. Ein boesartiger Dateiname bricht nichts auf und stuerzt nicht ab")
# ⚠️⚠️ `_datei_lesen` nimmt den Namen aus dem Formular. Zwei Fragen, zwei
# Antworten:
#
#   AUSBRUCH   `Path(name).name` streift das Verzeichnis ab. Der Name
#              landet IMMER im temporaeren Ordner, nie darueber.
#
#   ABSTURZ    Bei `..`, `.` und `/` bleibt nach dem Abstreifen nichts
#              (bzw. `..`) uebrig, `pfad` zeigte auf das VERZEICHNIS, und
#              `datei.save()` wuerfe `IsADirectoryError` am Behandler
#              vorbei: HTTP 500 mit HTML-Rueckverfolgung, wo
#              `docs/API_OBERFLAECHE.md` eine JSON-Absage zusagt.
#
# Geprueft wird die EIGENSCHAFT: kein 5xx, egal was im Namen steht. Die
# Liste unten ist die Stichprobe, die Bedingung ist allgemein.
for _name in ("..", ".", "/", "", "../../etc/passwd", "..\\..\\boese.txt",
              "x/../../y.txt", "a" * 300 + ".txt", "\x00.txt", "-.txt"):
    r = c.post("/api/lesen",
               data={"datei": (io.BytesIO(b"Hallo Welt"), _name)},
               content_type="multipart/form-data")
    check(r.status_code < 500,
          f"Dateiname {_name!r} ergibt {r.status_code} — der Server "
          f"stuerzt an einem Namen ab, statt ihn abzuweisen")
    check(r.headers.get("Content-Type", "").startswith("application/json"),
          f"Dateiname {_name!r}: Antwort ist kein JSON "
          f"({r.headers.get('Content-Type')!r}) — der Vertrag sagt JSON")
print("   OK   10 Namen, kein 5xx, jede Antwort JSON")

print("8b. /api/lesen liest — und maskiert NICHT")
# ⚠️ Eine abgelegte Datei wird nur GELESEN, nicht maskiert — sonst fuehre
# ein Ablegen die ganze Kette, ohne dass jemand MASKIEREN gedrueckt hat.
# Hier steht der Vertrag dazu: Klartext zurueck, KEIN `maskiert`, KEIN
# Woerterbuch.
with tempfile.TemporaryDirectory() as ordner:
    p = Path(ordner) / "ticket.txt"
    p.write_bytes(TEXT.encode("cp1252"))
    with p.open("rb") as fh:
        r = c.post("/api/lesen", data={"datei": (fh, "ticket.txt")},
                   content_type="multipart/form-data")
    d8 = r.get_json()
    check(r.status_code == 200, f"lesen {r.status_code}")
    check(d8.get("original", "").strip() == TEXT.strip(),
          "der gelesene Text stimmt nicht mit dem Original ueberein")
    check("maskiert" not in d8, "lesen hat trotzdem maskiert")
    check("woerterbuch" not in d8, "lesen liefert ein Woerterbuch")
    check("spans" not in d8, "lesen liefert Fundstellen")
    # Die Meldungen des Lesers gehen mit — sie aendern, was in Spalte 1 steht.
    check(any(h["werte"].get("kodierung") == "cp1252"
              for h in d8.get("hinweise", [])),
          f"Kodierung nicht gemeldet: {d8.get('hinweise')}")

    # Dieselben Wachen wie am Dateizweig von `/api/anonymisieren`. Sie duerfen
    # nicht schwaecher sein, sonst ist der neue Endpunkt der bequeme Weg
    # daran vorbei.
    p2 = Path(ordner) / "bild.png"
    p2.write_bytes(b"\x89PNG")
    with p2.open("rb") as fh:
        r = c.post("/api/lesen", data={"datei": (fh, "bild.png")},
                   content_type="multipart/form-data")
    check(r.status_code == 400, "unlesbares Format nicht abgewiesen")

    # ⚠️ Ein leerer Befund ist keine Entwarnung — auch hier nicht.
    p3 = Path(ordner) / "leer.txt"
    p3.write_text("   \n", encoding="utf-8")
    with p3.open("rb") as fh:
        r = c.post("/api/lesen", data={"datei": (fh, "leer.txt")},
                   content_type="multipart/form-data")
    check(r.status_code == 400, "leere Datei nicht abgewiesen")
    check("fehler" in r.get_json(), "leere Datei ohne Begruendung abgewiesen")

r = c.post("/api/lesen", json={"text": "ohne Datei"})
check(r.status_code == 400, "ohne Datei nicht abgewiesen")

print("9. Eigene Regeln")
GUT = """
version: 1
regeln:
  - id: vertrag
    bezeichnung: Vertragsnummer
    platzhalter: Vertrag
    art: etikett
    etiketten: ["Vertrag Nr.", "Vertragsnummer"]
    wertform: ziffern_gruppiert
    min: 6
    max: 16
"""
r = c.put("/api/regeln", json={"yaml": GUT})
check(r.status_code == 200, f"gute Regeln abgelehnt: {r.get_json()}")
check(REGELN.is_file(), "Regeldatei nicht geschrieben")
r = c.get("/api/regeln")
d6 = r.get_json()
check(len(d6["regeln"]) == 1, f"eine Regel erwartet, {len(d6['regeln'])}")
check(d6["regeln"][0]["tag"] == "X_vertrag", "Regeltag falsch")
check(d6["warnung"], "Warnung zum Messergebnis fehlt")

r = c.post("/api/anonymisieren",
           json={"text": "Der Vertrag Nr. 12 345 678 ist erledigt."})
d7 = r.get_json()
check("[Vertrag_1]" in d7["maskiert"],
      f"eigene Regel greift nicht: {d7['maskiert']}")
r = c.post("/api/anonymisieren",
           json={"text": "Der Vertrag Nr. 12 345 678 ist erledigt.",
                 "regeln": False})
check("[Vertrag_1]" not in r.get_json()["maskiert"],
      "regeln=false wirkt nicht")

# Kaputte Regeln duerfen die guten nicht ueberschreiben.
vorher = REGELN.read_text(encoding="utf-8")
for schlecht, warum in [
    ("version: 1\nregeln:\n  - id: 'GROSS'\n    art: wortliste\n"
     "    woerter: [Seerose]\n", "Kennung in Grossbuchstaben"),
    ("version: 1\nregeln:\n  - id: kollision\n    platzhalter: FULLNAME\n"
     "    art: wortliste\n    woerter: [Seerose]\n", "Platzhalter des Packs"),
    ("dies: ist: kein: yaml\n", "kaputtes YAML"),
]:
    r = c.put("/api/regeln", json={"yaml": schlecht})
    check(r.status_code == 400, f"angenommen trotz {warum}")
check(REGELN.read_text(encoding="utf-8") == vorher,
      "abgelehnte Regeln haben die Datei ueberschrieben")

print("10. Kein /api/senden")
r = c.post("/api/senden", json={"prompt": "x"})
check(r.status_code == 404,
      "/api/senden existiert — solange die Anbieterfrage offen ist, darf es "
      "das nicht")

print("10b. Ein fremder Wirtsname kommt nicht durch")
# ⚠️⚠️ «Der Dienst hoert nur auf 127.0.0.1, also kann ihn niemand von
# aussen rufen» ist eine Aussage ueber die ADRESSE. Der Browser schickt
# aber einen NAMEN mit, und ein Angreifer laesst seinen eigenen auf
# 127.0.0.1 zeigen (DNS-Rebinding) — fuer den Browser derselbe Ursprung,
# also ohne CORS-Schranke und mit lesbarer Antwort. `GET /api/vorlagen`
# gaebe die Prompts des Anwenders heraus, `GET /api/regeln` die
# Regeldatei im Rohtext.
#
# ⚠️ Geprueft wird an `/api/zustand`, dem harmlosesten Endpunkt. Trifft
# die Wache SCHON DEN, sitzt sie vor allen — sie haengt an
# `before_request` und nicht an einer Liste von Endpunkten, die beim
# naechsten wieder unvollstaendig waere.
import os as _os2  # noqa: E402
from serve import erlaubte_wirte as _ew, wirt_von as _wv  # noqa: E402

_wirt_vorher = _os2.environ.get("MASCHERA_WIRT")
try:
    _os2.environ.pop("MASCHERA_WIRT", None)
    for _h in ("127.0.0.1:4141", "localhost:4141", "[::1]:4141"):
        check(c.get("/api/zustand", headers={"Host": _h}).status_code == 200,
              f"der eigene Rechner wird abgewiesen: {_h}")
    for _h in ("boese.example.com", "maschera.example.ch:443"):
        _r = c.get("/api/zustand", headers={"Host": _h})
        check(_r.status_code == 403,
              f"fremder Wirt {_h} bekommt {_r.status_code} statt 403")
        check(_r.get_json().get("fehler_schluessel") == "wirt_unbekannt",
              "die Absage traegt keinen Schluessel zum Uebersetzen")

    # Der Betriebsfall: hinter dem Proxy antwortet der Dienst unter SEINEM
    # Namen — und der eigene Rechner bleibt trotzdem drin, sonst schluege
    # der HEALTHCHECK des Abbilds fehl, der 127.0.0.1 ruft.
    _os2.environ["MASCHERA_WIRT"] = "maschera.example.ch"
    check(c.get("/api/zustand",
                headers={"Host": "maschera.example.ch"}).status_code == 200,
          "der eingetragene Wirt wird abgewiesen")
    check(c.get("/api/zustand",
                headers={"Host": "127.0.0.1:4141"}).status_code == 200,
          "127.0.0.1 faellt heraus, sobald MASCHERA_WIRT gesetzt ist — "
          "dann scheitert der HEALTHCHECK im Abbild")
    check(c.get("/api/zustand",
                headers={"Host": "boese.example.com"}).status_code == 403,
          "mit gesetztem MASCHERA_WIRT kommt jeder durch")

    # Und der Ausweg, ausdruecklich und nicht als Nebenwirkung.
    _os2.environ["MASCHERA_WIRT"] = "*"
    check(_ew() is None, "`*` schaltet die Pruefung nicht ab")
    check(c.get("/api/zustand",
                headers={"Host": "boese.example.com"}).status_code == 200,
          "`*` wirkt nicht")
finally:
    _os2.environ.pop("MASCHERA_WIRT", None)
    if _wirt_vorher is not None:
        _os2.environ["MASCHERA_WIRT"] = _wirt_vorher

# ⚠️ IPv6 steht im `Host:`-Kopf in Klammern. Ein blosses `rsplit(":", 1)`
# machte aus `[::1]:4141` ein `[::1` — die Wache haette den eigenen
# Rechner nicht mehr erkannt und sich selbst ausgesperrt.
check(_wv("[::1]:4141") == "::1", "IPv6 in Klammern falsch zerlegt")
check(_wv("127.0.0.1:4141") == "127.0.0.1", "Port nicht abgeschnitten")
check(_wv("X.Example.CH:8080") == "x.example.ch", "nicht kleingeschrieben")
print("   OK   eigener Rechner ja, fremder Name 403, MASCHERA_WIRT und `*`")

print("11. Klartext-Vorlieben lesen und schreiben")
# ⚠️ `/api/anonymisieren` liest die Vorlieben bei fehlendem `ohne` selbst
# aus; ohne diesen Endpunkt koennte die Oberflaeche sie anzeigen, aber
# nicht sichern.
import core.vorlieben as _v  # noqa: E402
_v.PFAD = Path(ORDNER.name) / "klartext.json"

r = c.get("/api/vorlieben")
check(r.status_code == 200, f"GET /api/vorlieben -> {r.status_code}")
d = r.get_json()
for feld in ("klartext", "bspd", "unbekannt", "pfad", "warnung"):
    check(feld in d, f"Feld `{feld}` fehlt")

r = c.put("/api/vorlieben", json={"klartext": ["DATE", "ORG"]})
check(r.status_code == 200, f"PUT -> {r.status_code}: {r.get_json()}")
check(r.get_json()["klartext"] == ["DATE", "ORG"], "nicht gespeichert")
check(c.get("/api/vorlieben").get_json()["klartext"] == ["DATE", "ORG"],
      "beim Lesen kommt etwas anderes zurueck als beim Schreiben")

# ⚠️ Ein Tippfehler muss ABGELEHNT werden, nicht ignoriert. Sonst meldet das
# Werkzeug eine Einstellung als gesetzt, die nichts bewirkt — und der
# Anwender glaubt, das Datum bleibe im Klartext.
r = c.put("/api/vorlieben", json={"klartext": ["DATUM"]})
check(r.status_code == 400, f"Tippfehler durchgelassen: {r.status_code}")
check(c.get("/api/vorlieben").get_json()["klartext"] == ["DATE", "ORG"],
      "abgelehnte Liste hat die bestehende ueberschrieben")

# ⚠️ Dieselbe Wache wie bei `ohne` in `/api/anonymisieren`. Waere sie hier
# schwaecher, liesse sie sich umgehen, indem man den Tag dauerhaft setzt
# statt ihn einmal mitzuschicken.
r = c.put("/api/vorlieben", json={"klartext": ["NATIONALITY"]})
check(r.status_code == 400, "bsPD ohne auch_bspd durchgelassen")
r = c.put("/api/vorlieben",
          json={"klartext": ["NATIONALITY"], "auch_bspd": True})
check(r.status_code == 200, f"bsPD mit auch_bspd -> {r.status_code}")
check(r.get_json()["bspd"] == ["NATIONALITY"], "bsPD nicht ausgewiesen")

r = c.put("/api/vorlieben", json={"klartext": "DATE"})
check(r.status_code == 400, "Zeichenkette statt Liste durchgelassen")
r = c.put("/api/vorlieben", json={})
check(r.status_code == 400, "fehlendes Feld durchgelassen")

c.put("/api/vorlieben", json={"klartext": []})
print("   OK   gelesen, geschrieben, beide Wachen greifen")

print("12. Vorlagen")
# ⚠️ Eigene Datei, damit der Test die Vorlagen des Anwenders nicht anfasst.
# `vorlieben` oben tut das nicht, und das ist ein offener Punkt — hier nicht
# noch einen dazulegen.
from core import vorlagen  # noqa: E402

vorlagen.PFAD = Path(ORDNER.name) / "vorlagen.json"

r = c.get("/api/vorlagen")
check(r.status_code == 200, f"vorlagen {r.status_code}")
d = r.get_json()
# ⚠️ Ein umgelenkter Pfad, der trotzdem am regulaeren Ort liest, ist eine
# Wache, die sich selbst aushebelt — die Pruefung saehe dann die echten
# Vorlagen des Anwenders.
check(d["vorlagen"] == [], "frische Ablage nicht leer")
check("Klartext" in d["warnung"],
      "keine Warnung — ein Prompt kann Personendaten enthalten")

gut = [{"name": "Danke, 4 Wochen", "text": "Antworte freundlich …"},
       {"name": "Zusammenfassen", "text": "Fasse den Sachverhalt zusammen."}]
r = c.put("/api/vorlagen", json={"vorlagen": gut})
check(r.status_code == 200, f"speichern {r.status_code}")
check(len(r.get_json()["vorlagen"]) == 2, "nicht beide gespeichert")
check(c.get("/api/vorlagen").get_json()["vorlagen"][0]["name"]
      == "Danke, 4 Wochen", "Reihenfolge nicht erhalten")

# ⚠️ Abgelehnte Listen duerfen die bestehende Datei nicht ueberschreiben —
# dieselbe Wache wie bei `PUT /api/regeln`. Sonst waere eine Vorlage weg,
# weil eine ANDERE fehlerhaft war.
for schlecht, was in [
        ([{"name": "", "text": "x"}], "leerer Name"),
        ([{"name": "A", "text": "  "}], "leerer Text"),
        ([{"name": "A", "text": "x"}, {"name": "a", "text": "y"}],
         "Name zweimal"),
        (["nur ein Text"], "kein Objekt"),
        ("keine Liste", "Zeichenkette statt Liste"),
        (None, "Feld fehlt"),
        ([{"name": "A", "text": "x" * 20_001}], "Text zu lang"),
        ([{"name": "N" * 81, "text": "x"}], "Name zu lang")]:
    r = c.put("/api/vorlagen", json={"vorlagen": schlecht})
    check(r.status_code == 400, f"{was} durchgelassen")
check(len(c.get("/api/vorlagen").get_json()["vorlagen"]) == 2,
      "eine abgelehnte Liste hat die bestehenden Vorlagen ueberschrieben")

c.put("/api/vorlagen", json={"vorlagen": []})
check(c.get("/api/vorlagen").get_json()["vorlagen"] == [], "Leeren ging nicht")
print("   OK   gelesen, geschrieben, 8 Faelle abgewiesen")

print("13. Einstellungen")
from core import einstellungen  # noqa: E402

einstellungen.PFAD = Path(ORDNER.name) / "einstellungen.json"

d = c.get("/api/einstellungen").get_json()
check(d["adresse"] == "127.0.0.1", "Vorgabeadresse fehlt")
check(d["port"] == 4141, f"Vorgabeport {d['port']}")
check(any(x["id"] == "claude" for x in d["dienste"]), "Claude fehlt")
# Die Vorgabe der Dienste: alphabetisch nach Name, Mistral dabei, gewaehlt bleibt
# Claude. Mistral fehlte bis 1.0.2 — die Oberflaeche kannte es, der Server nicht,
# und die Liste kommt vom Server.
_namen = [x["name"] for x in d["dienste"]]
check(_namen == sorted(_namen, key=str.lower),
      f"die Vorgabe der Dienste ist nicht alphabetisch: {_namen}")
check("Mistral" in _namen and any(x["url"] == "https://chat.mistral.ai/chat"
                                  for x in d["dienste"]),
      f"Mistral fehlt in der Vorgabe: {_namen}")
check(d.get("dienst") == "claude",
      f"gewaehlt ist nicht Claude, sondern {d.get('dienst')!r}")
check(d["schriftgroesse"] == 100 and d["schriftart"] == "werk",
      "Schriftvorgabe fehlt")

gut = {"adresse": "127.0.0.1", "port": "9000", "eigenes_fenster": False,
       "dienst": "eigen", "schriftgroesse": 125, "schriftart": "serif",
       "dienste": [{"id": "eigen", "name": "Eigene KI",
                    "url": "https://ki.example.ch"}]}
r = c.put("/api/einstellungen", json=gut)
check(r.status_code == 200, f"speichern {r.status_code}")
check(r.get_json()["port"] == 9000, "Port nicht als Zahl uebernommen")
check(c.get("/api/einstellungen").get_json()["eigenes_fenster"] is False,
      "Fensterschalter nicht gespeichert")

# ⚠️ Die Adresse landet in `window.open`. `javascript:` liefe dort im
# Zusammenhang der eigenen Seite — mit Zugriff auf Woerterbuch und
# Originaltext. Dass der Anwender sie selbst eingetippt hat, hilft nicht:
# er tippt sie ab, weil sie irgendwo stand.
for schlecht, was in [
        ({**gut, "dienste": [{"name": "X", "url": "javascript:alert(1)"}]},
         "javascript:-Adresse"),
        ({**gut, "dienste": [{"name": "X", "url": "file:///etc/passwd"}]},
         "file:-Adresse"),
        ({**gut, "dienste": [{"name": "", "url": "https://a.ch"}]},
         "Dienst ohne Namen"),
        ({**gut, "dienste": [{"id": "a", "name": "A", "url": "https://a.ch"},
                             {"id": "a", "name": "B", "url": "https://b.ch"}]},
         "Kennung zweimal"),
        ({**gut, "port": 0}, "Port 0"),
        ({**gut, "port": 70000}, "Port 70000"),
        ({**gut, "adresse": "  "}, "leere Adresse"),
        ({**gut, "eigenes_fenster": "ja"}, "Schalter als Text"),
        ({**gut, "schriftgroesse": 117}, "Schriftgroesse dazwischen"),
        ({**gut, "schriftart": "comic"}, "unbekannte Schriftart"),
        ("kein Objekt", "Zeichenkette statt Objekt")]:
    r = c.put("/api/einstellungen", json=schlecht)
    check(r.status_code == 400, f"{was} durchgelassen")
d = c.get("/api/einstellungen").get_json()
check(d["port"] == 9000,
      "eine abgelehnte Einstellung hat die bestehende ueberschrieben")
check(d["schriftgroesse"] == 125 and d["schriftart"] == "serif",
      "Schrifteinstellung nicht gespeichert")
check(d["dienst"] == "eigen", "gewaehlter Dienst nicht gespeichert")

# ⚠️ Wer den gewaehlten Dienst loescht, bekommt den ersten. Sonst zeigte der
# Sendeknopf einen Namen, zu dem keine Adresse mehr gehoert.
r = c.put("/api/einstellungen", json={**gut, "dienst": "weg",
                                      "dienste": [{"id": "a", "name": "A",
                                                   "url": "https://a.ch"}]})
check(r.get_json()["dienst"] == "a", "verwaister Dienst nicht ersetzt")
print("   OK   gelesen, geschrieben, 11 Faelle abgewiesen")

print("14. Die schnelle Zeilennummer sagt dasselbe wie die langsame")
# ⚠️ `serve.py` stellt die Zeilenumbrueche einmal auf und sucht mit
# `bisect`, statt je Spanne von vorne zu zaehlen — bei 124 000 Zeichen und
# tausenden Spannen waere das quadratisch.
#
# Sagt die schnelle Fassung eine andere Zahl, zeigt ein Befund auf die
# falsche Zeile — und der Anwender sucht an der falschen Stelle in seinem
# Dokument. Das faellt niemandem auf, deshalb steht es hier.
import bisect as _bi  # noqa: E402
import random as _rnd  # noqa: E402

from filter_document import _zeile as _zeile_langsam  # noqa: E402

_zf = _rnd.Random(20260830)
_text = "".join(_zf.choice("aaabb \n\n.,x") for _ in range(4000))
_um = [i for i, ch in enumerate(_text) if ch == "\n"]
_falsch = 0
for _ in range(1000):
    _pos = _zf.randrange(0, len(_text) + 1)
    if _bi.bisect_left(_um, _pos) + 1 != _zeile_langsam(_text, _pos):
        _falsch += 1
# Die Raender ausdruecklich mit: Anfang, Ende, und direkt auf einem Umbruch.
for _pos in [0, len(_text)] + [i for i in _um[:20]] + [i + 1 for i in _um[:20]]:
    if _bi.bisect_left(_um, _pos) + 1 != _zeile_langsam(_text, _pos):
        _falsch += 1
check(_falsch == 0, f"{_falsch} Abweichung(en) bei der Zeilennummer")
print("   OK   1040 Stellen, gleiche Zeile")

print("15. Der Fortschritt ist abfragbar, waehrend gerechnet wird")
r = c.get("/api/fortschritt")
check(r.status_code == 200, f"/api/fortschritt -> {r.status_code}")
d = r.get_json()
for feld in ("aktiv", "schritt", "von", "phase"):
    check(feld in d, f"/api/fortschritt ohne `{feld}`")
check(d["aktiv"] is False, "es laeuft nichts, und trotzdem meldet er `aktiv`")
# ⚠️ Er darf `z.sperre` NICHT nehmen. Sonst antwortet er erst, wenn es
# nichts mehr zu melden gibt — eine Anzeige, die nach dem Ende erscheint.
import inspect as _insp  # noqa: E402

import serve as _serve  # noqa: E402

_quelle = _insp.getsource(_serve.baue)
_fort = _quelle.split("/api/fortschritt")[1].split("@app.")[0]
# ⚠️ `with z.sperre`, nicht bloss `z.sperre`: der Text der Begruendung
# steht als Kommentar IN diesem Endpunkt und nennt sie beim Namen. Beim
# ersten Versuch schlug die Pruefung an ihrer eigenen Erklaerung an.
check("with z.sperre" not in _fort,
      "/api/fortschritt nimmt die Sperre — dann wartet er bis zum Schluss")
check("dauer_ms" in _insp.getsource(_serve._durchlauf),
      "die Antwort traegt die gemessene Dauer nicht mehr")
if not failures:
    print("   OK   vier Felder, ohne Sperre, Dauer in den Kennzahlen")

print("16. Das Modell wird im Konstruktor geladen")
# ⚠️ Mit Modell baut `Zustand.__init__` den `TorchScorer`. Rutscht dieser
# Block je hinter ein `return` oder in eine andere Methode, bleibt
# `z.scorer` None, und das Werkzeug laeuft OHNE MODELL — waehrend alle
# anderen Pruefungen gruen bleiben, weil sie `Zustand("ch")` aus Kosten-
# gruenden ohne Modell bauen.
#
# «Ohne Modell leckt jeder Name.» Diese Pruefung ist billig und deckt
# genau diesen Weg ab.
_quelle_init = _insp.getsource(_serve.Zustand.__init__)
for name in ("TorchScorer", "OnnxScorer", "Mitschreiber"):
    check(name in _quelle_init,
          f"`{name}` steht nicht mehr in Zustand.__init__ — laedt das "
          f"Modell noch jemand?")
check("return" not in _quelle_init,
      "in Zustand.__init__ steht ein `return` — dahinter wird nichts mehr "
      "geladen")
print("   OK   beide Laeufer werden im Konstruktor gebaut")

print("17. Die Schriftgroessen haben vier Verwalter, die sich einig sind")
# Die Liste steht an VIER Stellen — in `core/einstellungen.py`, in
# `maschera.js`, im Auswahlfeld von `index.html` und im Vertrag.
#
# Fehlt eine, hat der Anwender die Wahl im Feld und bekommt vom Server
# eine 400 zurueck. Oder umgekehrt: der Server nimmt einen Wert an, den
# niemand auswaehlen kann. Beides faellt erst dem auf, der es probiert.
#
# Dasselbe Muster wie der Vorgabeport, der einmal an NEUN Stellen stand.
import re as _re  # noqa: E402

_html = (WURZEL / "app" / "static" / "index.html").read_text(encoding="utf-8")
_js = (WURZEL / "app" / "static" / "maschera.js").read_text(encoding="utf-8")
_vertrag = (WURZEL / "docs" / "API_OBERFLAECHE.md").read_text(encoding="utf-8")

from core.einstellungen import GROESSEN as _QUELLE  # noqa: E402

_feld = _re.search(r'<select id="einst-schriftgroesse">(.*?)</select>',
                   _html, _re.S)
check(_feld is not None, "kein Auswahlfeld fuer die Schriftgroesse im HTML")
_im_feld = tuple(int(x) for x in _re.findall(r'value="(\d+)"', _feld.group(1))) \
    if _feld else ()
_m_js = _re.search(r"const GROESSEN = \[([^\]]*)\]", _js)
check(_m_js is not None, "keine GROESSEN in maschera.js")
_im_js = tuple(int(x) for x in _re.findall(r"\d+", _m_js.group(1))) \
    if _m_js else ()
_m_v = _re.search(r'"schriftgroesse": \d+,\s*//([^\n]*)', _vertrag)
_im_vertrag = tuple(int(x) for x in _re.findall(r"\d+", _m_v.group(1))) \
    if _m_v else ()

check(_im_feld == tuple(_QUELLE),
      f"das Auswahlfeld bietet {_im_feld}, der Server nimmt {tuple(_QUELLE)}")
check(_im_js == tuple(_QUELLE),
      f"maschera.js kennt {_im_js}, der Server nimmt {tuple(_QUELLE)}")
check(_im_vertrag == tuple(_QUELLE),
      f"API_OBERFLAECHE.md nennt {_im_vertrag}, der Server nimmt "
      f"{tuple(_QUELLE)}")

# ⚠️ DIESELBE KLAMMER FUER DIE VIER SPRACHEN.
#
# Die Liste der Bediensprachen hat VIER Verwalter: `core/einstellungen.py`,
# die Flaggenknoepfe in `index.html`, die Saetze des Startbildschirms in
# `app/fenster.py` und der Vertrag. Fehlt einer eine Sprache, bietet die
# Oberflaeche einen Knopf an, den der Server ablehnt — und keine andere
# Pruefung merkt es.
from core.einstellungen import SPRACHEN as _SPR  # noqa: E402
import fenster as _fenster_spr  # noqa: E402

_im_html = tuple(_re.findall(r'data-sprache="([a-z]{2})"', _html))
check(_im_html == tuple(_SPR),
      f"die Flaggenknoepfe bieten {_im_html}, der Server nimmt {tuple(_SPR)}")
check(tuple(_fenster_spr.START_SAETZE) == tuple(_SPR),
      f"der Startbildschirm kennt {tuple(_fenster_spr.START_SAETZE)}, "
      f"der Server nimmt {tuple(_SPR)}")
_m_vspr = _re.search(r'"sprache": "de",\s*//([^\n]*)', _vertrag)
_im_vspr = tuple(_re.findall(r"[a-z]{2}", _m_vspr.group(1))) \
    if _m_vspr else ()
check(_im_vspr == tuple(_SPR),
      f"API_OBERFLAECHE.md nennt {_im_vspr}, der Server nimmt {tuple(_SPR)}")

# Und der Weg hin und zurueck.
r = c.put("/api/einstellungen", json={**gut, "sprache": "it"})
check(r.status_code == 200, f"PUT sprache=it -> {r.status_code}")
check(c.get("/api/einstellungen").get_json()["sprache"] == "it",
      "die Sprache kommt anders zurueck, als sie geschrieben wurde")
r = c.put("/api/einstellungen", json={**gut, "sprache": "xx"})
check(r.status_code == 400, f"unbekannte Sprache durchgelassen: {r.status_code}")
check(r.get_json().get("fehler_schluessel") == "oberflaechensprache_unbekannt",
      "die Ablehnung traegt den falschen Schluessel: "
      f"{r.get_json().get('fehler_schluessel')!r}")
check(c.get("/api/einstellungen").get_json()["sprache"] == "it",
      "die abgelehnte Sprache hat die bestehende ueberschrieben")

# Und die Probe aufs Exempel: jede angebotene Groesse muss durchgehen.
for _g in _QUELLE:
    _r = c.put("/api/einstellungen", json={**gut, "schriftgroesse": _g})
    check(_r.status_code == 200,
          f"Schriftgroesse {_g} steht im Feld, der Server weist sie ab")
c.put("/api/einstellungen", json=gut)
if not failures:
    print(f"   OK   {len(_QUELLE)} Groessen, vier Verwalter einig, alle "
          f"angenommen")

# ---------------------------------------------------------------------------
import re  # noqa: E402
print("\n18. Jeder Hinweis-Schluessel steht in allen vier Sprachen")
# ⚠️ Ein Hinweis besteht aus zwei Haelften an zwei Orten: dem Schluessel im
# Server und den vier Saetzen in `maschera.js`. Wer nur die erste Haelfte
# schreibt, bekommt keinen Fehler — die Oberflaeche faellt still auf die
# deutsche Fassung zurueck, und unter einer italienischen Oberflaeche
# stehen deutsche Zeilen. Diese Pruefung macht das laut.

QUELLEN = [WURZEL / "app" / "serve.py", WURZEL / "tools" / "dokumente.py"]
benutzt = set()
for datei in QUELLEN:
    benutzt |= set(re.findall(r'hinweis\(\s*"([a-z_]+)"', datei.read_text()))
# Die Teilnamen aus `nicht_gelesen` reisen als Werte, nicht als Aufruf.
benutzt |= set(re.findall(r'"(t_[a-z]+)":',
                          (WURZEL / "tools" / "dokumente.py").read_text()))
check(len(benutzt) >= 15, f"zu wenige Schluessel gefunden: {sorted(benutzt)}")

js = (WURZEL / "app" / "static" / "maschera.js").read_text()
bloecke = re.findall(r"hinweise: \{(.*?)\n        \},", js, re.S)
check(len(bloecke) == 4, f"{len(bloecke)} Hinweistabellen statt vier")
for nr, block in enumerate(bloecke):
    da = set(re.findall(r"^\s+([a-z_]+):", block, re.M))
    fehlt = sorted(benutzt - da)
    check(not fehlt, f"Sprachtabelle {nr + 1} ohne: {fehlt}")
    zuviel = sorted(da - benutzt)
    check(not zuviel, f"Sprachtabelle {nr + 1} hat unbenutzte: {zuviel}")
if not failures:
    print(f"   OK   {len(benutzt)} Schluessel, vier Tabellen, keine Luecke")


print("\n19. Jeder Meldungs-Schluessel steht in allen vier Sprachen")
# ⚠️ Dieselbe Pruefung wie 18, eine Etage tiefer: der Server schickt an
# drei Stellen Text an die Oberflaeche — Hinweise, Fehler, Warnungen.
# Eine Pruefung, die nur ihren eigenen Fall kennt, meldet Ruhe ueber den
# Nachbarn.
#
# ⚠️ Gelesen wird die QUELLE, nicht der laufende Server. Ein Schluessel,
# der nur in einem selten getroffenen Zweig steht, wuerde von keinem
# Testaufruf erreicht — und genau der bliebe dann unuebersetzt.

MELDEQUELLEN = [WURZEL / "app" / "serve.py",
                WURZEL / "core" / "vorlagen.py",
                WURZEL / "core" / "vorlieben.py",
                WURZEL / "core" / "einstellungen.py",
                # Seit 0.9.61 mit eigenen Schluesseln statt `{grund}`
                WURZEL / "core" / "user_rules.py",
                WURZEL / "tools" / "dokumente.py"]
gesetzt = set()
for datei in MELDEQUELLEN:
    roh = datei.read_text()
    # Eine Form, ueberall: `schluessel="..."` als Schluesselwort. Positionell
    # ginge auch und waere hier nicht auffindbar — deshalb nehmen
    # `fehler`, `warnung` und `Abgelehnt` den Namen ausdruecklich entgegen.
    gesetzt |= set(re.findall(r'schluessel="([a-z_]+)"', roh))
    # Die eine Antwort, die einen Fehler mit Kennung 200 traegt: die
    # kaputte Regeldatei in `GET /api/regeln`. Sie baut das Feld von Hand,
    # weil sie den Rohtext trotzdem mitliefert.
    gesetzt |= set(re.findall(r'"fehler_schluessel": "([a-z_]+)"', roh))
check(len(gesetzt) >= 40, f"zu wenige Schluessel gefunden: {len(gesetzt)}")

bloecke = re.findall(r"meldungen: \{(.*?)\n        \},", js, re.S)
check(len(bloecke) == 4, f"{len(bloecke)} Meldungstabellen statt vier")
for nr, block in enumerate(bloecke):
    da = set(re.findall(r"^\s+([a-z_]+):", block, re.M))
    fehlt = sorted(gesetzt - da)
    check(not fehlt, f"Sprachtabelle {nr + 1} ohne: {fehlt}")
    zuviel = sorted(da - gesetzt)
    check(not zuviel, f"Sprachtabelle {nr + 1} hat unbenutzte: {zuviel}")

# ⚠️ Und die PLATZHALTER muessen mitwandern. Ein Satz, der `{grund}` im
# Deutschen einsetzt und im Italienischen nicht, verliert genau die
# Auskunft, um derentwillen die Meldung existiert — lautlos, weil ein
# fehlender Platzhalter kein Fehler ist, sondern nur eine kuerzere Zeile.
if len(bloecke) == 4:
    felder = []
    for block in bloecke:
        felder.append({k: set(re.findall(r"\{([a-z_]+)\}", v)) for k, v in
                       re.findall(r"^\s+([a-z_]+): (.*),$", block, re.M)})
    for nr in range(1, 4):
        for k, wollte in felder[0].items():
            hat = felder[nr].get(k, set())
            check(hat == wollte,
                  f"Sprachtabelle {nr + 1}, {k}: Platzhalter "
                  f"{sorted(hat)} statt {sorted(wollte)}")
# ⚠️ KEIN ROHTEXT ALS BEGRUENDUNG. Bis 0.9.61 setzte der Server `str(e)`
# als `{grund}` in einen uebersetzten Satz: deutsch aus der Regelpruefung,
# englisch aus PyMuPDF samt temporaerem Pfad, in der Sprache von Windows
# aus dem Betriebssystem. Uebersetzbar ist nur, was einen Schluessel hat.
for datei in MELDEQUELLEN:
    roh = datei.read_text()
    check("grund=str(" not in roh,
          f"{datei.name} setzt den Text einer Ausnahme als Wert ein")
    # Mit Text, nicht der Programmausgang `raise SystemExit(main())`.
    check(not re.search(r"raise SystemExit\(\s*f?[\"']", roh),
          f"{datei.name} bricht ohne Schluessel ab — `Abbruch` nehmen")
check("{grund}" not in js, "eine Meldung setzt noch `{grund}` ein")

# Und am laufenden Server: die Begruendung kommt als eigener Schluessel,
# ein Fremdtext gar nicht.
r = c.put("/api/regeln", json={"yaml": "rules:\n  - id: x1\n    type: wordlist\n    words: [AG]\n"})
d = r.get_json()
check(r.status_code == 400 and d.get("fehler_schluessel") == "regel_woerter_kurz"
      and d.get("fehler_werte", {}).get("kurz") == "AG",
      f"zu kurzes Wort nicht mit eigenem Schluessel: {d}")
r = c.put("/api/regeln", json={"yaml": "rules: [\n"})
d = r.get_json()
check(d.get("fehler_schluessel") == "regeln_kein_yaml"
      and isinstance(d.get("fehler_werte", {}).get("zeile"), int),
      f"kaputtes YAML ohne Zeile: {d}")
import io as _io  # noqa: E402
r = c.post("/api/lesen", data={"datei": (_io.BytesIO(b"kein pdf"), "x.pdf")},
           content_type="multipart/form-data")
d = r.get_json()
check(d.get("fehler_schluessel") == "datei_unlesbar"
      and not d.get("fehler_werte"),
      f"kaputtes PDF traegt Fremdtext in die Oberflaeche: {d}")
# ⚠️ Und auch NICHT in `fehler`. Bis 1.0.1 blieb dort der Text der Bibliothek
# samt temporaerem Pfad stehen («fuer die Kommandozeile und die API»); bei der
# Docker-Fassung im Netz verriet das Serverpfade an jeden Aufrufer (CodeQL
# `py/stack-trace-exposure`). Geprueft am echten Aufruf, mit dem Temp-Ordner
# als Suchwort.
import tempfile as _tf_api  # noqa: E402
check(_tf_api.gettempdir() not in str(d.get("fehler", "")),
      f"die Antwort nennt einen temporaeren Pfad: {d.get('fehler')}")
check(str(d.get("fehler", "")) == "Datei nicht lesbar",
      f"die Antwort traegt mehr als den eigenen Satz: {d.get('fehler')!r}")
r = c.post("/api/lesen", data={"datei": (_io.BytesIO(b"PK\x03\x04kaputt"), "x.docx")},
           content_type="multipart/form-data")
d = r.get_json()
check(d.get("fehler_schluessel") == "docx_kaputt",
      f"kaputtes DOCX ohne eigenen Schluessel: {d}")

if not failures:
    print(f"   OK   {len(gesetzt)} Schluessel, vier Tabellen, "
          "Platzhalter gleich, kein Rohtext")

# ---------------------------------------------------------------------------
print("\n20. Der Einstellungsdialog schickt JEDES Feld zurueck")
# ⚠️ `PUT /api/einstellungen` prueft das GANZE Objekt und setzt fuer jedes
# fehlende Feld die Vorgabe ein. Laesst `sichereEinstellungen()` in
# `maschera.js` ein Feld aus, setzt jedes Schliessen des Dialogs diese
# Einstellung still zurueck — «die Einstellung greift nicht, und nach dem
# Neustart ist sie wieder weg».
#
# Deshalb steht die Pruefung gegen `VORGABE` und nicht gegen einzelne
# Namen: so faengt sie den NAECHSTEN neuen Schluessel mit.
from core.einstellungen import VORGABE as _VORG  # noqa: E402

_m_s = _re.search(r"async function sichereEinstellungen\(\) \{(.*?)\n  \}\);",
                  _js, _re.S)
check(_m_s is not None, "sichereEinstellungen() in maschera.js nicht gefunden")
# ⚠️ NICHT nur zeilenanfangs. `port` steht mitten in einer Zeile —
# `...(portFeld() ? { port: portFeld() } : {})`, weil ein leeres Feld das
# Feld absichtlich weglaesst und den Server seine eigene Vorgabe setzen
# laesst. Kommentarzeilen fliegen vorher raus, sonst zaehlt ein «heisst:»
# im Satz als Feldname.
_rumpf_s = _re.sub(r"//[^\n]*", "", _m_s.group(1)) if _m_s else ""
_gesendet = set(_re.findall(r"\b([a-z_]+):", _rumpf_s))
_fehlt = set(_VORG) - _gesendet
check(not _fehlt,
      f"sichereEinstellungen() schickt {sorted(_fehlt)} nicht mit — "
      "der Server setzt das Feld beim Schliessen des Dialogs auf die Vorgabe")

# ⚠️ Ein Stand, der sich in JEDEM Feld von der Vorgabe unterscheidet.
# Die Gleichheit der Schluessel ist mitgeprueft: wer `VORGABE` erweitert,
# muss hier einen abweichenden Wert nachtragen, sonst bricht die Wache —
# und genau das ist der Zweck. Ein `dict`, das stillschweigend altert,
# waere der zwoelfte Verwalter dieses Projekts.
_abweichend = {"adresse": "127.0.0.2", "port": 9001, "eigenes_fenster": False,
               "dienst": "eigen", "schriftgroesse": 125, "schriftart": "serif",
               "schrift_ueberall": True, "sprache": "it", "tray": False,
               "fenstermodus": "voll", "thema": "dunkel",
               "dienste": [{"id": "eigen", "name": "Eigene KI",
                            "url": "https://ki.example.ch"}]}
check(set(_abweichend) == set(_VORG),
      f"die Probe kennt {sorted(set(_abweichend) ^ set(_VORG))} nicht wie "
      "die Vorgabe")
for _k in set(_abweichend) & set(_VORG):
    check(_abweichend[_k] != _VORG[_k],
          f"«{_k}» steht in der Probe auf dem Vorgabewert und beweist nichts")

check(c.put("/api/einstellungen", json=_abweichend).status_code == 200,
      "der abweichende Stand liess sich nicht schreiben")
# Und jetzt genau das, was der Dialog beim Schliessen schickt.
_nach = c.put("/api/einstellungen",
              json={_k: _abweichend[_k] for _k in _gesendet
                    if _k in _abweichend}).get_json()
for _k in _VORG:
    check(_nach.get(_k) == _abweichend[_k],
          f"«{_k}» hat das Schliessen des Einstellungsdialogs nicht "
          f"ueberlebt: {_nach.get(_k)!r} statt {_abweichend[_k]!r}")
if not failures:
    print(f"   OK   {len(_VORG)} Felder, keines faellt auf die Vorgabe")


print("21. Jede Wahlliste hat EINEN Verwalter")
# ⚠️⚠️ WAHLLISTEN MIT MEHREREN VERWALTERN. `THEMEN` und `SCHRIFTEN` stehen
# in `maschera.js`, in `core/einstellungen.py` und in `index.html`. Ein
# Wert, der an einer Stelle fehlt, ist ein Knopf ohne Wirkung oder eine
# Einstellung, die der Server ablehnt.
#
# Geprueft wird die BEZIEHUNG, nicht der Wert: keine abgeschriebene
# Aufzaehlung hier, sondern der Vergleich der Verwalter gegeneinander.
# Eine Wache, die eine Liste festnagelt, verbietet die richtige Aenderung
# mit.
from core import einstellungen as _E  # noqa: E402

# ⚠️ NACH DER SACHE FRAGEN, NICHT NACH DER BAUFORM. Gefragt wird: WELCHE
# WERTE bietet die Oberflaeche an dieser Kennung an — gleich ob als
# `value=` in Optionen oder als `data-thema=` an Knoepfen. Eine Suche nach
# `<select id="…">` wuerde rot, sobald aus der Auswahl eine Knopfreihe
# wird, ohne dass etwas kaputt ist.
def _angeboten(kennung: str) -> tuple:
    _i = _html.find('id="' + kennung + '"')
    if _i < 0:
        return ()
    _auf = _html.rfind("<", 0, _i)
    _tag = _html[_auf:_auf + 40].split()[0].lstrip("<")
    _zu = _html.find("</" + _tag + ">", _i)
    _block = _html[_i:_zu if _zu > 0 else _i + 900]
    return tuple(_re.findall(r'(?:value|data-thema)="([a-z]+)"', _block))

for _name, _select, _jsmuster in [
        ("THEMEN", "einst-thema", r"const THEMEN = \[([^\]]*)\]"),
        ("SCHRIFTEN", "einst-schriftart", r"const SCHRIFTEN = \{([^}]*)\}")]:
    _quelle = tuple(getattr(_E, _name))

    _im_html = _angeboten(_select)
    check(_im_html, f"die Oberflaeche bietet unter «{_select}» gar nichts an")
    check(set(_im_html) == set(_quelle),
          f"{_select} bietet {_im_html}, der Server nimmt {_quelle}")

    _m = _re.search(_jsmuster, _js, _re.S)
    check(_m is not None, f"kein {_name} in maschera.js")
    # ⚠️ Zwei Schreibweisen: `THEMEN` ist eine Liste aus Zeichenketten,
    # `SCHRIFTEN` ein Objekt — dort stehen die Namen als SCHLUESSEL, ohne
    # Anfuehrung. Beides einsammeln, sonst prueft die Wache bei einem der
    # zwei ins Leere und meldet dabei nichts.
    _im_js = tuple(_re.findall(r'"([a-z]+)"', _m.group(1))
                   or _re.findall(r'(?m)^\s*([a-z]+)\s*:', _m.group(1))) \
        if _m else ()
    check(set(_im_js) == set(_quelle),
          f"maschera.js kennt fuer {_name} {_im_js}, der Server nimmt "
          f"{_quelle}")

# ⚠️ `FENSTERMODI` hatte zwar eine Wache — sie nagelte aber den WERT fest
# (`== ("voll", "widget")`), statt die Verwalter zu vergleichen. Damit
# haette eine Umbenennung sie rot gemacht, eine Abweichung zwischen
# Server und Oberflaeche aber NICHT. Hier die Beziehung.
_modi = tuple(_E.FENSTERMODI)
for _m in _modi:
    check(f'"{_m}"' in _js,
          f"die Oberflaeche kennt den Fenstermodus «{_m}» nicht")

# ⚠️ Und die Gegenrichtung: `THEMEN` darf nicht in `app/serve.py` ein
# drittes Mal stehen. Der Endpunkt liest die Liste, er kopiert sie nicht.
_serve = (WURZEL / "app" / "serve.py").read_text(encoding="utf-8")
check('"automatisch"' not in _serve,
      "serve.py schreibt die Themenliste ein zweites Mal aus")
if not failures:
    print(f"   OK   {len(_E.THEMEN)}+{len(_E.SCHRIFTEN)}+{len(_modi)} "
          "Eintraege, je ein Verwalter")


print("21b. Die Hilfe hat in allen vier Sprachen denselben Bau")
# ⚠️⚠️ Die Zusage «es wird nichts nachgeladen» gilt fuer den BETRIEB — die
# schlanken Pakete holen das Modell einmal beim ersten Start. Der Satz
# steht in `seiten.js` VIERMAL, einmal je Sprache, ausgeschrieben.
#
# ⚠️ Das ist die gefaehrlichste Sorte Doppelfuehrung. Ein vergessener
# Schluessel faellt auf (Punkt 18 und 19 zaehlen sie); vergessene PROSA
# faellt niemandem auf, weil in der anderen Sprache ja etwas dasteht. Es
# stuende nur etwas Falsches da — ueber den Umgang mit Personendaten,
# gegenueber jemandem, der die deutsche Fassung nie zu Gesicht bekommt.
#
# ⚠️ Geprueft wird der BAU und nicht der Wortlaut. Gleich viele Absaetze
# und gleich viele Ueberschriften heisst: wer einen Absatz ergaenzt, hat
# ihn in allen vier ergaenzt oder faellt hier auf.
_roh = (WURZEL / "app" / "static" / "seiten.js").read_text(encoding="utf-8")
_bau = {}
for _spr in ("DE", "FR", "IT", "EN"):
    _start = _roh.find(f"const HILFE_{_spr} = [")
    check(_start != -1, f"HILFE_{_spr} fehlt in seiten.js")
    if _start == -1:
        continue
    _naechst = _roh.find("\nconst ", _start + 10)
    _teil = _roh[_start:_naechst if _naechst != -1 else len(_roh)]
    _bau[_spr] = (_teil.count('["p",') + _teil.count('["p", ['),
                  _teil.count('["h",'))
_werte = set(_bau.values())
check(len(_werte) <= 1,
      f"die vier Hilfetexte sind verschieden gebaut: {_bau} — "
      f"(Absaetze, Ueberschriften). Wer eine Sprache aendert, aendert "
      f"alle vier, sonst steht in dreien etwas Ueberholtes")
if not failures and _bau:
    _a, _u = next(iter(_werte))
    print(f"   OK   4 Sprachen, je {_a} Abs\u00e4tze und {_u} \u00dcberschriften")

print("21c. Die Anwendertexte duzen — in JEDER Sprache")
# ⚠️⚠️ DIE OBERFLAECHE DUZT, IN JEDER SPRACHE (Englisch kennt den
# Unterschied nicht).
#
# ⚠️ Warum das keine Geschmacksfrage ist: die erste Flaeche, die ein
# Anwender eines SCHLANKEN Pakets sieht, ist der Modell-Dialog. Siezt der
# und duzt die Hilfe zwei Klicks spaeter, liest sich das Werkzeug wie aus
# zwei Haenden. Bei einem, das um Vertrauen im Umgang mit Personendaten
# bittet, ist der Ton kein Beiwerk.
#
# ⚠️⚠️ DAS BEISPIELDOKUMENT IST AUSGENOMMEN. `BEISPIEL` in `maschera.js`
# ist ein GESCHAEFTSBRIEF — «Wir bitten um eine Rueckmeldung», «Nous vous
# prions», «Vi preghiamo». Ein Brief an eine Behoerde siezt, und zwar
# richtigerweise. Die Wache spricht ueber die Anrede des ANWENDERS durch
# das Werkzeug, nicht ueber den Inhalt eines Dokuments, das durch das
# Werkzeug laeuft.
import re as _r5                                                # noqa: E402

_ANREDE = {
    "de": _r5.compile(r"\b(Sie|Ihnen|Ihre[nmrs]?|Ihr)\b"),
    "fr": _r5.compile(r"\b(vous|votre|vos)\b", _r5.I),
    "it": _r5.compile(r"\b(Lei|Suo|Sua|Vostro)\b"),
    # Die Mehrzahl-Hoeflichkeit: bis 1.0.0 stand im Impressum der App
    # durchgehend «i vostri documenti … spetta a voi», unbemerkt.
    "it-voi": _r5.compile(r"\b(voi|vostr[aeio])\b", _r5.I),
}


def _ohne_beispiel(text: str) -> str:
    """Den Beispielbrief herausschneiden. Er darf siezen — er ist einer."""
    i = text.find("const BEISPIEL = {")
    if i == -1:
        return text
    j = text.find("\nconst ", i + 10)
    return text[:i] + text[j if j != -1 else len(text):]


# ⚠️⚠️ IN `fenster.py` NUR `START_SAETZE`. Dort steht der gesamte deutsche
# Anwendertext dieser Datei. Ein Docstring beginnt nicht mit `#` und
# kann «Sie» in einem anderen Sinn tragen («Sie gilt ueber den Start
# hinaus» — gemeint ist die Sprachwahl); eine Wache ueber die ganze
# Datei schluege dort an. Die `print()`-Meldungen daneben gehen ins
# Terminal, nicht in die Oberflaeche.
def _nur_saetze(text: str) -> str:
    i = text.find("START_SAETZE = {")
    if i == -1:
        return ""
    j = text.find("\n\n\ndef ", i)
    return text[i:j if j != -1 else len(text)]


_gesiezt = []
for _d in ("app/static/maschera.js", "app/static/seiten.js",
           "app/static/index.html", "app/fenster.py"):
    _roh = (WURZEL / _d).read_text(encoding="utf-8")
    _roh = _nur_saetze(_roh) if _d.endswith(".py") else _ohne_beispiel(_roh)
    _vorige = ""
    for _nr, _z in enumerate(_roh.splitlines(), 1):
        if _z.strip().startswith(("*", "//", "#", "/*")):
            continue
        # Eine FORTGESETZTE Zeichenkette (`+ "Ihnen. …`) beginnt keinen
        # Satz — ob dort einer beginnt, sagt das Ende der Zeile davor.
        # So stand bis 1.0.0 «liegt bei " + "Ihnen.» im Impressum und
        # wurde als Satzanfang uebersprungen.
        _fortsetzung = _r5.match(r"\s*\+\s*[\"']", _z) is not None
        _vorher_satzende = _vorige.rstrip().rstrip("\"' ").endswith(
            (".", ":", "!", "?"))
        _vorige = _z
        for _spr, _muster in _ANREDE.items():
            for _m in _muster.finditer(_z):
                _davor = _z[:_m.start()].rstrip()
                # ⚠️ Am Satzanfang kann «Sie» im Deutschen «sie» sein, und
                # `vous` steht nie dort ohne Verb. Nur das Wort MITTEN im
                # Satz ist eindeutig die Anrede.
                if _fortsetzung and _r5.fullmatch(r"\s*\+\s*[\"']", _davor):
                    if _vorher_satzende:
                        continue
                elif not _davor or _davor.endswith((".", ":", ">", '"',
                                                    "'", "|", "!", "?")):
                    continue
                _gesiezt.append(f"{_d}:{_nr} [{_spr}] {_m.group(0)!r}")
check(not _gesiezt,
      f"Anwendertext siezt: {'; '.join(_gesiezt[:6])} — entschieden ist "
      f"durchgehend duzen, und eine halb geduzte Oberflaeche liest sich "
      f"wie aus zwei Haenden")
if not failures:
    print(f"   OK   4 Dateien, {len(_ANREDE)} Sprachen mit Siezform, "
          f"keine gefunden (Beispielbrief ausgenommen)")

print("22. Die Hilfe nennt keine Formate, die der Server ablehnt")
# ⚠️⚠️ Die Formatliste steht in `tools/dokumente.py` (`ALLE`) — und ein
# zweites Mal in `app/static/seiten.js`, ausgeschrieben, in VIER Sprachen.
# Vier weitere Verwalter.
#
# ⚠️ Warum das kein Schoenheitsfehler ist: die Hilfe ist das, worauf sich
# der Anwender verlaesst, wenn ihm eine Datei abgewiesen wird — steht dort
# ein Format, das der Server nicht nimmt, sucht er den Fehler bei sich.
#
# ⚠️ Geprueft wird die BEZIEHUNG, nicht eine abgeschriebene Liste, und in
# BEIDE Richtungen. `.log`, `.text` und die endungslose Datei bleiben
# ungenannt — sie sind Aliasse desselben Textwegs, den `txt` schon
# vertritt. Deshalb verlangt die Wache nicht jede Endung, sondern JEDEN
# LESEWEG: ein Weg, den die Hilfe verschweigt, ist ein Weg, von dem
# niemand weiss.
import dokumente as _dok  # noqa: E402

_seiten_roh = (WURZEL / "app" / "static" / "seiten.js").read_text(
    encoding="utf-8")
_erlaubt = {e.lstrip(".") for e in _dok.ALLE if e}

# ⚠️ ERST DIE ZEICHENKETTEN ZUSAMMENSETZEN. Die Aufzaehlung ist im
# Quelltext ueber `"…" + "…"` umgebrochen, und die Umbruchstelle liegt in
# jeder Sprache woanders.
#
# ⚠️ Verlangt sind genau vier Fassungen, keine untere Schranke: eine Wache
# mit «3+ erwartet» uebersaehe genau den Fall, fuer den sie da ist — dass
# eine Sprache fehlt.
_seiten = _re.sub(r'"\s*\+\s*"', "", _seiten_roh)

_zeilen = _re.findall(r"txt, md, csv, json, ([a-z, ]+?)\.", _seiten)
check(len(_zeilen) == 4,
      f"{len(_zeilen)} Formatzeilen in seiten.js, genau vier erwartet — "
      "eine Sprache nennt andere Formate oder gar keine")

# ⚠️ Alles, was irgendwo in `seiten.js` wie eine Endungsaufzaehlung
# aussieht, gegen den Server halten.
_genannt = set()
for _m in _re.finditer(r"\b((?:txt|md|csv|json|eml|msg|mbox|pdf|docx|doc|"
                       r"rtf|odt|xlsx)(?:, ?[a-z0-9]+)*)\b", _seiten):
    for _e in _m.group(1).split(","):
        _genannt.add(_e.strip())
_zuviel = sorted(_genannt - _erlaubt)
check(not _zuviel,
      f"die Hilfe nennt {_zuviel} — der Server weist sie ab, und der "
      "Anwender sucht den Fehler bei sich")

# Und jeder Leseweg kommt vor. Ein Weg, den die Hilfe verschweigt, ist
# ein Weg, von dem niemand weiss.
for _weg, _vertreter in [("Text", {"txt", "md", "csv", "json"}),
                         ("Mail", {"eml", "msg", "mbox"}),
                         ("PDF", {"pdf"}),
                         ("DOCX", {"docx"})]:
    check(_vertreter & _genannt,
          f"die Hilfe verschweigt den Leseweg «{_weg}» ganz")

# ⚠️ Und die vier Sprachen nennen DIESELBEN Formate. Eine franzoesische
# Hilfe, die ein Format weniger kennt, ist derselbe Fehler wie eine
# deutsche Beschriftung unter italienischer Oberflaeche.
_pro_sprache = [set(z.replace(" ", "").split(",")) for z in _zeilen]
check(all(x == _pro_sprache[0] for x in _pro_sprache),
      f"die Sprachfassungen nennen verschiedene Formate: {_pro_sprache}")
if not failures:
    print(f"   OK   {len(_genannt)} Formate, {len(_zeilen)} Sprachen, "
          "vier Lesewege")


print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("OK — Endpunkte entsprechen API_OBERFLAECHE.md.")
