# 10 Reuse

目标：让这套工作流可以复用到下一个行业项目。

复用步骤：

1. 清空或替换 `data/raw/` 中的新项目原始数据，但不要修改原始文件内容。
2. 从 `prompts/00_master_prompt.md` 开始执行。
3. 先做数据理解，再做行业识别。
4. 根据 `docs/行业识别报告.md` 确认项目主题。
5. 选择对应 `domain_packs/` 模板作为参考。
6. 基于真实字段生成业务分析框架、指标口径、SQL、Python 数据校验、Power BI 和报告。

下次直接使用：

```text
请按照 prompts/00_master_prompt.md 执行本项目的通用 AI 数据分析工作流。先从 Context / Data Understanding 开始，扫描 data/raw，不要修改原始数据；然后执行 Domain Identification，输出行业识别报告，并等我确认项目主题后再继续。
```
