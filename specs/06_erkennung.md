# Erkennung

Die vollständige, aus dem Code erzeugte Liste steht in [tags.md](erzeugt/tags.md), die Muster in [erkennungsregeln.md](erzeugt/erkennungsregeln.md).

## Taxonomie: 45 Tags

BIO-Schema: `2 × 45 + 1 = 91` Labels.

**Legende Aktion:** `M` = maskieren · `T` = nur taggen (bleibt im Klartext)
**Legende Budget:** `R` = recall-first · `A` = ausgewogen · `P` = precision-first
**bsPD** = besonders schützenswerte Personendaten (revDSG Art. 5 Bst. c)

### Stufe 1: Prüfsummen-Override (6)

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

### Stufe 2: Regex mit Kontextanker, kein Override (17)

| Tag | Anker / Muster | Aktion | Budget |
|---|---|---|---|
| `EGID` | Kontextwort zwingend, 4-sprachig | M | R |
| `EWID` | Kontextwort zwingend, nur mit EGID | M | R |
| `MUNICIPALITY_ID` | Kontextwort zwingend | M | R |
| `INSURANCE_CARD` | `80756` + 15 Ziffern | M | R |
| `PHONE` | +41 / 0xx | M | A |
| `PLATE` | Kantonskürzel + 1 bis 6 Ziffern | M | A |
| `ZIPCODE` | 1000 bis 9699, Ortsname folgt | M | P |
| `AMOUNT` | CHF / Fr. / franc | M | P |
| `PERMIT_TYPE` | Ausweis B/C/Ci/L/G/F/N/S | M | R |
| `IDDOC` | Buchstabe + 7 Ziffern | M | R |
| `ZSR_RCC` | Zahlstellenregister | M | R |
| `PATIENT_ID` | Kontextwort zwingend | M | R |
| `CASE_ID` | Dossier-/Geschäftsnummer | M | A |
| `PARCEL` | Parzelle / Grundstück | M | A |
| `URL`, `IPADDRESS` | Standardmuster | M | P |
| `EMAIL` | Standardmuster | M | R |

### Stufe 3: rein neuronal (22)

| Tag | Aktion | Budget | Bemerkung |
|---|---|---|---|
| `FULLNAME` | M | **R** | zentraler Identifikator |
| `GIVENNAME` | M | **R** | |
| `DATE` | M | R | dazu ein deterministischer Erkenner gegen Zerstückelung |
| `TIME` | M | R | |
| `STREET` | M | R | |
| `BUILDINGNUM` | M | R | |
| `CITY` | M | A | Stadt ≠ Kleinstgemeinde, Kompromiss |
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
| `PLACE_OF_ORIGIN` | M | R | Heimatort, siehe unten |
| `CANTON` | **T** | P | trägt Kontext, identifiziert nicht |
| `ORG` | M | P | Schwelle 0.40, gemessen (siehe `taxonomy.yaml`) |
| `HEALTHCARE_ORG` | M | **R** | Spezialklinik verrät mehr als Diagnose |
| `USERNAME` | M | R | Kontoname, Pfadbestandteil, Anmeldename |

**Warum `PLACE_OF_ORIGIN` maskiert wird:** Der Heimatort verrät zwar nichts über den
Wohnort, aber Wohnorte mit Kantonskürzel sehen exakt aus wie Heimatorte («Reute AR»).
Ein als Heimatort gelesener Wohnort bliebe sonst im Klartext. Solange ein nicht
maskierendes Tag einem maskierenden zum Verwechseln gleicht, bleibt das ein Leck.
Der einzige Tag mit Aktion `T` ist `CANTON`.

**Stufe ist eine Eigenschaft des Tags, nicht der Quelle.** Stufe-3-Tags dürfen
zusätzlich Muster haben, zum Beispiel `ORG` und `PLACE_OF_ORIGIN`, und `DATE` einen
deterministischen Erkenner. Beim Vorrang zählt die Stufe des Tags.

