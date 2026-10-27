# Tablero de competitividad y diversificación agroexportadora

Dashboard interactivo para explorar la competitividad agroexportadora de países
de Sudamérica. La aplicación está construida con [Streamlit](https://streamlit.io/)
y utiliza archivos CSV como fuente de datos.

## Funcionalidades

El tablero permite seleccionar países y un rango de años, y ofrece cinco vistas:

- **Panorama Regional:** compara el valor exportado, la concentración (HHI), el
	crecimiento y la dependencia entre países mediante mapas y rankings.
- **Perfil por País:** muestra la evolución temporal de indicadores de un país y
	permite comparar varios países con un gráfico radar normalizado.
- **Comercio y Precios:** analiza la Ventaja Comparativa Revelada (RCA) por
	producto y relaciona la cantidad exportada con el precio implícito.
- **Datos filtrados:** permite consultar y descargar en CSV los datos que
	corresponden a los filtros seleccionados.
- **Tipologías y Clusters:** visualiza en un mapa la clasificación de cada país
	para las ventanas `2005-11`, `2012-18` y `2019-24`.

## Requisitos

- Python 3.9 o posterior.
- Las dependencias listadas en `requirements.txt`.

Se recomienda crear un entorno virtual antes de instalar las dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows, la activación del entorno virtual es:

```powershell
.venv\Scripts\Activate.ps1
```

## Ejecución

Desde la carpeta raíz del proyecto, ejecuta:

```bash
streamlit run app.py
```

Streamlit mostrará en la terminal la dirección local de la aplicación,
normalmente `http://localhost:8501`.

## Estructura del proyecto

```text
.
├── app.py
├── requirements.txt
├── README.md
└── data/
		├── perfil_final_aux.csv
		├── rca_final.csv
		├── precio_vs_volumen_final.csv
		└── variables_ventana_con_clusters.csv
```

## Fuentes de datos

La aplicación busca los CSV en la carpeta `data/`, relativa a la ubicación de
`app.py`:

| Archivo | Contenido principal |
| --- | --- |
| `perfil_final_aux.csv` | Indicadores por país y año: valor exportado, crecimiento, HHI, dependencia e intensidad exportadora. |
| `rca_final.csv` | RCA por país, año y producto. |
| `precio_vs_volumen_final.csv` | Cantidad, valor, precio implícito y precio del productor por país, año y producto. |
| `variables_ventana_con_clusters.csv` | Indicadores calculados por ventana temporal y cluster de competitividad. |

El archivo de clustering debe incluir, como mínimo, las columnas `Area`,
`Ventana`, `Cluster`, `HHI_Familias` y `k60`. La aplicación traduce los valores
de `Cluster` a estas tipologías:

- `0`: Consolidado/Diversificado
- `1`: Volátil/Especialista
- `2`: Crisis/Dependiente

## Uso del tablero

1. Selecciona uno o varios países en la barra lateral.
2. Ajusta el rango de años.
3. Navega entre las pestañas para consultar los indicadores.
4. En **Datos filtrados**, selecciona un dataset y utiliza el botón de descarga
	 para exportar la tabla resultante.

Los datos se cargan automáticamente al iniciar la aplicación. Las columnas
numéricas se convierten durante la carga y los nombres de país se mapean a
códigos ISO-3 para construir los mapas.

## Configuración de rutas

Si se cambia la ubicación de los datos, modifica las constantes de rutas al
inicio de `app.py`: `RUTA_PERFIL`, `RUTA_RCA`, `RUTA_PRECIO_VOLUMEN` y
`RUTA_VARIABLES_VENTANA_CON_CLUSTERS`.