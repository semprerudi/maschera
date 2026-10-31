#!/usr/bin/env python3
"""Die erzeugten Teile des Anforderungskatalogs in `specs/`.

    python3 tools/specs_bauen.py            schreibt `specs/erzeugt/`
    python3 tools/specs_bauen.py --html     dazu die Leseansicht `specs/html/`
    python3 tools/specs_bauen.py --pruefen  schreibt nichts, meldet Veraltetes
    python3 tools/specs_bauen.py --release BASIS FASSUNG   Stand vor dem Release

Was sich aus dem Code lesen laesst, wird nicht von Hand gepflegt: Prüfungen,
Tags, Muster, Endpunkte und die Beschriftungen. Eine Handliste dieser Laenge
veraltet wie `SPEC.md` nach dem 26.9.2026. `tests/test_specs.py` ruft
`erzeuge()` und vergleicht mit dem, was im Baum liegt.

⚠️ Nur oeffentliche Prüfungen: `tools/pruefungen_intern.txt` nennt die
internen, und im oeffentlichen Stand liegen sie gar nicht. Beide Baeume
ergeben so dieselben Dateien, und die Wache ist in beiden gruen.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "specs" / "erzeugt"
KOPF = ("<!-- Erzeugt von tools/specs_bauen.py aus dem Code. "
        "Nicht von Hand aendern. -->\n\n")
PUNKT = re.compile(r"^\s*(\d+[a-z]?)\.\s+(.+)$", re.S)
PRUEFWORTE = {"check", "pruefe"}


def sauber(text: str) -> str:
    """Eine Zeile fuer Menschen: kein Umbruch, kein Gedankenstrich."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*[—–]\s*", ", ", text)
    return text.rstrip(": ").strip()


def _literal(knoten: ast.AST) -> str | None:
    """Der lesbare Teil eines Strings oder f-Strings, sonst None."""
    if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str):
        return knoten.value
    if isinstance(knoten, ast.JoinedStr):
        teile = []
        for t in knoten.values:
            if isinstance(t, ast.Constant):
                teile.append(str(t.value))
            else:
                teile.append("…")
        return "".join(teile)
    if isinstance(knoten, ast.BinOp) and isinstance(knoten.op, ast.Add):
        links, rechts = _literal(knoten.left), _literal(knoten.right)
        if links is not None and rechts is not None:
            return links + rechts
    return None


def _python_punkte(pfad: Path) -> tuple[str, list[dict]]:
    """Zweck und Punkte einer Pruefung in Python, ueber den Syntaxbaum."""
    baum = ast.parse(pfad.read_text(encoding="utf-8"))
    ereignisse: list[tuple[int, str, str]] = []
    for k in ast.walk(baum):
        if not isinstance(k, ast.Call) or not isinstance(k.func, ast.Name):
            continue
        if k.func.id == "print" and k.args:
            text = _literal(k.args[0])
            if text is not None:
                ereignisse.append((k.lineno, "punkt", text))
        elif k.func.id in PRUEFWORTE and len(k.args) >= 2:
            text = _literal(k.args[-1])
            if text is not None:
                ereignisse.append((k.lineno, "pruefung", text))
    doc = ast.get_docstring(baum) or ""
    return doc, _sammeln(ereignisse)


def _argumente_ende(text: str, start: int) -> int:
    """Stelle der schliessenden Klammer, Strings und Vorlagen beachtet."""
    tiefe, i, quote = 0, start, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "/" and text[i + 1:i + 2] == "/":
            i = text.find("\n", i)
            if i < 0:
                return len(text)
            continue
        elif c in "([{":
            tiefe += 1
        elif c in ")]}":
            tiefe -= 1
            if tiefe == 0:
                return i
        i += 1
    return len(text)


_JS_TEXT = re.compile(r'"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\]|\\.)*)`')


