"""Nichts Persoenliches, nichts Hausinternes im oeffentlichen Repository.

    python3 tests/test_veroeffentlichung.py

MASCHERA soll fuer alle da sein. Im Repository darf deshalb nichts stehen,
was auf eine bestimmte Stelle, einen bestimmten Rechner oder eine
bestimmte Person zeigt. Eine einmalige Bereinigung reicht dafuer nicht —
was heute entfernt wird, kommt ueber einen Kommentar oder ein Beispiel
zurueck. Deshalb eine Wache.

ZWEI SCHICHTEN
==============

  allgemein   gilt fuer jeden Baum: keine Heimatpfade, keine Adressen im
              Heimnetz, keine Metadaten in Bueroakten, kein Hochladeweg,
              die Zahlen im README mit einem Verwalter.

  intern      liegt `VERBOTEN_INTERN.txt` im Projektstamm, kommen deren
              Muster dazu — Benutzer-, Rechner- und Personennamen der
              Arbeitsumgebung —, und die Pruefungen der internen Dokumente
              und der Fernkopien laufen mit. Die Datei selbst ist intern:
              eine Wache, die im oeffentlichen Paket die Namen traegt, die
              sie schuetzen soll, veroeffentlicht sie.

WAS BLEIBEN DARF
================

Die Grenze verlaeuft zwischen «woher stammen die Daten» und «was weiss man
aus der eigenen Arbeit». Offene Standards und Datenquellen mit Nummer —
`eCH-0135`, BFS, swisstopo — bleiben; sie zu entfernen waere
Verschleierung, nicht Bereinigung. Interne Formate, Abteilungskuerzel,
Rechner-, Benutzer- und Systemnamen gehen.
"""
import re
import subprocess
import sys
import zipfile
from fnmatch import fnmatch
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# Dateien, die nie veroeffentlicht werden. Die Liste steht in
# `tools/intern.txt`; in der Arbeitsumgebung bricht eine fehlende oder
# leere Liste ab — waere INTERN still leer, meldete Punkt 1 OK, ohne ein
# einziges Dokument geprueft zu haben.
#
# Die interne Schicht. Fehlt `VERBOTEN_INTERN.txt`, ist das kein Fehler,
# sondern das oeffentliche Paket — und das wird GESAGT, nicht verschwiegen.
INTERNE_LISTE = WURZEL / "VERBOTEN_INTERN.txt"
ARBEITSUMGEBUNG = INTERNE_LISTE.is_file()


def _interne_liste() -> tuple[list, dict]:
    muster, ausnahmen = [], {}
    if not ARBEITSUMGEBUNG:
        return muster, ausnahmen
    for zeile in INTERNE_LISTE.read_text(encoding="utf-8").splitlines():
        if not zeile.strip() or zeile.lstrip().startswith("#"):
            continue
        teile = zeile.split("\t")
        if teile[0] == "muster" and len(teile) == 3:
            muster.append((teile[1], teile[2]))
        elif teile[0] == "ausnahme" and len(teile) == 4:
            ausnahmen[(teile[1], teile[2])] = teile[3]
        else:
            raise SystemExit(f"ABBRUCH — unlesbare Zeile in {INTERNE_LISTE}: "
                             f"{zeile!r}")
    if not muster:
        raise SystemExit(f"ABBRUCH — {INTERNE_LISTE} traegt kein Muster. "
                         "Ein leerer Befund ist keine Entwarnung.")
    return muster, ausnahmen


def _intern_lesen() -> set[str]:
    if not ARBEITSUMGEBUNG:
        return set()
    quelle = WURZEL / "tools" / "intern.txt"
    if not quelle.is_file():
        raise SystemExit(f"ABBRUCH — {quelle} fehlt. Ohne die Liste weiss "
                         "diese Wache nicht, was intern ist.")
    namen = {z.strip() for z in quelle.read_text(encoding="utf-8").splitlines()
             if z.strip() and not z.lstrip().startswith("#")}
    if not namen:
        raise SystemExit(f"ABBRUCH — {quelle} ist leer. Ein leerer Befund "
                         "ist keine Entwarnung.")
    return namen


INTERN = _intern_lesen()

# Verzeichnisse ohne Quelltext.
UEBERSPRINGEN = {".git", "__pycache__", "dist", "raw", "runs", "release",
                 "node_modules"}

# ⚠️ Pfade, die diese Wache NICHT LESEN DARF — nicht «kein Quelltext»,
# sondern moegliche Personendaten. Deshalb eine eigene Liste mit eigenem
# Grund.
#
# Gezielt und nicht pauschal `eval`: `packs/*/eval/synthetic/` enthaelt
# erfundene Dokumente und gehoert geprueft wie jede andere Quelle. Gesperrt
# sind nur die Orte, an denen ein eigenes Testset liegen koennte, falls es
# jemand im Projektbaum ablegt statt unter dem Goldpfad (`core/pfade.py`).
# Dass die Verzeichnisse hier leer sind, ist kein Grund, die Sperre zu
# streichen.
#
# `packs/*/…`, nie `packs/ch/…` — die Sperre gilt fuer jedes Pack.
#
# `fnmatch` und nicht `Path.match`: `Path.match` ist rechtsverankert und
# laesst `*` kein `/` ueberqueren — `packs/ch/eval/real/tief/dok.txt` fiele
# durch. `fnmatch` uebersetzt `*` nach `.*` und trifft jede Tiefe.
#
# `tools/oeffentlich_paket.py` fuehrt in `DATEN` eine eigene Liste mit
# eigener Begruendung («Daten, keine Bausteine»). Bewusst NICHT
# zusammengelegt — wer eine aendert, faellt der anderen auf.
#
# Punkt 5 unten prueft, dass dieser Sprung gezielt bleibt.
GESPERRT = (
    "packs/*/eval/real/*",
    "packs/*/eval/markup/*",
)

if not GESPERRT:
    raise SystemExit("ABBRUCH — GESPERRT ist leer. Die Wache wuerde die "
                     "echten Dokumente einlesen und dabei «alles geprueft» "
                     "melden. Ein leerer Befund ist keine Entwarnung.")


# ⚠️⚠️ WAS HINAUSGEHT, WIRD GEPRUEFT — auch unter einer Sperre.
#
# `oeffentlich_paket.py` nimmt aus einem DATEN-Verzeichnis genau zwei
# Dateien mit: `README.md` und `.gitkeep`, sie erklaeren den leeren Ordner.
# Uebersprange `GESPERRT` das ganze Verzeichnis, waeren sie die einzigen
# Dateien, die hinausgehen und die diese Wache nie ansieht.
#
# Die Sperre selbst bleibt: diese Wache soll keine Dokumente EINLESEN.
# `README.md` und `.gitkeep` sind keine Dokumente — sie stehen in git und
# liegen im Paket.
#
# ⚠️ DER NAME KOMMT AUS DEM WERKZEUG, nicht aus einer zweiten Liste hier.
# Wer dort einen dritten Namen eintraegt, prueft ihn hier im selben
# Augenblick mit.
sys.path.insert(0, str(WURZEL / "tools"))
from oeffentlich_paket import DRAUSSEN, ERKLAERER              # noqa: E402


