import pandas as pd
from pathlib import Path
from typing import Optional


class DataLoader:
    @staticmethod
    def load_csv(filepath: str, **kwargs) -> pd.DataFrame:
        return pd.read_csv(filepath, **kwargs)

    @staticmethod
    def load_excel(filepath: str, **kwargs) -> pd.DataFrame:
        return pd.read_excel(filepath, **kwargs)

    @staticmethod
    def save_csv(df: pd.DataFrame, filepath: str, **kwargs):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False, encoding='utf-8-sig', **kwargs)

    @staticmethod
    def save_excel(df: pd.DataFrame, filepath: str, sheet_name: str = 'Sheet1', **kwargs):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(filepath, index=False, sheet_name=sheet_name, **kwargs)
