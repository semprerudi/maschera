#!/usr/bin/env python3
"""Fügt jedem maskierten Tag eine lesbare Platzhalterbezeichnung hinzu.

Einmalig ausgeführt, danach steht `placeholder:` in taxonomy.yaml.
Bewusst ASCII ohne Leerzeichen: der Platzhalter muss sich verlustfrei
wiederfinden lassen, auch nachdem ein Frontier-Modell den Text umgebaut hat.
"""

import re
from pathlib import Path

PLACEHOLDERS = {
    # Stufe 1
    "AHVN13": "AHVN13",
    "UID": "UID",
    "IBAN": "IBAN",
    "QR_REFERENCE": "Referenz",
    "CREDITCARD": "Karte",
    "GLN": "GLN",
    # Stufe 2
    "EGID": "EGID",
    "EWID": "EWID",
    "MUNICIPALITY_ID": "Gemeindenr",
    "INSURANCE_CARD": "Versichertenkarte",
    "PHONE": "Telefon",
    "PLATE": "Kontrollschild",
    "ZIPCODE": "PLZ",
    "AMOUNT": "Betrag",
    "PERMIT_TYPE": "Ausweis",
    "IDDOC": "Ausweisnr",
    "ZSR_RCC": "ZSR",
    "PATIENT_ID": "PatientNr",
    "CASE_ID": "Dossier",
    "PARCEL": "Parzelle",
    "URL": "URL",
    "IPADDRESS": "IP",
    "EMAIL": "Email",
    # Stufe 3
    "FULLNAME": "Name",
    "GIVENNAME": "Vorname",
    "DATE": "Datum",
    "TIME": "Zeit",
    "STREET": "Strasse",
    "BUILDINGNUM": "Hausnr",
    "CITY": "Ort",
    "COUNTRY": "Land",
    "AGE": "Alter",
    "SEX": "Geschlecht",
    "MARITALSTATUS": "Zivilstand",
    "RELIGION": "Konfession",
    "NATIONALITY": "Nation",
    "SOCIAL_INSURANCE": "Sozialversicherung",
    "INSURANCE_POLICY": "Police",
    "RESIDENCE_STATUS": "Aufenthalt",
    "VOTING_RIGHTS": "Stimmrecht",
    "ORG": "Firma",
    "HEALTHCARE_ORG": "Klinik",
    # tag_only -> kein Platzhalter, bleibt im Klartext
}

path = Path(__file__).resolve().parent.parent / "packs/ch/taxonomy.yaml"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

out = []
current = None
for line in lines:
    m = re.match(r"^  - tag: (\w+)\s*$", line)
    if m:
        current = m.group(1)
    out.append(line)
    if current and re.match(r"^    action: \w+\s*$", line):
        if current in PLACEHOLDERS:
            out.append(f"    placeholder: {PLACEHOLDERS[current]}\n")
        current = None

path.write_text("".join(out), encoding="utf-8")
print(f"{len(PLACEHOLDERS)} Platzhalter eingefügt.")
