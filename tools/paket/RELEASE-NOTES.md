# MASCHERA 2.3.2

**Security update for Word files.** Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Security

- **Word: a document type declaration (DTD) could get past the check**, behind a long
  comment or in a document encoded as UTF-16. The whole document part is now searched
  in any encoding, and broken XML stops with a message instead of an error.
- Docker: every build now pulls Debian's security updates. The base image was missing
  the zlib fix from DSA-6613-1; MASCHERA does not use the affected function.

## Fixed

- The command in the READMEs to verify the Docker image signature named the tag of an
  old release and therefore failed.

## Maintenance

- New GitHub page with logo, preview and download buttons.
- GitHub Actions updated, still pinned to commits (cosign-installer 4.1.3 and others).

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.3.2

**Sicherheitsupdate für Word-Dateien.** Wie MASCHERA maskiert, bleibt gleich.

- **Word: Eine Dokumenttyp-Erklärung (DTD) kam an der Prüfung vorbei**, hinter einem
  langen Kommentar oder in einem UTF-16 kodierten Dokument. Jetzt wird der ganze Teil in
  jeder Kodierung durchsucht, und kaputtes XML bricht mit einer Meldung ab.
- Der Befehl zum Prüfen der Docker-Signatur in den READMEs nannte eine alte Fassung.
- Neue GitHub-Seite mit Logo, Vorschau und Download-Knöpfen.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert. Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
