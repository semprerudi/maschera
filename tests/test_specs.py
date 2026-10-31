#!/usr/bin/env python3
"""Der Anforderungskatalog in `specs/` bleibt wahr.

    python3 tests/test_specs.py

Der Katalog soll reichen, um MASCHERA neu zu bauen. Das haelt er nur, wenn
er nicht zurueckbleibt: `SPEC.md` stand vom 26.9. bis 30.10.2026 still, und nichts
schlug an. Hier schlaegt es an.

⚠️ Geprueft wird die FORM, nicht die Wahrheit jedes Satzes: erzeugte Teile
aktuell, Kennungen eindeutig, jeder Verweis vorhanden, jede Anforderung mit
Pruefung oder ausdruecklichem Vermerk. Ob ein Satz stimmt, liest ein Mensch.
"""
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))
import specs_bauen  # noqa: E402

SPECS = WURZEL / "specs"
failures: list[str] = []


def check(ok, msg):
    if not ok:
        failures.append(msg)
        print(f"   FEHL {msg}")


def handdateien() -> list[Path]:
    return sorted(SPECS.glob("*.md"))


def ohne_code(text: str) -> str:
    """Text ohne Codebloecke: dort darf stehen, was der Code enthaelt."""
    return re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)


KAPITEL = ("README", "01_ziele", "02_funktional", "03_nichtfunktional",
           "04_architektur", "05_ablaeufe", "06_erkennung", "07_api",
           "08_synthese_training", "09_evaluation", "10_oberflaeche",
           "11_design", "12_pakete_release", "13_sicherheit", "14_regeln",
           "15_entscheide", "16_neubau")

print("1. Alle Kapitel sind da")
for name in KAPITEL:
    check((SPECS / f"{name}.md").is_file(), f"specs/{name}.md fehlt")
check(len(handdateien()) == len(KAPITEL),
      "ein Kapitel in specs/ ist nicht in der Liste KAPITEL")

print("\n2. Die erzeugten Teile sind aktuell")
for name, inhalt in specs_bauen.erzeuge().items():
    pfad = SPECS / "erzeugt" / name
    check(pfad.is_file() and pfad.read_text(encoding="utf-8") == inhalt,
          f"specs/erzeugt/{name} ist veraltet: python3 tools/specs_bauen.py")

print("\n3. Jede Kennung ist einmal vergeben")
KENNUNG = r"(?:FA|NFA|EN)-\d{3}"
vergeben: dict[str, str] = {}
for pfad in handdateien():
    for k in re.findall(rf"^#+ ({KENNUNG})\b", pfad.read_text(encoding="utf-8"),
                        flags=re.M):
        check(k not in vergeben, f"{k} doppelt: {vergeben.get(k)}, {pfad.name}")
        vergeben[k] = pfad.name

print("\n4. Jeder Verweis zeigt auf etwas")
pruefpunkte = specs_bauen.alle_testkennungen()
for pfad in handdateien():
    text = pfad.read_text(encoding="utf-8")
    for k in set(re.findall(rf"\b{KENNUNG}\b", text)):
        check(k in vergeben, f"{pfad.name} nennt {k}, das es nicht gibt")
    for k in set(re.findall(r"\bT-[A-Z][A-Z-]*-\d+[A-Z]?\b", text)):
        check(k in pruefpunkte, f"{pfad.name} nennt {k}, das es nicht gibt")

print("\n5. Jede Anforderung hat eine Pruefung oder sagt, dass sie keine hat")
for name in ("02_funktional.md", "03_nichtfunktional.md"):
    text = (SPECS / name).read_text(encoding="utf-8")
    teile = re.split(r"^(?=#+ (?:FA|NFA)-\d{3}\b)", text, flags=re.M)
    for teil in teile[1:]:
        kopf = teil.split("\n", 1)[0]
        check(re.search(r"\bT-[A-Z]", teil) or "ohne Prüfung" in teil,
              f"{name}: «{kopf}» nennt keine Pruefung")

print("\n6. Keine toten Links")
for pfad in sorted(SPECS.rglob("*.md")):
    for ziel in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)",
                           ohne_code(pfad.read_text(encoding="utf-8"))):
        if re.match(r"[a-z]+:", ziel):
            continue
        check((pfad.parent / ziel).exists(),
              f"{pfad.relative_to(WURZEL)}: Link {ziel} zeigt ins Leere")

print("\n7. Kein Gedankenstrich in den Texten")
for pfad in handdateien():
    for nr, zeile in enumerate(ohne_code(pfad.read_text(encoding="utf-8"))
                               .splitlines(), 1):
        check(not re.search(r"[—–]", zeile),
              f"{pfad.name}: Gedankenstrich in «{zeile.strip()[:50]}»")

