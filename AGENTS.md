# 通用 AI 数据分析工作流总控规则

## 核心规则

1. 本项目不预设行业。
2. 每次分析开始前，必须先执行 Context / Data Understanding。
3. 在理解数据后，必须执行 Domain Identification，也就是行业识别。
4. Codex 需要根据字段名、表名、样例数据、业务含义，判断当前数据更接近哪个行业或业务场景。
5. 如果行业不明确，需要输出 2-3 个可能方向，并标注判断依据。
6. 不允许在行业未确认前直接套用电商指标。
7. 不允许虚构业务背景。
8. 不允许虚构字段。
9. 不允许虚构数据。
10. 不允许虚构结论。
11. 所有分析模块必须基于当前真实字段设计。
12. 所有指标必须先写业务口径，再写 SQL 或 Python。
13. SQL 默认使用 MySQL 8.0。
14. Python 默认使用 pandas、numpy、matplotlib，用于数据质量检查、辅助 EDA、异常识别、SQL 结果校验；另允许使用数据库连接器执行已审核 SQL、导入数据和导出结果。
15. Python 不是最终可视化工具，不负责生成 README、报告或 Power BI 替代展示图。
16. 最终可视化工具是 Power BI；BI 样例图可由 OpenAI Images API 或图片提示词生成。
17. 图表必须服务于业务问题，且必须基于真实字段、真实 ADS 表和明确指标口径。
18. 最终结果必须适合 GitHub 展示、简历项目和面试讲解。

## 数据与产物规则

- 永远不要修改 `data/raw` 中的原始数据。
- 所有清洗结果必须输出到 `data/processed`。
- Python 诊断图必须输出到 `outputs/diagnostics/charts/`，并标注“内部检查图，不用于最终展示”。
- `outputs/charts/` 不再作为 Python 图表默认输出目录。
- Power BI 样例图输出到 `outputs/bi_mockups/`。
- Power BI 实际截图输出到 `outputs/bi_screenshots/`。
- 所有分析报告必须输出到 `outputs/reports`。
- 所有 SQL 文件必须按照 ODS / DWD / ADS / CHECKS 分层保存。
- 如果字段含义不明确，先根据字段名和样例数据推测，并标注“待确认”。
- 每一步都要生成可保存的文件，而不是只在聊天里回答。

## SQL 中文命名规则

1. SQL 表名和字段名默认尽量使用简约明了的中文。
2. MySQL 中所有中文表名和中文字段名必须使用反引号包裹。
3. 中文命名要短、直观，不要写成完整句子。
4. 表名应体现数据分层：
   - ODS 原始层：`原始_事件表`、`原始_订单表`、`原始_用户表`
   - DWD 清洗明细层：`清洗_事件明细`、`清洗_订单明细`、`清洗_用户画像`
   - DIM 维度层：`维度_设备`、`维度_地区`、`维度_产品`
   - ADS 应用层：`应用_每日概览`、`应用_用户分层`、`应用_渠道分析`
   - CHECK 校验层：`校验_数据质量明细`、`校验_指标汇总`
5. 字段名示例：
   - user_id -> `用户编号`
   - session_id -> `会话编号`
   - event_type -> `事件类型`
   - event_target -> `事件目标`
   - event_time -> `事件时间`
   - device_os -> `设备系统`
   - app_version -> `应用版本`
   - user_age -> `用户年龄_原始`
   - user_age_clean -> `用户年龄_清洗`
   - is_user_age_abnormal -> `年龄是否异常`
   - abnormal_reason -> `异常原因`
   - total_events -> `事件数`
   - total_users -> `用户数`
   - total_sessions -> `会话数`
   - avg_duration -> `平均时长`
   - abnormal_rate -> `异常率`
6. 如果某些字段是技术字段，可以保留简短英文，但必须在字段注释中写中文解释。
7. 所有 SQL 必须给表和字段加中文注释。
8. SQL 生成时必须同时生成 `docs/SQL中英文命名映射表.md`。
9. 如果 MySQL 环境因为中文表名或中文字段名出现兼容问题，必须提供备选方案：物理表名使用英文，创建中文视图供 Navicat / Power BI 使用，同时保留中英文映射表。
10. 默认优先方案为：SQL 物理表和字段使用中文命名，全部中文标识符使用反引号。

