# MAS**CH**ERA

[English](README.md) · **Deutsch**

**Personendaten aus Schweizer Dokumenten maskieren — auf dem eigenen
Gerät, im Betrieb ohne Netz.** Vier Sprachen: Deutsch, Französisch,
Italienisch, Englisch.

Du hast ein Schreiben, einen Mailverlauf oder ein PDF und willst ein
KI-Werkzeug darüber fragen — aber die Namen, AHV-Nummern und Adressen
sollen nicht mit. MASCHERA ersetzt sie durch Platzhalter:

    Sehr geehrte Frau Brülhart       ->   Sehr geehrte Frau [FULLNAME_1]
    AHV 756.1234.5678.97             ->   AHV [AHVN13_1]
    Lindenstrasse 12, 3011 Bern      ->   [STREET_1] [BUILDINGNUM_1], [ZIPCODE_1] [CITY_1]

Den maskierten Text gibst du dem Dienst deiner Wahl. Die Antwort fügst du
zurück ein, und MASCHERA setzt die echten Werte wieder ein.

Gedacht für alle, die mit Schweizer Dokumenten arbeiten: Verwaltungen von
Bund, Kantonen und Gemeinden, Unternehmen, Kanzleien, Vereine und
Privatpersonen.

**Die Erkennung läuft vollständig auf deinem Gerät.** Im Betrieb wird
nichts nachgeladen und nichts gesendet — auch keine Schriften, keine
Symbole, keine Statistik. Einen Endpunkt, der Text verschickt, gibt es
nicht und wird es nicht geben; der Weg nach draussen führt immer über
deine Zwischenablage.

⚠️ **Das Modell ist 1,2 GB gross, und es gibt zwei Zuschnitte.** Die
AppImage und der Windows-Installer tragen es mit — herunterladen,
starten, fertig. Das Flatpak holt es **einmal beim ersten
Start**: aus einer benannten Quelle, mit Prüfsumme, und erst nachdem du
zugestimmt hast. Wer gerade kein WLAN hat, lehnt ab und holt es ein
andermal. **Danach ist beides gleich offline.**

*maschera* ist italienisch für **Maske** — und trägt die Landeskennung
**CH** in der Mitte.

