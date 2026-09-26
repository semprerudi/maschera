# Der Zeichenumfang — was in einem Schweizer Namen stehen kann

Welche Zeichen in einem amtlich geführten Schweizer Namen stehen können —
und wie weit MASCHERA sie trägt.

## Die Rechtslage

Der Bundesrat entschied am **12. Mai 2021**, in allen Personenregistern der
Schweiz einen einheitlichen Zeichensatz einzuführen. Er besteht aus
**ISO 8859-1 + Latin Extended-A** und kam mit der Inbetriebnahme von
dem neuen Registersystem am **11. November 2024** zur Anwendung; seither werden Vor- und
Nachnamen in allen Personenstandsregistern so gespeichert. Der bis dahin
verwendete Satz war ISO 8859-15.

Quellen: Medienmitteilung des Bundesrats vom 12.5.2021, Leitfaden von
eOperations Schweiz und BFS, sowie die UPI-Schnittstellen eCH-0084, eCH-0085,
eCH-0086 und eCH-0212 in der Fassung 2.0 (produktiv seit 1.1.2024).

## Was das konkret heisst

```
U+0020 – U+007E     ISO 8859-1, unterer Teil
U+00A0 – U+00FF     ISO 8859-1, oberer Teil
U+0100 – U+017F     Latin Extended-A
```

Zusammen **319 druckbare Zeichen**. Alles ausserhalb — griechische,
kyrillische, vietnamesische Zeichen, und auch Latin Extended-B — kommt in
einem amtlich geführten Schweizer Namen nicht vor.

⚠️ **Latin Extended-B ist nicht dabei.** Das rumänische `ș` mit Komma
darunter ist `U+0219` und liegt ausserhalb; das ähnlich aussehende `ş` mit
Cedille ist `U+015F` und liegt darin. Wer die beiden verwechselt, misst am
falschen Zeichen.

## Wofür das im Projekt gilt

| Betrifft | Stand |
|---|---|
| **Schriften der Oberfläche** | `latin` und `latin-ext` decken den Satz ab, Vietnamesisch weggelassen. `tests/test_schriften.py` misst die Abdeckung und führt die Lücken von Barlow mit Begründung |
| **Regex-Zeichenklassen** | Lücke, aber grösstenteils folgenlos. Latin Extended-A: 0 von 63 Grossbuchstaben am Wortanfang. Stufe 3 fängt es bei `FULLNAME` und `PLACE_OF_ORIGIN` auf; bei `ORG` schlägt es durch. Siehe unten |
| **Nomenklaturen** | Lücke. Latin Extended-A kommt in den Namenslisten praktisch nicht vor. Siehe unten |
| **Tokenizer** | kein Problem. Von 317 druckbaren Zeichen fällt **keines** auf `<unk>`. Siehe unten |
| **Volle Kette** | bei der letzten Messung alle echten Lecks bei `ORG`; Namen und Heimatorte trägt Stufe 3. Siehe unten |
| **Kodierungserkennung** | teilweise. `KODIERUNGEN` in `dokumente.py` versucht `cp1252` und `iso-8859-1`; beide können Latin Extended-A **nicht** darstellen. Eine Datei mit `Ł` liegt zwangsläufig in UTF-8 vor |

## Die Messung

Nachzumessen mit `tools/mess_zeichensatz.py`. Die Zahlen unten stammen von
einem früheren Modellstand; die Punkte 1 bis 3 hängen nicht am Modell.

### 1. Regex-Zeichenklassen — die Lücke ist echt

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
`Šarić & Partner GmbH`, ein `Łukasiewicz-Amt`, ein Heimatort `Žabern` —
Stufe 2 sieht keinen davon. Das ist die Lücke, die dieses Dokument
vermutet hat.

**Innerhalb von Latin-1 sind die vier Klassen verschieden breit.** `À-Þ`
gegen `ÀÉÈ` gegen gar nichts — dieselbe Sachfrage, vier Antworten. Das ist
die Klasse «eine Sache, mehrere Verwalter», diesmal in einer
Zeichenklasse. `PLACE_OF_ORIGIN` verliert 24 Zeichen, `ORG_BEHOERDE_AMT`
27, darunter `Ç`, `Ñ`, `Ø` und alle Akzente ausser `ÀÉÈ`.

⚠️ **Diese Zahlen messen Stufe 2 allein, nicht die Kette.** Die
Kettenmessung steht unter Punkt 4 und fällt deutlich anders aus: Stufe 3
fängt `FULLNAME` und `PLACE_OF_ORIGIN` vollständig auf. Wer diese Tabelle
allein liest, überschätzt die Lücke um den Faktor vier.

### 2. Nomenklaturen — das Modell sieht diese Zeichen nie

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
Trainingsbeispielen tragen 22 Zeilen ein solches Zeichen — und da die
Nomenklaturen keines liefern, stammen sie aus festem Vorlagentext, nicht
aus Namen.

Das heisst: selbst wenn die Muster geweitet würden, hätte das Modell
`Kovačević` im Training nie gesehen. Die beiden Zeilen hängen zusammen und
sind einzeln nicht lösbar.

### 3. Tokenizer — kein Problem

`jhu-clsp/mmBERT-base`, schneller Tokenizer vorhanden. Alle **317**
druckbaren Zeichen des Satzes einzeln durchgeschickt:

    auf <unk> gefallen: 0

