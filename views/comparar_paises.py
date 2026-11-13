"""Vista exploratoria para comparar dos países por variable y ventana."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PALETA_CLUSTERS, PERFILES_CLUSTER, VENTANAS
from data import load_clusters
from theme import inject_css, plotly_template, render_html


VARIABLES_COMPARACION = (
    ("k60", "k60"),
    ("HHI_Familias", "HHI de familias"),
    ("Part_1_Producto", "Participación del producto principal"),
    ("Volatilidad_YoY_Log", "Volatilidad interanual"),
    ("Dep_Mediana", "Dependencia mediana"),
    ("Int_Mediana", "Intensidad mediana"),
    ("Proc_Ponderado", "Procesamiento ponderado"),
)


def _seleccionar_paises(clusters: pd.DataFrame) -> tuple[str, str]:
    """Renderiza los dos selectores de países comparables."""
    paises = sorted(clusters["Area"].unique().tolist())
    columnas = st.columns(2)
    with columnas[0]:
        pais_a = st.selectbox(
            "País 1",
            paises,
            index=paises.index("Ecuador") if "Ecuador" in paises else 0,
            key="comparar_pais_a",
        )
    with columnas[1]:
        paises_b = [pais for pais in paises if pais != pais_a] or paises
        indice_b = paises_b.index("Perú") if "Perú" in paises_b else 0
        pais_b = st.selectbox(
            "País 2",
            paises_b,
            index=indice_b,
            key="comparar_pais_b",
        )
    return pais_a, pais_b


def _render_perfiles(clusters: pd.DataFrame, paises: tuple[str, str]) -> None:
    """Muestra el perfil de cada ventana encima de los gráficos."""
    st.subheader("Perfil por ventana")
    columnas = st.columns(2)
    for columna, pais in zip(columnas, paises):
        datos = (
            clusters.loc[clusters["Area"] == pais]
            .set_index("Ventana")
            .reindex(VENTANAS)
        )
        with columna:
            st.markdown(f"**{pais}**")
            chips = []
            for ventana in VENTANAS:
                perfil = datos.loc[ventana, "Perfil"]
                color = PALETA_CLUSTERS[perfil]
                texto = "#111111" if perfil == PERFILES_CLUSTER["especializacion"] else "#FFFFFF"
                chips.append(
                    f'<div style="background:{color};color:{texto};padding:8px 10px;'
                    f'font-size:16px;font-weight:700;text-align:center;min-height:64px;">'
                    f"{ventana}<br>{perfil}</div>"
                )
            render_html(
                '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;">'
                + "".join(chips)
                + "</div>"
            )


def _grafico_variable(
    clusters: pd.DataFrame,
    paises: tuple[str, str],
    columna: str,
    etiqueta: str,
) -> go.Figure:
    """Construye un gráfico agrupado con el eje propio de una variable."""
    figura = go.Figure()
    for pais in paises:
        datos = (
            clusters.loc[clusters["Area"] == pais]
            .set_index("Ventana")
            .reindex(VENTANAS)
        )
        figura.add_trace(
            go.Bar(
                x=list(VENTANAS),
                y=datos[columna].tolist(),
                text=[f"{valor:.2f}" for valor in datos[columna]],
                textposition="outside",
                textfont={"size": 16},
                name=pais,
                offsetgroup=pais,
                alignmentgroup="paises",
                hovertemplate=f"{pais}<br>%{{x}}<br>{etiqueta}: %{{y:.3f}}<extra></extra>",
            )
        )
    figura.update_layout(
        template=plotly_template(),
        height=330,
        title=etiqueta,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        font={"size": 16, "color": "#111111"},
        xaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": list(VENTANAS),
            "tickmode": "array",
            "tickvals": list(VENTANAS),
            "ticktext": list(VENTANAS),
            "tickfont": {"size": 16},
            "title": {"font": {"size": 16}},
        },
        yaxis={"title": etiqueta, "tickfont": {"size": 16}, "title_font": {"size": 16}},
        legend={"font": {"size": 16}},
        margin={"l": 70, "r": 18, "t": 62, "b": 70},
    )
    return figura


def render() -> None:
    """Renderiza la comparación de dos países en modo exploración."""
    inject_css(presentation=False)
    clusters = load_clusters()
    st.title("Comparar países")
    st.caption(
        "Archivo: variables_ventana_con_clusters.csv · "
        "Cada gráfico: 3 ventanas × 2 países · valores originales, sin Min-Max."
    )
    paises = _seleccionar_paises(clusters)
    _render_perfiles(clusters, paises)
    for indice in range(0, len(VARIABLES_COMPARACION), 2):
        columnas = st.columns(2)
        for columna, (nombre, etiqueta) in zip(
            columnas,
            VARIABLES_COMPARACION[indice : indice + 2],
        ):
            with columna:
                st.plotly_chart(
                    _grafico_variable(clusters, paises, nombre, etiqueta),
                    width="stretch",
                    config={"displayModeBar": False},
                )
