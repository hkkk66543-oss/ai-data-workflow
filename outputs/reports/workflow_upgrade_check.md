# 通用 AI 数据分析工作流升级自检报告

生成时间：2026-06-13

## 1. 已完成项

### AGENTS.md 通用化

- 已从单一行业项目规则升级为通用数据分析工作流规则。
- 已明确“本项目不预设行业”。
- 已要求每次分析先执行 Context / Data Understanding。
- 已新增 Domain Identification 行业识别阶段。
- 已明确根据字段名、表名、样例数据、业务含义判断行业或业务场景。
- 已明确行业不清晰时输出 2-3 个候选方向并标注依据。
- 已明确行业未确认前不允许直接套用电商指标。
- 已保留不修改 `data/raw`、不虚构字段、不虚构数据、不虚构结论等规则。

### 标准流程

已更新为：

```text
Context / Data Understanding
-> Domain Identification
-> Brainstorming
-> Plan
-> Work-Plan
-> Execute
-> Test / Verify / QA
-> Review
-> Learn
-> Reuse
```

### domain_packs 行业适配层

已创建 `domain_packs/` 文件夹。

已包含以下行业模板：

- `domain_packs/通用数据分析.md`
- `domain_packs/电商分析.md`
- `domain_packs/互联网产品分析.md`
- `domain_packs/金融风控分析.md`
- `domain_packs/用户增长分析.md`
- `domain_packs/内容平台分析.md`
- `domain_packs/教育数据分析.md`
- `domain_packs/招聘数据分析.md`
- `domain_packs/零售经营分析.md`
- `domain_packs/运营分析.md`
- `domain_packs/AB实验分析.md`

每个 domain_pack 均已包含以下小节：

- 适用数据特征
- 常见表结构
- 常见字段
- 常见业务问题
- 常见核心指标
- 常见分析模块
- 常见图表
- SQL 建模重点
- Power BI 看板设计重点
- 简历项目包装方向
- 面试讲解角度

### Domain Identification 提示词

`prompts/02_domain_identification.md` 已明确说明：

- 如何根据文件名、表名、字段名、样例数据、表关系和业务含义判断行业。
- 如何根据字段判断业务场景。
- 如何避免强行套用电商模板和电商指标。
- 行业不明确时如何输出 2-3 个候选方向。
- 如何让用户确认最终项目主题。
- 如何根据确认后的行业调用对应 `domain_packs/`。

### README.md

- 已明确说明本项目不是单一电商项目，而是一套通用 AI 数据分析工作流。
- 已列出支持的项目类型，包括电商、互联网产品、用户增长、金融风控、A/B Test、内容平台、教育、招聘、零售经营、运营等。
- 已说明使用方式：复制模板、放入 `data/raw`、执行数据理解、识别行业、确认项目主题、生成 SQL / Python / Power BI / 报告。
- 已列出项目输出内容。

### 通用流程文档

- `docs/经验总结.md` 已更新为十阶段通用流程。
- `docs/行业识别报告.md` 已创建。
- `docs/项目选题建议.md` 已创建。
- `docs/业务分析框架.md` 已改为通用分析模块模板。
- `docs/指标口径.md` 已改为通用指标口径模板，避免默认套用 GMV、DAU、逾期率等行业专属指标。

## 2. 未完成项

当前升级自检未发现必须补齐的缺失项。

需要注意：真实数据尚未放入 `data/raw/`，所以以下内容仍处于模板状态：

- `docs/数据字典.md`
- `docs/数据质量报告.md`
- `docs/表关系说明.md`
- `docs/行业识别报告.md`
- `docs/项目选题建议.md`
- 行业专属 SQL、Python 分析结果、图表和最终报告

这些不是升级缺口，而是等待新数据集后生成的项目产物。

## 3. 需要补充的文件

暂无必须补充的结构性文件。

后续放入新数据后，需要由工作流自动生成或更新：

- `docs/行业识别报告.md`
- `docs/项目选题建议.md`
- `docs/业务分析框架.md`
- `docs/指标口径.md`
- `sql/01_ods/`
- `sql/02_dwd/`
- `sql/03_ads/`
- `sql/04_checks/check_all.sql`
- `outputs/reports/数据分析报告.md`
- `outputs/reports/qa_report.md`
- `outputs/reports/review_report.md`
- `docs/简历项目描述.md`
- `docs/面试讲解稿.md`

## 4. 需要修改的规则

当前无需修改核心规则。

建议在真实项目执行后，根据行业识别经验补充：

- 新增行业 domain_pack，如果遇到当前 11 类以外的数据集。
- 更新 `AGENTS.md` 中的行业识别风险规则。
- 更新 `prompts/02_domain_identification.md` 中的字段识别样例。

## 5. 当前工作流是否可以正式用于新数据集

结论：可以正式用于新数据集。

理由：

- 总控规则已通用化。
- 标准流程已加入 Domain Identification。
- 行业适配层已创建并覆盖 11 类常见分析场景。
- 行业识别提示词已明确防止强行套用电商指标。
- README 已说明这是通用工作流。
- 核心输出目录和模板文件完整。

## 6. 如果不能正式使用，请自动补齐缺失内容

本次自检结论为“可以正式使用”，未发现阻塞性缺失内容，因此无需自动补齐。

下一步使用方式：

```text
请按照 prompts/00_master_prompt.md 执行本项目的通用 AI 数据分析工作流。先从 Context / Data Understanding 开始，扫描 data/raw，不要修改原始数据；然后执行 Domain Identification，输出行业识别报告，并等我确认项目主题后再继续。
```

行业识别完成后，用户应按以下格式确认项目主题：

```text
我确认选择「项目主题名称」，请基于该主题继续执行 Plan -> Work-Plan -> Execute -> Test / Verify / QA -> Review -> Learn -> Reuse。
```
