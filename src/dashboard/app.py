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

df_departements_central["Latitude_centrale"] = (    df_departements_central["Latitude la plus au nord"] + df_departements_central["Latitude la plus au sud"]) / 2
df_departements_central["Longitude_centrale"] = (    df_departements_central["Longitude la plus à l’est"] + df_departements_central["Longitude la plus à l’ouest"]) / 2

df_departements = pd.merge(
    df_departements_without_central, df_departements_central, on='Departement', how='left'
)

df_merge = pd.merge(df_resultat, df_departements, on='Departement', how='left')
df_merge = pd.merge(df_merge, df_crimes, on='Code index', how='left')
for col in ['Annee', 'Categorie_Crime', 'Service', 'Region', 'Libellé']:
    if col in df_merge.columns:
        df_merge[col] = df_merge[col].astype(str)

st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>Analyses des crimes en France</h1>",
    unsafe_allow_html=True
)


# --- Filtres ---
optionsAnnee = st.sidebar.multiselect(
    "Choix de l'année :", sorted(df_merge['Annee'].unique()), placeholder='Année'
)
optionCategorieCrime = st.sidebar.multiselect(
    "Choix de la catégorie :", sorted(df_merge['Categorie_Crime'].unique()), placeholder='Catégorie'
)
optionDelit = st.sidebar.multiselect(
    "Choix du délit :", sorted(df_merge['Libelle_Index'].unique()), placeholder='Délit'
)
optionService = st.sidebar.multiselect(
    "Choix du service :", sorted(df_merge['Service'].unique()), placeholder='Service'
)
optionRegion = st.sidebar.multiselect(
    "Choix de la région :", sorted(df_merge['Region'].unique()), placeholder='Région'
)
optionDepartement = st.sidebar.multiselect(
    "Choix du département :", sorted(df_merge['Libellé'].unique()), placeholder='Département'
)

# --- Filtrage ---
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

if optionsAnnee:
    df_filtered = df_filtered_no_year[df_filtered_no_year['Annee'].isin(optionsAnnee)]
else:
    df_filtered = df_filtered_no_year

# --- Layout KPIs + Top3 ---
col_left, col_right = st.columns(2)

# Bloc de gauche : KPIs
with col_left:
    st.subheader("🕵️‍♀️​ En quelques chiffres")
    c1, c2, c3 = st.columns(3)

    total_crimes = df_filtered['Valeur'].sum()

    if not df_filtered.empty:
        annee_max = df_filtered['Annee'].astype(int).max()
        crimes_N = df_filtered_no_year.loc[df_filtered_no_year['Annee'] == str(annee_max), 'Valeur'].sum()
        crimes_Nm1 = df_filtered_no_year.loc[df_filtered_no_year['Annee'] == str(annee_max-1), 'Valeur'].sum()
    else:
        annee_max, crimes_N, crimes_Nm1 = None, 0, 0

    if crimes_Nm1 > 0:
        delta = (crimes_N - crimes_Nm1) / crimes_Nm1 * 100
        delta_str = f"{delta:.1f}%"
    else:
        delta_str = "N/A"

    c1.metric("Crimes totaux de 2018 à 2021", f"{total_crimes:,}".replace(",", " "))
    c2.metric(
        f"Crimes en {annee_max}" if annee_max else "Crimes année N",
        f"{crimes_N:,}".replace(",", " "),
        delta_str
    )
    c3.metric(
        f"Crimes en {annee_max-1}" if annee_max else "Crimes année N-1",
        f"{crimes_Nm1:,}".replace(",", " ")
    )

