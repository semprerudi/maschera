<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Testkatalog

Jede Prüfung mit ihren Punkten. Die Kennung `T-<DATEI>-<PUNKT>` ist stabil, solange der Punkt seine Nummer behält. Unter jedem Punkt steht, woran er anschlägt (die Fehlermeldung der Prüfung; `…` ist ein Wert, der erst zur Laufzeit feststeht).

| Prüfung | Punkte | Meldungen |
|---|---:|---:|
| `tests/test_alignment.py` | 9 | 21 |
| `tests/test_api.py` | 36 | 216 |
| `tests/test_app.py` | 24 | 112 |
| `tests/test_befunde.py` | 7 | 8 |
| `tests/test_ch_checksums.py` | 4 | 10 |
| `tests/test_dist_frisch.py` | 4 | 4 |
| `tests/test_dokumente_docx.py` | 13 | 31 |
| `tests/test_evaluate.py` | 8 | 21 |
| `tests/test_fenster.py` | 33 | 199 |
| `tests/test_gold_ersetzen.py` | 7 | 17 |
| `tests/test_gold_markup.py` | 7 | 15 |
| `tests/test_goldpfad.py` | 7 | 10 |
| `tests/test_inference.py` | 6 | 16 |
| `tests/test_injector.py` | 9 | 15 |
| `tests/test_labelvertrag_eingefroren.py` | 4 | 7 |
| `tests/test_langes_dokument.py` | 4 | 8 |
| `tests/test_mail.py` | 8 | 45 |
| `tests/test_masking.py` | 11 | 17 |
| `tests/test_modell.py` | 14 | 50 |
| `tests/test_oberflaeche.js` | 95 | 556 |
| `tests/test_patterns.py` | 9 | 11 |
| `tests/test_rauschen.py` | 7 | 15 |
| `tests/test_regressionen.py` | 1 | 14 |
| `tests/test_scan_pdf.py` | 8 | 29 |
| `tests/test_schriften.py` | 6 | 15 |
| `tests/test_specs.py` | 12 | 34 |
| `tests/test_streuung.py` | 4 | 12 |
| `tests/test_user_rules.py` | 7 | 17 |
| `tests/test_vertrauen.py` | 8 | 14 |
| `tests/test_vorlieben.py` | 6 | 16 |
| **Summe** | **378** | **1555** |

## `tests/test_alignment.py`

Test der Ausrichtung Zeichenspanne <-> BIO (SPEC §11).

### T-ALIGNMENT-1: Grundfall

- erstes Token falsch
- zweites Token falsch
- Sonderzeichen muessen -100 bekommen, nicht O
- Spanne ohne Token
- Round-Trip Grundfall: …

### T-ALIGNMENT-2: Subword-Schnitt mitten in einer Entitaet

- Testaufbau falsch
- BIO-Folge falsch: …
- Decode liefert …

### T-ALIGNMENT-3: Grenzkonflikt wird gezaehlt, nicht verschwiegen

- Grenzkonflikt nicht erkannt: …

### T-ALIGNMENT-4: Zwei gleiche Tags nebeneinander bleiben getrennt

- zwei Entitaeten verschmolzen: …
- Decode verschmilzt sie wieder

### T-ALIGNMENT-5: Unbekanntes Tag wird laut, nicht still

- unbekanntes Tag muesste KeyError werfen

### T-ALIGNMENT-6: SentencePiece-Muster: Leerraum als eigenes Token

- Testaufbau falsch
- Leerraum-Token bricht die Entitaet: …
- Betrag zerfaellt: …
- Leerraum zwischen Entitaeten muesste O sein: …
- zwei Namen verschmolzen

### T-ALIGNMENT-6B: Echte Zefix-Namensformen

- Testaufbau falsch
- Zefix-Name verstuemmelt: … -> …

### T-ALIGNMENT-7: Round-Trip ueber das echte Trainingsset

- … von … Beispielen scheitern am Round-Trip

### T-ALIGNMENT-8: Wortweise Tokenisierung (ohne Subwords) als Gegenprobe

- … Beispiele scheitern bei wortweiser Tokenisierung

## `tests/test_api.py`

Die Endpunkte aus `specs/07_api.md`.

### T-API-1: Zustand

- zustand …
- Dienstname fehlt
- 45 Tags erwartet, …
- Labelvertrag-Fingerabdruck fehlt
- ohne_modell nicht gemeldet
- ohne Modell ohne Hinweis, das ist eine Leckquelle
- max_mb … passt nicht zu MAX_UPLOAD
- die Hilfe bekaeme eine Null als Obergrenze

### T-API-2: Tags

- 45 Tags erwartet, …
- Tag ohne Bezeichnung, leerer Menueeintrag in der Oberflaeche
- Endpunkt und Pack uneins ueber die Schwelle: …
- CANTON nicht tag_only
- AHVN13 ohne Pruefsumme
- NATIONALITY nicht bspd
- Sprache fehlt in der Antwort
- …: 45 Tags erwartet
- …: Tag ohne Bezeichnung
- …: … ist …, erwartet …
- unbekannte Sprache nicht abgewiesen, sie faellt sonst still auf Deutsch

### T-API-3: Maskieren

- anonymisieren …
- Original nicht unveraendert zurueck
- AHV-Nummer nicht maskiert
- Platzhalter [AHVN13_1] fehlt
- Zeichenzahl falsch
- Fundstellen != spans
- Hinweis ohne Modell fehlt
- einer Fundstelle fehlen Felder aus API_OBERFLAECHE.md
- eine AHVN13 erwartet, …
- AHVN13 aus …
- Positionen zeigen nicht ins ORIGINAL
- Vertrauen bei Muster nicht null

### T-API-3B: Vertrauen wird richtig zugeordnet

- ausgedehnte Modellspanne ohne Vertrauen: …
- Regextreffer traegt eine Modellzahl: …

### T-API-4: Rueckwandeln

- Woerterbuch leer
- AHV-Nummer nicht zurueckgeschrieben
- Mailadresse nicht zurueckgeschrieben
- nichts ersetzt
- unerwartet offen: …
- erfundener Platzhalter nicht gemeldet
- erfundener Platzhalter still entfernt
- abweichende Schreibweise nicht gemeldet

### T-API-5: Ohne Woerterbuch, endgueltig

- Woerterbuch trotz woerterbuch=false gefuellt
- Nummerierung fehlt trotzdem
- fehlende Umkehrbarkeit nicht gemeldet

### T-API-6: Klartext-Tags und bsPD

- EMAIL trotz `ohne` maskiert
- nicht ersetztes Tag traegt einen Platzhalter
- Klartext-Spanne traegt nicht `klartext: true`
- ohne Woerterbuch gilt eine ersetzte Spanne als Klartext
- bsPD im Klartext ohne auch_bspd durchgelassen
- auch_bspd wirkt nicht
- unbekanntes Tag nicht abgewiesen

### T-API-7: Leerer und fehlender Text

- leerer Text nicht abgewiesen
- fehlender Text nicht abgewiesen

### T-API-8: Datei statt Text

- Datei …
- Datei nicht maskiert
- Kodierung nicht gemeldet: …
- UTF-8 loest einen Kodierungshinweis aus
- unlesbares Format nicht abgewiesen

### T-API-8A: Ein boesartiger Dateiname bricht nichts auf und stuerzt nicht ab

- Dateiname … ergibt …, der Server stuerzt an einem Namen ab, statt ihn abzuweisen
- Dateiname …: Antwort ist kein JSON (…), der Vertrag sagt JSON

### T-API-8B: /api/lesen liest, und maskiert NICHT

- lesen …
- der gelesene Text stimmt nicht mit dem Original ueberein
- lesen hat trotzdem maskiert
- lesen liefert ein Woerterbuch
- lesen liefert Fundstellen
- Kodierung nicht gemeldet: …
- unlesbares Format nicht abgewiesen
- leere Datei nicht abgewiesen
- leere Datei ohne Begruendung abgewiesen
- ohne Datei nicht abgewiesen

### T-API-9: Eigene Regeln

- gute Regeln abgelehnt: …
- Regeldatei nicht geschrieben
- eine Regel erwartet, …
- Regeltag falsch
- Warnung zum Messergebnis fehlt
- eigene Regel greift nicht: …
- regeln=false wirkt nicht
- angenommen trotz …
- abgelehnte Regeln haben die Datei ueberschrieben

### T-API-10: Kein /api/senden

- /api/senden existiert, solange die Anbieterfrage offen ist, darf es das nicht

### T-API-10B: Ein fremder Wirtsname kommt nicht durch

- der eigene Rechner wird abgewiesen: …
- fremder Wirt … bekommt … statt 403
- die Absage traegt keinen Schluessel zum Uebersetzen
- der eingetragene Wirt wird abgewiesen
- 127.0.0.1 faellt heraus, sobald MASCHERA_WIRT gesetzt ist, dann scheitert der HEALTHCHECK im Abbild
- mit gesetztem MASCHERA_WIRT kommt jeder durch
- lokal unter …: … statt …
- `*` schaltet die Pruefung nicht ab
- `*` wirkt nicht
- IPv6 in Klammern falsch zerlegt
- Port nicht abgeschnitten
- nicht kleingeschrieben

### T-API-11: Klartext-Vorlieben lesen und schreiben

- GET /api/vorlieben -> …
- Feld `…` fehlt
- PUT -> …: …
- nicht gespeichert
- beim Lesen kommt etwas anderes zurueck als beim Schreiben
- Tippfehler durchgelassen: …
- abgelehnte Liste hat die bestehende ueberschrieben
- bsPD ohne auch_bspd durchgelassen
- bsPD mit auch_bspd -> …
- bsPD nicht ausgewiesen
- Zeichenkette statt Liste durchgelassen
- fehlendes Feld durchgelassen

### T-API-12: Vorlagen

- vorlagen …
- frische Ablage nicht leer
- keine Warnung, ein Prompt kann Personendaten enthalten
- speichern …
- nicht beide gespeichert
- Reihenfolge nicht erhalten
- … durchgelassen
- eine abgelehnte Liste hat die bestehenden Vorlagen ueberschrieben
- Leeren ging nicht

### T-API-13: Einstellungen

- Vorgabeadresse fehlt
- Vorgabeport …
- Claude fehlt
- die Vorgabe der Dienste ist nicht alphabetisch: …
- Mistral fehlt in der Vorgabe: …
- gewaehlt ist nicht Claude, sondern …
- Schriftvorgabe fehlt
- speichern …
- Port nicht als Zahl uebernommen
- Fensterschalter nicht gespeichert
- … durchgelassen
- eine abgelehnte Einstellung hat die bestehende ueberschrieben
- Schrifteinstellung nicht gespeichert
- gewaehlter Dienst nicht gespeichert
- verwaister Dienst nicht ersetzt

### T-API-14: Die schnelle Zeilennummer sagt dasselbe wie die langsame

- … Abweichung(en) bei der Zeilennummer

### T-API-15: Der Fortschritt ist abfragbar, waehrend gerechnet wird

- /api/fortschritt -> …
- /api/fortschritt ohne `…`
- es laeuft nichts, und trotzdem meldet er `aktiv`
- /api/fortschritt nimmt die Sperre, dann wartet er bis zum Schluss
- die Antwort traegt die gemessene Dauer nicht mehr

### T-API-16: Das Modell wird im Konstruktor geladen

- `…` steht nicht mehr in Zustand.__init__, laedt das Modell noch jemand?
- in Zustand.__init__ steht ein `return`, dahinter wird nichts mehr geladen

### T-API-17: Die Schriftgroessen haben vier Verwalter, die sich einig sind

- kein Auswahlfeld fuer die Schriftgroesse im HTML
- keine GROESSEN in maschera.js
- das Auswahlfeld bietet …, der Server nimmt …
- maschera.js kennt …, der Server nimmt …
- API_OBERFLAECHE.md nennt …, der Server nimmt …
- … Sprachgruppen statt 2 (Kopf, Willkommen)
- ein Sprachknopf steht ausserhalb der Sprachgruppen
- die Flaggenknoepfe bieten …, der Server nimmt …
- der Startbildschirm kennt …, der Server nimmt …
- PUT sprache=it -> …
- die Sprache kommt anders zurueck, als sie geschrieben wurde
- unbekannte Sprache durchgelassen: …
- die Ablehnung traegt den falschen Schluessel: …
- die abgelehnte Sprache hat die bestehende ueberschrieben
- Schriftgroesse … steht im Feld, der Server weist sie ab

### T-API-18: Jeder Hinweis-Schluessel steht in allen vier Sprachen

- zu wenige Schluessel gefunden: …
- … Hinweistabellen statt vier
- Sprachtabelle … ohne: …
- Sprachtabelle … hat unbenutzte: …

### T-API-19: Jeder Meldungs-Schluessel steht in allen vier Sprachen

- zu wenige Schluessel gefunden: …
- … Meldungstabellen statt vier
- Sprachtabelle … ohne: …
- Sprachtabelle … hat unbenutzte: …
- Sprachtabelle …, …: Platzhalter … statt …
- … setzt den Text einer Ausnahme als Wert ein
- … bricht ohne Schluessel ab, `Abbruch` nehmen
- eine Meldung setzt noch `{grund}` ein
- zu kurzes Wort nicht mit eigenem Schluessel: …
- kaputtes YAML ohne Zeile: …
- kaputtes PDF traegt Fremdtext in die Oberflaeche: …
- die Antwort nennt einen temporaeren Pfad: …
- die Antwort traegt mehr als den eigenen Satz: …
- kaputtes DOCX ohne eigenen Schluessel: …

### T-API-20: Der Einstellungsdialog schickt JEDES Feld zurueck

- sichereEinstellungen() in maschera.js nicht gefunden
- sichereEinstellungen() schickt … nicht mit, der Server setzt das Feld beim Schliessen des Dialogs auf die Vorgabe
- die Probe kennt … nicht wie die Vorgabe
- «…» steht in der Probe auf dem Vorgabewert und beweist nichts
- der abweichende Stand liess sich nicht schreiben
- «…» hat das Schliessen des Einstellungsdialogs nicht ueberlebt: … statt …

### T-API-21: Jede Wahlliste hat EINEN Verwalter

- die Oberflaeche bietet unter «…» gar nichts an
- … bietet …, der Server nimmt …
- kein … in maschera.js
- maschera.js kennt fuer … …, der Server nimmt …
- die Oberflaeche kennt den Fenstermodus «…» nicht
- serve.py schreibt die Themenliste ein zweites Mal aus
- alte Schrift «sans» wird abgewiesen statt umgesetzt, lade() verwirft dann alle Einstellungen

### T-API-21B: Die Hilfe hat in allen vier Sprachen denselben Bau

- HILFE_… fehlt in seiten.js
- die vier Hilfetexte sind verschieden gebaut: …, (Absaetze, Ueberschriften). Wer eine Sprache aendert, aendert alle vier, sonst steht in dreien etwas Ueberholtes

### T-API-21C: Die Anwendertexte duzen, in JEDER Sprache

- Anwendertext siezt: …, entschieden ist durchgehend duzen, und eine halb geduzte Oberflaeche liest sich wie aus zwei Haenden

### T-API-22: Die Hilfe nennt keine Formate, die der Server ablehnt

- … Formatzeilen in seiten.js, genau vier erwartet, eine Sprache nennt andere Formate oder gar keine
- die Hilfe nennt …, der Server weist sie ab, und der Anwender sucht den Fehler bei sich
- die Hilfe verschweigt den Leseweg «…» ganz
- die Sprachfassungen nennen verschiedene Formate: …

### T-API-23: Nach Updates suchen: eine feste Adresse, nur die Nummer, nur auf POST

- neuere Fassung nicht erkannt: … …
- die Antwort reicht eine Adresse von GitHub weiter
- gleiche Fassung gilt als neuer: …
- eine AELTERE Fassung gilt als neuer
- ohne Netz kein 503 mit Schluessel: …
- unlesbare Antwort … nicht abgewiesen: …
- gefragt wurde nicht die feste Adresse: …
- feste Adresse unerwartet: …
- GET /api/neueste antwortet …, gefragt: …
- adressen.json: Eintrag «neueste» fehlt oder zeigt woanders hin: …
- die CSP oeffnet GitHub fuer das Fenster: …

