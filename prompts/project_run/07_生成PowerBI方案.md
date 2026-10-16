# 07 生成 Power BI 方案

请只执行本阶段。优先从本次 status: passed 的运行读取 tables/、model/fields.csv、model/model.json、source/sql/ 和 run.json；临时模式还需确认清理完成。不得根据已删除的临时数据库编造新结果。执行前必须读取真实 ADS 表说明、`docs/指标口径.md`、`docs/SQL中英文命名映射表.md` 和 QA 结果。

任务：

1. 自动判断当前项目应该做几页 Power BI 看板。
2. 每一页对应一个明确业务问题。
3. 生成：
   - `powerbi_notes/dashboard_plan.md`
   - `powerbi_notes/dax_measures.md`
   - `powerbi_notes/layout_reference.md`
   - `powerbi_notes/BI样例图生成说明.md`
   - `powerbi_notes/image_prompts.md`
   - `powerbi_notes/page_01_xxx.md`
   - `powerbi_notes/page_02_xxx.md`
   - `powerbi_notes/page_03_xxx.md`
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