Eine Nebenbeobachtung: ein Name
der Form `Ma?er` zerfällt in **1,6** Subwortstücke bei ASCII, in **2,97**
bei Latin-1 oben und in **2,95** bei Latin Extended-A. Kein Leck, aber
teurer im Kontextfenster.

(Dieses Dokument nennt 319 druckbare Zeichen, gemessen wurden 317. Der
Unterschied sind `U+00A0` und `U+00AD` — geschütztes Leerzeichen und
weicher Trennstrich —, die Python nicht als druckbar führt. Beide sind
keine Namenszeichen.)

### 4. Die volle Kette — die Lücke schlägt nur bei `ORG` durch

Gemessen mit `tools/mess_zeichensatz.py` an einem früheren Modellstand, 135 Proben, je
Zeichen ein Personenname, ein Firmenname und ein Heimatort. Drei Ausgänge
statt zwei, denn «nicht unter dem richtigen Tag gefunden» wirft zwei sehr
verschiedene Fälle zusammen:

| | |
|---|---|
| **richtig** | die Spanne ist da, unter dem erwarteten Tag |
| **falsches Etikett** | sie ist **maskiert**, aber unter einem anderen Tag. Kein Leck — der Klartext ist weg, das Wörterbuch führt ihn unter falschem Namen |
| **LECK** | nichts deckt die Stelle. Der Wert steht im Klartext |

| Block | Tag | richtig | Etikett | LECK | gefunden von |
|---|---|---|---|---|---|
| Latin-1 | `FULLNAME` | **55/55** | 0 | 0 | model |
| Latin-1 | `ORG` | **55/55** | 0 | 0 | regex |
| Latin-1 | `PLACE_OF_ORIGIN` | **55/55** | 0 | 0 | model, regex |
| LatExt-A | `FULLNAME` | **63/63** | 0 | 0 | model |
| LatExt-A | `PLACE_OF_ORIGIN` | **63/63** | 0 | 0 | model |
| LatExt-A | `ORG` | 4 | 45 | **14** | model |

**Stufe 3 fängt auf, was Stufe 2 nicht sieht — bei Namen und Heimatorten
vollständig.** `PLACE_OF_ORIGIN` steht in der Musterzeile auf 0 von 63 und
in der Kette auf 63 von 63. Deshalb werden die Muster nicht auf Verdacht
geweitet: die Lücke, die Stufe 2 zeigt, ist für zwei von drei Tags
folgenlos.

**Die Ausnahme ist `ORG`, und dort leckt es wirklich.** Bei 14 von 63
Zeichen bleibt der Firmenname im Klartext:

    Ē Ę Ě Ĝ Ğ Ģ Ī Ĭ İ Ŕ Ş Ű Ų Ÿ

Bei weiteren 45 Zeichen wird er maskiert, aber als `FULLNAME` — «Šarić &
Partner GmbH» wird zu «[FULLNAME_2] & Partner GmbH». Kein Leck, ein
falsches Etikett. Nur bei vier Zeichen (`Ă`, `Ĳ`, `Ř`, `Ŭ`) trifft das
Modell `ORG`.

⚠️ **Das hängt an den Trainingsdaten für `ORG`.** Ein Modell, das als `ORG`
vor allem Behördennamen gesehen hat, erkennt `Ģebhardt & Co. AG` nicht als
Firma — es sieht einen Personennamen und liegt damit fast richtig. Der
Datenerzeuger zieht `ORG` deshalb je zur Hälfte aus Behörden und aus
Firmennamen (`core/injector.py`).

**Was daraus NICHT folgt:** dass die Zeichenklassen zu weiten wären. Sie
sind für `FULLNAME` und `PLACE_OF_ORIGIN` nachweislich folgenlos, und für
`ORG` wäre eine breitere Klasse eine Behandlung des Symptoms.

### Die Kennnummern

Im selben Lauf mitgemessen, je Schreibweise:

| Tag | ungetrennt | Leerzeichen | Punkt | Bindestrich | Apostroph |
|---|---|---|---|---|---|
| `AHVN13` | ok | ok | ok | ok (model) | ok (model) |
| `INSURANCE_CARD` | ok | **falsch: `ORG`** | **nichts** | **falsch: `PATIENT_ID`** | **nichts** |
| `ZSR_RCC` | ok | — | **falsch: `SOCIAL_INSURANCE`** | — | — |
| `PATIENT_ID` | ok | — | — | ok | ok (Schrägstrich) |

`AHVN13` trägt alle fünf Schreibweisen: das Muster erlaubt `[.\s]?`, und
wo es nicht greift, springt das Modell ein. `INSURANCE_CARD` trägt eine
einzige — das Muster lautet `(?<!\d)80756\d{15}(?!\d)`. **Auf der
Versichertenkarte steht die Nummer gruppiert.**

⚠️ Dieselbe Sachfrage, zwei Antworten, in derselben Datei. Und die falschen
Etiketten sind hier gravierender als beim Zeichensatz: eine gruppierte
Versichertenkartennummer als `ORG` zu führen heisst, sie mit dem
`ORG`-Platzhalter zu ersetzen — kein Leck, aber ein Wörterbuch, das eine
Kennnummer als Organisation führt.

⚠️ **Nicht auf Verdacht die Muster weiten.** Eine breitere Zeichenklasse
ändert das Messergebnis, und ohne die Kettenmessung weiss niemand in
welche Richtung. Und die Nomenklatur sagt hier deutlich: die Zeichen sind
gar nicht drin.
