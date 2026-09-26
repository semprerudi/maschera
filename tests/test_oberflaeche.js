#!/usr/bin/env node
/* Die Oberflaechenlogik gegen eine strenge DOM-Attrappe.
 *
 *     node tests/test_oberflaeche.js
 *
 * Ein Fehler in der Oberflaeche steht oft nur in der Browserkonsole: wirft
 * eine Zeichenfunktion mitten drin, bleibt alles danach unverdrahtet, und
 * weder die Serverpruefungen noch das Protokoll zeigen etwas.
 *
 * Deshalb ist diese Attrappe STRENG:
 *   - `getElementById` liefert null fuer alles, was nicht im HTML steht
 *   - `remove()` und `hidden` werden mitgefuehrt; ein entferntes Element
 *     ist danach nicht mehr auffindbar
 *   - jeder Zugriff auf null wirft, wie im Browser
 *
 * Eine grosszuegige Attrappe verschluckt genau solche Fehler.
 */
"use strict";

const fs = require("fs");

/* ⚠️ CODE OHNE KOMMENTARE. Eine Pruefung, die nach einer Zeichenkette
 * sucht, findet sie sonst auch in dem Kommentar, der ERKLAERT, warum sie
 * nicht dastehen darf — und schlaegt genau dann an, wenn alles richtig
 * ist.
 *
 * ⚠️ Und es ist die Voraussetzung dafuer, die Kommentare ueberhaupt
 * anfassen zu koennen: eine Wache, die am Wortlaut eines Kommentars
 * haengt, verbietet stillschweigend, ihn umzuschreiben.
 */
function ohneKommentare(text) {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, " ")   // Blockkommentare, CSS wie JS
    .replace(/(^|[^:])\/\/.*$/gm, "$1");   // Zeilenkommentare, `://` ausgenommen
}
const path = require("path");

const WURZEL = path.resolve(__dirname, "..");
const HTML = fs.readFileSync(
  path.join(WURZEL, "app/static/index.html"), "utf8");

let fehler = 0;
// ⚠️ EIN HAENGENDES VERSPRECHEN IST KEIN BESTANDEN. Wartet eine Pruefung
// auf etwas, das nie eintritt, hat Node nichts mehr zu tun und endet —
// still, mit Rueckgabewert 0, mitten in einem Punkt. So lief Punkt 79 mit
// einem abgeschalteten Escape «gruen» durch. Nur wer das Ende erreicht,
// darf mit 0 enden.
let amEnde = false;
process.on("exit", (code) => {
  if (!amEnde && code === 0) {
    console.log("   FEHL die Pruefung endete vor ihrem Ende — ein "
                + "Versprechen haengt");
    process.exitCode = 1;
  }
});
function pruefe(ok, was) {
  if (!ok) { fehler++; console.log("   FEHL " + was); }
}

// Kennungen aus dem HTML — nur die gibt es.
const imHtml = new Set(
  [...HTML.matchAll(/id="([A-Za-z0-9_-]+)"/g)].map((m) => m[1]));

const knoten = {};
const entfernt = new Set();

function mach(id) {
  const o = {
    id, textContent: "", value: "", title: "", disabled: false, hidden: false,
    offsetWidth: 0, clientWidth: 0,
    className: "", style: {}, dataset: {}, files: [], _h: {}, _attr: {},
    _kinder: [],
    // ⚠️ Eine echte Menge. Eine Attrappe, die jede Klasse vergisst, liesse
    // alles ungeprueft, was ueber eine Klasse geht — und das ist in dieser
    // Oberflaeche die halbe Anzeige.
    _klassen: new Set(),
    classList: {
      add(...ks) { for (const k of ks) o._klassen.add(k); },
      remove(...ks) { for (const k of ks) o._klassen.delete(k); },
      toggle(k, an) {
        const soll = an === undefined ? !o._klassen.has(k) : !!an;
        if (soll) o._klassen.add(k); else o._klassen.delete(k);
        return soll;
      },
      contains(k) { return o._klassen.has(k); },
    },
    setAttribute(k, v) { o._attr[k] = v; },
    getAttribute(k) { return o._attr[k] === undefined ? null : o._attr[k]; },
    addEventListener(ev, fn) { (o._h[ev] = o._h[ev] || []).push(fn); },
    // ⚠️ Angehaengte Knoten mitschreiben. Sonst waere jede Anzeige, die aus
    // erzeugten Elementen besteht, ungeprueft: Fundstellen, Legende, und vor
    // allem die Meldung ueber nicht zugeordnete Platzhalter.
    append(...kinder) {
      for (const k of kinder) o._kinder.push(k);
      if (o.id === "offen05" || o.id === "gut05") {
        for (const k of kinder) angehaengt.push(text(k));
      }
    },
    replaceChildren(...kinder) {
      o._kinder = [];
      if (o.id === "offen05" || o.id === "gut05") angehaengt.length = 0;
      o.append(...kinder);
    },
    appendChild(k) { o.append(k); },
    prepend(...kinder) { o._kinder.unshift(...kinder); },
    focus() {}, blur() {}, select() {},
    // ⚠️ Mitschreiben, nicht verschlucken: die gestapelte Ansicht springt
    // zum naechsten Schritt, und eine Attrappe, die `scrollIntoView` still
    // schluckt, wuerde das nie pruefen.
    _gerollt: [],
    scrollIntoView(wie) { o._gerollt.push(wie || {}); },
    // ⚠️ `_top` ist SETZBAR. Eine Attrappe, die jedem Element `top: 0`
    // gibt, laesst jede Rechnung mit Abstaenden auf 0 - 0 hinauslaufen —
    // sie ist dann nicht streng, sondern blind. Punkt 65 setzt es.
    _top: 0,
    // ⚠️ `_hoehe` ebenfalls setzbar, und aus demselben Grund. Sie stand
    // fest auf 0, und damit war der Abzug der Kopfzeile in `springeZu()`
    // IMMER 0 — die Wache war gruen und prueft an der Stelle nichts. Beim
    // Schreiben aufgefallen, nicht im Gebrauch: eine Attrappe, die eine
    // Zahl verschweigt, verschweigt jede Rechnung damit.
    _hoehe: 0,
    getBoundingClientRect() {
      return { top: o._top, left: 0, width: 0, height: o._hoehe };
    },
    remove() { entfernt.add(id); },
    querySelector() { return mach("_kind"); },
    querySelectorAll() { return []; },
  };
  return o;
}

global.document = {
  // ⚠️ `style.setProperty` und `appendChild` gehoeren dazu, seit die
  // Oberflaeche die Breite des Rollbalkens MISST und als CSS-Variable
  // ablegt. Eine Attrappe ohne diese beiden liess `start()` mit einer
  // Ausnahme abbrechen — was immerhin auffiel, weil sie streng ist.
  documentElement: { lang: "de", style: { setProperty() {} } },
  // Der Roller der SEITE — gestapelt rollt sie und nicht das Raster.
  //
  // ⚠️ `getBoundingClientRect().top` ist `-scrollTop`, und das ist keine
  // Bequemlichkeit, sondern das gemessene Verhalten des Browsers: der
  // Kasten der Rollwurzel beginnt am Dokumentanfang und wandert beim
  // Rollen mit hinauf. Bei `scrollTop` 500 liefert ein echter Browser
  // `top: -500`.
  //
  // ⚠️ Ohne `getBoundingClientRect` hier und ohne `requestAnimationFrame`
  // liefe die Sprungrechnung in der Pruefung nie durch — zwei Luecken, die
  // sich gegenseitig zudecken.
  scrollingElement: {
    scrollTop: 0,
    getBoundingClientRect() { return { top: -this.scrollTop, left: 0 }; },
  },
  body: {
    appendChild() {},
    removeChild() {},
    // Die gesetzten Klassen werden mitgeschrieben, nicht verworfen.
    _klassen: new Set(),
    classList: {
      add(k) {
        document.body._klassen.add(k);
        if (k === "drei") spaltenOffen = true;
      },
      remove(k) {
        document.body._klassen.delete(k);
        if (k === "drei") spaltenOffen = false;
      },
      toggle() {},
      contains(k) { return document.body._klassen.has(k); },
    },
  },
  getElementById(id) {
    // ⚠️ Wie im Browser: nicht vorhanden oder entfernt heisst null.
    if (!imHtml.has(id) || entfernt.has(id)) return null;
    return knoten[id] || (knoten[id] = mach(id));
  },
  createElement: (t) => mach("_neu_" + t),
  // ⚠️ Die Sinnbilder im Feldmenue sind SVG und entstehen ueber
  // `createElementNS` — ausdruecklich so, damit sie nicht ueber
  // `innerHTML` gebaut werden (Punkt 33). Ohne diese Zeile warf die
  // Attrappe, sobald Punkt 61 das Menue wirklich oeffnete.
  createElementNS: (raum, t) => mach("_svg_" + t),
  createTextNode: (t) => ({ t }),
  // ⚠️ `querySelectorAll("button")` liefert die bekannten Knoepfe, nicht
  // eine leere Liste. Die Oberflaeche setzt daraus die Tooltips — mit einer
  // leeren Liste liefe die Funktion ins Nichts, und die Pruefung, dass sie
  // EIGENE Titel (die Klartext-Warnung am Speichern-Knopf) nicht
  // ueberschreibt, pruefte gar nichts.
  querySelectorAll(wahl) {
    if (String(wahl) !== "button") return [];
    return [...imHtml].filter((k) => k.startsWith("knopf"))
      .map((k) => document.getElementById(k))
      .filter(Boolean);
  },
  // ⚠️ Horcher auf dem DOKUMENT werden mitgefuehrt, nicht weggeworfen.
  // Sonst waere alles ungeprueft, was nicht an einem einzelnen Element
  // haengt: der Ziehschleier ueber der ganzen Seite und, wichtiger, das
  // `preventDefault`, das den Browser daran hindert, eine daneben abgelegte
  // Datei zu OEFFNEN.
  _h: {},
  addEventListener(ev, fn) {
    (document._h[ev] = document._h[ev] || []).push(fn);
  },
};
let geoeffnet = null;
let geoeffnetZahl = 0;
let bestaetigt = true;
let letzteFrage = null;
let neuGeladen = 0;
global.window = {
  // ⚠️ Aufzeichnen statt verwerfen. Seit der Fuss im Rollfluss steht,
  // haengt der Schatten der Kopfzeile am `scroll` DES FENSTERS — mit
  // einem leeren `addEventListener` waere Punkt 44 gestapelt gruen
  // gewesen, ohne je etwas ausgeloest zu haben.
  _h: {},
  addEventListener(ev, fn) { (window._h[ev] = window._h[ev] || []).push(fn); },
  // Gezaehlt statt ausgefuehrt — Punkt 79 prueft, dass ein Nein NICHT
  // neu laedt.
  location: { href: "http://127.0.0.1:4141/", hostname: "127.0.0.1",
              port: "4141", reload() { neuGeladen++; } },
  // ⚠️ OHNE DIESE ZEILE PRUEFT DIE BEWEGUNG NICHTS. `springeZu()` faellt
  // ohne `requestAnimationFrame` auf `scrollIntoView` zurueck — und damit
  // lief die ganze Rechnung, um die es geht, in keiner Pruefung je
  // durch. Sie ist steuerbar (`_raf`), damit ein Punkt sie auch
  // abschalten und den Rueckfall pruefen kann.
  //
  // Der Zeitstempel liegt weit hinter dem Beginn: die Bewegung laeuft in
  // einem Zug bis ans Ende, statt in Bildschritten. Geprueft wird, WO sie
  // ankommt, nicht wie sie unterwegs aussieht.
  //
  // ⚠️ Sie muss AUCH GLOBAL stehen. `springeZu()` ruft sie ohne `window.`
  // davor, und `maschera.js` wird hier als gewoehnliches Modul geladen —
  // der blosse Name trifft `global`, nicht die Attrappe. Node bringt
  // `requestAnimationFrame` nicht mit; ohne die Zuweisung unten bliebe
  // `typeof` auf `undefined`, und der Rueckfall griffe weiter.
  _raf: true,
  // ⚠️ Die Attrappe muss `getComputedStyle` kennen, seit `springeZu()`
  // fragt, ob die Kopfzeile `sticky` steht. Sie liefert steuerbare Werte
  // (`_kopfPosition`, `_kopfHoehe`), damit ein Punkt BEIDE Faelle pruefen
  // kann — gestapelt verdeckt sie, nebeneinander nicht. Eine Attrappe,
  // die immer «static» sagt, haette den Abzug nie gesehen.
  _kopfPosition: "sticky",
  _kopfHoehe: 90,
  // ⚠️ Die Attrappe muss `matchMedia` kennen, seit die Oberflaeche zwischen
  // drei, zwei und einer Spalte unterscheidet. `breite` ist steuerbar:
  // eine Attrappe, die immer «breit» sagt, prueft die gestapelte Ansicht
  // nie — und genau die ist neu.
  _breite: 1400,
  matchMedia(abfrage) {
    const m = String(abfrage).match(/max-width:\s*([\d.]+)em/);
    const passt = m
      ? window._breite <= parseFloat(m[1]) * 16
      : false;
    return { matches: passt, media: abfrage,
             addEventListener() {}, removeEventListener() {} };
  },
  open(url, name, merkmale) {
    geoeffnet = { url, name, merkmale };
    geoeffnetZahl++;
    // Wie im Browser: mit `noopener` in den Merkmalen ist der
    // Rueckgabewert null, auch wenn das Fenster aufgeht.
    return /noopener/.test(merkmale || "") ? null : { closed: false };
  },
};
// Siehe `_raf` oben: der blosse Name trifft `global`, nicht `window`.
global.getComputedStyle = (el) => ({
  position: el && el.id === "kopfzeile" ? window._kopfPosition : "static",
  getPropertyValue: () => "",
});
window.getComputedStyle = global.getComputedStyle;
global.requestAnimationFrame = (fn) => {
  if (!window._raf) return 0;
  fn(Date.now() + 10000);
  return 1;
};
window.requestAnimationFrame = global.requestAnimationFrame;
// Node 22 hat ein eigenes `navigator` ohne Setter — deshalb definieren.
Object.defineProperty(global, "navigator", {
  value: { clipboard: { writeText: async (t) => { letztKopiert = t; } } },
  configurable: true, writable: true,
});

let letzteAnfrage = null;
let letztKopiert = null;
let rueckOffen = false;
let vorlieben = ["DATE"];
const angehaengt = [];
/* Text eines Knotens samt Kindern — die Meldung besteht aus verschachtelten
 * Elementen, nicht aus einer Zeichenkette. */
function text(k) {
  if (k == null) return "";
  if (typeof k === "string") return k;
  if (k.t !== undefined) return String(k.t);
  return String(k.textContent || "")
    + (k._kinder || []).map(text).join(" ");
}
let spaltenOffen = false;
let einstellungen = { adresse: "127.0.0.1", port: 4141,
                      eigenes_fenster: true, dienste: [
  { id: "claude", name: "Claude", url: "https://claude.ai/new" }] };
let vorlagen = [{ name: "Danke, 4 Wochen", text: "Antworte freundlich." }];
let anonymRufe = 0;
const GELESEN = "Sehr geehrte Frau Brülhart\nIhr Schreiben vom 14.03.2026";
global.fetch = async (url, opt) => {
  letzteAnfrage = { url: String(url), opt };
  const u = String(url);
  if (u.includes("/api/anonymisieren")) anonymRufe++;
  // ⚠️ Eigener Zweig, und zwar VOR dem Rueckfall unten. Der Rueckfall
  // antwortet auf jede unbekannte Adresse mit der Anonymisierungsantwort —
  // ohne diesen Zweig saehe ein Aufruf von `/api/lesen` aus, als haette er
  // maskiert, und Punkt 29 bestuende, ohne etwas zu zeigen.
  if (u.includes("/api/lesen")) {
    return { ok: true, json: async () => ({ original: GELESEN }) };
  }
  if (u.includes("zustand")) {
    return { ok: true, json: async () => ({
      // ⚠️ Eine ERFUNDENE Nummer. Die Attrappe darf nicht die echte
      // Fassung tragen — sonst muesste sie bei jedem Erhoehen
      // mitgezogen werden, und das ist genau der Verwalter, den
      // `app/serve.py` allein sein soll. Geprueft wird, dass die
      // Oberflaeche ANZEIGT, was der Server sagt, nicht welche
      // Zahl das ist.
      dienst: "maschera", version: "0.0.0-attrappe", pack: "ch",
      label_hash: "b7a96dc9abcdef", tags: 45, modell: "runs/ch-v62",
      ohne_modell: false, hinweise: [] }) };
  }
  if (u.includes("tags")) {
    return { ok: true, json: async () => ({ tags: [
      { tag: "DATE", bezeichnung: "Datum", gruppe: "process",
        bspd: false, aktion: "mask" },
      { tag: "FULLNAME", bezeichnung: "Nachname", gruppe: "person",
        bspd: false, aktion: "mask" },
      { tag: "AHVN13", bezeichnung: "AHV-Nummer", gruppe: "official",
        bspd: false, aktion: "mask", pruefsumme: true },
      { tag: "NATIONALITY", bezeichnung: "Nationalität", gruppe: "origin",
        bspd: true, aktion: "mask" },
      { tag: "CANTON", bezeichnung: "Kanton", gruppe: "plain",
        bspd: false, aktion: "tag_only" },
    ] }) };
  }
  if (u.includes("vorlieben")) {
    if ((opt || {}).method === "PUT") {
      const k = JSON.parse(opt.body).klartext;
      const bspd = JSON.parse(opt.body).auch_bspd;
      if (k.includes("NATIONALITY") && !bspd) {
        return { ok: false, status: 400, json: async () => ({
          fehler: "Besonders schuetzenswerte Personendaten: NATIONALITY" }) };
      }
      if (k.includes("DATUM")) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Unbekannte Tags: DATUM" }) };
      }
      vorlieben = k;
      return { ok: true, json: async () => ({
        klartext: k, bspd: k.filter((x) => x === "NATIONALITY"),
        warnung: "Gespeichert." }) };
    }
    return { ok: true, json: async () => ({
      klartext: vorlieben, bspd: [], unbekannt: [], pfad: "x",
      warnung: "w" }) };
  }
  if (u.includes("/api/einstellungen")) {
    if ((opt || {}).method === "PUT") {
      const e = JSON.parse(opt.body);
      const boese = (e.dienste || []).find(
        (d) => !d.name.trim() || !/^https?:\/\//i.test(d.url));
      if (boese) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Dienst abgelehnt: "
                                              + (boese.name || "ohne Namen") }) };
      }
      einstellungen = { ...e, port: parseInt(e.port, 10) };
      return { ok: true, json: async () => einstellungen };
    }
    return { ok: true, json: async () => einstellungen };
  }
  if (u.includes("/api/vorlagen")) {
    if ((opt || {}).method === "PUT") {
      const liste = JSON.parse(opt.body).vorlagen;
      // Der echte Server prueft und schreibt erst dann. Die Attrappe bildet
      // genau diesen Fall nach: eine namenlose Vorlage wird abgewiesen, und
      // die bestehende Liste bleibt.
      if (liste.some((v) => !v.name || !v.name.trim())) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Vorlage 1 hat keinen Namen." }) };
      }
      vorlagen = liste;
      return { ok: true, json: async () => ({ vorlagen: vorlagen,
                                              pfad: "x", warnung: "w" }) };
    }
    return { ok: true, json: async () => ({ vorlagen: vorlagen, pfad: "x",
                                            warnung: "w" }) };
  }
  if (u.includes("/api/regeln")) {
    if ((opt || {}).method === "PUT") {
      const y = JSON.parse(opt.body).yaml;
      if (y.includes("kaputt")) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Regeln abgelehnt: Zeile 1" }) };
      }
      return { ok: true, json: async () => ({ regeln: 2,
                                              warnung: "Gespeichert." }) };
    }
    return { ok: true, json: async () => ({
      pfad: "x", yaml: "woerter:\n  - Seerose\n", regeln: [] }) };
  }
  if (u.includes("zurueckwandeln")) {
    return { ok: true, json: async () => ({
      text: "am 14.03.2026 hat Frau [Fullname_1] geschrieben.",
      ersetzt: 1,
      nicht_gefunden: rueckOffen ? ["[Fullname_1]"] : [],
      hinweise: rueckOffen
        ? ["[Fullname_1] unterscheidet sich von [FULLNAME_1] nur in der "
           + "Schreibweise — nicht ersetzt."] : [] }) };
  }
  if (u.includes("vorlieben")) {
    if ((opt || {}).method === "PUT") {
      const k = JSON.parse(opt.body).klartext;
      const bspd = JSON.parse(opt.body).auch_bspd;
      if (k.includes("NATIONALITY") && !bspd) {
        return { ok: false, status: 400, json: async () => ({
          fehler: "Besonders schuetzenswerte Personendaten: NATIONALITY" }) };
      }
      if (k.includes("DATUM")) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Unbekannte Tags: DATUM" }) };
      }
      vorlieben = k;
      return { ok: true, json: async () => ({
        klartext: k, bspd: k.filter((x) => x === "NATIONALITY"),
        warnung: "Gespeichert." }) };
    }
    return { ok: true, json: async () => ({
      klartext: vorlieben, bspd: [], unbekannt: [], pfad: "x",
      warnung: "w" }) };
  }
  if (u.includes("/api/regeln")) {
    if ((opt || {}).method === "PUT") {
      const y = JSON.parse(opt.body).yaml;
      if (y.includes("kaputt")) {
        return { ok: false, status: 400,
                 json: async () => ({ fehler: "Regeln abgelehnt: Zeile 1" }) };
      }
      return { ok: true, json: async () => ({ regeln: 2,
                                              warnung: "Gespeichert." }) };
    }
    return { ok: true, json: async () => ({
      pfad: "x", yaml: "woerter:\n  - Seerose\n", regeln: [] }) };
  }
  if (u.includes("zurueckwandeln")) {
    return { ok: true, json: async () => ({
      text: "Antwort mit 14.03.2026 und Andrea Brülhart.",
      ersetzt: 2, nicht_gefunden: [], hinweise: [] }) };
  }
  return { ok: true, json: async () => ({
    maskiert: "am [DATE_1] hat Frau [FULLNAME_1] geschrieben.",
    original: "am 14.03.2026 hat Frau Andrea Brülhart geschrieben.",
    spans: [
      { tag: "DATE", start: 3, end: 13, platzhalter: "[DATE_1]",
        quelle: "regex", vertrauen: null, bspd: false },
      { tag: "FULLNAME", start: 23, end: 38, platzhalter: "[FULLNAME_1]",
        quelle: "model", vertrauen: 0.94, bspd: false },
    ],
    woerterbuch: { "[DATE_1]": "14.03.2026",
                   "[FULLNAME_1]": "Andrea Brülhart" },
    verworfen: [], hinweise: [],
    kennzahlen: { zeichen: 50, maskiert: 25, anteil: 0.5 } }) };
};

// Nicht abgefangene Fehler sind das, was wir suchen.
process.on("uncaughtException", (e) => {
  console.log("   FEHL Ausnahme: " + e.message);
  console.log("        " + (e.stack || "").split("\n")[1]);
  process.exit(1);
});
process.on("unhandledRejection", (e) => {
  console.log("   FEHL Ausnahme (async): " + (e && e.message));
  console.log("        " + ((e && e.stack) || "").split("\n")[1]);
  process.exit(1);
});

const M = require(path.join(WURZEL, "app/static/maschera.js"));
// Die Rueckfragen beantwortet die Pruefung ueber die Weiche, nicht ueber
// den Dialog — den prueft Punkt 79 fuer sich.
// ⚠️ Steuerbar, nicht fest auf «ja». Eine Wache, die immer bestaetigt wird,
// ist keine gepruefte Wache — Punkt 30 braucht das Nein.
let eingabeAntwort = null;
M.frageErsetzen(async (m, opt) => {
  letzteFrage = String(m || "");
  if (opt && typeof opt.vorschlag === "string") return eingabeAntwort;
  return bestaetigt;
});

/* Eine Datei auf die Ablage ziehen. Der Horcher ist nicht `await`-bar — er
 * stoesst `ablegen()` nur an —, deshalb danach kurz warten. */
async function feuerAblage(name) {
  const o = document.getElementById("ablage");
  const fns = o._h["drop"] || [];
  if (!fns.length) { pruefe(false, "kein Horcher auf ablage/drop"); return; }
  for (const f of fns) {
    f({ preventDefault() {}, stopPropagation() {}, target: o,
        currentTarget: o, dataTransfer: { files: [{ name: name }] } });
  }
  await new Promise((r) => setTimeout(r, 30));
}

async function feuer(id, ev) {
  const o = document.getElementById(id);
  if (!o) { pruefe(false, `Element ${id} nicht auffindbar`); return; }
  const fns = o._h[ev || "click"] || [];
  if (!fns.length) {
    pruefe(false, `kein Horcher auf ${id}/${ev || "click"}`); return;
  }
  for (const f of fns) {
    await f({ preventDefault() {}, stopPropagation() {},
              target: o, currentTarget: o, dataTransfer: null });
  }
}

