"""Einstellungen des Anwenders — Adresse, Port, Dienste, Fensterschalter.

    from core import einstellungen
    e = einstellungen.lade()
    einstellungen.speichere(e)      # prueft, bevor es schreibt

Aufbewahrt in `~/.config/maschera/einstellungen.json`.

Der Grundsatz dazu: **Nichts wird geschrieben ausser den Einstellungen des
Anwenders**, alle nach `~/.config/maschera/`, alle nur auf ausdruecklichen
Befehl. Kein Dokumentinhalt, kein Woerterbuch, kein Protokoll.

**Keine Geheimnisse.** Es gibt kein Feld fuer Endpunkt, Modell oder
API-Schluessel: MASCHERA sendet nichts selbst (`/api/senden` gibt es
nicht), und ein Schluessel laege sonst im Klartext auf der Platte, ohne
etwas zu bewirken.
"""
from __future__ import annotations

import json

from core import hinweise, pfade

PFAD = pfade.konfig("einstellungen.json")

MAX_DIENSTE = 20
ERLAUBTE_SCHEMATA = ("https://", "http://")

# Die erlaubten Schriftgroessen. Dieselbe Liste steht in `maschera.js`,
# im Auswahlfeld von `index.html` und im Vertrag `docs/API_OBERFLAECHE.md`;
# `tests/test_api.py` Punkt 17 haelt die vier Stellen zusammen.
GROESSEN = (70, 80, 90, 100, 110, 125, 140)
SCHRIFTEN = ("werk", "serif", "sans", "mono")

# Die vier Bediensprachen, in derselben Reihenfolge wie im Kopf der
# Oberflaeche. Es ist die Sprache der BEDIENUNG, nicht die des Dokuments.
#
# Hier gilt nicht «unbekannte Sprache -> 400»: das gilt fuer die Maskierung,
# wo eine falsche Amtsform ein fachlicher Fehler ist. Eine unbekannte
# Bediensprache ist eine kaputte Einstellungsdatei, und `lade()` faellt dann
# fuer die ganze Datei auf die Vorgabe zurueck.
SPRACHEN = ("de", "fr", "it", "en")

# Zwei Fenstermodi: `voll` ist das normale Fenster, `widget` dasselbe
# Fenster schmal, einspaltig und immer im Vordergrund.
#
# Kein echtes Plattform-Widget: das wuerde vier Technologien verlangen
# (MSIX mit Adaptive Cards, WidgetKit, ein QML-Plasmoid, eine
# GNOME-Erweiterung), und die zwei grossen erlauben weder Texteingabe noch
# eigenen Webinhalt. Ein zweiter Fenstermodus ist eine Technologie und
# ueberall gleich.
#
# Die Mindestbreite ist gemessen: bei 100 % Schrift braucht der Inhalt
# 378 px, darunter entsteht ein waagrechter Rollbalken. Sie gilt bei 100 %
# Schrift — bei 140 % waechst jedes `rem`, und dieselbe Breite reicht nicht
# mehr. Eine feste Untergrenze kann das nicht auffangen, weil die Schrift
# erst nach dem Oeffnen geaendert wird.
FENSTERMODI = ("voll", "widget")

# Zwei Zahlen, die Verschiedenes messen:
#
# GEMESSENE_MINDESTBREITE  was der INHALT braucht (Viewport)
# WIDGET_RAHMEN            was das Fenster zusaetzlich verbraucht
#                          (Rahmen, senkrechter Rollbalken)
# WIDGET_BREITE            die Summe — was `create_window` bekommt
#
# Die Summe wird gerechnet und nicht hingeschrieben; eine dritte Zahl waere
# die, die man beim naechsten Mal vergisst.
GEMESSENE_MINDESTBREITE = 378
WIDGET_RAHMEN = 32
WIDGET_BREITE = GEMESSENE_MINDESTBREITE + WIDGET_RAHMEN

# Die einzige Quelle fuer den Vorgabeport. Keine andere Datei nennt die
# Zahl; `tests/test_fenster.py` Punkt 6 haelt das fest.
#
# Warum 4141: 5005 ist in `/etc/services` `avt-profile-2` und in der Praxis
# der uebliche Port fuer Java-Fernfehlersuche (JDWP). 5555 waere
# `personal-agent` und in der Praxis ADB ueber TCP. 4141 traegt `oirtgsvc`,
# einen toten Eintrag, und liegt unter der fluechtigen Portspanne
# (32768-60999). Merkhilfe: +41, doppelt.
VORGABE_PORT = 4141

# Drei Stufen, «automatisch» ist die Vorgabe: die Oberflaeche setzt dann
# nichts und laesst `prefers-color-scheme` entscheiden. Das ist nicht
# dasselbe wie «hell» — wer ausdruecklich hell waehlt, bekommt hell, auch
# wenn das System nachts umschaltet.
THEMEN = ("automatisch", "hell", "dunkel")

