from __future__ import annotations

import json
from pathlib import Path

import chardet
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DOCS_DIR = ROOT / "docs"


def detect_encoding(path: Path) -> str:
    with path.open("rb") as fh:
        sample = fh.read(100_000)
    result = chardet.detect(sample)
    return result.get("encoding") or "utf-8"


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        encoding = detect_encoding(path)
        return pd.read_csv(path, encoding=encoding)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported tabular file: {path.name}")


def profile_file(path: Path) -> dict:
    encoding = detect_encoding(path) if path.suffix.lower() in {".csv", ".json", ".sql"} else "binary/xlsx"
    base = {
        "file": path.name,
        "path": str(path.relative_to(ROOT)),
        "size_bytes": path.stat().st_size,
        "encoding": encoding,
        "suffix": path.suffix.lower(),
    }
    if path.suffix.lower() == ".sql":
        base.update({"rows": None, "columns": None, "column_profile": [], "sample": []})
        return base

    df = read_table(path)
    base["rows"] = len(df)
    base["columns"] = len(df.columns)
    base["sample"] = df.head(10).astype("string").fillna("").to_dict(orient="records")
    base["column_profile"] = [
        {
            "column": str(col),
            "dtype": str(df[col].dtype),
            "non_null_rate": round(float(df[col].notna().mean()), 4) if len(df) else None,
            "unique_count": int(df[col].nunique(dropna=True)),
            "sample_values": [str(v) for v in df[col].dropna().head(5).tolist()],
        }
        for col in df.columns
    ]
    return base


def write_markdown(profiles: list[dict]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    dictionary_lines = ["# 数据字典", ""]
    quality_lines = ["# 数据质量报告", ""]
    relation_lines = ["# 表关系说明", ""]

    for profile in profiles:
        dictionary_lines.extend([f"## {profile['file']}", ""])
        quality_lines.extend([f"## {profile['file']}", ""])

        quality_lines.extend(
            [
                f"- 路径：`{profile['path']}`",
                f"- 文件大小：{profile['size_bytes']} bytes",
                f"- 编码：{profile['encoding']}",
                f"- 行数：{profile['rows']}",
                f"- 列数：{profile['columns']}",
                "",
            ]
        )

        if not profile["column_profile"]:
            dictionary_lines.append("SQL 文件或暂不支持结构化画像，待确认。")
            dictionary_lines.append("")
            continue

        dictionary_lines.append("| 字段名 | 推测含义 | 数据类型 | 非空率 | 唯一值数 | 样例值 | 备注 |")
        dictionary_lines.append("|---|---|---|---:|---:|---|---|")
        for col in profile["column_profile"]:
            samples = ", ".join(col["sample_values"])
            dictionary_lines.append(
                f"| {col['column']} | 待确认 | {col['dtype']} | {col['non_null_rate']} | "
                f"{col['unique_count']} | {samples} | 基于字段名和样例值推测 |"
            )
        dictionary_lines.append("")

    relation_lines.extend(
        [
            "当前仅完成基础字段画像。",
            "",
            "后续请结合字段名、唯一性、覆盖率和样例值推断主键、外键与表关系，并标注待确认项。",
        ]
    )

    (DOCS_DIR / "数据字典.md").write_text("\n".join(dictionary_lines), encoding="utf-8")
    (DOCS_DIR / "数据质量报告.md").write_text("\n".join(quality_lines), encoding="utf-8")
    (DOCS_DIR / "表关系说明.md").write_text("\n".join(relation_lines), encoding="utf-8")


def main() -> None:
    files = sorted(
        p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".json", ".sql"}
    )
    if not files:
        raise SystemExit("data/raw is empty. Please add csv, xlsx, json, or sql files first.")

    profiles = [profile_file(path) for path in files]
    write_markdown(profiles)
    (ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs" / "tables" / "data_profile.json").write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
