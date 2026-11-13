"""Configuración central del Observatorio de Competitividad Agroexportadora."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

ARCHIVO_CLUSTERS = BASE_DIR / "variables_ventana_con_clusters.csv"
ARCHIVO_PERFIL = BASE_DIR / "perfil_final_aux.csv"
ARCHIVO_RCA = BASE_DIR / "rca_final.csv"
ARCHIVO_PRECIO_VOLUMEN = BASE_DIR / "precio_vs_volumen_final.csv"
ARCHIVO_DICCIONARIO_BORRADOR = BASE_DIR / "diccionario_productos_borrador.csv"

VENTANAS = ("2005-11", "2012-18", "2019-24")

OBSERVACIONES_CLUSTERS = 27
NUMERO_CLUSTERS = 3
TAMANOS_CLUSTER = frozenset({13, 6, 8})
TAMANOS_CLUSTER_ORDENADOS = (13, 6, 8)
VARIANZA_PCA = 62.0
SILUETA = 0.476
VARIABLES_AGRUPAMIENTO = 7
ARI_VENEZUELA_COMPARACION = 0.12
MILES_US_A_MILES_MILLONES = 1_000_000

PERFILES_CLUSTER = {
    "lideres": "Alta Diversificación (Líderes)",
    "transicion": "Transición / Diversificación Media",
    "especializacion": "Especialización / Agroexportador",
}

PALETA_CLUSTERS = {
    PERFILES_CLUSTER["lideres"]: "#21908D",
    PERFILES_CLUSTER["transicion"]: "#440154",
    PERFILES_CLUSTER["especializacion"]: "#FDE725",
    "Caso fuera del modelo": "#111111",
}

MAPA_NOMBRES_PAIS = {
    "Argentina": "Argentina",
    "Bolivia": "Bolivia",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Brazil": "Brasil",
    "Chile": "Chile",
    "Colombia": "Colombia",
    "Ecuador": "Ecuador",
    "Paraguay": "Paraguay",
    "Peru": "Perú",
    "Uruguay": "Uruguay",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
}


def normalizar_pais(nombre: object) -> object:
    """Devuelve el nombre de presentación común para cualquier CSV."""
    if nombre is None:
        return nombre
    return MAPA_NOMBRES_PAIS.get(str(nombre).strip(), str(nombre).strip())