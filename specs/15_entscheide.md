# Entscheide

Jeder Entscheid mit Grund. Eine Kennung wird nie neu vergeben.

### EN-001 Was als `ORG` zählt

`ORG` bezeichnet eine **Stelle, der eine Person zugeordnet werden kann**,
Arbeitgeber, Behörde, Verein, Firma, Amtsstelle. Getaggt wird, was über die
Zugehörigkeit auf eine Person zurückführt.

**Nicht** getaggt werden Namen von Registern, Anwendungen und Systemen
(`SAP`, `EasyGov`, `ePortal`, `Zefix`, `Sedex`). Zwei Begründungen, die je
für sich tragen:

1. Ein Registername identifiziert niemanden. Er benennt ein Werkzeug, und
   ein System hat keine Angehörigen.
2. In einem IT-Ticket ist der Anwendungsname der Sachinhalt. Wer ihn
   maskiert, macht das Ticket unbrauchbar, ohne dass jemand geschützt wäre.

Faustregel im Zweifelsfall: *Kann jemand dort angestellt sein?* Ja → `ORG`.
Nein → stehen lassen.

Im Training teilen sich zwei Listen die `ORG`-Plätze: rund 190
Behördennamen je Sprache und rund 20 000 Firmennamen aus dem
Handelsregister (`GETEILT` in `core/injector.py`). Verdeckte die
Behördenliste die Firmen, sähe das Modell als `ORG` nur Ämter, und hielte
«Šarić & Partner GmbH» für einen Personennamen.

### EN-002 Übermaskierung ist kein Leck

Ein unterdrücktes Datum ist immer teurer als eines zuviel. Die Kette ist
durchgehend so gebaut, bei einem Zielkonflikt gewinnt der Recall.

Das hat eine Grenze, und der `ORG`-Entscheid oben ist sie: wo Übermaskierung
den **Zweck des Dokuments** kostet, wiegt sie doch. Der Merksatz entbindet
nicht vom Nachdenken.

### EN-003 Die Schwellen sind gemessen, nicht gesetzt

`tools/kalibriere_schwellen.py` **setzt keine Schwelle.** Es zeigt für jedes
Tag die Kurve: bei welchem Wert wie viele Lecks entstehen und wie viel
übermaskiert wird. Welcher Punkt richtig ist, ist eine fachliche
Entscheidung, bei `RELIGION` wiegt ein Leck schwerer als bei `TIME`. Dafür
gibt es die Budgets `R`/`A`/`P`, und deshalb schlägt das Werkzeug vor und
schreibt nichts.

⚠️ Tags unter fünf Belegen werden weggelassen. Eine Schwelle auf einer
einzigen Goldspanne ist geraten, nicht gemessen; die Belegzahl steht
deshalb in jeder Zeile.

### EN-004 Eine Form je Sprache

Schweizer Amtsbegriffe haben je Amtssprache **eine** richtige Form (eCH).
Eine unbekannte Sprache führt zu einem Fehler, nicht zu einem stillen
Rückfall auf Deutsch. Eine deutsche Ausprägung in einem französischen
Dokument ist keine Näherung, sondern falsch.

### EN-005 Keine medizinischen Inhaltstags

Der Vertrag kennt keine Tags für Diagnosen, Medikamente oder Behandlungen.
Eine Pathologie ohne Identität ist kein Personendatum; wer sie maskiert,
macht den Arztbericht unbrauchbar, ohne jemanden zu schützen, dieselbe
Überlegung wie beim `ORG`-Entscheid.

Was schützt, ist die **Kennnummer**, über die eine Person zurückgeholt
werden kann, und die führt der Vertrag durchgehend als besonders
schützenswert: `INSURANCE_CARD`, `PATIENT_ID`, `SOCIAL_INSURANCE`,
`INSURANCE_POLICY`, `HEALTHCARE_ORG`, dazu `ZSR_RCC`, `GLN` und `AHVN13`.

### EN-006 Warum es mehrere Verpackungen gibt und keine `.deb`

Sie unterscheiden sich vor allem in **einer** Frage: fährt das Modell mit (1,2 GB)
oder wird es beim ersten Start geholt? Die Liste steht in
[12 Pakete und Release](12_pakete_release.md).

**Kein `.deb`**, und der Grund ist gemessen. Debian und Ubuntu paketieren
`flask`, `yaml`, `pymupdf`, `olefile`, `qtpy` und `PyQt6-WebEngine`,
**PyTorch, `transformers` und `tokenizers` nicht**. Ein `.deb` könnte seine
Hauptabhängigkeit also nicht aus dem System beziehen. Das Flatpak deckt
Debian, Ubuntu, Fedora und openSUSE in **einem** Bauweg.

