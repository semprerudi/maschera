<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Erkennungsregeln

Quelle: `packs/ch/patterns.yaml`. Stufe 1: das Muster findet Kandidaten, die Prüfsumme entscheidet. Stufe 2: das Muster findet Kandidaten, der Anker entscheidet.

## AHVN13

```yaml
stage: 1
pattern: 756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}(?!\d)
validator: AHVN13
```

## UID

```yaml
stage: 1
pattern: CHE[-\s]?\d{3}[.\s]?\d{3}[.\s]?\d{3}(?:\s?(?:MWST|TVA|IVA|HR))?
validator: UID
```

## QR_REFERENCE

```yaml
stage: 1
pattern: (?<!\d)\d{2}(?:[\s]?\d{5}){5}(?!\d)
validator: QR_REFERENCE
```

## GLN

```yaml
stage: 1
pattern: (?<!\d)\d{13}(?!\d)
validator: GLN
anchor_window: 60
anchor:
  required: true
  words:
  - GLN
  - Global Location Number
  - Medizinalperson
  - MedReg
  - numéro GLN
  - numero GLN
```

## CREDITCARD

```yaml
stage: 1
pattern: (?<![\d-])(?:4\d{3}|5[1-5]\d{2}|2[2-7]\d{2}|3[47]\d{2}|36\d{2}|6011)[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{2,4}(?![\d-])
validator: CREDITCARD
```

## EGID

```yaml
stage: 2
pattern: (?<!\d)\d{3,9}(?!\d)
anchor_same_line: true
anchor_window: 45
anchor:
  required: true
  words:
  - EGID
  - Gebäudeidentifikator
  - Gebaeudeidentifikator
  - eidg. Gebäudenummer
  - identificateur fédéral de bâtiment
  - identificateur de bâtiment
  - identificatore federale dell'edificio
  - identificatore dell'edificio
  - federal building identifier
  - building identifier
```

## EWID

```yaml
stage: 2
pattern: (?<!\d)\d{1,3}(?!\d)
anchor_same_line: true
anchor_window: 40
anchor:
  required: true
  words:
  - EWID
  - Wohnungsidentifikator
  - eidg. Wohnungsnummer
  - identificateur de logement
  - identificatore di abitazione
  - dwelling identifier
```

## MUNICIPALITY_ID

```yaml
stage: 2
pattern: (?<!\d)\d{1,4}(?!\d)
anchor_same_line: true
anchor_window: 45
anchor:
  required: true
  words:
  - BFS-Nr
  - BFS-Nummer
  - BFS Nr
  - Gemeindenummer
  - Gemeinde-Nr
  - numéro OFS
  - no OFS
  - numero UST
  - FSO number
  - municipality number
```

## INSURANCE_CARD

```yaml
stage: 2
pattern: (?<!\d)80756\d{15}(?!\d)
```

## PHONE

```yaml
stage: 2
pattern: (?:\+41|0041|0)[\s./-]?\(?\d{2}\)?[\s./-]?\d{3}[\s./-]?\d{2}[\s./-]?\d{2}(?!\d)
```

## PLATE

```yaml
stage: 2
pattern: (?<![A-Z])(?:AG|AI|AR|BE|BL|BS|FR|GE|GL|GR|JU|LU|NE|NW|OW|SG|SH|SO|SZ|TG|TI|UR|VD|VS|ZG|ZH)[\s·-]?\d{1,6}(?!\d)
```

## ZIPCODE

```yaml
stage: 2
pattern: (?<!\d)(?:[1-8]\d{3}|9[0-5]\d{2}|96[0-8]\d|969[0-9])(?=[ \t]+(?!Franken|Fr\.|CHF|francs?|franchi)[A-ZÄÖÜ][a-zäöüàéèêîôûç])
```

## AMOUNT

