# MASCHERA 2.3.1

**Security update: please upgrade.** Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Security

- **The check for Brotli PDF files could be bypassed in 2.3.0 (CVE-2026-111497).** An
  inline image split over two content streams of a page still reached the decoder.
  The streams of a page are now also checked together. If a PDF is refused, save it
  again with a PDF program or paste the text directly.

## Fixed

- A resource whose name starts with `/Xb` could cause a healthy PDF to be refused.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.3.1

**Sicherheitsupdate: bitte aktualisieren.** Wie MASCHERA maskiert, bleibt gleich.

- **Die Prüfung auf Brotli-PDF war in 2.3.0 umgehbar (CVE-2026-111497).** Ein über zwei
  Inhaltsströme verteiltes Inline-Bild erreichte den Decoder trotzdem. Das ist behoben.
  Ein abgewiesenes PDF speicherst du neu oder fügst den Text direkt ein.
- Ein gesundes PDF konnte wegen eines Ressourcennamens abgewiesen werden. Behoben.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
