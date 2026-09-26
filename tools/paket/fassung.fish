#!/usr/bin/env fish
# Die Fassungsnummer aus `app/serve.py` — die einzige Quelle.
#
#     set -l V (fish tools/paket/fassung.fish)
set -l stamm (realpath (dirname (status filename))/../..)
set -l zeile (grep -m1 '^VERSION = ' $stamm/app/serve.py)
if test -z "$zeile"
    echo "ABBRUCH: keine VERSION in app/serve.py gefunden." >&2
    exit 1
end
echo $zeile | string replace -r '^VERSION = "(.*)"$' '$1'
