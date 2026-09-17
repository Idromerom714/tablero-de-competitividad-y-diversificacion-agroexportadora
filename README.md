# tablero-de-competitividad-y-diversificacion-agroexportadora

## Dashboard interactivo

El dashboard se ejecuta con Streamlit y lee los tres archivos CSV desde la carpeta `data/`.

```bash
pip install streamlit pandas plotly
streamlit run app.py
```

Si los datos se encuentran en otra ubicación, ajusta las variables `RUTA_PERFIL`, `RUTA_RCA` y `RUTA_PRECIO_VOLUMEN` al inicio de `app.py`.