### Warum keine medizinischen Inhaltstags

**Eine Pathologie ohne Identität ist kein Personendatum.** Solange nicht
klar ist, über wen gesprochen wird, schützt ihre Maskierung niemanden, sie
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
| `HEALTHCARE_ORG` | **bsPD**, eine Spezialklinik verrät mehr als eine Diagnose |
| `ZSR_RCC` · `GLN` | Leistungserbringer |
| `AHVN13` | Versichertennummer, Stufe 1 |

⚠️ Wer medizinische Inhaltstags braucht, muss den **Labelvertrag auftauen
und neu trainieren**, eine neue Tagliste macht jedes bisher trainierte
Modell unbrauchbar. Neue Tags werden angehängt, nie eingefügt.

## Fehlerbudgets

| | Recall-Fehler | Precision-Fehler |
|---|---|---|
| Was passiert | echtes Personendatum übersehen | Unbeteiligtes maskiert |
| Folge | Klartext geht hinaus | Text löchrig, Antwortqualität sinkt |
| Reparierbar | **nein** | ja, sofort sichtbar |

**Wirkung im System, ein Budget ohne diese zwei Konsequenzen ist Dekoration:**

1. **Entscheidungsschwelle** pro Tag-Klasse: `R` = 0.30, `A` = 0.50,
   `P` = 0.70. Eine Ausnahme je Tag braucht eine Messung, festgehalten neben
   dem Wert in `taxonomy.yaml`.
2. **Report** weist die Klassen **getrennt** aus, nie als einen Micro-F1.

Grundsatz: **Übermaskierung ist kein Leck.** Ein unterdrücktes Datum ist
teurer als eines zu viel.

## Prüfsummen

| Identifikator | Verfahren | Details |
|---|---|---|
| AHVN13 | EAN-13 | `756` + 9 Ziffern + Prüfziffer; Gewichte 1,3,1,3… von links über 12 Stellen |
| UID | Modulo-11 | `CHE` + 8 Ziffern + Prüfziffer; Gewichte **5,4,3,2,7,6,5,4**; Ergebnis 10 → nie vergeben, 11 → 0 |
| GLN | EAN-13 | identisch zu AHVN13, ohne 756-Prüfung |
| IBAN | Modulo-97 | ISO 13616; feste Länge je Land, CH/LI = 21 Zeichen |
| QR-Referenz | Modulo-10 rekursiv | 27 Stellen, Tabellenverfahren |
| Kreditkarte | Luhn | 12 bis 19 Ziffern |

Verifiziert gegen `756.9217.0769.85` und `CHE-116.281.710`, plus Round-Trip
über 2000 generierte Nummern je Typ.

> ⚠️ Die UID-Gewichte sind gegen echte Nummern gegengeprüft, **nicht**
> gegen die offizielle BFS-Spezifikation. Vor dem Produktiveinsatz
> gegenlesen.

**Das neuronale Modell läuft nie allein.** Das Netz aus Regex und
Prüfsummen verhindert den klassischen Fehlerfall, dass ein Tagger eine
lange Ziffernfolge in Fragmente zerlegt.

## Namenserkennung: Dokument-Propagation

Anreden (`Herr`, `Frau`, `Monsieur`, `Signora`, `Dr.`) sind **Merkmal,
nicht Label** → auf `O` trainiert.

> «Herr Meier beantragte am 3. März… Meier reichte die Unterlagen verspätet
> ein… Die Einsprache von Meier ist abzuweisen. Sachbearbeiter: R. Bertholet»

Anrede einmal, Name viermal. **Sobald ein Wert irgendwo mit hoher
Konfidenz erkannt wurde, wird jedes weitere Vorkommen desselben Werts
maskiert**, auch das nackte «Meier». Grösster einzelner Recall-Gewinn im
ganzen System.

## Der Labelvertrag: 45 Tags, eingefroren

