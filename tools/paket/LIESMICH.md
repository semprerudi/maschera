# MASCHERA verpacken — Docker, AppImage, Flatpak

Die Fassung steht an einer Stelle: `VERSION` in `app/serve.py`. Alle
Bauskripte lesen sie dort über `tools/paket/fassung.fish`.

| | |
|---|---|
| `Dockerfile` | das Abbild. Bau-Kontext ist der **Projektstamm** |
| `compose.yaml` | Betrieb mit Docker Compose. Port nur auf 127.0.0.1 |
| `bauen.fish` | baut das Abbild und hinterlegt die Fassung für `compose` |
| `requirements-paket.txt` | die Laufzeit des Pakets — mit torch, begründet |
| `appimage_bauen.fish` | baut die AppImage nach `dist/` |
| `AppRun`, `maschera.desktop` | der Start der AppImage |
| `ch.maschera.Maschera.yml` | das Flatpak |
| `.dockerignore` | im Projektstamm. **Eine Sperre, keine Aufräumhilfe** |

---

## Docker

### Das Modell holen

Die Gewichte sind nicht im Repository — 1,2 GB gehören nicht in Git. Das
Abbild erwartet sie unter `runs/ch-v63b` im Projektstamm:

```fish
hf download semprerudi/maschera-ch-v63b --local-dir runs/ch-v63b
```

`.dockerignore` lässt aus `runs/` **nur** dieses eine Verzeichnis in den
Bau-Kontext.

### Bauen

```fish
fish tools/paket/bauen.fish
```

**Rund 4 GB auf der Platte, 1,4 GB komprimiert übertragen.** Woraus:

| | |
|---|---|
| `runs/ch-v63b` | 1,26 GB — das Modell, **torch statt ONNX** |
| Abhängigkeiten | 1,23 GB — torch 746 MB, transformers 109, sympy 72, pymupdf 64 |
| Python-Unterbau | rund 130 MB |
| MASCHERA selbst | unter 1 MB |

⚠️ **Warum torch und nicht ONNX.** Gemessen wird mit torch; derselbe Weg
wird ausgeliefert. Zwei Läufer mit zwei Verhalten sind eine Quelle von
Lecks, die keine Messung sieht — der eine Weg wäre gemessen und der
andere ausgeliefert. Die vollständige Begründung und die Messung stehen
in `requirements-paket.txt`.

⚠️ **Der Benutzer wird VOR dem Kopieren angelegt** und mit `--chown`
kopiert. Ein `chown -R` danach ändert jede Datei, und Docker schriebe
das ganze Modell ein zweites Mal in eine neue Schicht.

### Betreiben

```fish
docker compose -f tools/paket/compose.yaml up -d
```

Danach hört der Dienst auf `127.0.0.1:4141` **des Wirts** — und sonst
nirgends.

### Prüfen, dass es wirklich läuft

```fish
docker inspect --format '{{.State.Health.Status}}' maschera
```

Und die Kette selbst — die Prüfsumme muss greifen, nicht nur das Modell:

```fish
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"text":"Planzer Paket AG in Lugano, AHV 756.9217.0769.85"}' \
  http://127.0.0.1:4141/api/anonymisieren
```

Erwartet: `[ORG_1], AHV [AHVN13_1]`.

Und dass die Einstellungen einen Neustart überleben:

```fish
curl -s -X PUT -H "Content-Type: application/json" \
  -d '{"vorlagen":[{"name":"Probe","text":"kurz"}]}' \
  http://127.0.0.1:4141/api/vorlagen
and docker compose -f tools/paket/compose.yaml restart
and curl -s http://127.0.0.1:4141/api/vorlagen
```

Das Verzeichnis für die Einstellungen muss im Abbild existieren und dem
Benutzer `maschera` gehören, **bevor** `VOLUME` es benennt — sonst legt
Docker das Volumen als root an, und der Dienst darf nicht hineinschreiben.

### Aktualisieren

Am einfachsten wird dort gebaut, wo der Dienst läuft:

```fish
git pull
and fish tools/paket/bauen.fish
and docker compose -f tools/paket/compose.yaml up -d
```

Soll dort nicht gebaut werden:

```fish
docker save maschera:<fassung> | zstd -T0 \
  | ssh <ziel> 'zstd -d | docker load'
```

