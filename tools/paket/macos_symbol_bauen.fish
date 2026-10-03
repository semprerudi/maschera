#!/usr/bin/env fish
# Die Vorlage fuer das macOS-Symbol neu erzeugen: `macos-symbol-1024.png`.
#
#     fish tools/paket/macos_symbol_bauen.fish
#
# 1024 × 1024, die Maske (aus `app/static/maske.svg`, quadratisch gelegt) auf
# einer abgerundeten Flaeche in der Farbe der Seite, mit dem Rand, den macOS
# bei Symbolen erwartet. Gebraucht wird `rsvg-convert` und `magick`.
# Daraus macht `macos_bauen.py` auf dem Mac das `.icns`.
set -l stamm (realpath (dirname (status filename))/../..)
set -l tmp (mktemp -d)
python3 $stamm/tools/paket/symbol_quadrat.py $stamm/app/static/maske.svg $tmp/q.svg >/dev/null
or exit 1
rsvg-convert -w 560 -h 560 $tmp/q.svg -o $tmp/m.png
or exit 1
magick -size 1024x1024 xc:none -fill '#fdfaf6' \
    -draw "roundrectangle 100,100 923,923 185,185" $tmp/m.png \
    -gravity center -composite -strip $stamm/tools/paket/macos-symbol-1024.png
and echo "ok: tools/paket/macos-symbol-1024.png"
rm -rf $tmp
