# Funktionale Anforderungen

Jede Anforderung nennt ihre Prüfungen aus dem [Testkatalog](erzeugt/testkatalog.md).
Das Verhalten im Einzelnen steht in den Fachkapiteln.

## Dokumente einlesen

### FA-001 Text einfügen und Dateien lesen

MASCHERA nimmt eingefügten Text sowie PDF, DOCX, TXT, MD, LOG, CSV, JSON, EML, MSG
und MBOX an. Prüfung: T-API-8, T-DOKUMENTE-DOCX-1, T-MAIL-1, T-MAIL-6, T-MAIL-8.

### FA-002 Ablegen liest nur

Eine abgelegte Datei wird zu Text, maskiert wird erst auf Knopfdruck. Getippter Text
wird nicht ungefragt ersetzt. Prüfung: T-OBERFLAECHE-29, T-OBERFLAECHE-30.

### FA-003 Scan ohne Textebene

Ein leeres Ergebnis ist ein Fehler mit Begründung. Prüfung: T-SCAN-PDF-1,
T-SCAN-PDF-3, T-SCAN-PDF-5, T-API-7.

### FA-004 Mail

Mails liefern Kopf und Text. Anhänge fallen weg, HTML wird entkleidet und gemeldet,
Binäres nach dem Textende wird abgeschnitten und gemeldet. Eine Mail ohne Textteil
erfindet keinen. Prüfung: T-MAIL-2, T-MAIL-3, T-MAIL-4, T-MAIL-5.

### FA-005 Word

Tabellen behalten Etikett und Wert auf einer Zeile. Kopf- und Fusszeilen werden
gemeldet. `.doc` wird abgewiesen, ZIP-Bomben ebenso. Prüfung: T-DOKUMENTE-DOCX-3,
T-DOKUMENTE-DOCX-5, T-DOKUMENTE-DOCX-10, T-DOKUMENTE-DOCX-11B.

### FA-006 Sicher hochladen

Ein Dateiname wird nie zum Pfad. Prüfung: T-API-26, T-APP-5.

### FA-007 Keine PDF mit Brotli

Ein PDF mit Brotli-Filter wird abgewiesen, bevor MuPDF den Filter erreicht. Die Meldung
sagt in vier Sprachen, was man tun kann: neu speichern oder den Text einfügen. Gesunde
PDF bleiben lesbar. Prüfung: T-SCAN-PDF-6, T-SCAN-PDF-7, T-SCAN-PDF-8.

## Erkennen

### FA-010 Drei Stufen

Prüfsummen, Muster mit Kontextankern und Modell laufen zusammen, jede Stufe mit
ihrer Aufgabe. Prüfung: T-INFERENCE-2, T-INFERENCE-3, T-INFERENCE-4, T-INFERENCE-6.

### FA-011 45 Tags in vier Sprachen

Der Labelvertrag umfasst 45 Tags und 91 BIO-Labels, de, fr, it, en sind gleichwertig.
Prüfung: T-LABELVERTRAG-EINGEFROREN-1, T-LABELVERTRAG-EINGEFROREN-2, T-PATTERNS-1,
T-PATTERNS-11.

### FA-012 Prüfsummen entscheiden

Eine gültige Prüfsumme maskiert ohne Modell, eine ungültige verwirft auch einen
Modelltreffer. Prüfung: T-CH-CHECKSUMS-1, T-CH-CHECKSUMS-2, T-CH-CHECKSUMS-3,
T-CH-CHECKSUMS-4, T-INFERENCE-2.

### FA-013 Schwelle je Fehlerbudget

Jeder Tag hat eine Schwelle aus seinem Budget, Ausnahmen sind begründet. Prüfung:
T-INFERENCE-1, T-EVALUATE-7.

### FA-014 Dokument-Propagation

Ein erkannter Wert wird an jeder weiteren Stelle maskiert. Prüfung: T-MASKING-2,
T-MASKING-3.

### FA-015 Lange Dokumente

Das Modell liest in überlappenden Fenstern und sieht das ganze Dokument. Prüfung:
T-LANGES-DOKUMENT-1, T-LANGES-DOKUMENT-3.

### FA-016 Decoys bleiben stehen

Rechtsverweise, Fristen und Schwellen sind keine Personendaten. Prüfung:
T-PATTERNS-2, T-MASKING-5, T-BEFUNDE-1, T-BEFUNDE-2.

### FA-017 Eigene Regeln

