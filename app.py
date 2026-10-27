"""Dashboard interactivo de competitividad agroexportadora sudamericana."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------------------------------------------------------
# Configuracion y rutas editables
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Competitividad agroexportadora de Sudamerica",
    page_icon="🌎",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
RUTA_PERFIL = BASE_DIR / "data" / "perfil_final_aux.csv"
RUTA_RCA = BASE_DIR / "data" / "rca_final.csv"
RUTA_PRECIO_VOLUMEN = BASE_DIR / "data" / "precio_vs_volumen_final.csv"
RUTA_VARIABLES_VENTANA = BASE_DIR / "data" / "variables_ventana_con_clusters.csv"
RUTA_VARIABLES_VENTANA_CON_CLUSTERS = (
    BASE_DIR / "data" / "variables_ventana_con_clusters.csv"
)

ISO3 = {
    "Argentina": "ARG",
    "Bolivia (Plurinational State of)": "BOL",
    "Brazil": "BRA",
    "Chile": "CHL",
    "Colombia": "COL",
    "Ecuador": "ECU",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Uruguay": "URY",
    "Venezuela (Bolivarian Republic of)": "VEN",
}


@st.cache_data
def cargar_datos():
    """Carga los datasets del tablero y prepara sus columnas numericas."""
    try:
        perfil = pd.read_csv(RUTA_PERFIL)
        rca = pd.read_csv(RUTA_RCA)
        precio_volumen = pd.read_csv(RUTA_PRECIO_VOLUMEN)
    except FileNotFoundError as error:
        st.error(f"No se encontro el archivo de datos: {error.filename}")
        st.stop()

    if RUTA_VARIABLES_VENTANA.exists():
        variables_ventana = pd.read_csv(RUTA_VARIABLES_VENTANA)
        if (
            "Cluster" not in variables_ventana.columns
            and RUTA_VARIABLES_VENTANA_CON_CLUSTERS.exists()
        ):
            variables_ventana = pd.read_csv(RUTA_VARIABLES_VENTANA_CON_CLUSTERS)
        if "Area" in variables_ventana:
            variables_ventana["ISO3"] = variables_ventana["Area"].map(ISO3)
        if "Cluster" in variables_ventana:
            variables_ventana["Cluster"] = pd.to_numeric(
                variables_ventana["Cluster"], errors="coerce"
            )
        for column in ["HHI_Familias", "k60"]:
            if column in variables_ventana:
                variables_ventana[column] = pd.to_numeric(
                    variables_ventana[column], errors="coerce"
                )
        nombres_clusters = {
            0: "Consolidado/Diversificado",
            1: "Volátil/Especialista",
            2: "Crisis/Dependiente",
        }
        if "Cluster" in variables_ventana:
            variables_ventana["Cluster_Nombre"] = variables_ventana["Cluster"].map(
                nombres_clusters
            )
        else:
            st.warning(
                "El archivo de variables de ventana no contiene la columna "
                "'Cluster'. Las vistas de clustering quedaran sin datos."
            )
            variables_ventana["Cluster_Nombre"] = pd.NA
    else:
        st.warning(
            f"No se encontro el archivo opcional de clustering: "
            f"{RUTA_VARIABLES_VENTANA.name}. Las vistas de clustering quedaran sin datos."
        )
        variables_ventana = pd.DataFrame()

    for dataframe in (perfil, rca, precio_volumen):
        dataframe["ISO3"] = dataframe["Area"].map(ISO3)
        dataframe["Year"] = pd.to_numeric(dataframe["Year"], errors="coerce")

    numeric_columns = {
        "perfil": [
            "Total Exported Value", "YoY Growth %", "Absolute Growth",
            "Accumulated Growth %", "HHI", "Strong Product Value",
            "Net Dependency Ratio", "Median Export Intensity", "YoY Growth Log",
        ],
        "rca": ["RCA"],
        "precio_volumen": [
            "Export Quantity", "Export Value", "Implied Export Price", "Producer Price",
        ],
    }
    for column in numeric_columns["perfil"]:
        if column not in perfil:
            perfil[column] = pd.NA
        perfil[column] = pd.to_numeric(perfil[column], errors="coerce")
    for column in numeric_columns["rca"]:
        rca[column] = pd.to_numeric(rca[column], errors="coerce")
    for column in numeric_columns["precio_volumen"]:
        precio_volumen[column] = pd.to_numeric(precio_volumen[column], errors="coerce")

    return perfil, rca, precio_volumen, variables_ventana


def mostrar_vacio(mensaje):
    """Muestra un aviso uniforme para una vista sin datos."""
    st.info(mensaje)


def normalizar_por_columna(dataframe, columnas):
    """Aplica Min-Max por indicador, conservando valores constantes como cero."""
    resultado = dataframe.copy()
    for columna in columnas:
        minimo = resultado[columna].min()
        maximo = resultado[columna].max()
        if pd.isna(minimo) or pd.isna(maximo) or minimo == maximo:
            resultado[columna] = 0.0
        else:
            resultado[columna] = (resultado[columna] - minimo) / (maximo - minimo)
    return resultado


def render_kpi_card(title, value, subtitle, color):
    """Renderiza una tarjeta KPI con estilos compatibles con el modo oscuro."""
    st.markdown(
        f"""
        <div style="
            background-color: #1E1E2E;
            border-left: 5px solid {color};
            border-radius: 10px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.8rem;
        ">
            <div style="color: #FFFFFF; font-size: 0.9rem; font-weight: 600;">
                {title}
            </div>
            <div style="color: #FFFFFF; font-size: 1.7rem; font-weight: 700; margin: 0.3rem 0;">
                {value}
            </div>
            <div style="color: #B8B8C7; font-size: 0.8rem;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


