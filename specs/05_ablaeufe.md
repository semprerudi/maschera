# Abläufe

## Arbeitsweg des Anwenders

Die fünf Schritte sind zugleich die Tab-Reihenfolge der Oberfläche
([10 Oberfläche](10_oberflaeche.md)).

```mermaid
flowchart LR
  A["01 Dokument<br>ablegen, einfügen, Beispiel"] --> B["02 Maskieren<br>prüfen, Rechtsklick, Vokabular"]
  B --> C["03 Prompt<br>Vorlage, Übernahme"]
  C --> D["04 KI-Werkzeug<br>kopieren, Dienst öffnen, von Hand einfügen"]
  D --> E["05 Zurückholen<br>Antwort einfügen, Wörterbuch anwenden"]
```

## Maskieren

```mermaid
sequenceDiagram
  actor A as Anwender
  participant O as Oberfläche
  participant S as Dienst
  participant K as Kette
  A->>O: Datei ablegen
  O->>S: POST /api/lesen
  S-->>O: Text oder Absage mit Begründung
  A->>O: Maskieren
  O->>S: POST /api/anonymisieren
  loop Fortschritt
    O->>S: GET /api/fortschritt
  end
  S->>K: filter_text unter Sperre
  K-->>S: Spannen, Text, Wörterbuch
  S-->>O: Antwort, nichts bleibt im Dienst
  O-->>A: Hervorhebung nach Quelle und Schwelle
```

Ablegen liest nur. Maskieren ist eine Handlung mit eigenem Knopf, weil sie eine
Entscheidung ist. Das Wörterbuch lebt allein im Browser des Anwenders.

## Die Kette

```mermaid
flowchart TD
  T[Text] --> M["Stufe 3: Modell in Fenstern<br>512 Token, Überlappung 128"]
  M --> S{"Wert über der<br>Schwelle des Tags?"}
  S -- nein --> V1[verworfen, gezählt]
  S -- ja --> W[auf Wortgrenzen ziehen]
  T --> R[Stufe 1 und 2: Muster]
  T --> U[Eigene Regeln]
  R --> Z
  U --> Z
  W --> P{"Prüfsummen-Tag?"}
  P -- nein --> Z
  P -- ja --> Q{"Prüfsumme gültig?"}
  Q -- nein --> V2[verworfen]
  Q -- ja --> Z["Zusammenführen<br>Stufe 1, dann Länge, dann Quelle"]
  Z --> PR["Dokument-Propagation<br>jedes weitere Vorkommen"]
  PR --> RU["Überlappungen erneut auflösen"]
  RU --> A["Aktion je Tag<br>mask oder tag_only, Vorlieben"]
  A --> PL["Platzhalter und Wörterbuch<br>[TAG_n]"]
```

## Zurückholen

```mermaid
flowchart TD
  A[Antwort des KI-Werkzeugs] --> B["POST /api/zurueckwandeln<br>Text und Wörterbuch"]
  B --> C[Platzhalter zählen]
  C --> D{"Im Wörterbuch?"}
  D -- ja --> E[ersetzen]
  D -- nein --> F{"Nur andere Schreibweise?"}
  F -- ja --> G["Hinweis, nicht ersetzt"]
  F -- nein --> H["nicht_gefunden melden"]
```

Was nicht zugeordnet werden kann, ist der wichtigste Teil der Antwort: Ein
Sprachmodell schreibt Platzhalter um, und ein still stehen gebliebener
`[FULLNAME_1]` im Brief darf nicht unbemerkt bleiben.

## Start des eigenen Fensters

```mermaid
flowchart TD
  A[Start] --> B{"Läuft MASCHERA schon?"}
  B -- ja --> C[Vorhandenes Fenster zeigen, Ende]
  B -- nein --> D{"Modell vorhanden?"}
  D -- nein --> E["Fragen: Quelle, Grösse, Ziel"]
  E -- Später --> F[Ende, nichts geladen]
  E -- Laden --> G[Holen und Prüfsumme prüfen]
  D -- ja --> H{"Port frei?"}
  G --> H
  H -- nein --> I["Nächster freier Port,<br>sofort gesichert"]
  H -- ja --> J[Dienst im Faden starten]
  I --> J
  J --> K[Fenster zeigen, Tray einrichten]
```

## Modell entstehen lassen

```mermaid
flowchart LR
  N["Offene Daten des Bundes"] --> B["nomenclatures/build.py"]
  L["Lokales Sprachmodell"] --> V["Vorlagen mit Slots"]
  V --> W["Wachen in core/injector.py"]
  B --> I["Injektor: Werte einsetzen,<br>Spannen merken"]
  W --> I
  I --> R["Round-Trip,<br>Layout-Rauschen"]
  R --> T["train.py auf mmBERT-base"]
  T --> E["Messen: synthetisch und Dokumente"]
  E --> P["Gewichte mit Pack und Hash"]
```

## Release

```mermaid
flowchart TD
  A["Fassung, Changelog, Metadaten, Releasetext"] --> B["Prüfen: Stand, Tests, Tag frei"]
  B --> C["Öffentlicher Stand, Push, Tag"]
  C --> D["GitHub baut alle Pakete,<br>signiert und schreibt das Release"]
  D --> E["Server zieht das signierte Abbild"]
  E --> F["Webseite nur nach Bedarf"]
```

Einzelheiten stehen in [12 Pakete und Release](12_pakete_release.md).
