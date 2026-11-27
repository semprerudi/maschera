# MASCHERA 2.5.0

**Job titles and family roles are now masked too, with a new model.**

Website: [www.maschera.ch](https://www.maschera.ch)

## New

- Two new kinds of personal data: **job titles** ("project manager", "Head of Legal",
  "cheffe de projet") and **family roles** (father, grandmother, guardian). Together with
  the surroundings they can point to a person. Both are masked; under "Person" in the
  settings they can be left visible.
- **New model `ch-v71f`.** It continues the previous model instead of starting over.
  Names in the header of minutes are now recognised as persons, not as organisations.
  On the nine gold documents: 6 leaks as before, micro-F1 0.757 instead of 0.736. The
  Flatpak asks before it downloads the new model (1.2 GB).
- **Right-click on an ID or a type in the vocabulary** opens the same menu as in the
  masked text: change the type or remove the mask. Recently used tags come first.
- **"How it works" dialog** with small scenes: set a mask, change its type, remove it. It appears
  after the first masking until you switch it off, and it is in the menu.
- **Release notes** in the menu, in all four languages. They ship with the app; nothing
  is fetched from the internet.

## Changed

- Narrow layout: the tiles follow the window height, "Take into prompt" also sits
  below the vocabulary, and the vocabulary leaves out the type column so the original
  value can be read.
- Tooltips appear above the button instead of under the mouse pointer.
- The vocabulary sorts naturally: `DATE_2` before `DATE_10`.

## Compatibility

- Label contract with 47 tags and 95 labels. A model with the old contract does not load
  in this version.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.5.0

**Jetzt werden auch Berufe und Familienrollen maskiert, mit einem neuen Modell.**

- Zwei neue Arten von Personendaten: **Berufe** («Projektleiterin», «Amtschef», «Head of
  Legal») und **Familienrollen** (Vater, Grossmutter, Beistand). Zusammen mit dem Umfeld
  führen sie auf eine Person. Beide werden maskiert; in den Einstellungen unter «Person»
  kannst du sie sichtbar lassen.
- **Neues Modell `ch-v71f`.** Es setzt das bisherige fort, statt von vorn zu lernen.
  Namen im Kopf von Protokollen erkennt es als Personen statt als Organisation. An den
  neun Golddokumenten: 6 Lecks wie bisher, Micro-F1 0,757 statt 0,736. Das Flatpak
  fragt, bevor es das neue Modell lädt (1,2 GB).
- **Rechtsklick auf ID oder Typ im Vokabular** öffnet dasselbe Menü wie im maskierten
  Text: Typ ändern oder Maske entfernen. Zuletzt verwendete Tags stehen oben.
- **Dialog «Bedienung»** mit kleinen Szenen: Maske setzen, Typ ändern, Maske entfernen.
  Er erscheint nach dem ersten Maskieren, bis du ihn abschaltest, und steht im Menü.
- **Versionshinweise** im Menü, in allen vier Sprachen. Sie reisen mit der App, nichts
  wird aus dem Netz geholt.
- Schmales Design: Die Kacheln richten sich nach der Fensterhöhe, «Übernahme in Prompt»
  steht auch unter dem Vokabular, und das Vokabular lässt die Spalte «Typ» weg, damit
  man den Originalwert lesen kann.
- Tooltips erscheinen über dem Knopf statt unter dem Mauszeiger.
- Ein Modell mit dem alten Labelvertrag lädt diese Fassung nicht (jetzt 47 Tags, 95
  Labels).

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-Apps sind weiter nicht signiert. Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