def gesperrt(rel: Path) -> bool:
    """Wahr, wenn der Pfad Golddokumente traegt und nicht gelesen wird."""
    if rel.name in ERKLAERER:
        # Geht ins Paket, also wird es geprueft.
        return False
    s = rel.as_posix()
    return any(fnmatch(s, muster) for muster in GESPERRT)


def uebersprungen(rel: Path) -> bool:
    """Wahr, wenn die Wache diesen Pfad nicht liest — aus welchem Grund auch
    immer.

    ⚠️ Punkt 5 prueft GENAU DIESE Funktion und nicht `gesperrt()` allein:
    wer `"eval"` in UEBERSPRINGEN schreibt, macht `synthetic/` unsichtbar,
    und nur eine Pruefung dieser Funktion schlaegt dann an.
    """
    return bool(set(rel.parts) & UEBERSPRINGEN) or gesperrt(rel)

ENDUNGEN = {".py", ".yaml", ".yml", ".md", ".fish", ".json", ".toml",
            ".html", ".css", ".js", ".sh", ".txt"}

# ⚠️ Dateien OHNE Endung, die trotzdem Text sind und ins Repository
# gehen. `Dockerfile` und `.dockerignore` haben keinen Suffix und koennen
# trotzdem Pfade und Namen tragen. Die Frage lautet nicht «welche Endung
# fehlt», sondern «welche Textdatei im Baum hat gar keine» — siehe auch
# `dateien()` unten.
NAMEN = {"Dockerfile", ".dockerignore", "Caddyfile", "Makefile",
         ".gitignore", ".gitattributes", ".editorconfig"}

# muster | was es findet | warum es nicht ins Repository gehoert
VERBOTEN = [
    (r"/home/[a-z][a-z0-9_-]*/", "absoluter Heimatpfad — bei jedem anderen falsch"),
    (r"\b192\.168\.\d+\.\d+\b", "Adresse im Heimnetz"),
]
_INTERN_MUSTER, _INTERN_AUSNAHMEN = _interne_liste()
VERBOTEN += _INTERN_MUSTER

# Begruendete Ausnahmen: Datei -> Grund, warum sie nicht gelesen wird.
#
# ⚠️ Jede Ausnahme braucht einen Grund, und der Grund steht hier. Ein Muster
# zu streichen, weil es einmal falsch anschlaegt, macht die Wache stumm.
AUSNAHMEN: dict[str, str] = {
    # Leer, und das ist Absicht: auch diese Datei wird geprueft. Die
    # persoenlichen Muster stehen in `VERBOTEN_INTERN.txt`, nicht hier.
}

# ⚠️ Dateien, die im ARBEITSVERZEICHNIS Rechner- und Benutzernamen tragen
# duerfen, weil `oeffentlich_paket.py` sie zurueckhaelt. Im PAKET sind sie
# nicht mehr da — laeuft die Wache dort, ist die Liste leer und jeder
# Treffer echt.
NUR_INTERN = {
    "tools/sync.fish": "haelt oeffentlich_paket.py zurueck",
    "tools/start.fish": "dito",
    "tools/feierabend.fish": "dito",
    "tools/github_ordner.fish": "dito",
}

# Einzelne Zeilen, die einen Treffer enthalten duerfen.
ZEILEN_AUSNAHMEN = {
    # Ein erfundener Pfad als Beispiel im Kommentar, nicht der echte.
    ("packs/ch/patterns.yaml", "/home/ist/"): "erfundenes Beispiel im Kommentar",
    ("packs/ch/taxonomy.yaml", "/home/mmueller/"): "erfundenes Beispiel im Kommentar",
    # Eine private IP MUSS als Testfall dastehen — IPADDRESS soll sie
    # erkennen. Sie zeigt auf kein reales Geraet.
    ("tests/test_patterns.py", "192.168.1.186"): "Testfall fuer IPADDRESS",
    # ⚠️ `/home/maschera/` ist der Heimatpfad IM CONTAINER, nicht auf einer
    # Maschine des Entwicklers. Der Benutzer heisst wie das Werkzeug, wird
    # im `Dockerfile` selbst angelegt und existiert nirgendwo sonst. Bei
    # jedem anderen ist er also gerade NICHT falsch — er ist ueberall
    # gleich, und das ist der Zweck.
    #
    # Ausgenommen, nicht durch Schwaechen des Musters: `/home/[a-z]+/`
    # soll weiter jeden echten Heimatpfad fangen.
    ("tools/paket/compose.yaml", "/home/maschera/"): "Pfad im Container",
    ("tools/paket/compose.traefik.yaml", "/home/maschera/"): "Pfad im Container",
    ("tools/paket/AppRun", "/home/maschera/"): "Pfad im Container",
    ("tools/paket/Dockerfile", "/home/maschera/"): "Pfad im Container",
    ("tools/paket/LIESMICH.md", "/home/maschera/"): "Pfad im Container",
    # Der Docker-Abschnitt nennt das Volumen fuer die Einstellungen —
    # derselbe Pfad im Container, seit 1.0.0 auch fuer Besucher.
    ("README.md", "/home/maschera/"): "Pfad im Container",
    ("README.de.md", "/home/maschera/"): "Pfad im Container",
    # Diese Datei nennt die Ausnahmen oben woertlich — sonst koennte sie
    # sie nicht ausnehmen.
    ("tests/test_veroeffentlichung.py", "/home/ist/"): "Ausnahmetabelle",
    ("tests/test_veroeffentlichung.py", "/home/mmueller/"): "Ausnahmetabelle",
    ("tests/test_veroeffentlichung.py", "/home/maschera/"): "Ausnahmetabelle",
    ("tests/test_veroeffentlichung.py", "192.168.1.186"): "Ausnahmetabelle",
}

