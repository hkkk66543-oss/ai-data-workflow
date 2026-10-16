# SQL 自动执行：本地 MySQL 8.0

此入口把已确认业务口径、已生成并审核的 SQL 串成可重复调用的执行流程；它不调用大模型、不需要 OpenAI Key，不会自动猜测字段或生成 SQL。Navicat 可以继续用于查看数据，但不再是运行 SQL 的必经步骤。

## 需要准备的信息

- MySQL 所在地址（本机通常为 `127.0.0.1`）、端口（通常为 `3306`）。
- 项目专用数据库名、数据库用户名。
- 仅在本机设置密码环境变量，默认名 `MYSQL_PASSWORD`。
- 真实原始文件、原始列与 ODS 字段对应关系、已确认的指标口径。
- 真实 ODS/DWD/ADS SQL、明确返回通过/失败的校验查询，以及需交付的导出查询。

数据库账号必须能读写项目库及执行已审核 SQL 所需的 DDL；自动建库仅在显式设置 `create_if_missing: true` 且账号有对应权限时使用。不要使用生产业务库作为试运行目标。不要把密码、原始数据或本地配置提交到 Git。

连接只能发生在实际运行此程序的机器能访问到的 MySQL 上。推荐在安装 MySQL 的 Windows 电脑本地运行；云端聊天不能通过 `127.0.0.1` 连接你的电脑。

## 第一次运行

在项目根目录，用 Python 3.10 或更新版本：

```powershell
python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.local.yaml
```

填写 `config.local.yaml` 的 `database` 和 `sql_pipeline` 部分。示例中的空列表表示尚未配置；母版没有真实业务 SQL，预览会明确失败，而不会虚报成功。

密码只存当前 PowerShell 进程环境，可用隐藏输入：

```powershell
$pipelineSecret = Read-Host "MySQL 密码" -AsSecureString
$pipelinePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pipelineSecret)
try {
    $env:MYSQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pipelinePtr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pipelinePtr)
    Remove-Variable pipelineSecret, pipelinePtr
}
```

预览只检查文件与计划，不连接 MySQL，也不检查数据库语法、权限、数据内容或网络连通性：

```powershell
python scripts/run_sql_pipeline.py
```

审核计划及 SQL 文件后，实际运行：

```powershell
python scripts/run_sql_pipeline.py --execute
```

结束后如不再使用，可移除密码环境变量：

```powershell
Remove-Item Env:MYSQL_PASSWORD
```

也可以通过电脑的环境变量设置界面配置自定义名称，再修改 `database.password_env`。`config.local.yaml` 不含密码。远程连接可以设置 `database.ssl_ca`，同时校验证书与主机名；本版本不包含 SSH 隧道配置。

## 文件及顺序

1. 读取配置，检查路径、标识符、脚本非空、校验与导出配置，记录文件 SHA-256。
2. `--execute` 时连接 MySQL，并取得数据库级流水线执行锁；同一数据库不允许两个本执行器并发运行。
3. 按文件名排序运行 `sql/01_ods/*.sql`，创建原始表。
4. 按 `imports` 顺序导入 `data/raw/` 下的 CSV/XLSX/JSON，核对导入行数。
5. 按文件名排序运行 `sql/02_dwd/*.sql`、`sql/03_ads/*.sql`。
6. 按配置顺序运行 `checks`，全部通过才导出。
7. 在同一只读一致性快照中按配置顺序运行 `exports`，写入本次运行的 CSV；全部导出成功后才把 `tables.partial` 改为 `tables`。一致性快照适用于 InnoDB 表，不能保证与外部程序的 DDL/非事务表并发修改一致。

层目录内的文件名建议带数字前缀；当前只扫描该层目录直属的 `.sql`，不递归。配置在 `exports` 中的 SQL 文件不在前面的分层执行阶段重复运行。导出查询建议独立放到 `sql/exports/`。

## 导入约定

先由审核过的 ODS SQL 明确字段类型，再导入数据；程序不擅自决定主键、金额类型或时间含义。

```yaml
imports:
  - file: data/raw/your_data.csv
    table: 原始_数据表
    encoding: utf-8-sig
    delimiter: ','
    null_values: ['']
    columns:
      source_id: 记录编号
      source_value: 指标值
```