Ein Paket, das seine Bibliotheken mit dem System teilt, ist kleiner, und
erbt jede Fassungsverschiebung zwischen zwei Paketquellen: liegt eine
Bibliothek in einer anderen Fassung vor als die, gegen die PyTorch gebaut
wurde, startet die Anwendung nicht. **Wer sich Bibliotheken teilt, teilt
auch die Unstimmigkeiten.** AppImage und Flatpak können diesen Fehler nicht
haben, weil sie nichts teilen.

### EN-007 Das Modell wird geholt, aber erst gefragt

Wo das Modell nicht mitfährt, **fragt der erste Start**: er nennt Quelle,
Grösse und Ziel, und «Später» schliesst die Anwendung, ohne etwas zu laden.
Wer nur über WLAN laden will und gerade nicht darin ist, soll nicht vor
vollendete Tatsachen gestellt werden. Danach läuft alles ohne Netz.

Im Flatpak ist `--share=network` deshalb die einzige heikle Erlaubnis, und
sie steht sichtbar am Paket. Sie wird für **einen** Vorgang gebraucht,
nicht fürs Maskieren, nicht fürs Öffnen eines Dienstes, nicht für
Statistik.

### EN-008 Kein Zugriff auf das Heimatverzeichnis

Das Flatpak erhält **kein** `--filesystem=home`. Dokumente kommen über das
Dateiauswahl-Portal herein, das ausserhalb des Sandkastens läuft und genau
die eine gewählte Datei hereinreicht. Damit ist «es liest nur, was du ihm
gibst» keine Zusage mehr, sondern eine Eigenschaft.

### EN-009 Eine Quelle für die Fassung

`VERSION` in `app/serve.py` ist die einzige Quelle, weil sie früher an sechs
Stellen stand. Die Bauskripte lesen sie mit `tools/paket/fassung.fish`.

### EN-010 Die Zahl steigt bei jeder Auslieferung

Die dritte Stelle steigt immer. Eine Zahl, die zwei verschiedene Stände
bezeichnet, ist in einem Fehlerbericht wertlos.

### EN-011 Testfassungen vor dem Release

Rückmelderunden laufen als `X.Y.Z-test.N` auf einer eigenen Testinstanz. Nur ein
fertiger Stand wird Release.

### EN-012 Ausgeliefert wird die torch-Kette

Der ONNX-Läufer int8 ist viel kleiner, leckte im Vergleich am selben Testset aber
mehr. Übermaskierung ist kein Leck, ein Leck schon. Deshalb fährt torch mit.

### EN-013 `ch-v63b` bleibt das Arbeitsmodell

Andere Läufe waren auf einzelnen Grössen besser. Die Schwellen sind aber auf
`ch-v63b` kalibriert, und richtig eingestellt liess es weniger Lecks als der Herausforderer. Ein
Wechsel verlangt neue Kalibrierung und mehrere Keime.

### EN-014 Keine Epochenänderung

Zwei Epochen brachten im Mittel über vier Keime weder bessere Werte noch weniger
Lecks, `ORG` wurde schlechter. Es bleiben drei.

### EN-015 Sequenzlänge 512

Der längste Trainingssatz hat 285 Token, bei 256 fielen Beispiele weg. Weil je
Stapel aufgefüllt wird, kostet 512 keinen Speicher.

### EN-016 Haltezone

Ein Zehntel der Nomenklaturwerte bleibt für die Auswertung reserviert. Nur so
lässt sich sehen, ob das Modell die Form gelernt hat statt der Liste.

### EN-017 Modell von einem festen Commit

Das Modell kommt von einem festen Commit auf Hugging Face, nie von `main`, und
jede Datei wird gegen ihre Prüfsumme geprüft.

### EN-018 Vokabular immer an

Der Schalter für das Vokabular ist weg. Wer es nicht braucht, arbeitet mit der
Antwort des KI-Werkzeugs weiter.

### EN-019 Grün heisst lokal, Rot heisst hinaus

Die Farbe sagt, ob man noch auf dem Gerät arbeitet. Die Spalte «hinaus» trägt
Rot, am Sendeknopf steht, dass der Text das Gerät verlässt.

### EN-020 Schriften

IBM Plex Sans und Mono für alles, nur die Wortmarke in Barlow Condensed. Die
Schriften liegen im Paket, nichts wird nachgeladen.

### EN-021 Knöpfe im Fuss der Kachel

Hauptknöpfe stehen im Fuss, nicht im Textfeld. Wird es eng, verlieren zuerst die
Nebenknöpfe ihr Wort.

### EN-022 Kopf nach Platz

Wird es eng, fällt zuerst «100% lokal», dann der Spruch, dann wird die Sprachwahl
zur Auswahlliste, zuletzt fällt der Schriftzug.

### EN-023 Tab folgt dem Arbeitsweg