ZEILEN_AUSNAHMEN.update(_INTERN_AUSNAHMEN)

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def dateien():
    for p in sorted(WURZEL.rglob("*")):
        if not p.is_file():
            continue
        # ⚠️ EIGENSCHAFT STATT LISTE. `ENDUNGEN` und `NAMEN` koennen zu kurz
        # sein — `LICENSE`, `AUTHORS`, `NOTICE` haben keine Endung. Deshalb: was
        # KEINE Endung hat und sich als Text lesen laesst, wird geprueft. Die zwei
        # Listen bleiben als Absicht stehen — sie sagen, was AUSSERDEM gemeint
        # ist.
        if p.suffix not in ENDUNGEN and p.name not in NAMEN:
            if p.suffix:
                continue
            try:
                roh = p.read_bytes()
            except OSError:
                continue
            # Binaeres hat NUL-Bytes; Text hat keine. Und mehr als ein
            # Megabyte ist kein Quelltext — das faengt eine versehentlich
            # abgelegte Binaerdatei ohne Endung ab, ohne sie zu lesen.
            if len(roh) > 1_000_000 or b"\x00" in roh:
                continue
            try:
                roh.decode("utf-8")
            except UnicodeDecodeError:
                continue
        rel = p.relative_to(WURZEL)
        if uebersprungen(rel):
            continue
        # ⚠️ Basisname UND relativer Pfad: `tools/intern.txt` fuehrt auch Pfade
        # in Unterverzeichnissen (`.claude/settings.local.json`), und dort greift
        # `p.name` allein nicht.
        if p.name in INTERN or rel.as_posix() in INTERN:
            continue
        yield p


print("1. Interne Dokumente sind von der Veroeffentlichung ausgenommen")

# ⚠️ GIT WIRD GEFRAGT, NICHT DER TEXT DER `.gitignore`. Eine Suche im
# Dateitext traefe auch Kommentare — ein Name, der nur in einer
# Begruendung steht, sieht dann aus wie eine Regel.
#
# `git check-ignore` beantwortet die richtige Frage: greift eine Regel,
# und welche. Es findet `.claude/` fuer `.claude/settings.local.json`,
# ohne dass dafuer eine zweite Zeile in die `.gitignore` muss.
#
# ⚠️ ES IST DIE ANDERE FRAGE ALS `git ls-files` DARUNTER, und beide
# werden gebraucht:
#
#     check-ignore   sie wird auch nicht VERSEHENTLICH verfolgt
#     ls-files       sie ist JETZT nicht verfolgt
#
# Die zweite kann die erste nicht ersetzen: eine Datei, die niemand
# angefasst hat, ist unverfolgt und trotzdem ungeschuetzt.
#
# Ohne interne Liste — im oeffentlichen Paket — gibt es nichts zu fragen.
# Dann entfaellt der Punkt und sagt es; ein `git ls-files` ohne Pfade
# liefe sonst ueber den ganzen Baum.
if not INTERN:
    print("   HINWEIS keine interne Liste — nichts, was intern bleiben "
          "muesste")
else:
    ignoriert = subprocess.run(
        ["git", "-C", str(WURZEL), "check-ignore", "-v", "--"] + sorted(INTERN),
        capture_output=True, text=True)
    # Rueckgabewert 0 = alle getroffen, 1 = mindestens eine nicht, 128 = kein
    # Git-Baum. Nur der letzte Fall ist eine andere Lage und keine Meldung.
    if ignoriert.returncode not in (0, 1):
        print("   HINWEIS kein Git-Baum — die Ignorierpruefung entfaellt")
    else:
        # `-v` schreibt je Treffer «datei:zeile:muster<TAB>pfad».
        getroffen = {z.rsplit("\t", 1)[-1]
                     for z in ignoriert.stdout.splitlines() if z.strip()}
        for name in sorted(INTERN):
            check(name in getroffen,
                  f"git ignoriert {name} NICHT — der Name mag im Text der "
                  f".gitignore stehen, aber keine REGEL trifft ihn. Ein "
                  f"Kommentar ist keine Regel")

    # ⚠️ Der Eintrag in `.gitignore` ist eine ZUSAGE, keine Eigenschaft. Git
    # ignoriert die Datei nur, solange sie unverfolgt ist — eine bereits
    # verfolgte Datei bleibt verfolgt, gleich was dort steht. Deshalb hier
    # `git ls-files`: gefragt wird, was git TATSAECHLICH fuehrt.
    verfolgt = subprocess.run(
        ["git", "-C", str(WURZEL), "ls-files", "--"] + sorted(INTERN),
        capture_output=True, text=True)
    if verfolgt.returncode != 0:
        # Kein Git-Baum (ausgepacktes Paket): dann gibt es nichts zu verfolgen.
        # Ein leerer Befund ist hier keine Entwarnung, sondern eine andere Lage —
        # und sie wird GENANNT, nicht verschwiegen.
        print("   HINWEIS kein Git-Baum — die Verfolgungspruefung entfaellt")
    else:
        drin = sorted(z for z in verfolgt.stdout.splitlines() if z.strip())
        check(not drin,
              f"von git VERFOLGT, obwohl intern: {', '.join(drin)} — "
              f"`git rm --cached` fehlt. Der Eintrag in .gitignore allein "
              f"nimmt eine bereits verfolgte Datei nicht heraus")
    # ⚠️ NUR wenn nichts angeschlagen hat — sonst stuende das OK unter dem FEHL.
    if not failures:
        print(f"   OK   {', '.join(sorted(INTERN))} bleiben intern")

print("\n2. Kein Rechnername, kein Heimatpfad, kein Personenname")
geprueft = 0
for pfad in dateien():
    geprueft += 1
    text = pfad.read_text(encoding="utf-8", errors="replace")
    rel = pfad.relative_to(WURZEL)
    if str(rel) in NUR_INTERN:
        continue
    if str(rel) in AUSNAHMEN:
        continue
    for muster, grund in VERBOTEN:
        # `IGNORECASE`: Namen stehen in Fliesstext auch gross geschrieben.
        # Eine Wache, die nur die kleingeschriebene Haelfte findet, meldet
        # Sauberkeit und meint Zufall.
        for m in re.finditer(muster, text, re.IGNORECASE):
            if (str(rel), m.group(0)) in ZEILEN_AUSNAHMEN:
                continue
            zeile = text[:m.start()].count("\n") + 1
            check(False, f"{rel}:{zeile}  {m.group(0)!r} — {grund}")
print(f"   OK   {geprueft} Dateien geprueft, {len(VERBOTEN)} Muster, "
      f"{len(AUSNAHMEN)} Datei-, {len(NUR_INTERN)} interne und "
      f"{len(ZEILEN_AUSNAHMEN)} Zeilenausnahmen")

print("\n3. Die Quellenangabe der Nomenklatur bleibt erhalten")
# Gegenprobe: Die Wache darf NICHT so scharf sein, dass sie die
# Datenherkunft mitentfernt. Wer nicht sagt, woher die Heimatortliste
# stammt, verschleiert statt zu bereinigen.
build = (WURZEL / "packs" / "ch" / "nomenclatures" / "build.py")
if build.is_file():
    quelle = build.read_text(encoding="utf-8")
    check("eCH-0135" in quelle,
          "die Quellenangabe der Heimatortliste fehlt — sie MUSS drinstehen")
    print("   OK   eCH-0135 als Quelle genannt")