```
Hash    b7a96dc99b05c6150302fc11943e0a357c7078b593e7382b4b06390245cceeee
Umfang  45 Tags, 91 BIO-Labels
```

Eingefroren, nachdem Golddokumente in vier Sprachen und vier Dokumenttypen
kein einziges Personendatum gezeigt hatten, das ein Tag gebraucht hätte,
das es nicht gibt.

### Was eingefroren ist und was nicht

| | |
|---|---|
| **Eingefroren** | die Tagliste und ihre **Reihenfolge**. Daraus entstehen die 91 BIO-Labels und der Hash |
| **Frei** | `action`, Schwellen, Budgets, Platzhalter, Muster, Vorlagen, Nomenklaturen, Benutzerregeln |

Der Unterschied ist mechanisch, nicht formal: eine neue Tagliste macht jedes
bisher trainierte Modell unbrauchbar, weil der Ausgabekopf eine andere
Grösse bekommt. Alles andere lässt sich ohne Neutraining ändern. Wäre das
Einfrieren umfassender, wäre jede Kalibrierung ein Vertragsbruch,
`tests/test_labelvertrag_eingefroren.py` prüft deshalb **beides**: dass der
Hash steht, und dass Schwellen und `action` sich weiter bewegen dürfen.

### Was das Einfrieren nicht behauptet

**Nicht:** «Die Tagliste ist richtig.»
**Sondern:** «Die Golddokumente haben keine Lücke gezeigt, und eine Änderung
kostet ein Neutraining.»

Zeigt ein späteres Dokument ein fehlendes Tag, wird aufgetaut, mit
Begründung und neuem Hash im Test.

### Die Grenze des Vertrags

Tags mit dem Präfix `X_` stehen bewusst **ausserhalb**. Sie beschreiben
Formate, die nur eine einzelne Stelle kennt, eine Dossiernummer, eine
Kundennummer. Der Vertrag beschreibt, was das **Modell** vorhersagt, und das
Modell soll allen dienen. Solche Kennungen gehören in eigene Regeln
(`core/user_rules.py`, Beispiel in `beispiele/regeln.beispiel.yaml`), die
ohne Neutraining greifen.

## Bekannte Schwächen

| | |
|---|---|
| **Gesetzesdatum** | Ein Datum in «Bundesgesetz vom 25. September 2020 über den Datenschutz» ist kein Personendatum. Die Rückblicke im `DATE`-Muster greifen, aber das Modell liefert dieselbe Spanne auf Stufe 3, und Stufe 2 kann hinzufügen, nicht verbieten. Vollständig lösbar nur im Training; ein Verbot in `merge` wäre ein Eingriff in den empfindlichsten Teil der Kette für eine **Übermaskierung**, also das falsche Risiko |
| **Zeichen ausserhalb Latin-1** | Der amtliche Zeichensatz der Personenregister umfasst Latin Extended-A. Namen und Heimatorte trägt Stufe 3 auch dann; bei Firmennamen mit solchen Zeichen fällt die Erkennung ab. Messung und Einzelheiten in [06 Erkennung](06_erkennung.md) |
| **`INSURANCE_CARD`** | Das Muster trifft nur die **ungetrennte** Form der Nummer. Auf der Versichertenkarte steht sie gruppiert; `AHVN13` erlaubt im selben Musterbestand Trenner. Der Entscheid steht aus ([01 Ziele](01_ziele.md)) |
| **`PERMIT_TYPE`** | im Vertrag vorhanden, in den Vorlagen aber kaum belegt, ein Vorlagen-, kein Vertragsproblem |

## Tags für das Kontextmenü: MASCHERA

45 Tags. Rechtsklick auf markierten Text: Maske setzen oder entfernen.

⚠️ = besonders schützenswertes Personendatum (revDSG). Braucht eine
zusätzliche Bestätigung beim Abschalten.

---

### Person

