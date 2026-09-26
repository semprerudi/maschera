/* HILFE UND IMPRESSUM — EINE QUELLE.
 *
 * Eine eigene Datei aus zwei Gruenden:
 *
 * 1. Der Text soll an einer Stelle gepflegt werden. Jede Kopie driftet,
 *    sobald jemand den Hilfetext korrigiert.
 *
 * 2. Das Impressum traegt den Namen des Entwicklers, und
 *    `test_veroeffentlichung.py` weist Personennamen zurueck. Die Ausnahme
 *    dafuer schluesselt auf (Datei, gefundener Text) — in `maschera.js`
 *    waere sie fuer Tausende Zeilen gueltig und die Wache dort blind. Hier
 *    traegt sie eine kleine Datei mit genau diesem Zweck.
 *
 * Sie wird VOR `maschera.js` geladen und legt ihren Inhalt an `globalThis`
 * ab — das ist im Browser und unter node dasselbe. Ein `export` waere im
 * Browser ein Modul und damit ein anderer Ladeweg.
 *
 * Der Aufbau ist Daten und kein HTML: `["h", …]`, `["p", …]`,
 * `["ul", […]]`, `["tab", [[links, rechts], …]]`. Gebaut wird daraus mit
 * `document.createElement` — `innerHTML` kommt nicht vor.
 *
 * FETT IST EIN STUECK, KEIN ZEICHEN IM TEXT. Statt einer Zeichenkette darf
 * der Inhalt eine LISTE aus Stuecken sein; ein Stueck ist entweder eine
 * Zeichenkette oder `["b", "…"]`. Eine Auszeichnung IM Text (`**so**`)
 * haette einen Zerleger gebraucht, und der naechste Schritt waere
 * `innerHTML` gewesen.
 */
