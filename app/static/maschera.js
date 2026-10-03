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
  model:       "1px solid var(--gr-kante)",
  propagation: "1px solid var(--color-neutral-500)",
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
  de: { zurueckW: "Weg zurück", uebernahme: "Übernahme in Prompt",
        einpflegen: "Vokabular einpflegen", rueckPlatz: "Antwort deines KI-Werkzeugs hier einfügen …", kopiertK: "Kopiert",
        ersetztN: "{} Platzhalter zurückgesetzt", nichtGefunden: "Nicht zugeordnet: {}",
        maskeWeg: "Maske entfernen",
        haeufig: "Häufig",
        alleTags: "Alle Typen …",
        nichtMaskiert: "nicht maskiert",
        bspdWeg: "Maske wirklich entfernen?\n{} ist ein besonders schützenswertes Personendatum.",
        bspdSetzen: "Als {} maskieren?\nDas ist ein besonders schützenswertes Personendatum.",
        einstT: "Einstellungen",
        schliessen: "Schliessen", einstZu: "Speichern", einstZuRest: " & schliessen",
        allgemeinT: "Allgemein",
        serverT: "Server",
        serverH: "Adresse und Port des lokalen Maskierdienstes. Der Text verlässt dein Gerät nicht — die Prüfung zeigt, ob der Dienst antwortet.",
        adresse: "Adresse",
        port: "Port",
        pruefen: "Prüfen",
        neuStarten: "Speichern & neu starten",
        nurSpeichern: "Speichern",
        startetNeu: "MASCHERA startet neu …",
        giltNachNeustart: "Gespeichert. Gilt ab dem nächsten Start des Dienstes.",
        keinDienstDa: "Unter {} antwortet kein MASCHERA.",
        diensteT: "Dienste",
        diensteH: "Der Web-Link wird beim Kopieren geöffnet.",
        hinzu: "Hinzufügen",
        entfernen: "Entfernen",
        fensterWort: "In eigenem Fenster öffnen statt im Reiter",
        trayWort: "Beim Schliessen in den Infobereich (Tray) statt beenden",
        widgetWort: "Schmales Fenster, immer im Vordergrund",
        fensterHilfe: "Beides wirkt erst nach dem Neustart der Applikation.",
        klartextT: "Klartext-Tags",
        klartextH: "Diese Typen bleiben dauerhaft im Klartext — erkannt, aber nicht ersetzt.",
        regelnT: "Eigene Regeln",
        regelnH: "Eigene Wörter und Muster, die zusätzlich maskiert werden. Als YAML. Wer sie ändert, ändert das Messergebnis.",
        regelnSpeichern: "Regeln speichern",
        pruefeLaeuft: "wird geprüft …",
        dienstDa: "MASCHERA {v} antwortet · Modell {m}",
        falscherDienst: "Antwortet, ist aber nicht MASCHERA: {}",
        keinDienst: "Keine Antwort: {}",
        bspdFrage: "{} dauerhaft im Klartext lassen?\nDas ist ein besonders schützenswertes Personendatum.",
        starrHinweis: "Bleibt ohnehin im Klartext — nicht umlegbar.",
        unbekannteTags: "Gespeicherte Tags, die es nicht mehr gibt: {}",
        einpflegen04: "Vokabular einpflegen", leerenA: "Leeren",
        antwortPlatz: "Antwort deines KI-Werkzeugs hier einfügen (Ctrl+V) …",
        offenText: "{} Platzhalter blieben stehen — im fertigen Text nachsehen:",
        gutText: "{} Platzhalter zurückgesetzt.",
        promptT: "Prompt", hinausT: "Das geht hinaus", trenner: "den oberen Prompt auf folgenden Text anwenden",
        sendenZu: "Kopieren und {} öffnen", onlineWarnung: "In {} arbeitest du online, sei vorsichtig!", origPlatz: "Originaltext hier einfügen …", promptPlatz: "Dein Prompt, z. B. «Beantworte diese E-Mail freundlich.»", hinausLeer: "Erst «Übernahme in Prompt» — dann steht hier, was hinausgeht.",
        hinausZahl: "Genau diese {} Zeichen gehen zu {dienst}, sobald du sie kopierst und dort einfügst.",
        verworfenHinweis: "Wörterbuch verworfen — der maskierte Text lässt sich nicht mehr zurückwandeln.",
        an: "An", aus: "Aus", spalteId: "ID",
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
        schriftT: "Schrift", schriftart: "Schriftart",
        schriftgroesse: "Grösse",
        schriftH: "Gilt für die Textflächen — Originaltext, maskierter Text, Prompt und Antwort.",
        schriftprobe: "Sehr geehrte Damen und Herren",
        schriftAlles: "Auch für Knöpfe und Beschriftungen",
        schriftSans: "Serifenlos", schriftSerif: "Serifen",
        schriftMono: "Feste Breite",
        herunterladen: "Herunterladen", einfuegen: "Einfügen",
        einfuegenHinweis: "Zwischenablage gesperrt — bitte Ctrl+V drücken.",
        kAusschneiden: "Ausschneiden", kKopieren: "Kopieren", kEinfuegen: "Einfügen",
        menu: "Menü",
        mBrowser: "Im Browser öffnen", mHilfe: "Hilfe",
        mHilfeBald: "kommt später", mWebseite: "maschera.ch",
        mGithub: "Quellcode auf GitHub", mDownload: "Herunterladen",
        mFehler: "Fehler melden",
        mImpressum: "Impressum", mKontakt: "Kontakt",
        finalKopieren: "Finalisierten Text kopieren",
        vokHerunter: "Vokabular herunterladen",
        vokHoch: "Vokabular hochladen",
        tplMenu: "Vorlagen", tplSichern: "Speichern",
        tplWaehlen: "Vorlage wählen ({})",
        tplSuchen: "Suchen …", tplNichts: "Keine Vorlage passt.",
        tplLokal: "lokal gespeichert",
        tplLeer: "Noch keine Vorlage gespeichert",
        tplName: "Name der Vorlage",
        tplWarnung: "Vorlagen liegen dauerhaft im Klartext auf der Platte. "
          + "Keine Personendaten in eine Vorlage schreiben.",
        tplWeg: "Vorlage «{}» löschen?", tplWegT: "Löschen",
        tplGesichert: "Vorlage «{}» gespeichert.",
        tplFehler: "Vorlage nicht gespeichert: {}",
        sichernWarnung: "Die Datei enthält {} Originalwerte im Klartext — "
          + "alles, was hier maskiert wurde. Sie liegt danach ungeschützt "
          + "im Downloadordner. Sichern?",
        vokGeladen: "{} Vokabulareinträge eingelesen.",
        vokKaputt: "Die Datei ist kein lesbares JSON — nichts eingelesen.",
        frageJa: "Weiter",
        frageNein: "Abbrechen",
        frageOk: "Übernehmen",
        neuladenFrage: "Wirklich neu laden?\n{} Vokabulareinträge gehen verloren.",
        verbindungWeg: "Keine Verbindung zum MASCHERA-Dienst — die Anfrage kam nicht an. Nochmals versuchen; hilft das nicht, MASCHERA neu starten.",
        httpFehler: "Der MASCHERA-Dienst hat die Anfrage abgelehnt (Fehler {status}).",
        vokFalsch: "Die Datei enthält kein Objekt — nichts eingelesen.",
        vokFremd: "Keine MASCHERA-Vokabulardatei — nichts eingelesen.",
        vokFassung: "Unbekannte Fassung {} — diese Ausgabe liest Fassung 1.",
        vokKein: "Kein Wörterbuch in der Datei — nichts eingelesen.",
        vokSchluessel: "Kein gültiger Platzhalter: {} — nichts eingelesen.",
        vokWert: "Der Wert zu {} ist keine Zeichenkette — nichts eingelesen.",
        vokText: "Der maskierte Text in der Datei ist keine Zeichenkette.",
        einklappen: "Einklappen", ausklappen: "Ausklappen",
        bearbeiten: "Bearbeiten", bearbeitenFertig: "Fertig",
        bearbeitenHilfe: "Text von Hand korrigieren. Platzhalter wie [FULLNAME_1] bitte stehen lassen — sie werden am Ende zurückgewandelt.",
        phUnbekannt: "Diese Platzhalter kennt das Wörterbuch nicht: {liste}. Sie bleiben am Ende stehen.",
        phEntwertet: "{} Platzhalter aus der Markdown-Auszeichnung zurückgeholt — der Dienst hatte sie mit Rückstrichen entwertet.",
        phErgaenzt: "{} zerschlagene Platzhalter ergänzt: {liste}. Das Wörterbuch kennt sie — die Klammer hatte der Dienst verschluckt.",
        phKaputt: "Diese Stellen sehen aus wie Platzhalter, sind aber keine: {liste}. Sie werden am Ende NICHT ersetzt — bitte im Text nachsehen.",
        fussLinks: "MASCHERA · Verarbeitung auf diesem Gerät · keine Online-Verbindung zu den KI-Diensten", bereitS: "Bereit",
        orig: "Originaltext", masked: "Maskiert", run: "Maskieren",
        fertig: "Finaler Text", prompt: "Prompt",
        antwort: "Antwort", neu: "Neu", lokal: "Lokal", online: "Online",
        hundert: "100% lokal", einst: "Einstellungen",
        spruch: "Maskiere deine Daten, bevor du sie mit anderen teilst! · "
              + "Lokales Modell · DSG / GDPR",
        spruch1: "Maskiere deine Daten, bevor du sie mit anderen teilst!",
        spruch2: "Lokales Modell · DSG / GDPR",
        laden: "Lokales KI-Modell wird geladen",
        keinStart: "Kein Server auf /api/zustand: {}",
        zeichenN: (n) => n + " Zeichen",
        eintraegeN: (n) => n + " Einträge",
        maskiertN: (n) => n + " maskiert",
        leer05: "Hier landet der fertige Text, sobald du das Vokabular "
              + "einpflegst.",
        leer02: "Noch nichts maskiert. Text in Spalte 1 einfügen und "
              + "«Maskieren» drücken.",
        dropN: "PDF, DOCX, TXT oder Mail hierher ziehen — oder klicken",
        laeuft: "läuft …", lWartet: "Text wird vorbereitet …", lModell: "Fenster {} von {}", lMaskieren: "Maskieren, Wörterbuch wird gebaut …", lRest: "noch etwa {}", lFertig: "in {} maskiert", drop: "Datei hierher ziehen oder wählen",
        portFehlt: "Kein Port angegeben.",
        verwerfenVok: "Wirklich fortfahren?\n{} Vokabulareinträge gehen verloren.",
        verwerfenText: "Wirklich fortfahren?\nDer Text in Spalte 1 geht verloren.",
        neuAlles: "Willst du wirklich neu beginnen?\nAlle Daten werden zurückgesetzt!",
        liestDatei: "Datei wird gelesen …",
        beispiel: "Beispiel", leeren: "Leeren", kopieren: "Kopieren",
        kopiert: "Kopiert", funde: "Fundstellen", vokabular: "Vokabular",
        verworfen: "Knapp verworfen", nichts: "nichts",
        bereit: "bereit", quelle: "Quelle", vertrauen: "Vertrauen",
        zeichen: "Zeichen", anteil: "maskiert",
        ohneModell: "OHNE MODELL — nur Prüfsummen und Muster. Namen, "
                  + "Daten und Adressen bleiben im Klartext.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "OHNE MODELL — nur Prüfsummen und Muster. Namen, Daten und Adressen bleiben im KLARTEXT.",
          fenster: "Länger als ein Fenster ({token} Token). Wird überlappend verarbeitet.",
          wortgrenzen: "{anzahl} Modellspannen lagen mitten in einem Wort und wurden auf Wortgrenzen gezogen.",
          mehrere_nachrichten: "{anzahl} Nachrichten in der Datei — nur die erste wird verarbeitet.",
          vorlieben: "Aus den gespeicherten Vorlieben im Klartext: {tags}",
          ohne_woerterbuch: "Ohne Wörterbuch — endgültig anonymisiert, keine Rückwandlung möglich.",
          eigene_regeln: "Eigene Regeln angewendet ({anzahl}): {namen}",
          schreibweise: "{platzhalter} unterscheidet sich von {treffer} nur in der Schreibweise — nicht ersetzt.",
          anhang_uebersprungen: "Anhang übersprungen: {name}",
          kein_textteil: "Die Mail hat keinen Textteil, nur {art}.",
          msg_ohne_textrumpf: "Die .msg hat keinen reinen Textrumpf (nur RTF oder HTML). In Outlook «Speichern unter» → .eml wählen.",
          binaer_abgeschnitten: "{zeichen} Zeichen nach dem Textende sahen aus wie Binärdaten und wurden weggelassen.",
          nur_html: "nur HTML-Teil vorhanden, grob entkleidet",
          kein_rumpf: "kein Textrumpf gefunden",
          pdf_ohne_text: "kein Text im PDF — vermutlich ein Scan. Ohne OCR sieht der Filter nichts, und ein leerer Befund heisst hier NICHT, dass keine Personendaten drin sind.",
          pdf_seiten: "{anzahl} Seiten, Layout geht beim Auslesen verloren",
          tabellen: "{anzahl} Tabellen, zeilenweise gelesen",
          nicht_gelesen: "NICHT gelesen: {teile} — dort steht bei Briefen oft der Absender",
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
          datei_unlesbar: "Datei nicht lesbar — beschädigt oder kein unterstütztes Format.",
          datei_zu_gross: "Datei grösser als {mb} MB.",
          dienst_kein_objekt: "Dienst {nummer} ist kein Objekt.",
          dienst_kennung_doppelt: "Kennung zweimal vergeben: {kennung}",
          dienst_ohne_adresse: "Dienst {name} hat keine Adresse.",
          dienst_ohne_namen: "Dienst {nummer} hat keinen Namen.",
          dienst_schema: "Dienst {name}: nur https:// oder http://, nicht {adresse}",
          dienste_keine_liste: "Feld `dienste` ist keine Liste.",
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
          klartext_gespeichert: "Gespeichert. Diese Tags bleiben dauerhaft im Klartext — auch in künftigen Dokumenten.",
          nicht_gespeichert: "Nicht gespeichert — die Datei im Einstellungsordner liess sich nicht schreiben.",
          ohne_tags_unbekannt: "Unbekannte Tags bei `ohne`: {tags}",
          port_ausserhalb: "Port ausserhalb 1–65535: {port}",
          regeldatei_fehlerhaft: "Die Regeldatei ist fehlerhaft und wurde nicht angewendet.",
          regeln_abgelehnt: "Regeln abgelehnt — die Datei enthält einen Fehler.",
          regeln_gelesen: "Wer die Regeln ändert, ändert das Messergebnis.",
          regeln_veraltete_schluessel: "Diese Regeldatei benutzt veraltete Schlüssel. Sie werden weiter gelesen oder übergangen: {umbenennungen}",
          regeln_gespeichert: "Gespeichert. Das Messergebnis ändert sich damit.",
          regeln_unlesbar: "Regeln nicht lesbar — ein Feld hat die falsche Form.",
          schrift_ueberall_kein_wahrheitswert: "Feld `schrift_ueberall` ist kein Wahrheitswert.",
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
          regel_zu_langsam: "Regel «{id}»: das Muster braucht {dauer} s für eine Probezeile — zu langsam, meist wegen geschachtelter Wiederholungen wie (a+)+.",
          regel_ohne_kennung: "Eine Regel hat keine Kennung (`id`).",
          regel_kennung: "Regel-Kennung «{id}»: nur Kleinbuchstaben, Ziffern und Unterstrich, 2 bis 32 Zeichen.",
          regel_platzhalter: "Regel «{id}»: der Platzhalter «{platzhalter}» muss aus 2 bis 20 Buchstaben oder Ziffern bestehen.",
          regel_woerter_leer: "Regel «{id}»: die Wortliste (`words`) ist leer.",
          regel_woerter_kurz: "Regel «{id}»: zu kurze Einträge ({kurz}). Unter {min} Zeichen treffen sie als Silbe überall.",
          regel_etiketten_leer: "Regel «{id}»: `labels` ist leer — ohne Etikett träfe die Regel jede Zahl.",
          regel_wertform: "Regel «{id}»: die Wertform «{form}» gibt es nicht. Möglich: {moeglich}",
          regel_min_max: "Regel «{id}»: min/max unplausibel ({min}/{max}).",
          regel_muster_fehlt: "Regel «{id}»: das Muster (`pattern`) fehlt.",
          regel_muster_ungueltig: "Regel «{id}»: das Muster ist ungültig (bei Zeichen {stelle}).",
          regel_art: "Regel «{id}»: die Art «{art}» gibt es nicht. Möglich: {moeglich}",
          regeln_doppelt: "Diese Regel-Kennungen stehen doppelt: {kennungen}",
          regel_platzhalter_vergeben: "Platzhalter schon vergeben: {platzhalter}. Wähle einen anderen Namen.",
          msg_ohne_olefile: "Outlook-Nachrichten (.msg) lassen sich hier nicht lesen. In Outlook «Speichern unter» → .eml wählen.",
          pdf_ohne_pymupdf: "PDF lassen sich hier nicht lesen — die PDF-Bibliothek fehlt.",
          docx_zu_gross: "Das Word-Dokument wäre ausgepackt {mb} MB gross; höchstens {hoechstens} MB werden gelesen.",
          docx_kaputt: "Keine lesbare .docx-Datei. Ältere .doc sind ein anderes Format.",
          docx_ohne_dokument: "Kein Word-Dokument — vermutlich .odt, .pptx oder .xlsx mit falscher Endung.",
          docx_dtd: "Das Word-Dokument enthält eine DTD; das kommt in echten Word-Dateien nicht vor und wird nicht gelesen.",
          word_alt: "Das alte Word-Format (.doc) wird nicht gelesen. In Word oder LibreOffice als .docx speichern.",
        },
        leer: "Noch nichts maskiert." },
  fr: { zurueckW: "Retour", uebernahme: "Reprise dans le prompt",
        einpflegen: "Appliquer le vocabulaire", rueckPlatz: "Colle ici la réponse de ton outil IA …", kopiertK: "Copié",
        ersetztN: "{} marqueurs rétablis", nichtGefunden: "Non attribué : {}",
        maskeWeg: "Retirer le masque",
        haeufig: "Fréquents",
        alleTags: "Tous les types …",
        nichtMaskiert: "non masqué",
        bspdWeg: "Retirer vraiment le masque ?\n{} est une donnée sensible.",
        bspdSetzen: "Masquer comme {} ?\nC'est une donnée sensible.",
        einstT: "Réglages",
        schliessen: "Fermer", einstZu: "Enregistrer", einstZuRest: " et fermer",
        allgemeinT: "Général",
        serverT: "Serveur",
        serverH: "Adresse et port du service de masquage local. Le texte ne quitte pas ton appareil — la vérification montre si le service répond.",
        adresse: "Adresse",
        port: "Port",
        pruefen: "Vérifier",
        neuStarten: "Enregistrer et redémarrer",
        nurSpeichern: "Enregistrer",
        startetNeu: "MASCHERA redémarre …",
        giltNachNeustart: "Enregistré. S'applique au prochain démarrage du service.",
        keinDienstDa: "Aucun MASCHERA ne répond à {}.",
        diensteT: "Services",
        diensteH: "Le lien web s’ouvre lors de la copie.",
        hinzu: "Ajouter",
        entfernen: "Supprimer",
        fensterWort: "Ouvrir dans une fenêtre plutôt qu’un onglet",
        trayWort: "À la fermeture, réduire dans la zone de notification",
        widgetWort: "Fenêtre étroite, toujours au premier plan",
        fensterHilfe: "Les deux prennent effet au prochain démarrage de l’application.",
        klartextT: "Types en clair",
        klartextH: "Ces types restent en clair — reconnus, mais non remplacés.",
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
        offenText: "{} substituts sont restés — à vérifier dans le texte final :",
        gutText: "{} substituts rétablis.",
        promptT: "Prompt", hinausT: "Ce qui sort", trenner: "appliquer le prompt ci-dessus au texte suivant",
        sendenZu: "Copier et ouvrir {}", onlineWarnung: "Dans {}, tu travailles en ligne — sois prudent !", origPlatz: "Coller ici le texte original …", promptPlatz: "Ton prompt, p. ex. « Réponds à ce courriel poliment. »", hinausLeer: "D’abord « Reprise dans le prompt » — ensuite tu verras ici ce qui sort.",
        hinausZahl: "Ces {} caractères précisément iront à {dienst} dès que tu les colles là-bas.",
        verworfenHinweis: "Vocabulaire supprimé — le texte masqué ne peut plus être rétabli.",
        an: "Activé", aus: "Désactivé", spalteId: "ID",
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
        schriftT: "Police", schriftart: "Police",
        schriftgroesse: "Taille",
        schriftH: "S'applique aux zones de texte — texte original, texte masqué, prompt et réponse.",
        schriftprobe: "Madame, Monsieur",
        schriftAlles: "Aussi pour les boutons et les libellés",
        schriftSans: "Sans empattement", schriftSerif: "Avec empattement",
        schriftMono: "Largeur fixe",
        herunterladen: "Télécharger", einfuegen: "Coller",
        einfuegenHinweis: "Presse-papiers bloqué — utilise Ctrl+V.",
        kAusschneiden: "Couper", kKopieren: "Copier", kEinfuegen: "Coller",
        menu: "Menu",
        mBrowser: "Ouvrir dans le navigateur", mHilfe: "Aide",
        mHilfeBald: "à venir", mWebseite: "maschera.ch",
        mGithub: "Code source sur GitHub", mDownload: "Télécharger",
        mFehler: "Signaler un problème",
        mImpressum: "Mentions légales", mKontakt: "Contact",
        finalKopieren: "Copier le texte final",
        vokHerunter: "Télécharger le vocabulaire",
        vokHoch: "Téléverser le vocabulaire",
        tplMenu: "Modèles", tplSichern: "Enregistrer",
        tplWaehlen: "Choisir un modèle ({})",
        tplSuchen: "Chercher …", tplNichts: "Aucun modèle ne correspond.",
        tplLokal: "enregistré en local",
        tplLeer: "Aucun modèle enregistré",
        tplName: "Nom du modèle",
        tplWarnung: "Les modèles restent en clair sur le disque. "
          + "N'y écrivez pas de données personnelles.",
        tplWeg: "Supprimer le modèle « {} » ?", tplWegT: "Supprimer",
        tplGesichert: "Modèle « {} » enregistré.",
        tplFehler: "Modèle non enregistré : {}",
        sichernWarnung: "Le fichier contient {} valeurs originales en clair "
          + "— tout ce qui a été masqué ici. Il restera sans protection "
          + "dans le dossier de téléchargement. Enregistrer ?",
        vokGeladen: "{} entrées de vocabulaire chargées.",
        vokKaputt: "Le fichier n'est pas du JSON lisible — rien de chargé.",
        frageJa: "Continuer",
        frageNein: "Annuler",
        frageOk: "Valider",
        neuladenFrage: "Recharger vraiment ?\n{} entrées de vocabulaire seront perdues.",
        verbindungWeg: "Pas de connexion au service MASCHERA — la requête n'est pas arrivée. Réessaie ; si cela ne suffit pas, redémarre MASCHERA.",
        httpFehler: "Le service MASCHERA a refusé la requête (erreur {status}).",
        vokFalsch: "Le fichier ne contient pas d'objet — rien de chargé.",
        vokFremd: "Ce n'est pas un vocabulaire MASCHERA — rien de chargé.",
        vokFassung: "Version inconnue {} — cette édition lit la version 1.",
        vokKein: "Pas de dictionnaire dans le fichier — rien de chargé.",
        vokSchluessel: "Marqueur non valable : {} — rien de chargé.",
        vokWert: "La valeur de {} n'est pas une chaîne — rien de chargé.",
        vokText: "Le texte masqué du fichier n'est pas une chaîne.",
        einklappen: "Replier", ausklappen: "Déplier",
        bearbeiten: "Modifier", bearbeitenFertig: "Terminé",
        bearbeitenHilfe: "Corriger le texte à la main. Laissez les marqueurs comme [FULLNAME_1] en place — ils sont rétablis à la fin.",
        phUnbekannt: "Le dictionnaire ne connaît pas ces marqueurs : {liste}. Ils resteront tels quels.",
        phEntwertet: "{} marqueurs récupérés du balisage Markdown — le service les avait échappés avec des barres obliques inverses.",
        phErgaenzt: "{} marqueurs cassés complétés : {liste}. Le dictionnaire les connaît — le service avait avalé le crochet.",
        phKaputt: "Ces passages ressemblent à des marqueurs sans en être : {liste}. Ils ne seront PAS rétablis — à vérifier dans le texte.",
        fussLinks: "MASCHERA · traitement sur cet appareil · aucune connexion en ligne aux services IA", bereitS: "Prêt",
        orig: "Texte original", masked: "Masqué", run: "Masquer",
        fertig: "Texte final", prompt: "Prompt",
        antwort: "Réponse", neu: "Nouveau", lokal: "Local", online: "En ligne",
        hundert: "100% local", einst: "Réglages",
        spruch: "Masque tes données avant de les partager ! · "
              + "Modèle local · LPD / RGPD",
        spruch1: "Masque tes données avant de les partager !",
        spruch2: "Modèle local · LPD / RGPD",
        laden: "Chargement du modèle local",
        keinStart: "Aucun serveur sur /api/zustand : {}",
        zeichenN: (n) => n + " caractères",
        eintraegeN: (n) => n + " entrées",
        maskiertN: (n) => n + " masqués",
        leer05: "Le texte final apparaîtra ici dès que tu appliques le "
              + "vocabulaire.",
        leer02: "Rien de masqué. Colle un texte dans la colonne 1 puis "
              + "presse « Masquer ».",
        dropN: "Glisser un PDF, DOCX, TXT ou courriel — ou cliquer",
        laeuft: "en cours …", lWartet: "Préparation du texte …", lModell: "Fenêtre {} sur {}", lMaskieren: "Masquage, création du glossaire …", lRest: "encore environ {}", lFertig: "masqué en {}", drop: "Glisser un fichier ou choisir",
        portFehlt: "Aucun port indiqué.",
        verwerfenVok: "Continuer vraiment ?\n{} entrées de vocabulaire seront perdues.",
        verwerfenText: "Continuer vraiment ?\nLe texte de la colonne 1 sera perdu.",
        neuAlles: "Veux-tu vraiment recommencer ?\nToutes les données seront réinitialisées !",
        liestDatei: "Lecture du fichier …",
        beispiel: "Exemple", leeren: "Vider", kopieren: "Copier",
        kopiert: "Copié", funde: "Occurrences", vokabular: "Vocabulaire",
        verworfen: "Rejeté de peu", nichts: "rien",
        bereit: "prêt", quelle: "Source", vertrauen: "Confiance",
        zeichen: "Caractères", anteil: "masqué",
        ohneModell: "SANS MODÈLE — seulement sommes de contrôle et motifs. "
                  + "Noms, dates et adresses restent en clair.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "SANS MODÈLE — seulement sommes de contrôle et motifs. Noms, dates et adresses restent EN CLAIR.",
          fenster: "Plus long qu’une fenêtre ({token} jetons). Traité par recouvrement.",
          wortgrenzen: "{anzahl} segments du modèle tombaient au milieu d’un mot et ont été étendus aux limites de mots.",
          mehrere_nachrichten: "{anzahl} messages dans le fichier — seul le premier est traité.",
          vorlieben: "D’après les préférences enregistrées, en clair : {tags}",
          ohne_woerterbuch: "Sans dictionnaire — anonymisé définitivement, aucun retour possible.",
          eigene_regeln: "Règles personnelles appliquées ({anzahl}) : {namen}",
          schreibweise: "{platzhalter} ne diffère de {treffer} que par la casse — non remplacé.",
          anhang_uebersprungen: "Pièce jointe ignorée : {name}",
          kein_textteil: "Le courriel n’a pas de partie texte, seulement {art}.",
          msg_ohne_textrumpf: "Le .msg n’a pas de corps en texte brut (seulement RTF ou HTML). Dans Outlook, choisir « Enregistrer sous » → .eml.",
          binaer_abgeschnitten: "{zeichen} caractères après la fin du texte ressemblaient à des données binaires et ont été omis.",
          nur_html: "seule la partie HTML est présente, dépouillée sommairement",
          kein_rumpf: "aucun corps de texte trouvé",
          pdf_ohne_text: "aucun texte dans le PDF — probablement un scan. Sans OCR le filtre ne voit rien, et un résultat vide ne signifie PAS qu’il n’y a pas de données personnelles.",
          pdf_seiten: "{anzahl} pages, la mise en page est perdue à la lecture",
          tabellen: "{anzahl} tableaux, lus ligne par ligne",
          nicht_gelesen: "NON lu : {teile} — c’est souvent là que figure l’expéditeur",
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
          datei_unlesbar: "Fichier illisible — endommagé ou format non pris en charge.",
          datei_zu_gross: "Fichier de plus de {mb} Mo.",
          dienst_kein_objekt: "Le service {nummer} n’est pas un objet.",
          dienst_kennung_doppelt: "Identifiant attribué deux fois : {kennung}",
          dienst_ohne_adresse: "Le service {name} n’a pas d’adresse.",
          dienst_ohne_namen: "Le service {nummer} n’a pas de nom.",
          dienst_schema: "Service {name} : uniquement https:// ou http://, pas {adresse}",
          dienste_keine_liste: "Le champ `dienste` n’est pas une liste.",
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
          klartext_gespeichert: "Enregistré. Ces types restent durablement en clair — dans les documents à venir également.",
          nicht_gespeichert: "Non enregistré — le fichier du dossier de réglages n'a pas pu être écrit.",
          ohne_tags_unbekannt: "Types inconnus dans `ohne` : {tags}",
          port_ausserhalb: "Port hors de 1–65535 : {port}",
          regeldatei_fehlerhaft: "Le fichier de règles est défectueux et n'a pas été appliqué.",
          regeln_abgelehnt: "Règles refusées — le fichier contient une erreur.",
          regeln_gelesen: "Modifier les règles, c’est modifier le résultat de mesure.",
          regeln_veraltete_schluessel: "Ce fichier de règles utilise des clés obsolètes. Elles restent lues ou sont ignorées : {umbenennungen}",
          regeln_gespeichert: "Enregistré. Le résultat de mesure change en conséquence.",
          regeln_unlesbar: "Règles illisibles — un champ n'a pas la bonne forme.",
          schrift_ueberall_kein_wahrheitswert: "Le champ `schrift_ueberall` n’est pas un booléen.",
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
          regel_zu_langsam: "Règle « {id} » : le motif prend {dauer} s pour une ligne d'essai — trop lent, souvent à cause de répétitions imbriquées comme (a+)+.",
          regel_ohne_kennung: "Une règle n'a pas d'identifiant (`id`).",
          regel_kennung: "Identifiant « {id} » : seulement minuscules, chiffres et trait de soulignement, 2 à 32 caractères.",
          regel_platzhalter: "Règle « {id} » : l'espace réservé « {platzhalter} » doit compter 2 à 20 lettres ou chiffres.",
          regel_woerter_leer: "Règle « {id} » : la liste de mots (`words`) est vide.",
          regel_woerter_kurz: "Règle « {id} » : entrées trop courtes ({kurz}). En dessous de {min} caractères, elles touchent partout comme syllabe.",
          regel_etiketten_leer: "Règle « {id} » : `labels` est vide — sans étiquette, la règle toucherait n'importe quel nombre.",
          regel_wertform: "Règle « {id} » : la forme de valeur « {form} » n'existe pas. Possible : {moeglich}",
          regel_min_max: "Règle « {id} » : min/max invraisemblables ({min}/{max}).",
          regel_muster_fehlt: "Règle « {id} » : le motif (`pattern`) manque.",
          regel_muster_ungueltig: "Règle « {id} » : le motif n'est pas valide (au caractère {stelle}).",
          regel_art: "Règle « {id} » : le type « {art} » n'existe pas. Possible : {moeglich}",
          regeln_doppelt: "Ces identifiants de règle figurent deux fois : {kennungen}",
          regel_platzhalter_vergeben: "Espace réservé déjà utilisé : {platzhalter}. Choisis un autre nom.",
          msg_ohne_olefile: "Les messages Outlook (.msg) ne peuvent pas être lus ici. Dans Outlook, « Enregistrer sous » → .eml.",
          pdf_ohne_pymupdf: "Les PDF ne peuvent pas être lus ici — la bibliothèque PDF manque.",
          docx_zu_gross: "Le document Word ferait {mb} Mo une fois décompressé ; au plus {hoechstens} Mo sont lus.",
          docx_kaputt: "Pas de fichier .docx lisible. Les anciens .doc sont un autre format.",
          docx_ohne_dokument: "Pas un document Word — sans doute un .odt, .pptx ou .xlsx mal nommé.",
          docx_dtd: "Le document Word contient une DTD ; cela n'existe pas dans un vrai fichier Word et n'est pas lu.",
          word_alt: "L'ancien format Word (.doc) n'est pas lu. Enregistre-le en .docx dans Word ou LibreOffice.",
        },
        leer: "Rien de masqué pour l’instant." },
  it: { zurueckW: "Ritorno", uebernahme: "Riprendi nel prompt",
        einpflegen: "Applica il vocabolario", rueckPlatz: "Incolla qui la risposta del tuo strumento IA …", kopiertK: "Copiato",
        ersetztN: "{} segnaposto ripristinati", nichtGefunden: "Non assegnato: {}",
        maskeWeg: "Togli la maschera",
        haeufig: "Frequenti",
        alleTags: "Tutti i tipi …",
        nichtMaskiert: "non mascherato",
        bspdWeg: "Togliere davvero la maschera?\n{} è un dato personale degno di particolare protezione.",
        bspdSetzen: "Mascherare come {}?\nÈ un dato degno di particolare protezione.",
        einstT: "Impostazioni",
        schliessen: "Chiudi", einstZu: "Salva", einstZuRest: " e chiudi",
        allgemeinT: "Generale",
        serverT: "Server",
        serverH: "Indirizzo e porta del servizio di mascheratura locale. Il testo non lascia il dispositivo — la verifica mostra se il servizio risponde.",
        adresse: "Indirizzo",
        port: "Porta",
        pruefen: "Verifica",
        neuStarten: "Salva e riavvia",
        nurSpeichern: "Salva",
        startetNeu: "MASCHERA si riavvia …",
        giltNachNeustart: "Salvato. Vale dal prossimo avvio del servizio.",
        keinDienstDa: "MASCHERA non risponde sul IP {}",
        diensteT: "Servizi",
        diensteH: "Il link web si apre alla copia.",
        hinzu: "Aggiungi",
        entfernen: "Rimuovi",
        fensterWort: "Aprire in una finestra invece che in una scheda",
        trayWort: "Alla chiusura, riduci nell’area di notifica",
        widgetWort: "Finestra stretta, sempre in primo piano",
        fensterHilfe: "Entrambi hanno effetto al prossimo avvio dell’applicazione.",
        klartextT: "Tipi in chiaro",
        klartextH: "Questi tipi restano in chiaro — riconosciuti, ma non sostituiti.",
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
        offenText: "{} segnaposto sono rimasti — da controllare nel testo finale:",
        gutText: "{} segnaposto ripristinati.",
        promptT: "Prompt", hinausT: "Questo esce", trenner: "applica il prompt qui sopra al testo seguente",
        sendenZu: "Copia e apri {}", onlineWarnung: "In {} lavori online, fai attenzione!", origPlatz: "Incolla qui il testo originale …", promptPlatz: "Il tuo prompt, p. es. «Rispondi a questa e-mail gentilmente.»", hinausLeer: "Prima «Riprendi nel prompt» — poi qui vedrai cosa esce.",
        hinausZahl: "Esattamente questi {} caratteri andranno a {dienst} appena li incolli lì.",
        verworfenHinweis: "Vocabolario eliminato — il testo mascherato non è più ripristinabile.",
        an: "Attivo", aus: "Spento", spalteId: "ID",
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
        schriftT: "Carattere", schriftart: "Carattere",
        schriftgroesse: "Dimensione",
        schriftH: "Vale per le aree di testo — testo originale, testo mascherato, prompt e risposta.",
        schriftprobe: "Gentili signore, egregi signori",
        schriftAlles: "Anche per pulsanti ed etichette",
        schriftSans: "Senza grazie", schriftSerif: "Con grazie",
        schriftMono: "Larghezza fissa",
        herunterladen: "Scarica", einfuegen: "Incolla",
        einfuegenHinweis: "Appunti bloccati — usa Ctrl+V.",
        kAusschneiden: "Taglia", kKopieren: "Copia", kEinfuegen: "Incolla",
        menu: "Menu",
        mBrowser: "Apri nel browser", mHilfe: "Aiuto",
        mHilfeBald: "in arrivo", mWebseite: "maschera.ch",
        mGithub: "Codice sorgente su GitHub", mDownload: "Scarica",
        mFehler: "Segnala un problema",
        mImpressum: "Note legali", mKontakt: "Contatto",
        finalKopieren: "Copiare il testo finale",
        vokHerunter: "Scarica il vocabolario",
        vokHoch: "Carica il vocabolario",
        tplMenu: "Modelli", tplSichern: "Salva",
        tplWaehlen: "Scegliere un modello ({})",
        tplSuchen: "Cerca …", tplNichts: "Nessun modello corrisponde.",
        tplLokal: "salvato in locale",
        tplLeer: "Nessun modello salvato",
        tplName: "Nome del modello",
        tplWarnung: "I modelli restano in chiaro sul disco. "
          + "Non scrivervi dati personali.",
        tplWeg: "Eliminare il modello «{}»?", tplWegT: "Elimina",
        tplGesichert: "Modello «{}» salvato.",
        tplFehler: "Modello non salvato: {}",
        sichernWarnung: "Il file contiene {} valori originali in chiaro — "
          + "tutto ciò che è stato mascherato. Resterà senza protezione "
          + "nella cartella dei download. Salvare?",
        vokGeladen: "{} voci di vocabolario caricate.",
        vokKaputt: "Il file non è JSON leggibile — non caricato nulla.",
        frageJa: "Continua",
        frageNein: "Annulla",
        frageOk: "Conferma",
        neuladenFrage: "Ricaricare davvero?\n{} voci di vocabolario andranno perse.",
        verbindungWeg: "Nessuna connessione al servizio MASCHERA — la richiesta non è arrivata. Riprova; se non basta, riavvia MASCHERA.",
        httpFehler: "Il servizio MASCHERA ha rifiutato la richiesta (errore {status}).",
        vokFalsch: "Il file non contiene un oggetto — non caricato nulla.",
        vokFremd: "Non è un vocabolario MASCHERA — non caricato nulla.",
        vokFassung: "Versione sconosciuta {} — questa edizione legge la 1.",
        vokKein: "Nessun dizionario nel file — non caricato nulla.",
        vokSchluessel: "Segnaposto non valido: {} — non caricato nulla.",
        vokWert: "Il valore di {} non è una stringa — non caricato nulla.",
        vokText: "Il testo mascherato nel file non è una stringa.",
        einklappen: "Richiudi", ausklappen: "Apri",
        bearbeiten: "Modifica", bearbeitenFertig: "Fatto",
        bearbeitenHilfe: "Correggere il testo a mano. Lasciare i segnaposto come [FULLNAME_1] — vengono ripristinati alla fine.",
        phUnbekannt: "Il dizionario non conosce questi segnaposto: {liste}. Resteranno invariati.",
        phEntwertet: "{} segnaposto recuperati dalla marcatura Markdown — il servizio li aveva protetti con barre rovesciate.",
        phErgaenzt: "{} segnaposto spezzati completati: {liste}. Il dizionario li conosce — il servizio aveva inghiottito la parentesi.",
        phKaputt: "Questi punti sembrano segnaposto ma non lo sono: {liste}. NON verranno ripristinati — da controllare nel testo.",
        fussLinks: "MASCHERA · elaborazione su questo dispositivo · nessuna connessione online ai servizi IA", bereitS: "Pronto",
        orig: "Testo originale", masked: "Mascherato", run: "Maschera",
        fertig: "Testo finale", prompt: "Prompt",
        antwort: "Risposta", neu: "Nuovo", lokal: "Locale", online: "Online",
        hundert: "100% locale", einst: "Impostazioni",
        spruch: "Maschera i tuoi dati prima di condividerli! · "
              + "Modello locale · LPD / GDPR",
        spruch1: "Maschera i tuoi dati prima di condividerli!",
        spruch2: "Modello locale · LPD / GDPR",
        laden: "Caricamento del modello locale",
        keinStart: "Nessun server su /api/zustand: {}",
        zeichenN: (n) => n + " caratteri",
        eintraegeN: (n) => n + " voci",
        maskiertN: (n) => n + " mascherati",
        leer05: "Il testo finale apparirà qui appena applichi il vocabolario.",
        leer02: "Niente mascherato. Incolla un testo nella colonna 1 e premi "
              + "«Maschera».",
        dropN: "Trascina PDF, DOCX, TXT o e-mail — oppure clicca",
        laeuft: "in corso …", lWartet: "Preparazione del testo …", lModell: "Finestra {} di {}", lMaskieren: "Mascheratura, creazione del glossario …", lRest: "ancora circa {}", lFertig: "mascherato in {}", drop: "Trascina un file o scegli",
        portFehlt: "Nessuna porta indicata.",
        verwerfenVok: "Continuare davvero?\n{} voci di vocabolario andranno perse.",
        verwerfenText: "Continuare davvero?\nIl testo nella colonna 1 andrà perso.",
        neuAlles: "Vuoi davvero ricominciare?\nTutti i dati verranno azzerati!",
        liestDatei: "Lettura del file …",
        beispiel: "Esempio", leeren: "Svuota", kopieren: "Copia",
        kopiert: "Copiato", funde: "Occorrenze", vokabular: "Vocabolario",
        verworfen: "Scartato per poco", nichts: "niente",
        bereit: "pronto", quelle: "Fonte", vertrauen: "Fiducia",
        zeichen: "Caratteri", anteil: "mascherato",
        ohneModell: "SENZA MODELLO — solo checksum e pattern. Nomi, date e "
                  + "indirizzi restano in chiaro.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "SENZA MODELLO — solo checksum e pattern. Nomi, date e indirizzi restano IN CHIARO.",
          fenster: "Più lungo di una finestra ({token} token). Elaborato con sovrapposizione.",
          wortgrenzen: "{anzahl} intervalli del modello cadevano dentro una parola e sono stati estesi ai confini di parola.",
          mehrere_nachrichten: "{anzahl} messaggi nel file — viene elaborato solo il primo.",
          vorlieben: "Dalle preferenze salvate, in chiaro: {tags}",
          ohne_woerterbuch: "Senza dizionario — anonimizzato definitivamente, nessun ritorno possibile.",
          eigene_regeln: "Regole proprie applicate ({anzahl}): {namen}",
          schreibweise: "{platzhalter} differisce da {treffer} solo per maiuscole e minuscole — non sostituito.",
          anhang_uebersprungen: "Allegato saltato: {name}",
          kein_textteil: "L’e-mail non ha una parte di testo, solo {art}.",
          msg_ohne_textrumpf: "Il .msg non ha un corpo in testo semplice (solo RTF o HTML). In Outlook scegliere «Salva con nome» → .eml.",
          binaer_abgeschnitten: "{zeichen} caratteri dopo la fine del testo sembravano dati binari e sono stati omessi.",
          nur_html: "presente solo la parte HTML, ripulita sommariamente",
          kein_rumpf: "nessun corpo di testo trovato",
          pdf_ohne_text: "nessun testo nel PDF — probabilmente una scansione. Senza OCR il filtro non vede nulla, e un esito vuoto NON significa che non ci siano dati personali.",
          pdf_seiten: "{anzahl} pagine, il layout va perso in lettura",
          tabellen: "{anzahl} tabelle, lette riga per riga",
          nicht_gelesen: "NON letto: {teile} — lì nelle lettere si trova spesso il mittente",
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
          datei_unlesbar: "File illeggibile — danneggiato o formato non supportato.",
          datei_zu_gross: "File più grande di {mb} MB.",
          dienst_kein_objekt: "Il servizio {nummer} non è un oggetto.",
          dienst_kennung_doppelt: "Identificativo assegnato due volte: {kennung}",
          dienst_ohne_adresse: "Il servizio {name} non ha indirizzo.",
          dienst_ohne_namen: "Il servizio {nummer} non ha nome.",
          dienst_schema: "Servizio {name}: solo https:// o http://, non {adresse}",
          dienste_keine_liste: "Il campo `dienste` non è un elenco.",
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
          klartext_gespeichert: "Salvato. Questi tipi restano permanentemente in chiaro — anche nei documenti futuri.",
          nicht_gespeichert: "Non salvato — impossibile scrivere il file nella cartella delle impostazioni.",
          ohne_tags_unbekannt: "Tipi sconosciuti in `ohne`: {tags}",
          port_ausserhalb: "Porta fuori da 1–65535: {port}",
          regeldatei_fehlerhaft: "Il file delle regole è difettoso e non è stato applicato.",
          regeln_abgelehnt: "Regole rifiutate — il file contiene un errore.",
          regeln_gelesen: "Chi cambia le regole cambia il risultato della misurazione.",
          regeln_veraltete_schluessel: "Questo file di regole usa chiavi obsolete. Vengono ancora lette o ignorate: {umbenennungen}",
          regeln_gespeichert: "Salvato. Il risultato della misurazione cambia di conseguenza.",
          regeln_unlesbar: "Regole illeggibili — un campo ha la forma sbagliata.",
          schrift_ueberall_kein_wahrheitswert: "Il campo `schrift_ueberall` non è un valore booleano.",
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
          regel_zu_langsam: "Regola «{id}»: il modello impiega {dauer} s per una riga di prova — troppo lento, spesso per ripetizioni annidate come (a+)+.",
          regel_ohne_kennung: "Una regola non ha identificativo (`id`).",
          regel_kennung: "Identificativo «{id}»: solo minuscole, cifre e trattino basso, da 2 a 32 caratteri.",
          regel_platzhalter: "Regola «{id}»: il segnaposto «{platzhalter}» deve avere da 2 a 20 lettere o cifre.",
          regel_woerter_leer: "Regola «{id}»: l'elenco di parole (`words`) è vuoto.",
          regel_woerter_kurz: "Regola «{id}»: voci troppo corte ({kurz}). Sotto i {min} caratteri colpiscono ovunque come sillaba.",
          regel_etiketten_leer: "Regola «{id}»: `labels` è vuoto — senza etichetta la regola colpirebbe qualsiasi numero.",
          regel_wertform: "Regola «{id}»: la forma di valore «{form}» non esiste. Possibile: {moeglich}",
          regel_min_max: "Regola «{id}»: min/max non plausibili ({min}/{max}).",
          regel_muster_fehlt: "Regola «{id}»: manca il modello (`pattern`).",
          regel_muster_ungueltig: "Regola «{id}»: il modello non è valido (al carattere {stelle}).",
          regel_art: "Regola «{id}»: il tipo «{art}» non esiste. Possibile: {moeglich}",
          regeln_doppelt: "Questi identificativi di regola compaiono due volte: {kennungen}",
          regel_platzhalter_vergeben: "Segnaposto già assegnato: {platzhalter}. Scegli un altro nome.",
          msg_ohne_olefile: "I messaggi Outlook (.msg) non si possono leggere qui. In Outlook «Salva con nome» → .eml.",
          pdf_ohne_pymupdf: "I PDF non si possono leggere qui — manca la libreria PDF.",
          docx_zu_gross: "Il documento Word sarebbe di {mb} MB una volta decompresso; se ne leggono al massimo {hoechstens} MB.",
          docx_kaputt: "Nessun file .docx leggibile. I vecchi .doc sono un altro formato.",
          docx_ohne_dokument: "Non è un documento Word — probabilmente .odt, .pptx o .xlsx con estensione sbagliata.",
          docx_dtd: "Il documento Word contiene una DTD; nei veri file Word non esiste e non viene letto.",
          word_alt: "Il vecchio formato Word (.doc) non viene letto. Salvalo come .docx in Word o LibreOffice.",
        },
        leer: "Niente mascherato finora." },
  en: { zurueckW: "Way back", uebernahme: "Take into prompt",
        einpflegen: "Apply vocabulary", rueckPlatz: "Paste your AI tool’s answer here …", kopiertK: "Copied",
        ersetztN: "{} placeholders restored", nichtGefunden: "Unmatched: {}",
        maskeWeg: "Remove mask",
        haeufig: "Frequent",
        alleTags: "All types …",
        nichtMaskiert: "not masked",
        bspdWeg: "Really remove the mask?\n{} is sensitive personal data.",
        bspdSetzen: "Mask as {}?\nThis is sensitive personal data.",
        einstT: "Settings",
        schliessen: "Close", einstZu: "Save", einstZuRest: " & close",
        allgemeinT: "General",
        serverT: "Server",
        serverH: "Address and port of the local masking service. The text never leaves your device — the check shows whether the service responds.",
        adresse: "Address",
        port: "Port",
        pruefen: "Check",
        neuStarten: "Save & restart",
        nurSpeichern: "Save",
        startetNeu: "MASCHERA is restarting …",
        giltNachNeustart: "Saved. Applies from the next start of the service.",
        keinDienstDa: "No MASCHERA answers at {}.",
        diensteT: "Services",
        diensteH: "The web link opens when you copy.",
        hinzu: "Add",
        entfernen: "Remove",
        fensterWort: "Open in a window rather than a tab",
        trayWort: "On close, minimise to the tray instead of quitting",
        widgetWort: "Narrow window, always on top",
        fensterHilfe: "Both take effect after restarting the application.",
        klartextT: "Plaintext types",
        klartextH: "These types stay in the clear — detected, but not replaced.",
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
        offenText: "{} placeholders remained — check them in the final text:",
        gutText: "{} placeholders restored.",
        promptT: "Prompt", hinausT: "This goes out", trenner: "apply the prompt above to the following text",
        sendenZu: "Copy and open {}", onlineWarnung: "In {} you are working online — be careful!", origPlatz: "Paste the original text here …", promptPlatz: "Your prompt, e.g. \u00abReply to this e-mail politely.\u00bb", hinausLeer: "First «Take into prompt» — then you see here what goes out.",
        hinausZahl: "Exactly these {} characters go to {dienst} once you paste them there.",
        verworfenHinweis: "Vocabulary discarded — the masked text can no longer be restored.",
        an: "On", aus: "Off", spalteId: "ID",
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
        schriftT: "Type", schriftart: "Typeface",
        schriftgroesse: "Size",
        schriftH: "Applies to the text areas — original, masked text, prompt and reply.",
        schriftprobe: "Dear Sir or Madam",
        schriftAlles: "Also for buttons and labels",
        schriftSans: "Sans serif", schriftSerif: "Serif",
        schriftMono: "Monospace",
        herunterladen: "Download", einfuegen: "Paste",
        einfuegenHinweis: "Clipboard blocked — press Ctrl+V.",
        kAusschneiden: "Cut", kKopieren: "Copy", kEinfuegen: "Paste",
        menu: "Menu",
        mBrowser: "Open in browser", mHilfe: "Help",
        mHilfeBald: "coming soon", mWebseite: "maschera.ch",
        mGithub: "Source code on GitHub", mDownload: "Download",
        mFehler: "Report an issue",
        mImpressum: "Legal notice", mKontakt: "Contact",
        finalKopieren: "Copy final text",
        vokHerunter: "Download vocabulary",
        vokHoch: "Upload vocabulary",
        tplMenu: "Templates", tplSichern: "Save",
        tplWaehlen: "Choose a template ({})",
        tplSuchen: "Search …", tplNichts: "No template matches.",
        tplLokal: "stored locally",
        tplLeer: "No template saved yet",
        tplName: "Template name",
        tplWarnung: "Templates stay in plain text on disk. "
          + "Do not put personal data into a template.",
        tplWeg: "Delete template “{}”?", tplWegT: "Delete",
        tplGesichert: "Template “{}” saved.",
        tplFehler: "Template not saved: {}",
        sichernWarnung: "The file holds {} original values in plain text — "
          + "everything masked here. It will then sit unprotected in your "
          + "downloads folder. Save?",
        vokGeladen: "{} vocabulary entries loaded.",
        vokKaputt: "The file is not readable JSON — nothing loaded.",
        frageJa: "Continue",
        frageNein: "Cancel",
        frageOk: "OK",
        neuladenFrage: "Really reload?\n{} vocabulary entries will be lost.",
        verbindungWeg: "No connection to the MASCHERA service — the request did not arrive. Try again; if that does not help, restart MASCHERA.",
        httpFehler: "The MASCHERA service refused the request (error {status}).",
        vokFalsch: "The file does not contain an object — nothing loaded.",
        vokFremd: "Not a MASCHERA vocabulary file — nothing loaded.",
        vokFassung: "Unknown version {} — this build reads version 1.",
        vokKein: "No dictionary in the file — nothing loaded.",
        vokSchluessel: "Not a valid placeholder: {} — nothing loaded.",
        vokWert: "The value for {} is not a string — nothing loaded.",
        vokText: "The masked text in the file is not a string.",
        einklappen: "Collapse", ausklappen: "Expand",
        bearbeiten: "Edit", bearbeitenFertig: "Done",
        bearbeitenHilfe: "Correct the text by hand. Leave placeholders such as [FULLNAME_1] in place — they are restored at the end.",
        phUnbekannt: "The dictionary does not know these placeholders: {liste}. They will stay as they are.",
        phEntwertet: "{} placeholders recovered from Markdown escaping — the service had escaped them with backslashes.",
        phErgaenzt: "{} broken placeholders completed: {liste}. The dictionary knows them — the service swallowed the bracket.",
        phKaputt: "These passages look like placeholders but are not: {liste}. They will NOT be restored — please check them in the text.",
        fussLinks: "MASCHERA · processed on this device · no online connection to the AI services", bereitS: "Ready",
        orig: "Original text", masked: "Masked", run: "Mask",
        fertig: "Final text", prompt: "Prompt",
        antwort: "Answer", neu: "New", lokal: "Local", online: "Online",
        hundert: "100% local", einst: "Settings",
        spruch: "Mask your data before you share it! · "
              + "Local model · FADP / GDPR",
        spruch1: "Mask your data before you share it!",
        spruch2: "Local model · FADP / GDPR",
        laden: "Loading the local model",
        keinStart: "No server on /api/zustand: {}",
        zeichenN: (n) => n + " characters",
        eintraegeN: (n) => n + " entries",
        maskiertN: (n) => n + " masked",
        leer05: "The final text appears here once you apply the vocabulary.",
        leer02: "Nothing masked yet. Paste text into column 1 and press "
              + "\u00abMask\u00bb.",
        dropN: "Drop a PDF, DOCX, TXT or e-mail — or click",
        laeuft: "running …", lWartet: "Preparing the text …", lModell: "Window {} of {}", lMaskieren: "Masking, building the glossary …", lRest: "about {} left", lFertig: "masked in {}", drop: "Drop a file or choose one",
        portFehlt: "No port given.",
        verwerfenVok: "Really continue?\n{} vocabulary entries will be lost.",
        verwerfenText: "Really continue?\nThe text in column 1 will be lost.",
        neuAlles: "Do you really want to start over?\nAll data will be reset!",
        liestDatei: "Reading file …",
        beispiel: "Example", leeren: "Clear", kopieren: "Copy",
        kopiert: "Copied", funde: "Findings", vokabular: "Vocabulary",
        verworfen: "Narrowly discarded", nichts: "none",
        bereit: "ready", quelle: "Source", vertrauen: "Confidence",
        zeichen: "Characters", anteil: "masked",
        ohneModell: "NO MODEL — checksums and patterns only. Names, dates "
                  + "and addresses stay in the clear.",
        // Hinweise des Servers. Er schickt den Schluessel und die
        // Werte, der Satz steht hier — s. `core/hinweise.py`.
        hinweise: {
          ohne_modell: "NO MODEL — checksums and patterns only. Names, dates and addresses stay IN THE CLEAR.",
          fenster: "Longer than one window ({token} tokens). Processed with overlap.",
          wortgrenzen: "{anzahl} model spans fell inside a word and were extended to word boundaries.",
          mehrere_nachrichten: "{anzahl} messages in the file — only the first one is processed.",
          vorlieben: "From the saved preferences, in the clear: {tags}",
          ohne_woerterbuch: "Without a dictionary — anonymised for good, no way back.",
          eigene_regeln: "Own rules applied ({anzahl}): {namen}",
          schreibweise: "{platzhalter} differs from {treffer} only in capitalisation — not replaced.",
          anhang_uebersprungen: "Attachment skipped: {name}",
          kein_textteil: "The e-mail has no text part, only {art}.",
          msg_ohne_textrumpf: "The .msg has no plain-text body (only RTF or HTML). In Outlook choose «Save as» → .eml.",
          binaer_abgeschnitten: "{zeichen} characters after the end of the text looked like binary data and were left out.",
          nur_html: "only an HTML part present, roughly stripped",
          kein_rumpf: "no text body found",
          pdf_ohne_text: "no text in the PDF — probably a scan. Without OCR the filter sees nothing, and an empty finding does NOT mean there is no personal data in it.",
          pdf_seiten: "{anzahl} pages, layout is lost on reading",
          tabellen: "{anzahl} tables, read row by row",
          nicht_gelesen: "NOT read: {teile} — that is where letters often carry the sender",
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
          datei_unlesbar: "File not readable — damaged or an unsupported format.",
          datei_zu_gross: "File larger than {mb} MB.",
          dienst_kein_objekt: "Service {nummer} is not an object.",
          dienst_kennung_doppelt: "Identifier used twice: {kennung}",
          dienst_ohne_adresse: "Service {name} has no address.",
          dienst_ohne_namen: "Service {nummer} has no name.",
          dienst_schema: "Service {name}: only https:// or http://, not {adresse}",
          dienste_keine_liste: "Field `dienste` is not a list.",
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
          klartext_gespeichert: "Saved. These types stay in plain text permanently — in future documents as well.",
          nicht_gespeichert: "Not saved — the file in the settings folder could not be written.",
          ohne_tags_unbekannt: "Unknown types in `ohne`: {tags}",
          port_ausserhalb: "Port outside 1–65535: {port}",
          regeldatei_fehlerhaft: "The rule file is faulty and was not applied.",
          regeln_abgelehnt: "Rules rejected — the file contains an error.",
          regeln_gelesen: "Changing the rules changes the measured result.",
          regeln_veraltete_schluessel: "This rule file uses outdated keys. They are still read or skipped: {umbenennungen}",
          regeln_gespeichert: "Saved. The measured result changes with it.",
          regeln_unlesbar: "Rules not readable — a field has the wrong form.",
          schrift_ueberall_kein_wahrheitswert: "Field `schrift_ueberall` is not a boolean.",
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
          regel_zu_langsam: "Rule “{id}”: the pattern takes {dauer} s on a test line — too slow, usually because of nested repetition such as (a+)+.",
          regel_ohne_kennung: "A rule has no identifier (`id`).",
          regel_kennung: "Rule identifier “{id}”: lowercase letters, digits and underscore only, 2 to 32 characters.",
          regel_platzhalter: "Rule “{id}”: the placeholder “{platzhalter}” must be 2 to 20 letters or digits.",
          regel_woerter_leer: "Rule “{id}”: the word list (`words`) is empty.",
          regel_woerter_kurz: "Rule “{id}”: entries too short ({kurz}). Below {min} characters they match everywhere as a syllable.",
          regel_etiketten_leer: "Rule “{id}”: `labels` is empty — without a label the rule would match any number.",
          regel_wertform: "Rule “{id}”: the value form “{form}” does not exist. Possible: {moeglich}",
          regel_min_max: "Rule “{id}”: implausible min/max ({min}/{max}).",
          regel_muster_fehlt: "Rule “{id}”: the pattern (`pattern`) is missing.",
          regel_muster_ungueltig: "Rule “{id}”: the pattern is invalid (at character {stelle}).",
          regel_art: "Rule “{id}”: the type “{art}” does not exist. Possible: {moeglich}",
          regeln_doppelt: "These rule identifiers appear twice: {kennungen}",
          regel_platzhalter_vergeben: "Placeholder already taken: {platzhalter}. Choose another name.",
          msg_ohne_olefile: "Outlook messages (.msg) cannot be read here. In Outlook choose “Save as” → .eml.",
          pdf_ohne_pymupdf: "PDFs cannot be read here — the PDF library is missing.",
          docx_zu_gross: "The Word document would be {mb} MB unpacked; at most {hoechstens} MB are read.",
          docx_kaputt: "Not a readable .docx file. Older .doc files are a different format.",
          docx_ohne_dokument: "Not a Word document — probably .odt, .pptx or .xlsx with the wrong extension.",
          docx_dtd: "The Word document declares a DTD; real Word files never do, so it is not read.",
          word_alt: "The old Word format (.doc) is not read. Save it as .docx in Word or LibreOffice.",
        },
        leer: "Nothing masked yet." }
};

