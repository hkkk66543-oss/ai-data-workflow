from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_profile import RAW_DIR, ROOT, read_table


REPORT = ROOT / "outputs" / "reports" / "eda_summary.md"
TABLE_DIR = ROOT / "outputs" / "tables"


def supported_files() -> list[Path]:
    return sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".json"})


def summarize_dataframe(name: str, df: pd.DataFrame) -> list[str]:
    lines = [f"## {name}", ""]
    lines.append(f"- 行数：{len(df)}")
    lines.append(f"- 列数：{len(df.columns)}")
    lines.append("")

    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        lines.append("### 数值字段描述统计")
        lines.append("")
        desc = numeric.describe().T.reset_index().rename(columns={"index": "字段"})
        lines.append(desc.to_markdown(index=False))
        lines.append("")

    categorical = df.select_dtypes(exclude="number")
    if not categorical.empty:
        lines.append("### 非数值字段概览")
        lines.append("")
        lines.append("| 字段 | 唯一值数 | 样例值 |")
        lines.append("|---|---:|---|")
        for col in categorical.columns:
            samples = ", ".join(str(v) for v in df[col].dropna().head(5).tolist())
            lines.append(f"| {col} | {int(df[col].nunique(dropna=True))} | {samples} |")
        lines.append("")

    lines.append("本节为辅助 EDA，不构成最终业务结论。")
    lines.append("")
    return lines


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    files = supported_files()
    if not files:
        raise SystemExit("data/raw has no supported tabular files.")

    lines = ["# EDA 摘要", "", "Python 仅用于辅助探索和数据校验，最终展示以 Power BI 为准。", ""]
    for path in files:
        df = read_table(path)
        lines.extend(summarize_dataframe(path.name, df))

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
