#debug_csv.py
import pandas as pd
import os

def debug_csv():
    csv_path = "logs/health_log.csv"
    if not os.path.exists(csv_path):
        print("❌ CSV file doesn't exist")
        return
    
    df = pd.read_csv(csv_path)
    print("📊 CSV CONTENTS:")
    print(f"Columns: {list(df.columns)}")
    print(f"Total rows: {len(df)}")
    
    if "slouch_flag" in df.columns:
        slouch_count = df["slouch_flag"].sum()
        print(f"Slouch flags found: {slouch_count}")
    
    if "alert" in df.columns:
        alerts = df["alert"].unique()
        print(f"Unique alerts: {alerts}")
    
    print("\nLast 5 rows:")
    print(df.tail())

if __name__ == "__main__":
    debug_csv()