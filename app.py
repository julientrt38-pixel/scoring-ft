import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from calculs import compute_scores  # import des calculs depuis calculs.py

# -------------------------
# Configuration page
# -------------------------
st.set_page_config(page_title="FT Scoring App", layout="wide")
st.title("📊 Dashboard — Évaluation Masters in Management")

# -------------------------
# Upload de l'Excel
# -------------------------
uploaded_file = st.file_uploader(
    "Importer un fichier Excel (.xlsx)", 
    type=["xlsx"]
)
if not uploaded_file:
    st.info(
        "Téléverse un fichier Excel contenant tes données "
        "(colonnes attendues: 'weighted salary', 'salary percentage increase', "
        "'tuition fee', 'posteinitial', 'posteactuel', 'tailleinitiale', "
        "'tailleactuelle', 'nationality', 'firstemploymentcountry', 'lastemploymentcountry', etc.)."
    )
    st.stop()

# Lecture
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Impossible de lire l'Excel : {e}")
    st.stop()

# Normalisation des en-têtes
df.columns = (
    df.columns.str.strip()
              .str.lower()
              .str.replace(r'[\s\W]+', ' ', regex=True)
              .str.replace('_', ' ')
              .str.strip()
)

# -------------------------
# Calcul des scores
# -------------------------
df = compute_scores(df)

# -------------------------
# Mapping affichage (émoticones + libellés)
# -------------------------
col_rename = {
    "weighted_salary_score": "💰 Salaire",
    "salary_increase_score": "📈 Croissance salaire",
    "aims_achieved_score": "🎯 Objectifs atteints",
    "value_for_money_score": "💹 Rentabilité école",
    "career_service_score": "🧑‍💼 Service carrière",
    "alumni_network_score": "🌐 Réseau alumni",
    "intl_work_mobility_score": "✈️ Mobilité internationale",
    "career_progress_score": "📊 Progression carrière",
    "final_score": "🏆 Score final",
    "posteinitial": "💼 Poste initial",
    "posteactuel": "💼 Poste actuel",
    "tailleinitiale": "🏢 Taille entreprise départ",
    "tailleactuelle": "🏢 Taille entreprise actuelle",
    "nationality": "🌍 Nationalité",
    "firstemploymentcountry": "🗺️ Pays d’emploi (1er)",
    "lastemploymentcountry": "🗺️ Pays d’emploi (dernier)",
    "tuition fee": "🏫 Frais de scolarité"
}
existing_renames = {k: v for k, v in col_rename.items() if k in df.columns}
df.rename(columns=existing_renames, inplace=True)

# -------------------------
# Recherche globale
# -------------------------
search_term = st.text_input("🔎 Recherche globale", value="").strip()
if search_term:
    mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
    df_display_base = df[mask].copy()
else:
    df_display_base = df.copy()

# -------------------------
# AgGrid Utilities
# -------------------------
cell_style_jscode = JsCode("""
function(params) {
    return {'textAlign': 'center', 'whiteSpace': 'normal', 'overflow': 'hidden', 'textOverflow': 'ellipsis'};
}
""")

def afficher_tableau_aggrid(df_to_show, height=350):
    gb = GridOptionsBuilder.from_dataframe(df_to_show)
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        minWidth=80,
        maxWidth=260,
        cellStyle=cell_style_jscode
    )
    grid_options = gb.build()
    AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        theme="streamlit",
        height=height,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True
    )

# -------------------------
# Onglets : Tableaux / Analyses
# -------------------------
tab1, tab2 = st.tabs(["📋 Données & Tableaux", "📈 Analyses"])

with tab1:
    st.subheader("1) Tableaux")

    # Scores only view
    scores_cols = [c for c in df_display_base.columns if "score" in str(c).lower() or str(c).lower() in ["final_score", "🏆 score final"]]
    id_cols = [c for c in df_display_base.columns if c.lower() in ["id", "identifiant", "identifier"]]
    nom_cols = [c for c in df_display_base.columns if c.lower() in ["nom", "name", "last name", "lastname", "surname"]]
    prenom_cols = [c for c in df_display_base.columns if c.lower() in ["prenom", "first name", "firstname", "given name"]]

    front_cols = [col for col in [*id_cols[:1], *nom_cols[:1], *prenom_cols[:1]] if col is not None]
    scores_view_cols = front_cols + [c for c in scores_cols if c not in front_cols]

    if scores_view_cols:
        df_scores_view = df_display_base[scores_view_cols].copy()
        st.markdown("**Tableau : Scores (avec ID / Nom / Prénom si détectés)**")
        afficher_tableau_aggrid(df_scores_view, height=380)
    else:
        st.info("Aucun score détecté dans les colonnes. Affichage complet.")
        afficher_tableau_aggrid(df_display_base, height=380)

    st.markdown("---")
    st.subheader("2) Données originales (sans colonnes de score)")
    no_score_cols = [c for c in df_display_base.columns if c not in scores_cols]
    if no_score_cols:
        afficher_tableau_aggrid(df_display_base[no_score_cols], height=380)
    else:
        st.info("Toutes les colonnes semblent être des scores.")

    st.markdown("---")
    st.subheader("3) Tableau complet")
    afficher_tableau_aggrid(df_display_base, height=480)

with tab2:
    st.subheader("Visualisations & analyses")
    st.info("Zone pour graphiques interactifs")
    if "final_score" in df_display_base.columns:
        try:
            import altair as alt
            chart_df = df_display_base[["final_score"]].dropna()
            if not chart_df.empty:
                hist = alt.Chart(chart_df).mark_bar().encode(
                    alt.X("final_score:Q", bin=alt.Bin(maxbins=20)),
                    y='count()'
                ).properties(width=700, height=300)
                st.altair_chart(hist, use_container_width=True)
            else:
                st.info("Pas assez de données numériques pour afficher un histogramme.")
        except Exception:
            st.info("Altair non disponible — graphiques désactivés.")
