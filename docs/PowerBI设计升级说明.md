# Power BI 主题与布局说明

## 持久设计规则与配置

项目内置 [.agents/skills/powerbi-report-design/SKILL.md](../.agents/skills/powerbi-report-design/SKILL.md)，由 `AGENTS.md` 和第 07 阶段提示词引用。每个新数据集先形成设计简报，再选择页数、图表、布局与颜色；不复制历史测试集，不固定四卡两图一表。

默认不放装饰性侧栏，优先保留分析面积；区分画布、内容表面和浅色分区，避免近白画布与全白组件造成层次不足。内置 palette 提供协调起点，支持如下显式配置：

```yaml
design:
  palette: ocean
  colors:
    canvas: '#E8EEF6'
    tint: '#EAF1FF'
    secondary_tint: '#FFF3DF'
```

`design.colors` 仅接受 palette 已有颜色角色，均使用 `#RRGGBB`。组件的 `role` 支持 primary、secondary、positive、negative、neutral，选择前须确定业务含义；`fill`、`color` 覆盖组件底色与主色。表格默认中性表面；卡片和分析图默认浅主色底，可用 secondary 等角色拉开层次。这些属性会写入原生视觉对象，不仅依赖主题继承。折线图默认关闭逐点数据标签，组件 `show_labels` 可覆盖；条形等图表的 `sort_by: measure` 按度量值降序排列。

金额卡片将单位放在数值后。度量值增加 `display_unit: 万` 时，生成器对真实聚合结果除以 10000，保留数值型 DAX，并把普通 `format: '#,0.00'` 写成 `#,0.00" 万"`。支持元、千、万、亿；不执行币种换算，百分比不得使用此配置。标题使用“收入”等指标名，不重复“/万元”。图表和明细需要不同单位时使用各自的数值型展示度量值，原始数据与金额资格口径不变。

颜色角色是组件级样式，不是按每个数据点自动判断正负的条件格式。Top N、正负条件色、连续时间轴与复杂交互仍须按实际支持情况配置、扩展或交接，不能仅凭效果图宣称实现。详细的按数据选择规则、对账和截图检查见 Skill；`powerbi_notes/design_tokens.yaml` 是设计记录，生成器只读取显式报表 YAML。

规则蒸馏参考 Anthropic frontend-design、UI UX Pro Max 与 Microsoft Fabric Skills 的设计方法，出处见 [颜色与单位参考](../.agents/skills/powerbi-report-design/references/color-and-units.md)。不要求运行时访问这些资源，不复制其品牌和业务数据。布局容量与 Desktop 验收边界见下文。

## 设计能力

设计层与 SQL/模型分离，原始数据和计算口径不因换主题而改变。`scripts/powerbi_design.py` 是原创实现，仅参考外部设计原则；不依赖外部安装器、CLI、自定义视觉或在线资源。

- 三套可配置浅色主题：ocean 蓝、forest 绿、plum 紫。主题注册到 PBIR 内，保留用户原始月度基础主题。
- 原生可编辑标题、眉题、说明、分区标题和页脚；统一字体层级、卡片圆角、图表标签、表格列宽/底色和栅格间距。
- overview 非对称概览、comparison 对比、detail 明细三种布局；auto 根据已配置的实际组件选择页面类型。布局计算位置、检测越界/重叠，过密时要求拆页，不把控件压小塞进去。
- 对本次真实 CSV 的行数、字段类型、类别数量（上限 1001）和标签长度生成 `design-profile.json`。auto 页面遇到较多或较长类别时改用横向条形图；不新增没有业务口径的指标。
- 支持 card、column、bar、line、table、slicer 六种数据组件，以及设计层生成的原生文本。
- `launcher: false` 可交付无启动脚本的工程；`--data-root` 可以预设目标电脑路径。

这不是按文件名自动判断行业的系统。业务理解、行业确认、指标口径仍在现有工作流前置阶段完成，之后根据真实字段编制 YAML。销售、行为、财务等场景应配置不同的分析问题和页面；缺少时间、目标、转化顺序等必要字段时不能生成同比、目标达成或漏斗指标。

## 生成

```bash
# RUN_DIR 为本次成功运行的 run.json 所在目录，请替换后执行。
python scripts/generate_powerbi.py --run-dir "RUN_DIR" --plan examples/sql_pipeline_demo/powerbi_design_plan.yaml --output outputs/powerbi/SqlBiDesign
```

报表计划配置：

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

未设置 design 时按显式组件位置生成，不启用设计层自动布局。自动布局暂支持 FHD 1920×1080；其他画布使用 manual 并设置 position。每页最多 4 卡、2 筛选、4 分析图、1 表格，受可读高度限制还可能需要拆页。manual 页面需为自动加入的标题/说明/页脚留空间；全部位置会检查重叠。

## 设计参考与采用范围

查阅时间：2026-10-16。

1. [Microsoft skills-for-fabric / design](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design.md)：先检查语义模型、确定页面问题、再选择图表与设计身份。
2. [Layout Composition](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design/layout.md)：8px 栅格、24px 间距、标题优先、页面原型、筛选区域和空间校验。
3. [Visual Cookbook](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/design/visual-cookbook-part-02.md)：原生文本、高度、表格和筛选器格式建议。未直接复制其主题文件或脚本。
4. [yasarkocyigit / powerbi-templates / DAQ](https://github.com/yasarkocyigit/powerbi-templates/tree/main/reports/daq)：参考按业务决策组织多页、保留口径说明、区分主题与分析结构的做法。没有复制其品牌、数据、模型、自定义视觉或主题。
5. [Microsoft report theme schemas](https://github.com/microsoft/powerbi-desktop-samples/tree/main/Report%20Theme%20JSON%20Schema)：实际使用 2.153 的官方 JSON Schema 校验三个生成主题。

## 支持边界与验收

设计规则运行时不依赖外部 GitHub Skill、CLI 或在线模板。导航按钮、书签、钻取、动态同比/环比、目标线和复杂自定义视觉需单独扩展；不能把参考资源的能力当成本生成器的能力。

生成器已配置下拉筛选器、date 字段分类轴、较大的文字及明细表空间，并检查越界和重叠。每个新数据集仍须检查真实日期粒度、长标签、单位、正负值表达和筛选联动。

先做结构、字段绑定、几何与单位对账检查，再在目标 Desktop 打开、刷新和检查实际显示。每份新工程默认保持 `status: draft`、`desktop_validated: false`，直到该工程完成实际验收。样例图、Schema 和 TOM 检查不替代 Desktop；历史示例的测试数量和检查结果见 [生成验证记录](PowerBI生成验证记录.md) 与 [显示修复记录](PowerBI显示修复记录.md)，不代表所有数据集均已验证。
