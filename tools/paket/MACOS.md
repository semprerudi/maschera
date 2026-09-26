# MASCHERA für macOS — das Drehbuch

Wie aus diesem Baum eine `.app` und ein `.dmg` werden. Das Gegenstück zu
`appimage_bauen.fish` für Linux und zu `WINDOWS.md`.

⚠️ **Diesen Bau gibt es noch nicht.** Wie beim Windows-Drehbuch ist das
hier die Reihenfolge und die Begründung, nicht der Bericht über einen
gelaufenen Bau. Abschnitt 6 trennt, was feststeht, von dem, was auf der
Maschine gemessen werden muss.

⚠️ **Kein Rechnername.** Das Rezept ist allgemeingültig; welche Maschine
und wie man drankommt, steht in `BETRIEB.md` und bleibt intern.

---

## 0. Was am Ende dasteht

| | |
|---|---|
| `MASCHERA-<fassung>.dmg` | rund 1,6 GB |
| enthält | `MASCHERA.app` mit Python, Modell `ch-v63b`, PyTorch (CPU) |
| lädt im Betrieb | **nichts** |
| signiert | **nein**, vorerst — siehe Abschnitt 7 |

---

## 0b. Fett oder schlank — und warum die AppImage anders ist

Es gibt **zwei** mögliche Zuschnitte:

| | Grösse | die Gewichte |
|---|---:|---|
| **fett** | ~1,6 GB | fahren im Paket mit |
| **schlank** | ~400 MB | werden beim **Einrichten** einmal geholt, mit Prüfsumme |

⚠️ **Danach ist beides gleich offline.** Der Unterschied liegt allein im
Einrichten; im Betrieb geht in keiner der beiden Fassungen etwas nach
aussen, und einen Endpunkt, der Text verschickt, gibt es nicht.

⚠️ **Die AppImage bleibt fett — ausdrücklich.** Sie ist *eine einzige
ausführbare Datei*: herunterladen, ausführbar machen, fertig. Das ist die
eleganteste Fassung des Werkzeugs, und das soll sie bleiben. Wer sie
schlank machte, tauschte diese Eigenschaft gegen ein paar hundert
Megabyte.

Für Windows und macOS ist die Wahl offen; für die Paketmanager
(`.deb`, AUR, winget) ist schlank die einzige, mit der man ernst genommen
wird.

### ⚠️ Der erste Start FRAGT — er lädt nicht einfach

Eine schlanke Fassung darf die 1,2 GB **nicht** von sich aus holen. Beim
ersten Start steht ein Dialog, und er hat zwei Antworten:

```
Für die Erkennung fehlt noch das Modell (1,2 GB).
Jetzt holen?            [ Jetzt holen ]   [ Später ]
```

**«Später» schliesst die Anwendung wieder.** Ohne Modell gibt es keinen
Betriebszustand — `--ohne-modell` ist eine Messhilfe der Kommandozeile
und nichts, was ein Anwender unbemerkt bekommen darf. Ein Fenster, das
sich ohne Modell bedienen lässt, ist eine Leckquelle mit grüner Anzeige.

⚠️ **Der Grund ist nicht Höflichkeit, sondern Mobilfunk.** Wer das nur
über WLAN tun will, ist vielleicht gerade nicht im WLAN. 1,2 GB über ein Datenabo sind ein echter Schaden, und ein
Programm, das ihn ungefragt anrichtet, hat sein Vertrauen verspielt —
bei einem Datenschutzwerkzeug doppelt.

⚠️ **Es ist derselbe Grundsatz wie beim Maskieren-Knopf.** Etwas, das von
selbst läuft, weil das Fenster aufgegangen ist, ist keine Entscheidung
mehr. Deshalb hat es einen Knopf, der die Handlung benennt.

Was der Dialog ausserdem können muss:

| | |
|---|---|
| **Quelle nennen** | woher geholt wird, sichtbar, nicht im Kleingedruckten |
| **Grösse nennen** | 1,2 GB, bevor geklickt wird |
| **Prüfsumme prüfen** | und bei Abweichung abbrechen, nicht «trotzdem» |
| **Abbrechen können** | ein halb geholtes Modell wird verworfen, nicht geflickt |
| **Wiederholbar sein** | wer «Später» wählt, bekommt beim nächsten Start dieselbe Frage |