- CSV 分块读取并使用参数化 INSERT，XLSX 和 JSON 整文件读入内存。JSON 必须为对象组成的数组，不支持嵌套字段。
- CSV/XLSX 默认按字符串读取，保留 `00123` 等编号；XLSX 中已被 Excel 存为数值而丢失的前导零不能恢复。`NA` 不会默认当成缺失；空字符串默认转为 NULL，可用 `null_values` 调整。
- 目标表必须为空；不提供自动追加、覆盖、跳过已导入或自动续跑。已有数据时停止，由你选择新项目库或审核清理方案。
- 每个文件导入后提交；InnoDB 文件导入失败时尝试回滚尚未提交的插入。之前成功的文件与 DDL 不会一起回滚。
- 这不是 SQL 沙箱。ODS 等脚本本身如果有 DROP/TRUNCATE/DELETE，仍会按审核后的代码执行；“表非空拒绝导入”不阻止 ODS SQL 提前清空表。

## 校验必须有明确通过条件

`checks` 只执行明确配置的查询；不会把 `sql/04_checks/` 下任意查询的成功运行当作业务通过。`check_all.sql` 当前是注释模板，不能替代真实业务校验。

```yaml
checks:
  - name: 主键重复检查
    sql_file: sql/04_checks/01_unique.sql
    expect: zero_rows
  - name: 汇总差额检查
    sql_file: sql/04_checks/02_reconcile.sql
    expect: scalar_equals
    value: 0
```

- `zero_rows`：查询列出异常记录，返回零行才通过。
- `scalar_equals`：只能返回一行一列，且结果等于 `value` 才通过；空结果、NULL（期望非 NULL 时）和多行/多列都失败。
- 小数比较采用 Decimal，业务允许误差时在 SQL 中明确 ROUND 或容差，不能随意放宽。
- SQL 中没有异常不代表口径正确。需要按真实业务配置主键、缺失、关联基数、原始到清洗行数及明细到汇总勾稽等校验。

校验/导出文件只支持单条以 SELECT 开头的查询；如需复杂逻辑，可先在前面层中建表或视图，再查询。它们是审核过的代码，不提供恶意 SQL 的权限隔离；SELECT 也可能调用函数，因此仍应使用项目专用账号。

## 导出与运行结果

```yaml
exports:
  - name: 应用_概览
    sql_file: sql/exports/overview.sql
```

每次运行独立输出 `outputs/runs/<UTC时间_随机编号>/`：

- `run.json`：预览或执行状态、输入校验和、SQL 文件/语句序号、耗时、导入/导出行数及校验结果。
- `tables/*.csv`：仅在本次所有校验与导出成功后存在，可作为 Power BI 数据源。CSV 使用 UTF-8 BOM，字段值原样导出；NULL 在 CSV 中表示为空。
- `tables.partial/`：导出中途失败时可能存在，仅供排错，不是成功交付。

状态 `preview_only` 不等于执行成功；仅 `passed` 代表这次执行完整通过。失败退出码为 1，成功/预览退出码为 0。每次路径不同，不自动更新 Power BI 数据源；BI 自动刷新不在本次范围。

运行报告不写数据库密码、完整 SQL、异常行或驱动原始错误文本。数据库错误通过错误类型、MySQL errno/sqlstate、最后一个步骤的文件与语句序号定位；结合 SQL 文件在本地排查。运行目录已加入 `.gitignore`。

## 失败和重复运行

MySQL DDL 会隐式提交，因此失败不能保证整条流水线回滚。修复前先检查已完成步骤；不要直接无限重试。默认执行全部层，不从中间自动恢复。建议第一次使用新的项目库。

本版本不自动调用大模型改 SQL 或自动重跑，不支持 `DELIMITER`、存储过程脚本、客户端 `SOURCE` 命令和执行注释。SQL 中禁止 `USE` 以及建库/删库语句；库由配置选择，但这不等于能阻止所有跨库 SQL，应审核脚本并限制账号权限。

## 验证范围

```powershell
python -m unittest discover -s tests -v
```

测试使用模拟数据库驱动覆盖分层顺序、导入、字符串处理、失败阻断、校验、执行锁与 CSV 导出；没有连接你的 MySQL，也不能替代 MySQL 8.0 实机联调。第一次实际运行需要检查建表类型、中文标识符、SQL 方言、账号权限和结果口径。