setTimeout(async () => {
  console.log("0. Das HTML ist ausgeglichen");
// ⚠️ Ein einziges fehlendes `</div>` meldet der Browser nicht — er
// schliesst still, was offen blieb, und verschachtelt alles Folgende
// hinein. Das Raster ist dann zerstoert, waehrend Skript und Kennungen in
// Ordnung sind. Deshalb wird der Baum selbst geprueft.
{
  const LEER = new Set(["br", "img", "input", "meta", "link", "hr"]);
  const SVG = new Set(["svg", "path", "rect", "circle", "line", "polyline",
                       "polygon", "g", "defs"]);
  const stapel = [];
  let zeile = 1;
  const re = /<(\/?)([a-zA-Z][\w-]*)([^>]*?)(\/?)>|\n|<!--[\s\S]*?-->/g;
  let m;
  while ((m = re.exec(HTML)) !== null) {
    if (m[0] === "\n") { zeile++; continue; }
    if (m[0].startsWith("<!--")) {
      zeile += (m[0].match(/\n/g) || []).length; continue;
    }
    const [, schluss, roh, , selbst] = m;
    const tag = roh.toLowerCase();
    if (SVG.has(tag) || LEER.has(tag) || selbst) continue;
    if (schluss) {
      const oben = stapel[stapel.length - 1];
      if (!oben || oben.tag !== tag) {
        pruefe(false, `Zeile ${zeile}: </${tag}> passt nicht zu `
          + (oben ? `<${oben.tag}> von Zeile ${oben.zeile}` : "nichts"));
      }
      stapel.pop();
    } else {
      stapel.push({ tag, zeile });
    }
  }
  const offen = stapel.filter((e) => e.tag !== "html");
  pruefe(offen.length === 0,
         "nie geschlossen: " + offen.map((e) => `<${e.tag}> Zeile ${e.zeile}`)
           .join(", "));
  if (!fehler) console.log("   OK   alle Marken ausgeglichen");
}

console.log("1. Alle Knoepfe sind verdrahtet");
  for (const id of ["knopf-maskieren", "knopf-beispiel", "knopf-neu",
                    "knopf-kopieren", "knopf-kopieren-orig",
                    "schalter-vokabular", "knopf-einklappen",
                    "knopf-ausklappen"]) {
    const o = document.getElementById(id);
    pruefe(o && (o._h.click || []).length > 0, `${id} hat keinen Horcher`);
  }
  if (!fehler) console.log("   OK   8 Knoepfe");

  console.log("2. Der Startbildschirm wird verborgen, nicht entfernt");
  // ⚠️ Wird der Startbildschirm entfernt statt versteckt, findet der
  // naechste Aufruf von `zeichneBeschriftung()` `start-lage` nicht mehr und
  // bricht ab.
  pruefe(document.getElementById("startbild") !== null,
         "Startbildschirm wurde entfernt statt verborgen");
  pruefe(document.getElementById("start-lage") !== null,
         "start-lage ist nach dem Start nicht mehr erreichbar");
  if (!fehler) console.log("   OK   noch auffindbar");

  console.log("3. «Beispiel» fuellt Spalte 1 und schaltet MASKIEREN frei");
  await feuer("knopf-beispiel");
  const zahl = document.getElementById("zahl-01").textContent;
  pruefe(/\d{3}/.test(zahl), `Zeichenzahl steht auf ${zahl!== "" ? zahl : "leer"}`);
  pruefe(document.getElementById("knopf-maskieren").disabled === false,
         "MASKIEREN bleibt gesperrt");
  if (!fehler) console.log("   OK   " + zahl);

  console.log("4. MASKIEREN ruft die Kette, nicht den Browser");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  pruefe(letzteAnfrage && letzteAnfrage.url.includes("/api/anonymisieren"),
         "keine Anfrage an /api/anonymisieren");
  const koerper = JSON.parse((letzteAnfrage.opt || {}).body || "{}");
  pruefe(koerper.text && koerper.text.length > 100, "Text nicht mitgeschickt");
  pruefe(koerper.woerterbuch === true, "Woerterbuch nicht angefordert");
  if (!fehler) console.log("   OK   " + koerper.text.length + " Zeichen");

  console.log("5. Der Vokabularschalter kippt und wirkt auf die Anfrage");
  await feuer("schalter-vokabular");
  pruefe(document.getElementById("schalterwort").textContent.length > 1,
         "Schalterwort nicht gesetzt");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  const k2 = JSON.parse((letzteAnfrage.opt || {}).body || "{}");
  pruefe(k2.woerterbuch === false,
         "Schalter aus, aber die Anfrage will trotzdem ein Woerterbuch");
  if (!fehler) console.log("   OK   woerterbuch: false");

  console.log("6. Ausschalten verwirft das Woerterbuch sofort");
  // ⚠️ Nicht erst beim naechsten Lauf. Wer die Warnung bestaetigt hat, hat
  // den Verlust beschlossen — bliebe die Tabelle stehen, saehe es aus, als
  // waeren die Werte noch da, und man koennte sie sogar noch ablesen.
  await feuer("knopf-beispiel");
  // Punkt 5 hat den Schalter ausgeschaltet — erst wieder an, sonst prueft
  // dieser Punkt das Einschalten statt das Ausschalten.
  if (document.getElementById("schalter-vokabular")
        .getAttribute("aria-checked") === "false") {
    await feuer("schalter-vokabular");
  }
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  const vorher = document.getElementById("zahl-vokabular").textContent;
  pruefe(/\d/.test(vorher) && !/·\s*0\s/.test(vorher),
         `vor dem Ausschalten steht ${vorher}`);
  await feuer("schalter-vokabular");
  const nachher = document.getElementById("zahl-vokabular").textContent;
  pruefe(/·\s*0\s/.test(nachher),
         `nach dem Ausschalten steht noch ${nachher}`);
  if (!fehler) console.log("   OK   " + vorher + "  ->  " + nachher);

  console.log("7. «Kopieren und öffnen» sendet nichts, sondern oeffnet");
  // ⚠️ `/api/senden` gibt es nicht und wird es nicht geben. Der Knopf legt
  // in die Zwischenablage und oeffnet den Dienst; eingefuegt wird von Hand.
  // Keine Zeile verlaesst das Geraet ohne Griff zur Tastatur.
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  // ⚠️ Erst die UEBERNAHME traegt den maskierten Text in die dritte
  // Spalte. Ohne sie hat der Sendeknopf nichts zu kopieren — und genau das
  // ist der Punkt.
  await feuer("knopf-uebernahme");
  letzteAnfrage = null;
  geoeffnetZahl = 0;
  await feuer("knopf-senden");
  await new Promise((r) => setTimeout(r, 20));
  pruefe(letzteAnfrage === null,
         "«Kopieren und öffnen» hat eine Anfrage an den Server geschickt");
  pruefe(geoeffnet && /claude\.ai/.test(geoeffnet.url),
         "kein Dienst geoeffnet: " + JSON.stringify(geoeffnet));
  // ⚠️ GENAU EIN Aufruf. `noopener` im Merkmalsstring laesst `window.open`
  // laut Spezifikation `null` zurueckgeben, auch wenn das Fenster aufgeht.
  // Ein Rueckfall, der das fuer ein Scheitern haelt, oeffnet ein zweites Mal:
  // Fenster UND Reiter, wobei der Reiter blockiert wird.
  pruefe(geoeffnetZahl === 1,
         `window.open ${geoeffnetZahl}x aufgerufen statt einmal`);
  // Die Groessenangaben machen aus dem Reiter ein Fenster, nicht der Name.
  pruefe(geoeffnet && /width=/.test(geoeffnet.merkmale || ""),
         "keine Fenstergroesse angegeben");
  pruefe(geoeffnet && /noopener/.test(geoeffnet.merkmale || ""),
         "ohne noopener geoeffnet");
  pruefe(letztKopiert && letztKopiert.includes("[") &&
         letztKopiert.includes("————"),
         "Zwischenablage traegt nicht Prompt und Anhang");
  if (!fehler) console.log("   OK   " + geoeffnet.url + " als Fenster");

  console.log("8. «Übernahme in Prompt» klappt Spalte 3 auf");
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  spaltenOffen = false;
  await feuer("knopf-uebernahme");
  pruefe(spaltenOffen, "die dritte Spalte bleibt zu");
  if (!fehler) console.log("   OK   aufgeklappt");

  console.log("9. «Weg zurück» macht 02 zum Eingabefeld");
  // ⚠️ Wer die dritte Spalte nicht braucht — weil er selbst mit dem Text
  // arbeitet —, muss trotzdem zum fertigen Ergebnis kommen.
  await feuer("schalter-zurueck");
  pruefe(document.getElementById("antwortfeld").hidden === false,
         "Antwortfeld bleibt verborgen");
  pruefe(document.getElementById("maskiert").hidden === true,
         "der maskierte Text bleibt sichtbar");
  const feld = document.getElementById("antwortfeld");
  feld.value = "Antwort mit [DATE_1] und [FULLNAME_1].";
  for (const f of feld._h.input || []) await f({ target: feld });
  await feuer("knopf-uebernahme");
  await new Promise((r) => setTimeout(r, 30));
  pruefe(letzteAnfrage && letzteAnfrage.url.includes("/api/zurueckwandeln"),
         "kein Aufruf von /api/zurueckwandeln");
  pruefe(document.getElementById("final").hidden === false,
         "Bereich 05 bleibt leer");
  if (!fehler) console.log("   OK   05 gefuellt");

  console.log("10. Nicht zugeordnete Platzhalter werden ANGEZEIGT");
  // ⚠️ Der wichtigste Punkt der Rueckwandlung. Sprachmodelle schreiben
  // Platzhalter um; der Server ersetzt das bewusst nicht still, sondern
  // meldet es. Wer die Meldung nicht sieht, verschickt einen Brief, in dem
  // `[FULLNAME_1]` steht.
  rueckOffen = true;
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  document.getElementById("antwort04").value = "am [DATE_1] hat Frau [Fullname_1] geschrieben.";
  await feuer("antwort04", "input");
  await feuer("knopf-einpflegen04");
  await new Promise((r) => setTimeout(r, 30));
  pruefe(angehaengt.some((n) => /Fullname_1/.test(n)),
         "der offene Platzhalter steht nirgends in der Anzeige");
  pruefe(angehaengt.some((n) => /Schreibweise/.test(n)),
         "der Hinweis des Servers wird verschwiegen");
  rueckOffen = false;
  if (!fehler) console.log("   OK   gemeldet samt Grund");

  console.log("11. Der Sendeknopf flackert nicht zwischen drei Texten");
  // ⚠️ `inZwischenablage` setzt nach 1400 ms auf «Kopieren» zurueck, der
  // Sendeablauf auf die volle Beschriftung nach 3000 ms. Beide zusammen
  // ergaben ein Flackern, je nachdem welcher Zeitgeber zuletzt lief.
  await feuer("schalter-zurueck");
  geoeffnetZahl = 0;
  await feuer("knopf-senden");
  await new Promise((r) => setTimeout(r, 20));
  const sofort = document.getElementById("senden-text").textContent;
  pruefe(/kopiert/i.test(sofort), `nach dem Klick steht «${sofort}»`);
  await feuer("knopf-beispiel");     // zwischendurch neu zeichnen
  const dazwischen = document.getElementById("senden-text").textContent;
  pruefe(/kopiert/i.test(dazwischen),
         `Neuzeichnen ueberschreibt zu «${dazwischen}»`);
  if (!fehler) console.log("   OK   bleibt «" + sofort + "»");

  console.log("12. Einstellungen: oeffnen, Tags, Regeln");
  await feuer("knopf-einstellungen");
  await new Promise((r) => setTimeout(r, 30));
  pruefe(document.getElementById("einst").hidden === false,
         "Einstellungen gehen nicht auf");
  pruefe(document.getElementById("einst-regeln").value.includes("Seerose"),
         "die YAML-Regeln werden nicht geladen");
  // ⚠️ `CANTON` ist `tag_only` — ein Schalter dafuer waere eine Einstellung
  // ohne Wirkung. Er muss gesperrt sein.
  // ⚠️ Die Attrappe nennt das Feld `aktion`, weil der Server es so nennt.
  // Hiesse es hier anders als im Server, waere CANTON in der Pruefung
  // gesperrt und in Wirklichkeit nie.
  const wolke = document.getElementById("einst-tags")._kinder
    .flatMap((k) => (k._kinder && k._kinder.length ? k._kinder : [k]));
  const canton = wolke.find((k) => text(k).includes("CANTON"));
  pruefe(canton && canton.disabled === true,
         "CANTON laesst sich umlegen, obwohl es tag_only ist");
  const natio = wolke.find((k) => text(k).includes("NATIONALITY"));
  pruefe(natio && natio.className.includes("bspd"),
         "NATIONALITY ist nicht als bsPD gekennzeichnet");
  // ⚠️ Farbe an allen drei Stellen gleich: Text, Kontextmenue, Tagwolke.
  const fullname = wolke.find((k) => text(k).includes("FULLNAME"));
  const punkt = fullname && fullname._kinder[0];
  pruefe(punkt && punkt.style && punkt.style.background,
         "der Farbpunkt in der Tagwolke ist ungefaerbt");
  const natioWarn = wolke.find((k) => text(k).includes("NATIONALITY"));
  pruefe(natioWarn && text(natioWarn).includes("\u26a0"),
         "bsPD ohne ⚠ — der gestrichelte Rand las sich wie ein hoeherer Knopf");
  pruefe(canton && text(canton).includes("Kanton"),
         "die Bezeichnung fehlt im Knopf — 45 Abkuerzungen sind keine Wahl");
  const ueberschriften = document.getElementById("einst-tags")._kinder
    .filter((k) => String(k.id || "").endsWith("h4"));
  pruefe(ueberschriften.length >= 2,
         `${ueberschriften.length} Gruppen gezeichnet, mindestens 2 erwartet`);
  if (!fehler) console.log("   OK   Regeln geladen, CANTON gesperrt");

  console.log("13. Abgelehnte Regeln werden GEMELDET, nicht verschluckt");
  // ⚠️ Der Server laesst die bestehende Datei unberuehrt, wenn er ablehnt.
  // Hier zaehlt nur, dass der Grund sichtbar wird — sonst glaubt der
  // Anwender, seine Regeln seien gespeichert.
  document.getElementById("einst-regeln").value = "kaputt: [";
  await feuer("knopf-regeln-speichern");
  await new Promise((r) => setTimeout(r, 30));
  const bef = document.getElementById("einst-regeln-befund");
  pruefe(/abgelehnt|Zeile/.test(bef.textContent),
         `der Grund steht nicht da: ${bef.textContent}`);
  pruefe(/schlecht/.test(bef.className), "die Ablehnung sieht aus wie Erfolg");
  if (!fehler) console.log("   OK   " + bef.textContent);

  console.log("14. Kontextmenue: Maske entfernen und Tag setzen");
  // ⚠️ Ohne Korrekturweg muss der Anwender jedes Leck und jede
  // Uebermaskierung hinnehmen. Bei 0.87 % Leckrate und ORG-Precision 0.545
  // war das der wichtigste fehlende Teil.
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));

  const vorText = M.zustand.antwort.maskiert;
  pruefe(vorText.includes("[FULLNAME_1]"),
         "die Attrappe liefert keinen Platzhalter zum Korrigieren");

  // Maske entfernen: der Originalwert steht wieder im Text, der Eintrag ist
  // aus dem Woerterbuch weg.
  const weg = M.maskeEntfernen("[FULLNAME_1]");
  pruefe(weg === true, "maskeEntfernen meldet Misserfolg");
  const nachText = M.zustand.antwort.maskiert;
  pruefe(!nachText.includes("[FULLNAME_1]"),
         "der Platzhalter steht noch im Text");
  pruefe(nachText.includes("Andrea Brülhart"),
         "der Originalwert wurde nicht eingesetzt");
  pruefe(M.zustand.antwort.woerterbuch["[FULLNAME_1]"] === undefined,
         "der Woerterbucheintrag lebt weiter");

  // ⚠️ Und wieder maskieren — ALLE Vorkommen, nicht nur eines. Derselbe Wert
  // an anderer Stelle im Klartext waere ein Leck.
  const zurueck = M.wertMaskieren("Andrea Brülhart", "FULLNAME");
  pruefe(zurueck === true, "wertMaskieren meldet Misserfolg");
  pruefe(!M.zustand.antwort.maskiert.includes("Andrea Brülhart"),
         "der Wert steht noch im Klartext");
  const neu = M.zustand.antwort.spans.find((sp) => sp.quelle === "manuell");
  pruefe(!!neu, "keine Fundstelle mit der Quelle «manuell»");
  pruefe(neu && neu.vertrauen === null,
         "eine Handmaskierung traegt ein Vertrauen");
  if (!fehler) console.log("   OK   entfernt, neu gesetzt, Quelle manuell");

  console.log("15. Maskieren trifft nur ganze Woerter");
  // ⚠️ `wertMaskieren` ersetzt ganze Woerter, nicht jedes Vorkommen der
  // Zeichenkette. «Damen» traefe sonst auch das «Damen» in «Sehr geehrte
  // Damen», und ein kurzer Wert wie «AG» oder «Bern» schluege mitten in
  // anderen Woertern zu — aus einer Korrektur wuerde eine Textzerstoerung.
  M.zustand.antwort = {
    maskiert: "Bern und Berner, 3011 Bern. Frau Meier, Herr Meiers Sohn.",
    woerterbuch: {}, spans: [], hinweise: [], kennzahlen: {},
  };
  M.wertMaskieren("Bern", "CITY");
  const t1 = M.zustand.antwort.maskiert;
  pruefe(/Berner/.test(t1), `«Berner» wurde zerlegt: ${t1}`);
  pruefe((t1.match(/\[CITY_1\]/g) || []).length === 2,
         `beide «Bern» haetten ersetzt werden muessen: ${t1}`);
  M.wertMaskieren("Meier", "FULLNAME");
  const t2 = M.zustand.antwort.maskiert;
  pruefe(/Meiers/.test(t2), `«Meiers» wurde zerlegt: ${t2}`);
  if (!fehler) console.log("   OK   " + t1.slice(0, 46));

  console.log("16. Mehrteilige Namen gehen als Ganzes");
  // ⚠️ «Maschera Immobilien AG» ist ein ORG und drei Woerter. Ohne die
  // Beruecksichtigung der AUSWAHL bekaeme man nur eines davon — und das war
  // der zweite Teil desselben Fehlers.
  M.zustand.antwort = {
    maskiert: "Die Maschera Immobilien AG hat bestätigt.",
    woerterbuch: {}, spans: [], hinweise: [], kennzahlen: {},
  };
  M.wertMaskieren("Maschera Immobilien AG", "ORG");
  const t3 = M.zustand.antwort.maskiert;
  pruefe(/\[ORG_1\]/.test(t3), `nicht maskiert: ${t3}`);
  pruefe(!/Maschera|Immobilien/.test(t3), `Reste geblieben: ${t3}`);
  if (!fehler) console.log("   OK   " + t3);

  console.log("17. Der Rand zeigt auf Arbeit, nicht auf Sicherheit");
  // ⚠️ Das Auge folgt der kraeftigeren Linie — also muss sie dorthin
  // zeigen, wo ein Mensch hinsehen muss, nicht auf «Pruefsumme, also
  // sicher».
  const stile = M.SRC_STYLE;
  pruefe(/solid/.test(stile.model),
         `model ist nicht ausgezogen: ${stile.model}`);
  pruefe(/dashed|dotted/.test(stile.checksum),
         `checksum ist nicht zurueckgenommen: ${stile.checksum}`);
  pruefe(/dashed|dotted/.test(stile.regex),
         `regex ist nicht zurueckgenommen: ${stile.regex}`);
  pruefe(/double/.test(stile.manuell),
         `manuell hebt sich nicht ab: ${stile.manuell}`);
  if (!fehler) console.log("   OK   model ausgezogen, checksum gestrichelt");

  console.log("18. Ein Platzhalter wird nie zweimal vergeben");
  // Der Vertrag verlangt: derselbe Wert, derselbe Platzhalter. Eine Nummer
  // zweimal zu vergeben hiesse, beim Zurueckwandeln zwei Werte zu
  // verwechseln.
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  const alle = Object.keys(M.zustand.antwort.woerterbuch);
  pruefe(alle.length === new Set(alle).size,
         "ein Platzhalter kommt doppelt vor");
  if (!fehler) console.log(`   OK   ${alle.length} Platzhalter, alle einmalig`);

  console.log("19. Mehrfaches Zeichnen bricht nicht ab");
  // Der erste Durchlauf klappt, der zweite muss es auch.
  for (let i = 0; i < 5; i++) await feuer("knopf-beispiel");
  await feuer("knopf-neu");
  await feuer("knopf-einklappen");
  await feuer("knopf-ausklappen");
  if (!fehler) console.log("   OK   9 weitere Durchlaeufe");

  console.log("20. Das Vokabular ueberlebt einen Rundlauf");
  // ⚠️ Der Grund fuer den ganzen Weg: nach dem Schliessen ist das
  // Woerterbuch weg, und ein maskierter Text ohne Woerterbuch laesst sich
  // nie mehr zurueckwandeln.
  await feuer("knopf-beispiel");
  await feuer("knopf-maskieren");
  await new Promise((r) => setTimeout(r, 30));
  {
    const datei = M.vokabularDatei();
    const vorher = { ...M.zustand.antwort.woerterbuch };
    pruefe(datei.maschera === "vokabular", "Kennung fehlt in der Datei");
    pruefe(typeof datei.maskiert === "string" && datei.maskiert.length > 0,
           "der maskierte Text fehlt in der Datei");
    // Ein anderer Zustand, dann zurueckholen.
    M.zustand.antwort = null;
    const n = M.uebernimmVokabular(JSON.parse(JSON.stringify(datei)));
    pruefe(n === Object.keys(vorher).length,
           `${n} statt ${Object.keys(vorher).length} Eintraege`);
    pruefe(M.zustand.antwort.maskiert === datei.maskiert,
           "der maskierte Text kam nicht mit");
    let gleich = true;
    for (const ph of Object.keys(vorher)) {
      if (M.zustand.antwort.woerterbuch[ph] !== vorher[ph]) gleich = false;
    }
    pruefe(gleich, "ein Wert hat sich beim Rundlauf veraendert");
    // ⚠️ Die Spannen gehoeren zum alten Lauf und muessen weg sein — sonst
    // faerbt die Anzeige Stellen ein, die es im neuen Text nicht gibt.
    pruefe(M.zustand.antwort.spans.length === 0,
           "alte Spannen ueberlebten das Einlesen");
    pruefe(M.zustand.vokabular === true,
           "der Schalter blieb aus, obwohl Eintraege da sind");
  }
  if (!fehler) console.log("   OK   hinaus und zurueck, Werte gleich");

  console.log("21. Eine fehlerhafte Datei wird GANZ abgewiesen");
  // ⚠️ Ein Teilimport hiesse: die Rueckwandlung ersetzt einen Teil, der
  // Rest bleibt als Platzhalter stehen, und niemand weiss warum.
  {
    const gut = M.vokabularDatei();
    const faelle = [
      [null, "null"],
      [[], "eine Liste"],
      [{ ...gut, maschera: "anderes" }, "eine fremde Datei"],
      [{ ...gut, fassung: 99 }, "eine unbekannte Fassung"],
      [{ ...gut, woerterbuch: null }, "kein Woerterbuch"],
      [{ ...gut, woerterbuch: { "Name_1": "X" } }, "Schluessel ohne Klammern"],
      [{ ...gut, woerterbuch: { "[123_1]": "X" } }, "Schluessel mit Ziffer"],
      [{ ...gut, woerterbuch: { "[FULLNAME]": "X" } }, "Schluessel ohne Nummer"],
      [{ ...gut, woerterbuch: { "[FULLNAME_1]": 7 } }, "Wert als Zahl"],
      [{ ...gut, maskiert: 42 }, "maskierter Text als Zahl"],
    ];
    for (const [o, was] of faelle) {
      pruefe(typeof M.pruefeVokabular(o) === "string",
             `${was} wurde durchgelassen`);
    }
    pruefe(M.pruefeVokabular(gut) === null,
           "eine gueltige Datei wurde abgewiesen");
    // ⚠️ Der verankerte Ausdruck darf keinen Zustand mitschleppen: mit `g`
    // waere jeder zweite Aufruf grundlos falsch.
    pruefe(M.VOK_PH_RE.test("[FULLNAME_1]") &&
           M.VOK_PH_RE.test("[FULLNAME_1]"),
           "VOK_PH_RE merkt sich lastIndex");
    pruefe(M.VOK_PH_RE.test("[FULLNAME_1a]"), "Vornamensform abgewiesen");
    pruefe(M.VOK_PH_RE.test("[Dossier_1]"), "Benutzerregel abgewiesen");
    pruefe(!M.VOK_PH_RE.test("[FULLNAME_1] "), "Anhang durchgelassen");
  }
  if (!fehler) console.log("   OK   10 fehlerhafte Faelle abgewiesen");

  console.log("22. Kein Beschriftungsschluessel doppelt");
  // ⚠️ In einem Objektliteral gewinnt bei einem doppelten Schluessel der
  // letzte — ein neuer Knopf mit dem Namen einer bestehenden Beschriftung
  // traegt dann still deren Text. Nichts stuerzt ab. Deshalb wird die QUELLE
  // geprueft und nicht das Objekt: zur Laufzeit ist der doppelte Schluessel
  // schon verschwunden.
  {
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const anfang = JS.indexOf("const I18N = {");
    pruefe(anfang > 0, "I18N nicht gefunden");
    const ohneText = JS.slice(anfang)
      .replace(/"(\\.|[^"\\])*"/g, '""')
      .replace(/'(\\.|[^'\\])*'/g, "''");
    let tiefe = 0, ende = 0;
    for (let i = 0; i < ohneText.length; i++) {
      if (ohneText[i] === "{") tiefe++;
      else if (ohneText[i] === "}") { tiefe--; if (!tiefe) { ende = i; break; } }
    }
    const block = ohneText.slice(0, ende);
    const marken = [...block.matchAll(/\n {2,4}(de|fr|it|en):\s*\{/g)];
    pruefe(marken.length === 4, `${marken.length} Sprachen gefunden, 4 erwartet`);
    for (let i = 0; i < marken.length; i++) {
      const von = marken[i].index;
      const bis = i + 1 < marken.length ? marken[i + 1].index : block.length;
      const teil = block.slice(von, bis);
      const namen = [...teil.matchAll(/[{,]\s*([A-Za-z_]\w*)\s*:/g)]
        .map((m) => m[1]);
      const doppelt = [...new Set(namen.filter(
        (k) => namen.indexOf(k) !== namen.lastIndexOf(k)))];
      pruefe(doppelt.length === 0,
             `${marken[i][1]}: doppelter Schluessel ${doppelt.join(", ")}`);
    }
  }
  if (!fehler) console.log("   OK   vier Sprachen, keine Kollision");

  console.log("23. Vorlagen: filtern, waehlen, loeschen");
  // Die Vorlagen liegen NICHT im Browser, sondern in
  // ~/.config/maschera/vorlagen.json — was nur im Fenster lebt, ist nach dem
  // Schliessen weg, und eine Vorlage, die man jedes Mal neu tippt, ist keine.
  //
  // ⚠️ Ein Feld, das filtert: tippen und finden wie beim `<select>`, und
  // trotzdem ein Papierkorb je Zeile. Beides zusammen kann keines von beiden
  // allein.
  {
    pruefe(M.zustand.vorlagen.length === 1,
           `${M.zustand.vorlagen.length} Vorlagen geladen, 1 erwartet`);
    M.vorlagenAuf(true);
    const liste = document.getElementById("vorlagen-liste");
    pruefe(liste._kinder.length === 1, "Vorlage fehlt in der Liste");
    // Jede Zeile traegt Auswahl UND Papierkorb.
    pruefe(liste._kinder[0]._kinder.length === 2,
           "kein Papierkorb neben dem Eintrag");
    // Ein Filter, der nicht passt, sagt es statt leer zu bleiben.
    M.zustand.vorlagenFilter = "zzz";
    M.zeichneVorlagen();
    pruefe(text(document.getElementById("vorlagen-liste")).length > 0,
           "kein Hinweis, dass nichts passt");
    M.zustand.vorlagenFilter = "";
    M.zeichneVorlagen();
    M.vorlageNehmen(M.zustand.vorlagen[0]);
    pruefe(M.zustand.prompt === "Antworte freundlich.",
           "Prompt ist: " + M.zustand.prompt);
    pruefe(document.getElementById("prompt").value === "Antworte freundlich.",
           "das Feld selbst wurde nicht gefuellt");
    pruefe(M.zustand.vorlage === "Danke, 4 Wochen",
           "die Wahl wurde nicht gemerkt — sie ist der Namensvorschlag beim "
           + "naechsten Speichern");
    pruefe(M.zustand.vorlagenOffen === false, "Menue blieb offen");
  }
  if (!fehler) console.log("   OK   gefiltert, gewaehlt, gemerkt");

  console.log("24. Ein neuer Dienst ist SOFORT im Sendeknopf");
  // ⚠️ Das Dienstmenue wird nach jeder Aenderung neu gezeichnet, nicht nur
  // beim Start. Sonst taucht ein neu eingetragener Dienst erst nach dem
  // Neuladen auf.
  {
    const vorher = document.getElementById("dienstmenu")._kinder.length;
    await feuer("knopf-dienst-neu");
    const nachher = document.getElementById("dienstmenu")._kinder.length;
    pruefe(nachher === vorher + 1,
           `Menue hat ${nachher} Eintraege, ${vorher + 1} erwartet`);
  }
  if (!fehler) console.log("   OK   Liste und Menue laufen zusammen");

  console.log("25. Abgelehnte Einstellungen schliessen den Dialog NICHT");
  // Zumachen und den Stand verwerfen waere die schlechtere Antwort: der
  // Anwender hat gerade etwas eingetippt, und der Grund stuende in einem
  // Kasten, den niemand mehr sieht.
  {
    await feuer("knopf-einstellungen");
    await new Promise((r) => setTimeout(r, 20));
    // Der leere Dienst aus Pruefung 24 ist noch da — der Server weist ihn ab.
    await feuer("knopf-einst-zu");
    await new Promise((r) => setTimeout(r, 20));
    pruefe(document.getElementById("einst").hidden === false,
           "Dialog schloss trotz abgelehnter Einstellungen");
    pruefe(/abgelehnt/i.test(document.getElementById("einst-befund").textContent),
           "kein Grund genannt");
    // Aufraeumen: den leeren Dienst wieder weg, dann geht das Schliessen.
    M.zustand.dienste = M.zustand.dienste.filter((d) => d.name.trim());
    await feuer("knopf-einst-zu");
    await new Promise((r) => setTimeout(r, 20));
    pruefe(document.getElementById("einst").hidden === true,
           "Dialog schloss auch mit gueltigem Stand nicht");
  }
  if (!fehler) console.log("   OK   offen mit Grund, zu mit Wirkung");

  console.log("26. Jeder Tag hat eine Gruppe");
  // ⚠️ Ein Tag ohne Gruppe landet unter «rest» — sichtbar, aber ohne
  // Bedeutung. Die Gruppe kommt aus dem Feld, das `/api/tags` wirklich
  // liefert.
  {
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const roh = JS.slice(JS.indexOf("const TAG_GRUPPEN = {"));
    const block = roh.slice(0, roh.indexOf("\n};"));
    const zugeordnet = [...block.matchAll(/"([A-Z][A-Z0-9_]*)"/g)]
      .map((m) => m[1]);
    pruefe(zugeordnet.length === 45,
           `${zugeordnet.length} Tags zugeordnet, 45 erwartet`);
    const doppelt = [...new Set(zugeordnet.filter(
      (k) => zugeordnet.indexOf(k) !== zugeordnet.lastIndexOf(k)))];
    pruefe(doppelt.length === 0, `Tag in zwei Gruppen: ${doppelt.join(", ")}`);
  }
  if (!fehler) console.log("   OK   45 Tags, acht Gruppen, keiner doppelt");

  console.log("27. Der gewaehlte Dienst wird sofort gemerkt");
  // ⚠️ Nicht erst beim Schliessen der Einstellungen: wer den Dienst
  // wechselt, geht danach nicht mehr in den Dialog, und nach dem Neuladen
  // stuende wieder der alte da.
  {
    M.zustand.dienste.push({ id: "mistral", name: "Mistral",
                             url: "https://chat.mistral.ai/chat" });
    M.zeichneDienstmenu();
    const menu = document.getElementById("dienstmenu");
    const eintrag = menu._kinder[menu._kinder.length - 1];
    for (const fn of (eintrag._h.click || [])) fn({});
    await new Promise((r) => setTimeout(r, 20));
    pruefe(M.zustand.dienst === "mistral",
           `Dienst ist ${M.zustand.dienst}`);
    pruefe(einstellungen.dienst === "mistral",
           "der Wechsel wurde nicht gesichert");
  }
  if (!fehler) console.log("   OK   gewaehlt und gesichert");

  console.log("28. Keine festen Pixel fuer Groessen im CSS");
  // ⚠️ Layout laesst sich hier nicht messen — die Attrappe hat keine
  // Darstellung, keine Breite, keinen Umbruch. Was sich pruefen laesst, ist
  // die DISZIPLIN: wer eine Hoehe in Pixeln setzt, haengt sie von der Skala
  // ab, und der Schriftregler wirkt dort nicht mehr. Das faengt den
  // Rueckfall, nicht den Fehler.
  //
  // Erlaubt bleiben Kanten und Versaetze: Rahmen, Schatten, Rundungen,
  // Umrisse und alles bis 2px — sie sind Linien, keine Groessen.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const GROESSEN = /(^|[;{}\s])(font-size|height|min-height|width|min-width|padding|padding-top|padding-right|padding-bottom|padding-left|gap|row-gap|column-gap|margin|margin-top|margin-bottom)\s*:\s*([^;{}]+)/g;
    const suender = [];
    // Zeilen in Kommentaren und in @media/@container zaehlen nicht.
    const ohneKommentar = CSS.replace(/\/\*[\s\S]*?\*\//g, "");
    const ohneAbfragen = ohneKommentar.replace(
      /@(?:media|container)[^{]*\{/g, "{");
    let m;
    while ((m = GROESSEN.exec(ohneAbfragen)) !== null) {
      const werte = [...m[3].matchAll(/(-?\d*\.?\d+)px/g)]
        .map((x) => Math.abs(parseFloat(x[1])))
        .filter((n) => n > 2);
      if (werte.length) suender.push(`${m[2]}: ${m[3].trim()}`);
    }
    pruefe(suender.length === 0,
           `${suender.length} feste Groesse(n): ${suender.slice(0, 4).join(" | ")}`);

    // Die Wortmarke und die Bereichstitel behalten ihre Schrift.
    const fest = (CSS.match(/var\(--font-heading\)/g) || []).length;
    pruefe(fest >= 4 && fest <= 6,
           `${fest} Stellen mit fester Titelschrift, 4 bis 6 erwartet`);
    pruefe(/--skala/.test(CSS) && /calc\(100% \* var\(--skala\)\)/.test(CSS),
           "die Wurzelgroesse haengt nicht an --skala");

    // ⚠️⚠️ UND DAS HTML. Ein `style`-Attribut ist dieselbe Aussage wie eine
    // CSS-Zeile und gehoert derselben Regel. Eine Wache, die nur
    // `maschera.css` liest, kennt den zweiten Verwalter nicht.
    const HTML = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const inline = [];
    for (const m of HTML.matchAll(/style="([^"]*)"/g)) {
      for (const g of m[1].matchAll(
             /(font-size|height|width|padding|margin|gap)[a-z-]*\s*:\s*([^;]+)/g)) {
        const zu = [...g[2].matchAll(/(-?\d*\.?\d+)px/g)]
          .map((x) => Math.abs(parseFloat(x[1])))
          .filter((n) => n > 2);
        if (zu.length) inline.push(g[0].trim());
      }
    }
    pruefe(inline.length === 0,
           `${inline.length} feste Groesse(n) INLINE im HTML: `
           + inline.slice(0, 4).join(" | "));
  }
  if (!fehler) console.log("   OK   alles in rem, im CSS wie im HTML");

  console.log("29. Ablegen LIEST — es maskiert nicht");
  // ⚠️ Eine abgelegte Datei landet in Bereich 01 und nirgends sonst. Ein
  // Ablegen, das gleich maskiert, fuellte drei Bereiche auf einmal —
  // Klartext, Maskierung und den ausgehenden Text —, ohne dass jemand
  // MASKIEREN gedrueckt hat. Der Knopf, der die Handlung benennt, wuerde
  // uebersprungen.
  {
    bestaetigt = true;
    await feuer("knopf-neu");
    const vorher = anonymRufe;
    await feuerAblage("brief.txt");
    pruefe(letzteAnfrage.url.includes("/api/lesen"),
           "Ablegen ging an " + letzteAnfrage.url);
    pruefe(anonymRufe === vorher,
           "Ablegen hat trotzdem maskiert (/api/anonymisieren gerufen)");
    pruefe(document.getElementById("orig").value === GELESEN,
           "Spalte 1 traegt nicht den gelesenen Text");
    pruefe(M.zustand.antwort === null,
           "Bereich 02 ist gefuellt, obwohl nur gelesen wurde");
    // ⚠️ Nicht «Bereich 03 ist leer» pruefen: dort steht ein Prompt aus
    // frueheren Punkten, und der gehoert dorthin. Gefragt ist, ob der
    // ABGELEGTE Text mitgewandert ist — `ausgehend()` haengt den maskierten
    // Text an, sobald es einen gibt.
    pruefe(!text(document.getElementById("hinaus")).includes("Brülhart"),
           "Bereich 03 traegt den abgelegten Text: "
           + text(document.getElementById("hinaus")).slice(0, 60));
    pruefe(document.getElementById("knopf-maskieren").disabled === false,
           "MASKIEREN ist nach dem Ablegen nicht bereit");
  }
  if (!fehler) console.log("   OK   gelesen, nicht maskiert");

  console.log("30. Getippter Text ueberlebt ein Ablegen nicht ungefragt");
  // ⚠️ `verwerfenOk` fragt auch nach getipptem Text, nicht nur nach einem
  // Woerterbuch. Wer eine Seite tippt und dann eine Datei ablegt, verloere
  // den Text sonst wortlos — der teurere Fall waere ungeschuetzt, der
  // billigere geschuetzt.
  {
    await feuer("knopf-neu");
    const feld = document.getElementById("orig");
    feld.value = "Von Hand getippt, noch nicht maskiert.";
    for (const f of (feld._h["input"] || [])) await f({ target: feld });
    bestaetigt = false;
    letzteFrage = null;
    const vorAdresse = letzteAnfrage.url;
    await feuerAblage("brief.txt");
    pruefe(letzteFrage !== null, "keine Rueckfrage vor dem Verwerfen");
    pruefe(letzteAnfrage.url === vorAdresse,
           "trotz Nein wurde gelesen: " + letzteAnfrage.url);
    pruefe(feld.value === "Von Hand getippt, noch nicht maskiert.",
           "der getippte Text ist weg, obwohl abgelehnt wurde");
    bestaetigt = true;
    await feuerAblage("brief.txt");
    pruefe(feld.value === GELESEN, "nach Ja wurde nicht gelesen");
  }
  if (!fehler) console.log("   OK   gefragt, und das Nein gilt");

  console.log("31. Die Oberflaeche schickt keine Datei mehr an die Kette");
  // ⚠️ Zwei Wege zu derselben Sache, von denen einer benutzt wird, ist die
  // Fehlerklasse, die in diesem Projekt viermal auftrat. Geprueft wird die
  // QUELLE: zur Laufzeit sieht man einen ungenutzten Pfad nicht.
  {
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const ohneKommentar = JS.replace(/\/\*[\s\S]*?\*\//g, "")
                            .replace(/^\s*\/\/.*$/gm, "");
    pruefe(!/FormData[\s\S]{0,400}?\/api\/anonymisieren/.test(ohneKommentar),
           "eine Datei geht noch an /api/anonymisieren");
    const formulare = (ohneKommentar.match(/new FormData\(\)/g) || []).length;
    pruefe(formulare === 1,
           formulare + " Stellen bauen ein FormData, genau eine erwartet");
  }
  if (!fehler) console.log("   OK   ein Dateiweg, nicht zwei");

  console.log("32. Die Fassung bleibt sichtbar, und ohne Attrappe");
  // ⚠️ Die FASSUNGSNUMMER steht in der Oberflaeche. Sie ist das Einzige,
  // was in einem Fehlerbericht aus der Beta sagt, welcher Stand gemeint war;
  // sie beim Aufraeumen zu verlieren waere teuer und unauffaellig.
  {
    const HTML2 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    pruefe(!/class="titelleiste"/.test(HTML2),
           "die nachgebaute Titelleiste ist zurueck");
    pruefe(!/data-ansicht/.test(HTML2),
           "der APP/WEB-Umschalter ist zurueck — er blendete nur die "
           + "Attrappe ein und aus");
    const feld = document.getElementById("version");
    pruefe(feld !== null, "kein Element `version` mehr im HTML");
    pruefe(String(feld.textContent).includes("0.0.0-attrappe"),
           "die Fassung steht nicht in der Oberflaeche, sondern: "
           + JSON.stringify(String(feld.textContent)));
    // ⚠️ Sie muss vom SERVER kommen. Eine Zahl im HTML waere ein zweiter
    // Verwalter fuer etwas, das in `app/serve.py` steht.
    pruefe(!/id="version"[^>]*>v?\d/.test(HTML2),
           "im HTML steht eine feste Fassungsnummer");
  }
  if (!fehler) console.log("   OK   keine Attrappe, Fassung vom Server");

  console.log("33. Zahnrad und Einklappen fluchten am rechten Rand");
  // Das Zahnrad steht aussen rechts und bildet mit dem «Einklappen»-Knopf
  // der Spalte darunter eine Linie.
  //
  // Zwei Zahlen meinen dasselbe: der rechte Innenabstand der Kopfzeile und
  // der von `.bereich-kopf`. Eine Buendigkeit, die niemand nachprueft, ist
  // beim naechsten Griff ins CSS wieder weg.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const HTML3 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const rechts = (regel) => {
      const m = CSS.match(
        new RegExp(regel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
                   + "\\s*\\{[^}]*?padding:\\s*([^;}]+)"));
      if (!m) return null;
      const teile = m[1].trim().split(/\s+/);
      // padding: oben rechts unten [links] — der zweite Wert ist rechts.
      return teile.length >= 2 ? teile[1] : teile[0];
    };
    const kopf = rechts(".kopfzeile");
    const bereich = rechts(".bereich-kopf");
    pruefe(kopf !== null && bereich !== null,
           `Innenabstand nicht gefunden: Kopfzeile ${kopf}, Bereich ${bereich}`);
    pruefe(kopf === bereich,
           `Kopfzeile haelt rechts ${kopf}, .bereich-kopf ${bereich} — das `
           + "Zahnrad flieht nicht mehr mit «Einklappen»");
    // Und die Reihenfolge: Zahnrad NACH den Sprachen, sonst steht es innen.
    const i_sprachen = HTML3.indexOf('id="sprachen"');
    const i_zahnrad = HTML3.indexOf('id="knopf-einstellungen"');
    pruefe(i_sprachen > 0 && i_zahnrad > i_sprachen,
           "das Zahnrad steht wieder vor den Sprachknoepfen, also nicht "
           + "aussen");
  }
  if (!fehler) console.log("   OK   gleicher Abstand, Zahnrad aussen");

  console.log("34. Der Knopf «Vokabular einpflegen» steht links");
  // ⚠️ Sein Pfeil zeigt nach LINKS — dorthin, wo das Vokabular einfliesst.
  // Rechts angeschlagen zeigte er aus dem Fenster hinaus. Das `.weit` am
  // Knopf setzt `margin-left: auto` und muss zurueckgenommen werden, sonst
  // gewinnt es gegen `justify-content`.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/\.fuss-04\s*\{[^}]*justify-content:\s*flex-start/.test(CSS),
           "der Fuss von 04 ist nicht linksbuendig");
    pruefe(/\.fuss-04\s+\.weit\s*\{[^}]*margin-left:\s*0/.test(CSS),
           "`.weit` schiebt den Knopf weiter nach rechts");
  }
  if (!fehler) console.log("   OK   linksbuendig, kein margin-left: auto");

  console.log("35. Beim Ziehen dunkelt die Seite ab, die Flaeche bleibt hell");
  // Eine gezogene Datei zeigt, wohin sie gehoert.
  //
  // ⚠️ Der zweite Teil ist der wichtigere: ohne `preventDefault` auf dem
  // DOKUMENT oeffnet der Browser die daneben abgelegte Datei und ersetzt die
  // Oberflaeche. Im eigenen Fenster gibt es keine Adresszeile, um
  // zurueckzukommen — ein ungespeichertes Woerterbuch waere weg.
  {
    const schleier = document.getElementById("ziehschleier");
    pruefe(schleier !== null, "kein Element `ziehschleier` im HTML");

    const ueber = (typen) => {
      let verhindert = false;
      const e = {
        preventDefault() { verhindert = true; },
        stopPropagation() {},
        dataTransfer: { types: typen, files: [] },
      };
      for (const f of (document._h["dragover"] || [])) f(e);
      return verhindert;
    };

    pruefe((document._h["dragover"] || []).length > 0,
           "kein Horcher auf dem Dokument fuer `dragover`");
    pruefe(ueber(["Files"]), "`dragover` mit Datei wird nicht verhindert");
    pruefe(schleier.hidden === false, "der Schleier bleibt verborgen");
    pruefe(document.body.classList.contains("zieht"),
           "der Koerper traegt die Klasse `zieht` nicht");

    // Ein gezogener TEXT ist keine Datei — dann darf nichts abdunkeln.
    let verhindert = ueber(["text/plain"]);
    pruefe(!verhindert,
           "auch gezogener Text wird verhindert — das ist zu viel");

    // Ablegen NEBEN der Flaeche: Schleier weg, und der Browser darf die
    // Datei nicht oeffnen.
    let dropVerhindert = false;
    const ed = {
      preventDefault() { dropVerhindert = true; },
      stopPropagation() {},
      dataTransfer: { types: ["Files"], files: [{ name: "x.pdf" }] },
    };
    for (const f of (document._h["drop"] || [])) f(ed);
    pruefe(dropVerhindert,
           "ein Ablegen neben der Flaeche wird nicht verhindert — der "
           + "Browser oeffnet die Datei und die Oberflaeche ist weg");
    pruefe(schleier.hidden === true, "der Schleier bleibt nach dem Ablegen");
    pruefe(!document.body.classList.contains("zieht"),
           "die Klasse `zieht` bleibt am Koerper haengen");

    // Und der Schleier darf nichts abfangen, sonst faengt er den Griff ab,
    // den er erklaert.
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/\.ziehschleier\s*\{[^}]*pointer-events:\s*none/.test(CSS),
           "der Schleier faengt Zeiger ab");
    pruefe(/\.ziehschleier\[hidden\]\s*\{[^}]*display:\s*none/.test(CSS),
           "`[hidden]` ist nicht mit `display: none` abgesichert — eine "
           + "spaetere `display`-Regel schlaegt es sonst");
  }
  if (!fehler) console.log("   OK   Schleier an und aus, Datei wird nicht "
                           + "geoeffnet");

  console.log("36. Der Fortschritt zeigt Gemessenes, nicht Gefuehltes");
  // Ein laengeres Dokument braucht Sekunden. Der Balken haengt an
  // `/api/fortschritt`, und der Server meldet dort die Zahl der FENSTER — die
  // steht nach dem Tokenisieren fest, bevor gerechnet wird.
  //
  // ⚠️ Solange keine Zahl da ist, muss er WANDERN und darf keine Strecke
  // vortaeuschen. Dasselbe Versprechen wie beim Startbildschirm, wo aus
  // genau diesem Grund kein Prozentbalken steht (`test_app.py` Punkt 15).
  {
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const ohneKommentar = JS.replace(/\/\*[\s\S]*?\*\//g, "")
                            .replace(/^\s*\/\/.*$/gm, "");
    pruefe(/fetch\("\/api\/fortschritt"\)/.test(ohneKommentar),
           "niemand fragt /api/fortschritt");
    // Kein setInterval: bei einem beschaeftigten Server stauen sich die
    // Anfragen, und die Anzeige haengt der Rechnung hinterher.
    pruefe(!/setInterval/.test(ohneKommentar),
           "der Fortschritt wird mit setInterval geholt");

    const kasten = document.getElementById("lauf");
    pruefe(kasten !== null, "kein Element `lauf` im HTML");
    // Waehrend eines Laufs — sonst greift die Wache unten.
    M.zustand.laeuft = true;

    M.laufAnzeigen(null);
    pruefe(kasten.hidden === false, "der Balken bleibt verborgen");
    pruefe(kasten.classList.contains("unbestimmt"),
           "ohne Zahl taeuscht der Balken eine Strecke vor");

    M.laufAnzeigen({ aktiv: true, schritt: 3, von: 12, phase: "modell" });
    pruefe(!kasten.classList.contains("unbestimmt"),
           "mit Zahl wandert der Balken immer noch");
    // ⚠️ 3 von 12 sind 25 %, davon 92 % Modellanteil = 23 %. Die letzten
    // 8 % gehoeren Regeln, Zusammenfuehren und Ersetzen — der Balken darf
    // beim letzten Fenster NICHT voll dastehen, waehrend noch gerechnet
    // wird. Das ist derselbe Grundsatz wie «keine erfundenen Prozente»,
    // nur andersherum: auch ein zu HOHER Wert ist eine falsche Zusage.
    pruefe(document.getElementById("lauf-fuellung").style.width === "23%",
           "die Fuellung sagt "
           + document.getElementById("lauf-fuellung").style.width
           + " statt 23%");
    {
      const wort = document.getElementById("lauf-wort").textContent;
      pruefe(/23\s*%/.test(wort), "kein Prozentsatz: " + wort);
      // ⚠️ «Fenster 9 von 12» sagt dem Anwender nichts. Die Zahl bleibt als
      // Tooltip — dort hilft sie beim Suchen —, sichtbar steht sie nicht.
      pruefe(!/\b12\b/.test(wort),
             "die Fensterzahl steht wieder sichtbar da: " + wort);
      pruefe(/3/.test(kasten.title) && /12/.test(kasten.title),
             "der Tooltip nennt die Fenster nicht: " + kasten.title);
    }

    // ⚠️ Die Restzeit NICHT beim ersten Fenster. Aus einem einzigen
    // Messpunkt laesst sich keine Geschwindigkeit ableiten; was dann
    // dastuende, waere geraten — und geratene Zahlen sind hier
    // ausdruecklich nicht erwuenscht (Grundsatz «Fortschritt zeigt
    // Gemessenes, nicht Gefuehltes»).
    pruefe(!/noch etwa/.test(document.getElementById("lauf-wort").textContent),
           "die Restzeit steht schon beim ersten Messpunkt da: "
           + document.getElementById("lauf-wort").textContent);

    // Volle Sekunden, keine Nachkommastelle — «noch etwa 4,3 s» taeuscht
    // eine Genauigkeit vor, die eine Hochrechnung nicht hat.
    pruefe(M.restWort(4300) === "4 s", "restWort(4300) = " + M.restWort(4300));
    pruefe(M.restWort(200) === "1 s", "restWort rundet auf null Sekunden");
    pruefe(M.restWort(125000) === "2 min", "restWort(125000) = "
           + M.restWort(125000));

    // In der Maskierphase steht der Balken nicht voll, aber weiter als das
    // letzte Fenster — dort laeuft noch etwas.
    M.laufAnzeigen({ aktiv: true, schritt: 12, von: 12, phase: "maskieren" });
    pruefe(document.getElementById("lauf-fuellung").style.width === "96%",
           "die Maskierphase steht bei "
           + document.getElementById("lauf-fuellung").style.width);

    M.laufAus();
    pruefe(kasten.hidden === true, "der Balken bleibt nach dem Lauf stehen");

    // ⚠️ Ein Rennen. `fortschrittHolen()` wartet auf die Antwort des
    // Servers; ist der Lauf in 200 ms vorbei, kommt sie NACH `laufAus()` an
    // und machte den Balken wieder sichtbar — mit `von: 0`, also wandernd und
    // ohne Ende, denn ein neuer Zeitgeber wird nicht mehr gestellt.
    //
    // Hier nachgestellt: eine spaete Meldung, nachdem der Lauf vorbei ist.
    M.zustand.laeuft = false;
    M.laufAnzeigen({ aktiv: false, schritt: 0, von: 0, phase: "" });
    pruefe(kasten.hidden === true,
           "eine spaete Meldung macht den Balken wieder sichtbar — genau "
           + "der Fehler beim Beispieltext");
    M.laufAnzeigen({ aktiv: true, schritt: 5, von: 9, phase: "modell" });
    pruefe(kasten.hidden === true,
           "auch eine spaete Meldung MIT Zahlen zeigt den Balken wieder");

    // Und die vier Sprachen — ein Balken, der nur deutsch beschriftet ist,
    // ist fuer drei Viertel der Oberflaeche keiner.
    for (const schluessel of ["lWartet", "lModell", "lMaskieren", "lFertig",
                              "lRest"]) {
      const n = (JS.match(new RegExp(schluessel + ":", "g")) || []).length;
      pruefe(n === 4, `${schluessel} steht ${n}x, viermal erwartet`);
    }
  }
  if (!fehler) console.log("   OK   echte Fenster, wandernd ohne Zahl, "
                           + "4 Sprachen");

  console.log("37. Leeren und Kopieren sind sichtbar und sagen, was sie tun");
  // Leeren und Kopieren tragen eine eigene Farbe. Ein Knopf, den man
  // suchen muss, ist im Zweifel keiner, und der Kopierknopf ist der Weg, auf
  // dem dieses Werkzeug ueberhaupt benutzt wird.
  //
  // ⚠️ Geprueft wird vor allem die ZUORDNUNG: jeder Knopf, dessen Kennung
  // «leeren» oder «kopieren» sagt, muss seine Klasse tragen. Sonst faerbt
  // sich der naechste neue Knopf still nicht mit.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const HTML4 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");

    pruefe(/\.imfeld\s*\{[^}]*background:\s*var\(--color-neutral-100\)/.test(CSS),
           "die Knoepfe stehen wieder auf weissem Grund");
    pruefe(/\.imfeld\s*\{[^}]*border:[^;]*--color-neutral-400/.test(CSS),
           "der Rand ist wieder zu blass");
    pruefe(/\.imfeld\.kopieren:hover:not\(:disabled\)\s+svg\s*\{[^}]*color:/
           .test(CSS), "kein gruenes Zeichen beim Kopieren");
    pruefe(/\.imfeld\.loeschen:hover:not\(:disabled\)\s+svg\s*\{[^}]*color:/
           .test(CSS), "kein rotes Zeichen beim Leeren");

    const knoepfe = [...HTML4.matchAll(
      /<button class="([^"]*imfeld[^"]*)" id="([^"]+)"/g)];
    pruefe(knoepfe.length >= 10,
           `nur ${knoepfe.length} Knoepfe im Feld gefunden`);
    for (const [, klassen, kennung] of knoepfe) {
      if (/leeren/.test(kennung)) {
        pruefe(/\bloeschen\b/.test(klassen),
               `${kennung} leert, traegt aber nicht \`loeschen\``);
      }
      if (/kopieren/.test(kennung)) {
        pruefe(/\bkopieren\b/.test(klassen),
               `${kennung} kopiert, traegt aber nicht \`kopieren\``);
      }
      // ⚠️ UND «BEARBEITEN» als hellgruene Nebenhandlung: Bereich 02 ist
      // beschreibbar, und eine Moeglichkeit, die niemand findet, gibt es
      // praktisch nicht.
      if (/bearbeiten/.test(kennung)) {
        pruefe(/\bbearbeiten\b/.test(klassen),
               `${kennung} oeffnet das Feld, traegt aber nicht `
               + "`bearbeiten`");
      }
      // Und andersherum: keine Klasse ohne passende Kennung.
      if (/\bloeschen\b/.test(klassen)) {
        pruefe(/leeren/.test(kennung),
               `${kennung} faerbt sich rot, leert aber nichts`);
      }
      if (/\bbearbeiten\b/.test(klassen)) {
        pruefe(/bearbeiten/.test(kennung),
               `${kennung} faerbt sich gruen, oeffnet aber nichts`);
      }
    }

    pruefe(/\.imfeld\.bearbeiten\s*\{[^}]*background:/.test(CSS),
           "«Bearbeiten» traegt keine eigene Farbe");
    // ⚠️ GEDRUECKT voll gruen — und die Regel muss HINTER `.imfeld.aktiv`
    // stehen. Gleiche Spezifitaet, also gewinnt die spaetere; davor
    // stehend faerbte `aktiv` den Knopf grau, und er verloere seine Farbe
    // genau dann, wenn das Feld beschreibbar ist.
    pruefe(/\.imfeld\.bearbeiten\.aktiv\s*\{/.test(CSS),
           "«Bearbeiten» verliert im gedrueckten Zustand seine Farbe");
    pruefe(CSS.indexOf(".imfeld.bearbeiten.aktiv")
             > CSS.indexOf(".imfeld.aktiv {"),
           "`.imfeld.bearbeiten.aktiv` steht vor `.imfeld.aktiv` — bei "
           + "gleicher Spezifitaet gewinnt dann das Grau");
    // ⚠️ Beim Ueberfahren NICHT umgekehrt, anders als beim Leerknopf:
    // dort ist die Umkehr eine Warnung, und Bearbeiten nimmt nichts weg.
    const hov = /\.imfeld\.bearbeiten:hover:not\(:disabled\)\s*\{([^}]*)\}/
      .exec(CSS);
    pruefe(hov !== null, "«Bearbeiten» reagiert nicht auf das Ueberfahren");
    pruefe(hov === null || !/#fff/.test(hov[1]),
           "«Bearbeiten» kehrt beim Ueberfahren um wie der Leerknopf — "
           + "das ist dort eine Warnung, und hier wird nichts geloescht");
  }
  if (!fehler) console.log("   OK   hellgrau, gruen fuers Kopieren, rot "
                           + "fuers Leeren, alle zugeordnet");

  console.log("38. Die dritte Spalte fuellt sich nicht von selbst");
  // ⚠️ Den maskierten Text traegt NUR der Klick auf «Uebernahme in Prompt»
  // in Spalte 3.
  //
  // Das ist kein Schoenheitsgriff. Spalte 3 ist die einzige, die hinausgeht
  // — sie soll sich nicht von selbst fuellen. Und weil Kopier- und
  // Sendeknopf an `ausgehend()` haengen, kopiert vor der Uebernahme auch
  // niemand versehentlich das Dokument.
  {
    await feuer("knopf-neu");
    await feuer("knopf-beispiel");
    await feuer("knopf-maskieren");
    await new Promise((r) => setTimeout(r, 30));

    pruefe(M.zustand.antwort !== null, "es wurde gar nicht maskiert");
    pruefe(M.uebernommenerText() === "",
           "der maskierte Text steht in Spalte 3, ohne dass jemand "
           + "uebernommen hat");
    pruefe(!/\[/.test(M.ausgehend()),
           "was hinausgeht, traegt schon Platzhalter: "
           + JSON.stringify(M.ausgehend().slice(0, 60)));
    // ⚠️ NICHT auf `istleer` pruefen: steht ein Prompt im Feld, ist die
    // Anzeige zu Recht nicht leer — sie zeigt dann den Prompt, und der
    // gehoert dem Anwender. Geprueft wird, dass vom DOKUMENT nichts drin
    // steht.
    const hinaus = document.getElementById("hinaus");
    const gezeigt = (hinaus._kinder || []).map((k) => k.t || k.textContent)
      .join(" ");
    pruefe(!/\[[A-Z]/.test(gezeigt),
           "Spalte 3 zeigt Platzhalter, ohne dass uebernommen wurde: "
           + JSON.stringify(gezeigt.slice(0, 60)));

    await feuer("knopf-uebernahme");
    pruefe(M.uebernommenerText() !== "",
           "nach der Uebernahme steht der Text immer noch nicht da");
    pruefe(/\[/.test(M.ausgehend()) && /————/.test(M.ausgehend()),
           "nach der Uebernahme fehlt der Anhang in `ausgehend()`");

    // ⚠️ Und ein NEUER Lauf nimmt die Uebernahme zurueck. Sonst stuende
    // dort der Text von vorhin, waehrend links ein anderes Dokument liegt
    // — und was dort steht, ist genau das, was hinausgeht.
    await feuer("knopf-maskieren");
    await new Promise((r) => setTimeout(r, 30));
    pruefe(M.uebernommenerText() === "",
           "nach einem neuen Lauf steht der alte Text weiter in Spalte 3");

    // Ebenso «Neu».
    await feuer("knopf-uebernahme");
    await feuer("knopf-neu");
    pruefe(M.zustand.uebernommen === false,
           "«Neu» nimmt die Uebernahme nicht zurueck");

    // Die Beschriftung des leeren Feldes muss auf den KNOPF zeigen, nicht
    // mehr aufs Maskieren — in allen vier Sprachen.
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const leerTexte = [...JS.matchAll(/hinausLeer: "([^"]*)"/g)].map((m) => m[1]);
    pruefe(leerTexte.length === 4,
           `${leerTexte.length} Sprachen mit hinausLeer statt 4`);
    for (const zeile of leerTexte) {
      pruefe(/«|»/.test(zeile),
             "der leere Hinweis nennt den Knopf nicht: " + zeile);
    }
  }
  if (!fehler) console.log("   OK   leer bis zum Klick, neuer Lauf setzt "
                           + "zurueck");

  console.log("39. Der Dienstname im Sendeknopf ist fett — und kein HTML");
  // ⚠️ Der wechselnde Teil des Sendeknopfs faellt auf: der Knopf ist der
  // Moment, in dem etwas hinausgeht.
  //
  // ⚠️ ZUSAMMENGESETZT AUS KNOTEN, nicht mit `innerHTML`. Der Dienstname
  // kommt aus den Einstellungen, also vom Server, und ein eigener Dienst
  // heisst, was der Anwender tippt. «Nie `innerHTML` mit Serverdaten» ist
  // einer der Grundsaetze, die nicht verhandelbar sind.
  {
    M.zustand.sendeUhr = null;
    M.laufAus();
    await feuer("knopf-beispiel");
    const feld = document.getElementById("senden-text");
    const fette = (feld._kinder || []).filter((k) => k.id === "_neu_b");
    pruefe(fette.length === 1,
           `${fette.length} fette Teile im Sendeknopf statt genau einem`);
    if (fette.length === 1) {
      pruefe(String(fette[0].textContent).length > 0,
             "der fette Teil ist leer");
      pruefe(!/[<>]/.test(String(fette[0].textContent)),
             "im fetten Teil steht Markup: " + fette[0].textContent);
    }
    // Der Rest der Beschriftung darf nicht verschwinden.
    const stuecke = (feld._kinder || []).length;
    pruefe(stuecke >= 2,
           `nur ${stuecke} Stueck(e) im Knopf — der Text um den Namen fehlt`);

    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const ohneKommentar = JS.replace(/\/\*[\s\S]*?\*\//g, "")
                            .replace(/^\s*\/\/.*$/gm, "");
    pruefe(!/innerHTML/.test(ohneKommentar),
           "es gibt wieder eine `innerHTML`-Stelle in der Oberflaeche");
  }
  if (!fehler) console.log("   OK   ein fetter Teil, aus Knoten gebaut");

  console.log("40. Zwei Stufen: drei Spalten oder alles untereinander");
  // ⚠️ Die Oberflaeche bricht um, statt eine Mindestbreite zu erzwingen.
  // Bei einem halbierten FullHD-Fenster (960 px) waere eine feste
  // Mindestbreite von rund 980 px eine Rollleiste unter einem Layout, das
  // sonst passt.
  //
  // ⚠️ Und weil `rem` an `--skala` haengt, wandert eine solche Mindestbreite
  // mit dem Schriftregler.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const HTML5 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");

    // ⚠️ Ohne Kommentare pruefen. Die Begruendung, warum die alte
    // Mindestbreite weg ist, NENNT sie — beim ersten Versuch schlug diese
    // Zeile an ihrer eigenen Erklaerung an. Derselbe Fehler wie heute
    // frueh beim fail2ban-Muster.
    const CSSohne = CSS.replace(/\/\*[\s\S]*?\*\//g, "");
    pruefe(!/min-width:\s*61\.25rem/.test(CSSohne),
           "die feste Mindestbreite von 980 px ist zurueck");

    // ⚠️ Die Grenzen MUESSEN in `em` stehen. `em` misst in einer
    // Medienabfrage die Schrift des Browsers, nicht `--skala` — sonst
    // verschoeben sich die Umbrueche mit dem Schriftregler.
    const abfragen = [...CSS.matchAll(/@media\s*\(max-width:\s*([\d.]+)(em|px|rem)\)/g)];
    pruefe(abfragen.length >= 1,
           `${abfragen.length} Umbruchpunkte, mindestens 1 erwartet`);
    for (const [, , einheit] of abfragen) {
      pruefe(einheit === "em",
             `ein Umbruchpunkt steht in ${einheit} statt in em`);
    }

    // Die sechs Kaesten brauchen Kennungen, sonst laesst sich weder eine
    // Reihenfolge setzen noch etwas anspringen.
    for (const k of ["b01", "b02", "b03", "b04", "b05", "bvok"]) {
      pruefe(new RegExp(`id="${k}"`).test(HTML5),
             `dem Kasten ${k} fehlt die Kennung`);
    }

    // ⚠️ Die Reihenfolge ist der ARBEITSWEG, nicht die des HTML: im HTML
    // stehen die Kaesten spaltenweise (01, 05, 02, …).
    // ⚠️ Das Vokabular steht an DRITTER Stelle, direkt unter 02 — dort
    // entsteht es. Zugeklappt unterbricht es den Weg nicht. Zuunterst, oder
    // mit einer zweispaltigen Zwischenstufe, rollte man an 05 vorbei und
    // muesste wieder hinauf.
    const folge = ["b01", "b02", "bvok", "b03", "b04", "b05"];
    folge.forEach((k, i) => {
      const m = CSS.match(new RegExp(`#${k}\\s*\\{\\s*order:\\s*(\\d+)`));
      pruefe(m !== null && Number(m[1]) === i + 1,
             `${k} hat order ${m ? m[1] : "keine"}, ${i + 1} erwartet`);
    });

    // Der Sprung darf NUR in der gestapelten Ansicht passieren.
    const ziel = document.getElementById("b02");
    const seite = document.scrollingElement;
    seite.scrollTop = 0;
    ziel._top = 600;
    window._breite = 1400;
    M.springeZu("b02");
    pruefe(seite.scrollTop === 0,
           "nebeneinander wird gesprungen — dort sieht man den naechsten "
           + "Kasten ohnehin");
    window._breite = 375;
    M.springeZu("b02");
    pruefe(seite.scrollTop === 600,
           `untereinander wird NICHT gesprungen (${seite.scrollTop})`);
    ziel._top = 0;
    seite.scrollTop = 0;

    // ⚠️ DIE BEWEGUNG GEHOERT UNS, nicht dem Browser. `behavior: "smooth"`
    // tat im eingebauten Browser gar nichts (auch nach 2.5 s nicht); die
    // Notbremse, die daraufhin nach 350 ms hart sprang, schnitt dann dort
    // ab, wo `smooth` sehr wohl laeuft — «man sieht es nicht mal dass es
    // scrollt». Eine Bewegung, die einmal ausbleibt und einmal
    // abgeschnitten wird, ist keine.
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const ohneK = JS.replace(/\/\*[\s\S]*?\*\//g, "")
                    .replace(/^\s*\/\/.*$/gm, "");
    pruefe(!/behavior:\s*"smooth"/.test(ohneK),
           "die Bewegung haengt wieder an `behavior: \"smooth\"`");
    pruefe(/requestAnimationFrame/.test(ohneK),
           "es gibt keine eigene Bewegung mehr");
    pruefe(/Math\.pow\(1 - t, 3\)/.test(ohneK),
           "die Bewegung bremst nicht ab (kubisch auslaufend)");
    // Ohne Bildfolge — etwa in dieser Pruefung — bleibt der harte Sprung.
    pruefe(/behavior:\s*"auto"/.test(ohneK),
           "ohne `requestAnimationFrame` gibt es keinen Rueckfall");

    // Das Vokabular startet zugeklappt.
    pruefe(M.zustand.vokZu === true,
           "das Vokabular startet aufgeklappt");
    M.vokabularKlappe();
    pruefe(document.getElementById("bvok").classList.contains("zu"),
           "der Kasten traegt die Klasse `zu` nicht");
    window._breite = 1400;
  }
  if (!fehler) console.log("   OK   em-Grenzen, Arbeitsweg-Reihenfolge, "
                           + "Sprung nur gestapelt, Vokabular zu");

  console.log("41. «Neu» leert das GANZE Formular, und fragt vorher");
  // ⚠️ «Neu» raeumt ALLE Bereiche, auch Prompt, eingefuegte Antwort und
  // finalen Text. Wer ein zweites Dokument beginnt, soll nicht mit dem
  // Prompt und der Antwort des vorigen weiterarbeiten, ohne es zu merken —
  // bei einem Werkzeug, dessen Zweck das Trennen von Dokumenten ist.
  {
    await feuer("knopf-beispiel");
    M.zustand.prompt = "Ein Prompt aus einer Vorlage";
    document.getElementById("prompt").value = M.zustand.prompt;
    M.zustand.antwort04 = "Antwort der Sitzung davor";
    document.getElementById("antwort04").value = M.zustand.antwort04;
    M.zustand.final = { text: "fertiger Text" };
    M.zustand.vorlage = "Meine Vorlage";

    // ⚠️ Erst das NEIN: eine Wache, die immer bestaetigt wird, ist keine.
    bestaetigt = false;
    letzteFrage = null;
    await feuer("knopf-neu");
    pruefe(letzteFrage !== null, "«Neu» fragt nicht nach");
    pruefe(M.zustand.prompt !== "", "trotz Nein wurde der Prompt geleert");

    bestaetigt = true;
    await feuer("knopf-neu");
    pruefe(M.zustand.orig === "", "Spalte 1 nicht geleert");
    pruefe(M.zustand.antwort === null, "der maskierte Text blieb stehen");
    pruefe(M.zustand.prompt === "", "der Prompt blieb stehen");
    pruefe(M.zustand.antwort04 === "", "die Antwort aus 04 blieb stehen");
    pruefe(M.zustand.final === null, "der finale Text blieb stehen");
    pruefe(M.zustand.vorlage === null,
           "die gewaehlte Vorlage steht noch im Feld");
    pruefe(document.getElementById("prompt").value === "",
           "das Prompt-FELD wurde nicht geleert, nur der Zustand");

    // ⚠️ Die gespeicherten Vorlagen duerfen NICHT mitgehen: sie liegen in
    // ~/.config/maschera und kommen nur ueber «Speichern» dorthin. Ein
    // «Neu», das sie mitnimmt, waere Datenverlust und kein Aufraeumen.
    pruefe(Array.isArray(M.zustand.vorlagen),
           "die Vorlagenliste ist verschwunden");

    // ⚠️ Der zweite Knopf darf NUR gestapelt sichtbar sein — und dafuer
    // muss seine Regel genauer sein als `button.tat { display: inline-flex }`.
    // Mit blossem `.neu-unten` gewinnt jene, egal in welcher Reihenfolge, und
    // der Knopf stuende auch breit da.
    const CSS0 = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/button\.tat\.neu-unten\s*\{[^}]*display:\s*none/.test(CSS0),
           "die Regel fuer den unteren «Neu» ist zu unspezifisch — "
           + "`button.tat` gewinnt dann");

    // ⚠️ DERSELBE Ablauf ueber den zweiten Einstieg. Untereinander steht
    // 05 am Ende des Weges, zwei Bildschirmlaengen vom Knopf oben
    // entfernt — deshalb gibt es unten einen zweiten. Er muss dasselbe
    // tun; zwei Fassungen desselben Ablaufs sind in diesem Projekt schon
    // viermal auseinandergelaufen.
    await feuer("knopf-beispiel");
    M.zustand.prompt = "Nochmals ein Prompt";
    document.getElementById("prompt").value = M.zustand.prompt;
    bestaetigt = true;
    await feuer("knopf-neu-unten");
    pruefe(M.zustand.orig === "" && M.zustand.prompt === "",
           "der Knopf unten leert nicht dasselbe wie der oben");

    // Und er rollt hinauf — aber nur gestapelt.
    //
    // ⚠️ Gemessen wird der ROLLSTAND, nicht ein `scrollIntoView`: das ist der
    // Rueckfallzweig, den `springeZu()` nur ohne Bildfolge nimmt, und dann
    // liefe nie die Rechnung, um die es geht.
    const oben = document.getElementById("b01");
    const seite1 = document.scrollingElement;
    seite1.scrollTop = 900;
    oben._top = -900;                 // b01 steht ganz oben im Dokument
    window._breite = 375;
    await feuer("knopf-neu-unten");
    pruefe(seite1.scrollTop === 0,
           `nach «Neu» steht die Seite auf ${seite1.scrollTop} statt oben`);
    oben._top = 0;
    seite1.scrollTop = 0;
    window._breite = 1400;
  }
  if (!fehler) console.log("   OK   alles geleert, Vorlagen bleiben, "
                           + "Nein gilt");

  console.log("42. Der Speichern-Knopf schrumpft, ohne stumm zu werden");
  // ⚠️ Wunsch des Anwenders: wird es eng, soll aus «Speichern» ein blosses
  // Zeichen werden. Gemessen wird der BEHAELTER und nicht das Fenster —
  // bei 960 px in drei Spalten ist die Zeile schmaler als auf einem Handy,
  // wo sie die volle Breite hat.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/container-type:\s*inline-size/.test(CSS),
           "es gibt keinen Behaelter — dann misst die Regel das Fenster "
           + "statt den Platz");
    pruefe(/@container[^{]*\(max-width[^)]*\)\s*\{[^}]*#vorlage-sichern-text[^}]*display:\s*none/
           .test(CSS.replace(/\s+/g, " ")),
           "die Beschriftung des Speichern-Knopfes verschwindet nie");

    // ⚠️ UND der Tooltip muss beides tragen: was der Knopf tut, erraet man am
    // Zeichen; dass die Vorlage im Klartext auf der Platte landet, nicht. Die
    // Warnung darf nicht von «Speichern» ueberschrieben werden.
    // ⚠️ NACH `knopfTitelSetzen()` geprueft — genau die Funktion, die sie
    // ueberschreiben koennte.
    M.knopfTitelSetzen();
    const titel = String(
      document.getElementById("knopf-vorlage-sichern").getAttribute("title")
      || document.getElementById("knopf-vorlage-sichern").title || "");
    pruefe(/Klartext/i.test(titel),
           "die Warnung ist aus dem Tooltip verschwunden: " + titel);
    pruefe(titel.length > 20 && /speich/i.test(titel),
           "der Tooltip sagt nicht, was der Knopf tut: " + titel);
  }
  if (!fehler) console.log("   OK   Behaelter statt Fenster, Warnung "
                           + "erhalten");

  console.log("43. Der Abstand der Feldknoepfe haengt am Rollbalken");
  // ⚠️ Der Abstand der Feldknoepfe zum Rand wird GEMESSEN, nicht geraten.
  // Eine feste Zahl passt nur auf den Rollbalken, fuer den sie geraten
  // wurde; bei einem breiteren kleben «Herunterladen» und «Kopieren» daran.
  // Gemessen wird beim Start und in `--rollbalken` abgelegt.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    // ⚠️ Die GRUNDREGEL, nicht irgendeine `.feldknoepfe`-Regel. Es gibt eine
    // zweite in einer `@container`-Abfrage. Erkennungsmerkmal der Grundregel:
    // `position: absolute`.
    const feld = CSS.match(/\.feldknoepfe\s*\{[^}]*position:\s*absolute[^}]*\}/);
    pruefe(feld !== null, "`.feldknoepfe` gibt es nicht mehr");
    if (feld) {
      pruefe(/var\(--rollbalken/.test(feld[0]),
             "der Abstand steht wieder als feste Zahl da: " + feld[0]);
      pruefe(!/right:\s*2\.75rem/.test(feld[0]),
             "die alte geratene Zahl ist zurueck");
    }
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const ohneK = JS.replace(/\/\*[\s\S]*?\*\//g, "")
                    .replace(/^\s*\/\/.*$/gm, "");
    pruefe(/offsetWidth\s*-\s*\S*clientWidth/.test(ohneK),
           "die Breite wird nicht mehr gemessen");
    pruefe(/setProperty\(\s*["']--rollbalken["']/.test(ohneK),
           "der gemessene Wert landet nicht in `--rollbalken`");
  }
  if (!fehler) console.log("   OK   gemessen statt geraten");

  console.log("44. Die Kopfzeile wirft einen Schatten, sobald gerollt ist");
  // ⚠️ Gestapelt schiebt sich der Inhalt unter die Kopfzeile, und ohne
  // Schatten sieht man nicht, dass darueber noch etwas liegt — die Kante
  // wirkt wie ein Seitenanfang.
  //
  // ⚠️ Der Schatten ist eine AUSSAGE und keine Verzierung: «oben geht es
  // weiter». Steht die Seite am Anfang, darf er nicht da sein.
  {
    const raster = document.getElementById("raster");
    const kopf = document.getElementById("kopfzeile");
    pruefe((raster._h["scroll"] || []).length === 1,
           "niemand horcht auf das Rollen des Rasters");

    raster.scrollTop = 0;
    for (const f of (raster._h["scroll"] || [])) f({});
    pruefe(!kopf.classList.contains("gerollt"),
           "am Seitenanfang wirft die Kopfzeile schon einen Schatten");

    raster.scrollTop = 240;
    for (const f of (raster._h["scroll"] || [])) f({});
    pruefe(kopf.classList.contains("gerollt"),
           "nach dem Rollen fehlt der Schatten");

    raster.scrollTop = 0;
    for (const f of (raster._h["scroll"] || [])) f({});
    pruefe(!kopf.classList.contains("gerollt"),
           "der Schatten bleibt haengen, wenn wieder ganz oben");

    // ⚠️ UND GESTAPELT. Dort rollt nicht das Raster, sondern die SEITE —
    // damit die Fusszeile im Fluss steht statt am Fensterrand zu kleben. Eine
    // Wache, die nur den breiten Fall kennt, meldet Ruhe, waehrend der
    // Schatten auf dem Handy stumm ausfaellt.
    {
      const vorher = window._breite;
      window._breite = 500;
      const seite = document.scrollingElement;
      seite.scrollTop = 240;
      for (const f of (window._h["scroll"] || [])) f({});
      pruefe(kopf.classList.contains("gerollt"),
             "gestapelt fehlt der Schatten nach dem Rollen der Seite");

      seite.scrollTop = 0;
      for (const f of (window._h["scroll"] || [])) f({});
      pruefe(!kopf.classList.contains("gerollt"),
             "gestapelt bleibt der Schatten haengen");
      window._breite = vorher;
    }

    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/\.kopfzeile\.gerollt\s*\{[^}]*box-shadow/.test(CSS),
           "die Klasse `gerollt` wirft keinen Schatten");
    // Die Fusszeile darf gestapelt nicht mehr am Fensterrand kleben.
    const gestapeltBlock = CSS.slice(CSS.indexOf(
      "@media (max-width: 59.99em)"));
    pruefe(/main\.raster\s*\{[^}]*overflow:\s*visible/.test(gestapeltBlock),
           "gestapelt rollt weiterhin das Raster — der Fuss bleibt kleben");
    // ⚠️ Ohne Stapelkontext liegt der Schatten UNTER dem Inhalt und ist
    // nicht zu sehen.
    const kopfRegel = CSS.match(/\.kopfzeile\s*\{[^}]*\}/);
    pruefe(kopfRegel !== null && /z-index/.test(kopfRegel[0]),
           "die Kopfzeile hat keinen Stapelkontext — der Schatten liegt "
           + "dann unter dem Inhalt");
  }
  if (!fehler) console.log("   OK   Schatten nur beim Rollen, und sichtbar");

  console.log("45. Jeder Knopf mit Zeichen und Wort hat einen Tooltip");
  // ⚠️ Wird ein Fuss eng, blendet das CSS die Beschriftungen aus und nur
  // die Zeichen bleiben. Ohne Tooltip waere der Knopf dann stumm — ein
  // Bild, das nichts erklaert.
  {
    M.knopfTitelSetzen();
    const knoepfe = document.querySelectorAll("button");
    pruefe(knoepfe.length > 5,
           `nur ${knoepfe.length} Knoepfe gefunden — die Attrappe liefert `
           + "wohl keine");
    let ohne = [];
    for (const k of knoepfe) {
      const wort = String(k.textContent || "").trim();
      if (!wort) continue;
      if (!String(k.getAttribute("title") || "").trim()) ohne.push(k.id);
    }
    pruefe(ohne.length === 0,
           `${ohne.length} Knoepfe ohne Tooltip: ${ohne.slice(0, 4)}`);

    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/@container fuss \(max-width[^)]*\)/.test(CSS),
           "die Fuesse sind keine Behaelter — dann schrumpft nichts");
  }
  if (!fehler) console.log("   OK   alle beschrifteten Knoepfe erklaeren sich");

  console.log("46. Gedreht wird nur, was eine Richtung meint");
  // ⚠️ Gestapelt dreht die Regel fuer Richtungspfeile NUR diese. Ein
  // Pfeil, der eine RICHTUNG meint, wird gedreht. Ein Zeichen, das etwas
  // anderes meint — das Kopierzeichen, das Plus in «Neu», der Pfeil des
  // Ausklappmenues —, nicht. Der Menuepfeil sagt «hier klappt etwas auf»;
  // zur Seite gedreht sagt er das Gegenteil von dem, was passiert.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const HTML6 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const ohneK = CSS.replace(/\/\*[\s\S]*?\*\//g, "");

    // ⚠️ Nicht jede `button.tat svg`-Regel ist falsch — eine setzt
    // `flex: none`, und die ist richtig. Geprueft wird die Regel, die
    // DREHT.
    const dreht = /button\.tat svg\s*\{[^}]*transform:\s*rotate/;
    pruefe(!dreht.test(ohneK),
           "es wird wieder JEDES Zeichen in einem `.tat`-Knopf gedreht");
    pruefe(/svg\.richtung/.test(ohneK),
           "die Drehung haengt nicht an `.richtung`");

    // Die drei Richtungspfeile sind ausgezeichnet — und nur die.
    // ⚠️ Gezaehlt wird das KLASSEN-TOKEN, nicht die Zeichenkette
    // `class="richtung"`: ein Pfeil darf eine zweite Klasse tragen. Eine
    // Wache prueft die Eigenschaft, nicht die Schreibweise.
    const ausgezeichnet = (HTML6.match(/class="[^"]*\brichtung\b[^"]*"/g) || []).length;
    pruefe(ausgezeichnet === 3,
           `${ausgezeichnet} Zeichen als Richtung ausgezeichnet, 3 erwartet`);

    // ⚠️ Und der Menuepfeil ist KEINER davon.
    const i = HTML6.indexOf('id="knopf-dienstmenu"');
    const bis = HTML6.indexOf("</button>", i);
    pruefe(i > 0 && !/class="richtung"/.test(HTML6.slice(i, bis)),
           "der Pfeil des Ausklappmenues gilt wieder als Richtungspfeil");
  }
  if (!fehler) console.log("   OK   drei Richtungspfeile, Menuepfeil "
                           + "bleibt");

  console.log("47. Hinweise des Servers folgen der Sprache der Oberflaeche");
  // ⚠️ Meldungen des Servers kommen als `{schluessel, werte, text}` und
  // nicht als fertige Saetze — der Server kennt die Sprache der Oberflaeche
  // nicht. Geprueft wird beides: dass die Sprache gilt UND dass die Werte
  // eingesetzt werden — ein uebersetzter Satz mit `{token}` darin waere kein
  // Fortschritt.
  {
    const alteSprache = M.zustand.sprache;
    const h = { schluessel: "fenster", werte: { token: 512 },
                text: "Länger als ein Fenster (512 Token)." };

    M.zustand.sprache = "it";
    const it = M.hinweisText(h);
    pruefe(it.includes("512"), "Wert nicht eingesetzt: " + it);
    pruefe(!/\{token\}/.test(it), "Platzhalter blieb stehen: " + it);
    pruefe(it === M.I18N.it.hinweise.fenster.replace("{token}", "512"),
           "italienisch stimmt nicht: " + it);
    pruefe(it !== M.I18N.de.hinweise.fenster.replace("{token}", "512"),
           "unter it steht der deutsche Satz");

    // Ein Feld als Wert ist eine Liste von SCHLUESSELN und wird selbst
    // uebersetzt — sonst stuenden «Kopfzeilen, Fusszeilen» deutsch mitten
    // in einem italienischen Satz.
    const t = M.hinweisText({ schluessel: "nicht_gelesen",
                              werte: { teile: ["t_kopfzeilen"] },
                              text: "NICHT gelesen: Kopfzeilen" });
    pruefe(t.includes(M.I18N.it.hinweise.t_kopfzeilen),
           "Teilname nicht uebersetzt: " + t);
    pruefe(!t.includes("Kopfzeilen"), "deutscher Teilname blieb: " + t);

    // Unbekannter Schluessel: lieber der deutsche Satz als eine leere
    // Zeile. Und die alte Form — eine blosse Zeichenkette — muss weiter
    // erscheinen, damit ein alter Server nichts verschluckt.
    pruefe(M.hinweisText({ schluessel: "gibtsnicht", werte: {},
                           text: "Rueckfall" }) === "Rueckfall",
           "kein Rueckfall auf `text`");
    pruefe(M.hinweisText("blanker Satz") === "blanker Satz",
           "alte Form verschwindet");
    pruefe(M.hinweisSchluessel(h) === "fenster", "Schluessel nicht lesbar");

    M.zustand.sprache = alteSprache;
  }
  if (!fehler) console.log("   OK   vier Sprachen, Werte gesetzt, Rueckfall da");

  console.log("48. Das Kontextmenue bleibt beim Aufklappen, wo es ist");
  // ⚠️ Beim Oeffnen einer Gruppe bleibt das Menue, wo es ist — nichts
  // verschiebt sich. Eine solche Zusage als Kommentar ueber dem Aufruf ist
  // keine Pruefung; hier wird sie nachgemessen. Zwei Ursachen koennen die
  // Verschiebung erzeugen, und beide werden festgehalten.
  {
    const quelle = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");

    // 1. Die BREITE steht fest, sobald das Menue offen ist. Ohne das
    //    springt der inhaltsbestimmte Kasten beim Aufklappen von 259 auf
    //    300 px, weil die Rubrikeintraege laengere Bezeichnungen tragen.
    pruefe(/menu\.style\.width\s*=\s*\(Number\.isFinite\(hoechst\)/
             .test(quelle),
           "die Breite des Tagmenues wird nicht festgenagelt");
    pruefe(/getComputedStyle\(menu\)\.maxWidth/.test(quelle),
           "die Hoechstbreite kommt nicht aus dem CSS — zwei Verwalter");

    // 2. Die LAGE wird beim Neuzeichnen NICHT neu gerechnet. Der vierte
    //    Wert traegt das; ohne ihn rutschte der Kasten am Rand mit der
    //    geaenderten Breite.
    pruefe(/zeichneKontext\(x, y, lage, true\)/.test(quelle),
           "das Neuzeichnen beim Aufklappen haelt die Lage nicht fest");
    pruefe(/if \(lageBehalten && z\.kontextLage\)/.test(quelle),
           "`lageBehalten` wird nicht ausgewertet");

    // 3. Nach dem Festnageln neu messen — sonst raegt der breitere Kasten
    //    rechts aus dem Fenster, weil mit der alten Zahl geklemmt wurde.
    pruefe(/const r2 = menu\.getBoundingClientRect\(\)/.test(quelle),
           "nach dem Festnageln wird nicht neu gemessen");

    // 4. Beide Menues teilen sich DASSELBE Element. Das Feldmenue muss die
    //    festgenagelte Breite zuruecksetzen, sonst erbt es sie.
    const feldTeil = quelle.slice(quelle.indexOf("function zeichneFeldKontext"));
    pruefe(/menu\.style\.width = "";/.test(feldTeil),
           "das Feldmenue erbt die Breite des Tagmenues");
  }
  if (!fehler) console.log("   OK   Breite fest, Lage gehalten, Feldmenue frei");

  console.log("49. Das Feldmenue trifft ein Wort auch ohne Markierung");
  // ⚠️ Ohne Markierung stehen «Ausschneiden» und «Kopieren» grau da — das
  // Menue kaeme, koennte aber nichts. Der Rechtsklick muss die Markierung
  // stehen lassen.
  {
    // Die Wortgrenzen sind EINE Quelle fuer den maskierten Text und die
    // Felder. Zwei Auslegungen von «dasselbe Wort» waeren zwei Verwalter.
    const satz = "Frau Andrea Brülhart, wohnhaft an der Lindenstrasse 12";
    const [a, b] = M.wortgrenzen(satz, satz.indexOf("Brülhart") + 3);
    pruefe(satz.slice(a, b) === "Brülhart",
           "Wortgrenzen treffen nicht: " + satz.slice(a, b));

    // Am Wortanfang und am Wortende dasselbe Wort — ein Rechtsklick trifft
    // selten die Mitte.
    const [a2, b2] = M.wortgrenzen(satz, satz.indexOf("Brülhart"));
    pruefe(satz.slice(a2, b2) === "Brülhart", "Wortanfang trifft nicht");
    const [a3, b3] = M.wortgrenzen(satz, satz.indexOf("Brülhart") + 8);
    pruefe(satz.slice(a3, b3) === "Brülhart", "Wortende trifft nicht");

    // ⚠️ Steht die Marke direkt HINTER einem Wort, ist dieses Wort gemeint
    // — Position 4 in «Frau Andrea …» greift «Frau». Das ist gewollt: ein
    // Rechtsklick landet oft am Wortende.
    const [a4, b4] = M.wortgrenzen(satz, 4);
    pruefe(satz.slice(a4, b4) === "Frau",
           "hinter dem Wort wird es nicht mehr gegriffen: " + satz.slice(a4, b4));

    // Zwischen zwei Trennzeichen gibt es kein Wort — dann darf nichts
    // markiert werden, statt irgendetwas zu greifen.
    const luecke = "Frau  Andrea";
    const [a5, b5] = M.wortgrenzen(luecke, 5);
    pruefe(a5 === b5, "im Leerraum wurde etwas gegriffen: "
                      + luecke.slice(a5, b5));

    const quelle = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(/feld\.setSelectionRange\(a, b\)/.test(quelle),
           "das getroffene Wort wird nicht markiert — keine Rueckmeldung");

    // Die drei Eintraege tragen Sinnbilder, und die sind inline gezeichnet.
    for (const name of ["ausschneiden", "kopieren", "einfuegen"]) {
      pruefe(Array.isArray(M.SINNBILDER[name]) && M.SINNBILDER[name].length,
             "kein Sinnbild fuer " + name);
    }
    // ⚠️ Ueber `createElementNS`, nicht ueber `innerHTML`. Dass die Datei
    // insgesamt kein `innerHTML` verwendet, zaehlt `tests/test_app.py` —
    // hier waere es ein zweiter Verwalter derselben Zusage.
    pruefe(/createElementNS/.test(quelle),
           "die Sinnbilder werden nicht ueber createElementNS gebaut");
  }
  if (!fehler) console.log("   OK   Wortgrenzen einig, Markierung gesetzt, drei Sinnbilder");

  console.log("50. Der Onlinehinweis verschwindet nie ganz");
  // ⚠️ Bei wenig Platz bleibt nur das Dreieck stehen. Der SATZ darf dabei
  // nicht verlorengehen: er steht weiter im Text (`tests/test_app.py`
  // Punkt 16 liest ihn dort) und zusaetzlich im Tooltip. Verborgen, nicht
  // entfernt.
  {
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(/\$\("onlinewarnung"\)\.title = warnsatz;/.test(js),
           "der Satz steht nicht im Tooltip");
    // ⚠️ DERSELBE Satz, kein zweiter Schluessel — sonst gaebe es zwei
    // Fassungen einer Warnung, die auseinanderlaufen koennen.
    pruefe(/const warnsatz = s\.onlineWarnung\.replace/.test(js),
           "Tooltip und Text kommen nicht aus derselben Zeichenkette");

    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const block = css.slice(css.indexOf("@container fuss (max-width: 34rem)"));
    pruefe(block.startsWith("@container fuss (max-width: 34rem)"),
           "kein Umschaltpunkt fuer den Onlinehinweis");
    const ende = block.indexOf("}\n}");
    const regel = block.slice(0, ende);
    pruefe(/#onlinewarnung-text/.test(regel),
           "der Umschaltpunkt trifft nicht den Text");
    // ⚠️ `display: none` waere falsch: der Satz muss im DOM UND fuer
    // Vorlesegeraete erhalten bleiben. Weggeklappt wird er optisch.
    pruefe(!/display:\s*none/.test(regel),
           "der Satz wird entfernt statt verborgen");
    pruefe(/clip-path/.test(regel), "der Satz wird nicht optisch weggeklappt");
  }
  if (!fehler) console.log("   OK   Tooltip aus derselben Quelle, Satz bleibt im Text");

  console.log("51. Die Hoehe misst, was auf dem Handy wirklich da ist");
  // ⚠️ Auf dem Handy muss die Fusszeile erreichbar bleiben. Klebt sie am
  // Fensterrand, verdeckt die Adressleiste des Browsers den unteren
  // Neu-Knopf.
  {
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/height: 100vh; height: 100dvh;/.test(css),
           "body misst nicht in dvh — oder ohne Rueckfall auf vh");
    // ⚠️ Die REIHENFOLGE traegt den Rueckfall: ein Browser ohne `dvh`
    // ueberliest die zweite Zeile und behaelt die erste. Andersherum
    // haette er gar keine Hoehe.
    pruefe(css.indexOf("height: 100vh; height: 100dvh;")
             < css.indexOf("min-height: 62dvh"),
           "Reihenfolge der Rueckfaelle stimmt nicht");
    pruefe(/env\(safe-area-inset-bottom\)/.test(css),
           "der unterste Fuss haelt keinen Abstand zur Gestenleiste");
  }
  if (!fehler) console.log("   OK   dvh mit Rueckfall, Sicherheitsstreifen unten");

  console.log("52. Der Gruppenkopf teilt seinen Klassennamen mit niemandem");
  // ⚠️ Der offene Gruppenkopf steht buendig mit den geschlossenen.
  //
  // Die Falle ist ein Klassennamen-Zusammenstoss: `.offen` gehoert auch der
  // roten Warnbox der nicht zugeordneten Platzhalter, mit einem Rand. Ein
  // Kopf mit `gruppenkopf offen` erbte ihn still. EIN NAME, ZWEI
  // BEDEUTUNGEN: die Regel greift, ohne dass jemand sie an dieser Stelle
  // vermutet.
  {
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/"gruppenkopf" \+ \(offen \? " aufgeklappt" : ""\)/.test(js),
           "der Gruppenkopf traegt wieder `offen`");
    pruefe(/\.kontext \.gruppenkopf\.aufgeklappt/.test(css),
           "das CSS kennt `aufgeklappt` nicht");
    pruefe(!/\.kontext \.gruppenkopf\.offen/.test(ohneKommentare(css)),
           "die alte Regel auf `.offen` steht noch da");
    // ⚠️ `.offen` selbst bleibt — es ist die rote Warnbox und traegt den
    // Rand zu Recht. Geprueft wird nur, dass sie ihn noch hat: faellt er
    // weg, war der Zusammenstoss doch nicht die Erklaerung.
    pruefe(/\.offen \{\s*\n\s*flex: none; margin: 0 1rem/.test(css),
           "die rote Warnbox hat ihren Rand verloren — dann stimmt die "
           + "Erklaerung von 8.6 nicht mehr");
  }
  if (!fehler) console.log("   OK   `aufgeklappt` getrennt von `.offen`");

  console.log("53. Der reservierte Rollbalkenstreifen steht nur, wo er wirkt");
  // ⚠️ Der Streifen fuer den Rollbalken gehoert nur dem Menue, das rollt —
  // nicht allen `.kontext`-Menues. Sonst steht im Feldmenue und bei den
  // Vorlagen eine weisse Flaeche, wo nichts ist.
  {
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(!/^\.kontext \{ overflow-x: hidden; scrollbar-gutter/m
             .test(ohneKommentare(css)),
           "der Streifen gilt wieder fuer BEIDE Menues");
    pruefe(/\.kontext\.tagmenu \{ scrollbar-gutter: stable; \}/.test(css),
           "das Tagmenue hat keinen Streifen — dann springt es beim "
           + "Aufklappen wieder");
    pruefe(/menu\.classList\.add\("tagmenu"\)/.test(js)
             && /menu\.classList\.remove\("tagmenu"\)/.test(js),
           "die Klasse wird nicht gesetzt und wieder weggenommen");
    pruefe(/#vorlagen-liste\.rollend \{ scrollbar-gutter: stable; \}/.test(css),
           "die Vorlagenliste kennt `rollend` nicht");
    pruefe(/liste\.classList\.toggle\("rollend"/.test(js),
           "`rollend` wird nie gesetzt");
  }
  if (!fehler) console.log("   OK   Tagmenue ja, Feldmenue nein, Vorlagen nach Bedarf");

  console.log("54. Der Rollbalken laesst die runden Ecken frei");
  // ⚠️ Ein nativer Rollbalken haelt sich nicht an den `border-radius` des
  // Elements, an dem er haengt — er schneidet in die abgerundeten Ecken.
  {
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/\*::-webkit-scrollbar-track \{ background: transparent; \}/.test(css),
           "die Laufbahn ist nicht durchsichtig");
    pruefe(/\*::-webkit-scrollbar-thumb \{[^}]*border-radius: 999px/.test(css),
           "der Griff ist nicht gerundet");
    pruefe(/scrollbar-color: var\(--color-neutral-400\) transparent/.test(css),
           "Firefox bekommt keine durchsichtige Laufbahn");
    // ⚠️ DIE BREITE BLEIBT. `messeRollbalken()` misst sie und setzt
    // `--rollbalken`; davon haengt der Abstand der Knoepfe in den
    // Textfeldern ab. Ein schmalerer Balken haette diese Messung
    // stillschweigend mitverschoben.
    const cssNackt = ohneKommentare(css);
    pruefe(!/::-webkit-scrollbar \{[^}]*width:/.test(cssNackt),
           "die Balkenbreite wurde angetastet — `--rollbalken` stimmt dann "
           + "nicht mehr");
    pruefe(!/scrollbar-width:\s*thin/.test(cssNackt),
           "`scrollbar-width: thin` aendert die Breite in Firefox");
  }
  if (!fehler) console.log("   OK   Laufbahn durchsichtig, Breite unangetastet");

  console.log("55. Bereich 05 ist ein Feld, und was drin steht, wird kopiert");
  // ⚠️ Alle Textfelder sind bearbeitbar, auch der finalisierte Text.
  {
    const html = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(/<textarea id="final"/.test(html), "Bereich 05 ist kein Textfeld");
    // ⚠️ Der Kasten in 02 kann keines werden — er traegt die Plaketten.
    // Er sagt stattdessen ausdruecklich, dass sein Text markierbar ist.
    pruefe(/<div id="maskiert" tabindex="0">/.test(html),
           "Bereich 02 ist nicht anwaehlbar");
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/#maskiert \{\s*\n\s*user-select: text/.test(css),
           "Bereich 02 sagt nicht, dass er markierbar ist");
    // ⚠️ Kopieren und Herunterladen nehmen den FELDINHALT. Naehmen sie
    // `z.final.text`, verschwaende eine Bearbeitung des Anwenders still.
    pruefe(/function finalText\(\)/.test(js), "`finalText()` fehlt");
    pruefe(/textHerunter\(finalText\(\), "maschera-final"\)/.test(js),
           "Herunterladen nimmt nicht den Feldinhalt");
    pruefe(/inZwischenablage\(finalText\(\), "final-kopieren-text"\)/.test(js),
           "Kopieren nimmt nicht den Feldinhalt");
    // Und der doppelte Knopf IM Feld ist weg.
    pruefe(!/knopf-kopieren-final/.test(ohneKommentare(html + js)),
           "der doppelte Kopieren-Knopf in 05 ist wieder da");
  }
  if (!fehler) console.log("   OK   Textfeld, Feldinhalt zaehlt, kein zweiter Knopf");

  console.log("56. Die Meldungen unter 02 stehen auf einer Zeile");
  {
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(/ruhig\.join\(" · "\)/.test(js),
           "die Meldungen werden nicht zusammengezogen");
    // ⚠️ Warnungen NICHT mitreihen — ein roter Satz zwischen Trennpunkten
    // geht unter. Sie stehen weiter als eigene Absaetze davor.
    pruefe(/el\("p", "hinweis warnhinweis", t\(\)\.verworfenHinweis\)/.test(js),
           "die Warnung hat ihre eigene Zeile verloren");
    // ⚠️ Eintraege sind Objekte, keine Zeichenketten; ein `h.startsWith`
    // wuerfe.
    pruefe(!/h\.startsWith\("OHNE MODELL"\)/.test(ohneKommentare(js)),
           "die Textsuche auf den Satzanfang steht wieder da");
    pruefe(/hinweisSchluessel\(h\) === "ohne_modell"/.test(js),
           "es wird nicht nach dem Schluessel gefragt");
  }
  if (!fehler) console.log("   OK   eine Zeile, Warnungen getrennt, Schluessel statt Satz");

  console.log("57. Das Burgermenue holt seine Adressen aus EINER Datei");
  {
    const js = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const adressen = JSON.parse(fs.readFileSync(
      path.join(WURZEL, "app/static/adressen.json"), "utf8"));
    pruefe(Array.isArray(adressen.eintraege) && adressen.eintraege.length,
           "die Adressdatei ist leer");
    // ⚠️ KEINE Adresse steht zusaetzlich im Code — sonst zwei Verwalter.
    for (const e of adressen.eintraege) {
      if (!e.url) continue;
      pruefe(!ohneKommentare(js).includes(e.url),
             "die Adresse steht auch im Code: " + e.url);
    }
    // ⚠️ Die BESCHRIFTUNGEN stehen NICHT in der Adressdatei, sondern in
    // allen vier Sprachtabellen — sonst stuenden deutsche Eintraege unter
    // italienischer Oberflaeche.
    for (const e of adressen.eintraege) {
      pruefe(!e.name && !e.text,
             "die Adressdatei traegt eine Beschriftung: " + e.schluessel);
      for (const sp of ["de", "fr", "it", "en"]) {
        pruefe(M.I18N[sp] && M.I18N[sp][e.schluessel],
               `${e.schluessel} fehlt in ${sp}`);
      }
    }
    // «Im Browser oeffnen» nur im eigenen Fenster — im Browser waere es
    // ein Knopf, der die Seite noch einmal daneben aufmacht.
    pruefe(/function imEigenenFenster\(\)/.test(js),
           "die Oberflaeche weiss nicht, wo sie laeuft");
    pruefe(/e\.selbst \? imEigenenFenster\(\)/.test(js),
           "der Eintrag `selbst` haengt nicht am eigenen Fenster");

    // ⚠️ JEDER EINTRAG TRAEGT EIN ZEICHEN. Ein leerer Kasten im Menue ist
    // die Sorte Fehler, die niemand meldet und die alle sehen. Geprueft wird
    // die ZUORDNUNG, nicht das Aussehen: wer einen Eintrag ergaenzt, muss
    // sein Zeichen mitentscheiden.
    for (const e of adressen.eintraege) {
      pruefe(e.bild, `${e.schluessel} hat kein Zeichen in adressen.json`);
      pruefe(!e.bild || M.MENUEBILDER[e.bild],
             `${e.schluessel} zeigt auf das Zeichen «${e.bild}», das es `
             + "in MENUEBILDER nicht gibt");
    }
    // ⚠️ Und andersherum: kein Zeichen ohne Eintrag. Ein totes Zeichen
    // sieht nach Gestaltung aus und ist keine.
    const benutzt = new Set(adressen.eintraege.map((e) => e.bild));
    for (const name of Object.keys(M.MENUEBILDER)) {
      pruefe(benutzt.has(name),
             `das Zeichen «${name}» wird von keinem Eintrag benutzt`);
    }
    // ⚠️ DIESELBE FAMILIE. Alle Pfade sind Striche in 24x24 — kein
    // `fill`, keine Wortmarke. Das ist der Unterschied, den der Anwender
    // gemeint hat: «Nimm aber fuer alles die selbe Icon Familie.»
    for (const [name, pfade] of Object.entries(M.MENUEBILDER)) {
      pruefe(Array.isArray(pfade) && pfade.length,
             `das Zeichen «${name}» hat keine Pfade`);
      for (const d of pfade) {
        pruefe(typeof d === "string" && /^[MmLlHhVvCcSsQqTtAaZz0-9 .,-]+$/.test(d),
               `«${name}» traegt etwas anderes als einen Pfad: ${d}`);
      }
    }

    // ⚠️ JEDER EINTRAG FAERBT SICH BEIM UEBERFAHREN. Das Menue baut ZWEI
    // Arten von Eintraegen: `a` fuer alles, was hinausfuehrt, und `button`
    // fuer die Einseiter, die im Fenster aufgehen. Eine Regel nur fuer
    // `a:hover` liesse genau die Eintraege aus, die nicht hinausfuehren.
    //
    // Die Wache haengt an den ARTEN, die der Zeichner erzeugt, nicht an
    // Namen: kommt eine dritte dazu, faellt sie auf.
    const menuTeil = js.slice(js.indexOf("function zeichneBurger"),
                              js.indexOf("function burgerAuf"));
    const CSS_B = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    for (const art of ["a", "button"]) {
      pruefe(new RegExp(`el\\("${art}"`).test(menuTeil),
             `das Burgermenue baut keine <${art}> mehr — die Wache ist alt`);
      pruefe(new RegExp(`\\.burgermenu ${art}[^,{]*:hover`).test(CSS_B),
             `<${art}>-Eintraege im Burgermenue faerben sich beim `
             + "Ueberfahren nicht");
    }
  }
  if (!fehler) console.log("   OK   eine Quelle, vier Sprachen, Browsereintrag bedingt, alle mit Rollover");

  console.log("58. Die rote Spalte spricht rot, ausser bei den Feldknoepfen");
  // ⚠️ Die Spalte, die als einzige nach draussen fuehrt, traegt ihre
  // Beschriftungen in ihrer eigenen, kraeftigen Farbe — grau auf rot ist zu
  // wenig Kontrast.
  {
    const css = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8"));
    // ⚠️ `lastIndexOf`: `.spalte.hinaus {` steht auch weiter oben (der
    // rote Rand der Spalte). Der Farbblock ist der LETZTE.
    const block = css.slice(css.lastIndexOf(".spalte.hinaus {"));
    pruefe(block.length > 0, "der Farbblock der roten Spalte fehlt");

    // ⚠️⚠️ DURCH DIE VARIABLEN HINDURCH. Eine Wache auf Farb-Literalen
    // wird rot, sobald die Farben in die Tokenschicht wandern — und
    // verbietet damit die richtige Aenderung. Deshalb wird aufgeloest. Damit
    // traegt sie auch in den Dunkelmodus: dort stehen andere Werte in
    // denselben Marken, und die Aussage «rot bleibt rot, gruen bleibt gruen»
    // bleibt pruefbar.
    const wurzel = {};
    for (const m of css.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;}]+)/g)) {
      if (!(m[1] in wurzel)) wurzel[m[1]] = m[2].trim();
    }
    const aufloesen = (wert) => {
      let w = String(wert);
      for (let i = 0; i < 6; i++) {
        const n = w.replace(/var\((--[a-z0-9-]+)\)/g,
                            (g, name) => wurzel[name] || g);
        if (n === w) break;
        w = n;
      }
      return w.trim();
    };

    // ⚠️ DER AKTIVE RAHMEN GEHOERT DAZU. Eine feste Farbe in einer Regel,
    // die ueber IDs greift (`#prompt`, `#antwort04`), schlaegt JEDE
    // Spaltenregel — gruen heisst hier «bleibt auf dem Geraet», und
    // ausgerechnet im Kasten, der hinausfuehrt, sagte sie das.
    //
    // Geprueft wird die EIGENSCHAFT und nicht der Ton: die Regel darf keine
    // feste Farbe tragen, und die Spalte muss ihre eigene setzen.
    {
      const regel = css.slice(css.indexOf("#prompt:focus"),
                              css.indexOf("#prompt:focus") + 220);
      pruefe(/border-color:\s*var\(--fokus\)/.test(regel)
             && /box-shadow:[^;]*var\(--fokus\)/.test(regel),
             "der aktive Rahmen traegt wieder eine feste Farbe");
      const spaltenFokus = (block.match(/--fokus:\s*([^;}]+)/) || [])[1];
      pruefe(aufloesen(spaltenFokus) === "#8c2f22",
             "die rote Spalte setzt --fokus nicht auf ihren eigenen Ton, "
             + "sondern auf " + aufloesen(spaltenFokus));
      const wurzelFokus = (css.match(/:root\s*\{\s*--fokus:\s*([^;}]+)/)
                           || [])[1];
      pruefe(aufloesen(wurzelFokus) === "#2f6b46",
             "ohne Spalte fehlt die gruene Vorgabe fuer --fokus");
    }

    // Eine Leiter aus EINEM Ton — jeder Wert ist eine Abstufung von
    // `#8c2f22`. Fuenf Einzelfarben waeren unruhig geworden.
    // ⚠️ `--bx-schrift` traegt nur die Schrift. Flaeche des Sendeknopfs,
    // Schrift der Titel und die kraeftige Kante sind im Hellen derselbe Wert,
    // im Dunkeln laufen sie auseinander: eine helle Schrift taugt nicht als
    // Flaeche.
    // ⚠️ Der Rollover arbeitet mit Kante und Schrift statt mit einer eigenen
    // hellroten Flaeche — die laege kaum vom Spaltengrund entfernt und damit
    // unter der Wahrnehmungsschwelle.
    //
    // Eine Leiter darf Sprossen verlieren. Was NICHT passieren darf, ist eine
    // Sprosse, die niemand benutzt und die trotzdem gepflegt wird.
    for (const marke of ["--bx-schrift", "--bx-flaeche", "--bx-kante-stark",
                         "--bx-matt", "--bx-aus",
                         "--bx-kante", "--bx-kante2"]) {
      pruefe(wurzel[marke], "die Marke " + marke + " fehlt");
      pruefe(!wurzel[marke] || /^#[0-9a-f]{6}$/i.test(aufloesen(wurzel[marke])),
             marke + " ist keine Farbe, sondern " + aufloesen(wurzel[marke]));
    }
    // ⚠️ Und die gruene Leiter daneben, nach derselben Bauart.
    for (const marke of ["--gr-flaeche", "--gr-flaeche2", "--gr-schrift",
                         "--gr-kante", "--gr-tief",
                         "--gr-hell", "--gr-matt", "--gr-aus"]) {
      pruefe(wurzel[marke], "die gruene Marke " + marke + " fehlt");
    }

    // ⚠️ KEINE REGEL FUER `.imfeld`. «Kopieren», «Herunterladen» und
    // «Einfuegen» sehen in allen sechs Bereichen gleich aus; einer, der
    // links grau und rechts rot waere, sagte mit der Farbe etwas Falsches.
    // Ausdruecklicher Entscheid des Anwenders.
    pruefe(!/\.spalte\.hinaus[^{]*\.imfeld/.test(block),
           "die Feldknoepfe werden mitgefaerbt — sie sollen grau bleiben");

    // ⚠️ Deaktiviert wird HELLER, nicht durchsichtiger: `opacity` legt
    // einen Schleier ueber Schrift UND Rahmen und ergibt auf rosa Grund
    // einen schmutzigen Ton.
    pruefe(/:disabled[^{]*\{[^}]*opacity: 1/.test(block),
           "deaktiviert haengt wieder an `opacity`");

    // ⚠️ Der rote Hauptknopf dunkelt beim Ueberfahren nach wie jeder andere
    // Hauptknopf — heller zu werden hiesse, sich als einziger anders zu
    // verhalten. Die Spaltenregel laesst ihn in Ruhe.
    pruefe(!/\.spalte\.hinaus[^{]*\.senden:hover/.test(block),
           "die rote Spalte faerbt den Hauptknopf wieder um");
    for (const [wahl, ton] of [["button.tat.haupt:hover", "#255239"],
                               ["button.tat.senden:hover", "#6b2119"]]) {
      const regel = css.slice(css.indexOf(wahl), css.indexOf(wahl) + 140);
      const hat = (regel.match(/background:\s*([^;}]+)/) || [])[1];
      pruefe(aufloesen(hat) === ton,
             wahl + " dunkelt beim Rollover nicht auf " + ton + " nach, "
             + "sondern auf " + aufloesen(hat));
    }

    // ⚠️ GRUEN IST AUSGENOMMEN. Rot sagt «geht hinaus», Gruen «bleibt
    // lokal»; «Vokabular einpflegen» zeigt als einziger Knopf der roten Spalte
    // nach innen. Ohne `:not(.einpflegen)` gewinnt die rote Regel gegen
    // `button.tat.einpflegen` — mehr Klassen — und der Knopf bekaeme hellroten
    // Rollover und rosa Schrift auf blassgruenem Grund.
    // ⚠️ `button.tat:not(` statt `!z.includes(".senden")`: die hover-Regel
    // nimmt auch den Hauptknopf aus, `.senden` steht also als `:not(.senden)`
    // IN der Zeile — die einfache Suche schloesse genau die Zeile aus, die sie
    // pruefen will.
    for (const teil of ["disabled", "hover"]) {
      const zeile = block.split("\n").find(
        (z) => z.includes("button.tat:not(") && z.includes(teil));
      pruefe(zeile && zeile.includes(":not(.einpflegen)"),
             "die " + teil + "-Regel nimmt den gruenen Knopf nicht aus");
    }
    // Der rote Hauptknopf gehoert ebenfalls heraus, sonst faengt ihn die
    // allgemeine Spaltenregel ab, sobald sein Sonderfall fehlt.
    {
      const zeile = block.split("\n").find(
        (z) => z.includes("button.tat:not(") && z.includes("hover"));
      pruefe(zeile && zeile.includes(":not(.senden)"),
             "die hover-Regel nimmt den roten Hauptknopf nicht aus");
    }
  }
  if (!fehler) console.log("   OK   eine Leiter, Feldknoepfe grau, Hauptknopf lesbar");

  console.log("59. Der Startbildschirm richtet die zwei Zeilen aneinander aus");
  // ⚠️ Der Satz steht unter dem ersten Buchstaben der Wortmarke, nicht
  // mittig zu ihr.
  {
    const fenster = fs.readFileSync(
      path.join(WURZEL, "app/fenster.py"), "utf8");
    pruefe(/\.zeile > div\{text-align:left\}/.test(fenster),
           "die zwei Zeilen im Startbildschirm sind nicht linksbuendig");
    pruefe(/Lokale Maskierung für Schweizer Dokumente/.test(fenster),
           "der Satz im Startbildschirm fehlt");
  }
  if (!fehler) console.log("   OK   Wortmarke und Satz an derselben Kante");

  console.log("60. Jeder deutsche Text im HTML hat einen Setzer im Skript");
  // Jeder sichtbare Text hat einen Schluessel.
  //
  // Die Zaehlung der Schluessel sagt nichts ueber Texte, die GAR KEINEN
  // haben: sie stehen nur im HTML, werden von keiner Zeile angefasst und
  // bleiben in jeder Sprache deutsch. Kein Test schlaegt an, weil keiner
  // nach etwas sucht, das nirgends steht.
  //
  // ⚠️ Die Pruefung ist grob und soll es sein: sie fragt nur, ob die
  // Kennung des Elements irgendwo im Skript als Zeichenkette vorkommt. Das
  // faengt nicht jeden Fall — ein `$("x")`, das etwas anderes tut als
  // beschriften, geht durch. Es faengt den haeufigsten: gar kein Zugriff.
  {
    // Was ohne Setzer dastehen DARF, mit Begruendung je Zeile. Nicht
    // durch Weglassen der Pruefung, sondern durch einen Eintrag hier —
    // dieselbe Regel wie bei `VERBOTEN` in `test_veroeffentlichung.py`.
    const OHNE_SETZER = {
      "MASCHERA": "der Name des Werkzeugs, in jeder Sprache derselbe",
      "MAS": "die Wortmarke, in drei Stuecke zerlegt fuer das fette CH",
      "ERA": "dasselbe Stueck der Wortmarke",
      "Barlow": "der Name der Hausschrift, kein deutsches Wort",
    };

    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const roh = HTML
      .replace(/<!--[\s\S]*?-->/g, "")
      .replace(/<(script|style|svg)\b[\s\S]*?<\/\1>/gi, "");

    // Jedes Element, dessen Text deutsche Buchstaben traegt.
    const offen = [];
    const re = /<(\w+)([^>]*)>([^<>]*[A-Za-zÄÖÜäöü]{3}[^<>]*)</g;
    let m;
    while ((m = re.exec(roh)) !== null) {
      const text = m[3].replace(/\s+/g, " ").trim();
      if (!text || OHNE_SETZER[text]) continue;
      const kennung = /\bid="([^"]+)"/.exec(m[2]);
      const klassen = /\bclass="([^"]+)"/.exec(m[2]);
      let gesetzt = false;
      if (kennung && JS.includes('"' + kennung[1] + '"')) gesetzt = true;
      if (!gesetzt && klassen) {
        for (const k of klassen[1].split(/\s+/)) {
          // ⚠️ NUR die Selektorform `".klasse"`. Der blosse Name als Fund liesse
          // einen Namenszusammenstoss durch: `class="spruch"` im Startbildschirm und
          // die KENNUNG `spruch` in der Kopfzeile sind verschiedene Elemente.
          if (JS.includes('".' + k + '"')) {
            gesetzt = true;
          }
        }
      }
      if (!gesetzt) {
        offen.push((kennung ? "#" + kennung[1] : "?") + " — " +
                   text.slice(0, 40));
      }
    }
    // ⚠️ UND DIE PLATZHALTER. Ein `placeholder` ist ein Attribut und kein
    // Text — eine Wache, die nur Text sieht, liesse das erste Wort, das der
    // Anwender in einem leeren Feld liest, in jeder Sprache deutsch.
    //
    // Der deutsche Wortlaut darf im HTML stehen bleiben — er ist der Stand
    // VOR dem ersten Zeichnen. Verlangt ist nur, dass ihn jemand ersetzt.
    for (const m of roh.matchAll(
        /<(?:textarea|input)([^>]*placeholder="([^"]*)"[^>]*)>/g)) {
      const wort = m[2].trim();
      if (!/[A-Za-zÄÖÜäöü]{3}/.test(wort)) continue;   // «—» und dergleichen
      const kennung = /\bid="([^"]+)"/.exec(m[1]);
      pruefe(kennung && new RegExp(
               `\\$\\("${kennung[1]}"\\)\\.placeholder`).test(JS),
             `Platzhalter ohne Setzer: ${kennung ? "#" + kennung[1] : "?"}`
             + ` — ${wort.slice(0, 40)}`);
    }

    pruefe(offen.length === 0,
           "ohne Setzer: " + offen.join(" | "));
  }
  if (!fehler) console.log("   OK   kein deutscher Text ohne Verwalter, kein Platzhalter ohne Setzer");

  console.log("61. Jedes Schreibfeld hat ein Rechtsklickmenue");
  // ⚠️ Das eigene Rechtsklickmenue gilt fuer JEDES Textfeld — auch in den
  // Einstellungen, im Regeleditor, in der Vokabulartabelle, im
  // Vorlagenfeld und im Feld fuer den Weg zurueck. Eine Liste von Kennungen
  // liesse alles aus, was nicht darin steht. Deshalb prueft dieser Punkt
  // die EIGENSCHAFT und nicht eine laengere Liste: eine Liste faengt wieder
  // an zu altern.
  {
    const quelle = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    pruefe(!/for \(const kennung of \["orig", "prompt"/.test(quelle),
           "das Feldmenue haengt wieder an einer Liste von Kennungen");
    pruefe((document._h["contextmenu"] || []).length > 0,
           "niemand horcht auf den Rechtsklick");

    const feld = (art) => ({
      tagName: art === "AREA" ? "TEXTAREA" : "INPUT",
      type: art === "AREA" ? undefined : art,
      value: "Frau Andrea", selectionStart: 0, selectionEnd: 0,
      disabled: false, readOnly: false, parentNode: null,
      setSelectionRange(a, b) { this.selectionStart = a; this.selectionEnd = b; },
    });

    // Ein Textfeld und ein Schreibkasten werden getroffen …
    for (const art of ["text", "AREA"]) {
      pruefe(M.schreibfeld(feld(art)) !== null,
             "ein Feld der Art " + art + " bekommt kein Menue");
    }
    // … tief verschachtelt ebenso, denn geklickt wird auf das Kind.
    const innen = { tagName: "SPAN", parentNode: feld("text") };
    pruefe(M.schreibfeld(innen) !== null,
           "ein Klick auf ein Kind des Feldes findet das Feld nicht");

    // ⚠️ UND WAS NICHT: ein Kennwort gehoert nicht in die Zwischenablage,
    // ein Haken hat nichts zu markieren, und `#maskiert` traegt sein
    // eigenes, reicheres Menue — zwei auf einem Element waeren zwei
    // Verwalter.
    for (const art of ["password", "checkbox", "file", "radio"]) {
      pruefe(M.schreibfeld(feld(art)) === null,
             "ein Feld der Art " + art + " bekommt faelschlich ein Menue");
    }
    pruefe(M.schreibfeld({ tagName: "DIV", id: "maskiert", parentNode: null })
             === null,
           "der maskierte Text bekommt das falsche Menue");
    const gesperrt = feld("text"); gesperrt.readOnly = true;
    pruefe(M.schreibfeld(gesperrt) === null,
           "ein schreibgeschuetztes Feld bekommt ein Menue, das nichts kann");

    // ⚠️⚠️ UND DIE OBERFLAECHE. `readText()` ist der Seite im Browser
    // gesperrt (Chrome fragt, Firefox gar nicht), das native Einfuegen ist
    // eine Browserhandlung und nicht nachbaubar. Im Browser darf das eigene
    // Menue das native deshalb nicht ersetzen — sonst ersetzt es das EINZIGE
    // Einfuegen, das dort wirkt.
    //
    // Deshalb wird hier BEIDES geprueft: das eigene Fenster und der
    // Browser.
    const rechtsklick = () => {
      const menu = document.getElementById("kontext");
      menu.hidden = true;
      let verhindert = false;
      for (const f of (document._h["contextmenu"] || [])) {
        f({ target: feld("text"), clientX: 30, clientY: 40,
            preventDefault() { verhindert = true; } });
      }
      return { offen: menu.hidden === false, verhindert: verhindert };
    };

    const vorher = window.pywebview;
    window.pywebview = { api: {} };
    let r = rechtsklick();
    pruefe(r.offen, "im eigenen Fenster oeffnet der Rechtsklick kein Menue");
    pruefe(r.verhindert,
           "das Browsermenue wird nicht unterdrueckt — es kaemen zwei");

    window.pywebview = undefined;
    r = rechtsklick();
    pruefe(!r.offen,
           "im Browser kommt unser Menue — und sein «Einfuegen» kann dort "
           + "nicht wirken");
    pruefe(!r.verhindert,
           "im Browser wird das native Menue unterdrueckt — damit ist das "
           + "einzige funktionierende Einfuegen weg");
    window.pywebview = vorher;

    // ⚠️ Und der Fokus. Der Klick auf den Eintrag nimmt ihn mit, und
    // `kontextSchliessen()` versteckt danach sein Element — ohne diese
    // Zeile steht die Einfuegemarke hinterher auf `<body>`.
    pruefe(/feld\.focus\(\);\s*\n\s*feld\.selectionStart/.test(quelle),
           "`feldSetzen` gibt den Fokus nicht ans Feld zurueck");
  }
  if (!fehler) console.log("   OK   Eigenschaft statt Liste, nur im eigenen Fenster");

  console.log("62. Hilfe und Impressum liegen im Paket, nicht im Netz");
  // Hilfe und Impressum werden mitgeliefert und gehen im Fenster auf.
  //
  // ⚠️ Es ist mehr als eine Bequemlichkeit. Ein Werkzeug, das damit wirbt,
  // dass der Text das Geraet nicht verlaesst, darf seine eigene Hilfe nicht
  // von einem fremden Server holen — schon der Abruf verriete einer fremden
  // Stelle, dass und wann jemand MASCHERA benutzt. Dieselbe Begruendung wie
  // bei den Schriften und beim Symbol.
  {
    const adressen = JSON.parse(fs.readFileSync(
      path.join(WURZEL, "app/static/adressen.json"), "utf8"));
    const nach = {};
    for (const e of adressen.eintraege) nach[e.schluessel] = e;

    for (const [schluessel, welche] of [["mHilfe", "hilfe"],
                                        ["mImpressum", "impressum"]]) {
      const e = nach[schluessel];
      pruefe(e, `${schluessel} fehlt in adressen.json`);
      pruefe(e && e.dialog === welche,
             `${schluessel} fuehrt nicht auf den Einseiter «${welche}», `
             + `sondern auf ${JSON.stringify(e && (e.url ?? null))}`);
      pruefe(e && e.url === undefined,
             `${schluessel} traegt noch eine Adresse nach draussen`);
    }

    // Beide Seiten, beide in allen vier Sprachen.
    //
    // ⚠️ «NICHT LEER» GENUEGT NICHT: vier Sprachen, die auf dieselbe deutsche
    // Liste zeigen, bestuenden eine solche Pruefung. Verlangt sind vier
    // verschiedene Fassungen mit gleicher Blockfolge.
    const alsText = (b) => JSON.stringify(b);
    for (const welche of ["hilfe", "impressum"]) {
      pruefe(M.SEITEN[welche], `die Seite «${welche}» fehlt`);
      const sprachen = Object.keys(M.SEITEN[welche] || {});
      pruefe(sprachen.join(",") === "de,fr,it,en",
             `${welche} kennt ${sprachen} statt der vier Bediensprachen`);
      for (const spr of sprachen) {
        pruefe((M.SEITEN[welche][spr] || []).length > 0,
               `${welche}/${spr} ist leer`);
      }
      // Paarweise verschieden — keine Fassung ist die Kopie einer anderen.
      for (const a of sprachen) {
        for (const b of sprachen) {
          if (a >= b) continue;
          pruefe(alsText(M.SEITEN[welche][a]) !== alsText(M.SEITEN[welche][b]),
                 `${welche}: ${a} und ${b} tragen denselben Text`);
        }
      }
      // Gleiche Zahl und gleiche Folge der Blockarten — so faellt eine
      // halb uebersetzte Fassung auf, statt still kuerzer dazustehen.
      const muster = (M.SEITEN[welche].de || []).map(([art]) => art).join(",");
      for (const spr of sprachen) {
        const hat = (M.SEITEN[welche][spr] || []).map(([art]) => art).join(",");
        pruefe(hat === muster,
               `${welche}/${spr} hat die Blockfolge ${hat} statt ${muster}`);
      }
    }

    // ⚠️ Gebaut wird ueber `createElement`, NICHT ueber `innerHTML`. Der
    // Grundsatz kennt keine Ausnahme, und «das ist ja eigener Text» ist
    // der Anfang der naechsten.
    const quelle = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    // ⚠️ Ab `textHinein` — der Helfer fuer die Fettauszeichnung und das
    // Kopfstueck gehoeren mit unter die Wache. Sie sind genau die
    // Stellen, an denen `innerHTML` bequem gewesen waere.
    const teil = quelle.slice(quelle.indexOf("function textHinein"),
                              quelle.indexOf("function seiteSchliessen"));
    pruefe(teil.length > 0, "seiteZeigen() fehlt");
    pruefe(/function seitenKopf/.test(teil) && /function seiteZeigen/.test(teil),
           "Kopfstueck oder Zeichner stehen nicht mehr unter der Wache");
    // ⚠️ OHNE KOMMENTARE. Die Begruendung daneben nennt das Wort — sie sagt
    // ja gerade, warum es hier nicht vorkommt.
    const ohneKommentar = teil.replace(/\/\*[\s\S]*?\*\//g, "")
                              .replace(/^\s*\/\/[^\n]*$/gm, "");
    pruefe(!/innerHTML/.test(ohneKommentar),
           "der Einseiter wird ueber innerHTML gebaut");

    // Und er geht wirklich auf.
    const kasten = document.getElementById("seite");
    const rumpf = document.getElementById("seite-rumpf");
    // Alle Knoten unter einem Element einsammeln, quer durch die Ebenen.
    const alle = (k) => [k, ...(k._kinder || []).flatMap(alle)];

    kasten.hidden = true;
    M.seiteZeigen("hilfe");
    pruefe(kasten.hidden === false, "die Hilfe geht nicht auf");
    pruefe(document.getElementById("seite-titel").textContent,
           "die Hilfe hat keinen Titel");
    pruefe((rumpf._kinder || []).length > 0, "die Hilfe ist leer");

    // ⚠️ DAS KOPFSTUECK, fuer BEIDE Seiten: Maske, Wortmarke und der
    // zweizeilige Untertitel, derselbe wie auf dem Startbildschirm. Geprueft
    // wird der Bau, nicht der Wortlaut.
    for (const welche of ["hilfe", "impressum"]) {
      M.seiteZeigen(welche);
      const knoten = alle(rumpf);
      const kopf = (rumpf._kinder || [])[0];
      pruefe(kopf && kopf.className === "seite-kopf",
             `${welche}: das Kopfstueck steht nicht zuoberst`);
      pruefe(knoten.some((k) => k.id === "_neu_img"),
             `${welche}: keine Maske im Kopfstueck`);
      const marke = knoten.find((k) => k.className === "marke");
      pruefe(marke && text(marke).replace(/\s+/g, "") === "MASCHERA",
             `${welche}: die Wortmarke lautet «${marke && text(marke)}»`);
      const spruch = knoten.find((k) => k.className === "spruch");
      pruefe(spruch && text(spruch).trim().length > 10,
             `${welche}: kein Untertitel im Kopfstueck`);
      pruefe(spruch && (spruch._kinder || []).some((k) => k.id === "_neu_br"),
             `${welche}: der Untertitel steht nicht auf zwei Zeilen`);
    }

    // ⚠️ FETT SIND KNOEPFE UND BEFEHLE. Die Auszeichnung kommt als Stueck
    // `["b", …]` aus den Daten und nicht als Zeichen im Text; hier zaehlt,
    // dass sie unten wirklich ankommt.
    M.seiteZeigen("hilfe");
    const fett = alle(rumpf).filter((k) => k.id === "_neu_b"
                                           && text(k) !== "CH");
    pruefe(fett.length >= 4,
           `nur ${fett.length} fette Stellen in der Hilfe — Knoepfe und `
           + "Befehle sollen hervorstehen");
    for (const f of fett) {
      pruefe(!/[<>*]/.test(text(f)),
             `im fetten Stueck steht Markup: ${text(f)}`);
    }
    // Und der Text drumherum darf dabei nicht verschwinden.
    pruefe(text(rumpf).includes("MASCHERA"),
           "der Fliesstext der Hilfe ist beim Fettsetzen abhanden gekommen");

    M.seiteZeigen("hilfe");
    M.seiteSchliessen();
    pruefe(kasten.hidden === true, "die Seite laesst sich nicht schliessen");

    // ⚠️ Der Schliessknopf sagt «Schliessen» und nicht «Speichern &
    // Schliessen». Ein Einseiter hat nichts zu speichern, und der Knopf
    // haette eine Handlung versprochen, die es nicht gibt.
    pruefe(/seite-zu-text"\)\.textContent = s\.schliessen/.test(quelle),
           "der Schliessknopf des Einseiters verspricht zu speichern");
  }
  if (!fehler) console.log("   OK   zwei Seiten im Paket, vier Sprachen, kein innerHTML");

  console.log("63. Bereich 02 laesst sich von Hand korrigieren");
  // ⚠️ Der maskierte Text in Bereich 02 ist bearbeitbar: falsch markierte
  // Stellen und einzelne Woerter lassen sich von Hand korrigieren.
  //
  // ⚠️ WARUM DAS UEBERHAUPT TRAEGT, und es ist der ganze Punkt: die
  // Rueckwandlung arbeitet ueber die PLATZHALTER im Text und nicht ueber
  // Textstellen (`app/serve.py`, `/api/zurueckwandeln`). Ein frei
  // bearbeiteter Text laesst sich deshalb genauso aufloesen. Und
  // `zeichneMaskiert()` baut die Plaketten ohnehin aus dem TEXT ueber
  // `PH_RE`; die Spannen liefern nur Quelle und Vertrauen und werden ueber
  // den Platzhaltertext zugeordnet.
  //
  // Wuerde eines von beidem je auf Textstellen umgestellt, zerbraeche das
  // Bearbeiten still — der Text saehe richtig aus und die Rueckwandlung
  // traefe daneben. Deshalb hier festgehalten.
  {
    const quelle = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const serve = fs.readFileSync(
      path.join(WURZEL, "app/serve.py"), "utf8");

    // 1. Die Zusage, auf der alles ruht.
    pruefe(/PLACEHOLDER_RE\.finditer\(text\)/.test(serve),
           "die Rueckwandlung sucht die Platzhalter nicht mehr im Text — "
           + "dann traegt das Bearbeiten von Bereich 02 nicht mehr");
    const zeichner = quelle.slice(quelle.indexOf("function zeichneMaskiert"),
                                  quelle.indexOf("function zeichneMaskiert")
                                  + 1800);
    pruefe(/PH_RE\.exec\(text\)/.test(zeichner),
           "zeichneMaskiert() baut die Plaketten nicht mehr aus dem Text");

    // 2. Das Feld gibt es, und es ist ein echtes Schreibfeld.
    const html = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    pruefe(/<textarea id="maskiert-feld"/.test(html),
           "das Schreibfeld in Bereich 02 fehlt");
    // ⚠️ KEIN `contenteditable` auf dem Kasten mit den Plaketten: wer
    // zwischen Elementen tippt, erzeugt Auszeichnung, die niemand
    // einliest.
    // ⚠️ Das ATTRIBUT, nicht das Wort — der Kommentar daneben nennt es
    // ausdruecklich, und eine Wache, die an ihrer eigenen Begruendung
    // anschlaegt, zwingt dazu, die Begruendung zu loeschen.
    pruefe(!/contenteditable\s*=/.test(html),
           "Bereich 02 wird ueber contenteditable bearbeitet");

    // 3. Umschalten: drei Ansichten, die einander ausschliessen.
    const knopf = document.getElementById("knopf-bearbeiten");
    pruefe((knopf._h.click || []).length > 0,
           "der Knopf «Bearbeiten» hat keinen Horcher");

    M.zustand.antwort = {
      maskiert: "Frau [FULLNAME_1] wohnt an der [STREET_1].",
      original: null, spans: [],
      woerterbuch: { "[FULLNAME_1]": "Andrea Brülhart",
                     "[STREET_1]": "Lindenstrasse" },
    };
    M.zustand.zurueck = false;
    M.zustand.bearbeiten = false;

    for (const f of knopf._h.click) f({});
    pruefe(M.zustand.bearbeiten === true, "der Knopf schaltet nicht ein");
    pruefe(document.getElementById("maskiert-feld").value
             === M.zustand.antwort.maskiert,
           "das Schreibfeld bekommt den maskierten Text nicht");
    pruefe(document.getElementById("maskiert").hidden === true
             && document.getElementById("maskiert-feld").hidden === false,
           "beide Ansichten stehen gleichzeitig da");

    // 4. Getippt wird in `z.antwort.maskiert` — daran haengt alles
    //    Weitere: der Zaehler, «Das geht hinaus», die Uebernahme.
    const feld = document.getElementById("maskiert-feld");
    feld.value = "Frau [FULLNAME_1] wohnt woanders.";
    for (const f of (feld._h.input || [])) f({ target: feld });
    pruefe(M.zustand.antwort.maskiert === "Frau [FULLNAME_1] wohnt woanders.",
           "das Getippte kommt nicht im Zustand an: "
           + M.zustand.antwort.maskiert);

    // 5. Ausschalten zeichnet neu — aus dem BEARBEITETEN Text.
    for (const f of knopf._h.click) f({});
    pruefe(M.zustand.bearbeiten === false, "der Knopf schaltet nicht aus");
    const plaketten = (document.getElementById("maskiert")._kinder || [])
      .filter((k) => k && k.className && String(k.className).includes("ph"));
    pruefe(plaketten.length === 1,
           `nach dem Bearbeiten stehen ${plaketten.length} Plaketten statt 1`);

    // 6. ⚠️ EIN ZERSCHLAGENER PLATZHALTER WIRD GEMELDET. Ihn zu LOESCHEN
    //    ist erlaubt — dafuer ist das Bearbeiten da. Aber `[FULLNAM_1]`
    //    mit Tippfehler bleibt im fertigen Text stehen und sieht dort aus
    //    wie eine Maskierung, die gewirkt hat.
    // ⚠️ Geprueft wird `z.vokMeldung` und NICHT ein Element. `meldeVok()`
    // schreibt in den Zustand; ein Blick auf ein Element, das es in der
    // Attrappe gar nicht gibt, waere eine Wache, die immer gruen ist.
    M.zustand.antwort.maskiert = "Frau [FULLNAM_1] wohnt hier.";
    M.zustand.vokMeldung = "";
    M.pruefePlatzhalter();
    pruefe(/FULLNAM_1/.test(M.zustand.vokMeldung || ""),
           "ein zerschlagener Platzhalter wird nicht gemeldet: "
           + JSON.stringify(M.zustand.vokMeldung));

    // Und ein bloss GELOESCHTER meldet nichts — ihn zu entfernen ist
    // erlaubt, dafuer ist das Bearbeiten da.
    M.zustand.antwort.maskiert = "Frau wohnt hier.";
    M.zustand.vokMeldung = "";
    M.pruefePlatzhalter();
    pruefe(!(M.zustand.vokMeldung || "").trim(),
           "das Loeschen einer Maske wird faelschlich gemeldet: "
           + JSON.stringify(M.zustand.vokMeldung));

    M.zustand.antwort = null;
    M.zustand.bearbeiten = false;
  }
  if (!fehler) console.log("   OK   Schreibfeld, Text im Zustand, Plaketten neu, Tippfehler gemeldet");

  console.log("64. Was das Skript versteckt, versteckt auch das CSS");
  // ⚠️ `hidden` ist ein Attribut, und das `[hidden] { display: none }` des
  // Browsers ist eine Regel des BROWSERS — jede Autorenregel mit `display:`
  // schlaegt sie. Ein `.hidden = true` im Skript bewirkt dann NICHTS, und
  // zwar lautlos: kein Fehler, keine Meldung, das Element steht einfach
  // weiter da.
  //
  // ⚠️ Deshalb hier keine Liste von Klassen, sondern der SCHLUSS: nimm
  // jedes Element, dessen `hidden` das Skript setzt, sieh nach, ob eine
  // seiner Regeln `display:` setzt, und verlange dann die Gegenregel. Eine
  // Liste haette den naechsten Fall nicht gekannt.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const JS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const HTML = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");

    const kennungen = new Set();
    for (const m of JS.matchAll(/\$\("([A-Za-z0-9_-]+)"\)\.hidden\s*=/g)) {
      kennungen.add(m[1]);
    }
    for (const m of JS.matchAll(
        /getElementById\("([A-Za-z0-9_-]+)"\)\.hidden\s*=/g)) {
      kennungen.add(m[1]);
    }
    // Die Schleife in `zeichne()` versteckt mehrere auf einmal.
    //
    // ⚠️ NUR WENN IM RUMPF WIRKLICH `.hidden` STEHT. Schleifen derselben Form
    // geben auch Behandler; eine Wache, die aus der FORM auf die WIRKUNG
    // schliesst, findet Dinge, die es nicht gibt.
    for (const m of JS.matchAll(
        /for \(const kennung of \[([^\]]*)\]\)\s*\{([\s\S]{0,400}?)\n  \}/g)) {
      if (!/\.hidden\s*=/.test(m[2])) continue;
      for (const k of m[1].matchAll(/"([A-Za-z0-9_-]+)"/g)) kennungen.add(k[1]);
    }
    pruefe(kennungen.size > 5,
           `nur ${kennungen.size} versteckte Elemente gefunden — die Wache `
           + "sieht das Skript nicht mehr");

    // Regeln ohne Kommentare, als Paare Selektor/Erklaerungen.
    const regeln = [];
    for (const m of CSS.replace(/\/\*[\s\S]*?\*\//g, "")
                       .matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      regeln.push([m[1].trim(), m[2]]);
    }
    const alsWort = (sel) => new RegExp(
      "(^|[\\s,>])" + sel.replace(/[.[\]]/g, "\\$&") + "($|[\\s,:{])");
    const setztDisplay = (sel) => regeln.some(
      ([s, d]) => alsWort(sel).test(s) && /display:\s*(?!none)/.test(d));
    const hatGegenregel = (sel) => regeln.some(
      ([s, d]) => s.includes(sel + "[hidden]") && /display:\s*none/.test(d));

    for (const id of [...kennungen].sort()) {
      const treffer = HTML.match(
        new RegExp("<[^>]*id=\"" + id + "\"[^>]*>"));
      if (!treffer) continue;          // aus dem Skript gebaut, kein Fall
      const klassen = (treffer[0].match(/class="([^"]*)"/) || ["", ""])[1]
        .trim().split(/\s+/).filter(Boolean);
      const kandidaten = ["#" + id, ...klassen.map((k) => "." + k)];
      const brennt = kandidaten.filter(setztDisplay);
      if (!brennt.length) continue;
      pruefe(kandidaten.some(hatGegenregel),
             `«${id}» wird im Skript versteckt, aber ${brennt.join(" ")} `
             + "setzt `display:` — das Attribut `hidden` verliert dagegen, "
             + "und das Element bleibt stehen");
    }
  }
  if (!fehler) console.log("   OK   jede display-Regel hat ihre hidden-Gegenregel");

  console.log("65. Der Sprung landet, wo der Kasten steht");
  // ⚠️ Gestapelt springt die Seite zum naechsten Schritt — und zwar genau
  // dorthin, nicht darueber hinaus.
  //
  // `springeZu()` darf den Kasten des Rollbehaelters nur bei einem ROLLENDEN
  // ELEMENT (`#raster`) abziehen. Fuer die ROLLWURZEL ist
  // `getBoundingClientRect().top` gleich `-scrollTop`, und die Subtraktion
  // addierte den Rollstand ein zweites Mal: bei `scrollTop` 500 rechnete die
  // Zeile 1000.
  //
  // ⚠️ Der ERSTE Sprung steht bei `scrollTop` 0, und dort ist der Fehler
  // ebenfalls 0. Erst der zweite landet doppelt so tief — deshalb prueft
  // dieser Punkt einen zweiten Sprung. Und er prueft, WOHIN gesprungen
  // wird, nicht nur, DASS.
  {
    const seite = document.scrollingElement;
    const ziel = document.getElementById("b03");
    const kopf = document.getElementById("kopfzeile");
    const vorherBreite = window._breite;
    window._breite = 375;             // gestapelt: die SEITE rollt
    // ⚠️ ZUERST OHNE KOPFZEILE, damit die reine Rechnung fuer sich steht.
    window._kopfPosition = "static";
    kopf._hoehe = 90;

    // Schon gerollt, Ziel genau an der Oberkante: es darf sich NICHTS tun.
    seite.scrollTop = 800;
    ziel._top = 0;
    M.springeZu("b03");
    pruefe(seite.scrollTop === 800,
           `der Sprung verdoppelt den Rollstand: ${seite.scrollTop} statt 800`);

    // Ziel 300 px unter der Oberkante: genau 300 weiter, nicht 1100 mehr.
    seite.scrollTop = 800;
    ziel._top = 300;
    M.springeZu("b03");
    pruefe(seite.scrollTop === 1100,
           `der Sprung landet auf ${seite.scrollTop} statt auf 1100`);

    // Und aufwaerts, mit negativem Abstand.
    seite.scrollTop = 800;
    ziel._top = -500;
    M.springeZu("b03");
    pruefe(seite.scrollTop === 300,
           `der Sprung nach oben landet auf ${seite.scrollTop} statt auf 300`);

    // ⚠️ UND MIT KLEBENDER KOPFZEILE. Die Kopfzeile ist gestapelt `sticky`
    // und liegt ueber dem oberen Rand. Ein Sprung auf Viewport-Null legte den
    // Kastentitel genau darunter.
    window._kopfPosition = "sticky";
    seite.scrollTop = 800;
    ziel._top = 300;
    M.springeZu("b03");
    pruefe(seite.scrollTop === 1010,
           `mit klebender Kopfzeile landet der Sprung auf `
           + `${seite.scrollTop} statt auf 1010 (1100 minus 90 Kopfzeile)`);

    // ⚠️ Nebeneinander steht die Kopfzeile im Fluss und verdeckt nichts —
    // dort waere ein Abzug ein Sprung, der zu kurz greift.
    window._kopfPosition = "static";
    seite.scrollTop = 800;
    ziel._top = 300;
    M.springeZu("b03");
    pruefe(seite.scrollTop === 1100,
           `ohne klebende Kopfzeile wird trotzdem abgezogen: `
           + seite.scrollTop);
    kopf._hoehe = 0;
    window._kopfPosition = "sticky";

    ziel._top = 0;
    seite.scrollTop = 0;
    window._breite = vorherBreite;

    // ⚠️ UND DER ANDERE FALL BLEIBT STEHEN, obwohl er heute nicht laufen
    // KANN: `springeZu()` kehrt sofort um, wenn die Kaesten nebeneinander
    // stehen, und gestapelt liefert `rollBehaelter()` immer die Rollwurzel.
    // Der Zweig fuer ein rollendes ELEMENT ist damit eine Wache fuer den Tag,
    // an dem jemand die fruehe Umkehr entfernt — dann waere `#raster` wieder
    // der Behaelter, und ohne die Unterscheidung liefe es still schief.
    //
    // Deshalb hier eine Quelltextwache und keine Nachbildung: eine Pruefung,
    // die einen unerreichbaren Zweig nachbaut, prueft ihre eigene
    // Nachbildung.
    const JSq = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const teil65 = JSq.slice(JSq.indexOf("function springeZu"),
                             JSq.indexOf("function vokabularKlappe"));
    pruefe(/scrollingElement \|\| document\.documentElement/.test(teil65),
           "springeZu() unterscheidet die Rollwurzel nicht mehr");
    pruefe(/rollen === wurzel \? 0/.test(teil65),
           "die Rollwurzel wird wieder wie ein rollendes Element gerechnet");

    // ⚠️ NACH DEM MASKIEREN WIRD NICHT MEHR GESPRUNGEN. «Sollte dort
    // stehen bleiben, da ich noch vielleicht etwas anpassen will.» Der
    // Sprung VOR dem Lauf setzt den Kasten schon an seinen Platz; der
    // zweite danach nahm dem Anwender die Stelle weg, an der er war.
    const JS65 = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8");
    const rumpf = JS65.slice(JS65.indexOf("async function laufen()"),
                             JS65.indexOf("async function ablegen("));
    pruefe(rumpf.length > 0, "laufen() nicht gefunden");
    const ohneK65 = rumpf.replace(/\/\*[\s\S]*?\*\//g, "")
                         .replace(/^\s*\/\/.*$/gm, "");
    const spruenge = (ohneK65.match(/springeZu\(/g) || []).length;
    pruefe(spruenge === 1,
           `laufen() springt ${spruenge}-mal statt genau einmal — der `
           + "Sprung gehoert VOR den Lauf, nicht dahinter");
  }
  if (!fehler) console.log("   OK   Rollwurzel und Element getrennt, ein Sprung je Lauf");

  console.log("66. Der Speichern-Knopf kuerzt in zwei Stufen");
  // ⚠️ Drei Stufen: voll, Zeichen und «Speichern», nur Zeichen. Ohne das
  // zweite Textstueck gaebe es keine mittlere Stufe — der Knopf spraenge von
  // voll auf Zeichen.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const HTML66 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const knopf = /<button[^>]*id="knopf-einst-zu"[\s\S]*?<\/button>/
      .exec(HTML66);
    pruefe(knopf !== null, "der Speichern-Knopf fehlt");
    if (knopf) {
      pruefe(/<svg/.test(knopf[0]), "der Speichern-Knopf hat kein Zeichen");
      const spannen = (knopf[0].match(/<span/g) || []).length;
      pruefe(spannen === 2,
             `der Speichern-Knopf traegt ${spannen} Textstueck(e) statt `
             + "zwei — dann gibt es keine mittlere Stufe");
    }
    pruefe(/\.einst-kopf\s*\{[^}]*container-type:\s*inline-size/.test(CSS),
           "der Dialogkopf ist kein Behaelter — die Stufen greifen nicht");
    const stufen = [...CSS.matchAll(
      /@container einstkopf \(max-width:\s*([\d.]+)rem\)/g)].map(
      (m) => Number(m[1]));
    pruefe(stufen.length === 2,
           `${stufen.length} Stufe(n) statt zwei`);
    pruefe(stufen.length === 2 && stufen[0] > stufen[1],
           `die Stufen stehen in der falschen Reihenfolge: ${stufen}`);
    // ⚠️ Und in `rem`, nicht in `px` — Punkt 28 verlangt es fuer alles,
    // was an `--skala` haengen soll.
    pruefe(!/@container einstkopf \(max-width:\s*\d+px/.test(CSS),
           "eine Stufe steht in Pixeln statt in rem");
  }
  if (!fehler) console.log("   OK   Zeichen, zwei Textstuecke, zwei Stufen");

  console.log("67. Die Fusszeile bricht zwischen den Aussagen, nicht in ihnen");
  // ⚠️ Die Fusszeile bricht nicht mitten in einer Aussage um, und die
  // Aussage selbst stimmt: es gibt keinen Upload, den ein Klick ausloest.
  // `/api/senden` existiert nicht und wird es nicht geben.
  {
    const CSS = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    for (const spr of ["de", "fr", "it", "en"]) {
      const satz = M.I18N[spr].fussLinks;
      pruefe(!/upload|envoi|invio/i.test(satz),
             `${spr}: die Fusszeile spricht noch von einem Upload — ${satz}`);
      pruefe(satz.split(" · ").length === 3,
             `${spr}: die Fusszeile hat ${satz.split(" · ").length} Stuecke `
             + "statt drei");
    }
    // ⚠️ IM DEUTSCHEN HEISST ES «KI», nicht «AI» — wie im uebrigen deutschen
    // Text und in der Hilfe. Franzoesisch und Italienisch sagen «IA»,
    // Englisch «AI».
    pruefe(!/\bAI\b/.test(M.I18N.de.fussLinks),
           `die deutsche Fusszeile sagt «AI» statt «KI»: `
           + M.I18N.de.fussLinks);
    pruefe(/KI/.test(M.I18N.de.fussLinks),
           "die deutsche Fusszeile nennt die Dienste gar nicht mehr");
    // Und die Zerlegung kommt wirklich an.
    M.zeichneBeschriftung();
    const kinder = document.getElementById("fuss-links")._kinder || [];
    pruefe(kinder.length === 3,
           `die Fusszeile steht in ${kinder.length} Knoten statt in drei — `
           + "dann bricht sie wieder irgendwo");
    pruefe(kinder.every((k) => k.className === "fuss-teil"),
           "die Stuecke tragen ihre Klasse nicht");
    pruefe(/\.fuss-teil\s*\{[^}]*display:\s*inline-block/.test(CSS),
           "die Stuecke halten nicht zusammen");
    // ⚠️ Und die Fassungsnummer bricht nicht am Bindestrich.
    pruefe(/#version\s*\{[^}]*white-space:\s*nowrap/.test(CSS),
           "die Fassungsnummer bricht wieder in «v0.9.5-» und «beta»");
  }
  if (!fehler) console.log("   OK   drei Stuecke, kein Upload mehr, Fassung ungebrochen");

  console.log("68. Markdown-entwertete Platzhalter werden zurueckgeholt");
  // ⚠️ Manche Dienste geben beim Kopieren Markdown-Quelltext heraus —
  // `\[FULLNAME\_2\]`. `PH_RE` erkennt das nicht als Platzhalter; ohne
  // Rueckbau blieben `nicht_gefunden` leer und `ersetzt` auf 0, die
  // Oberflaeche meldete NICHTS, und im fertigen Text stuende jede Maskierung
  // noch da. «Ein leerer Befund ist keine Entwarnung.»
  {
    const a = M.markdownZurueck("Gruss \\[FULLNAME\\_2\\] von \\[ORG\\_1]");
    pruefe(a.text === "Gruss [FULLNAME_2] von [ORG_1]",
           `entwertet zurueckgeholt: ${a.text}`);
    pruefe(a.anzahl === 2, `${a.anzahl} statt 2 gemeldet`);

    // ⚠️ DIE GEGENPROBE ZUR NAHELIEGENDEN LOESUNG. Ein globales
    // `\\(.)` -> `$1` haette dasselbe Beispiel bestanden und dabei jeden
    // Pfad und jedes LaTeX in der Antwort zerstoert.
    const b = M.markdownZurueck("C:\\Users\\test und \\alpha + \\beta");
    pruefe(b.text === "C:\\Users\\test und \\alpha + \\beta",
           `ein Rueckstrich ausserhalb eines Platzhalters wurde `
           + `angefasst: ${b.text}`);
    pruefe(b.anzahl === 0, "es wurde etwas gemeldet, wo nichts war");

    // Ein gueltiger Platzhalter bleibt, wie er ist.
    const c = M.markdownZurueck("Frau [FULLNAME_1] wohnt hier.");
    pruefe(c.text === "Frau [FULLNAME_1] wohnt hier." && c.anzahl === 0,
           "ein heiler Platzhalter wurde angefasst");

    // ⚠️ WAS NICHT REPARIERT WIRD, WIRD GEMELDET. Eine fehlende Klammer
    // laesst sich nicht erraten — `NAME_2]` koennte gewoehnlicher Text
    // sein, und wer das erriete, schriebe einen echten Wert in einen
    // Brief, den niemand geprueft hat.
    pruefe(M.entwerteteReste("Frau [FULLNAME_1] wohnt hier.").length === 0,
           "ein heiler Text wird als kaputt gemeldet");
    const reste = M.entwerteteReste("Gruss \\[ORG\\_1] und [FULLNAME_1]");
    pruefe(reste.length === 1 && /ORG/.test(reste[0]),
           `entwertete Reste nicht erkannt: ${JSON.stringify(reste)}`);

    // Und der Weg beim Einfuegen meldet beides.
    M.zustand.vokMeldung = "";
    M.antwortUebernehmen("Gruss \\[FULLNAME\\_2\\]");
    pruefe(document.getElementById("antwort04").value
             === "Gruss [FULLNAME_2]",
           "das Feld traegt den reparierten Text nicht");
    pruefe(/1/.test(M.zustand.vokMeldung || ""),
           "die Reparatur wird nicht gemeldet: "
           + JSON.stringify(M.zustand.vokMeldung));
    // ⚠️ ZERSCHLAGENE PLATZHALTER. Eine Antwort kann auf
    // `GIVENNAME_2]\[FULLNAME_2]GIVENNAME\_2]` enden: der Haelfte fehlt die
    // OEFFNENDE Klammer, und `markdownZurueck()` fasst das zu Recht nicht an.
    //
    // ⚠️ DAS WOERTERBUCH IST DER BEWEIS. Ergaenzt wird nur, was in diesem Lauf
    // wirklich vergeben wurde; alles andere bleibt stehen.
    const wb68 = { "[GIVENNAME_2]": "Andrea", "[FULLNAME_2]": "Brülhart" };
    const d = M.zerschlageneErgaenzen("Gruss\nGIVENNAME_2] [FULLNAME_2]", wb68);
    pruefe(d.text === "Gruss\n[GIVENNAME_2] [FULLNAME_2]",
           `zerschlagener Platzhalter nicht ergaenzt: ${d.text}`);
    pruefe(d.ergaenzt.length === 1 && d.ergaenzt[0] === "[GIVENNAME_2]",
           `gemeldet wurde ${JSON.stringify(d.ergaenzt)}`);

    // ⚠️ WAS DAS WOERTERBUCH NICHT KENNT, BLEIBT STEHEN. Ein Wert, den
    // niemand vergeben hat, wird nicht eingesetzt — auch nicht mit guter
    // Absicht. Das ist derselbe Entscheid, den `app/serve.py` fuer die
    // Gross-/Kleinschreibung schon getroffen hat.
    const e68 = M.zerschlageneErgaenzen("Gruss ORG_9] und PLZ_3]", wb68);
    pruefe(e68.text === "Gruss ORG_9] und PLZ_3]",
           `ein unbekannter Platzhalter wurde erfunden: ${e68.text}`);
    pruefe(e68.ergaenzt.length === 0, "es wurde etwas gemeldet, wo nichts war");

    // Und der ganze Weg, mit dem echten Text aus dem Bericht.
    M.zustand.antwort = { maskiert: "", woerterbuch: wb68 };
    M.zustand.vokMeldung = "";
    M.antwortUebernehmen(
      "Freundliche Gruesse\n\nGIVENNAME_2]\\[FULLNAME_2]");
    const raus = document.getElementById("antwort04").value;
    // ⚠️ Ohne Regex: `[^[]` im Muster hat Nodes Parser hier den Rest der
    // Datei verhagelt. Zwei Zeichenkettenfragen sagen dasselbe und
    // lassen sich beim Lesen nachvollziehen.
    pruefe(raus.includes("[GIVENNAME_2]")
             && !raus.includes("\n\nGIVENNAME_2]"),
           `der Bericht aus dem Gebrauch wird nicht aufgefangen: ${raus}`);
    pruefe(raus.includes("[FULLNAME_2]") && !raus.includes("\\["),
           `es steht noch eine Entwertung im Text: ${raus}`);
    M.zustand.antwort = null;
  }
  if (!fehler) console.log("   OK   entwertet zurueckgeholt, zerschlagene ergaenzt, Unbekanntes stehen gelassen");

  console.log("71. Die Obergrenze steht im Server, nicht in der Hilfe");
  // Die Hilfe nennt die maximale Dateigroesse.
  //
  // Die Zahl auszuschreiben ergaebe VIER Verwalter — je Sprache einen — fuer
  // etwas, das als `MAX_UPLOAD` in `app/serve.py` steht. Geprueft wird die
  // EIGENSCHAFT: die Hilfe traegt eine Luecke, der Server fuellt sie.
  {
    const roh = fs.readFileSync(
      path.join(WURZEL, "app/static/seiten.js"), "utf8");
    const serve = fs.readFileSync(
      path.join(WURZEL, "app/serve.py"), "utf8");

    const m = serve.match(/MAX_UPLOAD = (\d+) \* 1024 \* 1024/);
    pruefe(m, "MAX_UPLOAD steht nicht mehr in app/serve.py");
    const mb = m ? Number(m[1]) : 0;
    pruefe(/"max_mb": MAX_UPLOAD \/\/ \(1024 \* 1024\)/.test(serve),
           "/api/zustand nennt die Obergrenze nicht — die Hilfe kann sie "
           + "dann nur erfinden");

    // Jede Sprache traegt die Luecke, keine die Zahl.
    for (const [sp, liste] of Object.entries(M.SEITEN.hilfe)) {
      const text = JSON.stringify(liste);
      pruefe(text.includes("{mb}"),
             `die Hilfe auf ${sp} nennt die Obergrenze nicht`);
      pruefe(!new RegExp("\\b" + mb + "\\s*(MB|Mo)", "i").test(text),
             `die Hilfe auf ${sp} schreibt die Zahl aus — zweiter Verwalter`);
    }
    pruefe(!/\b\d+\s*(MB|Mo)\b/i.test(roh),
           "seiten.js traegt eine ausgeschriebene Groesse");

    // ⚠️ Und die Luecke wird auch WIRKLICH gefuellt. Eine Vorlage, die
    // niemand ersetzt, zeigt dem Anwender «{mb} MB» — schlimmer als gar
    // keine Angabe, weil sie nach einem Fehler aussieht.
    const vorher = M.zustand.zustand;
    M.zustand.zustand = { max_mb: mb };
    M.seiteZeigen("hilfe");
    const gezeigt = text(document.getElementById("seite-rumpf"));
    pruefe(gezeigt.includes(String(mb)),
           "die Obergrenze erscheint nicht in der gezeigten Hilfe");
    pruefe(!gezeigt.includes("{mb}"),
           "die Luecke `{mb}` steht ungefuellt in der Hilfe");

    // ⚠️ Und ohne Antwort KEINE erfundene Zahl. Lieber die sichtbare
    // Luecke als eine falsche Zusage.
    M.zustand.zustand = null;
    M.seiteZeigen("hilfe");
    pruefe(text(document.getElementById("seite-rumpf")).includes("{mb}"),
           "ohne Serverantwort erscheint eine Zahl, die niemand kennt");
    M.zustand.zustand = vorher;
    M.seiteSchliessen();
  }
  if (!fehler) console.log("   OK   eine Zahl, vier Sprachen, ein Verwalter");

  console.log("72. Keine Farbe steht unterhalb der Tokenschicht");
  // ⚠️⚠️ UNTERHALB DER TOKENSCHICHT STEHT KEINE FARBE.
  //
  // Jede Farbe hat einen Namen in `:root` und wird ueberall ueber ihn
  // gelesen. Derselbe Wert zweimal ausgeschrieben waere ZWEI VERWALTER fuer
  // eine Farbe, und der Dunkelmodus muesste jede Stelle einzeln finden.
  //
  // ⚠️ `#fff` kann ZWEIERLEI meinen — die Papierflaeche eines Feldes oder
  // die Schrift auf farbigem Grund. Im Dunkelmodus laufen die auseinander;
  // deshalb zwei Marken.
  //
  // ⚠️ Geprueft wird die EIGENSCHAFT, nicht eine Liste erlaubter Farben:
  // eine Liste waere beim naechsten Knopf wieder unvollstaendig.
  {
    const roh = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    const trenner = ":root { --fokus:";
    pruefe(roh.includes(trenner), "die Tokenschicht ist nicht mehr zu finden");
    const rumpf = ohneKommentare(roh.slice(roh.indexOf(trenner)));

    // ⚠️ `#b01` bis `#b05` sind KENNUNGEN, keine Farben — sie stehen in den
    // Umbruchregeln. Deshalb nur sechsstellige Werte und `#fff`.
    // ⚠️⚠️ AUCH `rgb()`, `rgba()` UND `hsl()`. `rgba(140, 47, 34, .55)` ist
    // dasselbe Rot wie `#8c2f22` — eine Wache, die nur `#hex` sucht, laesst
    // die naechste Schreibweise durch, und im Dunkelmodus bliebe die Farbe
    // hell.
    const sünder = [
      ...rumpf.matchAll(/#[0-9a-fA-F]{6}\b|#fff\b/g),
      ...rumpf.matchAll(/\b(?:rgba?|hsla?)\(\s*[\d.]/g),
    ].map((m) => m[0]);
    pruefe(sünder.length === 0,
           `${sünder.length} Farbliteral(e) unterhalb der Tokenschicht: `
           + [...new Set(sünder)].slice(0, 5).join(" "));

    // ⚠️ Und andersherum: keine tote Marke. Eine Farbe, die niemand
    // benutzt, sieht nach Gestaltung aus und ist keine — dieselbe
    // Begruendung wie bei den Menuezeichen in Punkt 57.
    const kopf = roh.slice(0, roh.indexOf(trenner));
    const erklaert = [...ohneKommentare(kopf)
      .matchAll(/(--(?:gr|bx)[a-z0-9-]*|--papier|--auf-farbe)\s*:/g)]
      .map((m) => m[1]);
    pruefe(erklaert.length >= 30,
           `nur ${erklaert.length} Marken in der Tokenschicht, 30+ erwartet`);
    const tot = erklaert.filter(
      (n) => !new RegExp("var\\(" + n + "\\)").test(roh));
    pruefe(tot.length === 0, "tote Marke(n): " + tot.join(" "));

    // ⚠️ Die zwei Bedeutungen von `#fff` bleiben getrennt. Sie tragen
    // heute denselben Wert; wer sie zusammenzieht, weil «das ist doch
    // dasselbe», nimmt dem Dunkelmodus seine Grundlage.
    pruefe(/--papier:\s*#/.test(kopf) && /--auf-farbe:\s*#/.test(kopf),
           "Papierflaeche und Schrift-auf-Farbe sind wieder eine Marke");
    pruefe(!/background(?:-color)?:\s*var\(--auf-farbe\)/.test(rumpf),
           "`--auf-farbe` wird als Flaeche benutzt — das ist die Schrift");
    pruefe(!/[^-]color:\s*var\(--papier\)/.test(rumpf),
           "`--papier` wird als Schrift benutzt — das ist die Flaeche");
    // ⚠️⚠️ UND DAS JAVASCRIPT. Dort standen 76 Literale: die 72 Werte der
    // 24 Platzhalterpaletten (`GROUP_PALETTE`, `TYPE_COLORS`,
    // `TYPE_FALLBACK`) und vier in `SRC_STYLE`.
    //
    // Die TABELLEN bleiben im Skript — sie entscheiden, WELCHE Palette
    // ein Tag bekommt, und das ist Logik. Nur die Farbe selbst ist
    // umgezogen. Ohne diese Trennung braeuchte der Dunkelmodus einen
    // zweiten Tabellensatz in JavaScript.
    //
    // ⚠️ Und die STRICHART bleibt auch dort: ausgezogen, doppelt,
    // gestrichelt, gepunktet sagen «vom Modell», «von Hand»,
    // «Pruefsumme», «Regel» — eine Form, keine Farbe, und im Dunkeln
    // unveraendert richtig.
    {
      const jsRoh = ohneKommentare(fs.readFileSync(
        path.join(WURZEL, "app/static/maschera.js"), "utf8"));
      const jsSünder = [
        ...jsRoh.matchAll(/#[0-9a-fA-F]{6}\b/g),
        ...jsRoh.matchAll(/\b(?:rgba?|hsla?)\(\s*[\d.]/g),
      ].map((m) => m[0]);
      pruefe(jsSünder.length === 0,
             `${jsSünder.length} Farbliteral(e) in maschera.js: `
             + [...new Set(jsSünder)].slice(0, 5).join(" "));
      // Die Zuordnung ist geblieben — sonst waere die Trennung eine
      // Verschiebung und keine.
      for (const tabelle of ["GROUP_PALETTE", "TYPE_COLORS", "TYPE_FALLBACK"]) {
        pruefe(new RegExp("const " + tabelle + " =").test(jsRoh),
               tabelle + " ist verschwunden — die Zuordnung gehoert ins Skript");
      }
      pruefe(/double/.test(M.SRC_STYLE.manuell)
             && /var\(--/.test(M.SRC_STYLE.manuell),
             "SRC_STYLE traegt die Farbe wieder selbst oder hat die Form verloren");
      // ⚠️ Jede Marke, auf die das Skript zeigt, muss es im Blatt geben.
      // Ein `var(--gibts-nicht)` faellt nicht auf: der Browser laesst die
      // Eigenschaft dann einfach weg, und der Platzhalter steht farblos
      // da — genau die Sorte Fehler, die niemand meldet und alle sehen.
      // ⚠️ Der Unterstrich gehoert dazu — `--ph-tag-case_id-fl`. Ohne ihn
      // meldete diese Wache drei Marken als fehlend, die es gibt.
      const imBlatt = new Set(
        [...roh.matchAll(/(--[a-z0-9_-]+)\s*:/g)].map((m) => m[1]));
      const gezeigt = [...jsRoh.matchAll(/var\((--ph-[a-z0-9_-]+|--gr-[a-z0-9-]+|--manuell|--muster)\)/g)]
        .map((m) => m[1]);
      pruefe(gezeigt.length >= 72,
             `nur ${gezeigt.length} Farbverweise im Skript, 72+ erwartet`);
      const fehlend = [...new Set(gezeigt)].filter((n) => !imBlatt.has(n));
      pruefe(fehlend.length === 0,
             "das Skript zeigt auf Marken, die es im Blatt nicht gibt: "
             + fehlend.slice(0, 5).join(" "));
    }
  }
  if (!fehler) console.log("   OK   keine Farbe in Blatt und Skript, keine tote Marke");

  console.log("73. Der Dunkelmodus kennt jede Marke, die es hell gibt");
  // ⚠️⚠️ DIE FALLE, DIE JEDER DUNKELMODUS STELLT: eine Marke wird beim
  // Umfaerben vergessen. Sie behaelt dann ihren hellen Wert — und das
  // ist nicht «etwas blass», sondern eine weisse Flaeche in einem
  // dunklen Fenster oder schwarze Schrift auf dunklem Grund. Fuer den,
  // der es baut, ist es eine Zeile; fuer den, der es sieht, ein Fehler.
  //
  // Geprueft wird die EIGENSCHAFT: jede Marke der hellen Wurzel hat im
  // Dunkeln eine Entsprechung, und die zwei Einhaengepunkte tragen
  // dieselbe Liste. Keine Aufzaehlung erlaubter Ausnahmen — die waere
  // beim naechsten Knopf wieder unvollstaendig.
  {
    const roh = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");

    const holBlock = (start) => {
      const i = roh.indexOf(start);
      if (i < 0) return "";
      const auf = roh.indexOf("{", i + start.length - 1);
      let tiefe = 0, j = auf;
      for (; j < roh.length; j++) {
        if (roh[j] === "{") tiefe++;
        else if (roh[j] === "}" && --tiefe === 0) break;
      }
      return roh.slice(auf, j);
    };
    const marken = (t) => new Set(
      [...t.matchAll(/(--[a-z0-9_-]+)\s*:/g)].map((m) => m[1]));

    const system = holBlock(':root:not([data-thema="hell"])');
    const gewaehlt = holBlock(':root[data-thema="dunkel"]');
    pruefe(system.length > 0, "der Systemzweig des Dunkelmodus fehlt");
    pruefe(gewaehlt.length > 0, "die ausdrueckliche Wahl «dunkel» fehlt");

    // ⚠️ `:root:not([data-thema="hell"])` und nicht blosses `:root`:
    // sonst schlaegt die Medienabfrage die ausdrueckliche Wahl «hell»,
    // weil sie weiter unten steht. Dann kann man hell nicht mehr
    // erzwingen, und die Einstellung waere angezeigt statt gespeichert.
    const medien = roh.slice(roh.indexOf("@media (prefers-color-scheme: dark)"),
                             roh.indexOf("@media (prefers-color-scheme: dark)") + 120);
    pruefe(/:root:not\(\[data-thema="hell"\]\)/.test(medien),
           "der Systemzweig laesst sich von der ausdruecklichen Wahl «hell» "
           + "nicht ueberstimmen");

    const a = marken(system), b = marken(gewaehlt);
    const nurA = [...a].filter((n) => !b.has(n));
    const nurB = [...b].filter((n) => !a.has(n));
    pruefe(nurA.length === 0 && nurB.length === 0,
           "die zwei Einhaengepunkte tragen verschiedene Marken: "
           + [...nurA, ...nurB].slice(0, 5).join(" "));

    // Und jede FARBmarke der hellen Wurzel kommt im Dunkeln vor.
    const kopf = roh.slice(0, roh.indexOf("@media (prefers-color-scheme: dark)"));
    const hell = [...kopf.matchAll(/(--[a-z0-9_-]+)\s*:\s*([^;}]+)/g)]
      .filter((m) => /#[0-9a-f]{3,6}\b|color-mix|rgba?\(/i.test(m[2]))
      .map((m) => m[1]);
    const vergessen = [...new Set(hell)].filter((n) => !a.has(n));
    pruefe(vergessen.length === 0,
           `${vergessen.length} Marke(n) haben keinen dunklen Wert und `
           + "blieben hell: " + vergessen.slice(0, 6).join(" "));
    pruefe(hell.length >= 100,
           `nur ${hell.length} Farbmarken gefunden, 100+ erwartet`);

    // ⚠️ Und die drei Stufen selbst. «automatisch» darf KEIN Attribut
    // setzen — nur ohne Attribut greift `prefers-color-scheme`. Ein
    // `data-thema="automatisch"` waere ein Zustand, den das Blatt nicht
    // kennt, und die Oberflaeche bliebe hell, waehrend die Einstellung
    // etwas anderes sagt.
    const js = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8"));
    pruefe(/removeAttribute\("data-thema"\)/.test(js),
           "«automatisch» entfernt das Attribut nicht — dann greift die "
           + "Systemwahl nie");
    for (const stufe of ["automatisch", "hell", "dunkel"]) {
      pruefe(js.includes('"' + stufe + '"'),
             "die Stufe «" + stufe + "» kennt das Skript nicht");
    }
    // ⚠️ Sofort sichtbar, nicht erst beim Speichern. Eine Farbwahl, die man
    // erst nach dem Schliessen des Dialogs sieht, kann man nicht beurteilen.
    //
    // ⚠️ Nach der SACHE fragen, nicht nach dem Ereignisnamen: die Wahl ist
    // eine Knopfreihe («click»); ein Auswahlfeld hiesse «change». Eine Zeile,
    // die den Ereignisnamen festnagelt, wird rot, wenn die Sache besser wird.
    const horcher = js.match(
      /\$\("einst-thema"\)\.addEventListener\("(\w+)",([\s\S]{0,400}?)\n  \}\);/);
    pruefe(horcher, "auf die Farbwahl horcht niemand");
    pruefe(!horcher || /themaAnwenden\(\)/.test(horcher[2]),
           "die Farbwahl wirkt nicht sofort — man muesste den Dialog "
           + "schliessen, um sie zu sehen");
  }
  if (!fehler) console.log("   OK   zwei Einhaengepunkte, eine Liste, keine vergessene Marke");

  console.log("74. Eine Meldung erscheint dort, wo der Anwender steht");
  // ⚠️⚠️ EINE FUNKTION ENTSCHEIDET, ZWEI KANAELE TRAGEN. Scheitert
  // «Einfuegen» im Einstellungsdialog, muss die Meldung dort erscheinen —
  // nicht im Vokabularbereich, den der Dialog verdeckt. Und umgekehrt: eine
  // Meldung aus Bereich 03 oder 05 («Vorlage gespeichert») gehoert NICHT in
  // den Dialog, auch nicht beim naechsten Oeffnen. Ein einziger gespiegelter
  // Kanal zeigte sie dort — rot, wie einen Fehler.
  {
    const js = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8"));
    pruefe(/\$\("einst-meldung"\)\.textContent = z\.einstMeldung/.test(js),
           "der Dialog zeigt nicht seinen eigenen Kanal");
    // Genau EINE Stelle setzt jeden Kanal mit Inhalt: meldeVok().
    for (const feld of ["vokMeldung", "einstMeldung"]) {
      const alle = (js.match(new RegExp(`z\\.${feld} = `, "g")) || []).length;
      const leer = (js.match(new RegExp(`z\\.${feld} = (null|"")`, "g"))
                    || []).length;
      pruefe(alle - leer === 1,
             `${alle - leer} Stellen setzen ${feld}, genau eine erwartet`);
    }
    // Und das Verhalten, an der Attrappe.
    const dlg = document.getElementById("einst");
    const warZu = dlg.hidden;
    M.zustand.vokMeldung = null; M.zustand.einstMeldung = "";
    dlg.hidden = true;
    M.meldeVok("Vorlage gespeichert");
    pruefe(!M.zustand.einstMeldung,
           "eine Meldung bei geschlossenem Dialog landet im Dialog: "
           + JSON.stringify(M.zustand.einstMeldung));
    pruefe(M.zustand.vokMeldung === "Vorlage gespeichert",
           "eine Meldung bei geschlossenem Dialog erscheint nicht in 05");
    M.zustand.vokMeldung = null;
    dlg.hidden = false;
    M.meldeVok("Einfuegen gescheitert");
    pruefe(M.zustand.einstMeldung === "Einfuegen gescheitert",
           "eine Meldung bei offenem Dialog erscheint nicht im Dialog");
    pruefe(!M.zustand.vokMeldung,
           "eine Meldung bei offenem Dialog landet hinter dem Dialog");
    dlg.hidden = warZu; M.zustand.einstMeldung = ""; M.zustand.vokMeldung = null;

    // Der Platz muss es im HTML geben, sonst wirft der Zugriff.
    const html = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    pruefe(/id="einst-meldung"/.test(html),
           "der Platz fuer die Meldung fehlt im Dialog");

    // ⚠️ Und er darf NICHT an `hidden` haengen. Ein leerer Absatz nimmt
    // keinen Platz; `hidden` haette die `display`-Falle aus Punkt 64
    // geoeffnet, die in diesem Projekt schon dreimal zugeschlagen hat.
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/\.einst-meldung:empty \{ display: none/.test(css),
           "die leere Meldung nimmt Platz weg");
    pruefe(!/\$\("einst-meldung"\)\.hidden/.test(js),
           "die Meldung haengt an `hidden` — das ist die display-Falle");

    // ⚠️ Und der Knopf «Einfuegen» in 04 gibt es nur im eigenen Fenster.
    // `readText()` ist der Seite im Browser gesperrt; ein Knopf, der
    // nicht wirken kann, gehoert weg und nicht grau.
    pruefe(/\$\("knopf-einfuegen-antwort"\)\.hidden = !imEigenenFenster\(\)/
             .test(js),
           "«Einfuegen» steht im Browser da und kann dort nicht wirken");
    pruefe(/\.imfeld\[hidden\] \{ display: none/.test(css),
           "`.imfeld` hat keine hidden-Gegenregel — das Ausblenden wirkt "
           + "nicht, `display: inline-flex` schlaegt es");
  }
  if (!fehler) console.log("   OK   eine Quelle, zwei Orte, kein wirkungsloser Knopf");

  console.log("75. Jeder Dialog startet oben, jeder Knopf traegt sein Zeichen");
  // Zwei Dinge, eine Wache — beide sind «etwas fehlt, wo der Anwender es
  // erwartet»:
  //
  // (1) Hilfe, Einstellungen, Impressum starten beim Oeffnen immer ganz
  //     oben.
  // (2) Jeder Knopf traegt ein Zeichen. Zeichen helfen, sich Dinge zu
  //     merken.
  {
    const js = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8"));
    const html = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");

    // ── (1) Der Rollstand ─────────────────────────────────────────────
    // ⚠️ ZWEI Elemente rollen: die Huelle (wenn der Dialog hoeher ist als
    // das Fenster) und der Rumpf (der Inhalt darin). Wer nur eines
    // zuruecksetzt, behebt es bei einer Fenstergroesse und bei der
    // anderen nicht — und das saehe wie erledigt aus.
    const fn = js.match(
      /function dialogVonOben\([^)]*\)\s*\{([\s\S]*?)\n\}/);
    pruefe(fn, "es gibt keine gemeinsame Stelle, die einen Dialog von "
           + "oben zeigt");
    const rumpfNull = fn && /\brumpf\.scrollTop = 0/.test(fn[1]);
    const huelleNull = fn && /\bhuelle\.scrollTop = 0/.test(fn[1]);
    pruefe(rumpfNull, "der Inhalt des Dialogs startet nicht oben");
    pruefe(huelleNull,
           "die Huelle startet nicht oben — bei einem Dialog, der hoeher "
           + "ist als das Fenster, bleibt der Rollstand stehen");

    // ⚠️ UND ALLE DREI GEHEN DURCH DIESE STELLE. Drei Oeffner — die
    // Einstellungen, die Hilfe und das Impressum —, aber nur EINE
    // Ruecksetzung. Wer einen daran vorbeibaut, bekommt sie nie.
    pruefe((js.match(/dialogVonOben\(/g) || []).length >= 3,
           "nicht jeder Dialog geht ueber `dialogVonOben` — der dritte "
           + "startet dann wieder dort, wo man zuletzt war");
    pruefe(!/\$\("(einst|seite)"\)\.hidden = false/.test(js),
           "ein Dialog wird an `dialogVonOben` vorbei sichtbar gemacht");

    // ── (2) Die Zeichen ───────────────────────────────────────────────
    // ⚠️ Geprueft wird die EIGENSCHAFT: jeder Knopf mit Beschriftung
    // traegt ein Zeichen — gleich ob aus dem HTML oder aus `KNOPFBILDER`.
    // Eine Liste der vier nachgeruesteten waere beim fuenften wieder
    // unvollstaendig, und genau so sind diese vier entstanden.
    // ⚠️ AUSNAHMEN MIT BEGRUENDUNG — nicht «die kennen wir schon».
    // Eine Liste ohne Grund je Zeile altert zur Gewohnheit; steht der
    // Grund daneben, laesst er sich beim naechsten Mal pruefen.
    const AUSNAHMEN = {
      // Die Wortmarke IST das Zeichen; ein Sinnbild daneben waere ein
      // zweites Logo.
      "knopf-marke": "die Wortmarke ist selbst das Zeichen",
      // ⚠️ Ausdruecklicher Entwurfsentscheid: «Beispiel» steht in
      // gemischter Schreibung und ohne Sperrung, WEIL es eine
      // Nebenhandlung ist und nicht wie eine Haupthandlung wirken soll
      // (`button.tat.neben`). Ein Zeichen davor machte es wieder
      // gewichtiger. Nicht vergessen, sondern entschieden.
      "knopf-beispiel": "Nebenhandlung, bewusst zurueckgenommen",
    };
    // ⚠️ WELCHE KENNUNGEN BEKOMMEN IHR ZEICHEN VOM SKRIPT? Einmal
    // eingesammelt statt je Knopf gesucht — und zwar um JEDE
    // `KNOPFBILDER`-Stelle herum. Ein geratener Abstand zwischen Kennung und
    // Tabelle waere beim naechsten Eintrag wieder falsch.
    const vomSkript = new Set();
    for (let i = js.indexOf("KNOPFBILDER"); i >= 0;
         i = js.indexOf("KNOPFBILDER", i + 1)) {
      const fenster = js.slice(Math.max(0, i - 1200), i + 400);
      for (const t of fenster.matchAll(/"([a-z0-9-]+)"/g)) {
        vomSkript.add(t[1]);
      }
    }

    const ohne = [];
    for (const m of html.matchAll(
           /<button[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/button>/g)) {
      const [, kennung, inhalt] = m;
      if (kennung in AUSNAHMEN) continue;
      const hatText = /<span/.test(inhalt) || /[A-Za-zÄÖÜäöü]{3}/.test(
        inhalt.replace(/<[^>]*>/g, ""));
      if (!hatText) continue;
      const imHtml = /<svg/.test(inhalt);
      // ⚠️ Zwei Bauarten zaehlen: das Zeichen steht im HTML, ODER das
      // Skript haengt es aus `KNOPFBILDER` an. Gesucht wird die Kennung
      // in der Naehe von `KNOPFBILDER` — 300 Zeichen, weil die
      // Themenknoepfe ihre Kennung in einer Tabelle vor der Schleife
      // tragen und nicht in derselben Zeile wie der Aufruf.
      const imSkript = vomSkript.has(kennung);
      if (!imHtml && !imSkript) ohne.push(kennung);
    }
    pruefe(ohne.length === 0,
           `${ohne.length} beschriftete(r) Knopf ohne Zeichen: `
           + ohne.join(" "));

    // ⚠️ Und die Zeichnungen stehen EINMAL. Die Diskette stand als
    // abgeschriebenes `<svg>` zweimal im HTML; ein drittes Mal waere der
    // dritte Verwalter derselben Zeichnung gewesen.
    pruefe(/const KNOPFBILDER = \{/.test(js),
           "es gibt keine gemeinsame Quelle fuer die Knopfzeichen");
    for (const name of ["speichern", "pruefen", "hinzufuegen",
                        "automatisch", "hell", "dunkel"]) {
      pruefe(new RegExp("\\b" + name + ":").test(
               js.slice(js.indexOf("const KNOPFBILDER"),
                        js.indexOf("const SINNBILDER"))),
             `das Zeichen «${name}» fehlt in KNOPFBILDER`);
    }
  }
  if (!fehler) console.log("   OK   drei Dialoge von oben, kein Knopf ohne Zeichen");

  console.log("76. Die Felder, die es dreimal erwischt hat");
  // ⚠️⚠️ EIN EINGABEFELD OHNE `background` nimmt die Vorgabe des Browsers:
  // WEISS. Im Hellmodus sieht das richtig aus — deshalb faellt es dort nie
  // auf. Im Dunkeln steht dann helle Schrift auf Weiss: man tippt und sieht
  // nichts.
  //
  // ⚠️⚠️ UND HIER STEHT, WAS DIESE WACHE NICHT KANN — das gehoert dazu,
  // sonst gilt sie fuer mehr als sie leistet.
  //
  // Die EIGENSCHAFT «jedes Eingabefeld wird von einer Regel getroffen, die
  // ihm eine Flaeche gibt» laesst sich hier nicht pruefen: welche Regel ein
  // Element wirklich trifft, entscheidet die Kaskade, und die kennt nur
  // eine Darstellungsschicht. Diese Pruefung laeuft an einer Attrappe ohne
  // Darstellung — ein Versuch faellt auf die Elementart zurueck und laesst
  // jedes Feld bestehen.
  //
  // Was bleibt, ist eine ehrliche Ruecklaufsperre fuer die benannten Felder.
  // Weniger, als es sein sollte — aber es sagt, was es ist.
  {
    const css = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8"));
    const regel = (wahl) => {
      const i = css.indexOf(wahl + " {");
      return i < 0 ? "" : css.slice(i, css.indexOf("}", i));
    };
    for (const wahl of ["#vorlagen-filter", ".dienstzeile input"]) {
      const r = regel(wahl);
      pruefe(r, `die Regel fuer ${wahl} ist fort`);
      pruefe(!r || /background(-color)?:/.test(r),
             `${wahl} setzt keine Flaeche — es nimmt die Browservorgabe `
             + "(weiss) und steht im Dunkelmodus als weisser Kasten da");
      pruefe(!r || /\bcolor:/.test(r),
             `${wahl} setzt keine Schriftfarbe — dann rechnet der Browser `
             + "sie gegen seine eigene Flaeche, nicht gegen unsere");
    }
    // ⚠️ Und der Platzhalter gehoert dazu: seine Vorgabefarbe ist auf die
    // VORGABEflaeche gerechnet, nicht auf unsere.
    pruefe(/#vorlagen-filter::placeholder/.test(css),
           "das Suchfeld setzt seine Platzhalterfarbe nicht");
  }
  if (!fehler) console.log("   OK   beide Felder tragen Flaeche, Schrift und Platzhalter");

  console.log("70. Einpflegen geht mehr als einmal");
  // ⚠️ «Vokabular einpflegen» wirkt jedes Mal, auch nach geloeschter und
  // neu eingefuegter Antwort.
  //
  // ⚠️ Und wirkt es nicht, passiert nicht NICHTS: Bereich 05 zeigte weiter
  // das ALTE Ergebnis — ein veralteter fertiger Text, der aussieht wie der
  // neue. Man kopiert ihn und merkt es nicht.
  //
  // Eine Bedingung, die BEIDES verlangt — Feld ungleich neuem Text UND Feld
  // ungleich zuletzt Geschriebenem —, sperrt nach dem ersten Einpflegen:
  // dann ist das Feld genau das zuletzt Geschriebene.
  {
    const feld = document.getElementById("final");
    M.zustand.final = { text: "Erstes Ergebnis", ersetzt: 3,
                        nicht_gefunden: [] };
    M.zustand.finalBearbeitet = null;
    M.zeichne();
    pruefe(feld.value === "Erstes Ergebnis",
           `erster Durchgang: ${feld.value}`);

    M.zustand.final = { text: "Zweites Ergebnis", ersetzt: 4,
                        nicht_gefunden: [] };
    M.zeichne();
    pruefe(feld.value === "Zweites Ergebnis",
           `zweiter Durchgang kommt nicht an — Bereich 05 zeigt weiter `
           + `«${feld.value}»`);

    // ⚠️ Und die andere Richtung: was der Anwender SELBST tippt, darf
    // die naechste Zeichnung nicht ueberschreiben. Dafuer gab es die
    // alte Bedingung, und der Zweck bleibt.
    feld.value = "Von Hand geaendert";
    M.zeichne();
    pruefe(feld.value === "Von Hand geaendert",
           "die eigene Bearbeitung wird bei der naechsten Zeichnung "
           + `ueberschrieben: ${feld.value}`);

    // ⚠️ DER PAPIERKORB im finalisierten Text leert NUR 05: das Woerterbuch
    // und Bereich 04 bleiben, denn wer unzufrieden ist, will neu einpflegen
    // und nicht von vorne.
    pruefe(document.getElementById("knopf-leeren-final") !== null,
           "in Bereich 05 fehlt der Papierkorb");
    M.zustand.antwort04 = "eine Antwort";
    await feuer("knopf-leeren-final");
    pruefe(M.zustand.final === null && feld.value === "",
           "der Papierkorb leert Bereich 05 nicht");
    pruefe(M.zustand.antwort04 === "eine Antwort",
           "der Papierkorb in 05 leert auch Bereich 04");
    M.zustand.antwort04 = "";
    M.zustand.finalBearbeitet = null;
  }
  if (!fehler) console.log("   OK   zweites Ergebnis kommt an, eigene Eingabe bleibt, Papierkorb leert nur 05");

  console.log("69. Der Seitenquelltext bleibt knapp und englisch");
  // ⚠️ `index.html` ist das EINZIGE Stueck dieses Werkzeugs, das jeder
  // Anwender im Browser lesen kann. Was hier als Kommentar steht, ist damit
  // veroeffentlicht und wird mit jeder Seite ausgeliefert. Kommentare im
  // HTML bleiben deshalb knapp; die Begruendungen haengen an den Pruefungen,
  // wo eine Wache sie haelt.
  {
    const HTML69 = fs.readFileSync(
      path.join(WURZEL, "app/static/index.html"), "utf8");
    const kommentare = HTML69.match(/<!--[\s\S]*?-->/g) || [];
    pruefe(kommentare.length > 0, "gar keine Kommentare — die Wache prueft nichts");

    const gesamt = kommentare.reduce((n, k) => n + k.length, 0);
    pruefe(gesamt < HTML69.length * 0.12,
           `${gesamt} von ${HTML69.length} Zeichen sind Kommentar `
           + `(${Math.round(gesamt / HTML69.length * 100)} %) — knapp `
           + "heisst unter 12 %");

    for (const k of kommentare) {
      const eine = k.replace(/\s+/g, " ").trim();
      pruefe(eine.length <= 220,
             `zu lang (${eine.length} Zeichen): ${eine.slice(0, 60)}…`);
      // ⚠️ Auf ENGLISCH. Umlaute sind das billigste sichere Merkmal —
      // der Quelltext wird von aussen gelesen, und `maschera.js` und das
      // CSS duerfen weiter deutsch kommentiert bleiben.
      pruefe(!/[äöüÄÖÜß]/.test(eine),
             `nicht englisch: ${eine.slice(0, 60)}…`);
      // Das Zeichen, mit dem dieses Projekt lange Begruendungen
      // markiert — genau die sollen hier nicht mehr stehen.
      pruefe(!eine.includes("⚠"),
             `eine lange Begruendung im Quelltext: ${eine.slice(0, 60)}…`);
    }
  }
  if (!fehler) console.log("   OK   kurze englische Zeilen, keine Begruendungen");

  console.log("77. Das Ablagefach wird nur angeboten, wo es eines gibt");
  // Das Symbol im Infobereich gibt es unter Linux (Qt) und Windows
  // (`pystray`), unter macOS nicht. Ein Schalter ohne Wirkung liesse sich
  // bedienen und bewirkte nichts. Das schmale Fenster geht ueberall.
  {
    const warFenster = window.pywebview;
    const warPlattform = navigator.platform;
    const fall = (fenster, plattform) => {
      window.pywebview = fenster ? {} : undefined;
      navigator.platform = plattform;
      M.zeichne();
      return {
        tray: !document.getElementById("zeile-tray").hidden,
        widget: !document.getElementById("zeile-widget").hidden,
      };
    };
    const linux = fall(true, "Linux x86_64");
    const win = fall(true, "Win32");
    const mac = fall(true, "MacIntel");
    const browser = fall(false, "Linux x86_64");
    pruefe(linux.tray && linux.widget,
           "unter Linux im eigenen Fenster fehlt ein Fensterschalter");
    pruefe(win.tray,
           "unter Windows fehlt der Schalter fuer den Infobereich");
    pruefe(!mac.tray,
           "unter macOS steht der Schalter fuer den Infobereich — es gibt keinen");
    pruefe(win.widget,
           "unter Windows fehlt der Schalter fuer das schmale Fenster");
    pruefe(!browser.tray && !browser.widget,
           "im Browser stehen Fensterschalter");
    window.pywebview = warFenster;
    navigator.platform = warPlattform;
    M.zeichne();
  }
  if (!fehler) console.log("   OK   Linux und Windows ja, macOS und Browser nein");

  console.log("78. Kein Fehlertext des Browsers in der Oberflaeche");
  // Kommt eine Anfrage nicht an, setzt der Browser den Text — englisch,
  // «Failed to fetch». So stand er in einer italienischen Oberflaeche.
  // Dasselbe fuer eine Absage ohne Begruendung: «HTTP 500» ist kein Satz.
  {
    const vorher = fehler;
    const alteSprache = M.zustand.sprache;
    for (const s of ["de", "fr", "it", "en"]) {
      M.zustand.sprache = s;
      const netz = M.fehlerText(new TypeError("Failed to fetch"));
      pruefe(netz === M.I18N[s].verbindungWeg,
             s + ": Netzfehler nicht uebersetzt: " + netz);
      const http = M.fehlerText(M.serverFehler({}, 500));
      pruefe(http === M.I18N[s].httpFehler.replace("{status}", "500"),
             s + ": Absage ohne Begruendung nicht uebersetzt: " + http);
      pruefe(!/HTTP|Failed|fetch/.test(netz + http),
             s + ": Rohtext sichtbar: " + netz + " / " + http);
    }
    M.zustand.sprache = "it";
    pruefe(M.fehlerText(M.serverFehler({ fehler: "x",
             fehler_schluessel: "datei_zu_gross", fehler_werte: { mb: 10 } },
             413)).includes("10"),
           "eine begruendete Absage verliert ihren eigenen Satz");
    M.zustand.sprache = alteSprache;
    if (fehler === vorher) console.log("   OK   vier Sprachen, beide Wege");
  }

  console.log("79. Rueckfragen im eigenen Dialog, nie im Browserdialog");
  // `window.confirm` traegt den Titel «127.0.0.1:4141 says», Knoepfe in der
  // Sprache des Browsers und eine feste Breite, die im schmalen Fenster
  // ueber den Rand ragt. Geprueft wird die Quelle UND der echte Dialog.
  {
    const vorher = fehler;
    const quelle = ohneKommentare(fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.js"), "utf8"));
    const roh = quelle.match(/\b(?:window\.)?(?:confirm|prompt|alert)\s*\(/g);
    pruefe(!roh, "Browserdialog im Skript: " + (roh || []).join(" "));
    const bl = document.getElementById("frage");
    const warSprache = M.zustand.sprache;
    M.zustand.sprache = "it";
    // Nein
    let p = M.frageZeigen("Vuoi davvero ricominciare?\nTutto via.", {});
    pruefe(!bl.hidden, "der Dialog geht nicht auf");
    pruefe(document.getElementById("frage-text").textContent
           .startsWith("Vuoi davvero"), "der Fragetext fehlt");
    pruefe(document.getElementById("frage-nein-text").textContent
           === M.I18N.it.frageNein, "«Abbrechen» nicht in der Sprache");
    pruefe(document.getElementById("frage-feld").hidden,
           "eine Ja/Nein-Frage zeigt ein Eingabefeld");
    await feuer("frage-nein");
    pruefe((await p) === false && bl.hidden, "Nein gilt nicht als Nein");
    // Ja
    p = M.frageZeigen("x", {});
    await feuer("frage-ja");
    pruefe((await p) === true && bl.hidden, "Ja gilt nicht als Ja");
    // Escape und Klick daneben sind ein Nein
    p = M.frageZeigen("x", {});
    for (const f of bl._h["keydown"] || []) {
      f({ key: "Escape", target: bl, preventDefault() {} });
    }
    pruefe((await p) === false, "Escape bestaetigt");
    p = M.frageZeigen("x", {});
    for (const f of bl._h["click"] || []) {
      f({ target: bl, preventDefault() {}, stopPropagation() {} });
    }
    pruefe((await p) === false, "ein Klick daneben bestaetigt");
    // Eine zweite Frage laesst die erste nicht haengen
    const erste = M.frageZeigen("eins", {});
    const zweite = M.frageZeigen("zwei", {});
    pruefe((await erste) === false, "die erste Frage haengt");
    await feuer("frage-ja");
    pruefe((await zweite) === true, "die zweite Frage antwortet nicht");
    // Eingabe
    p = M.frageZeigen("Nome del modello", { vorschlag: "Lettera" });
    pruefe(!document.getElementById("frage-feld").hidden,
           "die Eingabe zeigt kein Feld");
    pruefe(document.getElementById("frage-eingabe").value === "Lettera",
           "der Vorschlag steht nicht im Feld");
    document.getElementById("frage-eingabe").value = "Lettera 2";
    await feuer("frage-ja");
    pruefe((await p) === "Lettera 2", "die Eingabe kommt nicht zurueck");
    p = M.frageZeigen("Nome del modello", { vorschlag: "Lettera" });
    await feuer("frage-nein");
    pruefe((await p) === null, "Abbrechen liefert trotzdem einen Namen");
    // Neuladen mit Woerterbuch fragt im eigenen Dialog, und das Nein gilt
    const warAntwort = M.zustand.antwort;
    M.zustand.antwort = { maskiert: "[FULLNAME_1]", spans: [],
                          woerterbuch: { "[FULLNAME_1]": "Muster" } };
    for (const [taste, strg] of [["F5", false], ["r", true]]) {
      bestaetigt = false; letzteFrage = null; neuGeladen = 0;
      let verhindert = false;
      for (const f of document._h["keydown"] || []) {
        await f({ key: taste, ctrlKey: strg, metaKey: false, target: document,
                  preventDefault() { verhindert = true; } });
      }
      pruefe(verhindert, taste + ": das Neuladen des Browsers laeuft los");
      pruefe(letzteFrage === M.I18N.it.neuladenFrage.replace("{}", "1"),
             taste + ": keine eigene Rueckfrage: " + letzteFrage);
      pruefe(neuGeladen === 0, taste + ": trotz Nein neu geladen");
    }
    bestaetigt = true;
    for (const f of document._h["keydown"] || []) {
      await f({ key: "F5", ctrlKey: false, metaKey: false, target: document,
                preventDefault() {} });
    }
    pruefe(neuGeladen === 1, "nach Ja nicht neu geladen");
    M.zustand.antwort = warAntwort;
    M.zustand.sprache = warSprache;
    // Schmal: Knoepfe untereinander
    const css = fs.readFileSync(
      path.join(WURZEL, "app/static/maschera.css"), "utf8");
    pruefe(/@media \(max-width: [\d.]+em\) \{\s*\.frage-knoepfe \{[^}]*flex-direction: column/.test(css),
           "im schmalen Fenster stehen die Knoepfe nicht untereinander");
    if (fehler === vorher) {
      console.log("   OK   Ja, Nein, Escape, daneben, Eingabe, schmal gestapelt");
    }
  }

  console.log("80. Neue Adresse: Speichern & neu starten statt Pruefen");
  // Pruefen gegen eine Adresse, auf der noch niemand horcht, meldet nur
  // «keine Antwort». Die neue Adresse gilt erst nach einem Neustart — also
  // sagt der Knopf das und tut es.
  {
    const vorher = fehler;
    const warFenster = window.pywebview;
    let neugestartet = 0;
    window.pywebview = { api: { neustart: async () => { neugestartet++; } } };
    await feuer("knopf-einstellungen");
    const port = document.getElementById("einst-port");
    const text = () => document.getElementById("pruefen-text").textContent;
    port.value = "4141";
    for (const f of port._h["input"] || []) await f({ target: port });
    pruefe(text() === M.I18N[M.zustand.sprache].pruefen,
           "gleicher Port, aber der Knopf heisst nicht «Pruefen»: " + text());
    port.value = "4142";
    for (const f of port._h["input"] || []) await f({ target: port });
    pruefe(text() === M.I18N[M.zustand.sprache].neuStarten,
           "neuer Port, aber kein «Speichern & neu starten»: " + text());
    await feuer("knopf-pruefen");
    pruefe(einstellungen.port === 4142, "der neue Port wurde nicht gespeichert");
    pruefe(neugestartet === 1, "gespeichert, aber nicht neu gestartet");
    // Im Browser: speichern, sagen ab wann — kein Neustart
    window.pywebview = undefined;
    port.value = "4143";
    for (const f of port._h["input"] || []) await f({ target: port });
    pruefe(text() === M.I18N[M.zustand.sprache].nurSpeichern,
           "im Browser verspricht der Knopf einen Neustart: " + text());
    await feuer("knopf-pruefen");
    pruefe(einstellungen.port === 4143 && neugestartet === 1,
           "im Browser nicht gespeichert oder doch neu gestartet");
    pruefe(document.getElementById("einst-befund").textContent
           === M.I18N[M.zustand.sprache].giltNachNeustart,
           "im Browser fehlt der Satz, ab wann es gilt");
    // Zurueck auf den laufenden Port
    port.value = "4141";
    for (const f of port._h["input"] || []) await f({ target: port });
    einstellungen = { ...einstellungen, port: 4141 };
    window.pywebview = warFenster;
    await feuer("knopf-einst-zu");
    if (fehler === vorher) {
      console.log("   OK   Pruefen, Speichern & neu starten, im Browser Speichern");
    }
  }

  console.log("");
  amEnde = true;
  if (fehler) {
    console.log(fehler + " Pruefung(en) fehlgeschlagen.");
    process.exit(1);
  }
  console.log("Oberflaechenlogik in Ordnung.");
}, 120);