Der Anwender erklärt eigene Bezeichner mit Etikett oder Wortliste. Sie stehen
ausserhalb des Labelvertrags. Prüfung: T-USER-RULES-1, T-USER-RULES-2,
T-USER-RULES-3, T-USER-RULES-5, T-API-9.

### FA-018 Klartext-Tags

Der Anwender nimmt Tags dauerhaft oder je Lauf von der Ersetzung aus. Tags mit
`bspd` brauchen eine ausdrückliche Bestätigung. Prüfung: T-API-6, T-API-11,
T-VORLIEBEN-2, T-VORLIEBEN-3, T-VORLIEBEN-5.

## Maskieren

### FA-020 Platzhalter und Wörterbuch

Jeder Wert wird zu einem Platzhalter `[TAG_n]`, das Wörterbuch ordnet ihn zu. Der
Weg zurück ist zeichengenau. Prüfung: T-MASKING-1, T-MASKING-1B, T-APP-12, T-API-3.

### FA-021 Ohne Wörterbuch

Ein Lauf ohne Wörterbuch ist möglich und endgültig, die Antwort sagt das. Prüfung:
T-API-5.

### FA-022 Korrektur von Hand

Plaketten lassen sich entfernen, umtaggen oder im ganzen Dokument zurücknehmen.
Wörter lassen sich maskieren, nur als ganze Wörter. Der Text ist bearbeitbar.
Prüfung: T-OBERFLAECHE-14, T-OBERFLAECHE-15, T-OBERFLAECHE-16, T-OBERFLAECHE-18,
T-OBERFLAECHE-63, T-OBERFLAECHE-85.

### FA-023 Herkunft sichtbar

Jede Stelle zeigt Quelle und Sicherheit. Der Rand zeigt auf Arbeit, nicht auf
Sicherheit. Prüfung: T-OBERFLAECHE-17, T-VERTRAUEN-1, T-VERTRAUEN-4, T-VERTRAUEN-8.

### FA-024 Fortschritt

Der Balken zeigt Gemessenes. Prüfung: T-API-15, T-OBERFLAECHE-36.

### FA-025 Vokabular sichern

Das Wörterbuch lässt sich herunterladen und wieder einlesen. Eine fehlerhafte Datei
wird ganz abgewiesen. Prüfung: T-OBERFLAECHE-20, T-OBERFLAECHE-21.

## Weitergeben

### FA-030 Nichts wird gesendet

Es gibt keinen Sendeendpunkt. Der Text geht über die Zwischenablage, der Dienst wird
geöffnet, eingefügt wird von Hand. Prüfung: T-API-10, T-APP-4, T-OBERFLAECHE-7,
T-OBERFLAECHE-81.

### FA-031 Vorlagen

Benannte Prompts lassen sich speichern, filtern, wählen und löschen. Prüfung:
T-API-12, T-OBERFLAECHE-23.

### FA-032 Dienste

Die Liste der Dienste ist veränderbar und alphabetisch. Ein neuer Dienst steht sofort
im Sendeknopf, ohne Dienst wird nicht gespeichert. Prüfung: T-OBERFLAECHE-24,
T-OBERFLAECHE-27, T-OBERFLAECHE-82, T-API-27.

### FA-033 Warnung an der Grenze

Am Sendeknopf steht immer, dass der Text das Gerät verlässt. Prüfung:
T-OBERFLAECHE-50, T-APP-16.

## Zurückholen

### FA-040 Antwort zurückwandeln

Platzhalter in der Antwort werden zu Werten. Prüfung: T-API-4, T-OBERFLAECHE-70.

### FA-041 Nicht zugeordnete Platzhalter

Sie werden angezeigt und nie still ersetzt. Prüfung: T-MASKING-6, T-OBERFLAECHE-10.

### FA-042 Umgeschriebene Platzhalter

Die Oberfläche nimmt die Markdown-Entwertung `\[X\_1\]` zurück, eine andere
Schreibweise wird gemeldet und nicht ersetzt. Prüfung: T-OBERFLAECHE-68.

## Oberfläche

### FA-050 Sechs Kacheln entlang des Wegs

Prüfung: T-OBERFLAECHE-1, T-OBERFLAECHE-8, T-OBERFLAECHE-86, T-OBERFLAECHE-88.

### FA-051 Vier Bediensprachen

Alle Texte und Hinweise folgen der Sprache der Oberfläche, ein Schlüssel je Sprache.
Prüfung: T-OBERFLAECHE-22, T-OBERFLAECHE-47, T-OBERFLAECHE-60, T-API-18, T-API-19,
T-MODELL-9C.

