# MASCHERA 2.4.0

**Now also for Intel Macs.** Nothing changes in how MASCHERA masks.

Website: [www.maschera.ch](https://www.maschera.ch)

## New

- **Intel Macs** (`MASCHERA-latest-x86_64.dmg`), macOS 13.4 Ventura or newer (older Ventura: run
  Software Update first). PyTorch no
  longer ships for Intel Macs, so this package computes the same model as ONNX with
  onnxruntime. On the gold test set and 200 synthetic cases it masks exactly the same as
  PyTorch, and no confidence value crosses a threshold differently. Detection needs about
  0.8 instead of 2.5 GB of memory (measured on Linux). GitHub builds for Intel Macs until about August 2027.
- PDF and Word files up to **25 MB** (was 10 MB).

## Fixed

- The Apple silicon package now states its minimum, **macOS 14 Sonoma**. PyTorch requires
  it; before, 23 program files required macOS 14 without the package saying so, and on
  macOS 11 to 13 the app could not start reliably. The build now
  checks every program file for architecture and minimum.

## Security and maintenance

- PyMuPDF 1.28 or newer (CVE-2026-3308).
- The AppImage is built on Ubuntu 24.04 and still runs from Ubuntu 22.04 and Debian 12;
  the build checks the glibc it needs.

Details: [CHANGELOG.md](CHANGELOG.md).

<!-- UNTEN -->

---

# MASCHERA 2.4.0

**Jetzt auch für Intel-Macs.** Wie MASCHERA maskiert, bleibt gleich.

- **Intel-Macs** ab macOS 13.4 Ventura: `MASCHERA-latest-x86_64.dmg`. Es rechnet dasselbe
  Modell mit ONNX statt PyTorch und maskiert in den Messungen genau gleich. Älteres
  Ventura: zuerst Softwareupdate.
- PDF- und Word-Dateien bis **25 MB**.
- Das Paket für Apple-Chips nennt sein Minimum, **macOS 14**.

Welches Mac-Paket? Apple-Menü › «Über diesen Mac»: «Chip» heisst Apple-Chip, «Prozessor»
heisst Intel.

**Fehler gefunden?** Bitte ein [Issue](https://github.com/semprerudi/maschera/issues)
eröffnen. Nie ein echtes Dokument oder echte Namen hineinkopieren.

Windows-Installer und macOS-Apps sind weiter nicht signiert. Prüfsummen in
`SHA256SUMS`, SBOMs (SPDX) liegen bei.
