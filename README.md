# 通用 AI 数据分析工作流母版

本项目是一套通用 AI 数据分析工作流母版，不绑定单一行业。它用于把不同业务场景的数据集转化为可展示、可复用、适合 GitHub、简历和面试讲解的数据分析项目。

## 核心定位

- 支持电商、互联网产品、用户增长、金融风控、内容平台、教育、招聘、零售经营、运营分析等不同方向。
- 每个真实项目都必须先做数据理解和行业识别，再确认主题、指标和执行计划。
- 不虚构业务背景、字段、数据和结论。
- 行业未确认前，不套用任何固定行业指标。

## 新版工作流边界

SQL 默认使用简约中文表名和中文字段名，提升 Navicat、Power BI 和报告阅读体验。MySQL 中文标识符必须使用反引号，例如 `应用_每日概览`、`用户编号`、`事件数`。

Python 不再承担最终展示图职责。Python 只负责数据质量检查、辅助 EDA、异常识别、SQL 结果辅助校验和导出检查。诊断图如确需生成，只能保存到 `outputs/diagnostics/charts/`，且不作为 README 或报告核心展示图。

Power BI 是最终可视化工具。Power BI 部分会基于真实 ADS 表和真实字段生成详细页面方案、DAX、页面操作说明和讲解话术。BI 样例图由 OpenAI Images API 或图片提示词生成，输出到 `outputs/bi_mockups/`。

SQL 默认使用临时 MySQL 自动执行：预览后启动临时数据库，完成 ODS 建表、数据导入、DWD/ADS 计算、校验、结果和模型导出，然后清理环境。本地/远程已有 MySQL 作为可选方式；不能把预览当成运行成功。Power BI 现可按明确报表计划生成 PBIP 草稿，详见 [Power BI 自动生成说明](docs/PowerBI自动生成说明.md)。

## 项目执行提示词包

真正做项目时，不要从聊天记录里找提示词，而是按 `prompts/project_run/` 文件夹顺序执行：

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

项目主题、指标口径和执行计划需要确认。SQL 实际执行需要用户授权目标数据库和审核过的 SQL；在授权范围内可连续执行、校验及导出，失败即停止，不自动修复重跑。其他阶段仍按阶段确认。

## 标准使用方式

1. 复制母版文件夹。
2. 改成新项目名。
3. 把原始数据放进 `data/raw/`，不要修改原始文件。
4. 从 `prompts/project_run/01_项目启动_数据理解与行业识别.md` 开始执行。
5. 检查 `docs/数据字典.md`、`docs/数据质量报告.md`、`docs/表关系说明.md`、`docs/行业识别报告.md`。
6. 确认项目主题后，继续执行后续提示词。
7. SQL 生成后，确认临时 MySQL 的执行环境，预览后使用 `--execute` 自动运行、校验、导出和清理。无需复制到 Navicat。
8. Power BI 阶段按已审核字段和指标配置报表计划，使用 `scripts/generate_powerbi.py` 自动生成模型与基础页面，在 Desktop 刷新检查后，将实际截图保存到 `outputs/bi_screenshots/`。

## SQL 自动执行：默认临时 MySQL 8.0

默认在执行环境中创建临时 MySQL 8.0，自动分配连接、导入数据、执行已确认 SQL、校验并导出，然后删除临时数据库。用户无需安装或连接自己的 MySQL、无需提供数据库密码。执行环境仍需能运行 Docker，或在 Linux/Unix 中提供现成的 MySQL 8.0 mysqld 二进制；缺少运行条件时明确失败，不切换 DuckDB 或模拟执行。

```powershell
python -m pip install -r requirements.txt
# 基于真实数据生成分层 SQL，并填写配置中的 imports/checks/exports
python scripts/run_sql_pipeline.py            # 预览，不启动数据库
python scripts/run_sql_pipeline.py --execute  # 实际启动临时 MySQL 并执行
```

可先用随附的三行合成数据验证链路（不代表真实业务成果）：

```powershell
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

每次运行在 `outputs/runs/<run_id>/` 保留：

- `tables/*.csv`：配置选择的真实查询结果；全部校验与导出成功后才交付。
- `model/fields.csv`、`model/model.json`：实际字段类型、注释、主键标识、显式外键和原始字段映射；加工逻辑见 SQL，不凭空推断字段血缘。
- `model/schema.sql`：实际 MySQL 建表/视图定义。
- `source/sql/`：此次使用的 SQL 原文件，保留源代码。
- `manifest.json`：产物清单、大小及 SHA-256。
- `run.json`：实际 MySQL 版本、校验结果、执行记录及临时环境清理状态。

失败保留已保存的 SQL 与运行记录，停止交付成功结果，并尝试清理临时环境。临时数据库不是长期存储；原始数据不删除。现有本地/远程 MySQL 仍可通过 `database.mode: existing` 使用，程序不会删除该库。

详细环境条件、现有数据库配置、失败处理与限制见 [SQL 自动执行说明](docs/SQL自动执行说明.md)。母版无真实业务 SQL/数据，需先完成数据理解和指标确认；空母版不会虚报成功。SQL 生成和 AI 自动修复不属于执行器本身。

验证：`python -m unittest discover -s tests -v`。设置 `MYSQLD_PATH` 后还会运行真实 MySQL 8.0 原生临时环境的端到端测试；Docker 生命周期有模拟测试，容器分支尚未在当前无 Docker 环境中实测。

## 主要输出

- 数据字典：`docs/数据字典.md`
- 数据质量报告：`docs/数据质量报告.md`
- 表关系说明：`docs/表关系说明.md`
- 行业识别报告：`docs/行业识别报告.md`
- SQL 中文命名规范：`docs/SQL中文命名规范.md`
- SQL 中英文命名映射表：`docs/SQL中英文命名映射表.md`
- SQL：`sql/01_ods/`、`sql/02_dwd/`、`sql/03_ads/`、`sql/04_checks/`
- SQL 执行入口：`scripts/run_sql_pipeline.py`
- 执行结果：`outputs/runs/<run_id>/` 下的 `run.json`、`tables/*.csv`、`model/`、`source/` 和 `manifest.json`
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

### Power BI 设计层

已增加三套主题、原生标题与分区、概览/对比/明细布局、实际类别分布适配，以及无启动脚本交付。使用 `examples/sql_pipeline_demo/powerbi_design_plan.yaml`，详见 [设计升级说明](docs/PowerBI设计升级说明.md)。它根据已审核计划适配页面，不会凭空推断行业指标；新主题和布局仍需 Desktop 显示验证。
