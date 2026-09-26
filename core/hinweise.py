"""Hinweise mit Schluessel statt fertigem Satz.

Die Oberflaeche spricht vier Sprachen, der Server einen Satz. Ein Hinweis
ist Beschriftung, und Beschriftung gehoert an EINEN Ort: `TEXTE` in
`maschera.js`. Deshalb traegt ein Hinweis drei Felder:

    schluessel  der Name in `TEXTE[sprache].hinweise`
    werte       die Zahlen und Namen, die eingesetzt werden
    text        die deutsche Fassung

`text` ist nicht ueberfluessig: die Kommandozeile (`filter_document.py`)
hat keine Uebersetzungstabelle, und ein Klient, der einen Schluessel nicht
kennt, soll etwas Lesbares zeigen. Wer einen Hinweis hinzufuegt, schreibt
beides — den Satz hier und die vier Fassungen in `maschera.js`.
`tests/test_api.py` Punkt 18 prueft, dass kein Schluessel in der
Oberflaeche fehlt.
"""


def hinweis(schluessel: str, text: str, **werte) -> dict:
    """Ein Hinweis. `text` ist die deutsche Fassung, `werte` das Einsetzbare."""
    return {"schluessel": schluessel, "werte": werte, "text": text}


# ---------------------------------------------------------------------------
# Meldungen — dieselbe Bauart wie ein Hinweis, fuer Fehler und Warnungen
# ---------------------------------------------------------------------------
#
# Fehler und Warnungen laufen durch dasselbe Rohr in dieselbe Zeile der
# Oberflaeche wie die Hinweise. Also tragen auch sie einen Schluessel statt
# eines fertigen deutschen Satzes.


class Abgelehnt(ValueError):
    """Eine Eingabe, die so nicht gespeichert werden darf.

    Die gemeinsame Basis fuer `vorlieben`, `vorlagen` und `einstellungen`.
    Sie erben von hier und behalten ihren eigenen Namen, damit ein `except
    vorlagen.Abgelehnt` weiterhin nur Vorlagen faengt.

    `text` ist die deutsche Fassung und bleibt die Nachricht der Ausnahme.
    `schluessel` und `werte` stehen daneben, fuer den, der uebersetzen kann.
    """

    def __init__(self, text: str, schluessel: str | None = None, **werte):
        super().__init__(text)
        self.schluessel = schluessel
        self.werte = werte


class Abbruch(SystemExit):
    """Ein Abbruch mit Begruendung — fuer die Kommandozeile und die Oberflaeche.

    Erbt von `SystemExit`, weil `user_rules` und `tools/dokumente.py` so
    abbrechen, seit es sie gibt: auf der Kommandozeile endet das Programm
    mit dem deutschen Satz, und jeder bestehende `except SystemExit` faengt
    weiter. Neu sind `schluessel` und `werte` daneben.

    ⚠️ Der Satz selbst geht NICHT in die Oberflaeche. Bis 0.9.61 setzte der
    Server `str(e)` als `{grund}` in einen uebersetzten Satz — die
    italienische Oberflaeche zeigte dann «Regole rifiutate: Regel 'x':
    zu kurze Eintraege …». Uebersetzbar ist nur, was einen Schluessel hat.
    """

    def __init__(self, text: str, schluessel: str, **werte):
        super().__init__(text)
        self.schluessel = schluessel
        self.werte = werte
