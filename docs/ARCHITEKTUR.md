# MASCHERA — wie es gebaut ist und warum

`SPEC.md` sagt, **was** das Werkzeug ist; `docs/API_OBERFLAECHE.md` ist der
massgebliche Vertrag der Endpunkte. Dieses Dokument sagt, **warum** die
Entscheide so gefallen sind. Bei einem Widerspruch gilt: **Code vor
Dokumentation.** Massgeblich sind `packs/ch/taxonomy.yaml` und der Hash des
Labelvertrags.

---

## 1. Was MASCHERA ist — und was es nicht ist

Lokale Maskierung für Schweizer Dokumente in vier Sprachen (de, fr, it,
en). Das Werkzeug ersetzt Personendaten durch Platzhalter und führt ein
Wörterbuch mit, über das die Ersetzung umkehrbar ist.

**Das Verfahren ist eine Pseudonymisierung, keine Anonymisierung.** Solange
das Wörterbuch existiert, bleiben die Daten nach revDSG Personendaten.
Deshalb heisst der Knopf in der Oberfläche «Maskieren» und nicht
«Anonymisieren». Wer das Wörterbuch verliert, hat nicht anonymisiert,
sondern die Daten verloren.

Das Werkzeug ist für alle gedacht, die mit Schweizer Dokumenten arbeiten —
Verwaltungen von Bund, Kantonen und Gemeinden, Unternehmen, Kanzleien,
Vereine und Private. Deshalb steht im Repository nichts, was auf eine
bestimmte Stelle, einen Rechner oder eine Person zeigt;
`tests/test_veroeffentlichung.py` hält das fest.