```yaml
stage: 2
pattern: (?:CHF|SFr\.|Fr\.)\s?(?:\d{1,3}(?:['’\s,]\d{3})+|\d+)(?:[.,]\d{2}(?!\d)|[.,]--)?|(?:\d{1,3}(?:['’\s,]\d{3})+|\d+)(?:[.,]\d{2}(?!\d))?\s?(?:Franken|franchi|francs|franc)(?![A-Za-zÀ-ÿ])
anchor_window: 45
anchor_not:
- Freibetrag
- Höchstbetrag
- Mindestbetrag
- Grundbedarf
- Ansatz
- Pauschale
- Gebühr
- Tarif
- franchise
- franchigia
- émolument
- emolument
- emolumento
- tassa
- forfait
- Beitragsansatz
- montant maximal
- montant minimal
- importo massimo
- importo minimo
- allowance
- tax-free
- fee
- flat rate
- maximum amount
- minimum amount
- deductible
```

## PERMIT_TYPE

```yaml
stage: 2
pattern: (?:Ausweis|Bewilligung|permis|permesso|permit)\s+(?:Ci|[BCLGFNS])(?![\w])
flags: i
```

## IDDOC

```yaml
stage: 2
pattern: (?<![A-Z0-9])[A-Z]\d{7}(?![A-Z0-9])
anchor_window: 50
anchor:
  required: false
  words:
  - Pass
  - Passnummer
  - Reisepass
  - Identitätskarte
  - Ausweisnummer
  - passeport
  - carte d'identité
  - passaporto
  - carta d'identità
  - passport
  - ID card
```

## ZSR_RCC

```yaml
stage: 2
pattern: (?<![A-Z0-9])[A-Z]\d{6}(?![A-Z0-9])
anchor_window: 50
anchor:
  required: true
  words:
  - ZSR
  - ZSR-Nr
  - Zahlstellenregister
  - RCC
  - registre des codes-créanciers
  - registro dei codici creditori
  - santésuisse
```

## PATIENT_ID

```yaml
stage: 2
pattern: '[A-Z0-9][A-Z0-9./-]{3,19}'
anchor_window: 40
anchor:
  required: true
  words:
  - Patientennummer
  - Patienten-Nr
  - Patienten-ID
  - Fallnummer
  - numéro de patient
  - numéro du patient
  - numero paziente
  - patient number
  - patient ID
```

## CASE_ID

```yaml
stage: 2
pattern: '[A-Z]{2,6}[-/][0-9]{2,4}[-/][0-9]{2,6}|[0-9]{4}[-/][0-9]{3,6}'
anchor_window: 40
anchor:
  required: false
  words:
  - Dossier
  - Geschäftsnummer
  - Geschäfts-Nr
  - Aktenzeichen
  - Referenz
  - numéro de dossier
  - numero d'incarto
  - case number
  - file number
```

## PARCEL

```yaml
stage: 2
pattern: (?<!\d)\d{1,5}(?:[.-]\d{1,3})?(?!\d)
anchor_same_line: true
anchor_window: 40
anchor:
  required: true
  words:
  - Parzelle
  - Parzellen-Nr
  - Grundstück
  - Grundstücks-Nr
  - Liegenschaft
  - parcelle
  - bien-fonds
  - particella
  - fondo
  - parcel
  - plot
```

## PLACE_OF_ORIGIN

