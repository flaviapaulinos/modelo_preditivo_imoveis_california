import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from joblib import load

from notebooks.src.config import DADOS_GEO_MEDIAN, DADOS_LIMPOS, MODELO_FINAL

@st.cache_data
def carregar_dados_limpos():
    return pd.read_parquet(DADOS_LIMPOS)

@st.cache_data
def carregar_dados_geo():
    return gpd.read_parquet(DADOS_GEO_MEDIAN)

@st.cache_resource
def carregar_modelo():
    return load(MODELO_FINAL)

df=carregar_dados_limpos()
gdf_geo=carregar_dados_geo()
modelo=carregar_modelo()


st.title("Previsão de preços de imóveis")

#a select box precisa receber uma lista
counties = list(gdf_geo['name'].sort_values())

selecionar_condado = st.selectbox("Condado", counties)

longitude = gdf_geo.query('name== @selecionar_condado')['longitude'].values
latitude =  gdf_geo.query('name== @selecionar_condado')['latitude'].values

housing_media_age = st.number_input("Idade do imóvel", value=10, min_value=1, max_value=50)
total_rooms =  gdf_geo.query('name== @selecionar_condado')['total_rooms'].values
total_bedrooms =  gdf_geo.query('name== @selecionar_condado')['total_bedrooms'].values
population = gdf_geo.query('name== @selecionar_condado')['population'].values
households =  gdf_geo.query('name== @selecionar_condado')['households'].values

median_income = st.slider("Renda média (em milhares de US$)", 5.0, 100.0, 45.0, 5.0) 
#para facilitar para o usuário, vamos multiplicar por 10 (depois precisamos dividir por 10 nas colunas que tem como base essa informação)
#para não dar erro, tudo float, ou tudo inteiro

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

df_entrada_modelo = pd.DataFrame(entrada_modelo, index=[0]) 

botao_previsao = st.button("Prever preco")

if botao_previsao:
    preco = modelo.predict(df_entrada_modelo)
    st.write(f"Preço previsto: | US${preco[0][0]:.2f}")
    
    
    
    
    
    
    
    
    