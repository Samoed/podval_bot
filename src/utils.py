import pandas as pd


async def update_table(gdrive_id: str, sheet_name: str) -> pd.DataFrame:
    """Update the table from Google Drive."""
    df = pd.read_excel(f"https://docs.google.com/spreadsheets/d/{gdrive_id}/export?format=xlsx", sheet_name=sheet_name)
    df = df.dropna(subset=["Ник в тг", "Имя", "День Рождения"])
    return df


def escape_markdown(text: str) -> str:
    """https://core.telegram.org/bots/api#markdownv2-style"""
    escape_chars = r"_*[]()~`>#-|{}.!+="
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)
