# 母版使用检查清单

用于复用前核对工作流说明与产物要求，不代表某个真实数据集已执行或通过验收。

| 检查范围 | 当前要求 | 入口 |
|---|---|---|
| 数据理解与行业识别 | 先检查真实字段和关系，再确认行业、主题、口径与计划 | AGENTS.md、prompts/project_run/01 与 02 |
| SQL 命名 | 简约中文、反引号、注释与中英文映射 | docs/SQL中文命名规范.md |
| SQL 执行 | 临时 MySQL 8.0，自动导入、运行、校验、导出及清理 | scripts/run_sql_pipeline.py、docs/SQL自动执行说明.md |
| SQL 交付 | 本次 passed、临时清理 completed；保留 CSV、字段、DDL、源码和清单 | outputs/runs/<run_id>/ |
| Python | 数据质量、辅助 EDA、执行与校验；诊断图仅供内部检查 | docs/Python定位说明.md |
| Power BI 工程 | 根据真实结果及报表 YAML 自动生成模型、DAX、主题与六种数据组件 | scripts/generate_powerbi.py、docs/PowerBI自动生成说明.md |
| 设计 | 依数据选择页面、布局、颜色和单位，配置写入工程 | .agents/skills/powerbi-report-design/SKILL.md |
| 最终验收 | Desktop 打开、刷新、对账、显示和筛选联动；记录截图 | docs/PowerBI最终展示规范.md |
| BI 样例图 | 可选布局参考，不替代实际工程或精确数据 | docs/PowerBI样例图生成规范.md |
| 操作交接 | 仅交接环境准备、Desktop 验收及确需的能力外扩展 | docs/手动操作提醒规范.md |

从 `prompts/project_run/01_项目启动_数据理解与行业识别.md` 开始。真实项目的每项状态应根据当次证据填写；不把清单存在、模拟测试或历史记录当作本次执行成功。
