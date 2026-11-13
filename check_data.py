"""Comprobación manual de esquemas y reglas de los datos del tablero."""

from data import (
    load_clusters,
    load_diccionario,
    load_perfil,
    load_precio_volumen,
    load_rca,
    validate,
)


def main() -> None:
    """Carga todos los CSV, muestra sus esquemas y ejecuta la validación."""
    load_clusters()
    load_perfil()
    load_rca()
    load_precio_volumen()
    load_diccionario()
    validate()
    print("\nOK: validación de datos completada.")


if __name__ == "__main__":
    main()