---

## ⚠️ Was der Betrieb auf einem anderen Rechner ändert

MASCHERA ist dafür entworfen, dass **der Klartext auf der Maschine
bleibt, auf der die Datei liegt.** Läuft der Dienst auf einem anderen
Rechner, gilt das nicht mehr — die Dokumente reisen dorthin. Das ist
kein Fehler, aber ein anderes Sicherheitsmodell, und es gehört gewusst
statt vorausgesetzt.

| | |
|---|---|
| **Keine Anmeldung** | Das Werkzeug hat keine. `app/app.py` warnt beim Start ausdrücklich. Ohne Proxy mit Anmeldung kann jeder, der den Namen kennt, Personendaten hochladen |
| **Einstellungen sind gemeinsam** | Regeln, Vorlagen und Vorlieben liegen in **einem** Verzeichnis. Bei mehreren Nutzern sieht jeder die Regeln aller |
| **Ein Dokument zur Zeit** | Eine Sperre um die ganze Kette. Zwei gleichzeitige Anfragen warten aufeinander |

### Die wichtigste Zeile

```yaml
ports:
  - "127.0.0.1:4141:4141"
```

Ohne das `127.0.0.1:` veröffentlicht Docker den Port auf **allen**
Schnittstellen — **und zwar an der Firewall vorbei**, weil Docker seine
Regeln in die Kette `DOCKER` einhängt und nicht in `INPUT`. Eine
ufw-Regel, die den Port sperrt, wirkt dann nicht. Das ist der häufigste
Weg, einen Dienst versehentlich ins Netz zu stellen, und er sieht in der
Konfiguration nach nichts aus.

Der Dienst bindet **im Container** auf `0.0.0.0` — das muss er, sonst ist
er nicht einmal für den Proxy davor erreichbar. Der Schutz sitzt eine
Ebene höher.

### Der Proxy davor

Wer MASCHERA im Netz anbietet, stellt einen Reverse Proxy **mit
Anmeldung** davor und trägt dessen Namen in `MASCHERA_WIRT` ein
(`tools/paket/.env`, Vorlage `.env.beispiel`). Der Dienst weist jeden
Namen ab, den er nicht kennt — Schutz gegen DNS-Rebinding.

Ein Beispiel mit Caddy:

```caddyfile
maschera.example.ch {
    basicauth {
        # Hash erzeugen mit: caddy hash-password
        anwender <BCRYPT-HASH>
    }
    # 50 MB: grosse PDF und Mailarchive laufen sonst in ein 413,
    # und die Meldung sagt dann nicht, woran es lag.
    request_body {
        max_size 50MB
    }
    reverse_proxy 127.0.0.1:4141
}
```

⚠️ **`basicauth` ist das Mindeste, nicht das Richtige.** Es schützt gegen
Vorbeikommende, nicht gegen einen ernsthaften Angreifer, und es hat keine
Sitzungsverwaltung. Für ein Werkzeug, das Personendaten entgegennimmt,
ist eine echte Anmeldung — OIDC, mTLS, oder gar kein öffentlicher Name —
der Massstab.

⚠️ **Prüfen, dass die Anmeldung wirklich greift.** Bei manchen Proxys
lässt ein falsch geschriebener Name einer Middleware die Anfrage still
durch — die Anmeldung fehlt dann einfach, ohne Fehlermeldung. Nach dem
ersten Start von aussen aufrufen: es muss eine Anmeldung kommen, nicht
die Anwendung.

---

## Was im Abbild NICHT ist

| | warum |
|---|---|
| `packs/*/nomenclatures/` | rund 100 MB, und **die Laufzeit liest sie nicht**. Nur `core/injector.py` greift darauf zu, und der erzeugt synthetische Trainingsdaten |
| `runs/*` ausser `ch-v63b` | andere Trainingsläufe |
| `release/` | der ONNX-Bau |
| `*.jsonl` | Trainingsdaten |
| `tests/`, `docs/`, `beispiele/` | Entwicklung |

⚠️ Aus `tools/` gehen **drei** Dateien mit: `dokumente.py`,
`filter_document.py` und `evaluate_model.py` (dort steht `TorchScorer`).
`evaluate_model` wird erst im Rumpf von `Zustand.__init__` geholt; ein
blosses `import serve` findet es nicht. Fehlt eine, stirbt der Container
erst beim **Start**, nicht beim Bauen. `tests/test_fenster.py` Punkt 12
hält alle Verpackungen gegen die Importe in `app/`.

