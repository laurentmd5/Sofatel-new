import pandas as pd
import sys
import os

try:
    file_path = 'MAQUETTE PROD VF xlsx.xlsx'
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    df = pd.read_excel(file_path)
    print("Columns:", list(df.columns))
    if not df.empty:
        print("First row values:")
        for col, val in df.iloc[0].to_dict().items():
            print(f"  {col}: {val}")
    else:
        print("Empty DataFrame")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
