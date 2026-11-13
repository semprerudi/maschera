#!/usr/bin/env fish
# tools/abgleich-schritte.fish — was MASCHERA beim Ankommen und Gehen
# braucht, zusaetzlich zum Abgleich des Projektordners.
#
# Aufgerufen von ~/projekte/abgleich/abgleich.fish (PROJEKTE START/END) in
# vier Phasen; der Rueckgabewert ist die Zahl der offenen Punkte:
#
#     vor-start    Code holen (git pull) und den GitHub-Ordner holen --
#                  VOR dem rsync, sonst passt die Liste der verfolgten
#                  Dateien nicht
#     nach-start   Daten ausserhalb von ~/projekte holen (tools/sync.fish),
#                  Umgebung und Pruefungen
#     vor-ende     pruefen, committen, pushen; Daten ausserhalb hochschieben
#                  -- VOR dem rsync
#     nach-ende    Uebergabe pruefen (tools/sync.fish uebergabe)
#
# Bis 9.11.2026 standen diese Schritte direkt in
# ~/projekte/projekte-abgleich.fish. Seither ist der Abgleich fuer alle
# Projekte gleich, und was nur MASCHERA betrifft, liegt hier im Repository.

set -g MASCHERA (realpath (dirname (status --current-filename))/..)
set -g FEHLER 0
function kopf;    echo ""; set_color --bold; echo "── $argv"; set_color normal; end
function gut;     set_color green;  echo -n "   ok    "; set_color normal; echo $argv; end
function warnung; set_color yellow; echo -n "   !     "; set_color normal; echo $argv; end
function schlecht
    set -g FEHLER (math $FEHLER + 1)
    set_color red; echo -n "   HALT  "; set_color normal; echo $argv
end

function finde_python
    for k in $MASCHERA_PY $HOME/.venvs/sempre/bin/python \
             $HOME/.venvs/maschera/bin/python $VIRTUAL_ENV/bin/python \
             $MASCHERA/.venv/bin/python
        if test -n "$k"; and test -x "$k"
            echo $k
            return 0
        end
    end
    type -q python3; and command -v python3
end
set -g PY (finde_python)


# --- MASCHERA: ankommen ----------------------------------------------------

function maschera_code_holen
    if not test -d $MASCHERA/.git
        warnung "kein MASCHERA-Checkout unter $MASCHERA"
        return 0
    end
    set -l offen (git -C $MASCHERA status --porcelain)
    if test -n "$offen"
        schlecht "MASCHERA hat ungesicherte Aenderungen, der Code wird nicht geholt:"
        for z in $offen
            echo "           $z"
        end
        echo "         Committen und pushen, oder verwerfen: git -C $MASCHERA checkout -- ."
        return 1
    end
    set -l vorher (git -C $MASCHERA rev-parse --short HEAD)
    # Ohne Pipe: `git … | string collect` meldete den Status von `string
    # collect`, und ein gescheitertes Pull blieb unbemerkt (so bis 19.10.2026
    # in tools/start.fish).
    if not git -C $MASCHERA pull -q --ff-only
        schlecht "git pull fehlgeschlagen, siehe oben"
        return 1
    end
    set -l nachher (git -C $MASCHERA rev-parse --short HEAD)
    if test "$vorher" = "$nachher"
        gut "Code war schon aktuell ($nachher)"
    else
        gut "Code $vorher -> $nachher"
    end
    echo "         "(git -C $MASCHERA log --oneline -1)
    fish $MASCHERA/tools/github_ordner.fish holen
end

function maschera_aussen -a richtung
    test -f $MASCHERA/tools/sync.fish; or return 0
    fish $MASCHERA/tools/sync.fish $richtung --jetzt 2>&1 \
        | string match -v -r '^\s*$' \
        | string match -v -r 'sent .* received' \
        | string match -v -r 'total size is' \
        | while read -l z
            echo "         $z"
        end
end