### T-API-24: Jeder Endpunkt des Servers steht im Vertrag

- nicht in API_OBERFLAECHE.md: …

### T-API-25: MASCHERA_WIRT=* meldet sich laut, auf allen drei Startwegen

- MASCHERA_WIRT=* warnt nicht
- ein benannter Wirt loest die Warnung aus
- ohne Variable warnt wirt_warnung (dafuer gibt es die andere)
- … gibt die Warnung nicht aus

### T-API-26: Der Name einer hochgeladenen Datei wird nie zum Pfad

- die temporaere Datei traegt wieder den Namen des Anwenders
- …: …

### T-API-27: Ohne Dienst wird nicht gespeichert, aber eine alte Datei laedt

- leere Dienstliste gespeichert: …
- falscher Schluessel: …
- eine alte Datei mit leerer Dienstliste verliert beim Laden die Schrift

### T-API-28: Eine Testfassung liegt VOR der gleichnamigen fertigen

- ist_neuer(…, …) ist nicht …
- der Vorabteil geht beim Lesen verloren

### T-API-29: Das GitHub-Abfragelimit heisst nicht «nicht erreichbar»

- HTTP … (Rest …): … … statt …

### T-API-30: Jedes Feld einer echten Antwort steht im Vertrag

- 07_api.md: Abschnitt … fehlt
- …: keine Objektantwort
- …: Feld `…` steht nicht im Vertrag

## `tests/test_app.py`

Auslieferung der Oberflaeche, C1.

### T-APP-1: Die Seite kommt an

- / antwortet …
- falscher Typ: …
- Titel fehlt

### T-APP-2: Umlaute kommen als UTF-8 an

- kein charset=utf-8 im Content-Type
- keine Sonderzeichen in der Seite, nichts geprueft
- Mojibake in der Seite, Kodierung stimmt nicht

### T-APP-3: Die Endpunkte sind daneben weiter erreichbar

- … antwortet …
- Dienstname fehlt
- ohne_modell nicht gemeldet

### T-APP-4: `/api/senden` bleibt 404, auch mit Oberflaeche

- … /api/senden antwortet … statt 404
- … /api/gibtesnicht antwortet … statt 404

### T-APP-5: Unbekannte Datei gibt 404, kein Ausbruch aus dem Ordner

- fehlende Datei nicht 404
- … liefert eine Datei ausserhalb von static/

### T-APP-6: Nichts wird von aussen nachgeladen

- …:… laedt von aussen: …
- keine Oberflaechendateien gefunden
- … Stellen sind als «nach-aussen-erlaubt» markiert, erlaubt ist genau eine (die Portpruefung)

### T-APP-7: Keine Kette im Browser

- … enthaelt …, die Attrappe des Entwurfs

### T-APP-8: `serve.py` laeuft weiter ohne Oberflaeche

- Kern antwortet nicht
- der nackte Kern liefert eine Oberflaeche aus

### T-APP-9: Die Schriften werden ausgeliefert

- keine Schriftdateien gefunden
- /schriften/… -> …
- /maschera.css -> …
- falscher Typ fuer CSS: …

### T-APP-10: Die Oberflaechenlogik wird ausgeliefert

- /maschera.js -> …
- falscher Typ: …
- ruft /api/anonymisieren nicht auf
- maschera.js benutzt innerHTML
- maschera.js benutzt outerHTML
- maschera.js benutzt insertAdjacentHTML

### T-APP-11: Maskieren laeuft ueber die Kette, nicht im Browser

- /api/anonymisieren -> …
- AHV-Nummer nicht maskiert
- AHVN13 fehlt, gefunden: …
- IBAN fehlt, gefunden: …

### T-APP-12: Jeder Platzhalter passt auf das Muster der Oberflaeche

- … Platzhalter im Text, … Spannen
- Platzhalter passt nicht aufs Muster: …
- maschera.js kennt das Platzhaltermuster nicht

### T-APP-13: Woerterbuch und Kennzahlen kommen mit

- kein Woerterbuch
- Woerterbuch leer
- Woerterbucheintrag … steht nicht im Original
- Zeichenzahl … statt …

### T-APP-14: Jede Kennung, die das JS anspricht, steht im HTML

- JS spricht an, HTML hat nicht: …

### T-APP-15: Logo und Startbildschirm werden ausgeliefert

- /maske.svg -> …
- /maske.svg kommt nicht als SVG
- … zeigt nicht auf maske.svg
- Kopfzeile zeigt nicht auf maske.svg
- … liegt noch in app/static/
- kein Startbildschirm im HTML
- es gibt wieder eine Prozentzahl beim Laden

### T-APP-16: Die Oberflaeche sagt, wo die Grenze verlaeuft

- … LOKAL-Plaketten, seit 2.1 keine
- kein Lokalzeiger im Kopf
- … ONLINE-Plaketten, sie sind zum Sendeknopf gewandert
- Spalte 3 ist nicht abgesetzt
- kein staendiger ONLINE-Hinweis am Sendeknopf
- … Sprachen mit ONLINE-Hinweis statt 4
- der Hinweis nennt den Dienst nicht oder an mehr als einer Stelle

### T-APP-17: Beim Schliessen wird vor Datenverlust gewarnt

- keine Warnung beim Schliessen
- keine Rueckfrage vor «Neu» und «Beispiel»

### T-APP-18: Einseitenanwendung: keine feste Hoehe im Raster

- … setzt min-height: …px, das schiebt den Inhalt aus dem Fenster
- … hat kein min-height: 0
- die Seite selbst darf nicht rollen

### T-APP-19: Nach aussen heisst es MASKIERUNG

- …: die Zeile mit … fehlt
- …: «Maskierung» fehlt in: …
- …: dort steht noch «Pseudonymisierung»
- dist/AppDir/maschera.desktop traegt noch das alte Wort, die AppImage ist aelter als die Quelle
- appimage_bauen.fish schreibt keine `X-AppImage-Version` in den Eintrag, Gearlever zeigt dann keine Fassung an
- die Fassung steht im Bauskript als feste Zeichenkette statt aus `fassung.fish`, siehe test_fenster.py Punkt 7
- appimage_bauen.fish sieht die geschriebene Fassung nicht nach, ein Tippfehler faende erst der Anwender in Gearlever
- der Startbildschirm kennt nicht genau die vier Bediensprachen
- …: der Startbildschirm fuehrt andere Saetze als de, fehlt …, zuviel …
- …: der Startbildschirm nennt das Werkzeug nicht, …
- der Startbildschirm liefert die Vorlage … unersetzt aus
- der ausgelieferte Startbildschirm (…) nennt das Werkzeug nicht

### T-APP-6B: Das Onboarding traegt gueltiges Skript und alle vier Sprachen

- das Onboarding liefert die Vorlage … unersetzt aus
- die eingebetteten Saetze sind kein gueltiges JSON: …
- das Onboarding traegt … statt vier Sprachen, dann faellt der Schalter auf eine leere Sprache
- das Skript des Onboardings parst nicht: …

### T-APP-20: Das Browsersymbol ist erzeugt, nicht gemalt

- app/static/favicon.ico fehlt, `fish tools/favicon_bauen.fish`
- favicon.ico ist aelter als maske.svg, neu bauen mit `fish tools/favicon_bauen.fish`
- favicon.ico ist kein ICO
- nur … Kantenlaenge(n), fuer die Schreibtischverknuepfung braucht es die grossen
- der SVG-Verweis fehlt
- der ICO-Verweis fehlt
- das ICO steht vor dem SVG, dann nimmt es auch ein Browser, der das SVG koennte
- /favicon.ico kommt nicht
- /adressen.json kommt nicht

### T-APP-21: Jede Antwort traegt die Sicherheitskopfzeilen

- …: keine Content-Security-Policy
- …: `X-Content-Type-Options: nosniff` fehlt
- die Policy erlaubt Inline-Code oder eval, dann schuetzt sie nichts
- script-src ist …, erwartet nur 'self'
- object-src ist nicht 'none'
- frame-ancestors ist nicht 'none', die Seite liesse sich einbetten
- connect-src erlaubt den eigenen Dienst nicht
- connect-src erlaubt Ziele ausserhalb der Maschine: …
- die Portpruefung auf 127.0.0.1 waere gesperrt
- Inline-Stil im HTML, `style-src 'self'` sperrt ihn still
- ein <style>-Block im HTML
- ein Inline-Skript im HTML
- ein on…=-Attribut im HTML
- ein CSS-Selektor haengt am `style`-Attribut, seit der Policy eine Markierung, die still verschwinden kann

### T-APP-22: Knoepfe, Kaesten und Fenster tragen EINE Rundung

- `--radius-md` ist nicht 4px, die Rundung der Feldknoepfe
- `…`, eine eigene Rundung neben `--radius-md`

### T-APP-23: Die Maske traegt auf dunklem Grund, in der App und als Symbol

- maske.svg: Flaeche oder Rand tragen ihre Klasse nicht mehr
- maske.svg folgt dem dunklen System nicht
- maske.svg kennt … nicht
- maske.svg: die Ziele #hell/#dunkel fehlen
- die Kopfzeile folgt der Wahl «…» nicht
- die Bilder der Maske folgen der Farbwahl nicht
- das Symbol ist nicht quadratisch
- das Symbol hat keinen Platz fuer den Rand
- das Symbol hat keinen hellen Aussenrand
- … zeichnet das Symbol nicht ueber core/symbol.py
- fenster.py: Ablagefach oder Fenster zeichnen die rohe Maske

## `tests/test_befunde.py`

Zwei gemessene Befunde: Gesetzesdatum und die `&`-Spanne.

### T-BEFUNDE-1: Gesetzesdaten: Stufe 2 schweigt, TEILWEISE behoben

- Gesetzesdatum maskiert: … in …

### T-BEFUNDE-2: Echte Daten werden maskiert, hier waere ein Ausfall ein LECK

- LECK, … nicht gefunden in …

### T-BEFUNDE-3: Beides im selben Text

- erwartet zwei echte Daten, gefunden …

### T-BEFUNDE-4: `&` bricht die Firmenspanne nicht mehr

- … nicht gefunden, sondern …

### T-BEFUNDE-5: Das Muster greift nicht ueber den Namen hinaus

- greift ueber den Namen hinaus: … in …

### T-BEFUNDE-6: Firmen OHNE Bindeglied haengen weiter am Modell

- unerwartet doch von Stufe 2 gefunden: …, dann gehoert der Kommentar in patterns.yaml korrigiert

### T-BEFUNDE-7: Ein Tag OHNE Schwelle bricht die Vertrauensliste nicht

- kein einziges Tag ohne Schwelle, dann misst diese Pruefung nichts mehr und die Begruendung oben ist veraltet
- Vertrauensliste bricht bei …: …

## `tests/test_ch_checksums.py`

Testsuite für die Prüfsummen (SPEC §5).

### T-CH-CHECKSUMS-1: Bekannte Vektoren

- … … müsste gültig sein
- … … müsste ungültig sein (…)
- kein einziger UID-Körper mit Prüfergebnis 10 gefunden

### T-CH-CHECKSUMS-2: Round-Trip, … Nummern je Typ

- …: … von … generierten Nummern fielen durch
- …: unformatierte Schreibweise fällt durch

### T-CH-CHECKSUMS-3: Mutation: eine Ziffer ändern, … Versuche je Typ

- …: … von … Einzelziffer-Fehlern nicht erkannt

### T-CH-CHECKSUMS-4: Transposition: Nachbarziffern tauschen, … Versuche je Typ

- UID müsste alle Transpositionen erkennen (Modulo 11)
- IBAN müsste alle Transpositionen erkennen (Modulo 97)
- QR-Referenz unter Erwartung: … %
- AHVN13 unter Erwartung: … %

## `tests/test_dist_frisch.py`

Ist `dist/` aelter als der Bauplan, der es erzeugt hat?.

### T-DIST-FRISCH-1: Ist der Bauplan da?

- fehlt: …

### T-DIST-FRISCH-2: Passt der Fingerabdruck zu den Dateien in dist/?

- dist/ wurde nach dem Bauen veraendert: … python3 packs/ch/nomenclatures/build.py --build

### T-DIST-FRISCH-3: Behoerdennamen ohne Ortsnamen

- Ortsnamen in den Behoerdenwerten: … Der Ortsname gehoert in einen eigenen {CITY}-Slot. Sonst erfasst das Muster nur den Teil ohne Ort, und jeder Wert wird zum Teiltreffer.

### T-DIST-FRISCH-4: Vertragen die Werkzeuge, die dist/ durchgehen, den Inhalt?

- Nomenklatur ohne meta/entries: … Traegt eine Datei den Vertrag nicht, gehoert sie nicht nach dist/ oder braucht einen Unterstrich.

## `tests/test_dokumente_docx.py`

DOCX einlesen, ohne neue Abhaengigkeit, ohne Word, ohne Beispieldatei.

### T-DOKUMENTE-DOCX-1: Endung ist angemeldet, .doc ausdruecklich nicht

- .docx fehlt in ALLE
- .doc steht in ALLE, landete im Textzweig
- .doc fehlt bei den alten Endungen

### T-DOKUMENTE-DOCX-2: Laeufe werden zusammengezogen, nicht zerschnitten

- Laeufe zerschnitten: …

### T-DOKUMENTE-DOCX-3: Tabellenzeilen behalten Etikett und Wert auf EINER Zeile

- 2 Zeilen erwartet, …: …
- Etikett und Wert getrennt: …
- Wert nicht in derselben Zeile wie der Anker
- Tabellen nicht gemeldet

### T-DOKUMENTE-DOCX-4: Umbruch und Tabulator im Absatz bleiben erhalten

- Umbruch verloren: …

### T-DOKUMENTE-DOCX-5: Kopf- und Fusszeilen werden GEMELDET, nicht verschwiegen

- Kopfzeilen nicht gemeldet: …
- Fusszeilen nicht gemeldet: …
- Auslassung nicht als solche benannt

### T-DOKUMENTE-DOCX-6: Ohne Kopfzeilen keine Warnung

- warnt ohne Grund: …

### T-DOKUMENTE-DOCX-7: Leeres Dokument sagt, dass es leer ist

- unerwarteter Text: …
- leeres Dokument schweigt: …

### T-DOKUMENTE-DOCX-8: Kaputte Datei bricht ab statt zu raten

- kaputte .docx wurde stillschweigend gelesen
- Meldung nennt das alte Format nicht: …

### T-DOKUMENTE-DOCX-9: ZIP ohne document.xml wird erkannt

- ZIP ohne word/document.xml wurde gelesen

### T-DOKUMENTE-DOCX-10: .doc wird vor dem Textzweig abgefangen

- .doc wurde als Text gelesen
- Meldung nennt den Ausweg nicht: …

### T-DOKUMENTE-DOCX-11: lies() liefert format 'docx' und die Hinweise

- … Dokumente statt 1
- format …
- Text kam nicht durch
- kennung …

### T-DOKUMENTE-DOCX-11B: Zwei Bomben werden abgewiesen, nicht ausgepackt

- eine DTD im Dokumentteil wird gelesen statt abgewiesen
- abgewiesen, aber mit falschem Grund: …
- die Groessengrenze wirkt nicht
- die Wache weist auch gewoehnliche ab

### T-DOKUMENTE-DOCX-12: Echte Word-Dateien in beispiele/, falls vorhanden

- …: nichts gelesen
- …: Nullbytes im Text, falsch gelesen
- …: format …

## `tests/test_evaluate.py`

Test der Auswertung (SPEC §4, §11).

### T-EVALUATE-1: Perfekte Vorhersage

- Leckrate muesste 0 sein: …
- F1 muesste 1 sein: …

### T-EVALUATE-2: Gewichtung: AHV-Nummer verpasst vs. Kanton verpasst

- AHV-Leck zu leicht gewichtet: …
- CANTON ist tag_only und kann gar nicht lecken: …

