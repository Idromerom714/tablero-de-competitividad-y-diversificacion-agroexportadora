"""Carga, normalización y validación de los datos del tablero."""

import csv
from pathlib import Path

import pandas as pd
import streamlit as st

from config import (
    ARCHIVO_CLUSTERS,
    ARCHIVO_DICCIONARIO_BORRADOR,
    ARCHIVO_PERFIL,
    ARCHIVO_PRECIO_VOLUMEN,
    ARCHIVO_RCA,
    MILES_US_A_MILES_MILLONES,
    OBSERVACIONES_CLUSTERS,
    PERFILES_CLUSTER,
    TAMANOS_CLUSTER,
    VENTANAS,
    normalizar_pais,
)


COLUMNAS_REQUERIDAS = {
    "variables_ventana_con_clusters.csv": {
        "Area", "Ventana", "k60", "Dep_Mediana", "Part_1_Producto", "Cluster"
    },
    "perfil_final_aux.csv": {
        "Area", "Year", "Total Exported Value", "HHI", "Net Dependency Ratio"
    },
    "rca_final.csv": {"Area", "Year", "Item", "RCA"},
    "precio_vs_volumen_final.csv": {
        "Area", "Year", "Item", "Export Quantity", "Export Value",
        "Implied Export Price", "Producer Price"
    },
}


def _imprimir_esquema(nombre: str, datos: pd.DataFrame) -> None:
    """Imprime columnas, tipos y primeras filas para auditar una carga."""
    print(f"\n=== {nombre} ===")
    print("columnas:", datos.columns.tolist())
    print("dtypes:")
    print(datos.dtypes.to_string())
    print("head:")
    print(datos.head().to_string(index=False))


def _normalizar_columna_pais(datos: pd.DataFrame) -> pd.DataFrame:
    """Aplica el normalizador único a la columna `Area`."""
    if "Area" not in datos.columns:
        raise AssertionError("El CSV no contiene la columna requerida 'Area'.")
    datos = datos.copy()
    datos["Area"] = datos["Area"].map(normalizar_pais)
    return datos


def _validar_columnas(datos: pd.DataFrame, nombre: str, requeridas: set[str]) -> None:
    """Lanza un error explícito si faltan columnas que la aplicación usa."""
    faltantes = sorted(requeridas.difference(datos.columns))
    if faltantes:
        raise AssertionError(f"{nombre}: faltan columnas requeridas: {faltantes}")


def _leer_csv(ruta: Path, nombre: str) -> pd.DataFrame:
    """Lee un CSV, imprime su esquema y normaliza los nombres de país."""
    datos = pd.read_csv(ruta)
    _imprimir_esquema(nombre, datos)
    _validar_columnas(datos, nombre, COLUMNAS_REQUERIDAS[nombre])
    return _normalizar_columna_pais(datos)


def _asignar_perfiles(datos: pd.DataFrame) -> pd.DataFrame:
    """Asigna perfiles comparando promedios, sin usar el número del cluster."""
    promedios = datos.groupby("Cluster")[["k60", "Dep_Mediana"]].mean()
    cluster_lider = promedios["k60"].idxmax()
    cluster_especializado = promedios["Dep_Mediana"].idxmax()
    restantes = [cluster for cluster in promedios.index if cluster not in {
        cluster_lider,
        cluster_especializado,
    }]
    if len(restantes) != 1 or cluster_lider == cluster_especializado:
        raise AssertionError("La regla de perfiles no identifica tres clusters distintos.")

    etiquetas = {
        cluster_lider: PERFILES_CLUSTER["lideres"],
        cluster_especializado: PERFILES_CLUSTER["especializacion"],
        restantes[0]: PERFILES_CLUSTER["transicion"],
    }
    resultado = datos.copy()
    resultado["Perfil"] = resultado["Cluster"].map(etiquetas)
    if resultado["Perfil"].isna().any():
        raise AssertionError("Hay clusters sin perfil asignado.")
    return resultado


@st.cache_data
def load_clusters() -> pd.DataFrame:
    """Carga clusters, normaliza países y asigna perfiles por regla."""
    datos = _leer_csv(ARCHIVO_CLUSTERS, ARCHIVO_CLUSTERS.name)
    return _asignar_perfiles(datos)


@st.cache_data
def load_perfil() -> pd.DataFrame:
    """Carga el panel país-año y normaliza el nombre de intensidad."""
    datos = _leer_csv(ARCHIVO_PERFIL, ARCHIVO_PERFIL.name)
    if "Median Export Intensity" in datos.columns:
        datos = datos.rename(columns={"Median Export Intensity": "Export Intensity"})
    return datos