def _js_meldung(argumente: str) -> str | None:
    """Die Meldung am Ende von `pruefe(bedingung, meldung)`."""
    # Von hinten: die zusammenhaengenden Strings am Schluss sind die Meldung.
    teile: list[str] = []
    rest = argumente.rstrip()
    while True:
        rest = rest.rstrip()
        treffer = None
        for t in _JS_TEXT.finditer(rest):
            if t.end() == len(rest):
                treffer = t
        if treffer is None:
            break
        roh = treffer.group(1) if treffer.group(1) is not None else treffer.group(2)
        teile.insert(0, re.sub(r"\$\{[^}]*\}", "…", roh))
        rest = rest[:treffer.start()].rstrip()
        if rest.endswith("+"):
            rest = rest[:-1]
            continue
        break
    return "".join(teile).replace('\\"', '"') if teile else None


def _js_punkte(pfad: Path) -> tuple[str, list[dict]]:
    """Punkte der Oberflaechenpruefung: `console.log("N. …")`, `pruefe(…)`."""
    text = pfad.read_text(encoding="utf-8")
    ereignisse: list[tuple[int, str, str]] = []
    for t in re.finditer(r'console\.log\("(?:\\n)*(\d+[a-z]?\.\s[^"]*)"\)', text):
        ereignisse.append((t.start(), "punkt", t.group(1)))
    for t in re.finditer(r"(?<![\w.])pruefe\(", text):
        ende = _argumente_ende(text, t.end() - 1)
        meldung = _js_meldung(text[t.end():ende])
        if meldung:
            ereignisse.append((t.start(), "pruefung", meldung))
    kopf = re.match(r"\s*(?:#![^\n]*\n)?\s*/\*\*?(.*?)\*/", text, re.S)
    doc = ""
    if kopf:
        doc = re.sub(r"^\s*\* ?", "", kopf.group(1), flags=re.M).strip()
    return doc, _sammeln(ereignisse)


def _sammeln(ereignisse: list[tuple[int, str, str]]) -> list[dict]:
    """Punkte in Reihenfolge; Pruefungen gehoeren zum Punkt davor."""
    punkte: dict[str, dict] = {}
    aktuell = None
    for _, art, text in sorted(ereignisse):
        if art == "punkt":
            t = PUNKT.match(text)
            if not t:
                continue
            nummer = t.group(1)
            aktuell = punkte.setdefault(
                nummer, {"nummer": nummer, "titel": sauber(t.group(2)),
                         "pruefungen": []})
        else:
            if aktuell is None:
                aktuell = punkte.setdefault(
                    "0", {"nummer": "0", "titel": "Ohne eigenen Punkt",
                          "pruefungen": []})
            m = sauber(text)
            if m and m not in aktuell["pruefungen"]:
                aktuell["pruefungen"].append(m)
    return list(punkte.values())


def intern_liste() -> set[str]:
    datei = WURZEL / "tools" / "pruefungen_intern.txt"
    if not datei.is_file():
        return set()
    namen = set()
    for z in datei.read_text(encoding="utf-8").splitlines():
        if "|" in z and not z.lstrip().startswith("#"):
            namen.add(z.split("|", 1)[1].strip())
    return namen


def pruefdateien() -> list[Path]:
    intern = intern_liste()
    dateien = sorted(p for p in (WURZEL / "tests").glob("test_*")
                     if p.suffix in (".py", ".js")
                     and f"tests/{p.name}" not in intern)
    return dateien


def kennung(pfad: Path) -> str:
    return pfad.stem.removeprefix("test_").upper().replace("_", "-")


def testkatalog() -> str:
    zeilen = [KOPF, "# Testkatalog\n\n",
              "Jede Prüfung mit ihren Punkten. Die Kennung `T-<DATEI>-<PUNKT>` ",
              "ist stabil, solange der Punkt seine Nummer behält. Unter jedem ",
              "Punkt steht, woran er anschlägt (die Fehlermeldung der Prüfung; ",
              "`…` ist ein Wert, der erst zur Laufzeit feststeht).\n"]
    summe_p = summe_m = 0
    uebersicht = ["\n| Prüfung | Punkte | Meldungen |\n|---|---:|---:|\n"]
    koerper: list[str] = []
    for pfad in pruefdateien():
        rel = pfad.relative_to(WURZEL).as_posix()
        doc, punkte = (_js_punkte(pfad) if pfad.suffix == ".js"
                       else _python_punkte(pfad))
        zweck = sauber(doc.split("\n\n")[0]) if doc else ""
        meldungen = sum(len(p["pruefungen"]) for p in punkte)
        summe_p += len(punkte)
        summe_m += meldungen
        uebersicht.append(f"| `{rel}` | {len(punkte)} | {meldungen} |\n")
        koerper.append(f"\n## `{rel}`\n\n")
        if zweck:
            koerper.append(f"{zweck}.\n" if not zweck.endswith(".")
                           else f"{zweck}\n")
        for p in punkte:
            koerper.append(f"\n### T-{kennung(pfad)}-{p['nummer'].upper()}: "
                           f"{p['titel']}\n\n")
            for m in p["pruefungen"]:
                koerper.append(f"- {m}\n")
    uebersicht.append(f"| **Summe** | **{summe_p}** | **{summe_m}** |\n")
    return "".join(zeilen + uebersicht + koerper)