### T-EVALUATE-3: Teiltreffer schuetzt teilweise

- Teiltreffer muesste zwischen 0 und Vollverlust liegen: …

### T-EVALUATE-3B: Umetikettierung ist KEIN Leck

- Umetikettierung darf nicht als Leck zaehlen: …
- Tagtreue muss trotzdem als Fehler in Precision/Recall erscheinen

### T-EVALUATE-4: Uebermaskierung wird getrennt ausgewiesen

- Uebermaskierung darf die Leckrate nicht erhoehen
- Uebermaskierung nicht gezaehlt: …

### T-EVALUATE-5: Grundlinie: nur Regex, ohne Modell, auf 300 Beispielen

- Leckrate muss zwischen 0 und 1 liegen
- Regex muesste AHVN13 fast vollstaendig finden: …

### T-EVALUATE-6: Je Dokument: die Gesamtzahl verdeckt den Einzelfall

- Leckzahl darf sich nicht aendern: … vs …
- ein leichtes Dokument muss die Leckrate verduennen, sonst misst dieser Test nicht, was er soll
- je_dokument nennt nicht beide Dokumente
- Gruppierungen fehlen
- Spaltenkollision: …

### T-EVALUATE-7: Schwellen: Budget als Vorgabe, Tag als begruendete Ausnahme

- die drei Budgets muessen gesetzt bleiben
- ein P-Tag muss den Budgetwert tragen
- Ausnahme … = … ist identisch mit Budget …. Eine Ausnahme, die nichts aendert, ist keine, streichen statt eintragen.
- Schwellen-Ausnahme … ist in taxonomy.yaml nicht mit einer Messung begruendet
- … Ausnahmen, ab hier ist das Budget keine Vereinfachung mehr, sondern eine Liste

## `tests/test_fenster.py`

Das eigene Fenster: Adresse, Port und dass die Wahl bleibt.

### T-FENSTER-0: Ohne eigenen Punkt

- die Pruefung zeigt auf …, das ist NICHT das temporaere Verzeichnis. Abbruch, bevor etwas geschrieben wird.

### T-FENSTER-1: `belegt` prueft BINDEN, nicht Antworten

- Port … ist gebunden und gilt trotzdem als frei
- der Grund ist unbrauchbar: …

### T-FENSTER-2: `naechster_freier` ueberspringt den belegten

- kein freier Port in 50 Schritten gefunden
- der Vorschlag … ist genau der belegte Port
- der Vorschlag … liegt nicht oberhalb
- der Vorschlag … ist selbst nicht frei
- bei belegtem Port fragt main() wieder einen Dialog
- der ausgewichene Port wird nicht gesichert
- der deutsche Qt-Dialog fuer den Port ist wieder da

### T-FENSTER-3: Die Wahl ueberlebt die Sitzung

- die Vorgabe ist nicht 127.0.0.1:4141, sondern …:…
- nach dem Sichern steht …, erwartet 5099
- die Adresse ging verloren: …
- beim Sichern von Adresse und Port sind die Dienste verschwunden

### T-FENSTER-4: Ein unmoeglicher Port wird abgewiesen

- Port … wurde angenommen

### T-FENSTER-5: Das Fenster nimmt keinen Zufallsport

- fenster.py liest die gespeicherten Einstellungen nicht
- fenster.py laesst sich noch einen zufaelligen Port geben, dann horcht der Dienst jedes Mal woanders, und die Einstellung des Anwenders bewirkt nichts
- die im Dialog gewaehlte Adresse wird nicht gesichert, dann fragt das Werkzeug bei jedem Start dasselbe

### T-FENSTER-6: Der Vorgabeport hat GENAU EINEN Verwalter

- in tools/paket/ wurde KEINE Portangabe gefunden, die Muster greifen nicht mehr, und dann prueft dieser Punkt nichts

### T-FENSTER-7: Die Fassungsnummer hat GENAU EINEN Verwalter

- keine VERSION in app/serve.py

### T-FENSTER-8: Beide Bauwege sehen nach, dass torch die CPU-Fassung ist

- … sieht nicht nach, ob torch die CPU-Fassung ist, ein Fehlgriff waere unsichtbar, weil CUDA-torch laeuft und nur 2 GB schwerer ist
- … liest `torch.__version__` nicht, dann prueft es etwas anderes als die eingebaute Fassung

### T-FENSTER-9: Qt wird ueber `qtpy` geholt, nie direkt

- Qt wird direkt geholt statt ueber `qtpy`: …, damit haengt die Bindung an dieser Zeile und nicht an QT_API, und die Anwendung laeuft teils auf der einen, teils auf der anderen

### T-FENSTER-10: Kein Name wird vor seinem Import im selben Rumpf benutzt

- hier wird ein Name vor seinem Import im selben Rumpf benutzt, das ist ein UnboundLocalError, und zwar erst zur Laufzeit und nur in dem Zweig, der ihn erreicht: …

### T-FENSTER-11: Der Prozess heisst maschera und nicht python

- benenne() bricht ab: …
- der Kernname ist …, erwartet 'maschera', `killall maschera` findet den Prozess sonst nicht
- benenne() konnte gar nichts setzen
- app/… benennt den Prozess nicht, auf diesem Weg heisst er weiter `python`, und `killall python` trifft alles andere mit

### T-FENSTER-12: Jede Verpackung nimmt dieselben tools/-Dateien mit

- nur … aus tools/ gefunden, die Ableitung greift nicht mehr
- … nimmt … nicht mit, das faellt nicht beim Bauen auf, sondern beim ersten Start
- draussen.txt fuehrt nur … Eintraege, geleert?
- der Windows-Zwischenstand enthaelt …
- Windows nimmt aus tools/ … mit, noetig …
- Bytecode im Windows-Zwischenstand: …
- … laesst … nicht weg, Werkstattdateien fahren zum Anwender (siehe draussen.txt)
- … liefert … nicht mit
- … nennt sich in der ERSTEN Fassungsangabe …, app/serve.py sagt …, zwei Fassungen fuer ein Paket
- keine Fassungsangabe in tools/paket/ gefunden, metainfo.xml traegt eine, die Suche greift nicht mehr

### T-FENSTER-13: Wer aus der Maske ein Symbol macht, legt sie aufs Quadrat

- … macht aus maske.svg ein Symbol, legt sie aber nicht aufs Quadrat, es wird in der Leiste verzogen, und das meldet niemand als Fehler
- nur … Stelle(n) gefunden, die aus der Maske ein Symbol machen, erwartet sind mindestens fuenf; die Suche greift nicht mehr

### T-FENSTER-14: Kein Bauskript ueberschreibt die Einstellungen des Anwenders


### T-FENSTER-15: Die Zwischenablage toetet das Fenster nicht mehr

- nichts gerichtet: …
- nur … Antworten
- … bekommt …, keine Aufzaehlung, daran stirbt der Prozess beim Kopieren
- … bekommt eine nackte Zahl
- die Zwischenablage ist verweigert, dann scheitert `writeText` still, und der Anwender fuegt nichts ein
- … ist erlaubt, Kamera, Mikrofon und Ort gehoeren verweigert

### T-FENSTER-16: Das Herunterladen tut im eigenen Fenster etwas

- Qt kennt `setPath` wieder, dann ist der Eingriff zu pruefen
- Qt kennt `…` nicht mehr, der Eingriff ist ueberholt
- nichts gerichtet: …
- der Download wurde nicht angenommen: …
- falsches Verzeichnis: …
- falscher Dateiname: …
- der Vorschlag traegt nicht den echten Namen: …
- der Dialogtitel steht in keiner der vier Sprachen: …
- abgebrochen wurde nicht abgebrochen: …
- trotz Abbruch wurde ein Ziel gesetzt
- der Speicherdialog kennt nicht die vier Bediensprachen

### T-FENSTER-17: Das Ablagefach, und was ohne Ablagefach passiert

- das Ablagefach ist vorgabemaessig aus
- das schmale Fenster ist nicht die Vorgabe
- unerwartete Fenstermodi: …
- der Widget-Modus ist zu schmal fuer einen Satz: …
- der Widget-Modus oeffnet mit …, gemessen braucht die Oberflaeche …
- der Widget-Modus rechnet Rahmen und Rollbalken nicht mit, dann ist der Inhalt schmaler als gemessen
- … ist nicht die Summe aus … und …, eine dritte Zahl ist die, die man beim naechsten Mal vergisst
- der Widget-Zweig ist nicht mehr zu finden
- der Widget-Modus setzt keine Untergrenze
- das Widget-Fenster laesst sich auf … ziehen, obwohl es mit … oeffnet, darunter kommt der waagrechte Rollbalken
- das Ablagefach kennt nicht die vier Bediensprachen
- tray_moeglich() meldet ein Ablagefach ohne QApplication
- TRAY_WORTE[…] fuehrt … Woerter, erwartet sind Beenden und Fenster zeigen
- TRAY_WORTE[…] traegt ein leeres Wort
- «Fenster zeigen» steht in TRAY_WORTE und beschriftet nichts
- «Beenden» steht in TRAY_WORTE und beschriftet nichts
- das Ablagefach raet wieder am Schreibtisch herum, der Eintrag steht ueberall, dann braucht es keine Erkennung
- ohne Ablagefach wird das Schliessen abgefangen, dann ist die App weg, ohne Fenster und ohne Symbol
- mit Ablagefach schliesst das X trotzdem
- «Beenden» aus dem Ablagefach wird abgefangen, die App laesst sich dann nur ueber den Prozessmanager loswerden
- `main()` haengt nichts an `closing`
- `main()` fragt beim Schliessen nicht, ob es ein Ablagefach gibt
- ohne Ablagefach gibt `main()` das Schliessen nicht frei
- `main()` versteckt das Fenster nicht
- `main()` fragt den Beendenwunsch nicht ab, «Beenden» versteckt das Fenster dann nur
- der Beendenwunsch wird erst nach dem Verstecken gefragt
- `tray_richten()` richtet kein __init__ mehr ein
- der Beenden-Eintrag merkt den Wunsch nicht vor
- `tray_bauen` wird nicht mehr aufgerufen
- `tray_bauen` bekommt … Argumente statt vier: …
- der Beenden-Rueckruf ist … statt `beenden`, zeigt er auf `self.close`, laeuft er in den Behandler und versteckt nur
- `tray_bauen()` nicht gefunden
- das Ablagefachsymbol hoert auf keinen Klick
- der einfache Linksklick wird nicht ausgewertet
- der Rueckruf ist nicht festgemacht, Python raeumt ihn ab, und die Verbindung stirbt lautlos mit ihm
- das Rechtsklickmenue kennt … Eintraege, erwartet sind Beenden und Fenster zeigen
- ein sichtbares Fenster wird beim Klick nicht versteckt
- es wird minimiert statt versteckt, unter Wayland kommt ein minimiertes Fenster ueber das Ablagefach nicht zurueck
- das versteckte Fenster kommt beim Klick nicht zurueck
- das Fenster kommt zurueck, aber nicht nach vorne
- ein minimiertes Fenster wird beim Klick noch weiter versteckt
- die Lage wird vor dem Verstecken nicht gemerkt
- die gemerkte Lage wird beim Zeigen nicht wiederhergestellt
- eine andere Lage kam zurueck: …
- die Lage wird gesetzt, bevor das Fenster wieder da ist
- das Symbol des Ablagefachs fehlt

### T-FENSTER-18: Die Ausgabe ueberlebt einen weggebrochenen Leser

- der Prozess starb mit …, obwohl nur die Ausgabe weggebrochen ist: …
- BrokenPipeError kam trotzdem durch: …
- ohne `ausgabe.sichern()` laeuft es auch durch, dann prueft dieser Punkt nichts
- `main()` nicht gefunden
- `main()` sichert die Ausgabe nicht, bevor es druckt

### T-FENSTER-19: Nur EIN MASCHERA

- ohne laufende App meldet `laeuft_schon()` trotzdem eine
- der Horcher ist nicht gestartet
- mit laufendem Horcher wird die laufende App nicht erkannt
- der zweite Start hat sich gemeldet, das Fenster erfaehrt es nicht
- eine tote Sockeldatei gilt als laufende App, dann startet MASCHERA nach einem Absturz nie wieder
- die tote Sockeldatei wird nicht weggeraeumt
- `main()` fragt nicht, ob schon eine laeuft
- die Frage nach der laufenden App kommt erst nach der Portpruefung, dann fragt der Dialog wieder nach einem anderen Port

### T-FENSTER-20: Das Fenster traegt die Maske, nicht das W

- `symbol_richten()` fehlt
- das Fenstersymbol kommt nicht aus der Maske
- das Fenster selbst bekommt kein Symbol
- die Anwendung bekommt kein Symbol, in der Fensterliste steht weiter das W
- `symbol_richten()` wird nie gerufen

### T-FENSTER-21: Der Startbildschirm kennt den Dunkelmodus

- der Startbildschirm hat keinen dunklen Zweig, er blitzt weiss auf
- die Systemwahl schlaegt hier die ausdrueckliche Wahl «hell»
- «dunkel» laesst sich hier nicht erzwingen
- die zwei Einhaengepunkte des Startbildschirms tragen verschiedene Marken
- … Farbliteral(e) im Startbildschirm ausserhalb der Marken: …
- die hellen Werte des Startbildschirms haben sich verschoben

### T-FENSTER-22: Flatpak und Abbild fuehren dieselben Pakete

- andere Pakete: nur im Abbild …, nur im Flatpak …
- …: Abbild …, Flatpak …
- PyQt steht in requirements-flatpak.txt, es kommt aus dem BaseApp, ein zweites waeren 525 MB doppelt
- pywebview[qt] im Flatpak zieht PyQt6 nach
- die Index-Zeilen (CPU-torch) unterscheiden sich

### T-FENSTER-23: Die Bruecken zur Seite zeigen nur ihre Methoden

- die Bruecke traegt oeffentliche Felder: …, pywebview reicht sie an die Seite weiter und steigt in sie hinein
- die Bruecke bietet der Seite … an, erwartet sind holen, neustart, spaeter, sprache, weiter
- die kleine Bruecke traegt oeffentliche Felder
- die kleine Bruecke bietet … an
- Windows startet nicht die .exe neu
- die AppImage startet das Python im verschwindenden Einhaengepunkt oder behaelt den alten Modellpfad
- ein alter --nach-pid wird weitergereicht
- warte_auf_ende erkennt einen beendeten Prozess nicht
- warte_auf_ende haelt einen laufenden Prozess fuer beendet

### T-FENSTER-24: Unter Windows: Infobereich und Hervorholen ohne Qt

- das Symbol laeuft nicht an (`run_detached` fehlt)
- das Symbol traegt nicht den Titel
- das Menue sagt …, erwartet «Fenster zeigen», «Beenden» in der Bediensprache
- der Linksklick holt das Fenster nicht hervor
- «Fenster zeigen» tut …
- «Beenden» merkt den Wunsch nicht vor, der Schliessbehandler versteckte dann nur
- «Beenden» laesst das Symbol im Infobereich stehen
- «Beenden» schliesst das Fenster nicht
- ein zweiter Start holt das Fenster unter Windows nicht hervor
- der Horchfaden endet nicht mit dem Programm

### T-FENSTER-25: Kein Paket nimmt Pickle-Dateien aus dem Modellordner mit

- windows_bauen.MODELL_DRAUSSEN fuehrt nicht alle Endungen: …
- .dockerignore laesst … im Modellordner nicht weg
- appimage_bauen.fish loescht … im Modellordner nicht
- der Windows-Modellordner enthaelt …

### T-FENSTER-28: Der Hilfsprozess der Standardbibliothek wird erkannt, fremder Code nicht

- der Tracker-Aufruf wird nicht erkannt: …, …
- ein fremder Aufruf wurde angenommen: …
- windows_start.py fuehrt Text aus (exec/eval)

### T-FENSTER-27: Was das AppRun an fenster.py weitergibt, kennt fenster.py

- die Optionen von fenster.py nicht gefunden: …
- AppRun gibt … an fenster.py weiter, das kennt es nicht
- MASCHERA_PORT=4242 wird nicht gelesen
- MASCHERA_PORT=… gilt als Portnummer
- ohne Variable gilt ein Port

