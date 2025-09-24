import pandas as pd
import streamlit as st
import pydeck as pdk
import numpy as np

import os

# base path = dossier courant du script
BASE_DIR = os.path.dirname(__file__)


# Chargement des fichiers avec chemins relatifs robustes
df_crimes = pd.read_csv(
    os.path.join(BASE_DIR, '..', '..', 'data', 'dimension_crime.csv'),
    sep=';', 
)

df_departements_without_central = pd.read_csv(
    os.path.join(BASE_DIR, '..', '..', 'data', 'dimension_departement_enrichi2.csv'),
    sep=';', 
)

df_departements_central = pd.read_csv(
    os.path.join(BASE_DIR, '..', '..', 'data', 'points-extremes-des-departements-metropolitains-de-france.csv'),
    sep=',',
)

df_resultat = pd.read_csv(
    os.path.join(BASE_DIR, '..',  'data_cleaning', 'resultat.csv'),
    sep=';', 
)



df_departements_central["Latitude_centrale"] = (df_departements_central["Latitude la plus au nord"] + df_departements_central["Latitude la plus au sud"]) /2 
df_departements_central["Longitude_centrale"] = (df_departements_central["Longitude la plus à l’est"] + df_departements_central["Longitude la plus à l’ouest"]) /2 


df_departements = pd.merge(df_departements_without_central, df_departements_central, on='Departement', how='left')
print (df_departements)

df_merge = pd.merge(df_resultat, df_departements, on='Departement', how='left')
df_merge = pd.merge(df_merge, df_crimes, on='Code index', how='left')
for col in ['Annee', 'Categorie_Crime', 'Service', 'Region', 'Libellé']:
    if col in df_merge.columns:
        df_merge[col] = df_merge[col].astype(str)

st.title('Analyses des crimes en france')

optionsAnnee = st.sidebar.multiselect(
    "Choix de l'année :",
    sorted(df_merge['Annee'].unique()),
    placeholder = 'Année'
)

optionCategorieCrime = st.sidebar.multiselect(
    "Choix de la catégorie :",
    sorted(df_merge['Categorie_Crime'].unique()),
    placeholder = 'Catégorie'
)
optionDelit = st.sidebar.multiselect(
    "Choix du délit :",
    sorted(df_merge['Libelle_Index'].unique()),
    placeholder = 'Délit'
)


optionService = st.sidebar.multiselect(
    "Choix du service :",
    sorted(df_merge['Service'].unique()),
    placeholder='Service'
)

optionRegion = st.sidebar.multiselect(
    "Choix de la région :",
    sorted(df_merge['Region'].unique()),
    placeholder='Région'
)

optionDepartement = st.sidebar.multiselect(
    "Choix du département :",
    sorted(df_merge['Libellé'].unique()),
    placeholder='Département'
)

# --- Filtrage général SANS année ---
df_filtered_no_year = df_merge.copy()

if optionCategorieCrime:
    df_filtered_no_year = df_filtered_no_year[df_filtered_no_year['Categorie_Crime'].isin(optionCategorieCrime)]

if optionDelit:
    df_filtered_no_year = df_filtered_no_year[df_filtered_no_year['Libelle_Index'].isin(optionDelit)]

if optionService:
    df_filtered_no_year = df_filtered_no_year[df_filtered_no_year['Service'].isin(optionService)]

if optionRegion:
    df_filtered_no_year = df_filtered_no_year[df_filtered_no_year['Region'].isin(optionRegion)]

if optionDepartement:
    df_filtered_no_year = df_filtered_no_year[df_filtered_no_year['Libellé'].isin(optionDepartement)]

# --- Maintenant on gère l'année séparément ---
if optionsAnnee:
    df_filtered = df_filtered_no_year[df_filtered_no_year['Annee'].isin(optionsAnnee)]
else:
    df_filtered = df_filtered_no_year

# --- KPIs dynamiques ---
col1, col2, col3 = st.columns(3)

# 1. Total crimes (avec tous les filtres)
total_crimes = df_filtered['Valeur'].sum()

# 2. Crimes année N et N-1
if not df_filtered.empty:
    annee_max = df_filtered['Annee'].astype(int).max()

    crimes_N = df_filtered_no_year.loc[df_filtered_no_year['Annee'] == str(annee_max), 'Valeur'].sum()
    crimes_Nm1 = df_filtered_no_year.loc[df_filtered_no_year['Annee'] == str(annee_max-1), 'Valeur'].sum()
else:
    annee_max = None
    crimes_N, crimes_Nm1 = 0, 0

# 3. Variation %
if crimes_Nm1 > 0:
    delta = (crimes_N - crimes_Nm1) / crimes_Nm1 * 100
    delta_str = f"{delta:.1f}%"
else:
    delta_str = "N/A"

# --- Affichage ---
col1.metric("Crimes totaux de 2018 à 2021", f"{total_crimes:,}".replace(",", " "))
col2.metric(
    f"Crimes en {annee_max}" if annee_max else "Crimes année N",
    f"{crimes_N:,}".replace(",", " "),
    delta_str
)
col3.metric(
    f"Crimes en {annee_max-1}" if annee_max else "Crimes année N-1",
    f"{crimes_Nm1:,}".replace(",", " ")
)


# --- Agrégation par département ---
df_map = df_filtered.groupby(
    ['Libellé', 'Latitude_centrale', 'Longitude_centrale'], as_index=False
)['Valeur'].sum()

# --- Normalisation pour les couleurs ---
val_min, val_max = df_map['Valeur'].min(), df_map['Valeur'].max()
val_range = val_max - val_min

def get_color(value):
    # Normaliser entre 0 et 1
    x = (value - val_min) / val_range if val_range > 0 else 0.5

    if x < 0.33:  # vert -> jaune
        ratio = x / 0.33
        r = int(0 + ratio * 255)
        g = 255
        b = 0
    elif x < 0.66:  # jaune -> orange
        ratio = (x - 0.33) / 0.33
        r = 255
        g = int(255 - ratio * (255 - 165))
        b = 0
    else:  # orange -> rouge
        ratio = (x - 0.66) / 0.34
        r = 255
        g = int(165 - ratio * 165)
        b = 0
    return [r, g, b]

df_map['color'] = df_map['Valeur'].apply(get_color)
df_map['radius'] = 5 + (df_map['Valeur'] - val_min) / (val_max - val_min) * 45
df_map['radius'] = np.log1p(df_map['Valeur']) 
r_min, r_max = df_map['radius'].min(), df_map['radius'].max()
df_map['radius'] = 5 + (df_map['radius'] - r_min) / (r_max - r_min) * 45

print(df_map)

# --- Création de la couche ---
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[Longitude_centrale, Latitude_centrale]',
    get_fill_color='color',
    get_radius="radius",
    radius_units='pixels',
    pickable=True
)

# --- Vue centrée sur la France ---
view_state = pdk.ViewState(
    latitude=46.6,
    longitude=2.5,
    zoom=5,
    pitch=0
)

# --- Affichage ---
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state,
                         tooltip={"text": "{Libellé}\nCrimes: {Valeur}"}))


st.dataframe(df_filtered)