Aufbauend auf [rizzo-pii](https://github.com/Rizzo-AI-Academy/rizzo-pii):
Schweizer Sprachen und Formate, Nomenklaturen aus offenen Daten des Bundes
und ein dokumentbasiertes Testset.

---

## 2. Die Kette — drei Stufen und eine Zusammenführung

| Stufe | was sie tut | wer entscheidet |
|---|---|---|
| **1 — Prüfsummen** | AHV, UID, IBAN, QR, Luhn, GLN | die Mathematik, kompromisslos |
| **2 — Muster** | Regexe mit viersprachigen Kontextankern | der Anker, nicht die Form allein |
| **3 — Modell** | ein feinabgestimmtes mmBERT je Pack | die Konfidenz gegen eine Schwelle |
| **merge** | führt die drei zusammen, löst Überlappungen | Stufe 1 schlägt 2 schlägt 3 |

Drei Eigenschaften dieser Anordnung sind wichtig und nicht offensichtlich:

**Stufe 2 kann hinzufügen, nicht verbieten.** Ein Muster, das schweigt,
verhindert nichts — das Modell liefert dieselbe Spanne trotzdem. Wer eine
Erkennung *unterdrücken* will, muss das im Training tun oder in `merge`, und
`merge` ist der empfindlichste Teil der Kette.

**Das Modell ist notwendig, nicht optional.** `--ohne-modell` ist kein
Betriebszustand. Ohne Stufe 3 leckt jeder Personenname, den kein Muster
kennt — und Personennamen sind bewusst *kein* Stufe-2-Muster, weil ein
Muster für «Grossbuchstabe, dann Kleinbuchstaben» in einem deutschen Text
jedes Substantiv trifft.

**Dokument-Propagation ist der grösste Recall-Gewinn im System.** Sobald ein
String irgendwo mit hoher Konfidenz als `FULLNAME` erkannt wurde, wird jedes
weitere Vorkommen desselben Strings maskiert — auch das nackte «Meier» im
Verteiler, in der Tabelle, im Unterschriftenblock. Anreden (`Herr`, `Frau`,
`Monsieur`, `Avv.`) sind dabei **Merkmal, nicht Label**: sie werden auf `O`
trainiert, weil in einem echten Dokument der Name viermal steht und die
Anrede einmal.

**Lange Dokumente werden ganz gesehen.** Das Modell liest in Fenstern von
512 Token mit Überlappung. Beide Läufer — torch für Messungen, ONNX als
Alternative — müssen die Abschneidung des Tokenizers abschalten, sonst sieht
das Modell nur den Kopf. `tests/test_langes_dokument.py` baut dafür ein
Dokument, das lang genug ist.

---

## 3. Der Labelvertrag — 45 Tags, eingefroren

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
Einfrieren umfassender, wäre jede Kalibrierung ein Vertragsbruch —
`tests/test_labelvertrag_eingefroren.py` prüft deshalb **beides**: dass der
Hash steht, und dass Schwellen und `action` sich weiter bewegen dürfen.

### Was das Einfrieren nicht behauptet

**Nicht:** «Die Tagliste ist richtig.»
**Sondern:** «Die Golddokumente haben keine Lücke gezeigt, und eine Änderung
kostet ein Neutraining.»

Zeigt ein späteres Dokument ein fehlendes Tag, wird aufgetaut — mit
Begründung und neuem Hash im Test.

### Die Grenze des Vertrags

Tags mit dem Präfix `X_` stehen bewusst **ausserhalb**. Sie beschreiben
Formate, die nur eine einzelne Stelle kennt — eine Dossiernummer, eine
Kundennummer. Der Vertrag beschreibt, was das **Modell** vorhersagt, und das
Modell soll allen dienen. Solche Kennungen gehören in eigene Regeln
(`core/user_rules.py`, Beispiel in `beispiele/regeln.beispiel.yaml`), die
ohne Neutraining greifen.

---

## 4. Entscheide, die sich nicht von selbst verstehen

### Was als `ORG` zählt

`ORG` bezeichnet eine **Stelle, der eine Person zugeordnet werden kann** —
Arbeitgeber, Behörde, Verein, Firma, Amtsstelle. Getaggt wird, was über die
Zugehörigkeit auf eine Person zurückführt.

**Nicht** getaggt werden Namen von Registern, Anwendungen und Systemen
(`SAP`, `EasyGov`, `ePortal`, `Zefix`, `Sedex`). Zwei Begründungen, die je
für sich tragen:

1. Ein Registername identifiziert niemanden. Er benennt ein Werkzeug — und
   ein System hat keine Angehörigen.
2. In einem IT-Ticket ist der Anwendungsname der Sachinhalt. Wer ihn
   maskiert, macht das Ticket unbrauchbar, ohne dass jemand geschützt wäre.

Faustregel im Zweifelsfall: *Kann jemand dort angestellt sein?* Ja → `ORG`.
Nein → stehen lassen.

Im Training teilen sich zwei Listen die `ORG`-Plätze: rund 190
Behördennamen je Sprache und rund 20 000 Firmennamen aus dem
Handelsregister (`GETEILT` in `core/injector.py`). Verdeckte die
Behördenliste die Firmen, sähe das Modell als `ORG` nur Ämter — und hielte
«Šarić & Partner GmbH» für einen Personennamen.

### Übermaskierung ist kein Leck

Ein unterdrücktes Datum ist immer teurer als eines zuviel. Die Kette ist
durchgehend so gebaut — bei einem Zielkonflikt gewinnt der Recall.

Das hat eine Grenze, und der `ORG`-Entscheid oben ist sie: wo Übermaskierung
den **Zweck des Dokuments** kostet, wiegt sie doch. Der Merksatz entbindet
nicht vom Nachdenken.

### Die Schwellen sind gemessen, nicht gesetzt

`tools/kalibriere_schwellen.py` **setzt keine Schwelle.** Es zeigt für jedes
Tag die Kurve: bei welchem Wert wie viele Lecks entstehen und wie viel
übermaskiert wird. Welcher Punkt richtig ist, ist eine fachliche
Entscheidung — bei `RELIGION` wiegt ein Leck schwerer als bei `TIME`. Dafür
gibt es die Budgets `R`/`A`/`P`, und deshalb schlägt das Werkzeug vor und
schreibt nichts.

⚠️ Tags unter fünf Belegen werden weggelassen. Eine Schwelle auf einer
einzigen Goldspanne ist geraten, nicht gemessen; die Belegzahl steht
deshalb in jeder Zeile.

### Eine Form je Sprache

Schweizer Amtsbegriffe haben je Amtssprache **eine** richtige Form (eCH).
Eine unbekannte Sprache führt zu einem Fehler, nicht zu einem stillen
Rückfall auf Deutsch. Eine deutsche Ausprägung in einem französischen
Dokument ist keine Näherung, sondern falsch.

### Keine medizinischen Inhaltstags

Der Vertrag kennt keine Tags für Diagnosen, Medikamente oder Behandlungen.
Eine Pathologie ohne Identität ist kein Personendatum; wer sie maskiert,
macht den Arztbericht unbrauchbar, ohne jemanden zu schützen — dieselbe
Überlegung wie beim `ORG`-Entscheid.

Was schützt, ist die **Kennnummer**, über die eine Person zurückgeholt
werden kann — und die führt der Vertrag durchgehend als besonders
schützenswert: `INSURANCE_CARD`, `PATIENT_ID`, `SOCIAL_INSURANCE`,
`INSURANCE_POLICY`, `HEALTHCARE_ORG`, dazu `ZSR_RCC`, `GLN` und `AHVN13`.

### Warum es drei Verpackungen gibt und keine `.deb`

Sie unterscheiden sich in **einer** Frage: fährt das Modell mit (1,2 GB)
oder wird es beim ersten Start geholt?

| | Paket | Modell |
|---|---|---|
| AppImage | rund 1,7 GB | fährt mit |
| Flatpak | rund 0,3 GB, dazu die KDE-Laufzeit | wird geholt |
| Docker | — | fährt mit |

**Kein `.deb`**, und der Grund ist gemessen. Debian und Ubuntu paketieren
`flask`, `yaml`, `pymupdf`, `olefile`, `qtpy` und `PyQt6-WebEngine` —
**PyTorch, `transformers` und `tokenizers` nicht**. Ein `.deb` könnte seine
Hauptabhängigkeit also nicht aus dem System beziehen. Das Flatpak deckt
Debian, Ubuntu, Fedora und openSUSE in **einem** Bauweg.

Ein Paket, das seine Bibliotheken mit dem System teilt, ist kleiner — und
erbt jede Fassungsverschiebung zwischen zwei Paketquellen: liegt eine
Bibliothek in einer anderen Fassung vor als die, gegen die PyTorch gebaut
wurde, startet die Anwendung nicht. **Wer sich Bibliotheken teilt, teilt
auch die Unstimmigkeiten.** AppImage und Flatpak können diesen Fehler nicht
haben, weil sie nichts teilen.

### Das Modell wird geholt, aber erst gefragt

Wo das Modell nicht mitfährt, **fragt der erste Start**: er nennt Quelle,
Grösse und Ziel, und «Später» schliesst die Anwendung, ohne etwas zu laden.
Wer nur über WLAN laden will und gerade nicht darin ist, soll nicht vor
vollendete Tatsachen gestellt werden. Danach läuft alles ohne Netz.

Im Flatpak ist `--share=network` deshalb die einzige heikle Erlaubnis, und
sie steht sichtbar am Paket. Sie wird für **einen** Vorgang gebraucht —
nicht fürs Maskieren, nicht fürs Öffnen eines Dienstes, nicht für
Statistik.

### Kein Zugriff auf das Heimatverzeichnis

Das Flatpak erhält **kein** `--filesystem=home`. Dokumente kommen über das
Dateiauswahl-Portal herein, das ausserhalb des Sandkastens läuft und genau
die eine gewählte Datei hereinreicht. Damit ist «es liest nur, was du ihm
gibst» keine Zusage mehr, sondern eine Eigenschaft.

---

## 5. Was das Werkzeug nicht tut

Diese Punkte stehen im Code und sind nicht verhandelbar. Sie sind der Grund,
warum das Werkzeug lokal überhaupt vertretbar ist.

| | |
|---|---|
| **Nichts wird geschrieben** | ausser den Einstellungen des Anwenders — Regeln, Vorlieben, Vorlagen, Einstellungen — und auch die nur auf ausdrücklichen Befehl. Kein Dokumentinhalt, kein Wörterbuch, kein Protokoll |
| **`/api/senden` gibt es nicht** | und wird es nicht geben. Wer den Text an einen Dienst geben will, kopiert ihn und fügt ihn von Hand ein. Eine Prüfung verlangt den 404 |
| **Keine Erkennung im Browser** | die ganze Kette läuft im Server. Eine Prüfung hält das fest |
| **Kein Nachladen von aussen** | genau eine benannte Ausnahme: die Portprüfung. Dazu eine Content Security Policy auf jeder Antwort |
| **Nie `innerHTML` mit Serverdaten** | ausnahmslos |
| **Ein leerer Befund ist keine Entwarnung** | ein Scan ohne Textebene ergibt einen Fehler mit Begründung, nicht «nichts gefunden» |

Der letzte Punkt ist der wichtigste und der am leichtesten zu übersehen. Ein
Werkzeug, das bei einem gescannten PDF ohne Textebene «keine Personendaten
gefunden» meldet, ist gefährlicher als eines, das gar nichts meldet.

---

## 6. Messen

Die Kennzahlen des ausgelieferten Modells stehen im README, mit beiden
Messgeräten: der reproduzierbaren synthetischen Messung
(`tools/mess_synthetisch.py`) und den Golddokumenten, die niemand
nachrechnen kann, weil sie echte Personendaten enthalten. Wie sich jeder
ein eigenes Testset anlegt, steht in `docs/GOLDDOKUMENTE.md`.

Zwei Regeln für das Lesen dieser Zahlen:

**Eine Gesamtzahl misst die Mischung des Testsets, nicht die Kette.**
Kommen leichtere Dokumente dazu, steigt der Micro-F1, ohne dass sich etwas
verbessert hat. Vergleichbar ist nur die Tabelle je Dokument, und nur am
selben Testset — wer eine Maildomain in einem Golddokument ersetzt, hat ein
anderes Testset.

**Ein kleines Testset löst wenig auf.** `tools/streuung.py` sagt, ob ein
Unterschied grösser ist als das Rauschen zwischen Läufen.

---

## 7. Bekannte Schwächen

| | |
|---|---|
| **Gesetzesdatum** | Ein Datum in «Bundesgesetz vom 25. September 2020 über den Datenschutz» ist kein Personendatum. Die Rückblicke im `DATE`-Muster greifen, aber das Modell liefert dieselbe Spanne auf Stufe 3 — und Stufe 2 kann hinzufügen, nicht verbieten. Vollständig lösbar nur im Training; ein Verbot in `merge` wäre ein Eingriff in den empfindlichsten Teil der Kette für eine **Übermaskierung**, also das falsche Risiko |
| **Zeichen ausserhalb Latin-1** | Der amtliche Zeichensatz der Personenregister umfasst Latin Extended-A. Namen und Heimatorte trägt Stufe 3 auch dann; bei Firmennamen mit solchen Zeichen fällt die Erkennung ab. Messung und Einzelheiten in `docs/ZEICHENSATZ.md` |
| **`INSURANCE_CARD`** | Das Muster trifft nur die **ungetrennte** Form der Nummer. Auf der Versichertenkarte steht sie gruppiert; `AHVN13` erlaubt im selben Musterbestand Trenner. Der Entscheid steht aus (`SPEC.md`, offene Punkte) |
| **`PERMIT_TYPE`** | im Vertrag vorhanden, in den Vorlagen aber kaum belegt — ein Vorlagen-, kein Vertragsproblem |

---

## 8. Wie geprüft wird

```
python3 tools/run_tests.py
```

Keine Abhängigkeiten ausser PyYAML und Flask für den Grossteil. Kein Modell,
keine GPU, keine Downloads nötig. Einige Erfahrungen stecken in der Art, wie
hier geprüft wird:

**Grosszügige Attrappen verschlucken Fehler.** Eine DOM-Attrappe, die für
alles ein Objekt liefert und `remove()` zur leeren Funktion macht, lässt
einen Absturz, der jeden Knopf lahmlegt, unsichtbar. Die Attrappe in
`tests/test_oberflaeche.js` ist deshalb **streng**: nicht vorhanden heisst
`null`, und jeder Zugriff darauf wirft.

**Eine Zusage im Kommentar ist keine Prüfung.** Die Frage, die am Anfang
steht: *welche Zusage steht in einem Kommentar und in keiner Prüfung?*

**Eine übersprungene Prüfung ist kein Erfolg.** Fehlt eine Abhängigkeit,
meldet die Prüfung `UEBERSPRUNGEN` am Zeilenanfang, und der Läufer zählt sie
nicht als bestanden — ein Skript, das sich selbst überspringt, gibt sonst 0
zurück.

**Der Einzelfall ist selten der Fall.** Dieselbe Sache mit mehreren
Verwaltern — ein Wert an mehreren Stellen, eine Liste in mehreren Dateien —
ist das häufigste Fehlermuster. Viele Prüfungen halten deshalb nicht einen
Wert fest, sondern die **Beziehung** zwischen den Stellen, die ihn tragen.
Die Frage gehört an den Anfang einer Fehlersuche: *welche anderen Stellen
haben dasselbe Muster?*

---

## 9. Herkunft und Quellen

Aufbauend auf [rizzo-pii](https://github.com/Rizzo-AI-Academy/rizzo-pii) von
Simone Rizzo (MIT). Keine Verbindung zum Originalprojekt, keine
Markenrechte an «Rizzo AI Academy» beansprucht.

Die Nomenklaturen stammen aus offenen Verwaltungsdaten. Alle verlangen eine
Quellenangabe; sie gehört in die Modellbeschreibung und in die Anwendung,
nicht nur hierhin.

| | |
|---|---|
| Nachnamen, Vornamen | Bundesamt für Statistik (BFS) |
| Ortschaften mit PLZ, Strassen | Bundesamt für Landestopografie (swisstopo) |
| Heimatorte | Bundesamt für Justiz (BJ/EJPD), eCH-0135 |
| Firmennamen | Zefix / EHRA über LINDAS, Provide-the-Source |

Die Rohdaten liegen **nicht** im Repository; `packs/ch/nomenclatures/build.py`
nennt die Bezugsquellen.

Lizenz: Quellcode MIT, ausgelieferte Pakete AGPL-3.0 — siehe `LIZENZ.md`.

---

## 10. Der Name

*maschera* ist italienisch für **Maske** — und trägt die Landeskennung
**CH** in der Mitte. Der Name ist der Sache nach genau: Das Werkzeug
**maskiert**. Es anonymisiert nicht, solange das Wörterbuch existiert.
