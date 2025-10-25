import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder

# =======================================
# 🔹 PARTIE ANALYTIQUE — Calcul des scores
# =======================================

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
    score = (score * 10 / 1.5) / 10
    return round(min(1, score), 2)

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

    df["weighted_salary_score"] = df[mapping["weighted_salary"]].apply(weighted_salary)
    df["salary_increase_score"] = df[mapping["salary_increase"]].apply(salary_increase)
    df["aims_achieved_score"] = df[mapping["aims_achieved"]].apply(simple_scale)
    df["career_service_score"] = df[mapping["career_service"]].apply(simple_scale)
    df["alumni_network_score"] = df[mapping["alumni_network"]].apply(simple_scale)

    df["value_for_money_score"] = df.apply(
        lambda x: value_for_money(x[mapping["weighted_salary"]], x[mapping["tuition"]]), axis=1)

    df["intl_work_mobility_score"] = df.apply(
        lambda x: international_work_mobility(x[mapping["fm"]], x[mapping["fn"]], x[mapping["fo"]]), axis=1)

    df["career_progress_score"] = df.apply(
        lambda x: career_progress_score(
            x[mapping["start_title"]], x[mapping["current_title"]],
            x[mapping["start_size"]], x[mapping["current_size"]]), axis=1)

    score_cols = [c for c in df.columns if c.endswith("_score")]
    df["final_score"] = df[score_cols].mean(axis=1).round(2)
    return df

# ====================================================
# 🔹 PARTIE INTERFACE — Affichage des tableaux & onglets
# ====================================================

st.set_page_config(page_title="FT Scoring App", layout="wide")
st.title("📊 Tableau de bord — Évaluation des Masters in Management")

uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = compute_scores(df)

    # Renommage colonnes avec emojis + simplification
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
    df.rename(columns=col_rename, inplace=True)

    # Création des onglets
    tab1, tab2 = st.tabs(["📋 Données & Tableaux", "📈 Analyses"])

    with tab1:
        st.subheader("📊 Tableau avec scores uniquement")
        score_cols = [c for c in df.columns if "score" in c.lower()]
        df_scores = df[score_cols]

        gb = GridOptionsBuilder.from_dataframe(df_scores)
        gb.configure_default_column(resizable=True, filter=True, sortable=True, min_column_width=120, wrapHeaderText=True, autoHeaderHeight=True)
        grid_options = gb.build()
        AgGrid(df_scores, gridOptions=grid_options, height=400)

        st.subheader("📁 Tableau sans scores")
        df_no_scores = df[[c for c in df.columns if not c.lower().endswith("_score") and c != "🏆 Score final"]]
        gb2 = GridOptionsBuilder.from_dataframe(df_no_scores)
        gb2.configure_default_column(resizable=True, filter=True, sortable=True, min_column_width=120, wrapHeaderText=True, autoHeaderHeight=True)
        AgGrid(df_no_scores, gridOptions=gb2.build(), height=400)

        st.subheader("📑 Tableau complet")
        gb3 = GridOptionsBuilder.from_dataframe(df)
        gb3.configure_default_column(resizable=True, filter=True, sortable=True, min_column_width=120, wrapHeaderText=True, autoHeaderHeight=True)
        AgGrid(df, gridOptions=gb3.build(), height=500)

    with tab2:
        st.subheader("📈 Analyses visuelles à venir...")
        st.info("Les graphiques interactifs seront ajoutés ici prochainement.")
