import pandas as pd
import streamlit as st

df_crimes = pd.read_csv('../../data/dimension_crime.csv', sep=';')
df_departements = pd.read_csv('../../data/dimension_departement_enrichi.csv', sep=';')
df_resultat = pd.read_csv('../data_cleaning/resultat.csv', sep=';')

df_merge = pd.merge(df_resultat, df_departements, on='Departement', how='left')
df_merge = pd.merge(df_merge, df_crimes, on='Code index', how='left')
for col in ['Annee', 'Categorie_Crime', 'Service', 'Region', 'Nom_Departement']:
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
    sorted(df_merge['Nom_Departement'].unique()),
    placeholder='Département'
)

# On part d'une copie
df_filtered = df_merge.copy()

if optionsAnnee:
    df_filtered = df_filtered[df_filtered['Annee'].isin(optionsAnnee)]

if optionCategorieCrime:
    df_filtered = df_filtered[df_filtered['Categorie_Crime'].isin(optionCategorieCrime)]

if optionService:
    df_filtered = df_filtered[df_filtered['Service'].isin(optionService)]

if optionRegion:
    df_filtered = df_filtered[df_filtered['Region'].isin(optionRegion)]

if optionDepartement:
    df_filtered = df_filtered[df_filtered['Nom_Departement'].isin(optionDepartement)]

# Et c'est ce dataframe filtré qu'on affiche

col1, col2, col3 = st.columns(3)
col1.metric("Temperature", "70 °F", "1.2 °F")
col2.metric("Wind", "9 mph", "-8%")
col3.metric("Humidity", "86%", "4%")

st.dataframe(df_filtered)

