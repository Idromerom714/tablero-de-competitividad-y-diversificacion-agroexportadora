"""Vista ejecutiva de estrategias exportadoras y cambios de trayectoria."""

from html import escape

import pandas as pd
import streamlit as st

from config import PALETA_CLUSTERS, PERFILES_CLUSTER, VENTANAS
from data import load_clusters, load_perfil
from theme import inject_css, render_html


PREFIJO_MENSAJE = (
    "Diez países, tres estrategias exportadoras, y casi ningún país cambia de una a otra"
)
PAISES_CAMBIAN = {"Brasil", "Bolivia", "Perú"}
ORDEN_PAISES = [
    "Chile",
    "Colombia",
    "Ecuador",
    "Argentina",
    "Paraguay",
    "Uruguay",
    "Brasil",
    "Bolivia",
    "Perú",
]
NOMBRE_CORTO = {
    PERFILES_CLUSTER["lideres"]: "Alta Diversificación",
    PERFILES_CLUSTER["transicion"]: "Transición",
    PERFILES_CLUSTER["especializacion"]: "Especialización",
}
COLOR_TEXTO_CELDA = {
    PERFILES_CLUSTER["lideres"]: "#FFFFFF",
    PERFILES_CLUSTER["transicion"]: "#FFFFFF",
    PERFILES_CLUSTER["especializacion"]: "#111111",
}


def _formatear_numero(valor: float, decimales: int = 2) -> str:
    """Formatea números con coma decimal para la presentación."""
    if pd.isna(valor):
        return "sin dato"
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _matriz_trayectorias(clusters: pd.DataFrame) -> pd.DataFrame:
    """Construye la matriz país-ventana en el orden narrativo de la vista."""
    matriz = clusters.pivot(index="Area", columns="Ventana", values="Perfil")
    return matriz.reindex(index=ORDEN_PAISES, columns=VENTANAS)


def _celda_perfil(perfil: str) -> str:
    """Genera una celda coloreada con nombre corto y contraste accesible."""
    color = PALETA_CLUSTERS[perfil]
    texto = COLOR_TEXTO_CELDA[perfil]
    nombre = escape(NOMBRE_CORTO[perfil])
    return (
        f'<td style="background:{color};color:{texto};font-weight:700;">'
        f"{nombre}</td>"
    )


def _render_matriz(matriz: pd.DataFrame) -> None:
    """Renderiza la matriz principal con marco para países que cambian."""
    filas = []
    for pais, fila in matriz.iterrows():
        clase = " class=\"cambia\"" if pais in PAISES_CAMBIAN else ""
        celdas = "".join(_celda_perfil(perfil) for perfil in fila)
        filas.append(f'<tr{clase}><th>{escape(pais)}</th>{celdas}</tr>')
    cabecera = "".join(f"<th>{escape(ventana)}</th>" for ventana in VENTANAS)
    render_html(
        f"""
        <style>
        .matriz-trayectorias {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 6px;
            color: #111111;
            font-size: 20px;
        }}
        .matriz-trayectorias th {{
            padding: 8px 12px;
            text-align: center;
            font-weight: 700;
        }}
        .matriz-trayectorias th:first-child {{ text-align: left; width: 18%; }}
        .matriz-trayectorias td {{
            padding: 11px 12px;
            text-align: center;
            border-top: 2px solid #FFFFFF;
            border-bottom: 2px solid #FFFFFF;
        }}
        .matriz-trayectorias tr.cambia td,
        .matriz-trayectorias tr.cambia th {{
            border-top: 4px solid #111111;
            border-bottom: 4px solid #111111;
        }}
        .matriz-trayectorias tr.cambia th {{ border-left: 4px solid #111111; }}
        .matriz-trayectorias tr.cambia td:last-child {{ border-right: 4px solid #111111; }}
        </style>
        <table class="matriz-trayectorias">
            <thead><tr><th>País</th>{cabecera}</tr></thead>
            <tbody>{''.join(filas)}</tbody>
        </table>
        <div style="font-size:18px;color:#111111;margin-top:8px;">
            Marco oscuro = cambia de estrategia entre ventanas.
        </div>
        """,
    )


def _resumen_perfiles(clusters: pd.DataFrame) -> pd.DataFrame:
    """Calcula observaciones y rasgos medios de cada perfil desde los datos."""
    columnas = ["k60", "Part_1_Producto", "Dep_Mediana"]
    resumen = clusters.groupby("Perfil")[columnas].agg(["mean", "size"])
    resultado = resumen.xs("mean", axis=1, level=1).copy()
    resultado["Observaciones"] = resumen["k60"]["size"]
    return resultado.reindex(
        [
            PERFILES_CLUSTER["lideres"],
            PERFILES_CLUSTER["transicion"],
            PERFILES_CLUSTER["especializacion"],
        ]
    )


def _render_tarjetas_perfil(resumen: pd.DataFrame) -> None:
    """Renderiza las tres tarjetas de rasgos medios por perfil."""
    columnas = st.columns(3)
    for perfil, columna in zip(resumen.index, columnas):
        color = PALETA_CLUSTERS[perfil]
        fila = resumen.loc[perfil]
        with columna:
            render_html(
                f"""
                <div style="border:2px solid #111111;border-top:12px solid {color};padding:14px 16px;min-height:188px;background:#FFFFFF;color:#111111;">
                    <div style="font-size:24px;font-weight:700;line-height:1.15;">{escape(NOMBRE_CORTO[perfil])}</div>
                    <div style="font-size:32px;font-weight:700;margin-top:10px;">{int(fila['Observaciones'])}</div>
                    <div style="font-size:18px;">observaciones</div>
                    <div style="font-size:18px;margin-top:9px;">k60 medio: <strong>{_formatear_numero(fila['k60'])}</strong></div>
                    <div style="font-size:18px;">producto líder: <strong>{_formatear_numero(fila['Part_1_Producto'] * 100)} %</strong></div>
                    <div style="font-size:18px;">dependencia: <strong>{_formatear_numero(fila['Dep_Mediana'] * 100)} %</strong></div>
                </div>
                """,
            )


def _render_venezuela(perfil: pd.DataFrame) -> None:
    """Renderiza el caso fuera del modelo con su máximo real de dependencia."""
    venezuela = perfil.loc[perfil["Area"] == "Venezuela"]
    maxima = venezuela["Net Dependency Ratio"].max()
    render_html(
        f"""
        <div style="border:3px solid #111111;padding:14px 18px;margin-top:22px;background:#FFFFFF;color:#111111;">
            <div style="font-size:28px;font-weight:700;">Venezuela: fuera del modelo</div>
            <div style="font-size:20px;margin-top:5px;">Dependencia neta máxima observada: <strong>{_formatear_numero(maxima)}</strong></div>
        </div>
        """,
    )


def render(presentation: bool = True) -> None:
    """Renderiza la pantalla ejecutiva del resumen regional."""
    inject_css(presentation=presentation)
    clusters = load_clusters()
    perfil = load_perfil()
    st.title(PREFIJO_MENSAJE)
    st.caption("Fuente: FAOSTAT, TCL. Ventanas: 2005-11, 2012-18 y 2019-24.")
    _render_matriz(_matriz_trayectorias(clusters))
    _render_tarjetas_perfil(_resumen_perfiles(clusters))
    _render_venezuela(perfil)