### T-FENSTER-26: Der macOS-Bau teilt die Listen mit Windows, die Workflows sind zahm

- macos_bauen.py benutzt … nicht, dann laufen die Listen von Windows und macOS auseinander
- tools/paket/macos-symbol-1024.png fehlt
- das macOS-Symbol misst …x…
- macos_bauen.py gibt PyInstaller kein Symbol mit (--icon, iconutil)
- … darf mehr als lesen: …
- … nutzt pull_request_target, das liehe Beitraegen von aussen Geheimnisse und Schreibrechte
- …: nur … Actions gefunden, die Wache sucht an der falschen Stelle
- …: Action nicht auf einen Commit festgenagelt: …
- der Paket-Workflow startet nicht nur von Hand: …
- release.yml startet nicht nur bei einem Tag: …
- release.yml legt auch im Probelauf ein Release an
- release.yml pusht das Abbild auch im Probelauf
- release.yml baut das Abbild ohne `pull: true`
- der Signatur-Workflow startet nicht nur von Hand: …
- abbild-signieren.yml setzt ${{ … }} direkt in ein Skript
- abbild-signieren.yml: Rechte des Jobs …
- der Testlauf startet bei etwas anderem als Push und Pull Request: …
- dependabot.yml hat keinen pip-Eintrag mehr
- dependabot.yml: pip … hebt die Untergrenze auf die neueste Fassung an

### T-FENSTER-29: Die Bauten holen das neueste Python, nicht das, was gerade daliegt

- bauen.fish: `docker build` ohne `--pull`
- appimage_bauen.fish: kein `uv python upgrade`

### T-FENSTER-30: Herunterladen ist im eigenen Fenster eingeschaltet

- fenster.py schaltet ALLOW_DOWNLOADS nicht ein; jeder Download-Knopf tut still nichts
- ALLOW_DOWNLOADS wird erst nach create_window gesetzt; der Slot ist dann schon (nicht) verbunden
- pywebview kennt … nicht mehr; der Schalter wirkt nicht

### T-FENSTER-31: Keine Telemetrie von Bibliotheken

- …: ORT_DISABLE_TELEMETRY wird nicht gesetzt
- …: ORT_DISABLE_TELEMETRY steht erst nach einem fremden Import
- AppRun setzt ORT_DISABLE_TELEMETRY nicht
- Dockerfile setzt ORT_DISABLE_TELEMETRY nicht
- core/inference.py schaltet die Telemetrie von onnxruntime nicht ab
- …: pymupdf ohne Obergrenze <2; 2.0 zieht onnxruntime mit Telemetrie nach
- …: pywebview nicht auf >=6.2.1,<7 festgelegt (…)

### T-FENSTER-32: Kein Zusatzindex: torch einzeln vom CPU-Index, alles andere von PyPI

- zu wenige Paketlisten gefunden: …
- …: «…» setzt eine weitere Paketquelle; sie gaelte fuer jedes Paket der Liste
- …: --extra-index-url
- …: torch vom CPU-Index MIT Abhaengigkeiten: …
- …: holt das torch-Rad nicht einzeln vom CPU-Index

## `tests/test_gold_ersetzen.py`

Werte in Golddokumenten ersetzen, die Spannen muessen mitwandern.

### T-GOLD-ERSETZEN-1: Laengengleiche Ersetzung laesst alle Spannen stehen

- Abbruch: …
- PHONE verschoben
- FULLNAME verschoben

### T-GOLD-ERSETZEN-2: Laengenverschiedene Ersetzung verschiebt korrekt

- Abbruch: …
- PHONE steht falsch: …
- FULLNAME steht falsch: …
- EMAIL nicht mitgewachsen: …

### T-GOLD-ERSETZEN-3: Kuerzere Ersetzung ebenso

- Abbruch: …
- PHONE verschoben

### T-GOLD-ERSETZEN-4: Halbe Ueberlappung bricht ab und schreibt nicht

- halbe Ueberlappung wurde durchgelassen
- Meldung nennt den Grund nicht: …
- Datei wurde trotz Abbruch geaendert

### T-GOLD-ERSETZEN-5: --probe schreibt nicht

- Abbruch: …
- --probe hat geschrieben

### T-GOLD-ERSETZEN-6: --zeigen-tag listet nur das gefragte Tag

- EMAIL nicht gezeigt
- PHONE mitgezeigt, obwohl nicht gefragt

### T-GOLD-ERSETZEN-7: Nicht gefundener Suchtext wird gemeldet, nicht verschwiegen

- Abbruch: …

## `tests/test_gold_markup.py`

Gold aus markiertem Text, Schritt 12.

### T-GOLD-MARKUP-1: Zerlegung: Spannen aus Markierungen

- unerwartete Befunde: …
- Text falsch: …
- 3 Spannen erwartet, …
- Spanne sitzt daneben: …

### T-GOLD-MARKUP-2: Wachen gegen Fehler in der Markierung

- haette melden muessen: …

### T-GOLD-MARKUP-3: Text ohne Markierung ergibt keine Spannen

- unerwartete Spannen
- Text veraendert

### T-GOLD-MARKUP-4: Die Verdachtswache greift nicht ueber Zeilenumbrueche

- Verdacht spannt ueber Zeilenumbruch: …
- Name auf einer Zeile nicht mehr gefunden: …
- Verdacht spannt ueber Tabulator: …
- Deutscher Satzanfang als Namensverdacht: …

### T-GOLD-MARKUP-5: Gruss- und Anredeformeln loesen keinen Namensverdacht aus

- Formeln kommen durch die Wache: …
- Frageanfaenge kommen durch: …

### T-GOLD-MARKUP-6: Ein echter Name wird davon NICHT verschluckt

- Name nicht mehr gefunden: …

### T-GOLD-MARKUP-7: HARMLOS traegt keine Doppelten

- Doppelte in HARMLOS: …

## `tests/test_goldpfad.py`

Wo die Golddokumente liegen, eine Stelle, allgemein, und laut, wenn leer.

### T-GOLDPFAD-1: MASCHERA_GOLD gesetzt, gilt

- MASCHERA_GOLD nicht befolgt: …
- Hinweis, obwohl das Verzeichnis da ist
- gold_schreiben folgt MASCHERA_GOLD nicht

### T-GOLDPFAD-2: Ohne Variable: der Datenordner des Programms

- Vorgabeort ist …, erwartet …
- der Vorgabeort ist nicht `daten("gold")`

### T-GOLDPFAD-3: Ein leerer Ort meldet sich

- leerer Ort fuer … bleibt still oder nennt die Variable nicht

### T-GOLDPFAD-4: Nie im Projektbaum

- …(…) zeigt in den Projektbaum: …

### T-GOLDPFAD-5: Unbekannte Art wird abgelehnt, nicht stillschweigend gebaut

- …('ch', …) haette abbrechen muessen

### T-GOLDPFAD-6: Der Pfad steht nur an EINER Stelle

- tools/… baut den Goldpfad selbst (…), core.pfade.gold_lesen()/gold_schreiben() benutzen

### T-GOLDPFAD-7: Kein Ordneraufbau eines Rechners im Aufloeser

- core/pfade.py enthaelt …, ein Ort, den es nur auf einer bestimmten Maschine gibt

## `tests/test_inference.py`

Test der Stufenzusammenfuehrung (SPEC §3, §4).

### T-INFERENCE-1: Schwelle aus dem Fehlerbudget

- ORG traegt denselben Wert wie ein gewoehnliches P-Tag, dann ist die Ausnahme wirkungslos und gehoert gestrichen
- ORG …: erwartet …, erhalten …
- …: erwartet …, erhalten …

### T-INFERENCE-2: Stufe-1-Override in beide Richtungen

- gueltige AHV-Nummer muss auch ohne Modell maskiert werden
- ungueltige Pruefziffer muss verworfen werden, trotz p=0.99
- Grund nicht vermerkt: …

### T-INFERENCE-3: Stufenvorrang bei Ueberlappung

- Stufe 1 muss Stufe 2 schlagen: …

### T-INFERENCE-4: Vollstaendiger Durchlauf mit Attrappe

- nackte Nachnamen muessen propagiert werden
- AHV-Nummer nicht maskiert
- Heimatort muss maskiert werden
- Gebuehr-Decoy faelschlich maskiert

### T-INFERENCE-5: Ohne Modell laeuft Stufe 1+2 weiter

- AHV-Nummer muss auch ohne Modell weg
- ohne Modell bleiben Namen im Klartext, erwartet

### T-INFERENCE-6: Zusammenfuehrung mit einem PERFEKTEN Modell

- Zusammenfuehrung verliert Spannen, der Wert steht unmaskiert da: …
- Zusammenfuehrung weitet Spannen aus, kein Leck, der Wert bleibt maskiert, aber die Grenzen wandern und der Platzhalter frisst Nachbartext: …
- … Faelle, in denen die Ansage nicht der Schleife entspricht, z. B. …

## `tests/test_injector.py`

Test des Injektors (SPEC §8, §11).

### T-INJECTOR-1: Vollstaendigkeit

- unersetzte Slots: …

### T-INJECTOR-2: Round-Trip: sitzen die Spannen zeichengenau?

- … Spannen mit Rand- oder Leerzeichenfehler
- … ueberlappende Spannen

### T-INJECTOR-3: Decoys duerfen keine Spanne beruehren

- … Decoys ueberlappen mit Spannen
- nur … % der Beispiele haben Decoys

### T-INJECTOR-4: Erzeugte Identifikatoren bestehen ihre Pruefsumme

- …: … ungueltige im Trainingsset

### T-INJECTOR-5: Kohaerenz von PLZ und Ort innerhalb einer Adresse

- … von … Adressen mit unpassender PLZ/Ort-Kombination: …

### T-INJECTOR-6: Vielfalt der Namen

- nur … verschiedene Nachnamen
- haeufigster Name macht … % aus
- mit echten Nomenklaturen erwartet man viele Namen, gefunden: …
- der Notvorrat muss divers besetzt bleiben, gefunden: …

### T-INJECTOR-7: Gegenprobe: Recognizer gegen die Wahrheit des Injektors

- …: Recognizer findet nur … % der gesetzten

### T-INJECTOR-8: Schlaegt der Recognizer auf Decoys an?


### T-INJECTOR-9: Beide Namensreihenfolgen kommen vor

- keine einzige Vorlage schreibt Register-Reihenfolge
- keine einzige Vorlage schreibt natuerliche Reihenfolge
- Reihenfolge zu einseitig: … % Register-Reihenfolge

## `tests/test_labelvertrag_eingefroren.py`

Der Labelvertrag ist EINGEFROREN.

### T-LABELVERTRAG-EINGEFROREN-1: Der Hash des Labelvertrags

- Der Labelvertrag hat sich geaendert. eingefroren: … jetzt: … Damit ist JEDES bisher trainierte Modell unbrauchbar, der Ausgabekopf hat eine andere Groesse. War das Absicht? Dann den Grund festhalten, das Modell neu trainieren und den Hash HIER nachfuehren.

### T-LABELVERTRAG-EINGEFROREN-2: Umfang

- … Tags statt …
- … Labels statt …

### T-LABELVERTRAG-EINGEFROREN-3: Was NICHT eingefroren ist, bleibt aenderbar

- Tag mit Budget, aber ohne Schwelle: …
- eine Schwelle stammt weder aus einem Budget noch aus einer eingetragenen Ausnahme
- CANTON ist tag_only, auch `action` ist nicht eingefroren

### T-LABELVERTRAG-EINGEFROREN-4: Benutzerspezifische Tags stehen AUSSERHALB

- X_-Tags im Labelvertrag: …

## `tests/test_langes_dokument.py`

Lange Dokumente: das Modell muss den SCHLUSS sehen, nicht nur den Kopf.

### T-LANGES-DOKUMENT-1: Der Quelltext schaltet die Abschneidung ab

- OnnxScorer schaltet die Abschneidung des Tokenizers nicht ab, alles ab Token 512 sieht das Modell nie
- OnnxScorer holt die Offsets MIT Sondertoken, dann zeigen sie auf Stellen, die es im Text nicht gibt
- OnnxScorer setzt die Sondertoken nicht je FENSTER. Werden sie einmal fuer den ganzen Text gesetzt und danach geschnitten, bekommt jedes Fenster ausser dem ersten eine Eingabeform, die das Modell im Training nie gesehen hat

### T-LANGES-DOKUMENT-2: Der Tokenizer schneidet den Text nicht mehr ab

- der Tokenizer liefert … Token, abgeschnitten
- roh …, im Scorer …, no_truncation wirkt nicht

### T-LANGES-DOKUMENT-3: Ein Name am SCHLUSS wird gefunden

- das Vorkommen bei Zeichen … wurde NICHT gefunden, getroffen: …. Genau hier steht bei einer Mail die Signatur
- nur … von 3 Vorkommen gefunden

### T-LANGES-DOKUMENT-4: Beide Laeufer sehen dasselbe

- … findet am Schluss nichts

## `tests/test_mail.py`

Der Mail-Einleser: nur der Textinhalt, und nichts, was nur so aussieht.

### T-MAIL-1: Eine gewoehnliche Mail: Kopf und Rumpf, sonst nichts

- der Absender fehlt im Text
- der Betreff fehlt im Text
- der Rumpf fehlt im Text
- technische Kopfzeilen stehen im Text
- unerwartete Hinweise: …

### T-MAIL-2: ⚠️ Binaeres nach dem Textende wird abgeschnitten UND gemeldet

- der lesbare Teil ist mit weggefallen
- der Binaerteil steht noch im Text: …
- es wurde abgeschnitten, aber nicht gemeldet, ein leerer Befund ist keine Entwarnung
- es blieben … Zeichen stehen, erwartet unter 400

### T-MAIL-3: Ein Anhang wird uebersprungen, der Text bleibt

- der Textteil fehlt
- der Anhang steht im Text
- der uebersprungene Anhang wird nicht gemeldet

### T-MAIL-4: HTML wird entkleidet und als solches gemeldet

- der HTML-Text fehlt
- die HTML-Entitaet wurde nicht aufgeloest
- die Auszeichnung steht noch im Text
- der HTML-Rueckfall wird nicht gemeldet

### T-MAIL-5: ⚠️ Eine Mail OHNE Textteil erfindet keinen

- eine Mail ohne Textteil wird nicht gemeldet: …
- aus einem Bild wurde Text: …
- der fehlende Rumpf wird nicht gemeldet

### T-MAIL-6: ⚠️ Ein Outlook-.msg wird als OLE2 erkannt und gelesen

- …: ein kaputtes OLE2 wurde gelesen
- …: die Absage sagt nicht, was zu tun ist: …
- …: unerwartete Ausnahme …: …
- der UTF-16-Rumpf kommt nicht zurueck
- der Betreff kommt nicht zurueck
- eine fehlende Eigenschaft liefert nicht leer
- die 8-Bit-Fassung kommt falsch zurueck: …
- der Betreff steht nicht im Text: …
- der Absender fehlt
- der Rumpf fehlt
- unerwartete Hinweise: …
- der fehlende Textrumpf wird nicht gemeldet: …
- der Betreff ging mit verloren
- `serve.py` faengt `SystemExit` aus den Einlesern nicht, eine Absage wird dort zur 500

### T-MAIL-7: Echter Text wird NICHT angetastet

- … wurde angetastet: … Zeichen weg

### T-MAIL-8: ⚠️ .mbox, das dritte Format auf der Liste, nie geprueft

- eine mbox mit zwei Nachrichten ergab …
- das Format heisst nicht mbox
- beide Nachrichten tragen dieselbe Kennung
- die Nachrichten sind nicht durchnummeriert: …
- der Betreff steht nicht in der Kennung
- die Rumpftexte sind vertauscht oder fehlen
- die Absenderadresse fehlt im Text, sie waere unmaskierbar
- eine leere mbox erfindet Nachrichten
- eine .eml unter .mbox-Namen wird stillschweigend gelesen, dann haengt das Ergebnis am Dateinamen statt am Inhalt
- filter_document laeuft ueber eine leere Sammeldatei wortlos hinweg
- der Server meldet eine textlose Datei nicht mehr

