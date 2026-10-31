# Nichtfunktionale Anforderungen

Status: `verbindlich` ist durch Prüfung oder Grundsatz festgelegt, `gemessen` ist ein
aus der Messung aufgerundeter Sollwert, `offen` wartet auf einen Entscheid.

**Referenzprofil der Messung:** Intel Core Ultra 9, 16 logische Kerne, 12 Rechenfäden,
62 GB Speicher, nur CPU, torch 2.14, Modell `ch-v63b`, 30.10.2026. Text: das
synthetische Beispiel der App, mehrfach aneinandergehängt, Median aus drei Läufen.
⚠️ Die Laufzeiten hängen stark vom Zustand des Rechners ab: Unter fremder Last und im
Energieprofil «balanced» wurde derselbe Lauf mit 12 Rechenfäden rund zehnmal langsamer,
mit 6 Fäden blieb er bei den Werten unten (31.10.2026). Paketgrössen stammen vom
aktuellen Release. `python3 tools/mess_nfa.py --model runs/ch-v63b
--release <Tag>` misst erneut und vergleicht mit den Sollwerten hier.

## Leistung

### NFA-001 Modell laden

Sollwert unter 10 s. Gemessen 5.5 s. Status `gemessen`, `ohne Prüfung`.

### NFA-002 Kurzer Text

500 Zeichen unter 1 s. Gemessen 0.13 s. Status `gemessen`, `ohne Prüfung`.

### NFA-003 Dokument

5000 Zeichen unter 3 s. Gemessen 1.3 s. Status `gemessen`, `ohne Prüfung`.

### NFA-004 Langes Dokument

25 000 Zeichen unter 15 s. Gemessen 7.4 s. Die Dauer wächst etwa linear. Status
`gemessen`, `ohne Prüfung`.

### NFA-005 Keine Grafikkarte

Die Anwendung läuft auf der CPU. Status `verbindlich`. Prüfung: T-FENSTER-8.

### NFA-006 Keine Sperre bei langen Läufen

Fortschritt und Oberfläche bleiben während eines Laufs abfragbar. Status
`verbindlich`. Prüfung: T-API-15.

## Speicher und Grösse

### NFA-010 Arbeitsspeicher

Spitze unter 2 GB im Lauf über 25 000 Zeichen. Gemessen 1.65 GB. Status `gemessen`,
`ohne Prüfung`.

### NFA-011 Paket mit Modell

AppImage, Windows und macOS unter 2 GB. Gemessen 1.69, 1.45 und 1.46 GB. Status
`gemessen`, `ohne Prüfung`. Die Aufteilung steht in
[12 Pakete](12_pakete_release.md).

### NFA-012 Paket ohne Modell

Flatpak unter 0.5 GB. Gemessen 0.33 GB. Status `gemessen`, `ohne Prüfung`.

### NFA-013 Modell

Rund 1.2 GB, Grösse und Prüfsummen stehen in `packs/ch/modell.json`. Status
`verbindlich`. Prüfung: T-MODELL-8.

## Erkennungsgüte

### NFA-020 Vorrang für Lecks

Ein Leck wiegt schwerer als eine Übermaskierung. Bei einem Zielkonflikt gewinnt der
Recall. Status `verbindlich`. Prüfung: T-EVALUATE-2, T-EVALUATE-4.

### NFA-021 Fehlerbudgets

Schwellen `R` 0.30, `A` 0.50, `P` 0.70, Ausnahmen je Tag mit Messung. Status
`verbindlich`. Prüfung: T-INFERENCE-1, T-EVALUATE-7.

### NFA-022 Leckrate synthetisch

Unter 0.1 % der Spannen im Befehl aus dem README. Veröffentlicht sind 0.02 %. Status
`gemessen`, `ohne Prüfung`.

### NFA-023 Leckrate an Dokumenten

Ein Sollwert fehlt. Zahlen an Golddokumenten stehen nur dort, wo sie schon öffentlich
sind. Status `offen`, `ohne Prüfung`.

### NFA-024 Prüfsummen ohne Fehlalarm

Auf Prosa und Zufallsziffern keine falschen Treffer der Stufe 1. Status `verbindlich`.
Prüfung: T-PATTERNS-3, T-CH-CHECKSUMS-3.

## Datenschutz

### NFA-030 Lokal

Dokumente verlassen das Gerät nicht über MASCHERA. Status `verbindlich`. Prüfung:
T-API-10, T-APP-4, T-APP-6, T-APP-7.

### NFA-031 Nichts wird aufbewahrt

Kein Dokumentinhalt, kein Wörterbuch, kein Protokoll im Dienst. Status `verbindlich`.
Prüfung: T-APP-11, T-VORLIEBEN-1, T-MODELL-9.

### NFA-032 Keine Telemetrie

Keine Verbindung ohne Klick oder Zustimmung, auch nicht aus Bibliotheken. Status
`verbindlich`. Prüfung: T-FENSTER-31.

### NFA-033 Kein Nachladen

Keine Schriften, Skripte oder Bilder von aussen. Status `verbindlich`. Prüfung:
T-APP-6, T-SCHRIFTEN-4.

## Sicherheit

### NFA-040 Kopfzeilen

Jede Antwort trägt Content Security Policy, `nosniff`, `no-referrer`. Status
`verbindlich`. Prüfung: T-APP-21.

### NFA-041 Wirtsprüfung

Unbekannte `Host`-Namen werden abgewiesen. Status `verbindlich`. Prüfung: T-API-25.

