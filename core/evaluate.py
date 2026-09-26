"""Auswertung (SPEC §4, §11).

**Die wichtigste Zahl ist nicht F1.** Micro-F1 mittelt über alle Tags und
belohnt gute Leistung auf häufigen, harmlosen Tags. Für einen Datenschutzfilter
zählt etwas anderes: *Wie viel Personendatum erreicht das Sprachmodell?*

Deshalb steht hier die **Leckrate** obenan — der Anteil der Entitäten, die
maskiert werden müssten und es nicht wurden, gewichtet nach Schwere:

    bsPD ungeschützt        schwer
    direkte Identifikatoren schwer     (AHVN13, FULLNAME, IBAN …)
    Quasi-Identifikatoren   mittel     (AGE, SEX, CITY …)
    Kontexttags             leicht

Ein Modell mit F1 0.98 kann trotzdem untauglich sein, wenn die fehlenden 2 %
ausgerechnet AHV-Nummern sind. Umgekehrt ist ein Fehler auf `CANTON` egal —
das Tag maskiert ohnehin nicht.

Zweite Zahl: **Übermaskierung**. Ein Filter, der zu viel schwärzt, macht das
Dokument für das Sprachmodell unbrauchbar. Wird getrennt ausgewiesen, weil
die Abwägung eine fachliche Entscheidung ist und keine technische.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.masking import Span

# Schwere eines ungeschützten Lecks. Direkte Identifikatoren und besonders
# schützenswerte Daten wiegen am schwersten.
SEVERITY_DIRECT = 3.0
SEVERITY_QUASI = 1.0
SEVERITY_CONTEXT = 0.2

DIRECT = {
    "AHVN13", "UID", "IBAN", "QR_REFERENCE", "CREDITCARD", "GLN",
    "INSURANCE_CARD", "IDDOC", "ZSR_RCC", "PATIENT_ID", "EMAIL", "PHONE",
    "PLATE", "FULLNAME", "EGID", "EWID", "STREET", "CASE_ID",
    "SOCIAL_INSURANCE", "INSURANCE_POLICY",
}
QUASI = {
    "GIVENNAME", "DATE", "BUILDINGNUM", "ZIPCODE", "CITY", "AGE", "SEX",
    "MARITALSTATUS", "RELIGION", "NATIONALITY", "PARCEL", "AMOUNT",
    "PERMIT_TYPE", "RESIDENCE_STATUS", "MUNICIPALITY_ID", "HEALTHCARE_ORG",
    "IPADDRESS",
}


def severity(tag: str, bspd: bool = False) -> float:
    base = (SEVERITY_DIRECT if tag in DIRECT
            else SEVERITY_QUASI if tag in QUASI
            else SEVERITY_CONTEXT)
    return base * (1.5 if bspd else 1.0)


@dataclass
class TagScore:
    tag: str
    gold: int = 0
    pred: int = 0
    exact: int = 0
    partial: int = 0   # überlappt, aber Grenzen daneben
    missed: int = 0    # NICHT als dieses Tag erkannt — sagt nichts über ein Leck
    leaked: int = 0    # Gold-Spannen mit ungeschuetzten Zeichen — das echte Leck
    leak_weight: float = 0.0

    @property
    def precision(self) -> float:
        return self.exact / self.pred if self.pred else 0.0

    @property
    def recall(self) -> float:
        return self.exact / self.gold if self.gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass
class Report:
    per_tag: dict[str, TagScore] = field(default_factory=dict)
    leaked: list[tuple[str, str]] = field(default_factory=list)
    over: list[tuple[str, str]] = field(default_factory=list)
    leak_weight: float = 0.0
    total_weight: float = 0.0
    # Bewusst im Klartext gelassen (`--ohne TAG`). Diese Spannen sind KEINE
    # Lecks — aber sie duerfen auch nicht spurlos verschwinden. Wer abschaltet,
    # was leckt, bekaeme sonst eine bessere Leckrate, und niemand saehe warum.
    # Ein Mass, das sich durch eine Einstellung verbessern laesst, misst die
    # Einstellung.
    im_klartext: list[tuple[str, str]] = field(default_factory=list)
    klartext_tags: tuple[str, ...] = ()

    @property
    def leak_rate(self) -> float:
        """Gewichteter Anteil ungeschützter Personendaten. Kleiner ist besser."""
        return self.leak_weight / self.total_weight if self.total_weight else 0.0

    @property
    def micro_f1(self) -> float:
        e = sum(s.exact for s in self.per_tag.values())
        g = sum(s.gold for s in self.per_tag.values())
        p = sum(s.pred for s in self.per_tag.values())
        prec = e / p if p else 0.0
        rec = e / g if g else 0.0
        return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def evaluate(
    cases: list[tuple[str, list[Span], list[Span]]],
    pack,
    partial_credit: bool = True,
    excluded: set[str] | None = None,
) -> Report:
    """`cases` sind Tripel (Text, Gold-Spannen, vorhergesagte Spannen).

    `excluded` — Tags, die bewusst im Klartext bleiben (`--ohne TAG`). Sie
    zaehlen nicht als Leck, werden aber getrennt ausgewiesen. Die Auswertung
    muss mit derselben Einstellung laufen wie die Kette, sonst misst sie eine
    Verarbeitung, die es nicht gab.
    """
    actions = dict(pack.get_actions())
    excluded = set(excluded or ())
    for tag in excluded:
        actions[tag] = "tag_only"
    bspd = {t.tag: t.bspd for t in pack.get_tags()}
    report = Report()
    report.klartext_tags = tuple(sorted(excluded))

    def score(tag: str) -> TagScore:
        return report.per_tag.setdefault(tag, TagScore(tag))

    for text, gold, pred in cases:
        used: set[int] = set()

        for g in gold:
            s = score(g.tag)
            s.gold += 1
            w = severity(g.tag, bspd.get(g.tag, False))
            # Nur maskierte Tags können lecken — tag_only bleibt ohnehin lesbar
            masks = actions.get(g.tag) == "mask"
            if masks:
                report.total_weight += w
            elif g.tag in excluded:
                report.im_klartext.append((g.tag, g.value(text)))

            # --- Leck: rein zeichenbasiert, TAGUNABHAENGIG ------------------
            #
            # Ein Leck ist, was im KLARTEXT stehen bleibt. Ob der Filter
            # "KL-2023-4471" als PATIENT_ID oder als CASE_ID erkannt hat, ist
            # dem Datenschutz egal — beide maskieren, der Wert ist weg. Ein
            # Datenschutzmass, das Etikettierfehler mitzaehlt, misst nicht mehr,
            # was es soll. Tagtreue steht in Precision und Recall.
            if masks:
                abgedeckt = bytearray(g.end - g.start)
                for p in pred:
                    if actions.get(p.tag) != "mask":
                        continue
                    a, b = max(p.start, g.start), min(p.end, g.end)
                    for k in range(a - g.start, b - g.start):
                        abgedeckt[k] = 1
                # Leerraum zaehlt nicht: ein nicht abgedecktes Leerzeichen zwischen
                # zwei maskierten Teilen ist kein Personendatum.
                wert = text[g.start:g.end]
                bedeutsam = [i for i, c in enumerate(wert) if not c.isspace()]
                offen = sum(1 for i in bedeutsam if not abgedeckt[i])
                if offen:
                    anteil = w * offen / max(1, len(bedeutsam))
                    report.leak_weight += anteil
                    s.leaked += 1
                    s.leak_weight += anteil
                    if offen == len(bedeutsam):
                        report.leaked.append((g.tag, text[g.start:g.end]))
                    else:
                        rest = "".join(
                            wert[i] for i in bedeutsam if not abgedeckt[i]
                        )
                        report.leaked.append((g.tag, f"{text[g.start:g.end]} -> {rest!r} offen"))

            # --- Tagtreue: exakte Uebereinstimmung fuer Precision/Recall ----
            exact = next(
                (i for i, p in enumerate(pred)
                 if i not in used and p.tag == g.tag
                 and p.start == g.start and p.end == g.end),
                None,
            )
            if exact is not None:
                used.add(exact)
                s.exact += 1
                continue

            loose = next(
                (i for i, p in enumerate(pred)
                 if i not in used and p.tag == g.tag
                 and p.start < g.end and g.start < p.end),
                None,
            )
            if loose is not None and partial_credit:
                used.add(loose)
                s.partial += 1
                continue

            s.missed += 1

        for i, p in enumerate(pred):
            score(p.tag).pred += 1
            if i not in used and p.tag not in excluded:
                # Ein bewusst offenes Tag kann nicht uebermaskieren — es maskiert ja
                # nichts. Die Leckseite und die Uebermaskierungsseite muessen es beide
                # wissen.
                report.over.append((p.tag, text[p.start:p.end]))

    return report


def format_report(report: Report, top: int = 8) -> str:
    lines = []
    # Die absolute Zahl gehoert NEBEN den Prozentwert. Ein wachsendes
    # Testset verduennt seine eigene Leckrate: dieselben drei Lecks sehen bei
    # zehn Dokumenten harmlos aus und bei zweien alarmierend.
    if report.klartext_tags:
        lines.append("BEWUSST IM KLARTEXT: " + ", ".join(report.klartext_tags)
                     + f"  ({len(report.im_klartext)} Spannen)")
        lines.append("  Diese zaehlen NICHT in die Leckrate. Sie stehen im"
                     " Dokument lesbar da.")
        lines.append("")
    gold_gesamt = sum(s.gold for s in report.per_tag.values())
    lines.append(f"Leckrate (gewichtet):   {100 * report.leak_rate:6.2f} %"
                 f"   ({len(report.leaked)} Leck(s) bei {gold_gesamt} Goldspannen)")
    lines.append(f"Micro-F1:               {report.micro_f1:6.3f}")
    lines.append(f"Uebermaskierungen:      {len(report.over)}")
    lines.append("")
    lines.append(f"{'Tag':<20}{'Gold':>6}{'Prec':>8}{'Rec':>8}{'F1':>8}"
                 f"{'Teil':>7}{'Verfehlt':>10}{'Leck':>7}")
    for tag, s in sorted(report.per_tag.items(),
                         key=lambda kv: (-kv[1].leaked, -kv[1].missed, kv[0])):
        if not s.gold and not s.pred:
            continue
        lines.append(f"{tag:<20}{s.gold:>6}{s.precision:>8.3f}{s.recall:>8.3f}"
                     f"{s.f1:>8.3f}{s.partial:>7}{s.missed:>10}{s.leaked:>7}")
    lines.append("")
    lines.append("  Verfehlt = nicht als DIESES Tag erkannt. Kein Leck, solange ein")
    lines.append("             anderes maskierendes Tag denselben Text abdeckt.")
    lines.append("  Leck     = Zeichen blieben im Klartext. Nur diese Spalte zaehlt")
    lines.append("             in die Leckrate oben.")
    if report.leaked:
        lines.append("")
        lines.append(f"Ungeschuetzt geblieben (erste {top}):")
        for tag, value in report.leaked[:top]:
            lines.append(f"   {tag:<20} {value!r}")
    return "\n".join(lines)
