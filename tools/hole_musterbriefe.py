#!/usr/bin/env python3
"""Musterbriefe des EDÖB holen und in Text umwandeln.

    python3 tools/hole_musterbriefe.py --liste
    python3 tools/hole_musterbriefe.py --holen

Legt `.txt`-Dateien im Goldordner unter `ch/markup/` ab (siehe
`core/pfade.py`: `MASCHERA_GOLD`, sonst der Datenordner), bereit fuer

    python3 tools/gold_from_markup.py --vormarkieren <datei> --model runs/ch-v63b \\
        --out $MASCHERA_GOLD/ch/markup/<name>.markiert.txt

`--liste` zeigt den tatsaechlich aufgeloesten Ort.

WARUM DIESES SKRIPT UND KEIN FERTIGES PAKET
===========================================

Die Dokumente werden HIER heruntergeladen, auf deiner Maschine, aus der
Quelle. Zwei Gruende, und beide sind wichtiger als die Bequemlichkeit:

1. **Ein Golddokument darf nicht von einem Sprachmodell stammen.** Der Zweck
   des Testsets ist zu messen, wie das Modell mit Text umgeht, den es nicht
   kennt. Die Vorlagenbank ist LLM-erzeugt (Gemma 4 31B, kuratiert von
   Claude). Waeren die Golddokumente es auch, pruefte man das Modell an dem,
   woraus es gelernt hat — die Zahlen saehen gut aus und bedeuteten nichts.
   Dieselbe Falle wie: eine Quelle speist die Vorlagenbank ODER das Testset,
   nie beides.

2. **Die Seiten tragen `©EDÖB-PFPDT`.** Ob Musterbriefe einer Bundesbehoerde
   unter URG Art. 5 fallen (amtliche Erlasse, Entscheidungen, Protokolle,
   Berichte), ist nicht offensichtlich — ein Musterbrief ist keines davon.
   Herunterladen und intern verwenden ist unproblematisch; sie in einem
   Paket weiterzugeben waere eine andere Frage.

QUELLEN
=======
DE  https://www.edoeb.admin.ch/de/musterbriefe-datenschutz
IT  https://www.edoeb.admin.ch/it/modelli-lettere
FR/EN: dieselben Seiten, Sprache oben rechts umschalten. Die Dateinamen
    unterscheiden sich je Sprache, die DAM-Kennung ist dieselbe — sollte
    ein Abruf scheitern, die URL von der Seite kopieren und unten eintragen.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from core import pfade  # noqa: E402

# Der Ort kommt aus `core/pfade.py` — kein Werkzeug baut den Goldpfad selbst.
# Die Quellen sind EDÖB-Musterbriefe, also fest `ch`. Gebraucht wird der
# SCHREIBORT, auch fuer die Anzeige in `--liste`: «vorhanden» soll dasselbe
# Verzeichnis meinen, in das gleich geschrieben wird.


def _ziel() -> Path:
    """Zur Aufrufzeit aufgeloest, nicht beim Import — sonst gaebe es
    `MASCHERA_GOLD` nur fuer den, der es vor dem Start gesetzt hat."""
    return pfade.gold_schreiben("ch", "markup")

# name | sprache | url
# Aendert sich eine URL, meldet `--holen` das mit Klartext statt es
# stillschweigend zu ueberspringen.
QUELLEN = [
    ("edoeb-auskunftsbegehren", "de",
     "https://www.edoeb.admin.ch/dam/de/sd-web/PD3Xh9MjbyH6/"
     "Musterbrief_Auskunftsrecht_DE.docx"),
    ("edoeb-berichtigung-bund", "de",
     "https://www.edoeb.admin.ch/dam/de/sd-web/lBuCMSQ4Y34y/"
     "DS_Musterbrief_Berichtigung_Bund.docx"),
    ("edoeb-berichtigung-private", "de",
     "https://www.edoeb.admin.ch/dam/de/sd-web/LGACmwRPzE-2/"
     "DS_Musterbrief_Berichtigung_Private.docx"),
    ("edoeb-loeschung-bund", "de",
     "https://www.edoeb.admin.ch/dam/de/sd-web/6MJ5yuLzdzpJ/"
     "DS_Musterbrief_L%C3%B6schbegehren_Bund.docx"),
    ("edoeb-loeschung-private", "de",
     "https://www.edoeb.admin.ch/dam/de/sd-web/c5AniFpFjW3I/"
     "DS_Musterbrief_L%C3%B6schbegehren_Private.docx"),
    ("edoeb-diritto-accesso", "it",
     "https://www.edoeb.admin.ch/dam/it/sd-web/PD3Xh9MjbyH6/"
     "Musterbrief_Auskunftsrecht_IT.docx"),
    ("edoeb-cancellazione-organo", "it",
     "https://www.edoeb.admin.ch/dam/it/sd-web/6MJ5yuLzdzpJ/"
     "DS_Musterbrief_IT_cancellazione_organo%20federale.docx"),
    ("edoeb-cancellazione-privati", "it",
     "https://www.edoeb.admin.ch/dam/it/sd-web/c5AniFpFjW3I/"
     "DS_Musterbrief_IT_cancellazione_privati.docx"),
    ("edoeb-correzione-organo", "it",
     "https://www.edoeb.admin.ch/dam/it/sd-web/lBuCMSQ4Y34y/"
     "DS_Musterbrief_IT_correzione_organo%20federale.docx"),
    ("edoeb-correzione-privata", "it",
     "https://www.edoeb.admin.ch/dam/it/sd-web/LGACmwRPzE-2/"
     "DS_Musterbrief_IT_correzione_persona%20privata.docx"),
    # FR, von https://www.edoeb.admin.ch/fr/lettres-types
    ("edoeb-droit-acces", "fr",
     "https://www.edoeb.admin.ch/dam/fr/sd-web/PD3Xh9MjbyH6/"
     "Musterbrief_Auskunftsrecht_FR.docx"),
    ("edoeb-rectification-organe", "fr",
     "https://www.edoeb.admin.ch/dam/fr/sd-web/lBuCMSQ4Y34y/"
     "DS_Musterbrief_Rectification_FR_organe_f%C3%A9d%C3%A9ral.docx"),
    ("edoeb-rectification-privee", "fr",
     "https://www.edoeb.admin.ch/dam/fr/sd-web/LGACmwRPzE-2/"
     "DS_Musterbrief_Rectification_FR_personne_priv%C3%A9e.docx"),
    ("edoeb-suppression-organe", "fr",
     "https://www.edoeb.admin.ch/dam/fr/sd-web/6MJ5yuLzdzpJ/"
     "DS_Musterbrief_suppression_FR_organe_f%C3%A9d%C3%A9ral.docx"),
    ("edoeb-suppression-privee", "fr",
     "https://www.edoeb.admin.ch/dam/fr/sd-web/c5AniFpFjW3I/"
     "DS_Musterbrief_suppression_FR_personne_priv%C3%A9e(r%C3%A9vision_TRS).docx"),
]

# Die DAM-Kennung ist SPRACHUEBERGREIFEND dieselbe, nur der Dateiname
# unterscheidet sich:
#   PD3Xh9MjbyH6  Auskunftsrecht / droit d'accès / diritto d'accesso
#   lBuCMSQ4Y34y  Berichtigung Bund / rectification organe / correzione organo
#   LGACmwRPzE-2  Berichtigung Private / rectification privée / correzione privata
#   6MJ5yuLzdzpJ  Löschung Bund / suppression organe / cancellazione organo
#   c5AniFpFjW3I  Löschung Private / suppression privée / cancellazione privati
#
# Englische Musterbriefe gibt es dort nicht.


def docx_zu_text(rohdaten: bytes) -> str:
    r"""Fliesstext aus einer .docx ziehen, ohne python-docx.

    Eine .docx ist ein ZIP mit `word/document.xml`. Absaetze sind <w:p>,
    Textstuecke <w:t>, Tabulatoren <w:tab/>, Umbrueche <w:br/>.

    `<w:t[^>]*>` funktioniert NICHT: `<w:tab w:val="left" w:pos="1400"/>`
    faengt mit `<w:t` an, und `[^>]*>` schluckt den Rest. Damit gaelte jedes
    `<w:tab/>` als oeffnendes Text-Tag, und `(.*?)</w:t>` naehme alles bis zum
    naechsten echten Textende mit.

    Deshalb `<w:t(?:\s[^>]*)?>`: nach `w:t` muss ein Leerzeichen oder das
    schliessende `>` folgen. Ein Praefix ist keine Uebereinstimmung.
    """
    with zipfile.ZipFile(BytesIO(rohdaten)) as z:
        xml = z.read("word/document.xml").decode("utf-8")

    # Marken IN DER REIHENFOLGE ihres Auftretens einsammeln: Text, Tabulator,
    # Umbruch. Ohne die Reihenfolge steht der Feldname neben statt vor der
    # Punktlinie, und die Formularstruktur geht verloren.
    marke = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:tab/>|<w:br/>", re.S)

    def entschluesseln(t: str) -> str:
        for roh, klar in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                          ("&apos;", "'"), ("&amp;", "&")):
            t = t.replace(roh, klar)
        return t

    absaetze = []
    for p in re.findall(r"<w:p(?:\s[^>]*)?>.*?</w:p>|<w:p/>", xml, re.S):
        teile = []
        for m in marke.finditer(p):
            if m.group(0) == "<w:tab/>":
                teile.append("\t")
            elif m.group(0) == "<w:br/>":
                teile.append("\n")
            else:
                teile.append(entschluesseln(m.group(1)))
        absaetze.append("".join(teile).rstrip())

    text = "\n".join(absaetze)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip() + "\n"

    # Letzte Wache: bleibt XML uebrig, ist die Umwandlung falsch — dann
    # lieber abbrechen als eine unbrauchbare Datei schreiben.
    if re.search(r"<w:[a-zA-Z]", text):
        rest = re.search(r"<w:[a-zA-Z][^>]{0,60}", text).group(0)
        raise ValueError(f"XML im Ergebnis, Umwandlung fehlerhaft: {rest!r}")
    return text


def befehl_liste() -> int:
    ziel_ordner = _ziel()
    print(f"{len(QUELLEN)} Quellen, Ziel: {ziel_ordner}\n")
    for name, lang, url in QUELLEN:
        vorhanden = ("vorhanden"
                     if (ziel_ordner / f"{name}.txt").is_file() else "—")
        print(f"  [{lang}] {name:32} {vorhanden}")
    print("\nSeiten zum Nachschauen (FR und EN dort umschalten):")
    print("  https://www.edoeb.admin.ch/de/musterbriefe-datenschutz")
    print("  https://www.edoeb.admin.ch/it/modelli-lettere")
    return 0


def befehl_holen(nur: str | None) -> int:
    ziel_ordner = _ziel()
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    fehler = 0
    for name, lang, url in QUELLEN:
        if nur and nur != lang:
            continue
        ziel = ziel_ordner / f"{name}.txt"
        try:
            # Ohne Kopfzeilen antwortet admin.ch mit "Connection reset by peer" — die
            # Schutzschicht vor der Seite weist `Python-urllib/3.x` ab. Deshalb ein
            # gewoehnlicher Browser-Kopf. Das ist keine Umgehung einer
            # Zugangsbeschraenkung: die Dateien sind oeffentlich verlinkt und werden
            # jedem ausgeliefert, der sie im Browser anklickt.
            anfrage = urllib.request.Request(url, headers={
                "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/126.0 Safari/537.36"),
                "Accept": "*/*",
                "Accept-Language": "de-CH,de;q=0.9",
            })
            with urllib.request.urlopen(anfrage, timeout=30) as r:
                roh = r.read()
            text = docx_zu_text(roh)
        except Exception as e:  # noqa: BLE001
            print(f"  FEHL [{lang}] {name}: {e}")
            print(f"       {url}")
            fehler += 1
            continue
        ziel.write_text(text, encoding="utf-8")
        print(f"  ok   [{lang}] {name:32} {len(text):5} Zeichen -> {ziel.name}")

    print()
    if fehler:
        print(f"{fehler} Abrufe fehlgeschlagen.")
        print()
        print("  'Connection reset by peer' bei ALLEN -> nicht die URLs,")
        print("  sondern die Verbindung. Zuerst pruefen, ob admin.ch")
        print("  ueberhaupt erreichbar ist:")
        print("    curl -sSI https://www.edoeb.admin.ch/de/musterbriefe-datenschutz | head -1")
        print()
        print("  Einzelne Fehlschlaege, 404 oder HTTPError -> die Datei wurde")
        print("  neu veroeffentlicht. URL von der EDÖB-Seite kopieren und in")
        print("  QUELLEN eintragen.")
    ordner = _ziel()
    print("Naechster Schritt je Datei:")
    print("  python3 tools/gold_from_markup.py --vormarkieren \\")
    print(f"      {ordner}/<name>.txt --model runs/ch-v63b \\")
    print(f"      --out {ordner}/<name>.markiert.txt")
    print()
    print("Dann im Editor: Markierungen pruefen UND die Platzhalter durch")
    print("erfundene Werte ersetzen. Ein Musterbrief hat Felder wie")
    print("«Vorname Name» oder «[Adresse]» — dort gehoeren erfundene, aber")
    print("plausible Schweizer Werte hinein, sonst misst das Testset an")
    print("einem Text, den so niemand schreibt.")
    return 1 if fehler else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--liste", action="store_true", help="nur anzeigen")
    ap.add_argument("--holen", action="store_true", help="herunterladen")
    ap.add_argument("--lang", default=None, choices=["de", "fr", "it", "en"],
                    help="nur eine Sprache")
    a = ap.parse_args()
    if a.holen:
        return befehl_holen(a.lang)
    return befehl_liste()


if __name__ == "__main__":
    sys.exit(main())