const HILFE_DE = [
  ["p", "MASCHERA ersetzt Personendaten in einem Text durch Platzhalter, "
      + "damit du ihn einem KI-Werkzeug geben kannst, ohne die Daten "
      + "preiszugeben. Aus «Andrea Brülhart» wird «[FULLNAME_1]». Die "
      + "Antwort setzt MASCHERA anschliessend wieder zurück."],

  ["h", "Warum nichts hinausgeht"],
  ["p", "Die Erkennung läuft vollständig auf diesem Gerät. Im Betrieb "
      + "wird nichts nachgeladen und nichts gesendet — auch keine "
      + "Schriften, keine Symbole und keine Statistik. Ohne "
      + "Netzverbindung funktioniert alles ausser dem Öffnen des "
      + "KI-Dienstes."],
  ["p", "Je nach Paket liegt das Modell schon darin, oder es wird einmal "
      + "beim ersten Start geholt — aus einer benannten Quelle, mit "
      + "Prüfsumme, und erst nachdem du zugestimmt hast. Du kannst auch "
      + "ablehnen und es später tun. Danach ist es hier und bleibt hier."],
  ["p", ["Es gibt in MASCHERA keinen Endpunkt, der Text verschickt, und es "
       + "wird auch keinen geben. Der Weg nach draussen führt immer über "
       + "deine Zwischenablage: du kopierst, du fügst ein. Damit bleibt "
       + "sichtbar, was hinausgeht — Bereich ", ["b", "03 Prompt"],
         " zeigt genau den Text, der zum Dienst gelangt, und zählt seine "
       + "Zeichen."]],
  ["p", "Geschrieben wird nur, was du ausdrücklich speicherst: deine "
      + "Regeln, Vorlagen, Vorlieben und Einstellungen. Kein "
      + "Dokumentinhalt, kein Wörterbuch, kein Protokoll."],

  ["h", "Der Weg durch das Fenster"],
  ["tab", [
    ["01 Originaltext",
     ["Text einfügen, tippen oder eine Datei hineinziehen — txt, md, csv, "
    + "json, eml, msg, mbox, pdf, docx. Dann ", ["b", "Maskieren"], ". "
    + "Höchstens {mb} MB je Datei; die Dauer hängt an der Textlänge und "
    + "nicht an der Dateigrösse — rund 100 Seiten (300 000 Zeichen) "
    + "brauchen etwa eine Minute."]],
    ["02 Maskiert",
     ["Das Ergebnis. Jeder Platzhalter ist farbig; ein Rechtsklick darauf "
    + "ändert oder entfernt ihn. Ein Rechtsklick auf gewöhnlichen Text "
    + "maskiert ihn nachträglich. ", ["b", "Bearbeiten"],
      " öffnet den Text zum Korrigieren von Hand — die Platzhalter dabei "
    + "stehen lassen."]],
    ["03 Prompt",
     ["Deine Frage an das KI-Werkzeug. Darunter steht, was wirklich "
    + "hinausgeht. Der rote Rand bedeutet: ab hier verlässt es das Gerät. ",
      ["b", "Kopieren"], " legt beides in die Zwischenablage und öffnet "
    + "den gewählten Dienst."]],
  ]],

  // ⚠️ Der Bruch zwischen 03 und 04 ist der einzige Moment,
  // in dem der Anwender das Werkzeug verlaesst.
  ["rot", "Ab hier arbeitest du selbst online. Nimm den Prompt zum KI-Dienst, arbeite dort, bis das Ergebnis stimmt — und komm mit der Antwort hierher zurück."],

  ["tab", [
    ["04 Antwort", "Die Antwort des Dienstes hier einfügen."],
    ["05 Finaler Text",
     [["b", "Vokabular einpflegen"], " setzt deine echten Daten wieder ein "
    + "— über das Wörterbuch."]],
  ]],

  ["h", "Das Wörterbuch"],
  ["p", ["Es hält fest, welcher Platzhalter für welchen Wert steht, und "
       + "liegt nur im Browserfenster. Wer es verliert, kann den Text nie "
       + "mehr zurückwandeln — deshalb der Knopf ", ["b", "Herunterladen"],
         ". Die Datei enthält die echten Werte im Klartext: sie gehört an "
       + "einen Ort, an den auch das Original gehört."]],

  ["h", "Übermaskierung ist kein Fehler"],
  ["p", "MASCHERA maskiert im Zweifel zu viel. Ein Ortsname, der wie ein "
      + "Nachname aussieht, wird ersetzt. Das ist Absicht: ein zu viel "
      + "ersetztes Wort kostet dich einen Handgriff, ein übersehenes "
      + "kostet die Daten einer Person."],
  ["p", "Umgekehrt ist ein leerer Befund keine Entwarnung. Ein "
      + "eingescanntes PDF ohne Textebene wird abgewiesen statt "
      + "«sauber» gemeldet — dort ist nichts zu erkennen, nicht nichts "
      + "zu finden."],

  ["h", "Eigene Regeln"],
  ["p", ["Dossiernummern, Fallnummern, interne Projektnamen: was nur bei "
       + "dir vorkommt, kennt kein Modell. Unter ",
         ["b", "Einstellungen → Eigene Regeln"],
         " trägst du es als YAML ein. Die Schlüssel sind englisch, "
       + "damit dieselbe Datei in jeder Bediensprache funktioniert; "
       + "die Werte bleiben in der Sprache deiner Dokumente."]],

  ["h", "Pseudonymisierung, nicht Anonymisierung"],
  ["p", ["Über das Wörterbuch ist jede Maskierung umkehrbar — genau das "
       + "macht das Werkzeug brauchbar. Deshalb heisst der Knopf ",
         ["b", "Maskieren"], ". Ein maskierter Text ist kein anonymer "
       + "Text: solange das Wörterbuch existiert, ist der Bezug zur "
       + "Person herstellbar."]],
  ["h", "⚠ Entwicklungsfassung — bitte nachsehen"],
  ["p", ["MASCHERA ist noch nicht fertig, und das Modell ist es nie: es "
       + "kann Personendaten ", ["b", "übersehen"], ". Sieh dir den "
       + "maskierten Text an, ", ["b", "bevor"], " du ihn hinausgibst — "
       + "das ist der einzige Handgriff, den dir kein Werkzeug abnimmt."]],
  ["p", ["Das Werkzeug ist offene Software. Wer einen Fehler findet oder "
       + "etwas beitragen möchte: der Quelltext steht im Menü unter ",
         ["b", "Quellcode auf GitHub"], "."]],
];

