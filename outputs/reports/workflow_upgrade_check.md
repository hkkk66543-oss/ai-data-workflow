# 工作流使用与交付检查清单

## 项目入口

使用 `prompts/project_run/` 按阶段执行。通用流程保持为 Context / Data Understanding → Domain Identification → Brainstorming → Plan → Work-Plan → Execute → Test / Verify / QA → Review → Learn → Reuse。

- 真实原始数据放入 `data/raw/`，保持原文件不变。
- 先生成数据字典、质量报告、表关系和行业识别报告。
- 基于真实字段提出候选主题，确认主题、业务口径及计划。
- `domain_packs/` 提供行业思路，不能替代真实字段判断。

## 执行交付

| 阶段 | 应交付内容 | 检查依据 |
|---|---|---|
| SQL | 各层源码、sql_pipeline 配置、结果 CSV、建模字段和实际 DDL、运行清单 | 临时 MySQL 8.0 实际执行；本次 passed 且清理 completed |
| Python | 数据质量、EDA 与 SQL 辅助校验报告；必要的内部诊断图 | 实际字段、行数、异常与汇总勾稽 |
| Power BI | 报表 YAML、设计记录、可编辑 PBIP、随附 CSV、模型、DAX、主题与原生组件 | 结构和引用检查、单位对账、Desktop 实际刷新与显示交互验收 |
| 报告与展示 | 分析报告、README、简历描述和面试稿 | 每条结论能追溯 SQL、QA 或实际报表 |
| 复盘 | 可复用方法、口径风险与规则 | 不带入其他项目的私有数据或未经证实结论 |

SQL 导入、执行和导出由执行器完成；Power BI 支持的组件由生成器创建。使用者负责业务确认及必要的 Desktop 验收。OpenAI 图片生成是可选布局参考。详见 [SQL 自动执行说明](../../docs/SQL自动执行说明.md)、[Power BI 自动生成说明](../../docs/PowerBI自动生成说明.md) 和 [主题与布局说明](../../docs/PowerBI设计升级说明.md)。

## 完成判断

没有真实数据时，数据字典、SQL 和报告等仍为模板。缺少执行环境、业务证据或 Desktop 实际检查时，如实标注待完成项，不预先写“通过”。每份工程独立记录验收状态，历史示例测试不代表新数据集通过。
