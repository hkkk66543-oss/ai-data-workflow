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

SQL 现在支持本地自动执行：预览计划后，程序直接连接 MySQL，完成 ODS 建表、数据导入、DWD/ADS 计算、业务校验与 CSV 导出。仅在缺少本地连接条件时需要用户操作；不能把预览当成运行成功。Power BI 自动建模/搭页不在本次升级范围。

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
7. SQL 生成后，按下方说明配置本地 MySQL，预览后使用 `--execute` 自动运行、校验和导出。无需逐段复制到 Navicat。
8. Power BI 阶段按 `powerbi_notes/page_xxx.md` 手动搭建看板，并将截图保存到 `outputs/bi_screenshots/`。

## SQL 自动执行入口

详细配置见 [SQL 自动执行说明](docs/SQL自动执行说明.md)。首次需要 Python 3.10+、MySQL 8.0、真实分层 SQL 及本机连接配置。数据库密码只放本机环境变量；不需要提供给聊天助手。

```powershell
python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.local.yaml
# 填写本地连接、导入字段映射、校验和导出查询，并在本机设置 MYSQL_PASSWORD
python scripts/run_sql_pipeline.py            # 只预览，不连接数据库
python scripts/run_sql_pipeline.py --execute  # 执行已审核的计划
```

执行顺序：ODS → 导入原始文件 → DWD → ADS → 校验 → 导出。目标原始表非空会拒绝重复导入；校验失败不导出。每次运行输出到独立的 `outputs/runs/<run_id>/`，只有完整成功才生成 `tables/`；`run.json` 保存结果与出错文件/语句序号。

母版没有业务数据与真实 ODS/DWD/ADS SQL，必须先按既有数据理解流程生成；空 SQL 或未配置校验会失败，不会虚报成功。MySQL DDL 无法整体回滚，首次建议使用项目专用新库。本版本不自动调用 AI 修复 SQL、不无限重试、不自动续跑。

验证：`python -m unittest discover -s tests -v`。测试采用模拟驱动，真实 MySQL 8.0 联调需要在可访问你的数据库的电脑上完成。

## 主要输出

- 数据字典：`docs/数据字典.md`
- 数据质量报告：`docs/数据质量报告.md`
- 表关系说明：`docs/表关系说明.md`
- 行业识别报告：`docs/行业识别报告.md`
- SQL 中文命名规范：`docs/SQL中文命名规范.md`
- SQL 中英文命名映射表：`docs/SQL中英文命名映射表.md`
- SQL：`sql/01_ods/`、`sql/02_dwd/`、`sql/03_ads/`、`sql/04_checks/`
- SQL 执行入口：`scripts/run_sql_pipeline.py`
- 执行结果：`outputs/runs/<run_id>/run.json`、成功运行的 `tables/*.csv`
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