const HILFE_FR = [
  ["p", "MASCHERA remplace les données personnelles d’un texte par des "
      + "marqueurs, pour que tu puisses le confier à un outil IA sans "
      + "livrer ces données. « Andrea Brülhart » devient « [FULLNAME_1] ». "
      + "MASCHERA rétablit ensuite la réponse."],

  ["h", "Pourquoi rien ne sort"],
  ["p", "La détection se fait entièrement sur cet appareil. En "
      + "fonctionnement, rien n’est téléchargé et rien n’est envoyé — ni "
      + "polices, ni icônes, ni statistiques. Sans connexion réseau, tout "
      + "fonctionne, sauf l’ouverture du service IA."],
  ["p", "Selon le paquet, le modèle y est déjà, ou il est récupéré une "
      + "seule fois au premier démarrage — d’une source nommée, avec une "
      + "somme de contrôle, et seulement après ton accord. Tu peux aussi "
      + "refuser et le faire plus tard. Ensuite il reste ici."],
  ["p", ["MASCHERA n’a aucun point d’accès qui expédie du texte, et il n’y "
       + "en aura pas. La sortie passe toujours par ton presse-papiers : "
       + "tu copies, tu colles. Ce qui sort reste ainsi visible — la zone ",
         ["b", "03 Prompt"], " montre exactement le texte qui parvient au "
       + "service et en compte les caractères."]],
  ["p", "N’est écrit que ce que tu enregistres expressément : tes règles, "
      + "tes modèles, tes préférences et tes réglages. Aucun contenu de "
      + "document, aucun vocabulaire, aucun journal."],

  ["h", "Le parcours dans la fenêtre"],
  ["tab", [
    ["01 Texte original",
     ["Coller du texte, l’écrire ou y glisser un fichier — txt, md, csv, "
    + "json, eml, msg, mbox, pdf, docx. Puis ", ["b", "Masquer"], ". "
    + "Au plus {mb} Mo par fichier ; la durée dépend de la longueur du "
    + "texte et non de la taille du fichier — environ 100 pages "
    + "(300 000 caractères) prennent à peu près une minute."]],
    ["02 Masqué",
     ["Le résultat. Chaque marqueur est coloré ; un clic droit dessus le "
    + "modifie ou le retire. Un clic droit sur du texte ordinaire le "
    + "masque après coup. ", ["b", "Modifier"],
      " ouvre le texte à la correction manuelle — en laissant les "
    + "marqueurs en place."]],
    ["03 Prompt",
     ["Ta question à l’outil IA. En dessous s’affiche ce qui sort "
    + "réellement. Le liseré rouge signifie : à partir d’ici, cela quitte "
    + "l’appareil. ", ["b", "Copier"], " met le tout dans le "
    + "presse-papiers et ouvre le service choisi."]],
  ]],

  // ⚠️ Der Bruch zwischen 03 und 04 ist der einzige Moment,
  // in dem der Anwender das Werkzeug verlaesst.
  ["rot", "À partir d’ici, tu travailles toi-même en ligne. Emporte le prompt vers le service d’IA, travaille là-bas jusqu’à ce que le résultat te convienne — puis reviens ici avec la réponse."],

  ["tab", [
    ["04 Réponse", "Coller ici la réponse du service."],
    ["05 Texte final",
     [["b", "Appliquer le vocabulaire"], " remet tes données réelles en "
    + "place — via le vocabulaire."]],
  ]],

  ["h", "Le vocabulaire"],
  ["p", ["Il retient quel marqueur correspond à quelle valeur et ne vit "
       + "que dans la fenêtre du navigateur. Qui le perd ne pourra plus "
       + "jamais rétablir le texte — d’où le bouton ",
         ["b", "Télécharger"], ". Le fichier contient les valeurs réelles "
       + "en clair : sa place est là où se trouve aussi l’original."]],

  ["h", "Trop masquer n’est pas une erreur"],
  ["p", "Dans le doute, MASCHERA masque trop. Un nom de lieu qui ressemble "
      + "à un nom de famille sera remplacé. C’est voulu : un mot remplacé "
      + "en trop te coûte un geste, un mot oublié coûte les données d’une "
      + "personne."],
  ["p", "À l’inverse, un résultat vide n’est pas un feu vert. Un PDF "
      + "scanné sans couche de texte est refusé au lieu d’être déclaré "
      + "« propre » — là, il n’y a rien à reconnaître, et non rien à "
      + "trouver."],

  ["h", "Règles personnelles"],
  ["p", ["Numéros de dossier, numéros d’affaire, noms de projets internes : "
       + "ce qui n’existe que chez toi, aucun modèle ne le connaît. Sous ",
         ["b", "Réglages → Règles personnelles"],
         " tu les saisis en YAML. Les clés sont en anglais, pour que le "
       + "même fichier fonctionne dans toutes les langues d’interface ; les "
       + "valeurs restent dans la langue de tes documents."]],

  ["h", "Pseudonymisation, pas anonymisation"],
  ["p", ["Via le vocabulaire, chaque masquage est réversible — et c’est "
       + "précisément ce qui rend l’outil utilisable. D’où le bouton ",
         ["b", "Masquer"], ". Un texte masqué n’est pas un texte anonyme : "
       + "tant que le vocabulaire existe, le lien avec la personne peut "
       + "être rétabli."]],
  ["h", "⚠ Version de développement — vérifiez"],
  ["p", ["MASCHERA n’est pas terminé, et le modèle ne le sera jamais : il "
       + "peut ", ["b", "passer à côté"], " de données personnelles. "
       + "Relisez le texte masqué ", ["b", "avant"], " de le transmettre — "
       + "c’est le seul geste qu’aucun outil ne fera à ta place."]],
  ["p", ["L’outil est un logiciel libre. Qui trouve une erreur ou veut "
       + "contribuer : le code source est au menu sous ",
         ["b", "Code source sur GitHub"], "."]],
];

