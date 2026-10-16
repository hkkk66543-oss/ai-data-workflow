# Power BI 生成验证记录

日期：2026-10-16。对象：SqlBiDemo，SQL run `20261016T023517Z_e55f4886` 的三行合成数据。

- 12 项新增生成器测试通过（含实际 PowerShell 准备路径、Unicode/空格目录、重复运行）。全套 37 项中 34 项通过，3 项真实 MySQL 测试因本次未配置 MYSQLD_PATH 而跳过；前一阶段已有真实 MySQL 验证记录。
- 11 份生成 JSON 文档通过 Microsoft 官方公开 JSON Schema 校验：PBIP、report、page、pages、version、6 个 visual。Schema 来自 developer.microsoft.com/json-schemas/fabric，引用一并解析。
- Microsoft.AnalysisServices 19.118.3 的真实 TmdlSerializer 成功反序列化：1 表、4 字段、2 度量值、0 关系；sourceColumn 与 CSV 表头一致。
- PowerShell 7.6.7 实际执行 PrepareAndOpen.ps1 -PrepareOnly，正确设置 DataRoot。未在 Windows cmd.exe 中运行启动器，未启动 Desktop。
- 使用 Power BI 插件模型向导生成了规划草稿。其自动猜测的维度没有写入实际工程；示例只使用真实导出的表和显式指定的指标。
- 插件 UnifiedReview -SkipLive 在 Linux 环境失败：其依赖间接调用 Win32_Process/Get-CimInstance。未将此结果记录为通过，未模拟 Windows API 绕过。以上官方 Schema/TOM 检查独立执行。

尚未完成：Power BI Desktop 打开、Power Query 刷新、DAX 实际求值、图表显示与联动。生成工程保持 draft、desktop_validated=false。预计值仅用于后续对账：记录数 3，数值合计 60.50，A 30.50，B 30.00。