print("\n8. Jeder Endpunkt und jedes Tag ist beschrieben")
_api = (SPECS / "07_api.md").read_text(encoding="utf-8")
for pfad in sorted(set(re.findall(r"`(/api/[a-z_]+)`",
                                  specs_bauen.endpunkte()))):
    check(pfad in _api, f"07_api.md beschreibt {pfad} nicht")
_erkennung = (SPECS / "06_erkennung.md").read_text(encoding="utf-8")
for tag in re.findall(r"^\| \d+ \| `([A-Z0-9_]+)`", specs_bauen.tags(), re.M):
    check(f"`{tag}`" in _erkennung, f"06_erkennung.md nennt {tag} nicht")

print("\n9. Jeder neue Pruefpunkt gehoert zu einer Anforderung")
# Eine Sperrklinke: die Altliste darf nur schrumpfen. Ein neuer Punkt ohne
# Anforderung ist eine Funktion, die der Katalog nicht kennt.
ALTLISTE = WURZEL / "tests" / "specs_altliste.txt"
_alt = {z.strip() for z in ALTLISTE.read_text(encoding="utf-8").splitlines()
        if z.strip() and not z.startswith("#")}
_genannt = set()
for pfad in handdateien():
    _genannt |= set(re.findall(r"\bT-[A-Z][A-Z-]*-\d+[A-Z]?\b",
                               pfad.read_text(encoding="utf-8")))
for k in sorted(pruefpunkte - _genannt - _alt):
    check(False, f"{k} steht in keiner Anforderung: in specs/ eintragen")
for k in sorted(_alt & _genannt):
    check(False, f"{k} ist jetzt zugeordnet: aus der Altliste streichen")
for k in sorted(_alt - pruefpunkte):
    check(False, f"{k} gibt es nicht mehr: aus der Altliste streichen")

print("\n10. Ein Release ohne Durchsicht des Katalogs haelt an")
_kapitel = ["specs/02_funktional.md"]
_log = "## 9.1.0 (2026-01-01)\n\nText.\n\n## 9.0.0 (2025-01-01)\n\n"
_gut = "| 9.1.x | ja |\n| 9.1.x | yes |\n"
_rb = specs_bauen.release_befunde
check(not _rb(_kapitel, _log, _gut, "9.1.0"), "Kapitel geaendert wird abgewiesen")
check(_rb(["app/serve.py"], _log, _gut, "9.1.0"),
      "Release ohne Kapitel laeuft durch")
check(_rb(["specs/erzeugt/tags.md"], _log, _gut, "9.1.0"),
      "Erzeugtes zaehlt als Durchsicht")
_grund = _log.replace("Text.", "Text.\n\nKatalog unverändert: nur Pakete.")
check(not _rb(["app/serve.py"], _grund, _gut, "9.1.0"),
      "die begruendete Zeile wirkt nicht")
_fremd = _log.replace("## 9.0.0 (2025-01-01)\n\n",
                      "## 9.0.0 (2025-01-01)\n\nKatalog unverändert: alt.\n")
check(_rb(["app/serve.py"], _fremd, _gut, "9.1.0"),
      "die Zeile eines aelteren Release gilt mit")
check(_rb(["app/serve.py"], _log.replace("Text.", "Katalog unverändert:"),
          _gut, "9.1.0"), "die Zeile ohne Grund gilt")

print("\n11. SECURITY.md nennt die Fassungsreihe des Release")
check(_rb(_kapitel, _log, "| 9.0.x | ja |\n| 9.0.x | yes |\n", "9.1.0"),
      "alte Fassungsreihe in SECURITY.md laeuft durch")
check(len(_rb(_kapitel, _log, "| 9.1.x | ja |\n", "9.1.0")) == 1,
      "die englische Zeile wird nicht verlangt")

print("\n12. Die Werte im Text sind die Werte im Code")
# Der Katalog sagte, der Heimatort bleibe lesbar; `taxonomy.yaml` maskiert ihn.
# Das fand nur ein Leser. Was sich vergleichen laesst, wird verglichen.
import yaml  # noqa: E402

def _lies(rel):
    return (WURZEL / rel).read_text(encoding="utf-8")

def _steht(rel, *teile):
    text = re.sub(r"\s+", " ", _lies(rel))
    for t in teile:
        check(str(t) in text, f"{rel} nennt {t} nicht mehr, der Code schon")

