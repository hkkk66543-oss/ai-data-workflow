# 08 生成报告、README、简历和面试稿

请只执行本阶段。执行前必须确认 SQL、QA、Python 辅助校验和 Power BI 方案已完成。

任务：

1. 生成或更新 `outputs/reports/数据分析报告.md`。
2. 更新项目 `README.md`。
3. 生成或更新 `docs/简历项目描述.md`。
4. 生成或更新 `docs/面试讲解稿.md`。
5. 生成或更新 `docs/分析结论.md`。

规则：

- 报告结论必须来自真实数据、SQL 结果、QA 结果或 Power BI 页面说明。
- 不允许虚构业务背景、字段、指标、数据和结论。
- README 优先引用 Power BI 实际截图或 `outputs/bi_mockups/`。
- 不允许把 Python 诊断图作为最终展示图。
- 如果缺少 Power BI 实际截图，必须标注“待用户手动截图补充”。

如果需要用户提供 Power BI 截图，必须输出：

```text
【需要你手动操作】
操作目标：保存 Power BI 页面截图用于 README 和报告展示。
为什么需要你操作：Power BI Desktop 页面截图需要你在本地手动完成，Codex 不能替你操作软件界面。
具体步骤：
1. 打开 Power BI Desktop。
2. 逐页检查看板是否已按 powerbi_notes/page_xxx.md 搭好。
3. 使用截图工具截取每一页完整画面。
4. 保存到 outputs/bi_screenshots/。
5. 文件名建议为 page_01_页面名称.png、page_02_页面名称.png。
完成后你应该看到：outputs/bi_screenshots/ 中有每页 Power BI 截图。
如果报错怎么办：如果截图模糊或字段显示不全，请调整页面缩放后重新截图。
完成后请回复我什么：请回复“Power BI 截图已保存”。
```

阶段结束时必须输出：

```text
下一步是否需要你手动操作：
如果需要，具体操作是什么：
操作完成后，请回复我什么：
```
