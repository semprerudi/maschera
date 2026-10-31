<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Design-Tokens

Quelle: `app/static/maschera.css`. Die Bedeutung steht in [11_design.md](../11_design.md).

## Tokens

110 Tokens, 78 davon im dunklen Thema anders.

| Token | Hell | Dunkel |
|---|---|---|
| `--skala` | `1` | `1` |
| `--textgroesse` | `0.84rem` | `0.84rem` |
| `--textschrift` | `var(--font-body)` | `var(--font-body)` |
| `--ui-schrift` | `var(--font-body)` | `var(--font-body)` |
| `--ui-heading` | `var(--font-heading)` | `var(--font-heading)` |
| `--color-bg` | `oklch(0.972 0.004 85)` | `oklch(0.19 0.006 85)` |
| `--color-surface` | `oklch(0.95 0.004 85)` | `oklch(0.215 0.006 85)` |
| `--color-text` | `oklch(0.24 0.01 85)` | `oklch(0.93 0.006 85)` |
| `--color-accent` | `oklch(0.45 0.1 155)` | `oklch(0.76 0.1 155)` |
| `--color-divider` | `color-mix(in srgb, var(--color-text) 16%, transparent)` | `color-mix(in srgb, #ece9e3 16%, transparent)` |
| `--color-neutral-100` | `oklch(0.985 0.003 85)` | `oklch(0.215 0.006 85)` |
| `--color-neutral-200` | `oklch(0.95 0.004 85)` | `oklch(0.26 0.007 85)` |
| `--color-neutral-300` | `oklch(0.91 0.005 85)` | `oklch(0.32 0.008 85)` |
| `--color-neutral-400` | `oklch(0.86 0.006 85)` | `oklch(0.38 0.008 85)` |
| `--color-neutral-500` | `oklch(0.74 0.008 85)` | `oklch(0.5 0.008 85)` |
| `--color-neutral-600` | `oklch(0.56 0.01 85)` | `oklch(0.64 0.008 85)` |
| `--color-neutral-700` | `oklch(0.45 0.01 85)` | `oklch(0.76 0.008 85)` |
| `--color-neutral-800` | `oklch(0.34 0.01 85)` | `oklch(0.86 0.007 85)` |
| `--color-neutral-900` | `oklch(0.26 0.01 85)` | `oklch(0.93 0.006 85)` |
| `--color-accent-100` | `oklch(0.955 0.025 155)` | `oklch(0.28 0.04 155);  --color-accent-600: oklch(0.74 0.1 155);  --color-accent-700: oklch(0.8 0.09 155);  --color-accent-800: oklch(0.88 0.06 155);  --color-accent-2-100: oklch(0.28 0.04 155);  --color-accent-2-800: oklch(0.88 0.06 155)` |
| `--color-accent-600` | `oklch(0.48 0.1 155)` | `oklch(0.48 0.1 155)` |
| `--color-accent-700` | `oklch(0.4 0.09 155)` | `oklch(0.4 0.09 155)` |
| `--color-accent-800` | `oklch(0.32 0.07 155)` | `oklch(0.32 0.07 155)` |
| `--color-accent-2-100` | `oklch(0.955 0.025 155)` | `oklch(0.955 0.025 155)` |
| `--color-accent-2-800` | `oklch(0.32 0.07 155)` | `oklch(0.32 0.07 155)` |
| `--font-marke` | `"Barlow Condensed", "Arial Narrow", sans-serif` | `"Barlow Condensed", "Arial Narrow", sans-serif` |
| `--font-heading` | `"IBM Plex Sans", system-ui, sans-serif` | `"IBM Plex Sans", system-ui, sans-serif` |
| `--font-heading-weight` | `600` | `600` |
| `--font-body` | `"IBM Plex Sans", system-ui, sans-serif` | `"IBM Plex Sans", system-ui, sans-serif` |
| `--font-mono` | `"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace` | `"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace` |
| `--space-1` | `0.2125rem` | `0.2125rem` |
| `--space-2` | `0.425rem` | `0.425rem` |
| `--space-3` | `0.6375rem` | `0.6375rem` |
| `--space-4` | `0.85rem` | `0.85rem` |
| `--radius-md` | `4px` | `4px` |
| `--radius-karte` | `12px` | `12px` |
| `--radius-feld` | `8px` | `8px` |
| `--radius-pille` | `6px` | `6px` |
| `--radius-lg` | `7px` | `7px` |
| `--shadow-sm` | `0 1px 2px color-mix(in srgb, #2b2b2d 14%, transparent)` | `0 1px 2px color-mix(in srgb, #000000 45%, transparent)` |
| `--shadow-md` | `0 3px 10px color-mix(in srgb, #2b2b2d 16%, transparent)` | `0 3px 10px color-mix(in srgb, #000000 50%, transparent)` |
| `--shadow-lg` | `0 12px 32px color-mix(in srgb, #2b2b2d 22%, transparent)` | `0 12px 32px color-mix(in srgb, #000000 58%, transparent)` |
| `--gr-flaeche` | `oklch(0.55 0.12 155)` | `oklch(0.62 0.13 155);  --gr-flaeche2: oklch(0.56 0.12 155);  --gr-schrift: oklch(0.78 0.1 155);  --gr-kante: oklch(0.62 0.12 155);  --bx-flaeche: oklch(0.7 0.14 38);  --bx-schrift: oklch(0.8 0.11 38);  --bx-kante-stark: oklch(0.68 0.13 38);  --bx-aus-schrift: oklch(0.55 0.038 38)` |
| `--gr-flaeche2` | `oklch(0.48 0.11 155)` | `oklch(0.48 0.11 155)` |
| `--gr-schrift` | `oklch(0.42 0.08 155)` | `oklch(0.42 0.08 155)` |
| `--gr-kante` | `oklch(0.5 0.1 155)` | `oklch(0.5 0.1 155)` |
| `--gr-hell` | `oklch(0.6 0.13 155)` | `oklch(0.72 0.13 155)` |
| `--gr-matt` | `oklch(0.75 0.07 155)` | `oklch(0.55 0.08 155)` |
| `--gr-grund` | `oklch(0.962 0.02 155)` | `oklch(0.25 0.03 155)` |
| `--gr-grund2` | `oklch(0.92 0.04 155)` | `oklch(0.3 0.045 155)` |
| `--gr-grund3` | `oklch(0.98 0.01 155)` | `oklch(0.22 0.02 155)` |
| `--haupt-flaeche` | `oklch(0.42 0.09 155)` | `oklch(0.5 0.1 155)` |
| `--haupt-tief` | `oklch(0.36 0.08 155)` | `oklch(0.44 0.09 155)` |
| `--test-gelb` | `oklch(0.92 0.12 95)` | `oklch(0.42 0.09 95)` |
| `--beispiel-grund` | `oklch(0.97 0.06 95)` | `oklch(0.32 0.05 95)` |
| `--beispiel-kante` | `oklch(0.86 0.09 90)` | `oklch(0.45 0.07 90)` |
| `--beispiel-tief` | `oklch(0.94 0.08 95)` | `oklch(0.36 0.06 95)` |
| `--lupe` | `url("lupe.svg")` | `url("lupe.svg")` |
| `--bx-schrift` | `oklch(0.48 0.13 45)` | `oklch(0.48 0.13 45)` |
| `--bx-flaeche` | `oklch(0.5 0.14 42)` | `oklch(0.5 0.14 42)` |
| `--bx-kante-stark` | `oklch(0.55 0.13 45)` | `oklch(0.55 0.13 45)` |
| `--bx-dunkel` | `oklch(0.44 0.13 42)` | `oklch(0.62 0.13 38)` |
| `--bx-tief` | `oklch(0.44 0.14 42)` | `oklch(0.76 0.13 38)` |
| `--bx-dunkel2` | `oklch(0.44 0.13 42)` | `oklch(0.62 0.13 38)` |
| `--bx-matt` | `oklch(0.58 0.09 38)` | `oklch(0.68 0.08 38)` |
| `--bx-matt2` | `oklch(0.64 0.07 38)` | `oklch(0.6 0.07 38)` |
| `--bx-matt3` | `oklch(0.7 0.07 38)` | `oklch(0.55 0.06 38)` |
| `--bx-aus` | `oklch(0.74 0.05 38)` | `oklch(0.5 0.05 38)` |
| `--bx-kante` | `oklch(0.8 0.07 38)` | `oklch(0.52 0.08 38)` |
| `--bx-kante-hell` | `oklch(0.84 0.05 38)` | `oklch(0.45 0.06 38)` |
| `--bx-kante2` | `oklch(0.88 0.038 38)` | `oklch(0.36 0.05 38)` |
| `--bx-grund` | `oklch(0.962 0.026 38)` | `oklch(0.235 0.036 38)` |
| `--bx-grund4` | `oklch(0.982 0.012 38)` | `oklch(0.21 0.02 38)` |
| `--bx-grund5` | `oklch(0.965 0.024 38)` | `oklch(0.24 0.032 38)` |
| `--bx-aus-schrift` | `oklch(0.66 0.038 38)` | `oklch(0.66 0.038 38)` |
| `--bx-aus-flaeche` | `oklch(0.9 0.026 38)` | `oklch(0.3 0.026 38)` |
| `--bx-aus-kante` | `oklch(0.86 0.038 38)` | `oklch(0.36 0.038 38)` |
| `--bx-loeschen` | `oklch(0.55 0.17 25)` | `oklch(0.68 0.16 25)` |
| `--bx-loeschen-kante` | `oklch(0.48 0.16 25)` | `oklch(0.6 0.15 25)` |
| `--bx-senden-aus` | `oklch(0.87 0.045 35)` | `oklch(0.3 0.026 38)` |
| `--bx-senden-aus-kante` | `oklch(0.83 0.055 35)` | `oklch(0.36 0.038 38)` |
| `--schatten-grund` | `oklch(0.24 0.01 85)` | `#000000` |
| `--manuell` | `oklch(0.45 0.15 300)` | `oklch(0.75 0.12 300)` |
| `--muster` | `oklch(0.68 0.08 250)` | `oklch(0.68 0.08 250)` |
| `--papier` | `#fff` | `oklch(0.235 0.007 85)` |
| `--auf-farbe` | `#fff` | `#f4f2ee` |
| `--auf-hinaus` | `#fff` | `oklch(0.2 0.02 50)` |
| `--auf-haupt` | `#fff` | `oklch(0.2 0.006 85)` |
| `--ph-gruppe-person-fl` | `oklch(0.95 0.035 300);  --ph-gruppe-person-ra: oklch(0.95 0.035 300);  --ph-gruppe-person-sc: oklch(0.42 0.12 300)` | `oklch(0.33 0.06 300);  --ph-gruppe-person-ra: oklch(0.33 0.06 300);  --ph-gruppe-person-sc: oklch(0.85 0.1 300)` |
| `--ph-gruppe-origin-fl` | `oklch(0.95 0.035 340);  --ph-gruppe-origin-ra: oklch(0.95 0.035 340);  --ph-gruppe-origin-sc: oklch(0.42 0.12 340)` | `oklch(0.33 0.06 340);  --ph-gruppe-origin-ra: oklch(0.33 0.06 340);  --ph-gruppe-origin-sc: oklch(0.85 0.1 340)` |
| `--ph-gruppe-address-fl` | `oklch(0.95 0.035 195);  --ph-gruppe-address-ra: oklch(0.95 0.035 195);  --ph-gruppe-address-sc: oklch(0.42 0.12 195)` | `oklch(0.33 0.06 195);  --ph-gruppe-address-ra: oklch(0.33 0.06 195);  --ph-gruppe-address-sc: oklch(0.85 0.1 195)` |
| `--ph-gruppe-contact-fl` | `oklch(0.95 0.035 250);  --ph-gruppe-contact-ra: oklch(0.95 0.035 250);  --ph-gruppe-contact-sc: oklch(0.42 0.12 250)` | `oklch(0.33 0.06 250);  --ph-gruppe-contact-ra: oklch(0.33 0.06 250);  --ph-gruppe-contact-sc: oklch(0.85 0.1 250)` |
| `--ph-gruppe-official-fl` | `oklch(0.95 0.035 20);  --ph-gruppe-official-ra: oklch(0.95 0.035 20);  --ph-gruppe-official-sc: oklch(0.42 0.12 20)` | `oklch(0.33 0.06 20);  --ph-gruppe-official-ra: oklch(0.33 0.06 20);  --ph-gruppe-official-sc: oklch(0.85 0.1 20)` |
| `--ph-gruppe-finance-fl` | `oklch(0.95 0.035 110);  --ph-gruppe-finance-ra: oklch(0.95 0.035 110);  --ph-gruppe-finance-sc: oklch(0.42 0.12 110)` | `oklch(0.33 0.06 110);  --ph-gruppe-finance-ra: oklch(0.33 0.06 110);  --ph-gruppe-finance-sc: oklch(0.85 0.1 110)` |
| `--ph-gruppe-health-fl` | `oklch(0.95 0.035 165);  --ph-gruppe-health-ra: oklch(0.95 0.035 165);  --ph-gruppe-health-sc: oklch(0.42 0.12 165)` | `oklch(0.33 0.06 165);  --ph-gruppe-health-ra: oklch(0.33 0.06 165);  --ph-gruppe-health-sc: oklch(0.85 0.1 165)` |
| `--ph-gruppe-process-fl` | `oklch(0.95 0.035 75);  --ph-gruppe-process-ra: oklch(0.95 0.035 75);  --ph-gruppe-process-sc: oklch(0.42 0.12 75)` | `oklch(0.33 0.06 75);  --ph-gruppe-process-ra: oklch(0.33 0.06 75);  --ph-gruppe-process-sc: oklch(0.85 0.1 75)` |
| `--ph-gruppe-plain-fl` | `oklch(0.95 0.006 85);  --ph-gruppe-plain-ra: oklch(0.95 0.006 85);  --ph-gruppe-plain-sc: oklch(0.42 0.01 85)` | `oklch(0.33 0.006 85);  --ph-gruppe-plain-ra: oklch(0.33 0.006 85);  --ph-gruppe-plain-sc: oklch(0.85 0.01 85)` |
| `--ph-tag-fullname-fl` | `oklch(0.95 0.035 300);  --ph-tag-fullname-ra: oklch(0.95 0.035 300);  --ph-tag-fullname-sc: oklch(0.42 0.12 300)` | `oklch(0.33 0.06 300);  --ph-tag-fullname-ra: oklch(0.33 0.06 300);  --ph-tag-fullname-sc: oklch(0.85 0.1 300)` |
| `--ph-tag-city-fl` | `oklch(0.95 0.035 195);  --ph-tag-city-ra: oklch(0.95 0.035 195);  --ph-tag-city-sc: oklch(0.42 0.12 195)` | `oklch(0.33 0.06 195);  --ph-tag-city-ra: oklch(0.33 0.06 195);  --ph-tag-city-sc: oklch(0.85 0.1 195)` |
| `--ph-tag-street-fl` | `oklch(0.95 0.035 195);  --ph-tag-street-ra: oklch(0.95 0.035 195);  --ph-tag-street-sc: oklch(0.42 0.12 195)` | `oklch(0.33 0.06 195);  --ph-tag-street-ra: oklch(0.33 0.06 195);  --ph-tag-street-sc: oklch(0.85 0.1 195)` |
| `--ph-tag-date-fl` | `oklch(0.95 0.035 75);  --ph-tag-date-ra: oklch(0.95 0.035 75);  --ph-tag-date-sc: oklch(0.42 0.12 75)` | `oklch(0.33 0.06 75);  --ph-tag-date-ra: oklch(0.33 0.06 75);  --ph-tag-date-sc: oklch(0.85 0.1 75)` |
| `--ph-tag-email-fl` | `oklch(0.95 0.035 250);  --ph-tag-email-ra: oklch(0.95 0.035 250);  --ph-tag-email-sc: oklch(0.42 0.12 250)` | `oklch(0.33 0.06 250);  --ph-tag-email-ra: oklch(0.33 0.06 250);  --ph-tag-email-sc: oklch(0.85 0.1 250)` |
| `--ph-tag-phone-fl` | `oklch(0.95 0.035 250);  --ph-tag-phone-ra: oklch(0.95 0.035 250);  --ph-tag-phone-sc: oklch(0.42 0.12 250)` | `oklch(0.33 0.06 250);  --ph-tag-phone-ra: oklch(0.33 0.06 250);  --ph-tag-phone-sc: oklch(0.85 0.1 250)` |
| `--ph-tag-org-fl` | `oklch(0.95 0.035 75);  --ph-tag-org-ra: oklch(0.95 0.035 75);  --ph-tag-org-sc: oklch(0.42 0.12 75)` | `oklch(0.33 0.06 75);  --ph-tag-org-ra: oklch(0.33 0.06 75);  --ph-tag-org-sc: oklch(0.85 0.1 75)` |
| `--ph-tag-case_id-fl` | `oklch(0.95 0.035 75);  --ph-tag-case_id-ra: oklch(0.95 0.035 75);  --ph-tag-case_id-sc: oklch(0.42 0.12 75)` | `oklch(0.33 0.06 75);  --ph-tag-case_id-ra: oklch(0.33 0.06 75);  --ph-tag-case_id-sc: oklch(0.85 0.1 75)` |
| `--ph-tag-ahvn13-fl` | `oklch(0.95 0.035 20);  --ph-tag-ahvn13-ra: oklch(0.95 0.035 20);  --ph-tag-ahvn13-sc: oklch(0.42 0.12 20)` | `oklch(0.33 0.06 20);  --ph-tag-ahvn13-ra: oklch(0.33 0.06 20);  --ph-tag-ahvn13-sc: oklch(0.85 0.1 20)` |
| `--ph-rest-1-fl` | `oklch(0.95 0.035 230);  --ph-rest-1-ra: oklch(0.95 0.035 230);  --ph-rest-1-sc: oklch(0.42 0.12 230)` | `oklch(0.33 0.06 230);  --ph-rest-1-ra: oklch(0.33 0.06 230);  --ph-rest-1-sc: oklch(0.85 0.1 230)` |
| `--ph-rest-2-fl` | `oklch(0.95 0.035 0);  --ph-rest-2-ra: oklch(0.95 0.035 0);  --ph-rest-2-sc: oklch(0.42 0.12 0)` | `oklch(0.33 0.06 0);  --ph-rest-2-ra: oklch(0.33 0.06 0);  --ph-rest-2-sc: oklch(0.85 0.1 0)` |
| `--ph-rest-3-fl` | `oklch(0.95 0.035 140);  --ph-rest-3-ra: oklch(0.95 0.035 140);  --ph-rest-3-sc: oklch(0.42 0.12 140)` | `oklch(0.33 0.06 140);  --ph-rest-3-ra: oklch(0.33 0.06 140);  --ph-rest-3-sc: oklch(0.85 0.1 140)` |
| `--ph-rest-4-fl` | `oklch(0.95 0.035 60);  --ph-rest-4-ra: oklch(0.95 0.035 60);  --ph-rest-4-sc: oklch(0.42 0.12 60)` | `oklch(0.33 0.06 60);  --ph-rest-4-ra: oklch(0.33 0.06 60);  --ph-rest-4-sc: oklch(0.85 0.1 60)` |

## Abfragen

- `@container teilkopf (max-width: 26rem)`
- `@media (max-width: 81.24em), (max-height: 44em)`
- `@media (prefers-color-scheme: dark)`
- `@container einstfuss (max-width: 18rem)`
- `@container einstfuss (max-width: 30rem)`
- `@container fuss (max-width: 13rem)`
- `@media (max-width: 30em)`
- `@media (max-width: 33em)`
- `@media (max-width: 39.99em)`
- `@media (max-width: 81.24em), (max-height: 44em)`
- `@container feld (max-width: 24rem)`
- `@container fuss (max-width: 22rem)`
- `@container fuss (max-width: 9rem)`
- `@container teilkopf (max-width: 20rem)`
- `@container teilkopf (max-width: 25rem)`
- `@media (max-width: 20em)`
- `@media (max-width: 30em)`
- `@media (max-width: 33em)`
- `@media (max-width: 40em)`
- `@media (max-width: 81.24em), (max-height: 44em)`
- `@media (prefers-color-scheme: dark)`
- `@media (prefers-reduced-motion: reduce)`