SQL 生成完成后，必须说明：

- 生成了哪些中文表。
- 每张中文表对应什么业务含义。
- 每张表由哪些原始字段加工而来。
- 哪些字段是清洗字段。
- 哪些字段是异常标记字段。
- 哪些表适合导入 Power BI。
- 默认临时 MySQL 的运行条件、真实版本、预览/执行结果，以及环境清理状态；不能默认要求本地 MySQL 或 Navicat。

## Python 定位规则

1. Python 用于数据质量检查、辅助 EDA、异常识别、SQL 结果校验，以及已授权的数据库执行和数据传输，不生成最终展示图。
2. Python 不生成最终展示图，不生成用于 README 或报告核心展示的 matplotlib / seaborn 图。
3. Python 可以生成少量诊断图，但只能保存到 `outputs/diagnostics/charts/`。
4. Python 输出重点包括：
   - `scripts/data_quality_check.py`
   - `scripts/eda_summary.py`
   - `scripts/sql_result_check.py`
   - `outputs/reports/eda_summary.md`
   - `outputs/reports/python_data_check_report.md`
   - `outputs/tables/` 下的 CSV / Excel 汇总表
5. README 和分析报告优先引用 Power BI 实际截图、`outputs/bi_mockups/` 中的 BI 样例图或 Power BI 页面设计说明。

## Power BI 最终展示规则

1. Power BI 是最终可视化工具。
2. Power BI 页面必须基于当前行业、真实字段、真实 ADS 表和明确业务问题设计。
3. 每页必须记录页面名称、业务目标、布局、实际使用的组件、表和字段、指标口径、排序、标签、交互规则、报表 YAML 绑定、生成与验收步骤和讲解话术。没有必要的组件应省略。
4. 每页必须生成一个 OpenAI Images API 图片提示词。
5. 不允许用 Python、matplotlib、seaborn 生成 BI 样例图。
6. BI 样例图用于布局参考，不作为精确数据来源。
7. 精确指标数值必须写在 `powerbi_notes/page_xxx.md` 中。
8. 如果 OpenAI Images API 无法调用，必须生成 `powerbi_notes/image_prompts.md` 并提醒用户手动复制提示词生成图片。
9. 根据已审核报表 YAML 使用 `scripts/generate_powerbi.py` 自动生成数据接入、模型、支持的 DAX、主题和原生组件；不得把 Navicat 运行、手动导入导出、复制 DAX 或逐项拖字段写成默认必经步骤。仅在本项目确需尚不支持的组件或交互时交接扩展步骤。
10. 样例图不作为 PBIP 生成的前置依赖；缺少图片 API 不阻断真实数据工程生成。

### 报表设计 Skill 与持久设计规则

Power BI 方案、主题或页面制作前，读取 `.agents/skills/powerbi-report-design/SKILL.md`；第 07 阶段提示词同样必须引用它。

- 根据本次业务问题、字段与分布选择页数、图表和布局；不能固定复制测试集或“四卡两图一表”。
- 默认不放装饰性侧栏，优先将画布用于分析。保留必要留白，按需拆分分析与明细。
- 区分画布、内容表面、浅色分区、强调色和风险色，避免近白画布加全白组件；颜色角色依业务选择，不强制所有项目同色。
- 金额卡片依据数量级将单位放在数值后，例如 `6,360.20 万`；保留数值型 DAX，缩放与格式一致，不改变原始统计口径。
- 将设计决策同时落入报表 YAML 和生成器支持的属性；检查实际截图，不将样例图或静态检查当作 Desktop 验收。

## 手动操作提醒规则

当某个步骤 Codex 无法替用户完成，或需要用户在外部软件中操作时，必须主动停止并提醒。不能假装已经完成需要用户手动完成的步骤。

每个需要用户手动操作的地方，必须使用固定格式：

```text
【需要你手动操作】
操作目标：
为什么需要你操作：
具体步骤：
完成后你应该看到：
如果报错怎么办：
完成后请回复我什么：
```

## SQL 自动执行规则

