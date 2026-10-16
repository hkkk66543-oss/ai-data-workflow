# AI 数据分析自动化工作流

从数据理解、行业识别和指标确认，到 **MySQL 8.0 自动执行 → 结果与模型导出 → 可编辑 Power BI 看板生成** 的通用项目母版。适用于不同业务数据集，不预设行业或套用固定电商指标。

当前版本已将临时 MySQL 执行器、Power BI 工程生成器、三套主题与自适应布局合并到 `main`。业务分析由 AI 辅助完成，程序负责执行已确认的 SQL 和报表计划；每份新看板仍需在 Power BI Desktop 中刷新验收。

## 已实现的能力

| 环节 | 当前能力 | 保留的产物 |
| --- | --- | --- |
| 理解与规划 | 根据字段、样例及业务说明识别行业，确认主题、数据粒度与指标口径 | 数据字典、质量报告、分析计划 |
| SQL 自动执行 | 自动创建临时 MySQL 8.0，执行 ODS → 导入 → DWD → ADS → 校验 → 导出，最后清理实例 | SQL 源码、CSV 结果、实际表结构与字段、执行记录 |
| Power BI 自动生成 | 依据明确 YAML 计划生成 Power Query、TMDL 模型、基础 DAX、显式关系和 PBIR 页面 | 可编辑 `.pbip` 工程与随附 CSV |
| 看板设计 | 蓝色 ocean、绿色 forest、紫色 plum；概览、对比、明细与手动布局；原生标题和分区 | 主题、页面计划、数据特征记录 |
| 布局适配 | 根据已配置组件、实际类别数量及标签长度调整布局；检测越界、重叠和页面过密 | `design-profile.json` |
| 质量与验收 | SQL 检查、文件哈希核验、字段与数值范围检查、关系约束检查；Desktop 中人工确认显示与交互 | `run.json`、`manifest.json`、实际截图 |

支持指标卡、折线图、柱状图、横向条形图、明细表和筛选器。生成器使用 Power BI 原生组件，可继续在 Desktop 编辑。

## 工作流

1. **理解数据**：检查字段、数据粒度、缺失、重复和时间范围，识别业务场景。
2. **确认分析口径**：确定分析问题、指标、币种换算、取消与异常记录处理方式。
3. **生成执行计划与 SQL**：分层保存 SQL，配置导入映射、检查规则和结果导出。
4. **自动执行 MySQL**：先预览，授权执行后启动临时实例，完成计算、校验和导出，再清理数据库。
5. **生成 Power BI 工程**：按本次成功结果与明确的报表计划建立模型、DAX、主题和页面。
6. **Desktop 验收**：完整解压工程、设置数据路径、刷新，核对数字、文字和筛选交互。
7. **整理项目成果**：生成分析报告、README、简历描述及面试讲解稿。

不虚构业务背景、字段、指标或结论。同名订单是否重复、金额是否需要换算等问题，应根据当前数据定义确认，不能沿用其他项目的口径。

## 快速开始

### 1. 准备环境

- Python 3.10+，安装本仓库依赖。
- SQL 执行环境：已运行的 Docker 引擎，或 Linux/Unix 中准备好的官方 MySQL 8.0 `mysqld` 二进制与所需动态库。
- 查看和验收看板：支持本仓库 PBIP/PBIR 格式的 Windows Power BI Desktop。

```powershell
python -m pip install -r requirements.txt
```

执行环境可以在云端，不一定是你的电脑。默认临时模式不需要已有 MySQL 账号和密码，也不需要复制 SQL 到 Navicat；运行器不会自动安装 Docker 或 MySQL。已有数据库可以通过 `database.mode: existing` 选择使用。

### 2. 使用自己的数据

复制母版，将原始文件放入 `data/raw/`，按 [项目执行说明](prompts/project_run/00_使用说明.md) 开始。先确认主题、指标和执行计划，再基于真实字段生成 SQL，并填写 `config.yaml` 的 `imports`、`checks`、`exports`。

```powershell
python scripts/run_sql_pipeline.py            # 预览，不连接数据库
python scripts/run_sql_pipeline.py --execute  # 实际执行、校验、导出并清理
```

空母版没有业务 SQL，不能直接产生真实分析。失败时停止后续步骤，保留运行记录并尝试清理，不自动调用 AI 改写并重跑。

### 3. 先跑合成数据演示

仓库包含三行合成数据，用于验证链路，不代表真实经营成果。

```powershell
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

命令会输出本次运行目录。确认该目录 `run.json` 中 `status: passed`、`runtime.cleanup: completed`，再把下面的 `<run_id>` 替换成本次实际目录名：

```powershell
python scripts/generate_powerbi.py --run-dir "examples/sql_pipeline_demo/outputs/runs/<run_id>" --plan examples/sql_pipeline_demo/powerbi_design_plan.yaml --output outputs/powerbi/SqlBiDesign --data-root "D:/SqlBiDesign/data"
```

`--output` 必须指向尚不存在的目录。`--data-root` 是目标电脑上 **生成工程的 data 文件夹**，请按实际位置填写；它不是原始 Excel 所在目录。生成器不修改原 SQL 结果。

合成示例的预期值：记录数 **3**、数值合计 **60.50**；筛选 A 后为 **2 / 30.50**。

## Power BI 主题和布局

在报表计划 YAML 中配置设计层；表、字段、度量值和图表绑定仍需按实际业务填写：

```yaml
design:
  palette: forest       # ocean / forest / plum
  eyebrow: BUSINESS ANALYSIS
  subtitle: 已确认的业务问题与口径说明
