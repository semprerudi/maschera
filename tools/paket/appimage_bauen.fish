#!/usr/bin/env fish
# MASCHERA als AppImage — eine Datei, kein root, kein Paketmanager.
#
#     fish tools/paket/appimage_bauen.fish
#
# Braucht `appimagetool` und `uv`. Ergebnis liegt in `dist/`.
#
# ⚠️ WARUM `uv` UND NICHT DAS SYSTEM-PYTHON. Eine AppImage wird zur
# Laufzeit unter `/tmp/.mount_XXXXXX` eingehaengt — der Pfad ist bei jedem
# Start ein anderer. Ein `venv` traegt seinen Pfad ABSOLUT in `pyvenv.cfg`
# und in jedem Startskript; er waere nach dem Einhaengen kaputt. `uv`
# liefert ein eigenstaendiges, verschiebbares CPython, und die Pakete
# gehen mit `pip install --target` in ein Verzeichnis, das ueber
# `PYTHONPATH` gefunden wird. Beides ueberlebt den Ortswechsel.
#
# ⚠️ Und deshalb NICHT das System-Python: die AppImage soll auf Ubuntu
# genauso laufen wie auf Arch. Ein Python, das auf der Baumaschine liegt,
# ist auf der Zielmaschine vielleicht eine andere Fassung — oder gar
# keine.

set -l STAMM (realpath (dirname (status filename))/../..)
set -l BAU $STAMM/dist/AppDir
set -l PYFASSUNG 3.13

# Die Fassungsnummer kommt aus `app/serve.py`, nicht aus dieser Datei —
# sonst truege die AppImage einen anderen Namen als die Zahl in
# `/api/zustand`.
set -l FASSUNG (fish $STAMM/tools/paket/fassung.fish)
or exit 1

cd $STAMM
or exit 1

for w in appimagetool uv
    if not command -v $w >/dev/null
        echo "ABBRUCH: $w fehlt."
        echo "  paru -S appimagetool-bin      # bzw. uv"
        exit 1
    end
end

if not test -f runs/ch-v63b/model.safetensors
    echo "ABBRUCH: runs/ch-v63b/model.safetensors fehlt."
    echo "  Ohne Modell leckt jeder Name — eine AppImage ohne Modell"
    echo "  ist kein Betriebszustand, sondern eine Leckquelle."
    exit 1
end

echo "── 1. Aufraeumen"
rm -rf $BAU
mkdir -p $BAU/usr/lib/maschera $BAU/usr/lib/python

echo "── 2. Eigenstaendiges Python $PYFASSUNG"
uv python install $PYFASSUNG
or exit 1
set -l PYQUELLE (uv python find $PYFASSUNG)
or exit 1
# Zwei Ebenen hoch: .../bin/python3 -> die Wurzel der Installation
set -l PYWURZEL (realpath (dirname $PYQUELLE)/..)
echo "   $PYWURZEL"
cp -a $PYWURZEL $BAU/usr/python
or exit 1

echo "── 3. Abhaengigkeiten nach usr/lib/python (mit Qt, rund 2 GB)"
$BAU/usr/python/bin/python3 -m pip install --quiet --no-cache-dir \
    --target $BAU/usr/lib/python \
    -r tools/paket/requirements-appimage.txt
or exit 1

# ⚠️⚠️ NACHSEHEN, NICHT HOFFEN: ist es wirklich die CPU-Fassung?
#
# `requirements-paket.txt` sagt `--extra-index-url`, und das ERGAENZT
# PyPI. Dass heute die CPU-Raeder gewinnen, liegt allein daran, dass
# `2.14.0+cpu` hoeher sortiert als `2.14.0`. Kippt das, kommen ueber 2 GB
# CUDA-Bibliotheken in eine AppImage, die keine GPU sieht — und es faellt
# NICHT auf, weil das Paket damit laeuft.
#
# Die Begruendung stand im Kommentar und in keiner Pruefung. Jetzt hier.
set -l torchfassung ($BAU/usr/python/bin/python3 -c \
    "import sys; sys.path.insert(0, '$BAU/usr/lib/python'); \
     import torch; print(torch.__version__)" 2>/dev/null)
