# Power BI 设计升级

## 已实现

设计层与 SQL/模型分离，原始数据和计算口径不因换主题而改变。`scripts/powerbi_design.py` 是原创实现，仅参考外部设计原则；不依赖外部安装器、CLI、自定义视觉或在线资源。

- 三套可配置浅色主题：ocean 蓝、forest 绿、plum 紫。主题注册到 PBIR 内，保留用户原始月度基础主题。
- 原生可编辑标题、眉题、说明、分区标题和页脚；统一字体层级、卡片圆角、图表标签、表格列宽/底色和栅格间距。
- overview 非对称概览、comparison 对比、detail 明细三种布局；auto 根据已配置的实际组件选择页面类型。布局计算位置、检测越界/重叠，过密时要求拆页，不把控件压小塞进去。
- 对本次真实 CSV 的行数、字段类型、类别数量（上限 1001）和标签长度生成 `design-profile.json`。auto 页面遇到较多或较长类别时改用横向条形图；不新增没有业务口径的指标。
- 新增横向条形图。原有基础可视化继续可用。
- `launcher: false` 可交付无启动脚本的工程；`--data-root` 可以预设目标电脑路径。

这不是按文件名自动判断行业的系统。业务理解、行业确认、指标口径仍在现有工作流前置阶段完成，之后根据真实字段编制 YAML。销售、行为、财务等场景应配置不同的分析问题和页面；缺少时间、目标、转化顺序等必要字段时不能生成同比、目标达成或漏斗指标。

## 生成

```bash
python scripts/generate_powerbi.py --run-dir examples/sql_pipeline_demo/outputs/runs/20261016T023517Z_e55f4886 --plan examples/sql_pipeline_demo/powerbi_design_plan.yaml --output outputs/powerbi/SqlBiDesign
```

报告计划增加：

```yaml
design:
  palette: ocean
  eyebrow: SQL / POWER BI
  subtitle: 已确认的业务问题与口径说明
launcher: false
pages:
  - title: 经营概览
    layout: auto # overview / comparison / detail / manual
    # visuals 继续配置真实表、列、度量值；自动布局可省略 position
```

未设置 design 时保留原生成行为。自动布局暂支持 FHD 1920×1080；其他画布使用 manual 并设置 position。每页最多 4 卡、2 筛选、4 分析图、1 表格，受可读高度限制还可能需要拆页。manual 页面需为自动加入的标题/说明/页脚留空间；全部位置会检查重叠。

## 设计参考与采用范围

查阅时间：2026-10-16。

1. [Microsoft skills-for-fabric / design](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design.md)：先检查语义模型、确定页面问题、再选择图表与设计身份。
2. [Layout Composition](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design/layout.md)：8px 栅格、24px 间距、标题优先、页面原型、筛选区域和空间校验。
3. [Visual Cookbook](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design/visual-cookbook-part-02.md)：原生文本、高度、表格和筛选器格式建议。未直接复制其主题文件或脚本。
4. [yasarkocyigit / powerbi-templates / DAQ](https://github.com/yasarkocyigit/powerbi-templates/tree/main/reports/daq)：参考按业务决策组织多页、保留口径说明、区分主题与分析结构的做法。没有复制其品牌、数据、模型、自定义视觉或主题。
5. [Microsoft report theme schemas](https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%20Theme%20JSON%20Schema)：实际使用 2.153 的官方 JSON Schema 校验三个生成主题。

本轮没有安装额外 GitHub skill 或第三方软件；设计规则已落实到项目模块和第 07 阶段提示词中。导航按钮、书签、钻取、动态同比/环比、目标线和复杂自定义视觉尚未实现，不能把参考仓库的能力当成当前项目的能力。

## 本次验证

- 全套 45 项：42 项通过，3 项真实 MySQL 测试因本次未设置 MYSQLD_PATH 跳过。新增设计测试检查输入不变、字段绑定保留、不同布局、实际长类别适配、重叠/密度阻断、主题与无启动脚本交付。
- 3 份设计示例（同一合成 SQL 结果）共 50 份 PBIP/PBIR 文档通过官方 Schema；3 个自定义主题通过官方月度主题 Schema。
- 3 个模型均通过 Microsoft TOM 19.118.3 实际反序列化（各 1 表、4 字段、2 指标）。
- 用户已于本次会话确认原基础示例的 Desktop 打开、刷新、数值和筛选联动检查通过。本轮新主题、文本与布局没有在此环境运行 Desktop，仍标记 draft、desktop_validated=false，不能继承基础示例的验证状态。

【需要你手动操作】
操作目标：验证新版设计在 Desktop 的显示与交互。
为什么需要你操作：当前环境没有 Windows 版 Power BI Desktop。
具体步骤：直接打开新示例的 PBIP，按说明确认 DataRoot，刷新；检查标题/文字不截断、卡片和图表样式、数值与筛选，然后保存。
完成后你应该看到：记录数 3、合计 60.50；筛选 A 后 2、30.50。
如果报错怎么办：提供完整错误、Desktop 版本和页面截图，不修改系统安全策略。
完成后请回复我什么：新版显示和筛选结果。


## 显示修复版本

依据用户 Desktop 截图，已针对下拉筛选、日期分类轴、明细表高度和字号更新生成器。具体修复、测试及版本验收边界见 [PowerBI显示修复记录](PowerBI显示修复记录.md)。用户已确认上一版三套功能验证通过，修复后的显示仍须单独检查。
