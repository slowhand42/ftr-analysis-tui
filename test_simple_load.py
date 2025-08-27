#!/usr/bin/env python3
"""Quick test to check what columns are in the data."""

import pandas as pd
import sys
sys.path.insert(0, '.')

from src.core.data_manager import ExcelDataManager

# Load the data
dm = ExcelDataManager()
dm.load_excel("./analysis_files/flow_results_processed_SEP25_R1_small.xlsx")

# Get a cluster
df = dm.get_cluster_data("SEP25", 4)

print("Columns in dataframe:")
print(list(df.columns)[:20])  # First 20 columns

print("\nFirst row data:")
for col in ["CLUSTER", "SP", "VIEW", "PACTUAL", "LIMIT"]:
    if col in df.columns:
        print(f"  {col}: {df.iloc[0][col] if len(df) > 0 else 'N/A'}")

print(f"\nDataframe shape: {df.shape}")
print(f"First 10 column names: {list(df.columns)[:10]}")

# Check if there are any columns with names like constraint or ID
print("\nColumns with 'ID' or 'CONSTRAINT' or 'NAME':")
for col in df.columns:
    if 'ID' in col.upper() or 'CONSTRAINT' in col.upper() or 'NAME' in col.upper():
        print(f"  {col}")