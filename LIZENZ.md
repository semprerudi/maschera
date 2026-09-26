# Lizenz

MASCHERA steht unter **zwei** Lizenzen, und welche gilt, hängt davon ab,
was du in der Hand hast.

| | | |
|---|---|---|
| **Quellcode** | MIT | `LICENSE` |
| **Ausgelieferte Binärdateien** — AppImage, Flatpak, Windows-Installer, Docker-Abbild | AGPL-3.0 | `LICENSE-AGPL-3.0.txt` |

Wer den Quellcode nimmt, ändert und weitergibt, ist unter MIT frei. Wer
ein **fertig gebautes** Paket — AppImage, Flatpak, Windows-Installer, Docker-Abbild — weitergibt oder
über ein Netz anbietet, tut das unter AGPL-3.0 — dann gehört der
Quellcode der eigenen Fassung dazu.

## Warum zwei

Die Binärdateien tragen Bibliotheken mit, deren Lizenzen strenger sind
als MIT — allen voran **PyQt6** (GPL-3) für das eigene Fenster unter Linux und
**PyMuPDF** (AGPL-3) für PDF. Sie zu ersetzen wäre möglich gewesen und
wurde geprüft:

- **PyQt6 → PySide6** (LGPL) ist **gestrichen**. Unter AGPL ist GPL-3
  verträglich; der Tausch hätte lizenzrechtlich nichts gewonnen.
- **PyMuPDF bleibt.** Das Schwärzen im PDF kommt als Funktion, und dafür
  gibt es keinen gleichwertigen Ersatz mit milderer Lizenz.

Ein einziges MIT über alles wäre also falsch gewesen: es hätte etwas
zugesagt, das die mitgelieferten Teile nicht hergeben.

## Das Modell

Die Gewichte sind **nicht** Teil des Quellcodes. Sie entstehen aus
synthetischen Daten, die aus den Nomenklaturen des Packs erzeugt werden,
und werden getrennt veröffentlicht. Wo sie liegen und unter welcher
Lizenz, steht im README.

⚠️ **Die Golddokumente, an denen gemessen wird, sind nicht
veröffentlichbar** — sie enthalten echte Personendaten. Damit kann
niemand die Kennzahlen an echten Dokumenten nachrechnen. Das steht offen
im README; die synthetische Messung ist dagegen vollständig
reproduzierbar.

## Übernommener Code

Teile von MASCHERA gehen auf
[rizzo-pii](https://github.com/Rizzo-AI-Academy/rizzo-pii) von Simone
Rizzo zurück, ebenfalls unter MIT: die Prüfsummen-Erkenner, die
Datumskohärenz und die Wachen der Vorlagenbank im Datenerzeuger, das
Abschalten einzelner Tags und die Vorlieben je Tag. Der
Urheberrechtsvermerk steht deshalb in `LICENSE` neben dem eigenen —
MIT verlangt, dass er jede Kopie begleitet.

Keine Verbindung zum Originalprojekt, keine Rechte an Name oder Marke
«Rizzo AI Academy» beansprucht.

## Dritte

Die mitgelieferten Bibliotheken behalten ihre eigenen Lizenzen. Die
Schriften liegen unter der SIL Open Font License; sie werden mit
ausgeliefert und nie nachgeladen.
