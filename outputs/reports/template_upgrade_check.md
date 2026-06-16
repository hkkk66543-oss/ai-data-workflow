# 母版升级自检报告

自检日期：2026-06-14

本次自检只检查通用母版规则、提示词、文档和脚本模板，不跑真实数据。

## 自检结果

| 检查项 | 结果 | 说明 |
|---|---|---|
| 是否已经支持中文 SQL 表名和字段名 | 通过 | `AGENTS.md`、`docs/SQL中文命名规范.md`、`prompts/project_run/03_确认计划_生成SQL.md` 已明确默认中文命名和反引号规则 |
| 是否已经生成 SQL 中文命名规范 | 通过 | 已生成 `docs/SQL中文命名规范.md` |
| 是否已经生成中英文命名映射表模板 | 通过 | 已生成 `docs/SQL中英文命名映射表.md` |
| Python 是否已从最终图表生成工具改为数据质量与辅助 EDA 工具 | 通过 | `AGENTS.md`、`docs/Python定位说明.md`、新版 06 提示词已明确 |
| 是否取消默认生成 outputs/charts 下的 matplotlib 展示图 | 通过 | `scripts/chart_export.py` 已改为输出 `outputs/diagnostics/charts/` |
| 是否新增 outputs/diagnostics/charts/ 作为诊断图目录 | 通过 | 目录已创建，规则已写入 |
| 是否明确 Power BI 才是最终可视化工具 | 通过 | `AGENTS.md`、`README.md`、`docs/PowerBI最终展示规范.md` 已明确 |
| 是否支持 OpenAI Images API 生成 BI 样例图 | 通过 | 已新增 `scripts/generate_bi_mockups_with_openai.py` |
| 是否生成 BI 图片提示词文件 | 通过 | 已新增 `powerbi_notes/image_prompts.md` |
| 是否生成具体 Power BI 操作说明规则 | 通过 | `docs/PowerBI最终展示规范.md`、`powerbi_notes/layout_reference.md`、`prompts/project_run/07_生成PowerBI方案.md` 已明确字段拖放级步骤 |
| 是否已经生成 project_run 项目执行提示词包 | 通过 | 已生成 `prompts/project_run/00` 到 `09` |
| 是否已经新增手动操作提醒规则 | 通过 | 已生成 `docs/手动操作提醒规范.md` 并写入 `AGENTS.md` 和 project_run 提示词 |
| 是否在需要手动操作的步骤中给出具体操作步骤 | 通过 | 01、03、04、05、07、08 提示词均包含固定格式手动操作提醒 |
| 是否更新 README.md | 通过 | README 已更新为新版母版说明 |
| 是否保留通用行业识别流程 | 通过 | `AGENTS.md` 和 01、02 提示词保留 Context / Data Understanding 与 Domain Identification |
| 是否仍然遵守不虚构字段、不虚构数据、不虚构结论 | 通过 | `AGENTS.md`、`README.md`、project_run 提示词均保留该约束 |

## 验证说明

- 已检查文件结构与关键文件存在性。
- 未运行真实数据处理。
- 当前终端的 `python` / `python3` 启动器不可用，未能执行 Python 语法编译检查；脚本已按静态方式检查并保持模板用途。

## 后续建议

真实项目开始时，从 `prompts/project_run/01_项目启动_数据理解与行业识别.md` 开始执行。不要直接跳到 SQL、Python 或 Power BI 阶段。
