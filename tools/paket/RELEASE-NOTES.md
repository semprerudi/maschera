# MASCHERA 2.1.1

A small polish of tile 03. Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Changed

- **"Prompt & masked text"** (was "Prompt + masked text") shows whether
  something has been taken over: an empty circle and pale text before, a short
  spin and then a check mark after "Take into prompt".
- "New", "Example" and other resets fold the outgoing text in 03 and the notes
  in 02 back in.
- On narrow screens, "Vocabulary applied" has a thin green border.
- The Docker image is now built and signed by the release workflow on GitHub;
  the README has the command to verify the signature.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.1.1

Kleiner Feinschliff an Kachel 03. Wie MASCHERA maskiert, bleibt gleich.

- **«Prompt & maskierter Text»** zeigt, ob schon etwas übernommen ist: vorher
  ein leerer Kreis und blasser Text, danach ein Haken.
- «Neu», «Beispiel» und anderes Zurücksetzen klappen die Tafeln in 02 und 03
  wieder zu.
- Auf schmalen Bildschirmen hat «Vokabular eingepflegt» einen dünnen grünen
  Rand.
- Das Docker-Abbild baut und signiert jetzt der Release-Workflow auf GitHub.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
