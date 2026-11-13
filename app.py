"""Aplicación principal del Observatorio de Competitividad Agroexportadora."""

from typing import Optional

import streamlit as st

from config import VENTANAS
from data import load_clusters, load_perfil, validate
from theme import inject_css
from views import comparar_paises, ficha_pais, metodologia, resumen


PANTALLAS = ("Resumen", "Ficha", "Metodología")
DEMO_PAISES = ("Ecuador", "Perú", "Venezuela")


def _pantallas(exploracion: bool) -> tuple[str, ...]:
    """Devuelve las pantallas visibles según el modo actual."""
    if exploracion:
        return (*PANTALLAS, "Comparar países")
    return PANTALLAS


def _modo_demo() -> bool:
    """Detecta la ruta de demo mediante el parámetro de URL."""
    return st.query_params.get("modo") == "demo"


def _validar_datos() -> bool:
    """Valida los clusters antes de permitir cualquier gráfico."""
    try:
        validate()
    except (AssertionError, OSError, ValueError) as error:
        st.error(f"No se puede mostrar el tablero: los datos no pasan la validación. {error}")
        st.info("Revisa los esquemas y ejecuta `python check_data.py` antes de continuar.")
        return False
    return True


def _indice_pantalla(pantallas: tuple[str, ...]) -> int:
    """Obtiene el índice de pantalla persistido en la sesión."""
    indice = st.session_state.get("pantalla_index", 0)
    return max(0, min(indice, len(pantallas) - 1))


def _navegacion_presentacion(pantallas: tuple[str, ...]) -> int:
    """Renderiza navegación, indicador y atajos de las pantallas."""
    indice = _indice_pantalla(pantallas)
    anterior, indicador, siguiente = st.columns([1, 2, 1])
    with anterior:
        if st.button("Anterior", width="stretch", disabled=indice == 0, key="nav_anterior"):
            st.session_state["pantalla_index"] = indice - 1
            st.rerun()
    with indicador:
        st.markdown(
            f'<div style="text-align:center;font-size:24px;font-weight:700;color:#111111;padding:10px 0;">{indice + 1} / {len(pantallas)}</div>',
            unsafe_allow_html=True,
        )
    with siguiente:
        if st.button("Siguiente", width="stretch", disabled=indice == len(pantallas) - 1, key="nav_siguiente"):
            st.session_state["pantalla_index"] = indice + 1
            st.rerun()

    atajos = st.columns(len(pantallas))
    for posicion, (atajo, columna) in enumerate(zip(pantallas, atajos)):
        with columna:
            if st.button(atajo, width="stretch", key=f"atajo_{atajo}"):
                st.session_state["pantalla_index"] = posicion
                st.rerun()
    return _indice_pantalla(pantallas)


def _navegacion_demo() -> int:
    """Renderiza la navegación reducida del guion Ecuador-Perú-Venezuela."""
    paso = max(0, min(st.session_state.get("demo_step", 0), len(DEMO_PAISES) - 1))
    anterior, indicador, siguiente = st.columns([1, 2, 1])
    with anterior:
        if st.button("Anterior", width="stretch", disabled=paso == 0, key="demo_anterior"):
            st.session_state["demo_step"] = paso - 1
            st.rerun()
    with indicador:
        st.markdown(
            f'<div style="text-align:center;font-size:24px;font-weight:700;color:#111111;padding:10px 0;">{paso + 1} / {len(DEMO_PAISES)}</div>',
            unsafe_allow_html=True,
        )
    with siguiente:
        if st.button("Siguiente", width="stretch", disabled=paso == len(DEMO_PAISES) - 1, key="demo_siguiente"):
            st.session_state["demo_step"] = paso + 1
            st.rerun()
    st.markdown(
        f'<div style="text-align:center;font-size:20px;color:#111111;margin:8px 0 18px;">Ecuador → Perú → Venezuela · paso {paso + 1}</div>',
        unsafe_allow_html=True,
    )
    return paso


def _modo_exploracion() -> bool:
    """Renderiza el conmutador discreto y devuelve el modo elegido."""
    izquierda, derecha = st.columns([6, 1])
    with derecha:
        return st.toggle(
            "Exploración",
            value=st.session_state.get("modo_exploracion", False),
            key="modo_exploracion",
            help="Muestra filtros para la sesión de preguntas.",
        )


def _filtros_exploracion() -> tuple[Optional[str], Optional[str]]:
    """Muestra filtros laterales y devuelve país y ventana seleccionados."""
    perfil = load_perfil()
    clusters = load_clusters()
    paises = sorted(set(perfil["Area"]) | set(clusters["Area"]))
    with st.sidebar:
        st.header("Filtros de exploración")
        pais = st.selectbox("País", paises, index=paises.index("Ecuador"))
        ventana = st.selectbox("Ventana", list(VENTANAS), index=2)
    return pais, ventana


def _render_pantalla(
    pantallas: tuple[str, ...],
    indice: int,
    presentation: bool,
    pais: Optional[str],
    ventana: Optional[str],
) -> None:
    """Renderiza una pantalla del guion principal."""
    pantalla = pantallas[indice]
    if pantalla == "Resumen":
        resumen.render(presentation=presentation)
    elif pantalla == "Ficha":
        ficha_pais.render(presentation=presentation, pais=pais, ventana=ventana)
    elif pantalla == "Comparar países":
        comparar_paises.render()
    else:
        metodologia.render(presentation=presentation)


def main() -> None:
    """Ejecuta la aplicación, la validación y la navegación del tablero."""
    st.set_page_config(
        page_title="Observatorio de Competitividad Agroexportadora",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    if not _validar_datos():
        st.stop()

    demo = _modo_demo()
    if demo:
        inject_css(presentation=True)
        paso = _navegacion_demo()
        ficha_pais.render(presentation=True, pais=DEMO_PAISES[paso])
        return

    exploracion = _modo_exploracion()
    inject_css(presentation=not exploracion)
    pantallas = _pantallas(exploracion)
    pais = ventana = None
    if exploracion:
        pais, ventana = _filtros_exploracion()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    indice = _navegacion_presentacion(pantallas)
    _render_pantalla(
        pantallas,
        indice,
        presentation=not exploracion,
        pais=pais,
        ventana=ventana,
    )


if __name__ == "__main__":
    main()