const HILFE_IT = [
  ["p", "MASCHERA sostituisce i dati personali di un testo con segnaposto, "
      + "così puoi darlo a uno strumento IA senza rivelarli. Da «Andrea "
      + "Brülhart» diventa «[FULLNAME_1]». La risposta viene poi "
      + "ripristinata da MASCHERA."],

  ["h", "Perché non esce nulla"],
  ["p", "Il riconoscimento avviene interamente su questo dispositivo. "
      + "Durante l’uso non viene scaricato né inviato nulla — nemmeno "
      + "caratteri, icone o statistiche. Senza connessione di rete "
      + "funziona tutto, tranne l’apertura del servizio IA."],
  ["p", "A seconda del pacchetto il modello è già incluso, oppure viene "
      + "scaricato una sola volta al primo avvio — da una fonte indicata, "
      + "con somma di controllo, e solo dopo il tuo consenso. Puoi anche "
      + "rifiutare e farlo più tardi. Dopodiché resta qui."],
  ["p", ["In MASCHERA non esiste alcun endpoint che spedisca testo, e non "
       + "ci sarà. La via verso l’esterno passa sempre dagli appunti: tu "
       + "copi, tu incolli. Così resta visibile ciò che esce — l’area ",
         ["b", "03 Prompt"], " mostra esattamente il testo che raggiunge "
       + "il servizio e ne conta i caratteri."]],
  ["p", "Viene scritto solo ciò che salvi espressamente: le tue regole, i "
      + "modelli, le preferenze e le impostazioni. Nessun contenuto di "
      + "documento, nessun vocabolario, nessun registro."],

  ["h", "Il percorso nella finestra"],
  ["tab", [
    ["01 Testo originale",
     ["Incollare il testo, scriverlo o trascinarvi un file — txt, md, csv, "
    + "json, eml, msg, mbox, pdf, docx. Poi ", ["b", "Maschera"], ". "
    + "Al massimo {mb} MB per file; la durata dipende dalla lunghezza "
    + "del testo e non dalla dimensione del file — circa 100 pagine "
    + "(300 000 caratteri) richiedono circa un minuto."]],
    ["02 Mascherato",
     ["Il risultato. Ogni segnaposto è colorato; un clic destro lo cambia "
    + "o lo rimuove. Un clic destro su testo normale lo maschera a "
    + "posteriori. ", ["b", "Modifica"],
      " apre il testo alla correzione a mano — lasciando i segnaposto al "
    + "loro posto."]],
    ["03 Prompt",
     ["La tua domanda allo strumento IA. Sotto si vede ciò che esce "
    + "davvero. Il bordo rosso significa: da qui in poi lascia il "
    + "dispositivo. ", ["b", "Copia"], " mette tutto negli appunti e apre "
    + "il servizio scelto."]],
  ]],

  // ⚠️ Der Bruch zwischen 03 und 04 ist der einzige Moment,
  // in dem der Anwender das Werkzeug verlaesst.
  ["rot", "Da qui in poi lavori tu stesso online. Porta il prompt al servizio di IA, lavora lì finché il risultato non ti soddisfa — poi torna qui con la risposta."],

  ["tab", [
    ["04 Risposta", "Incollare qui la risposta del servizio."],
    ["05 Testo finale",
     [["b", "Applica il vocabolario"], " reinserisce i tuoi dati reali — "
    + "tramite il vocabolario."]],
  ]],

  ["h", "Il vocabolario"],
  ["p", ["Tiene nota di quale segnaposto sta per quale valore e vive solo "
       + "nella finestra del browser. Chi lo perde non potrà mai più "
       + "ripristinare il testo — per questo il pulsante ",
         ["b", "Scarica"], ". Il file contiene i valori reali in chiaro: "
       + "va tenuto dove sta anche l’originale."]],

  ["h", "Mascherare troppo non è un errore"],
  ["p", "Nel dubbio MASCHERA maschera troppo. Un nome di località che "
      + "sembra un cognome viene sostituito. È voluto: una parola "
      + "sostituita di troppo ti costa un gesto, una parola sfuggita "
      + "costa i dati di una persona."],
  ["p", "Al contrario, un esito vuoto non è un via libera. Un PDF "
      + "scansionato senza livello di testo viene respinto invece di "
      + "essere dichiarato «pulito» — lì non c’è nulla da riconoscere, "
      + "non nulla da trovare."],

  ["h", "Regole proprie"],
  ["p", ["Numeri di dossier, numeri di pratica, nomi di progetti interni: "
       + "ciò che esiste solo da te, nessun modello lo conosce. In ",
         ["b", "Impostazioni → Regole proprie"],
         " li inserisci come YAML. Le chiavi sono in inglese, così lo "
       + "stesso file funziona in tutte le lingue dell’interfaccia; i "
       + "valori restano nella lingua dei tuoi documenti."]],

  ["h", "Pseudonimizzazione, non anonimizzazione"],
  ["p", ["Tramite il vocabolario ogni mascheratura è reversibile — ed è "
       + "proprio questo a rendere utile lo strumento. Per questo il "
       + "pulsante si chiama ", ["b", "Maschera"], ". Un testo mascherato "
       + "non è un testo anonimo: finché il vocabolario esiste, il legame "
       + "con la persona è ricostruibile."]],
  ["h", "⚠ Versione in sviluppo — controlla"],
  ["p", ["MASCHERA non è finito, e il modello non lo sarà mai: può ",
         ["b", "non riconoscere"], " dati personali. Rileggi il testo "
       + "mascherato ", ["b", "prima"], " di consegnarlo — è l’unico gesto "
       + "che nessuno strumento può fare al posto tuo."]],
  ["p", ["Lo strumento è software libero. Chi trova un errore o vuole "
       + "contribuire: il codice sorgente è nel menu sotto ",
         ["b", "Codice sorgente su GitHub"], "."]],
];