### FA-052 Willkommensschirm

Fünf Seiten und Schluss, abwählbar, im Menü wieder erreichbar. Prüfung:
T-OBERFLAECHE-90, T-OBERFLAECHE-92.

### FA-053 Beispiel

Ein erfundener Text lässt sich laden. Prüfung: T-OBERFLAECHE-3.

### FA-054 Neu

«Neu» leert das ganze Formular und fragt vorher. Beim Schliessen wird vor
Datenverlust gewarnt. Prüfung: T-OBERFLAECHE-41, T-APP-17.

### FA-055 Suchen und Vergrössern

Rechtsklickmenü, Einstellungen und Vokabular sind durchsuchbar, jede Kachel lässt
sich vergrössern. Prüfung: T-OBERFLAECHE-89.

### FA-056 Einstellungen

Abbrechen nimmt zurück, ein Fehler steht beim Abschnitt. Prüfung: T-API-13, T-API-20,
T-OBERFLAECHE-12, T-OBERFLAECHE-25, T-OBERFLAECHE-87.

### FA-057 Eigene Dialoge

Rückfragen laufen im eigenen Dialog. Prüfung: T-OBERFLAECHE-79.

### FA-058 Hilfe und Impressum im Paket

Prüfung: T-OBERFLAECHE-62.

## Fenster und Betrieb

### FA-060 Eigenes Fenster

Das Fenster trägt Dienst und Oberfläche und beendet beides zusammen. Nur ein
MASCHERA läuft. Prüfung: T-FENSTER-19, T-FENSTER-20, T-FENSTER-21.

### FA-061 Portwahl

Vorgabe `127.0.0.1:4141`. Ist er belegt, weicht MASCHERA ohne Rückfrage auf den nächsten
freien der folgenden 50 Ports aus und sichert die Wahl sofort, kein Zufallsport. Prüfung:
T-FENSTER-1, T-FENSTER-2, T-FENSTER-3, T-FENSTER-4, T-FENSTER-5.

### FA-062 Tray und Seitenleiste

Prüfung: T-FENSTER-17, T-FENSTER-24, T-OBERFLAECHE-77.

### FA-063 Modell holen

Fehlt das Modell, fragt der erste Start. Es wird vollständig und geprüft geholt, ein
Abbruch lässt nichts Halbes liegen. Prüfung: T-MODELL-1, T-MODELL-2, T-MODELL-3,
T-MODELL-5, T-MODELL-6, T-MODELL-7, T-MODELL-12.

### FA-064 Nach Updates suchen

Nur auf Klick, eine feste Adresse, nur die Fassungsnummer. Prüfung: T-API-23,
T-API-28, T-API-29, T-OBERFLAECHE-84.

### FA-065 Serverbetrieb

Hinter einem Reverse Proxy mit benanntem Wirt. Prüfung: T-API-25, T-APP-8.

### FA-066 Kommandozeile

`tools/filter_document.py` maskiert Dateien ohne Oberfläche. `ohne Prüfung` als
eigener Punkt, die Kette dahinter prüfen T-INFERENCE-4 und T-VERTRAUEN-8.

## Modellbau und Messung

### FA-070 Trainingsdaten

Der Injektor erzeugt Beispiele aus Vorlagen und Nomenklaturen. Spannen sitzen
zeichengenau, Decoys bleiben ohne Label. Prüfung: T-INJECTOR-1, T-INJECTOR-2,
T-INJECTOR-3, T-INJECTOR-4, T-INJECTOR-5, T-ALIGNMENT-7.

### FA-071 Rauschen und Haltezone

Prüfung: T-RAUSCHEN-1, T-RAUSCHEN-4, T-RAUSCHEN-5, T-RAUSCHEN-7.

### FA-072 Auswertung

Leckrate gewichtet, Klassen getrennt, je Dokument. Prüfung: T-EVALUATE-2,
T-EVALUATE-3B, T-EVALUATE-4, T-EVALUATE-6, T-VORLIEBEN-6.

### FA-073 Streuung

Prüfung: T-STREUUNG-1, T-STREUUNG-3.

### FA-074 Eigene Golddokumente

Werkzeuge legen ein eigenes Testset an, ausserhalb des Projektbaums. Prüfung:
T-GOLDPFAD-3, T-GOLDPFAD-4, T-GOLD-MARKUP-2, T-GOLD-ERSETZEN-4.