- 数据理解、行业、项目主题、指标口径与执行计划仍须先确认。
- 在生成真实 SQL 时，同时配置 `sql_pipeline.imports/checks/exports`。默认 database.mode: temporary，在执行环境自动创建实例和凭据，用户不需要提供已有数据库信息；仅 existing 模式从本机环境变量取密码。真实数据、凭据及运行目录不得提交到 Git。
- 使用 `scripts/run_sql_pipeline.py` 先预览；预览不连接数据库，不能称为 SQL 已执行或业务校验通过。
- 用户确认项目及已审核 SQL 后，可用 `--execute` 在临时 MySQL 8.0 中连续执行 ODS、导入、DWD、ADS、校验、导出、建模元数据提取和清理；不要求用户逐层复制或反馈。必须保存 SQL 源码、结果表、字段定义、实际表结构和执行/清理记录。
- 失败即停，不自动用大模型修改并重跑，不从部分完成处盲目续跑。MySQL DDL 有隐式提交，禁止宣称整条流水线能够回滚。
- 缺少临时运行环境、真实数据或业务口径时，明确缺少项。优先在可用的执行环境准备临时 MySQL；不能把模拟驱动当成真实 MySQL，也不能自动切换其他数据库。只有用户明确选择 existing 时才需要已有数据库连接。
- 校验 SQL 必须明确配置零异常行或一行一列等于期望值；业务异常要阻断导出。空 SQL、空校验配置不算成功。
- 成功交付只使用本次 status: passed 的运行；临时模式要求 runtime.cleanup: completed。运行目录须保留 tables/、model/、source/、manifest.json 和 run.json，不能引用历史/partial 冒充新结果。失败也必须尝试清理临时实例；清理失败明确记录。
- 已授权的执行细节自动连续完成；更换目标库、扩大改写范围或改变业务口径需重新确认。
- Power BI 最终展示定位保持不变。允许使用 `scripts/generate_powerbi.py` 按明确报表计划生成 PBIP/PBIR 草稿；只读本次成功运行结果，不能推断不存在的字段、指标或关系。仅支持的基础组件可自动搭建，其余需明确交接。工程必须标记 Desktop 尚未验证，直到实际打开、刷新、校对并检查交互。

常见手动场景包括：

- 把真实 CSV / Excel / JSON 放到 `data/raw/`，不要修改原始文件。
- 执行环境没有 Docker 或 MySQL 8.0 二进制时，选择可运行临时数据库的环境；不默认让用户配置已有数据库。
- 用户自选 existing 模式时，首次填写连接并在本机设置密码；无法连接时交接本机运行入口。
- 配置 `OPENAI_API_KEY`（仅在需要 BI 样例图时）、在 Power BI Desktop 中打开生成工程、刷新、校对数值及页面交互并截图；不支持的组件再手动扩展。

每次执行阶段结束时，Codex 必须输出：

```text
下一步是否需要你手动操作：
如果需要，具体操作是什么：
操作完成后，请回复我什么：
```

## 标准工作流

Context / Data Understanding -> Domain Identification -> Brainstorming -> Plan -> Work-Plan -> Execute -> Test / Verify / QA -> Review -> Learn -> Reuse

## 行业适配规则

1. 先扫描数据，再判断行业。
2. 行业识别输出到 `docs/行业识别报告.md`。
3. 行业确认后，从 `domain_packs/` 中选择最匹配的模板作为参考。
4. 行业模板只能提供思路，不能替代真实字段判断。
5. 如果用户确认的项目主题与自动识别不同，以用户确认结果为准，但仍需标注依据和风险。

## 输出约定

- 原始数据：`data/raw/`
- 清洗数据：`data/processed/`
- 抽样数据：`data/sample/`
- SQL：`sql/01_ods/`、`sql/02_dwd/`、`sql/03_ads/`、`sql/04_checks/`
- Python 诊断图：`outputs/diagnostics/charts/`
- BI 样例图：`outputs/bi_mockups/`
- BI 实际截图：`outputs/bi_screenshots/`
- 表格：`outputs/tables/`
- 报告：`outputs/reports/`
- 过程文档：`docs/`
- Power BI 说明：`powerbi_notes/`
- 行业模板：`domain_packs/`
- 可复用提示词：`prompts/`
- 项目执行提示词包：`prompts/project_run/`
