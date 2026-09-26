# MAS**CH**ERA — Spezifikation

**Lokale Maskierung von Personendaten in Schweizer Dokumenten**

Sprachen: **DE / FR / IT / EN** ·
Backbone: [mmBERT-base](https://huggingface.co/jhu-clsp/mmBERT-base)
(ModernBERT-Architektur)

⚠️ Massgeblich ist der Code. Wo diese Spezifikation und der Code sich
widersprechen, gilt der Code — insbesondere `packs/ch/taxonomy.yaml` und
der Labelvertrag `b7a96dc9`.

---

## 1. Ziel und Abgrenzung

Dokumente lokal maskieren, damit sie an ein Sprachmodell gegeben werden
können, ohne dass Personendaten das eigene Gerät verlassen. Die Antwort
wird lokal über ein Wörterbuch zurückgewandelt.

Gedacht für alle, die mit Schweizer Dokumenten arbeiten: Verwaltungen von
Bund, Kantonen und Gemeinden, Unternehmen, Kanzleien, Vereine und
Privatpersonen.

| | |
|---|---|
| Sprachen | DE/FR/IT/EN gleichwertig, ein Modell |
| Tags | 45, in drei Stufen |
| Rechtsrahmen | RHG (SR 431.02) Art. 6 + revDSG |
| Erkennen ≠ Maskieren | getrennt (`TAG_MAP` + `ACTION_MAP`) |
| Fehlerbudget | drei Klassen, getrennt ausgewiesen |
| Architektur | **Country Pack**, austauschbar |
| Datengenerierung | lokales Sprachmodell, keine externe API |
| Evaluation | synthetisch **+ Dokument-Testset** |

**Wichtig, rechtlich:** Das Verfahren ist eine **Pseudonymisierung**, keine
Anonymisierung. Solange das Wörterbuch existiert, bleiben die Daten nach
revDSG Personendaten. Ob sie gegenüber dem Anbieter eines Sprachmodells
als anonym gelten, hängt vom relativen bzw. absoluten Ansatz der
Identifizierbarkeit ab — juristisch umstritten. Vor dem produktiven
Einsatz in einer Organisation — Verwaltung, Unternehmen, Kanzlei —
schriftliche Beurteilung durch die zuständige Datenschutzstelle einholen.

---

## 2. Architekturprinzipien

1. **Erkennen und Maskieren sind zwei Achsen.** Ein Tag kann erkannt werden,
   ohne ersetzt zu werden. Die Maskierungspolitik liegt in `ACTION_MAP`
   (Daten), nicht in den Trainingsdaten — änderbar ohne Neutraining.
2. **Prüfsummen schlagen das Modell**, aber nur wo sie mathematisch
   beweisend sind.
3. **Das neuronale Modell ist die Recall-Engine, die Regex die
   Precision-Garantie.**
4. **Alles Länderspezifische ist Daten, kein Code** (→ Country Pack,
   Abschnitt 12).
5. **Das Modell ist notwendig.** `--ohne-modell` ist eine Messhilfe, kein
   Betriebszustand: ohne Modell bleibt jeder Name im Klartext.

---

## 3. Taxonomie — 45 Tags

BIO-Schema: `2 × 45 + 1 = 91` Labels.

**Legende Aktion:** `M` = maskieren · `T` = nur taggen (bleibt im Klartext)
**Legende Budget:** `R` = recall-first · `A` = ausgewogen · `P` = precision-first
**bsPD** = besonders schützenswerte Personendaten (revDSG Art. 5 Bst. c)

### Stufe 1 — Prüfsummen-Override (6)

Gültige Prüfsumme → maskieren, auch wenn das Modell schweigt.
Ungültige → verwerfen, auch wenn das Modell anschlägt.

| Tag | Prüfung | Aktion |
|---|---|---|
| `AHVN13` | EAN-13, Präfix 756 | M |
| `UID` | Modulo-11, Präfix CHE | M |
| `IBAN` | Modulo-97, feste Länge je Land (ISO 13616) | M |
| `QR_REFERENCE` | Modulo-10 rekursiv, 27-stellig | M |
| `CREDITCARD` | Luhn | M |
| `GLN` | EAN-13 (Medizinalperson) | M |

### Stufe 2 — Regex mit Kontextanker, kein Override (17)

| Tag | Anker / Muster | Aktion | Budget |
|---|---|---|---|
| `EGID` | Kontextwort zwingend, 4-sprachig | M | R |
| `EWID` | Kontextwort zwingend, nur mit EGID | M | R |
| `MUNICIPALITY_ID` | Kontextwort zwingend | M | R |
| `INSURANCE_CARD` | `80756` + 15 Ziffern | M | R |
| `PHONE` | +41 / 0xx | M | A |
| `PLATE` | Kantonskürzel + 1–6 Ziffern | M | A |
| `ZIPCODE` | 1000–9699, Ortsname folgt | M | P |
| `AMOUNT` | CHF / Fr. / franc | M | P |
| `PERMIT_TYPE` | Ausweis B/C/Ci/L/G/F/N/S | M | R |
| `IDDOC` | Buchstabe + 7 Ziffern | M | R |
| `ZSR_RCC` | Zahlstellenregister | M | R |
| `PATIENT_ID` | Kontextwort zwingend | M | R |
| `CASE_ID` | Dossier-/Geschäftsnummer | M | A |
| `PARCEL` | Parzelle / Grundstück | M | A |
| `URL`, `IPADDRESS` | Standardmuster | M | P |
| `EMAIL` | Standardmuster | M | R |

### Stufe 3 — rein neuronal (22)

| Tag | Aktion | Budget | Bemerkung |
|---|---|---|---|
| `FULLNAME` | M | **R** | zentraler Identifikator |
| `GIVENNAME` | M | **R** | |
| `DATE` | M | R | dazu ein deterministischer Erkenner gegen Zerstückelung |
| `TIME` | M | R | |
| `STREET` | M | R | |
| `BUILDINGNUM` | M | R | |
| `CITY` | M | A | Stadt ≠ Kleinstgemeinde — Kompromiss |
| `COUNTRY` | M | P | |
| `AGE` | M | A | Quasi-Identifikator |
| `SEX` | M | A | Quasi-Identifikator |
| `MARITALSTATUS` | M | A | |
| `RELIGION` | M | **R (bsPD)** | RHG Art. 6 Bst. l |
| `NATIONALITY` | M | **R (bsPD)** | Ethnie-Rückschluss |
| `SOCIAL_INSURANCE` | M | **R (bsPD)** | IV-Fall, Kassennr. |
| `INSURANCE_POLICY` | M | **R (bsPD)** | |
| `RESIDENCE_STATUS` | M | A | Niederlassung / Aufenthalt |
| `VOTING_RIGHTS` | M | A | |
| `PLACE_OF_ORIGIN` | **T** | R | Heimatort — bleibt lesbar |
| `CANTON` | **T** | P | trägt Kontext, identifiziert nicht |
| `ORG` | M | P | Schwelle 0.40, gemessen (siehe `taxonomy.yaml`) |
| `HEALTHCARE_ORG` | M | **R** | Spezialklinik verrät mehr als Diagnose |
| `USERNAME` | M | R | Kontoname, Pfadbestandteil, Anmeldename |

**Warum `T` mit Budget `R`?** Das Budget steuert die *Erkennung*, nicht die
Maskierung. Hoher Recall auf `PLACE_OF_ORIGIN` sorgt dafür, dass der
Heimatort **nicht versehentlich als `CITY` mitmaskiert** wird. Er bleibt
verlässlich lesbar.

### Warum keine medizinischen Inhaltstags

**Eine Pathologie ohne Identität ist kein Personendatum.** Solange nicht
klar ist, über wen gesprochen wird, schützt ihre Maskierung niemanden — sie
macht nur den Arztbericht unbrauchbar. Dieselbe Überlegung wie bei `ORG`,
wo Anwendungsnamen wie `Sedex` stehen bleiben: was niemanden identifiziert,
ist Sachinhalt.

**Was schützt, ist die Kennnummer**, über die eine Person zurückgeholt
werden kann. Die führt der Vertrag, durchgehend als besonders
schützenswert:

| | |
|---|---|
| `INSURANCE_CARD` | Versichertenkarte, **bsPD** |
| `PATIENT_ID` | **bsPD**, Kontextwort zwingend |
| `SOCIAL_INSURANCE` | IV-Fall, Kassennummer, **bsPD** |
| `INSURANCE_POLICY` | **bsPD** |
| `HEALTHCARE_ORG` | **bsPD** — eine Spezialklinik verrät mehr als eine Diagnose |
| `ZSR_RCC` · `GLN` | Leistungserbringer |
| `AHVN13` | Versichertennummer, Stufe 1 |

⚠️ Wer medizinische Inhaltstags braucht, muss den **Labelvertrag auftauen
und neu trainieren** — eine neue Tagliste macht jedes bisher trainierte
Modell unbrauchbar. Neue Tags werden angehängt, nie eingefügt.

---

## 4. Fehlerbudgets

| | Recall-Fehler | Precision-Fehler |
|---|---|---|
| Was passiert | echtes Personendatum übersehen | Unbeteiligtes maskiert |
| Folge | Klartext geht hinaus | Text löchrig, Antwortqualität sinkt |
| Reparierbar | **nein** | ja, sofort sichtbar |

**Wirkung im System — ein Budget ohne diese zwei Konsequenzen ist Dekoration:**

1. **Entscheidungsschwelle** pro Tag-Klasse: `R` = 0.30, `A` = 0.50,
   `P` = 0.70. Eine Ausnahme je Tag braucht eine Messung, festgehalten neben
   dem Wert in `taxonomy.yaml`.
2. **Report** weist die Klassen **getrennt** aus, nie als einen Micro-F1.

Grundsatz: **Übermaskierung ist kein Leck.** Ein unterdrücktes Datum ist
teurer als eines zu viel.

---

## 5. Prüfsummen

| Identifikator | Verfahren | Details |
|---|---|---|
| AHVN13 | EAN-13 | `756` + 9 Ziffern + Prüfziffer; Gewichte 1,3,1,3… von links über 12 Stellen |
| UID | Modulo-11 | `CHE` + 8 Ziffern + Prüfziffer; Gewichte **5,4,3,2,7,6,5,4**; Ergebnis 10 → nie vergeben, 11 → 0 |
| GLN | EAN-13 | identisch zu AHVN13, ohne 756-Prüfung |
| IBAN | Modulo-97 | ISO 13616; feste Länge je Land, CH/LI = 21 Zeichen |
| QR-Referenz | Modulo-10 rekursiv | 27 Stellen, Tabellenverfahren |
| Kreditkarte | Luhn | 12–19 Ziffern |

Verifiziert gegen `756.9217.0769.85` und `CHE-116.281.710`, plus Round-Trip
über 2000 generierte Nummern je Typ.

> ⚠️ Die UID-Gewichte sind gegen echte Nummern gegengeprüft, **nicht**
> gegen die offizielle BFS-Spezifikation. Vor dem Produktiveinsatz
> gegenlesen.

**Das neuronale Modell läuft nie allein.** Das Netz aus Regex und
Prüfsummen verhindert den klassischen Fehlerfall, dass ein Tagger eine
lange Ziffernfolge in Fragmente zerlegt.

---

## 6. Nomenklaturquellen

Die Nomenklaturen werden gebaut, nicht verteilt:
`packs/ch/nomenclatures/build.py` holt die offenen Verwaltungsdaten und
normalisiert sie; `raw/` und `dist/` stehen nicht im Repository.

| Bedarf | Quelle |
|---|---|
| `PLACE_OF_ORIGIN` | eCH-0135 Heimatortverzeichnis (BJ) |
| `CITY`, `ZIPCODE` | Amtliches Ortschaftenverzeichnis mit PLZ (swisstopo) |
| `STREET` | Amtliches Strassenverzeichnis (swisstopo) |
| `FULLNAME`, `GIVENNAME` | Nach- und Vornamen der ständigen Wohnbevölkerung (BFS) |
| `ORG` | Zefix über LINDAS (Handelsregister), dazu Behördennamen kombinatorisch |
| `NATIONALITY` u. a. | Amtlicher Katalog der Merkmale (BFS), viersprachig |

**eCH-0135** — Befunde, die den Generator prägen:

- Historisierte Namen stehen weiterhin in gültigen Pässen — **der
  Generator zieht sie mit.**
- Einträge in Klammerform (`Hautemorges (Apples)`) sind ein
  Registerartefakt → zwei Oberflächenformen, die zusammengesetzte verworfen.
- Namen, die in **mehreren Kantonen** vorkommen (`Buchs` in ZH/LU/SG/AG) →
  das Kantonskürzel gehört **in die Entitätsspanne**.
- Namen sind vielfach Alltagswörter: `Wald`, `Berg`, `Stein`, `Egg`, `Au`.
  → **Gazetteer nur zur Generierung, nie zur Erkennung. Kein Override.**
- Schrägstrich-Namen (`Breil/Brigels`) sind deutsch-romanische
  Doppelnamen. Rätoromanisch steht damit faktisch als fünfte Sprache in
  den Daten, ohne unterstützt zu sein.
- **Heimatortliste ≠ Gemeindeverzeichnis.** Zwei getrennte Nomenklaturen.

**Identifikatoren** werden **generiert**, mit gültigen Prüfsummen.

**Fairness:** Ohne italienische, portugiesische, balkanische, türkische
und tamilische Namen hätte das Modell den schlechtesten Recall bei genau
den Gruppen, die in Schweizer Dokumenten häufig vorkommen. Die Namenslisten
des BFS bilden die ständige Wohnbevölkerung ab.

**Englisch** ist keine Amtssprache und hat keine amtliche Nomenklatur.
Vorlagen komplett synthetisch, Identifikatoren bleiben schweizerisch.

---

## 7. Vorlagenbank

**Nicht pro Dokumenttyp budgetieren, sondern pro Tag.** Seltene Tags
(`RELIGION`, `VOTING_RIGHTS`, `EWID`, `PLACE_OF_ORIGIN`, `PERMIT_TYPE`)
brauchen genug eigene Rahmen, sonst lernt das Modell sie nie.

**Deutsch bewusst überproportional.** In FR/IT/EN ist ein grossgeschriebenes
Wort mitten im Satz ein starkes Namenssignal — im Deutschen ist jedes
Substantiv gross. Qualität überträgt sich **nicht** von FR/IT/EN nach DE.

**Zeilen pro Vorlage begrenzen.** Zu wenige verschenken Wertvielfalt, zu
viele lehren das Modell den Rahmen statt der Entität.

Vorlagen werden von einem lokalen Sprachmodell geschrieben
(`tools/generate_templates.py`) oder von Hand, und jede läuft durch
dieselben Wachen (`core/injector.py`) — vor dem Training trotzdem lesen:
die Wachen prüfen die Form, nicht den Sinn.

---

## 8. Slot-Grammatik

```
{TAG}           echte Entität, wird getaggt
{@makro}        gekoppelte Gruppe aus macros.yaml
{~decoy}        sieht aus wie eine Entität, bleibt O
```

**Makros erzwingen Kohärenz.** `@address` zieht Strasse, Hausnummer, PLZ und
Ort aus EINEM Datensatz — sonst entsteht «Marktgasse 12, 6900 Bern», und das
Modell lernt, dass PLZ und Ort nichts miteinander zu tun haben.

### Decoys — nie gelabelt

| Makro | Beispiel |
|---|---|
| `~legal_ref` | Art. 6 Abs. 1 Bst. i RHG (SR 431.02) |
| `~deadline` | innert 30 Tagen seit Eröffnung |
| `~threshold` | Vermögensfreibetrag von 4000 Franken |
| `~doc_meta` | Version 2.1, Stand 01.2026 |

Verwaltungstexte wimmeln von Zahlen, die keine Personendaten sind. Ohne
Decoys übertaggt das Modell. **Decoys sind das Precision-Werkzeug und
kosten nur Vorlagenzeilen.** Sie sind je Sprache getrennt: ein deutscher
Decoy in einer französischen Vorlage lehrt eine Sprachmischung, die in
echten Dokumenten nicht vorkommt.

---

## 9. Makros

### Sprachregion koppelt Geografie

| Sprache | Pool |
|---|---|
| DE | Deutschschweiz |
| FR | Romandie |
| IT | Tessin + italienischsprachiges Graubünden |
| EN | alle, gewichtet nach Wirtschaftsräumen |

Dazu bewusst ein Anteil **Überkreuz** — ein Berner Verfahren mit Genfer
Gegenpartei ist normal. Ohne diesen Anteil wird das Modell überkonfident
auf Region.

### Wichtige Kopplungen

| Makro | Kopplungsregel |
|---|---|
| `@address` | PLZ ↔ Ort aus swisstopo |
| `@origin` | Heimatort mit dem Kanton, an den er in eCH-0135 gebunden ist |
| `@person` | Namensreihenfolge wechselt — auch Register-Reihenfolge «Nachname Vorname» |
| `@company` | Rechtsform sprachrichtig: AG/SA/SA, GmbH/Sàrl/Sagl |

**Jede Vorlage mit Heimatort enthält auch einen Wohnort.** Ohne dieses
Minimalpaar lernt das Modell die Unterscheidung *von* ↔ *wohnhaft in* nie,
und der Entscheid «Heimatort bleibt lesbar» geht in der Praxis unter.

**Wortstellung ist sprachabhängig, nicht übersetzbar.** FR: «Rue du Marché
12» *oder* «12, rue du Marché». Makros einmal auf Deutsch definieren und
übersetzen ergibt Deutsch mit französischen Wörtern.

---

## 10. Namenserkennung — Dokument-Propagation

Anreden (`Herr`, `Frau`, `Monsieur`, `Signora`, `Dr.`) sind **Merkmal,
nicht Label** → auf `O` trainiert.

> «Herr Meier beantragte am 3. März… Meier reichte die Unterlagen verspätet
> ein… Die Einsprache von Meier ist abzuweisen. Sachbearbeiter: R. Bertholet»

Anrede einmal, Name viermal. **Sobald ein Wert irgendwo mit hoher
Konfidenz erkannt wurde, wird jedes weitere Vorkommen desselben Werts
maskiert** — auch das nackte «Meier». Grösster einzelner Recall-Gewinn im
ganzen System.

---

## 11. Labeling-Vertrag

**Das Sprachmodell schreibt ausschliesslich Prosa mit Slots und sieht nie
einen echten Wert.** Der Code injiziert die Werte und erzeugt die
BIO-Labels aus den Einsetzpositionen.

1. Der Injektor merkt sich beim Einsetzen die Zeichen-Offsets.
2. Tokenisieren, BIO daran ausrichten (`core/alignment.py`).
3. **Round-Trip:** jeden gelabelten Span zurücklesen und mit dem
   eingesetzten Wert vergleichen.
4. Kein Match → **Zeile verwerfen**, nicht ins Training.

**Layout-Rauschen ist Pflicht**, weil der echte Input aus PDFs und Mails
kommt: Zeilenumbrüche in Entitäten, Tippfehler, aufgelöste Umlaute,
Versalien. Ein Zeilenumbruch mitten in einem Namen muss den Round-Trip
überleben.

**Haltezone:** ein Zehntel der Nomenklaturwerte wird deterministisch
zurückgehalten und nur in der Auswertung verwendet. Fällt der Wert dort
ab, hat das Modell die Liste gelernt und nicht die Form.

---

## 12. Country Pack

```
packs/
└─ ch/
   ├─ pack.yaml            Manifest: Version, Sprachen, Backbone, Labelvertrag
   ├─ taxonomy.yaml        45 Tags: Stufe, Aktion, Budget, BIO-Index, Schwellen
   ├─ patterns.yaml        Regex + Kontextanker, viersprachig
   ├─ macros.yaml          Expansionen + Kopplungsregeln
   ├─ bezeichnungen.yaml   Tagnamen in vier Sprachen
   ├─ modell.json          woher das Modell kommt, Grösse, Prüfsummen
   ├─ validators/          Prüfsummen
   ├─ generators/          Identifikatoren
   ├─ nomenclatures/
   │  ├─ build.py          raw → normalisiert, reproduzierbar
   │  ├─ raw/              (nicht im Repository) Downloads
   │  └─ dist/             (nicht im Repository)
   ├─ templates/           de/ fr/ it/ en/
   ├─ eval/                nur Wegweiser; das Testset liegt ausserhalb
   └─ adapter.py
```

### Adapter-Interface

```python
def get_tags()          -> tuple[Tag, ...]      # in der eingefrorenen Reihenfolge
def get_labels()        -> tuple[str, ...]      # BIO-Liste, stabile Reihenfolge
def get_label_hash()    -> str                  # Fingerabdruck des Labelvertrags
def get_bezeichnungen(sprache) -> dict[str, str]
def get_actions()       -> dict[str, str]       # mask | tag_only
def get_thresholds()    -> dict[str, float]     # aus Budget, Ausnahmen je Tag
def get_placeholders()  -> dict[str, str]
def validate()          -> list[str]            # Befunde, leer = in Ordnung
```

### Drei Fallen

1. **Labelreihenfolge einfrieren.** Die BIO-Indexreihenfolge ist Vertrag.
   Neue Tags **anhängen, nie einfügen** — sonst passen alte Checkpoints
   stillschweigend nicht mehr. Reihenfolge explizit in `taxonomy.yaml`.
2. **Checkpoint kennt den Pack.** In jedem Modellordner: Pack-Version und
   Hash der Labelliste, beim Laden geprüft. Ohne das lädt man irgendwann ein
   Modell mit falschem Mapping und bekommt plausibel aussehenden Unsinn —
   nichts stürzt ab.
3. **Nomenklaturen nicht ins Repository.** `build.py` erzeugt sie
   reproduzierbar; verteilt wird der Bauplan, nicht die Daten.

---

## 13. Training

- **Backbone:** mmBERT-base. Nicht ohne Messung wechseln.
- **Sequenzlänge 512** im Training. Trainingsdaten sind satz- und
  absatzweise; lange Dokumente verarbeitet die Anwendung in überlappenden
  Fenstern, mit Sondertoken **je Fenster**.
- **bf16** setzt eine GPU ab Ampere voraus. Das Training braucht eine GPU,
  die Anwendung nicht.
- **Keine externe API in der Kette** — die Vorlagen entstehen an einem
  lokalen, OpenAI-kompatiblen Endpunkt.
- **Streuung messen.** Derselbe Datensatz mit verschiedenen Keimen kann
  weiter auseinanderliegen als zwei Bedingungen (`tools/streuung.py`).

---

## 14. Evaluation

| Set | Ort | Zweck |
|---|---|---|
| **Synthetisch** | aus der Haltezone erzeugt (`tools/mess_synthetisch.py`) | reproduzierbar — Erzeuger, Keim und Code-Stand genügen |
| **Dokument-Testset** | lokal, nie im Repository | echte Dokumentarten, Personendaten durch Nomenklaturwerte ersetzt |

**Wer nur auf synthetischen Daten aus dem eigenen Generator misst, misst,
ob das Modell den Generator gelernt hat.** Deshalb beide:

    synthetisch   = misst genau, sieht nur die eigene Welt
    Golddokument  = misst grob, sieht die Wirklichkeit

Das Dokument-Testset enthält echte Dokumente — auch nach dem Ersetzen der
Werte bleibt ihre Struktur schützenswert. Es wird nicht veröffentlicht;
nur seine Zahlen. Siehe `docs/GOLDDOKUMENTE.md`.

**Der Report weist die Fehlerbudget-Klassen getrennt aus** (Abschnitt 4)
und nennt die **Leckrate** — den gewichteten Anteil der Entitäten, die
maskiert werden müssten und es nicht wurden — mit der absoluten Zahl
daneben.

---

## 15. Betrieb

| | |
|---|---|
| **Nur `127.0.0.1`** | `--host 0.0.0.0` ist möglich und warnt |
| **Serverseitig nichts aufbewahren** | der Dienst würde sonst zur Klartext-Datenbank |
| **Nichts nachladen** | keine Schriften, keine Bibliotheken von aussen; einzige Ausnahme ist die Portprüfung in den Einstellungen, die eine selbst getippte lokale Adresse fragt |
| **Nichts senden** | `/api/senden` gibt es nicht; eingefügt wird von Hand |
| **Hinter einem Reverse Proxy** | nur mit Anmeldung davor; `MASCHERA_WIRT` nennt den Namen |

---

## 16. Was das Werkzeug auf die Platte schreibt

> **Nichts wird geschrieben ausser den Einstellungen des Anwenders** — alle
> nach `~/.config/maschera/`, alle nur auf ausdrücklichen Befehl.

| Endpunkt | Datei |
|---|---|
| `PUT /api/regeln` | `regeln.yaml` |
| `PUT /api/vorlieben` | `klartext.json` |
| `PUT /api/vorlagen` | `vorlagen.json` |
| `PUT /api/einstellungen` | `einstellungen.json` |

⚠️ **Der zweite Satz ist der wichtigere:** kein Dokumentinhalt, kein
Wörterbuch, kein Protokoll, keine Zwischendatei. Ein weiterer Fall, der
Text anfasst, ist durch diese Formulierung **nicht** gedeckt.

Alle vier prüfen gegen dieselbe Funktion, die später lädt. Eine abgelehnte
Eingabe lässt die bestehende Datei unberührt.

**Das Wörterbuch geht ebenfalls hinaus**, aber nicht über den Server:
«Vokabular herunterladen» erzeugt die Datei im Browser (`Blob`), der Dienst
sieht sie nie.

Dazu kommt ein Ort, der keine Einstellung ist: ein beim ersten Start
nachgeholtes Modell liegt unter `~/.local/share/maschera/modelle/`.

---

## 17. Offene Punkte

| # | Punkt | Blockiert |
|---|---|---|
| 1 | Prüfmechanismus `INSURANCE_CARD` verifizieren; gruppierte Schreibweise | Stufe-1-Einordnung |
| 2 | UID-Gewichte gegen die offizielle BFS-Spezifikation gegenlesen | Produktiveinsatz |
| 3 | Datenschutzrechtliche Beurteilung der Pseudonymisierung | Produktiveinsatz in Organisationen |
| 4 | Mit `# ?` markierte Tagbezeichnungen gegen TERMDAT prüfen | — |