perfil, rca, precio_volumen, variables_ventana = cargar_datos()
todos_los_paises = list(ISO3)

# -----------------------------------------------------------------------------
# Sidebar: filtros globales
# -----------------------------------------------------------------------------
st.sidebar.header("Filtros globales")
if perfil["Median Export Intensity"].isna().all():
    st.sidebar.warning(
        "El CSV de perfil no contiene datos para 'Median Export Intensity'; "
        "las vistas que lo usan quedarán sin valores."
    )
paises_seleccionados = st.sidebar.multiselect(
    "Países",
    options=todos_los_paises,
    default=todos_los_paises,
)
anios = st.sidebar.slider("Rango de años", min_value=2005, max_value=2024, value=(2005, 2024))

if not paises_seleccionados:
    st.warning("Selecciona al menos un país para visualizar el dashboard.")
    st.stop()

perfil_filtrado = perfil[
    perfil["Area"].isin(paises_seleccionados) & perfil["Year"].between(anios[0], anios[1])
].copy()
rca_filtrado = rca[
    rca["Area"].isin(paises_seleccionados) & rca["Year"].between(anios[0], anios[1])
].copy()
precio_vol_filtrado = precio_volumen[
    precio_volumen["Area"].isin(paises_seleccionados)
    & precio_volumen["Year"].between(anios[0], anios[1])
].copy()

tab_panorama, tab_perfil, tab_comercio, tab_datos, tab_clusters = st.tabs(
    [
        "🌎 Panorama Regional",
        "🔍 Perfil por País",
        "📦 Comercio y Precios",
        "📋 Datos",
        "🧩 Tipologías y Clusters",
    ]
)

