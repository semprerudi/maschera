#!/usr/bin/env python3
"""Die Projektseite www.maschera.ch — spiegeln, vergleichen, hochladen.

    python3 tools/seite.py spiegeln      Live-Seite nach site/ holen (HTTPS, ohne Anmeldung)
    python3 tools/seite.py vergleichen   site/ gegen die Live-Seite halten (HTTPS)
    python3 tools/seite.py verbindung    FTPS-Anmeldung und Ordner pruefen, ohne etwas zu aendern
    python3 tools/seite.py hochladen     zeigt, was sich aendert (Trockenlauf)
    python3 tools/seite.py hochladen --ja    ... und laedt es nach Bestaetigung hoch

⚠️ **`site/` ist, was online steht.** Die Seite entsteht in Claude Design; ein
neuer Export wird nach `site/` entpackt, `vergleichen` zeigt den Unterschied,
`hochladen` bringt ihn auf den Server. Bis zum 3.10.2026 lag in `site/` ein
aelterer Entwurf mit anderer Ordnerordnung — ein Upload davon haette die
Live-Seite zerstoert. Deshalb gibt es `spiegeln`, und deshalb vergleicht
`hochladen` immer zuerst mit der Live-Seite.

⚠️ **Zugangsdaten stehen nie hier.** Sie kommen aus `~/.netrc` (Rechte 600),
Eintrag `machine maschera.ch` (oder den Servernamen). Das Skript liest sie mit dem `netrc`-Modul der
Standardbibliothek; sie erscheinen in keiner Ausgabe.

⚠️ **Nur verschluesselt.** Die Verbindung ist FTPS (explizites TLS). Bietet
der Server kein TLS an, bricht das Skript ab — es faellt NIE auf Klartext
zurueck, denn dann ginge das Passwort unverschluesselt ueber das Netz.
Die Zertifikatspruefung bleibt an.

⚠️ **Nichts wird geloescht.** Es gibt keinen Loeschbefehl in diesem Werkzeug.
Dateien auf dem Server, die nicht in `site/` liegen, bleiben unberuehrt.

⚠️ **Nur dieser Ordner.** Gearbeitet wird ausschliesslich in `FTP_ORDNER`.
Jede Datei wird unter einem Zwischennamen hochgeladen und dann umbenannt,
damit die Seite nie halb geschrieben ausgeliefert wird; `index.html` kommt
zuletzt, damit sie nie auf Dateien verweist, die noch fehlen.
"""
from __future__ import annotations

import argparse
import ftplib
import hashlib
import netrc
import os
import re
import shutil
import ssl
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath

WURZEL = Path(__file__).resolve().parent.parent
SEITE = "https://www.maschera.ch/"
# ⚠️ Der Servername, nicht die Domain: das Zertifikat des FTP-Servers gilt fuer
# `*.web.hostpoint.ch`, nicht fuer `maschera.ch`. Mit der Domain scheitert die
# Zertifikatspruefung (so gemessen am 3.10.2026) — und sie bleibt an. Den Namen
# nennt die Rueckaufloesung der Adresse von www.maschera.ch.
FTP_HOST = os.environ.get("MASCHERA_FTP_HOST", "sl2195.web.hostpoint.ch")
# Unter welchem Namen `~/.netrc` die Zugangsdaten fuehrt: der Servername oder
# die Domain, in dieser Reihenfolge.
NETRC_NAMEN = (FTP_HOST, "maschera.ch")
FTP_ORDNER = "/www/maschera"
SPRACHEN = ("de", "fr", "it", "en")
AGENT = "maschera-seite/1.0"


# ---------------------------------------------------------------- Entdecken

