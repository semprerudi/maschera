<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Tags

Quelle: `packs/ch/taxonomy.yaml`. Die Reihenfolge ist der BIO-Indexvertrag.

45 Tags, 91 BIO-Labels. Vertrag sha256 `b7a96dc99b05c6150302fc11943e0a357c7078b593e7382b4b06390245cceeee`.

| Index | Tag | Stufe | Aktion | Budget | bspd | Override | Notiz |
|---:|---|---:|---|---|---|---|---|
| 0 | `AHVN13` | 1 | mask |  | nein | checksum | EAN-13, Präfix 756, 13-stellig |
| 1 | `UID` | 1 | mask |  | nein | checksum | Modulo-11, Präfix CHE, Gewichte 5,4,3,2,7,6,5,4 |
| 2 | `IBAN` | 1 | mask |  | nein | checksum | Modulo-97 nach ISO 13616, CH/LI = 21 Zeichen |
| 3 | `QR_REFERENCE` | 1 | mask |  | nein | checksum | Modulo-10 rekursiv, 27-stellig |
| 4 | `CREDITCARD` | 1 | mask |  | nein | checksum | Luhn, 12-19 Ziffern |
| 5 | `GLN` | 1 | mask |  | nein | checksum | EAN-13 ohne 756-Prüfung, Medizinalperson |
| 6 | `EGID` | 2 | mask | R | nein |  | Kontextwort zwingend, viersprachig |
| 7 | `EWID` | 2 | mask | R | nein |  | Kontextwort zwingend, nie ohne EGID |
| 8 | `MUNICIPALITY_ID` | 2 | mask | R | nein |  | BFS-Gemeindenummer, Kontextwort zwingend |
| 9 | `INSURANCE_CARD` | 2 | mask | R | ja |  | Versichertenkarte, 80756 + 15 Ziffern. OFFENER PUNKT 1: Prüfmechanismus nicht verifiziert, deshalb Stufe 2 statt Stufe 1. Bei Verifikation nach Stufe 1 verschieben, der BIO-Index bleibt davon unberührt. |
| 10 | `PHONE` | 2 | mask | A | nein |  | +41 / 0xx |
| 11 | `PLATE` | 2 | mask | A | nein |  | Kantonskürzel + 1-6 Ziffern |
| 12 | `ZIPCODE` | 2 | mask | P | nein |  | 1000-9699, Ortsname muss folgen |
| 13 | `AMOUNT` | 2 | mask | P | nein |  | CHF / Fr. / franc / franchi |
| 14 | `PERMIT_TYPE` | 2 | mask | R | nein |  | Ausweis B/C/Ci/L/G/F/N/S |
| 15 | `IDDOC` | 2 | mask | R | nein |  | Pass-/ID-Nummer, Buchstabe + 7 Ziffern |
| 16 | `ZSR_RCC` | 2 | mask | R | nein |  | Zahlstellenregister santésuisse |
| 17 | `PATIENT_ID` | 2 | mask | R | ja |  | Kontextwort zwingend |
| 18 | `CASE_ID` | 2 | mask | A | nein |  | Dossier- / Geschäftsnummer |
| 19 | `PARCEL` | 2 | mask | A | nein |  | Parzelle / Grundstück |
| 20 | `URL` | 2 | mask | P | nein |  | Standardmuster |
| 21 | `IPADDRESS` | 2 | mask | P | nein |  | Standardmuster, v4 und v6 |
| 22 | `EMAIL` | 2 | mask | R | nein |  | Standardmuster |
| 23 | `FULLNAME` | 3 | mask | R | nein |  | zentraler Identifikator, Dokument-Propagation setzt hier an |
| 24 | `GIVENNAME` | 3 | mask | R | nein |  |  |
| 25 | `DATE` | 3 | mask | R | nein |  | vier Formatvarianten |
| 26 | `TIME` | 3 | mask | R | nein |  |  |
| 27 | `STREET` | 3 | mask | R | nein |  |  |
| 28 | `BUILDINGNUM` | 3 | mask | R | nein |  |  |
| 29 | `CITY` | 3 | mask | A | nein |  | eine Stadt identifiziert nicht, eine Kleinstgemeinde schon, bewusster Kompromiss |
| 30 | `COUNTRY` | 3 | mask | P | nein |  |  |
| 31 | `AGE` | 3 | mask | A | nein |  | Quasi-Identifikator |
| 32 | `SEX` | 3 | mask | A | nein |  | Quasi-Identifikator |
| 33 | `MARITALSTATUS` | 3 | mask | A | nein |  |  |
| 34 | `RELIGION` | 3 | mask | R | ja |  | RHG Art. 6 Bst. l |
| 35 | `NATIONALITY` | 3 | mask | R | ja |  | Ethnie-Rückschluss |
| 36 | `SOCIAL_INSURANCE` | 3 | mask | R | ja |  | IV-Fall, Kassennummer |
| 37 | `INSURANCE_POLICY` | 3 | mask | R | ja |  |  |
| 38 | `RESIDENCE_STATUS` | 3 | mask | A | nein |  | Niederlassung / Aufenthalt |
| 39 | `VOTING_RIGHTS` | 3 | mask | A | nein |  |  |
| 40 | `PLACE_OF_ORIGIN` | 3 | mask | R | nein |  | mask, nicht tag_only. Der Heimatort verrät zwar nichts über den Wohnort, aber: das Schweizer Ortschaftenverzeichnis hängt Kantonskürzel an, um gleichnamige Orte zu unterscheiden ("Reute AR", "Benken SG"). Wohnorte sehen damit exakt aus wie Heimatorte, und die Fehlerrichtung war asymmetrisch, ein als Heimatort gelesener Wohnort blieb im Klartext, umgekehrt ging nur Kontext verloren. Solange ein nicht maskierendes Tag einem maskierenden zum Verwechseln ähnlich sieht, lecken Fehler in eine Richtung. Das ist nicht wegtrainierbar, weil die Formen an der Oberfläche identisch sind. |
| 41 | `CANTON` | 3 | tag_only | P | nein |  | trägt Kontext, identifiziert nicht |
| 42 | `ORG` | 3 | mask | P | nein |  |  |
| 43 | `HEALTHCARE_ORG` | 3 | mask | R | ja |  | Spezialklinik verrät mehr als die Diagnose |
| 44 | `USERNAME` | 3 | mask | R | nein |  | Kontoname, Pfadbestandteil, Anmeldename |

## Schwellen

```yaml
R: 0.3
A: 0.5
P: 0.7
ORG: 0.4
```
