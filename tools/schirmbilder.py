#!/usr/bin/env python3
"""Die Bildschirmfotos fuer die Projektseite — immer dieselben 24 Bilder.

    python3 tools/schirmbilder.py --model runs/ch-v63b --nach dist/schirmbilder

Startet die Anwendung mit einer LEEREN Konfiguration, oeffnet sie in einem
Chromium ohne Fenster und spielt je Sprache (de, fr, it, en) und je Thema
(hell, dunkel) den immer gleichen Ablauf durch. Es entstehen drei Bildsorten,
je acht Bilder, plus ein ZIP mit allen:

    hauptansicht-<sprache>[-dunkel].png    die ganze Oberflaeche, 2000×1178
    maskierung-<sprache>[-dunkel].png      Spalte 02 mit dem Menue an einer
                                           Maske, ca. 855×945
    ki-menue-<sprache>[-dunkel].png        der Knopf «Kopieren und … oeffnen»
                                           mit dem aufgeklappten Menue, ca.
                                           1080×1120

Das Ziel ist ein Satz Rohbilder, aus dem sich die Seite zuschneiden laesst.
Aufloesung und Ausschnitt folgen den von Hand aufgenommenen Vorlagen — ohne
Titelleiste des Fensters.

⚠️ **Leere Konfiguration, mit Absicht.** Die Anwendung liest eigene
Regeln, Vorlagen und Dienste aus `~/.config/maschera/` — und die koennen
Namen tragen, interne Kuerzel, den Arbeitgeber. `XDG_CONFIG_HOME` zeigt
deshalb auf ein temporaeres Verzeichnis. Die EINE Vorlage in den Bildern ist
erfunden und steht unten; die Dienste sind die Vorgaben.

Der Ablauf, in dieser Reihenfolge: Beispiel laden, maskieren, Menue an der
Maske «Andrea» oeffnen (Bildsorte 2), in den Prompt uebernehmen, Vorlage
waehlen, die Antwort des Dienstes einsetzen, das Vokabular einpflegen
(Bildsorte 1), das Dienstmenue aufklappen (Bildsorte 3).

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
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "dist" / "schirmbilder"
SPRACHEN = ("de", "fr", "it", "en")
THEMEN = (("", "light"), ("-dunkel", "dark"))

# Das Fenster der Vorlagen: Die Schrift der Hauptansicht ist 1,2-mal so gross
# wie bei 1 Punkt = 1 Pixel (gemessen an Zeilenbreiten und Knopfhoehen), also
# 1,2 Pixel je Punkt. 1667 Punkte ergeben die 2000 Pixel Breite, 982 Punkte
# 1178 Pixel Hoehe (die Vorlagen messen 1208–1216 mit einer Titelleiste von
# 33 Pixeln, die hier fehlt). Unter 44em Hoehe stapelt die Oberflaeche die
# Bereiche untereinander — 982 Punkte liegen weit darueber.
FENSTER = {"width": 1667, "height": 982}
HAUPT_DICHTE = 1.2

# Bildsorte 2: Spalte 02. Die Vorlagen sind gegenueber der Hauptansicht um
# 1,284 vergroessert: 1,2 × 1,284 = 1,54 Pixel je Punkt; 555×614 Punkte
# ergeben die ca. 855×945 Pixel.
MENUE_DICHTE = 1.54
MENUE_FLAECHE = (555, 614)
# Bildsorte 3: der Knopf mit dem Menue, um 3,07 vergroessert: 3,68 Pixel je
# Punkt; 294×305 Punkte ergeben ca. 1082×1122 Pixel.
KI_DICHTE = 3.68
KI_FLAECHE = (294, 305)

# Die Vorlage in den Bildern: Name und Text stehen in der Sprache der
# Aufnahme. «4W» heisst vier Wochen (Wartezeit). Der deutsche Name ist der
# der Vorlagen-Bilder, die uebrigen sind seine Uebersetzungen.
VORLAGE_NAME = {
    "de": "Verständnisvoll, nett aber 4W",
    "fr": "Compréhensif, aimable mais 4 sem.",
    "it": "Comprensivo, gentile ma 4 sett.",
    "en": "Understanding, kind but 4W",
}
VORLAGE_TEXT = {
    "de": ("Beantworte verständnisvoll, nett und sage aber, dass sie sich "
           "vier Wochen gedulden müssen, da aktuell viele Anfragen "
           "reinkommen! Erwähne dabei die Details, damit sie sich "
           "abgeholt fühlen."),
    "fr": ("Réponds avec compréhension et gentillesse, mais dis qu’ils "
           "devront patienter quatre semaines, car beaucoup de demandes "
           "arrivent actuellement ! Mentionne les détails pour qu’ils se "
           "sentent pris au sérieux."),
    "it": ("Rispondi con comprensione e gentilezza, ma di’ che dovranno "
           "pazientare quattro settimane, perché al momento arrivano molte "
           "richieste! Menziona i dettagli, così si sentiranno presi sul "
           "serio."),
    "en": ("Reply with understanding and kindness, but say that they will "
           "have to wait four weeks, because many enquiries are coming in "
           "at the moment! Mention the details so that they feel taken "
           "seriously."),
}

# Die Antwort des Dienstes — je Sprache, mit den Platzhaltern des
# Beispiels. Der sichtbare Teil stammt aus den Vorlagen; der Schluss ist so
# bemessen, dass der finale Text auf die Zeichenzahl der Vorlagen kommt
# (ZEICHEN_FINAL) — dann stehen auch die Zaehler im Bild richtig.
ANTWORT = {
    "de": ("Sehr geehrter [GIVENNAME_2] [FULLNAME_2]\n\n"
           "herzlichen Dank für Ihr Schreiben und die Informationen zum "
           "Dossier [CASE_ID_1].\n\n"
           "Wir haben davon Kenntnis genommen, dass Frau [FULLNAME_1] am "
           "[DATE_1] bei uns eine Beschwerde eingereicht hat. Wir "
           "verstehen gut, dass Ihnen diese Angelegenheit wichtig ist und "
           "Sie rasch Klarheit wünschen. Auch danken wir Ihnen für die "
           "Bestätigung der [ORG_1], wonach Frau [FULLNAME_1] die Miete "
           "seit Januar fristgerecht bezahlt. Diese Information ist für "
           "die Prüfung des Falls hilfreich, und wir haben sie im Dossier "
           "vermerkt.\n\n"
           "Wir wissen, dass Sie uns um eine Rückmeldung bis am [DATE_2] "
           "gebeten haben. Leider gehen bei uns aktuell sehr viele "
           "Anfragen ein, sodass wir um etwas Geduld bitten müssen. Wir "
           "rechnen damit, uns in etwa vier Wochen bei Ihnen zu melden. "
           "Wir bitten Sie um Verständnis für diese Verzögerung und danken "
           "Ihnen für Ihre Geduld. Sollte sich in der Zwischenzeit etwas "
           "ändern oder die Angelegenheit dringlicher werden, teilen Sie "
           "uns dies bitte mit, damit wir es bei der Bearbeitung "
           "berücksichtigen können. Wir melden uns bald unter [EMAIL_1] "
           "oder [PHONE_1].\n\n"
           "Freundliche Grüsse"),
    "fr": ("Monsieur [GIVENNAME_2] [FULLNAME_2],\n\n"
           "nous vous remercions de votre courrier et des informations "
           "transmises au sujet du dossier [CASE_ID_1].\n\n"
           "Nous avons bien pris note que Madame [FULLNAME_1] a déposé une "
           "réclamation le [DATE_1]. Nous comprenons que cette situation "
           "vous tienne à cœur et que vous souhaitiez obtenir rapidement "
           "une réponse. Nous vous remercions également de la confirmation "
           "de [ORG_1], selon laquelle Madame [FULLNAME_1] paie son loyer "
           "dans les délais depuis janvier. Cette information est "
           "précieuse pour l’examen du dossier et a été versée à "
           "celui-ci.\n\n"
           "Nous sommes conscients que vous nous avez demandé une réponse "
           "jusqu’au [DATE_2]. Cependant, nous recevons actuellement un "
           "très grand nombre de demandes et nous devons malheureusement "
           "vous prier de faire preuve d’un peu de patience. Nous pensons "
           "pouvoir revenir vers vous dans environ quatre semaines. Nous "
           "vous prions de nous excuser pour ce délai et vous remercions "
           "de votre patience. Si la situation devait évoluer entre-temps "
           "ou si l’affaire devenait plus urgente, veuillez nous en "
           "informer afin que nous puissions en tenir compte lors du "
           "traitement. Nous vous contacterons via [EMAIL_1] ou au "
           "[PHONE_1].\n\n"
           "Avec nos meilleures salutations"),
    "it": ("Egregio signor [GIVENNAME_2] [FULLNAME_2],\n\n"
           "vi ringraziamo per la vostra lettera e per le informazioni "
           "relative al dossier [CASE_ID_1].\n\n"
           "Abbiamo preso atto che il [DATE_1] la signora [FULLNAME_1] ha "
           "presentato un reclamo. Comprendiamo che la questione vi stia a "
           "cuore e che desideriate ottenere una risposta in tempi rapidi. "
           "Vi ringraziamo anche per la conferma di [ORG_1], secondo cui "
           "la signora [FULLNAME_1] paga la pigione puntualmente da "
           "gennaio. Si tratta di un’informazione preziosa per l’esame del "
           "caso, che abbiamo provveduto ad annotare nel dossier.\n\n"
           "Siamo consapevoli che ci avete chiesto una risposta entro il "
           "[DATE_2]. Al momento riceviamo però moltissime richieste e "
           "dobbiamo purtroppo chiedervi un po’ di pazienza. Pensiamo di "
           "potervi rispondere entro circa quattro settimane. Vi preghiamo "
           "di scusare il ritardo e vi ringraziamo per la pazienza. Se nel "
           "frattempo dovesse cambiare qualcosa o la questione dovesse "
           "diventare più urgente, vi preghiamo di comunicarcelo, così da "
           "poterne tenere conto durante la trattazione. Vi contatteremo "
           "presto all’indirizzo [EMAIL_1] o al numero [PHONE_1].\n\n"
           "Cordiali saluti"),
    "en": ("Dear [GIVENNAME_2] [FULLNAME_2],\n\n"
           "Thank you for your letter and for the information regarding "
           "case [CASE_ID_1].\n\n"
           "We have noted that on [DATE_1], Ms [FULLNAME_1] filed a "
           "complaint with us. We understand that this matter is important "
           "to you and that you would like clarity as soon as possible. "
           "Thank you also for the confirmation from [ORG_1] that Ms "
           "[FULLNAME_1] has paid her rent on time since January. This is "
           "helpful for reviewing the case, and we have added it to the "
           "file.\n\n"
           "We are aware that you asked for a reply by [DATE_2]. However, "
           "we are currently receiving a very high volume of enquiries, "
           "and we must unfortunately ask for a little patience. We expect "
           "to be able to get back to you in about four weeks. We "
           "apologise for the delay and thank you for your "
           "patience. Should anything change in the meantime, or should "
           "the matter become more urgent, please let us know so that we "
           "can take it into account when handling your case. We will "
           "contact you at [EMAIL_1] or on [PHONE_1].\n\n"
           "Kind regards"),
}
# Die Zeichenzahl des finalen Textes in den Vorlagen. Weicht sie ab, ist
# entweder das Beispiel der Anwendung geaendert oder die Antwort oben —
# das Skript meldet es, statt falsche Zaehler ins Bild zu setzen.
ZEICHEN_FINAL = {"de": 1147, "fr": 1235, "it": 1147, "en": 1023}


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
    anfrage = urllib.request.Request(
        adresse + "/api/vorlagen", method="PUT",
        data=json.dumps({"vorlagen": [{
            "name": VORLAGE_NAME[sprache],
            "text": VORLAGE_TEXT[sprache]}]})
        .encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=10) as r:
        if r.status != 200:
            raise SystemExit(f"Vorlage nicht gesetzt: HTTP {r.status}")


def dienste_setzen(adresse: str) -> None:
    """Die Vorgaben und Mistral — wie in den Vorlagen-Bildern; ein eigener
    Dienst des Entwicklers gehoert nicht ins Bild."""
    dienste = [
        {"id": "claude", "name": "Claude", "url": "https://claude.ai/new"},
        {"id": "chatgpt", "name": "ChatGPT", "url": "https://chatgpt.com/"},
        {"id": "gemini", "name": "Gemini",
         "url": "https://gemini.google.com/app"},
        {"id": "copilot", "name": "Copilot",
         "url": "https://copilot.microsoft.com/"},
        {"id": "mistral", "name": "Mistral",
         "url": "https://chat.mistral.ai/chat"},
    ]
    anfrage = urllib.request.Request(
        adresse + "/api/einstellungen", method="PUT",
        data=json.dumps({"dienste": dienste}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=10) as r:
        if r.status != 200:
            raise SystemExit(f"Dienste nicht gesetzt: HTTP {r.status}")


def ablauf(seite, sprache: str, bis: str):
    """Spielt den Ablauf bis zu einer Stelle durch.

    `bis` ist "maske" (nach dem Menue an der Maske), "final" (nach dem
    Einpflegen der Antwort) oder "dienste" (dazu das aufgeklappte
    Dienstmenue). Gibt den Kasten der Spalte 02 zurueck.
    """
    seite.click(f"[data-sprache='{sprache}']")
    # Drei Spalten von Anfang an — sonst klappt die dritte erst mit der
    # Uebernahme auf, und 01 und 02 sind doppelt breit.
    seite.click("#knopf-ausklappen")
    seite.wait_for_selector("#knopf-beispiel:not([disabled])")
    seite.click("#knopf-beispiel")
    seite.wait_for_selector("#knopf-maskieren:not([disabled])")
    seite.click("#knopf-maskieren")
    seite.wait_for_selector("#knopf-uebernahme:not([disabled])",
                            timeout=180_000)
    seite.wait_for_function(
        "document.querySelector('#legende') &&"
        " document.querySelector('#legende').children.length > 0")
    seite.evaluate("window.scrollTo(0, 0)")

    if bis == "maske":
        # Das Menue an der Maske «Andrea»: Herkunft, Entfernen, Typwechsel.
        plakette = seite.locator(
            "#maskiert .ph[data-ph^='[GIVENNAME_1']").first
        plakette.click(button="right")
        seite.wait_for_selector("#kontext:not([hidden])")
        # Die Maus weg vom Menue, damit kein Eintrag nur wegen des Zeigers
        # hervorgehoben ist.
        seite.mouse.move(5, 5)
        return seite.locator("#b02").bounding_box()

    seite.click("#knopf-uebernahme")
    seite.wait_for_selector("#prompt", state="visible")
    seite.click("#knopf-vorlagen")
    seite.locator("#vorlagen-liste button.waehlen").first.click()
    seite.wait_for_selector("#knopf-kopieren-hinaus:not([disabled])")
    seite.fill("#antwort04", ANTWORT[sprache])
    seite.wait_for_selector("#knopf-einpflegen04:not([disabled])")
    seite.click("#knopf-einpflegen04")
    seite.wait_for_selector("#knopf-final-kopieren:not([disabled])",
                            timeout=60_000)
    zaehler = seite.locator("#b05").inner_text()
    treffer = re.search(r"(\d[\d’'. ]*)\s*(?:Zeichen|caractères|caratteri"
                        r"|characters)", zaehler)
    if treffer:
        zahl = int(re.sub(r"\D", "", treffer.group(1)))
        if zahl != ZEICHEN_FINAL[sprache]:
            print(f"   ⚠️ {sprache}: finaler Text hat {zahl} statt "
                  f"{ZEICHEN_FINAL[sprache]} Zeichen")
    # Alle Felder an den Anfang: nach dem Einpflegen steht die Antwort unten.
    seite.evaluate("window.scrollTo(0, 0);"
                   "document.querySelectorAll('textarea')"
                   ".forEach(t => { t.scrollTop = 0; })")
    seite.mouse.move(5, 5)
    if bis == "dienste":
        seite.click("#knopf-dienstmenu")
        seite.wait_for_selector("#dienstmenu:not([hidden])")
        seite.mouse.move(5, 5)
    return seite.locator("#b02").bounding_box()


def aufnehmen(browser, adresse: str, ordner: Path, sprache: str,
              zusatz: str, schema: str) -> None:
    """Drei Durchgaenge je Sprache und Thema — jeder mit eigener Dichte."""
    def durchgang(dichte: float, bis: str):
        kontext = browser.new_context(
            viewport=FENSTER, color_scheme=schema,
            device_scale_factor=dichte)
        seite = kontext.new_page()
        seite.goto(adresse)
        seite.wait_for_selector("#knopf-beispiel")
        return kontext, seite, ablauf(seite, sprache, bis)

    # 2. Das Menue an der Maske, Ausschnitt um Spalte 02.
    kontext, seite, kasten = durchgang(MENUE_DICHTE, "maske")
    seite.screenshot(path=str(ordner / f"maskierung-{sprache}{zusatz}.png"),
                     clip={"x": kasten["x"] - 4, "y": kasten["y"] - 5,
                           "width": MENUE_FLAECHE[0],
                           "height": MENUE_FLAECHE[1]})
    kontext.close()

    # 1. Die ganze Oberflaeche nach dem Ablauf.
    kontext, seite, _ = durchgang(HAUPT_DICHTE, "final")
    seite.screenshot(path=str(ordner / f"hauptansicht-{sprache}{zusatz}.png"))
    kontext.close()

    # 3. Das Dienstmenue am Knopf «Kopieren und … oeffnen».
    kontext, seite, _ = durchgang(KI_DICHTE, "dienste")
    knopf = seite.locator("#knopf-senden").bounding_box()
    # Der Knopf sitzt am rechten Fensterrand: den Ausschnitt nach links
    # schieben, damit er nicht ueber das Fenster hinausragt.
    links = min(knopf["x"] - 18, FENSTER["width"] - KI_FLAECHE[0])
    seite.screenshot(path=str(ordner / f"ki-menue-{sprache}{zusatz}.png"),
                     clip={"x": links, "y": knopf["y"] - 9,
                           "width": KI_FLAECHE[0],
                           "height": KI_FLAECHE[1]})
    kontext.close()


def packen(ordner: Path, zip_pfad: Path) -> None:
    with zipfile.ZipFile(zip_pfad, "w", zipfile.ZIP_STORED) as z:
        for bild in sorted(ordner.glob("*.png")):
            z.write(bild, bild.name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default="runs/ch-v63b")
    ap.add_argument("--port", type=int, default=4199)
    ap.add_argument("--nach", default=str(ZIEL),
                    help="Zielordner fuer die Bilder und das ZIP")
    ap.add_argument("--sprachen", default=",".join(SPRACHEN))
    ap.add_argument("--zip", default=None,
                    help="Pfad des ZIP (Vorgabe: <nach>/schirmbilder.zip)")
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
    ordner = Path(args.nach)
    ordner.mkdir(parents=True, exist_ok=True)
    for alt in ordner.glob("*.png"):
        alt.unlink()
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
            dienste_setzen(adresse)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                for sprache in sprachen:
                    vorlage_setzen(adresse, sprache)
                    for zusatz, schema in THEMEN:
                        aufnehmen(browser, adresse, ordner, sprache,
                                  zusatz, schema)
                    print(f"   {sprache}: fertig")
                browser.close()
        finally:
            dienst.terminate()
            dienst.wait(timeout=30)
    zip_pfad = Path(args.zip) if args.zip else ordner / "schirmbilder.zip"
    packen(ordner, zip_pfad)
    print(f"   {len(list(ordner.glob('*.png')))} Bilder, ZIP: {zip_pfad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
