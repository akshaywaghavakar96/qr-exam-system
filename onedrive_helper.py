"""
OneDrive Helper - Reads/Writes Excel file via Microsoft Graph API
Set these environment variables:
  ONEDRIVE_CLIENT_ID     - Azure App Client ID
  ONEDRIVE_CLIENT_SECRET - Azure App Client Secret
  ONEDRIVE_TENANT_ID     - Azure Tenant ID (use 'common' for personal)
  ONEDRIVE_FILE_PATH     - Path to Excel file in OneDrive e.g. /exam_data.xlsx
"""

import os
import io
import requests
import pandas as pd

CLIENT_ID     = os.environ.get("ONEDRIVE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ONEDRIVE_CLIENT_SECRET")
TENANT_ID     = os.environ.get("ONEDRIVE_TENANT_ID", "common")
FILE_PATH     = os.environ.get("ONEDRIVE_FILE_PATH", "/exam_data.xlsx")

SHEETS = {
    "Users":       ["username", "password", "registered_date"],
    "ExamResults": ["username", "score", "passed", "cert_id", "date"],
}

def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

def download_excel():
    """Download the Excel file from OneDrive and return as BytesIO."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    encoded_path = FILE_PATH.replace("/", "%2F").lstrip("%2F")
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"
    r = requests.get(url, headers=headers)

    if r.status_code == 404:
        # File doesn't exist yet → return None
        return None
    r.raise_for_status()
    return io.BytesIO(r.content)

def upload_excel(buffer):
    """Upload the Excel BytesIO buffer back to OneDrive."""
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    encoded_path = FILE_PATH.replace("/", "%2F").lstrip("%2F")
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"
    buffer.seek(0)
    r = requests.put(url, headers=headers, data=buffer.read())
    r.raise_for_status()

def read_excel_from_onedrive(sheet_name):
    """Read a sheet from OneDrive Excel. Returns empty DataFrame if missing."""
    buf = download_excel()
    if buf is None:
        return pd.DataFrame(columns=SHEETS[sheet_name])
    try:
        df = pd.read_excel(buf, sheet_name=sheet_name)
        # Ensure all expected columns exist
        for col in SHEETS[sheet_name]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=SHEETS[sheet_name])

def write_excel_to_onedrive(df, sheet_name):
    """Write a DataFrame to a sheet in the OneDrive Excel file."""
    buf = download_excel()

    # Load existing data into all sheets
    existing_sheets = {}
    if buf is not None:
        try:
            xf = pd.ExcelFile(buf)
            for name in xf.sheet_names:
                existing_sheets[name] = xf.parse(name)
        except Exception:
            pass

    # Update the target sheet
    existing_sheets[sheet_name] = df

    # Write all sheets back
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, data in existing_sheets.items():
            data.to_excel(writer, sheet_name=name, index=False)

    upload_excel(out)