const HILFE_EN = [
  ["p", "MASCHERA replaces personal data in a text with placeholders so "
      + "you can hand it to an AI tool without giving the data away. "
      + "«Andrea Brülhart» becomes «[FULLNAME_1]». MASCHERA then restores "
      + "the answer."],

  ["h", "Why nothing goes out"],
  ["p", "Detection runs entirely on this device. In operation nothing "
      + "is fetched and nothing is sent — no fonts, no icons, no "
      + "statistics. Without a network connection everything works except "
      + "opening the AI service."],
  ["p", "Depending on the package the model is already inside, or it is "
      + "fetched once on first start — from a named source, with a "
      + "checksum, and only after you agree. You can also decline and do "
      + "it another time. After that it stays here."],
  ["p", ["MASCHERA has no endpoint that sends text, and there will not be "
       + "one. The way out always goes through your clipboard: you copy, "
       + "you paste. What leaves stays visible that way — area ",
         ["b", "03 Prompt"], " shows exactly the text that reaches the "
       + "service, and counts its characters."]],
  ["p", "Only what you explicitly save is written: your rules, templates, "
      + "preferences and settings. No document content, no vocabulary, no "
      + "log."],

  ["h", "The way through the window"],
  ["tab", [
    ["01 Original text",
     ["Paste text, type it, or drag a file in — txt, md, csv, json, eml, "
    + "msg, mbox, pdf, docx. Then ", ["b", "Mask"], ". "
    + "At most {mb} MB per file; how long it takes depends on the text "
    + "length, not the file size — about 100 pages (300,000 characters) "
    + "take roughly a minute."]],
    ["02 Masked",
     ["The result. Every placeholder is coloured; a right-click changes or "
    + "removes it. A right-click on ordinary text masks it after the fact. ",
      ["b", "Edit"], " opens the text for correction by hand — leave the "
    + "placeholders in place."]],
    ["03 Prompt",
     ["Your question to the AI tool. Below it stands what actually goes "
    + "out. The red border means: from here on it leaves the device. ",
      ["b", "Copy"], " puts both on the clipboard and opens the chosen "
    + "service."]],
  ]],

  // ⚠️ Der Bruch zwischen 03 und 04 ist der einzige Moment,
  // in dem der Anwender das Werkzeug verlaesst.
  ["rot", "From here you work online yourself. Take the prompt to the AI service, work there until the result is right — then come back here with the answer."],

  ["tab", [
    ["04 Answer", "Paste the service’s answer here."],
    ["05 Final text",
     [["b", "Apply vocabulary"], " puts your real data back in — through "
    + "the vocabulary."]],
  ]],

  ["h", "The vocabulary"],
  ["p", ["It records which placeholder stands for which value, and lives "
       + "only in the browser window. Whoever loses it can never restore "
       + "the text — hence the ", ["b", "Download"], " button. The file "
       + "holds the real values in the clear: it belongs where the "
       + "original belongs."]],

  ["h", "Over-masking is not a fault"],
  ["p", "When in doubt MASCHERA masks too much. A place name that looks "
      + "like a surname gets replaced. That is deliberate: one word "
      + "replaced too many costs you a moment, one word missed costs a "
      + "person’s data."],
  ["p", "Conversely, an empty finding is not an all-clear. A scanned PDF "
      + "without a text layer is refused rather than reported «clean» — "
      + "there is nothing to recognise there, not nothing to find."],

  ["h", "Own rules"],
  ["p", ["File numbers, case numbers, internal project names: what occurs "
       + "only at your place, no model knows. Under ",
         ["b", "Settings → Own rules"],
         " you enter them as YAML. The keys are English so the same file "
       + "works in every interface language; the values stay in the "
       + "language of your documents."]],

  ["h", "Pseudonymisation, not anonymisation"],
  ["p", ["Through the vocabulary every masking is reversible — which is "
       + "exactly what makes the tool usable. Hence the button is called ",
         ["b", "Mask"], ". A masked text is not an anonymous text: as long "
       + "as the vocabulary exists, the link to the person can be "
       + "restored."]],
  ["h", "⚠ Development version — please check"],
  ["p", ["MASCHERA is not finished, and the model never will be: it can ",
         ["b", "miss"], " personal data. Read the masked text ",
         ["b", "before"], " you pass it on — that is the one step no tool "
       + "can take for you."]],
  ["p", ["The tool is open software. If you find a fault or want to "
       + "contribute: the source code is in the menu under ",
         ["b", "Source code on GitHub"], "."]],
];

