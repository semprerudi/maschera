# Sicherheit

## Betrieb

| | |
|---|---|
| **Nur `127.0.0.1`** | `--host 0.0.0.0` ist möglich und warnt |
| **Serverseitig nichts aufbewahren** | der Dienst würde sonst zur Klartext-Datenbank |
| **Nichts nachladen** | keine Schriften, keine Bibliotheken von aussen. Benannte Ausnahmen: die Portprüfung, das Modell im Flatpak nach Zustimmung, «Nach Updates suchen» nur auf Klick über den Dienst |
| **Nichts senden** | `/api/senden` gibt es nicht; eingefügt wird von Hand |
| **Hinter einem Reverse Proxy** | nur mit Anmeldung davor; `MASCHERA_WIRT` nennt den Namen |

---

## Was das Werkzeug auf die Platte schreibt

> **Nichts wird geschrieben ausser den Einstellungen des Anwenders**, alle
> nach `~/.config/maschera/`, alle nur auf ausdrücklichen Befehl.

| Endpunkt | Datei |
|---|---|
| `PUT /api/regeln` | `regeln.yaml` |
| `PUT /api/vorlieben` | `klartext.json` |
| `PUT /api/vorlagen` | `vorlagen.json` |
| `PUT /api/einstellungen` | `einstellungen.json` |

⚠️ **Der zweite Satz ist der wichtigere:** kein Dokumentinhalt, kein
Wörterbuch, kein Protokoll. Eine hochgeladene Datei liegt nur für die Dauer des Lesens in
einem temporären Verzeichnis. Ein weiterer Fall, der
Text anfasst, ist durch diese Formulierung **nicht** gedeckt.

Alle vier prüfen gegen dieselbe Funktion, die später lädt. Eine abgelehnte
Eingabe lässt die bestehende Datei unberührt.

**Das Wörterbuch geht ebenfalls hinaus**, aber nicht über den Server:
«Vokabular herunterladen» erzeugt die Datei im Browser (`Blob`), der Dienst
sieht sie nie.

Dazu kommt ein Ort, der keine Einstellung ist: ein beim ersten Start
nachgeholtes Modell liegt unter `~/.local/share/maschera/modelle/`.

## Bedrohungen

| Bedrohung | Massnahme |
|---|---|
| Klartext verlässt das Gerät über MASCHERA | Kein Sendeweg im Code, `/api/senden` antwortet 404, `T-API-10` hält das fest |
| Eingeschleuster Code schickt Text fort | Kein `innerHTML` mit Serverdaten, kein `eval`, keine Inline-Skripte, dazu Content Security Policy auf jeder Antwort |
| Fremde Webseite spricht den lokalen Dienst an (DNS Rebinding) | Wirtsprüfung auf **allen** Endpunkten. `MASCHERA_WIRT` nennt weitere Namen, `*` schaltet sie mit lauter Warnung ab |
| Dienst ist im Netz erreichbar | Vorgabe `127.0.0.1`. `0.0.0.0` warnt, im Netz nur mit Anmeldung davor |
| Pfadausbruch beim Hochladen | Der Dateiname wird nie zum Pfad, auch keine Gerätenamen unter Windows |
| Fehlermeldungen verraten Serverdaten | Antworten nennen den Text einer Ausnahme nicht, er steht nur im Protokoll |
| Ein Leser übersieht einen Scan | Scan ohne Textebene ist ein Fehler mit Begründung, keine leere Meldung |
| Besonders schützenswerte Daten werden versehentlich Klartext | Tags mit `bspd` verlangen `auch_bspd` |
| Gefälschtes Modell | Fester Commit, Prüfsumme je Datei, nur `safetensors` |
| Gefälschtes Paket | SHA256SUMS, SBOM, Signatur des Docker-Abbilds mit cosign |
| Dependency Confusion | Keine zusätzliche Paketquelle. torch kommt einzeln als Datei ohne Abhängigkeiten, alles andere nur von PyPI |
| Präpariertes PDF greift den Decoder an (CVE-2026-111497) | Drei Stufen in `tools/dokumente.py`: Brotli-Namen vor dem Öffnen überschreiben, verdeckte Filter abweisen, Objekte und Ströme vor dem Textauszug prüfen, siehe EN-033 |
| Telemetrie einer Bibliothek | Abgeschaltet und per Prüfung festgehalten, onnxruntime ist nicht im Paket |
| Personendaten im öffentlichen Repository | Echte Dokumente liegen ausserhalb des Baums. Eine Wache prüft Pfade, Namen und interne Dateien vor jeder Veröffentlichung |

Das Verhalten beschreibt [07 API](07_api.md). Die Kopfzeilen jeder Antwort:

| Kopfzeile | Wert |
|---|---|
| `Content-Security-Policy` | `default-src`, `script-src`, `style-src`, `img-src` und `font-src` je `'self'`; `connect-src 'self'` plus Loopback; `object-src 'none'`; `base-uri 'none'`; `frame-ancestors 'none'`; `form-action 'self'` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `no-referrer` |

## Schwachstellen melden

Der Weg steht in `SECURITY.md`: private Meldung über GitHub, erste Antwort
innert 7 Tagen, keine echten Personendaten in einer Meldung. Unterstützt wird nur
die aktuelle Fassungsreihe.

## Was im Betrieb nicht zugesagt wird

- Die Pseudonymisierung ist keine Anonymisierung. Ein übersehener Wert geht
  hinaus. Der Anwender prüft vor dem Kopieren.
- Der Windows-Installer und die macOS-App sind nicht signiert.
- Vor dem produktiven Einsatz in einer Organisation gehört eine Beurteilung der
  zuständigen Datenschutzstelle dazu ([01 Ziele](01_ziele.md)).