launcher: false         # 交付中不包含启动脚本
pages:
  - title: 经营概览
    layout: auto        # auto / overview / comparison / detail / manual
    # visuals 中声明真实字段与度量值
```

`auto` 根据已配置组件选择布局，遇到较多或较长类别时可转为横向条形图。不同数据集应编制不同业务问题与报表计划；这不等于自动发现行业指标。自动布局目前针对 1920×1080，其他画布使用 `manual` 配置位置。

关系仅采用明确配置的多对一单向关系，检查一端唯一、非空和多端匹配，不根据字段名猜测关联。复杂 DAX、自定义视觉、书签、钻取和导航等需要另外实现。

详见 [Power BI 自动生成说明](docs/PowerBI自动生成说明.md)、[设计升级说明](docs/PowerBI设计升级说明.md) 和 [显示修复记录](docs/PowerBI显示修复记录.md)。

## 打开看板与排错

1. **完整解压整个工程文件夹**，再打开 `.pbip`。不要在 ZIP 内直接双击，也不要单独移动入口文件。
2. `.pbip`、对应的 `.Report`、`.SemanticModel` 和 `data` 文件夹应保持生成时的相对位置。
3. 若刷新提示找不到 CSV：进入 **主页 → 转换数据 → 管理参数 → DataRoot**，填写实际 `data` 文件夹完整路径。参数输入框不加引号、不含 CSV 文件名。
4. 点击 **确定 → 关闭并应用**，检查数值、筛选、日期轴及文字显示，保存工程。

若出现“循环引用”，检查查询依赖和 `DataRoot` 的 M 表达式，不要直接认定是数据金额问题。需要高级编辑器修复时，M 字符串必须带英文双引号；这与“管理参数”输入框的填写方式不同。

普通计划默认可附带 `OpenReport.cmd` 与 `PrepareAndOpen.ps1`，用于设置工程内 CSV 路径后打开；设计示例采用 `launcher: false`，可以直接打开 PBIP 并管理参数。无需为此更改系统安全策略。

## 结果和源码保存在哪里

```text
outputs/runs/<run_id>/
├── tables/            # 实际 SQL 查询导出的 CSV
├── model/
│   ├── fields.csv     # 实际字段定义
│   ├── model.json     # 表、字段、显式外键及来源映射
│   └── schema.sql     # 数据库实际 DDL
├── source/            # 本次 SQL 与输入配置快照
├── manifest.json      # 产物清单、大小和 SHA-256
└── run.json           # 引擎版本、执行步骤、检查与清理结果
```

临时数据库可以删除，结果、SQL、字段定义和执行报告会保留。已有数据库模式不删除目标库；MySQL DDL 有隐式提交，整条流水线不能保证整体回滚。

生成的 Power BI 工程默认位于你指定的 `--output` 目录，包含模型、DAX、报表定义、CSV、计划与工程清单。真实业务数据、结果表、连接凭据和公司看板不得提交到公开仓库。

## 验证范围

- SQL 执行器已使用 MySQL Community Server 8.0.46 实际验证；Docker 生命周期另有模拟测试，不能据此宣称 Docker 已实测。
- Power BI 提供模型与生成契约测试、官方 JSON Schema 检查记录及可选 Microsoft TOM 解析脚本。
- 每个新生成工程默认 `status: draft`、`desktop_validated: false`。文件结构或模型解析通过，不代表 M 刷新、DAX 运行和页面显示通过；示例验收也不能代替新数据工程验收。

```powershell
python -m unittest discover -s tests -v
```

当前 BI 测试依赖演示运行目录 `examples/sql_pipeline_demo/outputs/runs/20261016T023517Z_e55f4886`；运行产物不随 Git 分发，全新克隆直接跑全部测试会因缺少该夹具报错。需先执行合成 SQL 演示，并将 `tests/test_powerbi.py` 中的 `RUN` 指向此次成功运行目录。真实 MySQL 集成测试还需设置 `MYSQLD_PATH`；未满足条件时会明确跳过。验证细节见 [SQL 执行验证记录](docs/SQL执行验证记录.md)。

## 提示词与配套产物

按 `prompts/project_run/` 的编号推进：数据理解与行业识别 → 主题和计划 → SQL → 报错修复 → QA → Python 辅助检查 → Power BI → 报告与简历 → 复盘。

- 数据定义和项目说明：`docs/`
- ODS / DWD / ADS / CHECKS SQL：`sql/`
- Power BI 页面目标、布局、口径及讲解：`powerbi_notes/`
- Python 诊断：`outputs/diagnostics/charts/`
- Desktop 实际截图：`outputs/bi_screenshots/`
- 分析报告：`outputs/reports/`
- 简历描述与面试稿：`docs/简历项目描述.md`、`docs/面试讲解稿.md`

Python 用于质量检查、辅助 EDA、SQL 执行和结果核验；最终可视化使用 Power BI。

## 可选：生成设计参考图

运行 SQL、生成 PBIP 和刷新随附 CSV 不需要 OpenAI API Key。只有调用 OpenAI Images API 生成 BI 布局参考图时才需要配置 `OPENAI_API_KEY`。参考图不作为精确数据来源；无法调用时使用 `powerbi_notes/image_prompts.md` 中的图片提示词。密钥只放本机环境变量，不写入代码或提交 Git。
