<!-- Erzeugt von tools/specs_bauen.py aus dem Code. Nicht von Hand aendern. -->

# Endpunkte

Aus den Dekoratoren in `app/app.py` und `app/serve.py`. Der Vertrag steht in [07_api.md](../07_api.md).

| Methode | Pfad | Datei | Beschreibung |
|---|---|---|---|
| GET | `/` | `app/app.py` | Die Oberflaeche, mit dem gewaehlten Thema schon im `<html>`. |
| GET | `/<path:datei>` | `app/app.py` |  |
| POST, PUT, DELETE, PATCH | `/api/<path:rest>` | `app/app.py` |  |
| GET | `/api/zustand` | `app/serve.py` | Laeuft der Server, welches Modell, welcher Labelvertrag. |
| POST | `/api/neueste` | `app/serve.py` | Gibt es eine neuere Fassung? Nur auf Klick im Burgermenue. |
| GET | `/api/tags` | `app/serve.py` |  |
| POST | `/api/lesen` | `app/serve.py` | Eine Datei zu Text machen, und SONST NICHTS. |
| POST | `/api/anonymisieren` | `app/serve.py` |  |
| GET | `/api/fortschritt` | `app/serve.py` | Wie weit ist der laufende Durchgang? |
| POST | `/api/zurueckwandeln` | `app/serve.py` |  |
| GET | `/api/regeln` | `app/serve.py` |  |
| PUT | `/api/regeln` | `app/serve.py` |  |
| GET | `/api/vorlieben` | `app/serve.py` |  |
| PUT | `/api/vorlieben` | `app/serve.py` |  |
| GET | `/api/vorlagen` | `app/serve.py` |  |
| PUT | `/api/vorlagen` | `app/serve.py` |  |
| GET | `/api/einstellungen` | `app/serve.py` |  |
| PUT | `/api/einstellungen` | `app/serve.py` |  |
