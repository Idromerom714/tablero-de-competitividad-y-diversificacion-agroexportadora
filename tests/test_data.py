"""Pruebas de contratos de datos y reglas metodológicas."""

import pandas as pd

from config import PERFILES_CLUSTER, normalizar_pais
from data import _asignar_perfiles, validate, valor_exportado_a_miles_millones


def test_validate_datos_reales():
    """Los CSV del repositorio cumplen tamaño, grupos y trayectorias."""
    validate()


def test_mapa_de_paises():
    """Los nombres fuente se presentan con una única convención."""
    assert normalizar_pais("Brazil") == "Brasil"
    assert normalizar_pais("Peru") == "Perú"
    assert normalizar_pais("Bolivia (Plurinational State of)") == "Bolivia"
    assert normalizar_pais("Venezuela (Bolivarian Republic of)") == "Venezuela"


def test_asignacion_de_perfil_no_depende_del_numero():
    """La etiqueta depende de promedios, aunque cambien los IDs de cluster."""
    datos = pd.DataFrame(
        {
            "Cluster": [10, 10, 20, 20, 30, 30],
            "k60": [10, 12, 2, 3, 5, 6],
            "Dep_Mediana": [0.10, 0.20, 0.90, 0.80, 0.30, 0.40],
        }
    )
    resultado = _asignar_perfiles(datos).drop_duplicates("Cluster").set_index("Cluster")
    assert resultado.loc[10, "Perfil"] == PERFILES_CLUSTER["lideres"]
    assert resultado.loc[20, "Perfil"] == PERFILES_CLUSTER["especializacion"]
    assert resultado.loc[30, "Perfil"] == PERFILES_CLUSTER["transicion"]


def test_conversion_a_miles_de_millones():
    """Convierte miles de US$ a miles de millones sin redondear el cálculo."""
    assert valor_exportado_a_miles_millones(123_456_789) == 123.456789
    assert valor_exportado_a_miles_millones(0) == 0
