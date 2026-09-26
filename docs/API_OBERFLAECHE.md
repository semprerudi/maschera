# API der Oberfläche

Der Vertrag zwischen der Oberfläche (`app/static/`) und dem Dienst
(`app/serve.py`). Was hier steht, liefert der Code; `tests/test_api.py`
prüft die Endpunkte gegen dieses Dokument.

**Was hier nicht steht, ist Gestaltung.** Farben, Anordnung, Schriften und
Verhalten beim Tippen gehören in die Oberfläche, nicht in den Vertrag.

---

## Die Platzhalter: englische Tagnamen in eckigen Klammern

Die Platzhalter tragen die Tagnamen selbst, damit eine französische oder
italienische Oberfläche sie nicht mitübersetzen muss.

```
[FULLNAME_1]     [GIVENNAME_1]    [ORG_1]        [CITY_1]
[STREET_1]       [ZIPCODE_1]      [AHVN13_1]     [PHONE_1]
[PLACE_OF_ORIGIN_1]               [CASE_ID_1]    [EMAIL_1]
```

44 Platzhalter für 45 Tags (`CANTON` ist `tag_only`, wird erkannt und nicht
ersetzt). Dazu die Benutzerregeln mit frei gewählten Namen: `[Dossier_1]`.

**Die eckigen Klammern sind einfach, nicht doppelt.** `[[TAG:wert]]` gehört
zum Gold-Markierungsformat und kommt in der Ausgabe nie vor.

⚠️ **Die Nummer ist stabil über das ganze Dokument.** Derselbe Wert bekommt
immer denselben Platzhalter — nur so bleibt der Text für ein Sprachmodell
verständlich. Kommt derselbe Name in einer anderen Form vor (`Hans Meier`,
später nur `Meier`), trägt die Variante einen Buchstaben: `[FULLNAME_1b]`.

### Für die farbliche Hervorhebung

```
\[[A-Za-z][A-Za-z0-9_]*_\d+[a-z]?\]
```

Dasselbe Muster wie die Rückwandlung. Es passt auf `[FULLNAME_1]`,
`[PLACE_OF_ORIGIN_1]`, `[FULLNAME_1b]` und `[Dossier_1]`, aber nicht auf
`[_1]`, `[123_1]` oder `[FULLNAME]`.

Reicher wird es über die Fundstellen (`spans` unten): Sie liefern zu jedem
Platzhalter das **Tag**, die **Quelle** und das **Vertrauen**.

---

## Der Wirtsname gilt für **alle** Endpunkte

Vor jedem Endpunkt — auch vor `/api/zustand`, auch vor der Oberfläche —
wird der `Host:`-Kopf geprüft. Ein Name, der nicht dazugehört, bekommt
**403** mit dem Schlüssel `wirt_unbekannt`.

```jsonc
{ "fehler": "Dieser Dienst antwortet nicht unter dem Namen «…».",
  "fehler_schluessel": "wirt_unbekannt",
  "fehler_werte": { "wirt": "boese.example.com" } }
```

Immer erlaubt sind `127.0.0.1`, `localhost`, `::1` und `0.0.0.0` — sonst
schlüge der `HEALTHCHECK` des Abbilds fehl, der 127.0.0.1 ruft. Hinter
einem Reverse Proxy kommt dessen Name in **`MASCHERA_WIRT`** dazu;
`MASCHERA_WIRT=*` schaltet die Prüfung ab.

⚠️ **Warum das nötig ist, obwohl der Dienst nur auf 127.0.0.1 hört.**
«Nur lokal» ist eine Aussage über die **Adresse** und keine über den
**Namen**. Ein Angreifer lässt seinen eigenen Namen auf 127.0.0.1 zeigen
(DNS-Rebinding); für den Browser ist das derselbe Ursprung, also ohne
CORS-Schranke und mit lesbarer Antwort. Zu holen gäbe es
`GET /api/vorlagen` (Prompts, können Personendaten tragen) und
`GET /api/regeln` (die Regeldatei im Rohtext).

