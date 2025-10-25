import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO

# --- CONFIG DE BASE ---
st.set_page_config(page_title="Scoring App", layout="wide")

# --- FONCTION D’IMPORT EXCEL ---
@st.cache_data
def load_excel(file):
    return pd.read_excel(file)

# --- UPLOAD ---
st.sidebar.header("📂 Import du fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisis ton fichier Excel", type=["xlsx"])

if uploaded_file:
    df = load_excel(uploaded_file)

    # --- ARRONDIS ET FORMAT ---
    df = df.round(2)

    # --- COLONNES À GARDER POUR LES SCORES ---
    score_columns = [
        "ID", "Nom", "Prénom", "Salaire", "Croissance Salaire",
        "Objectifs atteints", "Service carrière", "Réseau alumni",
        "Mobilité internationale", "Progression carrière",
        "Score final", "Frais de scolarité"
    ]

    df_scores = df[[c for c in df.columns if c in score_columns]]

    # --- RENOMMER LES COLONNES AVEC ÉMOJIS ---
    rename_dict = {
        "Salaire": "💰 Salaire",
        "Croissance Salaire": "📈 Croissance Salaire",
        "Objectifs atteints": "🎯 Objectifs atteints",
        "Service carrière": "🧭 Service carrière",
        "Réseau alumni": "🤝 Réseau alumni",
        "Mobilité internationale": "✈️ Mobilité internationale",
        "Progression carrière": "🚀 Progression carrière",
        "Score final": "🏆 Score final",
        "Frais de scolarité": "💸 Frais de scolarité",
        "Poste initial": "💼 Poste initial",
        "Poste actuel": "💼 Poste actuel",
        "Taille entreprise initiale": "🏢 Taille entreprise initiale",
        "Taille entreprise actuelle": "🏢 Taille entreprise actuelle",
        "Nationalité": "🌍 Nationalité",
        "Valeur argent": "💹 Rentabilité école",
        "1er pays d'emploi": "🌍 1er pays d'emploi",
        "Dernier pays d'emploi": "🌍 Dernier pays d'emploi"
    }
    df.rename(columns=rename_dict, inplace=True)
    df_scores.rename(columns=rename_dict, inplace=True)

    # --- ONGLET 1 : TABLEAUX INTERACTIFS ---
    tab1, tab2 = st.tabs(["📊 Données", "📈 Analyses"])

    with tab1:
        st.subheader("Tableaux interactifs")

        # Style plus compact
        st.markdown("### 🎯 Tableau des scores")
        gb = GridOptionsBuilder.from_dataframe(df_scores)
        gb.configure_default_column(
            resizable=True,
            wrapHeaderText=True,  # retour à la ligne dans les entêtes
            autoHeaderHeight=True,
            filter=True,
            sortable=True,
            floatingFilter=False,  # les filtres passent sous les titres
            cellStyle={'textAlign': 'center'},
        )
        gb.configure_grid_options(domLayout='normal')
        grid_options = gb.build()

        AgGrid(
            df_scores,
            gridOptions=grid_options,
            fit_columns_on_grid_load=False,
            height=500,
            theme="alpine"
        )

        st.markdown("### 📄 Tableau sans scores")
        no_score_cols = [c for c in df.columns if c not in df_scores.columns]
        df_no_scores = df[no_score_cols]

        gb2 = GridOptionsBuilder.from_dataframe(df_no_scores)
        gb2.configure_default_column(
            resizable=True,
            wrapHeaderText=True,
            autoHeaderHeight=True,
            filter=True,
            sortable=True,
            floatingFilter=False,
            cellStyle={'textAlign': 'center'},
        )
        AgGrid(
            df_no_scores,
            gridOptions=gb2.build(),
            fit_columns_on_grid_load=False,
            height=500,
            theme="alpine"
        )

        st.markdown("### 🧾 Tableau complet")
        gb3 = GridOptionsBuilder.from_dataframe(df)
        gb3.configure_default_column(
            resizable=True,
            wrapHeaderText=True,
            autoHeaderHeight=True,
            filter=True,
            sortable=True,
            floatingFilter=False,
            cellStyle={'textAlign': 'center'},
        )
        AgGrid(
            df,
            gridOptions=gb3.build(),
            fit_columns_on_grid_load=False,
            height=600,
            theme="alpine"
        )

    with tab2:
        st.subheader("📈 Analyses (à venir)")
        st.info("Les visualisations et analyses seront ajoutées ici prochainement.")
else:
    st.warning("Merci d’importer un fichier Excel à gauche pour commencer.")


