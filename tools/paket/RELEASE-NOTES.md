# MASCHERA 2.2.3

**Keyboard navigation and a safer way to get packages.** Nothing changes in
how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## New

- **Tab follows the steps.** In the three-column layout, Tab went from 01
  to 05 first and stopped at every small button. Now it moves only through
  fields and main buttons, in the order of the work: original text, Mask,
  masked text, Take over, Templates, Prompt, Send, Answer, Apply, final
  text, Copy, New. Shift+Tab goes the same way back; disabled buttons are
  skipped.
- **Arrow keys reach the small buttons.** When a button of a tile has the
  focus, ← and → move to the others: Clear, Copy, Download, Enlarge,
  Example, Vocabulary.
- **Open a file with the keyboard:** the drop area in 01 can be reached,
  Enter or Space opens the file dialog.

## Security

- **Each package from one source.** The builds named the PyTorch package
  index as an extra source next to PyPI, so pip could have taken any
  package from there (dependency confusion). Now only PyTorch itself comes
  from there, all other packages only from PyPI. Reported by Lockpick. The
  package lists are the same before and after the change.

## Maintenance

- PyTorch 2.15.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.2.3

**Bedienung mit der Tastatur und ein sicherer Bezug der Pakete.** Wie
MASCHERA maskiert, bleibt gleich.

- **Tab folgt den Schritten** von 01 bis 05, nur über Felder und
  Hauptknöpfe; Shift-Tab geht denselben Weg zurück. Die kleinen Knöpfe
  einer Kachel erreichen die Pfeiltasten, die Ablage öffnet mit Enter.
- **Jedes Paket aus einer Quelle:** Nur PyTorch kommt vom Index von
  PyTorch, alle anderen Pakete nur von PyPI (Hinweis von Lockpick).
- PyTorch 2.15.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