VORGABE = {
    "adresse": "127.0.0.1",
    "port": VORGABE_PORT,
    "eigenes_fenster": True,
    "dienst": "claude",
    "schriftgroesse": 100,
    "schriftart": "werk",
    "schrift_ueberall": False,
    # Die Vorgabe greift nur beim allerersten Start. Danach steht hier, was
    # der Anwender zuletzt gewaehlt hat.
    "sprache": "de",
    # `tray` und das schmale Fenster sind vorgabemaessig AN — unter Linux
    # und Windows so gewuenscht, damit sie ab dem ersten Start wirken.
    # Tragbar ist das nur, weil das X nie ins Leere versteckt: gibt es kein
    # Symbol (GNOME ohne AppIndicator-Erweiterung, `pystray` gescheitert),
    # gibt `beim_schliessen` in `app/fenster.py` das Schliessen frei.
    # `tests/test_fenster.py` Punkt 17 prueft genau diesen Fall.
    "tray": True,
    "fenstermodus": "widget",
    "thema": "automatisch",
    "dienste": [
        {"id": "claude", "name": "Claude", "url": "https://claude.ai/new"},
        {"id": "chatgpt", "name": "ChatGPT", "url": "https://chatgpt.com/"},
        {"id": "gemini", "name": "Gemini",
         "url": "https://gemini.google.com/app"},
        {"id": "copilot", "name": "Copilot",
         "url": "https://copilot.microsoft.com/"},
    ],
}


class Abgelehnt(hinweise.Abgelehnt):
    """Eine Einstellung, die so nicht gespeichert werden darf."""


def _dienste(roh) -> list[dict]:
    """WACHE — das Schema der Adresse wird geprueft, nicht nur die Form.

    Diese URL landet in `window.open`. Ein Eintrag `javascript:…` liefe dort
    im Zusammenhang der eigenen Seite, also mit Zugriff auf Woerterbuch und
    Originaltext. Erlaubt sind `https://` und `http://`, sonst nichts.
    """
    if not isinstance(roh, list):
        raise Abgelehnt("Feld `dienste` ist keine Liste.",
                        schluessel="dienste_keine_liste")
    if len(roh) > MAX_DIENSTE:
        raise Abgelehnt(f"Hoechstens {MAX_DIENSTE} Dienste.",
                        schluessel="dienste_zu_viele", hoechstens=MAX_DIENSTE)
    sauber: list[dict] = []
    kennungen: set[str] = set()
    for i, d in enumerate(roh, 1):
        if not isinstance(d, dict):
            raise Abgelehnt(f"Dienst {i} ist kein Objekt.",
                            schluessel="dienst_kein_objekt", nummer=i)
        name = d.get("name")
        url = d.get("url")
        kennung = d.get("id") or ""
        if not isinstance(name, str) or not name.strip():
            raise Abgelehnt(f"Dienst {i} hat keinen Namen.",
                            schluessel="dienst_ohne_namen", nummer=i)
        if not isinstance(url, str) or not url.strip():
            raise Abgelehnt(f"Dienst {name} hat keine Adresse.",
                            schluessel="dienst_ohne_adresse", name=name)
        url = url.strip()
        if not url.lower().startswith(ERLAUBTE_SCHEMATA):
            raise Abgelehnt(
                f"Dienst {name}: nur https:// oder http://, "
                f"nicht {url[:24]!r}",
                schluessel="dienst_schema", name=name, adresse=url[:24])
        if not isinstance(kennung, str) or not kennung.strip():
            kennung = name.strip().lower().replace(" ", "-")
        kennung = kennung.strip()
        if kennung in kennungen:
            raise Abgelehnt(f"Kennung zweimal vergeben: {kennung}",
                            schluessel="dienst_kennung_doppelt", kennung=kennung)
        kennungen.add(kennung)
        sauber.append({"id": kennung, "name": name.strip(), "url": url})
    return sauber


