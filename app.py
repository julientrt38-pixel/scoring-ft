import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =======================
# 🔹 Page Streamlit
# =======================
st.set_page_config(page_title="FT Scoring", layout="wide")
st.title("Calculateur de scoring FT")
st.markdown("""
Cette application permet aux écoles de calculer automatiquement les scores des profils étudiants
selon les critères utilisés par le Financial Times.  
**Instructions :**  
- Téléversez votre fichier Excel avec les colonnes attendues.  
- Vérifiez les colonnes détectées ci-dessous.  
- Visualisez les scores, top 10 et graphiques.
""")

# =======================
# 🔹 Upload fichier
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
    st.subheader("Colonnes détectées")
    st.write(list(df.columns))

    # ============================================
    # 🔹 Fonctions de calcul des scores
    # ============================================
    def weighted_salary(salary):
        if pd.isna(salary): return np.nan
        salary = max(30000, min(150000, salary))
        return (salary - 30000) / (150000 - 30000)

    def salary_increase(perc):
        if pd.isna(perc): return np.nan
        perc = max(0, min(100, perc))
        return perc / 100

    def simple_scale(value):
        if pd.isna(value): return np.nan
        return min(1, max(0, value / 10))

    def value_for_money(salary, tuition):
        if pd.isna(salary) or pd.isna(tuition): return np.nan
        value = salary - tuition
        value = max(10000, min(100000, value))
        return (value - 10000) / (100000 - 10000)

    def career_progress_score(start_title, current_title, start_size, current_size):
        levels = {
            1: ["intern", "assistant", "analyst", "associate", "trainee"],
            2: ["manager", "senior", "specialist", "lead", "head"],
            3: ["director", "vp", "vice president", "chief", "ceo", "founder", "president"]
        }
        def get_level(title):
            if pd.isna(title): return 1
            title = str(title).lower()
            for lvl, keywords in levels.items():
                if any(k in title for k in keywords):
                    return lvl
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
    # 🔹 Mapping colonnes pour les scores
    # ====================================
    mapping = {
        "weighted_salary": "weighted salary",
        "salary_increase": "salary percentage increase",
        "aims_achieved": "aims achieved",
        "value_for_money": "value for money",
        "tuition": "tuition fee",
        "career_service": "careers service satisfaction",
        "alumni_network": "alumni network satisfaction",
        "start_title": "posteinitial",
        "current_title": "posteactuel",
        "start_size": "tailleinitiale",
        "current_size": "tailleactuelle"
    }

    # ====================================
    # 🔹 Calcul des scores
    # ====================================
    df["weighted_salary_score"] = df[mapping["weighted_salary"]].apply(weighted_salary)
    df["salary_increase_score"] = df[mapping["salary_increase"]].apply(salary_increase)
    df["aims_achieved_score"] = df[mapping["aims_achieved"]].apply(simple_scale)
    df["career_service_score"] = df[mapping["career_service"]].apply(simple_scale)
    df["alumni_network_score"] = df[mapping["alumni_network"]].apply(simple_scale)
    df["value_for_money_score"] = df.apply(
        lambda x: value_for_money(x[mapping["weighted_salary"]], x[mapping["tuition"]]), axis=1)
    df["career_progress_score"] = df.apply(
        lambda x: career_progress_score(x[mapping["start_title"]], x[mapping["current_title"]],
                                        x[mapping["start_size"]], x[mapping["current_size"]]), axis=1)

    # Score final
    score_cols = [c for c in df.columns if c.endswith("_score")]
    df["final_score"] = df[score_cols].mean(axis=1)

    # =======================================
    # 🔹 Onglets : Données + Analyses
    # =======================================
    tab1, tab2 = st.tabs(["Données & Top 10", "Visualisations"])

    # ------------------- Onglet 1 -------------------
    with tab1:
        st.subheader("Tableau complet avec scores")
        st.dataframe(df.head(20))

        # Filtres interactifs
        st.subheader("Filtrer les profils")
        score_min = st.slider("Score minimum", 0.0, 1.0, 0.0)
        filtered_df = df[df["final_score"] >= score_min]
        st.dataframe(filtered_df.head(20))

        # Top 10
        st.subheader("Top 10 profils")
        top10 = df.sort_values("final_score", ascending=False).head(10)
        st.dataframe(top10)

        # Téléchargements
        output_file = "resultats_scores.xlsx"
        df.to_excel(output_file, index=False, engine='openpyxl')
        with open(output_file, "rb") as f:
            st.download_button("Télécharger le fichier complet", f, file_name=output_file)

        top10_file = "top10_scores.xlsx"
        top10.to_excel(top10_file, index=False, engine='openpyxl')
        with open(top10_file, "rb") as f:
            st.download_button("Télécharger le Top 10", f, file_name=top10_file)

    # ------------------- Onglet 2 -------------------
    with tab2:
        st.subheader("Distribution des scores")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("final_score", bin=alt.Bin(maxbins=20)),
            y='count()'
        )
        st.altair_chart(chart, use_container_width=True)

        st.subheader("Boxplot des scores par critère")
        score_melted = df[score_cols].melt(var_name='critere', value_name='score')
        boxplot = alt.Chart(score_melted).mark_boxplot().encode(
            x='critere',
            y='score'
        )
        st.altair_chart(boxplot, use_container_width=True)
