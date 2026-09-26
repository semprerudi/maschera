#!/usr/bin/env fish
# Das Docker-Abbild bauen und die Fassung fuer `compose` hinterlegen.
#
#     fish tools/paket/bauen.fish
#
# ⚠️ Warum ein Skript und nicht ein `docker build` von Hand: die Marke
# muss zur Nummer in `app/serve.py` passen, und `compose.yaml` muss
# dieselbe Marke finden. Von Hand sind das zwei Stellen, die auseinander
# laufen — und ein Container, der still ein altes Abbild faehrt, ist
# genau die Sorte Fehler, die niemand sieht.

set -l STAMM (realpath (dirname (status filename))/../..)
cd $STAMM
or exit 1

set -l FASSUNG (fish $STAMM/tools/paket/fassung.fish)
or exit 1

echo "MASCHERA $FASSUNG"
docker build -f tools/paket/Dockerfile -t maschera:$FASSUNG .
or exit 1

# `docker compose` liest `.env` aus dem Verzeichnis der Compose-Datei.
# Deshalb liegt sie in `tools/paket/` und nicht im Projektstamm.
#
# ERGAENZEN, NICHT UEBERSCHREIBEN (`>>`, nicht `>`): in der `.env` stehen
# die Werte des Betreibers. Ein Werkzeug, das sie zerstoert und dabei
# «geschrieben» meldet, ist schlimmer als eines, das abbricht.
set -l ENVDATEI $STAMM/tools/paket/.env
set -l rest
if test -f $ENVDATEI
    # Alle Zeilen ausser der Fassung behalten, in ihrer Reihenfolge.
    set rest (grep -v '^MASCHERA_FASSUNG=' $ENVDATEI)
end
printf '%s\n' $rest "MASCHERA_FASSUNG=$FASSUNG" > $ENVDATEI.neu
and mv $ENVDATEI.neu $ENVDATEI
or exit 1
echo "gesetzt in tools/paket/.env:  MASCHERA_FASSUNG=$FASSUNG"
if test (count $rest) -gt 0
    echo "  "(count $rest)" weitere Zeile(n) unveraendert erhalten"
end

# Derselbe Bau unter dem Namen, unter dem er auf GitHub liegt. Nur ein
# zweiter Name, kein zweites Abbild — hochgeladen wird er erst auf
# ausdrueckliches «Los» (`docker push`, von Hand).
set -l GHCR ghcr.io/semprerudi/maschera
docker tag maschera:$FASSUNG $GHCR:$FASSUNG
and docker tag maschera:$FASSUNG $GHCR:latest
or exit 1

docker images maschera:$FASSUNG --format '  {{.Repository}}:{{.Tag}}  {{.Size}}'
echo "  auch als $GHCR:$FASSUNG und :latest"
