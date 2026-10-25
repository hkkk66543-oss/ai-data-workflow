# 颜色、单位与实现边界

## 可选风格

现代商务适合通用经营分析；经营简报适合管理层复盘；深色监控只在受众和环境合适时使用。当前内置生成器的 ocean、forest、plum 都是浅色主题，不代表已实现深色模式。先根据业务和数据选择，再指定主色；不得按文件名猜行业。

## 颜色角色示例

| 角色 | 可用起点 | 用法 |
|---|---|---|
| 画布 | `#E8EEF6` | 与内容表面形成可见区别 |
| 内容表面 | `#FFFFFF` | 明细、密集信息与局部留白 |
| 主色 / 浅底 | `#2563EB` / `#EAF1FF` | 常规主指标或重点分析 |
| 次色 / 浅底 | `#B77916` / `#FFF3DF` | 次要指标或另一分析分区 |
| 正向 / 浅底 | `#14857A` / `#E5F4F0` | 业务定义为有利的结果 |
| 风险 / 浅底 | `#C34C42` / `#FBECE9` | 业务定义为需关注的结果 |
| 文字 / 次文字 | `#182B49` / `#5E6C84` | 保持与所选背景的可读对比 |

这些配色不是固定的“收入蓝、成本橙”映射。按本次指标含义配置；成本上升是否有利要看业务。分类图的不同类别可以使用协调色系，但不能挪用风险色表达普通分类。重点和其余对象可用同色系深浅区分。

普通正文目标对比度至少 4.5:1，大字至少 3:1；实际使用时检查文字与各自表面，不仅检查主题默认色。使用浅底和深色文字，避免浅色数字叠浅色卡片。

## 已支持的 YAML

下面只演示接口，不是每个项目必须有的指标或布局。`真实明细`、`金额` 必须替换为当前成功运行实际存在的表和数值列。

```yaml
design:
  palette: ocean
  colors:
    canvas: '#E8EEF6'
    tint: '#EAF1FF'
    secondary_tint: '#FFF3DF'
measures:
  - name: 金额展示
    table: 真实明细
    aggregation: sum
    column: 金额
    format: '#,0.00'
    display_unit: 万
pages:
  - title: 已确认的业务问题
    layout: auto
    visuals:
      - type: card
        title: 金额
        measure: 金额展示
        role: primary
      - type: bar
        title: 各类别金额 / 万元
        table: 真实明细
        column: 类别
        measure: 金额展示
        role: secondary
        sort_by: measure
        fill: '#FFF3DF'
```

`role` 可用 primary、secondary、positive、negative、neutral，控制组件背景与主色，不改变指标计算。`fill`、`color` 可覆盖单组件；`design.colors` 可覆盖内置 palette 的颜色角色；均使用 `#RRGGBB`。`show_labels: false` 可减少图表标签，折线图默认关闭逐点标签。

`display_unit` 可用 元、千、万、亿，分别按 1、1000、10000、100000000 缩放数值，并在普通数值 `format` 后追加单位。它不是汇率换算。原值 63601984.8221 选择万时，数值为 6360.19848221，显示 `6,360.20 万`；筛选后的数值仍由 DAX 重新计算。千/万/亿也可用于已明确口径的数量指标；百分比不使用此接口。

卡片与图表需要不同单位时，定义各自的数值型展示度量值；完整明细继续保留原始数值与精度。不能改变原度量值后让其他引用误用单位。

正负值条件格式、按类别突出 Top N、连续时间轴、书签和复杂导航，不因设置 `role` 自动实现。先核实生成器支持范围；需要时在可编辑工程内扩展并实际验证，或明确交接。

## 方法来源

- [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)：根据主题作出明确视觉选择，先形成设计系统，再检查实际显示。
- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)：语义样式、场景适配、颜色与可读性检查、避免通用反面模式。
- [Microsoft Fabric Skills](https://github.com/microsoft/skills-for-fabric)：真实模型与业务问题先行，区分规划、制作和实际验收。

采用的是这些资源的设计思路；没有直接安装它们，也没有把其网页能力宣称为 Power BI 原生能力。