def alle_testkennungen() -> set[str]:
    ids = set()
    for pfad in pruefdateien():
        _, punkte = (_js_punkte(pfad) if pfad.suffix == ".js"
                     else _python_punkte(pfad))
        ids |= {f"T-{kennung(pfad)}-{p['nummer'].upper()}" for p in punkte}
    return ids


def _zelle(wert) -> str:
    if wert is None:
        return ""
    if wert is True:
        return "ja"
    if wert is False:
        return "nein"
    return str(wert).replace("|", "\\|").replace("\n", " ").strip()


def tags() -> str:
    tax = yaml.safe_load((WURZEL / "packs/ch/taxonomy.yaml")
                         .read_text(encoding="utf-8"))
    pack = yaml.safe_load((WURZEL / "packs/ch/pack.yaml")
                          .read_text(encoding="utf-8"))
    eintraege = tax["tags"]
    zeilen = [KOPF, "# Tags\n\n",
              "Quelle: `packs/ch/taxonomy.yaml`. Die Reihenfolge ist der "
              "BIO-Indexvertrag.\n\n",
              f"{len(eintraege)} Tags, {len(eintraege) * 2 + 1} BIO-Labels. "
              f"Vertrag sha256 `{pack['label_contract']['sha256']}`.\n\n",
              "| Index | Tag | Stufe | Aktion | Budget | bspd | Override | Notiz |\n",
              "|---:|---|---:|---|---|---|---|---|\n"]
    for i, e in enumerate(eintraege):
        zeilen.append(
            f"| {i} | `{e['tag']}` | {_zelle(e.get('stage'))} "
            f"| {_zelle(e.get('action'))} | {_zelle(e.get('budget'))} "
            f"| {_zelle(e.get('bspd'))} | {_zelle(e.get('override'))} "
            f"| {_zelle(sauber(str(e.get('note') or '')))} |\n")
    zeilen.append("\n## Schwellen\n\n```yaml\n")
    zeilen.append(yaml.safe_dump(tax.get("thresholds"), allow_unicode=True,
                                 sort_keys=False))
    zeilen.append("```\n")
    return "".join(zeilen)


def erkennungsregeln() -> str:
    roh = yaml.safe_load((WURZEL / "packs/ch/patterns.yaml")
                         .read_text(encoding="utf-8"))
    zeilen = [KOPF, "# Erkennungsregeln\n\n",
              "Quelle: `packs/ch/patterns.yaml`. Stufe 1: das Muster findet "
              "Kandidaten, die Prüfsumme entscheidet. Stufe 2: das Muster "
              "findet Kandidaten, der Anker entscheidet.\n"]
    for name, regel in roh["patterns"].items():
        zeilen.append(f"\n## {name}\n\n```yaml\n")
        zeilen.append(yaml.safe_dump(regel, allow_unicode=True,
                                     sort_keys=False, width=68))
        zeilen.append("```\n")
    return "".join(zeilen)