Jede Antwort trägt ausserdem eine Content-Security-Policy
(`script-src 'self'`, `style-src 'self'`, `connect-src` nur zum eigenen
Dienst und zu Loopback), `X-Content-Type-Options: nosniff` und
`Referrer-Policy: no-referrer`.

## Endpunkte

### `POST /api/lesen`

Macht eine hochgeladene Datei zu Text — und sonst nichts. Nur
`multipart/form-data`, Feld `datei`.

```jsonc
// Antwort
{
  "original": "Sehr geehrte Damen und Herren\n…",
  "hinweise": [                                 // nur wenn vorhanden
    { "schluessel": "kodierung", "werte": { "kodierung": "cp1252" },
      "text": "Kodierung cp1252" }
  ]
}
```

⚠️ **Ablegen liest ein, es maskiert nicht.** Maskieren ist die Handlung, um
die es in diesem Werkzeug geht; sie hat einen eigenen Knopf, weil sie eine
Entscheidung ist. Etwas, das von selbst läuft, weil eine Datei ins Fenster
gezogen wurde, ist keine Entscheidung mehr.

⚠️ **Gelesen wird im Server.** PDF und DOCX gehen im Browser ohnehin nicht —
und der leere Befund, «Scan ohne Textebene», muss aus derselben Quelle
kommen wie sonst. Ein leerer Befund ist keine Entwarnung: eine leere Datei
antwortet mit **400** und der Begründung des Lesers, nicht mit einem leeren
`original`.

⚠️ **Dieselben Wachen wie am Dateizweig von `/api/anonymisieren`**, und
zwar buchstäblich dieselbe Funktion — Formatliste, temporäres Verzeichnis,
Mehrfachnachricht, die Meldungen des Lesers.

⚠️ **Geschrieben wird nichts.** Die Datei liegt für die Dauer des Lesens in
einem temporären Verzeichnis und ist danach weg.

Der Dateizweig von `/api/anonymisieren` bleibt — die Kommandozeile braucht
ihn. Die Oberfläche geht ihn nicht.

### `POST /api/anonymisieren`

```jsonc
// Anfrage
{
  "text": "Sehr geehrte Damen und Herren\n…",   // ODER Datei per multipart
  "ohne": ["DATE"],          // Tags im Klartext lassen, optional
  "woerterbuch": true,       // umkehrbar? Vorgabe true
  "regeln": true             // eigene Regeln anwenden, Vorgabe true
}
```

```jsonc
// Antwort
{
  "maskiert": "Sehr geehrte Damen und Herren\n… [FULLNAME_1] …",
  "original": "…",                    // unverändert zurück, für Spalte 1
  "spans": [
    {
      "tag": "FULLNAME",
      "start": 142, "end": 151,        // Positionen im ORIGINAL
      "platzhalter": "[FULLNAME_1]",
      "quelle": "model",               // checksum | regex | model
                                       // rule | propagation | manuell
      "vertrauen": 0.94,               // null ausser bei `model`
      "bspd": false,                   // besonders schützenswert
      "budget": "R",                   // R | A | P | null
      "zeile": 7
    }
  ],
  "woerterbuch": { "[FULLNAME_1]": "Brülhart", "[GIVENNAME_1]": "Andrea" },
  "verworfen": [
    { "tag": "ORG", "text": "…", "grund": "unter Schwelle 0.40 (0.31)" }
  ],
  "hinweise": [
    { "schluessel": "fenster", "werte": { "token": 512 },
      "text": "Länger als ein Fenster (512 Token). Wird überlappend
               verarbeitet." }
  ],
  "kennzahlen": {
    "zeichen": 4237, "maskiert": 590, "anteil": 0.137,
    "fundstellen": 52, "woerterbucheintraege": 41,
    "dauer_ms": 1240
  }
}
```

⚠️ **Ein Hinweis ist ein Objekt, kein Satz.** Er trägt drei Felder:

| Feld | |
|---|---|
| `schluessel` | der Name des Hinweises, z. B. `fenster`, `ohne_woerterbuch` |
| `werte` | was einzusetzen ist, z. B. `{ "token": 512 }`. Ein Feld als Wert ist eine **Liste von Schlüsseln** und wird selbst übersetzt |
| `text` | die deutsche Fassung, fertig gesetzt |