FULLNAME: Nachname, ganzer Name
GIVENNAME: Vorname
AGE: Alter
SEX: Geschlecht
MARITALSTATUS: Zivilstand

### Herkunft und Zugehörigkeit

NATIONALITY ⚠: Staatsangehörigkeit
RELIGION ⚠: Konfession
PLACE_OF_ORIGIN: Heimatort
RESIDENCE_STATUS: Niederlassung, Aufenthalt
PERMIT_TYPE: Ausweis B, C, L, G, F, N, S
VOTING_RIGHTS: Stimmrecht
COUNTRY: Land

### Anschrift und Ort

STREET: Strasse
BUILDINGNUM: Hausnummer
ZIPCODE: Postleitzahl
CITY: Ort

### Erreichbarkeit

EMAIL: Mailadresse
PHONE: Telefon
URL: Webadresse
IPADDRESS: IP-Adresse
USERNAME: Anmeldename

### Amtliche Nummern

AHVN13: AHV-Nummer
UID: Unternehmens-Identifikationsnummer
IDDOC: Pass- oder ID-Nummer
MUNICIPALITY_ID: BFS-Gemeindenummer
EGID: Gebäudeidentifikator
EWID: Wohnungsidentifikator
PLATE: Kontrollschild
PARCEL: Parzelle, Grundstück

### Finanzen

IBAN: Kontonummer
CREDITCARD: Kreditkarte
QR_REFERENCE: QR-Referenz
AMOUNT: Betrag

### Gesundheit und Versicherung

INSURANCE_CARD ⚠: Versichertenkarte
PATIENT_ID ⚠: Patientennummer
SOCIAL_INSURANCE ⚠: Sozialversicherung, IV-Fall
INSURANCE_POLICY ⚠: Policennummer
HEALTHCARE_ORG ⚠: Klinik, Praxis
ZSR_RCC: Zahlstellenregister
GLN: Medizinalperson

### Verfahren, Zeit, Organisation

CASE_ID: Dossier-, Geschäftsnummer
DATE: Datum
TIME: Uhrzeit
ORG: Firma, Behörde, Verein

### Nur erkannt, nie ersetzt

CANTON: Kantonskürzel

Bleibt immer im Klartext. Im Menü ausgegraut oder weglassen.

---

### Hinweise

Sechs Tags stammen aus Prüfsummen und sind mathematisch verifiziert:
AHVN13, UID, IBAN, QR_REFERENCE, CREDITCARD, GLN.

Sieben Tags sind besonders schützenswert (⚠). Sie sollten sich sichtbar
unterscheiden und beim Abschalten eine Rückfrage auslösen.

Ein Dokument enthält typisch 25 bis 55 Fundstellen. Im Kontextmenü sind
meist nur wenige Tags relevant, häufig verwendete zuerst, Rest hinter
einer Gruppierung.


## Der Zeichenumfang: was in einem Schweizer Namen stehen kann

Welche Zeichen in einem amtlich geführten Schweizer Namen stehen können,
und wie weit MASCHERA sie trägt.

### Die Rechtslage

Der Bundesrat entschied am **12. Mai 2021**, in allen Personenregistern der
Schweiz einen einheitlichen Zeichensatz einzuführen. Er besteht aus
**ISO 8859-1 + Latin Extended-A** und kam mit der Inbetriebnahme von
dem neuen Registersystem am **11. November 2024** zur Anwendung; seither werden Vor- und
Nachnamen in allen Personenstandsregistern so gespeichert. Der bis dahin
verwendete Satz war ISO 8859-15.

Quellen: Medienmitteilung des Bundesrats vom 12.5.2021, Leitfaden von
eOperations Schweiz und BFS, sowie die UPI-Schnittstellen eCH-0084, eCH-0085,
eCH-0086 und eCH-0212 in der Fassung 2.0 (produktiv seit 1.1.2024).

### Was das konkret heisst

```
U+0020 – U+007E     ISO 8859-1, unterer Teil
U+00A0 – U+00FF     ISO 8859-1, oberer Teil
U+0100 – U+017F     Latin Extended-A
```

