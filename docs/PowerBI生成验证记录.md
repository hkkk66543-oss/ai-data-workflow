# Power BI 生成验证记录

本文保存指定示例与日期的验证快照，不是当前项目的操作步骤或实时测试状态。使用方法见 [自动生成说明](PowerBI自动生成说明.md)；每份新工程须独立验收。

日期：2026-10-16。对象：SqlBiDemo，SQL run `20261016T023517Z_e55f4886` 的三行合成数据。

- 12 项新增生成器测试通过（含实际 PowerShell 准备路径、Unicode/空格目录、重复运行）。全套 37 项中 34 项通过，3 项真实 MySQL 测试因本次未配置 MYSQLD_PATH 而跳过；前一阶段已有真实 MySQL 验证记录。
- 11 份生成 JSON 文档通过 Microsoft 官方公开 JSON Schema 校验：PBIP、report、page、pages、version、6 个 visual。Schema 来自 developer.microsoft.com/json-schemas/fabric，引用一并解析。
- Microsoft.AnalysisServices 19.118.3 的真实 TmdlSerializer 成功反序列化：1 表、4 字段、2 度量值、0 关系；sourceColumn 与 CSV 表头一致。
- PowerShell 7.6.7 实际执行 PrepareAndOpen.ps1 -PrepareOnly，正确设置 DataRoot。未在 Windows cmd.exe 中运行启动器，未启动 Desktop。
- 使用 Power BI 插件模型向导生成了规划草稿。其自动猜测的维度没有写入实际工程；示例只使用真实导出的表和显式指定的指标。
- 插件 UnifiedReview -SkipLive 在 Linux 环境失败：其依赖间接调用 Win32_Process/Get-CimInstance。未将此结果记录为通过，未模拟 Windows API 绕过。以上官方 Schema/TOM 检查独立执行。

尚未完成：Power BI Desktop 打开、Power Query 刷新、DAX 实际求值、图表显示与联动。生成工程保持 draft、desktop_validated=false。预计值仅用于后续对账：记录数 3，数值合计 60.50，A 30.50，B 30.00。

## 主题与布局验证快照（2026-10-16）

- 全套 45 项：42 项通过，3 项真实 MySQL 测试因本次未设置 MYSQLD_PATH 跳过。新增设计测试检查输入不变、字段绑定保留、不同布局、实际长类别适配、重叠/密度阻断、主题与无启动脚本交付。
- 3 份设计示例（同一合成 SQL 结果）共 50 份 PBIP/PBIR 文档通过官方 Schema；3 个自定义主题通过官方月度主题 Schema。
- 3 个模型均通过 Microsoft TOM 19.118.3 实际反序列化（各 1 表、4 字段、2 指标）。
- 用户已于本次会话确认原基础示例的 Desktop 打开、刷新、数值和筛选联动检查通过。本轮新主题、文本与布局没有在此环境运行 Desktop，仍标记 draft、desktop_validated=false，不能继承基础示例的验证状态。

## 颜色与单位验证快照（2026-10-25）

Power BI 专项单元测试共 28 项，27 项通过、1 项可选环境检查跳过；Skill 元数据验证通过。使用合成单元测试输入生成的 17 个报表定义通过官方 JSON Schema 检查，未发现几何越界或重叠。测试数据明确标注为合成输入，不作为真实 SQL 执行证据。

新默认颜色与单位设置仍需在目标 Power BI Desktop 中打开、刷新并检查实际显示，生成交付继续保持 `desktop_validated: false`。完整测试另有 4 项 SQL 测试失败，在未修改的 Gitee 基线中同样复现；另有 2 项因本机缺少 MySQL Connector 无法执行，均未作为本次已通过的检查。