Ein Klient, der die Schlüssel kennt, setzt den Satz in seiner Sprache; die
Oberfläche tut das über `TEXTE[sprache].hinweise` in `maschera.js`. Ein
Klient, der sie nicht kennt — die Kommandozeile — zeigt `text`. Der Server
kennt die Sprache des Betrachters nicht und soll sie nicht kennen müssen.
`tests/test_api.py` Punkt 18 weist zurück, wer einen Schlüssel im Server
anlegt und die vier Sätze vergisst.

⚠️ **Fehler und Warnungen tragen dieselben Schlüssel.** Neben dem deutschen
Satz stehen zwei weitere Felder:

```jsonc
{ "fehler": "Port ausserhalb 1–65535: 99999",
  "fehler_schluessel": "port_ausserhalb",
  "fehler_werte": { "port": "99999" } }
```

```jsonc
{ "warnung": "Wer die Regeln ändert, ändert das Messergebnis.",
  "warnung_schluessel": "regeln_gelesen",
  "warnung_werte": {} }
```

| Feld | |
|---|---|
| `fehler` / `warnung` | die deutsche Fassung, fertig gesetzt |
| `fehler_schluessel` / `warnung_schluessel` | der Name in `TEXTE[sprache].meldungen` |
| `fehler_werte` / `warnung_werte` | was einzusetzen ist |

⚠️ **Der Text einer Ausnahme steht nie in `fehler_werte`.** Eine
Begründung aus der Regelprüfung oder dem Dokumentleser kommt als eigener
Schlüssel (`regel_woerter_kurz`, `docx_kaputt` …) mit ihren Werten; ein
Fremdtext — PDF-Bibliothek, YAML-Leser, Betriebssystem — nur in `fehler`,
für Kommandozeile und API. Er ist englisch oder in der Sprache des Systems
und trägt mitunter einen temporären Pfad. `tests/test_api.py` Punkt 19.

Getrennte Namen und nicht ein gemeinsames `schluessel`, weil beides
zusammen vorkommt: `GET /api/regeln` schickt eine Warnung **und** einen
Fehler, wenn die gespeicherte Regeldatei kaputt ist. `tests/test_api.py`
Punkt 19 weist zurück, wer einen Schlüssel anlegt und die vier Sätze
vergisst.

⚠️ **`verworfen` ist keine Randnotiz.** Dort stehen Spannen, die das Modell
gefunden und die Schwelle abgewiesen hat. Wer wissen will, was *fast*
maskiert worden wäre, sieht es dort.

⚠️ **`woerterbuch` ist leer, wenn `"woerterbuch": false`.** Dann entsteht
keine Zuordnung, und die Maskierung ist endgültig — die Daten, aus denen
sich die Zuordnung rekonstruieren liesse, entstehen gar nicht erst.

⚠️ **Ein leerer Befund ist keine Entwarnung.** Ein gescanntes PDF ohne
Textebene ergibt null Zeichen. Der Endpunkt antwortet mit **400** und trägt
im Feld `fehler` die Meldung des Dokumentlesers samt Begründung, dazu alle
`hinweise`:

```jsonc
{ "fehler": "kein Text im PDF — vermutlich ein Scan. Ohne OCR sieht der
             Filter nichts, und ein leerer Befund heisst hier NICHT, dass
             keine Personendaten drin sind.",
  "hinweise": [ { "schluessel": "pdf_ohne_text", "werte": {},
                  "text": "…" } ] }
```

`dauer_ms` ist gemessen, nicht geschätzt — damit steht in einem
Fehlerbericht eine Zahl und nicht «es war langsam».

### `GET /api/fortschritt`

```jsonc
{ "aktiv": true, "schritt": 12, "von": 196, "phase": "modell" }
```

Wie weit der laufende Durchgang ist. `phase` ist `"modell"`, solange
Fenster gerechnet werden, und `"maskieren"` für den Rest — Schwellen,
Überlappungen, Propagation, Ersetzen. Läuft nichts, ist `aktiv` falsch und
die Zahlen sind null.