if not string match -q "*+cpu*" -- "$torchfassung"
    echo "   HALT  torch ist '$torchfassung' — ohne '+cpu'."
    echo "         Das sind ueber 2 GB CUDA in einer AppImage ohne GPU."
    echo "         Siehe den Kopf von tools/paket/requirements-paket.txt."
    exit 1
end
echo "   ok    torch $torchfassung"

echo "── 4. MASCHERA selbst"
# ⚠️ Dieselbe Liste wie im Dockerfile, und aus derselben Rechnung:
# `app/serve.py` importieren und `sys.modules` nach Dateien unter dem
# Projektstamm durchsehen. Wer hier etwas ergaenzt, ergaenzt es dort auch —
# sonst laeuft die eine Verpackung und die andere stirbt beim Start.
for teil in app core packs
    cp -a $teil $BAU/usr/lib/maschera/
end
mkdir -p $BAU/usr/lib/maschera/tools
for datei in dokumente.py filter_document.py evaluate_model.py
    cp -a tools/$datei $BAU/usr/lib/maschera/tools/
end
# Was die Laufzeit nicht liest — die Liste steht in `draussen.txt`.
rm -rf $BAU/usr/lib/maschera/packs/*/nomenclatures \
       $BAU/usr/lib/maschera/packs/*/templates \
       $BAU/usr/lib/maschera/packs/*/macros.yaml \
       $BAU/usr/lib/maschera/packs/*/generators \
       $BAU/usr/lib/maschera/packs/*/eval \
       $BAU/usr/lib/maschera/packs/*/pack.yaml \
       $BAU/usr/lib/maschera/core/injector.py
find $BAU/usr/lib/maschera -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null

mkdir -p $BAU/usr/lib/maschera/runs
cp -a runs/ch-v63b $BAU/usr/lib/maschera/runs/
rm -rf $BAU/usr/lib/maschera/runs/ch-v63b/checkpoint-*
# Und alles, was Pickle sein kann — `training_args.bin` ist eine. Wird zur
# Laufzeit nicht gelesen (`core/modell.py`, `PFLICHT`), und eine Pickle-Datei
# im Paket kann beim Oeffnen Code ausfuehren. Dieselbe Liste: `.dockerignore`,
# `windows_bauen.py`; `tests/test_fenster.py` Punkt 25 haelt sie zusammen.
find $BAU/usr/lib/maschera/runs/ch-v63b -type f '(' -name '*.bin' -o -name '*.pt' \
    -o -name '*.pth' -o -name '*.pkl' -o -name '*.ckpt' -o -name '*.pickle' ')' -delete

# Die Lizenztexte fahren mit — das gebaute Paket steht unter AGPL-3.0, und
# wer es weitergibt, gibt den Text mit. `tests/test_fenster.py` Punkt 12.
mkdir -p $BAU/usr/share/licenses/maschera
cp LICENSE LICENSE-AGPL-3.0.txt LIZENZ.md $BAU/usr/share/licenses/maschera/

echo "── 5. Symbol und Eintrag"
# `maske.svg` liegt in der Oberflaeche; AppImage will PNG.
#
# DURCHSICHTIG um die Maske herum — kein Kaestchen. Die Maske traegt in
# `maske.svg` eine eigene weisse Flaeche und ist damit auf hell wie auf
# dunkel sichtbar; um sie herum darf durchscheinen, was die Leiste anzeigt.
#
# Kein stiller Rueckfall: fehlt der Zeichner, bricht der Bau ab und sagt,
# was zu installieren ist.
#
# Quadratisch, 256x256. Die Maske steht hochkant (1278x1506); ohne
# Leinwand darum kaeme ein 218x256 grosses Bild heraus, und ein
# Symbolthema, das quadratisch erwartet, verzieht es. Die Rechnung steht in
# `core/symbol.py`.
if command -v rsvg-convert >/dev/null
    rsvg-convert --page-width 256 --page-height 256 \
        --width 200 --height 236 --left 28 --top 10 -a \
        app/static/maske.svg -o $BAU/maschera.png
