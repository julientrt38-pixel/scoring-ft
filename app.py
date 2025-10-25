import streamlit as st
import pandas as pd
from calculs import compute_scores
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide", page_title="Scoring FT")

st.title("🔹 Scoring des étudiants – FT")

uploaded_file = st.file_uploader("📤 Charger un fichier Excel", type=["xlsx", "xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df = compute_scores(df)

    st.subheader("📊 Tableau des scores")
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filterable=True, resizable=True, sortable=True)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, fit_columns_on_grid_load=True)