⚠️ **Die Zahl der Fenster ist bekannt, bevor gerechnet wird.** Nach dem
Tokenisieren steht sie fest: 510 nutzbare Token je Fenster, Schritt 382.
Der Balken in der Oberfläche zeigt deshalb etwas Gemessenes.

⚠️ **Der Endpunkt nimmt die Sperre der Kette NICHT.** Der Lauf hält sie die
ganze Zeit; wer hier wartete, bekäme die Antwort erst, wenn es nichts mehr
zu melden gibt.

Er trägt drei Zahlen und ein Wort — keinen Text, keinen Platzhalter, keinen
Wert. Der Stand lebt im Arbeitsspeicher des Prozesses.

### `POST /api/zurueckwandeln`

```jsonc
{ "text": "Die Antwort des Sprachmodells mit [FULLNAME_1] …",
  "woerterbuch": { "[FULLNAME_1]": "Brülhart" } }
```

```jsonc
{ "text": "Die Antwort … mit Brülhart …",
  "ersetzt": 12,
  "nicht_gefunden": ["[ORG_3]"] }
```

⚠️ **`nicht_gefunden`** ist der wichtige Teil: Sprachmodelle schreiben
Platzhalter manchmal um — aus `[FULLNAME_1]` wird `**[FULLNAME_1]**` oder
`[Fullname_1]`. Was nicht zugeordnet werden konnte, muss der Anwender
sehen, sonst verschickt er einen Brief, in dem `[FULLNAME_1]` steht.

### `GET /api/tags`

Die 45 Tags mit Bezeichnung, Platzhalter, Budget, `bspd`, `aktion` und der
aktuellen Schwelle. Für den Tag-Filter und die Legende.

`GET /api/tags?sprache=fr` — `de` (Vorgabe), `fr`, `it`, `en`. Alle vier
vollständig; sie stehen in `packs/ch/bezeichnungen.yaml`. Kein
Vertragsbestandteil des Modells — ein Tag darf umbenannt werden, ohne dass
ein Checkpoint ungültig wird. `check_taxonomy.py` prüft Vollständigkeit in
allen vier Sprachen.

⚠️ **Kein Rückfall auf Deutsch, und eine unbekannte Sprache gibt 400.** Eine
französische Oberfläche mit einzelnen deutschen Einträgen sähe aus wie ein
Übersetzungsfehler statt wie ein Programmierfehler.

⚠️ **Einzelne Einträge sind mit `# ?` markiert** und ungeprüft — sie stehen
da, damit die Oberfläche läuft, nicht weil sie sicher richtig sind. Wer
Zugang zu TERMDAT hat, entscheidet sie.

### `GET|PUT /api/regeln`

Eigene Wörter und Muster (`~/.config/maschera/regeln.yaml`, Format in
`core/user_rules.py`). `GET` liefert den Dateiinhalt im Original (`yaml`)
und die gelesenen Regeln. `PUT` prüft gegen dieselbe Funktion, die später
lädt; abgelehnte Regeln lassen die bestehende Datei unberührt.

⚠️ **Wer sie ändert, ändert das Messergebnis** — das gehört in der
Oberfläche sichtbar gemacht, nicht in ein Untermenü versteckt.

### `GET|PUT /api/vorlieben`

Welche Tags dauerhaft im Klartext bleiben
(`~/.config/maschera/klartext.json`).

```jsonc
// GET
{ "klartext": ["DATE", "ORG"], "bspd": [], "unbekannt": [],
  "pfad": "~/.config/maschera/klartext.json",
  "warnung": "Diese Tags bleiben dauerhaft im Klartext." }
```

```jsonc
// PUT
{ "klartext": ["DATE", "ORG"], "auch_bspd": false }
```

⚠️ **Dieselben zwei Wachen wie bei `ohne`.** Unbekannte Tags werden mit 400
abgewiesen statt ignoriert — ein Tippfehler wäre sonst eine wirkungslose
Einstellung, die als gesetzt gemeldet wird. Und besonders schützenswerte
Tags verlangen `auch_bspd`. Wäre das hier schwächer, liesse sich die Wache
umgehen, indem man einen Tag dauerhaft setzt, statt ihn einmal
mitzuschicken.

### `GET|PUT /api/vorlagen`