⚠️ **Was noch fehlt, bevor «schlank» gebaut werden kann:** der Holweg
selbst — woher, mit welcher Prüfsumme, wohin, und was passiert, wenn die
Maschine kein Netz hat. Dazu gehört, dass die Zusage «es wird nichts
nachgeladen» im README, in `SPEC.md` und in der Hilfe **auf den Betrieb
eingegrenzt** wird. Eine Zusage zu präzisieren ist etwas anderes, als sie
aufzuweichen — aber sie muss geschrieben stehen, sonst ist sie beim
ersten Nachfragen unhaltbar.

---

## 1. Was auf die Maschine muss

| | wozu |
|---|---|
| **Remote Login** (ssh) | der ganze Rest läuft darüber |
| **RustDesk** | zum **Hinsehen** — siehe Abschnitt 5 |
| **Xcode Command Line Tools** | Compiler, `codesign`, `hdiutil` |
| **Homebrew** | Python und Kleinkram |
| **Python 3.12 oder 3.13** | die Laufzeit im Paket |
| **PyInstaller** | aus dem Baum eine `.app` machen |

*Entfernte Anmeldung* einschalten unter **Systemeinstellungen →
Allgemein → Teilen**. Zum Hinsehen eignet sich **RustDesk** — dasselbe
Werkzeug wie unter Windows, Vermittlerdienst selbst zu betreiben. Danach:

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.13 git create-dmg
```

⚠️ **Der Mac schläft.** Ein Bau über ssh, der mitten in der Nacht
abbricht, ist meist kein Fehler im Skript. `caffeinate -s` um den Bau
legen oder den Ruhezustand im Netzbetrieb abschalten.

---

## 2. Apple Silicon oder Intel — das ist eine Entscheidung, keine Einstellung

`arm64` und `x86_64` sind **zwei** Pakete. PyInstaller baut für die
Architektur, auf der es läuft; ein `universal2` ist nur so weit möglich,
wie **alle** Räder universal vorliegen, und PyTorch tut das nicht.

Also:

| Zielgruppe | Bau |
|---|---|
| Mac ab 2020 (M1 und neuer) | `arm64`, auf einem Apple-Silicon-Mac |
| ältere Intel-Macs | eigener `x86_64`-Bau, oder gar nicht |

⚠️ **Ein `arm64`-Paket läuft NICHT auf Intel.** Umgekehrt läuft ein
`x86_64`-Paket über Rosetta 2 auf Apple Silicon — langsamer, und bei
einem Werkzeug, das ein 308-Mio-Parameter-Modell rechnet, ist das
spürbar. Wer nur eines baut, baut `arm64` und sagt es im README.

---

## 3. Der Baum

```bash
git clone <adresse> maschera
cd maschera
python3.13 -m venv .venv
source .venv/bin/activate
```

Das Modell gehört nach `runs/ch-v63b/` und ist nicht im Repository.

---

## 4. Abhängigkeiten und Bauen

```bash
pip install -r tools/paket/requirements-paket.txt
pip install pywebview pyinstaller
```

⚠️ **PyTorch auf CPU prüfen, nicht annehmen** — die Begründung steht
ausführlich in `WINDOWS.md` Abschnitt 3 und gilt hier gleich:
`--extra-index-url` ergänzt PyPI und ersetzt es nicht.

```bash
python -c "import torch; print(torch.__version__)"
```

Dann:

```bash
pyinstaller --noconfirm --windowed --name MASCHERA \
  --add-data "app/static:app/static" \
  --add-data "packs:packs" \
  --add-data "runs/ch-v63b:runs/ch-v63b" \
  app/fenster.py