print("\n4. Buerodateien tragen keine Metadaten")
# ⚠️ Eine `.docx` ist ein ZIP, und die Wache oben liest nur Textendungen —
# eine Binaerdatei geht ungelesen durch. Word legt in `docProps/core.xml` den
# Verfasser und den zuletzt Speichernden ab, in `docProps/app.xml` die Firma.
# Das sind Personendaten, die im sichtbaren Text NICHT vorkommen. Bei einem
# Werkzeug, dessen Zweck Datenschutz ist, waere ein Beispieldokument mit dem
# Benutzernamen des Entwicklers darin die peinlichste Art von Leck.
BUEROENDUNGEN = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
FELDER = ("creator", "lastModifiedBy", "lastPrinted", "Company", "Manager",
          "description", "keywords", "category")

buero = 0
for pfad in sorted(WURZEL.rglob("*")):
    if not pfad.is_file() or pfad.suffix.lower() not in BUEROENDUNGEN:
        continue
    if uebersprungen(pfad.relative_to(WURZEL)):
        continue
    buero += 1
    rel = pfad.relative_to(WURZEL)
    try:
        with zipfile.ZipFile(pfad) as z:
            namen = z.namelist()
            for teil in ("docProps/core.xml", "docProps/app.xml",
                         "meta.xml"):
                if teil not in namen:
                    continue
                roh = z.read(teil).decode("utf-8", errors="replace")
                for feld in FELDER:
                    for m in re.finditer(
                            rf"<[^<>]*\b{feld}\b[^<>]*>([^<]+)<", roh):
                        wert = m.group(1).strip()
                        if wert:
                            check(False,
                                  f"{rel}  {teil} {feld}={wert!r} — "
                                  f"Metadaten im Beispieldokument")
            # Kommentare tragen den Namen dessen, der sie geschrieben hat.
            if "word/comments.xml" in namen:
                check(False, f"{rel}  enthaelt Kommentare mit Verfassernamen")
    except zipfile.BadZipFile:
        check(False, f"{rel}  keine lesbare Buerodatei — altes Binaerformat?")
if not buero:
    print("   OK   keine Buerodateien im Repository")
elif not failures:
    print(f"   OK   {buero} Buerodatei(en) ohne Metadaten")

print("\n5. Der Sprung ueber eval/ ist gezielt, nicht pauschal")
# ⚠️ Diese Pruefung schlaegt in BEIDE Richtungen an: der Sprung darf weder
# zu eng werden (dann liest die Wache echte Dokumente) noch zu weit (dann
# geht Erfundenes ungeprueft ins Paket). Die Erwartungen stehen als
# Literalpfade da und werden NICHT aus GESPERRT abgeleitet — eine Liste
# gegen sich selbst zu pruefen ist zirkulaer.
#
# Es wird keine Datei angelegt: geprueft wird das Praedikat. Eine Probe
# unter `real/` waere selbst der Fehler, den diese Wache verhindern soll.
ERWARTET = (
    ("packs/ch/eval/real/dok.txt", True, "echte Dokumente"),
    ("packs/ch/eval/real/tief/dok.txt", True, "auch tiefer geschachtelt"),
    ("packs/ch/eval/markup/dok.txt", True, "markierte Fassungen"),
    ("packs/it/eval/real/dok.txt", True, "jeder Pack, nicht nur ch"),
    ("packs/ch/eval/synthetic/dok.txt", False, "erfunden — gehoert geprueft"),
    ("packs/ch/eval/hinweis.md", False, "eval/ selbst ist nicht gesperrt"),
    ("core/pfade.py", False, "gewoehnlicher Quelltext"),
    # ⚠️ DIE ZWEI, DIE INS PAKET GEHEN — sie MUESSEN geprueft werden.
    ("packs/ch/eval/real/README.md", False, "geht ins Paket"),
    ("packs/ch/eval/real/.gitkeep", False, "geht ins Paket"),
    ("packs/ch/eval/markup/README.md", False, "geht ins Paket"),
    ("packs/ch/eval/markup/.gitkeep", False, "geht ins Paket"),
    # … und die Dokumente daneben weiterhin NICHT. Beide Richtungen, sonst
    # ist die Ausnahme fuer die zwei Namen ein Weg, die Sperre zu oeffnen.
    ("packs/ch/eval/real/README.md.txt", True, "kein Erklaerer, ein Dokument"),
    ("packs/ch/eval/real/tief/README.md", False, "Erklaerer, auch tiefer"),
)
for pfad_txt, soll, warum in ERWARTET:
    ist = uebersprungen(Path(pfad_txt))
    check(ist == soll,
          f"{pfad_txt} — {'nicht gelesen' if ist else 'geprueft'}, erwartet "
          f"{'nicht gelesen' if soll else 'geprueft'} ({warum})")

# Gegenprobe zu `core/pfade.py`: dort steht dieselbe Tatsache ein zweites
# Mal, aus einem anderen Grund (welche Arten der Goldpfad kennt). Zwei
# Listen, zwei Begruendungen — wer eine aendert, faellt der anderen auf.
# Bewusst KEINE gemeinsame Quelle: schrumpfte `ARTEN`, weitete sich der
# Sprung dieser Wache still auf ein Verzeichnis mit echten Dokumenten aus.
sys.path.insert(0, str(WURZEL))
from core.pfade import ARTEN                                  # noqa: E402
for art in ARTEN:
    check(f"packs/*/eval/{art}/*" in GESPERRT,
          f"core.pfade.ARTEN kennt {art!r}, GESPERRT nicht — eine der "
          "beiden Listen ist gewandert")

# ⚠️ Und die Ausnahme von der Sperre traegt GENAU die Namen, die das
# Paketwerkzeug mitnimmt — sonst entsteht der Spalt von neuem, nur
# andersherum: eine Datei, die die Wache liest und die gar nicht
# hinausgeht, oder eine, die hinausgeht und wieder ungeprueft bleibt.
check(ERKLAERER == ("README.md", ".gitkeep"),
      f"ERKLAERER in oeffentlich_paket.py ist {ERKLAERER} — kommt ein Name "
      f"dazu, gehoert er hier in ERWARTET, sonst ist er wieder ungeprueft")
if not failures:
    print(f"   OK   {len(ERWARTET)} Pfade, GESPERRT deckt "
          f"{', '.join(ARTEN)}")

