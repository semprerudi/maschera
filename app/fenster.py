#!/usr/bin/env python3
"""MASCHERA als eigenes Fenster — nicht als Webseite im Browser.

    python3 app/fenster.py --model runs/ch-v63b

Das ist keine Geschmacksfrage. MASCHERA verspricht, dass nichts das
Geraet verlaesst — und ein Fenster mit Adresszeile, Lesezeichen und
Verlauf sagt genau das Gegenteil. Wer nicht sieht, ob er lokal arbeitet,
traut dem Versprechen zu Recht nicht.

## Wie es laeuft

Ein Faden traegt den Flask-Dienst, das Hauptprogramm traegt das Fenster.
Beim Schliessen des Fensters endet der Prozess und damit der Dienst.

## Adresse und Port

Sie kommen aus `~/.config/maschera/einstellungen.json` — derselben Datei,
die die Oberflaeche unter «Einstellungen» schreibt. Vorgabe 127.0.0.1:4141.

Laesst sich dort nicht binden, kommt ein kleiner Dialog: Adresse und
Port, der Port mit Pfeilen um eins verstellbar, vorbelegt mit dem
naechsten freien. Was gewaehlt wird, wird SOFORT gesichert und gilt beim
naechsten Start. Kein Zufallsport: ein Dienst, der jedes Mal woanders
horcht, ist genau die Undurchschaubarkeit, gegen die dieses Fenster
gebaut wurde.

## Was hier NICHT passiert

Kein Nachladen von aussen. Die Oberflaeche kommt aus `app/static`, das
Modell liegt daneben. Die eine benannte Ausnahme des Projekts — die
Portpruefung — betrifft diesen Weg nicht.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import threading
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

TITEL = "MASCHERA"

# Die Zwischenablage darf das Fenster nicht toeten.
#
# pywebview uebergibt fuer Berechtigungsanfragen nackte Zahlen (`1`, `2`).
# PyQt6 nimmt fuer Aufzaehlungen keine Zahlen mehr an und wirft — und eine
# Python-Ausnahme in einem Qt-Slot beendet den Prozess mit `abort()`:
#
#     File ".../webview/platforms/qt.py", in onFeaturePermissionRequested
#         self.setFeaturePermission(url, feature, 2)
#     TypeError: argument 3 has unexpected type 'int'
#
# Qt 6.8+ fragt fuer `navigator.clipboard` eine Berechtigung an. Ohne diese
# Ersetzung stirbt das Fenster am ersten Kopierknopf.
#
# Die Zwischenablage wird ERLAUBT — sie ist der Weg, auf dem dieses Werkzeug
# arbeitet. Sie zu verweigern tauschte den Absturz gegen einen stillen
# Fehlschlag. Kamera und Mikrofon dagegen werden VERWEIGERT: ein Werkzeug,
# das nichts sendet, hat dort nichts zu suchen.
ERLAUBT = ("ClipboardReadWrite",)


def fassung_lesen() -> str:
    """Die Fassungsnummer aus `app/serve.py`, ohne `serve` zu importieren.

    Der Import von `serve` zieht torch und transformers nach — Sekunden, die
    erst NACH dem Fenster vergehen sollen. Gelesen wird trotzdem aus der
    einen Quelle, wie in `tools/paket/fassung.fish`.
    """
    try:
        text = (Path(__file__).resolve().parent / "serve.py").read_text(
            encoding="utf-8")
        treffer = re.search(r'^VERSION = "([^"]+)"', text, re.M)
        return treffer.group(1) if treffer else ""
    except OSError:
        return ""


# DAS STARTFENSTER.
#
# Das Laden des Modells dauert mehrere Sekunden. Schneller wird das nicht,
# aber es darf nicht SCHWEIGEN. Deshalb steht das Fenster sofort da und
# traegt diese Seite; das Modell laedt dahinter. Ist es bereit, wird auf
# die Oberflaeche umgeschaltet.
#
# Kein Fortschrittsbalken, sondern eine ruhige Bewegung: wie lange das
# Laden dauert, weiss niemand, und eine Prozentzahl waere erfunden.
#
# «Lokale Maskierung», nicht «Pseudonymisierung»: nach aussen heisst es
# Maskierung; dass das Verfahren fachlich eine Pseudonymisierung ist, steht
# in SPEC.md. Die Quelle desselben Satzes fuer den Schreibtisch ist
# `tools/paket/maschera.desktop`.
#
# Alles eingebettet: kein Nachladen von aussen, auch nicht die Schrift. In
# diesen Sekunden gibt es noch keinen Server, von dem etwas kommen koennte.
STARTSEITE = """<!doctype html>
<html__THEMA__ lang="de"><head><meta charset="utf-8"><title>MASCHERA</title>
<style>
  /* Dieser Bildschirm ist eigenes HTML in Python und wird weder von
     `maschera.css` noch von den Farbpruefungen fuer Blatt und Skript
     erfasst. Deshalb hier dieselbe Bauart wie im Blatt: Marken oben,
     zwei Einhaengepunkte darunter, EINE Liste. `test_fenster.py`
     Punkt 19 verlangt beide. */
  :root{--grund:#fff;--schrift:#1d1f20;--matt:#5c5c60;--leise:#8c8c90;
        --balken:#e7e7ea;--balkenkante:#b7b7ba;--balkenzug:#24523a;
        --aufschrift:#fff;--fehler:#c0392b}
  @media (prefers-color-scheme: dark){
    :root:not([data-thema="hell"]){
      --grund:#1a1917;--schrift:#ece9e3;--matt:#a5a29b;--leise:#7d7972;
      --balken:#2b2a27;--balkenkante:#423f3b;--balkenzug:#4e9a6c;
      --aufschrift:#12211a;--fehler:#e8836f}}
  :root[data-thema="dunkel"]{
    --grund:#1a1917;--schrift:#ece9e3;--matt:#a5a29b;--leise:#7d7972;
    --balken:#2b2a27;--balkenkante:#423f3b;--balkenzug:#4e9a6c;
    --aufschrift:#12211a;--fehler:#e8836f}
  html,body{height:100%;margin:0}
  body{display:flex;align-items:center;justify-content:center;
       background:var(--grund);color:var(--schrift);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
  /* `width:100%` UND `box-sizing`: `max-width:26rem` sind 416 px, und
     ein Polster von zweimal 2rem obendrauf ragte aus einem
     Widget-Fenster von 380 px hinaus. */
  .mitte{display:flex;flex-direction:column;align-items:center;gap:1.25rem;
         width:100%;max-width:26rem;box-sizing:border-box;
         padding:2rem 1.25rem;text-align:center}
  .zeile{display:flex;align-items:center;gap:1.25rem}
  svg{display:block;width:4.5rem;height:auto;max-width:100%}
  .marke{font-size:2.25rem;letter-spacing:.1em;font-weight:400}
  .marke b{font-weight:700}
  /* ⚠️ LINKSBUENDIG, nicht mittig. `.mitte` zentriert alles, und damit
     stand der Satz mittig zur Wortmarke statt unter ihrem ersten
     Buchstaben — er ragte links darueber hinaus und sah verrissen aus.
     Die Maske steht daneben, die zwei Zeilen darunter beginnen an
     derselben Kante. */
  .zeile > div{text-align:left}
  /* ⚠️ KEIN `white-space:nowrap` mehr. Es stand hier, damit der Satz
     neben der Maske auf einer Zeile bleibt — und machte ihn im schmalen
     Fenster zur festen Mindestbreite, gegen die kein Umbruch half. Wo es
     eng wird, stapelt die Zeile ohnehin (siehe unten); dann darf der Satz
     brechen. */
  .satz{margin:.25rem 0 0;font-size:.875rem;color:var(--matt)}
  .balken{width:100%;height:.5rem;background:var(--balken);
          border:1px solid var(--balkenkante);overflow:hidden}
  .balken i{display:block;height:100%;width:32%;background:var(--balkenzug);
            animation:wandern 1.5s ease-in-out infinite}
  @keyframes wandern{0%{transform:translateX(-110%)}
                     50%{transform:translateX(220%)}
                     100%{transform:translateX(-110%)}}
  p{margin:0;font-size:.9375rem;color:var(--matt);line-height:1.5}
  /* Der Satz unter dem Balken ist Beiwerk: kleiner und mit Abstand, sonst
     klebt er am Balken und wirkt wie dessen Beschriftung. */
  #t_laden{margin-top:1.5rem;font-size:.8125rem;line-height:1.6}
  .fassung{font-size:.8125rem;color:var(--leise)}
  @media (prefers-reduced-motion: reduce){
    .balken i{animation:none;width:100%;opacity:.5}}
  /* ⚠️ SCHMAL WIRD GESTAPELT, wie beim Startbild der Oberflaeche und an
     derselben Grenze (33em). Maske neben Wortmarke braucht rund 400 px;
     der Widget-Modus hat 380. Dann steht die Maske oben und die Marke
     darunter, und die linksbuendige Ausrichtung der zwei Zeilen wird
     mittig — sie richtet sich sonst an einer Kante aus, die es
     gestapelt nicht mehr gibt. */
  @media (max-width:33em){
    .mitte{padding:1.25rem;gap:1rem}
    .zeile{flex-direction:column;gap:.75rem}
    .zeile > div{text-align:center}
    svg{width:3.5rem}
    .marke{font-size:1.75rem}
    .satz{font-size:.8125rem}}

  /* Das Onboarding ist KEIN zweiter Bildschirm, sondern derselbe: Maske,
     Wortmarke und Fassung bleiben stehen, und nur der Block dazwischen
     wechselt. */
  [hidden]{display:none !important}
  .schritt{display:flex;flex-direction:column;gap:1rem;width:100%;
           text-align:left}
  .titel{font-size:1.125rem;font-weight:600;margin:0}
  /* `overflow-wrap:anywhere` und nicht `word-break:break-all`: das
     zweite bricht JEDES Wort an jeder Stelle, mitten im Namen.
     `anywhere` bricht erst, wenn ein Wort wirklich nicht passt.
     Kein Blocksatz: die Spalte ist rund vierzig Zeichen breit, und ohne
     Silbentrennung reisst Blocksatz Loecher. Auf Silbentrennung ist
     kein Verlass — Chromium laedt dafuer Woerterbuecher nach, und
     dieses Programm laedt nichts nach. */
  .fein{font-size:.8125rem;color:var(--leise);overflow-wrap:anywhere;
        margin:0;line-height:1.45}
  .fein b{font-weight:600;color:var(--matt)}
  .warn{font-size:.875rem;color:var(--matt);margin:0;line-height:1.55}
  /* Die Frage und die Kosten stehen zusammen und tragen die Farbe des
     Textes, nicht die des Beiwerks — sie sind das, worauf geantwortet
     wird. */
  .frage{color:var(--schrift);border-left:2px solid var(--balkenkante);
         padding-left:.75rem}
  .schritt{gap:.875rem}
  .knopfzeile{display:flex;gap:.5rem;justify-content:flex-end;
              flex-wrap:wrap}
  button{font:inherit;font-size:.9375rem;padding:.5rem 1rem;
         border:1px solid var(--balkenkante);background:var(--balken);
         color:var(--schrift);cursor:pointer}
  button:hover{border-color:var(--matt)}
  button.haupt{background:var(--balkenzug);border-color:var(--balkenzug);
               color:var(--aufschrift);font-weight:600}
  button:disabled{opacity:.5;cursor:default}
  /* Der Sprachschalter: vier Kuerzel, das gewaehlte hervorgehoben. */
  .sprachen{display:flex;gap:.375rem;flex-wrap:wrap;align-items:center}
  .sprachen button{padding:.3125rem .625rem;font-size:.8125rem;
                   text-transform:uppercase;letter-spacing:.05em}
  .sprachen button[aria-pressed="true"]{background:var(--balkenzug);
                                        border-color:var(--balkenzug);
                                        color:var(--aufschrift)}
  /* ⚠️ Der Fortschritt ist ein ANDERER Balken als der wandernde oben:
     dieser zeigt einen Anteil und darf sich nicht bewegen, wenn nichts
     geschieht. Ein Balken, der laeuft, waehrend nichts passiert, ist
     eine Anzeige, die luegt. */
  .fortschritt{width:100%;height:.5rem;background:var(--balken);
               border:1px solid var(--balkenkante);overflow:hidden}
  .fortschritt i{display:block;height:100%;width:0;
                 background:var(--balkenzug);transition:width .2s linear}
  /* Ueber eine Marke, nicht als Literal (Punkt 19): ein Literal waere
     beim naechsten Farbwechsel die Stelle, die niemand findet. */
  .fehler{font-size:.875rem;color:var(--fehler);margin:0;
          line-height:1.5}
</style></head><body>
<div class="mitte">
  <div class="zeile">
    __MASKE__
    <div>
      <div class="marke">MAS<b>CH</b>ERA</div>
      <p class="satz" id="unter">__SATZ__</p>
    </div>
  </div>

  <!-- Der Ladebildschirm. Bei einem gewoehnlichen Start das Einzige,
       was zu sehen ist. -->
  <div id="s_laden">
    <div class="balken"><i></i></div>
    <p id="t_laden">__LADEN__<br>__ERSTER__</p>
  </div>

  <!-- Willkommen: nur beim allerersten Start und wenn das Modell fehlt. -->
  <div id="s_willkommen" class="schritt" hidden>
    <p class="titel" id="t_wtitel"></p>
    <p class="warn" id="t_wtext"></p>
    <div class="sprachen" id="sprachen"></div>
    <div class="knopfzeile">
      <button class="haupt" id="k_weiter"></button>
    </div>
  </div>

  <!-- Das fehlende Modell. -->
  <div id="s_modell" class="schritt" hidden>
    <p class="titel" id="t_mtitel"></p>
    <p class="warn" id="t_mtext"></p>
    <p class="fein"><span id="t_quelle"></span></p>
    <p class="fein"><span id="t_ziel"></span></p>
    <p class="warn" id="t_danach"></p>
    <p class="warn frage" id="t_kosten"></p>
    <div class="fortschritt" id="fortschritt" hidden><i></i></div>
    <p class="warn" id="t_stand" hidden></p>
    <p class="fehler" id="t_fehler" hidden></p>
    <div class="knopfzeile">
      <button id="k_spaeter"></button>
      <button class="haupt" id="k_holen"></button>
    </div>
  </div>

  <div class="fassung">v__FASSUNG__</div>
</div>
<script>
/* ⚠️ ALLE VIER SPRACHEN LIEGEN IN DER SEITE. Der Schalter wechselt
   sofort und ohne Neuladen — wer die Sprache umstellt, will nicht einen
   Moment lang auf einen weissen Bildschirm sehen. Python bekommt die
   Wahl trotzdem, damit sie ueber den Start hinaus gilt. */
const SAETZE = __SAETZE__;
const ORTE   = __ORTE__;
let sprache  = "__SPRACHE__";
let letzterFehler = null;
let laeuft = false;

function schritt(name) {
  for (const s of ["s_laden", "s_willkommen", "s_modell"]) {
    document.getElementById(s).hidden = (s !== name);
  }
}

function setzen(id, wert) { document.getElementById(id).textContent = wert; }

/* Etikett fett, Wert daneben — beides ueber Knoten, nie `innerHTML`. */
function zeile(id, etikett, wert) {
  const e = document.getElementById(id);
  e.textContent = "";
  const b = document.createElement("b");
  b.textContent = etikett + " ";
  e.append(b, wert);
}

function malen() {
  const s = SAETZE[sprache];
  document.documentElement.lang = sprache;
  setzen("unter", s.unter);
  document.getElementById("t_laden").innerHTML = "";
  document.getElementById("t_laden").append(s.laden, document.createElement("br"), s.erster);
  setzen("t_wtitel", s.w_titel);
  setzen("t_wtext", s.w_text);
  setzen("k_weiter", s.w_weiter);
  setzen("t_mtitel", s.m_titel);
  setzen("t_mtext", s.m_text.replace("{name}", ORTE.name).replace("{gb}", ORTE.gb));
  /* ⚠️ NICHT DIE GANZE ADRESSE. `https://` und `/resolve/main` sagen dem
     Leser nichts und kosten zwei Zeilen; was zaehlt, ist das
     Repositorium. Beim Ziel wird das Heimatverzeichnis zu `~` — dieselbe
     Angabe, halb so lang. Gekuerzt wird nur, was ohnehin jeder kennt. */
  zeile("t_quelle", s.m_quelle, ORTE.quelle_kurz);
  zeile("t_ziel", s.m_ziel, ORTE.ziel_kurz);
  setzen("t_danach", s.m_danach);
  setzen("t_kosten", s.m_kosten.replace("{gb}", ORTE.gb));
  setzen("k_holen", s.m_holen);
  setzen("k_spaeter", laeuft ? s.m_abbrechen : s.m_spaeter);
  for (const k of document.querySelectorAll("#sprachen button")) {
    k.setAttribute("aria-pressed", String(k.dataset.spr === sprache));
  }
  if (letzterFehler) {
    document.getElementById("t_fehler").textContent = fehlersatz();
  }
}

/* ⚠️ `createElement` und `textContent`, nie `innerHTML` mit Werten. Hier
   kommen `quelle` und `ziel` aus einer Datei auf der Platte — dieselbe
   Regel wie in `maschera.js`, und sie kennt keine Ausnahme. */
for (const code of ["de", "fr", "it", "en"]) {
  const k = document.createElement("button");
  k.textContent = code;
  k.dataset.spr = code;
  k.onclick = () => { sprache = code; malen();
                      if (window.pywebview) pywebview.api.sprache(code); };
  document.getElementById("sprachen").append(k);
}

document.getElementById("k_weiter").onclick = () => {
  if (ORTE.fehlt) { schritt("s_modell"); }
  else { schritt("s_laden"); pywebview.api.weiter(); }
};
document.getElementById("k_spaeter").onclick = () => pywebview.api.spaeter();
document.getElementById("k_holen").onclick = () => {
  document.getElementById("k_holen").disabled = true;
  document.getElementById("fortschritt").hidden = false;
  document.getElementById("t_stand").hidden = false;
  document.getElementById("t_fehler").hidden = true;
  setzen("t_stand", SAETZE[sprache].m_laedt);
  /* ⚠️ DER KNOPF SAGT, WAS ER TUT. Waehrend des Ladens beendet «Spaeter»
     nicht bloss spaeter — er bricht einen laufenden Download ab, wartet
     auf das Aufraeumen und schliesst die Anwendung. Ein Knopf, dessen
     Aufschrift das verschweigt, ist eine Falle. */
  laeuft = true;
  malen();
  pywebview.api.holen();
};

/* Von Python gerufen. */
function fortschritt(promille, name) {
  document.querySelector("#fortschritt i").style.width = (promille / 10) + "%";
  setzen("t_stand", SAETZE[sprache].m_laedt + "  " + name + "  " +
                    Math.round(promille / 10) + " %");
}
/* ⚠️ DER FEHLER WIRD GEMERKT, nicht nur angezeigt. Wer die Sprache
   umstellt, waehrend eine Absage dasteht, soll sie uebersetzt sehen —
   sonst bleibt genau der Satz stehen, dessentwegen das Ganze gebaut
   wurde. `malen()` setzt ihn deshalb mit. `letzterFehler` steht oben,
   weil `let` nicht hochgezogen wird und `malen()` frueher laeuft. */
function fehlersatz() {
  if (!letzterFehler) return "";
  const vorlage = SAETZE[sprache][letzterFehler.schluessel];
  if (!vorlage) return letzterFehler.roh;      /* unbekannt: Rohtext */
  let satz = vorlage;
  for (const k of Object.keys(letzterFehler.werte)) {
    satz = satz.split("{" + k + "}").join(letzterFehler.werte[k]);
  }
  return satz;
}

function gescheitert(schluessel, werte, roh) {
  letzterFehler = { schluessel: schluessel, werte: werte || {}, roh: roh };
  document.getElementById("fortschritt").hidden = true;
  document.getElementById("t_stand").hidden = true;
  const f = document.getElementById("t_fehler");
  f.hidden = false;
  f.textContent = fehlersatz();
  document.getElementById("k_holen").disabled = false;
  laeuft = false;
  malen();
}
function fertig() { schritt("s_laden"); }

malen();
schritt("__SCHRITT__");
</script>
</body></html>"""


# Der Startbildschirm spricht vier Sprachen — die zuletzt gewaehlte.
#
# Er ist die einzige Stelle, die ihre Sprache nicht aus `maschera.js`
# holen kann: er steht, bevor die Oberflaeche geladen ist. Deshalb liest er
# die Einstellung direkt. Die Saetze unten stehen in keiner anderen Datei.
#
# Benannte Schluessel statt eines Tupels: `test_app.py` prueft, dass alle
# vier Sprachen DIESELBEN Schluessel fuehren — so faellt ein Satz auf, der
# in einer Sprache fehlt.
START_SAETZE = {
    "de": {
        "unter": "Lokale Maskierung für Schweizer Dokumente",
        "laden": "Lokales KI-Modell wird geladen …",
        "erster": "Der erste Start dauert etwas länger.",
        "w_titel": "Willkommen",
        "w_text": "MASCHERA ersetzt Personendaten in einem Text durch "
                  "Platzhalter, damit du ihn einem KI-Werkzeug geben "
                  "kannst, ohne die Daten preiszugeben. Die Antwort setzt "
                  "MASCHERA anschliessend wieder zurück.",
        "w_sprache": "Sprache",
        "w_weiter": "Weiter",
        "m_titel": "Es fehlt noch das Sprach-Modell",
        "m_text": "Diese Version von MASCHERA benötigt noch das "
                  "eigentliche Sprach-Modell ({name}, {gb} GB) für die "
                  "lokale Verarbeitung auf diesem Gerät.",
        "m_quelle": "Quelle",
        "m_ziel": "Ziel",
        "m_danach": "Nach dem Download und der Qualitätsprüfung des "
                    "Modells läuft MASCHERA komplett offline bzw. lokal "
                    "auf diesem Gerät, also auch ohne Internet-Verbindung.",
        "m_kosten": "Es werden rund {gb} GB heruntergeladen. Mit Mobilfunk "
                    "und/oder Roaming entstehen womöglich echte "
                    "Zusatzkosten für die Datenübertragung.",
        "m_holen": "Jetzt herunterladen",
        "m_spaeter": "Später",
        "m_laedt": "Wird heruntergeladen und geprüft …",
        "m_ende": "Ohne Modell kein Betrieb — MASCHERA schliesst sich und "
                  "fragt beim nächsten Start wieder.",
        "m_f_abgebrochen":
            "Abgebrochen. Es liegt nichts Halbes auf der Platte.",
        "m_f_pruefsumme":
            "{datei}: die Prüfsumme stimmt nicht. Die Datei wurde verworfen — was nicht stimmt, wird nicht geflickt.",
        "m_f_groesse":
            "{datei}: unerwartete Grösse. Verworfen.",
        "m_f_nicht_berechtigt":
            "Nicht berechtigt (HTTP {code}). Das heisst bei Hugging Face auch: es gibt das Repositorium noch nicht, oder es ist privat.",
        "m_f_nicht_gefunden":
            "Nicht gefunden (HTTP {code}). Die Adresse im Manifest stimmt nicht.",
        "m_f_gegenstelle":
            "Die Gegenstelle hat ein Problem (HTTP {code}), nicht du. Später nochmals.",
        "m_f_http":
            "Unerwartete Antwort (HTTP {code}).",
        "m_f_keine_verbindung":
            "Keine Verbindung. Netz prüfen und nochmals versuchen.",
        "m_f_nicht_schreibbar":
            "{datei} lässt sich nicht schreiben — Datenträger voll oder keine Schreibrechte?",
        "m_f_unvollstaendig":
            "Nach dem Holen fehlt etwas. Nichts wurde übernommen.",
        "m_abbrechen": "Abbrechen",
    },
    "fr": {
        "unter": "Masquage local pour documents suisses",
        "laden": "Chargement du modèle d’IA local …",
        "erster": "Le premier démarrage prend un peu plus de temps.",
        "w_titel": "Bienvenue",
        "w_text": "MASCHERA remplace les données personnelles d’un texte "
                  "par des marqueurs, pour que tu puisses le confier à un "
                  "outil d’IA sans divulguer ces données. MASCHERA "
                  "rétablit ensuite les valeurs dans la réponse.",
        "w_sprache": "Langue",
        "w_weiter": "Continuer",
        "m_titel": "Le modèle linguistique manque encore",
        "m_text": "Cette version de MASCHERA a encore besoin du modèle "
                  "linguistique ({name}, {gb} Go) pour le traitement "
                  "local sur cet appareil.",
        "m_quelle": "Source",
        "m_ziel": "Destination",
        "m_danach": "Après le téléchargement et la vérification du "
                    "modèle, MASCHERA fonctionne entièrement en local sur "
                    "cet appareil, donc aussi sans connexion Internet.",
        "m_kosten": "Environ {gb} Go seront téléchargés. En itinérance ou "
                    "via le réseau mobile, cela peut entraîner de vrais "
                    "frais de transmission.",
        "m_holen": "Télécharger maintenant",
        "m_spaeter": "Plus tard",
        "m_laedt": "Téléchargement et vérification …",
        "m_ende": "Pas de modèle, pas de fonctionnement — MASCHERA se "
                  "ferme et redemandera au prochain démarrage.",
        "m_f_abgebrochen":
            "Interrompu. Rien d’incomplet ne reste sur le disque.",
        "m_f_pruefsumme":
            "{datei} : la somme de contrôle ne correspond pas. Le fichier a été rejeté — ce qui ne correspond pas n’est pas rafistolé.",
        "m_f_groesse":
            "{datei} : taille inattendue. Rejeté.",
        "m_f_nicht_berechtigt":
            "Non autorisé (HTTP {code}). Chez Hugging Face cela signifie aussi : le dépôt n’existe pas encore, ou il est privé.",
        "m_f_nicht_gefunden":
            "Introuvable (HTTP {code}). L’adresse du manifeste est fausse.",
        "m_f_gegenstelle":
            "Le serveur distant a un problème (HTTP {code}), pas toi. Réessaie plus tard.",
        "m_f_http":
            "Réponse inattendue (HTTP {code}).",
        "m_f_keine_verbindung":
            "Pas de connexion. Vérifie le réseau et réessaie.",
        "m_f_nicht_schreibbar":
            "Impossible d’écrire {datei} — disque plein ou pas de droits d’écriture ?",
        "m_f_unvollstaendig":
            "Après le téléchargement il manque quelque chose. Rien n’a été repris.",
        "m_abbrechen": "Annuler",
    },
    "it": {
        "unter": "Mascheratura locale per documenti svizzeri",
        "laden": "Caricamento del modello IA locale …",
        "erster": "Il primo avvio richiede un po’ più di tempo.",
        "w_titel": "Benvenuto",
        "w_text": "MASCHERA sostituisce i dati personali di un testo con "
                  "segnaposto, così puoi darlo a uno strumento di IA "
                  "senza rivelarli. Poi MASCHERA ripristina i valori "
                  "nella risposta.",
        "w_sprache": "Lingua",
        "w_weiter": "Avanti",
        "m_titel": "Manca ancora il modello linguistico",
        "m_text": "Questa versione di MASCHERA ha ancora bisogno del "
                  "modello linguistico ({name}, {gb} GB) per "
                  "l’elaborazione locale su questo dispositivo.",
        "m_quelle": "Fonte",
        "m_ziel": "Destinazione",
        "m_danach": "Dopo il download e la verifica del modello, MASCHERA "
                    "funziona completamente in locale su questo "
                    "dispositivo, quindi anche senza connessione a "
                    "Internet.",
        "m_kosten": "Verranno scaricati circa {gb} GB. Con rete mobile "
                    "e/o roaming possono sorgere costi di trasmissione "
                    "reali.",
        "m_holen": "Scarica ora",
        "m_spaeter": "Più tardi",
        "m_laedt": "Download e verifica in corso …",
        "m_ende": "Senza modello non si lavora — MASCHERA si chiude e "
                  "chiederà di nuovo al prossimo avvio.",
        "m_f_abgebrochen":
            "Interrotto. Sul disco non resta nulla di incompleto.",
        "m_f_pruefsumme":
            "{datei}: la somma di controllo non corrisponde. Il file è stato scartato — ciò che non torna non si aggiusta.",
        "m_f_groesse":
            "{datei}: dimensione inattesa. Scartato.",
        "m_f_nicht_berechtigt":
            "Non autorizzato (HTTP {code}). Su Hugging Face significa anche: il repository non esiste ancora, oppure è privato.",
        "m_f_nicht_gefunden":
            "Non trovato (HTTP {code}). L’indirizzo nel manifesto non è corretto.",
        "m_f_gegenstelle":
            "Il server remoto ha un problema (HTTP {code}), non tu. Riprova più tardi.",
        "m_f_http":
            "Risposta inattesa (HTTP {code}).",
        "m_f_keine_verbindung":
            "Nessuna connessione. Controlla la rete e riprova.",
        "m_f_nicht_schreibbar":
            "Impossibile scrivere {datei} — disco pieno o mancano i permessi di scrittura?",
        "m_f_unvollstaendig":
            "Dopo il download manca qualcosa. Non è stato preso nulla.",
        "m_abbrechen": "Annulla",
    },
    "en": {
        "unter": "Local masking for Swiss documents",
        "laden": "Loading local AI model …",
        "erster": "The first start takes a little longer.",
        "w_titel": "Welcome",
        "w_text": "MASCHERA replaces personal data in a text with "
                  "placeholders, so you can hand it to an AI tool without "
                  "giving the data away. MASCHERA then puts the real "
                  "values back into the answer.",
        "w_sprache": "Language",
        "w_weiter": "Continue",
        "m_titel": "The language model is still missing",
        "m_text": "This version of MASCHERA still needs the language "
                  "model ({name}, {gb} GB) for local processing on this "
                  "device.",
        "m_quelle": "Source",
        "m_ziel": "Target",
        "m_danach": "After the download and the integrity check, MASCHERA "
                    "runs completely locally on this device — also "
                    "without an internet connection.",
        "m_kosten": "About {gb} GB will be downloaded. On mobile data "
                    "and/or roaming this can cause real transfer costs.",
        "m_holen": "Download now",
        "m_spaeter": "Later",
        "m_laedt": "Downloading and verifying …",
        "m_ende": "No model, no operation — MASCHERA closes and will ask "
                  "again on the next start.",
        "m_f_abgebrochen":
            "Cancelled. Nothing half-finished is left on disk.",
        "m_f_pruefsumme":
            "{datei}: the checksum does not match. The file was discarded — what does not match is not patched up.",
        "m_f_groesse":
            "{datei}: unexpected size. Discarded.",
        "m_f_nicht_berechtigt":
            "Not authorised (HTTP {code}). On Hugging Face this also means: the repository does not exist yet, or it is private.",
        "m_f_nicht_gefunden":
            "Not found (HTTP {code}). The address in the manifest is wrong.",
        "m_f_gegenstelle":
            "The remote side has a problem (HTTP {code}), not you. Try again later.",
        "m_f_http":
            "Unexpected response (HTTP {code}).",
        "m_f_keine_verbindung":
            "No connection. Check the network and try again.",
        "m_f_nicht_schreibbar":
            "Cannot write {datei} — disk full or no write permission?",
        "m_f_unvollstaendig":
            "Something is missing after the download. Nothing was taken over.",
        "m_abbrechen": "Cancel",
    },
}


def start_sprache() -> str:
    """Die zuletzt gewaehlte Sprache — oder Deutsch.

    Faellt nie mit einem Fehler aus: der Startbildschirm ist das Erste, was
    der Anwender sieht, und eine kaputte Einstellungsdatei darf ihn nicht
    verhindern. Auch der Import selbst koennte auf einer halben Umgebung
    scheitern.
    """
    try:
        from core import einstellungen
        return einstellungen.lade().get("sprache", "de")
    except Exception:
        return "de"


def startseite(schritt: str = "s_laden", modell: dict | None = None) -> str:
    """Die Startseite mit der echten Maske und der echten Fassung.

    `schritt` waehlt, was zu sehen ist — `s_laden` ist der gewoehnliche
    Start, `s_willkommen` das Onboarding. `modell` traegt Name, Groesse,
    Quelle und Ziel, wenn die Gewichte fehlen.

    Alle vier Sprachen gehen mit in die Seite, damit der Schalter ohne
    Neuladen wechselt — ein Neuladen verloere Schritt und Fortschritt.
    """
    maske = ""
    try:
        roh = (Path(__file__).resolve().parent / "static" / "maske.svg"
               ).read_text(encoding="utf-8")
        # Nur das <svg>-Element, ohne die Kommentare davor.
        i = roh.find("<svg")
        if i >= 0:
            maske = roh[i:]
    except OSError:
        pass
    spr = start_sprache()
    saetze = START_SAETZE.get(spr, START_SAETZE["de"])
    # Die ausdrueckliche Farbwahl gilt auch hier. Sonst folgte der
    # Startbildschirm dem System, waehrend die Oberflaeche dahinter die Wahl
    # des Anwenders traegt, und es gaebe einen hellen Blitz. Dieselbe
    # Ueberlegung wie in der Wurzelroute in `app/app.py`.
    try:
        from core import einstellungen as _e
        thema = _e.lade().get("thema", "automatisch")
    except Exception:  # noqa: BLE001
        thema = "automatisch"
    kopf = f' data-thema="{thema}"' if thema in ("hell", "dunkel") else ""

    # ⚠️ Ueber `json.dumps` und nicht von Hand zusammengesetzt. Die Saetze
    # tragen Anfuehrungszeichen, Apostrophe und Zeilenumbrueche in vier
    # Sprachen; eine selbstgebaute Maskierung waere die Stelle, an der
    # eines Tages ein franzoesisches «l’outil» die Seite zerlegt.
    orte = modell or {"fehlt": False, "name": "", "gb": "",
                      "quelle": "", "quelle_kurz": "",
                      "ziel": "", "ziel_kurz": ""}
    return (STARTSEITE.replace("__THEMA__", kopf)
                      .replace("__MASKE__", maske)
                      .replace("__SATZ__", saetze["unter"])
                      .replace("__LADEN__", saetze["laden"])
                      .replace("__ERSTER__", saetze["erster"])
                      .replace("__FASSUNG__", fassung_lesen())
                      .replace("__SAETZE__", json.dumps(START_SAETZE,
                                                        ensure_ascii=False))
                      .replace("__ORTE__", json.dumps(orte,
                                                      ensure_ascii=False))
                      .replace("__SPRACHE__", spr)
                      .replace("__SCHRITT__", schritt))


def berechtigungen_richten() -> str:
    """Die kaputte Methode in pywebview ersetzen. Gibt zurueck, was geschah.

    `tests/test_fenster.py` Punkt 15 ruft sie auf — ohne Fenster, ohne
    Anzeige.
    """
    from webview.platforms import qt as schicht
    from qtpy.QtWebEngineCore import QWebEnginePage as Seite

    seite = getattr(schicht.BrowserView, "WebPage", None)
    if seite is None or not hasattr(seite, "onFeaturePermissionRequested"):
        # Kein WebEngine — dann gibt es die Methode nicht und auch den
        # Fehler nicht. Nicht still hinnehmen: der Bau soll es sagen.
        return "keine WebEngine-Schicht — nichts zu richten"

    erlaubt = {getattr(Seite.Feature, n) for n in ERLAUBT
               if hasattr(Seite.Feature, n)}
    ja = Seite.PermissionPolicy.PermissionGrantedByUser
    nein = Seite.PermissionPolicy.PermissionDeniedByUser

    def onFeaturePermissionRequested(self, url, merkmal):
        self.setFeaturePermission(url, merkmal,
                                  ja if merkmal in erlaubt else nein)

    seite.onFeaturePermissionRequested = onFeaturePermissionRequested
    return f"{len(erlaubt)} Merkmal(e) erlaubt, alles andere verweigert"



# Herunterladen im eigenen Fenster.
#
# pywebview ruft beim Herunterladen eine Qt5-Schnittstelle auf, die es in
# Qt6 nicht mehr gibt:
#
#     webview/platforms/qt.py, on_download_requested:
#         download.setPath(path)
#     QWebEngineDownloadRequest.setPath  ->  gibt es nicht
#     setDownloadDirectory / setDownloadFileName  ->  gibt es
#
# Zwei weitere Maengel derselben Methode:
#
#   * Der Namensvorschlag kaeme aus `download.url().path()`. Die
#     Oberflaeche laedt ueber einen `blob:`-Verweis herunter, und dessen
#     Pfad ist eine nackte UUID. Der richtige Name steht in
#     `downloadFileName()` — Qt fuellt ihn aus dem `download`-Merkmal des
#     Verweises, und genau das setzt `maschera.js`.
#   * Wer den Dialog abbricht, liesse die Anfrage haengen. Ohne `cancel()`
#     wartet Qt auf eine Entscheidung, die nie kommt.
#
# NICHTS WIRD OHNE DIALOG GESCHRIEBEN. Ein Werkzeug, das damit wirbt,
# nichts abzulegen, darf nicht von sich aus in einen Ordner schreiben —
# auch nicht in den Downloadordner.
SPEICHERN_UNTER = {
    "de": "Speichern unter",
    "fr": "Enregistrer sous",
    "it": "Salva con nome",
    "en": "Save as",
}


def downloads_richten() -> str:
    """Die kaputte Methode in pywebview ersetzen. Gibt zurueck, was geschah.

    `tests/test_fenster.py` ruft sie auf — ohne Fenster, ohne Anzeige.
    """
    from webview.platforms import qt as schicht

    sicht = getattr(schicht, "BrowserView", None)
    if sicht is None or not hasattr(sicht, "on_download_requested"):
        return "keine WebEngine-Schicht — nichts zu richten"

    def on_download_requested(self, anfrage):
        # Erst hier importieren und nicht weiter oben: ein Import beim Richten
        # bindet die Klasse fest ins Abschlussobjekt, und dann laesst sie sich
        # nicht mehr ersetzen. `test_fenster.py` Punkt 16 baut den Dialog nach, um
        # ohne Anzeige zu pruefen, und bekaeme sonst den echten — der braucht eine
        # QApplication und bricht den Lauf ab.
        from qtpy.QtWidgets import QFileDialog

        name = ""
        try:
            name = anfrage.downloadFileName() or ""
        except Exception:  # noqa: BLE001
            pass
        if not name:
            name = "maschera"

        titel = SPEICHERN_UNTER.get(start_sprache(), SPEICHERN_UNTER["de"])
        ziel, _ = QFileDialog.getSaveFileName(
            self, titel, str(Path.home() / name))
        if not ziel:
            # ⚠️ Abgebrochen heisst ABGEBROCHEN, nicht «wartet weiter».
            anfrage.cancel()
            return
        p = Path(ziel)
        anfrage.setDownloadDirectory(str(p.parent))
        anfrage.setDownloadFileName(p.name)
        anfrage.accept()

    sicht.on_download_requested = on_download_requested
    return "Ziel ueber Verzeichnis und Name statt setPath()"


# DAS ABLAGEFACH.
#
# Der gefaehrliche Teil ist nicht das Ablagefach, sondern sein Fehlen.
# Unter GNOME gibt es ohne AppIndicator-Erweiterung keines. Minimiert die
# App dorthin, wo kein Symbol erscheint, ist sie WEG. Deshalb wird Qt
# GEFRAGT (`isSystemTrayAvailable`), und ohne Ablagefach schliesst das X
# wie gewohnt.
#
# Gebaut wird es auf dem HAUPTFADEN. `webview.start(fn)` ruft `fn` in einem
# eigenen Faden; ein dort erzeugtes Qt-Widget laeuft manchmal und stuerzt
# manchmal ab. Deshalb haengt der Bau an `BrowserView.__init__`, und die
# laeuft in `create_window` auf dem Hauptfaden — pywebviews Klasse
# ergaenzen, statt daneben eine zweite Verdrahtung zu bauen.
#
# Ein Wort je Sprache fuer den Menueeintrag; der Tooltip kommt aus `TITEL`.
TRAY_WORTE = {
    "de": ("Beenden", "Fenster zeigen"),
    "fr": ("Quitter", "Afficher la fenêtre"),
    "it": ("Esci", "Mostra la finestra"),
    "en": ("Quit", "Show window"),
}


def tray_moeglich() -> bool:
    """Gibt es ein Ablagefach? Fragt Qt, statt es anzunehmen — und unter
    Windows, ob das Symbol aus `tray_windows_bauen()` wirklich steht."""
    if sys.platform.startswith("win"):
        return _WIN_TRAY is not None
    try:
        from qtpy.QtWidgets import QApplication, QSystemTrayIcon
        if QApplication.instance() is None:
            return False
        return bool(QSystemTrayIcon.isSystemTrayAvailable())
    except Exception:  # noqa: BLE001
        return False


def tray_bauen(sichtbar, umschalten, beenden, sprache: str = "de"):
    """Ein Ablagefachsymbol: Linksklick schaltet um, Rechtsklick beendet.

    ⚠️ Das Symbol wird AM AUFRUFER FESTGEMACHT (`sichtbar`), sonst raeumt
    Python es gleich wieder ab und es verschwindet nach einem Wimpernschlag
    aus dem Ablagefach. Ein Qt-Objekt ohne Eigentuemer lebt nur so lange
    wie sein Name in Python.

    Nimmt `umschalten` und `beenden` als Rueckrufe, damit diese Funktion
    ohne pywebview pruefbar ist — `tests/test_fenster.py` Punkt 17 ruft sie
    mit Attrappen auf.
    """
    from qtpy.QtGui import QIcon
    from qtpy.QtWidgets import QMenu, QSystemTrayIcon

    beenden_wort, zeigen_wort = TRAY_WORTE.get(sprache, TRAY_WORTE["de"])
    # Quadratisch, sonst zieht die Leiste es breit. `maske.svg` ist hoeher als
    # breit; ein Symbolthema rechnet mit einem Quadrat. Die Rechnung steht in
    # `core/symbol.py`, dieselbe fuer alle Stellen, an denen aus der Maske ein
    # Symbol wird.
    from qtpy.QtGui import QPixmap
    from core.symbol import quadratisch

    _bild = QPixmap()
    _bild.loadFromData(quadratisch(
        (Path(__file__).resolve().parent / "static" / "maske.svg"
         ).read_text(encoding="utf-8")).encode("utf-8"), "SVG")
    symbol = QIcon(_bild)
    tray = QSystemTrayIcon(symbol, sichtbar)
    tray.setToolTip(TITEL)

    # Zwei Eintraege, ueberall: «Fenster zeigen» und «Beenden».
    #
    # Unter KDE schickt Plasma beim Linksklick «Activate», und der Klick
    # kommt an. Unter GNOME mit AppIndicator kennt das Protokoll keine
    # Aktivierung: der Klick oeffnet dort nur das Menue, und stuende darin
    # allein «Beenden», waere die App sichtbar und unerreichbar.
    #
    # Die Desktopumgebung zu erkennen und den Eintrag nur dort zu setzen, waere
    # eine Heuristik ueber eine Umgebungsvariable — sie kann falsch liegen, und
    # dann ist die App unerreichbar. Ein Eintrag, den man unter KDE nicht
    # anklickt, kostet eine Zeile.
    menu = QMenu()
    menu.addAction(zeigen_wort, umschalten)
    menu.addAction(beenden_wort, beenden)
    tray.setContextMenu(menu)
    # Das Menue festmachen: `setContextMenu` uebernimmt den Besitz nicht —
    # ohne diese Zeile ist es beim ersten Rechtsklick fort.
    tray._menu = menu

    # Linksklick schaltet um. `Trigger` ist der einfache Klick, `DoubleClick`
    # der doppelte — beide meinen dasselbe, und wer zweimal klickt, will nicht
    # zweimal umschalten. Der Rechtsklick gehoert dem Menue.
    def geklickt(grund):
        if grund in (QSystemTrayIcon.ActivationReason.Trigger,
                     QSystemTrayIcon.ActivationReason.DoubleClick):
            umschalten()

    tray.activated.connect(geklickt)
    # Auch den Rueckruf festmachen, aus demselben Grund wie das Menue: ein
    # Python-Objekt ohne Namen wird abgeraeumt, und die Verbindung stirbt
    # lautlos mit ihm.
    tray._geklickt = geklickt
    tray.show()
    return tray


# DER BEENDENWUNSCH — und warum er gebraucht wird.
#
# `BrowserView.closeEvent` in `webview/platforms/qt.py`:
#
#     should_cancel = self.pywebview_window.events.closing.set()
#     if should_cancel:
#         event.ignore()
#         return
#
# Der Behandler in `main()` gibt mit Ablagefach IMMER `False` zurueck —
# das Schliessen wird also immer abgebrochen. Ein «Beenden», das `close()`
# ruft, landete in genau diesem Zweig und versteckte das Fenster nur.
#
# Kein zweiter Schliessweg als Antwort darauf, sondern ein Zustand am
# bestehenden: wer wirklich beenden will, sagt es hier, und der Behandler
# fragt zuerst danach.
#
# Ein `Event` und kein blosses `bool`: gesetzt wird aus dem Qt-Faden,
# gelesen im Behandler, und `tests/test_fenster.py` kann es setzen und
# zuruecksetzen.
BEENDEN = threading.Event()

# Ein zweiter Start hat sich gemeldet. Gesetzt vom Horchfaden in
# `core/einmalig.py`, gelesen vom Fenster in seinem eigenen Takt — ein
# Fenster aus einem fremden Faden anzufassen geht manchmal gut und
# stuerzt manchmal ab.
ZEIGEN = threading.Event()

# «Speichern & neu starten» aus den Einstellungen. Gesetzt von
# `Onboarding.neustart()`, gelesen am Ende von `main()`: erst wenn das Fenster
# zu ist, startet der Nachfolger — und der wartet, bis dieser Prozess weg
# ist (`--nach-pid`), sonst faende er ihn noch laufend, holte ihn nach vorne
# und beendete sich selbst.
NEUSTART = threading.Event()


def neustart_befehl(argv: list[str], python: str, gefroren: bool,
                    appimage: str | None, pid: int) -> list[str]:
    """Womit der Nachfolger startet — derselbe Weg wie dieser Start.

    Drei Faelle:
      gefroren (Windows)  die .exe selbst; `argv[0]` hat `windows_start.py`
                          auf `fenster.py` umgebogen und zaehlt nicht
      AppImage            die AppImage-Datei, NICHT das Python darin: der
                          Einhaengepunkt verschwindet mit diesem Prozess
      sonst               dieselbe Python mit demselben Skript
    `--model` faellt bei der AppImage weg: `AppRun` setzt ihn neu, und der
    alte Pfad zeigte in den verschwundenen Einhaengepunkt.
    """
    # `--nach-pid 123` als zwei Woerter: beide weg.
    sauber: list[str] = []
    ueberspringen = False
    for a in argv[1:]:
        if ueberspringen:
            ueberspringen = False
            continue
        if a == "--nach-pid":
            ueberspringen = True
            continue
        if a.startswith("--nach-pid="):
            continue
        sauber.append(a)
    rest = sauber
    if gefroren:
        kopf = [python]
    elif appimage:
        kopf = [appimage]
        ohne: list[str] = []
        ueberspringen = False
        for a in rest:
            if ueberspringen:
                ueberspringen = False
                continue
            if a == "--model":
                ueberspringen = True
                continue
            if a.startswith("--model="):
                continue
            ohne.append(a)
        rest = ohne
    else:
        kopf = [python, argv[0]]
    return kopf + rest + ["--nach-pid", str(pid)]


def warte_auf_ende(pid: int, frist: float = 15.0) -> bool:
    """Warten, bis der Vorgaenger weg ist. True, wenn er es ist."""
    ende = time.monotonic() + frist
    if sys.platform.startswith("win"):
        import ctypes
        kernel = ctypes.windll.kernel32
        griff = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not griff:
            return True
        try:
            return kernel.WaitForSingleObject(griff, int(frist * 1000)) == 0
        finally:
            kernel.CloseHandle(griff)
    while time.monotonic() < ende:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        time.sleep(0.2)
    return False


def neustart_ausloesen(fenster) -> None:
    """«Speichern & neu starten»: die Einstellungen sind schon gesichert.

    Nur ausloesen, nichts entgegennehmen — die neue Adresse liest der
    Nachfolger aus der gespeicherten Datei, nicht aus der Seite.
    """
    NEUSTART.set()
    BEENDEN.set()
    if _WIN_TRAY is not None:
        try:
            _WIN_TRAY.stop()
        except Exception:  # noqa: BLE001
            pass
    if fenster is None:
        neu_starten()
        return
    try:
        fenster.destroy()
    except Exception as fehler:  # noqa: BLE001
        print(f"  ⚠ Fenster nicht geschlossen ({fehler}) — Neustart hart.")
        neu_starten()


def port_uebersteuerung(umgebung=None) -> int | None:
    """`MASCHERA_PORT` — eine Uebersteuerung fuer DIESEN einen Start.

    ⚠️ Das `AppRun` versprach sie («nur als ausdrueckliche Uebersteuerung fuer
    diesen einen Start») und gab sie als `--port` an `fenster.py` weiter, das
    diese Option nicht kennt: wer die Variable setzte, bekam sofort einen
    Abbruch mit der Fehlermeldung von argparse. Eine Zusage im Kommentar
    ohne Pruefung. Jetzt liest `fenster.py` die Variable selbst.

    Gueltig ist eine ganze Zahl von 1 bis 65535; alles andere wird ignoriert
    (und gemeldet), damit ein Tippfehler nicht den Start verhindert.
    """
    roh = (os.environ if umgebung is None else umgebung).get("MASCHERA_PORT")
    if not roh:
        return None
    try:
        port = int(roh)
    except ValueError:
        port = 0
    if not 1 <= port <= 65535:
        print(f"  ⚠ MASCHERA_PORT={roh!r} ist keine Portnummer — ignoriert.")
        return None
    return port


class Bruecke:
    """Die Bruecke der laufenden Oberflaeche, wenn es kein Onboarding gibt.

    EINE Methode. Was hier steht, darf die Seite ausloesen — und sonst
    nichts. Keine oeffentlichen Felder: pywebview steigt in jedes hinein
    (siehe `Onboarding`), unter Windows endlos. `tests/test_fenster.py`
    Punkt 23 haelt beides fest.
    """

    def __init__(self):
        self._fenster = None

    def neustart(self) -> None:
        neustart_ausloesen(self._fenster)


def neu_starten() -> None:
    """Den Nachfolger starten und diesen Prozess sofort beenden.

    `os._exit` und nicht `return`: ein Faden, der nicht als Hintergrundfaden
    laeuft (das Symbol im Infobereich), hielte den Prozess am Leben — und
    damit den Einmal-Sockel und den alten Port.
    """
    import subprocess
    befehl = neustart_befehl(sys.argv, sys.executable,
                             bool(getattr(sys, "frozen", False)),
                             os.environ.get("APPIMAGE"), os.getpid())
    print(f"MASCHERA: Neustart — {' '.join(befehl)}")
    optionen: dict = {"stdin": subprocess.DEVNULL,
                      "stdout": subprocess.DEVNULL,
                      "stderr": subprocess.DEVNULL, "close_fds": True}
    if sys.platform.startswith("win"):
        optionen["creationflags"] = (subprocess.DETACHED_PROCESS
                                     | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        optionen["start_new_session"] = True
    try:
        subprocess.Popen(befehl, **optionen)
    except OSError as fehler:
        print(f"  ⚠ Neustart gescheitert ({fehler}) — bitte von Hand starten.")
    sys.stdout.flush()
    os._exit(0)


# ── Windows: Infobereich und Hervorholen ohne Qt ──────────────────────────
#
# Unter Windows nimmt pywebview Edge (WebView2), und Qt gibt es nicht. Das
# Symbol im Infobereich baut deshalb `pystray`, und den Wunsch eines zweiten
# Starts (`ZEIGEN`) liest ein kleiner Faden statt eines Qt-Zeitgebers.
# Dieselben Woerter (`TRAY_WORTE`), dasselbe Beenden-Signal (`BEENDEN`),
# dasselbe Verhalten beim Schliessen wie unter Linux.
_WIN_TRAY = None


def tray_windows_bauen(fenster, sprache: str = "de"):
    """Das Symbol im Infobereich unter Windows. Gibt das Symbol zurueck.

    Linksklick holt das Fenster hervor, das Menue traegt «Fenster zeigen» und
    «Beenden». Das Symbol laeuft in einem eigenen Faden (`run_detached`);
    pywebview gibt `show()`, `hide()` und `destroy()` von dort an den Faden
    der Anzeigeschicht weiter.
    """
    import pystray
    from PIL import Image

    beenden_wort, zeigen_wort = TRAY_WORTE.get(sprache, TRAY_WORTE["de"])
    # Dieselbe Maske, quadratisch — `favicon.ico` baut `favicon_bauen.fish`
    # schon auf das Quadrat.
    bild = Image.open(Path(__file__).resolve().parent / "static"
                      / "favicon.ico")

    def zeigen(icon=None, item=None):
        fenster.show()
        fenster.restore()

    def beenden(icon=None, item=None):
        BEENDEN.set()
        if icon is not None:
            icon.stop()
        fenster.destroy()

    menu = pystray.Menu(
        pystray.MenuItem(zeigen_wort, zeigen, default=True),
        pystray.MenuItem(beenden_wort, beenden))
    icon = pystray.Icon("maschera", bild, TITEL, menu)
    icon.run_detached()
    return icon


def zeigen_windows(fenster) -> threading.Thread:
    """Meldet sich ein zweiter Start, das Fenster hervorholen — unter Linux
    tut das ein Qt-Zeitgeber in `zeigen_richten()`."""
    def horchen():
        while not BEENDEN.is_set():
            if ZEIGEN.wait(0.5):
                ZEIGEN.clear()
                try:
                    fenster.show()
                    fenster.restore()
                except Exception:  # noqa: BLE001
                    pass
    faden = threading.Thread(target=horchen, daemon=True,
                             name="zeigen-windows")
    faden.start()
    return faden


def fenster_umschalten(w) -> str:
    """Sichtbar -> weg, weg -> sichtbar. Gibt zurueck, was geschah.

    `hide()`, nicht `showMinimized()`. Unter Wayland laesst der
    Fenstermanager ein Programm sich ohne frisches Interaktionsmerkmal
    (xdg-activation) nicht selbst hervorholen: ein minimiertes Fenster kaeme
    auf einen Klick ins Ablagefach nicht zurueck. Andere Qt-Anwendungen mit
    Ablagefach verhalten sich dort genauso — es ist die Grenze des
    Protokolls, nicht dieser Code.

    Das Ablagefach ist also ein Schalter fuer sichtbar/unsichtbar, das
    Minimieren gehoert der Fensterleiste. Ein verstecktes Fenster kommt unter
    Wayland mittig zurueck; wem die Stelle wichtig ist, dem hilft eine
    KDE-Fensterregel («Fenstereigenschaften -> Groesse & Position ->
    Position: Erinnern») zuverlaessiger, als es das Programm von innen
    koennte. Unter X11 stellt `restoreGeometry` Groesse und Lage her.

    Nicht `close()`: das liefe durch den `closing`-Behandler, der seinerseits
    versteckt — ein Umweg, der zur Falle wird, sobald jemand eine der beiden
    Stellen anfasst.

    Nimmt das Fenster als Argument, damit die Pruefung es ohne Qt mit einer
    Attrappe aufrufen kann.
    """
    if w.isVisible() and not w.isMinimized():
        # Die Lage trotzdem merken. Unter X11 stellt `restoreGeometry` sie wieder
        # her; unter Wayland ist es ein Sicherheitsnetz, das nichts kostet.
        try:
            w._maschera_lage = w.saveGeometry()
        except Exception:  # noqa: BLE001
            w._maschera_lage = None
        w.hide()
        return "versteckt"

    w.showNormal()
    # Nach `showNormal()`: auf ein unsichtbares Fenster wirkt
    # `restoreGeometry` nicht.
    lage = getattr(w, "_maschera_lage", None)
    if lage:
        try:
            w.restoreGeometry(lage)
        except Exception:  # noqa: BLE001
            pass
    # `raise_()` und `activateWindow()` gehoeren dazu. Ohne sie kommt das
    # Fenster unter Umstaenden hinter dem zurueck, was gerade vorne steht.
    w.raise_()
    w.activateWindow()
    return "gezeigt"


def symbol_richten() -> str:
    """Dem Fenster die Maske als Symbol geben. Gibt zurueck, was geschah.

    Ohne das traegt das Fenster pywebviews eigenes Symbol. Gesetzt wird es AM
    FENSTER und AN DER ANWENDUNG: das eine traegt die Titelleiste, das andere
    die Fensterliste und den Anwendungswechsler.

    Dieselbe Datei wie Kopfzeile, Startbild, Ablagefach und Paketsymbol.
    """
    from webview.platforms import qt as schicht

    sicht = getattr(schicht, "BrowserView", None)
    if sicht is None:
        return "keine WebEngine-Schicht — kein Symbol"
    if getattr(sicht, "_maschera_symbol", False):
        return "schon gerichtet"

    alt = sicht.__init__

    def __init__(self, fenster):
        alt(self, fenster)
        try:
            from qtpy.QtGui import QIcon
            from qtpy.QtWidgets import QApplication
            pfad = Path(__file__).resolve().parent / "static" / "maske.svg"
            symbol = QIcon(str(pfad))
            self.setWindowIcon(symbol)
            anwendung = QApplication.instance()
            if anwendung is not None:
                anwendung.setWindowIcon(symbol)
        except Exception as e:  # noqa: BLE001
            # Nicht toedlich — ein Fenster mit fremdem Symbol laeuft. Aber
            # nicht still: sonst sucht beim naechsten Bericht jemand an
            # der falschen Stelle.
            print(f"  ⚠ Fenstersymbol nicht gesetzt ({type(e).__name__}: {e})")

    sicht.__init__ = __init__
    sicht._maschera_symbol = True
    return "Maske als Fenstersymbol"


def zeigen_richten() -> str:
    """Das Fenster sieht in seinem Takt nach, ob sich jemand gemeldet hat.

    Ein Takt und kein Rueckruf aus dem Faden: der Horcher laeuft in einem
    eigenen Faden, und von dort ein Fenster zu zeigen hiesse, aus einem
    fremden Faden in Qt zu greifen. Ein Viertelsekundentakt kostet nichts
    und ist offensichtlich richtig.

    Der Takt haengt AM FENSTER (`QTimer(self)`), nicht am Modul. Ohne
    Eigentuemer raeumt Python ihn ab, und er hoert lautlos auf.
    """
    from webview.platforms import qt as schicht

    sicht = getattr(schicht, "BrowserView", None)
    if sicht is None:
        return "keine WebEngine-Schicht — kein Einmal-Start"
    if getattr(sicht, "_maschera_zeigen", False):
        return "schon gerichtet"

    alt = sicht.__init__

    def __init__(self, fenster):
        alt(self, fenster)
        try:
            from qtpy.QtCore import QTimer

            def nachsehen():
                if ZEIGEN.is_set():
                    ZEIGEN.clear()
                    # Immer ZEIGEN, nie umschalten: wer das Symbol im Startmenue anklickt,
                    # will die App sehen — auch wenn sie schon offen ist.
                    self.showNormal()
                    self.raise_()
                    self.activateWindow()

            takt = QTimer(self)
            takt.timeout.connect(nachsehen)
            takt.start(250)
            self._maschera_takt = takt
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ Einmal-Start nicht am Fenster "
                  f"({type(e).__name__}: {e})")

    sicht.__init__ = __init__
    sicht._maschera_zeigen = True
    return "zweiter Start zeigt dieses Fenster"


def tray_richten(sprache: str = "de") -> str:
    """`BrowserView` um ein Ablagefach ergaenzen. Gibt zurueck, was geschah."""
    from webview.platforms import qt as schicht

    sicht = getattr(schicht, "BrowserView", None)
    if sicht is None:
        return "keine WebEngine-Schicht — kein Ablagefach"
    if getattr(sicht, "_maschera_tray", False):
        return "schon gerichtet"

    alt = sicht.__init__

    def __init__(self, fenster):
        alt(self, fenster)
        if not tray_moeglich():
            # Kein Ablagefach: dann bleibt das X das X. Nicht still — sonst sucht
            # der Anwender eine Einstellung, die nichts tut.
            print("  ⚠ Kein Ablagefach vorhanden (GNOME ohne "
                  "AppIndicator?) — das Fenster schliesst wie bisher.")
            return

        def beenden():
            # Zuerst merken, dann schliessen. Andersherum liefe `close()` durch den
            # Behandler, der noch nichts weiss, und das Fenster versteckte sich
            # wieder.
            BEENDEN.set()
            self.close()

        try:
            self._maschera_tray = tray_bauen(
                self, lambda: fenster_umschalten(self), beenden, sprache)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ Ablagefach nicht gebaut ({type(e).__name__}: {e})")

    sicht.__init__ = __init__
    sicht._maschera_tray = True
    return "Ablagefach am Fenster, auf dem Hauptfaden"


def belegt(adresse: str, port: int) -> str | None:
    """Laesst sich dort binden? Gibt den Grund zurueck, sonst None.

    Geprueft wird BINDEN, nicht verbinden: ein Port kann von einem Dienst
    gehalten werden, der nicht antwortet, und dann scheitert der Start
    trotzdem. Gefragt ist genau das, was gleich getan wird.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((adresse, port))
        return None
    except OSError as e:
        return str(e)


def naechster_freier(adresse: str, port: int, weite: int = 50) -> int | None:
    """Der naechste freie Port aufwaerts.

    Seit 0.9.63 nimmt `main()` ihn ohne Rueckfrage (Entscheid des Anwenders):
    der Qt-Dialog, der vorher fragte, war nur deutsch und brach unter Windows
    den Start ab, weil es dort kein Qt gibt. Sichtbar bleibt der Port in den
    Einstellungen, und die Wahl wird gesichert.

    ⚠️ Das ist nur tragbar, weil `core/einmalig.py` VORHER prueft, ob
    MASCHERA schon laeuft. Ein belegter Port heisst hier: ein ANDERES
    Programm. Ohne die Einmal-Pruefung suchte sich jeder weitere Start
    seinen eigenen Port — so gingen einmal drei Fenster auf.
    """
    for kandidat in range(port + 1, min(port + weite, 65536)):
        if belegt(adresse, kandidat) is None:
            return kandidat
    return None


class Onboarding:
    """Was der Startbildschirm nach Python zurueckrufen darf.

    Vier Methoden und sonst nichts. `js_api` macht jede oeffentliche Methode
    dieser Klasse fuer die Seite aufrufbar; was hier steht, ist die ganze
    Angriffsflaeche. Deshalb keine Bequemlichkeitsmethoden und kein
    Durchreichen von Pfaden — die Seite nennt nichts, sie loest nur aus.

    Der eigentliche Holweg steht in `core/modell.py` und weiss nichts von
    Fenstern; `tests/test_modell.py` prueft den Kern ohne Anzeige.
    """

    def __init__(self, m: dict, ziel, weiter_ereignis):
        self._m = m
        self._ziel = ziel
        self._weiter = weiter_ereignis
        self._abbruch = False
        self._faden = None
        # ⚠️ Alles, was nicht Methode ist, beginnt mit `_`. pywebview macht
        # jedes oeffentliche Feld fuer die Seite erreichbar und steigt dafuer
        # hinein — ein oeffentliches `fenster` gaebe der Seite das ganze
        # Fensterobjekt, und unter Windows (WinForms) laeuft das Hineinsteigen
        # endlos: `native.AccessibilityObject.Bounds.Empty.Empty…`, bis der
        # Speicher voll ist. `tests/test_fenster.py` Punkt 23 haelt das fest.
        self._geholt = False
        self._fenster = None     # setzt `main()`, sobald es steht

    # -- von der Seite gerufen ---------------------------------------------

    def sprache(self, code: str) -> None:
        """Die Wahl im Willkommensschritt festhalten.

        Sie gilt ueber den Start hinaus, sonst waere der Schalter eine Bedienung,
        die nichts bewirkt. Geschrieben wird in dieselbe Datei, die auch die
        Oberflaeche fuehrt.
        """
        try:
            from core import einstellungen
            e = einstellungen.lade()
            if code in einstellungen.SPRACHEN and code != e.get("sprache"):
                einstellungen.speichere({**e, "sprache": code})
        except Exception as fehler:  # noqa: BLE001
            # ⚠️ Nicht abbrechen: eine nicht gesicherte Sprachwahl ist
            # aergerlich, ein Startbildschirm, der daran stirbt, ist
            # schlimmer. Aber auch nicht still.
            print(f"  ⚠ Sprachwahl nicht gesichert ({fehler})")

    def weiter(self) -> None:
        """Vom Willkommensschritt in die Anwendung."""
        self._weiter.set()

    def spaeter(self) -> None:
        """Ohne Modell kein Betrieb — die Anwendung schliesst sich.

        Das ist kein Ausweg in einen halben Betriebszustand: ein Fenster, das
        sich ohne Modell bedienen laesst, waere eine Leckquelle mit gruener
        Anzeige. `--ohne-modell` bleibt eine Messhilfe der Kommandozeile.

        Waehrend eines laufenden Downloads heisst der Knopf ABBRECHEN. Dann wird
        dem Faden Bescheid gegeben und auf ihn GEWARTET — `core.modell` raeumt
        seine `.teil` selbst weg, und wer den Prozess vorher beendet, laesst sie
        liegen.
        """
        self._abbruch = True
        BEENDEN.set()
        faden = self._faden
        if faden is not None and faden.is_alive():
            print("MASCHERA: Abbruch — es wird aufgeraeumt …")
            faden.join(timeout=15)
        print("MASCHERA: ohne Modell kein Betrieb. Beendet.")
        # ⚠️ Damit `laden_und_starten` nicht ewig auf das Onboarding
        # wartet. Es prueft danach `BEENDEN` und kehrt zurueck.
        self._weiter.set()
        if self._fenster is None:
            return
        try:
            self._fenster.destroy()
        except Exception as fehler:  # noqa: BLE001
            # Nicht verschlucken. Schliesst sich das Fenster nicht, bliebe die
            # Anwendung offen UND `_abbruch` auf True — der naechste Klick auf
            # «Herunterladen» braeche sofort ab, und niemand wuesste warum.
            print(f"  ⚠ Das Fenster liess sich nicht schliessen "
                  f"({type(fehler).__name__}: {fehler}).")
            print("    Harter Abgang, damit nicht ein halber Zustand "
                  "stehenbleibt.")
            os._exit(0)

    def neustart(self) -> None:
        """«Speichern & neu starten» — siehe `neustart_ausloesen()`."""
        neustart_ausloesen(self._fenster)

    def holen(self) -> None:
        """Das Modell holen. Laeuft im eigenen Faden, meldet in die Seite.

        Eigener Faden: `js_api` ruft auf dem Faden der Anzeigeschicht, und 1,3 GB
        darin wuerden das Fenster einfrieren — genau waehrend der Anwender wissen
        will, ob noch etwas passiert.
        """
        # Den Abbruch zuruecksetzen. Sonst erbt ein zweiter Anlauf die
        # Entscheidung des ersten und bricht sofort wieder ab, bevor der erste
        # Datenblock kommt. Dasselbe gilt fuer «Nochmals versuchen» nach einem
        # gescheiterten Versuch.
        self._abbruch = False
        self._faden = threading.Thread(target=self._holen, daemon=True)
        self._faden.start()

    # -- innen --------------------------------------------------------------

    def _melde(self, ruf: str) -> None:
        try:
            if self._fenster is not None:
                self._fenster.evaluate_js(ruf)
        except Exception:  # noqa: BLE001
            pass

    def _holen(self) -> None:
        from core import modell as kern
        gesamt = max(1, kern.groesse(self._m))
        fertige: dict = {}

        def melde(name, geholt, soll):
            # Der Balken zaehlt ueber ALLE Dateien. `melde` bekommt den Stand der
            # laufenden; ohne diese Rechnung fiele er bei jeder Datei auf null zurueck.
            fertige[name] = geholt
            anteil = min(sum(fertige.values()) / gesamt, 1.0)
            self._melde(f"fortschritt({int(anteil * 1000)}, "
                        f"{json.dumps(name)})")

        try:
            kern.hole(self._m, self._ziel, melde=melde,
                      abbruch=lambda: self._abbruch)
        except Exception as fehler:  # noqa: BLE001
            # Schluessel und Werte, nicht der fertige Satz: dieses Modul spricht
            # Deutsch, die Seite vier Sprachen. Der Rohtext faehrt mit, damit ein
            # unbekannter Fehler nicht sprachlos dasteht.
            self._melde("gescheitert({}, {}, {})".format(
                json.dumps(getattr(fehler, "schluessel", "")),
                json.dumps(getattr(fehler, "werte", {})),
                json.dumps(str(fehler))))
            return
        self._geholt = True
        self._melde("fertig()")
        self._weiter.set()


def main() -> int:
    # Als Erstes, vor jedem `print`: manche Starter haengen eine Pipe an die
    # Ausgabe und beenden sich, waehrend das Modell noch laedt. Siehe
    # `core/ausgabe.py`.
    from core import ausgabe
    ausgabe.sichern()

    # So frueh wie moeglich: wer den Prozess sucht, sucht ihn meist, weil
    # etwas haengt — dann ist er womoeglich noch gar nicht fertig gestartet.
    from core import prozess
    prozess.benenne()


    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--onnx", default=None)
    ap.add_argument("--ohne-modell", action="store_true")
    ap.add_argument("--pack", default="ch")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--regeln", default=None)
    ap.add_argument("--im-browser", action="store_true",
                    help="statt eines Fensters den Browser oeffnen")
    ap.add_argument("--nach-pid", type=int, default=None,
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    # Nach «Speichern & neu starten»: erst wenn der Vorgaenger weg ist, sind
    # Einmal-Sockel und Port frei.
    if args.nach_pid:
        warte_auf_ende(args.nach_pid)

    # Ohne Angabe wird gesucht — und wenn nichts da ist, gefragt. Wer eine
    # App doppelklickt, gibt keine Argumente mit.
    #
    # Zwei Zuschnitte, ein Weg hier durch:
    #
    #   fett     `runs/<name>` liegt neben dem Code -> `suche()` findet es,
    #            das Onboarding kommt nie. So faehrt die AppImage.
    #   schlank  nichts da -> die Frage, einmal. Danach ist es da.
    #
    # `--ohne-modell` bleibt als Messhilfe moeglich, wird hier aber NICHT als
    # Ausweg angeboten: ohne Modell geht jeder Name durch.
    #
    # Das Fenster steht vor dem Modell: es ist EIN Bildschirm — derselbe
    # Startbildschirm, der ohnehin steht, mit einem Schritt davor.
    # `laden_und_starten` laedt in einem eigenen Faden nach; das Onboarding
    # haelt diesen Moment nur an.
    _onboarding = None
    _schritt = "s_laden"
    _orte = None
    WEITER = threading.Event()
    WEITER.set()

    if not (args.model or args.onnx or args.ohne_modell):
        # Hier importieren und nicht erst weiter unten. `einstellungen` wird in
        # `main()` nochmals geholt; ein Import irgendwo im Rumpf macht den Namen
        # fuer die GANZE Funktion lokal, und jede Benutzung davor ist ein
        # `UnboundLocalError`. Die Zeile laeuft nur, wenn kein Modell angegeben ist
        # — also genau beim ersten Start eines schlanken Pakets.
        from core import einstellungen
        from core import modell as _modell
        try:
            _m = _modell.manifest(args.pack)
        except _modell.Abgelehnt as e:
            ap.error(f"{e}")
        _gefunden = _modell.suche(_m["name"])
        _ziel = _modell.modell_ziel(_m["name"])

        if _gefunden is None and args.im_browser:
            # Kein schlankes Paket ohne Fenster: `--im-browser` hat keine
            # Anzeigeschicht fuer das Onboarding, und ungefragt zu holen ist
            # ausgeschlossen. Also wird gesagt, was zu tun ist.
            print(f"MASCHERA: das Modell {_m['name']} fehlt "
                  f"({_modell.groesse(_m) / 1e9:.1f} GB).")
            print("  Ohne Fenster wird nicht gefragt und deshalb auch "
                  "nicht geholt.")
            print("  Einmal ohne --im-browser starten, dann kommt die "
                  "Frage.")
            return 1

        # Willkommen beim ersten Start UND wenn das Modell fehlt. Wer «Spaeter»
        # gewaehlt oder das Modell geloescht hat, kaeme sonst in eine Sackgasse —
        # und er soll die Sprache setzen koennen, BEVOR er 1,3 GB holt.
        _erststart = not einstellungen.PFAD.is_file()
        if _gefunden is None or _erststart:
            _schritt = "s_willkommen"
            WEITER.clear()
            _onboarding = Onboarding(_m, _ziel, WEITER)
            _gb = f"{_modell.groesse(_m) / 1e9:.1f}".replace(".", ",")
            # ⚠️ Lang UND kurz. Die kurze Form steht auf dem Bildschirm,
            # die lange bleibt dabei — wer sie braucht (Fehlersuche,
            # Fehlerbericht), soll sie nicht rekonstruieren muessen.
            _lang = _m["quelle"].split("{")[0].rstrip("/")
            _kurz = (_lang.removeprefix("https://").removeprefix("http://")
                          .removesuffix("/resolve/main"))
            _heim = str(Path.home())
            _zielkurz = str(_ziel)
            if _zielkurz.startswith(_heim + "/"):
                _zielkurz = "~" + _zielkurz[len(_heim):]
            _orte = {"fehlt": _gefunden is None, "name": _m["name"],
                     "gb": _gb,
                     "quelle": _lang, "quelle_kurz": _kurz,
                     "ziel": str(_ziel), "ziel_kurz": _zielkurz}
        if _gefunden is not None:
            args.model = str(_gefunden)

    # Einmal lesen, mehrfach benutzt: Fenstermass, Ablagefach und die
    # Sprache seiner Eintraege. `lade()` faellt bei einer kaputten Datei auf
    # die Vorgabe zurueck und wirft nicht. Der Import deckt den Fall ab, dass
    # oben ein Modell angegeben war.
    from core import einstellungen                        # noqa: F811
    _einst = einstellungen.lade()
    _sprache = _einst.get("sprache", "de")

    # Hier wird nichts geladen. `from serve import Zustand` zieht torch und
    # transformers nach, und das Modell kostet nochmals Sekunden. Beides
    # passiert weiter unten in einem eigenen Faden, DAMIT DAS FENSTER VORHER
    # DASTEHT.

    def dienst_starten(wirt, port):
        """Modell laden, Dienst in einem Faden starten.

        Eine Fassung fuer alle drei Wege — Fenster, `--im-browser` und der
        Rueckfall ohne Anzeigeschicht.
        """
        from app import baue_mit_oberflaeche
        from serve import VERSION, Zustand

        z = Zustand(args.pack, args.model, args.onnx, args.max_length,
                    args.regeln)
        dienst = baue_mit_oberflaeche(z)

        print(f"MASCHERA {VERSION} · Pack {args.pack} · "
              f"Labelvertrag {z.pack.get_label_hash()[:8]}")
        if z.ohne_modell:
            # Auch im Fenster: `--ohne-modell` ist kein Betriebszustand, und die
            # Warnung darf nicht verschwinden, weil kein Terminal sichtbar ist.
            print("  ⚠ OHNE MODELL — Namen, Daten und Adressen bleiben "
                  "im Klartext.")
        else:
            print(f"  Modell {z.modellname}")

        # ⚠️ `daemon=True`: schliesst der Anwender das Fenster, endet der
        # Dienst mit. Ohne das bliebe ein Flask-Server im Speicher stehen,
        # der Personendaten verarbeitet hat, und niemand saehe ihn.
        threading.Thread(
            target=lambda: dienst.run(host=wirt, port=port,
                                      threaded=True, debug=False,
                                      use_reloader=False),
            daemon=True,
        ).start()

    def warte_auf(adresse):
        """Warten, bis der Dienst wirklich antwortet. Sofort umzuschalten zeigte
        eine Fehlerseite: der Faden braucht einen Augenblick, bis er horcht.
        """
        import urllib.request
        for _ in range(200):                          # hoechstens 20 s
            try:
                urllib.request.urlopen(adresse + "api/zustand", timeout=1)
                return True
            except Exception:  # noqa: BLE001
                time.sleep(0.1)
        return False

    def laden_und_starten(fenster, adresse, wirt, port):
        """Laden, warten, dann auf die Oberflaeche umschalten.

        Laeuft in einem eigenen Faden, nachdem das Fenster steht.
        """
        try:
            # Erst auf das Onboarding warten. Bei einem gewoehnlichen Start ist das
            # Ereignis schon gesetzt, und es wird nicht gewartet.
            WEITER.wait()
            if BEENDEN.is_set():
                return
            # Das Modell kann erst jetzt dastehen: der Anwender hat es gerade
            # geholt. Deshalb nochmals suchen und nicht die Antwort von vorhin
            # glauben.
            if not (args.model or args.onnx or args.ohne_modell):
                from core import modell as _mo
                _jetzt = _mo.suche(_mo.manifest(args.pack)["name"])
                if _jetzt is None:
                    raise SystemExit("Das Modell fehlt weiterhin.")
                args.model = str(_jetzt)
            dienst_starten(wirt, port)
            warte_auf(adresse)
            fenster.load_url(adresse)
        except Exception as e:  # noqa: BLE001
            # Der Fehler gehoert INS FENSTER: wer die AppImage anklickt, hat kein
            # Terminal davor.
            print(f"  ✖ Start fehlgeschlagen: {type(e).__name__}: {e}")
            fenster.load_html(
                "<body style='font-family:system-ui;padding:2rem;"
                "line-height:1.5'><h2>MASCHERA konnte nicht starten</h2>"
                f"<p><b>{type(e).__name__}</b></p><pre style='white-space:"
                f"pre-wrap'>{e}</pre></body>")

    # Adresse und Port kommen aus den GESPEICHERTEN Einstellungen, nicht aus
    # einer Zahl im Code und nicht aus einem Zufallsport.
    from core import einstellungen as est

    gespeichert = est.lade()
    wirt = gespeichert.get("adresse") or "127.0.0.1"
    port = int(gespeichert.get("port") or est.VORGABE_PORT)
    # Eine Uebersteuerung gilt nur fuer diesen Start und wird NIE gespeichert
    # (weder hier noch beim Ausweichen unten).
    ueberstimmt = port_uebersteuerung()
    if ueberstimmt is not None:
        port = ueberstimmt
        print(f"  MASCHERA_PORT: Port {port} nur fuer diesen Start.")

    # Laeuft schon eine? Gefragt wird VOR dem Modell — das laedt Sekunden,
    # und ein zweiter Start soll in einem Wimpernschlag wieder weg sein. Die
    # Frage ist nicht, OB der Port belegt ist, sondern WER ihn haelt (siehe
    # `core/einmalig.py`).
    #
    # Nicht im Browserzweig: `--im-browser` ist der ausdrueckliche Ausweg fuer
    # einen zweiten Blick auf dieselbe Sitzung.
    if not args.im_browser:
        from core import einmalig
        if einmalig.laeuft_schon():
            print("MASCHERA laeuft bereits — das laufende Fenster kommt "
                  "nach vorne.")
            return 0
        einmalig.horche(ZEIGEN.set)

    grund = belegt(wirt, port)
    if grund is not None:
        frei = naechster_freier(wirt, port)
        if frei is None:
            print(f"  ABBRUCH: {wirt}:{port} ist belegt — {grund} — und "
                  f"auch die naechsten 50 Ports")
            return 1
        print(f"  {wirt}:{port} ist belegt ({grund}) — weiche aus auf {frei}")
        port = frei
        # ⚠️ Sofort sichern, nicht erst beim Beenden. Wer das Fenster
        # hart schliesst, soll die Wahl trotzdem behalten — sonst fragt
        # das Werkzeug jedes Mal dasselbe.
        try:
            if ueberstimmt is not None:
                print("  (Die Uebersteuerung wird nicht gespeichert.)")
            else:
                est.speichere({**gespeichert, "adresse": wirt, "port": port})
                print(f"  Neue Adresse gesichert: {wirt}:{port}")
        except (est.Abgelehnt, OSError) as e:
            # Kein Abbruch — der Start soll gelingen. Aber nicht still:
            # sonst glaubt der Anwender, es sei gemerkt.
            print(f"  ⚠ Nicht gesichert ({e}) — gilt nur diese Sitzung.")

    adresse = f"http://{wirt}:{port}/"

    if args.im_browser:
        import webbrowser
        dienst_starten(wirt, port)
        warte_auf(adresse)
        print(f"  {adresse}")
        webbrowser.open(adresse)
        threading.Event().wait()
        return 0

    def im_browser(warum: str) -> int:
        # ⚠️ KEIN STILLER RUECKFALL. Wer hier im Browser landet, ohne es zu
        # erfahren, glaubt, das sei die Anwendung — und sieht eine
        # Adresszeile, wo keine sein sollte.
        print(f"  ⚠ Kein Fenster moeglich: {warum}")
        print("     Es geht im Browser weiter, und das ist NICHT dasselbe:")
        print("     ein Fenster mit Adresszeile sieht aus wie eine Webseite.")
        print(f"     {adresse}")
        import webbrowser
        dienst_starten(wirt, port)
        warte_auf(adresse)
        webbrowser.open(adresse)
        threading.Event().wait()
        return 0

    try:
        import webview
    except ImportError as e:
        return im_browser(f"`pywebview` fehlt ({e})")

    # Der Import allein genuegt nicht: `pywebview` laedt seine Anzeigeschicht
    # erst beim Start und sucht dann `qtpy` oder `gi`. `pywebview` ohne das
    # Extra `[qt]` bringt `qtpy` nicht mit — ein Fehler, der nur in einer
    # Verpackung auftritt und erst beim Start stirbt.
    #
    # Vor `create_window`: `BrowserView.WebPage.__init__` verbindet den Slot
    # beim Anlegen des Fensters; danach zu ersetzen kaeme zu spaet.
    # Nur unter Linux nimmt pywebview Qt. Unter Windows (Edge/WebView2) und
    # macOS (WebKit) gibt es die Qt-Fehler nicht, die diese Eingriffe
    # beheben — dort waere die Warnung unten eine falsche Faehrte.
    if not sys.platform.startswith("linux"):
        print(f"  Anzeigeschicht: nicht Qt ({sys.platform}) — Qt-Eingriffe "
              f"entfallen")
    else:
        try:
            print("  Berechtigungen: " + berechtigungen_richten())
            print("  Herunterladen:  " + downloads_richten())
            print("  Fenstersymbol:  " + symbol_richten())
            print("  Einmal-Start:   " + zeigen_richten())
            if _einst.get("tray"):
                print("  Ablagefach:     " + tray_richten(_sprache))
        except Exception as e:  # noqa: BLE001
            # Kein Abbruch — aber laut. Ohne diese Ersetzung stirbt das
            # Fenster beim ersten Kopierknopf, und zwar wortlos.
            print(f"  ⚠ Qt-Eingriffe NICHT gerichtet ({type(e).__name__}: {e})")
            print("     Das Fenster stuerzt beim Kopieren ab, und das")
            print("     Herunterladen tut nichts. Siehe fenster.py.")

    try:
        # Das Fenster traegt zuerst die STARTSEITE und nicht die Adresse: den
        # Dienst gibt es noch gar nicht. Es steht damit nach rund einer Sekunde da.
        #
        # Zwei Masse, ein Fenster: der Widget-Modus ist dasselbe Fenster schmal
        # und im Vordergrund. Die einspaltige Ansicht greift ab 59.99em und damit
        # hier von selbst.
        # Ohne Onboarding die kleine Bruecke — sonst haette die laufende
        # Oberflaeche keinen Weg zu «Speichern & neu starten».
        _bruecke = _onboarding if _onboarding is not None else Bruecke()
        if _einst.get("fenstermodus") == "widget":
            breite = einstellungen.WIDGET_BREITE
            # Die Untergrenze ist die Breite selbst. Gemessen liegt die Grenze bei
            # 378 (siehe `core/einstellungen.py`); eine Untergrenze darunter liesse das
            # Fenster in einen Zustand ziehen, in dem es nicht mehr passt.
            fenster = webview.create_window(
                TITEL, html=startseite(_schritt, _orte),
                js_api=_bruecke,
                width=breite, height=900,
                min_size=(breite, 480), on_top=True)
        else:
            fenster = webview.create_window(
                TITEL, html=startseite(_schritt, _orte),
                js_api=_bruecke,
                width=1400, height=900, min_size=(900, 600))
        # Die Bruecke braucht das Fenster, um in die Seite zu melden — und es
        # gibt es erst jetzt. Ohne diese Zeile stuende der Balken still.
        _bruecke._fenster = fenster

        # Das X versteckt, wenn das Ablagefach steht: `closing` bricht das
        # Schliessen ab, sobald ein Behandler `False` zurueckgibt.
        #
        # Nur mit Ablagefach: ohne Symbol waere die App nach dem X unerreichbar.
        # `tray_moeglich()` fragt Qt, und zwar HIER — beim Start gab es die
        # QApplication noch nicht.
        if _einst.get("tray"):
            def beim_schliessen():
                # Der Beendenwunsch zuerst. Ohne diese Abfrage braeche der Behandler
                # JEDES Schliessen ab — auch das aus dem Ablagefachmenue. Siehe `BEENDEN`
                # weiter oben.
                if BEENDEN.is_set():
                    return True
                if not tray_moeglich():
                    return True
                # Verstecken, nicht minimieren — siehe `fenster_umschalten()`.
                fenster.hide()
                return False
            fenster.events.closing += beim_schliessen
        # Unter Windows gibt es weder die Qt-Eingriffe noch den Qt-Zeitgeber:
        # das Symbol im Infobereich baut `pystray`, den Wunsch eines zweiten
        # Starts liest ein eigener Faden.
        if sys.platform.startswith("win"):
            global _WIN_TRAY
            zeigen_windows(fenster)
            if _einst.get("tray"):
                try:
                    _WIN_TRAY = tray_windows_bauen(fenster, _sprache)
                    print("  Infobereich:    Symbol steht")
                except Exception as e:  # noqa: BLE001
                    # Ohne Symbol gibt `beim_schliessen` das Schliessen frei —
                    # die App ist nie unsichtbar und unerreichbar.
                    print(f"  ⚠ Infobereich nicht gebaut "
                          f"({type(e).__name__}: {e}) — das X beendet")

            def symbol_weg():
                if _WIN_TRAY is not None:
                    _WIN_TRAY.stop()
            fenster.events.closed += symbol_weg
        # `webview.start(fn)` ruft `fn` in einem eigenen Faden, NACHDEM die
        # Anzeigeschicht laeuft. Vorher zu laden hiesse, `load_url` auf einem
        # Fenster zu rufen, das es noch nicht gibt.
        webview.start(laden_und_starten,
                      (fenster, adresse, wirt, port))
    except Exception as e:  # noqa: BLE001
        return im_browser(f"keine Anzeigeschicht ({type(e).__name__}: {e})")
    if NEUSTART.is_set():
        neu_starten()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
