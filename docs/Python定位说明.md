# Python 定位说明

## 定位

Python 是数据质量检查、辅助 EDA、异常识别和 SQL 结果校验工具，不是最终可视化工具。

## Python 可以做什么

- 数据文件快速读取。
- 编码识别。
- 字段类型识别。
- 缺失值统计。
- 重复值检查。
- 异常值识别。
- 描述性统计。
- 数据质量报告生成。
- SQL 结果辅助校验。
- ADS 表导出检查。
- 复杂字段处理建议。
- 输出 CSV / Excel 汇总表到 `outputs/tables/`。

## Python 不做什么

- 不生成 README 或报告的核心展示图。
- 不生成 Power BI 替代图。
- 不默认输出 matplotlib / seaborn 展示图到 `outputs/charts/`。
- 不把诊断图写入最终 Power BI 页面方案。

## 诊断图规则

如果确实需要图，只能生成诊断图：

- 输出目录：`outputs/diagnostics/charts/`
- 图名和报告中必须标注“内部检查图，不用于最终展示”。
- 只用于发现异常、分布偏态、缺失模式或离群点。

## 默认脚本

- `scripts/data_quality_check.py`
- `scripts/eda_summary.py`
- `scripts/sql_result_check.py`

默认报告：

- `outputs/reports/python_data_check_report.md`
- `outputs/reports/eda_summary.md`