---

## Die AppImage

```fish
fish tools/paket/appimage_bauen.fish
```

Ergebnis: `dist/MASCHERA-<fassung>-x86_64.AppImage`, **rund 1,7 GB**.
Eine Datei, kein root, kein Paketmanager, läuft auf Arch wie auf Ubuntu.

Braucht `appimagetool` und `uv`, und das Modell unter `runs/ch-v63b`
wie beim Docker-Bau.

⚠️ **Warum `uv` und nicht das System-Python.** Eine AppImage wird zur
Laufzeit unter `/tmp/.mount_XXXXXX` eingehängt — der Pfad ist bei jedem
Start ein anderer. Ein `venv` trägt seinen Pfad **absolut** in
`pyvenv.cfg` und in jedem Startskript; er wäre nach dem Einhängen kaputt.
`uv` liefert ein eigenständiges, verschiebbares CPython, und die Pakete
gehen über `pip install --target` in ein Verzeichnis, das `AppRun` per
`PYTHONPATH` findet. Beides überlebt den Ortswechsel.

⚠️ **`HF_HUB_OFFLINE=1` und `TRANSFORMERS_OFFLINE=1` in `AppRun`.** Ohne
sie fragt `transformers` beim Start den Hub — ein Netzzugriff, den
dieses Werkzeug nicht macht.

⚠️ **Die AppImage öffnet ein eigenes Fenster, keinen Browser.**
`app/fenster.py` trägt den Dienst in einem Faden und das Fenster im
Hauptprogramm. Das ist kein Aussehen: MASCHERA verspricht, dass nichts
das Gerät verlässt, und ein Fenster mit Adresszeile, Lesezeichen und
Verlauf sagt das Gegenteil. Fehlt `pywebview`, **sagt** `fenster.py` das,
statt still in den Browser auszuweichen. `--im-browser` gibt es als
ausdrückliche Wahl.

Für Aktualisierungen über Gearlever und andere AppImage-Verwalter:
`MASCHERA_UPDATE_URL` in `tools/paket/.env` (siehe `.env.beispiel`).

### Adresse und Port

Beide kommen aus `~/.config/maschera/einstellungen.json` — **derselben
Datei**, die die Oberfläche unter «Einstellungen» schreibt. Vorgabe
`127.0.0.1:4141`. `tests/test_fenster.py` Punkt 5 hält fest, dass das
Fenster keinen eigenen Port wählt.

Lässt sich dort nicht binden — meist, weil MASCHERA schon läuft oder das
Docker-Paket den Port hält —, kommt ein kleiner Dialog: Adresse als
Textfeld, Port als Drehfeld, vorbelegt mit dem nächsten freien. **Die
Wahl wird sofort gesichert** und gilt beim nächsten Start.

⚠️ **Geprüft wird BINDEN, nicht Antworten.** Ein Port kann von einem
Dienst gehalten werden, der nicht antwortet, und dann scheitert der
Start trotzdem. **Beim Drücken wird nochmals geprüft:** zwischen
Vorschlag und Klick können Sekunden liegen.

---

## Flatpak

`ch.maschera.Maschera.yml` baut ein Flatpak für Debian, Ubuntu, Fedora,
openSUSE und alle anderen Distributionen mit Flatpak. Das Modell fährt
nicht mit: der erste Start holt es und **fragt vorher** — mit Quelle,
Grösse und Ziel.

⚠️ **Kein `.deb`, und der Grund ist gemessen.** Debian und Ubuntu
paketieren PyTorch, transformers und tokenizers nicht — ein `.deb` kann
seine Hauptabhängigkeit also nicht aus dem System beziehen. Das Flatpak
bringt seine Laufzeit selbst mit und deckt dieselben Distributionen in
**einem** Bauweg.

---

## Windows und macOS

`WINDOWS.md` und `MACOS.md` sind die Drehbücher dafür — Reihenfolge und
Begründung. Beide sind **noch nicht gelaufen**; jede sagt in ihrem
Abschnitt 6 ausdrücklich, was feststeht und was auf der Maschine erst
gemessen werden muss.
