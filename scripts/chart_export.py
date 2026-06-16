from __future__ import annotations

import matplotlib.pyplot as plt

from data_profile import RAW_DIR, ROOT, read_table


DIAGNOSTIC_CHART_DIR = ROOT / "outputs" / "diagnostics" / "charts"


def main() -> None:
    DIAGNOSTIC_CHART_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls", ".json"})
    if not files:
        raise SystemExit("data/raw has no supported tabular files.")

    for path in files:
        df = read_table(path)
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            continue
        numeric.hist(figsize=(12, 8), bins=30)
        plt.suptitle(f"内部检查图，不用于最终展示 - {path.name}")
        plt.tight_layout()
        plt.savefig(DIAGNOSTIC_CHART_DIR / f"{path.stem}_numeric_diagnostic.png", dpi=160)
        plt.close("all")


if __name__ == "__main__":
    main()