_tax = yaml.safe_load(_lies("packs/ch/taxonomy.yaml"))
_tags = {t["tag"]: t for t in _tax["tags"]}
_zeilen = 0
_stufe = None
_text06 = _lies("specs/06_erkennung.md").split("## Fehlerbudgets")[0]
for z in _text06.splitlines():
    t = re.match(r"### Stufe (\d)", z)
    if t:
        _stufe = int(t.group(1))
        continue
    if z.startswith("### "):
        _stufe = None
    if _stufe is None or not z.startswith("| `"):
        continue
    zellen = [c.strip() for c in z.strip("|").split("|")]
    for tag in re.findall(r"`([A-Z0-9_]+)`", zellen[0]):
        _zeilen += 1
        e = _tags.get(tag)
        check(e is not None, f"06_erkennung.md nennt das Tag {tag}, das es nicht gibt")
        if e is None:
            continue
        check(e["stage"] == _stufe,
              f"{tag}: Text Stufe {_stufe}, Code Stufe {e['stage']}")
        _soll = "M" if e["action"] == "mask" else "T"
        _aktion = [c.strip("*") for c in zellen[1:] if c.strip("*") in ("M", "T")]
        check(_aktion == [_soll], f"{tag}: Text {_aktion}, Code {_soll}")
        if e.get("budget"):
            _budget = [c.strip("*")[0] for c in zellen[1:]
                       if re.match(r"\*{0,2}[RAP]( |\*|$)", c)]
            check(not _budget or _budget[0] == e["budget"],
                  f"{tag}: Text Budget {_budget}, Code {e['budget']}")
check(_zeilen == len(_tags),
      f"06_erkennung.md fuehrt {_zeilen} Tags in den Stufen, es sind {len(_tags)}")

from core.einstellungen import (GROESSEN, GEMESSENE_MINDESTBREITE,  # noqa: E402
                                VORGABE_PORT, WIDGET_BREITE, WIDGET_RAHMEN)
from core.masking import MIN_PART_LEN, PROPAGATE_TAGS  # noqa: E402

_steht("specs/02_funktional.md", f"127.0.0.1:{VORGABE_PORT}")
_sw = _tax["thresholds"]
_steht("specs/06_erkennung.md",
       *(f"`{k}` = {_sw[k]:.2f}" for k in ("R", "A", "P")))
_steht("specs/04_architektur.md", *(f"`{t}`" for t in sorted(PROPAGATE_TAGS)),
       f"ab {MIN_PART_LEN} Zeichen", "Überlappung 128", "Schritt 382",
       "davon 510 nutzbar")
_steht("specs/10_oberflaeche.md",
       f"Breite {WIDGET_BREITE} px ({GEMESSENE_MINDESTBREITE} Inhalt, "
       f"{WIDGET_RAHMEN} Rahmen)",
       f"Grösse {GROESSEN[0]} bis {GROESSEN[-1]} %")

_js = _lies("app/static/maschera.js")
_weg = re.findall(r'"([\w-]+)"', re.search(
    r"const ARBEITSWEG = \[(.*?)\];", _js, re.S).group(1))
_stand = _lies("specs/10_oberflaeche.md").split("## Tastatur")[1]
_orte = [_stand.find(f"`{k}`") for k in _weg]
check(-1 not in _orte, "10_oberflaeche.md: ein Element des Tab-Wegs fehlt")
check(_orte == sorted(_orte),
      "10_oberflaeche.md: der Tab-Weg steht in anderer Folge als ARBEITSWEG")
_accept = re.search(r'id="datei"\s+accept="([^"]+)"',
                    _lies("app/static/index.html")).group(1).split(",")
_steht("specs/10_oberflaeche.md", *(f"`{e}`" for e in _accept))
_adr = yaml.safe_load(_lies("app/static/adressen.json"))["eintraege"]
_burger = _stand = _lies("specs/10_oberflaeche.md").split("## Burgermenü")[1]
_i18n_de = specs_bauen._flach(specs_bauen._i18n()["de"])
_orte = [_burger.find(_i18n_de[e["schluessel"]]) for e in _adr]
check(-1 not in _orte and _orte == sorted(_orte),
      "10_oberflaeche.md: das Burgermenue weicht von adressen.json ab")

_serve = _lies("app/serve.py")
for teil in re.findall(r'^\s+"([a-z-]+-src|object-src|base-uri|frame-ancestors)'
                       r' ', _serve, re.M):
    check(teil.split("-")[0] in _lies("specs/13_sicherheit.md"),
          f"13_sicherheit.md nennt {teil} nicht")

_train = _lies("train.py")
_08 = _lies("specs/08_synthese_training.md")
for name, zeile in (("--epochs", "| Epochen | 3 |"),
                    ("--lr", "| Lernrate | 3e-5 |"),
                    ("--max-length", "| Sequenzlänge | 512 |")):
    wert = re.search(name + r'", type=\w+, default=([\w.-]+)', _train).group(1)
    soll = zeile.split("|")[2].strip()
    check(float(wert) == float(soll), f"train.py {name}={wert}, Katalog {soll}")
    check(zeile in _08, f"08 fuehrt die Zeile {zeile} nicht")
for wert in ("warmup_ratio=0.1", "weight_decay=0.01"):
    check(wert in _train, f"train.py: {wert} nicht mehr gefunden")

print()
if failures:
    print(f"{len(failures)} FEHLER")
    sys.exit(1)
print("OK: der Katalog ist vollstaendig verdrahtet")
