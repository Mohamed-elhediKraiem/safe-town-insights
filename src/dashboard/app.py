import pandas as pd
import streamlit as st
import pydeck as pdk

df_crimes = pd.read_csv('../../data/dimension_crime.csv', sep=';')
df_departements = pd.read_csv('../../data/dimension_departement_enrichi2.csv', sep=';')
df_resultat = pd.read_csv('../data_cleaning/resultat.csv', sep=';')

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
    ['Libellé', 'latitude_departement', 'longitude_departement'], as_index=False
)['Valeur'].sum()

# --- Normalisation pour les couleurs ---
# On mappe la valeur en un dégradé bleu -> rouge
max_val = df_map['Valeur'].max()
df_map['color_r'] = (df_map['Valeur'] / max_val * 255).astype(int)
df_map['color_b'] = 255 - df_map['color_r']

# --- Création de la couche ---
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude_departement, latitude_departement]',
    get_fill_color='[color_r, 0, color_b, 160]',
    get_radius="Valeur",  # taille relative au nombre de crimes
    radius_scale=50,    # ← ajuste ici (10 est trop petit si les valeurs sont grandes)
    radius_min_pixels=3,
    radius_max_pixels=50,
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

