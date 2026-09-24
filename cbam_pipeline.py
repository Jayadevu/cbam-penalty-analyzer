import pandas as pd
import numpy as np


def generate_mock_data():
    """Generates mock CSV files representing an industrial pump's Bill of Materials and EU emission factors."""
    bom_data = pd.DataFrame({
        'Component': ['Pump Casing', 'Impeller', 'Shaft', 'Fasteners'],
        'Material_Type': ['Steel Slab', 'Steel Slab', 'Steel Slab', 'Steel Slab'],
        'Origin': ['China', 'Germany', 'China', 'India'],
        'Weight_tonnes': [2.5, 0.4, 0.8, 0.1],
        # Only the German supplier provided verified data
        'Supplier_Verified_EF': [np.nan, 1.450, np.nan, np.nan]
    })

    ef_data = pd.DataFrame({
        'Material_Type': ['Steel Slab'],
        'EU_Benchmark_EF': [1.370],
        # EU default penalty for unverified Chinese steel slab
        'Default_Penalty_EF': [3.167]
    })

    bom_data.to_csv('pump_bom.csv', index=False)
    ef_data.to_csv('cbam_ef.csv', index=False)


def calculate_cbam_liability():
    """Calculates the financial penalty incurred due to missing Scope 3 supplier data."""
    df_bom = pd.read_csv('pump_bom.csv')
    df_ef = pd.read_csv('cbam_ef.csv')

    df_merged = pd.merge(df_bom, df_ef, on="Material_Type", how="left")

    # Routing Logic: Apply verified supplier data if it exists; otherwise, apply the default penalty
    df_merged['Applied_EF'] = np.where(
        df_merged['Supplier_Verified_EF'].notna(),
        df_merged['Supplier_Verified_EF'],
        df_merged['Default_Penalty_EF']
    )

    df_merged['Data_Status'] = np.where(
        df_merged['Supplier_Verified_EF'].notna(),
        "Verified",
        "Unverified Default"
    )

    # Carbon and Cost Calculation (2030 Projection)
    cbam_factor = 0.485
    carbon_price = 86.43

    df_merged['Emissions_tCO2e'] = df_merged['Weight_tonnes'] * \
        df_merged['Applied_EF']
    df_merged['CBAM_Cost_EUR'] = df_merged['Emissions_tCO2e'] * \
        cbam_factor * carbon_price

    # Calculate the penalty paid compared to a scenario where all data met the EU benchmark
    df_merged['Ideal_Cost_EUR'] = (
        df_merged['Weight_tonnes'] * df_merged['EU_Benchmark_EF']) * cbam_factor * carbon_price
    df_merged['Penalty_Paid_EUR'] = df_merged['CBAM_Cost_EUR'] - \
        df_merged['Ideal_Cost_EUR']

    return df_merged


if __name__ == "__main__":
    generate_mock_data()
    results = calculate_cbam_liability()

    print("\n--- CBAM Scope 3 Data Audit Report ---")
    print(results[['Component', 'Origin', 'Data_Status', 'Applied_EF',
          'CBAM_Cost_EUR', 'Penalty_Paid_EUR']].to_string(index=False))

    total_penalty = results[results['Data_Status'] ==
                            'Unverified Default']['Penalty_Paid_EUR'].sum()
    print(
        f"\nTotal Financial Penalty due to Missing Supplier Data: €{total_penalty:.2f}")