print("\nX. Wer sich auslaesst, sagt es SO, dass der Laeufer es hoert")
# Ein Selbstauslassen muss der Laeufer hoeren. `run_tests.py` erkennt
# es an der Marke `UEBERSPRUNGEN` am Zeilenanfang. Eine Pruefung, die sich
# bei fehlendem Flask oder pymupdf ganz auslaesst, ohne die Marke zu
# tragen, gilt sonst als BESTANDEN — «eine uebersprungene Pruefung hat
# NICHTS geprueft», und niemand saehe es.
#
# ⚠️ Wer einen ERKENNUNGSWEG aendert, muss alle ERZEUGER aufzaehlen,
# nicht nur die, die er anfasst. Deshalb prueft dieser Punkt jede Datei.
#
# Erkannt wird ein Selbstauslassen daran, dass die Datei danach ENDET.
# Ein Punkt, der bloss einen Teil ueberspringt und weiterlaeuft, darf die
# Marke NICHT tragen — er wuerde die ganze Datei als ausgelassen melden.
_marke = "UEBERSPRUNGEN"
# ⚠️ ZUSAMMENGESETZT, nicht als Literal. Diese Datei durchsucht auch sich
# selbst, und ein `"SystemExit(0)"` im Quelltext waere ein Treffer in der
# Bedingung, die danach sucht.
_ende = "SystemExit" + "(0)"
_ohne_marke = []
# ⚠️ OHNE KOMMENTARZEILEN — sonst schlaegt die Wache an der Begruendung
# an, die erklaert, wonach gesucht wird.
for _p in sorted((WURZEL / "tests").glob("test_*.py")):
    _zeilen = [("" if _z.lstrip().startswith("#") else _z)
               for _z in _p.read_text(encoding="utf-8").splitlines()]
    for _nr, _z in enumerate(_zeilen):
        if _ende not in _z:
            continue
        # Die drei Zeilen davor: steht dort die Marke?
        _davor = "\n".join(_zeilen[max(0, _nr - 3):_nr])
        if _marke not in _davor:
            _ohne_marke.append(f"{_p.name}:{_nr + 1}")
check(not _ohne_marke,
      "diese Stellen beenden die Pruefung, ohne es dem Laeufer zu sagen — "
      f"er zaehlt sie als BESTANDEN: {', '.join(_ohne_marke)}")
if not failures:
    print("   OK   jedes Selbstauslassen traegt die Marke")

print("\nY. Keine Pruefung traegt eine Nummer zweimal")
# Die Punktnummern sind KENNUNGEN: Kommentare quer durch den Baum
# verweisen auf sie («`test_fenster.py` Punkt 12»). Eine doppelt vergebene
# Nummer schickt den Leser an die falsche Stelle, und er merkt es nicht,
# weil dort auch etwas steht. Ebenso ein Verweis auf eine Nummer, die es
# nicht (mehr) gibt.
#
# Deshalb zwei Pruefungen: jede Nummer einmal je Datei, und jeder Verweis
# «`test_x.py` Punkt N» im Baum trifft eine Nummer, die es in der Datei
# gibt. Wer umnummeriert, sieht so jeden Verweis, den er nachziehen muss.
#
# `7b`, `8a` sind KEINE Doppel. Ein Buchstabe dahinter ist eine eigene
# Kennung.
import collections as _coll
_doppelte = {}
for _p in sorted((WURZEL / "tests").glob("test_*.py")):
    _n = _coll.Counter()
    for _z in _p.read_text(encoding="utf-8").splitlines():
        _mm = re.match(r'\s*print\(f?"(?:\\n)?\s*(\d+[a-z]?)\.\s', _z)
        if _mm:
            _n[_mm.group(1)] += 1
    _d = {k: v for k, v in _n.items() if v > 1}
    if _d:
        _doppelte[_p.name] = _d
check(not _doppelte,
      f"doppelt vergebene Punktnummern: {_doppelte} — die Nummer ist eine "
      f"Kennung, auf die Kommentare im Baum verweisen")


def _nummern(datei: Path) -> set[str]:
    """Die Punktnummern, die eine Pruefdatei ausgibt."""
    muster = (r'^\s*print\(f?"(?:\\n)?\s*(\d+[a-z]?)\.\s'
              if datei.suffix == ".py" else
              r'^\s*console\.log\([`"\'](?:\\n)?\s*(\d+[a-z]?)\.\s')
    return set(re.findall(muster, datei.read_text(encoding="utf-8"), re.M))


_VERWEIS = re.compile(r"(test_[a-z_]+\.(?:py|js))`?\s+Punkte?\s+(\d+[a-z]?)\b")
_ins_leere = []
_verweise = 0
for _p in dateien():
    _txt = _p.read_text(encoding="utf-8", errors="replace")
    for _mv in _VERWEIS.finditer(_txt):
        _ziel = WURZEL / "tests" / _mv.group(1)
        if not _ziel.is_file():
            # Eine zurueckgehaltene Pruefdatei: im Paket nicht da.
            continue
        _verweise += 1
        if _mv.group(2) not in _nummern(_ziel):
            _zeile = _txt[:_mv.start()].count("\n") + 1
            _ins_leere.append(f"{_p.relative_to(WURZEL)}:{_zeile} "
                              f"{_mv.group(1)} Punkt {_mv.group(2)}")
check(not _ins_leere,
      "diese Verweise zeigen auf eine Punktnummer, die es in der Datei "
      f"nicht gibt: {'; '.join(_ins_leere[:6])}")
if not failures:
    _wieviele = sum(1 for _p in (WURZEL / "tests").glob("test_*.py"))
    print(f"   OK   {_wieviele} Python-Pruefdateien, jede Nummer einmal, "
          f"{_verweise} Verweise treffen")

print("\nREADME: die Zahlen darin haben einen Verwalter")
# Die READMEs nennen Zahlen, die sich aendern — wieviele Pruefungen, was
# gemessen wurde. Prosa altert lautlos, und das README ist die Datei, die
# ein Fremder zuerst liest. Geprueft wird die BEZIEHUNG: was ein README
# behauptet, muss stimmen — in JEDER Sprache, sonst altert die zweite
# Fassung still hinter der ersten her.
import json as _js
import re as _r2

_ZAHLWORT = {
    "zwanzig": 20, "einundzwanzig": 21, "zweiundzwanzig": 22,
    "dreiundzwanzig": 23, "vierundzwanzig": 24, "fuenfundzwanzig": 25,
    "fünfundzwanzig": 25, "sechsundzwanzig": 26, "siebenundzwanzig": 27,
    "achtundzwanzig": 28, "neunundzwanzig": 29, "dreissig": 30,
    "einunddreissig": 31, "zweiunddreissig": 32, "dreiunddreissig": 33,
}


def _zahl(wort: str) -> int | None:
    return int(wort) if wort.isdigit() else _ZAHLWORT.get(wort.lower())