Zusammen **319 druckbare Zeichen**. Alles ausserhalb, griechische,
kyrillische, vietnamesische Zeichen, und auch Latin Extended-B, kommt in
einem amtlich geführten Schweizer Namen nicht vor.

⚠️ **Latin Extended-B ist nicht dabei.** Das rumänische `ș` mit Komma
darunter ist `U+0219` und liegt ausserhalb; das ähnlich aussehende `ş` mit
Cedille ist `U+015F` und liegt darin. Wer die beiden verwechselt, misst am
falschen Zeichen.

### Wofür das im Projekt gilt

| Betrifft | Stand |
|---|---|
| **Schriften der Oberfläche** | `latin` und `latin-ext` decken den Satz ab, Vietnamesisch weggelassen. `tests/test_schriften.py` misst die Abdeckung je Schrift: IBM Plex Sans und Mono 319 von 319, Barlow Condensed (nur Wortmarke) mit ihren Lücken und Begründung |
| **Regex-Zeichenklassen** | Lücke, aber grösstenteils folgenlos. Latin Extended-A: 0 von 63 Grossbuchstaben am Wortanfang. Stufe 3 fängt es bei `FULLNAME` und `PLACE_OF_ORIGIN` auf; bei `ORG` schlägt es durch. Siehe unten |
| **Nomenklaturen** | Lücke. Latin Extended-A kommt in den Namenslisten praktisch nicht vor. Siehe unten |
| **Tokenizer** | kein Problem. Von 317 druckbaren Zeichen fällt **keines** auf `<unk>`. Siehe unten |
| **Volle Kette** | bei der letzten Messung alle echten Lecks bei `ORG`; Namen und Heimatorte trägt Stufe 3. Siehe unten |
| **Kodierungserkennung** | teilweise. `KODIERUNGEN` in `dokumente.py` versucht `cp1252` und `iso-8859-1`; beide können Latin Extended-A **nicht** darstellen. Eine Datei mit `Ł` liegt zwangsläufig in UTF-8 vor |

### Die Messung

Nachzumessen mit `tools/mess_zeichensatz.py`. Die Zahlen unten stammen von
einem früheren Modellstand; die Punkte 1 bis 3 hängen nicht am Modell.

#### Regex-Zeichenklassen: die Lücke ist echt

Gemessen wurde am **Wortanfang**, denn dort steht die enge Klasse; im
Wortinneren deckt `\w` den ganzen Unicode ab und niemand fällt durch. Je
Muster eine Probe, der Anfangsbuchstabe durch alle 119 Grossbuchstaben des
amtlichen Satzes ersetzt, Treffer über `core.recognizers.recognize()`
gezählt:

| Muster | Klasse im Muster | Latin-1 | Latin Extended-A |
|---|---|---|---|
| `ORG_FIRMA` | `[A-ZÄÖÜÀ-Þ]` | **56/56** | **0/63** |
| `ORG_BEHOERDE_KANTON` | `[A-ZÄÖÜÀ-Þ]` | **56/56** | **0/63** |
| `PLACE_OF_ORIGIN` | `[A-ZÄÖÜÀÉÈ]` | 32/56 | **0/63** |
| `ORG_BEHOERDE_AMT` | `[A-ZÄÖÜ]` | 29/56 | **0/63** |

Zwei Befunde, nicht einer:

**Latin Extended-A fällt überall durch, ausnahmslos.** Eine Firma
`Šarić & Partner GmbH`, ein `Łukasiewicz-Amt`, ein Heimatort `Žabern`,
Stufe 2 sieht keinen davon. Das ist die Lücke, die dieses Dokument
vermutet hat.