```yaml
stage: 2
pattern: '[A-ZÄÖÜÀÉÈ][\wäöüàéèêîôûç.''’/-]+(?:[ -](?:[A-ZÄÖÜÀÉÈ][\wäöüàéèêîôûç.''’/-]*|(?:de|di|du|da|dal|des|dei|degli|della|dello|la|le|les|el|am|im|an|auf|bei|ob|vor|unter|ausser|sur|sous|sopra|sotto|en|aux|au|à|in|et|ed|e)(?=[
  -]))){0,4}(?:\s\([^()]*(?:\([^()]*\)[^()]*)*\))?\s(?:AG|AI|AR|BE|BL|BS|FR|GE|GL|GR|JU|LU|NE|NW|OW|SG|SH|SO|SZ|TG|TI|UR|VD|VS|ZG|ZH)(?![A-Za-z])'
anchor_window: 60
anchor_after: true
anchor_max_distance: 4
anchor:
  required: true
  words:
  - Heimatort
  - heimatberechtigt
  - Bürgerort
  - Buergerort
  - Bürgerrecht
  - von
  - lieu d'origine
  - originaire de
  - droit de cité
  - luogo di origine
  - attinente
  - place of origin
  - luogo di attinenza
  - Heimatorte
  - lieu d'origine
  - lieux d'origine
  - luoghi di attinenza
  - places of origin
```

## DATE

```yaml
stage: 2
flags: i
pattern: (?<!gesetz vom )(?<!gesetzes vom )(?<!verordnung vom )(?<!verordnungen
  vom )(?<!beschluss vom )(?<!abkommen vom )(?<!reglement vom )(?<!richtlinie
  vom )(?<!weisung vom )(?<!kreisschreiben vom )(?<!loi du )(?<!loi fédérale
  du )(?<!ordonnance du )(?<!arrêté du )(?<!règlement du )(?<!directive
  du )(?<!convention du )(?<!legge del )(?<!legge federale del )(?<!ordinanza
  del )(?<!decreto del )(?<!regolamento del )(?<!direttiva del )(?<!convenzione
  del )(?<!act of )(?<!regulation of )(?<!directive of )(?<![\d.])(?:[0-3]?\d[./-][0-1]?\d[./-](?:\d{4}|\d{2})|\d{4}-[0-1]\d-[0-3]\d|[0-3]?\d\.?\s(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre|gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|dicembre|January|February|March|May|June|July|August|September|October|November|December)\s\d{4})(?!\d)(?!\.\d)
```

## USERNAME

```yaml
stage: 2
pattern: (?<=/home/)[a-z][a-z0-9._-]{3,30}|(?<=\\Users\\)[A-Za-z][A-Za-z0-9._-]{3,30}|(?<![A-Za-z0-9])[A-Z]{2,6}\\[a-z][a-z0-9._-]{3,30}
flags: ''
```

## USERNAME_ETIKETT

```yaml
tag: USERNAME
stage: 2
pattern: (?<![^\s:=])[A-Za-z][A-Za-z0-9._-]{3,30}
anchor_window: 30
anchor_same_line: true
anchor_max_distance: 3
anchor:
  required: true
  words:
  - Benutzername
  - Benutzerkonto
  - Anmeldename
  - Kontoname
  - Login
  - Username
  - User-ID
  - Userid
  - nom d'utilisateur
  - identifiant
  - nome utente
```

## EMAIL

```yaml
stage: 2
pattern: '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
```

## URL

```yaml
stage: 2
pattern: https?://[^\s<>"]*[^\s<>",.;:!?)]|www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s<>"]*[^\s<>",.;:!?)])?
```

## IPADDRESS

```yaml
stage: 2
pattern: (?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?![\d.])|(?<![:\w])(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}(?![:\w])|(?<![:\w])(?=[A-Fa-f0-9:]*[A-Fa-f0-9])(?:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4})*)?::(?:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4})*)?(?![:\w])
```

## ORG_FIRMA

```yaml
tag: ORG
stage: 2
pattern: \b[A-ZÄÖÜÀ-Þ][\w.'’-]*(?:[ \t]*[&+][ \t]*|[ \t]+(?:und|and|et|e)[
  \t]+)[A-ZÄÖÜÀ-Þ][\w.'’-]*(?:[ \t]+[A-ZÄÖÜÀ-Þ][\w.'’-]*){0,2}[ \t]+(?:AG|SA|SpA|GmbH|Sàrl|Sarl|Sagl|Ltd|LLC|Inc|KlG|KmG|Genossenschaft|Stiftung|Verein|Anstalt|Holding|Treuhand)\b
```