# -----------------------------------------------------------------------------
# Tab 1: panorama regional
# -----------------------------------------------------------------------------
with tab_panorama:
    st.header("Panorama Regional")
    if perfil_filtrado.empty:
        mostrar_vacio("No hay datos de perfil para los filtros seleccionados.")
    else:
        ultimo_anio = int(perfil_filtrado["Year"].max())
        perfil_ultimo = perfil_filtrado[perfil_filtrado["Year"] == ultimo_anio].copy()
        valor_total = perfil_ultimo["Total Exported Value"].sum()
        hhi_promedio = perfil_ultimo["HHI"].mean()
        metrica_1, metrica_2, metrica_3 = st.columns(3)
        metrica_1.metric("Valor Total Exportado Regional", f"{valor_total:,.0f}")
        metrica_2.metric("HHI Promedio Regional", f"{hhi_promedio:,.4f}")
        metrica_3.metric("Países seleccionados", len(paises_seleccionados))

        kpi = st.selectbox(
            "Indicador para colorear el mapa",
            [
                "Total Exported Value", "HHI", "YoY Growth %",
                "Net Dependency Ratio", "Median Export Intensity",
            ],
        )
        mapa = px.choropleth(
            perfil_ultimo,
            locations="ISO3",
            color=kpi,
            locationmode="ISO-3",
            scope="south america",
            hover_name="Area",
            hover_data={kpi: ":,.4f"},
            color_continuous_scale="YlGnBu",
            title=f"{kpi} en {ultimo_anio}",
        )
        st.plotly_chart(mapa, use_container_width=True)

        ranking = perfil_ultimo.sort_values(kpi, ascending=False)
        barras = px.bar(
            ranking,
            x=kpi,
            y="Area",
            orientation="h",
            text_auto=".3s",
            title=f"Ranking regional por {kpi} ({ultimo_anio})",
            labels={"Area": "País"},
        )
        barras.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(barras, use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 2: perfil por pais
# -----------------------------------------------------------------------------
with tab_perfil:
    st.header("Perfil por País")
    if perfil_filtrado.empty:
        mostrar_vacio("No hay datos de perfil para los filtros seleccionados.")
    else:
        pais = st.selectbox("País a inspeccionar", paises_seleccionados)
        perfil_pais = perfil_filtrado[perfil_filtrado["Area"] == pais]
        if perfil_pais.empty:
            mostrar_vacio("No hay observaciones para el país elegido en ese rango.")
        else:
            for inicio in range(0, 3, 2):
                columnas = st.columns(min(2, 3 - inicio))
                for columna, indicador in zip(
                    columnas, ["Total Exported Value", "YoY Growth Log", "HHI"][inicio:inicio + 2]
                ):
                    figura = px.line(
                        perfil_pais.sort_values("Year"), x="Year", y=indicador,
                        markers=True, title=indicador,
                    )
                    columna.plotly_chart(figura, use_container_width=True)

            paises_comparar = st.multiselect(
                "Países a comparar (2 a 4)",
                options=paises_seleccionados,
                default=paises_seleccionados[: min(2, len(paises_seleccionados))],
            )
            if len(paises_comparar) < 2:
                st.info("Selecciona al menos 2 países para construir el radar.")
            else:
                indicadores_radar = [
                    "HHI", "Net Dependency Ratio", "Median Export Intensity",
                    "Accumulated Growth %", "Total Exported Value",
                ]
                promedios = (
                    perfil_filtrado[perfil_filtrado["Area"].isin(paises_comparar)]
                    .groupby("Area", as_index=False)[indicadores_radar].mean()
                )
                normalizados = normalizar_por_columna(promedios, indicadores_radar)
                radar = normalizados.melt(
                    id_vars="Area", var_name="Indicador", value_name="Valor normalizado"
                )
                figura_radar = px.line_polar(
                    radar, r="Valor normalizado", theta="Indicador", color="Area",
                    line_close=True, markers=True, title="Comparación multidimensional",
                )
                st.plotly_chart(figura_radar, use_container_width=True)
                st.caption("Los valores están normalizados con Min-Max (0 a 1) para hacerlos comparables en la misma escala.")

# -----------------------------------------------------------------------------
# Tab 3: comercio y precios
# -----------------------------------------------------------------------------
with tab_comercio:
    st.header("Comercio y Precios")
    if rca_filtrado.empty:
        mostrar_vacio("No hay datos RCA para los filtros seleccionados.")
    else:
        productos_rca = sorted(rca_filtrado["Item"].dropna().unique())
        modo_producto = st.radio(
            "Definición de productos para el análisis RCA",
            ["Top N por RCA promedio", "Producto específico"],
            horizontal=True,
        )
        if modo_producto == "Top N por RCA promedio":
            max_productos = min(50, len(productos_rca))
            minimo_productos = min(5, max_productos)
            valor_inicial = min(15, max_productos)
            top_n = st.slider(
                "Top N productos por RCA promedio",
                minimo_productos,
                max_productos,
                valor_inicial,
            )
            productos_top = (
                rca_filtrado.groupby("Item")["RCA"].mean()
                .nlargest(top_n).index.tolist()
            )
        else:
            producto_elegido = st.selectbox("Producto de interés", productos_rca)
            productos_top = [producto_elegido]

        rca_heatmap = (
            rca_filtrado[rca_filtrado["Item"].isin(productos_top)]
            .groupby(["Area", "Item"], as_index=False)["RCA"].mean()
            .pivot(index="Area", columns="Item", values="RCA")
            .reindex(index=paises_seleccionados, columns=productos_top)
        )
        figura_heatmap = px.imshow(
            rca_heatmap, aspect="auto", color_continuous_scale="YlOrRd",
            labels={"x": "Producto", "y": "País", "color": "RCA promedio"},
            title="RCA promedio por país y producto",
        )
        st.plotly_chart(figura_heatmap, use_container_width=True)

        if precio_vol_filtrado.empty:
            mostrar_vacio("No hay datos de precios y volumen para los filtros seleccionados.")
        else:
            productos_scatter = sorted(precio_vol_filtrado["Item"].dropna().unique())
            producto_scatter = st.selectbox("Producto para el gráfico de precio y volumen", productos_scatter)
            datos_scatter = precio_vol_filtrado[precio_vol_filtrado["Item"] == producto_scatter]
            datos_scatter = datos_scatter.dropna(subset=["Export Quantity", "Implied Export Price"])
            if datos_scatter.empty:
                mostrar_vacio("El producto elegido no tiene valores de cantidad y precio disponibles.")
            else:
                figura_scatter = px.scatter(
                    datos_scatter, x="Export Quantity", y="Implied Export Price",
                    color="Area", size="Export Value", hover_data=["Year", "Item"],
                    title=f"Precio implícito vs. cantidad exportada: {producto_scatter}",
                )
                st.plotly_chart(figura_scatter, use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 4: datos descargables
# -----------------------------------------------------------------------------
with tab_datos:
    st.header("Datos filtrados")
    dataset_nombre = st.selectbox("Dataset", ["Perfil País-Año", "RCA", "Precio vs Volumen"])
    datasets = {
        "Perfil País-Año": perfil_filtrado,
        "RCA": rca_filtrado,
        "Precio vs Volumen": precio_vol_filtrado,
    }
    dataset = datasets[dataset_nombre]
    if dataset.empty:
        mostrar_vacio("El dataset seleccionado no contiene filas con los filtros actuales.")
    else:
        st.dataframe(dataset, use_container_width=True)
        st.download_button(
            "Descargar CSV filtrado",
            data=dataset.to_csv(index=False).encode("utf-8"),
            file_name=f"{dataset_nombre.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

# -----------------------------------------------------------------------------
# Tab 5: tipologias y clusters
# -----------------------------------------------------------------------------
with tab_clusters:
    st.header("Tipologías y Clusters")
    ventanas_disponibles = ["2005-11", "2012-18", "2019-24"]
    ventana_elegida = st.selectbox("Ventana temporal", ventanas_disponibles)

    if variables_ventana_con_clusters.empty:
        mostrar_vacio("No hay datos de clustering disponibles.")
    elif not {
        "Area",
        "Ventana",
        "Cluster_Nombre",
        "ISO3",
        "HHI_Familias",
        "k60",
    }.issubset(variables_ventana_con_clusters.columns):
        mostrar_vacio(
            "El archivo de clustering no contiene las columnas necesarias para esta vista."
        )
    else:
        datos_cluster = variables_ventana_con_clusters[
            (variables_ventana_con_clusters["Ventana"] == ventana_elegida)
            & variables_ventana_con_clusters["Area"].isin(paises_seleccionados)
        ].copy()

        if datos_cluster.empty:
            mostrar_vacio(
                f"No hay datos de clustering para la ventana {ventana_elegida} "
                "y los países seleccionados."
            )
        else:
            columna_mapa, columna_kpi = st.columns([2, 1])

            with columna_mapa:
                colores_clusters = {
                    "Consolidado/Diversificado": "#2E8B57",
                    "Volátil/Especialista": "#F2C94C",
                    "Crisis/Dependiente": "#D64545",
                }
                mapa_clusters = px.choropleth(
                    datos_cluster,
                    locations="ISO3",
                    color="Cluster_Nombre",
                    locationmode="ISO-3",
                    scope="south america",
                    hover_name="Area",
                    hover_data=["Cluster_Nombre"],
                    color_discrete_map=colores_clusters,
                    title=f"Tipologías de competitividad ({ventana_elegida})",
                )
                mapa_clusters.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend_title_text="Cluster",
                )
                mapa_clusters.update_geos(bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(mapa_clusters, use_container_width=True)

            cluster_mas_comun = (
                datos_cluster.groupby("Cluster_Nombre")["Area"]
                .nunique()
                .sort_values(ascending=False)
            )
            cluster_nombre = cluster_mas_comun.index[0]
            paises_cluster_mas_comun = int(cluster_mas_comun.iloc[0])

            with columna_kpi:
                promedio_hhi = datos_cluster["HHI_Familias"].mean()
                promedio_k60 = datos_cluster["k60"].mean()
                render_kpi_card(
                    "HHI promedio",
                    f"{promedio_hhi:,.4f}" if pd.notna(promedio_hhi) else "N/D",
                    "Promedio de HHI_Familias",
                    "#2E8B57",
                )
                render_kpi_card(
                    "k60 promedio",
                    f"{promedio_k60:,.2f}" if pd.notna(promedio_k60) else "N/D",
                    "Promedio de k60",
                    "#F2C94C",
                )
                render_kpi_card(
                    "Cluster dominante",
                    str(paises_cluster_mas_comun),
                    f"Países en {cluster_nombre}",
                    "#D64545",
                )
