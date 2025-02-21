import subprocess
import sys
import sys
print(sys.path)

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])

install("geopandas")
install("shapely")
install("pyproj")


import geopandas as gpd
import numpy as np
import pandas as pd
import pydeck as pdk
import shapely

import streamlit as st

from joblib import load

from notebooks.src.config import DADOS_GEO_MEDIAN, DADOS_LIMPOS, MODELO_FINAL

@st.cache_data
def carregar_dados_limpos():
    return pd.read_parquet(DADOS_LIMPOS)

@st.cache_data
def carregar_dados_geo():
    gdf_geo= gpd.read_parquet(DADOS_GEO_MEDIAN)

    #explode Multipolygons into individual polygons
    gdf_geo = gdf_geo.explode(ignore_index=True)

    #Function to check and fix invalid geometries
    def fix_and_orient_geometry(geometry):
        if not geometry.is_valid:
            geometry=geometry.buffer(0)#fix invalid geometry

        #orient the polygon to be counter-clockwise if it's a Polygon or Multypolygon
        if isinstance(
            geometry, (shapely.geometry.Polygon, shapely.geometry.MultiPolygon)
        ):
            geometry = shapely.geometry.polygon.orient(geometry, sign=1.0)
        
        return geometry
    #Apple the fix orientation function to geometries
    gdf_geo['geometry']=gdf_geo['geometry'].apply(fix_and_orient_geometry)
   
    #extract polygon coordinates
    def get_polygon_coordinates(geometry):
        return(
            [[[x,y]for x,y in geometry.exterior.coords]]
            if isinstance(geometry, shapely.geometry.Polygon)
            else[
                [[X,y] for x,y in polygon.exterior.coords]
            ]
        )

    #apply the coordinate conversion and store in a new column
    gdf_geo['geometry'] = gdf_geo['geometry'].apply(get_polygon_coordinates)

    return gdf_geo

@st.cache_resource
def carregar_modelo():
    return load(MODELO_FINAL)

df=carregar_dados_limpos()
gdf_geo=carregar_dados_geo()
modelo=carregar_modelo()


st.title("Previsão de preços de imóveis")

counties = sorted(gdf_geo['name'].unique()) 

coluna1, coluna2 = st.columns(2)

with coluna1: 

    with st.form(key='formulario'):
    
        selecionar_condado = st.selectbox("Condado", counties)
        
        longitude = gdf_geo.query('name== @selecionar_condado')['longitude'].values
        latitude =  gdf_geo.query('name== @selecionar_condado')['latitude'].values
        
        housing_media_age = st.number_input("Idade do imóvel", value=10, min_value=1, max_value=50)
        total_rooms =  gdf_geo.query('name== @selecionar_condado')['total_rooms'].values
        total_bedrooms =  gdf_geo.query('name== @selecionar_condado')['total_bedrooms'].values
        population = gdf_geo.query('name== @selecionar_condado')['population'].values
        households =  gdf_geo.query('name== @selecionar_condado')['households'].values
        
        median_income = st.slider("Renda média (em milhares de US$)", 5.0, 100.0, 45.0, 5.0) 
        
        ocean_proximity = gdf_geo.query('name== @selecionar_condado')['ocean_proximity'].values
        
        
        bins_income=[0, 1.5, 3, 4.5, 6, np.inf]
        median_income_cat = np.digitize(median_income/10, bins=bins_income)
        
        rooms_per_household =  gdf_geo.query('name== @selecionar_condado')['rooms_per_household'].values
        population_per_household = gdf_geo.query('name== @selecionar_condado')['population_per_household'].values
        bedrooms_per_room =  gdf_geo.query('name== @selecionar_condado')['bedrooms_per_room'].values
        
        
        
        entrada_modelo = {
            'longitude': longitude,
            'latitude': latitude,
            'housing_median_age': housing_media_age,
            'total_rooms': total_rooms,
            'total_bedrooms': total_bedrooms,
            'population': population,
            'households': households,
            'median_income': median_income/10,
            'ocean_proximity': ocean_proximity,
            'median_income_cat': median_income_cat,
            'rooms_per_household': rooms_per_household,
            'population_per_household': population_per_household,
            'bedrooms_per_room': bedrooms_per_room,
        }
        
        df_entrada_modelo = pd.DataFrame(entrada_modelo) 
        
        botao_previsao = st.form_submit_button("Submeter e prever preco")
    if botao_previsao:
        preco = modelo.predict(df_entrada_modelo)
        texto_preco = f" | US${preco[0][0]:_.2f}"
        texto_preco = texto_preco.replace('.',',').replace('_','.')
        st.metric("Preço previsto:", value=texto_preco)
        
    
            
        
with coluna2:
    view_state = pdk.ViewState(
        latitude=float(latitude[0]),
        longitude=float(longitude[0]),
        zoom=6,
        min_zomm=5,
        max_zoom=15,
    )

    polygon_layer = pdk.Layer(
        'PolygonLayer',
        data=gdf_geo[['name','geometry']],
        get_polygon='geometry', 
        get_fill_color=[0,128,128,100],
        get_line_color=[255, 255, 255],
        get_line_width=500,
        pickable=True,
        auto_highlight=True, 
        highlighted_color=[255, 255, 0, 100],
    )

  
    condado_selecionado= gdf_geo.query('name== @selecionar_condado')

    highlight_layer=pdk.Layer(
        'PolygonLayer',
        data=condado_selecionado[['name','geometry']],
        get_polygon='geometry',
        get_fill_color=[255,69,0,100],
        get_line_color=[255,69,0],
        get_line_width=900,
        pickable=True,
        auto_highlight=True, 
    )

    tooltip={
        'html': '<b>Condado: </b> {name}',
        'style': {'backgroundColor': 'steelblue', 'color': 'white', 'fontsize': '10px'}
    }
        

        
    mapa = pdk.Deck(
        initial_view_state = view_state,
        map_style="road",
        layers=[polygon_layer, highlight_layer],
        tooltip = tooltip,
    )
    
    st.pydeck_chart(mapa)
    
    
    
    