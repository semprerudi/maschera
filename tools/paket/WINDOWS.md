# MASCHERA für Windows

Wie aus diesem Baum ein Windows-Installer wird. Das Gegenstück zu
`appimage_bauen.fish` für Linux und zum `Dockerfile` für den Server.

⚠️ **Es steht kein Rechnername darin.** Das Rezept ist allgemeingültig;
welche Maschine dafür benutzt wird und wie man drankommt, gehört nicht in
das öffentliche Repository.

---

## 0. Was am Ende dasteht

| | |
|---|---|
| `dist\MASCHERA-<fassung>-x64-setup.exe` | ein Installer, rund 1,4 GB |
| installiert | ohne Administratorrechte in den Benutzerordner, rund 1,7 GB in gut 5000 Dateien |
| enthält | Python, das Modell `ch-v63b`, PyTorch (CPU), die Anzeigeschicht Edge (WebView2) |
| lädt im Betrieb | **nichts** — dieselbe Zusage wie bei der AppImage |

⚠️ **Die Gewichte fahren mit**, wie bei der AppImage: das Werkzeug ist nach
der Installation vollständig und war nie im Netz.

**Gemessen: Windows maskiert wie Linux.** Dieselbe synthetische Messung
(`tools/mess_synthetisch.py --n 200 --seed 7`) ergab auf beiden
Plattformen 0 Lecks bei 2978 Goldspannen, Micro-F1 0.996 und 10
Übermaskierungen — Tabelle für Tabelle gleich. Einzelne Etiketten können
an einer knappen Schwelle anders ausfallen (die CPU-Rechenbibliotheken
runden anders); an der Leckrate ändert das nichts.

---

## 1. Was auf die Maschine muss

Einmalig, danach alles über ssh.

| | wozu |
|---|---|
| **OpenSSH-Server** | der ganze Rest läuft darüber |
| **RustDesk** | zum **Hinsehen** — siehe Abschnitt 5 |
| **Python 3.13**, 64 Bit | die Laufzeit im Paket |
| **Inno Setup 6** | aus dem gebauten Verzeichnis einen Installer machen |
| **WebView2-Runtime** | die Anzeigeschicht; unter Windows 11 schon da |

```powershell
winget install Python.Python.3.13 JRSoftware.InnoSetup RustDesk.RustDesk
```

### OpenSSH einrichten

In einer PowerShell **als Administrator**:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
```

⚠️ **Hängt `Add-WindowsCapability` lange, steht es meist hinter einem
laufenden Windows-Update in der Schlange.** Abwarten; im Notfall über
*Einstellungen → Optionale Features* oder
`winget install Microsoft.OpenSSH.Preview`.

⚠️ **Die Shell für ssh:** Windows PowerShell 5.1 ist immer da und
funktioniert. PowerShell 7 aus dem **Store** liegt unter `WindowsApps` —
die kann der ssh-Server nicht starten, und er meldet dann nicht «Shell
fehlt», sondern nur «Permission denied». Der Grund steht allein im
Protokoll (`Get-WinEvent -LogName OpenSSH/Operational`).

```powershell
Set-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell `
  -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
```

⚠️ **Den Schlüssel für ein Administratorkonto** legt Windows nicht nach
`~/.ssh/authorized_keys`, sondern nach
`C:\ProgramData\ssh\administrators_authorized_keys`, als reiner
ASCII-Text und mit scharfen Rechten. Die Gruppe heisst je nach
Sprache anders; die SID ist sprachunabhängig:

```powershell
Set-Content -Path C:\ProgramData\ssh\administrators_authorized_keys `
  -Value "<öffentlicher Schlüssel>" -Encoding ascii
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r `
  /grant "*S-1-5-32-544:F" /grant "*S-1-5-18:F"
```

⚠️ **Läuft ssh ins Leere, obwohl `ping` antwortet:** das Netz ist als
*Öffentlich* eingestuft, die ssh-Regel der Firewall gilt nur für
*Privat*.

```powershell
Set-NetConnectionProfile -InterfaceAlias Ethernet -NetworkCategory Private
```

---

## 2. Der Baum

Der Quellcode aus diesem Repository, dazu das Modell unter `runs\ch-v63b\`
(nicht im Repository — 1,2 GB gehören nicht in Git):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install huggingface_hub
.\.venv\Scripts\hf.exe download semprerudi/maschera-ch-v63b --local-dir runs\ch-v63b
```

---

