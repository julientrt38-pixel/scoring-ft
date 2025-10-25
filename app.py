# app.py — Version complète, prête à coller
import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# -------------------------
# Configuration page
# -------------------------
st.set_page_config(page_title="FT Scoring App", layout="wide")
st.title("📊 Dashboard — Évaluation Masters in Management")

# -------------------------
# PARTIE ANALYTIQUE : fonctions de scoring
# -------------------------
def weighted_salary(salary):
    if pd.isna(salary): return np.nan
    salary = max(30000, min(150000, salary))
    return round((salary - 30000) / (150000 - 30000), 2)

def salary_increase(perc):
    if pd.isna(perc): return np.nan
    perc = max(0, min(100, perc))
    return round(perc / 100, 2)

def simple_scale(value):
    if pd.isna(value): return np.nan
    return round(min(1, max(0, value / 10)), 2)

def value_for_money(salary, tuition):
    if pd.isna(salary) or pd.isna(tuition): return np.nan
    value = salary - tuition
    value = max(10000, min(100000, value))
    return round((value - 10000) / (100000 - 10000), 2)

def international_work_mobility(fm, fn, fo):
    if (fn == "-" and fo == "-"): return np.nan
    score = 0
    if fn != "-":
        if fm != "France" and fn == "France": score += 0.25
        elif fn != fm: score += 1
    if fo != "-":
        if fn == "-":
            if fm != "France" and fo == "France": score += 0.25
            elif fo != fm: score += 1
        else:
            if fo != fn and fo != fm and fo != "France": score += 0.5
            elif fm == fn and fo != fm and fo != fn: score += 1
            elif fo == "France" and fm != "France" and fn != "France": score += 0.5
    return round(min(1, score * 10 / 1.5 / 10), 2)

def career_progress_score(start_title, current_title, start_size, current_size):
    levels = {
        1: ["intern", "assistant", "analyst", "associate", "trainee"],
        2: ["manager", "senior", "specialist", "lead", "head"],
        3: ["director", "vp", "chief", "ceo", "founder", "president"]
    }
    def get_level(title):
        if pd.isna(title): return 1
        title = str(title).lower()
        for lvl, keywords in levels.items():
            if any(k in title for k in keywords): return lvl
        return 1
    def get_company_size(size_label):
        if pd.isna(size_label): return 1
        mapping = {
            "1 to 9 employees": 1,
            "10 to 19 employees": 2,
            "20 to 49 employees": 3,
            "50 to 249 employees": 4,
            "250 to 4999 employees": 5,
            "5000 employees and more": 6
        }
        for key in mapping:
            if key in str(size_label).lower(): return mapping[key]
        return 1

    start_level = get_level(start_title)
    current_level = get_level(current_title)
    start_size = get_company_size(start_size)
    current_size = get_company_size(current_size)

    level_progress = max(0, current_level - start_level)
    size_progress = max(0, current_size - start_size)
    score = (level_progress + size_progress) / 7
    return round(min(1, score), 2)

def compute_scores(df):
    # mapping des colonnes sources (attendues)
    mapping = {
        "weighted_salary": "weighted salary",
        "salary_increase": "salary percentage increase",
        "aims_achieved": "aims achieved",
        "value_for_money": "value for money",
        "tuition": "tuition fee",
        "career_service": "careers service satisfaction",
        "alumni_network": "alumni network satisfaction",
        "fm": "nationality",
        "fn": "firstemploymentcountry",
        "fo": "lastemploymentcountry",
        "start_title": "posteinitial",
        "current_title": "posteactuel",
        "start_size": "tailleinitiale",
        "current_size": "tailleactuelle"
    }

    # safe checks : si une colonne manque, on évite le crash en ajoutant NaN
    for key, col in mapping.items():
        if col not in df.columns:
            df[col] = np.nan

    # arrondir num cols d'origine (sécurité)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df[num_cols] = df[num_cols].round(2)

    # calculs
    df["weighted_salary_score"]   = df[mapping["weighted_salary"]].apply(weighted_salary)
    df["salary_increase_score"]   = df[mapping["salary_increase"]].apply(salary_increase)
    df["aims_achieved_score"]     = df[mapping["aims_achieved"]].apply(simple_scale)
    df["career_service_score"]    = df[mapping["career_service"]].apply(simple_scale)
    df["alumni_network_score"]    = df[mapping["alumni_network"]].apply(simple_scale)
    df["value_for_money_score"]   = df.apply(lambda x: value_for_money(x[mapping["weighted_salary"]], x[mapping["tuition"]]), axis=1)
    df["intl_work_mobility_score"]= df.apply(lambda x: international_work_mobility(x[mapping["fm"]], x[mapping["fn"]], x[mapping["fo"]]), axis=1)
    df["career_progress_score"]   = df.apply(lambda x: career_progress_score(x[mapping["start_title"]], x[mapping["current_title"]], x[mapping["start_size"]], x[mapping["current_size"]]), axis=1)

    score_cols = [c for c in df.columns if c.endswith("_score")]
    # final_score
    if len(score_cols) > 0:
        df["final_score"] = df[score_cols].mean(axis=1).round(2)
    else:
        df["final_score"] = np.nan

    # arrondir scores à 2 décimales (sécurité)
    for sc in score_cols + ["final_score"]:
        if sc in df.columns:
            df[sc] = df[sc].round(2)

    return df

# -------------------------
# upload de l'Excel (interface)
# -------------------------
uploaded_file = st.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])
if not uploaded_file:
    st.info("Téléverse un fichier Excel contenant tes données (colonnes attendues: 'weighted salary', 'salary percentage increase', 'tuition fee', 'posteinitial', 'posteactuel', 'tailleinitiale', 'tailleactuelle', 'nationality', 'firstemploymentcountry', 'lastemploymentcountry', etc.).")
    st.stop()

