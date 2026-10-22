/* MASCHERA — Spalte 1 und 2.
 *
 * ⚠️ **Hier wird nichts erkannt.** Jede Maskierung kommt aus
 * `POST /api/anonymisieren`. Browserseitige Regexe als Notloesung waeren
 * genau der Fall, vor dem `docs/API_OBERFLAECHE.md` bei `ohne_modell`
 * warnt: eine Maskierung mit gruener Anzeige, die keine ist.
 * `tests/test_app.py` prueft das.
 *
 * ⚠️ **Nur `textContent`, nie `innerHTML` mit Serverdaten.** Der Text
 * stammt aus einem Dokument des Anwenders, also aus einer Quelle, die man
 * nicht kennt. Eine Oberflaeche, die sich das an einer Stelle angewoehnt,
 * tut es spaeter auch dort, wo es zaehlt.
 *
 * Farben, Quellenstriche und Tag-Plaketten stammen aus dem Entwurf.
 */

"use strict";

/* --- Aus dem Entwurf uebernommen ---------------------------------------- */

const GROUP_PALETTE = {
  person:   ["var(--ph-gruppe-person-fl)", "var(--ph-gruppe-person-ra)", "var(--ph-gruppe-person-sc)"],
  origin:   ["var(--ph-gruppe-origin-fl)", "var(--ph-gruppe-origin-ra)", "var(--ph-gruppe-origin-sc)"],
  address:  ["var(--ph-gruppe-address-fl)", "var(--ph-gruppe-address-ra)", "var(--ph-gruppe-address-sc)"],
  contact:  ["var(--ph-gruppe-contact-fl)", "var(--ph-gruppe-contact-ra)", "var(--ph-gruppe-contact-sc)"],
  official: ["var(--ph-gruppe-official-fl)", "var(--ph-gruppe-official-ra)", "var(--ph-gruppe-official-sc)"],
  finance:  ["var(--ph-gruppe-finance-fl)", "var(--ph-gruppe-finance-ra)", "var(--ph-gruppe-finance-sc)"],
  health:   ["var(--ph-gruppe-health-fl)", "var(--ph-gruppe-health-ra)", "var(--ph-gruppe-health-sc)"],
  process:  ["var(--ph-gruppe-process-fl)", "var(--ph-gruppe-process-ra)", "var(--ph-gruppe-process-sc)"],
  plain:    ["var(--ph-gruppe-plain-fl)", "var(--ph-gruppe-plain-ra)", "var(--ph-gruppe-plain-sc)"]
};

const TYPE_COLORS = {
  FULLNAME: ["var(--ph-tag-fullname-fl)", "var(--ph-tag-fullname-ra)", "var(--ph-tag-fullname-sc)"],
  CITY:     ["var(--ph-tag-city-fl)", "var(--ph-tag-city-ra)", "var(--ph-tag-city-sc)"],
  STREET:   ["var(--ph-tag-street-fl)", "var(--ph-tag-street-ra)", "var(--ph-tag-street-sc)"],
  ZIPCODE:  ["var(--ph-tag-street-fl)", "var(--ph-tag-street-ra)", "var(--ph-tag-street-sc)"],
  DATE:     ["var(--ph-tag-date-fl)", "var(--ph-tag-date-ra)", "var(--ph-tag-date-sc)"],
  EMAIL:    ["var(--ph-tag-email-fl)", "var(--ph-tag-email-ra)", "var(--ph-tag-email-sc)"],
  PHONE:    ["var(--ph-tag-phone-fl)", "var(--ph-tag-phone-ra)", "var(--ph-tag-phone-sc)"],
  ORG:      ["var(--ph-tag-org-fl)", "var(--ph-tag-org-ra)", "var(--ph-tag-org-sc)"],
  CASE_ID:  ["var(--ph-tag-case_id-fl)", "var(--ph-tag-case_id-ra)", "var(--ph-tag-case_id-sc)"],
  AHVN13:   ["var(--ph-tag-ahvn13-fl)", "var(--ph-tag-ahvn13-ra)", "var(--ph-tag-ahvn13-sc)"],
  IBAN:     ["var(--ph-tag-ahvn13-fl)", "var(--ph-tag-ahvn13-ra)", "var(--ph-tag-ahvn13-sc)"]
};

const TYPE_FALLBACK = [
  ["var(--ph-rest-1-fl)", "var(--ph-rest-1-ra)", "var(--ph-rest-1-sc)"],
  ["var(--ph-rest-2-fl)", "var(--ph-rest-2-ra)", "var(--ph-rest-2-sc)"],
  ["var(--ph-rest-3-fl)", "var(--ph-rest-3-ra)", "var(--ph-rest-3-sc)"],
  ["var(--ph-rest-4-fl)", "var(--ph-rest-4-ra)", "var(--ph-rest-4-sc)"]
];

/* **Der Rand sagt, wo Arbeit liegt — nicht, wo es sicher ist.**
 *
 * Die kraeftige Linie zieht den Blick dorthin, wo ein Mensch hinsehen muss.
 * Andersherum — kraeftig fuer «Pruefsumme, also sicher» — zeigte sie auf
 * die Stellen, an denen ohnehin nichts zu tun ist.
 *
 * `manuell` sticht hervor, obwohl dort nichts zu pruefen ist: wer als
 * Zweiter draufschaut, braucht genau diese Auskunft. Deshalb doppelt statt
 * einfach — es ist eine andere Aussage, nicht dieselbe in staerker.
 */
/* Die Farben stehen im Blatt, nicht hier. Was hier bleibt, ist die
 * STRICHART, und die ist eine Aussage und keine Farbe: ausgezogen, doppelt,
 * gestrichelt, gepunktet tragen im Dunkeln unveraendert.
 */
const SRC_STYLE = {
  // Seit 2.0 ohne sichtbaren Rand: die haeufigste Herkunft sieht aus wie im
  // Entwurf. Die anderen behalten ihren Rand als Hinweis.
  model:       "1px solid transparent",
  propagation: "1px solid transparent",
  manuell:     "3px double var(--manuell)",
  checksum:    "1px dashed var(--gr-matt)",
  regex:       "1px dashed var(--muster)",
  rule:        "1px dotted var(--color-neutral-500)"
};

/* Die zehn haeufigsten zuoberst im Kontextmenue — sie decken den Grossteil
 * der Korrekturen ab, und niemand soll fuer «Nachname» durch 45 Eintraege
 * scrollen.
 */
const FREQUENT = ["FULLNAME", "GIVENNAME", "STREET", "ZIPCODE", "CITY",
                  "EMAIL", "PHONE", "DATE", "CASE_ID", "ORG"];

const PH_RE = /\[[A-Za-z][A-Za-z0-9_]*_\d+[a-z]?\]/g;

/* Wie `PH_RE`, aber duldet Markdown-Rueckstriche.
 *
 * Der Kopierknopf mancher KI-Dienste gibt MARKDOWN-QUELLTEXT heraus, und
 * dort werden `_` und `[` entwertet: `\[FULLNAME\_2\]`. `PH_RE` erkennt so
 * etwas nicht als Platzhalter — `nicht_gefunden` bliebe LEER, `ersetzt`
 * stuende auf 0, und die Oberflaeche meldete nichts, waehrend im fertigen
 * Text jede Maskierung stehen bliebe. Ein leerer Befund ist keine
 * Entwarnung.
 */
const PH_ROH = /\\?\[([A-Za-z][A-Za-z0-9_\\]*?)\\?_(\d+)([a-z]?)\\?\]/g;

/* Markdown-Entwertung in Platzhaltern zuruecknehmen.
 *
 * NUR INNERHALB VON PLATZHALTERN. Ein globales `\\(.)` -> `$1` waere das
 * Naheliegende und das Falsche: KI-Antworten tragen Pfade wie `C:\Users\…`,
 * LaTeX wie `\alpha` und Code, in denen der Rueckstrich etwas bedeutet.
 * Angefasst wird nur, was die FORM eines Platzhalters hat.
 *
 * Das ist DEKODIEREN, nicht raten: `\_` ist derselbe Platzhalter in einer
 * Transportform. Anders bei der Gross-/Kleinschreibung, fuer die
 * `app/serve.py` bewusst nichts repariert — dort waere es ein anderer
 * Platzhalter, hier derselbe.
 *
 * Gibt Text und Anzahl zurueck, damit der Aufrufer es MELDEN kann.
 */
function markdownZurueck(text) {
  let anzahl = 0;
  const sauber = String(text || "").replace(
    PH_ROH, (ganz, name, nr, endung) => {
      const neu = "[" + name.replace(/\\/g, "") + "_" + nr + endung + "]";
      if (neu !== ganz) anzahl++;
      return neu;
    });
  return { text: sauber, anzahl };
}

/* Zerschlagene Platzhalter ergaenzen — aber NUR, was das Woerterbuch
 * bestaetigt.
 *
 * Manche KI-Antworten enthalten Reste wie
 *
 *     GIVENNAME_2]\[FULLNAME_2]GIVENNAME\_2] \[FULLNAME\_2]
 *
 * — die Haelfte ohne oeffnende Klammer. `markdownZurueck()` fasst das zu
 * Recht nicht an.
 *
 * **Das Woerterbuch ist der Beweis, nicht die Vermutung.** Ergaenzt wird
 * eine Klammer nur, wenn `[NAME_N]` in diesem Lauf WIRKLICH vergeben wurde
 * — ein Abgleich mit dem, was das Werkzeug selbst eingesetzt hat, kein
 * Raten ueber den Text. Deshalb etwas anderes als die
 * Gross-/Kleinschreibung, fuer die `app/serve.py` nichts repariert: dort
 * waere `[name_1]` ein Platzhalter, den es nie gab. Hier gab es ihn.
 *
 * Was das Woerterbuch NICHT kennt, bleibt stehen und wird GEMELDET.
 */
const PH_BRUCH = /(^|[^[\\])\\?([A-Z][A-Z0-9_]*?)\\?_(\d+)([a-z]?)\]/g;

function zerschlageneErgaenzen(text, woerterbuch) {
  const wb = woerterbuch || {};
  const ergaenzt = [];
  const sauber = String(text || "").replace(
    PH_BRUCH, (ganz, davor, name, nr, endung) => {
      const ph = "[" + name.replace(/\\/g, "") + "_" + nr + endung + "]";
      if (!(ph in wb)) return ganz;      // unbekannt -> unangetastet
      if (!ergaenzt.includes(ph)) ergaenzt.push(ph);
      return davor + ph;
    });
  return { text: sauber, ergaenzt };
}

/* Steht noch etwas Platzhalteraehnliches im Text, das KEIN gueltiger
 * Platzhalter ist? Gibt die Fundstellen zurueck.
 *
 * Repariert wird hier NICHTS — ein `NAME_2]` ohne oeffnende Klammer koennte
 * gewoehnlicher Text sein, und wer das erriete, schriebe einen echten Wert
 * in einen Brief, den niemand geprueft hat.
 */
function entwerteteReste(text) {
  const s = String(text || "");
  const gut = new Set(s.match(PH_RE) || []);
  const reste = [];
  PH_ROH.lastIndex = 0;
  let m;
  while ((m = PH_ROH.exec(s)) !== null) {
    if (!gut.has(m[0]) && !reste.includes(m[0])) reste.push(m[0]);
  }
  return reste;
}

const I18N = {
  de: { uebernahme: "Übernahme in Prompt",
        einpflegen: "Vokabular einpflegen", kopiertK: "Kopiert",
        maskeWeg: "Maske entfernen",
        haeufig: "Häufig",
        maskiertDurch: { model: "durch das KI-Modell maskiert", propagation: "maskiert, weil derselbe Wert schon erkannt war", manuell: "von Hand maskiert", checksum: "durch Prüfziffer bestätigt und maskiert", regex: "durch ein Muster maskiert", rule: "durch eine eigene Regel maskiert" },
        maskiertSonst: "maskiert",
        spracheW: "Sprache",
        sicherheit: "{} % sicher",
        knopfTipps: {
          "knopf-kopieren-orig": "Originaltext kopieren",
          "knopf-leeren-orig": "Originaltext leeren",
          "knopf-bearbeiten": "Maskierten Text bearbeiten",
          "knopf-herunter-mask": "Maskierten Text herunterladen",
          "knopf-kopieren": "Maskierten Text kopieren",
          "knopf-kopieren-prompt": "Nur Prompt kopieren",
          "knopf-leeren-prompt": "Prompt leeren",
          "knopf-einfuegen-antwort": "Antwort einfügen",
          "knopf-leeren-antwort": "Antwort leeren",
          "knopf-herunter-final": "Finalen Text herunterladen",
          "knopf-leeren-final": "Finalen Text leeren",
          "knopf-final-kopieren": "Finalen Text kopieren" },
        anwenden: "wird angewendet",
        suchLeeren: "Suche leeren", einpflegenZeile: "Vokabular wird eingepflegt",
        eingepflegtZeile: "Vokabular eingepflegt",
        davonMaskiert: "davon {} maskiert", inDauer: "in {}", hinweiseInfo: "Hinweise zum Lauf",
        dienstWeg: "Dienst entfernen",
        spalteSichern: "Vorlage speichern", spalteKopieren: "Prompt kopieren", spalteLeeren: "Prompt leeren",
        vergroessern: "Vergrössern", verkleinern: "Verkleinern",
        suchen: "Suchen …", keinTreffer: "Kein Treffer",
        nichtMaskiert: "nicht maskiert",
        bspdWeg: "Maske wirklich entfernen?\n{} ist ein besonders schützenswertes Personendatum.",
        bspdSetzen: "Als {} maskieren?\nDas ist ein besonders schützenswertes Personendatum.",
        einstT: "Einstellungen",
        schliessen: "Schliessen", einstZu: "Speichern", einstZuRest: " & schliessen", einstAbbrechen: "Abbrechen",
        zoneHinaus: "Verlässt dein Gerät", vokAlle: "Alle", ablauf: "Ablauf", schritte: ["Text einfügen", "Prüfen", "Prompt senden", "Antwort einfügen", "Zurückübersetzen"],
        allgemeinT: "Allgemein",
        serverT: "Server",
        serverH: "Adresse und Port des lokalen Maskierdienstes. Der Text verlässt dein Gerät nicht. Die Prüfung zeigt, ob der Dienst antwortet.",
        adresse: "Adresse",
        port: "Port",
        pruefen: "Prüfen",
        neuStarten: "Speichern & neu starten",
        nurSpeichern: "Speichern",
        startetNeu: "MASCHERA startet neu …",
        giltNachNeustart: "Gespeichert. Gilt ab dem nächsten Start des Dienstes.",
        keinDienstDa: "Unter {} antwortet kein MASCHERA.",
        diensteT: "Dienste",
        diensteH: "Diese Dienste stehen im Menü neben dem Sendeknopf. Beim Kopieren öffnet MASCHERA die Adresse des gewählten Dienstes. Der zuletzt gewählte bleibt auch für künftige Sitzungen gespeichert.",
        hinzu: "Hinzufügen", vorgabenZurueck: "Vorgaben wiederherstellen",
        entfernen: "Entfernen",
        vokWeg: "{} entfernen: Der Platzhalter verschwindet im ganzen Text, dort steht wieder der Originalwert. Gibst du den Text danach weiter, geht er unmaskiert mit.",
        fensterWort: "Dienste in neuem Fenster öffnen statt im Reiter",
        trayWort: "Beim Schliessen in den Infobereich (Tray) statt beenden",
        widgetWort: "Schmales Fenster, immer im Vordergrund",
        fensterHilfe: "Beides wirkt erst nach dem Neustart der Applikation.",
        klartextT: "Klartext-Tags",
        klartextStelle: "erkannt, bleibt im Klartext",
        klartextWort: "Klartext",
        klartextH: "Wähle die Typen, die MASCHERA nie maskieren soll. Sie werden weiter erkannt, bleiben im Text aber stehen. Das gilt für jedes Dokument, bis du sie wieder abwählst.",
        regelnT: "Eigene Regeln",
        regelnH: "Eigene Wörter und Muster, die zusätzlich maskiert werden. Als YAML. Wer sie ändert, ändert das Messergebnis.",
        regelnSpeichern: "Regeln speichern",
        pruefeLaeuft: "wird geprüft …",
        dienstDa: "MASCHERA {v} antwortet · Modell {m}",
        falscherDienst: "Antwortet, ist aber nicht MASCHERA: {}",
        keinDienst: "Keine Antwort: {}",
        bspdFrage: "{} dauerhaft im Klartext lassen?\nDas ist ein besonders schützenswertes Personendatum.",
        starrHinweis: "Bleibt ohnehin im Klartext. Nicht umlegbar.",
        unbekannteTags: "Gespeicherte Tags, die es nicht mehr gibt: {}",
        einpflegen04: "Vokabular einpflegen", leerenA: "Leeren",
        antwortPlatz: "Antwort deines KI-Werkzeugs hier einfügen (Ctrl+V) …",
        offenText: "{} Platzhalter blieben stehen. Im fertigen Text nachsehen:",
        gutText: "{} Platzhalter zurückgesetzt.",
        hinausT: "Prompt + maskierter Text", trenner: "den oberen Prompt auf folgenden Text anwenden",
        sendenZu: "Alles kopieren und {} öffnen", onlineWarnung: "In {} arbeitest du online, sei vorsichtig!", origPlatz: "Originaltext hier einfügen …", promptPlatz: "Dein Prompt, z. B. «Beantworte diese E-Mail freundlich.»", hinausLeer: "Erst «Übernahme in Prompt», dann steht hier, was hinausgeht.",
        spalteId: "ID",
        spalteWert: "Originalwert", spalteTyp: "Typ", anteilW: "Maskierter Anteil",
        keinVokabular: "Noch kein Vokabular. Es entsteht beim Maskieren.",
        gruppen: { person: "Person", herkunft: "Herkunft und Zugehörigkeit",
          anschrift: "Anschrift und Ort", erreichbar: "Erreichbarkeit",
          amtlich: "Amtliche Nummern", finanzen: "Finanzen",
          gesundheit: "Gesundheit und Versicherung",
          verfahren: "Verfahren, Zeit, Organisation",
          nurerkannt: "Nur erkannt, nie ersetzt" },
        darstellungT: "Darstellung", themaEtikett: "Farben",
        themaH: "«Automatisch» folgt der Einstellung deines Systems.",
        themaAuto: "Automatisch", themaHell: "Hell", themaDunkel: "Dunkel",
        schriftT: "Schriftart", schriftart: "Schriftfamilie",
        schriftgroesse: "Grösse",
        schriftH: "Gilt für die Textflächen: Originaltext, maskierter Text, Prompt und Antwort.",
        schriftprobe: "Sehr geehrte Damen und Herren", vorschauE: "Vorschau",
        schriftSerif: "Serifen",
        schriftMono: "Feste Breite",
        herunterladen: "Herunterladen", hochladen: "Hochladen", einfuegen: "Einfügen",
        einfuegenHinweis: "Zwischenablage gesperrt. Bitte Ctrl+V drücken.",
        drop_ohne_datei: "Aus diesem Programm kommt keine Datei an. Ziehe die Nachricht zuerst auf den Schreibtisch und dann hierher.",
        mUpdate: "Nach Updates suchen", neuesteSucht: "Frage GitHub nach der neuesten Fassung …", neuesteAktuell: "Du hast {aktuell}. Das ist die neueste Fassung.", neuesteNeu: "Fassung {neueste} ist da. Du hast {aktuell}.", neuesteSeite: "Zur Download-Seite",
        kAusschneiden: "Ausschneiden", kKopieren: "Kopieren", kEinfuegen: "Einfügen",
        menu: "Menü",
        mBrowser: "Im Browser öffnen", mHilfe: "Hilfe",
        mHilfeBald: "kommt später", mWebseite: "maschera.ch",
        mGithub: "Quellcode auf GitHub", mDownload: "Herunterladen",
        mFehler: "Fehler melden",
        mImpressum: "Impressum", mKontakt: "Kontakt",
        finalKopieren: "Kopieren",
        vokHerunter: "Vokabular herunterladen",
        vokHoch: "Vokabular hochladen",
        tplSichern: "Speichern",
        tplWaehlen: "Vorlagen ({})",
        tplSuchen: "Suchen …", tplNichts: "Keine Vorlage passt.",
        tplLeer: "Noch keine lokale Vorlage gespeichert",
        tplName: "Name der Vorlage",
        tplWarnung: "Vorlagen liegen dauerhaft im Klartext auf der Platte. "
          + "Keine Personendaten in eine Vorlage schreiben.",
        tplWeg: "Vorlage «{}» löschen?", tplWegT: "Vorlage löschen",
        tplGesichert: "Vorlage «{}» gespeichert.",
        tplFehler: "Vorlage nicht gespeichert: {}",
        sichernWarnung: "Die Datei enthält {} Originalwerte im Klartext, "
          + "also alles, was hier maskiert wurde. Sie liegt danach ungeschützt "
          + "im Downloadordner. Sichern?",
        vokGeladen: "{} Vokabulareinträge eingelesen.",
        vokKaputt: "Die Datei ist kein lesbares JSON. Nichts eingelesen.",
        frageJa: "Weiter",
        frageNein: "Abbrechen",
        frageOk: "Übernehmen",
        neuladenFrage: "Wirklich neu laden?\n{} Vokabulareinträge gehen verloren.",
        verbindungWeg: "Keine Verbindung zum MASCHERA-Dienst. Die Anfrage kam nicht an. Nochmals versuchen; hilft das nicht, MASCHERA neu starten.",
        httpFehler: "Der MASCHERA-Dienst hat die Anfrage abgelehnt (Fehler {status}).",
        vokFalsch: "Die Datei enthält kein Objekt. Nichts eingelesen.",
        vokFremd: "Keine MASCHERA-Vokabulardatei. Nichts eingelesen.",
        vokFassung: "Unbekannte Fassung {}. Diese Ausgabe liest Fassung 1.",
        vokKein: "Kein Wörterbuch in der Datei. Nichts eingelesen.",
        vokSchluessel: "Kein gültiger Platzhalter: {}. Nichts eingelesen.",
        vokWert: "Der Wert zu {} ist keine Zeichenkette. Nichts eingelesen.",
        vokText: "Der maskierte Text in der Datei ist keine Zeichenkette.",
       
        bearbeiten: "Bearbeiten", bearbeitenFertig: "Fertig",
        bearbeitenHilfe: "Text von Hand korrigieren. Platzhalter wie [FULLNAME_1] bitte stehen lassen. Sie werden am Ende zurückgewandelt.",
        phUnbekannt: "Diese Platzhalter kennt das Wörterbuch nicht: {liste}. Sie bleiben am Ende stehen.",
        phEntwertet: "{} Platzhalter aus der Markdown-Auszeichnung zurückgeholt. Der Dienst hatte sie mit Rückstrichen entwertet.",
        phErgaenzt: "{} zerschlagene Platzhalter ergänzt: {liste}. Das Wörterbuch kennt sie. Die Klammer hatte der Dienst verschluckt.",
        phKaputt: "Diese Stellen sehen aus wie Platzhalter, sind aber keine: {liste}. Sie werden am Ende NICHT ersetzt. Bitte im Text nachsehen.",
        fussLinks: "MASCHERA · Verarbeitung auf diesem Gerät · keine Online-Verbindung zu den KI-Diensten", bereitS: "Bereit",
        orig: "Originaltext", masked: "Maskiert", run: "Maskieren",
        fertig: "Finaler Text", prompt: "Promptzusammenführung", promptT: "Prompt",
        antwort: "Antwort", neu: "Neu",
        hundert: "100% lokal", einst: "Einstellungen",
        spruch: "Maskiere deine Daten, bevor du sie mit anderen teilst! · "
              + "Lokales Modell · DSG / GDPR",
        spruch1: "Maskiere deine Daten, bevor du sie mit anderen teilst!",
        spruch2: "Lokales Modell · DSG / GDPR",
        laden: "Lokales KI-Modell wird geladen",
        keinStart: "Kein Server auf /api/zustand: {}",
        zeichenN: (n) => n + " Zeichen",
        eintraegeN: (n) => n + " Einträge",
        leer05: "Hier landet der fertige Text, sobald du das Vokabular "
              + "einpflegst.",
        leer02: "Noch nichts maskiert. Text in Spalte 1 einfügen und "
              + "«Maskieren» drücken.",
        dropN: "Klicken oder Textdatei bzw. Mail hierher ziehen", dropT: "Unterstützt: PDF, DOCX, TXT, MD, LOG, CSV, JSON und Mails als EML, MSG oder MBOX. Ein Klick öffnet die Dateiauswahl.",
        laeuft: "läuft …", lWartet: "Text wird vorbereitet …", lModell: "Fenster {} von {}", lMaskieren: "Maskieren, Wörterbuch wird gebaut …", lRest: "noch etwa {}", drop: "Datei hierher ziehen oder wählen",
        portFehlt: "Kein Port angegeben.",
        verwerfenVok: "Wirklich fortfahren?\n{} Vokabulareinträge gehen verloren.",
        verwerfenText: "Wirklich fortfahren?\nDer Text in Spalte 1 geht verloren.",
        neuAlles: "Willst du wirklich neu beginnen?\nAlle Daten werden zurückgesetzt!",
        beispiel: "Beispiel", kopieren: "Kopieren",
        kopiert: "Kopiert", vokabular: "Vokabular",
        ohneModell: "OHNE MODELL: nur Prüfsummen und Muster. Namen, "
                  + "Daten und Adressen bleiben im Klartext.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "OHNE MODELL: nur Prüfsummen und Muster. Namen, Daten und Adressen bleiben im KLARTEXT.",
          fenster: "Länger als ein Fenster ({token} Token). Wird überlappend verarbeitet.",
          wortgrenzen: "{anzahl} Modellspannen lagen mitten in einem Wort und wurden auf Wortgrenzen gezogen.",
          mehrere_nachrichten: "{anzahl} Nachrichten in der Datei. Nur die erste wird verarbeitet.",
          vorlieben: "Aus den gespeicherten Vorlieben im Klartext: {tags}",
          ohne_woerterbuch: "Ohne Wörterbuch: endgültig anonymisiert, keine Rückwandlung möglich.",
          eigene_regeln: "Eigene Regeln angewendet ({anzahl}): {namen}",
          schreibweise: "{platzhalter} unterscheidet sich von {treffer} nur in der Schreibweise. Nicht ersetzt.",
          anhang_uebersprungen: "Anhang übersprungen: {name}",
          kein_textteil: "Die Mail hat keinen Textteil, nur {art}.",
          msg_ohne_textrumpf: "Die .msg hat keinen reinen Textrumpf (nur RTF oder HTML). In Outlook «Speichern unter» → .eml wählen.",
          binaer_abgeschnitten: "{zeichen} Zeichen nach dem Textende sahen aus wie Binärdaten und wurden weggelassen.",
          nur_html: "nur HTML-Teil vorhanden, grob entkleidet",
          kein_rumpf: "kein Textrumpf gefunden",
          pdf_ohne_text: "kein Text im PDF. Vermutlich ein Scan. Ohne OCR sieht der Filter nichts, und ein leerer Befund heisst hier NICHT, dass keine Personendaten drin sind.",
          pdf_seiten: "{anzahl} Seiten, Layout geht beim Auslesen verloren",
          tabellen: "{anzahl} Tabellen, zeilenweise gelesen",
          nicht_gelesen: "NICHT gelesen: {teile}. Dort steht bei Briefen oft der Absender",
          docx_leer: "kein Text im Dokument. Ein leerer Befund heisst hier NICHT, dass keine Personendaten drin sind.",
          kodierung: "Kodierung {kodierung}",
          bom: "Byte-Order-Mark am Textanfang, entfernt",
          t_kopfzeilen: "Kopfzeilen",
          t_fusszeilen: "Fusszeilen",
          t_kommentare: "Kommentare",
          t_fussnoten: "Fussnoten",
        },
        // MELDUNGEN — dieselbe Bauart wie `hinweise` darueber. Der Server schickt
        // zu `fehler` und `warnung` einen Schluessel mit; hier stehen die vier
        // Fassungen dazu. Wer eine Meldung im Server hinzufuegt und hier nichts
        // eintraegt, faellt still auf den deutschen Satz zurueck —
        // `tests/test_api.py` Punkt 19 macht das laut.
        //
        // Die Feldnamen in Ruecken-Anfuehrung (`text`, `yaml`, `dienste`) bleiben
        // in JEDER Sprache stehen. Sie sind Namen auf der Leitung; uebersetzt waeren
        // sie nicht mehr auffindbar.
        meldungen: {
          adresse_fehlt: "Feld `adresse` fehlt oder ist leer.",
          adresse_zu_lang: "Adresse länger als {hoechstens} Zeichen.",
          datei_ohne_text: "Datei ergab keinen Text.",
          datei_unlesbar: "Datei nicht lesbar: beschädigt oder kein unterstütztes Format.",
          datei_zu_gross: "Datei grösser als {mb} MB.",
          dienst_kein_objekt: "Dienst {nummer} ist kein Objekt.",
          dienst_kennung_doppelt: "Kennung zweimal vergeben: {kennung}",
          dienst_ohne_adresse: "Dienst {name} hat keine Adresse.",
          dienst_ohne_namen: "Dienst {nummer} hat keinen Namen.",
          dienst_schema: "Dienst {name}: nur https:// oder http://, nicht {adresse}",
          dienste_keine_liste: "Feld `dienste` ist keine Liste.",
          dienste_leer: "Mindestens ein Dienst ist nötig. Sonst weiss «Kopieren und öffnen» nicht, wohin.",
          dienste_zu_viele: "Höchstens {hoechstens} Dienste.",
          einst_kein_objekt: "Kein Objekt.",
          einstellungen_gespeichert: "Gespeichert.",
          feld_klartext: "Feld `klartext` fehlt oder ist keine Tagliste.",
          feld_text: "Feld `text` fehlt oder ist kein Text.",
          feld_woerterbuch: "Feld `woerterbuch` fehlt oder ist kein Objekt.",
          feld_yaml: "Feld `yaml` fehlt oder ist kein Text.",
          fenster_kein_wahrheitswert: "Feld `eigenes_fenster` ist kein Wahrheitswert.",
          format_unbekannt: "Format {endung} wird nicht gelesen. Möglich: {moeglich}",
          keine_datei: "Keine Datei erhalten.",
          klartext_gelesen: "Diese Tags bleiben dauerhaft im Klartext.",
          klartext_gespeichert: "Gespeichert. Diese Tags bleiben dauerhaft im Klartext, auch in künftigen Dokumenten.",
          nicht_gespeichert: "Nicht gespeichert. Die Datei im Einstellungsordner liess sich nicht schreiben.",
          ohne_tags_unbekannt: "Unbekannte Tags bei `ohne`: {tags}",
          port_ausserhalb: "Port ausserhalb 1–65535: {port}",
          regeldatei_fehlerhaft: "Die Regeldatei ist fehlerhaft und wurde nicht angewendet.",
          regeln_abgelehnt: "Regeln abgelehnt. Die Datei enthält einen Fehler.",
          regeln_gelesen: "Wer die Regeln ändert, ändert das Messergebnis.",
          regeln_veraltete_schluessel: "Diese Regeldatei benutzt veraltete Schlüssel. Sie werden weiter gelesen oder übergangen: {umbenennungen}",
          regeln_gespeichert: "Gespeichert. Das Messergebnis ändert sich damit.",
          neueste_begrenzt: "GitHub begrenzt gerade die Abfragen. Für dein Netz sind die 60 pro Stunde aufgebraucht. In einer Stunde nochmals versuchen, oder direkt auf die Download-Seite.",
          neueste_nicht_erreichbar: "GitHub ist nicht erreichbar: ohne Netz, oder der Server darf nicht hinaus. Die neueste Fassung steht auf der Download-Seite.",
          neueste_unlesbar: "GitHub hat geantwortet, aber ohne lesbare Fassungsnummer. Die neueste Fassung steht auf der Download-Seite.",
          regeln_unlesbar: "Regeln nicht lesbar. Ein Feld hat die falsche Form.",
          tray_kein_wahrheitswert: "Feld `tray` ist kein Wahrheitswert.",
          fenstermodus_unbekannt: "Fenstermodus {wert} gibt es nicht. Möglich: {moeglich}",
          thema_unbekannt: "Thema {wert} gibt es nicht. Möglich: {moeglich}",
          schriftart_unbekannt: "Schriftart {wert} gibt es nicht. Möglich: {moeglich}",
          schriftgroesse_unbekannt: "Schriftgrösse {wert} gibt es nicht. Möglich: {moeglich}",
          sprache_unbekannt: "Sprache {sprache} gibt es nicht. Möglich: {moeglich}",
          oberflaechensprache_unbekannt: "Bediensprache {wert} gibt es nicht. Möglich: {moeglich}",
          text_leer: "Der Text ist leer.",
          vorlage_kein_objekt: "Vorlage {nummer} ist kein Objekt.",
          vorlage_name_doppelt: "Name zweimal vergeben: {name}",
          vorlage_name_zu_lang: "Name länger als {hoechstens} Zeichen: {name}",
          vorlage_ohne_namen: "Vorlage {nummer} hat keinen Namen.",
          vorlage_ohne_text: "Vorlage {nummer} ({name}) hat keinen Text.",
          vorlage_text_zu_lang: "Vorlage {name} länger als {hoechstens} Zeichen.",
          vorlagen_feld_fehlt: "Feld `vorlagen` fehlt oder ist keine Liste.",
          vorlagen_klartext: "Vorlagen liegen dauerhaft im Klartext auf der Platte. Keine Personendaten in eine Vorlage schreiben.",
          vorlagen_zu_viele: "Höchstens {hoechstens} Vorlagen.",
          vorliebe_bspd: "Besonders schützenswerte Personendaten: {tags}. Diese Tags bleiben nur mit ausdrücklicher Zustimmung im Klartext.",
          vorliebe_tags_unbekannt: "Unbekannte Tags: {tags}",
          wirt_unbekannt: "Dieser Dienst antwortet nicht unter dem Namen «{wirt}». Lokal ist er unter 127.0.0.1 erreichbar; hinter einem Proxy gehört der Name in MASCHERA_WIRT.",
          regeln_kein_yaml: "Die Regeln sind kein gültiges YAML (Zeile {zeile}).",
          regel_zu_langsam: "Regel «{id}»: das Muster braucht {dauer} s für eine Probezeile. Das ist zu langsam, meist wegen geschachtelter Wiederholungen wie (a+)+.",
          regel_ohne_kennung: "Eine Regel hat keine Kennung (`id`).",
          regel_kennung: "Regel-Kennung «{id}»: nur Kleinbuchstaben, Ziffern und Unterstrich, 2 bis 32 Zeichen.",
          regel_platzhalter: "Regel «{id}»: der Platzhalter «{platzhalter}» muss aus 2 bis 20 Buchstaben oder Ziffern bestehen.",
          regel_woerter_leer: "Regel «{id}»: die Wortliste (`words`) ist leer.",
          regel_woerter_kurz: "Regel «{id}»: zu kurze Einträge ({kurz}). Unter {min} Zeichen treffen sie als Silbe überall.",
          regel_etiketten_leer: "Regel «{id}»: `labels` ist leer. Ohne Etikett träfe die Regel jede Zahl.",
          regel_wertform: "Regel «{id}»: die Wertform «{form}» gibt es nicht. Möglich: {moeglich}",
          regel_min_max: "Regel «{id}»: min/max unplausibel ({min}/{max}).",
          regel_muster_fehlt: "Regel «{id}»: das Muster (`pattern`) fehlt.",
          regel_muster_ungueltig: "Regel «{id}»: das Muster ist ungültig (bei Zeichen {stelle}).",
          regel_art: "Regel «{id}»: die Art «{art}» gibt es nicht. Möglich: {moeglich}",
          regeln_doppelt: "Diese Regel-Kennungen stehen doppelt: {kennungen}",
          regel_platzhalter_vergeben: "Platzhalter schon vergeben: {platzhalter}. Wähle einen anderen Namen.",
          msg_ohne_olefile: "Outlook-Nachrichten (.msg) lassen sich hier nicht lesen. In Outlook «Speichern unter» → .eml wählen.",
          pdf_ohne_pymupdf: "PDF lassen sich hier nicht lesen. Die PDF-Bibliothek fehlt.",
          docx_zu_gross: "Das Word-Dokument wäre ausgepackt {mb} MB gross; höchstens {hoechstens} MB werden gelesen.",
          docx_kaputt: "Keine lesbare .docx-Datei. Ältere .doc sind ein anderes Format.",
          docx_ohne_dokument: "Kein Word-Dokument. Vermutlich .odt, .pptx oder .xlsx mit falscher Endung.",
          docx_dtd: "Das Word-Dokument enthält eine DTD; das kommt in echten Word-Dateien nicht vor und wird nicht gelesen.",
          word_alt: "Das alte Word-Format (.doc) wird nicht gelesen. In Word oder LibreOffice als .docx speichern.",
        },
        leer: "Noch nichts maskiert." },
  fr: { uebernahme: "Reprise dans le prompt",
        einpflegen: "Appliquer le vocabulaire", kopiertK: "Copié",
        maskeWeg: "Retirer le masque",
        haeufig: "Fréquents",
        maskiertDurch: { model: "masqué par le modèle d’IA", propagation: "masqué, car la même valeur avait déjà été détectée", manuell: "masqué à la main", checksum: "confirmé par chiffre de contrôle et masqué", regex: "masqué par un motif", rule: "masqué par une règle personnelle" },
        maskiertSonst: "masqué",
        spracheW: "Langue",
        sicherheit: "sûr à {} %",
        knopfTipps: {
          "knopf-kopieren-orig": "Copier le texte original",
          "knopf-leeren-orig": "Vider le texte original",
          "knopf-bearbeiten": "Modifier le texte masqué",
          "knopf-herunter-mask": "Télécharger le texte masqué",
          "knopf-kopieren": "Copier le texte masqué",
          "knopf-kopieren-prompt": "Copier seulement le prompt",
          "knopf-leeren-prompt": "Vider le prompt",
          "knopf-einfuegen-antwort": "Coller la réponse",
          "knopf-leeren-antwort": "Vider la réponse",
          "knopf-herunter-final": "Télécharger le texte final",
          "knopf-leeren-final": "Vider le texte final",
          "knopf-final-kopieren": "Copier le texte final" },
        anwenden: "application en cours",
        suchLeeren: "Effacer la recherche", einpflegenZeile: "Application du vocabulaire",
        eingepflegtZeile: "Vocabulaire appliqué",
        davonMaskiert: "dont {} masqués", inDauer: "en {}", hinweiseInfo: "Remarques sur le traitement",
        dienstWeg: "Retirer le service",
        spalteSichern: "Enregistrer le modèle", spalteKopieren: "Copier le prompt", spalteLeeren: "Vider le prompt",
        vergroessern: "Agrandir", verkleinern: "Réduire",
        suchen: "Rechercher …", keinTreffer: "Aucun résultat",
        nichtMaskiert: "non masqué",
        bspdWeg: "Retirer vraiment le masque ?\n{} est une donnée sensible.",
        bspdSetzen: "Masquer comme {} ?\nC'est une donnée sensible.",
        einstT: "Réglages",
        schliessen: "Fermer", einstZu: "Enregistrer", einstZuRest: " et fermer", einstAbbrechen: "Annuler",
        zoneHinaus: "Quitte ton appareil", vokAlle: "Tous", ablauf: "Déroulement", schritte: ["Insérer le texte", "Vérifier", "Envoyer le prompt", "Insérer la réponse", "Retraduire"],
        allgemeinT: "Général",
        serverT: "Serveur",
        serverH: "Adresse et port du service de masquage local. Le texte ne quitte pas ton appareil. La vérification montre si le service répond.",
        adresse: "Adresse",
        port: "Port",
        pruefen: "Vérifier",
        neuStarten: "Enregistrer et redémarrer",
        nurSpeichern: "Enregistrer",
        startetNeu: "MASCHERA redémarre …",
        giltNachNeustart: "Enregistré. S'applique au prochain démarrage du service.",
        keinDienstDa: "Aucun MASCHERA ne répond à {}.",
        diensteT: "Services",
        diensteH: "Ces services figurent dans le menu à côté du bouton d’envoi. Lors de la copie, MASCHERA ouvre l’adresse du service choisi. Le dernier choisi reste enregistré pour les prochaines sessions.",
        hinzu: "Ajouter", vorgabenZurueck: "Rétablir les services par défaut",
        entfernen: "Supprimer",
        vokWeg: "Supprimer {} : le substitut disparaît de tout le texte et la valeur originale revient à sa place. Si tu transmets ensuite le texte, elle part sans masque.",
        fensterWort: "Ouvrir les services dans une nouvelle fenêtre plutôt qu’un onglet",
        trayWort: "À la fermeture, réduire dans la zone de notification",
        widgetWort: "Fenêtre étroite, toujours au premier plan",
        fensterHilfe: "Les deux prennent effet au prochain démarrage de l’application.",
        klartextT: "Types en clair",
        klartextStelle: "reconnu, reste en clair",
        klartextWort: "en clair",
        klartextH: "Choisis les types que MASCHERA ne doit jamais masquer. Ils restent reconnus, mais ne sont pas remplacés dans le texte. Cela vaut pour chaque document, jusqu’à ce que tu les désélectionnes.",
        regelnT: "Règles personnelles",
        regelnH: "Mots et motifs supplémentaires à masquer. En YAML. Les modifier modifie le résultat de mesure.",
        regelnSpeichern: "Enregistrer",
        pruefeLaeuft: "vérification …",
        dienstDa: "MASCHERA {v} répond · modèle {m}",
        falscherDienst: "Répond, mais ce n’est pas MASCHERA : {}",
        keinDienst: "Pas de réponse : {}",
        bspdFrage: "Laisser {} en clair durablement ?\nC'est une donnée sensible.",
        starrHinweis: "Reste en clair de toute façon.",
        unbekannteTags: "Types enregistrés qui n’existent plus : {}",
        einpflegen04: "Appliquer le vocabulaire", leerenA: "Vider",
        antwortPlatz: "Colle ici la réponse de ton outil d’IA (Ctrl+V) …",
        offenText: "{} substituts sont restés. À vérifier dans le texte final :",
        gutText: "{} substituts rétablis.",
        hinausT: "Prompt + texte masqué", trenner: "appliquer le prompt ci-dessus au texte suivant",
        sendenZu: "Tout copier et ouvrir {}", onlineWarnung: "Dans {}, tu travailles en ligne, sois prudent !", origPlatz: "Coller ici le texte original …", promptPlatz: "Ton prompt, p. ex. « Réponds à ce courriel poliment. »", hinausLeer: "D’abord « Reprise dans le prompt », ensuite tu verras ici ce qui sort.",
        spalteId: "ID",
        spalteWert: "Valeur d’origine", spalteTyp: "Type", anteilW: "Part masquée",
        keinVokabular: "Pas encore de vocabulaire. Il naît au masquage.",
        gruppen: { person: "Personne", herkunft: "Origine et appartenance",
          anschrift: "Adresse et lieu", erreichbar: "Contact",
          amtlich: "Numéros officiels", finanzen: "Finances",
          gesundheit: "Santé et assurance",
          verfahren: "Procédure, temps, organisation",
          nurerkannt: "Reconnu, jamais remplacé" },
        darstellungT: "Apparence", themaEtikett: "Couleurs",
        themaH: "« Automatique » suit le réglage de ton système.",
        themaAuto: "Automatique", themaHell: "Clair", themaDunkel: "Sombre",
        schriftT: "Police", schriftart: "Famille",
        schriftgroesse: "Taille",
        schriftH: "S'applique aux zones de texte : texte original, texte masqué, prompt et réponse.",
        schriftprobe: "Madame, Monsieur", vorschauE: "Aperçu",
        schriftSerif: "Avec empattement",
        schriftMono: "Largeur fixe",
        herunterladen: "Télécharger", hochladen: "Téléverser", einfuegen: "Coller",
        einfuegenHinweis: "Presse-papiers bloqué. Utilise Ctrl+V.",
        drop_ohne_datei: "Ce programme ne fournit aucun fichier. Glisse d’abord le message sur le bureau, puis ici.",
        mUpdate: "Rechercher des mises à jour", neuesteSucht: "Je demande à GitHub la version la plus récente …", neuesteAktuell: "Tu as la {aktuell}. C’est la version la plus récente.", neuesteNeu: "La version {neueste} est disponible. Tu as la {aktuell}.", neuesteSeite: "Vers la page de téléchargement",
        kAusschneiden: "Couper", kKopieren: "Copier", kEinfuegen: "Coller",
        menu: "Menu",
        mBrowser: "Ouvrir dans le navigateur", mHilfe: "Aide",
        mHilfeBald: "à venir", mWebseite: "maschera.ch",
        mGithub: "Code source sur GitHub", mDownload: "Télécharger",
        mFehler: "Signaler un problème",
        mImpressum: "Mentions légales", mKontakt: "Contact",
        finalKopieren: "Copier",
        vokHerunter: "Télécharger le vocabulaire",
        vokHoch: "Téléverser le vocabulaire",
        tplSichern: "Enregistrer",
        tplWaehlen: "Modèles ({})",
        tplSuchen: "Chercher …", tplNichts: "Aucun modèle ne correspond.",
        tplLeer: "Aucun modèle local enregistré",
        tplName: "Nom du modèle",
        tplWarnung: "Les modèles restent en clair sur le disque. "
          + "N'y écrivez pas de données personnelles.",
        tplWeg: "Supprimer le modèle « {} » ?", tplWegT: "Supprimer le modèle",
        tplGesichert: "Modèle « {} » enregistré.",
        tplFehler: "Modèle non enregistré : {}",
        sichernWarnung: "Le fichier contient {} valeurs originales en clair, "
          + "soit tout ce qui a été masqué ici. Il restera sans protection "
          + "dans le dossier de téléchargement. Enregistrer ?",
        vokGeladen: "{} entrées de vocabulaire chargées.",
        vokKaputt: "Le fichier n'est pas du JSON lisible. Rien de chargé.",
        frageJa: "Continuer",
        frageNein: "Annuler",
        frageOk: "Valider",
        neuladenFrage: "Recharger vraiment ?\n{} entrées de vocabulaire seront perdues.",
        verbindungWeg: "Pas de connexion au service MASCHERA. La requête n'est pas arrivée. Réessaie ; si cela ne suffit pas, redémarre MASCHERA.",
        httpFehler: "Le service MASCHERA a refusé la requête (erreur {status}).",
        vokFalsch: "Le fichier ne contient pas d'objet. Rien de chargé.",
        vokFremd: "Ce n'est pas un vocabulaire MASCHERA. Rien de chargé.",
        vokFassung: "Version inconnue {}. Cette édition lit la version 1.",
        vokKein: "Pas de dictionnaire dans le fichier. Rien de chargé.",
        vokSchluessel: "Marqueur non valable : {}. Rien de chargé.",
        vokWert: "La valeur de {} n'est pas une chaîne. Rien de chargé.",
        vokText: "Le texte masqué du fichier n'est pas une chaîne.",
       
        bearbeiten: "Modifier", bearbeitenFertig: "Terminé",
        bearbeitenHilfe: "Corriger le texte à la main. Laissez les marqueurs comme [FULLNAME_1] en place. Ils sont rétablis à la fin.",
        phUnbekannt: "Le dictionnaire ne connaît pas ces marqueurs : {liste}. Ils resteront tels quels.",
        phEntwertet: "{} marqueurs récupérés du balisage Markdown. Le service les avait échappés avec des barres obliques inverses.",
        phErgaenzt: "{} marqueurs cassés complétés : {liste}. Le dictionnaire les connaît. Le service avait avalé le crochet.",
        phKaputt: "Ces passages ressemblent à des marqueurs sans en être : {liste}. Ils ne seront PAS rétablis. À vérifier dans le texte.",
        fussLinks: "MASCHERA · traitement sur cet appareil · aucune connexion en ligne aux services IA", bereitS: "Prêt",
        orig: "Texte original", masked: "Masqué", run: "Masquer",
        fertig: "Texte final", prompt: "Assemblage du prompt", promptT: "Prompt",
        antwort: "Réponse", neu: "Nouveau",
        hundert: "100% local", einst: "Réglages",
        spruch: "Masque tes données avant de les partager ! · "
              + "Modèle local · LPD / RGPD",
        spruch1: "Masque tes données avant de les partager !",
        spruch2: "Modèle local · LPD / RGPD",
        laden: "Chargement du modèle local",
        keinStart: "Aucun serveur sur /api/zustand : {}",
        zeichenN: (n) => n + " caractères",
        eintraegeN: (n) => n + " entrées",
        leer05: "Le texte final apparaîtra ici dès que tu appliques le "
              + "vocabulaire.",
        leer02: "Rien de masqué. Colle un texte dans la colonne 1 puis "
              + "presse « Masquer ».",
        dropN: "Cliquer ou glisser ici un fichier texte ou un courriel", dropT: "Pris en charge : PDF, DOCX, TXT, MD, LOG, CSV, JSON et courriels EML, MSG ou MBOX. Un clic ouvre le choix de fichier.",
        laeuft: "en cours …", lWartet: "Préparation du texte …", lModell: "Fenêtre {} sur {}", lMaskieren: "Masquage, création du glossaire …", lRest: "encore environ {}", drop: "Glisser un fichier ou choisir",
        portFehlt: "Aucun port indiqué.",
        verwerfenVok: "Continuer vraiment ?\n{} entrées de vocabulaire seront perdues.",
        verwerfenText: "Continuer vraiment ?\nLe texte de la colonne 1 sera perdu.",
        neuAlles: "Veux-tu vraiment recommencer ?\nToutes les données seront réinitialisées !",
        beispiel: "Exemple", kopieren: "Copier",
        kopiert: "Copié", vokabular: "Vocabulaire",
        ohneModell: "SANS MODÈLE : seulement sommes de contrôle et motifs. "
                  + "Noms, dates et adresses restent en clair.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "SANS MODÈLE : seulement sommes de contrôle et motifs. Noms, dates et adresses restent EN CLAIR.",
          fenster: "Plus long qu’une fenêtre ({token} jetons). Traité par recouvrement.",
          wortgrenzen: "{anzahl} segments du modèle tombaient au milieu d’un mot et ont été étendus aux limites de mots.",
          mehrere_nachrichten: "{anzahl} messages dans le fichier. Seul le premier est traité.",
          vorlieben: "D’après les préférences enregistrées, en clair : {tags}",
          ohne_woerterbuch: "Sans dictionnaire : anonymisé définitivement, aucun retour possible.",
          eigene_regeln: "Règles personnelles appliquées ({anzahl}) : {namen}",
          schreibweise: "{platzhalter} ne diffère de {treffer} que par la casse. Non remplacé.",
          anhang_uebersprungen: "Pièce jointe ignorée : {name}",
          kein_textteil: "Le courriel n’a pas de partie texte, seulement {art}.",
          msg_ohne_textrumpf: "Le .msg n’a pas de corps en texte brut (seulement RTF ou HTML). Dans Outlook, choisir « Enregistrer sous » → .eml.",
          binaer_abgeschnitten: "{zeichen} caractères après la fin du texte ressemblaient à des données binaires et ont été omis.",
          nur_html: "seule la partie HTML est présente, dépouillée sommairement",
          kein_rumpf: "aucun corps de texte trouvé",
          pdf_ohne_text: "aucun texte dans le PDF. Probablement un scan. Sans OCR le filtre ne voit rien, et un résultat vide ne signifie PAS qu’il n’y a pas de données personnelles.",
          pdf_seiten: "{anzahl} pages, la mise en page est perdue à la lecture",
          tabellen: "{anzahl} tableaux, lus ligne par ligne",
          nicht_gelesen: "NON lu : {teile}. C’est souvent là que figure l’expéditeur",
          docx_leer: "aucun texte dans le document. Un résultat vide ne signifie PAS qu’il n’y a pas de données personnelles.",
          kodierung: "Encodage {kodierung}",
          bom: "marque d’ordre des octets en tête, supprimée",
          t_kopfzeilen: "En-têtes",
          t_fusszeilen: "Pieds de page",
          t_kommentare: "Commentaires",
          t_fussnoten: "Notes de bas de page",
        },
        meldungen: {
          adresse_fehlt: "Le champ `adresse` est absent ou vide.",
          adresse_zu_lang: "Adresse de plus de {hoechstens} caractères.",
          datei_ohne_text: "Le fichier n’a donné aucun texte.",
          datei_unlesbar: "Fichier illisible : endommagé ou format non pris en charge.",
          datei_zu_gross: "Fichier de plus de {mb} Mo.",
          dienst_kein_objekt: "Le service {nummer} n’est pas un objet.",
          dienst_kennung_doppelt: "Identifiant attribué deux fois : {kennung}",
          dienst_ohne_adresse: "Le service {name} n’a pas d’adresse.",
          dienst_ohne_namen: "Le service {nummer} n’a pas de nom.",
          dienst_schema: "Service {name} : uniquement https:// ou http://, pas {adresse}",
          dienste_keine_liste: "Le champ `dienste` n’est pas une liste.",
          dienste_leer: "Il faut au moins un service. Sinon « Copier et ouvrir » ne sait pas où aller.",
          dienste_zu_viele: "{hoechstens} services au maximum.",
          einst_kein_objekt: "Pas un objet.",
          einstellungen_gespeichert: "Enregistré.",
          feld_klartext: "Le champ `klartext` est absent ou n’est pas une liste de types.",
          feld_text: "Le champ `text` est absent ou n’est pas du texte.",
          feld_woerterbuch: "Le champ `woerterbuch` est absent ou n’est pas un objet.",
          feld_yaml: "Le champ `yaml` est absent ou n’est pas du texte.",
          fenster_kein_wahrheitswert: "Le champ `eigenes_fenster` n’est pas un booléen.",
          format_unbekannt: "Le format {endung} n’est pas lu. Possible : {moeglich}",
          keine_datei: "Aucun fichier reçu.",
          klartext_gelesen: "Ces types restent durablement en clair.",
          klartext_gespeichert: "Enregistré. Ces types restent durablement en clair, dans les documents à venir également.",
          nicht_gespeichert: "Non enregistré. Le fichier du dossier de réglages n'a pas pu être écrit.",
          ohne_tags_unbekannt: "Types inconnus dans `ohne` : {tags}",
          port_ausserhalb: "Port hors de 1–65535 : {port}",
          regeldatei_fehlerhaft: "Le fichier de règles est défectueux et n'a pas été appliqué.",
          regeln_abgelehnt: "Règles refusées. Le fichier contient une erreur.",
          regeln_gelesen: "Modifier les règles, c’est modifier le résultat de mesure.",
          regeln_veraltete_schluessel: "Ce fichier de règles utilise des clés obsolètes. Elles restent lues ou sont ignorées : {umbenennungen}",
          regeln_gespeichert: "Enregistré. Le résultat de mesure change en conséquence.",
          neueste_begrenzt: "GitHub limite les requêtes en ce moment. Les 60 par heure de ton réseau sont épuisées. Réessaie dans une heure, ou va directement sur la page de téléchargement.",
          neueste_nicht_erreichbar: "GitHub est injoignable : pas de réseau, ou le serveur n’a pas le droit de sortir. La version la plus récente se trouve sur la page de téléchargement.",
          neueste_unlesbar: "GitHub a répondu, mais sans numéro de version lisible. La version la plus récente se trouve sur la page de téléchargement.",
          regeln_unlesbar: "Règles illisibles. Un champ n'a pas la bonne forme.",
          tray_kein_wahrheitswert: "Le champ `tray` n’est pas un booléen.",
          fenstermodus_unbekannt: "Le mode de fenêtre {wert} n’existe pas. Possible : {moeglich}",
          thema_unbekannt: "Le thème {wert} n’existe pas. Possible : {moeglich}",
          schriftart_unbekannt: "La police {wert} n’existe pas. Possible : {moeglich}",
          schriftgroesse_unbekannt: "La taille {wert} n’existe pas. Possible : {moeglich}",
          sprache_unbekannt: "La langue {sprache} n’existe pas. Possible : {moeglich}",
          oberflaechensprache_unbekannt: "La langue d’interface {wert} n’existe pas. Possible : {moeglich}",
          text_leer: "Le texte est vide.",
          vorlage_kein_objekt: "Le modèle {nummer} n’est pas un objet.",
          vorlage_name_doppelt: "Nom attribué deux fois : {name}",
          vorlage_name_zu_lang: "Nom de plus de {hoechstens} caractères : {name}",
          vorlage_ohne_namen: "Le modèle {nummer} n’a pas de nom.",
          vorlage_ohne_text: "Le modèle {nummer} ({name}) n’a pas de texte.",
          vorlage_text_zu_lang: "Le modèle {name} dépasse {hoechstens} caractères.",
          vorlagen_feld_fehlt: "Le champ `vorlagen` est absent ou n’est pas une liste.",
          vorlagen_klartext: "Les modèles restent en clair sur le disque. N’y écrivez pas de données personnelles.",
          vorlagen_zu_viele: "{hoechstens} modèles au maximum.",
          vorliebe_bspd: "Données personnelles sensibles : {tags}. Ces types ne restent en clair qu’avec un accord explicite.",
          vorliebe_tags_unbekannt: "Types inconnus : {tags}",
          wirt_unbekannt: "Ce service ne répond pas sous le nom « {wirt} ». En local, il est joignable sur 127.0.0.1 ; derrière un proxy, le nom se met dans MASCHERA_WIRT.",
          regeln_kein_yaml: "Les règles ne sont pas du YAML valide (ligne {zeile}).",
          regel_zu_langsam: "Règle « {id} » : le motif prend {dauer} s pour une ligne d'essai. C'est trop lent, souvent à cause de répétitions imbriquées comme (a+)+.",
          regel_ohne_kennung: "Une règle n'a pas d'identifiant (`id`).",
          regel_kennung: "Identifiant « {id} » : seulement minuscules, chiffres et trait de soulignement, 2 à 32 caractères.",
          regel_platzhalter: "Règle « {id} » : l'espace réservé « {platzhalter} » doit compter 2 à 20 lettres ou chiffres.",
          regel_woerter_leer: "Règle « {id} » : la liste de mots (`words`) est vide.",
          regel_woerter_kurz: "Règle « {id} » : entrées trop courtes ({kurz}). En dessous de {min} caractères, elles touchent partout comme syllabe.",
          regel_etiketten_leer: "Règle « {id} » : `labels` est vide. Sans étiquette, la règle toucherait n'importe quel nombre.",
          regel_wertform: "Règle « {id} » : la forme de valeur « {form} » n'existe pas. Possible : {moeglich}",
          regel_min_max: "Règle « {id} » : min/max invraisemblables ({min}/{max}).",
          regel_muster_fehlt: "Règle « {id} » : le motif (`pattern`) manque.",
          regel_muster_ungueltig: "Règle « {id} » : le motif n'est pas valide (au caractère {stelle}).",
          regel_art: "Règle « {id} » : le type « {art} » n'existe pas. Possible : {moeglich}",
          regeln_doppelt: "Ces identifiants de règle figurent deux fois : {kennungen}",
          regel_platzhalter_vergeben: "Espace réservé déjà utilisé : {platzhalter}. Choisis un autre nom.",
          msg_ohne_olefile: "Les messages Outlook (.msg) ne peuvent pas être lus ici. Dans Outlook, « Enregistrer sous » → .eml.",
          pdf_ohne_pymupdf: "Les PDF ne peuvent pas être lus ici. La bibliothèque PDF manque.",
          docx_zu_gross: "Le document Word ferait {mb} Mo une fois décompressé ; au plus {hoechstens} Mo sont lus.",
          docx_kaputt: "Pas de fichier .docx lisible. Les anciens .doc sont un autre format.",
          docx_ohne_dokument: "Pas un document Word. Sans doute un .odt, .pptx ou .xlsx mal nommé.",
          docx_dtd: "Le document Word contient une DTD ; cela n'existe pas dans un vrai fichier Word et n'est pas lu.",
          word_alt: "L'ancien format Word (.doc) n'est pas lu. Enregistre-le en .docx dans Word ou LibreOffice.",
        },
        leer: "Rien de masqué pour l’instant." },
  it: { uebernahme: "Riprendi nel prompt",
        einpflegen: "Applica il vocabolario", kopiertK: "Copiato",
        maskeWeg: "Togli la maschera",
        haeufig: "Frequenti",
        maskiertDurch: { model: "mascherato dal modello di IA", propagation: "mascherato perché lo stesso valore era già stato rilevato", manuell: "mascherato a mano", checksum: "confermato da cifra di controllo e mascherato", regex: "mascherato da un modello di testo", rule: "mascherato da una regola personale" },
        maskiertSonst: "mascherato",
        spracheW: "Lingua",
        sicherheit: "sicuro al {} %",
        knopfTipps: {
          "knopf-kopieren-orig": "Copia il testo originale",
          "knopf-leeren-orig": "Svuota il testo originale",
          "knopf-bearbeiten": "Modifica il testo mascherato",
          "knopf-herunter-mask": "Scarica il testo mascherato",
          "knopf-kopieren": "Copia il testo mascherato",
          "knopf-kopieren-prompt": "Copia solo il prompt",
          "knopf-leeren-prompt": "Svuota il prompt",
          "knopf-einfuegen-antwort": "Incolla la risposta",
          "knopf-leeren-antwort": "Svuota la risposta",
          "knopf-herunter-final": "Scarica il testo finale",
          "knopf-leeren-final": "Svuota il testo finale",
          "knopf-final-kopieren": "Copia il testo finale" },
        anwenden: "in applicazione",
        suchLeeren: "Svuota la ricerca", einpflegenZeile: "Applicazione del vocabolario",
        eingepflegtZeile: "Vocabolario applicato",
        davonMaskiert: "di cui {} mascherati", inDauer: "in {}", hinweiseInfo: "Note sull’elaborazione",
        dienstWeg: "Rimuovi il servizio",
        spalteSichern: "Salva il modello", spalteKopieren: "Copia il prompt", spalteLeeren: "Svuota il prompt",
        vergroessern: "Ingrandisci", verkleinern: "Riduci",
        suchen: "Cerca …", keinTreffer: "Nessun risultato",
        nichtMaskiert: "non mascherato",
        bspdWeg: "Togliere davvero la maschera?\n{} è un dato personale degno di particolare protezione.",
        bspdSetzen: "Mascherare come {}?\nÈ un dato degno di particolare protezione.",
        einstT: "Impostazioni",
        schliessen: "Chiudi", einstZu: "Salva", einstZuRest: " e chiudi", einstAbbrechen: "Annulla",
        zoneHinaus: "Lascia il tuo dispositivo", vokAlle: "Tutti", ablauf: "Procedura", schritte: ["Inserire il testo", "Verificare", "Inviare il prompt", "Inserire la risposta", "Ritradurre"],
        allgemeinT: "Generale",
        serverT: "Server",
        serverH: "Indirizzo e porta del servizio di mascheratura locale. Il testo non lascia il dispositivo. La verifica mostra se il servizio risponde.",
        adresse: "Indirizzo",
        port: "Porta",
        pruefen: "Verifica",
        neuStarten: "Salva e riavvia",
        nurSpeichern: "Salva",
        startetNeu: "MASCHERA si riavvia …",
        giltNachNeustart: "Salvato. Vale dal prossimo avvio del servizio.",
        keinDienstDa: "MASCHERA non risponde sul IP {}",
        diensteT: "Servizi",
        diensteH: "Questi servizi compaiono nel menu accanto al pulsante di invio. Alla copia MASCHERA apre l’indirizzo del servizio scelto. L’ultimo scelto resta salvato anche per le sessioni future.",
        hinzu: "Aggiungi", vorgabenZurueck: "Ripristina i servizi predefiniti",
        entfernen: "Rimuovi",
        vokWeg: "Rimuovi {}: il segnaposto scompare da tutto il testo e al suo posto torna il valore originale. Se poi inoltri il testo, esce senza maschera.",
        fensterWort: "Aprire i servizi in una nuova finestra invece che in una scheda",
        trayWort: "Alla chiusura, riduci nell’area di notifica",
        widgetWort: "Finestra stretta, sempre in primo piano",
        fensterHilfe: "Entrambi hanno effetto al prossimo avvio dell’applicazione.",
        klartextT: "Tipi in chiaro",
        klartextStelle: "riconosciuto, resta in chiaro",
        klartextWort: "in chiaro",
        klartextH: "Scegli i tipi che MASCHERA non deve mai mascherare. Vengono comunque riconosciuti, ma restano invariati nel testo. Vale per ogni documento, finché non li deselezioni.",
        regelnT: "Regole proprie",
        regelnH: "Parole e schemi aggiuntivi da mascherare. In YAML. Modificarle cambia il risultato della misura.",
        regelnSpeichern: "Salva regole",
        pruefeLaeuft: "verifica in corso …",
        dienstDa: "MASCHERA {v} risponde · modello {m}",
        falscherDienst: "Risponde, ma non è MASCHERA: {}",
        keinDienst: "Nessuna risposta: {}",
        bspdFrage: "Lasciare {} in chiaro?\nÈ un dato personale degno di particolare protezione.",
        starrHinweis: "Resta comunque in chiaro.",
        unbekannteTags: "Tipi salvati che non esistono più: {}",
        einpflegen04: "Applica il vocabolario", leerenA: "Svuota",
        antwortPlatz: "Incolla qui la risposta del tuo strumento IA (Ctrl+V) …",
        offenText: "{} segnaposto sono rimasti. Da controllare nel testo finale:",
        gutText: "{} segnaposto ripristinati.",
        hinausT: "Prompt + testo mascherato", trenner: "applica il prompt qui sopra al testo seguente",
        sendenZu: "Copia tutto e apri {}", onlineWarnung: "In {} lavori online, fai attenzione!", origPlatz: "Incolla qui il testo originale …", promptPlatz: "Il tuo prompt, p. es. «Rispondi a questa e-mail gentilmente.»", hinausLeer: "Prima «Riprendi nel prompt», poi qui vedrai cosa esce.",
        spalteId: "ID",
        spalteWert: "Valore originale", spalteTyp: "Tipo", anteilW: "Quota mascherata",
        keinVokabular: "Nessun vocabolario. Nasce con la mascheratura.",
        gruppen: { person: "Persona", herkunft: "Origine e appartenenza",
          anschrift: "Indirizzo e luogo", erreichbar: "Contatti",
          amtlich: "Numeri ufficiali", finanzen: "Finanze",
          gesundheit: "Salute e assicurazione",
          verfahren: "Procedura, tempo, organizzazione",
          nurerkannt: "Riconosciuto, mai sostituito" },
        darstellungT: "Aspetto", themaEtikett: "Colori",
        themaH: "«Automatico» segue l’impostazione del tuo sistema.",
        themaAuto: "Automatico", themaHell: "Chiaro", themaDunkel: "Scuro",
        schriftT: "Carattere", schriftart: "Famiglia",
        schriftgroesse: "Dimensione",
        schriftH: "Vale per le aree di testo: testo originale, testo mascherato, prompt e risposta.",
        schriftprobe: "Gentili signore, egregi signori", vorschauE: "Anteprima",
        schriftSerif: "Con grazie",
        schriftMono: "Larghezza fissa",
        herunterladen: "Scarica", hochladen: "Carica", einfuegen: "Incolla",
        einfuegenHinweis: "Appunti bloccati. Usa Ctrl+V.",
        drop_ohne_datei: "Da questo programma non arriva alcun file. Trascina prima il messaggio sulla scrivania, poi qui.",
        mUpdate: "Cerca aggiornamenti", neuesteSucht: "Chiedo a GitHub la versione più recente …", neuesteAktuell: "Hai la {aktuell}. È la versione più recente.", neuesteNeu: "È disponibile la versione {neueste}. Tu hai la {aktuell}.", neuesteSeite: "Alla pagina di download",
        kAusschneiden: "Taglia", kKopieren: "Copia", kEinfuegen: "Incolla",
        menu: "Menu",
        mBrowser: "Apri nel browser", mHilfe: "Aiuto",
        mHilfeBald: "in arrivo", mWebseite: "maschera.ch",
        mGithub: "Codice sorgente su GitHub", mDownload: "Scarica",
        mFehler: "Segnala un problema",
        mImpressum: "Note legali", mKontakt: "Contatto",
        finalKopieren: "Copia",
        vokHerunter: "Scarica il vocabolario",
        vokHoch: "Carica il vocabolario",
        tplSichern: "Salva",
        tplWaehlen: "Modelli ({})",
        tplSuchen: "Cerca …", tplNichts: "Nessun modello corrisponde.",
        tplLeer: "Nessun modello locale salvato",
        tplName: "Nome del modello",
        tplWarnung: "I modelli restano in chiaro sul disco. "
          + "Non scrivervi dati personali.",
        tplWeg: "Eliminare il modello «{}»?", tplWegT: "Elimina il modello",
        tplGesichert: "Modello «{}» salvato.",
        tplFehler: "Modello non salvato: {}",
        sichernWarnung: "Il file contiene {} valori originali in chiaro, "
          + "cioè tutto ciò che è stato mascherato. Resterà senza protezione "
          + "nella cartella dei download. Salvare?",
        vokGeladen: "{} voci di vocabolario caricate.",
        vokKaputt: "Il file non è JSON leggibile. Non caricato nulla.",
        frageJa: "Continua",
        frageNein: "Annulla",
        frageOk: "Conferma",
        neuladenFrage: "Ricaricare davvero?\n{} voci di vocabolario andranno perse.",
        verbindungWeg: "Nessuna connessione al servizio MASCHERA. La richiesta non è arrivata. Riprova; se non basta, riavvia MASCHERA.",
        httpFehler: "Il servizio MASCHERA ha rifiutato la richiesta (errore {status}).",
        vokFalsch: "Il file non contiene un oggetto. Non caricato nulla.",
        vokFremd: "Non è un vocabolario MASCHERA. Non caricato nulla.",
        vokFassung: "Versione sconosciuta {}. Questa edizione legge la 1.",
        vokKein: "Nessun dizionario nel file. Non caricato nulla.",
        vokSchluessel: "Segnaposto non valido: {}. Non caricato nulla.",
        vokWert: "Il valore di {} non è una stringa. Non caricato nulla.",
        vokText: "Il testo mascherato nel file non è una stringa.",
       
        bearbeiten: "Modifica", bearbeitenFertig: "Fatto",
        bearbeitenHilfe: "Correggere il testo a mano. Lasciare i segnaposto come [FULLNAME_1]. Vengono ripristinati alla fine.",
        phUnbekannt: "Il dizionario non conosce questi segnaposto: {liste}. Resteranno invariati.",
        phEntwertet: "{} segnaposto recuperati dalla marcatura Markdown. Il servizio li aveva protetti con barre rovesciate.",
        phErgaenzt: "{} segnaposto spezzati completati: {liste}. Il dizionario li conosce. Il servizio aveva inghiottito la parentesi.",
        phKaputt: "Questi punti sembrano segnaposto ma non lo sono: {liste}. NON verranno ripristinati. Da controllare nel testo.",
        fussLinks: "MASCHERA · elaborazione su questo dispositivo · nessuna connessione online ai servizi IA", bereitS: "Pronto",
        orig: "Testo originale", masked: "Mascherato", run: "Maschera",
        fertig: "Testo finale", prompt: "Composizione del prompt", promptT: "Prompt",
        antwort: "Risposta", neu: "Nuovo",
        hundert: "100% locale", einst: "Impostazioni",
        spruch: "Maschera i tuoi dati prima di condividerli! · "
              + "Modello locale · LPD / GDPR",
        spruch1: "Maschera i tuoi dati prima di condividerli!",
        spruch2: "Modello locale · LPD / GDPR",
        laden: "Caricamento del modello locale",
        keinStart: "Nessun server su /api/zustand: {}",
        zeichenN: (n) => n + " caratteri",
        eintraegeN: (n) => n + " voci",
        leer05: "Il testo finale apparirà qui appena applichi il vocabolario.",
        leer02: "Niente mascherato. Incolla un testo nella colonna 1 e premi "
              + "«Maschera».",
        dropN: "Clicca o trascina qui un file di testo o un’e-mail", dropT: "Supportati: PDF, DOCX, TXT, MD, LOG, CSV, JSON ed e-mail EML, MSG o MBOX. Un clic apre la scelta del file.",
        laeuft: "in corso …", lWartet: "Preparazione del testo …", lModell: "Finestra {} di {}", lMaskieren: "Mascheratura, creazione del glossario …", lRest: "ancora circa {}", drop: "Trascina un file o scegli",
        portFehlt: "Nessuna porta indicata.",
        verwerfenVok: "Continuare davvero?\n{} voci di vocabolario andranno perse.",
        verwerfenText: "Continuare davvero?\nIl testo nella colonna 1 andrà perso.",
        neuAlles: "Vuoi davvero ricominciare?\nTutti i dati verranno azzerati!",
        beispiel: "Esempio", kopieren: "Copia",
        kopiert: "Copiato", vokabular: "Vocabolario",
        ohneModell: "SENZA MODELLO: solo checksum e pattern. Nomi, date e "
                  + "indirizzi restano in chiaro.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "SENZA MODELLO: solo checksum e pattern. Nomi, date e indirizzi restano IN CHIARO.",
          fenster: "Più lungo di una finestra ({token} token). Elaborato con sovrapposizione.",
          wortgrenzen: "{anzahl} intervalli del modello cadevano dentro una parola e sono stati estesi ai confini di parola.",
          mehrere_nachrichten: "{anzahl} messaggi nel file. Viene elaborato solo il primo.",
          vorlieben: "Dalle preferenze salvate, in chiaro: {tags}",
          ohne_woerterbuch: "Senza dizionario: anonimizzato definitivamente, nessun ritorno possibile.",
          eigene_regeln: "Regole proprie applicate ({anzahl}): {namen}",
          schreibweise: "{platzhalter} differisce da {treffer} solo per maiuscole e minuscole. Non sostituito.",
          anhang_uebersprungen: "Allegato saltato: {name}",
          kein_textteil: "L’e-mail non ha una parte di testo, solo {art}.",
          msg_ohne_textrumpf: "Il .msg non ha un corpo in testo semplice (solo RTF o HTML). In Outlook scegliere «Salva con nome» → .eml.",
          binaer_abgeschnitten: "{zeichen} caratteri dopo la fine del testo sembravano dati binari e sono stati omessi.",
          nur_html: "presente solo la parte HTML, ripulita sommariamente",
          kein_rumpf: "nessun corpo di testo trovato",
          pdf_ohne_text: "nessun testo nel PDF. Probabilmente una scansione. Senza OCR il filtro non vede nulla, e un esito vuoto NON significa che non ci siano dati personali.",
          pdf_seiten: "{anzahl} pagine, il layout va perso in lettura",
          tabellen: "{anzahl} tabelle, lette riga per riga",
          nicht_gelesen: "NON letto: {teile}. Lì nelle lettere si trova spesso il mittente",
          docx_leer: "nessun testo nel documento. Un esito vuoto NON significa che non ci siano dati personali.",
          kodierung: "Codifica {kodierung}",
          bom: "byte order mark all’inizio del testo, rimosso",
          t_kopfzeilen: "Intestazioni",
          t_fusszeilen: "Piè di pagina",
          t_kommentare: "Commenti",
          t_fussnoten: "Note a piè di pagina",
        },
        meldungen: {
          adresse_fehlt: "Il campo `adresse` manca o è vuoto.",
          adresse_zu_lang: "Indirizzo più lungo di {hoechstens} caratteri.",
          datei_ohne_text: "Il file non ha prodotto alcun testo.",
          datei_unlesbar: "File illeggibile: danneggiato o formato non supportato.",
          datei_zu_gross: "File più grande di {mb} MB.",
          dienst_kein_objekt: "Il servizio {nummer} non è un oggetto.",
          dienst_kennung_doppelt: "Identificativo assegnato due volte: {kennung}",
          dienst_ohne_adresse: "Il servizio {name} non ha indirizzo.",
          dienst_ohne_namen: "Il servizio {nummer} non ha nome.",
          dienst_schema: "Servizio {name}: solo https:// o http://, non {adresse}",
          dienste_keine_liste: "Il campo `dienste` non è un elenco.",
          dienste_leer: "Serve almeno un servizio, altrimenti «Copia e apri» non sa dove andare.",
          dienste_zu_viele: "Al massimo {hoechstens} servizi.",
          einst_kein_objekt: "Non è un oggetto.",
          einstellungen_gespeichert: "Salvato.",
          feld_klartext: "Il campo `klartext` manca o non è un elenco di tipi.",
          feld_text: "Il campo `text` manca o non è testo.",
          feld_woerterbuch: "Il campo `woerterbuch` manca o non è un oggetto.",
          feld_yaml: "Il campo `yaml` manca o non è testo.",
          fenster_kein_wahrheitswert: "Il campo `eigenes_fenster` non è un valore booleano.",
          format_unbekannt: "Il formato {endung} non viene letto. Possibili: {moeglich}",
          keine_datei: "Nessun file ricevuto.",
          klartext_gelesen: "Questi tipi restano permanentemente in chiaro.",
          klartext_gespeichert: "Salvato. Questi tipi restano permanentemente in chiaro, anche nei documenti futuri.",
          nicht_gespeichert: "Non salvato. Impossibile scrivere il file nella cartella delle impostazioni.",
          ohne_tags_unbekannt: "Tipi sconosciuti in `ohne`: {tags}",
          port_ausserhalb: "Porta fuori da 1–65535: {port}",
          regeldatei_fehlerhaft: "Il file delle regole è difettoso e non è stato applicato.",
          regeln_abgelehnt: "Regole rifiutate. Il file contiene un errore.",
          regeln_gelesen: "Chi cambia le regole cambia il risultato della misurazione.",
          regeln_veraltete_schluessel: "Questo file di regole usa chiavi obsolete. Vengono ancora lette o ignorate: {umbenennungen}",
          regeln_gespeichert: "Salvato. Il risultato della misurazione cambia di conseguenza.",
          neueste_begrenzt: "GitHub sta limitando le richieste. Le 60 all’ora della tua rete sono esaurite. Riprova tra un’ora, oppure vai direttamente alla pagina di download.",
          neueste_nicht_erreichbar: "GitHub non è raggiungibile: niente rete, oppure il server non può uscire. La versione più recente è nella pagina di download.",
          neueste_unlesbar: "GitHub ha risposto, ma senza un numero di versione leggibile. La versione più recente è nella pagina di download.",
          regeln_unlesbar: "Regole illeggibili. Un campo ha la forma sbagliata.",
          tray_kein_wahrheitswert: "Il campo `tray` non è un valore booleano.",
          fenstermodus_unbekannt: "La modalità finestra {wert} non esiste. Possibili: {moeglich}",
          thema_unbekannt: "Il tema {wert} non esiste. Possibili: {moeglich}",
          schriftart_unbekannt: "Il carattere {wert} non esiste. Possibili: {moeglich}",
          schriftgroesse_unbekannt: "La dimensione {wert} non esiste. Possibili: {moeglich}",
          sprache_unbekannt: "La lingua {sprache} non esiste. Possibili: {moeglich}",
          oberflaechensprache_unbekannt: "La lingua dell’interfaccia {wert} non esiste. Possibili: {moeglich}",
          text_leer: "Il testo è vuoto.",
          vorlage_kein_objekt: "Il modello {nummer} non è un oggetto.",
          vorlage_name_doppelt: "Nome assegnato due volte: {name}",
          vorlage_name_zu_lang: "Nome più lungo di {hoechstens} caratteri: {name}",
          vorlage_ohne_namen: "Il modello {nummer} non ha nome.",
          vorlage_ohne_text: "Il modello {nummer} ({name}) non ha testo.",
          vorlage_text_zu_lang: "Il modello {name} supera {hoechstens} caratteri.",
          vorlagen_feld_fehlt: "Il campo `vorlagen` manca o non è un elenco.",
          vorlagen_klartext: "I modelli restano in chiaro sul disco. Non scrivervi dati personali.",
          vorlagen_zu_viele: "Al massimo {hoechstens} modelli.",
          vorliebe_bspd: "Dati personali degni di particolare protezione: {tags}. Questi tipi restano in chiaro solo con consenso esplicito.",
          vorliebe_tags_unbekannt: "Tipi sconosciuti: {tags}",
          wirt_unbekannt: "Questo servizio non risponde con il nome «{wirt}». In locale è raggiungibile su 127.0.0.1; dietro un proxy il nome va in MASCHERA_WIRT.",
          regeln_kein_yaml: "Le regole non sono YAML valido (riga {zeile}).",
          regel_zu_langsam: "Regola «{id}»: il modello impiega {dauer} s per una riga di prova. È troppo lento, spesso per ripetizioni annidate come (a+)+.",
          regel_ohne_kennung: "Una regola non ha identificativo (`id`).",
          regel_kennung: "Identificativo «{id}»: solo minuscole, cifre e trattino basso, da 2 a 32 caratteri.",
          regel_platzhalter: "Regola «{id}»: il segnaposto «{platzhalter}» deve avere da 2 a 20 lettere o cifre.",
          regel_woerter_leer: "Regola «{id}»: l'elenco di parole (`words`) è vuoto.",
          regel_woerter_kurz: "Regola «{id}»: voci troppo corte ({kurz}). Sotto i {min} caratteri colpiscono ovunque come sillaba.",
          regel_etiketten_leer: "Regola «{id}»: `labels` è vuoto. Senza etichetta la regola colpirebbe qualsiasi numero.",
          regel_wertform: "Regola «{id}»: la forma di valore «{form}» non esiste. Possibile: {moeglich}",
          regel_min_max: "Regola «{id}»: min/max non plausibili ({min}/{max}).",
          regel_muster_fehlt: "Regola «{id}»: manca il modello (`pattern`).",
          regel_muster_ungueltig: "Regola «{id}»: il modello non è valido (al carattere {stelle}).",
          regel_art: "Regola «{id}»: il tipo «{art}» non esiste. Possibile: {moeglich}",
          regeln_doppelt: "Questi identificativi di regola compaiono due volte: {kennungen}",
          regel_platzhalter_vergeben: "Segnaposto già assegnato: {platzhalter}. Scegli un altro nome.",
          msg_ohne_olefile: "I messaggi Outlook (.msg) non si possono leggere qui. In Outlook «Salva con nome» → .eml.",
          pdf_ohne_pymupdf: "I PDF non si possono leggere qui. Manca la libreria PDF.",
          docx_zu_gross: "Il documento Word sarebbe di {mb} MB una volta decompresso; se ne leggono al massimo {hoechstens} MB.",
          docx_kaputt: "Nessun file .docx leggibile. I vecchi .doc sono un altro formato.",
          docx_ohne_dokument: "Non è un documento Word. Probabilmente .odt, .pptx o .xlsx con estensione sbagliata.",
          docx_dtd: "Il documento Word contiene una DTD; nei veri file Word non esiste e non viene letto.",
          word_alt: "Il vecchio formato Word (.doc) non viene letto. Salvalo come .docx in Word o LibreOffice.",
        },
        leer: "Niente mascherato finora." },
  en: { uebernahme: "Take into prompt",
        einpflegen: "Apply vocabulary", kopiertK: "Copied",
        maskeWeg: "Remove mask",
        haeufig: "Frequent",
        maskiertDurch: { model: "masked by the AI model", propagation: "masked because the same value was already detected", manuell: "masked by hand", checksum: "confirmed by check digit and masked", regex: "masked by a pattern", rule: "masked by a custom rule" },
        maskiertSonst: "masked",
        spracheW: "Language",
        sicherheit: "{}% certain",
        knopfTipps: {
          "knopf-kopieren-orig": "Copy original text",
          "knopf-leeren-orig": "Clear original text",
          "knopf-bearbeiten": "Edit masked text",
          "knopf-herunter-mask": "Download masked text",
          "knopf-kopieren": "Copy masked text",
          "knopf-kopieren-prompt": "Copy prompt only",
          "knopf-leeren-prompt": "Clear prompt",
          "knopf-einfuegen-antwort": "Paste answer",
          "knopf-leeren-antwort": "Clear answer",
          "knopf-herunter-final": "Download final text",
          "knopf-leeren-final": "Clear final text",
          "knopf-final-kopieren": "Copy final text" },
        anwenden: "applying",
        suchLeeren: "Clear search", einpflegenZeile: "Applying vocabulary",
        eingepflegtZeile: "Vocabulary applied",
        davonMaskiert: "{} of them masked", inDauer: "in {}", hinweiseInfo: "Notes on this run",
        dienstWeg: "Remove service",
        spalteSichern: "Save template", spalteKopieren: "Copy prompt", spalteLeeren: "Clear prompt",
        vergroessern: "Enlarge", verkleinern: "Shrink",
        suchen: "Search …", keinTreffer: "No match",
        nichtMaskiert: "not masked",
        bspdWeg: "Really remove the mask?\n{} is sensitive personal data.",
        bspdSetzen: "Mask as {}?\nThis is sensitive personal data.",
        einstT: "Settings",
        schliessen: "Close", einstZu: "Save", einstZuRest: " & close", einstAbbrechen: "Cancel",
        zoneHinaus: "Leaves your device", vokAlle: "All", ablauf: "Steps", schritte: ["Insert text", "Check", "Send prompt", "Insert answer", "Translate back"],
        allgemeinT: "General",
        serverT: "Server",
        serverH: "Address and port of the local masking service. The text never leaves your device. The check shows whether the service responds.",
        adresse: "Address",
        port: "Port",
        pruefen: "Check",
        neuStarten: "Save & restart",
        nurSpeichern: "Save",
        startetNeu: "MASCHERA is restarting …",
        giltNachNeustart: "Saved. Applies from the next start of the service.",
        keinDienstDa: "No MASCHERA answers at {}.",
        diensteT: "Services",
        diensteH: "These services appear in the menu next to the send button. When you copy, MASCHERA opens the address of the chosen service. The last one you chose is kept for future sessions.",
        hinzu: "Add", vorgabenZurueck: "Restore defaults",
        entfernen: "Remove",
        vokWeg: "Remove {}: the placeholder disappears from the whole text and the original value is back in its place. If you pass the text on afterwards, it goes out unmasked.",
        fensterWort: "Open services in a new window rather than a tab",
        trayWort: "On close, minimise to the tray instead of quitting",
        widgetWort: "Narrow window, always on top",
        fensterHilfe: "Both take effect after restarting the application.",
        klartextT: "Plaintext types",
        klartextStelle: "detected, stays in plain text",
        klartextWort: "in the clear",
        klartextH: "Choose the types MASCHERA should never mask. They are still detected, but stay as they are in the text. This applies to every document until you deselect them.",
        regelnT: "Own rules",
        regelnH: "Extra words and patterns to mask. As YAML. Changing them changes the measurement.",
        regelnSpeichern: "Save rules",
        pruefeLaeuft: "checking …",
        dienstDa: "MASCHERA {v} responds · model {m}",
        falscherDienst: "Responds, but this is not MASCHERA: {}",
        keinDienst: "No response: {}",
        bspdFrage: "Keep {} in the clear permanently?\nThis is sensitive personal data.",
        starrHinweis: "Stays in the clear anyway.",
        unbekannteTags: "Saved types that no longer exist: {}",
        einpflegen04: "Apply vocabulary", leerenA: "Clear",
        antwortPlatz: "Paste your AI tool’s answer here (Ctrl+V) …",
        offenText: "{} placeholders remained. Check them in the final text:",
        gutText: "{} placeholders restored.",
        hinausT: "Prompt + masked text", trenner: "apply the prompt above to the following text",
        sendenZu: "Copy all and open {}", onlineWarnung: "In {} you are working online, be careful!", origPlatz: "Paste the original text here …", promptPlatz: "Your prompt, e.g. \u00abReply to this e-mail politely.\u00bb", hinausLeer: "First «Take into prompt», then you see here what goes out.",
        spalteId: "ID",
        spalteWert: "Original value", spalteTyp: "Type", anteilW: "Masked share",
        keinVokabular: "No vocabulary yet. It appears when you mask.",
        gruppen: { person: "Person", herkunft: "Origin and status",
          anschrift: "Address and place", erreichbar: "Contact",
          amtlich: "Official numbers", finanzen: "Finance",
          gesundheit: "Health and insurance",
          verfahren: "Case, time, organisation",
          nurerkannt: "Detected, never replaced" },
        darstellungT: "Appearance", themaEtikett: "Colours",
        themaH: "“Automatic” follows your system setting.",
        themaAuto: "Automatic", themaHell: "Light", themaDunkel: "Dark",
        schriftT: "Typeface", schriftart: "Family",
        schriftgroesse: "Size",
        schriftH: "Applies to the text areas: original, masked text, prompt and reply.",
        schriftprobe: "Dear Sir or Madam", vorschauE: "Preview",
        schriftSerif: "Serif",
        schriftMono: "Monospace",
        herunterladen: "Download", hochladen: "Upload", einfuegen: "Paste",
        einfuegenHinweis: "Clipboard blocked. Press Ctrl+V.",
        drop_ohne_datei: "This program does not hand over a file. Drag the message to the desktop first, then here.",
        mUpdate: "Check for updates", neuesteSucht: "Asking GitHub for the newest version …", neuesteAktuell: "You have {aktuell}. That is the newest version.", neuesteNeu: "Version {neueste} is out. You have {aktuell}.", neuesteSeite: "To the download page",
        kAusschneiden: "Cut", kKopieren: "Copy", kEinfuegen: "Paste",
        menu: "Menu",
        mBrowser: "Open in browser", mHilfe: "Help",
        mHilfeBald: "coming soon", mWebseite: "maschera.ch",
        mGithub: "Source code on GitHub", mDownload: "Download",
        mFehler: "Report an issue",
        mImpressum: "Legal notice", mKontakt: "Contact",
        finalKopieren: "Copy",
        vokHerunter: "Download vocabulary",
        vokHoch: "Upload vocabulary",
        tplSichern: "Save",
        tplWaehlen: "Templates ({})",
        tplSuchen: "Search …", tplNichts: "No template matches.",
        tplLeer: "No local template saved yet",
        tplName: "Template name",
        tplWarnung: "Templates stay in plain text on disk. "
          + "Do not put personal data into a template.",
        tplWeg: "Delete template “{}”?", tplWegT: "Delete template",
        tplGesichert: "Template “{}” saved.",
        tplFehler: "Template not saved: {}",
        sichernWarnung: "The file holds {} original values in plain text, "
          + "that is everything masked here. It will then sit unprotected in your "
          + "downloads folder. Save?",
        vokGeladen: "{} vocabulary entries loaded.",
        vokKaputt: "The file is not readable JSON. Nothing loaded.",
        frageJa: "Continue",
        frageNein: "Cancel",
        frageOk: "OK",
        neuladenFrage: "Really reload?\n{} vocabulary entries will be lost.",
        verbindungWeg: "No connection to the MASCHERA service. The request did not arrive. Try again; if that does not help, restart MASCHERA.",
        httpFehler: "The MASCHERA service refused the request (error {status}).",
        vokFalsch: "The file does not contain an object. Nothing loaded.",
        vokFremd: "Not a MASCHERA vocabulary file. Nothing loaded.",
        vokFassung: "Unknown version {}. This build reads version 1.",
        vokKein: "No dictionary in the file. Nothing loaded.",
        vokSchluessel: "Not a valid placeholder: {}. Nothing loaded.",
        vokWert: "The value for {} is not a string. Nothing loaded.",
        vokText: "The masked text in the file is not a string.",
       
        bearbeiten: "Edit", bearbeitenFertig: "Done",
        bearbeitenHilfe: "Correct the text by hand. Leave placeholders such as [FULLNAME_1] in place. They are restored at the end.",
        phUnbekannt: "The dictionary does not know these placeholders: {liste}. They will stay as they are.",
        phEntwertet: "{} placeholders recovered from Markdown escaping. The service had escaped them with backslashes.",
        phErgaenzt: "{} broken placeholders completed: {liste}. The dictionary knows them. The service swallowed the bracket.",
        phKaputt: "These passages look like placeholders but are not: {liste}. They will NOT be restored. Please check them in the text.",
        fussLinks: "MASCHERA · processed on this device · no online connection to the AI services", bereitS: "Ready",
        orig: "Original text", masked: "Masked", run: "Mask",
        fertig: "Final text", prompt: "Prompt assembly", promptT: "Prompt",
        antwort: "Answer", neu: "New",
        hundert: "100% local", einst: "Settings",
        spruch: "Mask your data before you share it! · "
              + "Local model · FADP / GDPR",
        spruch1: "Mask your data before you share it!",
        spruch2: "Local model · FADP / GDPR",
        laden: "Loading the local model",
        keinStart: "No server on /api/zustand: {}",
        zeichenN: (n) => n + " characters",
        eintraegeN: (n) => n + " entries",
        leer05: "The final text appears here once you apply the vocabulary.",
        leer02: "Nothing masked yet. Paste text into column 1 and press "
              + "\u00abMask\u00bb.",
        dropN: "Click or drop a text file or e-mail here", dropT: "Supported: PDF, DOCX, TXT, MD, LOG, CSV, JSON and e-mails as EML, MSG or MBOX. A click opens the file picker.",
        laeuft: "running …", lWartet: "Preparing the text …", lModell: "Window {} of {}", lMaskieren: "Masking, building the glossary …", lRest: "about {} left", drop: "Drop a file or choose one",
        portFehlt: "No port given.",
        verwerfenVok: "Really continue?\n{} vocabulary entries will be lost.",
        verwerfenText: "Really continue?\nThe text in column 1 will be lost.",
        neuAlles: "Do you really want to start over?\nAll data will be reset!",
        beispiel: "Example", kopieren: "Copy",
        kopiert: "Copied", vokabular: "Vocabulary",
        ohneModell: "NO MODEL: checksums and patterns only. Names, dates "
                  + "and addresses stay in the clear.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "NO MODEL: checksums and patterns only. Names, dates and addresses stay IN THE CLEAR.",
          fenster: "Longer than one window ({token} tokens). Processed with overlap.",
          wortgrenzen: "{anzahl} model spans fell inside a word and were extended to word boundaries.",
          mehrere_nachrichten: "{anzahl} messages in the file. Only the first one is processed.",
          vorlieben: "From the saved preferences, in the clear: {tags}",
          ohne_woerterbuch: "Without a dictionary: anonymised for good, no way back.",
          eigene_regeln: "Own rules applied ({anzahl}): {namen}",
          schreibweise: "{platzhalter} differs from {treffer} only in capitalisation. Not replaced.",
          anhang_uebersprungen: "Attachment skipped: {name}",
          kein_textteil: "The e-mail has no text part, only {art}.",
          msg_ohne_textrumpf: "The .msg has no plain-text body (only RTF or HTML). In Outlook choose «Save as» → .eml.",
          binaer_abgeschnitten: "{zeichen} characters after the end of the text looked like binary data and were left out.",
          nur_html: "only an HTML part present, roughly stripped",
          kein_rumpf: "no text body found",
          pdf_ohne_text: "no text in the PDF. Probably a scan. Without OCR the filter sees nothing, and an empty finding does NOT mean there is no personal data in it.",
          pdf_seiten: "{anzahl} pages, layout is lost on reading",
          tabellen: "{anzahl} tables, read row by row",
          nicht_gelesen: "NOT read: {teile}. That is where letters often carry the sender",
          docx_leer: "no text in the document. An empty finding does NOT mean there is no personal data in it.",
          kodierung: "Encoding {kodierung}",
          bom: "byte order mark at the start of the text, removed",
          t_kopfzeilen: "Headers",
          t_fusszeilen: "Footers",
          t_kommentare: "Comments",
          t_fussnoten: "Footnotes",
        },
        meldungen: {
          adresse_fehlt: "Field `adresse` is missing or empty.",
          adresse_zu_lang: "Address longer than {hoechstens} characters.",
          datei_ohne_text: "The file yielded no text.",
          datei_unlesbar: "File not readable: damaged or an unsupported format.",
          datei_zu_gross: "File larger than {mb} MB.",
          dienst_kein_objekt: "Service {nummer} is not an object.",
          dienst_kennung_doppelt: "Identifier used twice: {kennung}",
          dienst_ohne_adresse: "Service {name} has no address.",
          dienst_ohne_namen: "Service {nummer} has no name.",
          dienst_schema: "Service {name}: only https:// or http://, not {adresse}",
          dienste_keine_liste: "Field `dienste` is not a list.",
          dienste_leer: "At least one service is needed. Otherwise “Copy and open” has nowhere to go.",
          dienste_zu_viele: "At most {hoechstens} services.",
          einst_kein_objekt: "Not an object.",
          einstellungen_gespeichert: "Saved.",
          feld_klartext: "Field `klartext` is missing or not a list of types.",
          feld_text: "Field `text` is missing or not text.",
          feld_woerterbuch: "Field `woerterbuch` is missing or not an object.",
          feld_yaml: "Field `yaml` is missing or not text.",
          fenster_kein_wahrheitswert: "Field `eigenes_fenster` is not a boolean.",
          format_unbekannt: "Format {endung} is not read. Possible: {moeglich}",
          keine_datei: "No file received.",
          klartext_gelesen: "These types stay in plain text permanently.",
          klartext_gespeichert: "Saved. These types stay in plain text permanently, in future documents as well.",
          nicht_gespeichert: "Not saved. The file in the settings folder could not be written.",
          ohne_tags_unbekannt: "Unknown types in `ohne`: {tags}",
          port_ausserhalb: "Port outside 1–65535: {port}",
          regeldatei_fehlerhaft: "The rule file is faulty and was not applied.",
          regeln_abgelehnt: "Rules rejected. The file contains an error.",
          regeln_gelesen: "Changing the rules changes the measured result.",
          regeln_veraltete_schluessel: "This rule file uses outdated keys. They are still read or skipped: {umbenennungen}",
          regeln_gespeichert: "Saved. The measured result changes with it.",
          neueste_begrenzt: "GitHub is limiting requests right now. Your network has used its 60 per hour. Try again in an hour, or go straight to the download page.",
          neueste_nicht_erreichbar: "GitHub cannot be reached: no network, or the server may not go out. The newest version is on the download page.",
          neueste_unlesbar: "GitHub answered, but without a readable version number. The newest version is on the download page.",
          regeln_unlesbar: "Rules not readable. A field has the wrong form.",
          tray_kein_wahrheitswert: "Field `tray` is not a boolean.",
          fenstermodus_unbekannt: "Window mode {wert} does not exist. Possible: {moeglich}",
          thema_unbekannt: "Theme {wert} does not exist. Possible: {moeglich}",
          schriftart_unbekannt: "Typeface {wert} does not exist. Possible: {moeglich}",
          schriftgroesse_unbekannt: "Size {wert} does not exist. Possible: {moeglich}",
          sprache_unbekannt: "Language {sprache} does not exist. Possible: {moeglich}",
          oberflaechensprache_unbekannt: "Interface language {wert} does not exist. Possible: {moeglich}",
          text_leer: "The text is empty.",
          vorlage_kein_objekt: "Template {nummer} is not an object.",
          vorlage_name_doppelt: "Name used twice: {name}",
          vorlage_name_zu_lang: "Name longer than {hoechstens} characters: {name}",
          vorlage_ohne_namen: "Template {nummer} has no name.",
          vorlage_ohne_text: "Template {nummer} ({name}) has no text.",
          vorlage_text_zu_lang: "Template {name} exceeds {hoechstens} characters.",
          vorlagen_feld_fehlt: "Field `vorlagen` is missing or not a list.",
          vorlagen_klartext: "Templates stay in plain text on disk. Do not put personal data into a template.",
          vorlagen_zu_viele: "At most {hoechstens} templates.",
          vorliebe_bspd: "Sensitive personal data: {tags}. These types stay in plain text only with explicit consent.",
          vorliebe_tags_unbekannt: "Unknown types: {tags}",
          wirt_unbekannt: "This service does not answer under the name “{wirt}”. Locally it is reachable on 127.0.0.1; behind a proxy the name belongs in MASCHERA_WIRT.",
          regeln_kein_yaml: "The rules are not valid YAML (line {zeile}).",
          regel_zu_langsam: "Rule “{id}”: the pattern takes {dauer} s on a test line. That is too slow, usually because of nested repetition such as (a+)+.",
          regel_ohne_kennung: "A rule has no identifier (`id`).",
          regel_kennung: "Rule identifier “{id}”: lowercase letters, digits and underscore only, 2 to 32 characters.",
          regel_platzhalter: "Rule “{id}”: the placeholder “{platzhalter}” must be 2 to 20 letters or digits.",
          regel_woerter_leer: "Rule “{id}”: the word list (`words`) is empty.",
          regel_woerter_kurz: "Rule “{id}”: entries too short ({kurz}). Below {min} characters they match everywhere as a syllable.",
          regel_etiketten_leer: "Rule “{id}”: `labels` is empty. Without a label the rule would match any number.",
          regel_wertform: "Rule “{id}”: the value form “{form}” does not exist. Possible: {moeglich}",
          regel_min_max: "Rule “{id}”: implausible min/max ({min}/{max}).",
          regel_muster_fehlt: "Rule “{id}”: the pattern (`pattern`) is missing.",
          regel_muster_ungueltig: "Rule “{id}”: the pattern is invalid (at character {stelle}).",
          regel_art: "Rule “{id}”: the type “{art}” does not exist. Possible: {moeglich}",
          regeln_doppelt: "These rule identifiers appear twice: {kennungen}",
          regel_platzhalter_vergeben: "Placeholder already taken: {platzhalter}. Choose another name.",
          msg_ohne_olefile: "Outlook messages (.msg) cannot be read here. In Outlook choose “Save as” → .eml.",
          pdf_ohne_pymupdf: "PDFs cannot be read here. The PDF library is missing.",
          docx_zu_gross: "The Word document would be {mb} MB unpacked; at most {hoechstens} MB are read.",
          docx_kaputt: "Not a readable .docx file. Older .doc files are a different format.",
          docx_ohne_dokument: "Not a Word document. Probably .odt, .pptx or .xlsx with the wrong extension.",
          docx_dtd: "The Word document declares a DTD; real Word files never do, so it is not read.",
          word_alt: "The old Word format (.doc) is not read. Save it as .docx in Word or LibreOffice.",
        },
        leer: "Nothing masked yet." }
};

/* Die vorgegebenen Dienste. Die Einstellungen koennen sie aendern. */
const DIENSTE = [
  { id: "chatgpt", name: "ChatGPT", url: "https://chatgpt.com/" },
  { id: "claude",  name: "Claude",  url: "https://claude.ai/new" },
  { id: "copilot", name: "Copilot", url: "https://copilot.microsoft.com/" },
  { id: "gemini",  name: "Gemini",  url: "https://gemini.google.com/app" },
  { id: "mistral", name: "Mistral", url: "https://chat.mistral.ai/chat" },
];

/* Die Zuordnung Tag -> Gruppe ist GESTALTUNG, kein Vertragsbestandteil.
 * Sie steht hier und nicht im Pack: ein Tag darf die Gruppe wechseln, ohne
 * dass ein Checkpoint ungueltig wird.
 *
 * Vollstaendigkeit wird geprueft (`tests/test_oberflaeche.js`). Ein Tag
 * ohne Gruppe landete sonst unter «-».
 */
const TAG_GRUPPEN = {
  person: ["FULLNAME", "GIVENNAME", "AGE", "SEX", "MARITALSTATUS"],
  herkunft: ["NATIONALITY", "RELIGION", "PLACE_OF_ORIGIN",
             "RESIDENCE_STATUS", "PERMIT_TYPE", "VOTING_RIGHTS",
             "COUNTRY"],
  anschrift: ["STREET", "BUILDINGNUM", "ZIPCODE", "CITY", "EGID", "EWID",
              "PARCEL"],
  erreichbar: ["EMAIL", "PHONE", "URL", "IPADDRESS", "USERNAME"],
  amtlich: ["AHVN13", "UID", "IDDOC", "MUNICIPALITY_ID", "PLATE"],
  finanzen: ["IBAN", "CREDITCARD", "QR_REFERENCE", "AMOUNT"],
  gesundheit: ["INSURANCE_CARD", "PATIENT_ID", "SOCIAL_INSURANCE",
               "INSURANCE_POLICY", "HEALTHCARE_ORG", "ZSR_RCC", "GLN"],
  verfahren: ["CASE_ID", "DATE", "TIME", "ORG"],
  // `CANTON` ist `tag_only`: erkannt, aber nie ersetzt. Eine eigene Gruppe
  // sagt, warum es sich nicht umstellen laesst — als gesperrter Knopf neben
  // lauter bedienbaren saehe es nach Fehler aus.
  nurerkannt: ["CANTON"],
};

const GRUPPE_VON = {};
for (const [g, liste] of Object.entries(TAG_GRUPPEN)) {
  for (const tag of liste) GRUPPE_VON[tag] = g;
}

/* Vier Sprachen: in einer franzoesischen Oberflaeche soll der Knopf, der
 * etwas vorfuehrt, keinen deutschen Text vorfuehren.
 */
const BEISPIEL = {
  de: "Sehr geehrte Damen und Herren\n\n"
    + "am 14.03.2026 hat Frau Andrea Brülhart, wohnhaft an der Lindenstrasse "
    + "12, 3011 Bern, bei uns eine Beschwerde zum Dossier ZH-2026/4471 "
    + "eingereicht. Sie erreichen sie unter andrea.bruelhart@example.ch oder "
    + "+41 79 412 55 08.\n\nDie Maschera Immobilien AG hat bestätigt, dass "
    + "Frau Brülhart die Miete seit Januar fristgerecht bezahlt. Ihre "
    + "Versichertennummer lautet 756.1234.5678.97.\n\n"
    + "Wir bitten um eine Rückmeldung bis am 30.04.2026.\n\n"
    + "Freundliche Grüsse\nMartin Kessler",
  fr: "Madame, Monsieur\n\n"
    + "le 14.03.2026, Madame Andrea Brülhart, domiciliée Lindenstrasse 12, "
    + "3011 Berne, a déposé une réclamation concernant le dossier "
    + "ZH-2026/4471. Vous pouvez la joindre à andrea.bruelhart@example.ch ou "
    + "au +41 79 412 55 08.\n\nMaschera Immobilien AG a confirmé que Madame "
    + "Brülhart paie son loyer dans les délais depuis janvier. Son numéro "
    + "d'assuré est 756.1234.5678.97.\n\n"
    + "Nous vous prions de nous répondre jusqu'au 30.04.2026.\n\n"
    + "Avec nos meilleures salutations\nMartin Kessler",
  it: "Gentili signore, egregi signori\n\n"
    + "il 14.03.2026 la signora Andrea Brülhart, domiciliata in "
    + "Lindenstrasse 12, 3011 Berna, ha presentato un reclamo relativo al "
    + "dossier ZH-2026/4471. È raggiungibile all'indirizzo "
    + "andrea.bruelhart@example.ch o al numero +41 79 412 55 08.\n\n"
    + "La Maschera Immobilien AG ha confermato che la signora Brülhart paga "
    + "la pigione puntualmente da gennaio. Il suo numero d'assicurato è "
    + "756.1234.5678.97.\n\n"
    + "Vi preghiamo di rispondere entro il 30.04.2026.\n\n"
    + "Cordiali saluti\nMartin Kessler",
  en: "Dear Sir or Madam\n\n"
    + "On 14.03.2026, Ms Andrea Brülhart, residing at Lindenstrasse 12, "
    + "3011 Bern, filed a complaint regarding case ZH-2026/4471. She can be "
    + "reached at andrea.bruelhart@example.ch or +41 79 412 55 08.\n\n"
    + "Maschera Immobilien AG has confirmed that Ms Brülhart has paid her "
    + "rent on time since January. Her insurance number is "
    + "756.1234.5678.97.\n\n"
    + "We kindly ask for a reply by 30.04.2026.\n\n"
    + "Kind regards\nMartin Kessler",
};

/* --- Zustand ------------------------------------------------------------ */

const z = {
  sprache: "de",
  // Filter im Vokabular (seit 2.0): «alle» oder eine Gruppe aus TAG_GRUPPEN.
  vokFilter: "alle",
  bearbeiten: false,
  tray: true,
  fenstermodus: "widget",
  // «automatisch» und nicht «hell»: die Vorgabe UEBERLAESST die Wahl dem
  // System.
  thema: "automatisch",
  // Was in Bereich 05 zuletzt stand — damit `zeichneFinal` eine
  // Bearbeitung des Anwenders nicht ueberschreibt.
  finalBearbeitet: null,
  // Die Eintraege des Burgermenues, aus `adressen.json`.
  adressen: [],
  burgerOffen: false,
  zustand: null,          // /api/zustand
  tags: {},               // tag -> {bezeichnung, gruppe, bspd, …}
  orig: "",
  antwort: null,          // /api/anonymisieren
  laeuft: false,
  sendeUhr: null,
  // Haelt den Ziehschleier, solange `dragover` nachkommt.
  ziehUhr: null,
  // Holt den Stand, solange maskiert wird.
  fortschrittUhr: null,
  // Erst ein Klick auf «Uebernahme in Prompt» traegt den maskierten Text in
  // die dritte Spalte. Vorher steht dort NICHTS von diesem Dokument: die
  // Spalte, die hinausgeht, fuellt sich nicht von selbst.
  uebernommen: false,
  prompt: "",
  antwort04: "",
  final: null,
  // Das Ergebnis, dessen Banner «Platzhalter blieben stehen» geschlossen ist.
  offenZu: null,
  dienst: "claude",
  kontext: null,
  // Offene Gruppen im Kontextmenue, jede von Hand auf- und zugeklappt
  // (seit 2.1); «Häufig» steht zu Beginn offen. Gilt fuer die Sitzung.
  kontextOffen: new Set(["haeufig"]),
  kontextSuche: "",      // Suchwort im Kontextmenue, gilt bis zum Schliessen
  gross: null,           // Kennung der vergroesserten Kachel, sonst null
  hinweiseAuf: false,    // ruhige Hinweise unter dem Kopf von 02 offen
  hinausAuf: false,      // «Prompt + maskierter Text» in 03 aufgeklappt
  dienste: DIENSTE.map((d) => ({ ...d })),
  eigenesFenster: true,
  schriftgroesse: 100,
  schriftart: "werk",
  klartext: [],
  bspdTags: [],
  regelnYaml: "",
  vokMeldung: null,
  // Die Meldung des Einstellungsdialogs — ein eigener Kanal, siehe meldeVok().
  einstMeldung: "",
  vorlagen: [],
  vorlage: null,          // Name der gewaehlten Vorlage
  vorlagenOffen: false,
  vorlagenFilter: "",
  vokSuche: "",           // Suchwort im Vokabular (seit 2.1)
};

function t() { return I18N[z.sprache] || I18N.de; }

// Ein Hinweis des Servers in der gewaehlten Sprache.
//
// Der Server schickt `{schluessel, werte, text}`; der Satz steht in
// `TEXTE[sprache].hinweise`. `text` ist die deutsche Rueckfallfassung fuer
// einen Schluessel, den diese Oberflaeche nicht kennt — besser ein deutscher
// Satz als keiner. Eine blosse Zeichenkette wird ebenfalls angezeigt.
//
// Ein Wert, der ein Feld ist, gilt als LISTE VON SCHLUESSELN und wird selbst
// uebersetzt — so bleiben auch «Kopfzeilen, Fusszeilen» in der Meldung
// `nicht_gelesen` in der richtigen Sprache.
function hinweisText(h) {
  if (typeof h === "string") return h;
  if (!h || typeof h !== "object") return "";
  const tab = t().hinweise || {};
  let satz = tab[h.schluessel];
  if (!satz) return h.text || "";
  for (const [name, wert] of Object.entries(h.werte || {})) {
    const gesetzt = Array.isArray(wert)
      ? wert.map((k) => tab[k] || k).join(", ")
      : String(wert);
    satz = satz.split("{" + name + "}").join(gesetzt);
  }
  return satz;
}

// Der Schluessel, wo einer da ist — fuer Vergleiche, die nicht am
// Wortlaut haengen sollen.
function hinweisSchluessel(h) {
  return (h && typeof h === "object") ? h.schluessel : null;
}

// Eine Meldung des Servers — Fehler oder Warnung — in der gewaehlten
// Sprache. Dieselbe Bauart wie `hinweisText`.
//
// `text` bleibt der Rueckfall: kennt die Oberflaeche den Schluessel nicht —
// ein neuerer Server, eine aeltere Oberflaeche —, steht der deutsche Satz
// da und nicht eine leere Zeile.
function meldungText(text, schluessel, werte) {
  const satz = (t().meldungen || {})[schluessel];
  if (!satz) return String(text == null ? "" : text);
  let fertig = satz;
  for (const [name, wert] of Object.entries(werte || {})) {
    fertig = fertig.split("{" + name + "}").join(String(wert));
  }
  return fertig;
}

// Der Warnungsteil einer Antwort, uebersetzt. Fehlt die Warnung, kommt
// der leere Text zurueck — die Befundzeile wird dann geleert, nicht mit
// «undefined» gefuellt.
function warnungText(d) {
  if (!d || !d.warnung) return "";
  return meldungText(d.warnung, d.warnung_schluessel, d.warnung_werte);
}

// Ein `Error` aus einer Serverantwort, mit Schluessel und Werten am
// Objekt. `fehlerText(e)` macht daraus den Satz in der Sprache der
// Oberflaeche.
//
// Die Sprache wird ERST BEIM ANZEIGEN gewaehlt, nicht beim Fangen. Sonst
// stuende ein Fehler, der vor einem Sprachwechsel entstand, danach in der
// alten Sprache da.
function serverFehler(d, status) {
  const e = new Error(d.fehler || ("HTTP " + status));
  e.schluessel = d.fehler_schluessel;
  e.werte = d.fehler_werte;
  e.status = status;
  return e;
}

// ⚠️ NIE DEN ROHEN TEXT DES BROWSERS. Kommt eine Anfrage gar nicht an,
// wirft `fetch` einen `TypeError`, dessen Text der Browser setzt —
// «Failed to fetch» in Edge und Chromium, «NetworkError …» in Firefox,
// immer englisch. Er stand so in einer italienischen Oberflaeche.
// `tests/test_oberflaeche.js` Punkt 78 haelt beide Wege fest.
function fehlerText(e) {
  if (!e) return "";
  if (e.schluessel) return meldungText(e.message, e.schluessel, e.werte);
  if (e instanceof TypeError) return t().verbindungWeg;
  if (e.status) return t().httpFehler.replace("{status}", String(e.status));
  return String(e.message || e);
}

function typOf(tag) {
  return String(tag || "").replace(/^\[|\]$/g, "").replace(/_\d+[a-z]?$/, "");
}

function farbe(typ) {
  if (TYPE_COLORS[typ]) return TYPE_COLORS[typ];
  // Die Palette des Entwurfs traegt englische Gruppennamen, die Zuordnung
  // hier deutsche. Eine Uebersetzung, damit beide bleiben duerfen.
  const englisch = { person: "person", herkunft: "origin",
                     anschrift: "address", erreichbar: "contact",
                     amtlich: "official", finanzen: "finance",
                     gesundheit: "health", verfahren: "process" };
  const g = englisch[GRUPPE_VON[typ]];
  if (g && GROUP_PALETTE[g]) return GROUP_PALETTE[g];
  let n = 0;
  for (let i = 0; i < typ.length; i++) n = (n * 31 + typ.charCodeAt(i)) % 997;
  return TYPE_FALLBACK[n % TYPE_FALLBACK.length];
}

/* Das Thema ans Wurzelelement — oder eben NICHT.
 *
 * «automatisch» entfernt das Attribut, statt eines zu setzen. Nur ohne
 * Attribut greift `@media (prefers-color-scheme: dark)`; ein
 * `data-thema="automatisch"` waere ein dritter Zustand, den das Blatt nicht
 * kennt.
 */
/* Die Adresse der Maske zur Farbwahl. Ein BILD sieht `data-thema` der Seite
 * nicht; die Wahl reist deshalb in der Adresse, und `maske.svg` faerbt per
 * `:target` um. «automatisch» braucht keine: dort entscheidet in der Datei
 * `prefers-color-scheme`. */
function maskeAdresse() {
  return z.thema === "hell" || z.thema === "dunkel"
    ? "maske.svg#" + z.thema : "maske.svg";
}

function themaAnwenden() {
  // Die Reihe zeigt, welche Stufe gilt — sonst waeren es drei Knoepfe, von
  // denen keiner sagt, wo man steht.
  for (const stufe of THEMEN) {
    const k = $("thema-" + stufe);
    if (!k) continue;
    k.classList.toggle("aktiv", z.thema === stufe);
    k.setAttribute("aria-checked", String(z.thema === stufe));
  }
  const w = document.documentElement;
  if (z.thema === "hell" || z.thema === "dunkel") {
    w.setAttribute("data-thema", z.thema);
  } else {
    w.removeAttribute("data-thema");
  }
  // Startbildschirm und Kopf der Einseiter zeigen die Maske als `<img>`;
  // die Kopfzeile als Hintergrund, und den stellt das Blatt um.
  for (const b of document.querySelectorAll("img.maske")) b.src = maskeAdresse();
}

function $(id) { return document.getElementById(id); }

/* --- Rueckfragen ---------------------------------------------------------
 *
 * ⚠️ KEIN `window.confirm`, KEIN `window.prompt`. Die Rueckfrage des
 * Browsers traegt einen Titel, den die Seite nicht setzen kann
 * («127.0.0.1:4141 says»), Knoepfe in der Sprache des Browsers statt der
 * Oberflaeche («OK / Cancel» unter einer italienischen Frage) und eine
 * feste Breite, die im schmalen Fenster ueber den Rand ragt.
 * `tests/test_oberflaeche.js` Punkt 79 verbietet beide.
 *
 * `frage()` gibt ein Versprechen auf ja/nein, `eingabe()` eines auf den
 * Text oder null. Beide gehen ueber `frageWeg`, damit die Pruefung
 * antworten kann, ohne einen Knopf zu druecken — den Dialog selbst prueft
 * sie getrennt.
 */
let frageOffen = null;
// Schon im eigenen Dialog bestaetigt — dann nicht nochmals im Browser.
let neuladenErlaubt = false;

function frageZeigen(text, opt) {
  const o = opt || {};
  const s = t();
  const mitEingabe = typeof o.vorschlag === "string";
  // Eine noch offene Frage gilt als abgelehnt. Zwei Versprechen auf einen
  // Dialog liessen das erste fuer immer haengen.
  if (frageOffen) frageSchliessen(false);
  $("frage-text").textContent = text;
  $("frage-ja-text").textContent = mitEingabe ? s.frageOk : s.frageJa;
  $("frage-nein-text").textContent = s.frageNein;
  $("frage-feld").hidden = !mitEingabe;
  $("frage-eingabe").value = mitEingabe ? o.vorschlag : "";
  $("frage").hidden = false;
  // Der Fokus steht auf «Abbrechen», wenn etwas verloren geht: ein
  // versehentliches Enter soll nichts wegwerfen. Mit Eingabe im Feld.
  if (mitEingabe) {
    $("frage-eingabe").focus();
    $("frage-eingabe").select();
  } else {
    $("frage-nein").focus();
  }
  return new Promise((erledigt) => {
    frageOffen = { erledigt, mitEingabe };
  });
}

function frageSchliessen(ja) {
  const offen = frageOffen;
  frageOffen = null;
  $("frage").hidden = true;
  if (!offen) return;
  if (offen.mitEingabe) {
    offen.erledigt(ja ? $("frage-eingabe").value : null);
  } else {
    offen.erledigt(Boolean(ja));
  }
}

let frageWeg = frageZeigen;
function frageErsetzen(fn) { frageWeg = fn || frageZeigen; }

function frage(text) { return frageWeg(text, {}); }
function eingabe(text, vorschlag) {
  return frageWeg(text, { vorschlag: String(vorschlag == null ? "" : vorschlag) });
}

function el(tag, klasse, text) {
  const e = document.createElement(tag);
  if (klasse) e.className = klasse;
  if (text != null) e.textContent = text;
  return e;
}

/* --- Serverzugriff ------------------------------------------------------ */

async function holeZustand() {
  const a = await fetch("/api/zustand");
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function holeTags(sprache) {
  const a = await fetch("/api/tags?sprache=" + encodeURIComponent(sprache));
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function maskiere(text) {
  const a = await fetch("/api/anonymisieren", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text, woerterbuch: true,
                           regeln: true })
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

// Eine Datei wird ueber `/api/lesen` gelesen, nicht ueber
// `/api/anonymisieren`. Dessen Dateizweig bleibt — er steht im Vertrag, und
// die Kommandozeile braucht ihn —, aber die Oberflaeche geht ihn nicht.

async function liesDatei(datei) {
  // Ein eigener Endpunkt, der NUR liest: ein Ablegen soll nicht die ganze
  // Kette fahren. Siehe die Begruendung an `/api/lesen` in `app/serve.py`.
  const f = new FormData();
  f.append("datei", datei);
  const a = await fetch("/api/lesen", { method: "POST", body: f });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) {
    // Der Grund ist wichtiger als der Status: ein gescanntes PDF ohne
    // Textebene landet hier, und der Server sagt ausdruecklich, dass ein
    // leerer Befund KEINE Entwarnung ist.
    const e = serverFehler(d, a.status);
    e.hinweise = d.hinweise || [];
    throw e;
  }
  return d;
}

async function zurueckwandeln(text, woerterbuch) {
  const a = await fetch("/api/zurueckwandeln", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text, woerterbuch: woerterbuch }),
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

async function holeVorlieben() {
  const a = await fetch("/api/vorlieben");
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function setzeVorlieben(klartext, auchBspd) {
  const a = await fetch("/api/vorlieben", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ klartext: klartext, auch_bspd: !!auchBspd }),
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

async function holeRegeln() {
  const a = await fetch("/api/regeln");
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function setzeRegeln(yaml) {
  const a = await fetch("/api/regeln", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ yaml: yaml }),
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

async function holeEinstellungen() {
  const a = await fetch("/api/einstellungen");
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function setzeEinstellungen(e) {
  const a = await fetch("/api/einstellungen", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(e),
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

async function holeVorlagen() {
  const a = await fetch("/api/vorlagen");
  if (!a.ok) throw serverFehler({}, a.status);
  return a.json();
}

async function setzeVorlagen(liste) {
  const a = await fetch("/api/vorlagen", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vorlagen: liste }),
  });
  const d = await a.json().catch(() => ({}));
  if (!a.ok) throw serverFehler(d, a.status);
  return d;
}

/* --- Spalte 2: der maskierte Text --------------------------------------- */

/* Die Einfaerbung ist das eigentliche Gestaltungsproblem: bei vielen
 * Fundstellen steht etwa alle 80 Zeichen ein Platzhalter, und zu grell
 * eingefaerbt wird der Text unlesbar. Deshalb helle Flaeche, Farbe nur in
 * Rand und Schrift — und die Quelle im Randstil statt in einer weiteren
 * Farbe.
 */
function platzhalter(text, span) {
  const typ = typOf(text);
  const c = farbe(typ);
  const s = el("span", "ph");
  s.textContent = text;
  s.dataset.ph = text;
  s.style.background = c[0];
  s.style.color = c[2];
  s.style.border = (span && SRC_STYLE[span.quelle]) || ("1px solid " + c[1]);
  // Kein `title` mehr (seit 2.1): der Browser-Tooltip blieb ueber dem
  // Klappmenue haengen und zeigte eine Konfidenz, die niemand lesen konnte.
  // Den eigenen zeigt `tippZeigen()`: Originalwert und Herkunft.
  s.addEventListener("mouseenter", () => tippZeigen(s));
  s.addEventListener("mouseleave", tippWeg);
  if (span) {
    if (span.vertrauen != null) s.dataset.vertrauen = String(span.vertrauen);
    s.dataset.tag = span.tag;
    s.dataset.quelle = span.quelle;
    s.dataset.ph = span.platzhalter || text;
  }
  return s;
}

/* Der Tooltip am Platzhalter (seit 2.1, Feedback 20.10.2026).
 *
 * Erste Zeile der Originalwert, denn danach sucht, wer ueber eine Maske
 * faehrt. Zweite Zeile, WODURCH maskiert wurde, als Satz statt als
 * Kennwort. Die Konfidenz des Modells steht nicht mehr da: sie half bei
 * keiner Entscheidung.
 *
 * Ein eigenes Element statt `title`, damit es zum Design passt und beim
 * Oeffnen des Klappmenues verschwindet. Gesetzt wird nur `textContent`.
 */
function tippZeigen(ph) {
  const tipp = $("tipp");
  if (!tipp || !$("kontext").hidden) return;
  const schluessel = ph.dataset.ph;
  const wert = ((z.antwort && z.antwort.woerterbuch) || {})[schluessel];
  if (wert === undefined) return;
  const st = t();
  const herkunft = (st.maskiertDurch || {})[ph.dataset.quelle] || st.maskiertSonst;
  // Im Vokabular steht der Originalwert in der Spalte daneben; dort zeigt
  // der Tooltip nur, wodurch und wie sicher (Feedback 20.10.2026).
  const zeilen = ph.dataset.ohneWert ? [] : [el("div", "tipp-wert", wert)];
  zeilen.push(el("div", "tipp-herkunft", herkunft));
  // Die Sicherheit in Prozent, wie Menschen sie lesen. Nur wo das Modell
  // eine liefert; Muster und Regeln kennen keine.
  const v = parseFloat(ph.dataset.vertrauen);
  if (Number.isFinite(v)) {
    zeilen.push(el("div", "tipp-herkunft",
      st.sicherheit.replace("{}", String(Math.round(v * 100)))));
  }
  tipp.replaceChildren(...zeilen);
  tipp.hidden = false;
  const r = ph.getBoundingClientRect();
  const k = tipp.getBoundingClientRect();
  const links = Math.max(8, Math.min(r.left, window.innerWidth - k.width - 8));
  const unten = r.bottom + 6 + k.height > window.innerHeight - 8;
  tipp.style.left = links + "px";
  tipp.style.top = (unten ? r.top - 6 - k.height : r.bottom + 6) + "px";
}

function tippWeg() {
  const tipp = $("tipp");
  if (tipp) tipp.hidden = true;
}

/* Was erkannt, aber bewusst nicht ersetzt wurde, rahmt 02 hellgrau. Gibt
 * eine Funktion zurueck, die ein Textstueck zwischen zwei Platzhaltern an
 * `ziel` haengt und die Klartext-Werte darin rahmt. */
function klartextStuecke(ziel, spans) {
  // Was erkannt, aber bewusst nicht ersetzt wurde, bekommt einen hellgrauen
  // Rahmen (Feedback 18.10.2026): sonst sieht «erkannt und stehen gelassen»
  // aus wie «uebersehen». Gesucht wird ueber den WERT in den Textstuecken
  // zwischen den Platzhaltern, nicht ueber die Position: die Positionen
  // gelten im Original, und jede Korrektur von Hand verschiebt den Text.
  const original = z.antwort.original || "";
  const klar = new Map();
  for (const sp of spans) {
    if (!sp.klartext) continue;
    const wert = original.slice(sp.start, sp.end);
    if (wert.trim() && !klar.has(wert)) klar.set(wert, sp.tag);
  }
  const werte = [...klar.keys()].sort((a, b) => b.length - a.length);
  return (seg) => {
    if (!werte.length) { ziel.append(document.createTextNode(seg)); return; }
    let i = 0, von = 0;
    while (i < seg.length) {
      const w = werte.find((x) => seg.startsWith(x, i)
        && !/[\p{L}\p{N}]/u.test(seg[i - 1] || "")
        && !/[\p{L}\p{N}]/u.test(seg[i + x.length] || ""));
      if (!w) { i++; continue; }
      if (i > von) ziel.append(document.createTextNode(seg.slice(von, i)));
      const k = el("span", "klartext-stelle", w);
      k.title = klar.get(w) + " · " + t().klartextStelle;
      ziel.append(k);
      i += w.length; von = i;
    }
    if (von < seg.length) ziel.append(document.createTextNode(seg.slice(von)));
  };
}

function zeichneMaskiert() {
  const ziel = $("maskiert");
  ziel.replaceChildren();
  if (!z.antwort) {
    ziel.append(el("p", "leer", t().leer02));
    return;
  }
  maskiertSetzen(ziel, z.antwort.maskiert || "", z.antwort.spans || []);
}

/* Maskierten Text mit farbigen Platzhaltern in `ziel` setzen. Dieselbe
 * Darstellung in 02 und, seit 2.1, in der Vorschau von 03 (Feedback
 * 21.10.2026: «genau gleiche Optik»). Nur `textContent` und Elemente.
 */
function maskiertSetzen(ziel, text, alleSpannen) {
  const spans = alleSpannen.slice();

  // Platzhalter -> Spanne. Die Nummer ist ueber das Dokument stabil, also
  // genuegt normalerweise eine Zuordnung nach Platzhaltertext.
  const nach = {};
  for (const sp of spans) {
    if (sp.platzhalter) nach[sp.platzhalter] = sp;
  }

  // Bei ausgeschaltetem Vokabular ist `platzhalter` null — der maskierte
  // Text traegt die Nummer trotzdem. Ohne Rueckfall verloeren dann alle
  // Fundstellen Quelle und Vertrauen, und eine Modellvermutung bei 0.31
  // saehe aus wie eine Pruefsumme. Deshalb der Reihe nach zuordnen: die
  // Spannen kommen in Dokumentreihenfolge, die Platzhalter auch.
  // Klartext-Stellen sind keine Kandidaten dafuer: sie tragen keine Nummer.
  const reihe = spans.filter((sp) => !sp.platzhalter && !sp.klartext);
  let n = 0;

  const stueck = klartextStuecke(ziel, spans);

  let letzte = 0, m;
  PH_RE.lastIndex = 0;
  while ((m = PH_RE.exec(text)) !== null) {
    if (m.index > letzte) stueck(text.slice(letzte, m.index));
    let sp = nach[m[0]];
    if (!sp && reihe.length) {
      // Nur nehmen, wenn das Tag passt — sonst lieber ohne Zusatz einfaerben
      // als mit einer falschen Quelle.
      const kandidat = reihe[n];
      if (kandidat && kandidat.tag === typOf(m[0])) { sp = kandidat; n++; }
    }
    ziel.append(platzhalter(m[0], sp));
    letzte = m.index + m[0].length;
  }
  if (letzte < text.length) stueck(text.slice(letzte));
}

/* ========================================================================
 * Kontextmenue — der Korrekturweg
 *
 * **Ohne ihn muss der Anwender jedes Leck und jede Uebermaskierung
 * hinnehmen.** Die Oberflaeche zeigt, was die Kette gefunden hat, und
 * laesst sich hier widersprechen.
 *
 * **Korrekturen leben NUR im Browser.** Sie aendern `z.antwort` und das
 * Woerterbuch, gehen aber nie an den Server zurueck — es gibt keinen
 * Endpunkt dafuer, und es soll keinen geben. Ein neuer Maskierlauf
 * verwirft sie. Das ist der Preis dafuer, dass der Server zustandslos
 * bleibt und ein Dokument zur Zeit verarbeitet.
 * ====================================================================
 */

/* Was der Rechtsklick meint: eine Auswahl, sonst das Wort darunter.
 *
 * **Knoten und Versatz muessen aus DERSELBEN Quelle stammen.** Wer den
 * Versatz von `caretPositionFromPoint` nimmt und den Knoten selbst raet,
 * bekommt einen Versatz in einen anderen Text — das Menue nennt dann ein
 * Wort, auf das der Zeiger nie stand, und die Maske landet falsch.
 *
 * Eine Auswahl schlaegt alles, und das loest mehrteilige Namen mit:
 * «Maschera Immobilien AG» ist ein ORG und drei Woerter — markieren,
 * rechtsklicken, Tag waehlen. Ohne Auswahl bekaeme man nur «Immobilien».
 */
/* `x`/`y` sind der KLICKPUNKT und optional.
 *
 * Das Wort aus `window.getSelection` zu lesen setzt voraus, dass ein
 * Rechtsklick die Einfuegemarke bewegt — das ist Browserverhalten und keine
 * Zusage der Norm. Der Klickpunkt ist die verlaesslichere Quelle; die Marke
 * bleibt Rueckfall.
 *
 * `caretRangeFromPoint` ist Chromium, `caretPositionFromPoint` die Norm
 * und Firefox. Beide sind da, wo sie gebraucht werden.
 */
/* Was ein Wort begrenzt. EINE Quelle — der maskierte Text und die Felder
 * teilen sie sich, sonst zerfaellt «dasselbe Wort» in zwei Auslegungen. */
const WORTGRENZE = /[\s.,;:!?()\[\]{}"'«»<>\/\\]/;

/* Die Wortgrenzen um eine Stelle in einer Zeichenkette. */
function wortgrenzen(text, pos) {
  let a = Math.max(0, Math.min(pos, text.length)), b = a;
  while (a > 0 && !WORTGRENZE.test(text[a - 1])) a--;
  while (b < text.length && !WORTGRENZE.test(text[b])) b++;
  return [a, b];
}

function auswahlOderWort(x, y) {
  const sel = window.getSelection && window.getSelection();
  if (!sel) return null;

  // Eine echte Auswahl schlaegt alles — der Anwender hat gesagt, was er
  // meint.
  if (!sel.isCollapsed) {
    const gewaehlt = String(sel).trim();
    if (gewaehlt) return gewaehlt;
  }

  // Sonst das Wort unter dem Zeiger, an Wortgrenzen. Der Klickpunkt zuerst,
  // die Einfuegemarke als Rueckfall.
  let knoten = null, versatz = 0;
  if (typeof x === "number" && typeof y === "number") {
    if (document.caretRangeFromPoint) {
      const r = document.caretRangeFromPoint(x, y);
      if (r) { knoten = r.startContainer; versatz = r.startOffset; }
    } else if (document.caretPositionFromPoint) {
      const pos = document.caretPositionFromPoint(x, y);
      if (pos) { knoten = pos.offsetNode; versatz = pos.offset; }
    }
  }
  if (!knoten || knoten.nodeType !== 3) {
    knoten = sel.anchorNode;
    versatz = sel.anchorOffset;
  }
  if (!knoten || knoten.nodeType !== 3) return null;
  const text = knoten.nodeValue || "";
  const [a, b] = wortgrenzen(text, versatz);
  const wort = text.slice(a, b).trim();
  return wort || null;
}

/* Die Sinnbilder im Feldmenue. Inline gezeichnet, kein Nachladen von
 * aussen — und ueber `createElementNS`, damit kein `innerHTML` noetig ist.
 * Strichstil wie ueberall sonst: 24x24, keine Fuellung, `currentColor`.
 * Einfarbig: das Tagmenue darunter traegt farbige Punkte, und der
 * Unterschied zwischen den zwei Teilen soll sichtbar bleiben.
 */
/* Die Zeichen des Burgermenues — dieselbe Familie wie die ganze
 * Oberflaeche: `viewBox="0 0 24 24"`, Strich, runde Enden, kein Fuellen.
 *
 * Fuer den Quellcode spitze Klammern und kein Firmenlogo: ein gefuelltes
 * Logo fiele aus der Strichfamilie heraus und waere eine fremde Marke in
 * einem Werkzeug, das sonst nur seine eigene traegt.
 *
 * Welcher Eintrag welches Zeichen bekommt, steht in `adressen.json` —
 * dort, wo der Eintrag selbst definiert wird.
 */
const MENUEBILDER = {
  // Kasten mit Pfeil hinaus
  hinaus: ["M15 3h6v6", "M10 14 21 3",
           "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"],
  // Fragezeichen im Kreis
  frage: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
          "M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3", "M12 17h.01"],
  // Globus
  globus: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M3 12h18",
           "M12 3a15 15 0 0 1 0 18", "M12 3a15 15 0 0 0 0 18"],
  // Pfeil auf eine Linie
  herunter: ["M12 3v13", "m7 11 5 5 5-5", "M4 21h16"],
  // Spitze Klammern
  code: ["m8 8-5 4 5 4", "m16 8 5 4-5 4", "m14 4-4 16"],
  // Waage
  waage: ["M12 3v18", "M5 7h14", "M7 7 4 14h6L7 7Z", "M17 7l-3 7h6l-3-7Z",
          "M8 21h8"],
  // Briefumschlag
  brief: ["M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z",
          "m3 7 9 6 9-6"],
  // Kreispfeil — «Nach Updates suchen»
  kreispfeil: ["M21 12a9 9 0 1 1-2.6-6.4", "M21 3v6h-6"],
  // Kaefer — «Fehler melden». Rumpf, Fuehler, sechs Beine.
  kaefer: ["M12 20a6 6 0 0 0 6-6v-3a6 6 0 0 0-12 0v3a6 6 0 0 0 6 6Z",
           "M9 7V6a3 3 0 1 1 6 0v1", "M12 20v-9",
           "M6 13H2", "M22 13h-4",
           "M3 5a4 4 0 0 0 3.5 4", "M21 5a4 4 0 0 1-3.5 4",
           "M3 21a4 4 0 0 1 3.5-4", "M21 21a4 4 0 0 0-3.5-4"],
};

/* Die Zeichen an den Knoepfen — eine Quelle. Jede Bedienung traegt ein
 * Zeichen; es hilft, sich Dinge zu merken.
 *
 * Die Zeichnung steht einmal hier, gesetzt wird sie ueber
 * `zeichenSinnbild` — derselbe Weg wie bei `MENUEBILDER` und `SINNBILDER`.
 * `test_oberflaeche` Punkt 75 verlangt, dass jeder beschriftete Knopf
 * eines traegt.
 */
const KNOPFBILDER = {
  // Diskette — Speichern.
  speichern: ["M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z",
              "M17 21v-8H7v8", "M7 3v5h8"],
  // Pulslinie — «antwortet dort etwas?». Nicht die Lupe: gesucht wird
  // nichts, es wird eine Verbindung geprueft. Ein Zeichen wird in DER Groesse
  // beurteilt, in der es steht (15 px), nicht in der, in der man es zeichnet.
  pruefen: ["M3 12h4l2.5-7 5 14 2.5-7h4"],
  // Kreispfeil: speichern und neu starten
  neustart: ["M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8", "M3 3v5h5"],
  // Pluszeichen im Kreis — «einer mehr». Das nackte Plus traegt schon
  // «+ Neu»; der Kreis unterscheidet die beiden auf einen Blick.
  hinzufuegen: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
                "M12 8v8", "M8 12h8"],
  // Kreuz — schliessen. Dieselbe Form wie das X der Einseiten.
  schliessen: ["M18 6 6 18", "m6 6 12 12"],
  // Halbe Sonne, halber Mond — «automatisch», das System entscheidet.
  automatisch: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
                "M12 3a9 9 0 0 0 0 18Z"],
  // Sonne
  hell: ["M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z", "M12 2v2", "M12 20v2",
         "m4.9 4.9 1.4 1.4", "m17.7 17.7 1.4 1.4", "M2 12h2", "M20 12h2",
         "m6.3 17.7-1.4 1.4", "m19.1 4.9-1.4 1.4"],
  // Mond
  dunkel: ["M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"],
  // Winkel: Rubrik auf- und zuklappen, wie die Pfeile im Kopf
  runter: ["m6 9 6 6 6-6"],
  hoch: ["m18 15-6-6-6 6"],
};

const SINNBILDER = {
  // Schere
  ausschneiden: ["M6 3v10", "M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
                 "M18 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
                 "M18 3 8.1 16.4", "M6 3l9.9 13.4"],
  // Zwei Blaetter, wie beim Knopf «Kopieren» im Feld
  kopieren: ["M9 9h11v11H9z",
             "M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"],
  // Klemmbrett
  einfuegen: ["M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2",
              "M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z"],
};

function zeichenSinnbild(name, karte) {
  const NS = "http://www.w3.org/2000/svg";
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  // Eine GRUNDGROESSE. Ohne sie hat das Zeichen nur, was eine CSS-Regel ihm
  // gibt — und wo die fehlt, steht der Knopf leer da (so am 16.10.2026 bei
  // «Entfernen» im Vokabular, erst auf dem Bildschirmfoto bemerkt). Eine
  // Regel im Stilblatt gewinnt weiter gegen das Attribut.
  s.setAttribute("width", "1em");
  s.setAttribute("height", "1em");
  s.setAttribute("fill", "none");
  s.setAttribute("stroke", "currentColor");
  s.setAttribute("stroke-width", "2");
  s.setAttribute("stroke-linecap", "round");
  s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true");
  for (const d of ((karte || SINNBILDER)[name] || [])) {
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", d);
    s.append(p);
  }
  return s;
}

/* Das Rechtsklickmenue in den Textfeldern.
 *
 * Es gibt es, weil pywebview `NoContextMenu` setzt: im eigenen Fenster kaeme
 * sonst gar keines, und Ctrl+V allein hilft nur, wer die Tastatur nimmt.
 *
 * Warum HIER gebaut und nicht in Qt: das volle Qt-Menue traegt «Zurueck»,
 * «Neu laden» und «Seitenquelltext» — genau danach soll dieses Fenster nicht
 * aussehen. Und ein eigenes Menue wirkt im Browser genauso, ohne zweiten
 * Weg fuer dieselbe Sache.
 */
function zeichneFeldKontext(x, y, feld) {
  const menu = $("kontext");
  const st = t();
  menu.replaceChildren();
  // Drei feste Eintraege — hier rollt nie etwas, also auch kein Streifen.
  menu.classList.remove("tagmenu");
  z.kontext = null;

  // Ohne Auswahl das Wort unter der Einfuegemarke NEHMEN UND MARKIEREN.
  // Im eigenen Fenster laesst sich mit der Maus nicht immer markieren; dann
  // bestimmt der Klick das Wort, und die gesetzte Markierung SAGT, welches es
  // ist.
  let a = feld.selectionStart || 0;
  let b = feld.selectionEnd || 0;
  if (b <= a) {
    const [wa, wb] = wortgrenzen(feld.value, a);
    if (wb > wa) {
      a = wa; b = wb;
      feld.setSelectionRange(a, b);
    }
  }
  const markiert = b > a;

  const eintrag = (text, aktiv, tu, sinnbild) => {
    const k = el("button");
    k.type = "button";
    k.disabled = !aktiv;
    const marke = el("span", "marke");
    if (sinnbild) marke.append(zeichenSinnbild(sinnbild));
    k.append(marke, document.createTextNode(text));
    if (aktiv) k.addEventListener("click", async () => {
      kontextSchliessen();
      await tu();
    });
    menu.append(k);
  };

  eintrag(st.kAusschneiden, markiert, async () => {
    const w = feld.value.slice(a, b);
    try { await navigator.clipboard.writeText(w); } catch (e) { return; }
    feldSetzen(feld, feld.value.slice(0, a) + feld.value.slice(b), a);
  }, "ausschneiden");
  eintrag(st.kKopieren, markiert, async () => {
    try { await navigator.clipboard.writeText(feld.value.slice(a, b)); }
    catch (e) { /* verweigert — nichts vortaeuschen */ }
  }, "kopieren");
  eintrag(st.kEinfuegen, true, async () => {
    let w = "";
    try { w = await navigator.clipboard.readText(); }
    catch (e) {
      // ⚠️ Kein stilles Nichts. Firefox gibt die Zwischenablage nicht
      // heraus, und dann ist Ctrl+V der Weg — das gehoert gesagt.
      meldeVok(st.einfuegenHinweis);
      return;
    }
    feldSetzen(feld, feld.value.slice(0, a) + w + feld.value.slice(b),
               a + w.length);
  }, "einfuegen");

  menu.hidden = false;
  menu.style.left = "0px";
  menu.style.top = "0px";
  // ⚠️ Die Breite zuruecksetzen. Beide Menues teilen sich DASSELBE Element;
  // das Tagmenue nagelt sie fest, und ohne diese Zeile erbte das Feldmenue
  // die Breite des zuletzt geoeffneten Tagmenues.
  menu.style.width = "";
  const r = menu.getBoundingClientRect();
  menu.style.left = Math.max(8, Math.min(x, window.innerWidth - r.width - 8))
    + "px";
  menu.style.top = Math.max(8, Math.min(y, window.innerHeight - r.height - 8))
    + "px";
}

/* Ist hier ein Schreibfeld — und welches?
 *
 * `closest()` waere kuerzer, aber die Pruefung fuehrt eine strenge
 * Attrappe, in der nicht jedes Element es kennt. Selbst hochlaufen traegt
 * ueberall.
 *
 * `password` ist ausdruecklich NICHT dabei: das Menue kann kopieren, und
 * ein Kennwort gehoert nicht in die Zwischenablage. `checkbox`, `radio`
 * und `file` haben nichts zu markieren.
 */
const SCHREIBARTEN = ["text", "search", "url", "email", "tel", "number"];

function schreibfeld(ziel) {
  let k = ziel;
  for (let tiefe = 0; k && tiefe < 8; tiefe++) {
    const tag = String(k.tagName || "").toUpperCase();
    if (tag === "TEXTAREA") return (k.disabled || k.readOnly) ? null : k;
    if (tag === "INPUT") {
      const art = String(k.type || "text").toLowerCase();
      if (!SCHREIBARTEN.includes(art)) return null;
      return (k.disabled || k.readOnly) ? null : k;
    }
    k = k.parentNode || null;
  }
  return null;
}

/* Ein Feld aendern und dabei melden, dass es sich geaendert hat. Ohne das
 * `input`-Ereignis merkt die Oberflaeche nichts — der Knopf «Maskieren»
 * bliebe grau, obwohl Text dasteht. */
function feldSetzen(feld, wert, marke) {
  feld.value = wert;
  // ⚠️ Den Fokus ZURUECKGEBEN. Der Klick auf den Menueeintrag hat ihn
  // mitgenommen, und `kontextSchliessen()` versteckt danach das Element, in
  // dem er sitzt — die Einfuegemarke landet auf `<body>`. Wer im Feld
  // weiterschreiben will, muss erst wieder hineinklicken. `focus()` VOR dem
  // Setzen der Marke: ein Feld, das den Fokus bekommt, richtet sie sonst
  // selbst neu aus.
  feld.focus();
  feld.selectionStart = feld.selectionEnd = marke;
  feld.dispatchEvent(new Event("input", { bubbles: true }));
}

/* Hat das Bearbeiten einen Platzhalter zerschlagen?
 *
 * ⚠️ NUR UNBEKANNTE werden gemeldet, nicht fehlende. Einen Platzhalter zu
 * LOESCHEN ist erlaubt — genau dafuer ist das Bearbeiten da, wenn etwas
 * faelschlich maskiert wurde. Aber ein `[FULLNAM_1]` mit Tippfehler ist
 * kein Platzhalter mehr: er bleibt am Ende stehen, im fertigen Text, und
 * sieht dort aus wie eine Maskierung, die gewirkt hat.
 *
 * `POST /api/zurueckwandeln` meldet denselben Fall am Ende noch einmal.
 * Hier ist er billiger zu beheben — der Anwender steht noch im Text.
 */
function pruefePlatzhalter() {
  if (!z.antwort) return;
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  if (!Object.keys(wb).length) return;
  const text = z.antwort.maskiert || "";
  const unbekannt = [];
  PH_RE.lastIndex = 0;
  let m;
  while ((m = PH_RE.exec(text)) !== null) {
    if (!(m[0] in wb) && !unbekannt.includes(m[0])) unbekannt.push(m[0]);
  }
  if (unbekannt.length) {
    meldeVok(t().phUnbekannt.replace("{liste}", unbekannt.join(", ")));
  }
}

function kontextSchliessen() {
  z.kontext = null;
  z.kontextSuche = "";
  $("kontext").hidden = true;
}

/* Eine neue Nummer fuer ein Tag — die naechste freie ueber das ganze
 * Dokument. Derselbe Wert traegt denselben Platzhalter; eine Nummer zweimal
 * zu vergeben hiesse, zwei verschiedene Werte beim Zurueckwandeln zu
 * verwechseln.
 */
function naechsterPlatzhalter(tag) {
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  const benutzt = new Set(Object.keys(wb));
  for (const sp of ((z.antwort && z.antwort.spans) || [])) {
    if (sp.platzhalter) benutzt.add(sp.platzhalter);
  }
  let n = 1;
  while (benutzt.has(`[${tag}_${n}]`)) n++;
  return `[${tag}_${n}]`;
}

/* Maske entfernen: Platzhalter im Text durch den Originalwert ersetzen. */
function maskeEntfernen(ph) {
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  const wert = wb[ph];
  if (wert === undefined) return false;
  z.antwort.maskiert = z.antwort.maskiert.split(ph).join(wert);
  delete z.antwort.woerterbuch[ph];
  z.antwort.spans = (z.antwort.spans || [])
    .filter((sp) => sp.platzhalter !== ph);
  return true;
}

/* Einen Wert maskieren, der bisher im Klartext stand. */
function wertMaskieren(wert, tag) {
  if (!z.antwort || !wert) return false;
  const ph = naechsterPlatzhalter(tag);
  if (!z.antwort.maskiert.includes(wert)) return false;

  // Nur an WORTGRENZEN ersetzen. Jedes Vorkommen der Zeichenkette zu
  // ersetzen traefe «Damen» auch in «Sehr geehrte Damen», und ein kurzer Wert
  // wie «AG» oder «Bern» schluege mitten in anderen Woertern zu.
  //
  // ALLE passenden Vorkommen bleiben richtig: derselbe Wert an anderer Stelle
  // im Klartext waere ein Leck, und genau dafuer gibt es `propagation` in der
  // Kette. Von Hand darf es nicht schlechter sein.
  const eck = wert.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const muster = new RegExp("(?<![\\p{L}\\p{N}])" + eck
                            + "(?![\\p{L}\\p{N}])", "gu");
  if (!muster.test(z.antwort.maskiert)) return false;
  muster.lastIndex = 0;
  z.antwort.maskiert = z.antwort.maskiert.replace(muster, ph);
  z.antwort.woerterbuch = z.antwort.woerterbuch || {};
  z.antwort.woerterbuch[ph] = wert;
  z.antwort.spans = z.antwort.spans || [];
  z.antwort.spans.push({
    tag: tag, platzhalter: ph, quelle: "manuell", vertrauen: null,
    bspd: !!(z.tags[tag] || {}).bspd, start: null, end: null,
  });
  return true;
}

/* Das Tag einer bestehenden Maske wechseln. */
function tagWechseln(ph, neuTag) {
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  const wert = wb[ph];
  if (wert === undefined) return false;
  const neuPh = naechsterPlatzhalter(neuTag);
  z.antwort.maskiert = z.antwort.maskiert.split(ph).join(neuPh);
  delete z.antwort.woerterbuch[ph];
  z.antwort.woerterbuch[neuPh] = wert;
  z.antwort.spans = (z.antwort.spans || []).map((sp) =>
    sp.platzhalter === ph
      ? { ...sp, tag: neuTag, platzhalter: neuPh, quelle: "manuell",
          vertrauen: null, bspd: !!(z.tags[neuTag] || {}).bspd }
      : sp);
  return true;
}

/* Das Menue zeichnen. */
function zeichneKontext(x, y, lage, lageBehalten) {
  tippWeg();
  const menu = $("kontext");
  const st = t();
  menu.replaceChildren();
  // Nur DIESES Menue bekommt den reservierten Rollbalkenstreifen — es rollt,
  // sobald eine Rubrik aufgeht. Das Feldmenue teilt sich das Element und
  // nimmt die Klasse gleich wieder weg.
  menu.classList.add("tagmenu");
  z.kontext = lage;

  const kopf = el("div", "kopf");
  kopf.append(el("div", "wert", lage.ph
    ? (z.antwort.woerterbuch[lage.ph] || lage.ph) : lage.wort));
  kopf.append(el("div", "unter", lage.ph
    ? lage.ph + " · " + ((st.maskiertDurch || {})[lage.quelle] || st.maskiertSonst)
    : st.nichtMaskiert));
  menu.append(kopf);

  let weg = null;
  if (lage.ph) {
    weg = el("button", "entfernen");
    weg.type = "button";
    // Dasselbe Kreuz wie im Vokabular (seit 2.1), kein Schriftzeichen.
    const kreuz = el("span", "marke kreuz");
    kreuz.append(zeichenSinnbild("schliessen", KNOPFBILDER));
    weg.classList.add("mit-kreuz");
    weg.append(kreuz, document.createTextNode(st.maskeWeg));
    weg.addEventListener("click", () => handlungEntfernen(lage));
  }

  const eintrag = (tag) => {
    const meta = z.tags[tag] || {};
    const b = el("button", "tagwahl");
    b.type = "button";
    // Drei Zeichen, drei Aussagen — nie zwei gleichzeitig, sonst wird die
    // Spalte unlesbar. Reihenfolge: gesetzt schlaegt bsPD schlaegt Pruefsumme.
    let marke = " ", klasse = "marke";
    if (lage.ph && typOf(lage.ph) === tag) { marke = "•"; klasse += " jetzt"; }
    else if (meta.bspd) { marke = "⚠"; klasse += " bspd"; }
    else if (meta.pruefsumme) { marke = "✓"; klasse += " pruef"; }
    b.append(el("span", klasse, marke));
    // Dieselben Farben wie die Plaketten im maskierten Text: wer `[ORG_1]`
    // sucht, sucht nach der Farbe, die er im Text gesehen hat.
    const c = farbe(tag);
    const punkt = el("i", "punkt");
    punkt.style.background = c[1];
    b.append(punkt);
    const name = el("span", "tagname", tag);
    name.style.color = c[2];
    b.append(name);
    if (meta.bezeichnung) b.append(el("span", "bez", meta.bezeichnung));
    // `CANTON` und alles andere `tag_only` bleibt ohnehin im Klartext. Ein
    // Eintrag, der sich anklicken laesst und nichts tut, ist schlechter als
    // einer, der sichtbar gesperrt ist. Das Feld heisst `aktion` (deutsch, wie
    // der Server es liefert).
    if (meta.aktion && meta.aktion !== "mask") {
      b.disabled = true;
      b.title = st.starrHinweis;
    } else {
      b.addEventListener("click", () => handlungTag(lage, tag, meta));
    }
    return b;
  };

  /* Suche (Feedback 20.10.2026): filtert nach Tag und Bezeichnung. Treffer
   * bleiben in ihren Gruppen, und jede Gruppe mit Treffern steht offen — wer
   * «adr» tippt, sieht die Anschrift und nicht eine neue, flache Liste.
   *
   * Das Menue zeichnet sich bei jedem Zeichen neu; das Feld bekommt danach
   * Fokus und Einfuegemarke zurueck.
   */
  const suche = (z.kontextSuche || "").trim().toLowerCase();
  const passt = (tag) => !suche || tag.toLowerCase().includes(suche)
    || ((z.tags[tag] || {}).bezeichnung || "").toLowerCase().includes(suche);
  const feld = document.createElement("input");
  feld.type = "search";
  feld.className = "tagsuche suchfeld";
  feld.id = "kontext-suche";
  feld.placeholder = st.suchen;
  feld.setAttribute("aria-label", st.suchen);
  feld.autocomplete = "off";
  feld.spellcheck = false;
  feld.value = z.kontextSuche || "";
  feld.addEventListener("input", () => {
    z.kontextSuche = feld.value;
    const pos = feld.selectionStart;
    zeichneKontext(x, y, lage, true);
    const neu = $("kontext-suche");
    if (neu) { neu.focus(); neu.setSelectionRange(pos, pos); }
  });
  // Enter nimmt den einzigen Treffer — sonst nichts.
  feld.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const k = [...menu.querySelectorAll("button.tagwahl:not(:disabled)")];
    if (k.length === 1) { e.preventDefault(); k[0].click(); }
  });
  // «Maske entfernen» und die Suche auf EINER Zeile (Feedback 20.10.2026).
  // Ohne Platzhalter gibt es nichts zu entfernen; dann hat die Suche die
  // Zeile fuer sich.
  const werkzeile = el("div", "werkzeile");
  if (weg) werkzeile.append(weg);
  werkzeile.append(feld);
  menu.append(werkzeile);
  suchfeldMitKreuz(feld);
  // Nur die Gruppen rollen (seit 2.1): Kopf und Suche stehen fest, und der
  // Rollbalken laeuft nicht mehr ueber alles (Feedback 20.10.2026).
  const rollen = el("div", "tagrollen");
  menu.append(rollen);

  /* Gruppen, jede aufklappbar — auch «Häufig» (Feedback 20.10.2026).
   *
   * Die Reihenfolge ist die von `TAG_GRUPPEN`, nicht alphabetisch. Sie folgt
   * dem Dokument: Person, Herkunft, Anschrift, Erreichbarkeit — so sucht
   * jemand, der einen Brief vor sich hat.
   *
   * Jede Rubrik wird von Hand auf- und zugeklappt, und offene bleiben offen
   * (seit 2.1, Feedback 21.10.2026: wer eine zweite oeffnet und die erste
   * dabei verliert, kommt nicht mehr mit). Bis 2.0 war nur EINE offen.
   */
  const uebrig = new Set(Object.keys(z.tags));
  for (const g of Object.keys(TAG_GRUPPEN)) {
    for (const tag of TAG_GRUPPEN[g]) uebrig.delete(tag);
  }
  const gruppen = ["haeufig"].concat(Object.keys(TAG_GRUPPEN),
                                     uebrig.size ? ["rest"] : []);
  let treffer = 0;
  for (const g of gruppen) {
    const tags = (g === "haeufig" ? FREQUENT
                  : g === "rest" ? [...uebrig].sort()
                  : TAG_GRUPPEN[g]).filter((x) => z.tags[x] && passt(x));
    if (!tags.length) continue;
    treffer += tags.length;
    const offen = suche ? true
      : z.kontextOffen.has(g);
    // `aufgeklappt` und NICHT `offen`: die Klasse `.offen` gehoert der roten
    // Warnbox fuer nicht zugeordnete Platzhalter und traegt einen Rand, den der
    // Gruppenkopf sonst still miterbte.
    const kopfKnopf = el("button",
                         "gruppenkopf" + (offen ? " aufgeklappt" : ""));
    kopfKnopf.type = "button";
    kopfKnopf.setAttribute("aria-expanded", String(offen));
    kopfKnopf.dataset.gruppe = g;
    const pfeil = el("span", "pfeil");
    pfeil.append(zeichenSinnbild(offen ? "hoch" : "runter", KNOPFBILDER));
    kopfKnopf.append(document.createTextNode(
      g === "haeufig" ? st.haeufig : ((st.gruppen || {})[g] || g)), pfeil);
    kopfKnopf.addEventListener("click", (e) => {
      e.stopPropagation();
      if (suche) return;
      if (offen) z.kontextOffen.delete(g);
      else z.kontextOffen.add(g);
      // Der Kopf bleibt unter der Maus (Feedback 21.10.2026): vorher seine
      // Lage merken, neu zeichnen, und den Rollbereich so stellen, dass der
      // Kopf wieder genau dort steht. Sonst begann die neue Liste bei
      // `scrollTop = 0`, und alles sprang.
      const vorher = kopfKnopf.getBoundingClientRect().top;
      const rollVorher = rollen.scrollTop;
      // Neu zeichnen an derselben Stelle — das Menue bleibt, wo es ist. Der
      // vierte Wert haelt die Lage fest.
      zeichneKontext(x, y, lage, true);
      const neuRollen = menu.querySelector(".tagrollen");
      const neuKopf = neuRollen && neuRollen.querySelector(
        '.gruppenkopf[data-gruppe="' + g + '"]');
      if (neuRollen && neuKopf) {
        neuRollen.scrollTop = rollVorher;
        neuRollen.scrollTop += neuKopf.getBoundingClientRect().top - vorher;
      }
    });
    rollen.append(kopfKnopf);
    if (offen) for (const tag of tags) rollen.append(eintrag(tag));
  }
  if (suche && !treffer) rollen.append(el("p", "keintreffer", st.keinTreffer));

  // Erst zeigen, dann einpassen — die Hoehe steht vorher nicht fest.
  menu.hidden = false;

  // Beim Aufklappen bewegt sich nichts. Zwei Ursachen, beide hier behandelt:
  //
  // 1. Die BREITE. Der Kasten misst sich an seinem Inhalt (`min-width`
  //    15.625rem bis `max-width` 18.75rem), und die Rubrikeintraege tragen
  //    laengere Bezeichnungen als die haeufigen. Deshalb steht die Breite
  //    fest, sobald das Menue offen ist.
  // 2. Die LAGE. `Math.min(x, innerWidth - breite - 8)` haelt den Kasten im
  //    Fenster — richtig beim Oeffnen, falsch beim Neuzeichnen: mit einer
  //    geaenderten Breite rutschte er mit.
  if (lageBehalten && z.kontextLage) {
    menu.style.left = z.kontextLage.x + "px";
    menu.style.top = z.kontextLage.y + "px";
    return;
  }
  menu.style.left = "0px";
  menu.style.top = "0px";
  menu.style.width = "";
  const r = menu.getBoundingClientRect();
  // Die Breite festnageln, BEVOR eine Rubrik sie veraendern kann — und zwar
  // auf die GROESSTE zulaessige, nicht auf die gerade gemessene. Sonst kuerzten
  // die laengeren Rubrikbezeichnungen mit Auslassungspunkten, obwohl Platz da
  // waere. Die Zahl kommt aus dem CSS — eine Quelle.
  const hoechst = parseFloat(getComputedStyle(menu).maxWidth);
  menu.style.width = (Number.isFinite(hoechst) ? hoechst
                                               : Math.ceil(r.width)) + "px";
  // NACH dem Festnageln neu messen, sonst ragte der breitere Kasten rechts
  // aus dem Fenster.
  const r2 = menu.getBoundingClientRect();
  const bx = Math.min(x, window.innerWidth - r2.width - 8);
  const by = Math.min(y, window.innerHeight - r2.height - 8);
  z.kontextLage = { x: Math.max(8, bx), y: Math.max(8, by) };
  menu.style.left = z.kontextLage.x + "px";
  menu.style.top = z.kontextLage.y + "px";
  // Mit der Maus gleich lostippen. Auf dem Handy nicht: dort schoebe die
  // Tastatur das halbe Menue aus dem Bild.
  if (typeof matchMedia === "function"
      && matchMedia("(pointer: fine)").matches) {
    feld.focus({ preventScroll: true });
  }
}

async function handlungEntfernen(lage) {
  const meta = z.tags[typOf(lage.ph)] || {};
  // Bei besonders schuetzenswerten Daten nachfragen. Der Server verlangt
  // dieselbe Bestaetigung fuer `ohne` und die Vorlieben — von Hand darf sie
  // nicht fehlen, sonst ist sie ueber diesen Weg umgangen.
  if (meta.bspd && !(await frage(t().bspdWeg.replace("{}",
      typOf(lage.ph))))) {
    kontextSchliessen();
    return;
  }
  if (maskeEntfernen(lage.ph)) zeichne();
  kontextSchliessen();
}

async function handlungTag(lage, tag, meta) {
  if (meta.bspd && !lage.ph
      && !(await frage(t().bspdSetzen.replace("{}", tag)))) {
    kontextSchliessen();
    return;
  }
  const ok = lage.ph ? tagWechseln(lage.ph, tag)
                     : wertMaskieren(lage.wort, tag);
  if (ok) zeichne();
  kontextSchliessen();
}

/* --- Spalte 2: Listen --------------------------------------------------- */

function plakette(tag) {
  const c = farbe(typOf(tag));
  const s = el("span", "pill", tag);
  s.style.background = c[0];
  s.style.border = "1px solid " + c[1];
  s.style.color = c[2];
  return s;
}


function zeichneVokabular() {
  const s = t();
  const w = (z.antwort && z.antwort.woerterbuch) || {};
  const schluessel = Object.keys(w);
  const spans = (z.antwort && z.antwort.spans) || [];

  // FILTER NACH GRUPPE (seit 2.0, Entwurf des UX-Architekten) statt einer
  // Plakette je Tag: «Alle» und je Gruppe ein Knopf mit Anzahl. Gezaehlt
  // werden die EINTRAEGE des Vokabulars, nicht die Fundstellen — der Filter
  // wirkt auf die Tabelle darunter.
  const jeGruppe = {};
  for (const ph of schluessel) {
    const g = GRUPPE_VON[typOf(ph)] || "rest";
    jeGruppe[g] = (jeGruppe[g] || 0) + 1;
  }
  if (z.vokFilter !== "alle" && !jeGruppe[z.vokFilter]) z.vokFilter = "alle";
  const leg = $("legende");
  leg.replaceChildren();
  const filterKnopf = (key, wort, n, probe) => {
    const b = el("button", "chip");
    b.type = "button";
    b.setAttribute("aria-pressed", String(z.vokFilter === key));
    const punkt = el("i");
    if (probe) punkt.style.background = farbe(probe)[2];
    b.append(punkt, document.createTextNode(wort + " "), el("b", null, String(n)));
    b.addEventListener("click", () => { z.vokFilter = key; zeichneVokabular(); });
    leg.append(b);
  };
  if (schluessel.length) {
    filterKnopf("alle", s.vokAlle, schluessel.length, null);
    for (const g of Object.keys(TAG_GRUPPEN).concat(["rest"])) {
      if (!jeGruppe[g]) continue;
      filterKnopf(g, (s.gruppen || {})[g] || g, jeGruppe[g],
                  (TAG_GRUPPEN[g] || [])[0]);
    }
  }
  // Die Suche erst ab elf Eintraegen (Feedback 20.10.2026: lange Listen
  // durchsuchbar). Bei einer Handvoll ist sie nur ein Feld mehr.
  const lang = schluessel.length > 10;
  $("vok-suche").classList.toggle("suchweg", !lang);
  const vh = $("vok-suche").parentElement;
  if (vh && vh.classList && vh.classList.contains("suchhuelle")) {
    vh.classList.toggle("suchweg", !lang);
  }
  $("vok-suche").placeholder = s.suchen;
  $("vok-suche").setAttribute("aria-label", s.suchen);
  if (!lang && z.vokSuche) {
    z.vokSuche = ""; $("vok-suche").value = ""; suchStand($("vok-suche"));
  }
  const suche = z.vokSuche.trim().toLowerCase();
  const ziel = $("vokabular-inhalt");
  ziel.replaceChildren();
  if (!schluessel.length) {
    ziel.append(el("p", "vokabular-leer",
      s.keinVokabular));
    return;
  }

  const tab = el("table", "vokabular");
  const kopf = el("tr");
  // Die vierte Spalte ohne sichtbare Ueberschrift: das spart Breite fuer den
  // Originalwert (Feedback 18.10.2026). Vorgelesen wird sie trotzdem, und das
  // Kreuz erklaert sich im Tooltip.
  const wegKopf = el("th", "vok-weg-kopf");
  wegKopf.setAttribute("aria-label", s.entfernen);
  kopf.append(el("th", null, s.spalteId), el("th", null, s.spalteWert),
              el("th", null, s.spalteTyp), wegKopf);
  const thead = el("thead"); thead.append(kopf);
  const tbody = el("tbody");

  const spanZu = {};
  for (const sp of ((z.antwort && z.antwort.spans) || [])) {
    if (sp.platzhalter && !spanZu[sp.platzhalter]) spanZu[sp.platzhalter] = sp;
  }

  // Sortiert nach Platzhalter, nicht nach Fundreihenfolge — sonst springt
  // die Tabelle bei jedem Lauf, und man sucht Zeilen statt sie zu lesen.
  let treffer = 0;
  for (const ph of schluessel.sort()) {
    const typ = typOf(ph);
    if (z.vokFilter !== "alle" && (GRUPPE_VON[typ] || "rest") !== z.vokFilter) continue;
    // Gesucht wird in Platzhalter, Originalwert und Typ.
    if (suche && !(ph + " " + w[ph] + " " + typ).toLowerCase().includes(suche)) continue;
    treffer++;
    const tr = el("tr");

    // DIESELBE Plakette wie im Text von 02, aus derselben Funktion: Farbe,
    // Schrift, Groesse und die Umrandung nach Herkunft koennen so nicht
    // auseinanderlaufen (Feedback 18.10.2026).
    const td1 = el("td");
    const marke = platzhalter(ph, spanZu[ph]);
    marke.dataset.ohneWert = "1";
    td1.append(marke);

    // Der Originalwert ist aenderbar. Wer beim Zurueckwandeln einen anderen
    // Wert einsetzen will — etwa einen bewusst erfundenen —, soll das hier tun
    // koennen. Geaendert wird nur die Anzeigekopie; der Server bekommt das
    // Woerterbuch erst beim Zurueckwandeln zu sehen.
    const td2 = el("td");
    const feld = document.createElement("input");
    feld.value = w[ph];
    feld.spellcheck = false;
    feld.addEventListener("change", (e) => {
      z.antwort.woerterbuch[ph] = e.target.value;
    });
    td2.append(feld);

    // Der Typ im selben Stil, eine Stufe kleiner (`.ph-typ`): nur Auskunft.
    const td3 = el("td");
    const art = platzhalter(ph, spanZu[ph]);
    art.textContent = typ;
    art.classList.add("ph-typ");
    art.dataset.ohneWert = "1";
    td3.append(art);

    // Entfernen von HIER aus, nicht nur ueber das Klappmenue in 02: bei einem
    // grossen Dokument mit viel Uebermaskierung ist die Tabelle der Ort, an
    // dem man sie sieht. Derselbe Weg wie «Maske entfernen» — der Platzhalter
    // verschwindet im GANZEN Dokument, der Originalwert steht wieder da.
    // Ohne Rueckfrage (Entscheid 16.10.2026): gesendet wird erst, wenn in 03
    // von Hand kopiert wird, und ein Fehlklick ist im Text sichtbar.
    const td4 = el("td");
    const weg = el("button", "imfeld nurbild loeschen vok-weg");
    weg.type = "button";
    weg.title = s.vokWeg.replace("{}", ph);
    weg.setAttribute("aria-label", ph + " · " + s.entfernen);
    weg.append(zeichenSinnbild("schliessen", KNOPFBILDER));
    weg.addEventListener("click", () => {
      if (maskeEntfernen(ph)) zeichne();
    });
    td4.append(weg);

    tr.append(td1, td2, td3, td4);
    tbody.append(tr);
  }
  tab.append(thead, tbody);
  ziel.append(tab);
  if (suche && !treffer) ziel.append(el("p", "vokabular-leer", s.keinTreffer));
}

function zeichneHinweise() {
  const ziel = $("hinweise");
  ziel.replaceChildren();
  const hs = (z.antwort && z.antwort.hinweise) || [];
  // Warnungen behalten ihre eigene Zeile. Die ruhigen Meldungen stehen auf
  // einer Zeile zusammen; ein roter Warnsatz zwischen Trennpunkten ginge dabei
  // unter.
  //
  // Der eigene Hinweis steht vor denen des Servers: er betrifft den Zustand
  // hier, nicht den letzten Lauf.
  if (z.vokMeldung) {
    ziel.append(el("p", "hinweis warnhinweis", z.vokMeldung));
  }
  // Der Dialog zeigt NUR, was entstand, waehrend er offen war — siehe
  // meldeVok(). Eine Meldung aus Bereich 03 oder 05 («Vorlage gespeichert»)
  // hat dort nichts verloren.
  //
  // `textContent`, nicht `hidden`: ein leerer Absatz nimmt keinen Platz, und
  // `hidden` haette die `display`-Falle aus Punkt 64 geoeffnet.
  $("einst-meldung").textContent = z.einstMeldung || "";

  const ruhig = [];
  for (const h of hs) {
    // Der Balken traegt den Satz schon; zweimal wird er zur Tapete.
    // Gefragt wird nach dem SCHLUESSEL, nicht nach dem Satzanfang.
    if (z.zustand && z.zustand.ohne_modell
        && hinweisSchluessel(h) === "ohne_modell") {
      continue;
    }
    ruhig.push(hinweisText(h));
  }
  // Die gemessene Dauer steht seit 2.1 im Kopf von 02, nicht mehr hier.
  // Die uebrigen ruhigen Hinweise stehen hinter dem Info-Zeichen im Kopf
  // und klappen auf Klick unter dem Kopf auf (Feedback 21.10.2026: «alle
  // Meldungen in den Header»). Warnungen oben bleiben immer sichtbar.
  // Das Trennzeichen ist `·` — dasselbe wie im Untertitel der Kopfzeile und
  // in der Fusszeile.
  const info = $("hinweise-info");
  info.classList.toggle("da", ruhig.length > 0);
  info.setAttribute("aria-expanded", String(!!z.hinweiseAuf));
  info.classList.toggle("aktiv", !!z.hinweiseAuf);
  if (ruhig.length && z.hinweiseAuf) {
    const zeile = ruhig.join(" · ");
    const p = el("p", "hinweis hinweiszeile");
    // Im Hinweis zu den Vorlieben traegt das Wort «Klartext» denselben
    // hellgrauen Rahmen wie die Stellen im Text darueber: so erklaert die
    // Zeile, was der Rahmen bedeutet (Feedback 18.10.2026).
    const wort = t().klartextWort;
    const i = hs.some((h) => hinweisSchluessel(h) === "vorlieben") && wort
      ? zeile.indexOf(wort) : -1;
    if (i < 0) {
      p.textContent = zeile;
    } else {
      p.append(document.createTextNode(zeile.slice(0, i)),
               el("span", "klartext-stelle", wort),
               document.createTextNode(zeile.slice(i + wort.length)));
    }
    ziel.append(p);
  }
}

/* --- Zeichnen ----------------------------------------------------------- */

function zeichneBeschriftung() {
  const s = t();
  document.documentElement.lang = z.sprache;
  $("titel-01").textContent = s.orig;
  $("titel-02").textContent = s.masked;
  $("titel-05").textContent = s.fertig;
  $("titel-03").textContent = s.prompt;
  $("titel-04").textContent = s.antwort;
  $("titel-vokabular").textContent = s.vokabular;
  // Kurz am Knopf, genau im Tooltip (Feedback 21.10.2026), wie in den
  // anderen Fuessen.
  $("vok-herunter-text").textContent = s.herunterladen;
  $("vok-hoch-text").textContent = s.hochladen;
  for (const [kid, satz] of [["knopf-vok-herunter", s.vokHerunter],
                             ["knopf-vok-hoch", s.vokHoch]]) {
    $(kid).title = satz;
    $(kid).setAttribute("aria-label", satz);
    $(kid).setAttribute("data-autotitel", "0");
  }
  $("vorlagen-filter").placeholder = s.tplSuchen;
  $("vorlage-sichern-text").textContent = s.spalteSichern;
  // BEIDES im Tooltip, und die Reihenfolge ist Absicht.
  //
  // Wird die Spalte eng, verschwindet die Beschriftung und nur das Zeichen
  // bleibt — dann ist der Tooltip das Einzige, was den Knopf erklaert. Hier
  // steht aber schon ein WARNENDER: Vorlagen liegen dauerhaft im Klartext auf
  // der Platte. Was der Knopf tut, erraet man am Zeichen; dass die Vorlage im
  // Klartext landet, nicht.
  $("knopf-vorlage-sichern").title = s.tplSichern + ". " + s.tplWarnung;
  $("spruch").textContent = s.spruch;
  $("lokalzeiger").textContent = s.hundert;
  // Kurz und einzeilig im Feld, die Formate im Tooltip (Feedback 22.10.2026).
  $("ablage-text").textContent = s.dropN;
  $("ablage").title = s.dropT;
  // Zuletzt: erst stehen alle Beschriftungen, dann werden daraus die
  // Tooltips. Vorher gerufen traege der Tooltip die Sprache von vorhin.
  knopfTitelSetzen();
  $("leer-05").textContent = s.leer05;
  $("start-lage").textContent = s.laden;
  // Der Untertitel des Startbildschirms kommt aus `spruch1` und `spruch2`,
  // viersprachig. `el("br")` statt eines festen `<br>` im HTML: die zwei Saetze
  // sind zwei Schluessel.
  $("start-spruch").replaceChildren(
    document.createTextNode(s.spruch1), el("br"),
    document.createTextNode(s.spruch2));
  $("knopf-einstellungen").title = s.einst;
  $("neu-text").textContent = s.neu;
  $("neu-unten-text").textContent = s.neu;
  $("beispiel-text").textContent = s.beispiel;
  $("maskieren-text").textContent = z.laeuft ? s.laeuft : s.run;
  $("kopieren-text").textContent = s.kopieren;
  $("bearbeiten-text").textContent =
    z.bearbeiten ? s.bearbeitenFertig : s.bearbeiten;
  $("maskiert-feld").placeholder = s.bearbeitenHilfe;
  $("kopieren-orig-text").textContent = s.kopieren;
  // In Stuecke zerlegt, damit die Zeile nur ZWISCHEN den Aussagen bricht
  // und nie mitten in einer.
  //
  // EIN Schluessel bleibt es trotzdem. Die Zerlegung ist ABGELEITET (am « · »,
  // dem Trenner im Satz selbst) und nicht abgeschrieben: drei Schluessel je
  // Sprache waeren zwoelf Stellen fuer einen Satz.
  //
  // Ueber `createElement`, nicht `innerHTML` — die Regel kennt keine Ausnahme,
  // auch nicht fuer eigenen Text.
  const fussTeile = s.fussLinks.split(" · ");
  $("fuss-links").replaceChildren(...fussTeile.map((teil, i) =>
    el("span", "fuss-teil",
       // Ein geschuetztes Leerzeichen nach dem Punkt: das gewoehnliche am
       // Ende eines `inline-block` faellt weg, und es stand «MASCHERA
       // ·Verarbeitung» da (gesehen 20.10.2026).
       i < fussTeile.length - 1 ? teil + " ·\u00a0" : teil)));
  $("uebernahme-text").textContent = s.uebernahme;
  $("herunter-mask-text").textContent = s.herunterladen;
  $("herunter-final-text").textContent = s.herunterladen;
  $("einfuegen-antwort-text").textContent = s.einfuegen;
  // Seit 2.1 stehen diese Knoepfe im Fuss, oft nur als Zeichen. Der Tooltip
  // sagt deshalb genau, WAS kopiert, geleert oder heruntergeladen wird
  // (Feedback 20.10.2026). Nach `knopfTitelSetzen()`, damit er gewinnt.
  for (const [kid, wort] of Object.entries(s.knopfTipps || {})) {
    const k = $(kid);
    if (!k) continue;
    k.title = wort;
    k.setAttribute("aria-label", wort);
    k.setAttribute("data-autotitel", "0");
  }
  $("final-kopieren-text").textContent = s.finalKopieren;
  for (const id of ["leeren-orig-text", "leeren-final-text",
                    "leeren-antwort-text"]) {
    $(id).textContent = s.leerenA;
  }
  $("leeren-prompt-text").textContent = s.spalteLeeren;
  $("titel-hinaus").textContent = s.hinausT;
  $("titel-prompt").textContent = s.promptT;
  grossKnoepfeZeichnen();
  $("hinweise-info").title = s.hinweiseInfo;
  $("hinweise-info").setAttribute("aria-label", s.hinweiseInfo);
  // Bereich 01: auch der Platzhalter eines Textfelds wird uebersetzt. Punkt
  // 60 prueft den Text von Elementen UND ihre Platzhalter-Attribute.
  $("orig").placeholder = s.origPlatz;
  $("prompt").placeholder = s.promptPlatz;
  $("kopieren-prompt-text").textContent = s.spalteKopieren;
  $("einst-titel").textContent = s.einstT;
  $("einst-suche").placeholder = s.suchen;
  $("sprachwahl").setAttribute("aria-label", s.spracheW);
  $("einst-suche").setAttribute("aria-label", s.suchen);
  // Die Zeichen an den nachgeruesteten Knoepfen. Sie kommen hierher und
  // nicht ins HTML, weil `KNOPFBILDER` die eine Quelle ist. Gesetzt wird
  // EINMAL: `zeichneBeschriftung()` laeuft bei jedem Sprachwechsel, und ein
  // zweiter Aufruf haengte ein zweites Zeichen an.
  for (const [kennung, bild] of [["knopf-regeln-speichern", "speichern"],
                                 ["knopf-dienst-neu", "hinzufuegen"],
                                 ["knopf-dienste-vorgabe", "neustart"],
                                 ["knopf-seite-zu", "schliessen"],
                                 ["knopf-einst-abbrechen", "schliessen"]]) {
    const k = $(kennung);
    if (!k.querySelector("svg")) {
      k.prepend(zeichenSinnbild(bild, KNOPFBILDER));
    }
  }
  $("einst-zu-text").textContent = s.einstZu;
  // Zwei Stuecke, damit der Knopf eine mittlere Stufe hat: eng zeigt er
  // Zeichen + «Speichern», ganz eng nur noch das Zeichen. Ein Satz, den man
  // an beliebiger Stelle zerschneidet, braeche in einer Sprache mit anderer
  // Wortstellung falsch — deshalb zwei Schluessel und nicht ein `split()`.
  $("einst-zu-rest").textContent = s.einstZuRest;
  $("einst-abbrechen-text").textContent = s.einstAbbrechen;
  $("schritte").setAttribute("aria-label", s.ablauf);
  $("einst-darstellung-titel").textContent = s.darstellungT;
  $("einst-thema-hilfe").textContent = s.themaH;
  $("einst-thema-etikett").textContent = s.themaEtikett;
  // Der TEXT in den Span, das Zeichen davor — und nur einmal. Wer den
  // ganzen Knopf beschriebe, wuerfe das Zeichen bei jedem Sprachwechsel weg.
  //
  // Die Kennungen AUSGESCHRIEBEN und nicht zusammengesetzt: Punkt 60 und
  // Punkt 75 lesen den Quelltext und finden `"thema-" + stufe + "-text"`
  // nicht. Eine Wache, die den Quelltext liest, sieht nur, was auch
  // geschrieben steht.
  for (const [stufe, knopf, kennung, wort] of [
        ["automatisch", "thema-automatisch", "thema-automatisch-text",
         s.themaAuto],
        ["hell", "thema-hell", "thema-hell-text", s.themaHell],
        ["dunkel", "thema-dunkel", "thema-dunkel-text", s.themaDunkel]]) {
    const k = $(knopf);
    $(kennung).textContent = wort;
    if (!k.querySelector("svg")) {
      k.prepend(zeichenSinnbild(stufe, KNOPFBILDER));
    }
    k.title = wort;
  }
  $("einst-schrift-titel").textContent = s.schriftT;
  $("einst-schrift-hilfe").textContent = s.schriftH;
  $("einst-schriftart-etikett").textContent = s.schriftart;
  $("einst-schriftgroesse-etikett").textContent = s.schriftgroesse;
  $("einst-vorschau-etikett").textContent = s.vorschauE;
  $("einst-schriftprobe").textContent = s.schriftprobe;
  // Die Eintraege der Schriftwahl wechseln die Sprache mit. «IBM Plex» bleibt,
  // wie es ist: der Name der Hausschrift, in jeder Sprache derselbe.
  $("schriftart-serif").textContent = s.schriftSerif;
  $("schriftart-mono").textContent = s.schriftMono;
  $("einst-allgemein-titel").textContent = s.allgemeinT;
  $("einst-server-titel").textContent = s.serverT;
  $("einst-server-hilfe").textContent = s.serverH;
  $("einst-adresse-etikett").textContent = s.adresse;
  $("einst-port-etikett").textContent = s.port;
  zeichnePruefknopf();
  $("einst-dienste-titel").textContent = s.diensteT;
  $("einst-dienste-hilfe").textContent = s.diensteH;
  $("dienst-neu-text").textContent = s.hinzu;
  $("dienste-vorgabe-text").textContent = s.vorgabenZurueck;
  // `schliessen` und nicht `einstZu`: der Einstellungsdialog sagt
  // «Speichern & Schliessen», weil er speichert; ein Einseiter hat nichts zu
  // speichern.
  $("seite-zu-text").textContent = s.schliessen;
  $("fenster-wort").textContent = s.fensterWort;
  $("tray-wort").textContent = s.trayWort;
  $("widget-wort").textContent = s.widgetWort;
  $("einst-fenster-hilfe").textContent = s.fensterHilfe;
  $("einst-klartext-titel").textContent = s.klartextT;
  $("einst-klartext-hilfe").textContent = s.klartextH;
  $("einst-regeln-titel").textContent = s.regelnT;
  $("einst-regeln-hilfe").textContent = s.regelnH;
  $("regeln-speichern-text").textContent = s.regelnSpeichern;
  $("einpflegen04-text").textContent = s.einpflegen04;
  $("antwort04").placeholder = s.antwortPlatz;
}

/* Was hinausgeht, wird hier gebaut und angezeigt — nicht erst beim
 * Kopieren. Die Leckrate ist nicht null; deshalb muss der ausgehende Text
 * sichtbar sein, BEVOR er die Zwischenablage erreicht. Das ist der ganze
 * Grund, warum es diesen Bereich gibt.
 *
 * Und er fuellt sich NICHT von selbst: es braucht den Klick auf «Uebernahme
 * in Prompt». Wer nicht uebernommen hat, kopiert auch nichts vom Dokument —
 * `ausgehend` traegt dann nur den Prompt.
 */
function uebernommenerText() {
  return (z.uebernommen && z.antwort && z.antwort.maskiert) || "";
}

function ausgehend() {
  const anhang = uebernommenerText();
  if (!anhang) return z.prompt || "";
  return (z.prompt ? z.prompt + "\n\n" : "")
       + "———— " + t().trenner + " ————\n" + anhang;
}

function zeichneHinaus() {
  const s = t();
  $("b03").classList.toggle("vorschau-zu", !z.hinausAuf);
  $("hinaus-klappe").setAttribute("aria-expanded", String(!!z.hinausAuf));
  const ziel = $("hinaus");
  ziel.replaceChildren();
  const anhang = uebernommenerText();
  if (!z.prompt && !anhang) {
    ziel.classList.add("istleer");
    ziel.append(document.createTextNode(s.hinausLeer));
    return;
  }
  ziel.classList.remove("istleer");
  if (z.prompt) ziel.append(document.createTextNode(z.prompt));
  if (anhang) {
    ziel.append(el("span", "trenner", "———— " + s.trenner + " ————"));
    const teil = el("span", "anhang");
    maskiertSetzen(teil, anhang, (z.antwort && z.antwort.spans) || []);
    ziel.append(teil);
  }
  // Keine Zeichenzahl mehr hinter dem Titel (Feedback 21.10.2026: sie
  // irritierte nur).
}

/* Was NICHT zurueckgewandelt werden konnte, ist der wichtigste Teil der
 * Antwort. Sprachmodelle schreiben Platzhalter um — aus `[FULLNAME_1]` wird
 * `**[FULLNAME_1]**` oder `[Fullname_1]`. Der Server ersetzt das bewusst
 * nicht still, weil er sonst etwas einsetzte, das so nie vergeben wurde. Er
 * meldet es, und was er meldet, muss man SEHEN — sonst verschickt jemand
 * einen Brief, in dem `[FULLNAME_1]` steht.
 */
function zeichneOffen() {
  const s = t();
  const ziel = $("offen05");
  const gut = $("gut05");
  ziel.replaceChildren();
  gut.replaceChildren();
  if (!z.final) return;

  const fehlend = z.final.nicht_gefunden || [];
  // Geschlossen gilt fuer DIESEN Befund: `z.offenZu` haelt das Ergebnis, zu
  // dem das Kreuz geklickt wurde. Ein neues «Vokabular einpflegen» bringt
  // ein neues Ergebnis und damit den Banner wieder (Entscheid 18.10.2026).
  if (fehlend.length && z.offenZu !== z.final) {
    const kasten = el("div", "offen mit-kreuz");
    const zu = el("button", "offen-zu kreuz");
    zu.type = "button";
    zu.title = s.schliessen;
    zu.setAttribute("aria-label", s.schliessen);
    zu.append(zeichenSinnbild("schliessen", KNOPFBILDER));
    zu.addEventListener("click", () => { z.offenZu = z.final; zeichneOffen(); });
    kasten.append(zu);
    kasten.append(el("strong", null,
      s.offenText.replace("{}", String(fehlend.length))));
    const liste = el("div", "liste");
    for (const ph of fehlend) liste.append(el("span", null, ph));
    kasten.append(liste);
    // Die Hinweise des Servers nennen den wahrscheinlichen Grund —
    // meist eine abweichende Schreibweise.
    for (const h of (z.final.hinweise || [])) {
      kasten.append(el("p", "hinweis", hinweisText(h)));
    }
    ziel.append(kasten);
  } else if (z.final.ersetzt) {
    gut.textContent = s.gutText.replace("{}", String(z.final.ersetzt));
  }
}

/* Was in Bereich 05 WIRKLICH steht. Das ist ein Textfeld, und der Anwender
 * darf darin tippen — gefragt ist also der Feldinhalt und nicht die Fassung,
 * die der Server geschickt hat.
 */
function finalText() {
  const f = $("final");
  return f && !f.hidden ? f.value : (z.final && z.final.text) || "";
}

function zeichneFinal() {
  zeichneOffen();
  zeichneEinpflegenZeile();
  const hat = !!(z.final && z.final.text);
  $("leer-05").hidden = hat;
  $("final").hidden = !hat;
  const s = t();
  if (hat) {
    // NUR schreiben, wenn sich das Ergebnis wirklich geaendert hat. Bereich 05
    // ist ein Textfeld, und `zeichne` laeuft bei jeder Kleinigkeit; ein
    // bedingungsloses Setzen ueberschriebe die Bearbeitung des Anwenders und
    // wuerfe die Einfuegemarke ans Ende.
    //
    // Verglichen wird mit dem, was ZULETZT GESCHRIEBEN wurde — nicht mit dem,
    // was im Feld steht. Sonst kaeme ein zweites Einpflegen nie an, und
    // Bereich 05 zeigte weiter das alte Ergebnis. Ein veralteter fertiger Text,
    // der aussieht wie der neue, ist schlimmer als ein Knopf, der sichtbar
    // nichts tut — man kopiert ihn und merkt es nicht.
    if (z.final.text !== z.finalBearbeitet) {
      $("final").value = z.final.text;
      z.finalBearbeitet = z.final.text;
    }
    $("zahl-05").textContent = s.zeichenN($("final").value.length);
  } else {
    $("final").value = "";
    z.finalBearbeitet = null;
    $("zahl-05").textContent = s.zeichenN(0);
  }
  // Der Papierkorb gehoert hierher, hinter die Zuweisung — nicht nach
  // `zeichne()`. Dort laese er den ALTEN Feldinhalt, und der Knopf kaeme erst
  // beim naechsten Zeichnen. Die Anzeige darf nicht aus dem DOM lesen, was
  // derselbe Durchgang erst schreibt.
  $("knopf-leeren-final").disabled = !hat;
}

/* ========================================================================
 * Einstellungen
 * ==================================================================== */

function zeichneDienstliste() {
  const ziel = $("einst-dienste");
  ziel.replaceChildren();
  dienstAlphabetisch(z.dienste).forEach((d) => {
    const zeile = el("div", "dienstzeile");
    const name = document.createElement("input");
    name.value = d.name; name.placeholder = "Name";
    name.addEventListener("change", (e) => {
      d.name = e.target.value; zeichne();
    });
    const url = document.createElement("input");
    url.value = d.url; url.placeholder = "https://…"; url.spellcheck = false;
    if (d.falsch === "name") name.classList.add("falsch");
    if (d.falsch === "url") url.classList.add("falsch");
    url.addEventListener("change", (e) => { d.url = e.target.value; });
    const weg = el("button", "kreuz");
    weg.type = "button";
    weg.append(zeichenSinnbild("schliessen", KNOPFBILDER));
    weg.title = t().dienstWeg;
    weg.setAttribute("aria-label", t().dienstWeg);
    zeile.classList.add("mit-kreuz");
    weg.addEventListener("click", () => {
      z.dienste.splice(z.dienste.indexOf(d), 1);
      if (!z.dienste.some((x) => x.id === z.dienst) && z.dienste.length) {
        z.dienst = z.dienste[0].id;
      }
      zeichneDienstliste(); zeichneDienstmenu(); zeichne();
    });
    zeile.append(name, url, weg);
    ziel.append(zeile);
  });
  // Nur aktiv, wenn ein Vorgabedienst fehlt.
  const vorgabe = $("knopf-dienste-vorgabe");
  if (vorgabe) {
    const da = new Set(z.dienste.map((d) => d.id));
    vorgabe.disabled = DIENSTE.every((d) => da.has(d.id));
  }
}

/* Alle 45 Tags, die besonders schuetzenswerten sichtbar anders. `CANTON`
 * ist `tag_only` und laesst sich nicht umlegen — ein Schalter dafuer waere
 * eine Einstellung ohne Wirkung.
 */
function zeichneTagwolke() {
  const ziel = $("einst-tags");
  const st = t();
  ziel.replaceChildren();
  const uebrig = new Set(Object.keys(z.tags));
  const gruppen = Object.keys(TAG_GRUPPEN).concat(["rest"]);
  for (const g of gruppen) {
    const tags = (g === "rest" ? [...uebrig].sort()
                               : TAG_GRUPPEN[g].filter((x) => z.tags[x]));
    if (!tags.length) continue;
    ziel.append(el("h4", "tagsgruppe", (st.gruppen || {})[g] || g));
    const wolke = el("div", "tagwolke");
    for (const tag of tags) {
      uebrig.delete(tag);
      wolke.append(tagKnopf(tag));
    }
    ziel.append(wolke);
  }
  // Neu gezeichnet nach jedem Umlegen: das Suchwort gilt weiter.
  einstFiltern();
}

/* Die Beschreibung steht IM Knopf, nicht im Titel. Wer `ZSR_RCC` oder
 * `EWID` nicht kennt, kann nicht entscheiden, ob er es im Klartext lassen
 * will — und genau das ist hier die Frage. Ein `title` erscheint erst nach
 * einer Sekunde Zeigen und nie auf einem Tastfeld.
 */
function tagKnopf(tag) {
  const meta = z.tags[tag] || {};
  const an = z.klartext.includes(tag);
  const b = el("button", meta.bspd ? "bspd" : null);
  b.type = "button";
  b.setAttribute("aria-pressed", String(an));
  // Dieselben Farben wie im Text und im Kontextmenue: ein Tag, der dreimal
  // anders aussieht, muss dreimal neu gelernt werden.
  const c = farbe(tag);
  const punkt = el("i");
  if (!an) punkt.style.background = c[1];
  b.append(punkt);
  if (meta.bspd) b.append(el("span", "warn", "\u26a0"));
  const name = el("span", "tagname", tag);
  if (!an) name.style.color = c[2];
  b.append(name);
  if (meta.bezeichnung) b.append(el("span", "tagwort", meta.bezeichnung));
  if (meta.aktion && meta.aktion !== "mask") {
    b.classList.add("starr");
    b.disabled = true;
    b.title = t().starrHinweis;
  } else {
    b.addEventListener("click", () => tagUmlegen(tag, meta));
  }
  return b;
}

async function tagUmlegen(tag, meta) {
  const an = z.klartext.includes(tag);
  // Beim EINschalten eines besonders schuetzenswerten Tags fragen. Der
  // Server verlangt `auch_bspd` und wiese es sonst mit 400 ab — aber die
  // Rueckfrage ist nicht bloss Formsache: bei einem Datum kostet ein
  // Fehlgriff Lesbarkeit, bei der Religionszugehoerigkeit den Zweck des
  // ganzen Werkzeugs.
  if (!an && meta.bspd && !(await frage(t().bspdFrage.replace("{}", tag)))) {
    return;
  }
  const neu = an ? z.klartext.filter((x) => x !== tag)
                 : z.klartext.concat([tag]);
  const befund = $("einst-tags-befund");
  try {
    const d = await setzeVorlieben(neu, true);
    z.klartext = d.klartext;
    z.bspdTags = d.bspd;
    befund.className = "einst-befund gut";
    befund.textContent = warnungText(d);
  } catch (e) {
    // Nicht stillschweigend uebernehmen. Lehnt der Server ab, bleibt der
    // Schalter, wie er war — sonst zeigte die Oberflaeche eine Einstellung als
    // gesetzt, die nirgends gilt.
    befund.className = "einst-befund schlecht";
    befund.textContent = fehlerText(e);
  }
  zeichneTagwolke();
}

/* WOHIN EIN FEHLER BEIM SPEICHERN GEHOERT (Issue #11).
 *
 * Bis 16.10.2026 landete JEDER Fehler in `#einst-befund` — und das steht im
 * Abschnitt Server. «Dienst 1 hat keinen Namen.» stand so unter Adresse und
 * Port, und wer bei den Diensten weiter unten stand, sah gar nichts: «es
 * passiert nichts».
 *
 * Unterschieden wird am SCHLUESSEL des Servers (`core/einstellungen.py`),
 * nicht am Text — der ist uebersetzt. Was keinem Abschnitt gehoert, steht in
 * der Fusszeile neben den Knoepfen.
 */
function befundFuer(e) {
  const k = String((e && e.schluessel) || "");
  if (/^dienst/.test(k)) return $("einst-dienste-befund");
  if (/^(adresse|port)_/.test(k)) return $("einst-befund");
  return $("einst-fuss-befund");
}

/* Das Feld, an dem es scheiterte, rot umranden. Die Nummer des Servers
 * zaehlt in der GESENDETEN Liste (`gesendet`), nicht in der Anzeige — die ist
 * alphabetisch. Deshalb wird das Objekt gesucht und am Objekt markiert. */
function feldMarkieren(e, gesendet) {
  const k = String((e && e.schluessel) || "");
  const w = (e && e.werte) || {};
  let d = null;
  if (k === "dienst_ohne_namen") d = gesendet[Number(w.nummer) - 1] || null;
  else if (w.name) d = gesendet.find((x) => String(x.name || "").trim() === w.name) || null;
  if (d) d.falsch = k === "dienst_ohne_namen" ? "name" : "url";
  if (/^adresse_/.test(k)) $("einst-adresse").classList.add("falsch");
  if (/^port_/.test(k)) $("einst-port").classList.add("falsch");
}

function befundeLeeren() {
  for (const id of ["einst-befund", "einst-dienste-befund",
                    "einst-fuss-befund"]) {
    $(id).className = "einst-befund";
    $(id).textContent = "";
  }
  $("einst-adresse").classList.remove("falsch");
  $("einst-port").classList.remove("falsch");
  for (const d of z.dienste) delete d.falsch;
}

/* Ein leerer Name oder eine Adresse ohne `https://` haelt den Dialog
 * offen und nennt den Grund. Zumachen und den Stand verwerfen waere die
 * schlechtere Antwort: der Anwender hat gerade etwas eingetippt.
 *
 * Der Grund steht seit 17.10.2026 BEIM ABSCHNITT, und der Dialog rollt hin.
 */
async function einstellungenSchliessen() {
  befundeLeeren();
  try {
    await sichereEinstellungen();
  } catch (e) {
    const befund = befundFuer(e);
    feldMarkieren(e, gesendeteDienste());
    befund.className = "einst-befund schlecht";
    befund.textContent = fehlerText(e);
    zeichneDienstliste();
    befund.scrollIntoView({ block: "center" });
    zeichne();
    return;
  }
  z.einstMeldung = "";
  z.einstVorher = null;
  $("einst").hidden = true;
  zeichne();
}

/* WAS BEIM OEFFNEN GALT — fuer «Abbrechen».
 *
 * ⚠️ Eine TIEFE Kopie der Dienste: die Eingabefelder in
 * `zeichneDienstliste()` schreiben direkt in die Objekte von `z.dienste`
 * (`d.name = …`). Eine flache Kopie der Liste truege dieselben Objekte und
 * stellte nichts her.
 *
 * Nicht darin, weil schon gespeichert und nicht zurueckzunehmen:
 * Klartext-Tags (beim Umlegen), eigene Regeln (eigener Knopf), Tray und
 * Schmales Fenster (`merkeFenster()` sofort).
 */
function einstMomentaufnahme() {
  return {
    dienste: z.dienste.map((x) => ({ ...x })),
    dienst: z.dienst,
    eigenesFenster: z.eigenesFenster,
    thema: z.thema,
    schriftart: z.schriftart,
    schriftgroesse: z.schriftgroesse,
    adresse: $("einst-adresse").value,
    port: $("einst-port").value,
  };
}

/* Abbrechen: Knopf, Escape und der Klick auf den Hintergrund. Was nur in
 * `z` und in den Feldern stand, geht zurueck auf den Stand beim Oeffnen —
 * auch Farben und Schrift, die beim Waehlen sofort wirken. */
function einstellungenAbbrechen() {
  const m = z.einstVorher;
  if (m) {
    z.dienste = m.dienste.map((x) => ({ ...x }));
    z.dienst = m.dienst;
    z.eigenesFenster = m.eigenesFenster;
    z.thema = m.thema;
    z.schriftart = m.schriftart;
    z.schriftgroesse = m.schriftgroesse;
    $("einst-adresse").value = m.adresse;
    $("einst-port").value = m.port;
    $("schalter-fenster").setAttribute("aria-checked",
                                       String(z.eigenesFenster));
    $("einst-schriftgroesse").value = String(z.schriftgroesse);
    $("einst-schriftart").value = z.schriftart;
    themaAnwenden();
    schriftAnwenden();
    zeichnePruefknopf();
    zeichneDienstmenu();
  }
  befundeLeeren();
  z.einstMeldung = "";
  z.einstVorher = null;
  $("einst").hidden = true;
  zeichne();
}

/* Einen Dialog von oben zeigen — beim Wiederoeffnen beginnen Hilfe,
 * Einstellungen und Impressum oben.
 *
 * ZWEI ELEMENTE ROLLEN, NICHT EINES:
 *
 *   `.einst-hintergrund`  rollt, sobald der Dialog hoeher ist als das
 *                         Fenster
 *   `.einst-rumpf`        rollt den Inhalt IM Dialog
 *
 * Wer nur eines zuruecksetzt, behebt es bei einer Fenstergroesse und bei
 * der anderen nicht.
 *
 * EINE Stelle fuer alle drei Dialoge: `einstellungenOeffnen()` zeigt die
 * Einstellungen, `seiteZeigen()` baut Hilfe UND Impressum in dieselbe
 * Huelle.
 */
function dialogVonOben(huelle, rumpf) {
  huelle.hidden = false;
  huelle.scrollTop = 0;
  rumpf.scrollTop = 0;
}

async function einstellungenOeffnen() {
  z.einstMeldung = "";
  dialogVonOben($("einst"), $("einst-rumpf"));
  befundeLeeren();
  z.einstVorher = einstMomentaufnahme();
  $("einst-regeln-befund").textContent = "";
  $("einst-tags-befund").textContent = "";
  try {
    const v = await holeVorlieben();
    z.klartext = v.klartext || [];
    z.bspdTags = v.bspd || [];
    if ((v.unbekannt || []).length) {
      const b = $("einst-tags-befund");
      b.className = "einst-befund schlecht";
      b.textContent = t().unbekannteTags.replace("{}", v.unbekannt.join(", "));
    }
  } catch (e) { z.klartext = []; }
  try {
    const r = await holeRegeln();
    z.regelnYaml = r.yaml || "";
    $("einst-regeln").value = z.regelnYaml;
    if (r.fehler) {
      const b = $("einst-regeln-befund");
      b.className = "einst-befund schlecht";
      b.textContent = meldungText(r.fehler, r.fehler_schluessel,
                                  r.fehler_werte);
    }
  } catch (e) { /* Regeln fehlen: leeres Feld ist die richtige Anzeige */ }
  zeichneTagwolke();
  zeichneDienstliste();
  $("einst-suche").value = "";
  suchStand($("einst-suche"));
  einstFiltern();
}

/* Die Einstellungen durchsuchen (seit 2.1, Feedback 20.10.2026).
 *
 * Trifft das Wort einen Abschnittstitel oder seine Erklaerung, steht der
 * ganze Abschnitt da. Sonst bleibt ein Abschnitt, in dem es vorkommt — in
 * einer Beschriftung, einem Dienstnamen, einem Feldwert. In den Klartext-
 * Tags, der laengsten Liste, wird je Tag gefiltert, und Gruppen ohne
 * Treffer verschwinden mit ihrer Ueberschrift.
 *
 * Eine KLASSE (`suchweg`) und nicht `hidden`: die Fensterabschnitte setzt
 * das Skript schon ueber `hidden`, und die Suche darf keinen davon zeigen.
 */
let einstSucheAktiv = false;
function einstFiltern() {
  const feld = $("einst-suche");
  const q = ((feld && feld.value) || "").trim().toLowerCase();
  if (!q && !einstSucheAktiv) return;
  einstSucheAktiv = !!q;
  const rumpf = $("einst-rumpf");
  const enthaelt = (knoten) => {
    let text = (knoten.textContent || "").toLowerCase();
    for (const f of knoten.querySelectorAll("input")) {
      text += " " + String(f.value || "").toLowerCase();
    }
    return text.includes(q);
  };
  const zeigen = (k, ja) => k.classList.toggle("suchweg", !ja);
  let irgendwo = false;
  for (const teil of rumpf.querySelectorAll(".einst-teil")) {
    const kopf = [...teil.querySelectorAll("h3, .einst-hilfe")]
      .some((k) => (k.textContent || "").toLowerCase().includes(q));
    const wolken = [...teil.querySelectorAll(".tagwolke")];
    let sichtbar;
    if (!q || kopf) {
      for (const k of teil.querySelectorAll(".suchweg")) zeigen(k, true);
      sichtbar = true;
    } else if (wolken.length) {
      sichtbar = false;
      for (const w of wolken) {
        let n = 0;
        for (const b of w.children) {
          const ja = enthaelt(b);
          zeigen(b, ja);
          if (ja) n++;
        }
        zeigen(w, n > 0);
        const h = w.previousElementSibling;
        if (h && h.classList.contains("tagsgruppe")) zeigen(h, n > 0);
        if (n) sichtbar = true;
      }
    } else {
      sichtbar = enthaelt(teil);
    }
    zeigen(teil, sichtbar);
    if (sichtbar && !teil.hidden) irgendwo = true;
  }
  $("einst-keintreffer").textContent = q && !irgendwo ? t().keinTreffer : "";
}

/* Die Dienste alphabetisch nach Name, ohne Rücksicht auf Gross- und
 * Kleinschreibung; ein Eintrag ohne Namen (gerade neu angelegt) steht
 * zuletzt, damit er beim Tippen nicht davonspringt. Eine KOPIE: die Reihenfolge
 * in `z.dienste` bleibt die gespeicherte. */
function dienstAlphabetisch(liste) {
  return [...liste].sort((a, b) => {
    if (!a.name !== !b.name) return a.name ? -1 : 1;
    return String(a.name).localeCompare(String(b.name), undefined,
                                        { sensitivity: "base" });
  });
}

function dienstJetzt() {
  return z.dienste.find((d) => d.id === z.dienst) || z.dienste[0]
         || { id: "?", name: "?", url: "" };
}

/* ========================================================================
 * Das Burgermenue
 *
 * Die ADRESSEN stehen in `app/static/adressen.json` und nur dort. Wer eine
 * aendert, aendert eine Zeile in einer Datei und fasst keinen Code an.
 *
 * Die BESCHRIFTUNGEN stehen nicht dort, sondern in `TEXTE` — vier Sprachen.
 *
 * Die Datei kommt vom EIGENEN Server, wie `maske.svg`. Das ist kein
 * Nachladen von aussen.
 * ====================================================================
 */

async function ladeAdressen() {
  try {
    const a = await fetch("adressen.json");
    if (!a.ok) throw serverFehler({}, a.status);
    const d = await a.json();
    z.adressen = Array.isArray(d.eintraege) ? d.eintraege : [];
  } catch (e) {
    // ⚠️ Kein lautes Scheitern: ein fehlendes Menue ist aergerlich, aber
    // es haelt niemanden vom Maskieren ab. Der Knopf verschwindet dann.
    z.adressen = [];
  }
}

/* Im eigenen Fenster laeuft die Oberflaeche unter pywebview, und das
 * setzt `window.pywebview`. Nur dort ergibt «Im Browser oeffnen» einen
 * Sinn — im Browser waere es ein Knopf, der die Seite noch einmal
 * daneben aufmacht. */
function imEigenenFenster() {
  return typeof window !== "undefined" && !!window.pywebview;
}

/* Ein Dienst wird als VERWEIS geoeffnet, wo `window.open` nicht verlaesslich
 * ist: im eigenen Fenster unter macOS und Windows. Unter Linux (Qt) und im
 * Browser geht `window.open`. */
function dienstUeberVerweis() {
  const plattform = typeof navigator !== "undefined"
    ? String(navigator.platform || "") : "";
  return imEigenenFenster() && !/linux/i.test(plattform);
}

/* Genau das, was ein Menue-Link ist: `<a target="_blank" rel="noopener …">`.
 * Die Anwendung oeffnet ihn selbst im Standardbrowser. Der Verweis wird
 * angelegt, angeklickt und wieder entfernt — alles in einem Zug, damit die
 * Nutzergeste noch gilt. */
function dienstOeffnenAlsVerweis(url) {
  const a = document.createElement("a");
  a.href = url;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/* Das Symbol im Infobereich baut `app/fenster.py` unter Linux mit Qt und
 * unter Windows mit `pystray`. Unter macOS gibt es keines; ein Schalter
 * dafuer liesse sich bedienen und bewirkte nichts. */
function ablagefachMoeglich() {
  const plattform = typeof navigator !== "undefined"
    ? String(navigator.platform || "") : "";
  return imEigenenFenster() && /linux|win/i.test(plattform);
}

/* Hilfe und Impressum stehen in `seiten.js`. Die Begruendung steht dort
 * im Kopf.
 *
 * Unter node gibt es kein `<script>` davor, also wird sie hier nachgeladen.
 * Im Browser ist sie da, und `require` gibt es nicht — die Abfrage deckt
 * beide Faelle ohne einen zweiten Ladeweg.
 */
if (typeof globalThis.MASCHERA_SEITEN === "undefined"
    && typeof require === "function") {
  require("./seiten.js");
}
const SEITEN = globalThis.MASCHERA_SEITEN;

/* Ein Stueck Text in einen Knoten haengen — Zeichenkette oder Liste.
 *
 * `createTextNode` und `el()`, NIE `innerHTML`. Deshalb kommt die
 * Auszeichnung als Daten und nicht als Zeichen im Text: ein Zerleger fuer
 * `**fett**` haette am Ende doch Markup gebaut.
 */
/* `{mb}` kommt aus `/api/zustand` und steht NICHT im Text.
 *
 * Die Obergrenze ist `MAX_UPLOAD` in `app/serve.py`. Der Hilfetext NENNT
 * sie, er kennt sie nicht — sonst stuende nach dem naechsten Verschieben der
 * Grenze in der Hilfe etwas anderes als im Server.
 *
 * Faellt die Antwort aus, bleibt `{mb}` stehen statt einer erfundenen Zahl:
 * eine sichtbare Luecke ist besser als eine falsche Zusage.
 */
function seitenWert(text) {
  const mb = z.zustand && z.zustand.max_mb;
  return mb ? String(text).replace("{mb}", String(mb)) : String(text);
}

function textHinein(knoten, inhalt) {
  if (!Array.isArray(inhalt)) {
    knoten.textContent = inhalt == null ? "" : seitenWert(inhalt);
    return knoten;
  }
  for (const stueck of inhalt) {
    if (Array.isArray(stueck)) {
      // ["b", "…"] — mehr Arten gibt es nicht, und mehr braucht es nicht.
      knoten.append(el(stueck[0], null, seitenWert(stueck[1])));
    } else {
      knoten.append(document.createTextNode(seitenWert(stueck)));
    }
  }
  return knoten;
}

/* Das Kopfstueck der beiden Einseiter: Maske, Wortmarke, Untertitel.
 *
 * Fuer BEIDE Seiten: sie teilen sich die Huelle des Einstellungsdialogs.
 * Der Untertitel kommt aus `spruch1`/`spruch2` — denselben Schluesseln, die
 * der Startbildschirm benutzt.
 */
function seitenKopf(st) {
  const kopf = el("div", "seite-kopf");
  const bild = el("img", "maske");
  bild.src = maskeAdresse();
  bild.alt = "";
  const rechts = el("div");
  // Die Wortmarke in drei Stuecken — das CH steht fett, wie ueberall.
  const marke = el("div", "marke");
  marke.append(document.createTextNode("MAS"), el("b", null, "CH"),
               document.createTextNode("ERA"));
  const spruch = el("p", "spruch");
  spruch.append(document.createTextNode(st.spruch1), el("br"),
                document.createTextNode(st.spruch2));
  rechts.append(marke, spruch);
  kopf.append(bild, rechts);
  return kopf;
}

/* Einen Einseiter zeichnen. `welche` ist `hilfe` oder `impressum`.
 *
 * Gebaut mit `createElement` und `textContent`. Der Grundsatz «nie
 * `innerHTML` mit Serverdaten» kennt keine Ausnahme, und eine Ausnahme «das
 * hier ist ja eigener Text» ist der Anfang der naechsten.
 */
function seiteZeigen(welche) {
  const st = t();
  const bloecke = (SEITEN[welche] || {})[z.sprache]
                  || (SEITEN[welche] || {}).de || [];
  $("seite-titel").textContent = st[welche === "hilfe" ? "mHilfe"
                                                      : "mImpressum"];
  const rumpf = $("seite-rumpf");
  rumpf.replaceChildren();
  rumpf.append(seitenKopf(st));

  for (const [art, inhalt] of bloecke) {
    if (art === "h") {
      rumpf.append(el("h3", "seite-h", inhalt));
    } else if (art === "p") {
      rumpf.append(textHinein(el("p", "seite-p"), inhalt));
    } else if (art === "rot") {
      // Rot heisst hier dasselbe wie ueberall: «geht hinaus». Der Hinweis steht
      // zwischen 03 und 04, weil das der einzige Moment ist, in dem der Anwender
      // das Werkzeug verlaesst — und er ist der einzige rote Absatz der Hilfe.
      // Waere er einer von vielen, sagte die Farbe nichts mehr.
      rumpf.append(textHinein(el("p", "seite-rot"), inhalt));
    } else if (art === "ul") {
      const liste = el("ul", "seite-liste");
      for (const zeile of inhalt) {
        liste.append(textHinein(el("li"), zeile));
      }
      rumpf.append(liste);
    } else if (art === "tab") {
      const tab = el("div", "seite-tab");
      for (const [links, rechts] of inhalt) {
        tab.append(textHinein(el("div", "seite-tab-links"), links),
                   textHinein(el("div", "seite-tab-rechts"), rechts));
      }
      rumpf.append(tab);
    }
  }
  dialogVonOben($("seite"), rumpf);
}

function seiteSchliessen() { $("seite").hidden = true; }

/* «Nach Updates suchen»: fragt `POST /api/neueste` und zeigt das Ergebnis in
 * derselben Huelle wie Hilfe und Impressum. Gefragt wird NUR hier, auf Klick.
 * Der Verweis zur Download-Seite steht in jedem Fall da — auch wenn GitHub
 * nicht erreichbar ist, ist der Weg zur neuesten Fassung bekannt.
 */
async function neuesteZeigen(seite) {
  const st = t();
  $("seite-titel").textContent = st.mUpdate;
  const rumpf = $("seite-rumpf");
  rumpf.replaceChildren();
  rumpf.append(seitenKopf(st));
  const zeile = el("p", "seite-p", st.neuesteSucht);
  rumpf.append(zeile);
  const verweis = el("a", "seite-p", st.neuesteSeite);
  verweis.href = seite;
  verweis.target = "_blank";
  verweis.rel = "noopener noreferrer";
  dialogVonOben($("seite"), rumpf);
  try {
    const a = await fetch("/api/neueste", { method: "POST" });
    const d = await a.json().catch(() => ({}));
    if (!a.ok) throw serverFehler(d, a.status);
    const satz = (d.neuer ? st.neuesteNeu : st.neuesteAktuell)
      .replace("{neueste}", String(d.neueste || ""))
      .replace("{aktuell}", String(d.aktuell || ""));
    zeile.textContent = satz;
  } catch (e) {
    zeile.className = "seite-p fehler-text";
    zeile.textContent = fehlerText(e);
  }
  if (seite) rumpf.append(verweis);
}

function zeichneBurger() {
  const knopf = $("knopf-burger");
  const menu = $("burgermenu");
  const st = t();
  knopf.title = st.menu;
  menu.replaceChildren();

  const sichtbar = z.adressen.filter(
    (e) => e && e.schluessel
           && (e.dialog ? true
                        : e.selbst ? imEigenenFenster()
                                   : e.url !== undefined));
  // Ohne Eintraege kein Knopf — ein Menue, das leer aufgeht, ist ein Fehler.
  knopf.hidden = !sichtbar.length;
  if (!sichtbar.length) { menu.hidden = true; return; }

  for (const e of sichtbar) {
    const wort = st[e.schluessel] || e.schluessel;
    // Ein Eintrag mit `dialog` fuehrt NICHT hinaus, sondern oeffnet eine Seite
    // im Fenster. Hilfe und Impressum liegen im Paket: ein Werkzeug, das damit
    // wirbt, dass nichts hinausgeht, darf seine eigene Hilfe nicht von einem
    // fremden Server holen.
    if (e.dialog) {
      const b = el("button", null);
      b.type = "button";
      b.append(zeichenSinnbild(e.bild, MENUEBILDER),
               document.createTextNode(wort));
      b.addEventListener("click", () => {
        burgerAuf(false);
        seiteZeigen(e.dialog);
      });
      menu.append(b);
      continue;
    }
    // «Nach Updates suchen» fuehrt nicht hinaus, sondern fragt ueber den
    // eigenen Server nach und zeigt das Ergebnis im Fenster.
    if (e.aktion === "neueste") {
      const b = el("button", null);
      b.type = "button";
      b.append(zeichenSinnbild(e.bild, MENUEBILDER),
               document.createTextNode(wort));
      b.addEventListener("click", () => {
        burgerAuf(false);
        neuesteZeigen(e.url || "");
      });
      menu.append(b);
      continue;
    }
    const ziel = e.selbst ? window.location.href : (e.url || "");
    if (!ziel) {
      // Ein Eintrag OHNE Adresse steht grau da und sagt, warum — ein Knopf,
      // der beim Klick nichts tut, liest sich als Fehler.
      const b = el("button", "tot");
      b.type = "button";
      b.disabled = true;
      b.append(zeichenSinnbild(e.bild, MENUEBILDER),
               document.createTextNode(wort),
               el("span", "spaeter", st.mHilfeBald));
      menu.append(b);
      continue;
    }
    // Ein echter Verweis und kein Knopf mit `location`: so laesst er sich mit
    // der mittleren Maustaste oder dem eigenen Rechtsklickmenue behandeln, wie
    // auf jeder Seite.
    const a = el("a", null);
    a.append(zeichenSinnbild(e.bild, MENUEBILDER),
             document.createTextNode(wort));
    a.href = ziel;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.addEventListener("click", () => burgerAuf(false));
    menu.append(a);
  }
  menu.hidden = !z.burgerOffen;
  knopf.setAttribute("aria-expanded", String(z.burgerOffen));
}

function burgerAuf(offen) {
  z.burgerOffen = offen;
  zeichneBurger();
}

function zeichneDienstmenu() {
  const menu = $("dienstmenu");
  menu.replaceChildren();
  for (const d of dienstAlphabetisch(z.dienste)) {
    const b = el("button", d.id === z.dienst ? "aktiv" : null, d.name);
    b.type = "button";
    b.addEventListener("click", () => {
      z.dienst = d.id;
      menu.hidden = true;
      $("knopf-dienstmenu").setAttribute("aria-expanded", "false");
      zeichne();
      // Sofort merken, nicht erst beim naechsten Schliessen der Einstellungen:
      // sonst stuende nach dem Neuladen wieder der alte Dienst da.
      sichereEinstellungen().catch(() => {});
    });
    menu.append(b);
  }
}

/* DIE SCHRITTLEISTE (seit 2.0, Entwurf des UX-Architekten).
 *
 * Sie FOLGT dem Ablauf, statt ihn zu steuern: welcher Schritt dran ist, ergibt
 * sich aus dem Zustand — maskiert? uebernommen? Antwort da? zurueckgewandelt?
 * Ein Klick springt zur Kachel.
 */
const SCHRITT_ZIEL = ["b01", "b02", "b03", "b04", "b05"];

/* Der WEITESTE erreichte Stand zaehlt, nicht der erste fehlende. Wer ohne
 * «Übernahme in Prompt» eine Antwort einpflegt, ist trotzdem bei 05 — vorher
 * blieb der Ring an 02 stehen und Schritt 5 ohne Haken (Feedback
 * 20.10.2026).
 */
function schrittJetzt() {
  if (!(z.antwort && z.antwort.maskiert)) return 0;
  if (z.final) return 5;
  if (String(z.antwort04 || "").trim()) return 3;
  if (z.uebernommen) return 2;
  return 1;
}

function schrittAnspringen(i) {
  const ziel = SCHRITT_ZIEL[i];
  // Die Leiste zentriert den ANGETIPPTEN Schritt, bis der Ablauf weiterrueckt.
  z.schrittMitte = i;
  schrittZentrieren(true);
  schrittMitteMarkieren();
  if (gestapelt()) {
    springeZu(ziel);
  }
  const k = $(ziel);
  k.classList.add("blitz");
  setTimeout(() => k.classList.remove("blitz"), 900);
}

const SCHRITTBILDER = { haken: ["M5 12.5 10 17.5 19 7"] };

/* Wo man ist: der angetippte Schritt bekommt einen Rahmen, solange er nicht
 * der aktuelle ist — der traegt seine Pille schon. Ohne den Rahmen stand
 * einspaltig ein Schritt in der Mitte, und nichts sagte, dass er der
 * gemeinte ist (Feedback 18.10.2026). */
function schrittMitteMarkieren() {
  const nav = $("schritte");
  if (!nav) return;
  const jetzt = schrittJetzt();
  (nav.querySelectorAll(".schritt") || []).forEach((b, i) => {
    b.classList.toggle("mitte", z.schrittMitte === i && i !== jetzt);
  });
  // Dieselbe Aussage an der Kachel: angetippt schlaegt aktuell, und der
  // Ring bleibt stehen, bis der Ablauf weiterrueckt (Feedback 20.10.2026).
  const gemeint = Math.min(z.schrittMitte == null ? jetzt : z.schrittMitte,
                           SCHRITT_ZIEL.length - 1);
  SCHRITT_ZIEL.forEach((kennung, i) => {
    const k = $(kennung);
    if (k) k.classList.toggle("amzug", i === gemeint && !z.einpflegenLaeuft);
  });
}

/* Den Schritt in der Mitte der Leiste zeigen — nur wenn sie seitlich rollt
 * (einspaltig). Mittig steht der angetippte, sonst der aktuelle. */
function schrittZentrieren(weich) {
  const nav = $("schritte");
  if (!nav || nav.scrollWidth <= nav.clientWidth) return;
  const i = z.schrittMitte == null ? schrittJetzt() : z.schrittMitte;
  const b = (nav.querySelectorAll(".schritt") || [])[Math.min(i, 4)];
  if (!b) return;
  const links = (b.offsetLeft || 0) - ((nav.clientWidth || 0) - (b.offsetWidth || 0)) / 2;
  const ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (typeof nav.scrollTo === "function") {
    // Weich nur nach einem Tippen. Beim Neuzeichnen sofort: `zeichne()`
    // laeuft waehrend eines Laufs oft hintereinander, und jedes Neuzeichnen
    // brach das Gleiten ab — die Leiste blieb daneben stehen (gemessen).
    nav.scrollTo({ left: links, behavior: weich === true && !ruhig ? "smooth" : "auto" });
  } else {
    nav.scrollLeft = links;
  }
}

function zeichneSchritte() {
  const nav = $("schritte");
  const namen = t().schritte || [];
  const jetzt = schrittJetzt();
  // Rueckt der Ablauf weiter, gilt wieder der aktuelle Schritt als Mitte.
  if (z.schrittZuletzt !== jetzt) { z.schrittMitte = null; z.schrittZuletzt = jetzt; }
  nav.replaceChildren();
  namen.forEach((wort, i) => {
    const b = el("button", "schritt"
      + (i < jetzt ? " fertig" : i === jetzt ? " jetzt" : "")
      + (i === 2 || i === 3 ? " aussen" : ""));
    b.type = "button";
    if (i === jetzt) b.setAttribute("aria-current", "step");
    // Der Haken als Zeichnung mit kraeftigem Strich: das Schriftzeichen «✓»
    // ging im gruenen Kreis fast unter (Feedback 18.10.2026).
    const nr = el("span", "schritt-nr", i < jetzt ? null : String(i + 1));
    if (i < jetzt) {
      const h = zeichenSinnbild("haken", SCHRITTBILDER);
      h.setAttribute("stroke-width", "3.5");
      nr.append(h);
    }
    b.append(nr, el("span", null, wort));
    b.addEventListener("click", () => schrittAnspringen(i));
    nav.append(b);
    if (i < namen.length - 1) nav.append(el("span", "schritt-pfeil", "→"));
  });
  schrittMitteMarkieren();
  // Nach dem Zeichnen, damit die Masse stimmen — mit `setTimeout` und nicht
  // `requestAnimationFrame`: der haelt in einem verdeckten Fenster an, und die
  // Leiste bliebe dann am falschen Schritt stehen (gemessen).
  setTimeout(() => schrittZentrieren(false), 0);
}

function zeichne() {
  zeichneBeschriftung();
  zeichneSchritte();
  zeichneBurger();
  // Auch das Dienstmenue neu zeichnen, sonst taucht ein neu eingetragener
  // Dienst im Sendeknopf erst nach dem Neuladen auf.
  zeichneDienstmenu();
  zeichneMaskiert();
  zeichneVokabular();
  zeichneVorlagen();
  zeichneHinweise();
  zeichneHinaus();
  const s = t();
  $("zahl-01").textContent = s.zeichenN(z.orig.length);
  const k = (z.antwort && z.antwort.kennzahlen) || null;
  // Ein eingelesenes Vokabular hat keine Kennzahlen — es kommt aus einem
  // anderen Lauf. «0 Zeichen · Maskierter Anteil 0 %» neben 41 Eintraegen
  // behauptete etwas anderes als die Tabelle daneben. Lieber die Laenge
  // zeigen und den Anteil weglassen.
  const mt = (z.antwort && z.antwort.maskiert) || "";
  // Alles, was der Lauf zu sagen hat, steht im Kopf (Feedback 21.10.2026):
  // Laenge, davon maskiert, Dauer. Die Zeile darunter ist weg.
  const teile02 = [s.zeichenN(mt.length)];
  if (k) teile02.push(s.davonMaskiert.replace("{}", String(k.maskiert)));
  if (k && typeof k.dauer_ms === "number") {
    teile02.push(s.inDauer.replace("{}", dauerWort(k.dauer_ms)));
  }
  $("zahl-02").textContent = teile02.join(" · ");
  const w = (z.antwort && z.antwort.woerterbuch) || {};
  const eintraege = s.eintraegeN(Object.keys(w).length);
  $("zahl-vokabular").textContent = k
    ? s.anteilW + " " + Math.round((k.anteil || 0) * 100) + " % · " + eintraege
    : eintraege;
  // Diese Zahlen werden beim Zusammenstauchen als Erstes gekuerzt — sie sind
  // Auskunft, kein Bedienelement. Der volle Text steht im Tooltip.
  $("zahl-vokabular").title = $("zahl-vokabular").textContent;
  $("zahl-02").title = $("zahl-02").textContent;
  $("knopf-maskieren").disabled = z.laeuft || !z.orig.trim();
  $("knopf-kopieren").disabled = !z.antwort;
  $("knopf-vok-herunter").disabled = !hatWoerterbuch();
  $("knopf-vorlage-sichern").disabled = !z.prompt.trim();
  $("schalter-fenster").setAttribute("aria-checked",
                                     String(z.eigenesFenster));
  $("schalter-tray").setAttribute("aria-checked", String(z.tray));
  $("schalter-widget").setAttribute("aria-checked",
                                    String(z.fenstermodus === "widget"));
  // Nur im eigenen Fenster: Ablagefach, Fenstermass und die Server-
  // einstellungen. Ein Schalter, der sich bedienen laesst und nichts
  // bewirkt, ist schlimmer als keiner. Also ausblenden statt grau setzen:
  // grau wirft die Frage auf, wie man es einschaltet.
  //
  // Der ganze Abschnitt «Allgemein» geht mit; sonst stuende eine
  // Ueberschrift ueber einem Satz, der von einem Neustart spricht, und
  // darunter nichts.
  //
  // Der Abschnitt «Server» ebenso: Adresse und Port liest nur
  // `app/fenster.py`, beim Start. Im Browser ist die Seite bereits vom
  // Dienst ausgeliefert, den sie einstellen wuerde — eine Aenderung wirkte
  // dort nie.
  //
  // `.einst-schalterzeile` traegt `display: flex`, und das schlaegt das
  // `[hidden]` des Browsers. Die Gegenregel steht im CSS; Punkt 64 prueft
  // sie fuer jedes Element, dessen `hidden` hier gesetzt wird.
  for (const kennung of ["teil-allgemein", "zeile-widget",
                         "einst-fenster-hilfe", "teil-server"]) {
    $(kennung).hidden = !imEigenenFenster();
  }
  $("zeile-tray").hidden = !ablagefachMoeglich();
  // «Einfuegen» in Bereich 04 gibt es nur im eigenen Fenster.
  //
  // Der Knopf ruft `navigator.clipboard.readText()`, und das ist der Seite
  // im Browser gesperrt — Chrome fragt um Erlaubnis, Firefox gibt es gar
  // nicht heraus. Im eigenen Fenster ist es ausdruecklich erlaubt.
  //
  // Ausblenden und nicht grau setzen. Der Weg im Browser ist Ctrl+V oder
  // das native Rechtsklickmenue.
  $("knopf-einfuegen-antwort").hidden = !imEigenenFenster();
  $("knopf-kopieren-orig").disabled = !z.orig.trim();
  $("knopf-kopieren-prompt").disabled = !z.prompt.trim();
  // ZWEI Ansichten in EINEM Kasten, und sie schliessen einander aus: die
  // gesetzte Ansicht und das Schreibfeld zum Korrigieren. Der «Weg zurueck»
  // als dritte ist seit 2.1 weg (Feedback 20.10.2026: niemand verstand ihn);
  // zurueck geht es ueber 04.
  const bearbeitet = z.bearbeiten && !!z.antwort;
  $("maskiert").hidden = bearbeitet;
  $("maskiert-feld").hidden = !bearbeitet;
  $("knopf-bearbeiten").disabled = !(z.antwort && z.antwort.maskiert);
  $("knopf-bearbeiten").classList.toggle("aktiv", bearbeitet);
  $("knopf-uebernahme").disabled = !(z.antwort && z.antwort.maskiert);
  zeichneFinal();
  $("knopf-einpflegen04").disabled =
    !z.antwort04.trim() || !hatWoerterbuch();
  // Seit 2.1 stehen die Leerknoepfe immer da und sind grau, solange nichts
  // zu leeren ist (Feedback 20.10.2026) — ein Knopf, der erscheint und
  // verschwindet, verschiebt seine Nachbarn im Fuss.
  $("knopf-leeren-antwort").disabled = !z.antwort04.trim();
  $("knopf-leeren-orig").disabled = !z.orig.trim();
  $("knopf-leeren-prompt").disabled = !z.prompt.trim();
  $("knopf-herunter-mask").disabled = !(z.antwort && z.antwort.maskiert);
  const fertig = !!(z.final && z.final.text);
  $("knopf-herunter-final").disabled = !fertig;
  $("knopf-final-kopieren").disabled = !fertig;
  // Der Pfeil daempft mit, aber er wird NICHT deaktiviert: die Dienstwahl
  // ist auch dann sinnvoll, wenn noch nichts zu senden ist — man stellt sie
  // ein, BEVOR man den Text einfuegt. Ein blasser Knopf neben einer
  // kraeftigen Kante saehe aber kaputt aus.
  const nichtsZuSenden = !ausgehend().trim();
  $("knopf-senden").disabled = nichtsZuSenden;
  $("knopf-dienstmenu").classList.toggle("gedaempft", nichtsZuSenden);
  if (!z.sendeUhr) {
    sendeBeschriftung();
  }
  // Der Warnhinweis wird IMMER geschrieben, auch waehrend die
  // Knopfbeschriftung auf «Kopiert» steht. Er haengt am Dienst, nicht am
  // Zustand des Knopfes — genau beim Kopieren geht ja etwas hinaus.
  const warnsatz = s.onlineWarnung.replace("{}", dienstJetzt().name);
  // Seit 2.0 steht hier kurz «Verlaesst dein Geraet» — die Zone, die vorher
  // als Leiste ueber der Spalte stand, gleich neben dem Knopf, der hinaus-
  // schickt. Der lange Satz mit dem Dienst bleibt als Tooltip.
  $("onlinewarnung-text").textContent = s.zoneHinaus;
  $("onlinewarnung").title = warnsatz;
  $("maskiert").classList.toggle("istleer", !z.antwort);
  fussEinpassenBald();
}

/* --- Handlungen --------------------------------------------------------- */

/* --- Fortschritt --------------------------------------------------------
 *
 * Der Balken zeigt eine GEMESSENE Zahl. Nach dem Tokenisieren steht die
 * Zahl der Fenster fest, bevor gerechnet wird — der Server meldet sie unter
 * `/api/fortschritt`. Ein Balken, der eine Zahl erfindet, waere in diesem
 * Werkzeug besonders falsch.
 *
 * Solange nichts zu melden ist, wandert er, statt eine Laenge
 * vorzutaeuschen. Erst wenn `von` dasteht, wird er zu einer Strecke.
 */
function laufAnzeigen(stand) {
  // Ein Rennen: ist der Lauf in wenigen Millisekunden vorbei, kommt die
  // Antwort von `fortschrittHolen` NACH `laufAus` an und machte den Balken
  // wieder sichtbar — wandernd und ohne Ende. Die Wache steht HIER und nicht
  // nur an der Abfrage: so ist jede spaete Meldung wirkungslos, gleich woher
  // sie kommt.
  if (!z.laeuft) return;
  const kasten = $("lauf");
  const fuellung = $("lauf-fuellung");
  const wort = $("lauf-wort");
  const st = t();
  kasten.hidden = false;
  if (!stand || !stand.von) {
    kasten.classList.add("unbestimmt");
    fuellung.style.width = "";
    wort.textContent = st.lWartet;
    return;
  }
  kasten.classList.remove("unbestimmt");

  // Die letzten 8 % gehoeren dem Rest der Kette. Die Fenster decken NUR die
  // Modellerkennung ab — davor liegt das Zerlegen, danach Regeln,
  // Zusammenfuehren und Ersetzen. Ein Balken, der beim letzten Fenster voll
  // dasteht und dann noch eine Sekunde rechnet, haelt seine Zusage nicht.
  // Lieber 92 % und ehrlich.
  const MODELLTEIL = 0.92;
  const roh = Math.max(0, Math.min(1, stand.schritt / stand.von));
  const anteil = stand.phase === "maskieren" ? 0.96 : roh * MODELLTEIL;
  fuellung.style.width = Math.round(anteil * 100) + "%";

  // «Fenster 9 von 12» ist ehrlich (der einzige Wert, den der Server vorher
  // exakt kennt), sagt dem Anwender aber nichts. Die Zahl bleibt als Tooltip;
  // sichtbar steht der Prozentsatz und, sobald er sich schaetzen laesst, die
  // Restzeit.
  kasten.title = st.lModell
    .replace("{}", stand.schritt).replace("{}", stand.von);

  if (stand.phase === "maskieren") {
    wort.textContent = st.lMaskieren;
    return;
  }

  // Die Restzeit erst ab dem ZWEITEN beobachteten Fenster. Aus einem
  // einzigen Messpunkt laesst sich keine Geschwindigkeit ableiten — was dann
  // dastuende, waere geraten.
  const jetzt = (window.performance || Date).now();
  if (!z.laufMessung || z.laufMessung.schritt > stand.schritt) {
    z.laufMessung = { zeit: jetzt, schritt: stand.schritt };
  }
  const fenster = stand.schritt - z.laufMessung.schritt;
  const verstrichen = jetzt - z.laufMessung.zeit;
  let text = Math.round(anteil * 100) + " %";
  if (fenster >= 1 && verstrichen > 0) {
    const jeFenster = verstrichen / fenster;
    const rest = jeFenster * Math.max(0, stand.von - stand.schritt);
    if (rest >= 500) text += " · " + st.lRest.replace("{}", restWort(rest));
  }
  wort.textContent = text;
}

/* Eine Restzeit ist eine Schaetzung, und sie soll auch so aussehen. Volle
 * Sekunden, keine Nachkommastelle — «noch etwa 4,3 s» taeuscht eine
 * Genauigkeit vor, die die Hochrechnung nicht hat. Nebenbei entfaellt
 * damit die Frage nach dem Dezimaltrennzeichen in vier Sprachen. */
function restWort(ms) {
  const s = Math.round(ms / 1000);
  if (s < 60) return Math.max(1, s) + " s";
  const m = Math.round(s / 60);
  return m + " min";
}

function laufAus() {
  clearTimeout(z.fortschrittUhr);
  z.fortschrittUhr = null;
  z.laufMessung = null;
  $("lauf").hidden = true;
  $("lauf").classList.remove("unbestimmt");
  $("lauf-fuellung").style.width = "";
}

/* Ein Zeitgeber, der sich SELBST neu stellt — kein `setInterval`. Ist der
 * Server beschaeftigt, staut ein Intervall die Anfragen auf, und die
 * Anzeige haengt der Rechnung hinterher, die sie beschreibt.
 */
async function fortschrittHolen() {
  if (!z.laeuft) return;
  try {
    const a = await fetch("/api/fortschritt");
    // Nach JEDEM `await` neu fragen, ob noch gelaufen wird. Zwischen dem
    // Absenden und der Antwort kann der Lauf zu Ende sein.
    if (a.ok && z.laeuft) laufAnzeigen(await a.json());
  } catch (e) { /* das Maskieren laeuft weiter; nur die Anzeige nicht */ }
  if (z.laeuft) z.fortschrittUhr = setTimeout(fortschrittHolen, 250);
}

/* Wie breit ist der Rollbalken auf DIESEM Geraet?
 *
 * Gemessen, nicht geraten: eine feste Zahl im CSS ist fuer einen schmalen
 * Balken zu gross und fuer einen breiten zu knapp, und dann kleben die
 * Feldknoepfe daran.
 *
 * Ein Probeklotz mit `overflow: scroll`: Aussenbreite minus Innenbreite.
 * Ueberlagernde Rollbalken geben 0 — dann bleibt der Abstand der blosse
 * Innenabstand, ohne Loch daneben.
 */
function messeRollbalken() {
  const probe = document.createElement("div");
  probe.style.position = "absolute";
  probe.style.top = "-9999px";
  probe.style.width = "100px";
  probe.style.height = "100px";
  probe.style.overflow = "scroll";
  document.body.appendChild(probe);
  const breite = probe.offsetWidth - probe.clientWidth;
  probe.remove();
  document.documentElement.style.setProperty(
    "--rollbalken", Math.max(0, breite) + "px");
  return breite;
}

/* --- Gestapelte Ansicht -------------------------------------------------
 *
 * Dieselben Grenzen wie im CSS, und dieselbe Einheit: `em` misst die
 * Schrift des BROWSERS, nicht `--skala`. Stuenden hier Pixel und dort `em`,
 * liefen Anzeige und Verhalten bei jedem Schriftwechsel auseinander.
 */
/* Die Grenze liegt seit 2.0 bei 81.24em (rund 1300 px): darunter stuenden
 * die drei Karten so schmal, dass das Vokabular seitlich rollte und 03
 * umbrach (Feedback des Anwenders, 18.10.2026). Vorher 59.99em. */
function gestapelt() {
  // Dieselbe Abfrage wie im CSS, Wort fuer Wort — Breite ODER Hoehe. Sonst
  // stuenden die Kaesten untereinander, aber es gaebe keinen Sprung zum
  // naechsten Schritt.
  return window.matchMedia(
    "(max-width: 81.24em), (max-height: 44em)").matches;
}

function einspaltig() {
  return window.matchMedia("(max-width: 39.99em)").matches;
}

/* Zum naechsten Schritt springen — aber NUR, wenn die Kaesten
 * untereinander stehen. Nebeneinander sieht man den naechsten ohnehin.
 *
 * `prefers-reduced-motion` wird geachtet: wer Bewegung abgestellt hat,
 * bekommt denselben Sprung ohne Fahrt.
 */
/* Welcher Behaelter rollt gerade?
 * Das WANDERT. Dreispaltig rollt `main.raster`; gestapelt rollt die SEITE,
 * damit die Fusszeile im Fluss steht statt am Fensterrand zu kleben.
 * `scrollTop` auf einem Element, das nicht rollt, wirft nicht — es tut
 * nichts, deshalb muss hier der richtige stehen.
 */
function rollBehaelter() {
  // An `gestapelt()` gebunden und NICHT an gemessene Hoehen. Es ist dieselbe
  // Abfrage, die im CSS entscheidet, welcher Behaelter rollt. Ein
  // `scrollHeight > clientHeight` haette dasselbe MEISTENS ergeben und beim
  // leeren Fenster das Gegenteil.
  if (!gestapelt()) return $("raster");
  return document.scrollingElement || document.documentElement;
}

function springeZu(kennung) {
  // Wer springt, will die Kachel im Raster sehen: eine vergroesserte geht
  // zuerst zurueck an ihren Platz.
  if (z.gross && z.gross !== kennung) kachelGross(null);
  if (!gestapelt()) return;
  const ziel = $(kennung);
  const rollen = rollBehaelter();
  if (!ziel || !rollen) return;

  // Wohin? Der Abstand des Ziels zum oberen Rand des Rollbehaelters, auf
  // dessen aktuellen Stand gerechnet. `scrollIntoView` waere kuerzer, aber
  // dann gehoert die Bewegung dem Browser.
  const ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (ruhig || typeof requestAnimationFrame !== "function") {
    ziel.scrollIntoView({ behavior: "auto", block: "start" });
    return;
  }

  const von = rollen.scrollTop;
  // Die Rollwurzel rechnet anders als ein rollendes Element.
  //
  // `document.scrollingElement.getBoundingClientRect().top` ist
  // **`-scrollTop`**: der Kasten der Wurzel beginnt am Dokumentanfang und
  // wandert beim Rollen mit hinauf. Ihn abzuziehen ADDIERTE den Rollstand
  // ein zweites Mal.
  //
  // Ein rollendes ELEMENT (`#raster`) verhaelt sich umgekehrt: sein Kasten
  // steht still, und sein `top` gehoert abgezogen.
  //
  // Tueckisch, weil der erste Sprung stimmt: die Seite steht noch oben, der
  // Rollstand ist 0 und der Fehler ebenso. Erst der zweite landet doppelt so
  // tief.
  const wurzel = document.scrollingElement || document.documentElement;
  const obenIm = rollen === wurzel ? 0
                                   : rollen.getBoundingClientRect().top;
  // Die Kopfzeile steht davor. Gestapelt ist sie `position: sticky` und
  // liegt ueber dem oberen Rand — ein Sprung auf Viewport-Null legte den
  // Kastentitel genau darunter.
  //
  // Gemessen, nicht als Zahl eingetragen: die Hoehe haengt an `--skala` und
  // am Umbruch der Kopfzeile. `position` wird mitgefragt: nebeneinander
  // steht die Kopfzeile im Fluss und verdeckt nichts.
  //
  // Darunter klebt die Schrittleiste und verdeckt ebenso — ohne sie lag der
  // Kachelkopf hinter ihr (Feedback 18.10.2026). Dazu ein Luftraum, damit
  // der obere Rand der Kachel samt Ecken sichtbar bleibt.
  const klebt = (el) => el && getComputedStyle(el).position === "sticky"
    ? el.getBoundingClientRect().height : 0;
  const kopf = $("kopfzeile");
  const leiste = $("schritte");
  const luft = klebt(leiste)
    ? parseFloat(getComputedStyle(document.documentElement).fontSize) * 0.75
    : 0;
  const verdeckt = klebt(kopf) + klebt(leiste) + luft;
  const nach = von + ziel.getBoundingClientRect().top - obenIm - verdeckt;
  if (Math.abs(nach - von) < 2) return;

  // Eigene Bewegung statt `behavior: "smooth"`. `smooth` tut in manchen
  // eingebauten Browsern gar nichts und ist in anderen zu schnell, um als
  // Bewegung sichtbar zu sein. Selbst gerechnet ist sie ueberall gleich:
  // schnell los, sanft aus (kubisch), rund vier Zehntel.
  const dauer = 420;
  const beginn = (window.performance || Date).now();
  const schritt = (jetzt) => {
    const t = Math.min(1, ((jetzt || (window.performance || Date).now())
                           - beginn) / dauer);
    const weich = 1 - Math.pow(1 - t, 3);
    rollen.scrollTop = von + (nach - von) * weich;
    if (t < 1) requestAnimationFrame(schritt);
  };
  requestAnimationFrame(schritt);
  // Absicherung (gemessen 21.10.2026): ein angefordertes Bild kam im
  // eingebauten Browser beim ersten Sprung nach dem Laden nie, und die Seite
  // blieb stehen. Nach der Bewegungszeit steht der Sprung auf jeden Fall am
  // Ziel; lief die Bewegung, aendert das nichts mehr.
  setTimeout(() => { rollen.scrollTop = nach; }, dauer + 120);
}

/* Die Sprachwahl hat zwei Gesichter: Knopfreihe und, bei wenig Breite,
 * ein Pulldown (seit 2.1, Feedback 20.10.2026). Beide zeigen dieselbe Wahl. */
function spracheMarkieren() {
  for (const k of document.querySelectorAll("[data-sprache]")) {
    k.classList.toggle("aktiv", k.dataset.sprache === z.sprache);
  }
  const wahl = $("sprachwahl");
  if (wahl) wahl.value = z.sprache;
}

async function spracheWaehlen(sprache) {
  if (!I18N[sprache]) return;
  z.sprache = sprache;
  spracheMarkieren();
  await ladeTags();
  zeichne();
  merkeSprache();
}

/* Das Vokabular steht seit 2.1 auch einspaltig immer offen (Feedback
 * 20.10.2026): das Auf- und Zuklappen war ein Handgriff mehr, und zugeklappt
 * sah niemand, was maskiert ist. */

/* Die Beschriftung des Sendeknopfes: der Dienstname FETT, damit man sieht,
 * wohin es geht.
 *
 * Zusammengesetzt aus Knoten, nicht mit `innerHTML`. Der Dienstname kommt
 * aus den Einstellungen, also vom Server; ein eigener Dienst heisst, was
 * der Anwender tippt, und das darf kein Markup werden. `tests/test_app.py`
 * zaehlt die `innerHTML`-Stellen.
 */
/* Jeder Knopf, der ein Zeichen UND ein Wort traegt, bekommt sein Wort auch
 * als Tooltip: wird ein Fuss eng, blendet das CSS die Beschriftungen aus,
 * und ohne Tooltip waere der Knopf stumm.
 *
 * Eigene Titel werden nicht ueberschrieben: am Speichern-Knopf steht eine
 * Warnung ueber Vorlagen im Klartext. Deshalb die Marke `data-autotitel` —
 * was diese Funktion gesetzt hat, darf sie ueberschreiben, alles andere
 * nicht.
 */
function knopfTitelSetzen() {
  for (const knopf of document.querySelectorAll("button")) {
    if (!knopf.querySelector || !knopf.querySelector("svg")) continue;
    const wort = String(knopf.textContent || "").trim();
    if (!wort) continue;
    const eigen = knopf.getAttribute("title");
    if (eigen && knopf.getAttribute("data-autotitel") !== "1") continue;
    knopf.setAttribute("title", wort);
    knopf.setAttribute("data-autotitel", "1");
  }
}

function sendeBeschriftung() {
  const teile = t().sendenZu.split("{}");
  const ziel = $("senden-text");
  ziel.replaceChildren(
    document.createTextNode(teile[0] || ""),
    el("b", null, dienstJetzt().name),
    document.createTextNode(teile[1] || ""),
  );
}

/* «1.2 s» statt «1234 ms» — und ab einer Minute mit Minuten. */
function dauerWort(ms) {
  if (ms < 1000) return ms + " ms";
  if (ms < 60000) return (ms / 1000).toFixed(1).replace(".", ",") + " s";
  const m = Math.floor(ms / 60000);
  return m + " min " + Math.round((ms - m * 60000) / 1000) + " s";
}

async function laufen() {
  // Maskiert, was in Spalte 1 steht — und NUR das. Eine Datei kommt ueber
  // `ablegen` dort hinein, nie direkt hierher.
  if (z.laeuft) return;
  abgleichOrig();
  z.laeuft = true;
  // Jeder neue Lauf nimmt die Uebernahme zurueck. Sonst stuende in der
  // dritten Spalte der Text von VORHIN, waehrend links schon ein anderes
  // Dokument liegt — und was dort steht, ist genau das, was hinausgeht.
  z.uebernommen = false;
  zeichne();
  $("fehler").replaceChildren();
  laufAnzeigen(null);
  // Schon jetzt springen, nicht erst am Ende. Der Balken steht ueber dem
  // Textfeld von 02; wer untereinander arbeitet, saehe ihn sonst gar nicht.
  // So steht der Kasten still da, und der Balken laeuft sichtbar darin.
  handlungSprung("b02");
  fortschrittHolen();
  try {
    z.antwort = await maskiere(z.orig);
    z.bearbeiten = false;
    z.vokMeldung = null;
  } catch (e) {
    z.antwort = null;
    z.bearbeiten = false;
    $("fehler").append(el("p", "fehler-text", fehlerText(e)));
    // Die uebrigen Hinweise darunter — etwa der Balken «ohne Modell», der
    // beim leeren Befund doppelt zaehlt.
    for (const h of (e.hinweise || [])) {
      // Ein Hinweis, der die Fehlerzeile wiederholt, gehoert nicht ein zweites
      // Mal darunter. Verglichen wird der SCHLUESSEL, nicht der Satz — so trifft
      // es auch nach einem Sprachwechsel zu. Der Textvergleich bleibt als zweiter
      // Weg: ein Server ohne Schluessel schickt nur Saetze.
      if (e.schluessel && hinweisSchluessel(h) === e.schluessel) continue;
      if ((h && h.text) === e.message || h === e.message) continue;
      if (z.zustand && z.zustand.ohne_modell
          && hinweisSchluessel(h) === "ohne_modell") {
        continue;
      }
      $("fehler").append(el("p", "hinweis", hinweisText(h)));
    }
  } finally {
    z.laeuft = false;
    laufAus();
    zeichne();
    // Hier wird nicht gesprungen. Der Sprung VOR dem Lauf setzt den Kasten
    // bereits an seinen Platz. Wer den maskierten Text ansieht, korrigiert
    // darin — eine Bewegung in dem Augenblick naehme ihm die Stelle weg, an der
    // er gerade ist. Im Fehlerfall steht dort die Meldung, und weggerollt
    // laese sie niemand.
  }
}

async function ablegen(datei) {
  // Ablegen liest EIN und maskiert NICHT. Maskieren ist die Handlung, um
  // die es hier geht; sie hat einen eigenen Knopf, weil sie eine Entscheidung
  // ist.
  if (z.laeuft) return;
  z.laeuft = true;
  zeichne();
  $("fehler").replaceChildren();
  try {
    const d = await liesDatei(datei);
    z.orig = d.original || "";
    $("orig").value = z.orig;
    // Was vorher da war, gehoert nicht zu diesem Text.
    z.antwort = null;
    z.bearbeiten = false;
    z.vokMeldung = null;
    // Hinweise des Lesers — mehrere Nachrichten in einer Mailbox, eine
    // ungewoehnliche Kodierung — gehoeren angezeigt, auch wenn das Lesen
    // geglueckt ist. Sie sind kein Fehler, aber sie aendern, was in
    // Spalte 1 steht.
    for (const h of (d.hinweise || [])) {
      $("fehler").append(el("p", "hinweis", hinweisText(h)));
    }
  } catch (e) {
    $("fehler").append(el("p", "fehler-text", fehlerText(e)));
    for (const h of (e.hinweise || [])) {
      // Dieselbe Doppelung wie beim Maskieren, siehe dort.
      if (e.schluessel && hinweisSchluessel(h) === e.schluessel) continue;
      if ((h && h.text) === e.message || h === e.message) continue;
      $("fehler").append(el("p", "hinweis", hinweisText(h)));
    }
  } finally {
    z.laeuft = false;
    zeichne();
  }
}

function verbinde() {
  // Die Knoepfe stehen im HTML, nicht hier. Uebersetzt wird ueber
  // `textContent` auf den Spannen darin — die Regel gegen `innerHTML` soll
  // absolut bleiben, auch fuer feste Zeichenketten.

  $("orig").addEventListener("input", (e) => {
    z.orig = e.target.value;
    zeichne();
  });
  $("knopf-maskieren").addEventListener("click", () => laufen());
  // «Beispiel» beginnt von vorne wie «Neu» (seit 2.1, Feedback
  // 20.10.2026): dieselbe eine Frage, dann ALLES leer und das Beispiel in 01.
  // Vorher blieben Prompt, Uebernahme, Antwort und Ergebnis stehen, und
  // nach der naechsten Uebernahme waren gleich alle fuenf Schritte erledigt.
  $("knopf-beispiel").addEventListener("click", async () => {
    if (!(await neuOk())) return;
    allesLeeren();
    z.orig = BEISPIEL[z.sprache] || BEISPIEL.de;
    $("orig").value = z.orig;
    zeichne();
    handlungSprung("b01");
  });
  // EIN Ablauf, mehrere Einstiege — der Knopf unten in 05, der oben in 01
  // und die Wortmarke tun dasselbe, samt Rueckfrage. Zwei Wege zu derselben
  // Handlung driften auseinander, und dann fragt der eine nach und der
  // andere nicht — bei einem Knopf, der ein Woerterbuch wegwirft, ist das die
  // teure Richtung.
  for (const kennung of ["knopf-neu", "knopf-neu-unten", "knopf-marke"]) {
    $(kennung).addEventListener("click", async () => {
      if (!(await neuOk())) return;
      allesLeeren();
      zeichne();
      handlungSprung("b01");
    });
  }
  $("knopf-kopieren").addEventListener("click", async () => {
    if (!z.antwort) return;
    try {
      await navigator.clipboard.writeText(z.antwort.maskiert || "");
      $("kopieren-text").textContent = t().kopiert;
      setTimeout(() => { $("kopieren-text").textContent = t().kopieren; },
                 1400);
    } catch (e) { /* Zwischenablage verweigert */ }
  });

  $("knopf-kopieren-orig").addEventListener("click", async () => {
    if (!z.orig.trim()) return;
    try {
      await navigator.clipboard.writeText(z.orig);
      $("kopieren-orig-text").textContent = t().kopiert;
      setTimeout(() => {
        $("kopieren-orig-text").textContent = t().kopieren;
      }, 1400);
    } catch (e) { /* Zwischenablage verweigert */ }
  });

  $("datei").addEventListener("change", async (e) => {
    const d = e.target.files && e.target.files[0];
    if (!d || !(await verwerfenOk())) { e.target.value = ""; return; }
    ablegen(d);
    e.target.value = "";
  });

  const ablage = $("ablage");
  ablage.addEventListener("dragover", (e) => {
    e.preventDefault(); ablage.classList.add("drueber");
  });
  ablage.addEventListener("dragleave", () => {
    ablage.classList.remove("drueber");
  });
  ablage.addEventListener("drop", async (e) => {
    e.preventDefault(); ablage.classList.remove("drueber");
    schleierAus();
    const d = e.dataTransfer && e.dataTransfer.files &&
              e.dataTransfer.files[0];
    if (d) {
      if (await verwerfenOk()) ablegen(d);
      return;
    }
    // Apple Mail & Co. liefern ein Versprechen statt einer Datei. Kein
    // stilles Nichts: sagen, was zu tun ist, und die Typen nennen, damit ein
    // Fehlerbericht zeigt, was die Quelle wirklich mitbrachte.
    const typen = Array.prototype.slice.call(
      (e.dataTransfer && e.dataTransfer.types) || []).join(", ");
    $("fehler").replaceChildren(
      el("p", "fehler-text", t().drop_ohne_datei + (typen ? " (" + typen + ")" : "")));
  });

  // ZWEI Dinge auf der ganzen Seite, nicht nur auf der Flaeche.
  //
  // Erstens: wer eine Datei ueber das Fenster zieht, sieht, WOHIN sie gehoert
  // — die Seite dunkelt ab, die Ablageflaeche bleibt hell.
  //
  // Zweitens, und das ist kein Schmuck: ohne `preventDefault` auf dem
  // Dokument OEFFNET der Browser die abgelegte Datei und ersetzt damit die
  // Oberflaeche. Im eigenen Fenster gibt es dann keine Adresszeile, um
  // zurueckzukommen — und ein ungespeichertes Woerterbuch waere weg.
  //
  // Kein Zaehlen von dragenter/dragleave: beim Wechsel zwischen Kindelementen
  // feuert `dragleave` NACH dem `dragenter` des neuen Ziels, und der Schleier
  // flackert. Stattdessen haelt ein Zeitgeber ihn, solange `dragover`
  // nachkommt — waehrend des Ziehens etwa alle 100 ms.
  const traegtDatei = (e) => {
    const t = e.dataTransfer && e.dataTransfer.types;
    if (!t) return false;
    return Array.prototype.indexOf.call(t, "Files") !== -1;
  };
  function schleierAus() {
    clearTimeout(z.ziehUhr); z.ziehUhr = null;
    $("ziehschleier").hidden = true;
    document.body.classList.remove("zieht");
  }
  document.addEventListener("dragover", (e) => {
    if (!traegtDatei(e)) return;
    e.preventDefault();
    $("ziehschleier").hidden = false;
    document.body.classList.add("zieht");
    clearTimeout(z.ziehUhr);
    z.ziehUhr = setTimeout(schleierAus, 250);
  });
  document.addEventListener("drop", (e) => {
    // Ausserhalb der Flaeche: nichts tun, aber die Datei auch NICHT vom
    // Browser oeffnen lassen.
    e.preventDefault();
    schleierAus();
  });

  for (const knopf of document.querySelectorAll("[data-sprache]")) {
    knopf.addEventListener("click", () => spracheWaehlen(knopf.dataset.sprache));
  }
  $("sprachwahl").addEventListener("change",
                                   (e) => spracheWaehlen(e.target.value));

  zeichneDienstmenu();

  // Rechtsklick auf den maskierten Text. Zwei Faelle: auf einem Platzhalter
  // — dann geht es um eine bestehende Maske; auf gewoehnlichem Text — dann um
  // ein Wort, das bisher im Klartext steht. Der zweite Fall ist der
  // wichtigere: dort sitzen die Lecks.
  $("maskiert").addEventListener("contextmenu", (e) => {
    if (!z.antwort) return;
    const plakette = e.target.closest && e.target.closest("[data-ph]");
    let lage = null;
    if (plakette && plakette.dataset.ph) {
      lage = { ph: plakette.dataset.ph, quelle: plakette.dataset.quelle };
    } else {
      const wort = auswahlOderWort(e.clientX, e.clientY);
      // Kein Wort gefunden: das Browsermenue durchlassen. Ein unterdruecktes
      // Menue ohne Ersatz waere schlechter als keines.
      if (!wort) return;
      lage = { ph: null, wort: wort };
    }
    e.preventDefault();
    zeichneKontext(e.clientX, e.clientY, lage);
  });

  // Eine Eigenschaft statt einer Liste: jedes Schreibfeld bekommt das Menue,
  // ohne dass jemand daran denkt — Dialog, Regeleditor, Vokabulartabelle,
  // und Vorlagenfeld eingeschlossen.
  //
  // `#maskiert` faellt NICHT darunter: es ist kein Schreibfeld, sondern eine
  // gesetzte Ansicht mit eigenem, reicherem Menue — und es wirkt auf beiden
  // Oberflaechen, weil es die Zwischenablage nie braucht.
  //
  // NUR IM EIGENEN FENSTER. Dort setzt pywebview `NoContextMenu`, und ohne
  // dieses Menue gaebe es keines. Im Browser bleibt das native: 
  //
  //   writeText()  Ausschneiden, Kopieren  geht ueberall mit Benutzergeste
  //   readText()   Einfuegen               Chrome fragt um Erlaubnis,
  //                                        Firefox gibt es der Seite gar nicht
  //
  // Das native Einfuegen ist eine Browserhandlung und kein Aufruf, den eine
  // Seite ausloesen darf — sonst koennte jede Seite mitlesen. Ein eigenes
  // Menue ersetzte im Browser also das einzige Einfuegen, das dort
  // funktioniert, durch eines, das es nicht kann.
  document.addEventListener("contextmenu", (e) => {
    if (!imEigenenFenster()) return;
    const feld = schreibfeld(e.target);
    if (!feld) return;
    e.preventDefault();
    zeichneFeldKontext(e.clientX, e.clientY, feld);
  });

  // Der Schatten unter der Kopfzeile, sobald gerollt ist: gestapelt schiebt
  // sich der Inhalt darunter, und ohne Schatten wirkte die Kante wie ein
  // Seitenanfang.
  const schattenPruefen = () => {
    $("kopfzeile").classList.toggle("gerollt", rollBehaelter().scrollTop > 2);
  };
  // Beide Roller anhoeren — welcher es ist, haengt an der Breite, und die
  // aendert sich im laufenden Fenster.
  $("raster").addEventListener("scroll", schattenPruefen);
  window.addEventListener("scroll", schattenPruefen);
  window.addEventListener("resize", schattenPruefen);
  // Die Schrittleiste klebt untereinander direkt unter der Kopfzeile — dafuer
  // braucht das Blatt deren Hoehe, und die aendert sich mit Schrift und Breite.
  const kopfMessen = () => document.documentElement.style.setProperty(
    "--kopfhoehe", $("kopfzeile").offsetHeight + "px");
  window.addEventListener("resize", kopfMessen);
  window.addEventListener("resize", fussEinpassenBald);
  window.addEventListener("resize", () => schrittZentrieren(false));
  kopfMessen();

  document.addEventListener("click", (e) => {
    const menu = $("kontext");
    if (menu && !menu.hidden && !menu.contains(e.target)) {
      kontextSchliessen();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") kontextSchliessen();
  });
  $("einst-suche").addEventListener("input", einstFiltern);
  // «Prompt + maskierter Text» klappt auf und zu (Feedback 21.10.2026);
  // zugeklappt gehoert die ganze Hoehe dem Promptfeld.
  $("hinaus-klappe").addEventListener("click", () => {
    z.hinausAuf = !z.hinausAuf;
    zeichne();
  });
  for (const b of document.querySelectorAll(".gross-knopf")) {
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      kachelGross(z.gross === b.dataset.kachel ? null : b.dataset.kachel);
    });
  }
  $("kachel-grund").addEventListener("click", () => kachelGross(null));
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !z.gross || e.defaultPrevented) return;
    // Erst ein offenes Menue oder ein Dialog, dann die grosse Kachel.
    if (!$("kontext").hidden || !$("einst").hidden || !$("frage").hidden
        || !$("seite").hidden || z.vorlagenOffen) return;
    kachelGross(null);
  });
  $("hinweise-info").addEventListener("click", () => {
    z.hinweiseAuf = !z.hinweiseAuf;
    zeichneHinweise();
  });
  $("vok-suche").addEventListener("input", (e) => {
    z.vokSuche = e.target.value;
    zeichneVokabular();
  });
  // Bei offenem Tagmenue rollt NUR seine Liste, wo die Maus auch steht
  // (Feedback 20.10.2026). Ohne das reichte der Browser das Rad ueber Kopf
  // und Suchzeile, und am Ende der Liste, an die Seite dahinter weiter.
  // `passive: false`, sonst gilt `preventDefault()` nicht.
  document.addEventListener("wheel", (e) => {
    const menu = $("kontext");
    if (!menu || menu.hidden || !menu.classList.contains("tagmenu")) return;
    e.preventDefault();
    const rollen = menu.querySelector(".tagrollen");
    if (!rollen) return;
    const zeile = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? rollen.clientHeight : 1;
    rollen.scrollTop += e.deltaY * zeile;
  }, { passive: false });
  document.addEventListener("touchmove", (e) => {
    const menu = $("kontext");
    if (!menu || menu.hidden || !menu.classList.contains("tagmenu")) return;
    const rollen = menu.querySelector(".tagrollen");
    if (rollen && rollen.contains(e.target)) return;
    e.preventDefault();
  }, { passive: false });
  // Das Vorlagenmenue haengt an einer festen Stelle: beim Rollen der Seite
  // (nicht seiner eigenen Liste) und bei Groessenaenderung geht es zu.
  document.addEventListener("scroll", (e) => {
    const menu = $("vorlagen-menu");
    if (z.vorlagenOffen && menu && !menu.contains(e.target)) vorlagenAuf(false);
  }, true);
  window.addEventListener("resize", () => { if (z.vorlagenOffen) vorlagenAuf(false); });
  // Der Tooltip haengt an einer festen Stelle; beim Rollen gehoert er weg.
  document.addEventListener("scroll", tippWeg, true);

  // --- Einstellungen ---
  $("knopf-einstellungen").addEventListener("click", einstellungenOeffnen);
  $("knopf-einst-zu").addEventListener("click", einstellungenSchliessen);
  $("knopf-einst-abbrechen").addEventListener("click", einstellungenAbbrechen);
  // Escape bricht ab — aber nicht, wenn die Rueckfrage darueber offen ist:
  // deren eigener Horcher nimmt das Escape (und ruft `preventDefault`).
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || e.defaultPrevented) return;
    if ($("einst").hidden || !$("frage").hidden) return;
    einstellungenAbbrechen();
  });
  $("frage-ja").addEventListener("click", () => frageSchliessen(true));
  $("frage-nein").addEventListener("click", () => frageSchliessen(false));
  // Ein Klick neben den Kasten ist ein Nein — nie ein Ja.
  $("frage").addEventListener("click", (e) => {
    if (e.target === $("frage")) frageSchliessen(false);
  });
  $("frage").addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); frageSchliessen(false); }
    else if (e.key === "Enter" && e.target === $("frage-eingabe")) {
      e.preventDefault(); frageSchliessen(true);
    }
  });
  $("knopf-seite-zu").addEventListener("click", seiteSchliessen);
  // Der Klick auf den Hintergrund schliesst ebenfalls. Nur der Hintergrund
  // selbst, nicht ein Kind — sonst schloesse jeder Klick im Text die Seite.
  $("seite").addEventListener("click", (e) => {
    if (e.target === $("seite")) seiteSchliessen();
  });
  // Seit 17.10.2026 ein ABBRECHEN, kein Speichern (Issue #11) — wie bei der
  // Rueckfrage: ein Klick neben den Kasten ist ein Nein, nie ein Ja.
  $("einst").addEventListener("click", (e) => {
    if (e.target === $("einst")) einstellungenAbbrechen();
  });

  // Die Portpruefung fragt wirklich nach und liest `dienst`. Wer auf 4141
  // antwortet, ist noch lange nicht MASCHERA.
  for (const feld of ["einst-adresse", "einst-port"]) {
    $(feld).addEventListener("input", () => zeichnePruefknopf());
  }
  $("knopf-pruefen").addEventListener("click", async () => {
    const befund = $("einst-befund");
    // Neue Adresse: speichern und — im eigenen Fenster — neu starten. Im
    // Browser kann sich die Seite nicht selbst neu starten; dann sagt sie,
    // ab wann es gilt.
    if (adresseGeaendert()) {
      befundeLeeren();
      try {
        await sichereEinstellungen();
      } catch (e) {
        const wo = befundFuer(e);
        feldMarkieren(e, gesendeteDienste());
        wo.className = "einst-befund schlecht";
        wo.textContent = fehlerText(e);
        zeichneDienstliste();
        wo.scrollIntoView({ block: "center" });
        return;
      }
      // Jetzt gespeichert: ein spaeteres Abbrechen nimmt das nicht zurueck.
      z.einstVorher = einstMomentaufnahme();
      if (kannNeuStarten()) {
        befund.className = "einst-befund";
        befund.textContent = t().startetNeu;
        await window.pywebview.api.neustart();
      } else {
        befund.className = "einst-befund gut";
        befund.textContent = t().giltNachNeustart;
      }
      return;
    }
    const adr = $("einst-adresse").value.trim() || "127.0.0.1";
    // Kein Rueckfall auf eine Zahl. Ist das Feld leer, gibt es nichts zu
    // pruefen, und das gehoert gesagt statt geraten: eine Pruefung gegen einen
    // erratenen Port meldete etwas ueber einen anderen Dienst, als der Anwender
    // vor sich sieht.
    const port = $("einst-port").value.trim();
    if (!port) {
      befund.className = "einst-befund schlecht";
      befund.textContent = t().portFehlt;
      return;
    }
    befund.className = "einst-befund";
    befund.textContent = t().pruefeLaeuft;
    try {
      /* nach-aussen-erlaubt: Portpruefung
       * Die EINZIGE Stelle, die eine fremde Adresse anspricht — und sie muss es,
       * sonst prueft sie nichts. Was hinausgeht, ist ein GET auf `/api/zustand`
       * an eine Adresse, die der Anwender selbst getippt hat. Kein
       * Dokumentinhalt, kein Woerterbuch, kein Platzhalter. `tests/test_app.py`
       * zaehlt die so markierten Stellen und schlaegt an, sobald es mehr als diese
       * eine wird.
       */
      const a = await fetch("http://" + adr + ":" + port + "/api/zustand");
      const d = await a.json();
      if (d.dienst !== "maschera") {
        befund.className = "einst-befund schlecht";
        befund.textContent = t().falscherDienst.replace("{}", String(d.dienst));
        return;
      }
      befund.className = "einst-befund gut";
      befund.textContent = t().dienstDa
        .replace("{v}", d.version || "?")
        .replace("{m}", d.modell || "—");
    } catch (e) {
      befund.className = "einst-befund schlecht";
      // Kommt die Anfrage nicht an, ist das die ganze Auskunft: dort horcht
      // niemand. «Keine Antwort: Keine Verbindung …» sagte dasselbe zweimal.
      befund.textContent = e instanceof TypeError
        ? t().keinDienstDa.replace("{}", adr + ":" + port)
        : t().keinDienst.replace("{}", fehlerText(e));
    }
  });

  // Vorgabedienste zurueckholen (seit 2.1, Feedback 21.10.2026): wer sie
  // beim Aufraeumen entfernt und gespeichert hat, hatte keinen Weg zurueck.
  // Fehlende werden angefuegt, eigene Dienste bleiben, nichts wird ersetzt.
  // Gespeichert wird erst mit «Speichern & schliessen», wie bei allem hier.
  $("knopf-dienste-vorgabe").addEventListener("click", () => {
    const da = new Set(z.dienste.map((d) => d.id));
    for (const d of DIENSTE) if (!da.has(d.id)) z.dienste.push({ ...d });
    zeichneDienstliste(); zeichneDienstmenu(); zeichne();
  });
  $("knopf-dienst-neu").addEventListener("click", () => {
    z.dienste.push({ id: "eigen" + Date.now(), name: "", url: "" });
    zeichneDienstliste();
    zeichne();
  });

  $("schalter-fenster").addEventListener("click", () => {
    z.eigenesFenster = !z.eigenesFenster;
    $("schalter-fenster").setAttribute("aria-checked",
                                       String(z.eigenesFenster));
  });

  // Diese beiden werden SOFORT gesichert. `app/fenster.py` liest sie beim
  // Start, nicht ueber die Oberflaeche — was hier nur in `z` stuende, waere
  // beim naechsten Oeffnen wieder fort.
  $("schalter-tray").addEventListener("click", () => {
    z.tray = !z.tray;
    $("schalter-tray").setAttribute("aria-checked", String(z.tray));
    merkeFenster();
  });
  $("schalter-widget").addEventListener("click", () => {
    z.fenstermodus = z.fenstermodus === "widget" ? "voll" : "widget";
    $("schalter-widget").setAttribute("aria-checked",
                                      String(z.fenstermodus === "widget"));
    merkeFenster();
  });

  $("knopf-regeln-speichern").addEventListener("click", async () => {
    const befund = $("einst-regeln-befund");
    try {
      const d = await setzeRegeln($("einst-regeln").value);
      befund.className = "einst-befund gut";
      befund.textContent = warnungText(d);
    } catch (e) {
      // ⚠️ Abgelehnte Regeln lassen die bestehende Datei unberuehrt — das
      // macht der Server. Hier zaehlt nur, dass der Grund sichtbar wird.
      befund.className = "einst-befund schlecht";
      befund.textContent = fehlerText(e);
    }
  });

  // Bereich 02 von Hand korrigieren: falsch markierte Bereiche oder
  // einzelne Woerter lassen sich im Text selbst berichtigen.
  //
  // Warum das traegt: `POST /api/zurueckwandeln` arbeitet ueber die
  // PLATZHALTER im Text und nicht ueber Textstellen. Ein frei bearbeiteter
  // Text laesst sich deshalb genauso zurueckwandeln — solange die Platzhalter
  // stehen bleiben. Und `zeichneMaskiert()` baut die Plaketten aus dem TEXT
  // (ueber `PH_RE`); die Spannen liefern nur Quelle und Vertrauen und werden
  // ueber den Platzhaltertext zugeordnet.
  $("knopf-bearbeiten").addEventListener("click", () => {
    z.bearbeiten = !z.bearbeiten;
    if (z.bearbeiten) {
      $("maskiert-feld").value = (z.antwort && z.antwort.maskiert) || "";
    } else {
      pruefePlatzhalter();
      zeichneMaskiert();
    }
    zeichne();
    if (z.bearbeiten) $("maskiert-feld").focus();
  });

  $("maskiert-feld").addEventListener("input", (e) => {
    if (!z.antwort) return;
    z.antwort.maskiert = e.target.value;
    // Der Zaehler im Kopf und der Kasten «Das geht hinaus» haengen daran.
    // Ohne dieses `zeichne()` zeigte die Oberflaeche waehrend des Tippens eine
    // Zeichenzahl, die nicht mehr stimmt — und mit dieser Zahl entscheidet der
    // Anwender, was er hinausgibt.
    zeichne();
  });

  // Der maskierte Text wandert in den Anhang, und es geht weiter zu 03.
  $("knopf-uebernahme").addEventListener("click", () => {
    // ⚠️ HIER wandert der maskierte Text hinueber, nirgends sonst.
    z.uebernommen = true;
    zeichne();
    handlungSprung("b03");
    $("prompt").focus();
  });

  $("antwort04").addEventListener("input", (e) => {
    z.antwort04 = e.target.value;
    zeichne();
  });
  // Auch bei Ctrl+V, nicht nur ueber den Knopf: ein Weg, der repariert, und
  // einer, der es nicht tut, waeren zwei Verhaltensweisen fuer denselben
  // Handgriff.
  //
  // `setTimeout(…, 0)`: im `paste`-Ereignis steht der neue Text noch nicht im
  // Feld. Es abzufangen und selbst einzusetzen waere kuerzer und schlechter —
  // dann ginge das Rueckgaengigmachen des Browsers verloren.
  $("antwort04").addEventListener("paste", () => {
    setTimeout(() => antwortUebernehmen($("antwort04").value), 0);
  });
  $("knopf-leeren-antwort").addEventListener("click", () => {
    z.antwort04 = ""; $("antwort04").value = ""; zeichne();
  });
  // Der Papierkorb in 05 leert NUR Bereich 05. Das Woerterbuch bleibt, und
  // der Text in 04 bleibt: wer mit dem Ergebnis unzufrieden ist, will es neu
  // einpflegen, nicht von vorne anfangen. Dafuer gibt es «Neu», und der fragt
  // vorher.
  $("knopf-leeren-final").addEventListener("click", () => {
    z.final = null;
    z.finalBearbeitet = null;
    $("final").value = "";
    zeichne();
  });
  // Der einzige Weg zurueck seit 2.1: die Antwort in 04 einpflegen.
  $("knopf-einpflegen04").addEventListener("click", () => {
    einpflegen(z.antwort04);
  });

  // Bereich 05 ist bearbeitbar. Der Zeichenzaehler muss mitgehen, sonst
  // zeigt er die Fassung des Servers zu einem Text, den der Anwender laengst
  // geaendert hat.
  $("final").addEventListener("input", () => {
    z.finalBearbeitet = $("final").value;
    $("zahl-05").textContent = t().zeichenN($("final").value.length);
  });

  $("prompt").addEventListener("input", (e) => {
    z.prompt = e.target.value;
    zeichne();
  });

  // eslint-disable-next-line no-inner-declarations
  async function inZwischenablage(text, spanne) {
    try {
      await navigator.clipboard.writeText(text);
      const alt = $(spanne).textContent;
      $(spanne).textContent = t().kopiert;
      // Zurueck auf das, was vorher dastand: nicht jeder Kopierknopf heisst
      // «Kopieren» (in 03 «Prompt kopieren»).
      setTimeout(() => { $(spanne).textContent = alt; }, 1400);
      return true;
    } catch (e) { return false; }
  }

  $("knopf-kopieren-prompt").addEventListener("click", () => {
    if (z.prompt.trim()) inZwischenablage(z.prompt, "kopieren-prompt-text");
  });
  // Kein eigener Kopierknopf fuer «Das geht hinaus» mehr (seit 2.1): der
  // Sendeknopf kopiert genau diesen Text.

  /* Das Dienstmenue unter den Knopf stellen.
   * NACH UNTEN, weil der Pfeil nach unten zeigt. Nach oben weicht es nur aus,
   * wenn unten wirklich kein Platz ist; ein Menue, das halb unter dem
   * Fensterrand steht, waere schlechter als eines, das die Richtung wechselt.
   * Rechtsbuendig zum Knopf.
   */
  function dienstmenuStellen() {
    const menu = $("dienstmenu");
    const knopf = $("knopf-dienstmenu");
    const gruppe = knopf.closest(".sendegruppe") || knopf;
    const k = gruppe.getBoundingClientRect();
    const luft = 4;
    // Erst messen, dann stellen: vorher steht die Breite noch nicht fest.
    menu.style.left = "0px";
    menu.style.top = "0px";
    const m = menu.getBoundingClientRect();
    const unten = k.bottom + luft;
    const passt = unten + m.height <= window.innerHeight - luft;
    menu.style.top = (passt ? unten : Math.max(luft, k.top - luft - m.height))
                     + "px";
    menu.style.left = Math.max(luft,
      Math.min(k.right - m.width, window.innerWidth - luft - m.width)) + "px";
  }

  $("knopf-dienstmenu").addEventListener("click", (e) => {
    e.stopPropagation();
    const menu = $("dienstmenu");
    menu.hidden = !menu.hidden;
    if (!menu.hidden) dienstmenuStellen();
    $("knopf-dienstmenu").setAttribute("aria-expanded", String(!menu.hidden));
  });
  // ⚠️ Ein `fixed` Menue haengt nicht mehr am Knopf. Rollt die Spalte oder
  // aendert sich das Fenster, stuende es sonst irgendwo im Raum. Beide
  // Ereignisse in der Erfassungsphase, damit auch das Rollen INNERHALB
  // eines Kastens ankommt — es steigt nicht auf.
  window.addEventListener("resize", () => {
    if (!$("dienstmenu").hidden) dienstmenuStellen();
  });
  window.addEventListener("scroll", () => {
    if (!$("dienstmenu").hidden) dienstmenuStellen();
  }, true);
  document.addEventListener("click", () => {
    const menu = $("dienstmenu");
    if (menu && !menu.hidden) {
      menu.hidden = true;
      $("knopf-dienstmenu").setAttribute("aria-expanded", "false");
    }
  });

  // Das Burgermenue — dasselbe Muster wie das Dienstmenue darueber.
  $("knopf-burger").addEventListener("click", (e) => {
    e.stopPropagation();
    burgerAuf(!z.burgerOffen);
  });
  $("burgermenu").addEventListener("click", (e) => e.stopPropagation());
  document.addEventListener("click", () => {
    if (z.burgerOffen) burgerAuf(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && z.burgerOffen) burgerAuf(false);
  });

  // **Es wird nichts gesendet.** `/api/senden` gibt es nicht und wird es
  // nicht geben. Was hier passiert, ist genau zweierlei: Text in die
  // Zwischenablage, Dienst im Browser oeffnen. Der Anwender fuegt selbst ein.
  // Damit sieht er, was hinausgeht, und keine Zeile verlaesst das Geraet ohne
  // seinen Griff zur Tastatur.
  $("knopf-senden").addEventListener("click", async () => {
    const text = ausgehend();
    if (!text.trim()) return;
    const d = dienstJetzt();
    // ⚠️ UNTER macOS UND WINDOWS IM EIGENEN FENSTER GENAU WIE IM BURGERMENUE:
    // ein echter Verweis, den die Anwendung selbst im Standardbrowser oeffnet.
    // Die Menue-Links gingen dort von Anfang an; `window.open` nach dem `await`
    // des Kopierens tat nichts, weil die Nutzergeste dann verbraucht ist
    // (WKWebView). Deshalb: das Kopieren STARTEN (ohne zu warten), den Verweis
    // SOFORT anklicken — beides noch in der Geste —, und erst danach warten.
    // Das Kopieren beginnt vor dem Oeffnen, damit das Fenster beim Schreiben
    // noch den Fokus hat.
    const ueberVerweis = dienstUeberVerweis();
    let kopiert = Promise.resolve();
    try {
      kopiert = Promise.resolve(navigator.clipboard.writeText(text))
        .catch(() => {});
    } catch (e) { /* keine Zwischenablage: weiter, der Dienst oeffnet trotzdem */ }
    if (ueberVerweis) dienstOeffnenAlsVerweis(d.url);
    await kopiert;
    // Nicht `inZwischenablage` — die setzt nach 1400 ms auf «Kopieren» zurueck,
    // waehrend dieser Ablauf die volle Beschriftung wiederherstellt. Beide
    // zusammen ergaeben ein Flackern zwischen drei Texten.
    $("senden-text").textContent = t().kopiertK;
    clearTimeout(z.sendeUhr);
    z.sendeUhr = setTimeout(() => {
      z.sendeUhr = null;
      sendeBeschriftung();
    }, 3000);
    // Unter Linux (Qt) und im Browser geht `window.open`: Text zuerst, dann der
    // Dienst. EIN Aufruf, kein Rueckfall. `noopener` im Merkmalsstring laesst
    // `window.open` laut Spezifikation `null` zurueckgeben — auch wenn das
    // Fenster aufgeht. Ein `if (!fenster)`-Rueckfall hielte das fuer ein
    // Scheitern und oeffnete ein zweites Mal.
    //
    // Eigenes Fenster statt Reiter: MASCHERA bleibt sichtbar und wird nicht
    // mitgeschlossen, wenn jemand nur den Reiter schliessen wollte — und beim
    // Schliessen ist das Woerterbuch weg. Die GROESSENANGABEN machen aus dem
    // Reiter ein Fenster, nicht der Fenstername; `noopener` verhindert, dass
    // die geoeffnete Seite auf dieses Fenster zugreift.
    if (!ueberVerweis) {
      window.open(d.url, "_blank", z.eigenesFenster
        ? "noopener,noreferrer,width=1100,height=900"
        : "noopener,noreferrer");
    }
    // Untereinander steht 04 als Naechstes: dort wird die Antwort
    // eingefuegt, wenn der Anwender aus dem Dienst zurueckkommt.
    handlungSprung("b04");
  });

  // ⚠️ Steht der Schalter auf aus, entsteht gar kein Woerterbuch — die
  // Anfrage traegt `"woerterbuch": false`. Dann ist die Maskierung
  // endgueltig, weil die Daten, aus denen sich die Zuordnung
  // rekonstruieren liesse, erst gar nicht entstehen. Das ist ein anderer
  // Ablauf, kein Verschweigen.
  // ⚠️ SOFORT ANWENDEN, nicht erst beim Speichern. Eine Farbwahl, die man
  // erst nach dem Schliessen des Dialogs sieht, kann man nicht beurteilen —
  // man muesste dreimal auf und zu, um zwei Stufen zu vergleichen.
  // ⚠️ EIN Horcher auf der Reihe statt drei auf den Knoepfen. Der
  // naechste Eintrag braucht dann keinen eigenen — dieselbe Ueberlegung
  // wie beim Rechtsklickmenue, das an der Eigenschaft haengt und nicht an
  // einer Liste von Kennungen.
  $("einst-thema").addEventListener("click", (e) => {
    const k = e.target.closest && e.target.closest("[data-thema]");
    if (!k) return;
    z.thema = THEMEN.includes(k.dataset.thema) ? k.dataset.thema
                                               : "automatisch";
    themaAnwenden();
  });
  $("einst-schriftart").addEventListener("change", (e) => {
    z.schriftart = SCHRIFTEN[e.target.value] ? e.target.value : "werk";
    schriftAnwenden();
  });
  $("einst-schriftgroesse").addEventListener("change", (e) => {
    const n = parseInt(e.target.value, 10);
    z.schriftgroesse = GROESSEN.includes(n) ? n : 100;
    schriftAnwenden();
  });
  $("knopf-leeren-orig").addEventListener("click", () => {
    z.orig = "";
    $("orig").value = "";
    zeichne();
  });
  $("knopf-leeren-prompt").addEventListener("click", () => {
    z.prompt = "";
    $("prompt").value = "";
    zeichne();
  });
  $("knopf-einfuegen-antwort").addEventListener("click", antwortEinfuegen);
  $("knopf-herunter-mask").addEventListener("click", () => {
    textHerunter(z.antwort && z.antwort.maskiert, "maschera-maskiert");
  });
  $("knopf-herunter-final").addEventListener("click", () => {
    // Der FELDINHALT, nicht `z.final.text` — Bereich 05 ist ein Textfeld, und
    // der Anwender kann ihn geaendert haben.
    textHerunter(finalText(), "maschera-final");
  });
  $("knopf-final-kopieren").addEventListener("click", () => {
    if (finalText()) {
      inZwischenablage(finalText(), "final-kopieren-text");
    }
  });
  $("knopf-vorlagen").addEventListener("click", (e) => {
    e.stopPropagation();
    vorlagenAuf(!z.vorlagenOffen);
  });
  $("vorlagen-filter").addEventListener("input", (e) => {
    z.vorlagenFilter = e.target.value;
    zeichne();
    $("vorlagen-filter").focus();
  });
  $("vorlagen-filter").addEventListener("keydown", (e) => {
    if (e.key === "Escape") { vorlagenAuf(false); return; }
    if (e.key !== "Enter") return;
    const suche = z.vorlagenFilter.trim().toLowerCase();
    const erste = z.vorlagen.find(
      (v) => !suche || v.name.toLowerCase().includes(suche));
    if (erste) vorlageNehmen(erste);
  });
  $("vorlagen-menu").addEventListener("click", (e) => e.stopPropagation());
  // Klick daneben schliesst — sonst verdeckt das Menue das Promptfeld, in
  // das man gerade tippen will.
  document.addEventListener("click", () => {
    if (z.vorlagenOffen) vorlagenAuf(false);
  });
  $("knopf-vorlage-sichern").addEventListener("click", vorlageSpeichern);

  $("knopf-vok-herunter").addEventListener("click",
                                           vokabularSichern);
  $("knopf-vok-hoch").addEventListener("click", () => {
    $("vok-datei").click();
  });
  $("vok-datei").addEventListener("change", (e) => {
    const datei = e.target.files && e.target.files[0];
    // ⚠️ Das Feld leeren, sonst loest dieselbe Datei beim zweiten Mal kein
    // `change` aus — der Knopf sähe kaputt aus, obwohl er tut, was er soll.
    e.target.value = "";
    z.vokMeldung = null;
    if (datei) vokabularEinlesen(datei);
  });


  // Nichts wird auf die Festplatte geschrieben. Damit ist das Woerterbuch
  // nach dem Schliessen unwiederbringlich weg, und ein maskierter Text ohne
  // Woerterbuch laesst sich NIE mehr zurueckwandeln. Man haette dann eine
  // Antwort voller [FULLNAME_1] und keine Moeglichkeit, sie aufzuloesen.
  // Vor- und Zurueckwaerts im Browser holt die Seite aus dem Zwischenspeicher;
  // dann laeuft `start` nicht noch einmal.
  window.addEventListener("pageshow", () => {
    if (abgleichOrig()) zeichne();
  });

  // ⚠️ Die Rueckfrage des Browsers beim Neuladen laesst sich nicht
  // gestalten — Titel, Sprache und Knoepfe setzt Edge («Leave site?»).
  // Im eigenen Fenster laedt nur die Tastatur neu; dort fragt der eigene
  // Dialog, und die Browserfrage bleibt das Netz fuer den Browserbetrieb.
  document.addEventListener("keydown", async (e) => {
    const neuladen = e.key === "F5"
      || ((e.ctrlKey || e.metaKey) && (e.key === "r" || e.key === "R"));
    if (!neuladen || !hatWoerterbuch()) return;
    e.preventDefault();
    const n = Object.keys(z.antwort.woerterbuch).length;
    if (!(await frage(t().neuladenFrage.replace("{}", String(n))))) return;
    neuladenErlaubt = true;
    window.location.reload();
  });

  window.addEventListener("beforeunload", (e) => {
    if (neuladenErlaubt || !hatWoerterbuch()) return;
    e.preventDefault();
    e.returnValue = "";
  });
}

/* Den Zustand aus dem Feld nachziehen. Gibt zurueck, ob sich etwas
 * geaendert hat — damit nicht bei jedem Aufruf neu gezeichnet wird. */
function abgleichOrig() {
  const wert = $("orig").value || "";
  if (wert === z.orig) return false;
  z.orig = wert;
  return true;
}

/* Eine HANDLUNG springt in eine Kachel: dann gilt wieder der Ablauf, nicht
 * der zuletzt angetippte Schritt. Sonst blieb der Ring an 02 haengen, wer
 * vorher «Prüfen» angetippt hatte (Feedback 20.10.2026). Das Antippen in
 * der Schrittleiste springt weiter ueber `springeZu()` und behaelt seine
 * Mitte.
 */
function handlungSprung(kennung) {
  z.schrittMitte = null;
  schrittMitteMarkieren();
  springeZu(kennung);
}

/* Die Zeile zwischen 04 und 05 (nur untereinander sichtbar): waehrend des
 * Einpflegens mit Ladezeichen, danach bleibt sie mit gruenem Haken stehen,
 * solange 05 ein Ergebnis traegt (Feedback 21.10.2026). Mit «Neu»,
 * «Beispiel», einem neuen Lauf oder geleertem 05 geht sie.
 */
function zeichneEinpflegenZeile() {
  const zeile = $("einpflegen-zeile");
  const text = $("einpflegen-zeile-text");
  if (!zeile || !text) return;
  const laeuft = !!z.einpflegenLaeuft;
  const fertig = !laeuft && !!z.final;
  zeile.classList.toggle("an", laeuft || fertig);
  zeile.classList.toggle("fertig", fertig);
  text.textContent = laeuft ? t().einpflegenZeile
    : fertig ? t().eingepflegtZeile : "";
}

/* Eine Kachel vergroessern (seit 2.1, Feedback 21.10.2026): sie legt sich
 * als schwebende Tafel ueber die ganze Seite, um darin besser zu arbeiten.
 * Es bleibt DIESELBE Kachel, nur anders gesetzt (Klasse `.gross`): Text,
 * Einfuegemarke, Rollstand und Horcher bleiben erhalten. Zurueck ueber den
 * Knopf, Escape oder einen Klick auf den Grund.
 */
const GROSS_AUF = ["M15 3h6v6", "M9 21H3v-6", "m21 3-7 7", "m3 21 7-7"];
const GROSS_ZU = ["M4 14h6v6", "M20 10h-6V4", "m14 10 7-7", "m3 21 7-7"];
/* Die Bewegung ist die der Webseite beim Bildschirmfoto (Feedback
 * 22.10.2026): 320 ms, schnell los und stark abbremsend
 * (`cubic-bezier(.2,.7,.2,1)`, wie `site/zoom.js`). Lage vorher und
 * nachher messen und den Rahmen der festen Tafel vom alten Rechteck ins neue
 * laufen lassen. Beim Schliessen umgekehrt, und erst am Ende kehrt sie ins
 * Raster zurueck.
 */
const GROSS_DAUER = 320, GROSS_KURVE = "cubic-bezier(.2,.7,.2,1)";
let grossVon = null;
let grossPlatz = null;
function grossBewegung(kachel, von, nach, zurueck) {
  if (typeof kachel.animate !== "function" || !von || !nach) return null;
  // Nur der RAHMEN bewegt sich: Lage, Breite und Hoehe der festen Tafel.
  // Mit `transform: scale` schrumpften Kopf, Knoepfe und Schrift mit, und
  // das ruckelte (Feedback 22.10.2026). So ordnet sich der Inhalt in jedem
  // Bild neu an und behaelt seine Groesse.
  const rahmen = (r) => ({
    left: r.left + "px", top: r.top + "px",
    width: r.width + "px", height: r.height + "px",
    right: "auto", bottom: "auto",
  });
  return kachel.animate(
    zurueck ? [rahmen(nach), rahmen(von)] : [rahmen(von), rahmen(nach)],
    { duration: GROSS_DAUER, easing: GROSS_KURVE, fill: zurueck ? "forwards" : "none" });
}
function kachelGross(kennung) {
  const vorher = z.gross;
  const neu = kennung || null;
  if (vorher === neu) return;
  const grund = $("kachel-grund");
  const fertigSetzen = () => {
    z.gross = neu;
    for (const k of document.querySelectorAll(".bereich.gross")) k.classList.remove("gross");
    if (z.gross && $(z.gross)) $(z.gross).classList.add("gross");
    grund.classList.toggle("an", !!z.gross);
    grossKnoepfeZeichnen();
    fussEinpassenBald();
  };
  // Zuerst eine offene schliessen, mit Bewegung zurueck an ihren Platz.
  if (vorher && $(vorher)) {
    const kachel = $(vorher);
    // `von` ist das Ziel der Bewegung (der Platz im Raster), `nach` die Lage,
    // in der die Kachel gerade steht: die Verschiebung rechnet vom
    // jetzigen Rechteck aus. Vertauscht wuchs die Kachel beim Schliessen
    // noch weiter (Feedback 22.10.2026).
    const a = grossBewegung(kachel, grossVon, kachel.getBoundingClientRect(), true);
    if (typeof grund.animate === "function" && !neu) {
      grund.animate([{ opacity: 1 }, { opacity: 0 }],
                    { duration: GROSS_DAUER, easing: "ease-in", fill: "forwards" });
    }
    let erledigt = false;
    const weiter = () => {
      if (erledigt) return;
      erledigt = true;
      if (a) a.cancel();
      z.gross = null;
      kachel.classList.remove("gross");
      if (grossPlatz) { grossPlatz.remove(); grossPlatz = null; }
      grund.classList.remove("an");
      grund.getAnimations && grund.getAnimations().forEach((x) => x.cancel());
      if (neu) kachelGross(neu); else fertigSetzen();
    };
    if (a) {
      a.onfinish = weiter;
      // Absicherung wie bei `springeZu`: liefert die Ansicht keine Bilder,
      // laeuft keine Animation zu Ende. Dann eben ohne Bewegung zurueck.
      setTimeout(weiter, GROSS_DAUER + 120);
    } else {
      weiter();
    }
    return;
  }
  // Oeffnen: Lage im Raster merken, gross setzen, vom alten Rechteck her.
  const kachel = $(neu);
  if (!kachel) return;
  grossVon = kachel.getBoundingClientRect();
  // Ein Platzhalter haelt ihren Platz im Raster frei (Feedback 22.10.2026):
  // ohne ihn rueckte die Nachbarkachel derselben Spalte nach oben, lag
  // hinter der Tafel, und beim Zurueckgehen fehlte sie.
  const stil = getComputedStyle(kachel);
  grossPlatz = el("div", "kachel-platz");
  grossPlatz.style.height = grossVon.height + "px";
  grossPlatz.style.flex = stil.flex;
  grossPlatz.style.order = stil.order;
  grossPlatz.style.margin = stil.margin;
  kachel.parentNode.insertBefore(grossPlatz, kachel);
  fertigSetzen();
  const auf = grossBewegung(kachel, grossVon, kachel.getBoundingClientRect(), false);
  if (auf) setTimeout(() => auf.cancel(), GROSS_DAUER + 120);
  if (typeof grund.animate === "function") {
    grund.animate([{ opacity: 0 }, { opacity: 1 }], { duration: GROSS_DAUER, easing: "ease-out" });
  }
}
function grossKnoepfeZeichnen() {
  const s = t();
  for (const b of document.querySelectorAll(".gross-knopf")) {
    const an = z.gross === b.dataset.kachel;
    b.setAttribute("aria-pressed", String(an));
    b.title = an ? s.verkleinern : s.vergroessern;
    b.setAttribute("aria-label", b.title);
    const bild = zeichenSinnbild("x", { x: an ? GROSS_ZU : GROSS_AUF });
    bild.setAttribute("width", "15");
    bild.setAttribute("height", "15");
    b.replaceChildren(bild);
  }
}

/* Eine Kachel kurz mit dem Ring zeigen. */
function blitzen(kennung, ms) {
  const k = $(kennung);
  if (!k) return;
  k.classList.add("blitz");
  setTimeout(() => k.classList.remove("blitz"), ms);
}

/* Die Aufloesung der Antwort aus Bereich 04.
 *
 * Seit 2.1 sieht man, was geschieht (Feedback 20.10.2026): eine Sekunde
 * lang leuchtet zuerst das Vokabular, das angewendet wird, daneben «wird
 * angewendet» mit Ladezeichen; danach leuchtet 05, wo das Ergebnis steht.
 * Das Ergebnis selbst wartet nicht auf die Bewegung — nur Ring, Wort und
 * Sprung folgen dem Takt.
 */
/* Takt (Feedback 20.10.2026: 05 erst, wenn das Vokabular erloschen ist):
 * Ring am Vokabular bis 450 ms, dann 0.2 s Ausblenden (`transition` an
 * `.bereich::after`), erst danach der Ring an 05. Waehrenddessen haelt
 * `z.einpflegenLaeuft` den Dauerring `.amzug` von 05 zurueck — er kaeme
 * sonst mit dem Ergebnis sofort, gleichzeitig mit dem Vokabular.
 */
const EINPFLEGEN_VOK = 450;
const EINPFLEGEN_05 = 650;
async function einpflegen(text) {
  if (!text || !text.trim()) return;
  const w = (z.antwort && z.antwort.woerterbuch) || {};
  const beginn = Date.now();
  const wort = $("vok-anwenden");
  $("vok-anwenden-text").textContent = t().anwenden;
  wort.classList.add("an");
  // Untereinander steht das Vokabular weit oben. Damit man den Schritt
  // trotzdem sieht, leuchtet zwischen 04 und 05 eine eigene Zeile auf
  // (Feedback 21.10.2026). Nebeneinander blendet das CSS sie aus.
  z.einpflegenLaeuft = true;
  z.schrittMitte = null;
  zeichneEinpflegenZeile();
  schrittMitteMarkieren();
  blitzen("bvok", EINPFLEGEN_VOK);
  try {
    z.final = await zurueckwandeln(text, w);
    zeichne();
    setTimeout(() => {
      wort.classList.remove("an");
      z.einpflegenLaeuft = false;
      zeichneEinpflegenZeile();
      // Das Ende des Weges. Untereinander GANZ nach unten, nicht nur an den
      // Anfang von 05: sonst blieben Knoepfe, «+ Neu» und Fusszeile unter
      // dem Rand (Feedback 21.10.2026).
      // Ziel ist die Fassungsnummer in der Fusszeile; der Rollstand wird am
      // Seitenende von selbst begrenzt. Nebeneinander tut `springeZu` nichts.
      springeZu("version");
      schrittMitteMarkieren();
    }, Math.max(0, EINPFLEGEN_05 - (Date.now() - beginn)));
  } catch (e) {
    wort.classList.remove("an");
    z.einpflegenLaeuft = false;
    zeichneEinpflegenZeile();
    schrittMitteMarkieren();
    $("fehler").replaceChildren(
      el("p", "fehler-text", fehlerText(e)));
  }
}

function hatWoerterbuch() {
  return !!(z.antwort && z.antwort.woerterbuch &&
            Object.keys(z.antwort.woerterbuch).length);
}

/* Dasselbe vor «Neu», «Beispiel» und einer neuen Datei: das Woerterbuch per
 * Knopf wegzuwerfen ist genauso endgueltig wie per Schliessen. */
/* «Neu» leert das GANZE Formular, nicht nur Spalte 1. Wer ein zweites
 * Dokument beginnt, arbeitete sonst mit dem Prompt und der Antwort des
 * vorigen weiter — bei einem Werkzeug, dessen Zweck das Trennen von
 * Dokumenten ist, die falsche Vorgabe.
 *
 * Gespeicherte Vorlagen bleiben. Geleert wird das FELD, nicht der Vorrat.
 */
function allesLeeren() {
  z.orig = "";
  z.antwort = null;
  z.bearbeiten = false;
  z.uebernommen = false;
  z.vokMeldung = null;
  z.prompt = "";
  z.vorlage = null;
  z.antwort04 = "";
  z.final = null;
  for (const feld of ["orig", "prompt", "antwort04"]) {
    const e = $(feld);
    if (e) e.value = "";
  }
  $("fehler").replaceChildren();
}

async function verwerfenOk() {
  // Zwei Verluste, nicht einer: das Woerterbuch UND getippter Text, der noch
  // nie maskiert wurde. Wer eine Seite Text tippt und dann eine Datei ablegt,
  // verloere sonst den Text wortlos — `laufen` ueberschreibt `z.orig` mit dem
  // Inhalt der Datei.
  if (hatWoerterbuch()) {
    return frage(t().verwerfenVok.replace(
      "{}", String(Object.keys(z.antwort.woerterbuch).length)));
  }
  // Getippter Text ohne Lauf. Der Vergleich geht gegen das Feld und nicht
  // gegen `z.orig`, weil das Feld den letzten Tastendruck sicher hat.
  if (($("orig").value || "").trim()) {
    return frage(t().verwerfenText);
  }
  return true;
}

/* Eigene Wache fuer «Neu», weil es das ganze Formular leert.
 *
 * `verwerfenOk` fragt nach dem Woerterbuch und nach Spalte 1 — zu wenig,
 * sobald auch Prompt, Antwort und finaler Text weggeraeumt werden. Wer eine
 * leere Spalte 1 hat, aber eine eingefuegte Antwort, kaeme sonst wortlos
 * um sie.
 */
async function neuOk() {
  // EINE Frage, nicht zwei hintereinander: «Neu» wirft alles weg, und genau
  // das sagt der Satz.
  const weiteres = hatWoerterbuch()
    || ($("orig").value || "").trim()
    || (z.prompt || "").trim()
    || (z.antwort04 || "").trim()
    || (z.final && z.final.text);
  if (weiteres) return frage(t().neuAlles);
  return true;
}

/* ========================================================================
 * Vokabular sichern und einlesen
 *
 * **Keine Bequemlichkeit.** Nichts wird auf die Platte geschrieben — nach
 * dem Schliessen des Fensters ist das Woerterbuch weg, und ein maskierter
 * Text ohne Woerterbuch laesst sich NIE mehr zurueckwandeln.
 *
 * **Die Datei traegt alle Originalwerte im KLARTEXT.** Sie ist die
 * Umkehrung dessen, was das Werkzeug tut. Deshalb fragt `vokabularSichern`
 * jedes Mal nach, und der Dateiname sagt es: ein Griff, der Personendaten
 * auf die Platte legt, soll nicht aussehen wie «Kopieren».
 *
 * **Nur eigene Vokabulare laden.** Ein fremdes Vokabular bestimmt, was bei
 * der Rueckwandlung eingesetzt wird — wer eines unterschiebt, kann einen
 * Namen oder Betrag im Ergebnis vertauschen.
 *
 * **Der Server ist nicht beteiligt.** Blob hinaus, FileReader herein. Es
 * gibt keinen Endpunkt dafuer und soll keinen geben.
 * ====================================================================
 */

const VOK_FASSUNG = 1;

/* Nicht `PH_RE` nehmen: die traegt `g`, und `g`-Ausdruecke merken sich
 * `lastIndex` ueber `.test`-Aufrufe hinweg — jeder zweite Schluessel waere
 * grundlos abgewiesen worden. Hier braucht es ohnehin die verankerte Form:
 * `[FULLNAME_1] ` mit Anhang ist kein gueltiger Schluessel.
 */
const VOK_PH_RE = /^\[[A-Za-z][A-Za-z0-9_]*_\d+[a-z]?\]$/;

function zeitstempel() {
  const d = new Date(), p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate())
       + "-" + p(d.getHours()) + p(d.getMinutes());
}

function vokabularDatei() {
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  return {
    maschera: "vokabular",
    fassung: VOK_FASSUNG,
    erstellt: new Date().toISOString(),
    label_hash: (z.zustand && z.zustand.label_hash) || null,
    eintraege: Object.keys(wb).length,
    woerterbuch: wb,
    maskiert: (z.antwort && z.antwort.maskiert) || ""
  };
}

/* ⚠️ Der maskierte und der finale Text duerfen auf die Platte — sie tragen
 * keine Personendaten mehr. Das Woerterbuch fragt vorher; diese zwei nicht,
 * sonst waere die Rueckfrage eine Gewohnheit statt einer Warnung. */
function textHerunter(text, name) {
  if (!text) return;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name + "-" + zeitstempel() + ".txt";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/* Eine Meldung erscheint dort, wo der Anwender steht. Ist der
 * Einstellungsdialog offen, verdeckt er den Vokabularbereich von 05 — eine
 * Meldung nur dort machte aus einem erklaerten Fehlschlag («Einfuegen» im
 * Dialog) einen Knopf, der nichts tut. Ist er zu, gehoert die Meldung in
 * den Vokabularbereich und NICHT in den Dialog, auch nicht beim naechsten
 * Oeffnen. EINE Funktion entscheidet, zwei Kanaele tragen. */
/* Eine Meldung im Kopf DER Kachel, um die es geht (seit 2.1, Feedback
 * 21.10.2026: «Vorlage gespeichert» stand in 02). Einblenden, fuenf
 * Sekunden stehen lassen, ausblenden. Der volle Satz steht im Tooltip,
 * falls der Kopf ihn kuerzt. Ist der Einstellungsdialog offen, geht die
 * Meldung dorthin wie bei `meldeVok()`.
 */
const KOPFMELDUNG_MS = 5000;
const kopfmeldungUhr = {};
function meldeKopf(kennung, text) {
  if (!$("einst").hidden) { meldeVok(text); return; }
  const ziel = $(kennung);
  if (!ziel) return;
  ziel.textContent = text;
  ziel.title = text;
  ziel.classList.add("an");
  clearTimeout(kopfmeldungUhr[kennung]);
  kopfmeldungUhr[kennung] = setTimeout(() => {
    ziel.classList.remove("an");
    // Erst nach dem Ausblenden leeren, sonst springt der Kopf.
    setTimeout(() => { if (!ziel.classList.contains("an")) ziel.textContent = ""; }, 300);
  }, KOPFMELDUNG_MS);
}

function meldeVok(text) {
  if (!$("einst").hidden) z.einstMeldung = text;
  else z.vokMeldung = text;
  zeichne();
}

async function vokabularSichern() {
  if (!hatWoerterbuch()) return;
  const n = Object.keys(z.antwort.woerterbuch).length;
  if (!(await frage(t().sichernWarnung.replace("{}", String(n))))) return;
  const blob = new Blob([JSON.stringify(vokabularDatei(), null, 2)],
                        { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "maschera-vokabular-klartext-" + zeitstempel() + ".json";
  a.click();
  // Der Blob liegt sonst bis zum Entladen im Speicher — hier mit
  // Personendaten drin, also so kurz wie moeglich.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/* ⚠️ **Ganz oder gar nicht.** Ein Teilimport hiesse: die Rueckwandlung
 * laeuft, ersetzt aber nur einen Teil, und der Rest bleibt als Platzhalter
 * im fertigen Text stehen, ohne dass jemand weiss warum. Lieber ablehnen und
 * begruenden — dieselbe Haltung wie `PUT /api/regeln`, das prueft, bevor es
 * schreibt. Gibt den Grund zurueck oder null, wenn alles stimmt. */
function pruefeVokabular(o) {
  const s = t();
  if (!o || typeof o !== "object" || Array.isArray(o)) return s.vokFalsch;
  if (o.maschera !== "vokabular") return s.vokFremd;
  if (o.fassung !== VOK_FASSUNG) {
    return s.vokFassung.replace("{}", String(o.fassung));
  }
  const wb = o.woerterbuch;
  if (!wb || typeof wb !== "object" || Array.isArray(wb)) return s.vokKein;
  for (const ph of Object.keys(wb)) {
    if (!VOK_PH_RE.test(ph)) return s.vokSchluessel.replace("{}", ph);
    if (typeof wb[ph] !== "string") return s.vokWert.replace("{}", ph);
  }
  if (o.maskiert != null && typeof o.maskiert !== "string") return s.vokText;
  return null;
}

/* Ersetzt, statt zusammenzufuehren — und wirft dabei die Spannen weg. Ein
 * eingelesenes Woerterbuch gehoert zu einem anderen Lauf; die alten Spannen
 * zeigten auf Stellen im alten Text. Zusammenfuehren erzeugte stille
 * Kollisionen: `[FULLNAME_1]` zweimal mit verschiedenen Werten. Was bleibt,
 * ist `z.orig` — den Text im Eingabefeld wirft niemand ungefragt weg.
 */
function uebernimmVokabular(o) {
  // Ein hochgeladenes Woerterbuch ersetzt den maskierten Text — was im
  // Schreibfeld stand, gehoert nicht mehr dazu.
  z.bearbeiten = false;
  z.antwort = {
    maskiert: typeof o.maskiert === "string" ? o.maskiert : "",
    original: null,
    spans: [],
    woerterbuch: { ...o.woerterbuch },
    verworfen: [],
    hinweise: [],
    kennzahlen: null
  };
  return Object.keys(z.antwort.woerterbuch).length;
}

function vokabularEinlesen(datei) {
  const leser = new FileReader();
  leser.onerror = () => meldeKopf("meldung-vok", t().vokKaputt);
  leser.onload = async () => {
    let o = null;
    try { o = JSON.parse(String(leser.result)); }
    catch (e) { meldeKopf("meldung-vok", t().vokKaputt); return; }
    const grund = pruefeVokabular(o);
    if (grund) { meldeKopf("meldung-vok", grund); return; }
    // Erst pruefen, dann fragen: wer eine kaputte Datei erwischt, soll
    // nicht vorher entscheiden muessen, ob er sein Woerterbuch dafuer
    // hergibt.
    if (!(await verwerfenOk())) return;
    const n = uebernimmVokabular(o);
    meldeKopf("meldung-vok", t().vokGeladen.replace("{}", String(n)));
  };
  leser.readAsText(datei);
}

/* ========================================================================
 * Prompt-Vorlagen
 *
 * ⚠️ **Nicht im Browser gespeichert**, sondern in den Einstellungen des
 * Anwenders ueber `GET|PUT /api/vorlagen`. Was nur im Fenster lebt, ist
 * nach dem Schliessen weg — und eine Vorlage, die man jedes Mal neu tippt,
 * ist keine.
 *
 * ⚠️ **Ein Prompt kann Personendaten enthalten** und laege dann dauerhaft
 * im Klartext auf der Platte. Deshalb traegt der Speichernknopf die
 * Warnung als Titel, und der Server schickt sie in jeder Antwort mit.
 *
 * ⚠️ **Der Server prueft, bevor er schreibt.** Eine abgelehnte Liste laesst
 * die bestehende Datei unberuehrt — sonst waere eine Vorlage weg, weil eine
 * ANDERE fehlerhaft war.
 * ==================================================================== */

/* ========================================================================
 * Einstellungen: Adresse, Port, Dienste, Fensterschalter
 *
 * ⚠️ Sie gehen auf die Platte. Laegen sie nur in `z`, waere jede Aenderung
 * nach dem Neuladen weg — eine Bedienung ohne Wirkung.
 *
 * ⚠️ Beim Schliessen wird gesichert, und ein abgelehnter Stand SCHLIESST
 * NICHT. Sonst verschwaende der Dialog mit den Aenderungen darin, und der
 * Grund stuende in einem Kasten, den niemand mehr sieht.
 * ==================================================================== */

/* Die Groesse skaliert die GANZE Oberflaeche: `--skala` haengt an der
 * Wurzelschriftgroesse, und weil alle Hoehen und Abstaende in `rem` stehen,
 * wachsen Knoepfe und Spalten mit.
 *
 * Die Wortmarke MASCHERA und die Bereichstitel behalten `--font-heading`.
 * Ein Werkzeug, dessen Name die Schrift wechselt, sieht nach einem anderen
 * Programm aus.
 */
const SCHRIFTEN = {
  werk: "var(--font-body)",
  serif: "Iowan Old Style, Palatino, Georgia, serif",
  mono: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
};
// Dieselbe Liste steht in `core/einstellungen.THEMEN`; `test_api`
// Punkt 21 haelt beide gegeneinander.
const THEMEN = ["automatisch", "hell", "dunkel"];

const GROESSEN = [70, 80, 90, 100, 110, 125, 140];

function schriftAnwenden() {
  const w = document.documentElement.style;
  w.setProperty("--skala", String(z.schriftgroesse / 100));
  const familie = SCHRIFTEN[z.schriftart] || SCHRIFTEN.werk;
  w.setProperty("--textschrift", familie);
  // Die Bedienschrift bleibt immer IBM Plex. Der Schalter «Auch für Knöpfe
  // und Beschriftungen» ist seit 18.10.2026 weg (Entscheid des Anwenders):
  // die Wahl gilt nur fuer den Dokumenttext.
  w.setProperty("--ui-schrift", SCHRIFTEN.werk);
  w.setProperty("--ui-heading", "var(--font-heading)");
}

/* Die gewaehlte Sprache behalten.
 *
 * LESEN, AENDERN, SCHREIBEN — und nicht nur `{sprache}` schicken.
 * `PUT /api/einstellungen` prueft das ganze Objekt und setzt fuer jedes
 * fehlende Feld die VORGABE ein. Ein Aufruf mit nur einem Feld setzte
 * Adresse, Port, Schrift und die ganze Dienstliste zurueck — still, bei
 * einem Klick auf eine Flagge.
 *
 * Und es scheitert leise: die Sprache steht in `z` und wirkt sofort; geht
 * das Speichern schief, ist sie beim naechsten Start wieder die alte.
 */
async function merkeFenster() {
  // Lesen, aendern, schreiben — aus demselben Grund wie bei der Sprache:
  // ein `PUT` mit nur zwei Feldern setzt alle uebrigen auf die Vorgabe.
  try {
    const d = await holeEinstellungen();
    d.tray = z.tray;
    d.fenstermodus = z.fenstermodus;
    await setzeEinstellungen(d);
  } catch (e) { /* nicht gemerkt — die Bedienung laeuft trotzdem */ }
}

async function merkeSprache() {
  try {
    const d = await holeEinstellungen();
    if (d.sprache === z.sprache) return;
    d.sprache = z.sprache;
    await setzeEinstellungen(d);
  } catch (e) { /* nicht gemerkt — die Bedienung laeuft trotzdem */ }
}

async function ladeEinstellungen() {
  try {
    const d = await holeEinstellungen();
    if (Array.isArray(d.dienste) && d.dienste.length) {
      z.dienste = d.dienste.map((x) => ({ ...x }));
      if (!z.dienste.some((x) => x.id === z.dienst)) z.dienst = z.dienste[0].id;
    }
    if (typeof d.eigenes_fenster === "boolean") {
      z.eigenesFenster = d.eigenes_fenster;
    }
    if (d.dienst && z.dienste.some((x) => x.id === d.dienst)) {
      z.dienst = d.dienst;
    }
    if (GROESSEN.includes(d.schriftgroesse)) z.schriftgroesse = d.schriftgroesse;
    if (SCHRIFTEN[d.schriftart]) z.schriftart = d.schriftart;
    // ⚠️ Die zuletzt gewaehlte Sprache. `SPRACHEN` ist die Liste im
    // Kopf der Oberflaeche; steht dort ein unbekannter Wert, bleibt die
    // Vorgabe — eine kaputte Einstellungsdatei darf die Bedienung nicht
    // in einer Sprache festsetzen, die es nicht gibt.
    if (typeof d.tray === "boolean") z.tray = d.tray;
    if (THEMEN.includes(d.thema)) {
      z.thema = d.thema;
      themaAnwenden();
    }
    if (d.fenstermodus === "voll" || d.fenstermodus === "widget") {
      z.fenstermodus = d.fenstermodus;
    }
    if (d.sprache && I18N[d.sprache]) {
      z.sprache = d.sprache;
      spracheMarkieren();
    }
    if (d.adresse) $("einst-adresse").value = d.adresse;
    if (d.port) $("einst-port").value = String(d.port);
    // Steht gespeichert etwas anderes als der laufende Dienst, soll der
    // Knopf das sagen — nicht erst nach dem ersten Tastendruck.
    zeichnePruefknopf();
    $("einst-schriftgroesse").value = String(z.schriftgroesse);
    $("einst-schriftart").value = z.schriftart;
    schriftAnwenden();
  } catch (e) {
    // Die Vorgabe in `z` bleibt stehen — ohne Dienste waere der Sendeknopf
    // leer, und das saehe aus wie ein kaputtes Werkzeug statt wie ein
    // fehlender Server.
  }
}

function portFeld() {
  return $("einst-port").value.trim();
}

/* Weichen Adresse oder Port vom LAUFENDEN Dienst ab?
 *
 * Der laufende Dienst ist der, der diese Seite ausgeliefert hat. Pruefen
 * gegen eine Adresse, auf der noch niemand horcht, meldete nur «keine
 * Antwort» — richtig, aber nutzlos: die neue Adresse gilt erst nach einem
 * Neustart. Dann wird aus «Pruefen» «Speichern & neu starten».
 */
function adresseGeaendert() {
  const port = portFeld();
  if (!port) return false;
  const adr = $("einst-adresse").value.trim() || "127.0.0.1";
  const l = window.location || {};
  return adr !== String(l.hostname || "") || port !== String(l.port || "");
}

function kannNeuStarten() {
  return imEigenenFenster() && Boolean(window.pywebview.api
    && typeof window.pywebview.api.neustart === "function");
}

function zeichnePruefknopf() {
  const s = t();
  const neu = adresseGeaendert();
  const k = $("knopf-pruefen");
  $("pruefen-text").textContent = !neu ? s.pruefen
    : (kannNeuStarten() ? s.neuStarten : s.nurSpeichern);
  const bild = !neu ? "pruefen" : (kannNeuStarten() ? "neustart" : "speichern");
  if (k.dataset.bild !== bild) {
    const alt = k.querySelector("svg");
    if (alt) alt.remove();
    k.prepend(zeichenSinnbild(bild, KNOPFBILDER));
    k.dataset.bild = bild;
  }
  k.classList.toggle("haupt", neu);
}

/* VOLLSTAENDIG, und zwar jedes Feld. `PUT /api/einstellungen` prueft das
 * ganze Objekt und setzt fuer jedes FEHLENDE Feld die Vorgabe ein —
 * dieselbe Falle, vor der `merkeFenster()` und `merkeSprache()` warnen.
 * Fehlte hier ein Feld, setzte jedes Schliessen des Dialogs es zurueck.
 *
 * Die beiden anderen Stellen lesen dafuer erst (`holeEinstellungen`), hier
 * nicht: `z` traegt alle Werte, gesetzt von `ladeEinstellungen()` und den
 * Schaltern.
 *
 * `tests/test_api.py` prueft den ganzen Rundlauf gegen `VORGABE` — jedes
 * Feld, damit auch der naechste neue Schluessel auffaellt.
 */
function gesendeteDienste() {
  return z.dienste.filter(
    (x) => String(x.name || "").trim() || String(x.url || "").trim());
}

async function sichereEinstellungen() {
  const d = await setzeEinstellungen({
    adresse: $("einst-adresse").value.trim() || "127.0.0.1",
    // Leeres Feld heisst: NICHTS mitschicken. Dann setzt der Server seine
    // eigene Vorgabe ein (`core/einstellungen.VORGABE_PORT`), und die steht an
    // genau einer Stelle.
    ...(portFeld() ? { port: portFeld() } : {}),
    eigenes_fenster: z.eigenesFenster,
    dienst: z.dienst,
    schriftgroesse: z.schriftgroesse,
    schriftart: z.schriftart,
    sprache: z.sprache,
    tray: z.tray,
    fenstermodus: z.fenstermodus,
    thema: z.thema,
    // Eine GANZ leere Zeile («Hinzufuegen» geklickt, nichts getippt) faellt
    // still weg (Issue #11). Eine halb ausgefuellte geht mit und wird vom
    // Server abgewiesen — dort fehlt etwas, das gemeint war.
    dienste: gesendeteDienste()
      .map((x) => ({ id: x.id, name: x.name, url: x.url })),
  });
  z.dienste = (d.dienste || []).map((x) => ({ ...x }));
  if (!z.dienste.some((x) => x.id === z.dienst) && z.dienste.length) {
    z.dienst = z.dienste[0].id;
  }
  return d;
}

/* ⚠️ Lesen aus der Zwischenablage darf der Browser verweigern — ohne
 * Berechtigung, in Firefox grundsaetzlich. Dann bekommt der Anwender den
 * Hinweis auf Ctrl+V statt eines Knopfs, der nichts tut. */
async function antwortEinfuegen() {
  const feld = $("antwort04");
  feld.focus();
  try {
    const text = await navigator.clipboard.readText();
    if (!text) return;
    antwortUebernehmen(text);
  } catch (e) {
    meldeKopf("meldung-04", t().einfuegenHinweis);
  }
}

/* Eingefuegte Antwort uebernehmen — und dabei die Markdown-Entwertung
 * zuruecknehmen.
 *
 * BEIM EINFUEGEN und nicht im Server: der Anwender soll das Ergebnis SEHEN
 * und noch anfassen koennen. Ein Text, der unterwegs still ein anderer
 * wird, ist in diesem Werkzeug das Letzte, was man will.
 *
 * Zwei Meldungen, zwei verschiedene Aussagen: was repariert wurde, und was
 * NICHT repariert werden konnte. Die zweite ist die wichtigere.
 */
function antwortUebernehmen(roh) {
  const wb = (z.antwort && z.antwort.woerterbuch) || {};
  // ⚠️ ZUERST die Entwertung, DANN die zerschlagenen. Andersherum saehe
  // `zerschlageneErgaenzen()` lauter Rueckstriche und muesste sie noch
  // einmal wegrechnen — zwei Stellen fuer dieselbe Regel.
  const { text: entwertet, anzahl } = markdownZurueck(roh);
  const { text, ergaenzt } = zerschlageneErgaenzen(entwertet, wb);
  $("antwort04").value = text;
  z.antwort04 = text;
  zeichne();
  const s = t();
  if (anzahl) meldeKopf("meldung-04", s.phEntwertet.replace("{}", String(anzahl)));
  if (ergaenzt.length) {
    meldeKopf("meldung-04", s.phErgaenzt.replace("{}", String(ergaenzt.length))
                         .replace("{liste}", ergaenzt.slice(0, 6).join(", ")));
  }
  const reste = entwerteteReste(text);
  if (reste.length) {
    meldeKopf("meldung-04", s.phKaputt.replace("{liste}", reste.slice(0, 6).join(", ")));
  }
}

async function ladeVorlagen() {
  try {
    const d = await holeVorlagen();
    z.vorlagen = Array.isArray(d.vorlagen) ? d.vorlagen : [];
  } catch (e) {
    z.vorlagen = [];
  }
}

/* Schreibt und zieht danach die Serverfassung nach. Nicht die eigene Liste
 * weiterverwenden: der Server ist die Wahrheit, und wenn er etwas
 * zurechtgerueckt hat (Namen ohne Leerzeichen am Rand), soll das hier
 * ankommen. */
async function sichereVorlagen(liste) {
  try {
    const d = await setzeVorlagen(liste);
    z.vorlagen = Array.isArray(d.vorlagen) ? d.vorlagen : [];
    return null;
  } catch (e) {
    return fehlerText(e);
  }
}

async function vorlageSpeichern() {
  const text = z.prompt.trim();
  if (!text) return;
  const s = t();
  /* ⚠️ Steht eine Vorlage in der Auswahl, ist ihr Name der Vorschlag —
   * nochmals speichern heisst fast immer: dieselbe Vorlage, neuer Inhalt.
   * Bleibt der Name stehen, wird ueberschrieben, ohne zu fragen. Eine
   * Rueckfrage waere hier eine Bestaetigung dessen, was man gerade getippt
   * hat. */
  const vorschlag = z.vorlage || text.slice(0, 40);
  const name = await eingabe(s.tplName, vorschlag);
  if (!name || !name.trim()) return;
  // Gleicher Name ersetzt die alte Vorlage — der Server weist zwei gleiche
  // Namen ab, und stillschweigend danebenlegen waere die schlechtere Antwort
  // auf «nochmals speichern».
  const rest = z.vorlagen.filter(
    (v) => v.name.toLowerCase() !== name.trim().toLowerCase());
  const grund = await sichereVorlagen(
    [{ name: name.trim(), text: text }].concat(rest));
  if (!grund) z.vorlage = name.trim();
  meldeKopf("meldung-03", grund ? s.tplFehler.replace("{}", grund)
                                : s.tplGesichert.replace("{}", name.trim()));
}

async function vorlageLoeschen(name) {
  const s = t();
  if (!(await frage(s.tplWeg.replace("{}", name)))) return;
  const grund = await sichereVorlagen(
    z.vorlagen.filter((v) => v.name !== name));
  if (grund) meldeKopf("meldung-03", s.tplFehler.replace("{}", grund));
  else {
    if (z.vorlage === name) z.vorlage = null;
    zeichne();
  }
}

function vorlageNehmen(v) {
  z.prompt = v.text;
  $("prompt").value = v.text;
  z.vorlage = v.name;
  z.vorlagenOffen = false;
  z.vorlagenFilter = "";
  zeichne();
}

/* Ein Auswahlfeld mit Filter, kein `<select>` und kein blosses Menue: das
 * `<select>` kann tippen und finden, aber keinen Papierkorb je Zeile; ein
 * Menue kann den Papierkorb, aber nicht das Tippen. Ein Feld, das filtert,
 * kann beides — und das Loeschen steht dort, wo der Eintrag steht.
 */
function zeichneVorlagen() {
  const st = t();
  const gewaehlt = z.vorlagen.find((v) => v.name === z.vorlage);
  $("vorlagen-anzeige").textContent = gewaehlt ? gewaehlt.name
    : (z.vorlagen.length ? st.tplWaehlen.replace("{}", String(z.vorlagen.length))
                         : st.tplLeer);
  $("knopf-vorlagen").setAttribute("aria-expanded", String(z.vorlagenOffen));
  const menu = $("vorlagen-menu");
  menu.hidden = !z.vorlagenOffen;
  const liste = $("vorlagen-liste");
  liste.replaceChildren();
  if (!z.vorlagenOffen) return;

  const suche = z.vorlagenFilter.trim().toLowerCase();
  const treffer = z.vorlagen.filter(
    (v) => !suche || v.name.toLowerCase().includes(suche));
  if (!treffer.length) {
    liste.append(el("div", "leer", z.vorlagen.length ? st.tplNichts
                                                     : st.tplLeer));
    return;
  }
  for (const v of treffer) {
    const zeile = el("div", "zeile" + (v.name === z.vorlage ? " aktiv" : ""));
    const waehlen = el("button", "waehlen", v.name);
    waehlen.type = "button";
    // Name UND Inhalt im Tooltip. Wird die Spalte schmal, kuerzt das CSS den
    // Namen mit «…» — dann ist der Tooltip die einzige Stelle, an der noch
    // steht, welche Vorlage das ist.
    waehlen.title = v.name + "\n\n" + v.text.slice(0, 200);
    waehlen.addEventListener("click", (e) => {
      e.stopPropagation();
      vorlageNehmen(v);
    });
    const weg = el("button", "weg");
    weg.type = "button";
    weg.title = st.tplWegT;
    weg.setAttribute("aria-label", st.tplWegT + ": " + v.name);
    weg.classList.add("kreuz");
    weg.append(zeichenSinnbild("schliessen", KNOPFBILDER));
    zeile.classList.add("mit-kreuz");
    weg.addEventListener("click", (e) => {
      e.stopPropagation();
      vorlageLoeschen(v.name);
    });
    zeile.append(waehlen, weg);
    liste.append(zeile);
  }
  // Der reservierte Rollbalkenstreifen nur, wenn die Liste ihn braucht —
  // bei einer einzigen Vorlage stuende er sonst leer daneben. Gemessen wird
  // NACH dem Fuellen.
  liste.classList.toggle("rollend", liste.scrollHeight > liste.clientHeight);
}

function vorlagenAuf(offen) {
  z.vorlagenOffen = offen;
  z.vorlagenFilter = "";
  $("vorlagen-filter").value = "";
  suchStand($("vorlagen-filter"));
  zeichne();
  if (offen) {
    vorlagenMenuSetzen();
    $("vorlagen-filter").focus();
  }
}

/* Das Vorlagenmenue liegt seit 2.1 frei ueber der Seite (`position: fixed`)
 * und wird an den Knopf gesetzt: rechtsbuendig darunter, bei Platzmangel
 * darueber, nie ueber den Fensterrand (Feedback 21.10.2026: in der Spalte
 * rechts schnitt die Kachel es ab).
 */
function vorlagenMenuSetzen() {
  const menu = $("vorlagen-menu");
  const knopf = $("knopf-vorlagen");
  if (!menu || !knopf || menu.hidden) return;
  const k = knopf.getBoundingClientRect();
  menu.style.width = "";
  const breite = Math.max(k.width, menu.getBoundingClientRect().width);
  menu.style.width = breite + "px";
  const hoehe = menu.getBoundingClientRect().height;
  const links = Math.max(8, Math.min(k.right - breite, window.innerWidth - breite - 8));
  let oben = k.bottom + 4;
  if (oben + hoehe > window.innerHeight - 8 && k.top - 4 - hoehe >= 8) {
    oben = k.top - 4 - hoehe;
  }
  menu.style.left = links + "px";
  menu.style.top = oben + "px";
}

async function ladeTags() {
  try {
    const d = await holeTags(z.sprache);
    z.tags = {};
    for (const e of (d.tags || d || [])) {
      if (e && e.tag) z.tags[e.tag] = e;
    }
  } catch (e) { z.tags = {}; }
}

/* Nebenknoepfe nur so lange mit Wort, wie der Fuss auf eine Zeile passt
 * (seit 2.1, Feedback 20.10.2026). Gemessen statt geschaetzt: erst ohne
 * `.eng` legen, dann pruefen, ob ein Kind in eine zweite Zeile rutscht oder
 * der Fuss ueberlaeuft. Ein Fuss in Spaltenrichtung (05 gestapelt) steht
 * absichtlich untereinander und zaehlt nicht.
 */
function fussEinpassen() {
  const passt = (f) => {
    const kinder = [...f.children].filter((k) => k.offsetWidth > 0);
    if (!kinder.length) return true;
    const oben = kinder[0].offsetTop;
    return !kinder.some((k) => k.offsetTop > oben + 2)
      && f.scrollWidth <= f.clientWidth + 1;
  };
  for (const f of document.querySelectorAll(".fuss")) {
    f.classList.remove("eng");
    const gerankt = [...f.querySelectorAll("[data-rang]")];
    for (const k of gerankt) k.classList.remove("kurz");
    if (getComputedStyle(f).flexDirection === "column") continue;
    if (passt(f)) continue;
    // Rangfolge (Feedback 21.10.2026): der Hauptknopf behaelt sein Wort am
    // laengsten, dann Kopieren (Rang 2), dann Bearbeiten, Leeren und
    // Herunterladen (3 und 4). Gekuerzt wird von hinten, Rang um Rang, und
    // nach jedem Schritt neu gemessen.
    let fertig = false;
    for (const rang of ["4", "3", "2"]) {
      const diese = gerankt.filter((k) => k.dataset.rang === rang);
      if (!diese.length) continue;
      for (const k of diese) k.classList.add("kurz");
      if (passt(f)) { fertig = true; break; }
    }
    if (!fertig) f.classList.add("eng");
  }
}
let fussGeplant = false;
function fussEinpassenBald() {
  if (fussGeplant) return;
  fussGeplant = true;
  // Die Kopfzeile mit: ein Sprachwechsel aendert ihre Breite, nicht ihre
  // Groesse, und ihr Beobachter merkte es nicht.
  setTimeout(() => { fussGeplant = false; fussEinpassen(); kopfEinpassen(); }, 0);
}

/* Jedes Suchfeld bekommt ein kleines Kreuz zum Leeren, sobald etwas darin
 * steht; es steht dort, wo sonst die Lupe ist (Feedback 21.10.2026). Ein
 * `input` hat keine Kinder, deshalb eine Huelle, die die Lage des Feldes
 * uebernimmt. `suchStand()` nach jedem Setzen von aussen aufrufen.
 */
function suchStand(feld) {
  const h = feld && feld.parentElement;
  if (h && h.classList && h.classList.contains("suchhuelle")) {
    h.classList.toggle("voll", !!feld.value);
  }
}
function suchfeldMitKreuz(feld) {
  if (!feld || !feld.parentNode || typeof feld.parentNode.insertBefore !== "function") return;
  if (feld.parentElement && feld.parentElement.classList
      && feld.parentElement.classList.contains("suchhuelle")) return;
  const huelle = el("span", "suchhuelle");
  feld.parentNode.insertBefore(huelle, feld);
  huelle.append(feld);
  const x = el("button", "kreuz such-leeren");
  x.type = "button";
  x.title = t().suchLeeren;
  x.setAttribute("aria-label", t().suchLeeren);
  x.append(zeichenSinnbild("schliessen", KNOPFBILDER));
  // Den Fokus im Feld lassen: weitertippen soll gleich gehen.
  x.addEventListener("mousedown", (e) => e.preventDefault());
  x.addEventListener("click", (e) => {
    e.stopPropagation();
    feld.value = "";
    feld.dispatchEvent(new Event("input", { bubbles: true }));
    suchStand(feld);
    const neu = feld.id ? $(feld.id) : feld;
    if (neu) neu.focus();
  });
  huelle.append(x);
  feld.addEventListener("input", () => suchStand(feld));
  suchStand(feld);
}

/* Die Kopfzeile in Stufen einpassen (Feedback 21.10.2026). Vorrang hat
 * die Wortmarke mit Schrift, danach die Sprachwahl als Knopfreihe. Passt
 * nicht alles, wird zuerst die Sprachwahl zum Pulldown, erst dann faellt
 * der Schriftzug. Gemessen wird die Summe der beiden Seiten gegen die
 * verfuegbare Breite, nach jeder Stufe neu.
 */
function kopfEinpassen() {
  const kopf = $("kopfzeile");
  if (!kopf) return;
  const links = kopf.querySelector(".links");
  const rechts = kopf.querySelector(".rechts");
  if (!links || !rechts) return;
  // In der Teststufe steht mittig «TEST». Dann muss jede Seite in ihre
  // Haelfte passen, abzueglich der halben Breite des Schriftzugs.
  const test = $("teststufe-marke");
  const passt = () => {
    const st = getComputedStyle(kopf);
    const lueke = parseFloat(st.columnGap) || 0;
    const platz = kopf.clientWidth - parseFloat(st.paddingLeft)
      - parseFloat(st.paddingRight) - lueke;
    const mitte = test && test.offsetWidth > 0 ? test.offsetWidth + 2 * lueke : 0;
    if (!mitte) return links.scrollWidth + rechts.scrollWidth <= platz;
    const haelfte = (platz + lueke - mitte) / 2;
    return links.scrollWidth <= haelfte && rechts.scrollWidth <= haelfte;
  };
  kopf.classList.remove("sprache-klein", "ohne-marke", "ohne-spruch", "ohne-test");
  if (passt()) return;
  // Teststufe: zuerst geht der Untertitel neben der Wortmarke, dann «TEST»;
  // erst danach die Stufen, die es auch sonst gibt.
  const wurzelKl = document.documentElement && document.documentElement.classList;
  if (wurzelKl && wurzelKl.contains("teststufe")) {
    kopf.classList.add("ohne-spruch");
    if (passt()) return;
    kopf.classList.add("ohne-test");
    if (passt()) return;
  }
  kopf.classList.add("sprache-klein");
  if (passt()) return;
  kopf.classList.add("ohne-marke");
}

/* Nicht nur bei `zeichne()` und `resize` messen (Feedback 20.10.2026: in 02
 * blieb `.eng` haengen, obwohl Platz war). Die Breite eines Fusses aendert
 * sich auch, wenn die Schriften fertig geladen sind oder eine Kachel ihre
 * Breite ohne Fensteraenderung verschiebt. Deshalb ein Beobachter je Fuss
 * und ein Lauf, sobald die Schriften da sind. Ohne Beobachter (alte
 * Browser, die Pruefung) bleibt es bei den zwei anderen Anlaessen.
 */
function fussBeobachten() {
  if (typeof ResizeObserver === "function") {
    const beob = new ResizeObserver(fussEinpassenBald);
    for (const f of document.querySelectorAll(".fuss")) beob.observe(f);
    if ($("kopfzeile")) new ResizeObserver(kopfEinpassen).observe($("kopfzeile"));
  }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fussEinpassenBald);
    document.fonts.ready.then(kopfEinpassen);
  }
  kopfEinpassen();
}

/* Die Teststufe sieht man sofort (seit 2.1, Feedback 21.10.2026): gelbe
 * Kopfzeile und ein Favicon mit «T». Die Bedingung ist die FASSUNG des
 * Servers (`2.1.0-test.N`), kein Schalter: ein echter Bau traegt nie
 * `-test` (auf_server.fish haelt das fest), also zeigt er beides nie.
 */
function teststufeZeigen(fassung) {
  if (!/-test\b/.test(String(fassung || ""))) return;
  document.documentElement.classList.add("teststufe");
  const icon = document.querySelector('link[rel="icon"]');
  if (icon) icon.setAttribute("href", "maske-test.svg");
  kopfEinpassen();
}

/* Beim allerersten Start leuchtet «Beispiel» (seit 2.1, Feedback
 * 20.10.2026), bis irgendein Knopf geklickt wird — wer MASCHERA zum ersten
 * Mal sieht, soll merken, dass er es ausprobieren kann.
 *
 * Die Marke liegt im Speicher des BROWSERS, nicht in den Einstellungen: auf
 * dem Server teilten sich sonst alle Nutzer eine Marke. Sie traegt keinen
 * Inhalt, nur «gesehen». Fehlt der Speicher (privates Fenster, gesperrt),
 * leuchtet der Knopf bei jedem Start; das ist harmlos.
 */
const BEISPIEL_MARKE = "maschera.beispielGesehen";
function beispielLeuchten() {
  let gesehen = false;
  try { gesehen = window.localStorage.getItem(BEISPIEL_MARKE) === "1"; }
  catch (e) { /* kein Speicher: leuchten */ }
  if (gesehen) return;
  const knopf = $("knopf-beispiel");
  knopf.classList.add("leuchtet");
  const aus = (e) => {
    let k = e.target;
    while (k && k.tagName !== "BUTTON") k = k.parentElement;
    if (!k) return;
    knopf.classList.remove("leuchtet");
    try { window.localStorage.setItem(BEISPIEL_MARKE, "1"); }
    catch (e2) { /* kein Speicher: beim naechsten Start wieder */ }
    document.removeEventListener("click", aus, true);
  };
  document.addEventListener("click", aus, true);
}

async function start() {
  verbinde();
  for (const id of ["einst-suche", "vok-suche", "vorlagen-filter"]) {
    suchfeldMitKreuz($(id));
  }
  beispielLeuchten();
  fussBeobachten();
  // ⚠️ Frueh, aber NACH `verbinde`: der Probeklotz braucht den Koerper.
  // Der gemessene Wert steckt danach in `--rollbalken` und bestimmt den
  // Abstand der Knoepfe in den Textfeldern.
  messeRollbalken();
  // Firefox stellt beim Neuladen den Inhalt von Textfeldern wieder her, ohne
  // ein `input`-Ereignis zu feuern. Dann zeigte die Oberflaeche Text, den sie
  // selbst nicht kennt: Zaehler auf 0, MASKIEREN und KOPIEREN grau.
  //
  // Einmal beim Start zu lesen genuegt nicht — die Wiederherstellung passiert
  // erst NACH diesem Skript. Deshalb dreierlei: `autocomplete="off"` im HTML
  // unterbindet sie, `pageshow` faengt den Fall ab, dass der Browser die
  // Seite aus dem Vor-Zurueck-Zwischenspeicher holt, und der Abgleich hier
  // deckt den Rest ab.
  abgleichOrig();
  zeichneBeschriftung();
  // Kein Prozentbalken: solange `Zustand` das Modell laedt, antwortet
  // nichts — der Browser kann nur fragen «schon da?». Eine Zahl waere
  // erfunden. Im Serverbetrieb antwortet es sofort, und der Startbildschirm
  // verschwindet, bevor er gezeichnet ist.
  const bis = Date.now() + 180000;
  while (true) {
    try { z.zustand = await holeZustand(); break; } catch (e) {
      if (Date.now() > bis) {
        // Auch dieser Satz ist Beschriftung, viersprachig — wer den
        // Startbildschirm auf Franzoesisch haengen sieht, soll keine deutsche
        // Fehlermeldung lesen.
        $("start-lage").textContent =
          t().keinStart.replace("{}", fehlerText(e));
        return;
      }
      await new Promise((r) => setTimeout(r, 400));
    }
  }
  // NICHT `.remove`. Der Startbildschirm enthaelt `start-lage`, und
  // `zeichneBeschriftung` beschriftet das bei JEDEM Zeichnen. Entfernt man
  // das Element, wirft der naechste Aufruf mitten in der Funktion — und alles
  // danach bleibt unbeschriftet und unverdrahtet, ohne dass am Server etwas
  // auffaellt.
  $("startbild").hidden = true;
  // ⚠️ Wer auf 4141 antwortet, ist noch lange nicht MASCHERA.
  if (z.zustand.dienst !== "maschera") {
    // `falscherDienst` gibt es in allen vier Sprachen — die Portpruefung in den
    // Einstellungen benutzt denselben Satz.
    $("fehler").append(el("p", "fehler-text",
      t().falscherDienst.replace("{}", z.zustand.dienst)));
    return;
  }
  $("version").textContent = z.zustand.version
    ? "v" + z.zustand.version : "";
  teststufeZeigen(z.zustand.version);
  // ⚠️ Ein Server, der still ohne Modell laeuft, waere eine Leckquelle mit
  // gruener Anzeige. Der Balken ist nicht wegklickbar, solange es gilt.
  if (z.zustand.ohne_modell) {
    const b = el("div", "warnung", t().ohneModell);
    b.id = "ohne-modell";
    $("warnbereich").append(b);
    document.body.classList.add("ohne-modell");
  }
  // EINSTELLUNGEN ZUERST. `ladeTags()` holt die Tagnamen in `z.sprache`, und
  // die steht erst fest, wenn die gespeicherte Sprache gelesen ist —
  // andersherum kaeme das Tagmenue in der Vorgabesprache.
  await ladeEinstellungen();
  zeichneBeschriftung();
  await ladeTags();
  await ladeVorlagen();
  await ladeAdressen();
  zeichne();
}

/* ⚠️ Nur fuer `tests/test_oberflaeche.js`. Im Browser gibt es `module`
 * nicht, also passiert hier nichts; unter node bekommt die Pruefung Zugriff
 * auf die Korrekturfunktionen, ohne dass sie ueber das DOM gehen muss.
 *
 * Das ist der ehrlichere Weg als eine Pruefung, die Klicks nachstellt und
 * dabei mehr die Attrappe prueft als den Code. */
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    zustand: z, SRC_STYLE, FREQUENT, PH_RE,
    MENUEBILDER,
    maskeEntfernen, wertMaskieren, tagWechseln, naechsterPlatzhalter,
    auswahlOderWort, wortgrenzen, typOf, schreibfeld,
    zeichneKontext, zeichneFeldKontext, SINNBILDER, KNOPFBILDER,
    pruefeVokabular, uebernimmVokabular, vokabularDatei, VOK_PH_RE,
    vorlageNehmen, zeichneVorlagen, zeichneDienstmenu, zeichneDienstliste,
    vorlagenAuf,
    zeichneBurger, burgerAuf, imEigenenFenster, finalText, neuesteZeigen,
    SEITEN, seiteZeigen, seiteSchliessen,
    pruefePlatzhalter, zeichneMaskiert, meldeVok, ablagefachMoeglich,
    fehlerText, serverFehler, frage, eingabe, frageZeigen, frageErsetzen,
    markdownZurueck, entwerteteReste, antwortUebernehmen,
    zerschlageneErgaenzen,
    ausgehend, uebernommenerText,
    laufAnzeigen, laufAus, dauerWort, restWort, fortschrittHolen,
    springeZu, gestapelt, einspaltig,
    zeichneSchritte, schrittJetzt, SCHRITT_ZIEL,
    zeichneBeschriftung,
    zeichne, zeichneFinal,
    messeRollbalken, knopfTitelSetzen,
    allesLeeren, neuOk,
    hinweisText, hinweisSchluessel, I18N,
  };
}

start();
