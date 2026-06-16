from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_profile import RAW_DIR, ROOT, read_table


REPORT = ROOT / "outputs" / "reports" / "python_data_check_report.md"
TABLE_DIR = ROOT / "outputs" / "tables"


def supported_files() -> list[Path]:
    return sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".json"})


def check_dataframe(name: str, df: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
    lines = [f"## {name}", ""]
    lines.append(f"- 行数：{len(df)}")
    lines.append(f"- 列数：{len(df.columns)}")
    lines.append(f"- 完全重复行数：{int(df.duplicated().sum())}")
    lines.append("")
    lines.append("| 字段 | 数据类型 | 缺失数 | 缺失率 | 唯一值数 | 异常提示 |")
    lines.append("|---|---|---:|---:|---:|---|")

    rows: list[dict] = []
    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())
        missing_rate = round(float(series.isna().mean()), 4) if len(df) else 0
        unique_count = int(series.nunique(dropna=True))
        warning = "待业务确认"
        if missing_rate == 1:
            warning = "全为空"
        elif unique_count == 1 and len(df) > 1:
            warning = "单一取值"
        elif pd.api.types.is_numeric_dtype(series):
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr != 0:
                outliers = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
                warning = f"IQR异常值 {outliers} 条"

        lines.append(f"| {col} | {series.dtype} | {missing} | {missing_rate} | {unique_count} | {warning} |")
        rows.append(
            {
                "文件": name,
                "字段": col,
                "数据类型": str(series.dtype),
                "缺失数": missing,
                "缺失率": missing_rate,
                "唯一值数": unique_count,
                "异常提示": warning,
            }
        )

    lines.append("")
    return lines, pd.DataFrame(rows)


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    files = supported_files()
    if not files:
        raise SystemExit("data/raw has no supported tabular files.")

    lines = ["# Python 数据质量检查报告", "", "Python 仅用于内部数据质量检查，不用于最终展示图。", ""]
    summary_frames: list[pd.DataFrame] = []
    for path in files:
        df = read_table(path)
        file_lines, summary = check_dataframe(path.name, df)
        lines.extend(file_lines)
        summary_frames.append(summary)

    if summary_frames:
        pd.concat(summary_frames, ignore_index=True).to_csv(TABLE_DIR / "python_data_quality_summary.csv", index=False)

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
