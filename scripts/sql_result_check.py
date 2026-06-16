from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
REPORT = ROOT / "outputs" / "reports" / "sql_result_check_report.md"


def read_export(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported exported table: {path.name}")


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in TABLE_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls"})
    if not files:
        raise SystemExit("outputs/tables has no exported SQL result files.")

    lines = [
        "# SQL 结果辅助校验报告",
        "",
        "本报告基于用户从 MySQL / Navicat 导出的 ADS 或 CHECKS 结果文件生成，仅用于辅助校验。",
        "",
    ]

    for path in files:
        df = read_export(path)
        lines.extend(
            [
                f"## {path.name}",
                "",
                f"- 行数：{len(df)}",
                f"- 列数：{len(df.columns)}",
                f"- 完全重复行数：{int(df.duplicated().sum())}",
                "",
            ]
        )
        if not df.empty:
            lines.append("### 字段缺失概览")
            lines.append("")
            lines.append("| 字段 | 缺失数 | 缺失率 |")
            lines.append("|---|---:|---:|")
            for col in df.columns:
                lines.append(f"| {col} | {int(df[col].isna().sum())} | {round(float(df[col].isna().mean()), 4)} |")
            lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