# Je Sprache: wie Pruefungen und Pruefdateien heissen, und woran die
# Kennzahlen ihr Messgeraet tragen.
_READMES = {
    "README.de.md": {
        "pruefungen": r"([A-Za-zÄÖÜäöü]+|\d+) Pr(?:ue|ü)fungen",
        "dateien": r"([A-Za-zÄÖÜäöü]+|\d+) Pr(?:ue|ü)fdateien",
        "messgeraet": ["synthetisch", "Golddokumente", "Goldspannen",
                       "Leckrate"],
        "nachrechenbar": ("nachrechenbar", "reproduzierbar"),
    },
    "README.md": {
        "pruefungen": r"(\d+) checks",
        "dateien": r"(\d+) test files",
        "messgeraet": ["synthetic", "gold documents", "gold spans",
                       "leak rate"],
        "nachrechenbar": ("reproducible",),
    },
}

# Wieviele Pruefungen fuehrt der Laeufer wirklich — im oeffentlichen
# Paket? Zurueckgehaltene Pruefdateien zaehlen dort nicht. Der Laeufer
# fuehrt eine Pruefung MEHR als es Dateien gibt: `check_taxonomy.py` liegt
# unter `tools/` und zaehlt mit.
_echt_dateien = sum(
    1 for _p in list((WURZEL / "tests").glob("test_*.py"))
    + list((WURZEL / "tests").glob("test_*.js"))
    if _p.relative_to(WURZEL).as_posix() not in DRAUSSEN)

# ⚠️⚠️ DIE MESSUNG AN DEN GOLDDOKUMENTEN STEHT AN MEHREREN ORTEN.
#
# In den READMEs (Tabelle «Wie gut ist es?») und in
# `tools/paket/requirements-paket.txt`, wo sie begruendet, warum das Paket
# torch traegt und nicht ONNX. Mehrere Orte sind hier RICHTIG: der eine
# spricht zum Besucher, der andere zum Bauenden. Falsch waere ein stiller
# Unterschied — eine abgeschriebene Zahl wandert weiter, etwa in eine
# Modellbeschreibung. Nicht zusammengelegt, sondern GEKLAMMERT.
_rq = (WURZEL / "tools" / "paket" / "requirements-paket.txt").read_text(
    encoding="utf-8")
_m_rq = _r2.search(r"torch\s+runs/ch-\S+\s+(\d+)\s+([\d.]+)\s+(\d+)", _rq)
check(_m_rq is not None,
      "die Messtabelle in requirements-paket.txt ist nicht mehr lesbar — "
      "sie begruendet, warum das Paket torch traegt")

# ⚠️⚠️ DIE ADRESSEN STEHEN AN ZWEI ORTEN — im Burgermenue
# (`adressen.json`) und in der Prosa der READMEs. Das Menue bedient den
# Anwender, das README den Besucher. Was nicht richtig ist, waere ein
# stiller Unterschied zwischen ihnen. Also nicht zusammenlegen, sondern
# klammern.
_adr = _js.loads((WURZEL / "app" / "static" / "adressen.json")
                 .read_text(encoding="utf-8"))

for _name, _sprache in _READMES.items():
    _pfad = WURZEL / _name
    check(_pfad.is_file(), f"{_name} fehlt")
    if not _pfad.is_file():
        continue
    _readme = _pfad.read_text(encoding="utf-8")

    _m = _r2.search(_sprache["pruefungen"], _readme)
    check(_m is not None, f"{_name} nennt keine Zahl der Pruefungen")
    if _m:
        _behauptet = _zahl(_m.group(1))
        check(_behauptet == _echt_dateien + 1,
              f"{_name} nennt {_m.group(1)!r} Pruefungen, es sind "
              f"{_echt_dateien + 1}")
    _m2 = _r2.search(_sprache["dateien"], _readme)
    check(_m2 is not None, f"{_name} nennt keine Zahl der Pruefdateien")
    if _m2:
        check(_zahl(_m2.group(1)) == _echt_dateien,
              f"{_name} nennt {_m2.group(1)!r} Pruefdateien, es sind "
              f"{_echt_dateien}")

    if _m_rq:
        _lecks, _f1, _uebermask = _m_rq.groups()
        for _wert, _was in ((_f1, "Micro-F1"),
                            (_uebermask, "Uebermaskierungen"),
                            (_lecks, "Lecks")):
            # Die deutsche README schreibt Dezimalzahlen mit Komma
            # (0,739) — dieselbe Zahl, andere Schreibweise.
            check(_wert in _readme or _wert.replace(".", ",") in _readme,
                  f"{_name} nennt {_was} {_wert} nicht — "
                  f"`requirements-paket.txt` misst so, und ein stiller "
                  f"Unterschied wandert weiter")

    # ⚠️ Die Kennzahlen tragen ihr Messgeraet. Eine Leckrate ohne die
    # Angabe, woran sie gemessen wurde, ist wertlos — zwei Zahlen aus zwei
    # Testsets sehen sonst vergleichbar aus.
    for _wort in _sprache["messgeraet"]:
        check(_wort.lower() in _readme.lower(),
              f"{_name} nennt «{_wort}» nicht — eine Kennzahl ohne ihr "
              "Messgeraet ist keine")
    check(any(w in _readme for w in _sprache["nachrechenbar"]),
          f"{_name} sagt nicht, welche Zahl nachrechenbar ist und welche "
          "nicht")

    for _e in _adr["eintraege"]:
        _u = _e.get("url", "")
        if not _u or "github.com" not in _u:
            continue
        check(_u in _readme,
              f"«{_u}» steht im Burgermenue und NICHT in {_name} — eine "
              "Adresse mit zwei Verwaltern, von denen einer altert")

    # ⚠️⚠️ KEIN BEFEHL ZEIGT INS LEERE. Ein Befehl, der «No such file»
    # sagt, ist fuer einen Fremden der erste Eindruck. Jedes
    # `python3 <pfad>` muss eine Datei treffen, die es gibt — und jede
    # Flagge dahinter muss das Werkzeug kennen: eine erfundene Flagge
    # laeuft nicht weiter als ein falscher Pfad, sie sieht nur richtiger
    # aus. ERST DIE ZEILENFORTSETZUNGEN AUFLOESEN, sonst bleiben die
    # Flaggen der Folgezeilen ungesehen.
    _befehle = _r2.findall(r"python3 ([\w/]+\.py)", _readme)
    check(_befehle, f"{_name} zeigt keinen einzigen Befehl")
    for _b in sorted(set(_befehle)):
        check((WURZEL / _b).is_file(),
              f"{_name} ruft `{_b}` — die Datei gibt es nicht")
    for _zeile in _readme.replace("\\\n", " ").split("\n"):
        _m3 = _r2.search(r"python3 ([\w/]+\.py)(.*)", _zeile)
        if not _m3 or not (WURZEL / _m3.group(1)).is_file():
            continue
        _txt3 = (WURZEL / _m3.group(1)).read_text(encoding="utf-8")
        for _flagge in _r2.findall(r"--[a-z][a-z-]+", _m3.group(2)):
            check(f'"{_flagge}"' in _txt3 or f"'{_flagge}'" in _txt3,
                  f"{_name} ruft `{_m3.group(1)} {_flagge}` — die Flagge "
                  "kennt das Werkzeug nicht")