# Bloc de droite : Top 3 départements
with col_right:
    st.subheader("🏆 Top 3 départements (selon filtres)")
    c1, c2, c3 = st.columns(3)

    top3 = df_map = df_filtered.groupby(
        ['Libellé', 'Latitude_centrale', 'Longitude_centrale'], as_index=False
    )['Valeur'].sum().nlargest(3, 'Valeur')[['Libellé', 'Valeur']]

    for i, (libelle, valeur) in enumerate(zip(top3['Libellé'], top3['Valeur'])):
        if i == 0:
            c1.metric(f"🥇 {libelle}", f"{valeur:,}".replace(",", " "))
        elif i == 1:
            c2.metric(f"🥈 {libelle}", f"{valeur:,}".replace(",", " "))
        elif i == 2:
            c3.metric(f"🥉 {libelle}", f"{valeur:,}".replace(",", " "))

# --- Préparation données pour la map ---
df_map = df_filtered.groupby(
    ['Libellé', 'Latitude_centrale', 'Longitude_centrale'], as_index=False
)['Valeur'].sum()

val_min, val_max = df_map['Valeur'].min(), df_map['Valeur'].max()
val_range = val_max - val_min

def get_color(value):
    x = (value - val_min) / val_range if val_range > 0 else 0.5
    if x < 0.33:  # vert -> jaune
        ratio = x / 0.33
        r, g, b = int(0 + ratio * 255), 255, 0
    elif x < 0.66:  # jaune -> orange
        ratio = (x - 0.33) / 0.33
        r, g, b = 255, int(255 - ratio * (255 - 165)), 0
    else:  # orange -> rouge
        ratio = (x - 0.66) / 0.34
        r, g, b = 255, int(165 - ratio * 165), 0
    return [r, g, b]

# --- Choix du mode d’affichage ---
st.sidebar.markdown("### Affichage de la carte")
mode_carte = st.sidebar.radio(
    "Mode d’affichage :",
    ["Bubble", "Heatmap"],
    index=0
)
layers = []

# --- Calcul des couleurs et tailles des bulles ---
df_map['color'] = df_map['Valeur'].apply(get_color)

if mode_carte == "Bubble":
    
    #df_map['radius'] = np.log1p(df_map['Valeur']) * 3  # rayon en mètres

    # Normalisation de la taille des bulles sur le MAX du périmètre filtré
    # rayon max fixé à 30 px
    # rayon min borné à 4 px pour garder la cliquabilité
    if val_max <= 0:
        df_map['radius_px'] = 4  # cas bord : toutes les valeurs nulles ou négatives
    else:
        df_map['radius_px'] = np.maximum(4, 30 * (df_map['Valeur'] / val_max))

    # --- Création de la couche ---
    layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_map,
            get_position='[Longitude_centrale, Latitude_centrale]',
            get_fill_color='color',
            get_radius='radius_px',
            radius_units='pixels',        # <<< clé : en pixels !
            radius_min_pixels=2,
            radius_max_pixels=30,         # borne supérieure stricte = 30 px
            stroked=True,                 # lisibilité
            get_line_color=[30, 30, 30],
            line_width_min_pixels=1,
            pickable=True,
            opacity=0.6,
            auto_highlight=True
        )
    layers.append(layer)
    
elif mode_carte == "Heatmap":
    layers.append(pdk.Layer(
        "HeatmapLayer",
        data=df_map,
        get_position='[Longitude_centrale, Latitude_centrale]',
        get_weight="Valeur",
        radiusPixels=40,        
        intensity=1.0,
        threshold=0.2
    ))
# --- Vue centrée sur la France ---
view_state = pdk.ViewState(
    latitude=46.6, longitude=2.5, zoom=5, pitch=0
)
col_left, col_right = st.columns([1, 1], vertical_alignment="top") 
with col_left:
    st.markdown(
        "<h2 style='text-align: center;'>🗺️ Carte interactive</h2>",
        unsafe_allow_html=True
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={"text": "{Libellé}\nCrimes: {Valeur}"}
        ),
        height=600
    )

with col_right:
    st.markdown(
        "<h2 style='text-align: center;'>📋 Tableau des données filtrées</h2>",
        unsafe_allow_html=True
    )
    st.dataframe(df_filtered, height=600)


