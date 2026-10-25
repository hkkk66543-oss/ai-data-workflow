# 通用 AI 数据分析工作流母版

本项目是一套通用 AI 数据分析工作流母版，不绑定单一行业。它用于把不同业务场景的数据集转化为可展示、可复用、适合 GitHub、简历和面试讲解的数据分析项目。

## 核心定位

- 支持电商、互联网产品、用户增长、金融风控、内容平台、教育、招聘、零售经营、运营分析等不同方向。
- 每个真实项目都必须先做数据理解和行业识别，再确认主题、指标和执行计划。
- 不虚构业务背景、字段、数据和结论。
- 行业未确认前，不套用任何固定行业指标。

## 工作流说明

SQL 默认使用简约中文表名和中文字段名，提升 Navicat、Power BI 和报告阅读体验。MySQL 中文标识符必须使用反引号，例如 `应用_每日概览`、`用户编号`、`事件数`。

Python 负责数据质量检查、辅助 EDA、异常识别、SQL 执行、结果辅助校验和导出检查。诊断图如确需生成，只能保存到 `outputs/diagnostics/charts/`，且不作为 README 或报告核心展示图。

Power BI 是最终可视化工具。Power BI 部分会基于真实 ADS 表和真实字段生成详细页面方案、DAX、页面操作说明和讲解话术。BI 样例图由 OpenAI Images API 或图片提示词生成，输出到 `outputs/bi_mockups/`。

当流程需要用户在外部软件中手动操作时，Codex 必须主动停止并用固定格式说明操作目标、原因、步骤、预期结果、报错处理和完成后应回复的内容。

## 项目执行提示词包

项目按 `prompts/project_run/` 文件夹中的提示词顺序执行：

1. `00_使用说明.md`
2. `01_项目启动_数据理解与行业识别.md`
3. `02_确认主题_生成业务框架与执行计划.md`
4. `03_确认计划_生成SQL.md`
5. `04_SQL报错修复.md`
6. `05_SQL结果_QA校验.md`
7. `06_生成Python_EDA与数据校验.md`
8. `07_生成PowerBI方案.md`
9. `08_生成报告_README_简历_面试稿.md`
10. `09_项目复盘_更新母版经验.md`

每个阶段一次只执行一个步骤。阶段完成后必须停止，等待用户确认。

## 标准使用方式

1. 复制母版文件夹。
2. 改成新项目名。
3. 把原始数据放进 `data/raw/`，不要修改原始文件。
4. 从 `prompts/project_run/01_项目启动_数据理解与行业识别.md` 开始执行。
5. 检查 `docs/数据字典.md`、`docs/数据质量报告.md`、`docs/表关系说明.md`、`docs/行业识别报告.md`。
6. 确认项目主题后，继续执行后续提示词。
7. SQL 生成并确认后，由执行器在临时 MySQL 8.0 中自动完成 ODS、导入、DWD、ADS、CHECKS、结果和字段导出，再清理实例，无需复制 SQL 到 Navicat。SQL 源码与运行结果均保留。
8. Power BI 阶段先生成 `powerbi_notes/page_xxx.md` 页面方案，再根据已确认的字段、指标和布局自动生成可编辑 Power BI 工程，包含模型、基础 DAX、主题与原生图表，无需逐项复制代码或手动搭建支持的组件。最后在 Desktop 打开、刷新和验收，并将截图保存到 `outputs/bi_screenshots/`。

自动化的环境条件与配置细节见 [SQL 自动执行说明](docs/SQL自动执行说明.md)、[Power BI 自动生成说明](docs/PowerBI自动生成说明.md) 和 [Power BI 主题与布局说明](docs/PowerBI设计升级说明.md)。执行器需可用的 MySQL 8.0 环境；生成的看板需在 Desktop 中刷新验收。

Power BI 阶段使用项目内置的 [报表设计 Skill](.agents/skills/powerbi-report-design/SKILL.md)：根据真实业务与数据选择页面和图表，统一颜色层次、文字与数值表达。默认不放装饰性侧栏，支持浅色分区、语义强调色以及 `6,360.20 万` 形式的数值单位；不同项目不套同一张固定看板。设计规则同时由第 07 阶段提示词和总控规则引用。

## 主要输出

- 数据字典：`docs/数据字典.md`
- 数据质量报告：`docs/数据质量报告.md`
- 表关系说明：`docs/表关系说明.md`
- 行业识别报告：`docs/行业识别报告.md`
- SQL 中文命名规范：`docs/SQL中文命名规范.md`
- SQL 中英文命名映射表：`docs/SQL中英文命名映射表.md`
- SQL：`sql/01_ods/`、`sql/02_dwd/`、`sql/03_ads/`、`sql/04_checks/`
- Python 辅助检查：`scripts/data_quality_check.py`、`scripts/eda_summary.py`、`scripts/sql_result_check.py`
- Power BI 方案：`powerbi_notes/`
- BI 样例图：`outputs/bi_mockups/`
- BI 实际截图：`outputs/bi_screenshots/`
- 分析报告：`outputs/reports/数据分析报告.md`
- 简历描述：`docs/简历项目描述.md`
- 面试讲解稿：`docs/面试讲解稿.md`

## OpenAI Images API

如需自动生成 BI 样例图，需要配置环境变量：

```powershell
$env:OPENAI_API_KEY="你的key"
```

不要把 API Key 写进代码。如果无法调用 OpenAI Images API，使用 `powerbi_notes/image_prompts.md` 中的提示词，手动复制到 ChatGPT 图片生成或其他支持 OpenAI Images API 的环境中生成。