function maschera_pruefen
    test -d $MASCHERA; or return 0
    # Die internen Dokumente: nicht in Git, reisen per rsync mit.
    set -l intern
    test -f $MASCHERA/tools/intern.txt
    and set intern (string trim <$MASCHERA/tools/intern.txt | string match -v -r '^(#|$)')
    if test (count $intern) -eq 0
        schlecht "tools/intern.txt fehlt oder ist leer, die internen Dokumente bleiben ungeprueft"
    else
        set -l fehlen 0
        for datei in $intern
            if not test -f $MASCHERA/$datei
                warnung "$datei fehlt"
                set fehlen (math $fehlen + 1)
            end
        end
        test $fehlen -eq 0; and gut (count $intern)" interne Dokumente da"
    end

    if test -z "$PY"; or not test -x "$PY"
        schlecht "keine Python-Umgebung (erwartet ~/.venvs/sempre/bin/python oder MASCHERA_PY)"
        return
    end
    gut (basename $PY)" "($PY --version | string split ' ')[2]
    for paket in flask yaml pymupdf fontTools olefile
        if not $PY -c "import $paket" 2>/dev/null
            switch $paket
                case flask
                    schlecht "Flask fehlt, der Server laeuft nicht: $PY -m pip install flask"
                case pymupdf
                    warnung "pymupdf fehlt, PDF wird nicht gelesen: $PY -m pip install pymupdf"
                case olefile
                    warnung "olefile fehlt, .msg wird nicht gelesen: $PY -m pip install olefile"
                case fontTools
                    warnung "fontTools fehlt: $PY -m pip install fonttools brotli"
                case '*'
                    schlecht "$paket fehlt"
            end
        end
    end
    type -q node; or warnung "node fehlt, die Oberflaechenpruefung wird uebersprungen (paru -S --needed nodejs)"

    # Eine Datei, ein Verwalter: nichts darf in Git UND in .gitignore stehen.
    set -l doppelt
    for f in (git -C $MASCHERA ls-files)
        git -C $MASCHERA check-ignore --no-index -q $f; and set -a doppelt $f
    end
    if test (count $doppelt) -gt 0
        schlecht "in Git UND in .gitignore: $doppelt (git -C $MASCHERA rm --cached <datei>)"
    end

    $PY $MASCHERA/tools/run_tests.py | tail -4 | while read -l z
        echo "         $z"
    end
    test $pipestatus[1] -eq 0; or schlecht "MASCHERA-Pruefungen fehlgeschlagen"
end

# --- MASCHERA: gehen -------------------------------------------------------

function maschera_sichern
    if not test -d $MASCHERA/.git
        warnung "kein MASCHERA-Checkout unter $MASCHERA"
        return 0
    end
    set -l offen (git -C $MASCHERA status --porcelain)
    set -l vorne (git -C $MASCHERA rev-list --count '@{upstream}..HEAD' 2>/dev/null)
    test -z "$vorne"; and set vorne 0

    # Gegenprobe vor dem Sichern. Scheitert sie, wird NICHT committet; die
    # Daten reisen trotzdem (rsync nimmt keine verfolgten Dateien).
    if test -x "$PY"
        $PY $MASCHERA/tools/run_tests.py | tail -4 | while read -l z
            echo "         $z"
        end
        if test $pipestatus[1] -ne 0
            schlecht "MASCHERA-Pruefungen fehlgeschlagen, nichts committet oder gepusht"
            return 1
        end
    else
        warnung "keine Python-Umgebung, ungeprueft"
    end

    if test -n "$offen"
        echo "   Geaendert:"
        for z in $offen
            echo "           $z"
        end
        if isatty stdin
            read -P "   Commitnachricht (leer = nicht committen) > " -l nachricht
            if test -n "$nachricht"
                git -C $MASCHERA add -A
                git -C $MASCHERA commit -q -m "$nachricht"
                and set vorne (math $vorne + 1)
            else
                warnung "nicht committet, die Aenderungen bleiben auf dieser Maschine"
            end
        else
            warnung "kein Terminal fuer die Commitnachricht, nicht committet"
        end
    end
    if test $vorne -gt 0
        if git -C $MASCHERA push -q
            gut "gepusht"
        else
            schlecht "push fehlgeschlagen"
        end
    else
        gut "Code: nichts zu pushen"
    end
end

# --- Phasen ---------------------------------------------------------------

switch "$argv[1]"
    case vor-start
        kopf "MASCHERA: Code holen"
        maschera_code_holen
    case nach-start
        kopf "MASCHERA: Daten ausserhalb von ~/projekte holen"
        maschera_aussen runter
        kopf "MASCHERA: Umgebung und Pruefungen"
        maschera_pruefen
    case vor-ende
        kopf "MASCHERA: pruefen, committen, pushen"
        maschera_sichern
        kopf "MASCHERA: Daten ausserhalb von ~/projekte hochschieben"
        maschera_aussen hoch
    case nach-ende
        if test -f $MASCHERA/tools/sync.fish
            fish $MASCHERA/tools/sync.fish uebergabe 2>&1 | tail -12 | while read -l z
                echo "         $z"
            end
            test $pipestatus[1] -eq 0; or set FEHLER (math $FEHLER + 1)
        end
    case '*'
        echo "Aufruf: fish tools/abgleich-schritte.fish vor-start|nach-start|vor-ende|nach-ende"
        exit 2
end
exit (math "min($FEHLER, 99)")
