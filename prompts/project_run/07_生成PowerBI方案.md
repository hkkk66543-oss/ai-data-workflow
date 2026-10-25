# 07 生成 Power BI 方案

请只执行本阶段。优先从本次 status: passed 的运行读取 tables/、model/fields.csv、model/model.json、source/sql/ 和 run.json；临时模式还需确认清理完成。不得根据已删除的临时数据库编造新结果。执行前必须读取真实 ADS 表说明、`docs/指标口径.md`、`docs/SQL中英文命名映射表.md` 和 QA 结果。

先读取 `.agents/skills/powerbi-report-design/SKILL.md`，按需要读取其中的颜色与单位参考；遵循 `docs/PowerBI设计升级说明.md`。设计标准对所有项目生效，具体页面随本次业务和数据变化，不能照搬历史测试集。

任务：

1. 自动判断当前项目应该做几页 Power BI 看板。
2. 每一页对应一个明确业务问题。
3. 生成：
   - `powerbi_notes/dashboard_plan.md`
   - `powerbi_notes/dax_measures.md`
   - `powerbi_notes/layout_reference.md`
   - `powerbi_notes/BI样例图生成说明.md`
   - `powerbi_notes/image_prompts.md`
   - `powerbi_notes/design_brief.md`：受众、核心问题、真实分布、风格及每页设计依据。
   - `powerbi_notes/design_tokens.yaml`：颜色角色、字体层级、间距和组件语义。
   - `powerbi_notes/design_review.md`：结构、单位、颜色、可读性及实际截图检查状态。
   - `powerbi_notes/page_xx_主题.md`：按实际需要生成页面，不预设三页或固定组件数量。
4. 如果可以调用 OpenAI Images API，生成或更新 `scripts/generate_bi_mockups_with_openai.py`。

每页必须包含：

- 页面名称。
- 页面业务目标。
- 页面布局草图说明。
- 指标卡内容。
- 图表类型。
- 使用的数据表。
- 使用的字段。
- 筛选器。
- 排序规则。
- 数据标签规则。
- 交互筛选规则。
- Power BI 具体操作步骤。
- 页面讲解话术。
- OpenAI Images API 图片生成提示词。

规则：

- 不允许用 Python、matplotlib、seaborn 生成 BI 样例图。
- 不允许生成与真实数据字段无关的图。
- 不允许套用电商模板。
- BI 样例图用于页面布局参考，不作为精确数据来源。
- 精确指标数值必须写在 `powerbi_notes/page_xxx.md` 中。

如果需要用户配置 OpenAI Images API，必须输出：

```text
【需要你手动操作】
操作目标：配置 OPENAI_API_KEY 并生成 BI 样例图。
为什么需要你操作：OpenAI Images API 需要你的本地环境变量，不能把 API Key 写进代码。
具体步骤：
1. 打开 Windows PowerShell。
2. 执行 $env:OPENAI_API_KEY="你的key"。
3. 在项目根目录运行 python scripts/generate_bi_mockups_with_openai.py。
4. 检查 outputs/bi_mockups/ 是否生成 page_01_xxx.png 等图片。
完成后你应该看到：outputs/bi_mockups/ 中出现每页一张 PNG 样例图。
如果报错怎么办：复制完整报错给 Codex；如果无法配置 API，改用 powerbi_notes/image_prompts.md 手动生成。
完成后请回复我什么：请回复“BI 样例图已生成”或粘贴完整报错。
```

如果需要用户在 Power BI 中手动搭页面，必须在每个 `page_xxx.md` 中写出字段拖放级别的步骤。

阶段结束时必须输出：

```text
下一步是否需要你手动操作：
如果需要，具体操作是什么：
操作完成后，请回复我什么：
```

## 自动生成基础工程

页面说明和业务口径审核后，优先依据本次成功 SQL 运行的 CSV、model/model.json、manifest.json 配置报表 YAML，执行 `scripts/generate_powerbi.py`。详细边界见 `docs/PowerBI自动生成说明.md`。首版支持五种基础组件，不能自行虚构关系或指标。保留模型字段、DAX、报表计划、CSV 和源码，标记为草稿。原空白工程是已提供的 `templates/powerbi_blank`，无需重复要求用户创建模板。

生成后先运行结构和引用检查，再交接 Desktop 打开、刷新、数值对账、联动检查和截图；这些实际检查完成前不得宣布报表验收成功。需要新增不支持的组件时说明手动扩展步骤。

## 按数据设计页面与样式

遵循 `docs/PowerBI设计升级说明.md`。理解真实模型、口径和数据分布后，为每页选择一个业务问题，配置 design.palette、标题、说明和 layout；生成器将计算栅格位置并检查重叠。不要所有数据集重复同一张页面。概览、分类对比、明细核查按需要拆页，auto 仅辅助布局，不替代业务判断。缺少字段不得生成目标、同比、漏斗等指标。优先交付 launcher: false 的工程，必要时用 --data-root 预设目标路径；Desktop 显示验证完成前始终保持新工程草稿状态。

具体执行：

1. 检查时间跨度、类别数量、名称长度、金额数量级、正负值、数据粒度和集中度，再确定页数、主分析区与辅助图。没有必要的指标卡、明细表或分区就省略。
2. 默认使用充分利用画布的布局，不放装饰性深色侧栏或占位导航。以底部页面标签切换；确需其他导航时检查实现与面积代价。
3. 为画布、内容表面、浅色分析分区、主色和状态色分别配置角色；不要近白画布叠全白组件。卡片可以浅蓝、浅琥珀、浅青等低饱和底色分组，主题与颜色含义根据本次业务选择。
4. 同一指标跨页同色，正负混合图不能全部涂成风险红；先确认业务上的有利/不利含义，结合符号、零基线和标签。尚不支持的条件格式须实现后验收或明确交接，不假称自动完成。
5. 卡片单位放在数字后；按真实规模选择元、千、万、亿。使用 `display_unit` 与普通数值 `format` 生成数值型展示度量值，标题不重复“/万元”。图表单位在标题明确，明细保留原值；不同单位使用各自度量值并对账。
6. 时间图减少刻度与逐点标签；长名称优先横向图并提供完整名称途径；排名明确排序、Top N、子集与全量口径。不能为了布局好看改变时间粒度或丢弃数据。
7. 将 `design.colors`、组件 `role/fill/color/show_labels` 和度量值 `display_unit` 等真实支持的配置写入报表 YAML。`design_tokens.yaml` 是决策记录，不会被生成器自动读取，不能只写文档而不配置工程。
8. 生成后检查实际背景是否生效、单位是否缩放正确、文字是否截断、趋势是否拥挤、筛选和联动是否符合口径。样例图、Schema 和几何检查分别记录；只有实际检查后才更新对应的 Desktop 验收状态。