## ORG_BEHOERDE_BUND

```yaml
tag: ORG
stage: 2
pattern: (?:(?:Bundesamt|Staatssekretariat|Bundesanwaltschaft|Eidgenössisches[
  \t]+Departement|Federal[ \t]+Office|Federal[ \t]+Department)(?:[ \t]+(?:für|fuer|for|of|des|and|und)\b)?(?:[
  \t]+(?:[A-ZÄÖÜÀ-Þ][A-Za-zÄÖÜÀ-Þäöüà-ÿ'’-]+|(?:für|fuer|for|of|des|and|und)\b)){1,4}|(?:Office[
  \t]+fédéral|Secrétariat[ \t]+d.État|Département[ \t]+fédéral|Ufficio[
  \t]+federale|Segreteria[ \t]+di[ \t]+Stato|Dipartimento[ \t]+federale)(?:[
  \t]+(?:di|de|del|della|dello|delle|degli|dei|des|du|aux|au|à|per|et|e)\b)?(?:[
  \t]+(?:[A-ZÄÖÜÀ-Þ][A-Za-zÄÖÜÀ-Þäöüà-ÿ'’-]+|(?:la|le|les|aux|au|du|des|de|di|del|della|dello|delle|degli|dei|et|e|per|à)\b|(?:l['’])?(?:approvvigionamento|approvisionnement|communications|intellectuelle|pianificazione|assicurazioni|communication|comunicazione|comunicazioni|constructions|contributions|contribuzioni|développement|environnement|cooperazione|informatique|statistiques|agricoltura|agriculture|alimentaire|aménagement|coopération|costruzioni|informatica|innovazione|istituzioni|medicamenti|mensuration|misurazione|médicaments|popolazione|statistique|topographie|veterinario|vétérinaire|abitazioni|alimentare|assurances|educazione|formazione|frontières|habitation|innovation|logistique|metrologia|migrations|migrazione|métrologie|patrimoine|patrimonio|population|protection|protezione|statistica|territoire|territorio|topografia|transports|étrangères|armamenti|aviazione|commercio|formation|giustizia|gestion|gestione|contrôle|controllo|surveillance|financière|financier|technique|administrative|administratif|juridique|finanziaria|finanziario|tecnica|tecnico|amministrativa|amministrativo|giuridica|giuridico|vigilanza|intérieur|logistica|migration|numérique|paesaggio|personale|personnel|proprietà|propriété|publiques|recherche|sanitaire|sanitario|sicurezza|trasporti|éducation|affaires|ambiente|armement|aviation|cadastre|commerce|digitale|economia|esercito|finances|gioventù|jeunesse|logement|pubblica|publique|registre|registro|sociales|sviluppo|sécurité|économie|catasto|confini|cultura|culture|douanes|défense|energia|finanze|foreste|interni|justice|paysage|polizia|ricerca|sociale|sociali|travail|égalité|énergie|affari|civile|difesa|dogana|dogane|douane|emploi|esteri|forêts|lavoro|natura|nature|police|routes|sanità|strade|acque|armée|santé|sport|eaux))){1,4})
```

## ORG_BEHOERDE_AMT