create-dmg --volname "MASCHERA" dist/MASCHERA.dmg dist/MASCHERA.app
```

⚠️ Die Fassung im Dateinamen kommt aus `VERSION` in `app/serve.py` und
wird **nicht** abgeschrieben. Eine zweite Zahl bleibt beim nächsten
Erhöhen zurück.

---

## 5. Prüfen — und was ssh **nicht** kann

```bash
curl http://127.0.0.1:4141/api/zustand
```

⚠️⚠️ **DAS FENSTER LÄSST SICH ÜBER SSH NICHT ANSEHEN**, und unter macOS
kommt etwas dazu: eine App, die über ssh gestartet wird, hat **keine
Fenstersitzung**. Sie startet entweder gar nicht oder ohne Anzeige, und
beides sieht aus wie ein Fehler im Paket.

Zum Hinsehen **RustDesk** benutzen. Bauen fern, prüfen über den
Bildschirm — dieselbe Grenze wie unter Windows.

---

## 6. Was VOR dem ersten Bau im Code zu ändern ist

### ✅ Kein Problem: die Pfade

`core/pfade.py` nimmt `~/.config/maschera/`. Unter macOS ist der
hausübliche Ort `~/Library/Application Support/`, aber `~/.config` ist
dort seit Jahren gebräuchlich und funktioniert. **Anders als unter
Windows ist hier nichts kaputt** — höchstens ungewohnt.

### ❓ Zu messen: der Einmal-Start

`core/einmalig.py` benutzt einen Unix-Sockel unter `XDG_RUNTIME_DIR`,
sonst `/tmp` mit `os.getuid()` im Namen. Beides gibt es unter macOS,
also läuft es — **aber `/tmp` wird dort nicht bei jedem Neustart
geleert** wie unter Linux. Eine Sockelleiche überlebt damit länger.
`laeuft_schon()` fängt das ab, weil es **verbindet** statt nachzusehen,
ob die Datei da ist; genau dafür ist es so gebaut. Zu prüfen, nicht
anzunehmen.

### ❓ Zu messen: die Anzeigeschicht

Unter Linux benutzt pywebview die **Qt**-Schicht, und `app/fenster.py`
repariert daran vier Dinge (Zwischenablage, Herunterladen, Ablagefach,
Symbol). Unter macOS nimmt pywebview eine andere. Welche, und was aus
den vier Eingriffen wird, ist hier **nicht nachgesehen**:

```bash
python -c "import webview; print(webview.platforms)"
```

⚠️ Diese Frage vor dem Bauen beantworten. Ein Paket, das aufgeht und
dessen Kopierknopf nichts tut, sieht fertig aus.

### ❓ Zu messen: das Ablagefach

Unter Linux ist es `QSystemTrayIcon`, und `tray` ist mit Absicht
**vorgabemässig aus**, weil es unter GNOME ohne Erweiterung kein
Ablagefach gibt. macOS hat eine Menüleiste, die anders funktioniert.

---

## 7. ⚠️ Gatekeeper — die Wahrheit über den ersten Start

**Diese App ist nicht signiert und nicht notarisiert.** Die
Notarisierung setzt ein Apple-Developer-Konto voraus (99 $ im Jahr), und
für die Beta wird es nicht angeschafft.

Das hat eine sichtbare Folge, und sie gehört ins README und nicht in eine
Fussnote: **beim ersten Doppelklick sagt macOS, die App sei beschädigt
oder stamme von einem nicht verifizierten Entwickler.** Sie ist es nicht.
Der Weg für den Anwender:

```
Rechtsklick auf MASCHERA.app  →  Öffnen  →  im Dialog nochmals Öffnen
```

Oder, wenn das Merkmal hartnäckig ist:

```bash
xattr -dr com.apple.quarantine /Applications/MASCHERA.app
```

⚠️ **Das ist ein schlechter erster Eindruck, und es ist der ehrliche
Preis der Entscheidung.** Bei einem Werkzeug, das für den Umgang mit
Personendaten wirbt, ist eine Warnung des Betriebssystems beim Start das
Letzte, was man will. Vor einer v1.0 für macOS gehört das
Konto angeschafft.

⚠️ **Homebrew Cask fällt damit vorerst weg.** Ein Cask setzt eine
notarisierte App voraus; bis dahin gibt es das `.dmg` von der eigenen
Seite. Der Mac App Store scheidet ohnehin aus — die Sandbox verträgt
sich nicht mit einem lokalen Dienst auf 127.0.0.1 samt eigenem Fenster.

---

## 8. Wenn das Konto später doch kommt

Dann kommen zwei Schritte dazu, und beide lassen sich über ssh
bedienen — mit einer Falle:

```bash
codesign --deep --force --options runtime \
  --sign "Developer ID Application: …" dist/MASCHERA.app
xcrun notarytool submit dist/MASCHERA.dmg --wait \
  --apple-id … --team-id … --password …
xcrun stapler staple dist/MASCHERA.dmg
```

⚠️ **Über ssh ist der Schlüsselbund GESPERRT.** `codesign` findet das
Zertifikat dann nicht und meldet einen Fehler, der nach einem fehlenden
Zertifikat aussieht und keiner ist. Vorher:

```bash
security unlock-keychain ~/Library/Keychains/login.keychain-db
```

Dieselbe Klasse wie `ssh -o BatchMode=yes`, das einmal «Permission
denied» meldete und daraus den falschen Schluss provozierte: **eine
Fehlermeldung, die unter der eigenen Zusatzbedingung entsteht, ist kein
Befund über das System.**

---

## 9. Die Lizenz ändert sich nicht

Quellcode MIT, das **gebaute** Paket AGPL-3.0 — PyMuPDF ist AGPL-3.
`LIZENZ.md` gilt unverändert.
