# Ziele

## Ziel und Abgrenzung

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
Identifizierbarkeit ab, juristisch umstritten. Vor dem produktiven
Einsatz in einer Organisation, Verwaltung, Unternehmen, Kanzlei,
schriftliche Beurteilung durch die zuständige Datenschutzstelle einholen.

Das Werkzeug ist für alle gedacht, die mit Schweizer Dokumenten arbeiten,
Verwaltungen von Bund, Kantonen und Gemeinden, Unternehmen, Kanzleien,
Vereine und Private. Deshalb steht im Repository nichts, was auf eine
bestimmte Stelle, einen Rechner oder eine Person zeigt; eine Wache bei
jeder Veröffentlichung hält das fest.

Aufbauend auf [rizzo-pii](https://github.com/Rizzo-AI-Academy/rizzo-pii):
Schweizer Sprachen und Formate, Nomenklaturen aus offenen Daten des Bundes
und ein dokumentbasiertes Testset.

## Was das Werkzeug nicht tut

Diese Punkte stehen im Code und sind nicht verhandelbar. Sie sind der Grund,
warum das Werkzeug lokal überhaupt vertretbar ist.

| | |
|---|---|
| **Nichts wird geschrieben** | ausser den Einstellungen des Anwenders, Regeln, Vorlieben, Vorlagen, Einstellungen, und auch die nur auf ausdrücklichen Befehl. Kein Dokumentinhalt, kein Wörterbuch, kein Protokoll |
| **`/api/senden` gibt es nicht** | und wird es nicht geben. Wer den Text an einen Dienst geben will, kopiert ihn und fügt ihn von Hand ein. Eine Prüfung verlangt den 404 |
| **Keine Erkennung im Browser** | die ganze Kette läuft im Server. Eine Prüfung hält das fest |
| **Kein Nachladen von aussen** | benannte Ausnahmen: die Portprüfung, das Modell im Flatpak (nach Zustimmung) und «Nach Updates suchen» (nur auf Klick, eine feste Adresse, nur die Fassungsnummer; `core/neueste.py`). Dazu eine Content Security Policy auf jeder Antwort, die das Fenster auf Loopback hält |
| **Nie `innerHTML` mit Serverdaten** | ausnahmslos |
| **Ein leerer Befund ist keine Entwarnung** | ein Scan ohne Textebene ergibt einen Fehler mit Begründung, nicht «nichts gefunden» |

Der letzte Punkt ist der wichtigste und der am leichtesten zu übersehen. Ein
Werkzeug, das bei einem gescannten PDF ohne Textebene «keine Personendaten
gefunden» meldet, ist gefährlicher als eines, das gar nichts meldet.

## Herkunft und Quellen

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

Lizenz: Quellcode MIT, ausgelieferte Pakete AGPL-3.0, siehe `LIZENZ.md`.

---

## Der Name

*maschera* ist italienisch für **Maske**, und trägt die Landeskennung
**CH** in der Mitte. Der Name ist der Sache nach genau: Das Werkzeug
**maskiert**. Es anonymisiert nicht, solange das Wörterbuch existiert.

## Offene Punkte

| # | Punkt | Blockiert |
|---|---|---|
| 1 | Prüfmechanismus `INSURANCE_CARD` verifizieren; gruppierte Schreibweise | Stufe-1-Einordnung |
| 2 | UID-Gewichte gegen die offizielle BFS-Spezifikation gegenlesen | Produktiveinsatz |
| 3 | Datenschutzrechtliche Beurteilung der Pseudonymisierung | Produktiveinsatz in Organisationen |
| 4 | Mit `# ?` markierte Tagbezeichnungen gegen TERMDAT prüfen | keine |
