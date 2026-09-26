#!/usr/bin/env python3
"""Firmennamen aus Zefix ueber LINDAS holen (SPEC §6, offener Punkt 4).

    python3 tools/fetch_zefix.py                    # 20000 Namen
    python3 tools/fetch_zefix.py --limit 50000
    python3 tools/fetch_zefix.py --query            # nur die Abfrage zeigen

Quelle: https://register.ld.admin.ch/.well-known/dataset/foj-zefix
Endpunkt: https://register.ld.admin.ch/sparql/
Graph: https://lindas.admin.ch/foj/zefix
Publiziert vom Eidgenoessischen Amt fuer das Handelsregister (EHRA).

**Es werden AUSSCHLIESSLICH Firmennamen geholt**, keine Adressen, keine UID,
keine Organe, keine Personen. Fuer die Templategenerierung wird die
Namensvielfalt gebraucht — alles andere waere Daten sammeln ohne Zweck, und
das waere bei einem Werkzeug zur Pseudonymisierung besonders schraeg.

Nicht gegen den Endpunkt getestet: die Entwicklungsumgebung erreicht admin.ch
nicht. Schlaegt die Abfrage fehl, mit --query die SPARQL-Abfrage ausgeben und
unter https://register.ld.admin.ch/sparql/ von Hand pruefen.
"""

from __future__ import annotations

import argparse
import csv
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Zwei moegliche Endpunkte. Der Datensatzbeschrieb nennt
# register.ld.admin.ch, die Daten liegen aber im LINDAS-Graphen — deshalb
# beide versuchen statt zu raten, lindas.admin.ch/query zuerst.
ENDPOINTS = [
    "https://lindas.admin.ch/query",
    "https://register.ld.admin.ch/sparql/",
]
OUT = Path(__file__).resolve().parent.parent / "packs/ch/nomenclatures/raw/zefix.csv"

# Gegen den Graphen geprueft (--probe):
#   Typ       https://schema.ld.admin.ch/ZefixOrganisation   rund 790'000 Stueck
#   Name      schema:legalName                               genau einer je Einheit
# `schema:name` gibt es auch an DefinedTerm und PostalAddress — deshalb
# legalName, nicht name.
#
# ORDER BY MD5 statt blossem LIMIT: ohne Sortierung liefert der Endpunkt eine
# beliebige, in der Praxis oft alphabetische Scheibe — dann bestuenden die
# Trainingsdaten aus lauter Firmen mit A. Der Hash streut gleichmaessig ueber
# den ganzen Bestand und bleibt bei jedem Lauf dieselbe Auswahl.
QUERY = """
PREFIX schema: <http://schema.org/>

SELECT ?name
FROM <https://lindas.admin.ch/foj/zefix>
WHERE {
  ?org a <https://schema.ld.admin.ch/ZefixOrganisation> ;
       schema:legalName ?name .
}
ORDER BY MD5(STR(?org))
LIMIT %d
"""

QUERY_ALL = """
PREFIX schema: <http://schema.org/>

SELECT ?name
FROM <https://lindas.admin.ch/foj/zefix>
WHERE {
  ?org a <https://schema.ld.admin.ch/ZefixOrganisation> ;
       schema:legalName ?name .
}
"""

# Der Graph fuehrt dcterms:license. Damit laesst sich die Lizenzfrage
# beantworten statt vermuten.
LICENSE = """
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX schema: <http://schema.org/>

SELECT ?p ?o
FROM <https://lindas.admin.ch/foj/zefix>
WHERE {
  ?s ?p ?o .
  VALUES ?p { dct:license dct:rights dct:publisher dct:creator
              schema:publisher dct:accrualPeriodicity dct:issued dct:modified }
}
"""


PROBE = """
SELECT ?t (COUNT(?s) AS ?anzahl)
FROM <https://lindas.admin.ch/foj/zefix>
WHERE { ?s a ?t }
GROUP BY ?t
ORDER BY DESC(?anzahl)
LIMIT 40
"""