```yaml
tag: ORG
stage: 2
pattern: (?<!Ges)\b[A-ZÄÖÜ][a-zäöüß-]{5,}(?:amt|behörde|behoerde|dienste)\b|\b(?:Gemeinde|Stadt|Kantons|Bundes|Steuer|Finanz|Zivilstands)verwaltung\b|\b(?:Einwohnergemeinde|Einwohnerdienste|Gemeindeverwaltung|Staatskanzlei|Regionalgericht|Bezirksgericht|Kreisbüro|Sozialdienst)\b|\bAmt[
  \t]+für[ \t]+[A-ZÄÖÜ][a-zäöüß]{3,}|\b[A-ZÄÖÜ][a-zäöüß]{2,}-[ \t]*und[
  \t]+[A-ZÄÖÜ][a-zäöüß]{3,}(?:behörde|amt|dienste)\b|(?:Ufficio|Sezione|Dipartimento|Servizio|Registro|Controllo|Settore)[
  \t]+(?:(?:dello|della|delle|degli|dei|del)[ \t]+[A-ZÄÖÜÀ-Þa-zàéèìòù'’-]{2,}|(?:di|d'|[a-zàéèìòù'’-]{4,}))(?:[
  \t]+(?:dello|della|delle|degli|dei|del|di|e|approvvigionamento|pianificazione|assicurazioni|comunicazione|comunicazioni|contribuzioni|cooperazione|agricoltura|costruzioni|informatica|innovazione|istituzioni|medicamenti|misurazione|popolazione|veterinario|abitazioni|alimentare|educazione|formazione|metrologia|migrazione|patrimonio|protezione|statistica|territorio|topografia|armamenti|aviazione|commercio|giustizia|gestion|gestione|contrôle|controllo|surveillance|financière|financier|technique|administrative|administratif|juridique|finanziaria|finanziario|tecnica|tecnico|amministrativa|amministrativo|giuridica|giuridico|vigilanza|logistica|paesaggio|personale|proprietà|sanitario|sicurezza|trasporti|ambiente|digitale|economia|esercito|gioventù|pubblica|registro|sviluppo|catasto|confini|cultura|energia|finanze|foreste|interni|polizia|ricerca|sociale|sociali|affari|civile|difesa|dogana|dogane|esteri|lavoro|natura|sanità|strade|acque|sport)){0,2}(?<![
  \t]di)(?<![ \t]da)(?:[ \t]+e[ \t]+[a-zàéèìòù'’-]{2,})?|\b(?:Civil Registry
  Office|Debt Enforcement Office|Land Registry|Residents.? Registration|Tax
  Administration|Federal Chancellery)\b|(?:Amministrazione|Servizio|Ufficio)[
  \t]+(?:comunale|sociale|cantonale)\b|(?:Service|Office|Registre)[ \t]+(?:social|communal|foncier)\b|(?:Office|Service|Contrôle|Registre|Administration|Chancellerie|Autorité)[
  \t]+(?:de|des|du|d'|foncier|communale|cantonale)(?:[ \t]+[a-zàéèêôûç'’-]{2,}){0,3}(?<![
  \t]de)(?<![ \t]du)(?<![ \t]à)(?:[ \t]+et[ \t]+(?:[a-zàéèêôûç'’-]{2,}[
  \t]+){0,2}[a-zàéèêôûç'’-]{2,})?
```

## ORG_BEHOERDE_KANTON

```yaml
tag: ORG
stage: 2
pattern: (?:Repubblica[ \t]+e[ \t]+Cantone|République[ \t]+et[ \t]+Canton(?:[
  \t]+de)?|Republik[ \t]+und[ \t]+Kanton|Staat[ \t]+und[ \t]+Kanton)[
  \t]+(?:St\.[ \t]+Gallen|[A-ZÄÖÜÀ-Þ][A-Za-zäöüà-ÿ'’/-]{2,}(?:[ \t]+[A-ZÄÖÜÀ-Þ][A-Za-zäöüà-ÿ'’/-]{2,})?)
```

## ORG_BEHOERDE_DEPARTEMENT

```yaml
tag: ORG
stage: 2
pattern: (?:Eidgenössisches[ \t]+)?[A-ZÄÖÜ][A-Za-zäöüß]{2,}(?:-\s*und[
  \t]+[A-ZÄÖÜ]?[A-Za-zäöüß]{2,})?departement\b(?:[ \t]+[A-ZÄÖÜ]{2,6}\b)?
```

## MARITALSTATUS_KATALOG

