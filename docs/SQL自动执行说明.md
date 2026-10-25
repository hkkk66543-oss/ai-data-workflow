# SQL 自动执行：临时 MySQL 8.0，保留结果与建模产物

此入口把已确认业务口径、已生成并审核的 SQL 串成可重复调用的执行流程；它不调用大模型、不需要 OpenAI Key，不会自动猜测字段或生成 SQL。Navicat 可以继续用于查看数据，但不再是运行 SQL 的必经步骤。

## 默认方式：临时 MySQL

你需要提供真实数据和确认分析口径，不需要提供现有数据库地址、用户名或密码。执行环境自动创建一次性 MySQL 8.0、随机凭据及项目专用账号；运行结束后关闭并删除这个实例，保留产物和原始文件。

执行环境需要 Python 3.10+，以及下面两种条件之一：

- Docker 客户端与已运行的 Docker 引擎，且能拉取 `mysql:8.0.46`。端口只发布到 `127.0.0.1` 的随机端口，不占用原来的 3306。无需预先启动 MySQL 容器。
- Linux/Unix 中已准备好 MySQL 8.0 的官方 `mysqld` 二进制及其动态库。通过 `MYSQLD_PATH` 或 `temporary_mysql.mysqld_path` 指定。程序为每次运行新建私有临时数据目录，不安装系统服务，不复用旧数据目录。

这里的“执行环境”可以是云端开发环境或 CI 运行器，不必是你的电脑。当前聊天是否能执行，要以真实运行条件与测试结果为准，不能仅因代码已生成就称为已运行。程序不会自动下载/安装 Docker 或 MySQL 二进制，不会降级到 DuckDB、MariaDB 或模拟执行。

```yaml
database:
  mode: temporary
  name: analysis_run
temporary_mysql:
  backend: auto
  image: mysql:8.0.46
  startup_timeout: 120
  # mysqld_path: /opt/mysql/bin/mysqld
  # transport: unix  # native 默认 Unix socket；不支持 AF_UNIX 的环境可用 tcp
```

`auto` 优先使用配置或环境变量给定的 mysqld，否则用 Docker；如果指定的方式不可用，报错停止。Docker 镜像记录实际 image ID，服务器还会通过 `SELECT VERSION()` 验证为 MySQL 8.0；不是 8.0 就拒绝执行业务 SQL。

原生进程默认关闭 TCP，仅使用私有目录中的 Unix socket。配置 `transport: tcp` 时改用回环随机端口并禁用 Unix socket，通过权限为 600 的私有启动文件在监听客户端之前设置随机 root 密码，文件随临时目录删除。临时凭据只用于此次实例，不写进项目配置、命令行参数或交付报告；Docker 管理员仍能检查容器环境，不应把不可信用户作为执行环境管理员。

## 如何运行

```powershell
python -m pip install -r requirements.txt
python scripts/run_sql_pipeline.py
python scripts/run_sql_pipeline.py --execute
```

以下 imports/checks/exports 示例分别展示 `sql_pipeline` 的子项；填写实际配置时合并在同一个 `sql_pipeline` 下，避免重复定义顶层键。

默认配置是 `config.example.yaml`。真实项目应根据已经确认的数据字典生成各层 SQL，并明确填写 `sql_pipeline.imports/checks/exports`；可复制为忽略提交的 `config.local.yaml`，通过 `--config config.local.yaml` 使用。空母版预览会失败，不会把没有执行的数据当成真实结果。

预览只检查文件和计划，不启动容器/进程、不连接数据库、不检查实际 SQL 语法或数据内容。实际执行须使用 `--execute`，并审核目标项目、SQL 和输入文件。

先验证随附演示（合成数据，不是用户业务数据）：

```powershell
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

## 可选：已有本地/远程 MySQL

仅选择 `existing` 模式时才需要数据库连接信息：

```yaml
database:
  mode: existing
  host: 127.0.0.1
  port: 3306
  name: your_project_db
  user: your_project_user
  password_env: MYSQL_PASSWORD
  create_if_missing: false
  # ssl_ca: C:/certs/ca.pem