def endpunkte() -> str:
    zeilen = [KOPF, "# Endpunkte\n\n",
              "Aus den Dekoratoren in `app/app.py` und `app/serve.py`. Der "
              "Vertrag steht in [07_api.md](../07_api.md).\n\n",
              "| Methode | Pfad | Datei | Beschreibung |\n|---|---|---|---|\n"]
    for rel in ("app/app.py", "app/serve.py"):
        baum = ast.parse((WURZEL / rel).read_text(encoding="utf-8"))
        for f in ast.walk(baum):
            if not isinstance(f, ast.FunctionDef):
                continue
            for d in f.decorator_list:
                if not (isinstance(d, ast.Call)
                        and isinstance(d.func, ast.Attribute)
                        and d.func.attr in ("get", "post", "put", "delete",
                                            "route")
                        and d.args and _literal(d.args[0])):
                    continue
                methoden = [d.func.attr.upper()]
                for kw in d.keywords:
                    if kw.arg == "methods":
                        methoden = [e.value for e in kw.value.elts]
                doc = (ast.get_docstring(f) or "").split("\n")[0]
                zeilen.append(
                    f"| {', '.join(methoden)} | `{_literal(d.args[0])}` "
                    f"| `{rel}` | {_zelle(sauber(doc))} |\n")
    return "".join(zeilen)


def _i18n() -> dict:
    """Die Beschriftungen, von node gelesen: sie sind JavaScript."""
    quelle = (WURZEL / "app/static/maschera.js").read_text(encoding="utf-8")
    t = re.search(r"^const I18N = \{.*?^\};", quelle, re.S | re.M)
    if not t:
        raise SystemExit("I18N nicht gefunden in maschera.js")
    skript = (t.group(0) + "\nprocess.stdout.write(JSON.stringify(I18N, "
              "(k, v) => typeof v === 'function' ? String(v) : v));")
    lauf = subprocess.run(["node", "-e", skript], capture_output=True,
                          text=True, encoding="utf-8", check=True)
    return json.loads(lauf.stdout)


def _flach(wert, vorn: str = "") -> dict[str, str]:
    if isinstance(wert, dict):
        aus: dict[str, str] = {}
        for k, v in wert.items():
            aus.update(_flach(v, f"{vorn}.{k}" if vorn else k))
        return aus
    if isinstance(wert, list):
        aus = {}
        for i, v in enumerate(wert):
            aus.update(_flach(v, f"{vorn}[{i}]"))
        return aus
    return {vorn: str(wert)}


def texte() -> str:
    i18n = {s: _flach(w) for s, w in _i18n().items()}
    sprachen = list(i18n)
    schluessel: list[str] = []
    for s in sprachen:
        schluessel += [k for k in i18n[s] if k not in schluessel]
    zeilen = [KOPF, "# Beschriftungen\n\n",
              "Quelle: `I18N` in `app/static/maschera.js`. Hilfe und Impressum "
              "stehen in `app/static/seiten.js`.\n\n",
              f"{len(schluessel)} Schlüssel in {len(sprachen)} Sprachen.\n\n",
              "| Schlüssel | " + " | ".join(sprachen) + " |\n",
              "|---|" + "---|" * len(sprachen) + "\n"]
    for k in schluessel:
        zellen = " | ".join(_zelle(i18n[s].get(k)) for s in sprachen)
        zeilen.append(f"| `{k}` | {zellen} |\n")
    return "".join(zeilen)


def design() -> str:
    css = (WURZEL / "app/static/maschera.css").read_text(encoding="utf-8")
    ohne_kommentar = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    zeilen = [KOPF, "# Design-Tokens\n\n",
              "Quelle: `app/static/maschera.css`. Die Bedeutung steht in "
              "[11_design.md](../11_design.md).\n"]
    dunkel = re.search(r':root\[data-thema="dunkel"\]\s*\{(.*?)^\}',
                       ohne_kommentar, re.S | re.M)
    if not dunkel:
        raise SystemExit("Dunkles Thema nicht gefunden in maschera.css")
    hell: dict[str, str] = {}
    for block in re.findall(r"^:root\s*\{(.*?)^\}", ohne_kommentar,
                            re.S | re.M):
        hell.update(re.findall(r"^\s*(--[\w-]+):\s*(.+?);\s*$", block, re.M))
    dunkelwerte = dict(re.findall(r"^\s*(--[\w-]+):\s*(.+?);\s*$",
                                  dunkel.group(1), re.M))
    zeilen.append(f"\n## Tokens\n\n{len(hell)} Tokens, "
                  f"{len(dunkelwerte)} davon im dunklen Thema anders.\n\n"
                  "| Token | Hell | Dunkel |\n|---|---|---|\n")
    for name, wert in hell.items():
        zeilen.append(f"| `{name}` | `{_zelle(wert)}` "
                      f"| `{_zelle(dunkelwerte.get(name, wert))}` |\n")
    fehlt = [n for n in dunkelwerte if n not in hell]
    for name in fehlt:
        zeilen.append(f"| `{name}` |  | `{_zelle(dunkelwerte[name])}` |\n")
    abfragen = sorted(set(re.findall(r"^\s*@(?:media|container)[^{]+",
                                     ohne_kommentar, re.M)))
    zeilen.append("\n## Abfragen\n\n")
    for a in abfragen:
        zeilen.append(f"- `{' '.join(a.split())}`\n")
    return "".join(zeilen)