## `tests/test_masking.py`

Test von Maskierung, Propagation und Rückführung.

### T-MASKING-0: Ohne eigenen Punkt

- Rueckfuehrung ist nicht zeichengenau

### T-MASKING-1: Round-Trip zeichengenau: …


### T-MASKING-1B: Jeder Platzhalter des Packs passt auf PLACEHOLDER_RE

- nicht rueckwandelbar: …
- … wird faelschlich als Platzhalter gelesen
- zu wenig propagiert: …
- nacktes 'Meier' steht noch im maskierten Text

### T-MASKING-2: Propagation: … zusaetzliche Spannen, kein 'Meier' mehr im Text: …

- Meier-Varianten haben verschiedene Gruppennummern: …
- Rita Bertschi muesste eine eigene Nummer haben

### T-MASKING-3: Koreferenz: Meier-Varianten …, zweite Person …

- Heimatort steht noch im Klartext
- Heimatort-Platzhalter fehlt
- Wohnort wurde nicht maskiert

### T-MASKING-4: Heimatort und Wohnort beide maskiert: …

- Rechtsverweis wurde angetastet

### T-MASKING-5: Rechtsverweis unberuehrt: OK

- unbekannter Platzhalter muesste stehen bleiben
- strict=True haette werfen muessen

### T-MASKING-6: Erfundener Platzhalter: bleibt stehen, strict wirft: …

- Round-Trip ueber Zeilenumbruch fehlgeschlagen

### T-MASKING-7: Zeilenumbruch in Entitaet: …

- … Abweichung(en) zwischen bisect und Durchlauf

### T-MASKING-8: Belegung: bisect == Durchlauf in 1200 Faellen: …

- propagate hat gar nicht gesucht
- … Suchlaeufe fuer … verschiedene Nadeln, dieselbe Nadel wird mehrfach durch den ganzen Text gejagt

### T-MASKING-9: Jede Nadel einmal gesucht: … Laeufe, … Nadeln: …


## `tests/test_modell.py`

Das Nachladen des Modells, ohne Netz, ohne Fenster, ohne 1,2 GB.

### T-MODELL-1: Ein vollstaendiges Modell wird gefunden, ein halbes nicht

- ein LEERES Verzeichnis gilt als Modell
- vier von fuenf Dateien gelten als vollstaendiges Modell, dann startet das Werkzeug in ein Modell hinein, das es nicht gibt
- fuenf von fuenf gelten NICHT als Modell

### T-MODELL-2: Geholt wird nur auf Befehl, und dann vollstaendig

- nach dem Holen fehlt etwas
- … kam anders an, als es abgeschickt wurde
- die Anzeige sah nicht alle Dateien: …

### T-MODELL-3: Eine falsche Pruefsumme bleibt NICHT liegen

- eine falsche Pruefsumme wurde angenommen
- abgewiesen, aber mit falschem Grund: …
- die verworfene Datei liegt trotzdem da
- eine `.teil`-Datei ist liegengeblieben
- das halbe Verzeichnis gilt als fertiges Modell, beim naechsten Start liefe die Erkennung darauf los

### T-MODELL-4: Eine fehlende Quelle bricht ab, statt Leeres abzulegen

- eine unerreichbare Quelle wurde nicht gemeldet
- `.teil` liegengeblieben
- leeres Verzeichnis gilt als Modell

### T-MODELL-5: Ein Abbruch mittendrin laesst nichts Halbes zurueck

- der Abbruch wurde nicht beachtet
- anderer Grund als Abbruch: …
- `.teil` nach Abbruch liegengeblieben
- nach Abbruch gilt es als Modell

### T-MODELL-6: Ein zweiter Anlauf holt nur, was fehlt

- der zweite Anlauf blieb unvollstaendig
- die grosse Datei wurde ein zweites Mal geholt, obwohl sie stimmte

### T-MODELL-7: `pruefe()` findet eine veraenderte Datei

- ein sauberes Modell wird bemaengelt: …
- eine veraenderte Datei faellt nicht auf

### T-MODELL-8: Das Manifest im Pack ist lesbar und deckt alle Pflichtdateien

- das Manifest kennt nicht alle Pflichtdateien: …
- die Quelle hat keine Stelle fuer den Dateinamen: …
- die Quelle zeigt nicht auf einen festen Commit: …
- das Manifest meldet … Bytes, das ist kein Modell dieser Bauart

### T-MODELL-9: Der Ort ist NICHT ~/.config/

- das Modell landet unter .config: …
- das Modell landet nicht im Datenverzeichnis: …

### T-MODELL-9B: Ein Netzfehler sagt, wo zu suchen ist

- …: …
- HTTP … steht nicht im Satz: …
- ein Ausfall ohne HTTP-Antwort wird nicht als solcher benannt
- 404 bekommt denselben Satz wie 401, dann sagt er nichts

### T-MODELL-9C: Jeder geworfene Schluessel steht in allen vier Sprachen

- core/modell.py wirft keine Schluessel mehr, dann steht die Uebersetzung wieder still
- …: fuer … gibt es keinen Satz, der Anwender saehe den deutschen Rohtext
- fuer … gibt es einen Satz, aber niemand wirft sie
- HTTP … -> …, erwartet …
- der deutsche Satz zu HTTP … nennt die Zahl nicht

### T-MODELL-10: Die Windows-Wege laufen, auf dieser Maschine nachgeprueft

- …: es laeuft schon, bevor etwas horcht
- …: der Horcher kam nicht auf
- …: der laufende Horcher wird nicht erkannt, dann gehen zwei Fenster auf
- …: das Zeichen kam nicht an, das erste Fenster kaeme nicht nach vorne
- der Windows-Weg schreibt keine Portnummer hin
- eine Portdatei ohne Horcher gilt als laufende Anwendung
- die Leiche wurde nicht weggeraeumt, `horche()` koennte danach nicht binden

### T-MODELL-11: Die Orte stimmen auf beiden Plattformen

- Windows: die Einstellungen landen nicht in APPDATA: …
- Windows: die Einstellungen landen in ~/.config, dort sucht kein Windows-Programm, und keine Sicherung erfasst es
- Windows: das Modell landet im wandernden Profil: …
- XDG_CONFIG_HOME wird unter Windows ignoriert, dann greift keine Wache mehr an den Einstellungen vorbei

### T-MODELL-12: Ein Modell wird nur aus safetensors geladen

- …: from_pretrained ohne use_safetensors=True
- nur … Aufrufe gefunden, 2+ erwartet, dann sucht die Wache an der falschen Stelle

## `tests/test_oberflaeche.js`

Die Oberflaechenlogik gegen eine strenge DOM-Attrappe.

### T-OBERFLAECHE-0: Ohne eigenen Punkt

- kein Horcher auf ablage/drop
- Element … nicht auffindbar
- kein Horcher auf …/…

### T-OBERFLAECHE-1: Alle Knoepfe sind verdrahtet

- … hat keinen Horcher

### T-OBERFLAECHE-2: Der Startbildschirm wird verborgen, nicht entfernt

- Startbildschirm wurde entfernt statt verborgen
- start-lage ist nach dem Start nicht mehr erreichbar

### T-OBERFLAECHE-3: «Beispiel» fuellt Spalte 1 und schaltet MASKIEREN frei

- Zeichenzahl steht auf …
- MASKIEREN bleibt gesperrt

### T-OBERFLAECHE-4: MASKIEREN ruft die Kette, nicht den Browser

- keine Anfrage an /api/anonymisieren
- Text nicht mitgeschickt
- Woerterbuch nicht angefordert

### T-OBERFLAECHE-5: Kein Vokabularschalter, keine Plakette «Lokal»

- der Schalter des Vokabulars ist wieder im HTML
- die Plakette «Lokal» steht wieder an einer Kachel

### T-OBERFLAECHE-6: Jeder Lauf verlangt ein Woerterbuch

- die Anfrage verlangt kein Woerterbuch

### T-OBERFLAECHE-7: «Kopieren und öffnen» sendet nichts, sondern oeffnet

- «Kopieren und öffnen» hat eine Anfrage an den Server geschickt
- window.open …x aufgerufen statt einmal
- keine Fenstergroesse angegeben
- ohne noopener geoeffnet
- Zwischenablage traegt nicht Prompt und Anhang

### T-OBERFLAECHE-8: Spalte 3 ist immer da, kein Ein- und Ausklappen mehr

- Schiene oder Klappknopf wieder im HTML
- das Blatt kennt die Klappe wieder
- die Uebernahme setzt wieder `drei`

### T-OBERFLAECHE-9: Zurueck geht es ueber 04, ohne Schalter «Weg zurück»

- der Schalter «Weg zurück» oder sein Feld ist wieder im HTML
- kein Aufruf von /api/zurueckwandeln
- Bereich 05 bleibt leer

### T-OBERFLAECHE-10: Nicht zugeordnete Platzhalter werden ANGEZEIGT

- der offene Platzhalter steht nirgends in der Anzeige
- der Hinweis des Servers wird verschwiegen

### T-OBERFLAECHE-11: Der Sendeknopf flackert nicht zwischen drei Texten

- nach dem Klick steht «…»
- Neuzeichnen ueberschreibt zu «…»

### T-OBERFLAECHE-12: Einstellungen: oeffnen, Tags, Regeln

- Einstellungen gehen nicht auf
- die YAML-Regeln werden nicht geladen
- CANTON laesst sich umlegen, obwohl es tag_only ist
- NATIONALITY ist nicht als bsPD gekennzeichnet
- der Farbpunkt in der Tagwolke ist ungefaerbt
- bsPD ohne ⚠, der gestrichelte Rand las sich wie ein hoeherer Knopf
- die Bezeichnung fehlt im Knopf, 45 Abkuerzungen sind keine Wahl
- … Gruppen gezeichnet, mindestens 2 erwartet

### T-OBERFLAECHE-13: Abgelehnte Regeln werden GEMELDET, nicht verschluckt

- der Grund steht nicht da: …
- die Ablehnung sieht aus wie Erfolg

### T-OBERFLAECHE-14: Kontextmenue: Maske entfernen und Tag setzen

- die Attrappe liefert keinen Platzhalter zum Korrigieren
- maskeEntfernen meldet Misserfolg
- der Platzhalter steht noch im Text
- der Originalwert wurde nicht eingesetzt
- der Woerterbucheintrag lebt weiter
- wertMaskieren meldet Misserfolg
- der Wert steht noch im Klartext
- keine Fundstelle mit der Quelle «manuell»
- eine Handmaskierung traegt ein Vertrauen

### T-OBERFLAECHE-15: Maskieren trifft nur ganze Woerter

- «Berner» wurde zerlegt: …
- beide «Bern» haetten ersetzt werden muessen: …
- «Meiers» wurde zerlegt: …

### T-OBERFLAECHE-16: Mehrteilige Namen gehen als Ganzes

- nicht maskiert: …
- Reste geblieben: …

### T-OBERFLAECHE-17: Der Rand zeigt auf Arbeit, nicht auf Sicherheit

- model ist nicht ausgezogen: …
- checksum ist nicht zurueckgenommen: …
- regex ist nicht zurueckgenommen: …
- manuell hebt sich nicht ab: …

### T-OBERFLAECHE-18: Ein Platzhalter wird nie zweimal vergeben

- ein Platzhalter kommt doppelt vor

### T-OBERFLAECHE-19: Mehrfaches Zeichnen bricht nicht ab


### T-OBERFLAECHE-20: Das Vokabular ueberlebt einen Rundlauf

- Kennung fehlt in der Datei
- der maskierte Text fehlt in der Datei
- … statt … Eintraege
- der maskierte Text kam nicht mit
- ein Wert hat sich beim Rundlauf veraendert
- alte Spannen ueberlebten das Einlesen

### T-OBERFLAECHE-21: Eine fehlerhafte Datei wird GANZ abgewiesen

- … wurde durchgelassen
- eine gueltige Datei wurde abgewiesen
- VOK_PH_RE merkt sich lastIndex
- Vornamensform abgewiesen
- Benutzerregel abgewiesen
- Anhang durchgelassen

### T-OBERFLAECHE-22: Kein Beschriftungsschluessel doppelt

- I18N nicht gefunden
- … Sprachen gefunden, 4 erwartet
- …: doppelter Schluessel …

### T-OBERFLAECHE-23: Vorlagen: filtern, waehlen, loeschen

- … Vorlagen geladen, 1 erwartet
- Vorlage fehlt in der Liste
- kein Papierkorb neben dem Eintrag
- kein Hinweis, dass nichts passt
- das Feld selbst wurde nicht gefuellt
- die Wahl wurde nicht gemerkt, sie ist der Namensvorschlag beim naechsten Speichern
- Menue blieb offen

### T-OBERFLAECHE-24: Ein neuer Dienst ist SOFORT im Sendeknopf

- Menue hat … Eintraege, … erwartet

### T-OBERFLAECHE-25: Abgelehnte Einstellungen schliessen den Dialog NICHT

- Dialog schloss trotz abgelehnter Einstellungen
- Dialog schloss auch mit gueltigem Stand nicht

### T-OBERFLAECHE-26: Jeder Tag hat eine Gruppe

- … Tags zugeordnet, 45 erwartet
- Tag in zwei Gruppen: …

### T-OBERFLAECHE-27: Der gewaehlte Dienst wird sofort gemerkt

- Dienst ist …
- der Wechsel wurde nicht gesichert

### T-OBERFLAECHE-28: Keine festen Pixel fuer Groessen im CSS

- … feste Groesse(n): …
- … Wortmarken in --font-marke, 5 erwartet
- die Wortmarke steht nicht mehr in Barlow Condensed
- die Wurzelgroesse haengt nicht an --skala

### T-OBERFLAECHE-29: Ablegen LIEST, es maskiert nicht

- Ablegen hat trotzdem maskiert (/api/anonymisieren gerufen)
- Spalte 1 traegt nicht den gelesenen Text
- Bereich 02 ist gefuellt, obwohl nur gelesen wurde
- MASKIEREN ist nach dem Ablegen nicht bereit

### T-OBERFLAECHE-30: Getippter Text ueberlebt ein Ablegen nicht ungefragt

- keine Rueckfrage vor dem Verwerfen
- der getippte Text ist weg, obwohl abgelehnt wurde
- nach Ja wurde nicht gelesen

### T-OBERFLAECHE-31: Die Oberflaeche schickt keine Datei mehr an die Kette

- eine Datei geht noch an /api/anonymisieren
- Stellen bauen ein FormData, genau eine erwartet

### T-OBERFLAECHE-32: Die Fassung bleibt sichtbar, und ohne Attrappe

- die nachgebaute Titelleiste ist zurueck
- der APP/WEB-Umschalter ist zurueck, er blendete nur die Attrappe ein und aus
- kein Element `version` mehr im HTML
- im HTML steht eine feste Fassungsnummer

### T-OBERFLAECHE-33: Zahnrad und Einklappen fluchten am rechten Rand

- Innenabstand nicht gefunden: Kopfzeile …, Bereich …
- Kopfzeile haelt rechts …, .bereich-kopf …, das Zahnrad flieht nicht mehr mit «Einklappen»
- das Zahnrad steht wieder vor den Sprachknoepfen, also nicht aussen

### T-OBERFLAECHE-34: Der Knopf «Vokabular einpflegen» steht links

- der Fuss von 04 ist nicht linksbuendig
- `.weit` schiebt den Knopf weiter nach rechts

### T-OBERFLAECHE-35: Beim Ziehen dunkelt die Seite ab, die Flaeche bleibt hell

- kein Element `ziehschleier` im HTML
- kein Horcher auf dem Dokument fuer `dragover`
- `dragover` mit Datei wird nicht verhindert
- der Schleier bleibt verborgen
- der Koerper traegt die Klasse `zieht` nicht
- auch gezogener Text wird verhindert, das ist zu viel
- ein Ablegen neben der Flaeche wird nicht verhindert, der Browser oeffnet die Datei und die Oberflaeche ist weg
- der Schleier bleibt nach dem Ablegen
- die Klasse `zieht` bleibt am Koerper haengen
- der Schleier faengt Zeiger ab
- `[hidden]` ist nicht mit `display: none` abgesichert, eine spaetere `display`-Regel schlaegt es sonst