# ⚠️⚠️ UND KEIN MENUEEINTRAG ZEIGT AUF EINEN ORT, DEN ES NICHT GIBT —
# ausser den hier benannten.
#
# In einer ausgelieferten Anwendung ist ein toter Verweis ein Klick ins
# Leere. Die Eintraege fuer die Projektseite stehen bewusst schon im Menue;
# bis die Seite steht, sind sie hier benannt, damit das nicht still zur
# Gewohnheit wird. Wer die Seite aufschaltet, streicht die Zeilen unten;
# wer einen weiteren toten Verweis einbaut, wird gefragt.
#
# Geprueft wird die Eigenschaft: jede Adresse im Menue liegt auf einem
# Ort, den das Projekt betreibt.
# Seit 0.9.65 ist www.maschera.ch ein betriebener Ort: die Projektseite
# `site/` geht dorthin (Entscheid des Anwenders, 26.9.2026). Bis zum
# Aufschalten antwortet sie mit 403 — Minuten, nicht Wochen.
_BETRIEBEN = ("github.com", "www.maschera.ch")
_NOCH_NICHT: dict[str, str] = {}
for _e in _adr["eintraege"]:
    _u = _e.get("url", "")
    if not _u or any(_h in _u for _h in _BETRIEBEN):
        continue
    check(_u in _NOCH_NICHT,
          f"«{_u}» ({_e.get('schluessel', '?')}) zeigt auf einen Ort, "
          f"den das Projekt nicht betreibt und der hier nicht benannt "
          f"ist — ein Klick ins Leere in der ausgelieferten Anwendung")
# Die Projektseite ist EINE Seite. Ein Pfad dahinter (`/download`, so stand
# es bis 0.9.65 im Menue) waere ein 404; ein Anker muss in `site/index.html`
# stehen.
_seite = (WURZEL / "site" / "index.html").read_text(encoding="utf-8")
for _e in _adr["eintraege"]:
    _u = _e.get("url", "")
    if "www.maschera.ch" not in _u:
        continue
    _rest = _u.split("www.maschera.ch", 1)[1]
    _pfad, _, _anker = _rest.partition("#")
    check(_pfad in ("", "/"),
          f"«{_u}» ({_e.get('schluessel', '?')}) zeigt auf einen Pfad — die "
          f"Projektseite hat nur eine Seite, das waere ein 404")
    check(not _anker or f'id="{_anker}"' in _seite,
          f"«{_u}» zeigt auf den Abschnitt «{_anker}», den site/index.html "
          f"nicht hat")

# ⚠️ Und die Ausnahmen altern nicht still: steht die Seite, muss die
# Zeile weg, sonst meldet sich diese Pruefung.
for _u, _grund in _NOCH_NICHT.items():
    check(any(_e.get("url") == _u for _e in _adr["eintraege"]),
          f"«{_u}» ist als «noch nicht da» benannt, steht aber gar nicht "
          f"mehr im Menue — die Ausnahme gehoert gestrichen ({_grund})")

# ⚠️⚠️ DIE KENNUNG IN DER MITTE HEISST «CH», NICHT «CHE».
#
# MAS·CH·ERA — so steht es in der App seit jeher. README, SPEC, Doku und
# Projektseite trugen bis 1.0.0 «CHE», im Schriftzug wie im Satz darueber,
# in vier Sprachen. Gesucht wird «CHE» als eigenes Wort in allem, was
# Besucher lesen; die UID der Unternehmen (`CHE-123.456.789`) bleibt, denn
# dort ist «CHE» das amtliche Praefix.
_che_orte = subprocess.run(
    ["git", "ls-files", "README.md", "README.de.md", "SPEC.md", "LIZENZ.md",
     "docs", "site", "app/static"],
    cwd=WURZEL, capture_output=True, text=True).stdout.split()
_che_treffer = []
for _f in _che_orte:
    _pfad = WURZEL / _f
    if _pfad.suffix not in (".md", ".html", ".js", ".css"):
        continue
    for _nr, _z in enumerate(_pfad.read_text(encoding="utf-8").splitlines(), 1):
        # Die UID selbst beschreiben darf «CHE» nennen (SPEC.md, Pruefziffer).
        if "UID" in _z:
            continue
        if re.search(r"(?<![A-Za-z])CHE(?![A-Za-z\-\d.])", _z) \
                or re.search(r"MAS(?:\*\*|<[^>]+>)CHE", _z):
            _che_treffer.append(f"{_f}:{_nr}")
check(not _che_treffer,
      f"«CHE» statt «CH» in {len(_che_treffer)} Zeile(n): "
      f"{', '.join(_che_treffer[:6])}")

# ⚠️⚠️ DER VERMERK DES UEBERNOMMENEN CODES STEHT IN `LICENSE`.
#
# MASCHERA traegt Code aus rizzo-pii (MIT). MIT verlangt, dass dessen
# Urheberrechtsvermerk JEDE Kopie begleitet — eine Nennung im README ist
# keine. Geprueft wird die Beziehung: solange irgendeine verfolgte Datei
# rizzo-pii nennt, muss die Zeile in `LICENSE` stehen. Wer die letzte
# Nennung entfernt, weil der Code ersetzt ist, darf auch die Zeile
# streichen — vorher nicht.
_lizenz = (WURZEL / "LICENSE").read_text(encoding="utf-8")
_nennt = [str(_p.relative_to(WURZEL)) for _p in dateien()
          if _p.name != "LICENSE"
          and "rizzo-pii" in _p.read_text(encoding="utf-8", errors="ignore")]
if _nennt:
    check("Copyright (c) 2026 Simone Rizzo" in _lizenz,
          f"{len(_nennt)} Datei(en) nennen rizzo-pii (z. B. {_nennt[0]}), "
          "aber `LICENSE` traegt dessen Urheberrechtsvermerk nicht — MIT "
          "verlangt ihn in jeder Kopie")

if not failures:
    print(f"   OK   {_echt_dateien + 1} Pruefungen, {_echt_dateien} Dateien, "
          f"{len(_READMES)} READMEs, Kennzahlen mit Messgeraet")