def elemente() -> str:
    html = (WURZEL / "app/static/index.html").read_text(encoding="utf-8")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    zeilen = [KOPF, "# Elemente der Oberflaeche\n\n",
              "Alle Elemente mit Kennung aus `app/static/index.html`, in der "
              "Reihenfolge der Datei.\n\n",
              "| Kennung | Element | Klassen |\n|---|---|---|\n"]
    for t in re.finditer(r"<([a-z0-9]+)\b([^>]*)>", html):
        attr = t.group(2)
        kennung = re.search(r'\bid="([^"]+)"', attr)
        if not kennung:
            continue
        klasse = re.search(r'\bclass="([^"]+)"', attr)
        zeilen.append(f"| `{kennung.group(1)}` | `{t.group(1)}` "
                      f"| {_zelle(klasse.group(1) if klasse else '')} |\n")
    return "".join(zeilen)


def seiten() -> str:
    """Hilfe und Willkommen. Das Impressum steht nur in `seiten.js`."""
    skript = ("const fs=require('fs'),vm=require('vm'),c={};"
              "vm.createContext(c);c.globalThis=c;"
              "vm.runInContext(fs.readFileSync('app/static/seiten.js','utf8'),c);"
              "const s=c.MASCHERA_SEITEN;process.stdout.write(JSON.stringify("
              "{hilfe:s.hilfe,willkommen:s.willkommen}));")
    lauf = subprocess.run(["node", "-e", skript], capture_output=True,
                          text=True, encoding="utf-8", check=True, cwd=WURZEL)
    daten = json.loads(lauf.stdout)
    zeilen = [KOPF, "# Hilfe und Willkommen\n\n",
              "Quelle: `app/static/seiten.js`. Der Aufbau ist Daten, gebaut "
              "wird daraus ohne `innerHTML`.\n"]
    for teil, sprachen in daten.items():
        zeilen.append(f"\n## {teil}\n")
        for sprache, inhalt in sprachen.items():
            zeilen.append(f"\n### {sprache}\n\n```json\n")
            zeilen.append(json.dumps(inhalt, ensure_ascii=False, indent=1))
            zeilen.append("\n```\n")
    return "".join(zeilen)


def abhaengigkeiten() -> str:
    zeilen = [KOPF, "# Abhaengigkeiten\n\n",
              "Die Listen im Wortlaut der Pakete, ohne Kommentare.\n"]
    # Ohne `requirements-dev.txt`: dessen interner Block fehlt im oeffentlichen
    # Stand, und die Datei fiele dort als veraltet auf.
    for rel in ("requirements.txt",
                "tools/paket/requirements-paket.txt",
                "tools/paket/requirements-appimage.txt",
                "tools/paket/requirements-flatpak.txt"):
        eintraege = []
        for z in (WURZEL / rel).read_text(encoding="utf-8").splitlines():
            z = z.split("#", 1)[0].strip()
            if z:
                eintraege.append(z)
        zeilen.append(f"\n## `{rel}`\n\n```text\n"
                      + "\n".join(eintraege) + "\n```\n")
    return "".join(zeilen)