/* Das Impressum nennt nur den Namen — keine Adresse, keine Mail.
 * Erreichbar ist der Entwickler ueber den Quelltextverweis im Menue.
 *
 * `test_veroeffentlichung.py` fuehrt die Ausnahme fuer den Namen in
 * `ZEILEN_AUSNAHMEN`, gueltig fuer DIESE Datei.
 */
const IMPRESSUM_DE = [
  ["h", "Verantwortlich für dieses Werkzeug"],
  ["tab", [
    ["Name", "Rodolfo Semprevivo"],
    ["Land", "Schweiz"],
    ["Web", "www.maschera.ch"],
  ]],

  ["h", "Zweck"],
  ["p", "MASCHERA ist ein Werkzeug zur lokalen Maskierung von "
      + "Personendaten in Schweizer Dokumenten. Es wird als offene "
      + "Software bereitgestellt."],

  ["h", "Datenbearbeitung"],
  ["p", "MASCHERA bearbeitet deine Dokumente ausschliesslich auf deinem "
      + "eigenen Gerät. Es werden keine Inhalte an den Herausgeber oder "
      + "an Dritte übermittelt, keine Nutzungsdaten erhoben und keine "
      + "Cookies gesetzt. Der Herausgeber erhält dadurch keine Kenntnis "
      + "von den bearbeiteten Daten und ist für sie nicht "
      + "Verantwortlicher im Sinne des DSG."],
  ["p", "Verantwortlich für die Daten bleibst du. Sobald du einen "
      + "maskierten Text in ein KI-Werkzeug einfügst, gelten die "
      + "Bedingungen jenes Anbieters."],

  ["h", "Haftung"],
  ["p", "MASCHERA wird ohne Gewähr bereitgestellt. Die Erkennung von "
      + "Personendaten erfolgt maschinell und ist nicht vollständig: sie "
      + "kann Angaben übersehen und maskiert im Zweifel zu viel. Die "
      + "Prüfung des maskierten Textes vor der Weitergabe liegt bei "
      + "dir. Eine Haftung für Schäden aus der Verwendung ist im "
      + "gesetzlich zulässigen Rahmen ausgeschlossen."],

  ["h", "Lizenz und Quelltext"],
  ["p", "Der Quelltext ist einsehbar; die Adresse steht im Menü unter "
      + "«GitHub». Verwendete Werke Dritter sind dort mit ihren Lizenzen "
      + "aufgeführt."],
];