@st.cache_data
def load_rca() -> pd.DataFrame:
    """Carga la ventaja comparativa revelada y normaliza países."""
    return _leer_csv(ARCHIVO_RCA, ARCHIVO_RCA.name)


@st.cache_data
def load_precio_volumen() -> pd.DataFrame:
    """Carga precio implícito y volumen, y normaliza países."""
    return _leer_csv(ARCHIVO_PRECIO_VOLUMEN, ARCHIVO_PRECIO_VOLUMEN.name)


def _reparar_fila_diccionario(fila: list[str]) -> list[str]:
    """Corrige la fila conocida que perdió Nivel_proceso por una coma."""
    if not fila or not fila[0].startswith("Communion wafers"):
        return fila
    return [
        "Communion wafers, empty cachets of a kind suitable for pharmaceutical use, sealing wafers, rice paper and similar products.",
        "23490.01",
        "Oblatas",
        "Alimentos Preparados",
        "2",
    ]


@st.cache_data
def load_diccionario() -> pd.DataFrame:
    """Carga el diccionario con parser CSV y repara su fila malformada."""
    with ARCHIVO_DICCIONARIO_BORRADOR.open("r", encoding="utf-8", newline="") as archivo:
        filas = list(csv.reader(archivo))
    encabezado, *filas_datos = filas
    _validar_columnas(
        pd.DataFrame(columns=encabezado),
        ARCHIVO_DICCIONARIO_BORRADOR.name,
        {"Item", "CPC", "Producto_ES", "Familia_ES", "Nivel_proceso"},
    )
    reparadas = [_reparar_fila_diccionario(fila) for fila in filas_datos]
    datos = pd.DataFrame(reparadas, columns=encabezado)
    datos["CPC"] = datos["CPC"].astype(str).str.lstrip("'")
    _imprimir_esquema(ARCHIVO_DICCIONARIO_BORRADOR.name, datos)
    return datos


def _validar_trayectorias(clusters: pd.DataFrame) -> None:
    """Comprueba la trayectoria esperada de cada país en las tres ventanas."""
    esperadas = {
        "Argentina": [PERFILES_CLUSTER["transicion"]] * 3,
        "Paraguay": [PERFILES_CLUSTER["transicion"]] * 3,
        "Uruguay": [PERFILES_CLUSTER["transicion"]] * 3,
        "Chile": [PERFILES_CLUSTER["lideres"]] * 3,
        "Colombia": [PERFILES_CLUSTER["especializacion"]] * 3,
        "Ecuador": [PERFILES_CLUSTER["especializacion"]] * 3,
        "Brasil": [PERFILES_CLUSTER["lideres"], PERFILES_CLUSTER["transicion"], PERFILES_CLUSTER["transicion"]],
        "Bolivia": [PERFILES_CLUSTER["especializacion"], PERFILES_CLUSTER["transicion"], PERFILES_CLUSTER["transicion"]],
        "Perú": [PERFILES_CLUSTER["especializacion"], PERFILES_CLUSTER["lideres"], PERFILES_CLUSTER["lideres"]],
    }
    for pais, trayectoria in esperadas.items():
        observado = (
            clusters.loc[clusters["Area"] == pais]
            .set_index("Ventana")
            .reindex(VENTANAS)["Perfil"]
            .tolist()
        )
        assert observado == trayectoria, f"Trayectoria inesperada para {pais}: {observado}"


def validate() -> None:
    """Valida tamaño, composición y trayectorias del modelo de clusters."""
    clusters = load_clusters()
    load_perfil()
    load_rca()
    load_precio_volumen()
    load_diccionario()
    assert len(clusters) == OBSERVACIONES_CLUSTERS, (
        f"El CSV de clusters no tiene {OBSERVACIONES_CLUSTERS} filas."
    )
    tamanos = set(clusters.groupby("Perfil").size().tolist())
    assert tamanos == set(TAMANOS_CLUSTER), f"Tamaños de perfil inesperados: {tamanos}"
    assert set(clusters["Ventana"]) == set(VENTANAS), "Las ventanas no coinciden."
    _validar_trayectorias(clusters)


def valor_exportado_a_miles_millones(valor: float) -> float:
    """Convierte miles de US$ a miles de millones de US$."""
    return valor / MILES_US_A_MILES_MILLONES