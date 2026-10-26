# MASCHERA 2.2.2

**Privacy fix, please update.** Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## Fixed

- **Telemetry of a library switched off.** Versions 2.1.1 to 2.2.1
  unintentionally contained onnxruntime 1.31, pulled in by PyMuPDF 2.0.
  Loading it opened a connection to Microsoft's telemetry service at start;
  measured in the Linux AppImage. The macOS app contains the same collector;
  on Windows the events go into the Windows diagnostic data. Documents,
  texts and vocabularies never passed through onnxruntime. This release switches
  the telemetry off at every start and keeps PyMuPDF below 2.0; onnxruntime
  is no longer in the packages. Docker images on an isolated network were
  not affected.
- **Downloads in the app window:** the download buttons (masked text, final
  text, vocabulary) did nothing on Linux. The save dialog appears again.
- **Template menu:** in the narrow layout it opened and closed at once.
- **Uploading a vocabulary:** it appeared only after 10 to 20 seconds. Now
  at once, and so does a saved template.

## New

- **Language choice in the welcome screen,** top right next to the cross.
- **On a server** the header says "Stores nothing" instead of "100% local",
  with an explanation on hover. Page 2 of the welcome screen says what
  applies on a server, too.

## Maintenance

- Flatpak dependencies with known vulnerabilities replaced (filelock,
  setuptools; certifi is no longer needed).
- pywebview pinned to 6.2.1 up to below 7.
- SECURITY.md names 2.2.x as the supported version.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.2.2

**Datenschutz-Korrektur, bitte aktualisieren.** Wie MASCHERA maskiert, bleibt
gleich.

- **Telemetrie abgestellt:** 2.1.1 bis 2.2.1 enthielten über PyMuPDF 2.0
  ungewollt onnxruntime, das beim Start Microsofts Telemetrie-Dienst
  ansprach (gemessen unter Linux; macOS gleich, Windows über die
  Diagnosedaten). Dokumente und Texte liefen nie hindurch. Diese Fassung schaltet
  das ab, onnxruntime ist nicht mehr in den Paketen.
- Behoben: Herunterladen im App-Fenster unter Linux, Vorlagenmenü in der
  schmalen Ansicht, Vokabular hochladen erscheint sofort.
- Neu: Sprachwahl im Willkommensschirm; auf einem Server «Speichert nichts»
  statt «100% lokal».

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-App sind weiter nicht signiert (siehe oben). Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
