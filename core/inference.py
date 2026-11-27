"""Inferenz: die drei Stufen zusammenführen (SPEC §3, §4).

Das ist das Stück, das aus Modell und Mustern den eigentlichen Filter macht.

Reihenfolge und Vorrang:

  Stufe 1  Prüfsumme. Gültig -> maskieren, auch wenn das Modell schweigt.
           Ungültig -> verwerfen, auch wenn das Modell anschlägt.
           Schlägt alles andere.

  Stufe 2  Regex mit Kontextanker. Vorschlag, kein Vetorecht. Verstärkt einen
           Modelltreffer und kann allein stehen.

  Stufe 3  Modell. Entscheidet über die Schwelle aus dem Fehlerbudget:
           R = 0.30, A = 0.50, P = 0.70 — Recall-first-Tags dürfen schon bei
           geringer Sicherheit maskieren, Precision-first-Tags erst bei hoher.

Das Modell ist **austauschbar**. `Scorer` ist ein Protokoll, kein Import: die
Zusammenführung ist damit ohne ONNX, ohne torch und ohne Gewichte testbar —
und genau hier liegen die Fehler, die man sonst erst im Betrieb sieht.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.masking import MaskResult, Span, mask
from core.recognizers import recognize
from packs.ch.validators.checksums import VALIDATORS


@dataclass(frozen=True)
class Scored:
    tag: str
    start: int
    end: int
    score: float


def fensterzahl(token: int, nutz: int, step: int) -> int:
    """Wie oft die Fensterschleife laeuft — bevor sie laeuft.

    Darauf steht der Fortschrittsbalken der Oberflaeche: nach dem
    Tokenisieren ist die Zahl bekannt, also zeigt der Balken etwas
    Gemessenes und keine Schaetzung.

    Nicht `ceil(token / step)`: die Schleife bricht ab, sobald ein Fenster
    bis ans Ende reicht, und laeuft also seltener, als die einfache Teilung
    sagt. Ein Balken, der ueber 100 % hinauslaeuft, sagt dem Anwender, dass
    hier niemand zaehlt.

    Eine Funktion und nicht zweimal dieselbe Zeile: die Schleife steht in
    BEIDEN Laeufern, und zwei Laeufer duerfen kein unterschiedliches
    Verhalten haben. `tests/test_inference.py` vergleicht sie gegen die
    nachgebaute Schleife.
    """
    if token <= nutz:
        return 1
    return 1 + -(-(token - nutz) // step)


def kopf_paesse(logits, kopf_alt: int | None):
    """Tokenentscheide aus den Logits: (Label-Index, Vertrauen) je Pass.

    Ein Pass: Softmax ueber alle Labels, wie bisher.

    Zwei Paesse, wenn das Modell `kopf_alt` traegt (seit 25.11.2026): die
    ersten `kopf_alt` Labels sind der Kopf eines aelteren Modells, die
    uebrigen wurden angehaengt (`train.py --start-von --nur-kopf`).
      Pass alt: Softmax NUR ueber die alten Labels. Die alten Tags entscheiden
                damit genau wie das Ausgangsmodell, Wert fuer Wert; die neuen
                Labels koennen ihnen keine Wahrscheinlichkeit wegnehmen.
      Pass neu: Softmax ueber «O» und die neuen Labels. Die neuen Tags
                kommen zusaetzlich dazu, sie ersetzen nichts.
    Anlass: in EINER Softmax senkten JOBTITLE und FAMILYROLE die
    Wahrscheinlichkeit alter Labels unter ihre Schwelle, und Lecks
    verschoben sich (ch-v67k, Schwelle 0.6: drei Lecks mehr).

    `logits` ist ein numpy-Feld (Token x Labels). Rueckgabe: Liste von
    (beste Indizes im vollen Labelraum, Vertrauen) als numpy-Felder.
    """
    import numpy as np

    def softmax(x):
        e = np.exp(x - x.max(axis=-1, keepdims=True))
        return e / e.sum(axis=-1, keepdims=True)

    zeilen = np.arange(logits.shape[0])
    n = logits.shape[-1]
    if not kopf_alt or kopf_alt >= n:
        p = softmax(logits)
        b = p.argmax(axis=-1)
        return [(b, p[zeilen, b])]
    alt = softmax(logits[:, :kopf_alt])
    b_alt = alt.argmax(axis=-1)
    idx = np.array([0] + list(range(kopf_alt, n)))
    neu = softmax(logits[:, idx])
    b_neu = neu.argmax(axis=-1)
    return [(b_alt, alt[zeilen, b_alt]), (idx[b_neu], neu[zeilen, b_neu])]


def spannen_aus_paessen(paesse: list[dict], labels, text: str) -> list["Scored"]:
    """Je Pass die Tokenlabels zu Spannen machen und alles zusammenlegen.

    `paesse` ist je Pass ein dict (Offset -> (Label, Vertrauen)). Das
    Vertrauen einer Spanne ist das kleinste der Token, die sie ueberschneiden
    (Begruendung bei den Laeufern). Beide Laeufer rufen dies auf: zwei
    Laeufer, ein Verhalten.
    """
    from core.alignment import decode
    spannen: list[Scored] = []
    for results in paesse:
        geordnet = sorted(results.items())
        off = [k for k, _ in geordnet]
        lab = [v[0] for _, v in geordnet]
        for span in decode(off, lab, text):
            ueber = [v[1] for (a, b), v in geordnet
                     if a < span.end and span.start < b]
            spannen.append(Scored(span.tag, span.start, span.end,
                                  min(ueber) if ueber else 0.0))
    return _rand_saeubern(_zusammenfuegen(spannen, text), text)


# Zeichen, die an den Rand einer Berufs- oder Familienspanne nicht gehoeren
# (Feedback Test 2, 25.11.2026: «(EGBA)», «-/UID» als JOBTITLE). Der Punkt
# am Ende bleibt: «avv.», «Dr.», «Stv.» sind Abkuerzungen.
_RAND_VORN = "([{-/–—«‹\"'„“,;:"
_RAND_HINTEN = ")]}-/–—»›\"'“”,;:"


def _rand_saeubern(spannen: list["Scored"], text: str) -> list["Scored"]:
    """Nur fuer die Tags des zweiten Kopfs: Satzzeichen am Rand abschneiden.

    Eine schliessende Klammer bleibt, wenn die Spanne ihre oeffnende traegt
    («Leiter (a. i.)»). Bleibt weniger als zwei Zeichen oder kein Buchstabe,
    faellt die Spanne weg. Die alten Tags bleiben unberuehrt: dort entscheidet
    weiter allein das Modell, wie vor dem zweiten Kopf.
    """
    aus: list[Scored] = []
    for sp in spannen:
        if sp.tag not in NACHRANG:
            aus.append(sp)
            continue
        a, b = sp.start, sp.end
        while a < b and (text[a] in _RAND_VORN or text[a].isspace()):
            a += 1
        while a < b and (text[b - 1] in _RAND_HINTEN or text[b - 1].isspace()):
            if text[b - 1] == ")" and "(" in text[a:b - 1]:
                break
            b -= 1
        wert = text[a:b]
        if len(wert) < 2 or not any(c.isalpha() for c in wert):
            continue
        aus.append(sp if (a, b) == (sp.start, sp.end)
                   else Scored(sp.tag, a, b, sp.score))
    return aus


# Tags, deren Teile zusammengehoeren, wenn sie nur Leerraum oder ein
# Bindestrich trennt: «consigliere» + «federale» ist EIN Titel. Das Modell
# zerlegte mehrteilige Titel (Pruefset berufe, 25.11.2026: 89 Teiltreffer).
# Nicht fuer Namen oder Orte: «Bern Zuerich» in einer Liste sind zwei.
ZUSAMMENHAENGEND = frozenset({"JOBTITLE", "FAMILYROLE"})

# Angehaengte Tags des zweiten Kopfs: in `merge` nachrangig (siehe dort).
NACHRANG = frozenset({"JOBTITLE", "FAMILYROLE"})


def _zusammenfuegen(spannen: list["Scored"], text: str) -> list["Scored"]:
    aus: list[Scored] = []
    for sp in sorted(spannen, key=lambda x: (x.start, x.end)):
        vor = aus[-1] if aus else None
        if (vor is not None and sp.tag == vor.tag
                and sp.tag in ZUSAMMENHAENGEND and vor.end <= sp.start
                and text[vor.end:sp.start].strip(" -\t") == ""
                and "\n" not in text[vor.end:sp.start]):
            aus[-1] = Scored(vor.tag, vor.start, sp.end,
                             min(vor.score, sp.score))
        else:
            aus.append(sp)
    return aus


class Scorer(Protocol):
    """Alles, was Zeichenspannen mit Wahrscheinlichkeit liefert."""

    def score(self, text: str) -> list[Scored]: ...


@dataclass
class FilterResult:
    masked: str
    dictionary: dict[str, str]
    spans: list[Span]
    dropped: list[tuple[str, str, str]]  # (Tag, Wert, Grund)
    erweitert: int = 0   # Modellspannen, die auf Wortgrenzen gezogen wurden

    def to_json(self, **kw) -> str:
        return self.dictionary and __import__("json").dumps(
            self.dictionary, ensure_ascii=False, **kw
        ) or "{}"


# ---------------------------------------------------------------------------
# Wortgrenzen
# ---------------------------------------------------------------------------

def _wortzeichen(c: str) -> bool:
    return c.isalnum() or c in "_'’"


def auf_wortgrenzen(text: str, spans: list[Span],
                    grenze: int = 50) -> tuple[list[Span], int]:
    """Modellspannen, die MITTEN in einem Wort beginnen oder enden, ausdehnen.

    Das Modell sagt auf Tokenebene vorher. Bei Text ausserhalb seines
    Trainingsbereichs — etwa italienischer und franzoesischer Fliesstext —
    schlaegt es auf einzelnen Subwort-Stuecken an:

        Settore giuri[ORG_1]e vigil[ORG_2]      (giuridico, vigilanza)
        m'inté[VOTING_RIGHTS_1]ait              (m'intéresserait)

    Ein Platzhalter, der Vollstaendigkeit vortaeuscht, waehrend Zeichen
    daneben im Klartext stehen — bei einem Namen waere es ein Leck.

    **Ausdehnen, nicht verwerfen.** Verwerfen waere die Wette, dass die
    Vorhersage falsch ist; ausdehnen ist die sichere Richtung — im Zweifel
    MEHR maskieren. Ein zuviel maskiertes Wort ist haesslich, ein zuwenig
    maskiertes ist ein Leck.

    Die Zahl der ausgedehnten Spannen ist zugleich eine Diagnose: steigt sie,
    sieht das Modell Text, den es nicht kennt.
    """
    out: list[Span] = []
    erweitert = 0
    for s in spans:
        a, b = s.start, s.end
        while (a > 0 and a > s.start - grenze
               and _wortzeichen(text[a - 1]) and _wortzeichen(text[a])):
            a -= 1
        while (b < len(text) and b < s.end + grenze
               and _wortzeichen(text[b]) and _wortzeichen(text[b - 1])):
            b += 1
        if (a, b) != (s.start, s.end):
            erweitert += 1
        out.append(Span(s.tag, a, b, source=s.source))
    return out, erweitert


def _stage(tag: str, pack) -> int:
    return {t.tag: t.stage for t in pack.get_tags()}.get(tag, 3)


def merge(
    text: str,
    model_spans: list[Scored],
    pack,
    scorer_present: bool = True,
    stats: dict | None = None,
    thresholds: dict[str, float] | None = None,
    user_spans: list[Span] | None = None,
) -> tuple[list[Span], list[tuple[str, str, str]]]:
    """Modelltreffer, Regexvorschläge und Prüfsummen zu einer Spannenliste."""
    thresholds = thresholds or pack.get_thresholds()
    stages = {t.tag: t.stage for t in pack.get_tags()}
    dropped: list[tuple[str, str, str]] = []

    # --- Stufe 3: Modell, gefiltert über die Schwelle ----------------------
    kept: list[Span] = []
    for s in model_spans:
        limit = thresholds.get(s.tag)
        if limit is not None and s.score < limit:
            dropped.append((s.tag, text[s.start:s.end],
                            f"unter Schwelle {limit:.2f} ({s.score:.2f})"))
            continue
        kept.append(Span(s.tag, s.start, s.end, source="model"))

    # Modellspannen auf Wortgrenzen ziehen, bevor irgendetwas zusammengefuehrt
    # wird — sonst konkurriert eine halbe Spanne mit einer ganzen und gewinnt
    # womoeglich ueber die Laenge.
    kept, erweitert = auf_wortgrenzen(text, kept)
    if stats is not None:
        stats["erweitert"] = erweitert

    # --- Stufe 1 und 2: Muster ---------------------------------------------
    regex_spans = recognize(text)

    # Benutzerregeln laufen wie Packmuster. Sie sind vom Anwender ausdruecklich
    # erklaert — deshalb kein Vetorecht gegen Stufe 1, aber gleichrangig mit
    # Stufe 2, und die Zusammenfuehrung entscheidet ueber die Laenge.
    if user_spans:
        regex_spans = list(regex_spans) + list(user_spans)

    # --- Stufe-1-Override: die Prüfsumme entscheidet -----------------------
    checksum_tags = {t.tag for t in pack.get_tags() if t.stage == 1}
    valid: list[Span] = [s for s in regex_spans if s.tag in checksum_tags]

    # Modelltreffer auf einem Prüfsummen-Tag, den die Prüfung nicht bestätigt,
    # wird verworfen. Das ist die Precision-Garantie: eine "AHV-Nummer" ohne
    # gültige Prüfziffer ist keine.
    survivors: list[Span] = []
    for s in kept:
        if s.tag not in checksum_tags:
            survivors.append(s)
            continue
        value = text[s.start:s.end]
        validator = VALIDATORS.get(s.tag)
        if validator and validator(value):
            survivors.append(s)
        else:
            dropped.append((s.tag, value, "Pruefsumme ungueltig"))
    kept = survivors

    # --- Alles zusammen, Überlappungen nach Stufenvorrang ------------------
    everything = valid + [s for s in regex_spans if s.tag not in checksum_tags] + kept

    def priority(s: Span) -> tuple[int, int, int]:
        stage = stages.get(s.tag, 3)
        # `benutzer` steht ausdruecklich in der Tabelle, gleichrangig mit den
        # Packmustern. Ohne Eintrag zaehlte die Quelle wie das Modell und gewaenne
        # bei gleicher Laenge nur durch einen Zufall der Reihenfolge.
        # `tests/test_user_rules.py` Punkt 5 haelt alle drei Faelle fest.
        rank = {"regex": 0, "benutzer": 0, "model": 1}.get(s.source, 1)
        # Reihenfolge: Stufe, dann LAENGE, dann Quelle.
        #
        # Die Laenge muss vor die Quelle. Sonst schluege ein kurzer Regextreffer
        # eine laengere, richtige Modellspanne derselben Stufe: aus "P-2024-0815"
        # (PATIENT_ID) wuerde "2024-0815" (CASE_ID), und das "P-" bliebe im
        # Klartext.
        #
        # Wo die Spannen gleich lang sind, gewinnt die Regex: dort ist sie das
        # praezisere Signal. Nur Stufe 1 (Pruefsumme) hat absoluten Vorrang.
        # Stufe 2 ist ein Vorschlag ohne Vetorecht (SPEC §3) und darf eine
        # laengere, richtige Modellspanne nicht verdraengen.
        vorrang = 1 if stage == 1 else 2
        # Seit 25.11.2026: angehaengte Tags (zweiter Kopf) kommen NACH allen
        # anderen. Ueberschneiden sie eine Spanne eines alten Tags, gewinnt das
        # alte, auch wenn die neue Spanne laenger ist. So behalten die alten
        # Tags ihr Verhalten; die neuen maskieren nur, wo sonst nichts steht.
        # Ohne das verdraengte eine lange FAMILYROLE-Spanne eine richtige
        # Strasse (STREET-Recall 0.33 statt wie ch-v63b).
        nachrang = 1 if s.tag in NACHRANG else 0
        return (vorrang, nachrang, -(s.end - s.start), rank)

    # `Belegung` beantwortet «ist diese Stelle schon belegt?» mit einer Suche
    # statt mit einem Durchlauf ueber alles bisher Behaltene — sonst waechst
    # der Aufwand quadratisch mit der Textlaenge. Das Verschmelzen ist hier
    # folgenlos: was behalten wird, ueberlappt sich per Konstruktion nicht.
    from core.masking import Belegung

    final: list[Span] = []
    belegt = Belegung()
    for s in sorted(everything, key=priority):
        if not belegt.frei(s.start, s.end):
            continue
        belegt.belegen(s.start, s.end)
        final.append(s)

    # ⚠️ Am 25.11.2026 versucht und verworfen: JOBTITLE durfte eine ORG-Spanne,
    # die es ganz abdeckt, ersetzen («Bundesrichter» als JOBTITLE statt ORG).
    # Recall JOBTITLE stieg von 41 auf 56 %, aber ch-v63b liest ganze Zeilen
    # wie «Bundesrichter X, Praesident» als ORG; mit JOBTITLE im Klartext
    # leckten dann die Namen darin (Pruefset familie: 9). Der Vorrang der alten
    # Tags bleibt ohne Ausnahme.
    return sorted(final, key=lambda s: s.start), dropped


def filter_text(
    text: str,
    pack,
    scorer: Scorer | None = None,
    propagate: bool = True,
    thresholds: dict[str, float] | None = None,
    excluded: set[str] | None = None,
    mapping_enabled: bool = True,
    rules: list | None = None,
) -> FilterResult:
    """Der vollständige Durchlauf: erkennen, zusammenführen, maskieren.

    Ohne `scorer` läuft nur Stufe 1 und 2 — brauchbar als Grundlinie und für
    Selbstprüfungen, aber Namen, Daten und Adressen bleiben dann im Klartext.
    """
    stats: dict = {}
    extra: dict = {}
    user_spans: list[Span] = []
    if rules:
        from core import user_rules
        user_spans = user_rules.erkenne(text, rules)
        extra = {
            "actions": user_rules.aktionen(rules),
            "placeholders": user_rules.platzhalter(rules),
            "stages": user_rules.stufen(rules),
        }
    model_spans = scorer.score(text) if scorer else []
    spans, dropped = merge(text, model_spans, pack,
                           scorer_present=bool(scorer), stats=stats,
                           thresholds=thresholds, user_spans=user_spans)
    result: MaskResult = mask(text, spans, pack, do_propagate=propagate,
                              excluded=excluded,
                              mapping_enabled=mapping_enabled, extra=extra)
    return FilterResult(
        masked=result.text,
        dictionary=result.dictionary,
        spans=result.spans,
        dropped=dropped,
        erweitert=stats.get("erweitert", 0),
    )


# ---------------------------------------------------------------------------
# ONNX-Läufer. Braucht beim Anwender NUR onnxruntime + tokenizers, kein torch.
# ---------------------------------------------------------------------------

class OnnxScorer:
    """Modell aus einem exportierten ONNX-Verzeichnis.

    Absichtlich getrennt von der Zusammenführung: `merge` und `filter_text`
    bleiben ohne Modell testbar, und der Anwender installiert kein torch.

        pip install onnxruntime tokenizers      # ~60 MB statt ~2 GB
    """

    def __init__(self, model_dir, max_length: int = 512, stride: int = 128,
                 datei: str = "model.onnx"):
        # `datei` nur fuer `build_release.py --verify`, das die fp32- und
        # die int8-Fassung im selben Verzeichnis gegeneinander laufen
        # laesst. Der Anwender laesst die Vorgabe stehen.
        import json
        from pathlib import Path

        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
        # Telemetrie aus, auch unter Windows (ETW); siehe app/serve.py.
        ort.disable_telemetry_events()

        self.np = np
        path = Path(model_dir)
        meta = json.loads((path / "pack.json").read_text(encoding="utf-8"))
        self.labels = meta["labels"]
        self.label_hash = meta["label_hash"]
        self.kopf_alt = meta.get("kopf_alt")
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))

        # Die wichtigste Zeile in dieser Klasse.
        #
        # `tokenizer.json` traegt aus dem Training `truncation: {max_length: 512}`.
        # Ohne dieses Abschalten schneidet `encode()` den Text auf 512 Token ab,
        # BEVOR die Fensterschleife anfaengt — die Schleife waere toter Code, und
        # alles nach Token 512 saehe das Modell nie. Am Ende eines Dokuments stehen
        # die Signaturbloecke: Name, Firma, Strasse, Ort.
        #
        #     14 000 Zeichen, abgeschnitten      ->  512 Token
        #     14 000 Zeichen, ohne Abschneidung  -> 3603 Token
        #
        # Kurze Testdokumente koennen diesen Fehler strukturell nicht sehen.
        # `tests/test_langes_dokument.py` stellt den Fall deshalb selbst her.
        self.tokenizer.no_truncation()

        # Sondertoken JE FENSTER, nicht einmal fuer den ganzen Text.
        #
        # `encode()` setzt das Anfangs- und das Endtoken um den GANZEN Text. Wird
        # danach in Fenster geschnitten, bekommt nur das erste Fenster ein
        # Anfangs- und nur das letzte ein Endtoken — jedes Fenster dazwischen
        # erhielte eine Eingabeform, die das Modell im Training nie gesehen hat,
        # und das kostet Lecks.
        #
        # Deshalb: Offsets OHNE Sondertoken holen und beide je Fenster selbst
        # setzen — genau wie `TorchScorer`.
        #
        # Die Namen stehen in `tokenizer_config.json` und werden nicht geraten.
        # mmBERT benutzt den Gemma-2-Tokenizer: die Sondertoken heissen `<bos>`
        # und `<eos>`, nicht `[CLS]`/`[SEP]`. `AutoTokenizer` liest dieselben zwei
        # Felder, deshalb stimmt der Torch-Weg mit diesem hier ueberein.
        tconf = json.loads(
            (path / "tokenizer_config.json").read_text(encoding="utf-8"))
        cls_name = tconf.get("cls_token") or tconf.get("bos_token")
        sep_name = tconf.get("sep_token") or tconf.get("eos_token")
        self.cls_id = (self.tokenizer.token_to_id(cls_name)
                       if cls_name else None)
        self.sep_id = (self.tokenizer.token_to_id(sep_name)
                       if sep_name else None)
        if self.cls_id is None or self.sep_id is None:
            raise SystemExit(
                "ABBRUCH: Tokenizer ohne Anfangs- und Endtoken.\n"
                f"  cls/bos: {cls_name!r} -> {self.cls_id}\n"
                f"  sep/eos: {sep_name!r} -> {self.sep_id}\n"
                "  Das Modell wurde mit beiden trainiert. Ohne sie ist\n"
                "  jede Vorhersage auf einer fremden Eingabeform.")
        self.session = ort.InferenceSession(
            str(path / datei),
            providers=["CPUExecutionProvider"],
        )
        self.max_length = max_length
        self.stride = stride

    def check_contract(self, pack) -> None:
        """Labelvertrag gegen den Pack prüfen. Ohne das mappt ein alter
        Checkpoint still auf falsche Labels."""
        if self.label_hash != pack.get_label_hash():
            raise SystemExit(
                "ABBRUCH: Labelvertrag des Modells passt nicht zum Pack.\n"
                f"  Modell: {self.label_hash}\n"
                f"  Pack:   {pack.get_label_hash()}"
            )

    def score(self, text: str) -> list[Scored]:
        from core.alignment import decode

        np = self.np
        # `add_special_tokens=False`: die Offsets sollen nur auf echten Text
        # zeigen. Die Sondertoken haben keine Stelle im Dokument; sie kommen je
        # Fenster dazu, und die Logit-Indizes verschieben sich deshalb um eins.
        enc = self.tokenizer.encode(text, add_special_tokens=False)
        offsets = enc.offsets
        ids = enc.ids

        # Lange Dokumente in überlappende Fenster schneiden. Die Überlappung
        # verhindert, dass eine Entität genau an der Schnittkante zerfällt.
        paesse: list[dict[tuple[int, int], tuple[str, float]]] = []
        nutz = self.max_length - 2          # Platz für [CLS] und [SEP]
        step = max(1, nutz - self.stride)
        # Wie im Torch-Weg: die Zahl der Fenster steht vorher fest. Zwei
        # Laeufer, ein Verhalten.
        fenster = fensterzahl(len(ids), nutz, step)
        melde = getattr(self, "melde", None)
        for nr, begin in enumerate(range(0, max(1, len(ids)), step), start=1):
            if melde is not None:
                melde(nr, fenster)
            chunk_ids = ids[begin:begin + nutz]
            chunk_off = offsets[begin:begin + nutz]
            if not chunk_ids:
                break
            arr = np.array([[self.cls_id] + list(chunk_ids) + [self.sep_id]],
                           dtype=np.int64)
            logits = self.session.run(
                None,
                {"input_ids": arr, "attention_mask": np.ones_like(arr)},
            )[0][0]
            for k, (best, conf) in enumerate(kopf_paesse(logits,
                                                         self.kopf_alt)):
                if len(paesse) <= k:
                    paesse.append({})
                results = paesse[k]
                for i, (a, b) in enumerate(chunk_off):
                    if b <= a:
                        continue
                    j = i + 1               # [CLS] steht davor
                    label = self.labels[int(best[j])]
                    p = float(conf[j])
                    # Bei Überlappung gewinnt die sicherere Vorhersage
                    prev = results.get((a, b))
                    if prev is None or p > prev[1]:
                        results[(a, b)] = (label, p)
            if begin + nutz >= len(ids):
                break

        # Vertrauen aus allen Token, die sich mit der Spanne UEBERSCHNEIDEN —
        # nicht nur aus den vollstaendig enthaltenen.
        #
        # SentencePiece haengt das fuehrende Leerzeichen an das Token: aus
        # " Schweiz" wird ein Token mit Offset (a, b), wobei a VOR dem
        # Entitaetsbeginn liegt. Verlangte man Enthaltensein, faende man bei einer
        # Entitaet aus genau einem Wort-Token gar kein Token, das Vertrauen waere
        # 0.0, und die Schwelle wuerfe die Entitaet weg — obwohl das Modell auf
        # Tokenebene richtig lag. Ziffernbasierte Tags merken davon nichts, weil
        # Zahlen in Einzelziffern zerlegt werden.
        return spannen_aus_paessen(paesse, self.labels, text)
