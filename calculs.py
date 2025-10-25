import pandas as pd
import numpy as np

# 🔹 Fonctions de calcul
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
    val = salary - tuition
    val = max(10000, min(100000, val))
    return (val - 10000) / (100000 - 10000)

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

    size_map = {
        "1 to 9 employees": 1,
        "10 to 19 employees": 2,
        "20 to 49 employees": 3,
        "50 to 249 employees": 4,
        "250 to 4999 employees": 5,
        "5000 employees and more": 6
    }

    def get_size(size_label):
        if pd.isna(size_label):
            return 1
        for key, val in size_map.items():
            if key.lower() in str(size_label).lower():
                return val
        return 1

    lvl_start, lvl_curr = get_level(start_title), get_level(current_title)
    sz_start, sz_curr = get_size(start_size), get_size(current_size)
    score = (max(0, lvl_curr - lvl_start) + max(0, sz_curr - sz_start)) / 7
    return min(1, round(score, 3))

# 🔹 Fonction principale pour calculer les scores
def compute_scores(df):
    # Nettoyer les colonnes pour éviter les KeyError
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(r'[\s\W]+', '_', regex=True)
    )

    mapping = {
        "weighted_salary": ["weighted_salary", "salaire"],
        "salary_increase": ["salary_percentage_increase", "croissance_salaire"],
        "aims_achieved": ["aims_achieved", "objectifs_atteints"],
        "value_for_money": ["value_for_money", "rentabilite_ecole"],
        "tuition": ["tuition_fee", "frais_de_scolarite"],
        "career_service": ["careers_service_satisfaction", "service_carriere"],
        "alumni_network": ["alumni_network_satisfaction", "reseau_alumni"],
        "fm": ["nationality", "nationalite"],
        "fn": ["firstemploymentcountry", "1er_pays_d_emploi"],
        "fo": ["lastemploymentcountry", "dernier_pays_d_emploi"],
        "start_title": ["posteinitial", "poste_initial"],
        "current_title": ["posteactuel", "poste_actuel"],
        "start_size": ["tailleinitiale", "taille_entreprise_initiale"],
        "current_size": ["tailleactuelle", "taille_entreprise_actuelle"]
    }

    def find_column(names):
        for name in names:
            if name in df.columns:
                return name
        return None

    # Appliquer les scores
    df["weighted_salary_score"] = df[find_column(mapping["weighted_salary"])].apply(weighted_salary)
    df["salary_increase_score"] = df[find_column(mapping["salary_increase"])].apply(salary_increase)
    df["aims_achieved_score"] = df[find_column(mapping["aims_achieved"])].apply(simple_scale)
    df["career_service_score"] = df[find_column(mapping["career_service"])].apply(simple_scale)
    df["alumni_network_score"] = df[find_column(mapping["alumni_network"])].apply(simple_scale)

    df["value_for_money_score"] = df.apply(
        lambda x: value_for_money(x[find_column(mapping["weighted_salary"])],
                                   x[find_column(mapping["tuition"])]), axis=1)

    df["intl_work_mobility_score"] = df.apply(
        lambda x: international_work_mobility(
            x[find_column(mapping["fm"])],
            x[find_column(mapping["fn"])],
            x[find_column(mapping["fo"])]
        ), axis=1)

    df["career_progress_score"] = df.apply(
        lambda x: career_progress_score(
            x[find_column(mapping["start_title"])],
            x[find_column(mapping["current_title"])],
            x[find_column(mapping["start_size"])],
            x[find_column(mapping["current_size"])]
        ), axis=1)

    # Score final = moyenne des critères disponibles
    score_cols = [c for c in df.columns if c.endswith("_score")]
    df["final_score"] = df[score_cols].mean(axis=1)

    return df