else if command -v magick >/dev/null
    magick -background none app/static/maske.svg \
        -resize 256x256 -gravity center -extent 256x256 $BAU/maschera.png
else
    echo "   ✖ Weder rsvg-convert noch magick — kein Symbol zu rechnen."
    echo "     paru -S librsvg     (oder imagemagick)"
    exit 1
end

echo "── 6. AppRun und .desktop"
cp tools/paket/AppRun $BAU/AppRun
chmod +x $BAU/AppRun
cp tools/paket/maschera.desktop $BAU/maschera.desktop

# Die Fassung in den Eintrag: `X-AppImage-Version` ist der Weg, den die
# AppImage-Spezifikation dafuer vorsieht, und Gearlever uebernimmt ihn beim
# Einrichten. Der Dateiname allein genuegt nicht — Gearlever kopiert die
# Datei beim Einrichten um und wirft den Namen dabei weg.
#
# Hier erzeugt, nicht in `tools/paket/maschera.desktop` eingetragen: die
# Fassung hat genau einen Verwalter (`tests/test_fenster.py` Punkt 7).
echo "X-AppImage-Version=$FASSUNG" >> $BAU/maschera.desktop
# Und gleich nachgesehen: ein Tippfehler oder eine leere `$FASSUNG` faende
# sonst erst der Anwender. Die Pruefung steht HIER und nicht in den
# Tests, weil nur der Bau weiss, welches `AppDir` frisch ist — eine
# Pruefung, die von der Lage der Maschine abhaengt, gehoert dorthin, wo die
# Lage bekannt ist.
set -l GESCHRIEBEN (grep '^X-AppImage-Version=' $BAU/maschera.desktop)
if test "$GESCHRIEBEN" != "X-AppImage-Version=$FASSUNG"
    echo "   ⚠ HALT: der Eintrag meldet «$GESCHRIEBEN» statt"
    echo "     «X-AppImage-Version=$FASSUNG». Gearlever zeigt dann die"
    echo "     falsche oder gar keine Fassung."
    exit 1
end

echo "── 7. Packen"
mkdir -p $STAMM/dist
set -l ZIEL $STAMM/dist/MASCHERA-$FASSUNG-x86_64.AppImage

# Die alte Datei ENTFERNEN statt sie zu ueberschreiben. Laeuft gerade eine
# AppImage aus dieser Datei, scheitert appimagetool sonst mit
#
#     Could not open regular file for writing as destination:
#     Text file busy
#
# `rm` geht auch bei einer laufenden Datei: der laufende Prozess behaelt
# seinen Inode, der Name wird nur geloest.
rm -f $ZIEL

# ⚠️ DIE UPDATE-ADRESSE — damit Gearlever eine Aktualisierung FINDET.
#
# Ohne sie vergleicht Gearlever nur die DATEIGROESSE (`content-length`
# gegen die lokale Datei, nachgelesen in `StaticFileUpdater`): zwei Bauten
# gleicher Groesse gaelten als «kein Update». Bei 1,6 GB, die sich zwischen
# zwei Fassungen um Kilobyte unterscheiden, ist das der Normalfall.
#
# Mit `-u` legt `appimagetool` die Angabe INS Abbild und erzeugt (weil
# `zsyncmake` da ist) die `.zsync` daneben. Gearlever liest daraus die
# SHA-1 — exakt statt geraten — und findet die Adresse von selbst, ohne
# dass auf jedem neuen Rechner jemand etwas eintippt.
#
# ⚠️ DER WIRTSNAME GEHOERT NICHT INS REPOSITORY.
# `test_veroeffentlichung.py` weist Rechnernamen zurueck, zu Recht. Er
# kommt aus `MASCHERA_UPDATE_URL` oder aus `tools/paket/.env` — beides
# ausserhalb von Git.
#
# ⚠️ Fehlt er, wird OHNE Update-Angabe gebaut — und das wird GESAGT. Ein
# stiller Sprung waere der Fehler, den `sync.fish` schon einmal gemacht
# hat: BEREIT melden ueber nichts.
set -l UPDATE_URL $MASCHERA_UPDATE_URL
if test -z "$UPDATE_URL"; and test -f $STAMM/tools/paket/.env
    set UPDATE_URL (string replace -rf '^MASCHERA_UPDATE_URL=' '' \
                    < $STAMM/tools/paket/.env | string trim -c '"')