## 3. Die Abhängigkeiten — torch zuerst, vom CPU-Index

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r tools\paket\requirements-paket.txt pywebview pyinstaller pystray pillow
```

⚠️⚠️ **PYTORCH MUSS DIE CPU-FASSUNG SEIN.** `requirements-paket.txt` nennt
den CPU-Index nur als `--extra-index-url` — das **ergänzt** PyPI, es
ersetzt es nicht. Auf einer Maschine mit Grafikkarte fällt ein Fehlgriff
nicht auf, weil die CUDA-Fassung dort läuft; sie bringt nur über 2 GB
Bibliotheken in den Installer. Deshalb torch zuerst, ausdrücklich vom
CPU-Index. `windows_bauen.py` prüft es und bricht ohne `+cpu` ab.

---

## 4. Bauen

```powershell
.\.venv\Scripts\python.exe tools\paket\windows_bauen.py
```

Das Skript:

1. liest die Fassung aus `app/serve.py` — die einzige Quelle — und gibt sie
   an Inno Setup weiter;
2. prüft, dass torch die CPU-Fassung ist und das Modell daliegt;
3. friert mit PyInstaller nur `tools/paket/windows_start.py` ein. Der
   Quellcode liegt **unverändert als Daten** daneben und wird von dort
   ausgeführt, wie in der AppImage — so stimmen alle Pfade, die
   `app/fenster.py` und `app/serve.py` aus ihrem eigenen Ort ableiten, und
   Windows führt denselben Code aus wie Linux. Damit PyInstaller trotzdem
   jede Bibliothek einpackt, sammelt das Skript alle Importe aus dem
   Quellcode (`_importe.py`) — eine Liste, die mit dem Code mitwächst.
   Mit fährt nur, was die Laufzeit liest: aus `tools/` drei Dateien, und
   nichts, was in `tools/paket/draussen.txt` steht (Nomenklaturen,
   Vorlagen, Generatoren, Messdokumente, `core/injector.py`) — dieselbe
   Auswahl wie Server, AppImage, Flatpak und Arch
   (`tests/test_fenster.py` Punkt 12);
4. schnürt mit Inno Setup (`tools/paket/maschera.iss`) den Installer.

Dauer auf einer schnellen Maschine: rund sechs Minuten.

⚠️ **Das Modell liegt unkomprimiert im Installer.** Gewichte lassen sich
kaum komprimieren; sie zu packen kostete beim Bauen und beim Installieren
Minuten für fast nichts.

---

## 5. Prüfen — und was ssh **nicht** kann

⚠️⚠️ **DAS FENSTER LÄSST SICH ÜBER SSH NICHT ANSEHEN.** Bauen geht fern,
hinsehen nicht. Dafür RustDesk oder jemand an der Maschine:

| | erwartet |
|---|---|
| Installieren | ohne Administratorrechte; SmartScreen warnt, weil der Installer nicht signiert ist |
| Start | Startbildschirm, dann die Oberfläche — kein Download-Angebot |
| Beispiel → Maskieren → Übernahme | Fundstellen farbig, Prompt übernommen |
| Kopieren, Herunterladen, Rechtsklick | funktionieren unter Edge ohne eigene Eingriffe — einzeln zu bestätigen |
| Zweiter Start | kein zweites Fenster |
| Schliessen | der Prozess endet |

---

## 6. Was unter Windows anders ist

**Die Anzeigeschicht ist Edge (WebView2), nicht Qt.** Unter Linux richtet
`app/fenster.py` vier Dinge an der Qt-Schicht von pywebview (Zwischenablage,
Herunterladen, Fenstersymbol, Ablagefach). Unter Windows entfallen sie; der
Start sagt das, statt eine Warnung auszugeben, die dort nicht stimmt.

**Der Infobereich (Tray) läuft über `pystray`**, nicht über Qt: Symbol aus
derselben Maske, Linksklick holt das Fenster hervor, das Menü trägt
«Fenster zeigen» und «Beenden». Mit eingeschaltetem Tray versteckt das X
das Fenster; ohne Symbol gibt es das Schliessen frei, die App wird nie
unsichtbar und unerreichbar. Einen zweiten Start meldet der laufende
Prozess einem kleinen Faden, der das Fenster hervorholt — unter Linux tut
das ein Qt-Zeitgeber. `tests/test_fenster.py` Punkt 24 prüft beides an
Attrappen.

⚠️ **Ein `js_api`-Objekt darf nichts Öffentliches tragen ausser seinen
Methoden.** pywebview reicht jedes öffentliche Feld an die Seite weiter und
steigt dafür hinein. Unter Windows ist das Fensterobjekt ein .NET-Objekt mit
endlos verschachtelten Eigenschaften
(`native.AccessibilityObject.Bounds.Empty.Empty…`): das Fenster reagiert
nicht mehr, der Prozess wächst, bis der Speicher voll ist, und überlebt das
Schliessen. `tests/test_fenster.py` Punkt 23 hält die Brücke zum
Startbildschirm deshalb auf ihre vier Methoden fest.

**Die Einstellungen** liegen unter `%APPDATA%\maschera`, ein geholtes
Modell unter `%LOCALAPPDATA%`. `tests/test_modell.py` Punkt 11 prüft beide
Wege auf Linux.

**Nur eine laufende Instanz** über eine Datei mit Portnummer und einen
Horcher auf 127.0.0.1 statt eines Unix-Sockels. `tests/test_modell.py`
Punkt 10 lässt beide Wege auf Linux durchlaufen.

---

## 7. Verteilen

| Kanal | Stand |
|---|---|
| **GitHub-Releases** | der Weg für den Anfang |
| **winget** | machbar: ein YAML-Manifest als Pull Request gegen `microsoft/winget-pkgs`, das auf den Installer samt Prüfsumme zeigt |
| **Microsoft Store** | braucht ein Partner-Center-Konto und MSIX; bringt gegenüber winget wenig |

⚠️ **Der Installer ist nicht signiert.** SmartScreen warnt beim ersten
Start («Weitere Informationen → Trotzdem ausführen»). Ein Zertifikat zur
Codesignatur behebt das; es kostet jährlich.

---

## 8. Die Lizenz

Der Quellcode steht unter MIT, das **gebaute** Paket unter AGPL-3.0 — wie
bei der AppImage und aus demselben Grund: PyMuPDF ist AGPL-3. `LIZENZ.md`
gilt unverändert.