print("\nZ. MASCHERA behauptet nicht, alle Landessprachen zu koennen")
# Die Schweiz hat VIER Landessprachen: Deutsch, Franzoesisch,
# Italienisch, **Raetoromanisch**. Amtssprachen des Bundes sind DREI.
# MASCHERA spricht Deutsch, Franzoesisch, Italienisch und **Englisch**.
#
# Das sind zwar auch vier — aber nicht dieselben vier. «In allen vier
# Landessprachen» behauptet zweierlei Falsches auf einmal: dass
# Raetoromanisch unterstuetzt sei, und dass Englisch eine Landessprache
# waere. Bei einem Werkzeug fuer Schweizer Dokumente ist das ein
# Versprechen an eine Sprachgemeinschaft, das nicht eingehalten wird: wer
# ein raetoromanisches Dokument einlegt, bekommt die Namen im Klartext
# zurueck.
#
# Geprueft wird die Behauptung, nicht die Zahl vier: «vier Sprachen» ist
# richtig und darf stehen. Falsch ist, sie AMTS- oder LANDESsprachen zu
# nennen.
LANDESSPRACHEN = [
    (r"vier\s+Amtssprachen", "Amtssprachen des Bundes sind DREI"),
    (r"vier\s+Landessprachen", "die vierte ist Raetoromanisch, nicht Englisch"),
    (r"four\s+(national|official)\s+languages", "same claim in English"),
    (r"quatre\s+langues\s+(nationales|officielles)", "dasselbe auf Franzoesisch"),
    (r"quattro\s+lingue\s+(nazionali|ufficiali)", "dasselbe auf Italienisch"),
]
_behauptet = []
for _p in dateien():
    _rel = _p.relative_to(WURZEL)
    if _rel.as_posix() == "tests/test_veroeffentlichung.py":
        continue          # das Regelwerk nennt die Muster selbst
    _txt = _p.read_text(encoding="utf-8", errors="replace")
    for _muster, _warum in LANDESSPRACHEN:
        for _m in re.finditer(_muster, _txt, re.IGNORECASE):
            _zeile = _txt[:_m.start()].count("\n") + 1
            _behauptet.append(f"{_rel}:{_zeile} {_m.group(0)!r} — {_warum}")
check(not _behauptet,
      "hier wird behauptet, MASCHERA koenne die Landes- oder Amtssprachen: "
      + "; ".join(_behauptet[:4]))
if not failures:
    print(f"   OK   {len(LANDESSPRACHEN)} Formeln geprueft, keine Behauptung")

print("\nKein Werkzeug im Baum kann von sich aus veroeffentlichen")
# Veroeffentlichen ist ein bewusster Schritt von Hand. MASCHERA selbst
# bekommt keinen Hochladeweg — kein Werkzeug im Baum ruft eine
# Schnittstelle, die Modelle oder Dateien zu einem Dienst schiebt. Aus «wir
# tun das nicht» wird «das Werkzeug kann das nicht».
#
# Was diese Wache NICHT kann: sie hindert niemanden daran, von Hand ein
# Skript zu tippen. Sie verhindert, dass ein Hochladeweg STILL in den Baum
# kommt.
HOCHLADEN = (
    ("HfApi", "der Zugang zur Hugging-Face-Schnittstelle"),
    ("upload_folder", "laedt ein ganzes Verzeichnis hoch"),
    ("upload_file", "laedt eine Datei hoch"),
    ("create_repo", "legt ein Repositorium an"),
    ("push_to_hub", "schiebt Modell oder Tokenizer hinauf"),
    ("create_pull_request", "oeffnet einen Antrag bei einem Dienst"),
)
_kann = []
for _p in dateien():
    _rel = _p.relative_to(WURZEL)
    # ⚠️ Diese Datei nennt die Namen, um nach ihnen zu suchen.
    if _rel.as_posix() == "tests/test_veroeffentlichung.py":
        continue
    if _p.suffix not in (".py", ".fish", ".sh", ".yaml", ".yml"):
        continue
    _text = _p.read_text(encoding="utf-8", errors="replace")
    _code = "\n".join("" if z.lstrip().startswith("#") else z
                      for z in _text.splitlines())
    for _wort, _was in HOCHLADEN:
        if _wort in _code:
            _kann.append(f"{_rel}: {_wort} ({_was})")
check(not _kann,
      f"ein Werkzeug im Baum kann veroeffentlichen: {'; '.join(_kann)} — "
      f"der Startschuss gehoert dem Anwender, und ein Hochladeweg im "
      f"Repositorium waere einer, den niemand mehr sieht")
if not failures:
    print(f"   OK   {len(HOCHLADEN)} Wege geprueft, keiner im Baum")

print("\nKeine Fernkopie zeigt nach draussen")
# In der Arbeitsumgebung traegt die Git-Geschichte die internen Dokumente.
# Sie darf nirgends hin, wo sie oeffentlich werden kann; das oeffentliche
# Repositorium entsteht aus `tools/oeffentlich_paket.py`.
#
# Geprueft wird die EIGENSCHAFT und nicht eine Liste verbotener Namen:
# jede Fernkopie muss ein Pfad oder eine ssh-Adresse ohne Punkt im
# Rechnernamen sein — also ein Rechner im eigenen Netz. Jeder oeffentliche
# Dienst faellt damit auf, auch einer, den heute niemand kennt.
#
# Nur in der Arbeitsumgebung: ein oeffentlicher Klon zeigt zu Recht auf
# sein oeffentliches Repositorium.
import subprocess as _sp
_fern = ""
if not ARBEITSUMGEBUNG:
    print("   HINWEIS keine interne Liste — die Pruefung der Fernkopien "
          "gilt nur in der Arbeitsumgebung")
else:
    try:
        _fern = _sp.run(["git", "remote", "-v"], cwd=WURZEL,
                        capture_output=True, text=True, timeout=10).stdout
    except Exception:  # noqa: BLE001
        check(False, "die Fernkopien lassen sich nicht lesen")

for _z in _fern.splitlines():
    _teile = _z.split()
    if len(_teile) < 2:
        continue
    _name, _adr = _teile[0], _teile[1]
    # Ein Pfad ist immer in Ordnung. Bei `benutzer@rechner:pfad` zaehlt
    # der Rechnername: ein Punkt darin heisst «im Internet».
    _wirt = _adr.split("@")[-1].split(":")[0] if "@" in _adr else ""
    if _adr.startswith(("/", ".", "~")):
        continue
    check("." not in _wirt and "://" not in _adr,
          f"die Fernkopie «{_name}» zeigt nach draussen: {_adr} — die "
          "Geschichte dieses Baums traegt die internen Dokumente und "
          "darf nirgends hin, wo sie oeffentlich werden kann. Das "
          "oeffentliche Repositorium entsteht aus oeffentlich_paket.py")
if not failures:
    print("   OK   nur der eigene Server")


print()
if failures:
    print(f"FEHLGESCHLAGEN — {len(failures)}:")
    for f in failures:
        print("  -", f)
    print("\n  Diese Angaben duerfen nicht ins oeffentliche Repository.")
    print("  Ist ein Treffer berechtigt, gehoert er in VERBOTEN ausgenommen —")
    print("  mit Begruendung, nicht durch Streichen des Musters.")
    raise SystemExit(1)
print("Alle Pruefungen bestanden.")