end

set -l STABIL MASCHERA-latest-x86_64.AppImage
if test -n "$UPDATE_URL"
    echo "   Update-Adresse: $UPDATE_URL/$STABIL.zsync"
    # ⚠️ `--file-url` RELATIV. Die `.zsync` traegt intern eine `URL:`-Zeile;
    # steht dort ein absoluter Name, zeigt sie beim Umzug ins Leere.
    env ARCH=x86_64 appimagetool \
        -u "zsync|$UPDATE_URL/$STABIL.zsync" \
        --file-url "$STABIL" \
        $BAU $ZIEL
    or exit 1
else
    echo "   ⚠ MASCHERA_UPDATE_URL fehlt — gebaut OHNE Update-Angabe."
    echo "     Gearlever findet damit keine Aktualisierung."
    echo "     Setze sie in tools/paket/.env (siehe .env.beispiel)."
    env ARCH=x86_64 appimagetool $BAU $ZIEL
    or exit 1
end

# ⚠️ Neuere `appimagetool` legen die `.zsync` ins AKTUELLE Verzeichnis
# statt neben die AppImage — hier also in den Projektstamm. Dorthin
# gehoert sie nicht; sie kommt neben die AppImage.
set -l ZNAME (basename $ZIEL).zsync
if test -f $STAMM/$ZNAME; and not test -f $ZIEL.zsync
    mv $STAMM/$ZNAME $ZIEL.zsync
end

# ⚠️ STABILE NAMEN, damit die Adresse sich nicht mit jeder Fassung aendert.
# HARTE VERKNUEPFUNG und keine Kopie: 1,6 GB zweimal auf der Platte fuer
# dieselben Bloecke, und der Abgleich schoebe sie ein zweites Mal uebers
# Netz.
rm -f $STAMM/dist/$STABIL $STAMM/dist/$STABIL.zsync
ln $ZIEL $STAMM/dist/$STABIL
if test -f "$ZIEL.zsync"
    ln $ZIEL.zsync $STAMM/dist/$STABIL.zsync
    echo "   $STABIL + .zsync verknuepft"
else if test -z "$UPDATE_URL"
    # ⚠️ NICHT «zsyncmake fehlte?» raten. Beim ersten Lauf stand genau das
    # da, waehrend `zsyncmake` installiert war — der Grund war die
    # fehlende Adresse, und ohne `-u` erzeugt `appimagetool` gar keine
    # `.zsync`. Eine Meldung, die die falsche Ursache nennt, schickt den
    # Naechsten in die Irre; das ist teurer als keine Meldung.
    echo "   $STABIL verknuepft (keine .zsync — ohne MASCHERA_UPDATE_URL"
    echo "     erzeugt appimagetool keine)"
else
    echo "   ⚠ $STABIL verknuepft, aber KEINE .zsync — Adresse ist gesetzt,"
    echo "     also fehlt `zsyncmake`. Ohne sie vergleicht Gearlever"
    echo "     wieder die Dateigroesse. paru -S zsync"
end

# Nur in einer Arbeitsumgebung mit Abgleich: liegt `tools/sync.fish` da,
# geht die fertige AppImage gleich zum Abgleichserver — sonst holt ein
# zweiter Arbeitsplatz einen alten Stand. Nur das Paar `dist`, nicht der
# ganze Abgleich. Ohne das Skript gibt es nichts abzugleichen.
if test -f $STAMM/tools/sync.fish
    echo
    echo "── Hinauf zum Abgleichserver"
    fish $STAMM/tools/sync.fish hoch dist --jetzt
    or begin
        echo "   ⚠ Der Abgleich ist fehlgeschlagen. Die AppImage liegt hier,"
        echo "     aber am zweiten Arbeitsplatz kommt der ALTE Stand an."
        echo "     Von Hand: fish tools/sync.fish hoch dist --jetzt"
    end
end

echo
echo "FERTIG: $ZIEL"
du -h $ZIEL
