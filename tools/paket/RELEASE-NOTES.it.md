# MASCHERA 2.5.0

**Ora vengono mascherate anche le professioni e i ruoli familiari, con un nuovo modello.**

- Due nuovi tipi di dati personali: le **professioni** («capoprogetto», «capo
  dell'ufficio», «Head of Legal») e i **ruoli familiari** (padre, nonna, curatore).
  Insieme al contesto riconducono a una persona. Entrambi vengono mascherati e nelle
  impostazioni, sotto «Persona», si possono lasciare visibili.
- **Nuovo modello `ch-v71f`.** Prosegue il modello precedente invece di ripartire da
  zero. Riconosce i nomi nell'intestazione dei verbali come persone e non più come
  organizzazione. Sui nove documenti di riferimento: 6 fughe come prima, micro-F1 0,757
  invece di 0,736. Il Flatpak chiede prima di scaricare il nuovo modello (1,2 GB).
- **Clic destro su ID o tipo nel vocabolario**: lo stesso menu del testo mascherato, per
  cambiare il tipo o rimuovere la maschera. I tag usati di recente stanno in alto.
- **Finestra «Utilizzo»** con piccole scene: mettere una maschera, cambiarne il tipo,
  rimuoverla. Compare dopo il primo mascheramento finché non la disattivi, e si trova
  nel menu.
- **Note di rilascio** nel menu, in tutte e quattro le lingue. Viaggiano con l'app, nulla
  viene scaricato da Internet.
- Visualizzazione stretta: i riquadri seguono l'altezza della finestra, «Riprendi nel
  prompt» si trova anche sotto il vocabolario, e il vocabolario omette la colonna
  «Tipo» perché si possa leggere il valore originale.
- I tooltip compaiono sopra il pulsante invece che sotto il puntatore.
- Un modello con il vecchio contratto delle etichette non si carica in questa versione
  (ora 47 tag, 95 etichette).