def entdecke(html: str, css: str, js: str) -> set[str]:
    """Alle Dateien, die die Seite beim Oeffnen braucht — relativ zur Wurzel.

    Gelesen wird, was `tests/test_webseite.py` ebenfalls liest: Verweise im
    HTML, `url()` im CSS, die Bildordner je Sprache aus `sprachen.js`. Die
    Bilder liegen je Sprache unter `bilder/<sprache>/`; das HTML nennt die
    deutschen, die anderen Sprachen bekommen dieselben Namen.
    """
    # Kommentare zuerst weg: im CSS steht der Schriftenblock auskommentiert
    # («bis sie geliefert sind»), und ein Verweis im Kommentar ist keine Datei,
    # die die Seite braucht.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js = re.sub(r"(?m)^\s*//.*$", "", js)
    pfade = {"index.html"}
    for u in re.findall(r'(?:src|srcset|href)="([^"#?]+)"', html):
        if re.match(r"(?:[a-z]+:)?//|mailto:|tel:|data:", u):
            continue
        pfade.add(u)
    for u in re.findall(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', css):
        if not re.match(r"(?:[a-z]+:)?//|data:", u):
            pfade.add(u)
    for u in re.findall(r'["\'](schriften/[\w./-]+)["\']', js):
        pfade.add(u)
    # Bilder je Sprache: aus dem Deutschen die Namen, fuer jede Sprache neu.
    for p in list(pfade):
        m = re.fullmatch(r"bilder/de/(.+)", p)
        if m:
            for s in SPRACHEN:
                pfade.add(f"bilder/{s}/{m.group(1)}")
    return {p for p in pfade if not p.endswith("/")}


# ------------------------------------------------------------------- Holen

def _hole(pfad: str) -> bytes | None:
    url = SEITE + ("" if pfad == "index.html" else pfad)
    anfrage = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(anfrage, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise SystemExit(f"{url}: HTTP {e.code}")
    except OSError as e:
        raise SystemExit(f"{url}: {e}")


def _sha(daten: bytes) -> str:
    return hashlib.sha256(daten).hexdigest()


def live_stand() -> dict[str, bytes]:
    """Die Live-Seite als {Pfad: Inhalt} — nur, was sie selbst nennt."""
    index = _hole("index.html")
    if index is None:
        raise SystemExit("index.html ist online nicht abrufbar.")
    html = index.decode("utf-8")
    css = (_hole("stil.css") or b"").decode("utf-8")
    js = (_hole("sprachen.js") or b"").decode("utf-8")
    stand = {"index.html": index}
    for p in sorted(entdecke(html, css, js)):
        if p in stand:
            continue
        d = _hole(p)
        if d is not None:
            stand[p] = d
    return stand


def lokal_stand(ordner: Path) -> dict[str, bytes]:
    if not (ordner / "index.html").is_file():
        raise SystemExit(f"{ordner}/index.html fehlt.")
    return {p.relative_to(ordner).as_posix(): p.read_bytes()
            for p in sorted(ordner.rglob("*")) if p.is_file()}


# ----------------------------------------------------------------- Vergleich

def vergleiche(lokal: dict[str, bytes], live: dict[str, bytes]):
    neu = sorted(p for p in lokal if p not in live)
    anders = sorted(p for p in lokal
                    if p in live and _sha(lokal[p]) != _sha(live[p]))
    gleich = sorted(p for p in lokal
                    if p in live and _sha(lokal[p]) == _sha(live[p]))
    # Online, aber nicht lokal: nur gemeldet, nie angefasst.
    nur_live = sorted(p for p in live if p not in lokal)
    return neu, anders, gleich, nur_live


def _reihenfolge(pfade: list[str]) -> list[str]:
    """Alles andere zuerst, `index.html` zuletzt."""
    return sorted(pfade, key=lambda p: (p == "index.html", p))


def _bericht(neu, anders, gleich, nur_live) -> None:
    print(f"   gleich:      {len(gleich)}")
    print(f"   neu:         {len(neu)}")
    print(f"   geaendert:   {len(anders)}")
    for p in neu:
        print(f"     + {p}")
    for p in anders:
        print(f"     ~ {p}")
    if nur_live:
        print(f"   nur online (bleiben unberuehrt): {len(nur_live)}")
        for p in nur_live[:10]:
            print(f"     · {p}")


# --------------------------------------------------------------------- FTPS

def verbinden() -> ftplib.FTP_TLS:
    try:
        daten = netrc.netrc()
        zugang = next((z for z in (daten.authenticators(n) for n in NETRC_NAMEN)
                       if z), None)
    except FileNotFoundError:
        raise SystemExit(
            "~/.netrc fehlt. Anlegen (mit eigenem Benutzer und Passwort):\n"
            f"  printf 'machine {NETRC_NAMEN[-1]}\\nlogin BENUTZER\\npassword "
            "PASSWORT\\n' >> ~/.netrc; chmod 600 ~/.netrc")
    except netrc.NetrcParseError as e:
        raise SystemExit(f"~/.netrc ist nicht lesbar oder zu offen: {e}")
    if not zugang:
        raise SystemExit("In ~/.netrc steht kein Eintrag `machine "
                         f"{NETRC_NAMEN[-1]}` (oder {NETRC_NAMEN[0]}).")
    benutzer, _, passwort = zugang
    ftps = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=60)
    try:
        ftps.connect(FTP_HOST, 21)
        ftps.auth()                       # explizites TLS, sonst Abbruch
    except (ssl.SSLError, ftplib.error_perm, OSError) as e:
        raise SystemExit(
            f"Keine verschluesselte Verbindung zu {FTP_HOST} ({type(e).__name__}"
            f": {e}). Es wird NICHT unverschluesselt weitergemacht.")
    ftps.login(benutzer, passwort)
    ftps.prot_p()                         # auch der Datenkanal verschluesselt
    try:
        ftps.cwd(FTP_ORDNER)
    except ftplib.error_perm:
        ftps.quit()
        raise SystemExit(f"Der Ordner {FTP_ORDNER} ist nicht erreichbar.")
    return ftps


def _stelle_ordner_sicher(ftps: ftplib.FTP_TLS, rel: str) -> None:
    teile = PurePosixPath(rel).parent.parts
    pfad = FTP_ORDNER
    for t in teile:
        pfad = f"{pfad}/{t}"
        try:
            ftps.cwd(pfad)
        except ftplib.error_perm:
            ftps.mkd(pfad)
    ftps.cwd(FTP_ORDNER)


def lade_hoch(ftps: ftplib.FTP_TLS, rel: str, daten: bytes) -> None:
    import io
    _stelle_ordner_sicher(ftps, rel)
    ziel = f"{FTP_ORDNER}/{rel}"
    zwischen = f"{FTP_ORDNER}/{PurePosixPath(rel).parent.as_posix()}/" \
               f".{PurePosixPath(rel).name}.neu".replace("/./", "/")
    ftps.storbinary(f"STOR {zwischen}", io.BytesIO(daten))
    ftps.rename(zwischen, ziel)


# ---------------------------------------------------------------- Befehle

def cmd_spiegeln(args) -> int:
    print("── Live-Seite holen")
    stand = live_stand()
    nach = Path(args.nach)
    with tempfile.TemporaryDirectory() as tmp:
        for rel, d in stand.items():
            ziel = Path(tmp) / rel
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_bytes(d)
        # Erst wenn alles da ist, wird `site/` ersetzt — nie halb.
        if nach.exists():
            for p in sorted(nach.rglob("*"), reverse=True):
                p.unlink() if p.is_file() or p.is_symlink() else p.rmdir()
        nach.mkdir(parents=True, exist_ok=True)
        for rel in stand:
            ziel = nach / rel
            ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(tmp) / rel, ziel)
    gesamt = sum(len(d) for d in stand.values())
    print(f"   {len(stand)} Dateien, {gesamt / 1e6:.1f} MB nach {nach}")
    return 0