def rueckverfolgung() -> str:
    """Anforderung zu Testfall, aus den Kapiteln 02 und 03."""
    zeilen = ["Kennung;Titel;Status;Testfaelle\n"]
    for name in ("02_funktional.md", "03_nichtfunktional.md"):
        text = (WURZEL / "specs" / name).read_text(encoding="utf-8")
        teile = re.split(r"^(?=#+ (?:FA|NFA)-\d{3}\b)", text, flags=re.M)
        for teil in teile[1:]:
            kopf = teil.split("\n", 1)[0].lstrip("# ").strip()
            kennung, _, titel = kopf.partition(" ")
            status = re.search(r"Status\s+`(\w+)`", teil)
            tests = sorted(set(re.findall(r"\bT-[A-Z][A-Z-]*-\d+[A-Z]?\b",
                                          teil)))
            zeilen.append(f"{kennung};{titel.replace(';', ',')};"
                          f"{status.group(1) if status else ''};"
                          f"{' '.join(tests)}\n")
    return "".join(zeilen)


def erzeuge() -> dict[str, str]:
    """Name unter `specs/erzeugt/` zu Inhalt."""
    return {
        "testkatalog.md": testkatalog(),
        "tags.md": tags(),
        "erkennungsregeln.md": erkennungsregeln(),
        "endpunkte.md": endpunkte(),
        "texte.md": texte(),
        "design.md": design(),
        "elemente.md": elemente(),
        "seiten.md": seiten(),
        "abhaengigkeiten.md": abhaengigkeiten(),
        "rueckverfolgung.csv": rueckverfolgung(),
    }