/* Die vorgegebenen Dienste. Die Einstellungen koennen sie aendern. */
const DIENSTE = [
  { id: "claude",  name: "Claude",  url: "https://claude.ai/new" },
  { id: "chatgpt", name: "ChatGPT", url: "https://chatgpt.com/" },
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
  vokabular: true,
  vokabularVerworfen: false,
  sendeUhr: null,
  // Haelt den Ziehschleier, solange `dragover` nachkommt.
  ziehUhr: null,
  // Holt den Stand, solange maskiert wird.
  fortschrittUhr: null,
  // Erst ein Klick auf «Uebernahme in Prompt» traegt den maskierten Text in
  // die dritte Spalte. Vorher steht dort NICHTS von diesem Dokument: die
  // Spalte, die hinausgeht, fuellt sich nicht von selbst.
  uebernommen: false,
  // Das Vokabular startet in der einspaltigen Ansicht ZUGEKLAPPT. Es steht
  // dort am Ende des Weges und wird selten gebraucht.
  vokZu: true,
  prompt: "",
  antwort04: "",
  zurueck: false,
  antwortText: "",
  final: null,
  dienst: "claude",
  kontext: null,
  kontextGruppe: null,   // welche Gruppe im Kontextmenue offen ist
  dienste: DIENSTE.map((d) => ({ ...d })),
  eigenesFenster: true,
  schriftgroesse: 100,
  schriftart: "werk",
  schriftUeberall: false,
  klartext: [],
  bspdTags: [],
  regelnYaml: "",
  dateiname: "",
  vokMeldung: null,
  // Die Meldung des Einstellungsdialogs — ein eigener Kanal, siehe meldeVok().
  einstMeldung: "",
  vorlagen: [],
  vorlage: null,          // Name der gewaehlten Vorlage
  vorlagenOffen: false,
  vorlagenFilter: "",
  offen: { funde: true, vokabular: false, verworfen: false }
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
    body: JSON.stringify({ text: text, woerterbuch: z.vokabular,
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
  if (span) {
    const teile = [span.tag, span.quelle];
    if (span.vertrauen != null) teile.push(span.vertrauen.toFixed(2));
    if (span.bspd) teile.push("bsPD");
    s.title = teile.join(" · ");
    s.dataset.tag = span.tag;
    s.dataset.quelle = span.quelle;
    s.dataset.ph = span.platzhalter || text;
  }
  return s;
}

function zeichneMaskiert() {
  const ziel = $("maskiert");
  ziel.replaceChildren();
  if (!z.antwort) {
    ziel.append(el("p", "leer", t().leer02));
    return;
  }
  const text = z.antwort.maskiert || "";
  const spans = (z.antwort.spans || []).slice();

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
  const reihe = spans.filter((sp) => !sp.platzhalter);
  let n = 0;

  let letzte = 0, m;
  PH_RE.lastIndex = 0;
  while ((m = PH_RE.exec(text)) !== null) {
    if (m.index > letzte) {
      ziel.append(document.createTextNode(text.slice(letzte, m.index)));
    }
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
  if (letzte < text.length) {
    ziel.append(document.createTextNode(text.slice(letzte)));
  }
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
    ? lage.ph + " · " + (lage.quelle || "?")
    : st.nichtMaskiert));
  menu.append(kopf);

  if (lage.ph) {
    const weg = el("button", "entfernen");
    weg.type = "button";
    weg.append(el("span", "marke", "×"),
               document.createTextNode(st.maskeWeg));
    weg.addEventListener("click", () => handlungEntfernen(lage));
    menu.append(weg, el("div", "trenner"));
  }

  const eintrag = (tag) => {
    const meta = z.tags[tag] || {};
    const b = el("button");
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

  menu.append(el("div", "gruppe", st.haeufig));
  for (const tag of FREQUENT) {
    if (z.tags[tag]) menu.append(eintrag(tag));
  }

  /* Alle 45 Tags, in Gruppen, jede aufklappbar.
   *
   * Die Reihenfolge ist die von `TAG_GRUPPEN`, nicht alphabetisch. Sie folgt
   * dem Dokument: Person, Herkunft, Anschrift, Erreichbarkeit — so sucht
   * jemand, der einen Brief vor sich hat.
   *
   * Immer nur EINE Gruppe offen: bei acht Gruppen und 45 Tags waere alles
   * offen eine Liste, die laenger ist als der Bildschirm.
   */
  menu.append(el("div", "trenner"));
  const uebrig = new Set(Object.keys(z.tags));
  for (const g of Object.keys(TAG_GRUPPEN)) {
    for (const tag of TAG_GRUPPEN[g]) uebrig.delete(tag);
  }
  const gruppen = Object.keys(TAG_GRUPPEN).concat(
    uebrig.size ? ["rest"] : []);

  for (const g of gruppen) {
    const tags = (g === "rest" ? [...uebrig].sort()
                               : TAG_GRUPPEN[g].filter((x) => z.tags[x]));
    if (!tags.length) continue;
    const offen = z.kontextGruppe === g;
    // `aufgeklappt` und NICHT `offen`: die Klasse `.offen` gehoert der roten
    // Warnbox fuer nicht zugeordnete Platzhalter und traegt einen Rand, den der
    // Gruppenkopf sonst still miterbte.
    const kopfKnopf = el("button",
                         "gruppenkopf" + (offen ? " aufgeklappt" : ""));
    kopfKnopf.type = "button";
    kopfKnopf.setAttribute("aria-expanded", String(offen));
    kopfKnopf.append(document.createTextNode((st.gruppen || {})[g] || g),
                     el("span", "pfeil", offen ? "\u2303" : "\u2304"));
    kopfKnopf.addEventListener("click", (e) => {
      e.stopPropagation();
      z.kontextGruppe = offen ? null : g;
      // Neu zeichnen an derselben Stelle — das Menue bleibt, wo es ist. Der
      // vierte Wert haelt die Lage fest.
      zeichneKontext(x, y, lage, true);
    });
    menu.append(kopfKnopf);
    if (offen) for (const tag of tags) menu.append(eintrag(tag));
  }

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

  // Legende: je Tagart eine Plakette mit Anzahl, alphabetisch.
  const zaehler = {};
  for (const sp of spans) {
    if (!sp.platzhalter) continue;
    zaehler[sp.tag] = (zaehler[sp.tag] || 0) + 1;
  }
  const leg = $("legende");
  leg.replaceChildren();
  for (const tag of Object.keys(zaehler).sort()) {
    const c = farbe(tag);
    const chip = el("span", "chip");
    chip.style.background = c[0];
    chip.style.border = "1px solid " + c[1];
    chip.style.color = c[2];
    const punkt = el("i");
    punkt.style.background = c[1];
    chip.append(punkt, document.createTextNode(tag + " "),
                el("b", null, String(zaehler[tag])));
    leg.append(chip);
  }

  const ziel = $("vokabular-inhalt");
  ziel.replaceChildren();
  if (!schluessel.length) {
    ziel.append(el("p", "vokabular-leer",
      z.vokabular ? s.keinVokabular : s.keinVokabularAus || s.keinVokabular));
    return;
  }

  const tab = el("table", "vokabular");
  const kopf = el("tr");
  kopf.append(el("th", null, s.spalteId), el("th", null, s.spalteWert),
              el("th", null, s.spalteTyp));
  const thead = el("thead"); thead.append(kopf);
  const tbody = el("tbody");

  // Sortiert nach Platzhalter, nicht nach Fundreihenfolge — sonst springt
  // die Tabelle bei jedem Lauf, und man sucht Zeilen statt sie zu lesen.
  for (const ph of schluessel.sort()) {
    const typ = typOf(ph);
    const c = farbe(typ);
    const tr = el("tr");

    const td1 = el("td");
    const kennung = el("span", "vok-ph", ph);
    kennung.style.background = c[0];
    kennung.style.border = "1px solid " + c[1];
    kennung.style.color = c[2];
    td1.append(kennung);

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

    const td3 = el("td");
    const art = el("span", "vok-ph", typ);
    art.style.background = c[0];
    art.style.border = "1px solid " + c[1];
    art.style.color = c[2];
    td3.append(art);

    tr.append(td1, td2, td3);
    tbody.append(tr);
  }
  tab.append(thead, tbody);
  ziel.append(tab);
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
  if (z.vokabularVerworfen) {
    const p = el("p", "hinweis warnhinweis", t().verworfenHinweis);
    ziel.append(p);
  }
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
  // Die GEMESSENE Dauer, vom Server — ohne Zahl stuende in einem
  // Fehlerbericht «es war langsam». Sie steht am Schluss, weil sie den Lauf
  // beschreibt und nicht den Text.
  const ms = z.antwort && z.antwort.kennzahlen
    && z.antwort.kennzahlen.dauer_ms;
  if (typeof ms === "number") {
    ruhig.push(t().lFertig.replace("{}", dauerWort(ms)));
  }
  // Das Trennzeichen ist `·` — dasselbe wie im Untertitel der Kopfzeile und
  // in der Fusszeile.
  if (ruhig.length) {
    ziel.append(el("p", "hinweis hinweiszeile", ruhig.join(" · ")));
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
  $("vok-herunter-text").textContent = s.vokHerunter;
  $("vok-hoch-text").textContent = s.vokHoch;
  $("vorlagen-lokal").textContent = s.tplMenu + " (" + s.tplLokal + ")";
  $("vorlagen-filter").placeholder = s.tplSuchen;
  $("vorlage-sichern-text").textContent = s.tplSichern;
  $("vorlagen-lokal").textContent = s.tplLokal;
  // BEIDES im Tooltip, und die Reihenfolge ist Absicht.
  //
  // Wird die Spalte eng, verschwindet die Beschriftung und nur das Zeichen
  // bleibt — dann ist der Tooltip das Einzige, was den Knopf erklaert. Hier
  // steht aber schon ein WARNENDER: Vorlagen liegen dauerhaft im Klartext auf
  // der Platte. Was der Knopf tut, erraet man am Zeichen; dass die Vorlage im
  // Klartext landet, nicht.
  $("knopf-vorlage-sichern").title = s.tplSichern + " — " + s.tplWarnung;
  $("spruch").textContent = s.spruch;
  $("lokalzeiger").textContent = s.hundert;
  $("ablage-text").textContent = s.dropN;
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
  for (const e of document.querySelectorAll(".p-lokal")) {
    e.textContent = s.lokal;
  }
  for (const e of document.querySelectorAll(".p-online")) {
    e.textContent = s.online;
  }
  $("neu-text").textContent = s.neu;
  $("neu-unten-text").textContent = s.neu;
  $("knopf-beispiel").textContent = s.beispiel;
  $("maskieren-text").textContent = z.laeuft ? s.laeuft : s.run;
  $("kopieren-text").textContent = s.kopieren;
  $("bearbeiten-text").textContent =
    z.bearbeiten ? s.bearbeitenFertig : s.bearbeiten;
  $("knopf-bearbeiten").title = s.bearbeitenHilfe;
  $("maskiert-feld").placeholder = s.bearbeitenHilfe;
  $("kopieren-orig-text").textContent = s.kopieren;
  $("einklappen-text").textContent = s.einklappen;
  $("schiene").title = s.ausklappen;
  $("schiene-text").textContent = "03 · " + s.prompt;
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
       i < fussTeile.length - 1 ? teil + " · " : teil)));
  $("zurueck-wort").textContent = s.zurueckW;
  // Bereich 02 und Bereich 04 sind zwei Felder mit zwei Schluesseln — in
  // 02 wird eingefuegt UND getippt.
  $("antwortfeld").placeholder = s.rueckPlatz;
  $("uebernahme-text").textContent =
    z.zurueck ? s.einpflegen : s.uebernahme;
  $("herunter-mask-text").textContent = s.herunterladen;
  $("herunter-final-text").textContent = s.herunterladen;
  $("einfuegen-antwort-text").textContent = s.einfuegen;
  for (const kid of ["knopf-leeren-orig", "knopf-leeren-prompt",
                     "knopf-leeren-antwort"]) {
    $(kid).title = s.leerenA;
    $(kid).setAttribute("aria-label", s.leerenA);
  }
  $("final-kopieren-text").textContent = s.finalKopieren;
  $("titel-prompt").textContent = s.promptT;
  $("titel-hinaus").textContent = s.hinausT;
  // Bereich 01: auch der Platzhalter eines Textfelds wird uebersetzt. Punkt
  // 60 prueft den Text von Elementen UND ihre Platzhalter-Attribute.
  $("orig").placeholder = s.origPlatz;
  $("prompt").placeholder = s.promptPlatz;
  $("kopieren-prompt-text").textContent = s.kopieren;
  $("kopieren-hinaus-text").textContent = s.kopieren;
  $("einst-titel").textContent = s.einstT;
  // Die Zeichen an den nachgeruesteten Knoepfen. Sie kommen hierher und
  // nicht ins HTML, weil `KNOPFBILDER` die eine Quelle ist. Gesetzt wird
  // EINMAL: `zeichneBeschriftung()` laeuft bei jedem Sprachwechsel, und ein
  // zweiter Aufruf haengte ein zweites Zeichen an.
  for (const [kennung, bild] of [["knopf-regeln-speichern", "speichern"],
                                 ["knopf-dienst-neu", "hinzufuegen"],
                                 ["knopf-seite-zu", "schliessen"]]) {
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
  $("einst-schriftprobe").textContent = s.schriftprobe;
  $("einst-schrift-ueberall-text").textContent = s.schriftAlles;
  // Die Eintraege der Schriftwahl wechseln die Sprache mit. «Barlow» bleibt,
  // wie es ist: der Name der Hausschrift, in jeder Sprache derselbe.
  $("schriftart-sans").textContent = s.schriftSans;
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
  const ziel = $("hinaus");
  ziel.replaceChildren();
  const anhang = uebernommenerText();
  if (!z.prompt && !anhang) {
    ziel.classList.add("istleer");
    ziel.append(document.createTextNode(s.hinausLeer));
    $("zahl-hinaus").textContent = "";
    return;
  }
  ziel.classList.remove("istleer");
  if (z.prompt) ziel.append(document.createTextNode(z.prompt));
  if (anhang) {
    ziel.append(el("span", "trenner", "———— " + s.trenner + " ————"));
    ziel.append(el("span", "anhang", anhang));
  }
  $("zahl-hinaus").textContent =
    s.hinausZahl.replace("{}", String(ausgehend().length))
                .replace("{dienst}", dienstJetzt().name);
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
  if (fehlend.length) {
    const kasten = el("div", "offen");
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
  $("knopf-leeren-final").hidden = !hat;
}

/* ========================================================================
 * Einstellungen
 * ==================================================================== */

function zeichneDienstliste() {
  const ziel = $("einst-dienste");
  ziel.replaceChildren();
  z.dienste.forEach((d, i) => {
    const zeile = el("div", "dienstzeile");
    const name = document.createElement("input");
    name.value = d.name; name.placeholder = "Name";
    name.addEventListener("change", (e) => {
      d.name = e.target.value; zeichne();
    });
    const url = document.createElement("input");
    url.value = d.url; url.placeholder = "https://…"; url.spellcheck = false;
    url.addEventListener("change", (e) => { d.url = e.target.value; });
    const weg = el("button", null, "×");
    weg.type = "button";
    weg.title = t().entfernen;
    weg.addEventListener("click", () => {
      z.dienste.splice(i, 1);
      if (!z.dienste.some((x) => x.id === z.dienst) && z.dienste.length) {
        z.dienst = z.dienste[0].id;
      }
      zeichneDienstliste(); zeichneDienstmenu(); zeichne();
    });
    zeile.append(name, url, weg);
    ziel.append(zeile);
  });
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

/* Ein leerer Name oder eine Adresse ohne `https://` haelt den Dialog
 * offen und nennt den Grund. Zumachen und den Stand verwerfen waere die
 * schlechtere Antwort: der Anwender hat gerade etwas eingetippt.
 */
async function einstellungenSchliessen() {
  const befund = $("einst-befund");
  try {
    await sichereEinstellungen();
  } catch (e) {
    befund.className = "einst-befund schlecht";
    befund.textContent = fehlerText(e);
    zeichne();
    return;
  }
  befund.className = "einst-befund";
  befund.textContent = "";
  z.einstMeldung = "";
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
  $("einst-befund").textContent = "";
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

/* Ein Dienst wird ueber die Anwendung geoeffnet, wo `window.open` nicht
 * verlaesslich ist: im eigenen Fenster unter macOS und Windows, wenn die
 * Bruecke die Methode anbietet. Unter Linux (Qt) und im Browser geht
 * `window.open`. */
function dienstUeberAnwendung() {
  const plattform = typeof navigator !== "undefined"
    ? String(navigator.platform || "") : "";
  return imEigenenFenster() && !/linux/i.test(plattform)
    && !!window.pywebview.api
    && typeof window.pywebview.api.oeffne_dienst === "function";
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
  const bild = el("img");
  bild.src = "maske.svg";
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
  for (const d of z.dienste) {
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

function zeichne() {
  zeichneBeschriftung();
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
  $("zahl-02").textContent = k
    ? s.zeichenN(mt.length) + " · " + s.maskiertN(k.maskiert)
    : s.zeichenN(mt.length);
  const w = (z.antwort && z.antwort.woerterbuch) || {};
  const eintraege = s.eintraegeN(Object.keys(w).length);
  $("zahl-vokabular").textContent = k
    ? s.anteilW + " " + Math.round((k.anteil || 0) * 100) + " % · " + eintraege
    : eintraege;
  // Diese Zahlen werden beim Zusammenstauchen als Erstes gekuerzt — sie sind
  // Auskunft, kein Bedienelement. Der volle Text steht im Tooltip.
  $("zahl-vokabular").title = $("zahl-vokabular").textContent;
  $("zahl-02").title = $("zahl-02").textContent;
  $("schalterwort").textContent = z.vokabular ? s.an : s.aus;
  $("schalter-vokabular").setAttribute("aria-checked", String(z.vokabular));
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
  // Im Rueckweg wird Bereich 02 zum Eingabefeld. Wer die dritte Spalte
  // nicht braucht — weil er selbst mit dem Text arbeitet —, kommt so
  // trotzdem zum fertigen Ergebnis.
  //
  // DREI Ansichten in EINEM Kasten, und sie schliessen einander aus: die
  // gesetzte Ansicht, das Schreibfeld zum Korrigieren und der «Weg zurueck».
  // Der Rueckweg gewinnt — wer ihn einschaltet, arbeitet nicht mehr am
  // maskierten Text.
  const bearbeitet = z.bearbeiten && !z.zurueck && !!z.antwort;
  $("maskiert").hidden = z.zurueck || bearbeitet;
  $("maskiert-feld").hidden = !bearbeitet;
  $("antwortfeld").hidden = !z.zurueck;
  $("knopf-kopieren").hidden = z.zurueck;
  $("knopf-bearbeiten").hidden = z.zurueck;
  $("knopf-bearbeiten").disabled = !(z.antwort && z.antwort.maskiert);
  $("knopf-bearbeiten").classList.toggle("aktiv", bearbeitet);
  $("schalter-zurueck").setAttribute("aria-checked", String(z.zurueck));
  $("knopf-uebernahme").disabled = z.zurueck
    ? !(z.antwortText.trim() && hatWoerterbuch())
    : !(z.antwort && z.antwort.maskiert);
  // Eine KLASSE, kein `style.transform`. Inline schlaegt jede Stilvorlage —
  // und in der einspaltigen Ansicht dreht das CSS alle Pfeile nach unten.
  $("uebernahme-pfeil").classList.toggle("gedreht", z.zurueck);
  zeichneFinal();
  $("knopf-kopieren-hinaus").disabled = !ausgehend().trim();
  $("knopf-einpflegen04").disabled =
    !z.antwort04.trim() || !hatWoerterbuch();
  $("knopf-leeren-antwort").hidden = !z.antwort04.trim();
  $("knopf-leeren-orig").hidden = !z.orig.trim();
  $("knopf-leeren-prompt").hidden = !z.prompt.trim();
  $("knopf-herunter-mask").disabled = !(z.antwort && z.antwort.maskiert);
  const fertig = !!(z.final && z.final.text);
  $("knopf-herunter-final").hidden = !fertig;
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
  $("onlinewarnung-text").textContent = warnsatz;
  // Derselbe Satz auch als Tooltip. Wird die Spalte eng, bleibt vom Hinweis
  // nur das Dreieck stehen (`maschera.css`, Behaelter `fuss`) — dann traegt
  // ihn der Tooltip. Kein zweiter Schluessel: es ist derselbe Satz.
  $("onlinewarnung").title = warnsatz;
  $("maskiert").classList.toggle("istleer", !z.antwort);
  vokabularKlappe();
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
function gestapelt() {
  // Dieselbe Abfrage wie im CSS, Wort fuer Wort — Breite ODER Hoehe. Sonst
  // stuenden die Kaesten untereinander, aber es gaebe keinen Sprung zum
  // naechsten Schritt.
  return window.matchMedia(
    "(max-width: 59.99em), (max-height: 44em)").matches;
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
  const kopf = $("kopfzeile");
  const verdeckt = kopf && getComputedStyle(kopf).position === "sticky"
    ? kopf.getBoundingClientRect().height : 0;
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
}

/* Das Vokabular auf- und zuklappen. Sichtbar ist der Knopf nur in der
 * einspaltigen Ansicht; der Zustand wird trotzdem immer gefuehrt, damit
 * beim Wechsel der Breite nichts springt. */
function vokabularKlappe() {
  const kasten = $("bvok");
  if (kasten) kasten.classList.toggle("zu", z.vokZu);
  const knopf = $("knopf-vok-klappe");
  if (knopf) knopf.setAttribute("aria-expanded", String(!z.vokZu));
}

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
  springeZu("b02");
  fortschrittHolen();
  try {
    z.antwort = await maskiere(z.orig);
    z.bearbeiten = false;
    z.vokabularVerworfen = false;
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
    z.vokabularVerworfen = false;
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
  $("knopf-beispiel").addEventListener("click", async () => {
    if (!(await verwerfenOk())) return;
    z.orig = BEISPIEL[z.sprache] || BEISPIEL.de;
    $("orig").value = z.orig;
    z.antwort = null;
    z.bearbeiten = false;
    zeichne();
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
      springeZu("b01");
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
    if (d && (await verwerfenOk())) ablegen(d);
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
    knopf.addEventListener("click", async () => {
      z.sprache = knopf.dataset.sprache;
      for (const k of document.querySelectorAll("[data-sprache]")) {
        k.classList.toggle("aktiv", k.dataset.sprache === z.sprache);
      }
      await ladeTags();
      zeichne();
      merkeSprache();
    });
  }

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
  // Vorlagenfeld und «Weg zurueck» eingeschlossen.
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

  $("knopf-vok-klappe").addEventListener("click", () => {
    z.vokZu = !z.vokZu;
    vokabularKlappe();
    if (!z.vokZu) springeZu("bvok");
  });

  document.addEventListener("click", (e) => {
    const menu = $("kontext");
    if (menu && !menu.hidden && !menu.contains(e.target)) {
      kontextSchliessen();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") kontextSchliessen();
  });

  // --- Einstellungen ---
  $("knopf-einstellungen").addEventListener("click", einstellungenOeffnen);
  $("knopf-einst-zu").addEventListener("click", einstellungenSchliessen);
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
  $("einst").addEventListener("click", (e) => {
    if (e.target === $("einst")) einstellungenSchliessen();
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
      try {
        await sichereEinstellungen();
      } catch (e) {
        befund.className = "einst-befund schlecht";
        befund.textContent = fehlerText(e);
        return;
      }
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

  $("antwortfeld").addEventListener("input", (e) => {
    z.antwortText = e.target.value;
    zeichne();
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

  $("schalter-zurueck").addEventListener("click", () => {
    z.zurueck = !z.zurueck;
    zeichne();
    if (z.zurueck) $("antwortfeld").focus();
  });

  // ⚠️ Zwei Handlungen an einem Knopf, je nach Richtung. Hin: der maskierte
  // Text wandert in den Anhang und die dritte Spalte klappt auf. Zurueck:
  // die eingefuegte Antwort wird ueber `POST /api/zurueckwandeln` aufgeloest
  // und landet in 05.
  $("knopf-uebernahme").addEventListener("click", async () => {
    if (!z.zurueck) {
      // ⚠️ HIER wandert der maskierte Text hinueber, nirgends sonst.
      z.uebernommen = true;
      document.body.classList.add("drei");
      zeichne();
      springeZu("b03");
      $("prompt").focus();
      return;
    }
    einpflegen(z.antwortText);
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
  // Derselbe Weg wie ueber «Weg zurück» in Spalte 2 — eine Auflösung, zwei
  // Einstiege. Wer die dritte Spalte nicht braucht, arbeitet links.
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
      setTimeout(() => { $(spanne).textContent = t().kopieren; }, 1400);
      return true;
    } catch (e) { return false; }
  }

  $("knopf-kopieren-prompt").addEventListener("click", () => {
    if (z.prompt.trim()) inZwischenablage(z.prompt, "kopieren-prompt-text");
  });
  $("knopf-kopieren-hinaus").addEventListener("click", () => {
    const t2 = ausgehend();
    if (t2.trim()) inZwischenablage(t2, "kopieren-hinaus-text");
  });

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
    // Nicht `inZwischenablage` — die setzt nach 1400 ms auf «Kopieren» zurueck,
    // waehrend dieser Ablauf die volle Beschriftung wiederherstellt. Beide
    // zusammen ergaeben ein Flackern zwischen drei Texten.
    try { await navigator.clipboard.writeText(text); } catch (e) {}
    $("senden-text").textContent = t().kopiertK;
    clearTimeout(z.sendeUhr);
    z.sendeUhr = setTimeout(() => {
      z.sendeUhr = null;
      sendeBeschriftung();
    }, 3000);
    const d = dienstJetzt();
    // EIN Aufruf, kein Rueckfall. `noopener` im Merkmalsstring laesst
    // `window.open` laut Spezifikation `null` zurueckgeben — auch wenn das
    // Fenster aufgeht. Ein `if (!fenster)`-Rueckfall hielte das fuer ein
    // Scheitern und oeffnete ein zweites Mal. Der Rueckgabewert ist hier also
    // nicht auswertbar — und das ist in Ordnung, denn was danach im fremden
    // Fenster passiert, geht uns nichts an.
    //
    // Eigenes Fenster statt Reiter: MASCHERA bleibt sichtbar und wird nicht
    // mitgeschlossen, wenn jemand nur den Reiter schliessen wollte — und beim
    // Schliessen ist das Woerterbuch weg. Die GROESSENANGABEN machen aus dem
    // Reiter ein Fenster, nicht der Fenstername; `noopener` verhindert, dass
    // die geoeffnete Seite auf dieses Fenster zugreift.
    //
    // ⚠️ UNTER macOS UND WINDOWS UEBER DIE ANWENDUNG. Dort tat `window.open`
    // nach dem `await` oben nichts (macOS: die Nutzergeste ist verfallen, und
    // pywebview baut kein Popup). Die Anwendung oeffnet die Adresse im
    // Standardbrowser — mit seinen Anmeldungen —, und nur eine Adresse aus
    // den eigenen Diensten (`fenster.dienst_oeffnen`). Unter Linux bleibt
    // alles, wie es war.
    if (dienstUeberAnwendung()) {
      try { await window.pywebview.api.oeffne_dienst(d.url); } catch (e) {}
    } else {
      window.open(d.url, "_blank", z.eigenesFenster
        ? "noopener,noreferrer,width=1100,height=900"
        : "noopener,noreferrer");
    }
    // Untereinander steht 04 als Naechstes: dort wird die Antwort
    // eingefuegt, wenn der Anwender aus dem Dienst zurueckkommt.
    springeZu("b04");
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
  $("einst-schrift-ueberall").addEventListener("change", (e) => {
    z.schriftUeberall = !!e.target.checked;
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

  $("schalter-vokabular").addEventListener("click", async () => {
    if (z.vokabular && !(await verwerfenOk())) return;
    z.vokabular = !z.vokabular;
    // ⚠️ Beim Ausschalten das Woerterbuch SOFORT wegwerfen, nicht erst beim
    // naechsten Lauf. Wer die Warnung bestaetigt hat, hat den Verlust
    // beschlossen — bliebe die Tabelle stehen, sähe es aus, als waeren die
    // Werte noch da, und man koennte sie sogar noch ablesen. Der maskierte
    // Text bleibt gueltig, nur der Weg zurueck ist zu.
    if (!z.vokabular && z.antwort) {
      z.antwort.woerterbuch = {};
      z.vokabularVerworfen = true;
    }
    if (z.vokabular) z.vokabularVerworfen = false;
    zeichne();
  });

  // ⚠️ Die dritte Spalte startet eingeklappt. Solange nichts hinausgeht,
  // soll die Oberflaeche auch nicht so aussehen, als ginge schon etwas
  // hinaus. Die Schiene bleibt sichtbar, damit klar ist, dass es sie gibt.
  const auf = () => document.body.classList.add("drei");
  $("schiene").addEventListener("click", auf);
  $("knopf-ausklappen").addEventListener("click", auf);
  $("knopf-einklappen").addEventListener("click", (e) => {
    e.stopPropagation();
    document.body.classList.remove("drei");
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

/* Eine Aufloesung, zwei Einstiege: «Weg zurück» in Spalte 2 und der Knopf
 * in Bereich 04. */
async function einpflegen(text) {
  if (!text || !text.trim()) return;
  const w = (z.antwort && z.antwort.woerterbuch) || {};
  try {
    z.final = await zurueckwandeln(text, w);
    zeichne();
    // Das Ende des Weges: untereinander steht 05 zuunterst.
    springeZu("b05");
  } catch (e) {
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
  z.vokabularVerworfen = false;
  z.vokMeldung = null;
  z.prompt = "";
  z.vorlage = null;
  z.antwort04 = "";
  z.antwortText = "";
  z.zurueck = false;
  z.final = null;
  for (const feld of ["orig", "prompt", "antwort04", "antwortfeld"]) {
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
    || (z.antwortText || "").trim()
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
  // ⚠️ Der Schalter muss mit. Stuende er auf «Aus», zeigte die Tabelle
  // Eintraege, die der naechste Lauf mit `"woerterbuch": false` sofort
  // wieder wegwirft — eine Anzeige, die ihrem eigenen Schalter widerspricht.
  z.vokabular = true;
  z.vokabularVerworfen = false;
  return Object.keys(z.antwort.woerterbuch).length;
}

function vokabularEinlesen(datei) {
  const leser = new FileReader();
  leser.onerror = () => meldeVok(t().vokKaputt);
  leser.onload = async () => {
    let o = null;
    try { o = JSON.parse(String(leser.result)); }
    catch (e) { meldeVok(t().vokKaputt); return; }
    const grund = pruefeVokabular(o);
    if (grund) { meldeVok(grund); return; }
    // Erst pruefen, dann fragen: wer eine kaputte Datei erwischt, soll
    // nicht vorher entscheiden muessen, ob er sein Woerterbuch dafuer
    // hergibt.
    if (!(await verwerfenOk())) return;
    const n = uebernimmVokabular(o);
    meldeVok(t().vokGeladen.replace("{}", String(n)));
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
  sans: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
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
  // ⚠️ Nur wenn der Anwender es will. Die Bedienschrift zu wechseln aendert
  // das Erscheinungsbild des Werkzeugs, nicht nur die Lesbarkeit eines
  // Textes — das gehoert an einen eigenen Schalter und nicht an denselben.
  const bedien = z.schriftUeberall ? familie : SCHRIFTEN.werk;
  w.setProperty("--ui-schrift", bedien);
  w.setProperty("--ui-heading",
                z.schriftUeberall && z.schriftart !== "werk"
                  ? familie : "var(--font-heading)");
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
    if (typeof d.schrift_ueberall === "boolean") {
      z.schriftUeberall = d.schrift_ueberall;
    }
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
      for (const k of document.querySelectorAll("[data-sprache]")) {
        k.classList.toggle("aktiv", k.dataset.sprache === z.sprache);
      }
    }
    $("einst-schrift-ueberall").checked = z.schriftUeberall;
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
    schrift_ueberall: z.schriftUeberall,
    sprache: z.sprache,
    tray: z.tray,
    fenstermodus: z.fenstermodus,
    thema: z.thema,
    dienste: z.dienste.map((x) => ({ id: x.id, name: x.name, url: x.url })),
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
    meldeVok(t().einfuegenHinweis);
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
  if (anzahl) meldeVok(s.phEntwertet.replace("{}", String(anzahl)));
  if (ergaenzt.length) {
    meldeVok(s.phErgaenzt.replace("{}", String(ergaenzt.length))
                         .replace("{liste}", ergaenzt.slice(0, 6).join(", ")));
  }
  const reste = entwerteteReste(text);
  if (reste.length) {
    meldeVok(s.phKaputt.replace("{liste}", reste.slice(0, 6).join(", ")));
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
  meldeVok(grund ? s.tplFehler.replace("{}", grund)
                 : s.tplGesichert.replace("{}", name.trim()));
}

async function vorlageLoeschen(name) {
  const s = t();
  if (!(await frage(s.tplWeg.replace("{}", name)))) return;
  const grund = await sichereVorlagen(
    z.vorlagen.filter((v) => v.name !== name));
  if (grund) meldeVok(s.tplFehler.replace("{}", grund));
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
    weg.textContent = "\u2715";
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
  zeichne();
  if (offen) $("vorlagen-filter").focus();
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

async function start() {
  verbinde();
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
    vorlageNehmen, zeichneVorlagen, zeichneDienstmenu, vorlagenAuf,
    zeichneBurger, burgerAuf, imEigenenFenster, finalText,
    SEITEN, seiteZeigen, seiteSchliessen,
    pruefePlatzhalter, zeichneMaskiert, meldeVok, ablagefachMoeglich,
    fehlerText, serverFehler, frage, eingabe, frageZeigen, frageErsetzen,
    markdownZurueck, entwerteteReste, antwortUebernehmen,
    zerschlageneErgaenzen,
    ausgehend, uebernommenerText,
    laufAnzeigen, laufAus, dauerWort, restWort, fortschrittHolen,
    springeZu, vokabularKlappe, gestapelt, einspaltig,
    zeichneBeschriftung,
    zeichne, zeichneFinal,
    messeRollbalken, knopfTitelSetzen,
    allesLeeren, neuOk,
    hinweisText, hinweisSchluessel, I18N,
  };
}

start();