**Innerhalb von Latin-1 sind die vier Klassen verschieden breit.** `À-Þ`
gegen `ÀÉÈ` gegen gar nichts, dieselbe Sachfrage, vier Antworten. Das ist
die Klasse «eine Sache, mehrere Verwalter», diesmal in einer
Zeichenklasse. `PLACE_OF_ORIGIN` verliert 24 Zeichen, `ORG_BEHOERDE_AMT`
27, darunter `Ç`, `Ñ`, `Ø` und alle Akzente ausser `ÀÉÈ`.

⚠️ **Diese Zahlen messen Stufe 2 allein, nicht die Kette.** Die
Kettenmessung steht unter Punkt 4 und fällt deutlich anders aus: Stufe 3
fängt `FULLNAME` und `PLACE_OF_ORIGIN` vollständig auf. Wer diese Tabelle
allein liest, überschätzt die Lücke um den Faktor vier.

#### Nomenklaturen: das Modell sieht diese Zeichen nie

Zeichen aus Latin Extended-A, gezählt über die ganze Datei:

| Nomenklatur | Grösse | Latin-1 oben | Latin Extended-A |
|---|---|---|---|
| `nachnamen.json` | 10 065 KB | 18 075 | **0** |
| `vornamen.json` | 3 019 KB | 4 445 | **0** |
| `strassen.json` | 24 995 KB | 123 277 | **0** |
| `heimatorte.json` | 463 KB | 1 410 | **0** |
| `ortschaften.json` | 202 KB | 615 | **0** |
| `organisationen.json` | 567 KB | 5 086 | 3 |
| `behoerden.json` | 8 KB | 151 | **0** |

Der obere Teil von Latin-1 ist reichlich vertreten. Latin Extended-A ist
in **10 MB Nachnamen kein einziges Mal** vorhanden. In 2000 erzeugten
Trainingsbeispielen tragen 22 Zeilen ein solches Zeichen, und da die
Nomenklaturen keines liefern, stammen sie aus festem Vorlagentext, nicht
aus Namen.

Das heisst: selbst wenn die Muster geweitet würden, hätte das Modell
`Kovačević` im Training nie gesehen. Die beiden Zeilen hängen zusammen und
sind einzeln nicht lösbar.

#### Tokenizer: kein Problem

`jhu-clsp/mmBERT-base`, schneller Tokenizer vorhanden. Alle **317**
druckbaren Zeichen des Satzes einzeln durchgeschickt:

    auf <unk> gefallen: 0

Eine Nebenbeobachtung: ein Name
der Form `Ma?er` zerfällt in **1,6** Subwortstücke bei ASCII, in **2,97**
bei Latin-1 oben und in **2,95** bei Latin Extended-A. Kein Leck, aber
teurer im Kontextfenster.

(Dieses Dokument nennt 319 druckbare Zeichen, gemessen wurden 317. Der
Unterschied sind `U+00A0` und `U+00AD`, geschütztes Leerzeichen und
weicher Trennstrich , , die Python nicht als druckbar führt. Beide sind
keine Namenszeichen.)

#### Die volle Kette: die Lücke schlägt nur bei `ORG` durch

Gemessen mit `tools/mess_zeichensatz.py` an einem früheren Modellstand, 135 Proben, je
Zeichen ein Personenname, ein Firmenname und ein Heimatort. Drei Ausgänge
statt zwei, denn «nicht unter dem richtigen Tag gefunden» wirft zwei sehr
verschiedene Fälle zusammen:

| | |
|---|---|
| **richtig** | die Spanne ist da, unter dem erwarteten Tag |
| **falsches Etikett** | sie ist **maskiert**, aber unter einem anderen Tag. Kein Leck, der Klartext ist weg, das Wörterbuch führt ihn unter falschem Namen |
| **LECK** | nichts deckt die Stelle. Der Wert steht im Klartext |