```

账号需具备项目库及已审核 SQL 所需权限；`create_if_missing: true` 需要建库权限。程序不会关闭或删除已有数据库。已有库也必须是 MySQL 8.0，验证不通过则不执行 SQL。

密码仅在运行电脑配置，不能提交到 Git 或发到聊天。例如当前 PowerShell 隐藏输入：

```powershell
$pipelineSecret = Read-Host "MySQL 密码" -AsSecureString
$pipelinePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pipelineSecret)
try {
    $env:MYSQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pipelinePtr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pipelinePtr)
    Remove-Variable pipelineSecret, pipelinePtr
}
python scripts/run_sql_pipeline.py --config config.local.yaml --execute
Remove-Item Env:MYSQL_PASSWORD
```

远程连接可配置 `ssl_ca` 并验证主机名和证书；本版本不包含 SSH 隧道。云端 `127.0.0.1` 不能连接你的个人电脑。用户主要需要结果时优先使用临时模式，避免此连接负担。

## 文件及顺序

1. 读取配置，检查路径、标识符、脚本非空、校验与导出配置，记录文件 SHA-256。
2. `--execute` 时先保存 SQL 源码，再启动临时实例（或连接已有库），验证真实版本并取得执行锁。
3. 按文件名排序运行 `sql/01_ods/*.sql`，创建原始表。
4. 按 `imports` 顺序导入 `data/raw/` 下的 CSV/XLSX/JSON，核对导入行数。
5. 按文件名排序运行 `sql/02_dwd/*.sql`、`sql/03_ads/*.sql`。
6. 按配置顺序运行 `checks`，全部通过才导出。
7. 在同一只读一致性快照中按配置顺序运行 `exports`，写入 `tables.partial`。一致性快照适用于 InnoDB 表，不能保证与外部程序的 DDL/非事务表并发修改一致。
8. 从真实 INFORMATION_SCHEMA / SHOW CREATE TABLE 保存字段、表结构和显式外键。关闭连接、清理此次临时环境成功后，才发布 `tables` 并生成产物清单；全过程完成后标为 passed。

层目录内的文件名建议带数字前缀；当前只扫描该层目录直属的 `.sql`，不递归。配置在 `exports` 中的 SQL 文件不在前面的分层执行阶段重复运行。导出查询建议独立放到 `sql/exports/`。

## 导入约定

先由审核过的 ODS SQL 明确字段类型，再导入数据；程序不擅自决定主键、金额类型或时间含义。

```yaml
sql_pipeline:
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
sql_pipeline:
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
sql_pipeline:
  exports:
    - name: 应用_概览
      sql_file: sql/exports/overview.sql
```

每次运行独立输出 `outputs/runs/<UTC时间_随机编号>/`：

- `run.json`：预览或执行状态、输入校验和、SQL 文件/语句序号、耗时、导入/导出行数、校验结果、真实 MySQL 版本与清理状态。
- `tables/*.csv`：明确配置的结果查询，只有校验、导出、模型保存与临时清理成功后交付，可作为 Power BI 数据源。不默认导出库中每张原始表；需要明细时把对应 SELECT 加入 exports。CSV 使用 UTF-8 BOM，字段值原样导出；NULL 在 CSV 中表示为空。
- `tables.partial/`：导出或后续产物/清理步骤失败时可能存在，不是成功交付。
- `source/sql/`：本次 SQL 文件的原始字节副本（不是仅有文件名），可追溯实际执行逻辑。`source/imports.json` 保存原始文件哈希和原始列到 ODS 字段的映射；不复制连接密码或真实原始数据。若存在，另保存数据字典、指标口径等文档。
- `model/fields.csv`：实际字段名、类型、顺序、可空、默认值、键标识、额外属性、注释，以及已明确的原始字段来源。
- `model/model.json`：实际表、字段及数据库显式声明的外键。不根据名字猜业务关系，也不声称自动完成 DWD/ADS 字段血缘解析；加工逻辑保存在 SQL 中。
- `model/schema.sql`：实际 SHOW CREATE TABLE/VIEW 定义。视图含服务器定义信息，复杂视图依赖和 DEFINER 等恢复条件仍需检查，不保证跨环境直接恢复。
- `manifest.json`：源代码、模型和结果产物的文件路径、字节数及 SHA-256。

状态 `preview_only` 不等于执行成功；仅 `passed` 代表这次执行完整通过。临时模式还需检查 runtime.cleanup 为 completed。失败退出码为 1，成功/预览退出码为 0。本次通过校验的目录可交给 `scripts/generate_powerbi.py` 自动生成数据接入、模型及报表，见 [Power BI 自动生成说明](PowerBI自动生成说明.md)。SQL 执行器本身不更新既有 PBIP 的数据源，也不执行 Desktop 刷新。

运行报告不写数据库密码、完整 SQL、异常行或驱动原始错误文本。数据库错误通过错误类型、MySQL errno/sqlstate、最后一个步骤的文件与语句序号定位；结合 SQL 文件在本地排查。运行目录已加入 `.gitignore`。

## 失败、清理和重复运行

临时模式每次创建全新数据目录/容器，因此无需清理上次的 ODS 表。成功、SQL 报错、校验失败、启动失败与可捕获的中断都会尝试清理，只处理此次实例，不运行 docker prune，不触碰已有库。Docker 镜像缓存不删除；容器及本实例匿名数据卷删除。

清理失败会在报告中标记，不能称为完整成功。宿主机掉电、进程被强制 SIGKILL 或 Docker 服务中断时无法保证立即清理；根据报告中本次 container_name 定位并只删除该实例，原生模式检查此次 mysqld 进程及私有临时目录。错误报告/源码已保留，失败不生成成功交付表；模型仅在计算及校验通过后提取，不承诺失败时仍可恢复整个临时数据库。

已有库模式失败不能回滚全部 MySQL DDL 和已提交步骤；先检查实际状态，不要盲目重跑。默认执行全部层，不从中间自动恢复。

本版本不自动调用大模型改 SQL，不支持 DELIMITER、存储过程脚本、客户端 SOURCE 命令及执行注释。SQL 中禁止 USE 和建库/删库语句；项目账号权限仅限项目库，但执行器不是不可信 SQL 沙箱。原生二进制/容器运行应在可信执行环境内进行。数据库初始化错误的原始服务日志不作为交付，避免包含凭据；保留安全错误摘要和服务版本。

## 验证范围

```powershell
python -m unittest discover -s tests -v
```

默认验证执行契约与临时环境生命周期（模拟驱动/模拟 Docker）。设置 MYSQLD_PATH 后，额外运行真实 MySQL 8.0 的成功、校验失败和 SQL 错误测试，检查导出数值、字段类型、外键、源码与清理。可用 MYSQL_NATIVE_TRANSPORT=tcp 指定测试传输方式。Docker 分支需要有 Docker 的环境另行实测，不能用原生进程测试冒充容器实测。
