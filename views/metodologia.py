"""Lámina única con el método, sus cifras y sus limitaciones."""

import streamlit as st

from config import (
    ARI_VENEZUELA_COMPARACION,
    OBSERVACIONES_CLUSTERS,
    SILUETA,
    TAMANOS_CLUSTER_ORDENADOS,
    VARIANZA_PCA,
    VARIABLES_AGRUPAMIENTO,
)
from theme import inject_css, render_html


def _decimal_es(valor: float, decimales: int) -> str:
    """Formatea un número con separador decimal español."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def _render_flujo() -> None:
    """Renderiza el flujo metodológico en cuatro cajas conectadas."""
    cajas = [
        ("01", "FAOSTAT", "Datos de comercio agroexportador"),
        ("02", "Ventanas disjuntas", "2005-11 · 2012-18 · 2019-24"),
        ("03", f"{VARIABLES_AGRUPAMIENTO} variables", "Diversificación, dependencia y evolución"),
        ("04", "PCA + K-means", "Reduce dimensiones y agrupa países"),
    ]
    contenido = []
    for numero, titulo, detalle in cajas:
        contenido.append(
            f"""
            <div class="metodo-caja">
                <div class="metodo-numero">{numero}</div>
                <div class="metodo-titulo">{titulo}</div>
                <div class="metodo-detalle">{detalle}</div>
            </div>
            """
        )
    render_html(
        f"""
        <style>
        .metodo-flujo {{
            display: grid;
            grid-template-columns: 1fr 30px 1fr 30px 1fr 30px 1fr;
            align-items: center;
            gap: 8px;
            margin: 8px 0 24px;
        }}
        .metodo-caja {{
            min-height: 132px;
            border: 2px solid #111111;
            padding: 14px 16px;
            background: #FFFFFF;
        }}
        .metodo-numero {{ font-size: 18px; font-weight: 700; color: #440154; }}
        .metodo-titulo {{ font-size: 25px; font-weight: 700; line-height: 1.12; color: #111111; margin-top: 8px; }}
        .metodo-detalle {{ font-size: 18px; line-height: 1.25; color: #111111; margin-top: 10px; }}
        .metodo-flecha {{ font-size: 30px; text-align: center; color: #111111; }}
        .metodo-cifras {{ border: 2px solid #111111; padding: 14px 18px; background: #FFFFFF; }}
        .metodo-cifra {{ border-bottom: 1px solid #111111; padding: 8px 0; }}
        .metodo-cifra:last-child {{ border-bottom: 0; }}
        .metodo-valor {{ display: block; font-size: 40px; font-weight: 700; color: #111111; line-height: 1.05; }}
        .metodo-etiqueta {{ display: block; font-size: 17px; color: #111111; margin-top: 3px; }}
        .metodo-nota {{ font-size: 19px; line-height: 1.35; color: #111111; border-top: 2px solid #111111; padding-top: 12px; margin-top: 16px; }}
        .metodo-definiciones {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 14px; }}
        .metodo-definicion {{ font-size: 18px; line-height: 1.35; color: #111111; }}
        @media (max-width: 900px) {{
            .metodo-flujo {{ grid-template-columns: 1fr; }}
            .metodo-flecha {{ transform: rotate(90deg); }}
            .metodo-definiciones {{ grid-template-columns: 1fr; }}
        }}
        </style>
        <div class="metodo-flujo">
            {contenido[0]}
            <div class="metodo-flecha">→</div>
            {contenido[1]}
            <div class="metodo-flecha">→</div>
            {contenido[2]}
            <div class="metodo-flecha">→</div>
            {contenido[3]}
        </div>
        """,
    )


def _render_cifras() -> None:
    """Renderiza las cuatro cifras principales desde la configuración."""
    tamanos = "/".join(str(valor) for valor in TAMANOS_CLUSTER_ORDENADOS)
    render_html(
        f"""
        <div class="metodo-cifras">
            <div class="metodo-cifra"><span class="metodo-valor">{OBSERVACIONES_CLUSTERS}</span><span class="metodo-etiqueta">observaciones</span></div>
            <div class="metodo-cifra"><span class="metodo-valor">{_decimal_es(VARIANZA_PCA, 1)} %</span><span class="metodo-etiqueta">varianza explicada por PCA</span></div>
            <div class="metodo-cifra"><span class="metodo-valor">{_decimal_es(SILUETA, 3)}</span><span class="metodo-etiqueta">silueta</span></div>
            <div class="metodo-cifra"><span class="metodo-valor">{tamanos}</span><span class="metodo-etiqueta">observaciones por grupo</span></div>
        </div>
        """,
    )


def render(presentation: bool = True) -> None:
    """Renderiza una sola lámina de metodología."""
    inject_css(presentation=presentation)
    st.title("Cómo se construyó la clasificación")
    izquierda, derecha = st.columns([3, 1])
    with izquierda:
        _render_flujo()
    with derecha:
        _render_cifras()
    render_html(
        f"""
        <div class="metodo-nota"><strong>Limitaciones:</strong> muestra pequeña · estructura débil · diccionario parcial.</div>
        <div class="metodo-nota"><strong>Venezuela excluida:</strong> cambia la estructura (ARI {_decimal_es(ARI_VENEZUELA_COMPARACION, 2)} con y sin ella).</div>
        <div class="metodo-definiciones">
            <div class="metodo-definicion"><strong>Cluster:</strong> grupo de países que se parecen entre sí según sus indicadores.</div>
            <div class="metodo-definicion"><strong>Ventana:</strong> período de años que se analiza como un bloque.</div>
        </div>
        """,
    )