# Mermaid fest gepinnt. Die Leseansicht ist ein Arbeitsmittel, sie fährt in
# keinem Paket mit; ohne Netz bleiben die Diagramme als Text lesbar.
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
GRUNDFORM = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MASCHERA Katalog</title>
<style>
:root { --grund:#fbfaf7; --flaeche:#f1efea; --text:#2b2a27; --matt:#6b6962;
  --akzent:#2f6f4f; --kante:#dcd9d2; }
@media (prefers-color-scheme: dark) { :root { --grund:#1d1d1b; --flaeche:#272725;
  --text:#ecebe6; --matt:#a3a199; --akzent:#7fc29e; --kante:#3b3b37; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--grund); color:var(--text);
  font:16px/1.55 "IBM Plex Sans",system-ui,sans-serif; }
.seite { display:grid; grid-template-columns:18rem minmax(0,1fr); min-height:100vh; }
nav { background:var(--flaeche); border-right:1px solid var(--kante); padding:1rem;
  position:sticky; top:0; height:100vh; overflow:auto; }
nav h1 { font-size:1.1rem; margin:0 0 .75rem; }
nav a { display:block; color:var(--text); text-decoration:none; padding:.25rem .5rem;
  border-radius:6px; font-size:.92rem; }
nav a.aktiv { background:var(--akzent); color:var(--grund); }
nav p { color:var(--matt); font-size:.78rem; margin:1rem 0 .25rem .5rem; }
#suche { width:100%; padding:.5rem; margin-bottom:.75rem; border:1px solid var(--kante);
  border-radius:8px; background:var(--grund); color:var(--text); font:inherit; }
main { padding:1.5rem 2rem 4rem; max-width:62rem; min-width:0; overflow-wrap:anywhere; }
main a { color:var(--akzent); }
article[hidden] { display:none; }
table { border-collapse:collapse; display:block; overflow-x:auto; max-width:100%; }
th,td { border:1px solid var(--kante); padding:.3rem .55rem; text-align:left;
  vertical-align:top; overflow-wrap:normal; }
pre { background:var(--flaeche); padding:.75rem; border-radius:8px; overflow-x:auto; }
code { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.88em; }
img { max-width:100%; border:1px solid var(--kante); border-radius:8px; }
pre.mermaid { background:#fff; }
.treffer { padding:.5rem 0; border-bottom:1px solid var(--kante); }
.treffer small { color:var(--matt); display:block; }
@media (max-width:48rem) {
  .seite { display:block; }
  nav { position:static; height:auto; max-height:15rem; border-right:0; border-bottom:1px solid var(--kante); }
  main { padding:1rem 1rem 3rem; }
}
</style></head><body><div class="seite">
<nav><h1>MASCHERA Katalog</h1>
<input id="suche" type="search" placeholder="Im Katalog suchen" aria-label="Suchen">
<div id="liste">@@LISTE@@</div></nav>
<main><div id="ergebnis" hidden></div>@@ARTIKEL@@</main></div>
<script src="@@MERMAID@@"></script>
<script>
const artikel=[...document.querySelectorAll("article")];
const links=[...document.querySelectorAll("#liste a")];
const ergebnis=document.getElementById("ergebnis");
const suche=document.getElementById("suche");
if(window.mermaid)mermaid.initialize({startOnLoad:false,securityLevel:"strict",
  theme:matchMedia("(prefers-color-scheme: dark)").matches?"dark":"default"});
function zeige(id){
  const ziel=document.getElementById(id)||artikel[0];
  const a=ziel.closest("article")||ziel;
  ergebnis.hidden=true;
  artikel.forEach(x=>x.hidden=x!==a);
  links.forEach(l=>l.classList.toggle("aktiv",l.getAttribute("href")==="#"+a.id));
  if(window.mermaid)mermaid.run({nodes:a.querySelectorAll("pre.mermaid:not([data-processed])")});
  if(ziel!==a)ziel.scrollIntoView();else scrollTo(0,0);
}
function suchen(wort){
  wort=wort.trim().toLowerCase();
  if(wort.length<2){zeige(location.hash.slice(1)||artikel[0].id);return;}
  artikel.forEach(x=>x.hidden=true);
  ergebnis.hidden=false;ergebnis.replaceChildren();
  let n=0;
  for(const a of artikel)for(const e of a.querySelectorAll("h1,h2,h3,p,li,td")){
    const t=e.textContent;
    if(n>=100||!t.toLowerCase().includes(wort))continue;
    n++;
    const d=document.createElement("div");d.className="treffer";
    const k=document.createElement("a");k.href="#"+a.id;
    k.textContent=a.querySelector("h1").textContent;
    const s=document.createElement("small");s.textContent=t.slice(0,180);
    d.append(k,s);ergebnis.append(d);
  }
  if(!n)ergebnis.textContent="Keine Treffer.";
}
addEventListener("hashchange",()=>{suche.value="";zeige(location.hash.slice(1));});
suche.addEventListener("input",()=>suchen(suche.value));
zeige(location.hash.slice(1)||artikel[0].id);
</script></body></html>
"""


def html_bauen() -> Path:
    """`specs/html/index.html`: eine Datei mit Navigation und Suche."""
    from html import escape
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    standard = md.renderer.rules.get("fence")

    def fence(tokens, idx, options, env):
        t = tokens[idx]
        if t.info.strip() == "mermaid":
            return f'<pre class="mermaid">{escape(t.content)}</pre>'
        return standard(tokens, idx, options, env)
    md.renderer.rules["fence"] = fence

    specs = WURZEL / "specs"
    kapitel = sorted(specs.glob("*.md"), key=lambda p: (p.stem != "README", p.stem))
    erzeugt = sorted((specs / "erzeugt").glob("*.md"))

    def kennung(pfad: Path) -> str:
        return (("erzeugt-" if pfad.parent.name == "erzeugt" else "") + pfad.stem)

    def wandeln(pfad: Path) -> str:
        roh = pfad.read_text(encoding="utf-8")
        titel = roh.split("\n# ", 1)[1].split("\n")[0] if not roh.startswith("# ") \
            else roh[2:].split("\n")[0]
        inhalt = md.render(roh)
        inhalt = re.sub(r'href="erzeugt/([\w-]+)\.md[^"]*"', r'href="#erzeugt-\1"', inhalt)
        inhalt = re.sub(r'href="\.\./([\w-]+)\.md[^"]*"', r'href="#\1"', inhalt)
        inhalt = re.sub(r'href="([\w-]+)\.md[^"]*"',
                        (lambda t: f'href="#{"erzeugt-" if pfad.parent.name == "erzeugt" else ""}{t.group(1)}"'),
                        inhalt)
        inhalt = inhalt.replace('src="../app/', 'src="../../app/')
        return titel, f'<article id="{kennung(pfad)}" hidden>{inhalt}</article>'

    liste, artikel = [], []
    for gruppe, dateien in (("Kapitel", kapitel), ("Aus dem Code", erzeugt)):
        liste.append(f"<p>{gruppe}</p>")
        for pfad in dateien:
            titel, block = wandeln(pfad)
            name = "Übersicht" if pfad.stem == "README" else titel
            liste.append(f'<a href="#{kennung(pfad)}">{escape(name)}</a>')
            artikel.append(block)
    ziel = specs / "html" / "index.html"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(GRUNDFORM.replace("@@LISTE@@", "".join(liste))
                    .replace("@@ARTIKEL@@", "".join(artikel))
                    .replace("@@MERMAID@@", MERMAID), encoding="utf-8")
    return ziel


def release_befunde(geaendert: list[str], changelog: str, security: str,
                    fassung: str) -> list[str]:
    """Was vor einem Release am Katalog fehlt. Leer heisst: in Ordnung.

    Ansage 30.10.2026: vor JEDEM Release wird `specs/` nachgefuehrt. Ob ein
    Satz stimmt, sieht keine Maschine; sie sieht aber, ob jemand hingesehen
    hat. Ein Release ohne geaendertes Kapitel braucht deshalb im CHANGELOG
    die Zeile «Katalog unveraendert: <Grund>». Erzeugtes zaehlt nicht, das
    aendert sich von selbst.
    """
    befunde = []
    kapitel = any(re.fullmatch(r"specs/\d\d_\w+\.md", p) for p in geaendert)
    abschnitt = re.search(rf"^## {re.escape(fassung)}\b.*?(?=^## |\Z)",
                          changelog, re.S | re.M)
    begruendet = abschnitt and re.search(r"^Katalog unverändert: \S",
                                         abschnitt.group(0), re.M)
    if not kapitel and not begruendet:
        befunde.append(f"specs/: kein Kapitel seit dem letzten Release "
                       f"geaendert. Nachfuehren, oder im CHANGELOG zu "
                       f"{fassung}: «Katalog unverändert: <Grund>»")
    reihe = ".".join(fassung.split(".")[:2]) + ".x"
    for wort in ("ja", "yes"):
        if f"| {reihe} | {wort} |" not in security:
            befunde.append(f"SECURITY.md: Zeile «| {reihe} | {wort} |» fehlt")
    return befunde


def vorpruefung_stand() -> str:
    """Fassung und Commit: was geprueft wurde, ist genau das, was hinausgeht."""
    serve = (WURZEL / "app/serve.py").read_text(encoding="utf-8")
    fassung = re.search(r'^VERSION = "([^"]+)"', serve, re.M).group(1)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=WURZEL, text=True,
                            capture_output=True, check=True).stdout.strip()
    return f"{fassung} {commit}"


def main() -> int:
    if "--vorpruefung" in sys.argv:
        # Nicht in Git: `dist/` reist mit dem Projektordner, und ein Eintrag
        # in einer verfolgten Datei waere schon der naechste Commit.
        ziel = WURZEL / "dist" / "vorpruefung.txt"
        ziel.parent.mkdir(exist_ok=True)
        ziel.write_text(vorpruefung_stand() + "\n", encoding="utf-8")
        print(f"   Vorpruefung festgehalten: {vorpruefung_stand()[:20]}")
        return 0
    if "--release" in sys.argv:
        i = sys.argv.index("--release")
        basis, fassung = sys.argv[i + 1], sys.argv[i + 2]
        lauf = subprocess.run(["git", "diff", "--name-only", basis, "HEAD"],
                              cwd=WURZEL, capture_output=True, text=True,
                              check=True)
        befunde = release_befunde(
            lauf.stdout.split(),
            (WURZEL / "CHANGELOG.md").read_text(encoding="utf-8"),
            (WURZEL / "SECURITY.md").read_text(encoding="utf-8"), fassung)
        for b in befunde:
            print(b)
        return 1 if befunde else 0
    dateien = erzeuge()
    if "--pruefen" in sys.argv:
        alt = [n for n, inhalt in dateien.items()
               if not (ZIEL / n).is_file()
               or (ZIEL / n).read_text(encoding="utf-8") != inhalt]
        for n in alt:
            print(f"   veraltet: specs/erzeugt/{n}")
        return 1 if alt else 0
    ZIEL.mkdir(parents=True, exist_ok=True)
    for n, inhalt in dateien.items():
        (ZIEL / n).write_text(inhalt, encoding="utf-8")
        print(f"   {n}: {len(inhalt) // 1024} KB")
    if "--html" in sys.argv:
        print(f"   {html_bauen().relative_to(WURZEL)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