Benannte Prompts, die der Anwender wiederverwendet
(`~/.config/maschera/vorlagen.json`).

```jsonc
// GET und die Antwort auf PUT
{ "vorlagen": [ { "name": "Danke, 4 Wochen",
                  "text": "Antworte freundlich, aber nenne vier Wochen." } ],
  "pfad": "~/.config/maschera/vorlagen.json",
  "warnung": "Vorlagen liegen dauerhaft im Klartext auf der Platte." }
```

⚠️ **Ein Prompt kann Personendaten enthalten.** «Fasse den Fall Brülhart
zusammen» ist eine Vorlage wie jede andere — und läge dann dauerhaft im
Klartext auf der Platte. Verhindern lässt sich das nicht; die Warnung in
jeder Antwort ist das, was das Werkzeug tun kann.

⚠️ **Ganz oder gar nicht.** Ein leerer Name, ein leerer Text, zwei gleiche
Namen (ohne Rücksicht auf Gross- und Kleinschreibung), mehr als 50 Vorlagen,
ein Name über 80 oder ein Text über 20 000 Zeichen: die ganze Liste wird mit
400 abgewiesen, und die bestehende Datei bleibt unberührt.

### `GET|PUT /api/einstellungen`

Adresse, Port, Dienste, Darstellung, Fensterschalter
(`~/.config/maschera/einstellungen.json`).

```jsonc
{ "adresse": "127.0.0.1", "port": 4141, "eigenes_fenster": true,
  "dienst": "claude",              // der zuletzt gewählte
  "schriftgroesse": 100,           // 70 | 80 | 90 | 100 | 110 | 125 | 140
  "schriftart": "werk",            // werk | sans | serif | mono
  "sprache": "de",                 // de | fr | it | en
  "thema": "automatisch",          // automatisch | hell | dunkel
  "tray": true,                    // beim Schliessen in den Infobereich
  "fenstermodus": "widget",        // voll | widget
  "dienste": [ { "id": "claude", "name": "Claude",
                 "url": "https://claude.ai/new" } ] }
```

⚠️ **`PUT` prüft das ganze Objekt** und setzt für jedes fehlende Feld die
Vorgabe ein. Wer ein einzelnes Feld ändern will, liest zuerst, ändert und
schreibt das Ganze zurück.

⚠️ **Der gewählte Dienst wird sofort gesichert**, nicht erst beim Schliessen
des Dialogs. Gibt es die Kennung nicht mehr, liefert der Server den ersten
— sonst zeigte der Sendeknopf einen Namen, zu dem keine Adresse gehört.

⚠️ **`sprache` ist die Sprache der BEDIENUNG**, nicht die des Dokuments.
Welche Sprache ein Text hat, entscheidet die Kette für sich. Sie gilt beim
nächsten Start weiter, samt Startbildschirm; den zeichnet `app/fenster.py`,
bevor der Server steht, und liest die Einstellung dafür selbst.

⚠️ Hier gilt **nicht** «unbekannte Sprache → 400 statt stillem Rückfall».
Der Grundsatz sitzt an der Maskierung, wo eine falsche Amtsform ein
fachlicher Fehler ist. `PUT` lehnt eine unbekannte Bediensprache mit
`oberflaechensprache_unbekannt` ab, aber `lade()` fällt bei einer kaputten
Datei auf die Vorgabe zurück, statt das Werkzeug unbenutzbar zu machen.

⚠️ **Adresse, Port, `tray` und `fenstermodus` gelten nur im eigenen
Fenster.** Gelesen werden sie von `app/fenster.py` beim Start; im Browser
ist die Seite bereits vom Dienst ausgeliefert, den sie einstellen würden.
Die Oberfläche blendet diese Abschnitte im Browser aus.

⚠️ **`tray` ist vorgabemässig `true`, `fenstermodus` `widget`.** Unter
GNOME gibt es ohne AppIndicator-Erweiterung kein Ablagefach; versteckte
sich die App dorthin, wäre sie **weg**. `fenster.py` fragt deshalb
`QSystemTrayIcon.isSystemTrayAvailable()` — unter Windows, ob das Symbol
von `pystray` steht — und lässt das X sonst das X sein.