### T-OBERFLAECHE-36: Der Fortschritt zeigt Gemessenes, nicht Gefuehltes

- niemand fragt /api/fortschritt
- der Fortschritt wird mit setInterval geholt
- kein Element `lauf` im HTML
- der Balken bleibt verborgen
- ohne Zahl taeuscht der Balken eine Strecke vor
- mit Zahl wandert der Balken immer noch
- statt 23%
- restWort rundet auf null Sekunden
- der Balken bleibt nach dem Lauf stehen
- eine spaete Meldung macht den Balken wieder sichtbar, genau der Fehler beim Beispieltext
- auch eine spaete Meldung MIT Zahlen zeigt den Balken wieder
- … steht …x, viermal erwartet

### T-OBERFLAECHE-37: Leeren und Kopieren sind sichtbar und sagen, was sie tun

- die Knoepfe stehen wieder auf weissem Grund
- der Rand ist wieder zu blass
- kein gruenes Zeichen beim Kopieren
- kein rotes Zeichen beim Leeren
- nur … Knoepfe im Feld gefunden
- … leert, traegt aber nicht \`loeschen\`
- … kopiert, traegt aber nicht \`kopieren\`
- … oeffnet das Feld, traegt aber nicht `bearbeiten`
- … faerbt sich rot, leert aber nichts
- … faerbt sich gruen, oeffnet aber nichts
- «Bearbeiten» traegt keine eigene Farbe
- `.imfeld.bearbeiten.aktiv` steht vor `.imfeld.aktiv`, bei gleicher Spezifitaet gewinnt dann das Grau
- «Bearbeiten» reagiert nicht auf das Ueberfahren
- «Bearbeiten» kehrt beim Ueberfahren um wie der Leerknopf, das ist dort eine Warnung, und hier wird nichts geloescht

### T-OBERFLAECHE-38: Die dritte Spalte fuellt sich nicht von selbst

- es wurde gar nicht maskiert
- der maskierte Text steht in Spalte 3, ohne dass jemand uebernommen hat
- der gemessene Wert landet nicht in `--rollbalken`
- nach der Uebernahme steht der Text immer noch nicht da
- nach einem neuen Lauf steht der alte Text weiter in Spalte 3
- «Neu» nimmt die Uebernahme nicht zurueck
- … Sprachen mit hinausLeer statt 4

### T-OBERFLAECHE-39: Der Dienstname im Sendeknopf ist fett, und kein HTML

- … fette Teile im Sendeknopf statt genau einem
- der fette Teil ist leer
- nur … Stueck(e) im Knopf, der Text um den Namen fehlt
- es gibt wieder eine `innerHTML`-Stelle in der Oberflaeche

### T-OBERFLAECHE-40: Zwei Stufen: drei Spalten oder alles untereinander

- die feste Mindestbreite von 980 px ist zurueck
- … Umbruchpunkte, mindestens 1 erwartet
- ein Umbruchpunkt steht in … statt in em
- dem Kasten … fehlt die Kennung
- … hat order …, … erwartet
- nebeneinander wird gesprungen, dort sieht man den naechsten Kasten ohnehin
- untereinander wird NICHT gesprungen (…)
- die Bewegung haengt wieder an `behavior: "smooth"`
- es gibt keine eigene Bewegung mehr
- die Bewegung bremst nicht ab (kubisch auslaufend)
- ohne `requestAnimationFrame` gibt es keinen Rueckfall
- der Klappknopf des Vokabulars ist wieder im HTML
- das Blatt kann das Vokabular wieder zuklappen

### T-OBERFLAECHE-41: «Neu» leert das GANZE Formular, und fragt vorher

- «Neu» fragt nicht nach
- trotz Nein wurde der Prompt geleert
- Spalte 1 nicht geleert
- der maskierte Text blieb stehen
- der Prompt blieb stehen
- die Antwort aus 04 blieb stehen
- der finale Text blieb stehen
- «Prompt & maskierter Text» blieb aufgeklappt
- die Hinweistafel in 02 blieb offen
- offene Rubriken im Rechtsklickmenue ueberleben «Neu»
- Suchwort oder Filter ueberleben «Neu»
- die vergroesserte Kachel bleibt nach «Neu» gross
- allesLeeren() setzt Suchwort oder Vorlagenfilter nicht zurueck
- die gewaehlte Vorlage steht noch im Feld
- das Prompt-FELD wurde nicht geleert, nur der Zustand
- die Vorlagenliste ist verschwunden
- die Regel fuer den unteren «Neu» ist zu unspezifisch, `button.tat` gewinnt dann
- der Knopf unten leert nicht dasselbe wie der oben
- nach «Neu» steht die Seite auf … statt oben

### T-OBERFLAECHE-42: Der Speichern-Knopf schrumpft, ohne stumm zu werden

- es gibt keinen Behaelter, dann misst die Regel das Fenster statt den Platz

### T-OBERFLAECHE-43: Der Abstand der Feldknoepfe haengt am Rollbalken

- `.feldknoepfe` gibt es nicht mehr
- die alte geratene Zahl ist zurueck
- die Breite wird nicht mehr gemessen

### T-OBERFLAECHE-44: Die Kopfzeile wirft einen Schatten, sobald gerollt ist

- niemand horcht auf das Rollen des Rasters
- am Seitenanfang wirft die Kopfzeile schon einen Schatten
- nach dem Rollen fehlt der Schatten
- der Schatten bleibt haengen, wenn wieder ganz oben
- gestapelt fehlt der Schatten nach dem Rollen der Seite
- gestapelt bleibt der Schatten haengen
- die Klasse `gerollt` wirft keinen Schatten
- gestapelt rollt weiterhin das Raster, der Fuss bleibt kleben
- die Kopfzeile hat keinen Stapelkontext, der Schatten liegt dann unter dem Inhalt

### T-OBERFLAECHE-45: Jeder Knopf mit Zeichen und Wort hat einen Tooltip

- nur … Knoepfe gefunden, die Attrappe liefert wohl keine
- … Knoepfe ohne Tooltip: …

### T-OBERFLAECHE-46: Gedreht wird nur, was eine Richtung meint

- es wird wieder JEDES Zeichen in einem `.tat`-Knopf gedreht
- die Drehung haengt nicht an `.richtung`
- … Zeichen als Richtung ausgezeichnet, 3 erwartet
- der Pfeil des Ausklappmenues gilt wieder als Richtungspfeil

### T-OBERFLAECHE-47: Hinweise des Servers folgen der Sprache der Oberflaeche

- unter it steht der deutsche Satz
- kein Rueckfall auf `text`
- alte Form verschwindet
- Schluessel nicht lesbar

### T-OBERFLAECHE-48: Das Kontextmenue bleibt beim Aufklappen, wo es ist

- die Hoechstbreite kommt nicht aus dem CSS, zwei Verwalter
- das Neuzeichnen beim Aufklappen haelt die Lage nicht fest
- `lageBehalten` wird nicht ausgewertet
- nach dem Festnageln wird nicht neu gemessen
- das Feldmenue erbt die Breite des Tagmenues

### T-OBERFLAECHE-49: Das Feldmenue trifft ein Wort auch ohne Markierung

- Wortanfang trifft nicht
- Wortende trifft nicht
- das getroffene Wort wird nicht markiert, keine Rueckmeldung
- die Sinnbilder werden nicht ueber createElementNS gebaut

### T-OBERFLAECHE-50: Der Hinweis am Sendeknopf ist immer sichtbar

- der lange Satz steht nicht im Tooltip
- der Tooltip kommt nicht aus `onlineWarnung`
- am Knopf steht nicht «Verlaesst dein Geraet»
- der Hinweis wird wieder weggeklappt

### T-OBERFLAECHE-51: Die Hoehe misst, was auf dem Handy wirklich da ist

- body misst nicht in dvh, oder ohne Rueckfall auf vh
- Reihenfolge der Rueckfaelle stimmt nicht
- der unterste Fuss haelt keinen Abstand zur Gestenleiste

### T-OBERFLAECHE-52: Der Gruppenkopf teilt seinen Klassennamen mit niemandem

- der Gruppenkopf traegt wieder `offen`
- das CSS kennt `aufgeklappt` nicht
- die alte Regel auf `.offen` steht noch da
- die rote Warnbox hat ihren Rand verloren, dann stimmt die Erklaerung von 8.6 nicht mehr

### T-OBERFLAECHE-53: Der reservierte Rollbalkenstreifen steht nur, wo er wirkt

- das Tagmenue hat keinen Streifen, dann springt es beim Aufklappen wieder
- die Klasse wird nicht gesetzt und wieder weggenommen
- die Vorlagenliste kennt `rollend` nicht

### T-OBERFLAECHE-54: Der Rollbalken laesst die runden Ecken frei

- die Laufbahn ist nicht durchsichtig
- der Griff ist nicht gerundet
- Firefox bekommt keine durchsichtige Laufbahn
- die Balkenbreite wurde angetastet, `--rollbalken` stimmt dann nicht mehr
- `scrollbar-width: thin` aendert die Breite in Firefox

### T-OBERFLAECHE-55: Bereich 05 ist ein Feld, und was drin steht, wird kopiert

- Bereich 05 ist kein Textfeld
- Bereich 02 ist nicht anwaehlbar
- `finalText()` fehlt
- Herunterladen nimmt nicht den Feldinhalt
- Kopieren nimmt nicht den Feldinhalt
- der doppelte Kopieren-Knopf in 05 ist wieder da

### T-OBERFLAECHE-56: Die Meldungen unter 02 stehen auf einer Zeile

- die Meldungen werden nicht zusammengezogen
- die Warnung hat ihre eigene Zeile verloren
- die Textsuche auf den Satzanfang steht wieder da
- es wird nicht nach dem Schluessel gefragt

### T-OBERFLAECHE-57: Das Burgermenue holt seine Adressen aus EINER Datei

- die Adressdatei ist leer
- … fehlt in …
- die Oberflaeche weiss nicht, wo sie laeuft
- der Eintrag `selbst` haengt nicht am eigenen Fenster
- … hat kein Zeichen in adressen.json
- … zeigt auf das Zeichen «…», das es in MENUEBILDER nicht gibt
- das Zeichen «…» wird von keinem Eintrag benutzt
- das Zeichen «…» hat keine Pfade
- «…» traegt etwas anderes als einen Pfad: …
- das Burgermenue baut keine <…> mehr, die Wache ist alt
- <…>-Eintraege im Burgermenue faerben sich beim Ueberfahren nicht

### T-OBERFLAECHE-58: Die rote Spalte spricht rot, ausser bei den Feldknoepfen

- der Farbblock der roten Spalte fehlt
- der aktive Rahmen traegt wieder eine feste Farbe
- ohne Spalte fehlt die gruene Vorgabe fuer --fokus
- fehlt
- die Feldknoepfe werden mitgefaerbt, sie sollen grau bleiben
- -Regel nimmt den gruenen Knopf nicht aus
- die hover-Regel nimmt den roten Hauptknopf nicht aus

### T-OBERFLAECHE-59: Der Startbildschirm richtet die zwei Zeilen aneinander aus

- die zwei Zeilen im Startbildschirm sind nicht linksbuendig
- der Satz im Startbildschirm fehlt

### T-OBERFLAECHE-60: Jeder deutsche Text im HTML hat einen Setzer im Skript

- Platzhalter ohne Setzer: …, …

### T-OBERFLAECHE-61: Jedes Schreibfeld hat ein Rechtsklickmenue

- niemand horcht auf den Rechtsklick
- bekommt kein Menue
- ein Klick auf ein Kind des Feldes findet das Feld nicht
- bekommt faelschlich ein Menue
- der maskierte Text bekommt das falsche Menue
- ein schreibgeschuetztes Feld bekommt ein Menue, das nichts kann
- im eigenen Fenster oeffnet der Rechtsklick kein Menue
- das Browsermenue wird nicht unterdrueckt, es kaemen zwei
- im Browser kommt unser Menue, und sein «Einfuegen» kann dort nicht wirken
- im Browser wird das native Menue unterdrueckt, damit ist das einzige funktionierende Einfuegen weg
- `feldSetzen` gibt den Fokus nicht ans Feld zurueck

### T-OBERFLAECHE-62: Hilfe und Impressum liegen im Paket, nicht im Netz

- … fehlt in adressen.json
- … fuehrt nicht auf den Einseiter «…», sondern auf …
- … traegt noch eine Adresse nach draussen
- die Seite «…» fehlt
- … kennt … statt der vier Bediensprachen
- …/… ist leer
- …: … und … tragen denselben Text
- …/… hat die Blockfolge … statt …
- seiteZeigen() fehlt
- Kopfstueck oder Zeichner stehen nicht mehr unter der Wache
- der Einseiter wird ueber innerHTML gebaut
- die Hilfe geht nicht auf
- die Hilfe hat keinen Titel
- die Hilfe ist leer
- …: das Kopfstueck steht nicht zuoberst
- …: keine Maske im Kopfstueck
- …: die Wortmarke lautet «…»
- …: kein Untertitel im Kopfstueck
- …: der Untertitel steht nicht auf zwei Zeilen
- nur … fette Stellen in der Hilfe, Knoepfe und Befehle sollen hervorstehen
- im fetten Stueck steht Markup: …
- der Fliesstext der Hilfe ist beim Fettsetzen abhanden gekommen
- die Seite laesst sich nicht schliessen

### T-OBERFLAECHE-63: Bereich 02 laesst sich von Hand korrigieren

- die Rueckwandlung sucht die Platzhalter nicht mehr im Text, dann traegt das Bearbeiten von Bereich 02 nicht mehr
- zeichneMaskiert() baut die Plaketten nicht mehr aus dem Text
- das Schreibfeld in Bereich 02 fehlt
- Bereich 02 wird ueber contenteditable bearbeitet
- der Knopf «Bearbeiten» hat keinen Horcher
- der Knopf schaltet nicht ein
- das Schreibfeld bekommt den maskierten Text nicht
- beide Ansichten stehen gleichzeitig da
- der Knopf schaltet nicht aus
- nach dem Bearbeiten stehen … Plaketten statt 1

### T-OBERFLAECHE-64: Was das Skript versteckt, versteckt auch das CSS

- nur … versteckte Elemente gefunden, die Wache sieht das Skript nicht mehr
- «…» wird im Skript versteckt, aber … setzt `display:`, das Attribut `hidden` verliert dagegen, und das Element bleibt stehen

### T-OBERFLAECHE-65: Der Sprung landet, wo der Kasten steht

- der Sprung verdoppelt den Rollstand: … statt 800
- der Sprung landet auf … statt auf 1100
- der Sprung nach oben landet auf … statt auf 300
- mit klebender Kopfzeile landet der Sprung auf … statt auf 1010 (1100 minus 90 Kopfzeile)
- springeZu() unterscheidet die Rollwurzel nicht mehr
- die Rollwurzel wird wieder wie ein rollendes Element gerechnet
- laufen() nicht gefunden
- laufen() springt …-mal statt genau einmal, der Sprung gehoert VOR den Lauf, nicht dahinter

### T-OBERFLAECHE-66: Der Speichern-Knopf kuerzt in zwei Stufen

- der Speichern-Knopf fehlt
- der Speichern-Knopf hat kein Zeichen
- der Speichern-Knopf traegt … Textstueck(e) statt zwei, dann gibt es keine mittlere Stufe
- die Dialogfusszeile ist kein Behaelter, die Stufen greifen nicht
- der Speichern-Knopf steht nicht in der Fusszeile
- … Stufe(n) statt zwei
- die Stufen stehen in der falschen Reihenfolge: …

### T-OBERFLAECHE-67: Die Fusszeile bricht zwischen den Aussagen, nicht in ihnen

- …: die Fusszeile spricht noch von einem Upload, …
- …: die Fusszeile hat … Stuecke statt drei
- die deutsche Fusszeile nennt die Dienste gar nicht mehr
- die Fusszeile steht in … Knoten statt in drei, dann bricht sie wieder irgendwo
- die Stuecke tragen ihre Klasse nicht
- die Stuecke halten nicht zusammen
- die Fassungsnummer bricht wieder in «v0.9.5-» und «beta»

### T-OBERFLAECHE-68: Markdown-entwertete Platzhalter werden zurueckgeholt

- entwertet zurueckgeholt: …
- … statt 2 gemeldet
- ein Rueckstrich ausserhalb eines Platzhalters wurde angefasst: …
- es wurde etwas gemeldet, wo nichts war
- ein heiler Platzhalter wurde angefasst
- ein heiler Text wird als kaputt gemeldet
- entwertete Reste nicht erkannt: …
- das Feld traegt den reparierten Text nicht
- zerschlagener Platzhalter nicht ergaenzt: …
- gemeldet wurde …
- ein unbekannter Platzhalter wurde erfunden: …
- der Bericht aus dem Gebrauch wird nicht aufgefangen: …
- es steht noch eine Entwertung im Text: …

### T-OBERFLAECHE-71: Die Obergrenze steht im Server, nicht in der Hilfe

- MAX_UPLOAD steht nicht mehr in app/serve.py
- /api/zustand nennt die Obergrenze nicht, die Hilfe kann sie dann nur erfinden
- die Hilfe auf … nennt die Obergrenze nicht
- die Hilfe auf … schreibt die Zahl aus, zweiter Verwalter
- seiten.js traegt eine ausgeschriebene Groesse
- die Obergrenze erscheint nicht in der gezeigten Hilfe
- die Luecke `{mb}` steht ungefuellt in der Hilfe
- ohne Serverantwort erscheint eine Zahl, die niemand kennt

### T-OBERFLAECHE-72: Keine Farbe steht unterhalb der Tokenschicht

- die Tokenschicht ist nicht mehr zu finden
- nur … Marken in der Tokenschicht, 30+ erwartet
- Papierflaeche und Schrift-auf-Farbe sind wieder eine Marke
- `--auf-farbe` wird als Flaeche benutzt, das ist die Schrift
- `--papier` wird als Schrift benutzt, das ist die Flaeche
- ist verschwunden, die Zuordnung gehoert ins Skript
- nur … Farbverweise im Skript, 72+ erwartet

### T-OBERFLAECHE-73: Der Dunkelmodus kennt jede Marke, die es hell gibt

- der Systemzweig des Dunkelmodus fehlt
- die ausdrueckliche Wahl «dunkel» fehlt
- der Systemzweig laesst sich von der ausdruecklichen Wahl «hell» nicht ueberstimmen
- nur … Farbmarken gefunden, 100+ erwartet
- «automatisch» entfernt das Attribut nicht, dann greift die Systemwahl nie
- » kennt das Skript nicht
- auf die Farbwahl horcht niemand
- die Farbwahl wirkt nicht sofort, man muesste den Dialog schliessen, um sie zu sehen

### T-OBERFLAECHE-74: Eine Meldung erscheint dort, wo der Anwender steht

- der Dialog zeigt nicht seinen eigenen Kanal
- … Stellen setzen …, genau eine erwartet
- eine Meldung bei geschlossenem Dialog erscheint nicht in 05
- eine Meldung bei offenem Dialog erscheint nicht im Dialog
- eine Meldung bei offenem Dialog landet hinter dem Dialog
- der Platz fuer die Meldung fehlt im Dialog
- die Meldung haengt an `hidden`, das ist die display-Falle
- «Einfuegen» steht im Browser da und kann dort nicht wirken

### T-OBERFLAECHE-75: Jeder Dialog startet oben, jeder Knopf traegt sein Zeichen

- es gibt keine gemeinsame Stelle, die einen Dialog von oben zeigt
- der Inhalt des Dialogs startet nicht oben
- die Huelle startet nicht oben, bei einem Dialog, der hoeher ist als das Fenster, bleibt der Rollstand stehen
- ein Dialog wird an `dialogVonOben` vorbei sichtbar gemacht
- das Zeichen «…» fehlt in KNOPFBILDER

### T-OBERFLAECHE-76: Die Felder, die es dreimal erwischt hat

- die Regel fuer … ist fort
- … setzt keine Flaeche, es nimmt die Browservorgabe (weiss) und steht im Dunkelmodus als weisser Kasten da
- … setzt keine Schriftfarbe, dann rechnet der Browser sie gegen seine eigene Flaeche, nicht gegen unsere
- das Suchfeld setzt seine Platzhalterfarbe nicht

### T-OBERFLAECHE-70: Einpflegen geht mehr als einmal

- erster Durchgang: …
- zweiter Durchgang kommt nicht an, Bereich 05 zeigt weiter «…»
- die eigene Bearbeitung wird bei der naechsten Zeichnung ueberschrieben: …
- in Bereich 05 fehlt der Papierkorb
- der Papierkorb leert Bereich 05 nicht
- der Papierkorb in 05 leert auch Bereich 04

### T-OBERFLAECHE-69: Der Seitenquelltext bleibt knapp und englisch

- gar keine Kommentare, die Wache prueft nichts
- … von … Zeichen sind Kommentar (… %), knapp heisst unter 12 %
- zu lang (… Zeichen): ……
- nicht englisch: ……
- eine lange Begruendung im Quelltext: ……

### T-OBERFLAECHE-77: Das Ablagefach wird nur angeboten, wo es eines gibt

- unter Linux im eigenen Fenster fehlt ein Fensterschalter
- unter Windows fehlt der Schalter fuer den Infobereich
- unter macOS steht der Schalter fuer den Infobereich, es gibt keinen
- unter Windows fehlt der Schalter fuer das schmale Fenster
- im Browser stehen Fensterschalter

### T-OBERFLAECHE-78: Kein Fehlertext des Browsers in der Oberflaeche

- eine begruendete Absage verliert ihren eigenen Satz

### T-OBERFLAECHE-79: Rueckfragen im eigenen Dialog, nie im Browserdialog

- der Dialog geht nicht auf
- der Fragetext fehlt
- «Abbrechen» nicht in der Sprache
- eine Ja/Nein-Frage zeigt ein Eingabefeld
- Nein gilt nicht als Nein
- Ja gilt nicht als Ja
- Escape bestaetigt
- Markieren mit Loslassen daneben schliesst den Dialog
- ein Klick daneben bestaetigt
- die erste Frage haengt
- die zweite Frage antwortet nicht
- die Eingabe zeigt kein Feld
- der Vorschlag steht nicht im Feld
- die Eingabe kommt nicht zurueck
- Abbrechen liefert trotzdem einen Namen
- : das Neuladen des Browsers laeuft los
- : trotz Nein neu geladen
- nach Ja nicht neu geladen

### T-OBERFLAECHE-80: Neue Adresse: Speichern & neu starten statt Pruefen

- der neue Port wurde nicht gespeichert
- gespeichert, aber nicht neu gestartet
- im Browser nicht gespeichert oder doch neu gestartet
- im Browser fehlt der Satz, ab wann es gilt

### T-OBERFLAECHE-81: «Kopieren und öffnen» geht unter macOS und Windows wie ein Menue-Link

- …: kein einzelner Verweis angeklickt: …
- …: der Verweis ist kein <a target="_blank" rel="noopener …">
- …: zusaetzlich window.open aufgerufen (…x), Dienst doppelt
- …: Reihenfolge … statt kopieren, verweis, (erst dann) mikro, der Verweis kommt nach einem await, und dann ist die Nutzergeste verbraucht
- …: nichts kopiert
- Linux: window.open sollte bleiben, kein Verweis angeklickt werden
- im Browser: window.open sollte bleiben, kein Verweis angeklickt werden

### T-OBERFLAECHE-82: Die Dienste stehen alphabetisch, im Menue und in den Einstellungen

- das Dienstmenue ist nicht alphabetisch: …
- die Einstellungen sind nicht alphabetisch: …
- Entfernen traf den falschen Eintrag: …

### T-OBERFLAECHE-83: Ein Ablegen ohne Datei (Apple Mail) meldet sich, statt zu schweigen

- keine Meldung beim Ablegen ohne Datei: «…»
- die Typen der Quelle fehlen in der Meldung
- drop_ohne_datei fehlt in …

### T-OBERFLAECHE-84: «Nach Updates suchen» fragt nur auf Klick und zeigt das Ergebnis im Fenster

- fetch(/api/neueste) steht …-mal in maschera.js statt einmal
- die Oberflaeche fragt GitHub selbst
- schon das Zeichnen des Menues fragt GitHub
- gefragt wurde nicht genau einmal per POST: …
- keine Meldung «neuere Fassung»: «…»
- der Verweis zur Download-Seite fehlt oder ist kein echter Link
- keine Meldung «neueste Fassung»: «…»
- ohne Netz keine verstaendliche Meldung: «…»
- ohne Netz fehlt der Verweis zur Download-Seite

### T-OBERFLAECHE-85: Das Vokabular entfernt eine Maske im ganzen Dokument

- Kopf der Tabelle: …
- keine Taste «Entfernen» in der Zeile [ORG_1]
- nicht ueberall entfernt: …
- Woerterbuch falsch: …
- eine ANDERE Maske ging mit weg

### T-OBERFLAECHE-86: Karten mit Abstand, dreispaltig wie untereinander

- dreispaltig gap …rem statt >= 0.75rem
- die Kachel ist keine Karte mehr (Rundung)
- gestapelt zu wenig Abstand: …

### T-OBERFLAECHE-87: Einstellungen: Abbrechen, Escape, Hintergrund, und der Fehler beim Abschnitt

- im Kopf des Einstellungsdialogs steht noch ein Knopf
- Abbrechen und Speichern stehen nicht zusammen in der Fusszeile
- «Abbrechen» fehlt in einer Sprache
- Abbrechen schliesst den Dialog nicht
- Abbrechen nimmt den geaenderten Dienstnamen nicht zurueck (flache Kopie?)
- Abbrechen laesst die Farbwahl stehen
- Abbrechen laesst die getippte Adresse stehen
- Abbrechen hat gespeichert
- Escape der Rueckfrage schliesst auch die Einstellungen
- Escape schliesst den Dialog nicht
- Escape nimmt nicht zurueck
- Klick auf den Hintergrund schliesst nicht
- Klick auf den Hintergrund hat gespeichert statt abgebrochen
- eine leere Zeile verhindert das Speichern
- die leere Zeile ging mit zum Server
- ohne Dienst gespeichert und geschlossen
- der Dienstfehler steht wieder unter Server
- der Dialog rollt nicht zur Meldung
- das leere Adressfeld ist nicht markiert
- der Name ist markiert, obwohl er da ist
- nach dem Abbrechen fehlen die Dienste
- die Markierung bleibt nach dem Abbrechen haengen

### T-OBERFLAECHE-88: Die Schrittleiste folgt dem Ablauf und steht einspaltig auf einer Zeile

- Schritt … statt …
- … Schritte statt 5
- Schritt 2 ist nach dem Maskieren nicht der aktuelle
- Schritt 1 ist nicht als fertig markiert
- ein Tippen zentriert den angetippten Schritt nicht

### T-OBERFLAECHE-89: Suchfelder mit Lupe, ein Kreuz fuer alles, Tooltips je Sprache

- … Suchfelder im HTML, mindestens 3 erwartet
- [^
- das Suchfeld im Klappmenue hat keine Lupe
- app/static/lupe.svg fehlt
- der doppelte Kopierknopf fuer «Das geht hinaus» ist zurueck
- ein Kreuz steht wieder als Schriftzeichen statt gezeichnet
- …: kein Tooltip fuer …
- wird wieder ausgeblendet statt deaktiviert
- startet wieder versteckt
- springt wieder ohne den Schritt aufzuheben
- Einpflegen hebt den angetippten Schritt nicht auf
- «Beispiel» laesst den vorigen Durchgang stehen
- nach «Beispiel» steht der Ablauf nicht am Anfang mit dem Beispiel in 01
- die Kopfzeile gibt den Schriftzug nicht mehr zuletzt auf
- die Hinweise von 02 stehen nicht mehr gleich unter dem Kopf
- Vorlagen stehen nicht mehr neben dem Titel «Prompt»
- Leeren und Kopieren stehen nicht mehr unter dem Promptfeld
- maske-test.svg hat nicht mehr dieselben Pfade wie maske.svg
- hat keinen Knopf zum Vergroessern
- die grosse Kachel oder ihr Grund ist nicht mehr gesetzt
- «Beispiel» leuchtet beim ersten Start nicht mehr

### T-OBERFLAECHE-90: 2.2: Willkommensschirm, Hintergrund, schwarze Schrift, grosse Ablage

- schliesst nicht ueber hintergrundSchliesst()
- ein Dialog prueft am Hintergrund wieder nur das Ziel des Klicks
- #ablage-gross fehlt im HTML
- die grosse Ablage geht beim Ziehen nicht auf oder nicht zu
- die grosse Ablage nimmt keine Datei an
- Willkommen nicht in vier Sprachen
- statt 6 Seiten
- traegt einen Gedankenstrich
- ist der deutsche Text
- .webp
- der Willkommensschirm steht nicht im Burgermenue
- der Start zeigt den Willkommensschirm nicht ohne Marke
- die Bildflaeche ist nicht mehr voll breit
- die Bilder des Willkommensschirms werden wieder zugeschnitten
- hell und dunkel der Willkommensbilder wechseln nicht mehr
- der Willkommensschirm geht nicht auf
- Weiter blaettert nicht
- Blaettern laeuft ueber den Anfang hinaus
- Escape schliesst den Willkommensschirm nicht

### T-OBERFLAECHE-91: Seit 23.10.2026: Kopf und Schrittleiste geben nach Platz nach, die Ablage nach Ereignissen

- kopfEinpassen(): Reihenfolge nicht lokal, Spruch, Sprache, Marke
- der Spruch darf umbrechen; dann merkt die Messung nicht, dass er nicht passt
- das Netz der Ablage ist kuerzer als 1.5 s; still gehaltene Dateien fallen wieder heraus
- ueber der grossen Ablage laeuft die Uhr wieder
- die Maske auf der Schlussseite steht wieder ueber ein gap (cqi meint dort das Fenster)
- die Buehne des Willkommensschirms rollt beim Blaettern wieder waagrecht

### T-OBERFLAECHE-92: Seit 25.10.2026: Sprachwahl im Willkommensschirm, «Speichert nichts» auf dem Server

- die Sprachwahl steht nicht oben rechts im Willkommensschirm neben dem Kreuz
- der Kopf traegt die gemeinsame Klasse der Sprachwahl nicht
- der offene Willkommensschirm zeichnet sich bei einem Sprachwechsel nicht neu
- auf einem Server steht wieder «100% lokal»
- «Speichert nichts» fehlt in einer Sprache
- : Seite 2 hat keinen eigenen Titel und Text fuer den Server
- : Servertext mit Gedankenstrich
- .webp
- Seite 2 zeigt auf dem Server das lokale Bild

### T-OBERFLAECHE-93: Seit 26.10.2026: Vorlagenmenue bleibt offen, Vokabular hochladen liest ein

- das Rollen der Schrittleiste schliesst das Vorlagenmenue wieder
- rollt der Kasten mit dem Knopf, bleibt das Menue irgendwo im Raum stehen
- rollt die Seite, bleibt das Menue offen
- «Vokabular hochladen» oeffnet die Dateiwahl nicht
- das hochgeladene Vokabular wurde nicht uebernommen
- der maskierte Text aus der Datei fehlt
- das Dateifeld wird nicht geleert; dieselbe Datei loest beim zweiten Mal nichts aus
- das eingelesene Vokabular erscheint erst beim naechsten zufaelligen Neuzeichnen
- die gespeicherte Vorlage steht erst nach dem naechsten Neuzeichnen in der Auswahl

### T-OBERFLAECHE-94: Seit 28.10.2026: Tab folgt dem Arbeitsweg, Pfeile durch die Nebenknoepfe

- Strg-Tab wird abgefangen
- tabWeg haengt an keinem keydown
- pfeilWeg haengt an keinem keydown
- die Ablage hat keinen Tab-Halt fuer die Pfeilgruppe

## `tests/test_patterns.py`

Test der Regex-Recognizer (SPEC §3 Stufe 1 und 2).

### T-PATTERNS-1: Treffer in vier Sprachen

- … Positivfaelle nicht erkannt: …

### T-PATTERNS-2: Decoys und Negativanker


### T-PATTERNS-2B: Behoerdenmuster: der Name endet, wo der Satz weitergeht


### T-PATTERNS-2C: Firmenmuster greift nicht auf das Wort davor ueber

- Firmenmuster frisst das Wort davor: … in …
- Behoerdenmuster: … nicht sauber abgegrenzt -> …
- Behoerdenmuster frisst weiter: …
- … faelschlich erkannt in … (…)

### T-PATTERNS-3: Falsch-Positiv-Rate der Pruefsummen auf Zufallsziffern

- EAN-13-Trefferquote unerwartet
- Luhn-Trefferquote unerwartet

### T-PATTERNS-9: USERNAME, Etikett gegen Paarschreibweise

- USERNAME … -> …, erwartet …

### T-PATTERNS-10: IPADDRESS, Uhrzeit gegen IPv6

- IPADDRESS … -> …, erwartet …

### T-PATTERNS-11: ORG, Behoerdennamen viersprachig

- ORG … -> …, erwartet …

### T-PATTERNS-12: Katalog der Merkmale, verankerte Auspraegungen

- … … -> …, erwartet …

## `tests/test_rauschen.py`

Rauschen und Haltezone, zwei Lehren aus der Auswertung.

### T-RAUSCHEN-1: Rauschen erzeugt echte Tippfehlerarten

- zu wenig Vielfalt: …
- die gemessene Vertauschung 'Pasqaule' kommt nicht vor
- Versalien fehlen (Formulare in Grossschrift)
- aufgeloester Umlaut fehlt: …

### T-RAUSCHEN-2: Der erste Buchstabe bleibt unangetastet

- …: Anfangsbuchstabe veraendert -> …

### T-RAUSCHEN-3: Kurze Werte bleiben unberuehrt

- … wurde veraendert

### T-RAUSCHEN-4: Pruefsummen-Tags werden NICHT verrauscht

- … steht in VERRAUSCHBAR

### T-RAUSCHEN-5: Halterzone: Training und Auswertung teilen keinen Wert

- Ueberschneidung: …
- zusammen nicht vollstaendig
- Halterzone ist … %, erwartet rund 10 %
- 'ORG@de' wird nicht geteilt, Sprachzusatz nicht abgeschnitten? Ueberschneidung: …
- 'ORG@de' liefert eine leere Zone
- ORG-Ziehungen teilen … Wert(e) ueber die Zonen

### T-RAUSCHEN-6: Geschlossene Listen bleiben ganz

- … wurde aufgeteilt

### T-RAUSCHEN-7: Die Trennung ist reproduzierbar

- andere Reihenfolge ergibt eine andere Halterzone

## `tests/test_regressionen.py`

Regressionen: bekannte Fehlerklassen von PII-Erkennern.

### T-REGRESSIONEN-0: Ohne eigenen Punkt

- … IBAN nicht gefunden
- … IBAN nur teilweise erfasst, der gefaehrliche Fall
- … Falsch-Positive auf Prosa
- … von … Dokumenten haben Daten in falscher Reihenfolge
- unplausible Geburtsjahre: …
- benachbarte Slots mit gleichem Tag muessten gemeldet werden
- verschiedene Tags nebeneinander sind KEIN Befund
- Slots mit Trenntext duerfen nicht gemeldet werden
- eigene Vorlagen verletzen die Regel: …
- literaler Escape muesste gemeldet werden
- Normalisierung behebt es nicht
- Normalisierung erzeugt keinen echten Umbruch
- … Platzhalter kleben an einem Wortzeichen: …
- amount-Decoys nicht einheitlich: …

## `tests/test_scan_pdf.py`

Ein gescanntes PDF ohne Textebene, der stille Nullbefund.

### T-SCAN-PDF-1: Der Leser meldet den leeren Scan

- unerwarteter Text: …
- keine Warnung, nur: …
- die Warnung nennt den Grund nicht

### T-SCAN-PDF-2: Ein PDF MIT Textebene wird normal gelesen

- Text nicht gelesen: …
- warnt ohne Grund: …

### T-SCAN-PDF-3: Der Endpunkt reicht die Warnung durch, statt sie zu ersetzen

- Status … statt 400
- die Meldung nennt den Grund nicht: …
- die Warnung des Lesers wurde durch die kurze Fassung ersetzt
- keine Hinweise im Fehlerkoerper

### T-SCAN-PDF-4: Ein lesbares PDF laeuft normal durch

- Status …: …
- AHV-Nummer nicht maskiert
- gefunden: …

### T-SCAN-PDF-5: Die Oberflaeche zeigt den Grund, nicht nur den Status

- maschera.js liest die Hinweise aus dem Fehlerkoerper nicht
- maschera.js kennt das Feld `hinweise` im Fehlerfall nicht

### T-SCAN-PDF-6: Brotli erreicht MuPDF nicht: die rohe Datei

- Laenge geaendert: …
- nicht ueberschrieben: …
- nicht erkannt: …

### T-SCAN-PDF-7: Gewoehnliche PDF fallen nicht durch

- zu Unrecht: …
- aehnliche Namen werden ueberschrieben
- Binaerdaten werden veraendert
- Binaerdaten loesen die Wache aus
- XML in einem Anhang loest aus
- Text oder Flate loest aus
- nicht erkannt: …

### T-SCAN-PDF-8: Der ganze Weg: echtes MuPDF, je Fall ein Prozess

- …: …
- … erreicht den Decoder: MuPDF haengt
- gesundes PDF …: …
- Status …
- Antwort …

## `tests/test_schriften.py`

Schriften, vorhanden, lokal, und was sie abdecken.

### T-SCHRIFTEN-1: Die Schriftdateien liegen da

- … woff2 statt 10
- … KB, mehr als erwartet

### T-SCHRIFTEN-2: Lizenz und Herkunft sind dabei

- OFL.txt fehlt, die Lizenz verlangt sie
- OFL.txt enthaelt nicht den Lizenztext
- HERKUNFT.md fehlt

### T-SCHRIFTEN-3: Jede @font-face-Regel zeigt auf eine vorhandene Datei

- maschera.css fehlt
- … @font-face-Regeln statt 10
- @font-face zeigt ins Leere: …
- … liegt herum, wird aber von keiner Regel benutzt

### T-SCHRIFTEN-4: Kein Verweis nach aussen in der CSS

- maschera.css laedt Schriften von Google

### T-SCHRIFTEN-5: Abdeckung des amtlichen Zeichensatzes

- … nicht lesbar: …
- …: unbekannte Schrift, in LUECKEN eintragen
- …: U+… … fehlt und steht nicht in LUECKEN, im amtlichen Zeichensatz seit 11.11.2024
- …: U+… … steht in LUECKEN, ist aber vorhanden, Eintrag streichen

### T-SCHRIFTEN-6: Die vier Sprachen kommen vollstaendig durch

- … fehlen: …

## `tests/test_specs.py`

Der Anforderungskatalog in `specs/` bleibt wahr.

### T-SPECS-1: Alle Kapitel sind da

- specs/….md fehlt
- ein Kapitel in specs/ ist nicht in der Liste KAPITEL

### T-SPECS-2: Die erzeugten Teile sind aktuell

- specs/erzeugt/… ist veraltet: python3 tools/specs_bauen.py

### T-SPECS-3: Jede Kennung ist einmal vergeben

- … doppelt: …, …

### T-SPECS-4: Jeder Verweis zeigt auf etwas

- … nennt …, das es nicht gibt

### T-SPECS-5: Jede Anforderung hat eine Pruefung oder sagt, dass sie keine hat

- …: «…» nennt keine Pruefung

### T-SPECS-6: Keine toten Links

- …: Link … zeigt ins Leere

### T-SPECS-7: Kein Gedankenstrich in den Texten

- …: Gedankenstrich in «…»

### T-SPECS-8: Jeder Endpunkt und jedes Tag ist beschrieben

- 07_api.md beschreibt … nicht
- 06_erkennung.md nennt … nicht

### T-SPECS-9: Jeder neue Pruefpunkt gehoert zu einer Anforderung

- … steht in keiner Anforderung: in specs/ eintragen
- … ist jetzt zugeordnet: aus der Altliste streichen
- … gibt es nicht mehr: aus der Altliste streichen

### T-SPECS-10: Ein Release ohne Durchsicht des Katalogs haelt an

- Kapitel geaendert wird abgewiesen
- Release ohne Kapitel laeuft durch
- Erzeugtes zaehlt als Durchsicht
- die begruendete Zeile wirkt nicht
- die Zeile eines aelteren Release gilt mit
- die Zeile ohne Grund gilt

### T-SPECS-11: SECURITY.md nennt die Fassungsreihe des Release

- alte Fassungsreihe in SECURITY.md laeuft durch
- die englische Zeile wird nicht verlangt

### T-SPECS-12: Die Werte im Text sind die Werte im Code

- … nennt … nicht mehr, der Code schon
- 06_erkennung.md nennt das Tag …, das es nicht gibt
- …: Text Stufe …, Code Stufe …
- …: Text …, Code …
- …: Text Budget …, Code …
- 06_erkennung.md fuehrt … Tags in den Stufen, es sind …
- 10_oberflaeche.md: ein Element des Tab-Wegs fehlt
- 10_oberflaeche.md: der Tab-Weg steht in anderer Folge als ARBEITSWEG
- 10_oberflaeche.md: das Burgermenue weicht von adressen.json ab
- 13_sicherheit.md nennt … nicht
- train.py …=…, Katalog …
- 08 fuehrt die Zeile … nicht
- train.py: … nicht mehr gefunden

## `tests/test_streuung.py`

Was `tools/streuung.py` zusagt, als Pruefung statt als Kommentar.

### T-STREUUNG-1: Die Schwellen des Urteils

- Δ unter σ gilt nicht als aufgeloest
- Δ genau auf σ gilt nicht als aufgeloest
- Δ zwischen einem und zwei σ ist schwach
- Δ ueber zwei σ ist deutlich
- σ = 0 darf keine Division ergeben, sondern eine Auskunft
- ein unaufgeloester Unterschied darf nicht als 'kein Unterschied' ausgegeben werden

### T-STREUUNG-2: Keine Leckwerte in der Ausgabe

- tools/streuung.py benutzt .… in Zeile … anders als in len(), Leckwerte koennten in die Ausgabe geraten

### T-STREUUNG-3: Die Wache gegen σ-Vielfache bei zu wenigen Laeufen

- keine Schwelle n < 3 im Quelltext, die σ-Vielfachen sind ungeschuetzt
- kein Zweig, der bei zu wenigen Laeufen auf die Vielfachen verzichtet

### T-STREUUNG-4: Kein zweiter Lader fuer die Golddokumente

- streuung.py holt die Golddokumente nicht ueber eval_documents.lade_gold()
- streuung.py entscheidet selbst ueber `geprueft`, diese Regel gehoert in lade_gold() und nur dorthin
- streuung.py sucht die Golddateien selbst zusammen statt ueber lade_gold()

## `tests/test_user_rules.py`

Eigene Regeln des Anwenders, Schritt 11.

### T-USER-RULES-1: Etikett, Wortliste, Kollisionen

- 2 Regeln erwartet, …
- Dossiernummer nicht maskiert
- Projektname nicht maskiert
- Nummer blieb im Klartext
- Gebuehr faelschlich maskiert

### T-USER-RULES-2: Wachen gegen Fehleingaben

- haette abbrechen muessen: …

### T-USER-RULES-2B: Die alten deutschen Schluessel werden gelesen, aber gemeldet

- die alte Datei wurde nicht gelesen: … Regeln
- die Bezeichnung ging verloren: …
- nicht gemeldet: … (gemeldet: …)
- die englische Datei meldet Altlasten: …

### T-USER-RULES-3: Benutzertags koennen nie ins Training gelangen

- Benutzertag steht in der Taxonomie

### T-USER-RULES-4: MASCHERA_REGELN zeigt auf die Regeln

- MASCHERA_REGELN wurde nicht gelesen, Regeln still weg

### T-USER-RULES-5: Eigene Regeln: Wettbewerb ueber die Laenge, keine Stufe

- die Probe-Regel trifft nicht wie erwartet: …
- Modellspanne …: gewonnen hat …, erwartet […]

### T-USER-RULES-5B: Ein altes `stage` bricht nichts, und wird gemeldet

- `…: 1` bricht die Regeldatei
- `…` wird nicht gemeldet (gemeldet: …)
- `…: 1` wirkt noch, die Regel hat Stufe …

## `tests/test_vertrauen.py`

Vertrauensaufloesung: `Mitschreiber.vertrauen_zu`.

### T-VERTRAUEN-1: Exakter Treffer kommt unveraendert durch

- exakter Schluessel liefert nicht den abgelegten Wert

### T-VERTRAUEN-2: Ausgedehnte Spanne behaelt ihren Wert

- ausgedehnte Modellspanne kommt mit … statt 0.31 an

### T-VERTRAUEN-3: Bei mehreren ueberlappenden gilt die unsicherste

- nimmt … statt der unsichersten 0.42

### T-VERTRAUEN-4: Regex erbt keine Modellzahl

- regex-Fundstelle traegt … statt None
- checksum-Fundstelle traegt … statt None
- propagation-Fundstelle traegt … statt None
- rule-Fundstelle traegt … statt None

### T-VERTRAUEN-5: Fremdes Tag am selben Ort faerbt nicht ab

- FULLNAME uebernimmt … von GIVENNAME

### T-VERTRAUEN-6: Beruehrung ohne Ueberlappung zaehlt nicht

- angrenzende Spanne uebernimmt …

### T-VERTRAUEN-7: Kein Wert vorhanden, kein Absturz

- leerer Mitschreiber liefert nicht None

### T-VERTRAUEN-8: Bericht und API benutzen dieselbe Aufloesung

- serve.py loest den Schluessel wieder selbst auf statt ueber Mitschreiber.vertrauen_zu
- serve.py ruft Mitschreiber.vertrauen_zu nicht auf
- filter_document.py schlaegt wieder roh nach
- filter_document.py ruft Mitschreiber.vertrauen_zu nicht auf

## `tests/test_vorlieben.py`

Klartext-Vorlieben: Wachen und getrennte Ausweisung.

### T-VORLIEBEN-1: Der Pfad zeigt nicht ins Projekt

- schreibt ausserhalb von XDG_CONFIG_HOME: …
- Vorlieben liegen im Projektbaum, sie wuerden ueber Git und rsync auf jede Maschine wandern

### T-VORLIEBEN-2: Unbekannte Tags werden abgelehnt, nicht ignoriert

- 'DATUM' (Tippfehler) wurde angenommen
- Meldung nennt das falsche Tag nicht

### T-VORLIEBEN-3: bspd-Tags brauchen --auch-bspd

- zu wenige bspd-Tags in der Taxonomie: …
- … ohne --auch-bspd angenommen
- mit --auch-bspd muss es durchgehen

### T-VORLIEBEN-4: Speichern und Laden

- gelesen: …

### T-VORLIEBEN-5: Ein abgeschaltetes Tag verschwindet NICHT aus der Auswertung

- ohne Ausschluss muss CITY als Leck zaehlen
- ein bewusst offenes Tag ist kein Leck
- der Wert fehlt in im_klartext: …
- Tags fehlen: …
- der Bericht verschweigt, dass ein Tag abgeschaltet ist

### T-VORLIEBEN-6: Ein bewusst offenes Tag ist keine Uebermaskierung

- erwartet 2 Uebermaskierungen: …
- ORG offen -> nur CITY darf uebrig bleiben: …
- falsches Tag: …
