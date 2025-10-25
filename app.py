import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from calculs import compute_scores

st.set_page_config(page_title="Scoring App", layout="wide")

# --- UPLOAD ---
st.sidebar.header("📂 Import du fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisis ton fichier Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.round(2)

    # Calcul des scores
    df = compute_scores(df)

    # --- Onglets ---
    tab1, tab2 = st.tabs(["📊 Données", "📈 Analyses"])

    with tab1:
        st.subheader("Tableaux interactifs")

        # --- Sélection des colonnes pour chaque tableau ---
        score_cols = [
            "ID", "Nom", "Prénom", "Salaire", "Croissance Salaire",
            "Objectifs atteints", "Service carrière", "Réseau alumni",
            "Mobilité internationale", "Progression carrière",
            "final_score", "Frais de scolarité"
        ]
        df_scores = df[[c for c in df.columns if c in score_cols]]

        # --- AgGrid ---
        gb = GridOptionsBuilder.from_dataframe(df_scores)
        gb.configure_default_column(
            resizable=True, wrapHeaderText=True, autoHeaderHeight=True,
            filter=True, sortable=True, cellStyle={'textAlign': 'center'}
        )
        grid_options = gb.build()
        AgGrid(df_scores, gridOptions=grid_options, fit_columns_on_grid_load=False, height=500, theme="alpine")

        st.markdown("### 📄 Tableau complet")
        gb2 = GridOptionsBuilder.from_dataframe(df)
        gb2.configure_default_column(
            resizable=True, wrapHeaderText=True, autoHeaderHeight=True,
            filter=True, sortable=True, cellStyle={'textAlign': 'center'}
        )
        AgGrid(df, gridOptions=gb2.build(), fit_columns_on_grid_load=False, height=600, theme="alpine")

    with tab2:
        st.subheader("📈 Analyses (à venir)")
        st.info("Les visualisations et analyses seront ajoutées ici prochainement.")

else:
    st.warning("Merci d’importer un fichier Excel à gauche pour commencer.")


