import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="CBAM Penalty Analyzer", layout="wide")
st.title("CBAM Scope 3 Penalty Analyzer")

# Inline sample data for the download button
sample_csv = """Component,Material_Type,Origin,Weight_tonnes,Supplier_Verified_EF
Pump Casing,Steel Slab,China,2.5,
Impeller,Steel Slab,Germany,0.4,1.450
Shaft,Steel Slab,China,0.8,
Fasteners,Steel Slab,India,0.1,"""

st.markdown("Upload a supplier Bill of Materials (BOM) to calculate regulatory financial exposure under the EU Carbon Border Adjustment Mechanism (CBAM).")

col1, col2 = st.columns([1, 1])
with col1:
    st.download_button(
        label="Download Sample BOM (pump_bom.csv)",
        data=sample_csv,
        file_name="pump_bom.csv",
        mime="text/csv"
    )

uploaded_file = st.file_uploader("Upload BOM CSV", type="csv")

# Trigger calculation if a file is uploaded OR the user clicks the demo button
if uploaded_file or st.button("Run Demonstration Scenario"):
    
    if uploaded_file:
        df_bom = pd.read_csv(uploaded_file)
    else:
        df_bom = pd.read_csv(io.StringIO(sample_csv))
        
    df_ef = pd.read_csv('cbam_ef.csv')
    
    # Core ETL Logic
    df_merged = pd.merge(df_bom, df_ef, on="Material_Type", how="left")
    df_merged['Applied_EF'] = np.where(df_merged['Supplier_Verified_EF'].notna(), df_merged['Supplier_Verified_EF'], df_merged['Default_Penalty_EF'])
    
    # Financial Calculation
    df_merged['CBAM_Cost_EUR'] = df_merged['Weight_tonnes'] * df_merged['Applied_EF'] * 0.485 * 86.43
    df_merged['Ideal_Cost_EUR'] = df_merged['Weight_tonnes'] * df_merged['EU_Benchmark_EF'] * 0.485 * 86.43
    df_merged['Penalty_Paid_EUR'] = df_merged['CBAM_Cost_EUR'] - df_merged['Ideal_Cost_EUR']
    
    st.markdown("---")
    
    # Executive KPI Cards
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total Penalty (Per Unit)", value=f"€{df_merged['Penalty_Paid_EUR'].sum():.2f}")
    
    top_risk = df_merged.loc[df_merged['Penalty_Paid_EUR'].idxmax()]
    kpi2.metric(label="Top Risk Component", value=top_risk['Component'], delta=f"€{top_risk['Penalty_Paid_EUR']:.2f}", delta_color="inverse")
    
    verified_pct = (df_merged['Supplier_Verified_EF'].notna().sum() / len(df_merged)) * 100
    kpi3.metric(label="Supplier Data Completeness", value=f"{verified_pct:.0f}%")
    
    # Visualizations
    st.subheader("Itemized Financial Penalty")
    st.dataframe(df_merged[['Component', 'Origin', 'Penalty_Paid_EUR', 'Applied_EF']], use_container_width=True)
    st.bar_chart(df_merged.set_index('Component')['Penalty_Paid_EUR'])
