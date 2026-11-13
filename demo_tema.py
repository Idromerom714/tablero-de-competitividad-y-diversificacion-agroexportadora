"""Demo visual del tema para proyección a 1280x720."""

import plotly.graph_objects as go
import streamlit as st

from config import (
    OBSERVACIONES_CLUSTERS,
    NUMERO_CLUSTERS,
    PALETA_CLUSTERS,
    PERFILES_CLUSTER,
    SILUETA,
    VARIANZA_PCA,
    VARIABLES_AGRUPAMIENTO,
)
from theme import cluster_chip, inject_css, kpi_card, plotly_template


st.set_page_config(
    page_title="Demo del tema | Observatorio",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css(presentation=True)

st.title("Observatorio de Competitividad Agroexportadora")
st.caption("Prueba de contraste y tamaños para proyector 1280 x 720")

columns = st.columns(3)
for column, (valor, etiqueta, delta) in zip(
    columns,
    [
        (str(OBSERVACIONES_CLUSTERS), "observaciones", "3 ventanas fijas"),
        (f"{VARIANZA_PCA:.1f} %".replace(".", ","), "varianza PCA", f"{VARIABLES_AGRUPAMIENTO} variables"),
        (f"{SILUETA:.3f}".replace(".", ","), "silueta", f"k = {NUMERO_CLUSTERS}"),
    ],
):
    with column:
        kpi_card(valor, etiqueta, delta)

st.subheader("Perfiles del modelo")
profile_columns = st.columns(4)
for column, nombre in zip(
    profile_columns,
    [
        PERFILES_CLUSTER["lideres"],
        PERFILES_CLUSTER["transicion"],
        PERFILES_CLUSTER["especializacion"],
        "Caso fuera del modelo",
    ],
):
    with column:
        if nombre == "Caso fuera del modelo":
            color = PALETA_CLUSTERS[nombre]
            st.markdown(
                f'<div class="cluster-chip" style="--cluster-background:#FFFFFF;--cluster-text:#111111;--cluster-border:{color};">{nombre}</div>',
                unsafe_allow_html=True,
            )
        else:
            cluster_chip(nombre)

figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=["2005-11", "2012-18", "2019-24"],
        y=[5, 7, 9],
        marker_color=PALETA_CLUSTERS[PERFILES_CLUSTER["lideres"]],
        text=["5", "7", "9"],
        textposition="outside",
        textfont={"size": 20, "color": "#111111"},
        name="Alta Diversificación",
    )
)
figure.update_layout(
    template=plotly_template(),
    title="Diversificación por ventana",
    xaxis_title="Ventana temporal",
    yaxis_title="Número de productos (k60)",
    showlegend=False,
    height=330,
)
st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})