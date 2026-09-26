# MASCHERA als Abbild — die Anwendung, nicht das Training.
#
#     fish tools/paket/bauen.fish
#
# Der Bau-Kontext ist der PROJEKTSTAMM, nicht dieses Verzeichnis. Der Punkt
# am Ende ist Absicht: `runs/`, `packs/` und `core/` liegen dort. Was NICHT
# mitfaehrt, steht in `.dockerignore` — eine Sperre, keine Aufraeumhilfe.
#
# MIT torch: im Paket laeuft derselbe Laeufer, mit dem gemessen wird.
# Begruendung in `tools/paket/requirements-paket.txt`.

FROM python:3.13-slim AS bau

# Nur die fuenf Zeilen aus `requirements.txt`. Die Datei sagt in ihrem
# eigenen Kopf, dass sie fuer genau diesen Zweck kurz gehalten ist.
COPY tools/paket/requirements-paket.txt /bau/requirements.txt
#
# ⚠️⚠️ Die letzte Zeile SIEHT NACH, ob es die CPU-Fassung ist.
#
# `requirements-paket.txt` sagt `--extra-index-url`, und das ERGAENZT
# PyPI. Dass heute die CPU-Raeder gewinnen, liegt allein an der
# Sortierung: `2.14.0+cpu` steht ueber `2.14.0`. Kippt das, kommen ueber
# 2 GB CUDA-Bibliotheken in ein Abbild, in dem keine GPU ist — und es
# faellt nicht auf, weil der Dienst damit laeuft. Nur die Schichten waeren
# ploetzlich riesig, und das sieht niemand beim Bauen.
#
# Der Bau bricht dann ab. Eine Zusage im Kommentar ist keine Pruefung.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r /bau/requirements.txt \
 && /opt/venv/bin/python -c "import torch, sys; v = torch.__version__; \
print('torch', v); sys.exit(0 if '+cpu' in v else 1)" 


FROM python:3.13-slim

COPY --from=bau /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # ⚠️ KEIN Nachladen von aussen. Ohne diese beiden fragt
    # `transformers` beim Start den Hub — und in einem Netz ohne Ausgang
    # haengt der Start dann in Zeitueberschreitungen, statt zu sagen,
    # was fehlt. Das Modell liegt im Abbild; es gibt nichts zu holen.
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    # ⚠️ Vier Faeden: die Zielmaschine hat 4 physische Kerne mit SMT.
    # Bei torch bringt SMT meist nichts und schadet manchmal.
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4

# ⚠️ Den Benutzer VOR dem Kopieren anlegen, und dann mit `--chown`
# kopieren. Der erste Bau machte es umgekehrt — kopieren, dann
# `chown -R /maschera` — und kostete **345 MB**: `chown` aendert jede
# Datei, also schreibt Docker das ganze Modell ein zweites Mal in eine
# neue Schicht. Gemessen mit `docker history`, nicht vermutet.
#
# ⚠️ Nicht als root laufen. Das Werkzeug nimmt Dateien von aussen entgegen
# und gibt sie an `pymupdf` und `mailbox` weiter — genau die Stelle, an
# der eine kaputte Datei etwas versucht.
# Angaben fuer die Paketseite auf GitHub: sie ordnet das Abbild dem
# Repository zu und nennt die Lizenz des GEBAUTEN Pakets (siehe LIZENZ.md).
LABEL org.opencontainers.image.source="https://github.com/semprerudi/maschera" \
      org.opencontainers.image.title="MASCHERA" \
      org.opencontainers.image.description="Lokale Pseudonymisierung fuer Schweizer Dokumente" \
      org.opencontainers.image.licenses="AGPL-3.0-only" \
      org.opencontainers.image.url="https://www.maschera.ch"

RUN useradd --create-home --uid 10001 maschera
USER maschera
WORKDIR /maschera

