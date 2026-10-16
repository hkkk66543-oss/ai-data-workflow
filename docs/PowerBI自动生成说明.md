# SQL 结果自动生成 Power BI 工程

## 现在能完成什么

从本次通过校验的 MySQL 运行目录读取 CSV 与实际字段元数据，依据明确的报表计划生成可编辑 PBIP：Power Query 导入、TMDL 字段、基础 DAX、显式多对一关系、PBIR 页面和组件。CSV 随工程保存，临时 MySQL 删除后仍可刷新。

空白基线来自用户提供的 `BI模板.Report.zip` 与 `BI模板.SemanticModel.zip`。两者分别是空白报表与空白语义模型，未包含外层 `.pbip`；已补入口并修正相对引用。保留用户主题，排除 `.pbi` 缓存和 `.platform` 标识。原 ZIP 不改动。基线位于 `templates/powerbi_blank/`。

## 使用

先按 SQL 自动执行说明运行并检查 `run.json`。临时模式还必须清理成功。然后按真实业务口径填写 YAML，可参考 `examples/sql_pipeline_demo/powerbi_plan.yaml`。本文件只是三行合成数据的链路演示，不代表真实业务分析。

```bash
python scripts/generate_powerbi.py --run-dir examples/sql_pipeline_demo/outputs/runs/20261016T023517Z_e55f4886 --plan examples/sql_pipeline_demo/powerbi_plan.yaml --output outputs/powerbi/SqlBiDemo
```

输出目录必须不存在。真实数据工程不要提交至 Git；不要改动原 SQL 运行目录。

- `tables`：声明模型表名、CSV 导出名、对应 SQL 源表。使用真实字段元数据；聚合/别名字段必须明确 `column_types`。
- `measures`：先确定业务口径，再配置 countrows、sum、average、min、max、distinctcount。复杂 DAX 需单独审核扩展。
- `relationships`：仅生成显式配置的多对一单向关系，并检查字段类型、一端唯一非空、多端匹配。不会按名称猜测维度或连接无关数据。
- `pages`：按业务问题配置页面及位置，支持 card、column、line、table、slicer 五种组件。首版不自动推断页面、指标或关系。
- 字符串保持文本，编号前导零不会自动去除。Int64 和固定小数检查实际数值范围；高精度 DECIMAL 不静默舍入。显式 double 是浮点数，需评估精度。

Windows 解压完整文件夹，双击 `OpenReport.cmd`。它调用 `PrepareAndOpen.ps1`，把 `DataRoot` 设置为同目录 data 的绝对路径，再打开 PBIP。文件夹移动后重新运行。若本机 PowerShell 策略禁止脚本，可直接打开 PBIP 并在 Power Query 的管理参数中手动设置 DataRoot；不需要更改系统安全策略。请使用能打开原空白工程的同版或较新版 Desktop。

## 验证边界

工程默认 `status: draft`、`desktop_validated: false`。静态结构正确不等于 M 刷新、DAX 执行、图表显示已经通过。

自动测试：

```bash
python -m unittest discover -s tests -v
```

可选真实 Microsoft TOM 模型解析（自行准备官方 Microsoft.AnalysisServices NuGet 库；不将 DLL 入库）：

```powershell
pwsh -File scripts/test_powerbi_model.ps1 -ProjectDirectory outputs/powerbi/SqlBiDemo -TomDirectory C:/tools/tom
```

TOM 解析只校验模型可反序列化及字段映射，不执行 DAX/M。

【需要你手动操作】
操作目标：完成 Power BI Desktop 最终刷新与显示验证。
为什么需要你操作：当前执行环境没有 Windows 版 Power BI Desktop。
具体步骤：解压工程，运行 OpenReport.cmd，点击刷新；检查两个指标、分类汇总、日期趋势、明细和筛选联动，然后保存。
完成后你应该看到：合成示例记录数 3、数值合计 60.50，类别 A 为 30.50、B 为 30.00；日期 2026-01-01 为 10.50、2026-01-02 为 50.00。筛选 A 后记录数 2、合计 30.50。
如果报错怎么办：复制完整错误和 Desktop 版本；脚本被策略阻止时手动设置 DataRoot。不要将静态通过记录改写为 Desktop 通过。
完成后请回复我什么：打开和刷新结果，或完整错误。

不自动发布到 Power BI Service，不创建租户资源，不处理登录与凭据。实际截图仍应在 Desktop 验证后保存至 `outputs/bi_screenshots/`。
