# Observatorio de Competitividad Agroexportadora

Tablero Streamlit + Plotly para explorar perfiles de competitividad agroexportadora en español.

## Arranque local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

La aplicación abre la presentación en `http://localhost:8501`. La demo del guion de tres pasos está disponible en `http://localhost:8501/?modo=demo`.

## Pruebas y respaldo

```bash
python -m pytest
python export_respaldo.py
```

El segundo comando genera cuatro PNG de 1280 x 720 en `respaldo/`. Requiere `kaleido` y sirve como copia local si falla la conexión durante la exposición.

## Streamlit Community Cloud

1. Sube este repositorio a GitHub.
2. En Streamlit Community Cloud selecciona **Create app** y elige el repositorio, rama y archivo `app.py`.
3. Confirma `requirements.txt` como archivo de dependencias y despliega.
4. Comprueba la URL pública y prueba también `?modo=demo`.

Los CSV deben permanecer en la raíz del repositorio junto a `app.py`.
