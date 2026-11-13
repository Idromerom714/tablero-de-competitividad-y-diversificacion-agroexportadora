"""Tema visual legible para proyección del Observatorio."""

import plotly.graph_objects as go
import streamlit as st

from config import PALETA_CLUSTERS


COLOR_TEXTO = "#111111"
COLOR_FONDO = "#FFFFFF"
COLOR_BORDE = "#111111"


def render_html(html: str) -> None:
    """Renderiza HTML sin que la sangría se interprete como código Markdown."""
    limpio = "\n".join(line.strip() for line in html.splitlines() if line.strip())
    if callable(getattr(st, "html", None)):
        st.html(limpio)
    else:
        st.markdown(limpio, unsafe_allow_html=True)


def plotly_template() -> go.layout.Template:
    """Devuelve la plantilla Plotly con tipografía grande y ejes despejados."""
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=COLOR_FONDO,
            plot_bgcolor=COLOR_FONDO,
            font={"family": "Arial, Helvetica, sans-serif", "size": 18, "color": COLOR_TEXTO},
            colorway=list(PALETA_CLUSTERS.values()),
            hoverlabel={"font": {"size": 18, "color": COLOR_TEXTO}},
            margin={"l": 76, "r": 32, "t": 64, "b": 76},
            title={"font": {"size": 36, "color": COLOR_TEXTO}, "x": 0},
            xaxis={
                "showgrid": False,
                "showline": True,
                "linecolor": COLOR_BORDE,
                "linewidth": 2,
                "ticks": "outside",
                "tickfont": {"size": 18, "color": COLOR_TEXTO},
                "title": {"font": {"size": 20, "color": COLOR_TEXTO}},
            },
            yaxis={
                "showgrid": True,
                "gridcolor": "#D9D9D9",
                "gridwidth": 1,
                "showline": True,
                "linecolor": COLOR_BORDE,
                "linewidth": 2,
                "ticks": "outside",
                "tickfont": {"size": 18, "color": COLOR_TEXTO},
                "title": {"font": {"size": 20, "color": COLOR_TEXTO}},
            },
            legend={"font": {"size": 18, "color": COLOR_TEXTO}},
        )
    )


def inject_css(presentation: bool = True) -> None:
    """Inyecta estilos para lectura a distancia y modo presentación."""
    sidebar_rule = ".stSidebar { display: none; }" if presentation else ""
    render_html(
        f"""
        <style>
        :root {{
            --color-fondo: {COLOR_FONDO};
            --color-texto: {COLOR_TEXTO};
            --color-borde: {COLOR_BORDE};
        }}
        html, body, [class*="css"], .stApp {{
            background: var(--color-fondo);
            color: var(--color-texto);
            font-size: 20px;
        }}
        .stApp {{ color: var(--color-texto); }}
        h1 {{ font-size: 44px !important; color: var(--color-texto) !important; }}
        h2, h3 {{ font-size: 36px !important; color: var(--color-texto) !important; }}
        p, label, .stCaption, [data-testid="stMetricLabel"] {{
            color: var(--color-texto) !important;
            font-size: 20px !important;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--color-texto) !important;
            font-size: 64px !important;
            line-height: 1.05 !important;
        }}
        [data-testid="stMetricDelta"] {{
            color: var(--color-texto) !important;
            font-size: 20px !important;
        }}
        .kpi-card {{
            border: 2px solid var(--color-borde);
            padding: 18px 20px;
            min-height: 150px;
            background: var(--color-fondo);
        }}
        .kpi-value {{
            color: var(--color-texto);
            font-size: 64px;
            font-weight: 700;
            line-height: 1.05;
        }}
        .kpi-label, .kpi-delta {{
            color: var(--color-texto);
            font-size: 20px;
            line-height: 1.25;
        }}
        .cluster-chip {{
            border: 2px solid var(--cluster-border, var(--color-borde));
            background: var(--cluster-background, var(--color-fondo));
            color: var(--cluster-text, var(--color-texto));
            font-size: 20px;
            font-weight: 700;
            padding: 12px 16px;
            min-height: 54px;
            display: flex;
            align-items: center;
        }}
        [data-testid="stToolbar"], #MainMenu, footer {{ visibility: hidden; }}
        {sidebar_rule}
        </style>
        """,
    )


def kpi_card(valor: str, etiqueta: str, delta: str = "") -> None:
    """Renderiza una tarjeta KPI grande con valor, etiqueta y delta."""
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">{valor}</div>
            <div class="kpi-label">{etiqueta}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """,
    )


def cluster_chip(nombre: str) -> None:
    """Renderiza una etiqueta de cluster con contraste adaptado a su color."""
    color = PALETA_CLUSTERS[nombre]
    texto = COLOR_TEXTO if nombre.endswith("Agroexportador") else COLOR_FONDO
    render_html(
        f'<div class="cluster-chip" style="--cluster-background:{color};--cluster-text:{texto};">{nombre}</div>',
    )