⚠️ **`widget` ist kein Plattform-Widget**, sondern dasselbe Fenster schmal
(380 px) und im Vordergrund.

⚠️ **Die Schriftgrösse skaliert die ganze Oberfläche** über `--skala`; die
Schriftart gilt für die Textflächen, auf Wunsch auch für die Bedienung.

⚠️ **Nur `https://` und `http://`.** Die Adresse eines Dienstes landet in
`window.open`; ein Eintrag `javascript:…` liefe dort im Zusammenhang der
eigenen Seite — mit Zugriff auf Wörterbuch und Originaltext.

⚠️ **Kein Endpunkt, kein Modell, kein Schlüssel.** MASCHERA sendet nichts
selbst; ein Schlüsselfeld wäre eine Einstellung ohne Wirkung, und der
Schlüssel läge im Klartext auf der Platte.

### `GET /api/zustand`

Läuft der Server, mit welchem Modell, unter welchem Labelvertrag.

```jsonc
{ "dienst": "maschera", "version": "x.y.z", "pack": "ch",
  "label_hash": "b7a96dc9…", "tags": 45,
  "modell": "runs/ch-v63b", "ohne_modell": false, "max_mb": 10,
  "hinweise": [] }
```

⚠️ Die **Portprüfung** aus den Einstellungen hängt hier: wer auf 4141
antwortet, ist noch lange nicht MASCHERA. Das Feld `dienst` ist die Antwort
auf diese Frage.

⚠️ **`ohne_modell: true` ist kein Betriebszustand.** Dann laufen nur
Prüfsummen und Muster — Namen, Daten und Adressen bleiben im Klartext. Jede
Antwort von `/api/anonymisieren` trägt in `hinweise` den Schlüssel
`ohne_modell`. Ein Server, der still ohne Modell läuft, wäre eine
Leckquelle mit grüner Anzeige.

### `POST /api/senden` — gibt es nicht

**Es wird ihn nicht geben.** Statt zu senden, legt die Oberfläche Prompt und
Anhang in die Zwischenablage und öffnet den Dienst im Browser; eingefügt
wird von Hand. So sieht der Anwender, was hinausgeht, und keine Zeile
verlässt das Gerät ohne seinen Griff zur Tastatur. `tests/test_api.py`
prüft, dass `/api/senden` mit 404 antwortet.

---

## Einzelheiten

| | |
|---|---|
| **`platzhalter` ist `null`**, nicht `"—"` | bei `CANTON` und bei allem, was über `ohne` im Klartext bleibt. Auch bei `"woerterbuch": false` — dort entsteht keine Zuordnung. Der maskierte Text trägt die Nummer trotzdem |
| **`ohne` fehlt ganz ≠ `"ohne": []`** | fehlt das Feld, gelten die gespeicherten Klartext-Vorlieben, und die Antwort sagt es in `hinweise`. Steht es da, gilt genau das. Sonst wäre «diesmal wirklich alles maskieren» nicht ausdrückbar |
| **`auch_bspd`** | ohne dieses Feld weist der Server `ohne: ["NATIONALITY"]` mit 400 ab. Besonders schützenswerte Personendaten dürfen nicht über einen Schalter im Klartext landen, den man einmal umlegt |
| **`zurueckwandeln` hat `hinweise`** | steht `[FULLNAME_1]` im Wörterbuch und `[fullname_1]` im Text, wird **nicht** stillschweigend ersetzt, aber gemeldet. Stilles Beheben hiesse: der Server ersetzt etwas, das so nie vergeben wurde |
| **Ein Dokument zur Zeit** | der Läufer merkt sich die Vertrauenswerte des letzten Laufs. Zwei gleichzeitige Anfragen würden sie vermischen. `/api/zustand` und `/api/fortschritt` bleiben daneben erreichbar |
| **Nur `127.0.0.1`** | `--host 0.0.0.0` ist möglich und warnt. Der Betrieb hinter einem Reverse Proxy braucht es, der Arbeitsplatz nicht |
| **Nichts wird geschrieben** | kein Protokoll, keine Zwischendatei. Ausnahmen sind die Einstellungen des Anwenders: `PUT /api/regeln`, `/api/vorlieben`, `/api/vorlagen`, `/api/einstellungen` — alle nach `~/.config/maschera/`, alle nur auf ausdrücklichen Befehl |
| **Höchstens 10 MB** | darüber 413 |
| **Mehrere Nachrichten in einer `.mbox`** | nur die erste wird verarbeitet, die Antwort sagt es. Stapel bleibt Sache der Kommandozeile |