### NFA-042 Modell nur als safetensors

Status `verbindlich`. Prüfung: T-MODELL-12, T-FENSTER-25.

### NFA-043 Eine Paketquelle

Status `verbindlich`. Prüfung: T-FENSTER-32.

### NFA-044 Kein Text wird Code

Kein `innerHTML` mit Serverdaten, kein `eval`, kein Inline-Skript. Status `verbindlich`.
Prüfung: T-OBERFLAECHE-39, T-APP-21, T-OBERFLAECHE-62.

### NFA-045 Aktuelle Abhängigkeiten

Bekannte Lücken gelten vor dem Release als Fehler, die Bauten holen das neueste
Python 3.13. Status `verbindlich`. Prüfung: T-FENSTER-29.

### NFA-046 Kein bekannt verwundbarer Decoder

Gibt es für eine Lücke in einer Bibliothek keine Fassung mit Fix, kommen Eingaben nicht
an die betroffene Stelle. Status `verbindlich`. Prüfung: T-SCAN-PDF-6, T-SCAN-PDF-8.

## Bedienbarkeit

### NFA-050 Tastatur

Der ganze Arbeitsweg lässt sich ohne Maus gehen. Status `verbindlich`. Prüfung:
T-OBERFLAECHE-94.

### NFA-051 Barrierefreiheit

Ziel ist WCAG 2.2 Stufe AA (Entscheid vom 30.10.2026). Das ist ein Ziel und keine
Zusage: Eine Prüfung gegen die Norm hat noch nicht stattgefunden. Vorhanden sind
Tastaturweg, `aria`-Angaben, `prefers-reduced-motion`, Skalierung 70 bis 140 %. Status
`verbindlich`, `ohne Prüfung`.

### NFA-052 Skalierbare Grössen

Alle Grössen in `rem`. Status `verbindlich`. Prüfung: T-OBERFLAECHE-28.

### NFA-053 Breiten

Nutzbar ab 378 px Inhalt, ohne waagrechten Rollbalken. Status `verbindlich`. Prüfung:
T-OBERFLAECHE-40, T-OBERFLAECHE-51, T-OBERFLAECHE-91.

### NFA-054 Hell und dunkel

Jede Marke gibt es in beiden Themen. Status `verbindlich`. Prüfung: T-OBERFLAECHE-72,
T-OBERFLAECHE-73, T-APP-23.

### NFA-055 Einheitliche Formen

Eine Rundung je Art von Element. Status `verbindlich`. Prüfung: T-APP-22.

## Kompatibilität

### NFA-060 Plattformen

Linux x86_64 (AppImage, Flatpak, Arch), Windows x64, macOS arm64, Docker. Status
`verbindlich`. Prüfung: T-FENSTER-12, T-FENSTER-22, T-FENSTER-26.

### NFA-061 Zeichensatz

Der amtliche Zeichensatz der Personenregister wird angezeigt. Status `verbindlich`.
Prüfung: T-SCHRIFTEN-5, T-SCHRIFTEN-6.

### NFA-062 Browser

Ein aktueller Browser mit OKLCH und `color-mix`. Eine Untergrenze fehlt. Status `offen`,
`ohne Prüfung`.

## Wartbarkeit

### NFA-070 Prüfbar ohne Modell

Bis auf eine Prüfung laufen alle in einem frischen Klon ohne Modell, GPU und Downloads.
Status `verbindlich`, `ohne Prüfung`.

### NFA-071 Eine Quelle

Fassung, Port, Goldpfad und Wahllisten haben je einen Verwalter. Status `verbindlich`.
Prüfung: T-FENSTER-6, T-FENSTER-7, T-GOLDPFAD-6, T-API-21.

### NFA-072 Länderspezifisches ist Daten

Status `verbindlich`. Prüfung: T-LABELVERTRAG-EINGEFROREN-3, T-USER-RULES-3.

### NFA-073 Katalog bleibt aktuell

Status `verbindlich`. Prüfung: T-SPECS-1, T-SPECS-2, T-SPECS-3, T-SPECS-4, T-SPECS-5,
T-SPECS-6, T-SPECS-7, T-SPECS-8, T-SPECS-12.

### NFA-075 Katalog bei jedem Release

Vor jedem Release wird `specs/` nachgeführt. Ohne geändertes Kapitel hält das Release
an, ausser das CHANGELOG sagt mit `Katalog unverändert: <Grund>`, warum. `SECURITY.md`
nennt die aktuelle Fassungsreihe. Jeder neue Prüfpunkt gehört zu einer Anforderung; die
Altliste `tests/specs_altliste.txt` darf nur schrumpfen. Status `verbindlich`. Prüfung:
T-SPECS-9, T-SPECS-10, T-SPECS-11.

### NFA-074 Testfassung vor Release

Status `verbindlich`, `ohne Prüfung`.

## Betrieb

### NFA-080 Support

Unterstützt wird die aktuelle Fassungsreihe. Erste Antwort auf eine Sicherheitsmeldung
innert 7 Tagen. Status `verbindlich`, `ohne Prüfung`.

### NFA-082 Vertrag und Antwort

Jedes Feld einer echten Antwort steht im Vertrag ([07 API](07_api.md)). Status
`verbindlich`. Prüfung: T-API-30, T-API-24.

### NFA-081 Offline

Ist das Modell da, läuft alles ohne Netz. Status `verbindlich`. Prüfung: T-APP-6.