```yaml
tag: MARITALSTATUS
stage: 2
pattern: (?i)(?:lié\ par\ un\ partenariat\ enregistré|in\ eingetragener\
  Partnerschaft|in\ unione\ domestica\ registrata|in\ a\ registered\ partnership|aufgelöste\
  Partnerschaft|unione\ domestica\ sciolta|separato\ giudizialmente|dissolved\
  partnership|séparé\ judiciairement|gerichtlich\ getrennt|freiwillig\
  getrennt|partenariat\ dissous|unverheiratet|non\ coniugato|verheiratet|célibataire|non\
  mariée|geschieden|divorziata|divorziato|non\ marié|verwitwet|coniugato|coniugata|divorced|divorcée|divorcé|widowed|married|nubile|celibe|mariée|vedova|single|vedovo|marié|ledig|veuve|veuf)
anchor:
  required: true
  words:
  - Zivilstand
  - état civil
  - etat civil
  - stato civile
  - marital status
  - Personenstand
anchor_same_line: true
anchor_max_distance: 3
```

## RELIGION_KATALOG

```yaml
tag: RELIGION
stage: 2
pattern: (?i)(?:Evangelisch\-Reformierte\ Kirche|jüdische\ Glaubensgemeinschaft|sans\
  appartenance\ religieuse|Chiesa\ evangelica\ riformata|Église\ évangélique\
  réformée|Römisch\-katholische\ Kirche|israelitische\ Gemeinschaft|Église\
  catholique\ romaine|no\ religious\ affiliation|Christkatholische\ Kirche|Chiesa\
  cattolica\ romana|evangelisch\-reformiert|catholique\ chrétienne|comunità\
  israelitica|communauté\ israélite|évangélique\ réformée|evangelica\
  riformata|Protestant\ Reformed|cattolica\ cristiana|catholique\ romaine|Christian\
  Catholic|römisch\-katholisch|senza\ confessione|christkatholisch|cattolica\
  romana|Jewish\ community|sans\ confession|ohne\ Konfession|Roman\ Catholic|protestantisch|konfessionslos|altkatholisch|protestante)
anchor:
  required: true
  words:
  - Konfession
  - Konfessionszugehörigkeit
  - Religion
  - confession
  - appartenance religieuse
  - confessione
  - religione
  - religious affiliation
anchor_same_line: true
anchor_max_distance: 3
```

## SEX_KATALOG

```yaml
tag: SEX
stage: 2
pattern: (?i)(?:femminile|masculin|männlich|weiblich|maschile|féminin|female|male)
anchor:
  required: true
  words:
  - Geschlecht
  - sexe
  - sesso
  - sex
  - gender
anchor_same_line: true
anchor_max_distance: 3
```

## RESIDENCE_STATUS_KATALOG

```yaml
tag: RESIDENCE_STATUS
stage: 2
pattern: (?i)(?:domicilio\ principale|résidence\ secondaire|residenza\
  principale|résidence\ principale|domicilio\ secondario|domicile\ secondaire|permanent\
  residence|temporary\ residence|secondary\ residence|domicile\ principal|Wochenaufenthalt|niedergelassen|main\
  residence|Niederlassung|Hauptwohnsitz|établissement|Nebenwohnsitz|Aufenthalt|domicilio|séjour|dimora)
anchor:
  required: true
  words:
  - Meldeverhältnis
  - Meldeverhaeltnis
  - Wohnsitzart
  - rapport d'annonce
  - type de domicile
  - rapporto di notifica
  - tipo di domicilio
anchor_same_line: true
anchor_max_distance: 3
```

## SEX_KURZ

```yaml
tag: SEX
stage: 2
pattern: (?<![A-Za-zÄÖÜäöü])[mwfdMWFD](?![A-Za-zÄÖÜäöü])
anchor:
  required: true
  words:
  - Geschlecht
  - sexe
  - sesso
  - sex
  - gender
anchor_same_line: true
anchor_max_distance: 2
```