- Website: [www.maschera.ch](https://www.maschera.ch)
- Quellcode: [github.com/semprerudi/maschera](https://github.com/semprerudi/maschera)
- Modell: [semprerudi/maschera-ch-v63b](https://huggingface.co/semprerudi/maschera-ch-v63b)
- Fehler melden: [Issues](https://github.com/semprerudi/maschera/issues)

> ⚠️ **Pseudonymisierung, nicht Anonymisierung.** Solange das Wörterbuch
> existiert, ist der Vorgang umkehrbar — und die Daten bleiben nach revDSG
> Personendaten. Deshalb heisst der Knopf «Maskieren».

Aufbauend auf [rizzo-pii](https://github.com/Rizzo-AI-Academy/rizzo-pii)
von Simone Rizzo (MIT). Keine Verbindung zum Originalprojekt, keine
Markenrechte an "Rizzo AI Academy" beansprucht.

## Wie gut ist es?

Das mitgelieferte Modell (`runs/ch-v63b`) wurde auf zwei Arten geprüft.
**Beide Ergebnisse stehen hier — auch das weniger schöne.**

| | Übungstexte (synthetisch) | echte Dokumente (Golddokumente) |
|---|---|---|
| Umfang | 2000 erzeugte Texte, 29 210 Personenangaben (Goldspannen) | 9 echte Dokumente, 280 Personenangaben (Goldspannen) |
| **Sichtbar geblieben** (Leckrate) | **0,02 %** — 13 Angaben ganz oder teilweise übersehen | **1,27 %** — 6 Angaben ganz oder teilweise übersehen |
| Gesamtnote (Micro-F1, 1 = perfekt) | 0,997 | 0,736 |
| Zu viel verdeckt | 84 Stellen | 95 Stellen |
| Kann jeder nachprüfen | **ja** | **nein** |

Die **Leckrate** ist der Anteil der Buchstaben und Ziffern aus
Personenangaben, die nach dem Maskieren noch lesbar sind. Die
**Gesamtnote** fasst zusammen, wie oft MASCHERA die richtigen Stellen
findet und wie oft es danebengreift.

**Die Übungstexte** erzeugt MASCHERA selbst, aus Mustervorlagen und
Namenslisten. Wer den Quellcode hat, bekommt mit diesem Befehl genau
dieselben Zahlen:

```fish
python3 tools/mess_synthetisch.py --model runs/ch-v63b --n 2000
```

Die Zahlen in der Tabelle sind so mit MASCHERA 1.0.1 gemessen. Die Texte
hängen von den Vorlagen und vom Erzeuger ab: ändern sich diese, ändern sich
die Zahlen mit, und die Tabelle muss neu gemessen werden.

⚠️ **Die Übungstexte sind dem Modell vertraut.** Sie sind nach denselben
Vorlagen gebaut wie die Texte, mit denen es gelernt hat. Die Namen und
Nummern darin hat es allerdings nie gesehen — es muss sie also wirklich
erkennen und kann sie nicht auswendig wissen. Echte Briefe sind trotzdem
schwieriger. Deshalb gibt es die zweite Messung.

**Die echten Dokumente** sind neun Schreiben, in denen jede
Personenangabe von Hand markiert ist. Weil sie echte Personendaten
enthalten, werden sie nicht veröffentlicht — diese Zahl kann niemand
nachprüfen. Sie ist aber die ehrlichste. Wie du eigene Testdokumente
anlegst: `docs/GOLDDOKUMENTE.md`.

⚠️ **Neun Dokumente sind wenig.** Unterscheiden sich zwei Modelle in der
Gesamtnote um weniger als etwa 0,06, ist das bei so wenigen Dokumenten
Zufall und keine Verbesserung.

**Was das für dich heisst:** In echten Dokumenten bleibt gut ein Prozent
der Personenangaben sichtbar, nicht null. MASCHERA nimmt dir die Arbeit
ab, nicht die Verantwortung — **sieh den maskierten Text an, bevor du ihn
weitergibst.** Dafür zeigt Bereich 02 jede Fundstelle farbig, mit ihrer
Herkunft.

⚠️ **Zu viel verdeckt ist kein Leck.** Ein Wort zu viel verdeckt macht den
Text etwas schlechter lesbar; ein Wort zu wenig gibt eine Personenangabe
preis. Im Zweifel verdeckt MASCHERA deshalb lieber zu viel.

## Das Modell

`ch-v63b`, ein feinjustiertes **ModernBERT** (`jhu-clsp/mmBERT-base`),
22 Schichten, 308 Mio Parameter. Trainiert auf **synthetischen** Daten,
die aus den Vorlagen und Nomenklaturen dieses Repositoriums erzeugt
werden — es hat nie ein echtes Dokument gesehen.

Die Gewichte liegen auf Hugging Face unter **MIT**:
[semprerudi/maschera-ch-v63b](https://huggingface.co/semprerudi/maschera-ch-v63b).
Sie sind nicht Teil dieses Repositoriums — 1,2 GB gehören nicht in Git.

**Der Trainingsweg ist offen.** Die Trainingsdaten liegen nicht als
Datei bei, sie werden ERZEUGT — Vorlagen, Nomenklaturen und Erzeuger
stehen in diesem Repositorium:

```fish
python3 tools/generate_dataset.py --n 40000 --rauschen 0.08 \
        --zone training --seed 2026 --out dataset.jsonl
python3 tools/generate_dataset.py --n 2000 --rauschen 0.08 \
        --zone halten --seed 63 --out eval.jsonl
python3 train.py --data dataset.jsonl --eval-data eval.jsonl \
        --out runs/eigenes --max-length 512 --seed 4711
```

### Womit `ch-v63b` trainiert wurde

Gelesen aus `training_args.bin` des ausgelieferten Laufs, nicht aus den
Vorgaben abgeschrieben:

| | |
|---|---|
| Epochen | 3 |
| Lernrate | 3e-5, linear, warmup 0.1 |
| Stapel | 8 × 2 (Gradientensammlung) |
| Gewichtszerfall | 0.01 |
| Rechengenauigkeit | bf16 |
| max_length | 512 |
| **Keim des Trainings** | **4711** |

⚠️ **`train.py` hat als Vorgabe den Keim 2026**, der ausgelieferte Lauf
benutzte **4711** — ohne `--seed` entsteht ein anderes Modell.

⚠️ **Der Keim des TRAININGSSATZES ist nicht überliefert.**
`training_args.bin` hält nur fest, wie trainiert wurde, nicht, woraus.
Der Befehl oben nennt darum 2026; das ist eine Empfehlung für den
Nachbau, **keine Angabe über den ausgelieferten Lauf**. Der Weg ist
begehbar, die Spur des einen Laufs ist es nicht ganz. Künftige Läufe
schreiben beides mit — `generate_dataset.py` legt seinen Keim in den Kopf
der `.jsonl`.

⚠️ **`--zone` ist nicht optional.** Ohne sie ziehen Trainings- und
Auswertungssatz aus derselben Nomenklatur, und die Zahlen liessen sich
mit «erkennt Namen» und mit «hat die Liste auswendig» gleich gut
erklären.

⚠️ **Und derselbe Keim genügt nicht.** Ändert sich der Erzeuger, ergibt
derselbe Befehl einen anderen Datensatz — der Code-Stand gehört zur
Angabe.

⚠️ **`--ohne-modell` ist kein Betriebszustand.** Ohne Modell greifen nur
Prüfsummen und Muster, und jeder Name geht durch. Die Kommandozeile
lässt es für Messungen zu und sagt es dabei.

## Installieren

Drei Wege unter Linux, ein Installer für Windows und ein Datenträgerabbild für macOS. Sie unterscheiden sich
in genau einer Frage: **fährt das Modell mit, oder wird es beim ersten
Start geholt?**

| | Paket | Modell | Für wen |
|---|---|---|---|
| **AppImage** | rund 1,7 GB | fährt mit | eine einzige ausführbare Datei; keine Installation, keine Abhängigkeiten |
| **Flatpak** | rund 0,3 GB, dazu die KDE-Laufzeit von Flathub | wird geholt, 1,2 GB | Debian, Ubuntu, Fedora, openSUSE, Arch — überall, wo Flatpak läuft |
| **Windows-Installer** | rund 1,4 GB | fährt mit | Windows 11, 64 Bit; installiert ohne Administratorrechte |
| **macOS-Abbild** | rund 1,4 GB | fährt mit | Macs mit Apple-Chip (M1 oder neuer); nicht signiert |
| **Docker** | rund 4,2 GB | fährt mit | Betrieb als Dienst; Oberfläche im Browser |

Wird das Modell geholt, **fragt der erste Start vorher**: er nennt
Quelle, Grösse und Ziel, und «Später» schliesst die Anwendung wieder,
ohne etwas zu laden. Danach läuft alles ohne Netz.

AppImage und Flatpak bringen ihre eigenen Bibliotheken mit und sind
dadurch unabhängig davon, was auf dem System sonst installiert ist.

### Herunterladen

Die fertigen Dateien liegen bei den
[Releases](https://github.com/semprerudi/maschera/releases/latest).

```fish
chmod +x MASCHERA-latest-x86_64.AppImage
./MASCHERA-latest-x86_64.AppImage
```

```fish
flatpak install --user MASCHERA-latest-x86_64.flatpak
flatpak run ch.maschera.Maschera
```

Das Flatpak holt die KDE-Laufzeit beim Installieren von Flathub.

Unter Windows `MASCHERA-latest-x64-setup.exe` starten. Der Installer ist
nicht signiert, deshalb warnt Windows beim ersten Start: «Weitere
Informationen» → «Trotzdem ausführen».

Unter macOS (nur Apple-Chip) `MASCHERA-latest-arm64.dmg` öffnen und `MASCHERA`
in *Programme* ziehen. Die App ist nicht signiert, und neuere macOS-Fassungen
lassen sie sich nicht per Rechtsklick öffnen. Einmal in *Terminal* die
Quarantäne-Markierung entfernen:

```fish
xattr -dr com.apple.quarantine /Applications/MASCHERA.app
```

Der macOS-Bau ist neu und bisher auf einem Mac getestet. In der App ist nicht
bestätigt, dass der Knopf «Kopieren und … öffnen» den Dienst dort öffnet; falls
nichts aufgeht, den Dienst von Hand öffnen — der Text liegt in der Zwischenablage.

### Docker

Ein fertiges Abbild, rund 4,2 GB, das Modell fährt mit:

```fish
docker run -d --name maschera -p 127.0.0.1:4141:4141 \
    ghcr.io/semprerudi/maschera:1.0.3
```

Danach im Browser `http://127.0.0.1:4141` öffnen. Der Server speichert
nichts: kein Dokument, kein Wörterbuch, kein Protokoll. Wer eigene Regeln
und Einstellungen über einen Neustart behalten will, ergänzt
`-v maschera-config:/home/maschera/.config/maschera`. Hinter einem Proxy
oder unter einem anderen Namen als `127.0.0.1` gehört `MASCHERA_WIRT`
gesetzt — siehe `tools/paket/LIESMICH.md`.

### Downloads prüfen

Jedes Release trägt `SHA256SUMS`. Neben die heruntergeladenen Dateien legen
und prüfen:

```fish
sha256sum -c --ignore-missing SHA256SUMS
```

Unter macOS gibt `shasum -a 256 MASCHERA-latest-arm64.dmg` die Summe aus, die du
mit der passenden Zeile in `SHA256SUMS` vergleichst.

Das Docker-Abbild ist ab 1.0.2 signiert (ohne eigenen Schlüssel, mit
[cosign](https://github.com/sigstore/cosign)); 1.0.1 ist es nicht. Die Signatur
gehört zur `noreply`-Adresse des GitHub-Kontos, derselben wie auf den Commits:

```fish
cosign verify ghcr.io/semprerudi/maschera:latest \
    --certificate-identity 30689933+semprerudi@users.noreply.github.com \
    --certificate-oidc-issuer https://github.com/login/oauth
```

Zu jedem Release seit 1.0.1 gehören eine SBOM (SPDX) für das Docker-Abbild
und eine für das AppImage.

### Selbst bauen

```fish
fish tools/paket/appimage_bauen.fish          # AppImage
flatpak-builder --user --install \
    --state-dir bau/zustand bau/ziel \
    tools/paket/ch.maschera.Maschera.yml      # Flatpak
fish tools/paket/bauen.fish                   # Docker
```

```powershell
.\.venv\Scripts\python.exe tools\paket\windows_bauen.py   # Windows, unter Windows
```

`tools/paket/LIESMICH.md` beschreibt jeden Weg samt den Entscheiden
dahinter, auch wie das Modell für AppImage und Docker geholt wird.
`WINDOWS.md` beschreibt den Windows-Bau, wie er gelaufen ist; `MACOS.md`
beschreibt den macOS-Bau, der auf GitHub läuft (Workflow `macOS-Bau`, von Hand gestartet).

## Sofort loslegen

```fish
python3 tools/run_tests.py
```

Dreiunddreissig Prüfungen, keine Abhängigkeiten ausser PyYAML und Flask.
Kein Modell, keine GPU, keine Downloads nötig — **zweiunddreissig laufen in einem
frischen Klon sofort durch.**

Die dreiunddreissigste braucht das Modell und sagt es; zwei weitere lassen je
einen Punkt aus, solange die Nomenklatur nicht gebaut ist
(`python3 packs/ch/nomenclatures/build.py`). Beides steht in der Ausgabe
— **eine übersprungene Prüfung hat nichts geprüft**, und der Läufer
zählt sie nicht als bestanden.

```fish
python3 tools/generate_dataset.py --n 20 --show
```

Erzeugt Trainingsbeispiele aus den Vorlagen — zeigt, wie das Ergebnis aussieht.

## Vollständige Beschreibung

`SPEC.md` beschreibt, was das Werkzeug ist und was es nicht ist.
`docs/API_OBERFLAECHE.md` ist der massgebliche Vertrag der Endpunkte.
`docs/ARCHITEKTUR.md` führt die getroffenen Entscheide und die bekannten
Schwächen.

## Aufbau

```
packs/ch/          Alles Schweizspezifische
  taxonomy.yaml      45 Tags, eingefrorene BIO-Reihenfolge  <- Quelle der Wahrheit
  patterns.yaml      Regexe mit viersprachigen Kontextankern
  macros.yaml        gekoppelte Slotgruppen (@address, @person)
  pack.yaml          Manifest, Labelvertrag-Hash, Backbone
  adapter.py         Schnittstelle des Packs
  validators/        Prüfsummen (AHV, UID, IBAN, QR, Luhn, GLN)
  generators/        gültige Identifikatoren erzeugen
  nomenclatures/     build.py + Bezugsquellen (Daten NICHT im Repo)
  templates/         Vorlagen je Sprache

core/              Sprachunabhängige Mechanik
  recognizers.py     Regex + Anker + Prüfsummen
  masking.py         Maskierung, Wörterbuch, Propagation
  injector.py        Vorlage + Nomenklatur -> Trainingsbeispiel
  alignment.py       Zeichenspanne <-> BIO (tokenizer-unabhängig)
  evaluate.py        Leckrate, entitätsweise Metriken
  inference.py       die drei Stufen zusammengeführt

app/               Oberfläche und Dienst
tools/             Werkzeuge
  run_tests.py         alle Prüfungen
  check_taxonomy.py    Labelvertrag
  generate_dataset.py  Trainingsset erzeugen
  verify_tokenizer.py  Tokenizer-Annahmen prüfen (braucht transformers)
  mess_synthetisch.py  die reproduzierbare Messung
  build_release.py     ONNX + INT8 (optional, nicht der Auslieferweg)
  paket/               AppImage, Flatpak, Docker

site/              die Projektseite (www.maschera.ch)

train.py           Training (braucht torch + GPU)
tests/             zweiunddreissig Prüfdateien
```

## Die eine Regel

Die Reihenfolge in `taxonomy.yaml` ist Vertrag. Neue Tags anhängen, nie
einfügen, nie umsortieren. Sonst mappen alte Checkpoints still auf falsche
Labels.

## Quellenangaben

Die Nomenklaturen stammen aus offenen Verwaltungsdaten. Alle verlangen eine
Quellenangabe; sie gehört in die Modellbeschreibung und in die App, nicht nur
hierhin.

- Nachnamen, Vornamen: Bundesamt für Statistik (BFS)
- Ortschaften mit PLZ, Strassen: Bundesamt für Landestopografie (swisstopo)
- Heimatorte: Bundesamt für Justiz (BJ/EJPD), eCH-0135
- Firmennamen: Zefix, Eidgenössisches Amt für das Handelsregister (EHRA),
  über LINDAS. Nutzungsbedingungen: Provide-the-Source (freie Nutzung,
  Quellenangabe Pflicht)

## Lizenz

**Quellcode MIT, ausgelieferte Pakete AGPL-3.0.** Welche wann gilt und
warum es zwei sind, steht in `LIZENZ.md`. Kurz: AppImage, Flatpak und
Docker-Abbild tragen PyQt6 (GPL-3) und PyMuPDF (AGPL-3) mit, der
Windows-Installer PyMuPDF; ein einziges
MIT über alles hätte etwas zugesagt, das die mitgelieferten Teile nicht
hergeben.

Die Modellgewichte stehen unter MIT.

## Wie es entstanden ist

Der Quellcode wurde mit Claude Code (Anthropic) geschrieben, unter
Anleitung und Verantwortung des Maintainers. Ab 1.0.1 tragen die Commits
eine Zeile `Co-Authored-By: Claude`.
