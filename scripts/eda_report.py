from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_profile import RAW_DIR, ROOT, read_table


REPORT = ROOT / "outputs" / "reports" / "eda_report.md"


def describe_dataframe(name: str, df: pd.DataFrame) -> list[str]:
    lines = [f"## {name}", ""]
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        lines.append("未识别到数值字段，待结合业务字段进一步分析。")
        lines.append("")
        return lines

    lines.append("### 数值字段描述统计")
    lines.append("")
    desc = numeric.describe().T.reset_index().rename(columns={"index": "field"})
    lines.append(desc.to_markdown(index=False))
    lines.append("")
    return lines


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".json"})
    if not files:
        raise SystemExit("data/raw has no supported tabular files.")

    lines = ["# EDA Report", "", "本报告基于真实数据自动生成基础探索结果。", ""]
    for path in files:
        lines.extend(describe_dataframe(path.name, read_table(path)))

    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