| Block | Tag | richtig | Etikett | LECK | gefunden von |
|---|---|---|---|---|---|
| Latin-1 | `FULLNAME` | **55/55** | 0 | 0 | model |
| Latin-1 | `ORG` | **55/55** | 0 | 0 | regex |
| Latin-1 | `PLACE_OF_ORIGIN` | **55/55** | 0 | 0 | model, regex |
| LatExt-A | `FULLNAME` | **63/63** | 0 | 0 | model |
| LatExt-A | `PLACE_OF_ORIGIN` | **63/63** | 0 | 0 | model |
| LatExt-A | `ORG` | 4 | 45 | **14** | model |

**Stufe 3 fängt auf, was Stufe 2 nicht sieht, bei Namen und Heimatorten
vollständig.** `PLACE_OF_ORIGIN` steht in der Musterzeile auf 0 von 63 und
in der Kette auf 63 von 63. Deshalb werden die Muster nicht auf Verdacht
geweitet: die Lücke, die Stufe 2 zeigt, ist für zwei von drei Tags
folgenlos.

**Die Ausnahme ist `ORG`, und dort leckt es wirklich.** Bei 14 von 63
Zeichen bleibt der Firmenname im Klartext:

    Ē Ę Ě Ĝ Ğ Ģ Ī Ĭ İ Ŕ Ş Ű Ų Ÿ

Bei weiteren 45 Zeichen wird er maskiert, aber als `FULLNAME`, «Šarić &
Partner GmbH» wird zu «[FULLNAME_2] & Partner GmbH». Kein Leck, ein
falsches Etikett. Nur bei vier Zeichen (`Ă`, `Ĳ`, `Ř`, `Ŭ`) trifft das
Modell `ORG`.

⚠️ **Das hängt an den Trainingsdaten für `ORG`.** Ein Modell, das als `ORG`
vor allem Behördennamen gesehen hat, erkennt `Ģebhardt & Co. AG` nicht als
Firma, es sieht einen Personennamen und liegt damit fast richtig. Der
Datenerzeuger zieht `ORG` deshalb je zur Hälfte aus Behörden und aus
Firmennamen (`core/injector.py`).

**Was daraus NICHT folgt:** dass die Zeichenklassen zu weiten wären. Sie
sind für `FULLNAME` und `PLACE_OF_ORIGIN` nachweislich folgenlos, und für
`ORG` wäre eine breitere Klasse eine Behandlung des Symptoms.

#### Die Kennnummern

Im selben Lauf mitgemessen, je Schreibweise:

| Tag | ungetrennt | Leerzeichen | Punkt | Bindestrich | Apostroph |
|---|---|---|---|---|---|
| `AHVN13` | ok | ok | ok | ok (model) | ok (model) |
| `INSURANCE_CARD` | ok | **falsch: `ORG`** | **nichts** | **falsch: `PATIENT_ID`** | **nichts** |
| `ZSR_RCC` | ok | keine | **falsch: `SOCIAL_INSURANCE`** | keine | keine |
| `PATIENT_ID` | ok | keine | keine | ok | ok (Schrägstrich) |

`AHVN13` trägt alle fünf Schreibweisen: das Muster erlaubt `[.\s]?`, und
wo es nicht greift, springt das Modell ein. `INSURANCE_CARD` trägt eine
einzige, das Muster lautet `(?<!\d)80756\d{15}(?!\d)`. **Auf der
Versichertenkarte steht die Nummer gruppiert.**

⚠️ Dieselbe Sachfrage, zwei Antworten, in derselben Datei. Und die falschen
Etiketten sind hier gravierender als beim Zeichensatz: eine gruppierte
Versichertenkartennummer als `ORG` zu führen heisst, sie mit dem
`ORG`-Platzhalter zu ersetzen, kein Leck, aber ein Wörterbuch, das eine
Kennnummer als Organisation führt.

⚠️ **Nicht auf Verdacht die Muster weiten.** Eine breitere Zeichenklasse
ändert das Messergebnis, und ohne die Kettenmessung weiss niemand in
welche Richtung. Und die Nomenklatur sagt hier deutlich: die Zeichen sind
gar nicht drin.
