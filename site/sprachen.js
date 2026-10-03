/* MASCHERA — sprachen.js
   Sprachumschalter und Linux-Teilknopf. Kein Gerüst, nichts von aussen.
   Die deutsche Fassung steht im HTML; hier stehen alle vier. */

(function () {
  "use strict";

  var T = {
    de: {},

    fr: {
      "nav.merkmale": "Caractéristiques",
      "nav.ablauf": "Déroulement",
      "nav.pruefen": "Contrôle",
      "thema.label": "Basculer clair/sombre",
      "nav.download": "Télécharger",
      "hero.kicker": "Logiciel libre · Open Source · fonctionne sans réseau",
      "hero.titel": "MASCHERA masque les données personnelles<br>dans les documents suisses<span style=\"display:block; font-size:0.75em; line-height:1.3; margin-top:0.3em\">Cela se fait sur ton appareil, toujours en local,<br>sans connexion réseau !</span>",
      "hero.lead": "Tu as une lettre, un fil de courriels ou un PDF et tu veux interroger un outil d’IA à son sujet. Les noms, numéros AVS et adresses ne doivent toutefois pas partir avec.",
      "hero.knopf1": "Télécharger",
      "hero.knopf2": "Comment ça marche",
      "bsp.vorher": "Avant",
      "bsp.nachher": "Après",
      "bsp.unten": "Tu transmets le texte masqué au service de ton choix. Tu recolles la réponse, et MASCHERA rétablit les valeurs réelles.",
      "bild.platzhalter": "Emplacement réservé",
      "bild.gross": "Capture de l’application avec le texte masqué et les occurrences en couleur · 1600 × 1000",
      "bild.schritt": "Capture · 800 × 600",
      "bild.herkunft": "Une occurrence et son origine · 1200 × 675",
      "merkmale.kicker": "Quatre caractéristiques",
      "merkmale.titel": "Ce qui fait cet outil",
      "m1.titel": "Il fonctionne sur ton appareil",
      "m1.text": "Toute la détection est locale. En fonctionnement, <strong>rien</strong> n’est téléchargé et <strong>rien</strong> n’est envoyé : ni polices, ni icônes, ni statistiques. Un point de terminaison qui expédierait du texte n’existe pas et n’existera pas. La sortie passe toujours par ton presse-papiers.",
      "m2.titel": "Il n’écrit rien",
      "m2.text": "Seuls tes propres réglages sont enregistrés, c’est-à-dire les règles, modèles de texte et préférences. Eux aussi ne le sont que sur ordre explicite. Aucun contenu de document, aucun dictionnaire, aucun journal.",
      "m3.titel": "Réversible, et c’est le but",
      "m3.text": "Tu masques, tu interroges, tu recolles la réponse : MASCHERA rétablit les valeurs réelles. C’est pourquoi on parle de <strong>pseudonymisation</strong> et non d’anonymisation. Tant que le dictionnaire existe, l’opération est réversible et les données restent des données personnelles au sens de la nLPD.",
      "m4.titel": "Conçu pour les documents suisses",
      "m4.text": "Sont reconnus le numéro AVS, l’IDE, l’IBAN, la référence QR, les identificateurs de bâtiment et de logement, la catégorie de permis, la plaque de contrôle et le numéro RCC, chacun avec sa somme de contrôle. <strong><br>45 types de données</strong> au total. Quatre langues : allemand, français, italien et anglais.",
      "ablauf.kicker": "Le déroulement",
      "ablauf.titel": "Cinq étapes",
      "s1.titel": "Ouvrir ou glisser un document, ou coller du texte",
      "s1.text": "Formats lus : .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Masquer",
      "s2.text": "Chaque occurrence est affichée en couleur, avec son origine : somme de contrôle, motif ou modèle.",
      "s3.titel": "Vérifier",
      "s3.text": "Tu vois ce qui a été remplacé, avant que le texte n’aille où que ce soit.",
      "s4.titel": "Copier et coller",
      "s4.text": "Dans le service de ton choix, à la main. L’outil n’envoie rien de lui-même.",
      "s5.titel": "Recoller la réponse",
      "s5.text": "Les valeurs réelles reviennent.",
      "ablauf.leer": "<strong>Un résultat vide n’est pas un feu vert.</strong> Un PDF numérisé sans couche de texte produit une erreur motivée, et non « aucune donnée personnelle trouvée ». Un outil qui rassure dans ce cas est plus dangereux qu’un outil qui se tait.",
      "stufen.titel": "Trois niveaux, pas seulement « une IA »",
      "stufen.th1": "Niveau",
      "stufen.th2": "Ce qu’il fait",
      "stufen.1t": "1 · Sommes de contrôle",
      "stufen.1b": "Numéro AVS, IDE, IBAN, référence QR, carte de crédit, GLN. Somme valide → masquer, même si le modèle se tait. Somme invalide → écarter, même s’il se déclenche.",
      "stufen.2t": "2 · Motifs avec ancre de contexte",
      "stufen.2b": "Numéro de téléphone, code postal, plaque de contrôle, catégorie de permis, numéro de dossier et d’autres. Ils sont reconnus grâce à des mots d’ancrage en quatre langues et n’ont pas la priorité sur le modèle. S’y ajoutent tes propres règles : des mots et des motifs que tu définis toi-même. Elles fonctionnent comme les motifs intégrés. Par exemple un n° de cas interne ou un n° de dossier interne.",
      "stufen.3t": "3 · Modèle de langue",
      "stufen.3b": "Noms, adresses, professions, organisations et dates, donc tout ce qui n’a pas de motif.",
      "stufen.modell": "Le modèle pèse <strong>1,2 Go</strong> et a été entraîné sur des données <strong>synthétiques</strong>. Il n’a jamais vu un document réel. <a href=\"#verweise\">Informations techniques sur le modèle</a>.",
      "pruefen.kicker": "La section la plus importante",
      "pruefen.satz": "MASCHERA t’enlève le travail, pas la responsabilité.",
      "pruefen.text": "Aucun outil ne trouve toutes les données personnelles. Relis le texte masqué avant de le transmettre. C’est pour cela que MASCHERA affiche chaque occurrence en couleur et avec son origine.",
      "herkunft.titel": "Ce que veut dire « origine »",
      "herkunft.text": "Chaque occurrence indique d’où elle vient : d’un numéro vérifié, d’un motif avec contexte, ou du modèle de langue. Un numéro AVS dont la somme de contrôle est valide est sûrement bien reconnu ; une supposition du modèle mérite un second regard.",
      "herkunft.menu": "Un clic droit sur une occurrence te permet de modifier le marquage : tu choisis un autre type de données ou tu retires le masque.",
      "moegl.titel": "Ce que tu peux faire s’il manque quelque chose",
      "moegl.lead": "Cinq possibilités, toutes présentes dans l’application.",
      "mo1t": "Corriger à la main",
      "mo1b": "Le texte masqué est modifiable. Les marqueurs comme <code>[FULLNAME_1]</code> restent en place et seront reconvertis à la fin.",
      "mo2t": "Règles personnelles",
      "mo2b": "Tes propres mots et motifs, masqués en plus. Un nom de projet, une abréviation interne, un surnom.",
      "mo3t": "Types en clair",
      "mo3b": "Tu peux laisser durablement certains types en clair. Ils sont reconnus, mais pas remplacés. Qui veut garder les localités le règle une fois pour toutes.",
      "mo4t": "Reconvertir",
      "mo4b": "Coller la réponse du service, et les valeurs réelles reviennent.",
      "mo5t": "Anonymiser définitivement",
      "mo5b": "Masquer sans dictionnaire. L’opération n’est alors <strong>plus réversible</strong>, et l’application te prévient à l’avance.",
      "moegl.beides": "<strong>MASCHERA sait faire les deux :</strong> réversible pour travailler avec un service d’IA, irréversible pour un texte qui quitte la maison tel quel.",
      "dl.kicker": "Télécharger",
      "dl.titel": "Quel fichier choisir ?",
      "dl.lead": "Pas de formulaire d’inscription, pas d’adresse courriel demandée, pas d’infolettre. Le fichier est là, on le télécharge, c’est tout.",
      "dl.linux": "<b>AppImage :</b> un seul fichier exécutable, le modèle est inclus. Télécharger, rendre exécutable et lancer. Rien n’est installé.",
      "dl.mac": "Image disque pour les Mac à puce Apple (M1 ou plus récent). Le modèle est inclus. L’app n’est pas signée : après l’avoir glissée dans « Applications », saisis une fois dans le « Terminal » <code>xattr -dr com.apple.quarantine /Applications/MASCHERA.app</code>, sinon elle ne s’ouvre pas.",
      "dl.win": "Installateur pour Windows 11, 64 bits. S’installe sans droits d’administrateur, le modèle est inclus.",
      "dl.flatpakHinweis": "<b>Flatpak :</b> Le modèle (1,3 Go) est téléchargé depuis Hugging Face au premier démarrage de l’application.",
      "dl.serverTitel": "Serveur",
      "dl.server": "Docker, pour un fonctionnement en tant que service. L’interface s’ouvre dans le navigateur. Le modèle est inclus. Le serveur ne conserve rien : aucun document, aucun dictionnaire, aucun journal. Après la réponse, tout est oublié.",
      "dl.platzhalterHinweis": "Tous les fichiers se trouvent dans les <a href=\"https://github.com/semprerudi/maschera/releases/latest\" rel=\"noopener noreferrer\">publications sur GitHub</a>, avec <code>SHA256SUMS</code> pour la vérification.",
      "dl.modellTitel": "À propos du modèle",
      "dl.modell": "Le modèle pèse 1,2 Go. L’AppImage, l’installateur Windows et l’image macOS l’embarquent. Le Flatpak le récupère <strong>une fois au premier démarrage</strong>. Il vient d’une source nommée, est vérifié par une somme de contrôle et n’est chargé qu’après ton accord. Sans wifi sous la main, tu refuses et tu le récupères une autre fois. Ensuite, tout fonctionne hors ligne de la même façon.",
      "dl.archTitel": "AppImage ou Flatpak ?",
      "dl.arch1": "AppImage est un seul fichier : télécharger, rendre exécutable et lancer. Rien n’est installé. Flatpak s’intègre à la gestion de paquets et se met à jour avec elle.",
      "dl.arch2": "Les deux embarquent leurs propres bibliothèques et sont donc indépendants de la version de ta distribution. Sur les systèmes Arch, Flatpak fonctionne parfaitement ; c’est pourquoi il n’y a pas de paquet Arch séparé.",
      "verweise.kicker": "Où se trouve tout le reste",
      "verweise.titel": "La technique est tenue à jour là-bas",
      "verweise.lead": "La qualité de mesure du modèle, son entraînement, la construction du programme : tout cela se trouve là-bas et y est tenu à jour.",
      "v1t": "Code source et versions",
      "v1b": "Comment c’est construit, quelle version du programme fonctionne avec quel modèle, tous les contrôles.",
      "v2t": "Le modèle",
      "v2b": "La qualité du modèle, son entraînement, les types de données qu’il connaît.",
      "v3t": "Signaler une erreur",
      "v3b": "Ce qui n’a pas été reconnu, ce qui a été mal remplacé, ce qui manque.",
      "imp.titel": "Mentions légales",
      "imp.verantw": "Responsable",
      "imp.name": "Nom",
      "imp.land": "Pays",
      "imp.landWert": "Suisse",
      "imp.kontakt": "Contact",
      "imp.web": "Web",
      "imp.kontaktWert": "via <a href=\"https://github.com/semprerudi/maschera/issues\" rel=\"noopener noreferrer\">GitHub Issues</a>",
      "imp.zweckT": "But",
      "imp.zweck": "MASCHERA est un outil de masquage local de données personnelles dans des documents suisses. Il est mis à disposition en tant que logiciel ouvert.",
      "imp.siteT": "Ce site",
      "imp.site": "Ce site est servi par GitHub Pages (GitHub, Inc., États-Unis). Lors de la consultation, GitHub traite des données techniquement nécessaires, comme l’adresse IP, dans ses journaux de serveur ; les détails figurent dans la déclaration de confidentialité de GitHub. Le site lui-même ne dépose aucun cookie, ne collecte aucune statistique et ne charge rien depuis des serveurs tiers. Les fichiers à télécharger se trouvent également chez GitHub.",
      "imp.appT": "L’application",
      "imp.app": "MASCHERA traite tes documents exclusivement sur ton propre appareil. Aucun contenu n’est transmis à l’éditeur ou à des tiers, aucune donnée d’utilisation n’est collectée et aucun cookie n’est déposé. L’éditeur n’a de ce fait aucune connaissance des données traitées et n’en est pas responsable au sens de la LPD. La responsabilité des données t’incombe. Dès que tu colles un texte masqué dans un outil IA, les conditions de ce fournisseur s’appliquent.",
      "imp.haftT": "Responsabilité",
      "imp.haft": "MASCHERA est fourni sans garantie. La reconnaissance des données personnelles est automatique et n’est pas exhaustive : elle peut omettre des indications et masque trop en cas de doute. La vérification du texte masqué avant transmission t’incombe. Toute responsabilité pour des dommages résultant de l’utilisation est exclue dans les limites légales. Les exploitants des sites liés sont responsables de leurs contenus.",
      "imp.lizT": "Licence",
      "imp.liz": "Code source MIT, paquets livrés AGPL-3.0, modèle MIT. Le code source et les œuvres de tiers utilisées, avec leurs licences, se trouvent sur <a href=\"https://github.com/semprerudi/maschera\" rel=\"noopener noreferrer\">GitHub</a>.",
      "fuss.impressum": "Mentions légales",
      "fuss.name": "<em>maschera</em> veut dire masque en italien et porte l’indicatif de pays CH en son milieu.",
      "fuss.lizenz": "Licence MIT"
    },

    it: {
      "nav.merkmale": "Caratteristiche",
      "nav.ablauf": "Procedura",
      "nav.pruefen": "Controllo",
      "thema.label": "Alternare chiaro/scuro",
      "nav.download": "Scaricare",
      "hero.kicker": "Software libero · Open Source · funziona senza rete",
      "hero.titel": "MASCHERA maschera i dati personali nei documenti svizzeri<span style=\"display:block; font-size:0.75em; line-height:1.3; margin-top:0.3em\">Lo fa sul tuo dispositivo, sempre in locale,<br>senza connessione di rete!</span>",
      "hero.lead": "Hai una lettera, uno scambio di e-mail o un PDF e vuoi interrogarci uno strumento di IA. Nomi, numeri AVS e indirizzi però non devono partire con esso.",
      "hero.knopf1": "Scaricare",
      "hero.knopf2": "Come funziona",
      "bsp.vorher": "Prima",
      "bsp.nachher": "Dopo",
      "bsp.unten": "Il testo mascherato lo consegni al servizio che preferisci. La risposta la incolli indietro, e MASCHERA reinserisce i valori reali.",
      "bild.platzhalter": "Segnaposto",
      "bild.gross": "Schermata dell’applicazione con testo mascherato e occorrenze colorate · 1600 × 1000",
      "bild.schritt": "Schermata · 800 × 600",
      "bild.herkunft": "Un’occorrenza con la sua provenienza · 1200 × 675",
      "merkmale.kicker": "Quattro caratteristiche",
      "merkmale.titel": "Che cosa distingue lo strumento",
      "m1.titel": "Funziona sul tuo dispositivo",
      "m1.text": "Tutto il riconoscimento avviene in locale. In esercizio <strong>nulla</strong> viene scaricato e <strong>nulla</strong> viene inviato: né caratteri, né icone, né statistiche. Un endpoint che spedisca testo non esiste e non esisterà. La via verso l’esterno passa sempre dagli appunti.",
      "m2.titel": "Non annota nulla",
      "m2.text": "Vengono salvate solo le tue impostazioni, cioè regole, modelli e preferenze. Anche queste vengono salvate solo su comando esplicito. Nessun contenuto di documento, nessun dizionario, nessun registro.",
      "m3.titel": "Reversibile, ed è questo il senso",
      "m3.text": "Maschera, chiedi e incolli indietro la risposta: MASCHERA reinserisce i valori reali. Per questo si chiama <strong>pseudonimizzazione</strong> e non anonimizzazione. Finché il dizionario esiste il procedimento è reversibile, e i dati restano dati personali ai sensi della revLPD.",
      "m4.titel": "Costruito per documenti svizzeri",
      "m4.text": "Vengono riconosciuti numero AVS, IDI, IBAN, riferimento QR, identificatore di edificio e abitazione, categoria di licenza, targa e numero RCC, ciascuno con la sua cifra di controllo. <strong><br>45 tipi di dati</strong> in totale. Quattro lingue: tedesco, francese, italiano e inglese.",
      "ablauf.kicker": "La procedura",
      "ablauf.titel": "Cinque passi",
      "s1.titel": "Aprire o trascinare un documento, oppure incollare del testo",
      "s1.text": "Vengono letti .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Mascherare",
      "s2.text": "Ogni occorrenza è mostrata a colori, con la sua provenienza: cifra di controllo, schema o modello.",
      "s3.titel": "Verificare",
      "s3.text": "Vedi che cosa è stato sostituito, prima che il testo vada da qualche parte.",
      "s4.titel": "Copiare e incollare",
      "s4.text": "Nel servizio che preferisci, a mano. Lo strumento non spedisce nulla da sé.",
      "s5.titel": "Incollare indietro la risposta",
      "s5.text": "I valori reali ritornano.",
      "ablauf.leer": "<strong>Un esito vuoto non è un via libera.</strong> Un PDF scansionato senza livello di testo produce un errore motivato, non «nessun dato personale trovato». Uno strumento che lì rassicura è più pericoloso di uno che tace del tutto.",
      "stufen.titel": "Tre livelli, non soltanto «un’IA»",
      "stufen.th1": "Livello",
      "stufen.th2": "Che cosa fa",
      "stufen.1t": "1 · Cifre di controllo",
      "stufen.1b": "Numero AVS, IDI, IBAN, riferimento QR, carta di credito, GLN. Cifra valida → mascherare, anche se il modello tace. Non valida → scartare, anche se il modello segnala.",
      "stufen.2t": "2 · Schemi con àncora di contesto",
      "stufen.2b": "Numero di telefono, NPA, targa, categoria di licenza, numero di pratica e altri. Vengono riconosciuti tramite parole d’àncora in quattro lingue e non hanno precedenza sul modello. Si aggiungono le tue regole personali: parole e schemi che definisci tu. Funzionano come gli schemi integrati. Per esempio un n. di caso interno o un n. di dossier interno.",
      "stufen.3t": "3 · Modello linguistico",
      "stufen.3b": "Nomi, indirizzi, professioni, organizzazioni e date, cioè tutto ciò che non ha uno schema.",
      "stufen.modell": "Il modello è grande <strong>1,2 GB</strong> ed è stato addestrato su dati <strong>sintetici</strong>. Non ha mai visto un documento reale. <a href=\"#verweise\">Indicazioni tecniche sul modello</a>.",
      "pruefen.kicker": "La sezione più importante",
      "pruefen.satz": "MASCHERA ti toglie il lavoro, non la responsabilità.",
      "pruefen.text": "Nessuno strumento trova ogni dato personale. Guarda il testo mascherato prima di trasmetterlo. Per questo MASCHERA mostra ogni occorrenza a colori e con la sua provenienza.",
      "herkunft.titel": "Che cosa significa «provenienza»",
      "herkunft.text": "Ogni occorrenza mostra da dove viene: da un numero verificato, da uno schema con contesto, o dal modello linguistico. Un numero AVS con cifra di controllo valida è riconosciuto con certezza, una supposizione del modello merita una seconda occhiata.",
      "herkunft.menu": "Con un clic destro su un’occorrenza modifichi la marcatura: scegli un altro tipo di dato oppure rimuovi la maschera.",
      "moegl.titel": "Che cosa puoi fare se manca qualcosa",
      "moegl.lead": "Cinque possibilità, tutte presenti nell’applicazione.",
      "mo1t": "Correggere a mano",
      "mo1b": "Il testo mascherato è modificabile. I segnaposto come <code>[FULLNAME_1]</code> restano al loro posto e alla fine vengono riconvertiti.",
      "mo2t": "Regole proprie",
      "mo2b": "Parole e schemi tuoi, mascherati in aggiunta. Il nome di un progetto, una sigla interna, un soprannome.",
      "mo3t": "Tipi in chiaro",
      "mo3b": "Puoi lasciare stabilmente singoli tipi in chiaro. Vengono riconosciuti, ma non sostituiti. Chi vuole conservare le località lo imposta una volta.",
      "mo4t": "Riconvertire",
      "mo4b": "Incolli la risposta del servizio, e i valori reali ritornano.",
      "mo5t": "Anonimizzare definitivamente",
      "mo5b": "Mascherare senza dizionario. Allora il procedimento <strong>non è più reversibile</strong>, e l’applicazione te lo dice prima.",
      "moegl.beides": "<strong>MASCHERA sa fare entrambe le cose:</strong> reversibile per lavorare con un servizio di IA, irreversibile per un testo che esce di casa così com’è.",
      "dl.kicker": "Scaricare",
      "dl.titel": "Quale file prendo?",
      "dl.lead": "Nessun modulo di registrazione, nessuna richiesta di e-mail, nessuna newsletter. Il file è lì, lo si scarica, fine.",
      "dl.linux": "<b>AppImage:</b> un unico file eseguibile, il modello è incluso. Scaricare, rendere eseguibile e avviare. Non viene installato nulla.",
      "dl.mac": "Immagine disco per Mac con chip Apple (M1 o più recente). Il modello è incluso. L’app non è firmata: dopo averla trascinata in «Programmi», digita una volta nel «Terminale» <code>xattr -dr com.apple.quarantine /Applications/MASCHERA.app</code>, altrimenti non si apre.",
      "dl.win": "Programma d’installazione per Windows 11, 64 bit. Si installa senza diritti di amministratore, il modello è incluso.",
      "dl.flatpakHinweis": "<b>Flatpak:</b> Il modello (1,3 GB) viene scaricato da Hugging Face al primo avvio dell’applicazione.",
      "dl.serverTitel": "Server",
      "dl.server": "Docker, per l’esercizio come servizio. L’interfaccia si apre nel browser. Il modello è incluso. Il server non conserva nulla: nessun documento, nessun dizionario, nessun registro. Dopo la risposta tutto è dimenticato.",
      "dl.platzhalterHinweis": "Tutti i file si trovano nelle <a href=\"https://github.com/semprerudi/maschera/releases/latest\" rel=\"noopener noreferrer\">pubblicazioni su GitHub</a>, insieme a <code>SHA256SUMS</code> per la verifica.",
      "dl.modellTitel": "L’avvertenza sul modello",
      "dl.modell": "Il modello è grande 1,2 GB. L’AppImage, il programma d’installazione per Windows e l’immagine macOS lo portano con sé. Il Flatpak lo scarica <strong>una volta al primo avvio</strong>. Proviene da una fonte indicata, viene verificato con una cifra di controllo e viene scaricato solo dopo il tuo consenso. Chi non ha il wifi a portata di mano rifiuta e lo scarica un’altra volta. Dopo, tutto funziona offline allo stesso modo.",
      "dl.archTitel": "AppImage o Flatpak?",
      "dl.arch1": "AppImage è un unico file: scaricare, rendere eseguibile e avviare. Non viene installato nulla. Flatpak si integra nella gestione dei pacchetti e si aggiorna con essa.",
      "dl.arch2": "Entrambi portano con sé le proprie librerie e sono quindi indipendenti dalla versione della tua distribuzione. Sui sistemi Arch, Flatpak funziona benissimo; per questo non esiste un pacchetto Arch a parte.",
      "verweise.kicker": "Dove si trova tutto il resto",
      "verweise.titel": "La parte tecnica è tenuta aggiornata lì",
      "verweise.lead": "Quanto bene misura il modello, come è stato addestrato, come è costruito il programma: tutto questo sta lì e lì viene tenuto aggiornato.",
      "v1t": "Codice sorgente e versioni",
      "v1b": "Come è costruito, quale versione del programma lavora con quale modello, tutte le verifiche.",
      "v2t": "Il modello",
      "v2b": "Quanto è buono il modello, come è stato addestrato, quali tipi di dati conosce.",
      "v3t": "Segnalare un errore",
      "v3b": "Che cosa non è stato riconosciuto, che cosa è stato sostituito male, che cosa manca.",
      "imp.titel": "Note legali",
      "imp.verantw": "Responsabile",
      "imp.name": "Nome",
      "imp.land": "Paese",
      "imp.landWert": "Svizzera",
      "imp.kontakt": "Contatto",
      "imp.web": "Web",
      "imp.kontaktWert": "tramite <a href=\"https://github.com/semprerudi/maschera/issues\" rel=\"noopener noreferrer\">GitHub Issues</a>",
      "imp.zweckT": "Scopo",
      "imp.zweck": "MASCHERA è uno strumento per la mascheratura locale di dati personali in documenti svizzeri. È messo a disposizione come software aperto.",
      "imp.siteT": "Questo sito",
      "imp.site": "Il sito è servito tramite GitHub Pages (GitHub, Inc., USA). Alla consultazione GitHub tratta dati tecnicamente necessari, come l’indirizzo IP, nei propri registri del server; i dettagli si trovano nell’informativa sulla privacy di GitHub. Il sito stesso non imposta cookie, non raccoglie statistiche e non carica nulla da server di terzi. Anche i file da scaricare si trovano su GitHub.",
      "imp.appT": "L’applicazione",
      "imp.app": "MASCHERA elabora i tuoi documenti esclusivamente sul tuo dispositivo. Nessun contenuto viene trasmesso all’editore o a terzi, non vengono raccolti dati d’uso e non vengono impostati cookie. L’editore non ha quindi conoscenza dei dati trattati e non ne è responsabile ai sensi della LPD. La responsabilità dei dati resta tua. Non appena incolli un testo mascherato in uno strumento IA, valgono le condizioni di quel fornitore.",
      "imp.haftT": "Responsabilità",
      "imp.haft": "MASCHERA è fornito senza garanzia. Il riconoscimento dei dati personali è automatico e non è completo: può tralasciare indicazioni e nel dubbio maschera troppo. La verifica del testo mascherato prima della trasmissione spetta a te. Ogni responsabilità per danni derivanti dall’uso è esclusa nei limiti di legge. Dei contenuti dei siti collegati rispondono i rispettivi gestori.",
      "imp.lizT": "Licenza",
      "imp.liz": "Codice sorgente MIT, pacchetti distribuiti AGPL-3.0, modello MIT. Il codice sorgente e le opere di terzi utilizzate, con le rispettive licenze, si trovano su <a href=\"https://github.com/semprerudi/maschera\" rel=\"noopener noreferrer\">GitHub</a>.",
      "fuss.impressum": "Note legali",
      "fuss.name": "<em>MASCHERA</em> non ha bisogno di spiegazioni e porta la sigla nazionale CH nel mezzo.",
      "fuss.lizenz": "Licenza MIT"
    },

    en: {
      "nav.merkmale": "Features",
      "nav.ablauf": "How it works",
      "nav.pruefen": "Review",
      "thema.label": "Toggle light/dark",
      "nav.download": "Download",
      "hero.kicker": "Free software · Open Source · runs without a network",
      "hero.titel": "MASCHERA masks personal data<br>in Swiss documents<span style=\"display:block; font-size:0.75em; line-height:1.3; margin-top:0.3em\">It does so on your device, always locally,<br>with no network connection!</span>",
      "hero.lead": "You have a letter, an email thread or a PDF and want to ask an AI tool about it. The names, AHV numbers and addresses should stay behind, though.",
      "hero.knopf1": "Download",
      "hero.knopf2": "How it works",
      "bsp.vorher": "Before",
      "bsp.nachher": "After",
      "bsp.unten": "You hand the masked text to the service of your choice. You paste the answer back, and MASCHERA puts the real values in again.",
      "bild.platzhalter": "Placeholder",
      "bild.gross": "Screenshot of the application with masked text and coloured findings · 1600 × 1000",
      "bild.schritt": "Screenshot · 800 × 600",
      "bild.herkunft": "One finding with its origin · 1200 × 675",
      "merkmale.kicker": "Four features",
      "merkmale.titel": "What defines the tool",
      "m1.titel": "It runs on your device",
      "m1.text": "All detection happens locally. While it runs, <strong>nothing</strong> is fetched and <strong>nothing</strong> is sent: no fonts, no icons, no analytics. An endpoint that ships text out does not exist and will not exist. The way out always leads through your clipboard.",
      "m2.titel": "It writes nothing down",
      "m2.text": "Only your own settings are stored, meaning rules, templates and preferences. Even those are stored only on explicit command. No document content, no dictionary, no log.",
      "m3.titel": "Reversible, and that is the point",
      "m3.text": "You mask, you ask, you paste the answer back: MASCHERA puts the real values in again. That is why this is <strong>pseudonymisation</strong> and not anonymisation. As long as the dictionary exists the process is reversible, and under the revised FADP the data remain personal data.",
      "m4.titel": "Built for Swiss documents",
      "m4.text": "It detects the AHV number, UID, IBAN, QR reference, building and dwelling identifier, licence category, number plate and ZSR number, each with its checksum. <strong><br>45 data types</strong> in all. Four languages: German, French, Italian and English.",
      "ablauf.kicker": "The process",
      "ablauf.titel": "Five steps",
      "s1.titel": "Open or drag in a document, or paste text",
      "s1.text": "Read: .pdf, .docx, .eml, .msg (Outlook), .mbox, .txt, .md, .csv, .json.",
      "s2.titel": "Mask",
      "s2.text": "Every finding is shown in colour, with its origin: checksum, pattern or model.",
      "s3.titel": "Check",
      "s3.text": "You see what was replaced before the text goes anywhere.",
      "s4.titel": "Copy and paste",
      "s4.text": "Into the service of your choice, by hand. The tool sends nothing itself.",
      "s5.titel": "Paste the answer back",
      "s5.text": "The real values come back in.",
      "ablauf.leer": "<strong>An empty result is not an all-clear.</strong> A scanned PDF without a text layer yields an error with a reason, not “no personal data found”. A tool that gives the all-clear there is more dangerous than one that says nothing at all.",
      "stufen.titel": "Three stages, not just “an AI”",
      "stufen.th1": "Stage",
      "stufen.th2": "What it does",
      "stufen.1t": "1 · Checksums",
      "stufen.1b": "AHV number, UID, IBAN, QR reference, credit card, GLN. Valid checksum → mask, even if the model stays silent. Invalid → discard, even if it fires.",
      "stufen.2t": "2 · Patterns with context anchors",
      "stufen.2b": "Phone number, postcode, number plate, licence category, case number and more. They are detected by anchor words in four languages and take no precedence over the model. Your own rules come on top: words and patterns you define yourself. They run like the built-in patterns. For example an internal case no. or an internal file no.",
      "stufen.3t": "3 · Language model",
      "stufen.3b": "Names, addresses, occupations, organisations and dates, meaning everything without a pattern.",
      "stufen.modell": "The model is <strong>1.2 GB</strong> and was trained on <strong>synthetic</strong> data. It has never seen a real document. <a href=\"#verweise\">Technical details on the model</a>.",
      "pruefen.kicker": "The most important section",
      "pruefen.satz": "MASCHERA takes the work off your hands, not the responsibility.",
      "pruefen.text": "No tool finds every piece of personal data. Look at the masked text before you pass it on. That is why MASCHERA shows every finding in colour and with its origin.",
      "herkunft.titel": "What “origin” means",
      "herkunft.text": "Every finding shows where it came from: a verified number, a pattern with context, or the language model. An AHV number with a valid checksum is certainly right; a guess from the model deserves a second look.",
      "herkunft.menu": "Right-click a finding to change its marking: choose a different data type or remove the mask.",
      "moegl.titel": "What you can do if something is missing",
      "moegl.lead": "Five options, all present in the application.",
      "mo1t": "Fix it by hand",
      "mo1b": "The masked text is editable. Placeholders such as <code>[FULLNAME_1]</code> stay put and are converted back at the end.",
      "mo2t": "Your own rules",
      "mo2b": "Your own words and patterns, masked in addition. A project name, an internal abbreviation, a nickname.",
      "mo3t": "Plain-text types",
      "mo3b": "You can leave individual data types in plain text for good. They are detected, but not replaced. If you want to keep place names, you set that once.",
      "mo4t": "Convert back",
      "mo4b": "Paste the service’s answer in, and the real values come back.",
      "mo5t": "Anonymise for good",
      "mo5b": "Mask without a dictionary. The process is then <strong>no longer reversible</strong>, and the application tells you so beforehand.",
      "moegl.beides": "<strong>MASCHERA can do both:</strong> reversible for working with an AI service, irreversible for text that leaves the house as it is.",
      "dl.kicker": "Download",
      "dl.titel": "Which file do I take?",
      "dl.lead": "No sign-up form, no email address, no newsletter. The file is there, you download it, done.",
      "dl.linux": "<b>AppImage:</b> a single executable file, the model is included. Download, make executable and start. Nothing is installed.",
      "dl.mac": "Disk image for Macs with Apple silicon (M1 or newer). The model is included. The app is not signed: after dragging it into “Applications”, enter <code>xattr -dr com.apple.quarantine /Applications/MASCHERA.app</code> once in “Terminal”, otherwise it will not open.",
      "dl.win": "Installer for Windows 11, 64-bit. Installs without administrator rights, the model is included.",
      "dl.flatpakHinweis": "<b>Flatpak:</b> The model (1.3 GB) is downloaded from Hugging Face the first time the application starts.",
      "dl.serverTitel": "Server",
      "dl.server": "Docker, for running as a service. The interface opens in the browser. The model is included. The server keeps nothing: no document, no dictionary, no log. Once the answer is out, everything is forgotten.",
      "dl.platzhalterHinweis": "All files are in the <a href=\"https://github.com/semprerudi/maschera/releases/latest\" rel=\"noopener noreferrer\">releases on GitHub</a>, together with <code>SHA256SUMS</code> for verification.",
      "dl.modellTitel": "The note about the model",
      "dl.modell": "The model is 1.2 GB. The AppImage, the Windows installer and the macOS image carry it. The Flatpak fetches it <strong>once on first start</strong>. It comes from a named source, is verified with a checksum and is only fetched after you have agreed. No wifi at hand? Decline and fetch it another time. After that, everything works offline alike.",
      "dl.archTitel": "AppImage or Flatpak?",
      "dl.arch1": "AppImage is a single file: download it, make it executable and start it. Nothing is installed. Flatpak integrates with the package manager and updates along with it.",
      "dl.arch2": "Both bring their own libraries and are therefore independent of your distribution’s release. On Arch systems Flatpak runs perfectly well, which is why there is no separate Arch package.",
      "verweise.kicker": "Where everything else lives",
      "verweise.titel": "The technical part is kept up to date there",
      "verweise.lead": "How well the model measures, how it was trained, how the program is built: all of that lives there and is kept current there.",
      "v1t": "Source code and versions",
      "v1b": "How it is built, which program version works with which model, all the checks.",
      "v2t": "The model",
      "v2b": "How good the model is, how it was trained, which data types it knows.",
      "v3t": "Report a bug",
      "v3b": "What was not detected, what was replaced wrongly, what is missing.",
      "imp.titel": "Legal notice",
      "imp.verantw": "Responsible",
      "imp.name": "Name",
      "imp.land": "Country",
      "imp.landWert": "Switzerland",
      "imp.kontakt": "Contact",
      "imp.web": "Web",
      "imp.kontaktWert": "via <a href=\"https://github.com/semprerudi/maschera/issues\" rel=\"noopener noreferrer\">GitHub Issues</a>",
      "imp.zweckT": "Purpose",
      "imp.zweck": "MASCHERA is a tool for masking personal data locally in Swiss documents. It is provided as open software.",
      "imp.siteT": "This website",
      "imp.site": "This website is served through GitHub Pages (GitHub, Inc., USA). When you visit it, GitHub processes technically necessary data such as your IP address in its server logs; details are in GitHub’s privacy statement. The website itself sets no cookies, collects no statistics and loads nothing from third-party servers. The download files are hosted on GitHub as well.",
      "imp.appT": "The application",
      "imp.app": "MASCHERA processes your documents exclusively on your own device. No content is transmitted to the publisher or to third parties, no usage data is collected and no cookies are set. The publisher therefore gains no knowledge of the processed data and is not its controller within the meaning of the FADP. Responsibility for the data remains yours. As soon as you paste a masked text into an AI tool, that provider’s terms apply.",
      "imp.haftT": "Liability",
      "imp.haft": "MASCHERA is provided without warranty. Personal data is detected automatically and not exhaustively: it can miss details and masks too much when in doubt. Checking the masked text before passing it on is up to you. Liability for damages arising from use is excluded to the extent permitted by law. The operators of linked sites are responsible for their content.",
      "imp.lizT": "Licence",
      "imp.liz": "Source code MIT, shipped packages AGPL-3.0, model MIT. The source code and the third-party works used, with their licences, are on <a href=\"https://github.com/semprerudi/maschera\" rel=\"noopener noreferrer\">GitHub</a>.",
      "fuss.impressum": "Legal notice",
      "fuss.name": "<em>maschera</em> is Italian for mask and carries the country code CH in the middle.",
      "fuss.lizenz": "MIT licence"
    }
  };

  var titel = {
    de: "MASCHERA: Personendaten maskieren, auf deinem Gerät",
    fr: "MASCHERA : masquer les données personnelles, sur ton appareil",
    it: "MASCHERA: mascherare i dati personali, sul tuo dispositivo",
    en: "MASCHERA: mask personal data, on your own device"
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

  function setzen(sprache, merken) {
    var w = T[sprache] || T.de;
    document.documentElement.lang = sprache;
    document.querySelectorAll("img[data-bild]").forEach(function (el) {
      el.setAttribute("src", "bilder/" + (T[sprache] ? sprache : "de") + "/" + el.getAttribute("data-bild") + ".png");
    });
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
    if (merken) try { localStorage.setItem("maschera.sprache", sprache); } catch (e) {}
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
    b.addEventListener("click", function () { setzen(b.getAttribute("data-sprache"), true); });
  });

  // Linux-Teilknopf
  document.querySelectorAll(".teilknopf .auf").forEach(function (knopf) {
    var liste = document.getElementById(knopf.getAttribute("aria-controls"));
    knopf.addEventListener("click", function () {
      var offen = knopf.getAttribute("aria-expanded") === "true";
      knopf.setAttribute("aria-expanded", offen ? "false" : "true");
      liste.setAttribute("data-offen", offen ? "false" : "true");
    });
  });
})();

(function () {
  var knopf = document.querySelector(".thema"), wurzel = document.documentElement;
  if (!knopf) return;
  function setzen(t, merken) {
    wurzel.setAttribute("data-thema", t);
    knopf.setAttribute("aria-pressed", t === "dunkel" ? "true" : "false");
    if (merken) try { localStorage.setItem("maschera.thema", t); } catch (e) {}
  }
  setzen(wurzel.getAttribute("data-thema") || "hell", false);
  knopf.addEventListener("click", function () {
    setzen(wurzel.getAttribute("data-thema") === "dunkel" ? "hell" : "dunkel", true);
  });
  if (window.matchMedia) {
    var mq = matchMedia("(prefers-color-scheme: dark)");
    var folgen = function (e) {
      var g = null; try { g = localStorage.getItem("maschera.thema"); } catch (x) {}
      if (!g) setzen(e.matches ? "dunkel" : "hell", false);
    };
    mq.addEventListener ? mq.addEventListener("change", folgen) : mq.addListener(folgen);
  }
})();
