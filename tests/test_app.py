"""Auslieferung der Oberflaeche — C1.

    python3 tests/test_app.py

Laeuft OHNE Modell. Geprueft wird die **Verdrahtung**, nicht die Erkennung:
kommt die Seite an, sind die Endpunkte daneben noch erreichbar, und laedt die
Oberflaeche etwas von aussen nach.

⚠️ Die dritte Frage ist die wichtigste und die einzige, die man nicht sieht.
Ein Werkzeug, das damit wirbt, dass der Text das Geraet nicht verlaesst, darf
beim Oeffnen keine Verbindung nach aussen aufbauen. Schon der Abruf einer
Schrift verraet einer fremden Stelle, dass und wann jemand MASCHERA benutzt —
ohne dass ein Zeichen des Dokuments dabei uebertragen wuerde. Ein Entwurf
aus einem Gestaltungswerkzeug bringt typischerweise React ueber `unpkg.com`
und die Schriften ueber Google mit; diese Pruefung ist der Grund, warum
nichts davon in die Anwendung kommt.
"""
import re
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "app"))
sys.path.insert(0, str(WURZEL / "tools"))

failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


try:
    import flask  # noqa: F401
except ImportError:
    print("UEBERSPRUNGEN: Flask nicht installiert.")
    raise SystemExit(0)

from app import baue_mit_oberflaeche  # noqa: E402
from serve import Zustand  # noqa: E402

ORDNER = tempfile.TemporaryDirectory()
z = Zustand("ch", regeln_pfad=str(Path(ORDNER.name) / "regeln.yaml"))
app = baue_mit_oberflaeche(z)
c = app.test_client()
STATIC = WURZEL / "app" / "static"

print("1. Die Seite kommt an")
r = c.get("/")
check(r.status_code == 200, f"/ antwortet {r.status_code}")
check("text/html" in r.headers.get("Content-Type", ""),
      f"falscher Typ: {r.headers.get('Content-Type')!r}")
seite = r.get_data(as_text=True)
check("MAS" in seite and "CHE" in seite, "Titel fehlt")
print(f"   OK   {len(seite)} Zeichen HTML")

print("2. Umlaute kommen als UTF-8 an")
# ⚠️ Eine falsch deklarierte Kodierung faellt an einem «ü» auf und
# spaeter an einem Namen im Dokument — dann aber mitten in der Maskierung,
# wo sie Zeichenpositionen verschiebt.
#
# Geprueft wird die KODIERUNG, nicht die Wortwahl: eine Pruefung, die auf
# Textaenderungen reagiert statt auf Fehler, wird beim naechsten Mal
# weggeklickt statt gelesen.
check("charset=utf-8" in r.headers.get("Content-Type", "").lower(),
      "kein charset=utf-8 im Content-Type")
ausser_ascii = [c for c in seite if ord(c) > 0x7F]
check(bool(ausser_ascii), "keine Sonderzeichen in der Seite — nichts geprueft")
# «Ã» und «Â» sind die Signatur von UTF-8, das als Latin-1 gelesen wurde.
check("Ã" not in seite and "Â" not in seite,
      "Mojibake in der Seite — Kodierung stimmt nicht")
print(f"   OK   charset=utf-8, {len(set(ausser_ascii))} Sonderzeichen sauber")

print("3. Die Endpunkte sind daneben weiter erreichbar")
# Der Kern darf durch die Auslieferung nicht verdeckt werden. Eine
# `/<path:datei>`-Route, die zu frueh greift, faengt `/api/…` mit ab.
for weg in ("/api/zustand", "/api/tags", "/api/regeln"):
    a = c.get(weg)
    check(a.status_code == 200, f"{weg} antwortet {a.status_code}")
d = c.get("/api/zustand").get_json()
check(d["dienst"] == "maschera", "Dienstname fehlt")
check(d["ohne_modell"] is True, "ohne_modell nicht gemeldet")
print("   OK   /api/zustand, /api/tags, /api/regeln")

print("4. `/api/senden` bleibt 404, auch mit Oberflaeche")
# `/api/senden` wird es nicht geben. Solange das hier steht, kann niemand
# versehentlich dagegen bauen.
#
# ⚠️ Alle Methoden pruefen, nicht nur POST. Die Sammelroute `/<path:datei>`
# nimmt jeden Pfad an und ist auf GET beschraenkt — damit passte
# `POST /api/senden` auf eine Regel, aber nicht auf die Methode, und Flask
# antwortete **405 statt 404**. 405 heisst «es gibt ihn, nur nicht so»; das
# ist das Gegenteil der Aussage. `tests/test_api.py` prueft den nackten
# Kern und saehe das nicht.
for methode in ("POST", "GET", "PUT", "DELETE"):
    a = c.open("/api/senden", method=methode)
    check(a.status_code == 404,
          f"{methode} /api/senden antwortet {a.status_code} statt 404")
for methode in ("POST", "GET", "PUT"):
    a = c.open("/api/gibtesnicht", method=methode)
    check(a.status_code == 404,
          f"{methode} /api/gibtesnicht antwortet {a.status_code} statt 404")
print("   OK   404 fuer alle Methoden")

print("5. Unbekannte Datei gibt 404, kein Ausbruch aus dem Ordner")
check(c.get("/gibtesnicht.js").status_code == 404, "fehlende Datei nicht 404")
for weg in ("/../serve.py", "/..%2fserve.py", "/%2e%2e/serve.py"):
    a = c.get(weg)
    check(a.status_code != 200 or "Zustand" not in a.get_data(as_text=True),
          f"{weg} liefert eine Datei ausserhalb von static/")
