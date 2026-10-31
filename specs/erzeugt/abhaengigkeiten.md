<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Abhaengigkeiten

Die Listen im Wortlaut der Pakete, ohne Kommentare.

## `requirements.txt`

```text
flask>=3.1.3
werkzeug>=3.1.9
jinja2>=3.1.6
pyyaml>=6.0
onnxruntime>=1.17
tokenizers>=0.15
pymupdf>=1.24,<2
olefile>=0.46
```

## `tools/paket/requirements-paket.txt`

```text
flask>=3.1.3
werkzeug>=3.1.9
jinja2>=3.1.6
gunicorn>=22.0
pyyaml>=6.0
tokenizers>=0.15
pymupdf>=1.24,<2
olefile>=0.46
torch>=2.13
transformers>=5.10
```

## `tools/paket/requirements-appimage.txt`

```text
-r requirements-paket.txt
pywebview[qt]>=6.2.1,<7
qtpy>=2.4
PyQt6-WebEngine>=6.11
```

## `tools/paket/requirements-flatpak.txt`

```text
flask>=3.1.3
werkzeug>=3.1.9
jinja2>=3.1.6
gunicorn>=22.0
pyyaml>=6.0
tokenizers>=0.15
pymupdf>=1.24,<2
olefile>=0.46
torch>=2.13
transformers>=5.10
pywebview>=6.2.1,<7
qtpy>=2.4
```
