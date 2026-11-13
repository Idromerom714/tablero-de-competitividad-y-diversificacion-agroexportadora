"""Genera cuatro láminas PNG para respaldo offline de la presentación."""

from pathlib import Path

import plotly.graph_objects as go

from config import (
    ARI_VENEZUELA_COMPARACION,
    OBSERVACIONES_CLUSTERS,
    PERFILES_CLUSTER,
    SILUETA,
    TAMANOS_CLUSTER_ORDENADOS,
    VARIANZA_PCA,
    VARIABLES_AGRUPAMIENTO,
    VENTANAS,
)
from data import (
    load_clusters,
    load_diccionario,
    load_perfil,
    load_rca,
)
from views.productos import _top_productos


OUTPUT_DIR = Path(__file__).resolve().parent / "respaldo"
RANGOS_VENTANA = {
    "2005-11": (2005, 2011),
    "2012-18": (2012, 2018),
    "2019-24": (2019, 2024),
}


def _base(titulo: str, subtitulo: str) -> go.Figure:
    """Crea una figura blanca de 1280 x 720 con encabezado común."""
    figura = go.Figure()
    figura.update_layout(
        width=1280,
        height=720,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": "Arial, Helvetica, sans-serif", "size": 22, "color": "#111111"},
        margin={"l": 70, "r": 50, "t": 125, "b": 60},
        showlegend=False,
    )
    figura.add_annotation(
        x=0,
        y=1.13,
        xref="paper",
        yref="paper",
        text=titulo,
        showarrow=False,
        xanchor="left",
        font={"size": 38, "color": "#111111"},
    )
    figura.add_annotation(
        x=0,
        y=1.06,
        xref="paper",
        yref="paper",
        text=subtitulo,
        showarrow=False,
        xanchor="left",
        font={"size": 20, "color": "#111111"},
    )
    return figura