PREDICATES = """
SELECT ?p (COUNT(*) AS ?anzahl)
FROM <https://lindas.admin.ch/foj/zefix>
WHERE { ?s ?p ?o }
GROUP BY ?p
ORDER BY DESC(?anzahl)
LIMIT 60
"""


def ask(query: str, timeout: int, verbose: bool = True) -> list[list[str]]:
    """Abfrage an die Endpunkte schicken, GET und POST, bis einer antwortet.

    Gibt die Fehlermeldung des Servers WEITER. Ein SPARQL-Endpunkt schreibt bei
    400 fast immer hin, was ihm nicht passt — diese Meldung zu verschlucken
    kostet mehr Zeit als jede Fehlersuche.
    """
    problems: list[str] = []
    for endpoint in ENDPOINTS:
        for method in ("POST", "GET"):
            try:
                headers = {
                    "Accept": "text/csv",
                    "User-Agent": "MASCHERA/0.1 (Nomenklaturaufbau; CH Country Pack)",
                }
                if method == "POST":
                    data = urllib.parse.urlencode({"query": query}).encode()
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
                    request = urllib.request.Request(endpoint, data=data,
                                                     headers=headers)
                else:
                    url = endpoint + "?" + urllib.parse.urlencode({"query": query})
                    request = urllib.request.Request(url, headers=headers)

                with urllib.request.urlopen(request, timeout=timeout) as response:
                    body = response.read().decode("utf-8", errors="replace")
                if verbose:
                    print(f"  Antwort von {endpoint} ({method})")
                return list(csv.reader(body.splitlines()))

            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:600]
                except Exception:
                    pass
                problems.append(f"{endpoint} [{method}] {exc.code}: {detail.strip()}")
            except Exception as exc:
                problems.append(f"{endpoint} [{method}] {exc}")

    print("Kein Endpunkt hat geantwortet:\n")
    for p in problems:
        print(f"  {p}\n")
    raise SystemExit(1)


def run(limit: int, timeout: int) -> list[str]:
    rows = ask(QUERY_ALL if limit <= 0 else QUERY % limit, timeout)
    if not rows:
        raise SystemExit("Antwort leer")
    header, *data = rows
    return [r[0].strip() for r in data if r and r[0].strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20000)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--query", action="store_true", help="nur die Abfrage zeigen")
    ap.add_argument("--all", action="store_true",
                    help="alle 791'231 Firmennamen holen statt einer Stichprobe")
    ap.add_argument("--license", action="store_true",
                    help="Lizenz und Herausgeber aus dem Graphen abfragen")
    ap.add_argument("--probe", action="store_true",
                    help="zeigen, welche Typen und Praedikate der Graph fuehrt")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    if args.query:
        print(QUERY % args.limit)
        print(f"Endpunkte: {ENDPOINTS}")
        return 0

    if args.license:
        print("Lizenz- und Herausgeberangaben im Graphen:\n")
        for row in ask(LICENSE, args.timeout)[1:]:
            print(f"   {row[0].rsplit('/', 1)[-1]:<22} {row[1]}")
        return 0

    if args.probe:
        print("Typen im Graph:")
        for row in ask(PROBE, args.timeout)[1:]:
            print(f"   {row[1]:>9}  {row[0]}")
        print("\nPraedikate im Graph:")
        for row in ask(PREDICATES, args.timeout, verbose=False)[1:]:
            print(f"   {row[1]:>9}  {row[0]}")
        return 0

    limit = 0 if args.all else args.limit
    print("Frage alle Firmennamen ab (791'231, dauert) …" if limit <= 0
          else f"Frage {limit} Firmennamen ab (gestreut ueber den Bestand) …")
    try:
        names = run(limit, args.timeout)
    except SystemExit:
        print("Naechster Schritt — schauen, was der Graph tatsaechlich fuehrt:")
        print("  python3 tools/fetch_zefix.py --probe")
        return 1

    unique = sorted(set(names))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name"])
        for n in unique:
            writer.writerow([n])

    print(f"{len(unique)} verschiedene Firmennamen -> {path}")
    print(f"Beispiele: {unique[:5]}")
    print("\nDanach:  python3 packs/ch/nomenclatures/build.py --build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