const IMPRESSUM_FR = [
  ["h", "Responsable de cet outil"],
  ["tab", [
    ["Nom", "Rodolfo Semprevivo"],
    ["Pays", "Suisse"],
    ["Web", "www.maschera.ch"],
  ]],

  ["h", "But"],
  ["p", "MASCHERA est un outil de masquage local de données personnelles "
      + "dans des documents suisses. Il est mis à disposition en tant que "
      + "logiciel ouvert."],

  ["h", "Traitement des données"],
  ["p", "MASCHERA traite tes documents exclusivement sur ton propre "
      + "appareil. Aucun contenu n’est transmis à l’éditeur ou à des "
      + "tiers, aucune donnée d’utilisation n’est collectée et aucun "
      + "cookie n’est déposé. L’éditeur n’a de ce fait aucune "
      + "connaissance des données traitées et n’en est pas responsable au "
      + "sens de la LPD."],
  ["p", "La responsabilité des données t’incombe. Dès que tu colles "
      + "un texte masqué dans un outil IA, les conditions de ce "
      + "fournisseur s’appliquent."],

  ["h", "Responsabilité"],
  ["p", "MASCHERA est fourni sans garantie. La reconnaissance des données "
      + "personnelles est automatique et n’est pas exhaustive : elle peut "
      + "omettre des indications et masque trop en cas de doute. La "
      + "vérification du texte masqué avant transmission t’incombe. "
      + "Toute responsabilité pour des dommages résultant de "
      + "l’utilisation est exclue dans les limites légales."],

  ["h", "Licence et code source"],
  ["p", "Le code source est consultable ; l’adresse figure au menu sous "
      + "« GitHub ». Les œuvres de tiers utilisées y sont listées avec "
      + "leurs licences."],
];

