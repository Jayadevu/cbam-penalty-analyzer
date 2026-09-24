import streamlit as st
import pandas as pd
import numpy as np

st.title("CBAM Scope 3 Penalty Analyzer")

uploaded_file = st.file_uploader(
    "Upload BOM CSV (e.g., pump_bom.csv)", type="csv")

if uploaded_file:
    df_bom = pd.read_csv(uploaded_file)
    # Loads the database you generated earlier
    df_ef = pd.read_csv('cbam_ef.csv')

    df_merged = pd.merge(df_bom, df_ef, on="Material_Type", how="left")
    df_merged['Applied_EF'] = np.where(df_merged['Supplier_Verified_EF'].notna(
    ), df_merged['Supplier_Verified_EF'], df_merged['Default_Penalty_EF'])

    df_merged['CBAM_Cost_EUR'] = df_merged['Weight_tonnes'] * \
        df_merged['Applied_EF'] * 0.485 * 86.43
    df_merged['Ideal_Cost_EUR'] = df_merged['Weight_tonnes'] * \
        df_merged['EU_Benchmark_EF'] * 0.485 * 86.43
    df_merged['Penalty_Paid_EUR'] = df_merged['CBAM_Cost_EUR'] - \
        df_merged['Ideal_Cost_EUR']

    st.subheader("Financial Penalty by Component")
    st.dataframe(df_merged[['Component', 'Origin', 'Penalty_Paid_EUR']])
    st.bar_chart(df_merged.set_index('Component')['Penalty_Paid_EUR'])