# lecture
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Impossible de lire l'Excel : {e}")
    st.stop()

# nettoyage des en-têtes (normalize)
df.columns = (
    df.columns.str.strip()
              .str.lower()
              .str.replace(r'[\s\W]+', ' ', regex=True)  # espaces et caractères non alphanum remplacés par espace
              .str.replace('_', ' ')
              .str.strip()
)

# compute scores (ajoute colonnes _score et final_score)
df = compute_scores(df)

# ---- mapping pour renommage affichage (émoticones + libellés)
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

# rename only if column exists
existing_renames = {k: v for k, v in col_rename.items() if k in df.columns}
df.rename(columns=existing_renames, inplace=True)

# -------------------------
# Recherche globale (server-side) : champ texte
# -------------------------
search_term = st.text_input("🔎 Recherche globale (texte présent n'importe où dans la ligne)", value="").strip()
if search_term:
    mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
    df_display_base = df[mask].copy()
else:
    df_display_base = df.copy()

# -------------------------
# Utilitaires AgGrid display
# -------------------------
# JS pour centrer les cellules proprement
cell_style_jscode = JsCode("""
function(params) {
    return {'textAlign': 'center', 'whiteSpace': 'normal', 'overflow': 'hidden', 'textOverflow': 'ellipsis'};
}
""")

def afficher_tableau_aggrid(df_to_show, height=350):
    """
    Affiche le dataframe avec AgGrid, colonnes centrées, en-têtes wrap, min/max width raisonnable.
    """
    # reorder to bring ID/nom/prenom first if present (on cherche noms communs dans en-têtes)
    possible_id_names = ['id', 'identifiant', 'identifier']
    possible_nom = ['nom', 'name', 'last name', 'lastname', 'surname']
    possible_prenom = ['prenom', 'first name', 'firstname', 'given name']

    cols = list(df_to_show.columns)
    first_cols = []
    for cands in (possible_id_names, possible_nom, possible_prenom):
        for c in cols:
            if c.lower() in cands:
                if c not in first_cols:
                    first_cols.append(c)
                break

    # ensure we keep original order for other columns
    remaining = [c for c in cols if c not in first_cols]
    df_to_show = df_to_show[first_cols + remaining]

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
    # enable quick filter in the UI (AgGrid shows a top quick filter if set in gridOptions)
    grid_options = gb.build()
    # add suppress row transform? keep default
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

    # Scores only: select columns that are renamed scores OR end with _score OR final_score
    # We want to ensure ID/nom/prénom are present in that view
    # Use display DataFrame df_display_base (which already takes into account search)
    df_base = df_display_base.copy()

    # detect ID/NOM/PRÉNOM columns (after rename they might be e.g. 'nom' etc.)
    # We'll look for original variants (lowercase)
    id_candidates = [c for c in df_base.columns if c.lower() in ["id", "identifiant", "identifier"]]
    nom_candidates = [c for c in df_base.columns if c.lower() in ["nom", "name", "last name", "lastname", "surname"]]
    prenom_candidates = [c for c in df_base.columns if c.lower() in ["prenom", "first name", "firstname", "given name"]]

    id_col = id_candidates[0] if id_candidates else None
    nom_col = nom_candidates[0] if nom_candidates else None
    prenom_col = prenom_candidates[0] if prenom_candidates else None

    # Compose scores-only columns
    scores_cols = [c for c in df_base.columns if ("score" in str(c).lower()) or (str(c).lower() == "🏆 score final") or (str(c).lower() == "final_score")]
    # ensure the display includes ID / nom / prenom first
    front_cols = [col for col in [id_col, nom_col, prenom_col] if col is not None]
    scores_view_cols = front_cols + [c for c in scores_cols if c not in front_cols]
    # fallback if no score columns found: show final_score + any *_score
    if len(scores_view_cols) == 0:
        # try common names
        for candidate in ["final_score", "final score", "🏆 score final", "🏆 score final".lower()]:
            if candidate in df_base.columns:
                scores_view_cols = front_cols + [candidate]
                break
    # Display scores-only table
    if len(scores_view_cols) == 0:
        st.info("Aucun score détecté dans les colonnes. Le tableau complet est affiché ci-dessous.")
        afficher_tableau_aggrid(df_base, height=380)
    else:
        df_scores_view = df_base[scores_view_cols].copy()
        st.markdown("**Tableau : Scores (avec ID / Nom / Prénom si détectés)**")
        afficher_tableau_aggrid(df_scores_view, height=380)

    st.markdown("---")
    st.subheader("2) Données originales (sans colonnes de score)")
    # columns without *_score and without final_score display
    no_score_cols = [c for c in df_base.columns if not (("score" in str(c).lower()) or (str(c).lower() == "final_score") or (str(c).lower() == "🏆 score final"))]
    if len(no_score_cols) == 0:
        st.info("Aucune colonne brute disponible (toutes semblent être des scores).")
    else:
        afficher_tableau_aggrid(df_base[no_score_cols], height=380)

    st.markdown("---")
    st.subheader("3) Tableau complet (données + scores)")
    afficher_tableau_aggrid(df_base, height=480)

with tab2:
    st.subheader("Visualisations & analyses")
    st.info("Zone pour graphiques interactifs (histogrammes, top N, comparaisons). Je peux ajouter ça maintenant si tu veux.")
    # On peut ajouter des graphiques ici (histogramme simple sur final_score si existant)
    if "final_score" in df.columns:
        try:
            import altair as alt
            chart_df = df[["final_score"]].dropna()
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
