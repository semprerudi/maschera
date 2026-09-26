#!/usr/bin/env python3
"""Die Bildschirmfotos der Projektseite erzeugen — vier Sprachen, hell und dunkel.

    python3 tools/schirmbilder.py --model runs/ch-v63b --nach dist/schirmbilder

Startet die Anwendung mit einer LEEREN Konfiguration, oeffnet sie in einem
Chromium ohne Fenster und spielt je Sprache den ganzen Ablauf durch: das
eingebaute Beispiel laden, maskieren, das Kontextmenue an einem Namen
oeffnen, in den Prompt uebernehmen, eine Vorlage waehlen, das Dienstmenue
aufklappen, eine Antwort einpflegen. Je Sprache entstehen unter
`<nach>/<sprache>/` diese Bilder, jedes hell und mit `-dunkel` dunkel:

    hero.png              die ganze Oberflaeche nach dem Ablauf, 2560×1372
    schritt1.png          01 Originaltext,                        874×656
    schritt2.png          02 Maskiert,                            874×656
    schritt3.png          Vokabular,                              874×656
    schritt4.png          03 Prompt mit Vorlage,                  874×656
    schritt4-auswahl.png  das aufgeklappte Dienstmenue,           448×461
    schritt5.png          05 Finaler Text,                        874×656
    herkunft-menu.png     Kontextmenue an einem Namen in 02,      894×754

Die Namen und Pixelgroessen sind die der Seite www.maschera.ch — dieselben
Dateien lassen sich dort je Sprache einsetzen.

⚠️ **Leere Konfiguration, mit Absicht.** Die Anwendung liest eigene
Regeln, Vorlagen und Vorlieben aus `~/.config/maschera/` — und die koennen
Namen tragen, interne Kuerzel, den Arbeitgeber. `XDG_CONFIG_HOME` zeigt
deshalb auf ein temporaeres Verzeichnis. Die EINE Vorlage in den Bildern ist
erfunden und steht unten; die Dienste sind die Vorgaben.

Braucht Playwright mit Chromium (`requirements-dev.txt`, danach einmal
`python3 -m playwright install chromium`), ImageMagick (`magick`) und das
Modell.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "dist" / "schirmbilder"
SPRACHEN = ("de", "fr", "it", "en")

# Doppelte Aufloesung: auf hochaufloesenden Bildschirmen sonst unscharf.
SKALA = 2
# Das Hauptbild zeigt die ganze Oberflaeche. Aufgenommen wird 1280×720:
# unter 44em (704 Punkte) HOEHE stapelt die Oberflaeche die Bereiche
# untereinander (`maschera.css`, einspaltige Ansicht). Danach auf die
# 2560×1372 Pixel der Seite zugeschnitten, von oben.
HERO = {"width": 1280, "height": 720}
HERO_PIXEL = "2560x1372"
# Fuer die Ausschnitte ein breiteres Fenster: jede Spalte misst dort gut
# 440 Punkte, und der Ausschnitt von 437 bleibt in seiner Spalte.
BREIT = {"width": 1400, "height": 1000}
# Ausschnitte in Punkten; mal SKALA gibt die Pixel der Seite.
AUSSCHNITT = (437, 328)          # 874×656
AUSWAHL_PIXEL = "448x461"        # das Dienstmenue, verkleinert
HERKUNFT = (447, 377)            # 894×754

# Eine erfundene Vorlage und eine Antwort, wie ein Dienst sie gaebe — je
# Sprache. Der Brief an die Absenderin siezt: es ist ein Geschaeftsbrief.
VORLAGE = {
    "de": ("Freundlich antworten",
           "Antworte freundlich und kurz. Sag, dass wir die Beschwerde "
           "prüfen und uns bis Ende Monat melden."),
    "fr": ("Répondre aimablement",
           "Réponds aimablement et brièvement. Dis que nous examinons la "
           "réclamation et que nous répondrons d’ici la fin du mois."),
    "it": ("Rispondere gentilmente",
           "Rispondi in modo gentile e breve. Di’ che esaminiamo il reclamo "
           "e che ci faremo sentire entro fine mese."),
    "en": ("Reply kindly",
           "Reply kindly and briefly. Say that we are looking into the "
           "complaint and will get back by the end of the month."),
}
ANTWORT = {
    "de": ("Sehr geehrte Frau {name}\n\nVielen Dank für Ihr Schreiben vom "
           "{datum}. Wir prüfen Ihre Beschwerde zum Dossier {fall} und "
           "melden uns bis Ende Monat.\n\nFreundliche Grüsse"),
    "fr": ("Madame {name},\n\nNous vous remercions de votre courrier du "
           "{datum}. Nous examinons votre réclamation concernant le dossier "
           "{fall} et vous répondrons d’ici la fin du mois.\n\n"
           "Meilleures salutations"),
    "it": ("Gentile signora {name},\n\nLa ringraziamo per la sua lettera del "
           "{datum}. Stiamo esaminando il suo reclamo relativo alla pratica "
           "{fall} e ci faremo sentire entro fine mese.\n\nCordiali saluti"),
    "en": ("Dear Ms {name},\n\nThank you for your letter of {datum}. We are "
           "looking into your complaint regarding case {fall} and will get "
           "back to you by the end of the month.\n\nKind regards"),
}


def warten_auf_dienst(adresse: str, sekunden: int = 180) -> None:
    ende = time.time() + sekunden
    while time.time() < ende:
        try:
            with urllib.request.urlopen(adresse + "/api/zustand",
                                        timeout=2) as r:
                if r.status == 200:
                    return
        except OSError:
            pass
        time.sleep(1)
    raise SystemExit(f"Der Dienst antwortet nach {sekunden} s nicht.")


def vorlage_setzen(adresse: str, sprache: str) -> None:
    """Genau eine Vorlage, in der Sprache der Aufnahme — ueber die API."""
    name, text = VORLAGE[sprache]
    anfrage = urllib.request.Request(
        adresse + "/api/vorlagen", method="PUT",
        data=json.dumps({"vorlagen": [{"name": name, "text": text}]})
        .encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=10) as r:
        if r.status != 200:
            raise SystemExit(f"Vorlage nicht gesetzt: HTTP {r.status}")


def antwort_aus(maskiert: str, sprache: str) -> str:
    """Eine Antwort, wie ein Dienst sie gaebe — mit den Platzhaltern."""
    platz = list(dict.fromkeys(re.findall(r"\[[A-Z_]+_\d+\]", maskiert)))
    def erster(vorsatz: str) -> str:
        return next((p for p in platz if p.startswith("[" + vorsatz)), "")
    return ANTWORT[sprache].format(name=erster("FULLNAME"),
                                   datum=erster("DATE"),
                                   fall=erster("CASE_ID"))


def ausschnitt(seite, pfad: Path, kasten: dict, masse: tuple,
               dx: float = 0, dy: float = 0) -> None:
    breite, hoehe = masse
    seite.screenshot(path=str(pfad), clip={
        "x": kasten["x"] + dx, "y": kasten["y"] + dy,
        "width": breite, "height": hoehe})


def aufnehmen(seite, ordner: Path, sprache: str, zusatz: str) -> None:
    """Ein Durchgang: eine Sprache, ein Thema. `zusatz` ist "" oder "-dunkel"."""
    def datei(name: str) -> Path:
        return ordner / f"{name}{zusatz}.png"

    seite.set_viewport_size(BREIT)
    seite.click(f"[data-sprache='{sprache}']")
    # Drei Spalten von Anfang an, wie im Hauptbild — sonst klappt die
    # dritte erst mit der Uebernahme auf, und 01 und 02 sind doppelt breit.
    seite.click("#knopf-ausklappen")
    seite.wait_for_selector("#knopf-beispiel:not([disabled])")
    seite.click("#knopf-beispiel")
    seite.wait_for_selector("#knopf-maskieren:not([disabled])")
    seite.evaluate("window.scrollTo(0, 0)")
    ausschnitt(seite, datei("schritt1"),
               seite.locator("#b01").bounding_box(), AUSSCHNITT)

    seite.click("#knopf-maskieren")
    seite.wait_for_selector("#knopf-uebernahme:not([disabled])",
                            timeout=180_000)
    seite.wait_for_function(
        "document.querySelector('#legende') &&"
        " document.querySelector('#legende').children.length > 0")
    ausschnitt(seite, datei("schritt2"),
               seite.locator("#b02").bounding_box(), AUSSCHNITT)
    seite.locator("#bvok").scroll_into_view_if_needed()
    ausschnitt(seite, datei("schritt3"),
               seite.locator("#bvok").bounding_box(), AUSSCHNITT)

    # Das Kontextmenue an einem Namen zeigt die Herkunft der Fundstelle.
    seite.evaluate("window.scrollTo(0, 0)")
    name = seite.locator("#maskiert .ph[data-ph^='[FULLNAME']").first
    name.click(button="right")
    seite.wait_for_selector("#kontext:not([hidden])")
    ausschnitt(seite, datei("herkunft-menu"),
               seite.locator("#b02").bounding_box(), HERKUNFT)
    seite.keyboard.press("Escape")

    # Das Prompt-Feld erscheint erst mit der Uebernahme.
    seite.click("#knopf-uebernahme")
    seite.wait_for_selector("#prompt", state="visible")
    seite.click("#knopf-vorlagen")
    seite.locator("#vorlagen-liste button.waehlen").first.click()
    seite.wait_for_selector("#knopf-kopieren-hinaus:not([disabled])")
    seite.locator("#b03").scroll_into_view_if_needed()
    ausschnitt(seite, datei("schritt4"),
               seite.locator("#b03").bounding_box(), AUSSCHNITT)

    # Das aufgeklappte Dienstmenue — ein kleiner Ausschnitt um den Knopf.
    seite.click("#knopf-dienstmenu")
    seite.wait_for_selector("#dienstmenu:not([hidden])")
    # Knopf samt Pfeil ist breiter als der Ausschnitt der Seite: den ganzen
    # Knopf aufnehmen, im Seitenverhaeltnis 448:461, und in `zuschneiden()`
    # auf die Pixel der Seite verkleinern.
    knopf = seite.locator("#knopf-senden").bounding_box()
    pfeil = seite.locator("#knopf-dienstmenu").bounding_box()
    links = knopf["x"] - 14
    breite = pfeil["x"] + pfeil["width"] + 10 - links
    seite.screenshot(path=str(datei("schritt4-auswahl")), clip={
        "x": links, "y": knopf["y"] - 10,
        "width": breite, "height": breite * 461 / 448})
    seite.keyboard.press("Escape")
    seite.evaluate("document.body.click()")

    maskiert = seite.locator("#b02").inner_text()
    seite.fill("#antwort04", antwort_aus(maskiert, sprache))
    seite.wait_for_selector("#knopf-einpflegen04:not([disabled])")
    seite.click("#knopf-einpflegen04")
    seite.wait_for_selector("#knopf-final-kopieren:not([disabled])",
                            timeout=60_000)
    seite.locator("#b05").scroll_into_view_if_needed()
    ausschnitt(seite, datei("schritt5"),
               seite.locator("#b05").bounding_box(), AUSSCHNITT)

    seite.set_viewport_size(HERO)
    seite.evaluate("window.scrollTo(0, 0)")
    seite.screenshot(path=str(datei("hero")))


def zuschneiden(ordner: Path) -> None:
    """Auf die Pixel der Seite: das Dienstmenue (verkleinert) und das
    Hauptbild (aufgenommen 1280×720, gezeigt 2560×1372)."""
    for bild in ordner.glob("schritt4-auswahl*.png"):
        subprocess.run(["magick", str(bild), "-resize",
                        AUSWAHL_PIXEL + "!", str(bild)], check=True)
    for bild in ordner.glob("hero*.png"):
        subprocess.run(["magick", str(bild), "-crop", HERO_PIXEL + "+0+0",
                        "+repage", str(bild)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default="runs/ch-v63b")
    ap.add_argument("--port", type=int, default=4199)
    ap.add_argument("--nach", default=str(ZIEL),
                    help="Zielordner, darunter je Sprache ein Ordner")
    ap.add_argument("--sprachen", default=",".join(SPRACHEN))
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright fehlt: pip install playwright, dann "
                         "python3 -m playwright install chromium")
    if shutil.which("magick") is None:
        raise SystemExit("ImageMagick (`magick`) fehlt.")

    adresse = f"http://127.0.0.1:{args.port}"
    sprachen = [s for s in args.sprachen.split(",") if s]
    with tempfile.TemporaryDirectory() as leer:
        umgebung = {**os.environ, "XDG_CONFIG_HOME": leer,
                    "PYTHONUNBUFFERED": "1"}
        dienst = subprocess.Popen(
            [sys.executable, str(WURZEL / "app" / "app.py"),
             "--model", args.model, "--host", "127.0.0.1",
             "--port", str(args.port)],
            cwd=WURZEL, env=umgebung,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            warten_auf_dienst(adresse)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                for sprache in sprachen:
                    ordner = Path(args.nach) / sprache
                    ordner.mkdir(parents=True, exist_ok=True)
                    vorlage_setzen(adresse, sprache)
                    for zusatz, schema in (("", "light"),
                                           ("-dunkel", "dark")):
                        kontext = browser.new_context(
                            viewport=BREIT, color_scheme=schema,
                            device_scale_factor=SKALA)
                        seite = kontext.new_page()
                        seite.goto(adresse)
                        aufnehmen(seite, ordner, sprache, zusatz)
                        kontext.close()
                    zuschneiden(ordner)
                    print(f"   {sprache}: {len(list(ordner.glob('*.png')))} "
                          f"Bilder nach {ordner}")
                browser.close()
        finally:
            dienst.terminate()
            dienst.wait(timeout=30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
