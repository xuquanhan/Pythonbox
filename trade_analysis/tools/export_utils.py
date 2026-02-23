import pandas as pd
from pathlib import Path
from typing import Optional, List
import json


class ExportUtils:
    def __init__(self, output_dir: str = './output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return str(filepath)

    def export_to_json(self, data: dict, filename: str) -> str:
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return str(filepath)

    def export_summary(self, summary: dict, filename: str = 'summary.txt') -> str:
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")
        return str(filepath)
