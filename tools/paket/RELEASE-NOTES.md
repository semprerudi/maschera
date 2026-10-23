# MASCHERA 2.2.0

A welcome screen explains what MASCHERA can do. Nothing changes in how
MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## New

- **Welcome screen:** at start, five pages with a picture of the interface
  each explain MASCHERA's strengths: mask and restore, 100% local, quick work
  as a sidebar, deciding what gets masked, templates and your own chatbots.
  The last page leads to the example or to www.maschera.ch. "Don't show
  again" hides it; it is always back in the menu under "Welcome".
- **Larger drop area:** drag a file over the window and the drop area grows
  over the row and text field of 01, so you no longer have to aim.

## Changed

- In the red column (03 and 04) text is black instead of red, disabled items
  dark grey.
- Tile titles no longer wrap on narrow screens; the message next to them is
  shortened first, then the count.
- "New" and "Example" also reset open groups in the right-click menu, search
  words, filters and an enlarged tile.

## Fixed

- Settings, questions and help closed when you selected text in a field and
  dragged the mouse past the edge. They now close only when you press and
  release outside.
- In the app window, "Example" glowed at every start because the window
  forgot its browser storage. Such marks now live in the settings there.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.2.0

Ein Willkommensschirm erklärt, was MASCHERA kann. Wie MASCHERA maskiert,
bleibt gleich.

- **Willkommensschirm:** fünf Seiten zu den Stärken von MASCHERA, mit Bildern
  der Oberfläche. «Nicht mehr anzeigen» blendet ihn aus, im Menü steht er unter
  «Willkommen» wieder.
- **Grosse Ablagefläche:** Beim Hineinziehen einer Datei wächst die Ablage
  über Zeile und Textfeld von 01.
- In der roten Spalte ist die Schrift schwarz statt rot.
- Titel der Kacheln brechen auf schmalen Bildschirmen nicht mehr um.
- «Neu» und «Beispiel» setzen auch Rubriken, Suchwörter, Filter und eine
  vergrösserte Kachel zurück.
- Behoben: Dialoge schlossen sich beim Markieren über den Rand hinaus; im
  eigenen Fenster leuchtete «Beispiel» bei jedem Start.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