---

## Das Wörterbuch sichern und einlesen

Zwei Knöpfe im Fuss des Vokabularbereichs: *Vokabular herunterladen* und
*Vokabular hochladen*.

⚠️ **Keine Bequemlichkeit.** Nichts wird auf die Platte geschrieben — nach dem
Schliessen des Fensters ist das Wörterbuch weg, und ein maskierter Text ohne
Wörterbuch lässt sich nie mehr zurückwandeln.

**Kein Endpunkt, und es soll keinen geben.** `Blob` hinaus, `FileReader`
herein; der Server sieht das Wörterbuch dabei nie. Die Datei trägt
`fassung`, `erstellt`, `label_hash`, `eintraege`, das Wörterbuch und den
maskierten Text.

⚠️ **Sie trägt alle Originalwerte im Klartext** — die Umkehrung dessen, was
das Werkzeug tut. Deshalb eine Rückfrage bei jedem Sichern und ein Dateiname,
der es sagt: `maschera-vokabular-klartext-JJJJMMTT-HHMM.json`.

⚠️ **Nur eigene Vokabulare laden.** Ein fremdes Vokabular bestimmt, was bei
der Rückwandlung eingesetzt wird; wer eines unterschiebt, kann einen Namen
oder Betrag im Ergebnis vertauschen.

⚠️ **Einlesen ersetzt, prüft ganz oder gar nicht** und wirft die Spannen des
alten Laufs weg. Zusammenführen erzeugte stille Kollisionen: `[FULLNAME_1]`
zweimal mit verschiedenen Werten, und die Rückwandlung setzte den falschen
ein.

---

## Die Quelle einer Fundstelle

| Quelle | Bedeutung |
|---|---|
| `checksum` | mathematisch sicher — AHV-Nummer, IBAN, UID, Karte |
| `regex` | Muster mit Anker, deterministisch |
| `rule` | eigene Regel des Anwenders |
| `model` | Vermutung des Modells, mit Vertrauen |
| `propagation` | derselbe Wert an anderer Stelle im Dokument |
| `manuell` | von Hand im Kontextmenü gesetzt oder geändert |

`manuell` entsteht nur im Browser und wird beim nächsten Lauf
überschrieben; der Server erzeugt sie nie.

### Der Randstil sagt, wo Arbeit liegt

| | Quelle | Rand |
|---|---|---|
| **prüfen** | `model`, `propagation` | ausgezogen |
| **eingegriffen** | `manuell` | ausgezogen, doppelt |
| **sicher** | `checksum`, `regex`, `rule` | gestrichelt |

Das Auge folgt der kräftigeren Linie — also zeigt sie dorthin, wo ein
Mensch hinsehen muss, nicht dorthin, wo schon alles stimmt. `manuell`
sticht hervor, obwohl dort nichts zu tun ist: wer als Zweiter draufschaut,
braucht genau diese Auskunft.

### Die Leckrate ist nicht null

Das ist der Grund, warum die dritte Spalte den ausgehenden Text zeigt,
**bevor** er in die Zwischenablage geht — und warum diese Anzeige gelesen
und nicht weggeklickt werden soll.

### Grössenordnungen

| | |
|---|---|
| Dokument | 1500 bis 4500 Zeichen typisch, mehr möglich |
| Fundstellen | 25 bis 55 pro Dokument |
| Maskierter Anteil | 13 bis 20 % der Zeichen |
| Laufzeit | wenige Sekunden auf CPU |

Ein Dokument mit 52 Fundstellen auf 4237 Zeichen heisst: **etwa alle 80
Zeichen ein Platzhalter.** Bei zu greller Einfärbung wird der Text unlesbar.
