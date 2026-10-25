# 06 Execute

目标：根据确认后的项目主题和执行计划，自动执行 SQL，生成 Python 辅助检查、Power BI 方案与可编辑工程、报告。

输出要求：

- ODS 层 SQL：`sql/01_ods/`
- DWD 层 SQL：`sql/02_dwd/`
- ADS 层 SQL：`sql/03_ads/`
- 数据校验 SQL：`sql/04_checks/`
- 数据质量检查脚本：`scripts/data_quality_check.py`
- EDA 摘要脚本：`scripts/eda_summary.py`
- 诊断图脚本：`scripts/chart_export.py`，只输出到 `outputs/diagnostics/charts/`，不用于最终展示
- Power BI 页面设计：`powerbi_notes/dashboard_plan.md`
- Power BI 报表 YAML 与设计简报、设计记录、验收记录：`powerbi_notes/`
- Power BI 可编辑工程：`outputs/powerbi/<工程名>/`
- DAX 指标文档：`powerbi_notes/dax_measures.md`
- BI 样例图提示词：`powerbi_notes/image_prompts.md`
- 分析报告：`outputs/reports/数据分析报告.md`
- GitHub README：`README.md`
- 简历描述：`docs/简历项目描述.md`
- 面试讲解稿：`docs/面试讲解稿.md`

禁止基于不存在的字段生成 SQL 或结论。

SQL 执行使用 `scripts/run_sql_pipeline.py`：先预览，经项目与脚本确认后在默认临时 MySQL 8.0 中实际执行。自动保存校验结果、CSV、建模字段、DDL 和 SQL 源码，并清理临时实例；已有库仅为可选模式，流程约定见 `docs/SQL自动执行说明.md`。

Power BI 阶段读取报表设计 Skill 和本次通过校验的 SQL 产物，编制报表 YAML 并运行 `scripts/generate_powerbi.py`。支持的模型、DAX、主题和六种数据组件直接写入工程；不只交付文字方案。按实际数据选择布局和单位，最后在 Desktop 刷新、对账、检查显示与联动。详见 `docs/PowerBI自动生成说明.md` 和 `docs/PowerBI设计升级说明.md`。
