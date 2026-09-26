#!/usr/bin/env fish
# Das Browsersymbol aus der Maske rechnen.
#
#     fish tools/favicon_bauen.fish
#
# Ergebnis: `app/static/favicon.ico`, mehrere Kantenlaengen in einer Datei.
#
# EINE QUELLE. `app/static/maske.svg` ist die Vorlage fuer alle Symbole
# dieses Projekts. Das `.ico` wird daraus ERZEUGT und nie von Hand gemalt.
#
# Warum ueberhaupt ein `.ico`: eine Schreibtischverknuepfung des Browsers
# zeigt kein SVG an. `<link rel="icon" href="maske.svg">` bleibt fuer die
# Browser, die es koennen — das `.ico` steht daneben.
#
# KEIN EINFAERBEN. `maske.svg` traegt ZWEI Farben: eine weisse Flaeche als
# Grund und darauf die dunklen Zuege. `-colorize 100` legt EINE Farbe ueber
# alle Farbkanaele und macht aus zwei Toenen einen — der Umriss bliebe,
# das Gesicht verschwaende. Die Maske bringt ihre Loesung selbst mit:
# weisser Grund traegt die Zuege auf dunklem Schreibtisch, die dunklen
# Zuege tragen den Grund im hellen Tab.

set -l STAMM (realpath (dirname (status filename))/..)
set -l QUELLE $STAMM/app/static/maske.svg
set -l ZIEL $STAMM/app/static/favicon.ico
set -l TMP (mktemp -d)

if not test -f $QUELLE
    echo "ABBRUCH: $QUELLE fehlt."
    exit 1
end

if not command -v magick >/dev/null
    echo "ABBRUCH: magick fehlt — es setzt die Kantenlaengen ins .ico."
    echo "  paru -S imagemagick"
    exit 1
end

# ⚠️ Die Maske ist 1278x1506 und damit NICHT quadratisch. Ein Symbol wird
# quadratisch erwartet; verzerrt sieht das Gesicht falsch aus. Also mittig
# in ein Quadrat einpassen und ringsum Luft lassen — dieselben Zahlen wie
# im AppImage-Bau, auf die jeweilige Kantenlaenge hochgerechnet.
#
# 16 bis 48 fuer den Tab, 64 bis 256 fuer die Verknuepfung auf dem
# Schreibtisch — dort wird das Symbol gross angezeigt.
set -l KANTEN 256 128 64 48 32 16

# JEDE KANTENLAENGE EINZELN AUS DEM SVG, nicht eine grosse Fassung
# heruntergerechnet. Aus 512 heruntergerechnet wird die Maske bei 16 px
# ein blasser grauer Fleck: ein Zug schrumpft auf unter einen Bildpunkt
# und mischt sich mit dem weissen Grund zu Grau. Direkt bei 16 gezeichnet
# legt rsvg den Zug auf das Punktraster, und Brauen, Augen und Mund
# bleiben unterscheidbar.
set -l TEILE

for K in $KANTEN
    # Dieselben Verhaeltnisse wie oben: 400/512 breit, 472/512 hoch,
    # 56/512 von links, 20/512 von oben.
    set -l W (math "round($K * 400 / 512)")
    set -l H (math "round($K * 472 / 512)")
    set -l L (math "round($K * 56 / 512)")
    set -l O (math "round($K * 20 / 512)")

    if command -v rsvg-convert >/dev/null
        rsvg-convert --page-width $K --page-height $K \
            --width $W --height $H --left $L --top $O -a \
            $QUELLE -o $TMP/k$K.png
        or exit 1
    else
        # ⚠️ Rueckfall ohne rsvg-convert. magick zeichnet das SVG in einer
        # Groesse und rechnet herunter — genau der Weg, der bei 16 px
        # verwaescht. Er ist hier, damit der Bau nicht scheitert, nicht
        # weil er gleich gut waere.
        magick -background none -density 600 $QUELLE \
            -resize {$W}x{$H} -gravity center -extent {$K}x{$K} $TMP/k$K.png
        or exit 1
    end
    set TEILE $TEILE $TMP/k$K.png
end

# ⚠️ KEIN `-define icon:auto-resize`. Die sechs Bilder liegen schon in der
# richtigen Groesse vor; auto-resize wuerde sie verwerfen und aus dem
# ersten neu rechnen — also genau das tun, was oben vermieden wurde.
magick $TEILE $ZIEL
or exit 1

rm -rf $TMP
echo "FERTIG: $ZIEL"
magick identify $ZIEL | awk '{print "   "$2, $3}'
