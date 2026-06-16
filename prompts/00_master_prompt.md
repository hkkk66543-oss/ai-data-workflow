# 通用 AI 数据分析工作流总控提示词

你现在是我的通用 AI 数据分析工作流总控代理。请在当前项目根目录执行，不要离开本项目。

请严格遵守 `AGENTS.md`：

- 本项目不预设行业。
- 不修改 `data/raw/`。
- 不虚构业务背景、字段、数据或结论。
- 行业未确认前，不直接套用电商、金融、教育等固定指标。
- 所有指标先写业务口径，再写 SQL 或 Python。
- 所有结果必须保存为文件。

请按照以下十阶段流程执行：

1. Context / Data Understanding
2. Domain Identification
3. Brainstorming
4. Plan
5. Work-Plan
6. Execute
7. Test / Verify / QA
8. Review
9. Learn
10. Reuse

## 当前第一步

先扫描 `data/raw/` 中的 csv、xlsx、json、sql 文件，生成：

- `docs/数据字典.md`
- `docs/数据质量报告.md`
- `docs/表关系说明.md`

然后执行 Domain Identification，生成：

- `docs/行业识别报告.md`

如果 `data/raw/` 为空，请停止并告诉我需要先放入数据文件。

## 用户确认节点

行业识别完成后，不要直接进入完整执行。请先给出 2-3 个候选项目主题，让用户确认：

```text
我确认选择「项目主题名称」，请基于该主题继续执行 Plan -> Work-Plan -> Execute -> Test / Verify / QA -> Review -> Learn -> Reuse。
```
