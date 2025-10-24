import streamlit as st
import pandas as pd
import numpy as np

st.title("Calculateur de scoring FT")

# =======================
# 🔹 Upload du fichier Excel
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
    st.write("Colonnes détectées :", list(df.columns))

    # ============================================
    # 🔹 Fonctions de calcul des critères
    # ============================================

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
        start_size_val = get_company_size(start_size)
        current_size_val = get_company_size(current_size)
        level_progress = max(0, current_level - start_level)
        size_progress = max(0, current_size_val - start_size_val)
        score = (level_progress + size_progress) / 7
        return min(1, round(score, 3))

    # ====================================
    # 🔹 Calcul des scores
    # ====================================

    # Correspondance avec les colonnes Excel
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

    # Score final = moyenne de tous les scores
    score_cols = [c for c in df.columns if c.endswith("_score")]
    df["final_score"] = df[score_cols].mean(axis=1)

    st.success("✅ Calcul des scores terminé.")
    st.dataframe(df.head(10))

    # Téléchargement
    output_file = "resultats_scores.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    with open(output_file, "rb") as f:
        st.download_button("Télécharger le fichier Excel", f, file_name=output_file)
