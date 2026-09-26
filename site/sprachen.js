/* MASCHERA — sprachen.js
   Sprachumschalter. Kein Gerüst, nichts von aussen.
   Die deutsche Fassung steht im HTML; hier stehen alle vier. */

(function () {
  "use strict";

  var T = {
    de: {},

    fr: {
      "nav.merkmale": "Caractéristiques",
      "nav.ablauf": "Déroulement",
      "nav.pruefen": "Contrôle",
      "nav.download": "Télécharger",
      "hero.kicker": "Logiciel libre · Open Source · fonctionne sans réseau",
      "hero.titel": "MASCHERA masque les données personnelles dans les documents suisses — sur ton appareil, sans connexion réseau en fonctionnement.",
      "hero.lead": "Tu as une lettre, un fil de courriels ou un PDF et tu veux interroger un outil d’IA à son sujet — mais les noms, numéros AVS et adresses ne doivent pas partir avec.",
      "hero.knopf1": "Télécharger",
      "hero.knopf2": "Comment ça marche",
      "bsp.vorher": "Avant",
      "bsp.nachher": "Après",
      "bsp.unten": "Tu transmets le texte masqué au service de ton choix. Tu recolles la réponse, et MASCHERA rétablit les valeurs réelles.",
      "bild.platzhalter": "Emplacement réservé",
      "bild.gross": "Capture de l’application avec le texte masqué et les occurrences en couleur",
      "bild.schritt": "Capture",
      "bild.herkunft": "Une occurrence et son origine",
      "merkmale.kicker": "Quatre caractéristiques",
      "merkmale.titel": "Ce qui fait cet outil",
      "m1.titel": "Il fonctionne sur ton appareil",
      "m1.text": "Toute la détection est locale. En fonctionnement, <strong>rien</strong> n’est téléchargé et <strong>rien</strong> n’est envoyé — ni polices, ni icônes, ni statistiques. Un point de terminaison qui expédierait du texte n’existe pas et n’existera pas ; la sortie passe toujours par ton presse-papiers.",
      "m2.titel": "Il n’écrit rien",
      "m2.text": "Seuls tes propres réglages sont enregistrés — règles, modèles de texte, préférences — et uniquement sur ordre explicite. Aucun contenu de document, aucun dictionnaire, aucun journal.",
      "m3.titel": "Réversible, et c’est le but",
      "m3.text": "Tu masques, tu interroges, tu recolles la réponse : MASCHERA rétablit les valeurs réelles. C’est pourquoi on parle de <strong>pseudonymisation</strong> et non d’anonymisation — tant que le dictionnaire existe, l’opération est réversible et les données restent des données personnelles au sens de la nLPD.",
      "m4.titel": "Conçu pour les documents suisses",
      "m4.text": "Numéro AVS, IDE, IBAN, référence QR, identificateurs de bâtiment et de logement, catégorie de permis, plaque de contrôle, numéro RCC — avec les sommes de contrôle qui vont avec. <strong>45 types de données</strong> au total. Quatre langues : allemand, français, italien et anglais.",
      "ablauf.kicker": "Le déroulement",
      "ablauf.titel": "Cinq étapes",
      "s1.titel": "Ouvrir ou glisser un document, ou coller du texte",
      "s1.text": "Formats lus : .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Masquer",
      "s2.text": "Chaque occurrence est affichée en couleur, avec son origine — somme de contrôle, motif ou modèle.",
      "s3.titel": "Vérifier",
      "s3.text": "Tu vois ce qui a été remplacé, avant que le texte n’aille où que ce soit.",
      "s4.titel": "Copier et coller",
      "s4.text": "Dans le service de ton choix, à la main. L’outil n’envoie rien de lui-même.",
      "s5.titel": "Recoller la réponse",
      "s5.text": "Les valeurs réelles reviennent.",
      "ablauf.leer": "<strong>Un résultat vide n’est pas un feu vert.</strong> Un PDF numérisé sans couche de texte produit une erreur motivée, et non « aucune donnée personnelle trouvée ». Un outil qui rassure dans ce cas est plus dangereux qu’un outil qui se tait.",
      "stufen.titel": "Trois niveaux — ce n’est pas seulement « une IA »",
      "stufen.th1": "Niveau",
      "stufen.th2": "Ce qu’il fait",
      "stufen.1t": "1 · Sommes de contrôle",
      "stufen.1b": "Numéro AVS, IDE, IBAN, référence QR, carte de crédit, GLN. Somme valide → masquer, même si le modèle se tait. Somme invalide → écarter, même s’il se déclenche.",
      "stufen.2t": "2 · Motifs avec ancre de contexte",
      "stufen.2b": "Numéro de téléphone, code postal, plaque de contrôle, catégorie de permis, numéro de dossier et d’autres — mots d’ancrage en quatre langues, sans priorité sur le modèle. S’y ajoutent tes propres règles : des mots et des motifs que tu définis toi-même. Elles fonctionnent comme les motifs intégrés. Par exemple un n° de cas interne ou un n° de dossier interne.",
      "stufen.3t": "3 · Modèle de langue",
      "stufen.3b": "Noms, adresses, professions, organisations, dates — tout ce qui n’a pas de motif.",
      "stufen.modell": "Le modèle pèse <strong>1,2 Go</strong> et a été entraîné sur des données <strong>synthétiques</strong> — il n’a jamais vu un document réel. <a href=\"#verweise\">Informations techniques sur le modèle</a>.",
      "pruefen.kicker": "La section la plus importante",
      "pruefen.satz": "MASCHERA t’enlève le travail, pas la responsabilité.",
      "pruefen.text": "Aucun outil ne trouve toutes les données personnelles. Relis le texte masqué avant de le transmettre — c’est pour cela que MASCHERA affiche chaque occurrence en couleur et avec son origine.",
      "herkunft.titel": "Ce que veut dire « origine »",
      "herkunft.text": "Chaque occurrence indique d’où elle vient : d’un numéro vérifié, d’un motif avec contexte, ou du modèle de langue. Un numéro AVS dont la somme de contrôle est valide est sûrement bien reconnu ; une supposition du modèle mérite un second regard.",
      "moegl.titel": "Ce que tu peux faire s’il manque quelque chose",
      "moegl.lead": "Cinq possibilités, toutes présentes dans l’application.",
      "mo1t": "Corriger à la main",
      "mo1b": "Le texte masqué est modifiable. Les marqueurs comme <code>[FULLNAME_1]</code> restent en place — ils seront reconvertis à la fin.",
      "mo2t": "Règles personnelles",
      "mo2b": "Tes propres mots et motifs, masqués en plus. Un nom de projet, une abréviation interne, un surnom.",
      "mo3t": "Types en clair",
      "mo3b": "Laisser durablement certains types en clair — reconnus, mais non remplacés. Qui veut garder les localités le règle une fois pour toutes.",
      "mo4t": "Reconvertir",
      "mo4b": "Coller la réponse du service, et les valeurs réelles reviennent.",
      "mo5t": "Anonymiser définitivement",
      "mo5b": "Masquer sans dictionnaire. L’opération n’est alors <strong>plus réversible</strong> — et l’application le dit à l’avance.",
      "moegl.beides": "<strong>MASCHERA sait faire les deux :</strong> réversible pour travailler avec un service d’IA, irréversible pour un texte qui quitte la maison tel quel.",
      "dl.kicker": "Télécharger",
      "dl.titel": "Quel fichier choisir ?",
      "dl.lead": "Pas de formulaire d’inscription, pas d’adresse courriel demandée, pas d’infolettre. Le fichier est là, on le télécharge, c’est tout.",
      "dl.linux": "AppImage : un seul fichier exécutable, le modèle est embarqué. Télécharger, rendre exécutable, terminé.",
      "dl.mac": "N’existe pas encore. Le travail est en cours — d’ici là, il n’y a pas de fichier pour macOS.",
      "dl.win": "Programme d’installation pour Windows 11, 64 bits. S’installe sans droits d’administrateur, le modèle est embarqué. Au premier démarrage, Windows avertit parce que le programme n’est pas signé : « Informations complémentaires » → « Exécuter quand même ».",
      "dl.arbeit": "En cours",
      "dl.nochnicht": "Pas encore disponible",
      "dl.serverTitel": "Serveur",
      "dl.server": "Docker, pour un fonctionnement en tant que service — l’interface s’ouvre dans le navigateur. Le modèle est embarqué. Le serveur ne conserve rien : aucun document, aucun dictionnaire, aucun journal — après la réponse, tout est oublié.",
      "dl.modellTitel": "À propos du modèle",
      "dl.modell": "Le modèle pèse 1,2 Go. L’AppImage l’embarque. Les paquets légers le récupèrent <strong>une fois au premier démarrage</strong> — depuis une source nommée, avec somme de contrôle, et seulement après ton accord. Sans wifi sous la main, tu refuses et tu le récupères une autre fois. Ensuite, les deux fonctionnent hors ligne de la même manière.",
      "dl.archTitel": "AppImage ou Flatpak ?",
      "dl.arch1": "AppImage est un seul fichier : télécharger, rendre exécutable, lancer — rien n’est installé. Flatpak s’intègre à la gestion de paquets et se met à jour avec elle.",
      "dl.arch2": "Les deux embarquent leurs propres bibliothèques et sont donc indépendants de la version de ta distribution. Sur les systèmes Arch, Flatpak fonctionne parfaitement ; c’est pourquoi il n’y a pas de paquet Arch séparé.",
      "verweise.kicker": "Où se trouve tout le reste",
      "verweise.titel": "La technique est tenue à jour là-bas",
      "verweise.lead": "La qualité de mesure du modèle, son entraînement, la construction du programme — tout cela se trouve là-bas et y est tenu à jour.",
      "v1t": "Code source et versions",
      "v1b": "Comment c’est construit, quelle version du programme fonctionne avec quel modèle, tous les contrôles.",
      "v2t": "Le modèle",
      "v2b": "La qualité du modèle, son entraînement, les types de données qu’il connaît.",
      "v3t": "Signaler une erreur",
      "v3b": "Ce qui n’a pas été reconnu, ce qui a été mal remplacé, ce qui manque.",
      "fuss.name": "<em>maschera</em> veut dire masque en italien — et porte l’indicatif de pays CH en son milieu.",
      "fuss.lizenz": "Code source MIT · paquets AGPL-3.0",
      "fuss.impressum": "Mentions légales",
      "impressum.verantwortlich": "Responsable :",
      "impressum.kontakt": "Contact via GitHub Issues"
    },

    it: {
      "nav.merkmale": "Caratteristiche",
      "nav.ablauf": "Procedura",
      "nav.pruefen": "Controllo",
      "nav.download": "Scaricare",
      "hero.kicker": "Software libero · Open Source · funziona senza rete",
      "hero.titel": "MASCHERA maschera i dati personali nei documenti svizzeri — sul tuo dispositivo, in esercizio senza connessione di rete.",
      "hero.lead": "Hai una lettera, uno scambio di e-mail o un PDF e vuoi interrogarci uno strumento di IA — ma nomi, numeri AVS e indirizzi non devono partire con esso.",
      "hero.knopf1": "Scaricare",
      "hero.knopf2": "Come funziona",
      "bsp.vorher": "Prima",
      "bsp.nachher": "Dopo",
      "bsp.unten": "Il testo mascherato lo consegni al servizio che preferisci. La risposta la incolli indietro, e MASCHERA reinserisce i valori reali.",
      "bild.platzhalter": "Segnaposto",
      "bild.gross": "Schermata dell’applicazione con testo mascherato e occorrenze colorate",
      "bild.schritt": "Schermata",
      "bild.herkunft": "Un’occorrenza con la sua provenienza",
      "merkmale.kicker": "Quattro caratteristiche",
      "merkmale.titel": "Che cosa distingue lo strumento",
      "m1.titel": "Funziona sul tuo dispositivo",
      "m1.text": "Tutto il riconoscimento avviene in locale. In esercizio <strong>nulla</strong> viene scaricato e <strong>nulla</strong> viene inviato — né caratteri, né icone, né statistiche. Un endpoint che spedisca testo non esiste e non esisterà; la via verso l’esterno passa sempre dagli appunti.",
      "m2.titel": "Non annota nulla",
      "m2.text": "Vengono salvate solo le tue impostazioni — regole, modelli, preferenze — e anche quelle solo su comando esplicito. Nessun contenuto di documento, nessun dizionario, nessun registro.",
      "m3.titel": "Reversibile, ed è questo il senso",
      "m3.text": "Maschera, chiedi e incolli indietro la risposta: MASCHERA reinserisce i valori reali. Per questo si chiama <strong>pseudonimizzazione</strong> e non anonimizzazione — finché il dizionario esiste il procedimento è reversibile, e i dati restano dati personali ai sensi della revLPD.",
      "m4.titel": "Costruito per documenti svizzeri",
      "m4.text": "Numero AVS, IDI, IBAN, riferimento QR, identificatore di edificio e abitazione, categoria di licenza, targa, numero RCC — con le cifre di controllo che vi appartengono. <strong>45 tipi di dati</strong> in totale. Quattro lingue: tedesco, francese, italiano e inglese.",
      "ablauf.kicker": "La procedura",
      "ablauf.titel": "Cinque passi",
      "s1.titel": "Aprire o trascinare un documento, oppure incollare del testo",
      "s1.text": "Vengono letti .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Mascherare",
      "s2.text": "Ogni occorrenza è mostrata a colori, con la sua provenienza — cifra di controllo, schema o modello.",
      "s3.titel": "Verificare",
      "s3.text": "Vedi che cosa è stato sostituito, prima che il testo vada da qualche parte.",
      "s4.titel": "Copiare e incollare",
      "s4.text": "Nel servizio che preferisci, a mano. Lo strumento non spedisce nulla da sé.",
      "s5.titel": "Incollare indietro la risposta",
      "s5.text": "I valori reali ritornano.",
      "ablauf.leer": "<strong>Un esito vuoto non è un via libera.</strong> Un PDF scansionato senza livello di testo produce un errore motivato, non «nessun dato personale trovato». Uno strumento che lì rassicura è più pericoloso di uno che tace del tutto.",
      "stufen.titel": "Tre livelli — non è soltanto «un’IA»",
      "stufen.th1": "Livello",
      "stufen.th2": "Che cosa fa",
      "stufen.1t": "1 · Cifre di controllo",
      "stufen.1b": "Numero AVS, IDI, IBAN, riferimento QR, carta di credito, GLN. Cifra valida → mascherare, anche se il modello tace. Non valida → scartare, anche se il modello segnala.",
      "stufen.2t": "2 · Schemi con àncora di contesto",
      "stufen.2b": "Numero di telefono, NPA, targa, categoria di licenza, numero di pratica e altri — parole d’àncora in quattro lingue, senza precedenza sul modello. Si aggiungono le tue regole personali: parole e schemi che definisci tu. Funzionano come gli schemi integrati. Per esempio un n. di caso interno o un n. di dossier interno.",
      "stufen.3t": "3 · Modello linguistico",
      "stufen.3b": "Nomi, indirizzi, professioni, organizzazioni, date — tutto ciò che non ha uno schema.",
      "stufen.modell": "Il modello è grande <strong>1,2 GB</strong> ed è stato addestrato su dati <strong>sintetici</strong> — non ha mai visto un documento reale. <a href=\"#verweise\">Indicazioni tecniche sul modello</a>.",
      "pruefen.kicker": "La sezione più importante",
      "pruefen.satz": "MASCHERA ti toglie il lavoro, non la responsabilità.",
      "pruefen.text": "Nessuno strumento trova ogni dato personale. Guarda il testo mascherato prima di trasmetterlo — per questo MASCHERA mostra ogni occorrenza a colori e con la sua provenienza.",
      "herkunft.titel": "Che cosa significa «provenienza»",
      "herkunft.text": "Ogni occorrenza mostra da dove viene: da un numero verificato, da uno schema con contesto, o dal modello linguistico. Un numero AVS con cifra di controllo valida è riconosciuto con certezza, una supposizione del modello merita una seconda occhiata.",
      "moegl.titel": "Che cosa puoi fare se manca qualcosa",
      "moegl.lead": "Cinque possibilità, tutte presenti nell’applicazione.",
      "mo1t": "Correggere a mano",
      "mo1b": "Il testo mascherato è modificabile. I segnaposto come <code>[FULLNAME_1]</code> restano — alla fine vengono riconvertiti.",
      "mo2t": "Regole proprie",
      "mo2b": "Parole e schemi tuoi, mascherati in aggiunta. Il nome di un progetto, una sigla interna, un soprannome.",
      "mo3t": "Tipi in chiaro",
      "mo3b": "Lasciare stabilmente singoli tipi in chiaro — riconosciuti, ma non sostituiti. Chi vuole conservare le località lo imposta una volta.",
      "mo4t": "Riconvertire",
      "mo4b": "Incolli la risposta del servizio, e i valori reali ritornano.",
      "mo5t": "Anonimizzare definitivamente",
      "mo5b": "Mascherare senza dizionario. Allora il procedimento <strong>non è più reversibile</strong> — e l’applicazione lo dice prima.",
      "moegl.beides": "<strong>MASCHERA sa fare entrambe le cose:</strong> reversibile per lavorare con un servizio di IA, irreversibile per un testo che esce di casa così com’è.",
      "dl.kicker": "Scaricare",
      "dl.titel": "Quale file prendo?",
      "dl.lead": "Nessun modulo di registrazione, nessuna richiesta di e-mail, nessuna newsletter. Il file è lì, lo si scarica, fine.",
      "dl.linux": "AppImage: un unico file eseguibile, il modello viaggia con esso. Scaricare, rendere eseguibile, fatto.",
      "dl.mac": "Non esiste ancora. Ci si sta lavorando — fino ad allora non c’è un file per macOS.",
      "dl.win": "Programma d’installazione per Windows 11, 64 bit. Si installa senza diritti di amministratore, il modello viaggia con esso. Al primo avvio Windows avverte perché il programma non è firmato: «Ulteriori informazioni» → «Esegui comunque».",
      "dl.arbeit": "In lavorazione",
      "dl.nochnicht": "Non ancora disponibile",
      "dl.serverTitel": "Server",
      "dl.server": "Docker, per l’esercizio come servizio — l’interfaccia si apre nel browser. Il modello viaggia con esso. Il server non conserva nulla: nessun documento, nessun dizionario, nessun registro — dopo la risposta tutto è dimenticato.",
      "dl.modellTitel": "L’avvertenza sul modello",
      "dl.modell": "Il modello è grande 1,2 GB. L’AppImage lo porta con sé. I pacchetti leggeri lo scaricano <strong>una volta al primo avvio</strong> — da una fonte indicata, con cifra di controllo, e solo dopo il tuo consenso. Chi in quel momento non ha il wifi rifiuta e lo scarica un’altra volta. Dopodiché entrambi sono ugualmente offline.",
      "dl.archTitel": "AppImage o Flatpak?",
      "dl.arch1": "AppImage è un unico file: scaricare, rendere eseguibile, avviare — non viene installato nulla. Flatpak si integra nella gestione dei pacchetti e si aggiorna con essa.",
      "dl.arch2": "Entrambi portano con sé le proprie librerie e sono quindi indipendenti dalla versione della tua distribuzione. Sui sistemi Arch, Flatpak funziona benissimo; per questo non esiste un pacchetto Arch a parte.",
      "verweise.kicker": "Dove si trova tutto il resto",
      "verweise.titel": "La parte tecnica è tenuta aggiornata lì",
      "verweise.lead": "Quanto bene misura il modello, come è stato addestrato, come è costruito il programma — sta lì e lì viene tenuto aggiornato.",
      "v1t": "Codice sorgente e versioni",
      "v1b": "Come è costruito, quale versione del programma lavora con quale modello, tutte le verifiche.",
      "v2t": "Il modello",
      "v2b": "Quanto è buono il modello, come è stato addestrato, quali tipi di dati conosce.",
      "v3t": "Segnalare un errore",
      "v3b": "Che cosa non è stato riconosciuto, che cosa è stato sostituito male, che cosa manca.",
      "fuss.name": "<em>MASCHERA</em> non ha bisogno di spiegazioni — e porta la sigla nazionale CH nel mezzo.",
      "fuss.lizenz": "Codice sorgente MIT · pacchetti AGPL-3.0",
      "fuss.impressum": "Colophon",
      "impressum.verantwortlich": "Responsabile:",
      "impressum.kontakt": "Contatto tramite GitHub Issues"
    },

    en: {
      "nav.merkmale": "Features",
      "nav.ablauf": "How it works",
      "nav.pruefen": "Review",
      "nav.download": "Download",
      "hero.kicker": "Free software · Open Source · runs without a network",
      "hero.titel": "MASCHERA masks personal data in Swiss documents — on your own device, offline while it runs.",
      "hero.lead": "You have a letter, an email thread or a PDF and want to ask an AI tool about it — but the names, AHV numbers and addresses should stay behind.",
      "hero.knopf1": "Download",
      "hero.knopf2": "How it works",
      "bsp.vorher": "Before",
      "bsp.nachher": "After",
      "bsp.unten": "You hand the masked text to the service of your choice. You paste the answer back, and MASCHERA puts the real values in again.",
      "bild.platzhalter": "Placeholder",
      "bild.gross": "Screenshot of the application with masked text and coloured findings",
      "bild.schritt": "Screenshot",
      "bild.herkunft": "One finding with its origin",
      "merkmale.kicker": "Four features",
      "merkmale.titel": "What defines the tool",
      "m1.titel": "It runs on your device",
      "m1.text": "All detection happens locally. While it runs, <strong>nothing</strong> is fetched and <strong>nothing</strong> is sent — no fonts, no icons, no analytics. An endpoint that ships text out does not exist and will not exist; the way out always leads through your clipboard.",
      "m2.titel": "It writes nothing down",
      "m2.text": "Only your own settings are stored — rules, templates, preferences — and even those only on explicit command. No document content, no dictionary, no log.",
      "m3.titel": "Reversible, and that is the point",
      "m3.text": "You mask, you ask, you paste the answer back: MASCHERA puts the real values in again. That is why this is <strong>pseudonymisation</strong> and not anonymisation — as long as the dictionary exists the process is reversible, and under the revised FADP the data remain personal data.",
      "m4.titel": "Built for Swiss documents",
      "m4.text": "AHV number, UID, IBAN, QR reference, building and dwelling identifier, licence category, number plate, ZSR number — with the checksums that belong to them. <strong>45 data types</strong> in all. Four languages: German, French, Italian and English.",
      "ablauf.kicker": "The process",
      "ablauf.titel": "Five steps",
      "s1.titel": "Open or drag in a document, or paste text",
      "s1.text": "Read: .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Mask",
      "s2.text": "Every finding is shown in colour, with its origin — checksum, pattern or model.",
      "s3.titel": "Check",
      "s3.text": "You see what was replaced before the text goes anywhere.",
      "s4.titel": "Copy and paste",
      "s4.text": "Into the service of your choice, by hand. The tool sends nothing itself.",
      "s5.titel": "Paste the answer back",
      "s5.text": "The real values come back in.",
      "ablauf.leer": "<strong>An empty result is not an all-clear.</strong> A scanned PDF without a text layer yields an error with a reason, not “no personal data found”. A tool that gives the all-clear there is more dangerous than one that says nothing at all.",
      "stufen.titel": "Three stages — it is not just “an AI”",
      "stufen.th1": "Stage",
      "stufen.th2": "What it does",
      "stufen.1t": "1 · Checksums",
      "stufen.1b": "AHV number, UID, IBAN, QR reference, credit card, GLN. Valid checksum → mask, even if the model stays silent. Invalid → discard, even if it fires.",
      "stufen.2t": "2 · Patterns with context anchors",
      "stufen.2b": "Phone number, postcode, number plate, licence category, case number and more — anchor words in four languages, no precedence over the model. Your own rules come on top: words and patterns you define yourself. They run like the built-in patterns. For example an internal case no. or an internal file no.",
      "stufen.3t": "3 · Language model",
      "stufen.3b": "Names, addresses, occupations, organisations, dates — everything without a pattern.",
      "stufen.modell": "The model is <strong>1.2 GB</strong> and was trained on <strong>synthetic</strong> data — it has never seen a real document. <a href=\"#verweise\">Technical details on the model</a>.",
      "pruefen.kicker": "The most important section",
      "pruefen.satz": "MASCHERA takes the work off your hands, not the responsibility.",
      "pruefen.text": "No tool finds every piece of personal data. Look at the masked text before you pass it on — that is why MASCHERA shows every finding in colour and with its origin.",
      "herkunft.titel": "What “origin” means",
      "herkunft.text": "Every finding shows where it came from: a verified number, a pattern with context, or the language model. An AHV number with a valid checksum is certainly right; a guess from the model deserves a second look.",
      "moegl.titel": "What you can do if something is missing",
      "moegl.lead": "Five options, all present in the application.",
      "mo1t": "Fix it by hand",
      "mo1b": "The masked text is editable. Placeholders such as <code>[FULLNAME_1]</code> stay put — they are converted back at the end.",
      "mo2t": "Your own rules",
      "mo2b": "Your own words and patterns, masked in addition. A project name, an internal abbreviation, a nickname.",
      "mo3t": "Plain-text types",
      "mo3b": "Leave individual data types in plain text for good — detected, but not replaced. If you want to keep place names, you set that once.",
      "mo4t": "Convert back",
      "mo4b": "Paste the service’s answer in, and the real values come back.",
      "mo5t": "Anonymise for good",
      "mo5b": "Mask without a dictionary. The process is then <strong>no longer reversible</strong> — and the application says so beforehand.",
      "moegl.beides": "<strong>MASCHERA can do both:</strong> reversible for working with an AI service, irreversible for text that leaves the house as it is.",
      "dl.kicker": "Download",
      "dl.titel": "Which file do I take?",
      "dl.lead": "No sign-up form, no email address, no newsletter. The file is there, you download it, done.",
      "dl.linux": "AppImage: a single executable file, the model travels with it. Download, make executable, done.",
      "dl.mac": "Does not exist yet. Work is under way — until then there is no file for macOS.",
      "dl.win": "Installer for Windows 11, 64-bit. Installs without administrator rights, the model travels with it. On first start Windows warns because the installer is not signed: “More info” → “Run anyway”.",
      "dl.arbeit": "In progress",
      "dl.nochnicht": "Not available yet",
      "dl.serverTitel": "Server",
      "dl.server": "Docker, for running as a service — the interface opens in the browser. The model travels with it. The server keeps nothing: no document, no dictionary, no log — once the answer is out, everything is forgotten.",
      "dl.modellTitel": "The note about the model",
      "dl.modell": "The model is 1.2 GB. The AppImage carries it. The slim packages fetch it <strong>once on first start</strong> — from a named source, with a checksum, and only after you have agreed. If you have no wifi right now, decline and fetch it another time. After that both are equally offline.",
      "dl.archTitel": "AppImage or Flatpak?",
      "dl.arch1": "AppImage is a single file: download it, make it executable, start it — nothing is installed. Flatpak integrates with the package manager and updates along with it.",
      "dl.arch2": "Both bring their own libraries and are therefore independent of your distribution’s release. On Arch systems Flatpak runs perfectly well, which is why there is no separate Arch package.",
      "verweise.kicker": "Where everything else lives",
      "verweise.titel": "The technical part is kept up to date there",
      "verweise.lead": "How well the model measures, how it was trained, how the program is built — that lives there and is kept current there.",
      "v1t": "Source code and versions",
      "v1b": "How it is built, which program version works with which model, all the checks.",
      "v2t": "The model",
      "v2b": "How good the model is, how it was trained, which data types it knows.",
      "v3t": "Report a bug",
      "v3b": "What was not detected, what was replaced wrongly, what is missing.",
      "fuss.name": "<em>maschera</em> is Italian for mask — and carries the country code CH in the middle.",
      "fuss.lizenz": "Source code MIT · packages AGPL-3.0",
      "fuss.impressum": "Legal notice",
      "impressum.verantwortlich": "Responsible:",
      "impressum.kontakt": "Contact via GitHub Issues"
    }
  };

  var titel = {
    de: "MASCHERA — Personendaten maskieren, auf deinem Gerät",
    fr: "MASCHERA — masquer les données personnelles, sur ton appareil",
    it: "MASCHERA — mascherare i dati personali, sul tuo dispositivo",
    en: "MASCHERA — mask personal data, on your own device"
  };

  // Die deutsche Fassung aus dem HTML lesen, damit sie nicht doppelt gepflegt wird.
  function deutschEinlesen() {
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      if (!(k in T.de)) T.de[k] = el.textContent;
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-html");
      if (!(k in T.de)) T.de[k] = el.innerHTML;
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      var teile = el.getAttribute("data-i18n-attr").split(":");
      if (!(teile[1] in T.de)) T.de[teile[1]] = el.getAttribute(teile[0]) || "";
    });
  }

  function setzen(sprache) {
    var w = T[sprache] || T.de;
    document.documentElement.lang = sprache;
    document.title = titel[sprache] || titel.de;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var t = w[el.getAttribute("data-i18n")];
      if (t != null) el.textContent = t;
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      var t = w[el.getAttribute("data-i18n-html")];
      if (t != null) el.innerHTML = t;
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      var teile = el.getAttribute("data-i18n-attr").split(":");
      var t = w[teile[1]];
      if (t != null) el.setAttribute(teile[0], t);
    });
    document.querySelectorAll("[data-sprache]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-sprache") === sprache ? "true" : "false");
    });
    try { localStorage.setItem("maschera.sprache", sprache); } catch (e) {}
  }

  function startsprache() {
    var gespeichert = null;
    try { gespeichert = localStorage.getItem("maschera.sprache"); } catch (e) {}
    if (gespeichert && T[gespeichert]) return gespeichert;
    var liste = navigator.languages || [navigator.language || "de"];
    for (var i = 0; i < liste.length; i++) {
      var k = String(liste[i]).slice(0, 2).toLowerCase();
      if (T[k]) return k;
    }
    return "de";
  }

  deutschEinlesen();
  setzen(startsprache());

  document.querySelectorAll("[data-sprache]").forEach(function (b) {
    b.addEventListener("click", function () { setzen(b.getAttribute("data-sprache")); });
  });
})();