Tab geht nur über Felder, Hauptknöpfe und die Vorlagenwahl, von 01 bis 05, «Neu» zuletzt. Nebenknöpfe erreicht man
mit den Pfeiltasten. Die Reihenfolge der Arbeit ist wichtiger als die Reihenfolge
im Quelltext.

### EN-024 Willkommensschirm mit Bildern der echten Oberfläche

Stärken standen sonst nur auf der Webseite. Die Bilder kommen aus der App und
werden vor dem Release neu aufgenommen, wenn sich die Oberfläche geändert hat.

### EN-025 Marken im Fenster liegen in den Einstellungen

Das eigene Fenster vergisst den Browserspeicher. Marken wie «nicht mehr anzeigen»
liegen dort in den Einstellungen, im Browser und auf dem Server im `localStorage`,
damit sich Anwender eines Servers keine Marke teilen.

### EN-026 Ein Befehl für das Release

Der Start des Befehls gibt jeden Schritt darin frei. Er prüft zuerst alles, was
sich prüfen lässt, und hält beim ersten Fehler an. GitHub baut alle Pakete.

### EN-027 Kein Cache für den Flatpak-Bau

Der Flatpak-Bau dauert rund 20 Minuten, davon 10 für `flatpak build-bundle`. Ein
Cache spart 2 bis 3 Minuten und bringt eine weitere Fehlerquelle in den
Release-Lauf.

### EN-028 Nur eine Paketquelle

Eine zusätzliche Paketquelle erlaubt Dependency Confusion. torch kommt einzeln
ohne Abhängigkeiten, alles andere nur von PyPI.

### EN-029 Keine Telemetrie, auch nicht fremde

MASCHERA enthielt über eine Abhängigkeit ungewollt eine Bibliothek, die beim Laden
eine Verbindung zu einem Telemetrie-Dienst öffnete. Dokumente liefen nie durch sie.
Sie ist entfernt, die Telemetrie wird an jedem Start abgeschaltet, und die
Abhängigkeit, die sie brachte, ist begrenzt.

### EN-030 Bestehende Geschichte auf GitHub

Der öffentliche Stand wächst durch normale Commits ohne Force-Push. Für den Zweig
`main` gilt ein Regelsatz dagegen.

### EN-031 Erkennen und Maskieren getrennt

Ein Tag kann erkannt werden, ohne ersetzt zu werden. Die Politik liegt in Daten,
sie lässt sich ohne Neutraining ändern.

### EN-032 Der Katalog wird bei jedem Release nachgeführt

`SPEC.md` stand vom 26.9. bis 30.10.2026 still, ohne dass etwas anschlug. Eine Maschine
sieht nicht, ob ein Satz stimmt, aber ob jemand hingesehen hat. Deshalb hält ein
Release ohne geändertes Kapitel an, und «unverändert» muss begründet sein. Eine
Sperrklinke hält neue Prüfpunkte an Anforderungen.

### EN-033 Brotli-Filter werden überschrieben, nicht gesucht

PyMuPDF bringt Brotli 1.2.0 statisch mit, das einen Schreibzugriff ausserhalb des Puffers
hat (CVE-2026-111497), und keine Fassung enthält den Fix. Mit harmlosen Proben gemessen
dekodiert MuPDF `/Filter` und `/F`, `BrotliDecode` und die Kurzform `Br`, als Name, im
Array, indirekt, mit `#xx` im Namen, in Objektströmen schon beim Öffnen und in
Inline-Bildern beim Textauszug. Ein kaputter Strom lässt es zudem hängen.

Die erste Fassung suchte Schlüssel und Wert. Eine Gegenlese fand vier Wege darum herum.
Deshalb werden jetzt drei Stufen genutzt:

1. Vor dem Öffnen wird jeder Brotli-Name in der Datei durch einen gleich langen,
   unbekannten Namen ersetzt, wo immer er steht. Ohne Namen gibt es keinen Filter.
2. Ein indirekter `/Filter` oder ein `/F` auf ein unsichtbares Ziel wird abgewiesen, denn
   dahinter könnte ein Name in einem Objektstrom stecken, den schon `open()` braucht.
3. Nach dem Öffnen werden alle Objekte und danach alle Ströme geprüft, vor dem Textauszug.
   So fallen auch Inline-Bilder und PDF auf, die wirklich Brotli nutzen.

Ein gültiges PDF mit indirektem Filter wird damit abgewiesen. Das ist selten, und die
Meldung sagt, was man tun kann. Die Wache fällt weg, sobald PyMuPDF einen Decoder ab
Brotli 1.2.1 mitbringt.

**Bekannte Grenze:** Ein Objektstrom hinter einem Filter, den Stufe 1 nicht sieht und der
nicht Flate ist, lässt sich nicht vollständig ausschliessen; Stufe 2 fängt den bekannten
Weg dorthin ab.