print("   OK   404, kein Ausbruch")

print("6. Nichts wird von aussen nachgeladen")
# Der eigentliche Punkt dieser Pruefung. Geprueft wird JEDE ausgelieferte
# Datei, nicht nur index.html — sonst wandert der Verweis eine Datei weiter.
AUSSEN = re.compile(
    r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//"""      # <script src="//…">
    r"""|url\(\s*["']?\s*(?:https?:)?//"""               # CSS url(//…)
    r"""|@import\s+["']?\s*(?:https?:)?//"""             # CSS @import
    r"""|\bfetch\(\s*["'](?:https?:)?//""",              # fetch("https://…")
    re.I)
gepr = 0
ausnahmen = 0
for p in sorted(STATIC.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in {
            ".html", ".css", ".js", ".mjs", ".svg"}:
        continue
    gepr += 1
    text = p.read_text(encoding="utf-8", errors="replace")
    # Kommentare zaehlen nicht: `unpkg.com` darf als abschreckendes Beispiel
    # dastehen, solange nichts davon geladen wird.
    ohne_kommentar = re.sub(r"<!--.*?-->|/\*.*?\*/", "", text, flags=re.S)
    # ⚠️ Benannte Ausnahmen statt gelockerter Regel. Genau eine Stelle darf
    # eine fremde Adresse ansprechen: die Portpruefung in den Einstellungen.
    # Sie MUSS es, sonst prueft sie nichts — was hinausgeht, ist ein GET auf
    # `/api/zustand` an eine Adresse, die der Anwender selbst getippt hat.
    # Die Markierung steht im Kommentar davor; gezaehlt wird sie unten.
    markiert = len(re.findall(r"nach-aussen-erlaubt:", text))
    ausnahmen += markiert
    for m in AUSSEN.finditer(ohne_kommentar):
        zeile = ohne_kommentar[:m.start()].count("\n") + 1
        if markiert and "fetch(" in m.group(0):
            markiert -= 1
            continue
        check(False, f"{p.name}:{zeile} laedt von aussen: {m.group(0)!r}")
check(gepr > 0, "keine Oberflaechendateien gefunden")
# ⚠️ Die Zahl der Ausnahmen ist selbst eine Pruefung. Waechst sie, hat jemand
# eine zweite Stelle nach aussen gebaut und die Markierung mitkopiert —
# genau der Weg, auf dem eine absolute Regel weich wird.
check(ausnahmen <= 1,
      f"{ausnahmen} Stellen sind als «nach-aussen-erlaubt» markiert, "
      f"erlaubt ist genau eine (die Portpruefung)")
if not failures:
    print(f"   OK   {gepr} Datei(en), {ausnahmen} benannte Ausnahme")

print("7. Keine Kette im Browser")
# ⚠️ Keine Erkennung im Browser, auch nicht als Rueckfall: eine
# Maskierung im Browser waere eine Maskierung, die niemand gemessen hat.
# Die Namen unten sind die typischen Bausteine einer solchen Attrappe.
VERDACHT = ("function detect", "function anonymiseText", "const PATTERNS",
            "function fakeReply")
for p in sorted(STATIC.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in {".html", ".js", ".mjs"}:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for wort in VERDACHT:
        check(wort not in text,
              f"{p.name} enthaelt {wort!r} — die Attrappe des Entwurfs")
print("   OK   keine Erkennung im Browser")

print("8. `serve.py` laeuft weiter ohne Oberflaeche")
# Der Serverbetrieb braucht keine Oberflaeche, und `tests/test_api.py` prueft
# weiterhin den nackten Kern. Beide Wege muessen getrennt lauffaehig bleiben.
from serve import baue  # noqa: E402
nackt = baue(z).test_client()
check(nackt.get("/api/zustand").status_code == 200, "Kern antwortet nicht")
check(nackt.get("/").status_code == 404,
      "der nackte Kern liefert eine Oberflaeche aus")
print("   OK   getrennt lauffaehig")

print("9. Die Schriften werden ausgeliefert")
# ⚠️ Die `@font-face`-Regeln koennen stimmen und die Auslieferung trotzdem
# nicht: `send_from_directory` muss den Unterordner mitnehmen. Faellt das
# aus, laedt der Browser still eine Ersatzschrift — es sieht dann nur
# „irgendwie anders“ aus, und niemand sucht an der richtigen Stelle.
schriften = sorted((STATIC / "schriften").glob("*.woff2"))
check(len(schriften) > 0, "keine Schriftdateien gefunden")
for d in schriften[:3] + schriften[-1:]:
    a = c.get(f"/schriften/{d.name}")
    check(a.status_code == 200, f"/schriften/{d.name} -> {a.status_code}")
a = c.get("/maschera.css")
check(a.status_code == 200, f"/maschera.css -> {a.status_code}")
check("css" in a.headers.get("Content-Type", ""),
      f"falscher Typ fuer CSS: {a.headers.get('Content-Type')!r}")
print(f"   OK   maschera.css und {len(schriften)} Schriften erreichbar")

print("10. Die Oberflaechenlogik wird ausgeliefert")
a = c.get("/maschera.js")
check(a.status_code == 200, f"/maschera.js -> {a.status_code}")
js = a.get_data(as_text=True)
check("javascript" in a.headers.get("Content-Type", "").lower(),
      f"falscher Typ: {a.headers.get('Content-Type')!r}")
check("/api/anonymisieren" in js, "ruft /api/anonymisieren nicht auf")
# ⚠️ `innerHTML` mit Serverdaten waere der Weg, ueber den Dokumentinhalt zu
# ausfuehrbarem Markup wird. Der Text stammt aus einer Datei des Anwenders,
# also aus einer Quelle, die niemand kennt.
#
# Kommentare ausnehmen: sonst schlaegt die Pruefung an der Warnung an, die
# vor der Sache warnt.
js_code = re.sub(r"/\*.*?\*/|//[^\n]*", "", js, flags=re.S)
check("innerHTML" not in js_code, "maschera.js benutzt innerHTML")
check("outerHTML" not in js_code, "maschera.js benutzt outerHTML")
check("insertAdjacentHTML" not in js_code,
      "maschera.js benutzt insertAdjacentHTML")
print(f"   OK   {len(js)} Zeichen, kein innerHTML")

print("11. Maskieren laeuft ueber die Kette, nicht im Browser")
# Ohne Modell greifen nur Stufe 1 und 2 — das genuegt: die Verdrahtung wird
# geprueft, nicht die Erkennung. Eine AHV-Nummer hat eine Pruefsumme und
# faellt deshalb auch ohne Modell an.
probe = ("Versichertennummer 756.1234.5678.97, "
         "IBAN CH93 0076 2011 6238 5295 7, am 14.03.2026.")
a = c.post("/api/anonymisieren", json={"text": probe})
check(a.status_code == 200, f"/api/anonymisieren -> {a.status_code}")
d = a.get_json()
check("756.1234.5678.97" not in d["maskiert"], "AHV-Nummer nicht maskiert")
tags = {s["tag"] for s in d["spans"]}
check("AHVN13" in tags, f"AHVN13 fehlt, gefunden: {sorted(tags)}")
check("IBAN" in tags, f"IBAN fehlt, gefunden: {sorted(tags)}")
print(f"   OK   {len(d['spans'])} Fundstellen: {', '.join(sorted(tags))}")

print("12. Jeder Platzhalter passt auf das Muster der Oberflaeche")
# ⚠️ Dasselbe Muster steht in `maschera.js` und in `docs/API_OBERFLAECHE.md`.
# Faellt eines auseinander, faerbt die Oberflaeche einen Platzhalter nicht
# ein — und ein nicht eingefaerbter Platzhalter sieht aus wie gewoehnlicher
# Text, also wie etwas, das man stehen lassen kann.
PH = re.compile(r"\[[A-Za-z][A-Za-z0-9_]*_\d+[a-z]?\]")
gefunden = PH.findall(d["maskiert"])
check(len(gefunden) == len(d["spans"]),
      f"{len(gefunden)} Platzhalter im Text, {len(d['spans'])} Spannen")
for s in d["spans"]:
    if s.get("platzhalter"):
        check(bool(PH.fullmatch(s["platzhalter"])),
              f"Platzhalter passt nicht aufs Muster: {s['platzhalter']!r}")
check(PH.pattern in js.replace("\\\\", "\\") or
      "PH_RE" in js, "maschera.js kennt das Platzhaltermuster nicht")
print(f"   OK   {len(gefunden)} Platzhalter, alle erkennbar")

print("13. Woerterbuch und Kennzahlen kommen mit")
check(isinstance(d.get("woerterbuch"), dict), "kein Woerterbuch")
check(len(d["woerterbuch"]) > 0, "Woerterbuch leer")
for ph, wert in d["woerterbuch"].items():
    check(wert in probe, f"Woerterbucheintrag {ph} steht nicht im Original")
k = d.get("kennzahlen") or {}
check(k.get("zeichen") == len(probe),
      f"Zeichenzahl {k.get('zeichen')} statt {len(probe)}")
print(f"   OK   {len(d['woerterbuch'])} Eintraege, "
      f"{k.get('zeichen')} Zeichen")

print("14. Jede Kennung, die das JS anspricht, steht im HTML")
# ⚠️ `$("titel-orig")` auf ein Element, das es nicht mehr gibt, wirft eine
# Ausnahme mitten im Zeichnen — und dann bleibt die halbe Oberflaeche leer,
# ohne dass etwas im Serverprotokoll steht. Beim Umbau von C3 auf C3a sind
# genau so acht Kennungen umbenannt worden.
seite2 = c.get("/").get_data(as_text=True)
ids_html = set(re.findall(r'id="([A-Za-z0-9_-]+)"', seite2))
ids_js = set(re.findall(r'\$\("([A-Za-z0-9_-]+)"\)', js))
# Was `baueFuesse()` zur Laufzeit anlegt, steht nicht im HTML.
gebaut = set(re.findall(r'\.id = "([A-Za-z0-9_-]+)"', js))
fehlt = sorted(ids_js - ids_html - gebaut)
check(not fehlt, f"JS spricht an, HTML hat nicht: {fehlt}")
print(f"   OK   {len(ids_js)} Kennungen, alle vorhanden")

print("15. Logo und Startbildschirm werden ausgeliefert")
# ⚠️ EINE Quelle fuer vier Stellen: Kopfzeile, Startbildschirm, Favicon und
# AppImage-Symbol zeigen alle auf `maske.svg`; das AppImage-Symbol wird
# daraus gerendert. Wer das Zeichen wechselt, wechselt es einmal.
a = c.get("/maske.svg")
check(a.status_code == 200, f"/maske.svg -> {a.status_code}")
check(a.headers.get("Content-Type", "").startswith("image/svg"),
      "/maske.svg kommt nicht als SVG")
for stelle, muster in (("Favicon", r'rel="icon"\s+href="maske\.svg"'),
                       ("Startbildschirm", r'<img src="maske\.svg"')):
    check(re.search(muster, seite2), f"{stelle} zeigt nicht auf maske.svg")
# `css` wird erst in Punkt 20 geholt — hier eigens, damit die Reihenfolge
# der Punkte frei bleibt.
check('url("maske.svg")' in c.get("/maschera.css").get_data(as_text=True),
      "Kopfzeile zeigt nicht auf maske.svg")
# Die alten Bilder sind fort — kein zweites Zeichen, das still weiterlebt.
for tot in ("logo.jpg", "logo-gross.jpg"):
    check(not (STATIC / tot).exists(), f"{tot} liegt noch in app/static/")
check("startbild" in seite2, "kein Startbildschirm im HTML")
# ⚠️ Variante A: kein Prozentbalken. Solange das Modell laedt, antwortet
# nichts — eine Zahl waere erfunden, und zwar im Werkzeug, dessen Sinn es
# ist, keine falsche Sicherheit anzuzeigen.
check("splashPct" not in js and "%\"" not in js.split("startbild")[0][-400:],
      "es gibt wieder eine Prozentzahl beim Laden")
print("   OK   maske.svg an vier Stellen, Startbildschirm ohne Prozentzahl")

print("16. Die Oberflaeche sagt, wo die Grenze verlaeuft")
# Das gestalterische Herzstueck: 01, 02, 05 und Vokabular verlassen das
# Geraet nie, 03 und 04 schon.
#
# ⚠️ Die Grenze zeigt ein staendiger Hinweis NEBEN dem Sendeknopf, der den
# Dienst beim Namen nennt — nicht eine Plakette an den Titeln von 03 und
# 04: dort geht noch nichts hinaus, erst der Knopf schickt. Der Grundsatz
# bleibt derselbe: die Oberflaeche muss die Grenze zeigen.
check(seite2.count("plakette lokal") == 4,
      f"{seite2.count('plakette lokal')} LOKAL-Plaketten statt 4")
check(seite2.count("plakette online") == 0,
      f"{seite2.count('plakette online')} ONLINE-Plaketten — sie sind zum "
      f"Sendeknopf gewandert")
check("spalte hinaus" in seite2, "Spalte 3 ist nicht abgesetzt")
check('id="onlinewarnung"' in seite2,
      "kein staendiger ONLINE-Hinweis am Sendeknopf")
# ⚠️ Der Hinweis muss in ALLEN VIER Sprachen dastehen und den Dienst nennen.
# Ein Hinweis, den nur die deutsche Fassung hat, ist fuer drei Viertel der
# Oberflaeche keiner.
check(js.count("onlineWarnung:") == 4,
      f"{js.count('onlineWarnung:')} Sprachen mit ONLINE-Hinweis statt 4")
check(js.count('s.onlineWarnung.replace("{}"') == 1,
      "der Hinweis nennt den Dienst nicht oder an mehr als einer Stelle")
print("   OK   4x Lokal, Spalte 3 abgesetzt, ONLINE-Hinweis am Knopf in "
      "4 Sprachen")

print("17. Beim Schliessen wird vor Datenverlust gewarnt")
# ⚠️ Nichts wird auf die Festplatte geschrieben. Das Woerterbuch ist nach
# dem Schliessen unwiederbringlich weg — und ein maskierter Text ohne
# Woerterbuch laesst sich NIE mehr zurueckwandeln.
check("beforeunload" in js, "keine Warnung beim Schliessen")
check("verwerfenOk" in js, "keine Rueckfrage vor «Neu» und «Beispiel»")
print("   OK   beforeunload und Rueckfrage")

print("18. Einseitenanwendung: keine feste Hoehe im Raster")
# ⚠️ Keine feste Mindesthoehe. Sie erzwingt in einem echten Fenster Inhalt
# hoeher als der Bildschirm; der untere Teil waere abgeschnitten, und
# einen Rollbalken gibt es nicht, weil `body` auf `overflow: hidden` steht.
#
# Die Hoehe kommt vom Fenster. Gerollt wird NUR in den Textfeldern — nie die
# Seite, nie einer der sechs Kaesten.
css = c.get("/maschera.css").get_data(as_text=True)
raster = re.findall(
    r'(main\.raster[^{]*|\.spalte[^{]*|\.bereich\b[^{]*|\.rumpf\b[^{]*)\{'
    r'([^}]*)\}', css)
for wahl, regeln in raster:
    m = re.search(r'min-height:\s*(\d+)px', regeln)
    check(not m,
          f"{wahl.strip()} setzt min-height: {m.group(1) if m else ''}px — "
          f"das schiebt den Inhalt aus dem Fenster")
# Jede Stufe muss schrumpfen duerfen, sonst greift `min-height: auto` von
# Flex und Grid und die Spalte waechst mit ihrem Inhalt.
for wahl in ("main.raster", ".bereich", ".rumpf"):
    treffer = [r for w, r in raster if w.strip() == wahl]
    check(treffer and "min-height: 0" in treffer[0],
          f"{wahl} hat kein min-height: 0")
check("overflow-y: hidden" in css, "die Seite selbst darf nicht rollen")
print(f"   OK   {len(raster)} Regeln, keine feste Hoehe")

print("19. Nach aussen heisst es MASKIERUNG")
# ⚠️ MASCHERA stellt sich als «Lokale Maskierung für Schweizer Dokumente»
# vor.
#
# ⚠️ DIE UNTERSCHEIDUNG IST DER GANZE PUNKT und darf nicht verlorengehen:
# fachlich IST das Verfahren eine Pseudonymisierung — es ist ueber das
# Woerterbuch umkehrbar, und genau deshalb heisst der Knopf «Maskieren».
# Diese Aussage bleibt in SPEC.md, im Pack und im README stehen. Umgestellt
# ist die BESCHREIBUNG des Werkzeugs nach aussen. Deshalb prueft dieser
# Punkt nur die Stellen, an denen sich MASCHERA vorstellt — und nicht, dass
# das Wort nirgends vorkommt.
VORSTELLUNG = {
    "tools/paket/maschera.desktop": "Comment=",
}
for datei, anker in VORSTELLUNG.items():
    text = (WURZEL / datei).read_text(encoding="utf-8")
    zeilen = [z for z in text.splitlines() if anker in z]
    check(zeilen, f"{datei}: die Zeile mit {anker!r} fehlt")
    for z in zeilen:
        check("Maskierung" in z,
              f"{datei}: «Maskierung» fehlt in: {z.strip()[:70]}")
        check("seudonymisierung" not in z,
              f"{datei}: dort steht noch «Pseudonymisierung»")

# ⚠️ Die Kopie unter `dist/AppDir/` wird beim Bau ERZEUGT und ist deshalb
# kein zweiter Verwalter — sie darf aber nicht zurueckfallen, sobald sie da
# ist. Fehlt sie, ist nichts zu pruefen: der Bau lief noch nicht.
kopie = WURZEL / "dist" / "AppDir" / "maschera.desktop"
if kopie.exists():
    zeile = [z for z in kopie.read_text(encoding="utf-8").splitlines()
             if z.startswith("Comment=")]
    check(zeile and "Maskierung" in zeile[0],
          "dist/AppDir/maschera.desktop traegt noch das alte Wort — "
          "die AppImage ist aelter als die Quelle")

# ⚠️ DIE FASSUNG IM EINTRAG. AppImage-Verwalter wie Gearlever lesen sie aus
# `X-AppImage-Version=` im `.desktop`. Der Dateiname genuegt nicht —
# Gearlever kopiert die AppImage beim Einrichten und wirft den Namen weg.
#
# ⚠️ Zwei Wachen, weil sie Verschiedenes koennen: die erste laeuft immer
# und prueft das BAUSKRIPT, die zweite nur nach einem Bau und prueft die
# ZAHL. Ohne die erste waere der Punkt auf einer frischen Maschine still.
_bau = (WURZEL / "tools" / "paket" / "appimage_bauen.fish"
        ).read_text(encoding="utf-8")
check("X-AppImage-Version=$FASSUNG" in _bau,
      "appimage_bauen.fish schreibt keine `X-AppImage-Version` in den "
      "Eintrag — Gearlever zeigt dann keine Fassung an")
check('X-AppImage-Version=0' not in _bau
      and 'X-AppImage-Version="' not in _bau,
      "die Fassung steht im Bauskript als feste Zeichenkette statt aus "
      "`fassung.fish` — siehe test_fenster.py Punkt 7")

# ⚠️⚠️ DIE ZAHL WIRD HIER NICHT GEPRUEFT — sie wird im BAU geprueft.
#
# Ein altes `dist/AppDir/` aus einem frueheren Bau liegt auf einer
# Maschine, die nur zieht und nicht baut, genauso da wie auf einer, die
# alt gebaut hat. Die zwei Faelle sind am Dateisystem nicht zu
# unterscheiden, und eine Wache, die sie nicht trennen kann, meldet
# Fehlalarme.
#
# Deshalb prueft `appimage_bauen.fish` die geschriebene Zeile selbst,
# direkt nachdem es sie schreibt. Dort ist die Lage bekannt, die Pruefung
# exakt, und ein Fehler bricht den Bau ab.
#
# Was HIER bleibt, haengt an keiner Maschinenlage: das Bauskript muss die
# Zeile ueberhaupt schreiben, und zwar aus `fassung.fish`.
check("grep '^X-AppImage-Version=' $BAU/maschera.desktop" in _bau,
      "appimage_bauen.fish sieht die geschriebene Fassung nicht nach — "
      "ein Tippfehler faende erst der Anwender in Gearlever")

# ⚠️ DER STARTBILDSCHIRM, IN VIER SPRACHEN. Die Saetze kommen aus
# `START_SAETZE`; im Quelltext steht nur die Vorlage `__SATZ__`. Geprueft
# wird deshalb die GERENDERTE Seite, je Sprache. Das faengt zwei Dinge auf
# einmal: das Wort, und dass die Vorlage ueberhaupt gefuellt wird.
import fenster as _fenster  # noqa: E402

check(set(_fenster.START_SAETZE) == {"de", "fr", "it", "en"},
      "der Startbildschirm kennt nicht genau die vier Bediensprachen")

VORSTELLWORT = {"de": "Maskierung", "fr": "Masquage",
                "it": "Mascheratura", "en": "masking"}

# ⚠️⚠️ GLEICHE SCHLUESSEL STATT GLEICHER ANZAHL.
#
# Eine ZAHL findet den Fall nicht, um den es geht: wer einen Satz auf
# Franzoesisch ergaenzt und dafuer einen anderen umbenennt, hat weiter
# gleich viele — und eine Oberflaeche, die an einer Stelle leer bleibt.
# Gleiche SCHLUESSEL findet genau das.
#
# Dieselbe Bauart wie `test_api.py` Punkt 21b fuer die Hilfe.
_schluessel = {_s: set(_v) for _s, _v in _fenster.START_SAETZE.items()}
_erste = _schluessel["de"]
for _spr, _hat in sorted(_schluessel.items()):
    check(_hat == _erste,
          f"{_spr}: der Startbildschirm fuehrt andere Saetze als de — "
          f"fehlt {sorted(_erste - _hat)}, zuviel {sorted(_hat - _erste)}")

for _spr, _saetze in _fenster.START_SAETZE.items():
    check(VORSTELLWORT[_spr] in _saetze["unter"],
          f"{_spr}: der Startbildschirm nennt das Werkzeug nicht — "
          f"{_saetze['unter']!r}")
    for _satz in _saetze.values():
        check("seudonymisierung" not in _satz and "seudonimizzazione"
              not in _satz and "seudonymisation" not in _satz,
              f"{_spr}: dort steht noch «Pseudonymisierung»")

# ⚠️ Und die Vorlage muss wirklich ersetzt werden. Bliebe ein `__SATZ__`
# stehen, saehe der Anwender es als Erstes — und die Pruefung oben waere
# trotzdem gruen gewesen.
_seite = _fenster.startseite()
for _rest in ("__SATZ__", "__LADEN__", "__ERSTER__", "__FASSUNG__"):
    check(_rest not in _seite,
          f"der Startbildschirm liefert die Vorlage {_rest} unersetzt aus")
# ⚠️ IN DER SPRACHE, DIE `startseite()` WIRKLICH WAEHLT — nicht auf
# Deutsch. `startseite()` liest ueber `start_sprache()` die zuletzt
# gewaehlte Bediensprache. Eine Pruefung, die von der Konfiguration des
# Entwicklers abhaengt, sagt auf seiner Maschine etwas anderes als im
# Bau.
_spr_start = _fenster.start_sprache()
check(VORSTELLWORT[_spr_start] in _seite,
      f"der ausgelieferte Startbildschirm ({_spr_start}) nennt das "
      "Werkzeug nicht")
print("   OK   Tooltip und Startbildschirm sagen «Maskierung»")

print("\n6b. Das Onboarding traegt gueltiges Skript und alle vier Sprachen")
# ⚠️⚠️ Der Startbildschirm traegt ein Skript, das den Sprachschalter, die
# drei Schritte und den Fortschrittsbalken bedient. Ein `"\n"`, das beim
# Einbetten in den Python-String zu einem ECHTEN Zeilenumbruch wird,
# steht dann mitten in einem JS-Stringliteral.
#
# Ergebnis: `Uncaught SyntaxError`, das GANZE Skript tot, kein Schalter,
# keine Knoepfe — und die Seite sieht dabei voellig in Ordnung aus. Eine
# Oberflaeche, die dasteht und nichts tut, faellt nur dem Auge auf.
# Deshalb wird das eingebettete Skript hier geparst.
_seite_ob = _fenster.startseite("s_willkommen", {
    "fehlt": True, "name": "probe", "gb": "1,3",
    "quelle": "https://example.ch/x", "ziel": "/tmp/probe"})

for _rest in ("__SAETZE__", "__ORTE__", "__SPRACHE__", "__SCHRITT__"):
    check(_rest not in _seite_ob,
          f"das Onboarding liefert die Vorlage {_rest} unersetzt aus")

# Alle vier Sprachen muessen IN der Seite liegen — sonst kann der
# Schalter nicht ohne Neuladen wechseln, und genau das ist sein Zweck.
import json as _js_ob                                           # noqa: E402
_i = _seite_ob.index("const SAETZE = ") + len("const SAETZE = ")
_j = _seite_ob.index(";\n", _i)
try:
    _eingebettet = _js_ob.loads(_seite_ob[_i:_j])
except ValueError as _e:
    _eingebettet = {}
    check(False, f"die eingebetteten Saetze sind kein gueltiges JSON: {_e}")
check(set(_eingebettet) == {"de", "fr", "it", "en"},
      f"das Onboarding traegt {sorted(_eingebettet)} statt vier Sprachen — "
      f"dann faellt der Schalter auf eine leere Sprache")

# ⚠️ UND DAS SKRIPT MUSS PARSEN. Das ist die Pruefung, die den Fehler von
# heute gefunden haette.
import shutil as _sh_ob, subprocess as _sp_ob, tempfile as _tf_ob  # noqa: E402
_skript = _seite_ob[_seite_ob.index("<script>") + 8:
                    _seite_ob.index("</script>")]
if _sh_ob.which("node") is None:
    print("   --   node fehlt, das Skript ist NICHT auf Syntax geprueft")
else:
    with _tf_ob.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                   delete=False) as _fh:
        _fh.write(_skript)
        _weg = _fh.name
    _r_ob = _sp_ob.run(["node", "--check", _weg],
                       capture_output=True, text=True)
    check(_r_ob.returncode == 0,
          f"das Skript des Onboardings parst nicht: "
          f"{_r_ob.stderr.strip().splitlines()[:3]}")
    Path(_weg).unlink(missing_ok=True)
if not failures:
    print(f"   OK   4 Sprachen eingebettet, {len(_skript)} Zeichen Skript "
          f"syntaktisch geprueft")

print("20. Das Browsersymbol ist erzeugt, nicht gemalt")
# Nicht jeder Browser zeigt ein SVG-Symbol; das `favicon.ico` daneben
# baut `tools/favicon_bauen.fish` aus derselben Maske wie Kopfzeile,
# Startbildschirm und AppImage-Symbol.
#
# ⚠️ DIESELBE WACHE WIE BEI `dist/`: ein Generator baut nicht rueckwirkend.
# Ist die Maske neuer als das Symbol, laeuft die Auslieferung mit einem
# alten Bild.
ico = WURZEL / "app" / "static" / "favicon.ico"
svg = WURZEL / "app" / "static" / "maske.svg"


# ⚠️ NICHT DIE DATEIZEIT ALLEIN. Ein frischer Klon schreibt beide Dateien
# im selben Augenblick, in beliebiger Reihenfolge — die Dateizeit sagt
# dann nichts. Deshalb: ist die Datei gegenueber HEAD unveraendert, zaehlt
# ihr letzter Commit. Nur eine geaenderte Datei faellt auf die Dateizeit
# zurueck. Eine von Hand geaenderte Maske schlaegt damit weiter an, ein
# Klon nicht.
#
# Ohne Git — etwa in einem entpackten Archiv — gibt es nichts, woran sich
# die Reihenfolge ablesen liesse. Dann entfaellt der Vergleich und sagt es.
def _in_git() -> bool:
    try:
        r = _sp_ob.run(["git", "-C", str(WURZEL), "rev-parse",
                        "--is-inside-work-tree"],
                       capture_output=True, text=True)
    except FileNotFoundError:
        return False
    return r.returncode == 0 and r.stdout.strip() == "true"

def _stand(pfad: Path) -> float:
    def git(*args):
        return _sp_ob.run(["git", "-C", str(WURZEL), *args],
                          capture_output=True, text=True)
    try:
        geaendert = git("status", "--porcelain", "--", str(pfad))
        commit = git("log", "-1", "--format=%ct", "--", str(pfad))
    except FileNotFoundError:
        return pfad.stat().st_mtime
    if (geaendert.returncode == 0 and not geaendert.stdout.strip()
            and commit.returncode == 0 and commit.stdout.strip()):
        return float(commit.stdout.strip())
    return pfad.stat().st_mtime


def _ohne_kommentare(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _zeichnung_stand(pfad: Path) -> float:
    """Zeit der letzten Aenderung an der Zeichnung selbst, ohne Kommentare."""
    rel = str(pfad.relative_to(WURZEL))

    def git(*args):
        return _sp_ob.run(["git", "-C", str(WURZEL), *args],
                          capture_output=True, text=True)
    try:
        kopf = git("show", f"HEAD:{rel}")
        verlauf = git("log", "--format=%H %ct", "--", rel)
    except FileNotFoundError:
        return pfad.stat().st_mtime
    if kopf.returncode != 0 or verlauf.returncode != 0:
        return pfad.stat().st_mtime
    jetzt = _ohne_kommentare(pfad.read_text(encoding="utf-8"))
    if jetzt != _ohne_kommentare(kopf.stdout):
        return pfad.stat().st_mtime
    eintraege = [z.split() for z in verlauf.stdout.split("\n") if z.strip()]
    for (h, zeit), naechster in zip(eintraege, eintraege[1:] + [None]):
        if naechster is None:
            return float(zeit)
        davor = git("show", f"{naechster[0]}:{rel}")
        diese = git("show", f"{h}:{rel}")
        if _ohne_kommentare(diese.stdout) != _ohne_kommentare(davor.stdout):
            return float(zeit)
    return pfad.stat().st_mtime


check(ico.exists(), "app/static/favicon.ico fehlt — "
                    "`fish tools/favicon_bauen.fish`")
if ico.exists():
    # Gefragt ist, wann sich die ZEICHNUNG der Maske zuletzt geaendert hat,
    # nicht die Datei: ein neuer Kommentar in `maske.svg` aendert das
    # Symbol nicht, und ein neu gebautes Symbol waere bytegleich — Git
    # nimmt es dann in keinen Commit auf.
    if _in_git():
        check(_stand(ico) >= _zeichnung_stand(svg),
              "favicon.ico ist aelter als maske.svg — neu bauen mit "
              "`fish tools/favicon_bauen.fish`")
    else:
        print("   HINWEIS kein Git — ob favicon.ico juenger ist als die "
              "Maske, bleibt ungeprueft")
    # Ein `.ico` faengt mit 00 00 01 00 an, danach die Zahl der Bilder.
    kopf = ico.read_bytes()[:6]
    check(kopf[:4] == b"\x00\x00\x01\x00", "favicon.ico ist kein ICO")
    anzahl = int.from_bytes(kopf[4:6], "little")
    check(anzahl >= 4, f"nur {anzahl} Kantenlaenge(n) — fuer die "
                       f"Schreibtischverknuepfung braucht es die grossen")
# Beide Verweise stehen im HTML, das SVG zuerst.
html = (WURZEL / "app" / "static" / "index.html").read_text(encoding="utf-8")
check('<link rel="icon" href="maske.svg">' in html, "der SVG-Verweis fehlt")
check('href="favicon.ico"' in html, "der ICO-Verweis fehlt")
check(html.index("maske.svg") < html.index("favicon.ico"),
      "das ICO steht vor dem SVG — dann nimmt es auch ein Browser, "
      "der das SVG koennte")
# Und es wird wirklich ausgeliefert.
check(c.get("/favicon.ico").status_code == 200, "/favicon.ico kommt nicht")
check(c.get("/adressen.json").status_code == 200, "/adressen.json kommt nicht")
print("   OK   ICO aus der Maske, beide Verweise, beide ausgeliefert")

print("\n21. Jede Antwort traegt die Sicherheitskopfzeilen")
# ⚠️⚠️ DIE ZWEITE VERTEIDIGUNGSLINIE. Die erste ist der Code — kein
# `innerHTML`, kein `eval`, kein Inline-Skript, bewacht in
# `test_oberflaeche.js`. Die Policy sorgt dafuer, dass selbst ein
# eingeschleuster Code den Klartext nicht per `fetch` nach aussen tragen
# kann. Diese Pruefung haelt fest, dass sie da ist, streng bleibt — und
# dass das HTML nichts enthaelt, was sie still lahmlegen wuerde.
#
# ⚠️ Auf JEDER Antwort, auch auf einem 404. Eine Liste der Antworten, die
# sie tragen, waere beim naechsten Endpunkt wieder unvollstaendig.
import re as _re21  # noqa: E402
for _pfad in ("/", "/maschera.js", "/maschera.css", "/api/zustand",
              "/gibt-es-nicht.txt"):
    _a = c.get(_pfad)
    check(_a.headers.get("Content-Security-Policy"),
          f"{_pfad}: keine Content-Security-Policy")
    check(_a.headers.get("X-Content-Type-Options") == "nosniff",
          f"{_pfad}: `X-Content-Type-Options: nosniff` fehlt")

_csp = c.get("/").headers.get("Content-Security-Policy", "")
_teile = {s.split()[0]: s.split()[1:]
          for s in (x.strip() for x in _csp.split(";")) if s}
check("'unsafe-inline'" not in _csp and "'unsafe-eval'" not in _csp,
      "die Policy erlaubt Inline-Code oder eval — dann schuetzt sie nichts")
check(_teile.get("script-src") == ["'self'"],
      f"script-src ist {_teile.get('script-src')}, erwartet nur 'self'")
check(_teile.get("object-src") == ["'none'"], "object-src ist nicht 'none'")
check(_teile.get("frame-ancestors") == ["'none'"],
      "frame-ancestors ist nicht 'none' — die Seite liesse sich einbetten")

# ⚠️ `connect-src`: der eigene Ursprung und LOOPBACK, sonst nichts. Das ist
# genau der Unterschied, um den es geht — alles, was die Maschine
# verlaesst, bleibt gesperrt. Und die Portpruefung auf 127.0.0.1 bleibt
# erreichbar, sonst prueft sie nichts.
_nach = _teile.get("connect-src", [])
check("'self'" in _nach, "connect-src erlaubt den eigenen Dienst nicht")
_fremd = [q for q in _nach if q != "'self'" and not _re21.fullmatch(
    r"http://(127\.0\.0\.1|localhost)(:\*|:\d+)?", q)]
check(not _fremd, f"connect-src erlaubt Ziele ausserhalb der Maschine: {_fremd}")
check(any(q.startswith("http://127.0.0.1") for q in _nach),
      "die Portpruefung auf 127.0.0.1 waere gesperrt")

# ⚠️ Und das HTML traegt nichts, was die Policy STILL sperrt. Ein
# Inline-Stil steht danach einfach ohne Wirkung da.
_html = (WURZEL / "app" / "static" / "index.html").read_text(encoding="utf-8")
check(not _re21.search(r'\sstyle="', _html),
      "Inline-Stil im HTML — `style-src 'self'` sperrt ihn still")
check("<style" not in _html.lower(), "ein <style>-Block im HTML")
check(not _re21.search(r"<script(?![^>]*\bsrc=)[^>]*>", _html, _re21.I),
      "ein Inline-Skript im HTML")
check(not _re21.search(r"\son[a-z]+\s*=", _html, _re21.I),
      "ein on…=-Attribut im HTML")
# ⚠️ UND KEIN CSS-SELEKTOR AUF `[style]`. Mit der Policy ist `[style]`
# grundsaetzlich zerbrechlich: im HTML darf es nicht stehen, und
# JavaScript erzeugt es beim Setzen von `.style` von selbst. Eine Regel,
# die daran haengt, aendert still ihre Wirkung.
_css21 = _re21.sub(r"/\*.*?\*/", "", (WURZEL / "app" / "static" /
                   "maschera.css").read_text(encoding="utf-8"), flags=_re21.S)
check("[style" not in _css21,
      "ein CSS-Selektor haengt am `style`-Attribut — seit der Policy eine "
      "Markierung, die still verschwinden kann")
if not failures:
    print("   OK   Policy und nosniff auf fuenf Antworten, connect-src nur "
          "Loopback, nichts Inline im HTML")

print("\n22. Knoepfe, Kaesten und Fenster tragen EINE Rundung")
# Eine Oberflaeche mit eckigen und verschieden runden Knoepfen sieht
# zusammengewuerfelt aus. Die Rundung steht einmal als Marke
# (`--radius-md`); jede Regel benutzt sie. Erlaubt sind daneben nur
# Formen, die keine Ecke haben sollen: Pillen und Punkte (999px, 50%)
# und `0` — gerade Kanten wie die Naht des geteilten Sendeknopfs.
# Geprueft wird der WERT jeder `border-radius`-Angabe, nicht eine Liste
# von Selektoren: der naechste neue Knopf faellt so von selbst darunter.
import re as _re22
_css22 = _re22.sub(r"/\*.*?\*/", "", (WURZEL / "app" / "static" /
                   "maschera.css").read_text(encoding="utf-8"), flags=_re22.S)
_erlaubt22 = {"var(--radius-md)", "999px", "50%", "0"}
_marke22 = _re22.search(r"--radius-md:\s*([^;]+);", _css22)
check(_marke22 and _marke22.group(1).strip() == "4px",
      "`--radius-md` ist nicht 4px — die Rundung der Feldknoepfe")
for _m in _re22.finditer(r"border(?:-[a-z]+)?-radius:\s*([^;]+);", _css22):
    for _teil in _m.group(1).split():
        check(_teil in _erlaubt22,
              f"`{_m.group(0)}` — eine eigene Rundung neben `--radius-md`")
if not failures:
    print("   OK   jede Rundung ist `--radius-md`, eine Pille oder gerade")

print()
if failures:
    print(f"{len(failures)} Pruefung(en) fehlgeschlagen.")
    raise SystemExit(1)
print("Oberflaechenauslieferung in Ordnung.")
