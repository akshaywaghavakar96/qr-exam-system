"""
Local File Storage - No OneDrive needed!
Data saved as JSON files in 'data/' folder on the server.
"""

import os
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SHEETS = {
    "Users":       ["username", "password", "registered_date"],
    "ExamResults": ["username", "score", "passed", "cert_id", "date"],
}

def _filepath(sheet_name):
    return os.path.join(DATA_DIR, f"{sheet_name}.json")

def read_excel_from_onedrive(sheet_name):
    path = _filepath(sheet_name)
    if not os.path.exists(path):
        return pd.DataFrame(columns=SHEETS[sheet_name])
    try:
        with open(path, "r") as f:
            records = json.load(f)
        df = pd.DataFrame(records)
        for col in SHEETS[sheet_name]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=SHEETS[sheet_name])

def write_excel_to_onedrive(df, sheet_name):
    path = _filepath(sheet_name)
    records = df.to_dict(orient="records")
    with open(path, "w") as f:
        json.dump(records, f, indent=2, default=str)
