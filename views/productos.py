"""Vista de productos competitivos y relación precio-volumen."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Optional

from config import VENTANAS
from data import load_diccionario, load_precio_volumen, load_rca
from theme import inject_css, plotly_template, render_html


RANGOS_VENTANA = {
    "2005-11": (2005, 2011),
    "2012-18": (2012, 2018),
    "2019-24": (2019, 2024),
}


def _nombres_paises(rca: pd.DataFrame) -> list[str]:
    """Devuelve países normalizados disponibles en el RCA."""
    return sorted(rca["Area"].dropna().unique().tolist())


def _filtrar_ventana(datos: pd.DataFrame, pais: str, ventana: str) -> pd.DataFrame:
    """Filtra un dataset país-año a una ventana fija."""
    inicio, fin = RANGOS_VENTANA[ventana]
    return datos.loc[
        (datos["Area"] == pais) & datos["Year"].between(inicio, fin)
    ].copy()


def _seleccion(
    pais_inicial: Optional[str] = None,
    ventana_inicial: Optional[str] = None,
) -> tuple[str, str]:
    """Renderiza los selectores de país y ventana."""
    rca = load_rca()
    render_html(
        """
        <style>
        div[data-testid="stSelectbox"] label { font-size: 24px !important; color: #111111 !important; }
        div[data-testid="stSelectbox"] [role="combobox"] { font-size: 24px !important; min-height: 58px; }
        </style>
        """,
    )
    columnas = st.columns(2)
    with columnas[0]:
        paises = _nombres_paises(rca)
        indice_pais = paises.index(pais_inicial) if pais_inicial in paises else 0
        pais = st.selectbox("País", paises, index=indice_pais)
    with columnas[1]:
        indice_ventana = list(VENTANAS).index(ventana_inicial) if ventana_inicial in VENTANAS else 2
        ventana = st.selectbox("Ventana", list(VENTANAS), index=indice_ventana)
    return pais, ventana


def _unir_diccionario(productos: pd.DataFrame, diccionario: pd.DataFrame) -> pd.DataFrame:
    """Añade nombre español y familia sin inventar correspondencias."""
    columnas = diccionario[["Item", "Producto_ES", "Familia_ES"]].drop_duplicates("Item")
    resultado = productos.merge(columnas, on="Item", how="left", validate="many_to_one")
    resultado["Sin_traduccion"] = resultado["Producto_ES"].isna()
    resultado["Nombre"] = resultado["Producto_ES"].fillna(resultado["Item"] + " ·")
    resultado["Familia"] = resultado["Familia_ES"].fillna("No disponible")
    resultado["Etiqueta"] = resultado["Nombre"] + " | " + resultado["Familia"]
    return resultado


def _top_productos(rca: pd.DataFrame, diccionario: pd.DataFrame, pais: str, ventana: str) -> pd.DataFrame:
    """Calcula los cinco productos con mayor RCA promedio."""
    filtrado = _filtrar_ventana(rca, pais, ventana)
    promedio = (
        filtrado.groupby("Item", as_index=False)["RCA"]
        .mean()
        .sort_values("RCA", ascending=False)
        .head(5)
    )
    return _unir_diccionario(promedio, diccionario)


def _render_barras(top: pd.DataFrame, pais: str, ventana: str) -> None:
    """Renderiza barras horizontales con etiquetas directas de RCA."""
    if top.empty:
        st.info("No hay productos RCA para este país y ventana.")
        return
    ordenado = top.sort_values("RCA", ascending=True)
    figura = go.Figure(
        go.Bar(
            x=ordenado["RCA"],
            y=ordenado["Etiqueta"],
            orientation="h",
            marker_color="#440154",
            text=ordenado["RCA"].map(lambda valor: f"{valor:.2f}"),
            textposition="outside",
            textfont={"size": 18, "color": "#111111"},
            customdata=ordenado[["Item", "Familia", "Sin_traduccion"]],
            hovertemplate=(
                "%{y}<br>RCA promedio: %{x:.3f}<br>"
                "Item original: %{customdata[0]}<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        template=plotly_template(),
        height=440,
        title=f"Top 5 productos por RCA promedio · {pais} · {ventana}",
        xaxis_title="RCA promedio de la ventana (índice)",
        yaxis_title="Producto | familia",
        showlegend=False,
        margin={"l": 290, "r": 40, "t": 72, "b": 70},
    )
    st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})


def _datos_precio(
    top: pd.DataFrame,
    precio: pd.DataFrame,
    diccionario: pd.DataFrame,
    pais: str,
    ventana: str,
) -> pd.DataFrame:
    """Agrega cantidad y valor de los cinco productos en la ventana."""
    filtrado = _filtrar_ventana(precio, pais, ventana)
    datos = filtrado[filtrado["Item"].isin(top["Item"])].copy()
    if datos.empty:
        return datos
    agregado = (
        datos.groupby("Item", as_index=False)
        .agg(
            **{
                "Export Quantity": ("Export Quantity", "sum"),
                "Export Value": ("Export Value", "sum"),
                "Producer Price": ("Producer Price", "mean"),
            }
        )
    )
    agregado["Implied Export Price"] = (
        agregado["Export Value"] / agregado["Export Quantity"].replace(0, pd.NA)
    )
    return _unir_diccionario(agregado, diccionario)


def _render_precio_volumen(
    top: pd.DataFrame,
    precio: pd.DataFrame,
    diccionario: pd.DataFrame,
    pais: str,
    ventana: str,
) -> None:
    """Renderiza el precio implícito frente a cantidad para los cinco productos."""
    datos = _datos_precio(top, precio, diccionario, pais, ventana)
    datos = datos.dropna(subset=["Export Quantity", "Implied Export Price"])
    if datos.empty:
        st.info("No hay cantidad y precio implícito disponibles para estos productos.")
        return
    figura = go.Figure(
        go.Scatter(
            x=datos["Export Quantity"],
            y=datos["Implied Export Price"],
            mode="markers+text",
            text=datos["Nombre"],
            textposition="top center",
            textfont={"size": 18, "color": "#111111"},
            marker={"size": 14, "color": "#21908D", "line": {"color": "#111111", "width": 2}},
            customdata=datos[["Item", "Familia"]],
            hovertemplate=(
                "%{text}<br>Cantidad exportada: %{x:.2f}<br>"
                "Precio implícito: %{y:.3f}<br>Familia: %{customdata[1]}<extra></extra>"
            ),
            showlegend=False,
        )
    )
    figura.update_layout(
        template=plotly_template(),
        height=470,
        title="Precio implícito frente a volumen exportado",
        xaxis_title="Cantidad exportada (unidad del CSV)",
        yaxis_title="Precio implícito (valor/cantidad, unidad del CSV)",
        showlegend=False,
    )
    st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})


def render(
    presentation: bool = True,
    pais: Optional[str] = None,
    ventana: Optional[str] = None,
) -> None:
    """Renderiza la vista de productos para país y ventana seleccionados."""
    inject_css(presentation=presentation)
    pais, ventana = _seleccion(pais, ventana)
    rca = load_rca()
    precio = load_precio_volumen()
    diccionario = load_diccionario()
    top = _top_productos(rca, diccionario, pais, ventana)
    st.title("Productos competitivos")
    st.caption("RCA promedio de la ventana. Los nombres traducidos provienen del diccionario disponible.")
    _render_barras(top, pais, ventana)
    with st.expander("Ver precio vs volumen"):
        _render_precio_volumen(top, precio, diccionario, pais, ventana)