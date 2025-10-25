import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from calculs import compute_scores

st.set_page_config(page_title="FT Scoring App", layout="wide")

st.markdown("""
<style>
/* Cards arrondies pour sections */
.card {
    background-color: #ffffff;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
}
/* Titres sections */
.card h3 {
    margin-top: 0;
    margin-bottom: 10px;
}
/* AgGrid rounded cells */
.ag-cell {
    border-radius: 8px !important;
    padding: 5px !important;
    line-height: 1.5 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard — Évaluation Masters in Management")

# -------------------------
# Upload Excel
# -------------------------
uploaded_file = st.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])
if not uploaded_file:
    st.info(
        "Téléverse un fichier Excel contenant tes données "
        "(colonnes attendues : 'weighted salary', 'salary percentage increase', 'tuition fee', "
        "'posteinitial', 'posteactuel', 'tailleinitiale', 'tailleactuelle', "
        "'nationality', 'firstemploymentcountry', 'lastemploymentcountry', etc.)."
    )
    st.stop()

try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Impossible de lire l'Excel : {e}")
    st.stop()

# Normalisation colonnes
df.columns = (
    df.columns.str.strip()
              .str.lower()
              .str.replace(r'[\s\W]+', ' ', regex=True)
              .str.replace('_', ' ')
              .str.strip()
)

# -------------------------
# Calcul scores
# -------------------------
df = compute_scores(df)

# -------------------------
# Mapping affichage
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
df.rename(columns={k:v for k,v in col_rename.items() if k in df.columns}, inplace=True)

# -------------------------
# Recherche globale
# -------------------------
search_term = st.text_input("🔎 Recherche globale", value="").strip()
df_display_base = df.copy()
if search_term:
    mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
    df_display_base = df[mask].copy()

# -------------------------
# Affichage AgGrid
# -------------------------
def afficher_tableau_aggrid(df_to_show, height=400):
    # ID/Nom/Prénom en premier
    id_cols = [c for c in df_to_show.columns if c.lower() in ["id", "identifiant", "identifier"]]
    nom_cols = [c for c in df_to_show.columns if c.lower() in ["nom", "name", "lastname", "surname"]]
    prenom_cols = [c for c in df_to_show.columns if c.lower() in ["prenom", "firstname", "given name"]]
    front_cols = [c for c in [*id_cols[:1], *nom_cols[:1], *prenom_cols[:1]] if c is not None]

    remaining_cols = [c for c in df_to_show.columns if c not in front_cols]
    df_to_show = df_to_show[front_cols + remaining_cols]

    gb = GridOptionsBuilder.from_dataframe(df_to_show)
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        minWidth=100,
        maxWidth=300
    )
    grid_options = gb.build()
    AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        theme="streamlit",
        height=height,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True
    )

# -------------------------
# Onglets / Sections
# -------------------------
tab1, tab2 = st.tabs(["📋 Tableaux", "📈 Analyses"])

with tab1:
    score_cols = [c for c in df_display_base.columns if "score" in str(c).lower() or str(c).lower() in ["final_score", "🏆 score final"]]

    # Scores card
    with st.container():
        st.markdown('<div class="card"><h3>Scores</h3></div>', unsafe_allow_html=True)
        afficher_tableau_aggrid(df_display_base, height=380)

    # Données originales card
    no_score_cols = [c for c in df_display_base.columns if c not in score_cols]
    with st.container():
        st.markdown('<div class="card"><h3>Données originales</h3></div>', unsafe_allow_html=True)
        afficher_tableau_aggrid(df_display_base[no_score_cols + [c for c in df_display_base.columns if c.lower() in ["id","nom","prenom"]]], height=380)

    # Tableau complet card
    with st.container():
        st.markdown('<div class="card"><h3>Tableau complet</h3></div>', unsafe_allow_html=True)
        afficher_tableau_aggrid(df_display_base, height=480)

with tab2:
    st.subheader("Visualisations")
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
