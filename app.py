# =======================
# app.py complet
# =======================

import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder

# =======================
# 🔹 Page Streamlit
# =======================
st.set_page_config(page_title="FT Scoring", layout="wide")
st.title("Calculateur de scoring FT")

# =======================
# 🔹 Upload Excel
# =======================
uploaded_file = st.file_uploader("Choisissez votre fichier Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Nettoyage des noms de colonnes
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(r'[\s\W]+', ' ', regex=True)
                  .str.replace('_', ' ')
                  .str.strip()
    )
    st.success("Fichier chargé et colonnes nettoyées")
    st.write("Colonnes détectées :", list(df.columns))

    # =======================
    # 🔹 Fonctions de calcul des scores
    # =======================
    def weighted_salary(salary):
        if pd.isna(salary):
            return np.nan
        salary = max(30000, min(150000, salary))
        return (salary - 30000) / (150000 - 30000)

    def salary_increase(perc):
        if pd.isna(perc):
            return np.nan
        perc = max(0, min(100, perc))
        return perc / 100

    def simple_scale(value):
        if pd.isna(value):
            return np.nan
        return min(1, max(0, value / 10))

    def value_for_money(salary, tuition):
        if pd.isna(salary) or pd.isna(tuition):
            return np.nan
        value = salary - tuition
        value = max(10000, min(100000, value))
        return (value - 10000) / (100000 - 10000)

    def international_work_mobility(fm, fn, fo):
        if (fn == "-" and fo == "-"):
            return np.nan
        score = 0
        if fn != "-":
            if fm != "France" and fn == "France":
                score += 0.25
            elif fn != fm:
                score += 1
        if fo != "-":
            if fn == "-":
                if fm != "France" and fo == "France":
                    score += 0.25
                elif fo != fm:
                    score += 1
            else:
                if fo != fn and fo != fm and fo != "France":
                    score += 0.5
                elif fm == fn and fo != fm and fo != fn:
                    score += 1
                elif fo == "France" and fm != "France" and fn != "France":
                    score += 0.5
        score = (score * 10 / 1.5) / 10
        return min(1, round(score, 3))

    def career_progress_score(start_title, current_title, start_size, current_size):
        levels = {
            1: ["intern", "assistant", "analyst", "associate", "trainee"],
            2: ["manager", "senior", "specialist", "lead", "head"],
            3: ["director", "vp", "vice president", "chief", "ceo", "founder", "president"]
        }
        def get_level(title):
            if pd.isna(title):
                return 1
            title = str(title).lower()
            for lvl, keywords in levels.items():
                if any(k in title for k in keywords):
                    return lvl
            return 1

        def get_company_size(size_label):
            if pd.isna(size_label):
                return 1
            mapping = {
                "1 to 9 employees": 1,
                "10 to 19 employees": 2,
                "20 to 49 employees": 3,
                "50 to 249 employees": 4,
                "250 to 4999 employees": 5,
                "5000 employees and more": 6
            }
            for key in mapping:
                if key in str(size_label).lower():
                    return mapping[key]
            return 1

        start_level = get_level(start_title)
        current_level = get_level(current_title)
        start_size_num = get_company_size(start_size)
        current_size_num = get_company_size(current_size)

        level_progress = max(0, current_level - start_level)
        size_progress = max(0, current_size_num - start_size_num)
        score = (level_progress + size_progress) / 7
        return min(1, round(score, 3))

    # =======================
    # 🔹 Calcul des scores
    # =======================
    df["weighted_salary_score"] = df["weighted salary"].apply(weighted_salary)
    df["salary_increase_score"] = df["salary percentage increase"].apply(salary_increase)
    df["aims_achieved_score"] = df["aims achieved"].apply(simple_scale)
    df["career_service_score"] = df["careers service satisfaction"].apply(simple_scale)
    df["alumni_network_score"] = df["alumni network satisfaction"].apply(simple_scale)
    df["value_for_money_score"] = df.apply(lambda x: value_for_money(x["weighted salary"], x["tuition fee"]), axis=1)
    df["career_progress_score"] = df.apply(lambda x: career_progress_score(x["posteinitial"], x["posteactuel"],
                                                                           x["tailleinitiale"], x["tailleactuelle"]), axis=1)

    score_cols = [c for c in df.columns if c.endswith("_score")]
    df["final_score"] = df[score_cols].mean(axis=1)

    st.success("Calcul des scores terminé ✅")

    # =======================
    # 🔹 Onglets Streamlit
    # =======================
    tab1, tab2 = st.tabs(["Tableaux", "Visualisations"])

    # ==================== Onglet Tableaux ====================
    with tab1:
        st.subheader("Scores seulement")
        scores_cols = score_cols + ["final_score"]
        df_scores = df[scores_cols]
        gb1 = GridOptionsBuilder.from_dataframe(df_scores)
        gb1.configure_default_column(filter=True, sortable=True, editable=False)
        gridOptions1 = gb1.build()
        AgGrid(df_scores, gridOptions=gridOptions1, height=300, fit_columns_on_grid_load=True)

        st.subheader("Données originales sans scores")
        original_cols = [c for c in df.columns if c not in scores_cols + ["final_score"]]
        df_original = df[original_cols]
        gb2 = GridOptionsBuilder.from_dataframe(df_original)
        gb2.configure_default_column(filter=True, sortable=True, editable=False)
        gridOptions2 = gb2.build()
        AgGrid(df_original, gridOptions=gridOptions2, height=300, fit_columns_on_grid_load=True)

        st.subheader("Tableau complet")
        gb3 = GridOptionsBuilder.from_dataframe(df)
        gb3.configure_default_column(filter=True, sortable=True, editable=False)
        gridOptions3 = gb3.build()
        AgGrid(df, gridOptions=gridOptions3, height=400, fit_columns_on_grid_load=True)

    # ==================== Onglet Visualisations ====================
    with tab2:
        st.subheader("Visualisations des scores")
        st.info("Les graphiques seront ajoutés ici prochainement.")


