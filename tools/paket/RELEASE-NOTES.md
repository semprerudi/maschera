# MASCHERA 2.2.1

Polish of the header, the drop area and the welcome screen. Nothing changes
in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Changed

- **Header by space:** when it gets narrow, "100% local" goes first, then the
  tagline next to the logo, then the language choice becomes a list and
  finally the wordmark goes. Before, tagline and "100% local" disappeared as
  soon as the tiles were stacked, even in a wide window.
- **Step bar:** stays left as long as all five steps fit; only when it no
  longer fits does it scroll with the current step in the middle.
- On the last page of the welcome screen the mask sits as close to the
  wordmark as in the app header.

## Fixed

- The large drop area collapsed when the file was held still over it. It now
  stays open until the file is dropped or leaves the window.
- Paging through the welcome screen briefly showed a horizontal scrollbar.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.2.1

Feinschliff an Kopf, Ablage und Willkommensschirm. Wie MASCHERA maskiert,
bleibt gleich.

- **Kopf nach Platz:** zuerst fällt «100% lokal», dann der Spruch, dann wird
  die Sprachwahl zur Liste, zuletzt fällt der Schriftzug.
- **Schrittleiste:** steht links, solange sie passt, und rollt erst danach.
- Auf der Schlussseite des Willkommensschirms sitzt die Maske näher am
  Schriftzug.
- Behoben: Die grosse Ablagefläche fiel unter einer still gehaltenen Datei
  zusammen; beim Blättern im Willkommensschirm erschien kurz ein Rollbalken.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