def cmd_vergleichen(args) -> int:
    print("── site/ gegen die Live-Seite")
    neu, anders, gleich, nur_live = vergleiche(
        lokal_stand(Path(args.nach)), live_stand())
    _bericht(neu, anders, gleich, nur_live)
    return 0


def cmd_verbindung(args) -> int:
    print(f"── FTPS-Verbindung zu {FTP_HOST}, Ordner {FTP_ORDNER}")
    ftps = verbinden()
    eintraege = []
    ftps.retrlines("NLST", eintraege.append)
    print(f"   angemeldet, verschluesselt (TLS), {len(eintraege)} Eintraege im Ordner")
    for e in sorted(eintraege)[:15]:
        print(f"     {e}")
    ftps.quit()
    return 0


def cmd_hochladen(args) -> int:
    nach = Path(args.nach)
    lokal = lokal_stand(nach)
    print("── Vergleich mit der Live-Seite")
    live = live_stand()
    neu, anders, gleich, nur_live = vergleiche(lokal, live)
    _bericht(neu, anders, gleich, nur_live)
    liste = _reihenfolge(neu + anders)
    if not liste:
        print("   Nichts zu tun: online steht schon, was in site/ liegt.")
        return 0
    if not args.ja:
        print("\n   Trockenlauf. Hochladen mit:  python3 tools/seite.py hochladen --ja")
        return 0
    if input(f"\n{len(liste)} Datei(en) nach {FTP_HOST}{FTP_ORDNER} hochladen? "
             "[ja/N] ").strip().lower() != "ja":
        print("   Abgebrochen.")
        return 1
    ftps = verbinden()
    for rel in liste:
        lade_hoch(ftps, rel, lokal[rel])
        print(f"   hochgeladen: {rel}")
    ftps.quit()
    print("── Nachpruefung gegen die Live-Seite")
    fehler = []
    for rel in liste:
        d = _hole(rel)
        if d is None or _sha(d) != _sha(lokal[rel]):
            fehler.append(rel)
    if fehler:
        print("   ⚠️ online weicht ab (Browser-Zwischenspeicher oder Fehler):")
        for rel in fehler:
            print(f"     {rel}")
        return 1
    print(f"   ok    {len(liste)} Datei(en) online, Pruefsummen gleich")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("befehl", choices=["spiegeln", "vergleichen", "verbindung",
                                       "hochladen"])
    ap.add_argument("--nach", default=str(WURZEL / "site"),
                    help="der lokale Ordner (Vorgabe: site/)")
    ap.add_argument("--ja", action="store_true",
                    help="hochladen: wirklich ausfuehren (sonst Trockenlauf)")
    args = ap.parse_args()
    return {"spiegeln": cmd_spiegeln, "vergleichen": cmd_vergleichen,
            "verbindung": cmd_verbindung,
            "hochladen": cmd_hochladen}[args.befehl](args)


if __name__ == "__main__":
    sys.exit(main())
