import pandas as pd


async def update_table(gdrive_id: str, sheet_name: str) -> pd.DataFrame:
    """Update the table from Google Drive."""
    df = pd.read_excel(f"https://docs.google.com/spreadsheets/d/{gdrive_id}/export?format=xlsx", sheet_name=sheet_name)
    return df
