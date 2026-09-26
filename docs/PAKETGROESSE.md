# Woraus die 1,55 GB bestehen

Gemessen an der AppImage für x86-64.

## Und die anderen Verpackungen

Diese Aufstellung gilt **nur** für die AppImage — sie ist die einzige, in
der alles in einer Datei steckt. Zum Vergleich:

| | Paket | Modell | Bibliotheken |
|---|---|---|---|
| **AppImage** | 1,55 GB | fährt mit | eigene |
| **Flatpak** | 1,4 GB | wird geholt | eigene, plus Laufzeit von Flathub |
| **Docker** | — | fährt mit | eigene |

⚠️ **Hier steht bewusst keine Fassungsnummer.** Sie hat genau eine Quelle
(`app/serve.py`), und `tests/test_fenster.py` Punkt 7 hält das fest — eine
Zahl in einem Dokument wäre die zweite und bliebe beim nächsten Erhöhen
zurück. Die Werte unten ändern sich mit jeder neuen Abhängigkeit, nicht
mit jeder Fassung.

| | |
|---|---|
| **Die AppImage** | **1,55 GB** — komprimiert, eine Datei |
| Entpackt im Betrieb | 2,86 GB |

Die AppImage ist ein zusammengepresstes Dateisystem: sie wird beim Start
eingehängt und nicht ausgepackt. Die 1,55 GB sind das, was auf die Platte
kommt; die 2,86 GB sind die Summe der Dateien darin.

---

## Die Hauptposten

| Posten | entpackt | Anteil | wofür |
|---|---:|---:|---|
| **Das Modell** `ch-v63b` | 1206 MB | 41 % | die Erkennung selbst |
| **PyTorch** (CPU) | 712 MB | 24 % | rechnet das Modell |
| **PyQt6 / Qt 6** | 515 MB | 18 % | das Fenster |
| **Python-Unterbau** | 104 MB | 4 % | eigener Python 3.13 |
| **transformers** | 97 MB | 3 % | lädt Modell und Tokenizer |
| **sympy** | 65 MB | 2 % | Abhängigkeit von PyTorch |
| **numpy** (+ `numpy.libs`) | 65 MB | 2 % | Zahlenfelder |
| **PyMuPDF** | 64 MB | 2 % | liest PDF |
| **networkx** | 15 MB | 0,5 % | Abhängigkeit von PyTorch |
| **hf_xet** | 12 MB | 0,4 % | Abhängigkeit von `huggingface_hub` |
| **tokenizers** | 10 MB | 0,3 % | zerlegt Text in Token |
| Kleinteile | 59 MB | 2 % | `pygments`, `huggingface_hub`, `mpmath`, `regex`, `yaml`, `rich`, `pywebview`, `setuptools`, … |
| **MASCHERA selbst** | **1,2 MB** | 0,04 % | `app`, `core`, `packs`, `tools` |

⚠️ **Der eigene Code ist ein Tausendstel des Pakets.** Alles andere ist
Modell und Unterbau. Das ist der Preis dafür, dass nichts das Gerät
verlässt: ein Werkzeug, das eine fremde Schnittstelle fragt, wäre ein paar
Megabyte gross — und würde bei jedem Dokument genau das tun, was hier
verhindert werden soll.

---

## Was die einzelnen Teile tun

### Das Modell — 1206 MB

`runs/ch-v63b`, ein **ModernBERT** zur Token-Klassifikation. Es liest den
Text und sagt für jedes Token, ob es Teil eines Personendatums ist und
welcher Art.

| Datei | | |
|---|---:|---|
| `model.safetensors` | 1173 MB | die Gewichte: 308 Mio Parameter als `float32` |
| `tokenizer.json` | 33 MB | der Wortschatz, 256 000 Einträge |
| `config.json`, `pack.json` | < 1 MB | Bauart und der Labelvertrag, 45 Tags |

⚠️ **Zwei Drittel der Gewichte sind der Wortschatz.** 256 000 Token mal 768
Dimensionen sind allein 197 Mio Parameter; der eigentliche Rechenteil ist
mit rund 111 Mio deutlich kleiner. Das Modell ist mehrsprachig ausgelegt,
während MASCHERA vier Sprachen und einen amtlich begrenzten Zeichensatz
braucht.

### PyTorch — 712 MB

Die Rechenmaschine, die das Modell ausführt. **Nur die CPU-Fassung** — die
CUDA-Fassung wäre um ein Vielfaches grösser, und eine Grafikkarte wird
nicht vorausgesetzt.

