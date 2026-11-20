# MASCHERA 2.3.3

**Works properly on the phone.** Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Fixed

- **Phone: the page jumped back after a step.** While fitting the header, it was briefly
  wider than the screen; the browser zoomed out and reset the scroll position, on every
  redraw.
- **Phone: the template menu closed the moment it opened.** The keyboard shrank the
  window. The menu now follows its button and only closes when the button leaves the
  window or the width changes.
- Phone: the template menu was wider than the screen and cut off on the right.
- With a finger, MASCHERA no longer puts the cursor into a text field after «Übernahme
  in Prompt» or in the template menu, so the keyboard only opens when you ask for it.

## Maintenance

- docker/login-action 4.8.0, still pinned to its commit.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.3.3

**Läuft sauber auf dem Handy.** Wie MASCHERA maskiert, bleibt gleich.

- **Handy: Die Seite sprang nach einem Schritt wieder zurück.** Behoben.
- **Handy: Das Vorlagen-Menü ging sofort wieder zu** und war breiter als der
  Bildschirm. Es bleibt jetzt offen und passt aufs Display.
- Mit dem Finger geht die Tastatur nur auf, wenn man sie holt.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert. Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
