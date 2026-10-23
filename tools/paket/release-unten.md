## Found a problem?

Please open an [issue](https://github.com/semprerudi/maschera/issues): what you did,
what you expected, what happened, and the system (Windows / macOS / Linux, which
package). Never paste a real document or real names into an issue.

## Downloads

| File | For | Size | Model |
|---|---|---|---|
| `MASCHERA-latest-x86_64.AppImage` | Linux, any distribution | 1.7 GB | included |
| `MASCHERA-latest-x86_64.flatpak` | Linux with Flatpak | 0.3 GB + KDE runtime | fetched once on first start (1.3 GB), after you agree |
| `MASCHERA-latest-x64-setup.exe` | Windows 11, 64-bit | 1.4 GB | included |
| `MASCHERA-latest-arm64.dmg` | macOS, Apple silicon | 1.4 GB | included |
| `ghcr.io/semprerudi/maschera:{FASSUNG}` | Docker, server | 4.2 GB | included |

Checksums are in `SHA256SUMS`; SBOMs (SPDX) for the Docker image and the AppImage are
attached. The Windows installer is still **not signed**, so Windows warns on first
start: "More info" → "Run anyway". The macOS app is not signed either: after dragging it
into *Applications*, run once in *Terminal*:
`xattr -dr com.apple.quarantine /Applications/MASCHERA.app`.

```fish
docker run -d --name maschera -p 127.0.0.1:4141:4141 \
    ghcr.io/semprerudi/maschera:{FASSUNG}
```

## Licence

Source code MIT. The shipped packages are AGPL-3.0 because they bundle
PyMuPDF (AGPL-3) and, on Linux, PyQt6 (GPL-3); see `LIZENZ.md`. Model weights:
MIT, [semprerudi/maschera-ch-v63b](https://huggingface.co/semprerudi/maschera-ch-v63b).