| | |
|---|---|
| `libtorch_cpu.so` | **414 MB** — eine einzige Datei, die gesamte Rechenschicht |
| `torch/test` | 82 MB — die Selbsttests von PyTorch |
| `torch/include` | 36 MB — Kopfdateien für C++-Erweiterungen |
| `torch/_inductor` | 20 MB — der Übersetzer für `torch.compile` |

### PyQt6 und Qt 6 — 515 MB

Das Fenster. MASCHERA läuft im Browser **und** als eigenes Fenster; für das
Fenster sorgt `pywebview` auf PyQt6.

| | |
|---|---|
| `libQt6WebEngineCore.so.6` | **194 MB** — die Anzeigeschicht, ein eingebettetes Chromium |
| `Qt6/translations` | 53 MB — Qt-Übersetzungen in alle Sprachen |
| `Qt6/resources` | 24 MB — Zeichensätze und Daten der Anzeigeschicht |
| `Qt6/plugins` | 20 MB — Bildformate, Eingabemethoden, Fenstersystem |

⚠️ Die Oberfläche ist HTML und wird ohnehin gebraucht — im Browser rendert
sie der Browser des Anwenders, im eigenen Fenster diese Schicht. Sie ist der
Preis dafür, dass es **eine** Oberfläche für beide Wege gibt statt zweier.

### Die kleineren, und warum sie da sind

| | |
|---|---|
| **transformers** | lädt Modell und Tokenizer und führt die Klassifikation aus |
| **tokenizers** | zerlegt den Text in Token — die schnelle Rust-Umsetzung |
| **PyMuPDF** | liest PDF. Ein Scan ohne Textebene wird erkannt und abgewiesen |
| **numpy** | Zahlenfelder, Unterbau von PyTorch |
| **PyYAML** | liest die Packs — Nomenklaturen, Muster, Schwellen |
| **pywebview** | verbindet die HTML-Oberfläche mit dem Qt-Fenster |
| **sympy**, **networkx**, **mpmath** | Abhängigkeiten von PyTorch für Symbolrechnen und Graphen. Beim reinen Anwenden eines Modells laufen sie nicht |
| **huggingface_hub**, **hf_xet** | kommen mit `transformers`. ⚠️ Im Betrieb **abgeschaltet**: `AppRun` setzt `HF_HUB_OFFLINE` und `TRANSFORMERS_OFFLINE`, sonst fragte `transformers` bei jedem Start nach draussen |
| **pygments**, **rich** | Textausgabe, Abhängigkeiten der Werkzeuge |

Nicht dabei: **Flask** ist winzig, und der Server läuft mit. Schriften
liegen bei — zehn Dateien, 178 KB.

---

## Was sich einsparen liesse

Ehrlich gerechnet, ohne dass die Anwendung etwas verliert:

| | entpackt | |
|---|---:|---|
| `torch/test` | 82 MB | Selbsttests von PyTorch |
| `Qt6/translations` | 53 MB | die Oberfläche bringt ihre vier Sprachen selbst mit |
| `torch/include` | 36 MB | nur für das Übersetzen eigener C++-Teile |
| `sympy` + `networkx` + `mpmath` | 84 MB | laufen beim Anwenden eines Modells nicht |
| `hf_xet` | 12 MB | Beschleuniger für Downloads, die es hier nicht gibt |
| **zusammen** | **rund 265 MB** | entpackt, also grob 130 bis 150 MB in der AppImage |

⚠️ **Jeder dieser Posten ist eine Abhängigkeit, keine Datei zum Löschen.**
Wer sie herausnimmt, muss prüfen, dass kein Pfad sie doch berührt — ein
Paket, das erst beim zwanzigsten Dokument abstürzt, ist teurer als 130 MB.

### Der grosse Hebel wäre ein anderer

Das Modell nach **ONNX** zu geben und mit `int8` zu quantisieren, statt
PyTorch mitzuliefern:

| | heute | mit ONNX |
|---|---:|---:|
| Modell | 1206 MB | rund 310 MB |
| Rechenmaschine | 712 MB (PyTorch) | rund 20 MB (ONNX Runtime) |

Den Wortschatz auf vier Sprachen zu beschneiden brächte weniger, als die
Rechnung verspricht, und kostet Sicherheit: ein Name in einer Schrift, die
beim Beschneiden wegfiel, wäre danach still nicht mehr maskierbar.

⚠️ **Das ist kein Umschalten, sondern eine Messreihe.** Quantisierung
verändert die Ausgabe, die Schwellen sind kalibriert und der Labelvertrag
ist eingefroren. Jede Fassung braucht eine neue Messung gegen die
Golddokumente — und für ein Werkzeug, bei dem ein übersehener Name teurer
ist als ein zu viel maskierter, ist das die Bedingung, nicht die Kür.
