import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from calculs import compute_scores

# --- CONFIG DE BASE ---
st.set_page_config(page_title="Scoring App", layout="wide")

# --- UPLOAD EXCEL ---
st.sidebar.header("📂 Import du fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisis ton fichier Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.round(2)

    # --- CALCUL DES SCORES ---
    df = compute_scores(df)

    # --- COLONNES SCORES ---
    score_columns = [
        "ID", "Nom", "Prénom", "Salaire", "Croissance Salaire",
        "Objectifs atteints", "Service carrière", "Réseau alumni",
        "Mobilité internationale", "Progression carrière",
        "Score final", "Frais de scolarité"
    ]
    df_scores = df[[c for c in df.columns if c in score_columns]]

    # --- ONGLETS ---
    tab1, tab2 = st.tabs(["📊 Données", "📈 Analyses"])

    with tab1:
        st.subheader("Tableaux interactifs")
        gb = GridOptionsBuilder.from_dataframe(df_scores)
        gb.configure_default_column(
            resizable=True, wrapHeaderText=True, autoHeaderHeight=True,
            filter=True, sortable=True, floatingFilter=False,
            cellStyle={'textAlign': 'center'}
        )
        AgGrid(df_scores, gridOptions=gb.build(), fit_columns_on_grid_load=False, height=500, theme="alpine")

    with tab2:
        st.subheader("📈 Analyses (à venir)")
        st.info("Les visualisations seront ajoutées ici prochainement.")

else:
    st.warning("Merci d’importer un fichier Excel à gauche pour commencer.")
