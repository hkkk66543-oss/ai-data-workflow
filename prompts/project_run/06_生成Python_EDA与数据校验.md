# 06 生成 Python EDA 与数据校验

请只执行本阶段。Python 只做数据质量检查、辅助 EDA、异常识别和 SQL 结果校验，不生成最终展示图。

任务：

1. 生成或更新 `scripts/data_quality_check.py`。
2. 生成或更新 `scripts/eda_summary.py`。
3. 生成或更新 `scripts/sql_result_check.py`。
4. 生成 `outputs/reports/eda_summary.md`。
5. 生成 `outputs/reports/python_data_check_report.md`。
6. 可以输出 CSV / Excel 汇总表到 `outputs/tables/`。

规则：

- 不再要求 Python 生成展示图。
- 不再要求 Python 生成 matplotlib / seaborn 风格的 BI 图。
- 如果确实需要图，只能生成诊断图，保存到 `outputs/diagnostics/charts/`。
- 诊断图必须标注为“内部检查图，不用于最终展示”。
- 不允许把 Python 图表写进最终 Power BI 页面方案。
- 不允许把 Python 图表作为 README 的主要展示内容。
- 最终可视化交给 Power BI 和 OpenAI Images API 样例图。

阶段结束时必须输出：

```text
下一步是否需要你手动操作：
如果需要，具体操作是什么：
操作完成后，请回复我什么：
```