const IMPRESSUM_IT = [
  ["h", "Responsabile di questo strumento"],
  ["tab", [
    ["Nome", "Rodolfo Semprevivo"],
    ["Paese", "Svizzera"],
    ["Web", "www.maschera.ch"],
  ]],

  ["h", "Scopo"],
  ["p", "MASCHERA è uno strumento per la mascheratura locale di dati "
      + "personali in documenti svizzeri. È messo a disposizione come "
      + "software aperto."],

  ["h", "Trattamento dei dati"],
  ["p", "MASCHERA elabora i tuoi documenti esclusivamente sul tuo "
      + "dispositivo. Nessun contenuto viene trasmesso all’editore o a "
      + "terzi, non vengono raccolti dati d’uso e non vengono impostati "
      + "cookie. L’editore non ha quindi conoscenza dei dati trattati e "
      + "non ne è responsabile ai sensi della LPD."],
  ["p", "La responsabilità dei dati resta tua. Non appena incolli un "
      + "testo mascherato in uno strumento IA, valgono le condizioni di "
      + "quel fornitore."],

  ["h", "Responsabilità"],
  ["p", "MASCHERA è fornito senza garanzia. Il riconoscimento dei dati "
      + "personali è automatico e non è completo: può tralasciare "
      + "indicazioni e nel dubbio maschera troppo. La verifica del testo "
      + "mascherato prima della trasmissione spetta a te. Ogni "
      + "responsabilità per danni derivanti dall’uso è esclusa nei limiti "
      + "di legge."],

  ["h", "Licenza e codice sorgente"],
  ["p", "Il codice sorgente è consultabile; l’indirizzo si trova nel menu "
      + "sotto «GitHub». Le opere di terzi utilizzate vi sono elencate con "
      + "le rispettive licenze."],
];

const IMPRESSUM_EN = [
  ["h", "Responsible for this tool"],
  ["tab", [
    ["Name", "Rodolfo Semprevivo"],
    ["Country", "Switzerland"],
    ["Web", "www.maschera.ch"],
  ]],

  ["h", "Purpose"],
  ["p", "MASCHERA is a tool for masking personal data locally in Swiss "
      + "documents. It is provided as open software."],

  ["h", "Data processing"],
  ["p", "MASCHERA processes your documents exclusively on your own "
      + "device. No content is transmitted to the publisher or to third "
      + "parties, no usage data is collected and no cookies are set. The "
      + "publisher therefore gains no knowledge of the processed data and "
      + "is not its controller within the meaning of the FADP."],
  ["p", "Responsibility for the data remains yours. As soon as you paste "
      + "a masked text into an AI tool, that provider’s terms apply."],

  ["h", "Liability"],
  ["p", "MASCHERA is provided without warranty. Personal data is detected "
      + "automatically and not exhaustively: it can miss details and masks "
      + "too much when in doubt. Checking the masked text before passing "
      + "it on is up to you. Liability for damages arising from use is "
      + "excluded to the extent permitted by law."],

  ["h", "Licence and source code"],
  ["p", "The source code is open to inspection; the address is in the menu "
      + "under «GitHub». Third-party works used are listed there with "
      + "their licences."],
];

/* Acht Listen: Hilfe und Impressum in je vier Sprachen. Die Pruefung
 * verlangt, dass jede Sprache einen eigenen, nicht leeren Text hat.
 */
globalThis.MASCHERA_SEITEN = {
  hilfe: { de: HILFE_DE, fr: HILFE_FR, it: HILFE_IT, en: HILFE_EN },
  impressum: { de: IMPRESSUM_DE, fr: IMPRESSUM_FR,
               it: IMPRESSUM_IT, en: IMPRESSUM_EN },
};