def pruefe(roh) -> dict:
    if not isinstance(roh, dict):
        raise Abgelehnt("Kein Objekt.", schluessel="einst_kein_objekt")

    adresse = roh.get("adresse", VORGABE["adresse"])
    if not isinstance(adresse, str) or not adresse.strip():
        raise Abgelehnt("Feld `adresse` fehlt oder ist leer.",
                        schluessel="adresse_fehlt")
    if len(adresse) > 255:
        raise Abgelehnt("Adresse laenger als 255 Zeichen.",
                        schluessel="adresse_zu_lang", hoechstens=255)

    port = roh.get("port", VORGABE["port"])
    if isinstance(port, str) and port.strip().isdigit():
        port = int(port)
    if not isinstance(port, int) or isinstance(port, bool) \
            or not 1 <= port <= 65535:
        raise Abgelehnt(f"Port ausserhalb 1–65535: {port!r}",
                        schluessel="port_ausserhalb", port=repr(port))

    fenster = roh.get("eigenes_fenster", VORGABE["eigenes_fenster"])
    if not isinstance(fenster, bool):
        raise Abgelehnt("Feld `eigenes_fenster` ist kein Wahrheitswert.",
                        schluessel="fenster_kein_wahrheitswert")

    groesse = roh.get("schriftgroesse", VORGABE["schriftgroesse"])
    if isinstance(groesse, str) and groesse.strip().isdigit():
        groesse = int(groesse)
    if groesse not in GROESSEN:
        raise Abgelehnt(f"Schriftgroesse nicht in {GROESSEN}: {groesse!r}",
                        schluessel="schriftgroesse_unbekannt", wert=repr(groesse),
                        moeglich=", ".join(str(g) for g in GROESSEN))

    schrift = roh.get("schriftart", VORGABE["schriftart"])
    if schrift not in SCHRIFTEN:
        raise Abgelehnt(f"Schriftart nicht in {SCHRIFTEN}: {schrift!r}",
                        schluessel="schriftart_unbekannt", wert=repr(schrift),
                        moeglich=", ".join(SCHRIFTEN))

    ueberall = roh.get("schrift_ueberall", VORGABE["schrift_ueberall"])
    if not isinstance(ueberall, bool):
        raise Abgelehnt("Feld `schrift_ueberall` ist kein Wahrheitswert.",
                        schluessel="schrift_ueberall_kein_wahrheitswert")

    sprache = roh.get("sprache", VORGABE["sprache"])
    if sprache not in SPRACHEN:
        # Eigener Schluessel, nicht `sprache_unbekannt`: jener gilt fuer die
        # Sprache des DOKUMENTS und endet mit 400. Zwei Faelle auf einem Schluessel
        # haetten in einem davon das Falsche gesagt.
        raise Abgelehnt(f"Bediensprache nicht in {SPRACHEN}: {sprache!r}",
                        schluessel="oberflaechensprache_unbekannt",
                        wert=repr(sprache),
                        moeglich=", ".join(SPRACHEN))

    tray = roh.get("tray", VORGABE["tray"])
    if not isinstance(tray, bool):
        raise Abgelehnt("Feld `tray` ist kein Wahrheitswert.",
                        schluessel="tray_kein_wahrheitswert")

    modus = roh.get("fenstermodus", VORGABE["fenstermodus"])
    if modus not in FENSTERMODI:
        raise Abgelehnt(f"Fenstermodus nicht in {FENSTERMODI}: {modus!r}",
                        schluessel="fenstermodus_unbekannt", wert=repr(modus),
                        moeglich=", ".join(FENSTERMODI))

    thema = roh.get("thema", VORGABE["thema"])
    if thema not in THEMEN:
        raise Abgelehnt(f"Thema nicht in {THEMEN}: {thema!r}",
                        schluessel="thema_unbekannt", wert=repr(thema),
                        moeglich=", ".join(THEMEN))

    dienste = _dienste(roh.get("dienste", VORGABE["dienste"]))

    # ⚠️ Der zuletzt gewaehlte Dienst muss es noch geben. Wer ihn geloescht
    # hat, bekommt den ersten — sonst zeigte der Sendeknopf einen Namen, zu
    # dem keine Adresse mehr gehoert, und der Klick ginge ins Leere.
    dienst = roh.get("dienst") or ""
    kennungen = [d["id"] for d in dienste]
    if dienst not in kennungen:
        dienst = kennungen[0] if kennungen else ""

    return {
        "adresse": adresse.strip(),
        "port": port,
        "eigenes_fenster": fenster,
        "dienst": dienst,
        "schriftgroesse": groesse,
        "schriftart": schrift,
        "schrift_ueberall": ueberall,
        "sprache": sprache,
        "tray": tray,
        "fenstermodus": modus,
        "thema": thema,
        "dienste": dienste,
    }


def lade() -> dict:
    """Gespeicherte Einstellungen. Fehlt oder kaputt -> die Vorgabe.

    Eine verdorbene Datei macht das Werkzeug nicht unbenutzbar: sie liefert
    die Vorgabe, und die Oberflaeche laeuft mit den vorgegebenen Diensten
    weiter.
    """
    try:
        roh = json.loads(PFAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return pruefe(VORGABE)
    try:
        return pruefe(roh)
    except Abgelehnt:
        return pruefe(VORGABE)


def speichere(roh) -> dict:
    sauber = pruefe(roh)
    PFAD.parent.mkdir(parents=True, exist_ok=True)
    PFAD.write_text(json.dumps(sauber, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return sauber