def _exportar(figura: go.Figure, nombre: str) -> None:
    """Escribe una figura PNG usando el motor Kaleido."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    figura.write_image(OUTPUT_DIR / nombre, width=1280, height=720, scale=1)


def _exportar_resumen() -> None:
    """Genera la lámina de resumen con la matriz de perfiles."""
    clusters = load_clusters()
    orden = ["Chile", "Colombia", "Ecuador", "Argentina", "Paraguay", "Uruguay", "Brasil", "Bolivia", "Perú"]
    matriz = clusters.pivot(index="Area", columns="Ventana", values="Perfil").reindex(index=orden, columns=VENTANAS)
    nombres = {
        PERFILES_CLUSTER["lideres"]: "Alta Diversificación",
        PERFILES_CLUSTER["transicion"]: "Transición",
        PERFILES_CLUSTER["especializacion"]: "Especialización",
    }
    valores = [[nombres.get(valor, "") for valor in matriz[ventana]] for ventana in VENTANAS]
    figura = _base(
        "Diez países, tres estrategias exportadoras",
        "Matriz de perfiles por ventana · FAOSTAT, TCL",
    )
    figura.add_trace(
        go.Table(
            domain={"x": [0, 1], "y": [0.04, 0.94]},
            header={"values": ["País", *VENTANAS], "fill_color": "#111111", "font": {"color": "#FFFFFF", "size": 22}, "align": "center", "height": 42},
            cells={"values": [[*orden], *valores], "fill_color": "#FFFFFF", "font": {"color": "#111111", "size": 20}, "align": "center", "height": 50},
        )
    )
    _exportar(figura, "01_resumen.png")


def _exportar_ficha() -> None:
    """Genera la lámina de ficha país para Ecuador."""
    clusters = load_clusters()
    perfil = load_perfil()
    pais = "Ecuador"
    anual = perfil[perfil["Area"] == pais].sort_values("Year")
    ventana = clusters[clusters["Area"] == pais].sort_values("Ventana")
    figura = _base("Ficha país: Ecuador", "Caso estable · indicadores anuales y de ventana")
    for nombre, (inicio, fin) in RANGOS_VENTANA.items():
        figura.add_vrect(x0=inicio - 0.5, x1=fin + 0.5, fillcolor="#D9D9D9", opacity=0.25, line_width=0)
    figura.add_trace(go.Scatter(x=anual["Year"], y=anual["HHI"], mode="lines+markers", line={"color": "#440154", "width": 4}, marker={"size": 8}, name="HHI"))
    figura.update_layout(xaxis_title="Año", yaxis_title="HHI (índice)", title="Concentración anual de la canasta exportadora", title_font={"size": 26}, legend={"font": {"size": 18}})
    for indice, (_, fila) in enumerate(ventana.iterrows()):
        figura.add_annotation(x=0.08 + indice * 0.3, y=1.02, xref="paper", yref="paper", text=f"{fila['Ventana']}: k60 {fila['k60']:.0f}", showarrow=False, font={"size": 18, "color": "#111111"})
    _exportar(figura, "02_ficha_ecuador.png")


def _exportar_productos() -> None:
    """Genera la lámina de productos competitivos para Ecuador."""
    top = _top_productos(load_rca(), load_diccionario(), "Ecuador", "2019-24").sort_values("RCA", ascending=True)
    figura = _base("Productos competitivos: Ecuador", "Top 5 por RCA promedio · ventana 2019-24")
    figura.add_trace(go.Bar(x=top["RCA"], y=top["Etiqueta"], orientation="h", marker_color="#440154", text=top["RCA"].map(lambda valor: f"{valor:.2f}"), textposition="outside", textfont={"size": 20, "color": "#111111"}))
    figura.update_layout(xaxis_title="RCA promedio (índice)", yaxis_title="Producto | familia", margin={"l": 330, "r": 50, "t": 125, "b": 70})
    _exportar(figura, "03_productos_ecuador.png")


def _exportar_metodologia() -> None:
    """Genera la lámina metodológica de respaldo."""
    figura = _base("Cómo se construyó la clasificación", "Método y límites del análisis")
    cajas = [("FAOSTAT", "Datos"), ("Ventanas disjuntas", f"{len(VENTANAS)} períodos"), (f"{VARIABLES_AGRUPAMIENTO} variables", "Indicadores"), ("PCA + K-means", "Agrupación")]
    for indice, (titulo, detalle) in enumerate(cajas):
        x0 = 0.03 + indice * 0.24
        figura.add_shape(type="rect", x0=x0, x1=x0 + 0.20, y0=0.48, y1=0.82, xref="paper", yref="paper", line={"color": "#111111", "width": 2}, fillcolor="#FFFFFF")
        figura.add_annotation(x=x0 + 0.10, y=0.68, xref="paper", yref="paper", text=f"<b>{titulo}</b><br>{detalle}", showarrow=False, font={"size": 22, "color": "#111111"})
    cifras = f"<b>{OBSERVACIONES_CLUSTERS}</b> observaciones    <b>{VARIANZA_PCA:.1f} %</b> varianza    <b>{SILUETA:.3f}</b> silueta    <b>{'/'.join(map(str, TAMANOS_CLUSTER_ORDENADOS))}</b> grupos"
    figura.add_annotation(x=0.5, y=0.30, xref="paper", yref="paper", text=cifras, showarrow=False, font={"size": 25, "color": "#111111"})
    figura.add_annotation(x=0.5, y=0.15, xref="paper", yref="paper", text=f"Muestra pequeña · estructura débil · diccionario parcial · Venezuela excluida (ARI {ARI_VENEZUELA_COMPARACION:.2f})", showarrow=False, font={"size": 20, "color": "#111111"})
    _exportar(figura, "04_metodologia.png")


def main() -> None:
    """Genera las cuatro imágenes de respaldo."""
    _exportar_resumen()
    _exportar_ficha()
    _exportar_productos()
    _exportar_metodologia()
    print(f"PNG generados en {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
