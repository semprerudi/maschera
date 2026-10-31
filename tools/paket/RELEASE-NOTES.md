# MASCHERA 2.3.0

**Security update: please upgrade.** The full documentation is now in the
repository too. Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Security

- **PDF files with Brotli compression are refused (CVE-2026-111497).** PyMuPDF
  contains a Brotli decoder with a flaw that a crafted PDF can reach during plain
  text extraction, and no fixed release exists yet. MASCHERA now checks every PDF
  before it reaches the decoder, including short forms, indirect filters and
  inline images. If a PDF is refused, save it again with a PDF program or paste
  the text directly. Other PDF files are not affected.

## New

- **Requirements catalog in `specs/`:** goals, functional and non-functional
  requirements, architecture, flow diagrams, detection, API, training, interface,
  design, security, decisions and a rebuild guide, plus a test catalog and lists
  generated from the code. In German.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.3.0

**Sicherheitsupdate: bitte aktualisieren.** Dazu steht jetzt die gesamte
Dokumentation im Repository. Wie MASCHERA maskiert, bleibt gleich.

- **PDF mit Brotli-Kompression werden abgewiesen (CVE-2026-111497).** Eine Lücke in
  der PDF-Bibliothek liess sich schon beim Auslesen des Textes erreichen. Ein
  abgewiesenes PDF speicherst du neu oder fügst den Text direkt ein.
- **Anforderungskatalog `specs/`:** alle Ziele, Anforderungen, Abläufe und Entscheide
  an einem Ort.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