# Reihenfolge nach Aenderungshaeufigkeit: das Modell zuerst, damit eine
# Codeaenderung nicht 329 MB neu schichtet.
COPY --chown=maschera:maschera runs/ch-v63b/ runs/ch-v63b/
COPY --chown=maschera:maschera packs/ packs/
COPY --chown=maschera:maschera core/ core/
# DREI Dateien aus `tools/`: `app/serve.py` legt `tools/` auf den
# Suchpfad und importiert von dort `dokumente` und `filter_document`, und
# `evaluate_model` erst IM RUMPF von `Zustand.__init__`, wenn ein Modell
# gesetzt ist. Fehlt eine, stirbt der Container erst beim Start, nicht beim
# Bauen.
#
# Gemessen wird STATISCH: jeden Import in `app/*.py` ansehen, auch die
# verzoegerten. `tests/test_fenster.py` Punkt 12 tut das und haelt diese
# Zeile gegen die anderen Verpackungen.
COPY --chown=maschera:maschera tools/dokumente.py tools/filter_document.py \
     tools/evaluate_model.py tools/
COPY --chown=maschera:maschera app/ app/
# Die Lizenztexte — das Abbild steht unter AGPL-3.0.
COPY --chown=maschera:maschera LICENSE LICENSE-AGPL-3.0.txt LIZENZ.md \
     lizenzen/
# ⚠️ KEIN `__init__.py`. `gunicorn app.wsgi:anwendung` findet `app`
# als NAMENSRAUMPAKET (seit Python 3.3 ohne `__init__.py`). Ein leeres
# `__init__.py` hier hat beim ersten Anlauf genau den Import gebrochen,
# den es ermoeglichen sollte.

# ⚠️ HOME setzen, weil `core/pfade.py` die Einstellungen unter
# `~/.config/maschera/` sucht. Ohne die Zeile schreibt der Dienst in ein
# Verzeichnis, das beim naechsten Start weg ist — und die Einstellungen
# waeren still fluechtig statt dauerhaft.
ENV HOME=/home/maschera

# Das Verzeichnis MUSS im Abbild existieren und `maschera` gehoeren, BEVOR
# `VOLUME` es benennt. Sonst legt Docker das benannte Volumen als root an,
# und der Dienst — der als `maschera` laeuft — darf nicht hineinschreiben:
#
#     {"fehler":"Nicht gespeichert: [Errno 13] Permission denied:
#      '/home/maschera/.config/maschera/vorlagen.json'"}
#
# Docker uebernimmt Inhalt UND Eigentuemer aus dem Abbild, wenn es ein
# neues benanntes Volumen anlegt — aber nur, wenn dort etwas steht.
RUN mkdir -p /home/maschera/.config/maschera
VOLUME ["/home/maschera/.config/maschera"]

EXPOSE 4141

# `--host 0.0.0.0` IST hier richtig, und nur hier. Der Container hat
# seinen eigenen Netzwerkraum; ohne die Fahne ist der Dienst nicht einmal
# fuer einen Proxy daneben erreichbar. Die Absicherung passiert eine Ebene
# hoeher: `compose.yaml` veroeffentlicht den Port NUR auf 127.0.0.1 des
# Wirts.
#
# Wer daraus schliesst, MASCHERA sei fuer den offenen Betrieb gedacht,
# liest es falsch. `app/app.py` warnt beim Start ausdruecklich, und die
# Warnung bleibt im Protokoll stehen.
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import urllib.request as u; \
u.urlopen('http://127.0.0.1:4141/api/zustand', timeout=4)" || exit 1

# gunicorn, nicht `app/app.py`: der Flask-Entwicklungsserver ist fuer den
# Betrieb nicht gedacht.
#
# EIN Arbeiter, acht Faeden. Zwei Prozesse haetten jeder ihr eigenes Modell
# (doppelter Speicher) und jeder seine eigene Sperre — und die Sperre
# verhindert, dass zwei Dokumente ihre Vertrauenswerte vermischen. Siehe
# `app/wsgi.py`.
#
# `--timeout 300`: ein grosses PDF braucht auf wenigen CPU-Kernen Minuten.
# Die Vorgabe von 30 s wuerde den Arbeiter mitten im Dokument abschiessen.
ENV MASCHERA_MODELL=runs/ch-v63b
ENTRYPOINT ["gunicorn"]
CMD ["--workers", "1", "--threads", "8", "--timeout", "300", \
     "--bind", "0.0.0.0:4141", "--access-logfile", "-", \
     "app.wsgi:anwendung"]
