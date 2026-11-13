"""Ficha país con evolución anual y métricas de las ventanas del modelo."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Optional

from config import PALETA_CLUSTERS, PERFILES_CLUSTER, VENTANAS
from data import load_clusters, load_perfil
from theme import inject_css, plotly_template, render_html


METRICAS_VENTANA = {
    "k60": "k60",
    "HHI_Familias": "HHI de familias",
    "Dep_Mediana": "Dependencia mediana",
    "Int_Mediana": "Intensidad mediana",
}
PERFILES_CORTOS = {
    PERFILES_CLUSTER["lideres"]: "Alta Diversificación",
    PERFILES_CLUSTER["transicion"]: "Transición",
    PERFILES_CLUSTER["especializacion"]: "Especialización",
}
RANGOS_VENTANA = {
    "2005-11": (2005, 2011),
    "2012-18": (2012, 2018),
    "2019-24": (2019, 2024),
}
COLORES_SOMBRA = {
    "2005-11": "rgba(33, 144, 141, 0.12)",
    "2012-18": "rgba(68, 1, 84, 0.10)",
    "2019-24": "rgba(253, 231, 37, 0.18)",
}
VARIABLES_PCA = (
    "k60",
    "HHI_Familias",
    "Part_1_Producto",
    "Volatilidad_YoY_Log",
    "Dep_Mediana",
    "Int_Mediana",
    "Proc_Ponderado",
)


def _formatear_valor(metrica: str, valor: float) -> str:
    """Formatea un KPI según la unidad de su variable."""
    if pd.isna(valor):
        return "sin dato"
    if metrica == "k60":
        return f"{valor:.0f}"
    if metrica in {"Dep_Mediana", "Int_Mediana"}:
        return f"{valor * 100:.1f} %"
    return f"{valor:.3f}"


def _formatear_delta(metrica: str, delta: Optional[float]) -> Optional[str]:
    """Formatea el cambio respecto de la ventana anterior."""
    if delta is None or pd.isna(delta):
        return None
    if metrica in {"Dep_Mediana", "Int_Mediana"}:
        return f"{delta * 100:+.1f} pp"
    return f"{delta:+.2f}"


def _selector_pais(
    perfil: pd.DataFrame,
    clusters: pd.DataFrame,
    pais_inicial: Optional[str] = None,
) -> str:
    """Renderiza botones de guion y el selector grande de país."""
    paises = sorted(set(perfil["Area"]) | set(clusters["Area"]))
    if pais_inicial is not None:
        st.session_state["ficha_pais"] = pais_inicial
    elif "ficha_pais" not in st.session_state:
        st.session_state["ficha_pais"] = "Ecuador"
    render_html(
        """
        <style>
        div[data-testid="stSelectbox"] label { font-size: 24px !important; color: #111111 !important; }
        div[data-testid="stSelectbox"] [role="combobox"] { font-size: 24px !important; min-height: 58px; }
        div[data-testid="stButton"] button { min-height: 58px; font-size: 22px; font-weight: 700; }
        </style>
        """,
    )
    st.markdown("### Casos del guion")
    botones = st.columns(2)
    for columna, pais, etiqueta in zip(
        botones,
        ["Ecuador", "Perú"],
        ["Ecuador · estable", "Perú · cambia"],
    ):
        with columna:
            if st.button(etiqueta, width="stretch", key=f"caso_{pais}"):
                st.session_state["ficha_pais"] = pais
    st.selectbox(
        "País de la ficha",
        paises,
        index=paises.index(st.session_state["ficha_pais"]),
        key="ficha_pais",
    )
    return st.session_state["ficha_pais"]


def _render_cinta(perfil_pais: pd.DataFrame) -> None:
    """Renderiza los tres perfiles como una cinta de ventanas."""
    columnas = st.columns(3)
    for columna, ventana in zip(columnas, VENTANAS):
        fila = perfil_pais.loc[perfil_pais["Ventana"] == ventana]
        with columna:
            if fila.empty:
                st.markdown(f"**{ventana}**\n\nSin perfil")
                continue
            perfil = fila.iloc[0]["Perfil"]
            color = PALETA_CLUSTERS[perfil]
            texto = "#111111" if perfil == PERFILES_CLUSTER["especializacion"] else "#FFFFFF"
            render_html(
                f"""
                <div style="background:{color};color:{texto};padding:14px 16px;min-height:84px;border:2px solid #111111;">
                    <div style="font-size:20px;font-weight:700;">{ventana}</div>
                    <div style="font-size:25px;font-weight:700;line-height:1.15;">{PERFILES_CORTOS[perfil]}</div>
                </div>
                """,
            )


def _render_kpis(clusters_pais: pd.DataFrame) -> None:
    """Renderiza los cuatro KPI de cada ventana en una disposición compacta."""
    st.subheader("Indicadores por ventana")
    series = {metrica: clusters_pais[metrica].tolist() for metrica in METRICAS_VENTANA}
    columnas = st.columns(3)
    for indice, (columna, ventana) in enumerate(zip(columnas, VENTANAS)):
        fila = clusters_pais.loc[clusters_pais["Ventana"] == ventana]
        if fila.empty:
            continue
        fila = fila.iloc[0]
        with columna:
            render_html(
                f'<div style="border:2px solid #111111;border-top:10px solid #440154;padding:10px 12px 4px;background:#FFFFFF;color:#111111;"><div style="font-size:23px;font-weight:700;margin-bottom:4px;">{ventana}</div>',
            )
            for metrica in METRICAS_VENTANA:
                indice_anterior = indice - 1 if indice > 0 else None
                delta = None if indice_anterior is None else fila[metrica] - series[metrica][indice_anterior]
                delta_texto = _formatear_delta(metrica, delta) or "base"
                render_html(
                    f'<div style="font-size:17px;font-weight:700;color:#111111;margin-top:5px;">{METRICAS_VENTANA[metrica]}: {_formatear_valor(metrica, fila[metrica])} <span style="font-weight:400;">({delta_texto})</span></div>',
                )
            render_html("</div>")


@st.cache_data
def _calcular_pca(clusters: pd.DataFrame) -> tuple[pd.DataFrame, tuple[float, float]]:
    """Estandariza las variables del modelo y calcula sus dos componentes."""
    escalados = StandardScaler().fit_transform(clusters.loc[:, VARIABLES_PCA])
    pca = PCA(n_components=2)
    coordenadas = pca.fit_transform(escalados)
    resultado = clusters[["Area", "Ventana", "Perfil"]].copy()
    resultado["PC1"] = coordenadas[:, 0]
    resultado["PC2"] = coordenadas[:, 1]
    varianza = tuple(float(valor * 100) for valor in pca.explained_variance_ratio_)
    return resultado, varianza


def _render_trayectoria_pca(clusters: pd.DataFrame, pais: str) -> None:
    """Renderiza todos los puntos PCA y la trayectoria del país elegido."""
    coordenadas, varianza = _calcular_pca(clusters)
    if tuple(round(valor, 1) for valor in varianza) != (36.7, 25.3):
        st.warning(
            "La varianza explicada del PCA no coincide con la esperada: "
            f"PC1 {varianza[0]:.1f} % y PC2 {varianza[1]:.1f} %."
        )
    seleccion = coordenadas.loc[coordenadas["Area"] == pais].sort_values(
        "Ventana",
        key=lambda valores: valores.map({ventana: indice for indice, ventana in enumerate(VENTANAS)}),
    )
    figura = go.Figure(
        go.Scatter(
            x=coordenadas["PC1"],
            y=coordenadas["PC2"],
            mode="markers",
            marker={"size": 10, "color": "#D9D9D9"},
            text=coordenadas["Area"] + " · " + coordenadas["Ventana"],
            hovertemplate="%{text}<extra></extra>",
            name="Otros países y ventanas",
        )
    )
    if not seleccion.empty:
        colores = [PALETA_CLUSTERS[fila] for fila in seleccion["Perfil"]]
        figura.add_trace(
            go.Scatter(
                x=seleccion["PC1"],
                y=seleccion["PC2"],
                mode="lines",
                line={"color": "#111111", "width": 3},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        figura.add_trace(
            go.Scatter(
                x=seleccion["PC1"],
                y=seleccion["PC2"],
                mode="markers+text",
                text=seleccion["Ventana"],
                textposition="top center",
                textfont={"size": 18, "color": "#111111"},
                marker={"size": 16, "color": colores, "line": {"color": "#111111", "width": 2}},
                customdata=seleccion["Perfil"],
                hovertemplate="%{text}<br>Perfil: %{customdata}<extra></extra>",
                showlegend=False,
            )
        )
        for anterior, siguiente in zip(seleccion.iloc[:-1].itertuples(), seleccion.iloc[1:].itertuples()):
            figura.add_annotation(
                x=siguiente.PC1,
                y=siguiente.PC2,
                ax=anterior.PC1,
                ay=anterior.PC2,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                arrowhead=3,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor="#111111",
                showarrow=True,
            )
    figura.update_layout(
        template=plotly_template(),
        height=560,
        title="Trayectoria en el plano PCA",
        font={"size": 18, "color": "#111111"},
        xaxis={
            "title": f"PC1 ({varianza[0]:.1f} %)".replace(".", ","),
            "title_font": {"size": 18},
            "tickfont": {"size": 18},
        },
        yaxis={
            "title": f"PC2 ({varianza[1]:.1f} %)".replace(".", ","),
            "title_font": {"size": 18},
            "tickfont": {"size": 18},
        },
        legend={"font": {"size": 18}},
        margin={"l": 90, "r": 40, "t": 85, "b": 85},
    )
    st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})


def _render_series_anuales(perfil_pais: pd.DataFrame) -> None:
    """Renderiza HHI anual con las tres ventanas sombreadas."""
    st.subheader("Evolución anual")
    figura_hhi = go.Figure()
    for ventana, (inicio, fin) in RANGOS_VENTANA.items():
        figura_hhi.add_vrect(
            x0=inicio - 0.5,
            x1=fin + 0.5,
            fillcolor=COLORES_SOMBRA[ventana],
            line_width=0,
            annotation_text=ventana,
            annotation_position="top left",
        )
    figura_hhi.add_trace(
        go.Scatter(
            x=perfil_pais["Year"],
            y=perfil_pais["HHI"],
            mode="lines+markers",
            line={"color": "#111111", "width": 4},
            marker={"color": "#440154", "size": 8},
            name="HHI",
            hovertemplate="Año %{x}<br>HHI: %{y:.3f}<extra></extra>",
        )
    )
    figura_hhi.update_layout(
        template=plotly_template(),
        height=430,
        title="Concentración de la canasta exportadora",
        xaxis_title="Año",
        yaxis_title="HHI (índice)",
        showlegend=False,
    )
    st.plotly_chart(figura_hhi, width="stretch", config={"displayModeBar": False})


def render(
    presentation: bool = True,
    pais: Optional[str] = None,
    ventana: Optional[str] = None,
) -> None:
    """Renderiza la ficha completa del país seleccionado."""
    inject_css(presentation=presentation)
    clusters = load_clusters()
    perfil = load_perfil()
    pais = _selector_pais(perfil, clusters, pais)
    st.title(f"Ficha país: {pais}")
    st.caption("Fuente: FAOSTAT, TCL. HHI y valor exportado provienen del panel anual.")
    perfil_pais = perfil.loc[perfil["Area"] == pais].sort_values("Year").copy()
    if pais == "Venezuela":
        st.warning("Sin perfil asignado: dependencia hasta Nx (ver Metodología)")
        _render_series_anuales(perfil_pais)
        return
    clusters_pais = clusters.loc[clusters["Area"] == pais].copy()
    _render_cinta(clusters_pais)
    _render_kpis(clusters_pais)
    _render_trayectoria_pca(clusters, pais)
    _render_series_anuales(perfil_pais)