"""Ausrichtung: Zeichenspannen <-> BIO-Labels auf Subword-Ebene (SPEC §11).

Diese Datei ist bewusst **tokenizer-unabhaengig**. Sie arbeitet auf dem
`offset_mapping`, das jeder schnelle HuggingFace-Tokenizer liefert:
eine Liste von (start, end)-Paaren je Token. Damit ist die Ausrichtung ohne
Modell, ohne torch und ohne Netzzugang pruefbar — und genau hier stecken die
Fehler, die man sonst erst nach Stunden auf der GPU bemerkt.

Der gefaehrlichste Fehler ist nicht ein Absturz, sondern eine stille
Verschiebung: sitzen die Labels systematisch ein Token daneben, sinkt die
Verlustkurve trotzdem und das Modell lernt Unsinn, der plausibel aussieht.
Deshalb gibt es `verify_roundtrip`.

Randfaelle, die hier entschieden werden:

  Sonderzeichen        Offset (0, 0) -> Label -100 (von der Verlustfunktion
                       ignoriert), nicht "O". Sonst lernt das Modell, auf
                       [CLS] "O" vorherzusagen, und das verzerrt die Metrik.

  Entitaetsgrenze      Ein Token, das teilweise in einer Entitaet liegt, ist
  mitten im Token      ein Grenzkonflikt. Er wird GEZAEHLT, nicht stillschweigend
                       aufgeloest: Haeufen sich Konflikte, stimmt etwas mit der
                       Tokenisierung oder den Spannen nicht.

  Leerraum-Token       Manche Tokenizer geben Offsets, die fuehrende Leerzeichen
                       einschliessen. Wird beim Vergleich abgezogen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.masking import Span

IGNORE_INDEX = -100  # PyTorch-Konvention: von der Verlustfunktion ausgenommen


@dataclass
class Alignment:
    labels: list[str]           # je Token: "O", "B-TAG", "I-TAG" oder ""
    ids: list[int]              # je Token: Index in der Labelliste oder -100
    boundary_conflicts: int = 0
    unlabelled_spans: list[Span] = field(default_factory=list)


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Fuehrenden und nachfolgenden Leerraum aus einem Offset entfernen."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def align(
    text: str,
    spans: list[Span],
    offsets: list[tuple[int, int]],
    label_list: list[str] | tuple[str, ...],
) -> Alignment:
    """Zeichenspannen auf Tokenlabels abbilden.

    `offsets` ist das `offset_mapping` des Tokenizers, `label_list` die
    eingefrorene BIO-Reihenfolge aus dem Pack.
    """
    index = {label: i for i, label in enumerate(label_list)}
    ordered = sorted(spans, key=lambda s: (s.start, s.end))

    labels: list[str] = []
    ids: list[int] = []
    conflicts = 0
    covered: set[int] = set()

    for token_start, token_end in offsets:
        # Sonderzeichen: [CLS], [SEP], Padding
        if token_end <= token_start:
            labels.append("")
            ids.append(IGNORE_INDEX)
            continue

        ts, te = _trim(text, token_start, token_end)
        if ts >= te:
            # Reines Leerraum-Token. SentencePiece erzeugt solche staendig:
            # "CHF 1'250.00" wird zu ['▁CHF', '▁', '1', "'", ...] — das nackte
            # '▁' traegt nur das Trennzeichen.
            #
            # Liegt es INNERHALB einer Entitaet, darf es nicht 'O' werden, sonst
            # zerfaellt "CHF 1'250.00" in zwei Spannen und das Modell lernt, dass
            # ein Leerzeichen den Betrag beendet. Gemessen: 368 von 400
            # Beispielen betroffen.
            inner = next(
                (i for i, span in enumerate(ordered)
                 if span.start <= token_start and token_end <= span.end
                 and i in covered),
                None,
            )
            if inner is not None:
                label = "I-" + ordered[inner].tag
                labels.append(label)
                ids.append(index[label])
            else:
                labels.append("O")
                ids.append(index["O"])
            continue

        hit = None
        for i, span in enumerate(ordered):
            if ts < span.end and span.start < te:
                hit = (i, span)
                # Token ragt ueber die Entitaetsgrenze hinaus
                if ts < span.start or te > span.end:
                    conflicts += 1
                break

        if hit is None:
            labels.append("O")
            ids.append(index["O"])
            continue

        i, span = hit
        prefix = "B-" if i not in covered else "I-"
        covered.add(i)
        label = prefix + span.tag
        if label not in index:
            # Tag nicht im Labelvertrag — lauter Fehler statt stiller Verlust
            raise KeyError(
                f"Label {label!r} steht nicht im Labelvertrag. "
                f"Passt der Datensatz zum Pack?"
            )
        labels.append(label)
        ids.append(index[label])

    missing = [s for i, s in enumerate(ordered) if i not in covered]
    return Alignment(labels, ids, conflicts, missing)


# Zeichen, die nie das Ende einer Entitaet bilden. Bewusst SEHR knapp:
#   "."  bleibt drin  -> "Fr." und "St." sind legitime Bestandteile
#   ")"  bleibt drin  -> "Ursy (Montet (Glane))" ist ein echter Heimatort
#   "-"  bleibt drin  -> "CHF 500.--" ist ein echter Betrag
#   '"'  bleibt drin  -> 'Studio "Zen"' und '"Der Bauer" Pius Henke' sind
#                        echte Firmennamen aus Zefix. Schnitt man das
#                        schliessende Anfuehrungszeichen ab, entstuende
#                        [Firma_1]" — ein Zeichen im Klartext unter einem
#                        Platzhalter, der Vollstaendigkeit vortaeuscht.
#
# Grundsatz: Im Zweifel MEHR maskieren. Ein Komma zuviel im Platzhalter ist
# haesslich; ein Zeichen zuwenig ist ein Leck.
_TRAILING = ",;:!?"


def _tighten(text: str, start: int, end: int) -> tuple[int, int]:
    """Nachgestellten Leerraum und eindeutige Trennzeichen abschneiden.

    Straddelt ein Token die Entitaetsgrenze — "3," statt "3" —, ragt das Label
    ueber die Entitaet hinaus. Zur Vorhersagezeit ist nicht bekannt, wo die
    Entitaet endete, aber ein Komma am Schluss ist nie Teil von ihr.
    """
    while end > start and (text[end - 1].isspace() or text[end - 1] in _TRAILING):
        end -= 1
    while start < end and text[start].isspace():
        start += 1
    return start, end


def decode(
    offsets: list[tuple[int, int]],
    labels: list[str],
    text: str | None = None,
) -> list[Span]:
    """BIO-Labels zurueck in Zeichenspannen. Gegenrichtung von `align`.

    Mit `text` werden die Raender nachgezogen (siehe `_tighten`).
    """
    out: list[Span] = []
    current_tag: str | None = None
    start = end = 0

    def flush() -> None:
        nonlocal current_tag
        if not current_tag:
            return
        a, b = (_tighten(text, start, end) if text is not None else (start, end))
        if a < b:
            out.append(Span(current_tag, a, b))
        current_tag = None

    for (ts, te), label in zip(offsets, labels):
        if te <= ts or label == "":
            continue
        if label == "O":
            flush()
            continue
        prefix, _, tag = label.partition("-")
        if prefix == "B" or tag != current_tag:
            flush()
            current_tag, start, end = tag, ts, te
        else:
            end = te

    flush()
    return out


def verify_roundtrip(
    text: str,
    spans: list[Span],
    offsets: list[tuple[int, int]],
    label_list: list[str] | tuple[str, ...],
) -> tuple[bool, list[str]]:
    """align -> decode muss die Ausgangsspannen zurueckgeben.

    Toleriert Randverschiebungen durch Leerraum, aber keine Tag- oder
    Zaehlfehler. Gibt (ok, Problemliste) zurueck.
    """
    a = align(text, spans, offsets, label_list)
    back = decode(offsets, a.labels, text)
    problems: list[str] = []

    if a.unlabelled_spans:
        problems.append(
            f"{len(a.unlabelled_spans)} Spannen ohne Token: "
            f"{[(s.tag, text[s.start:s.end]) for s in a.unlabelled_spans][:3]}"
        )

    want = sorted((s.tag, text[s.start:s.end].strip()) for s in spans)
    got = sorted((s.tag, text[s.start:s.end].strip()) for s in back)
    if want != got:
        only_want = [w for w in want if w not in got][:3]
        only_got = [g for g in got if g not in want][:3]
        problems.append(f"Abweichung — fehlt: {only_want}, zusaetzlich: {only_got}")

    return not problems, problems
