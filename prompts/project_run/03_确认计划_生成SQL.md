# 03 确认计划：生成 SQL

请只执行本阶段。执行前必须确认用户已经认可 `docs/执行计划.md` 和 `docs/指标口径.md`。

任务：

1. 基于真实字段生成 MySQL 8.0 SQL。
2. SQL 文件按分层保存：
   - `sql/01_ods/`
   - `sql/02_dwd/`
   - `sql/03_ads/`
   - `sql/04_checks/`
3. 表名和字段名默认使用简约中文，并用反引号包裹。
4. 所有表和字段必须加中文注释。
5. 生成或更新 `docs/SQL中文命名规范.md`。
6. 生成或更新 `docs/SQL中英文命名映射表.md`。

命名规则：

- ODS：`原始_事件表`、`原始_订单表`、`原始_用户表`
- DWD：`清洗_事件明细`、`清洗_订单明细`、`清洗_用户画像`
- DIM：`维度_设备`、`维度_地区`、`维度_产品`
- ADS：`应用_每日概览`、`应用_用户分层`、`应用_渠道分析`
- CHECK：`校验_数据质量明细`、`校验_指标汇总`

字段示例：

- user_id -> `用户编号`
- session_id -> `会话编号`
- event_type -> `事件类型`
- event_time -> `事件时间`
- total_users -> `用户数`
- abnormal_rate -> `异常率`

SQL 生成后必须说明：

- 生成了哪些中文表。
- 每张中文表对应什么业务含义。
- 每张表由哪些原始字段加工而来。
- 哪些字段是清洗字段。
- 哪些字段是异常标记字段。
- 哪些表适合导入 Power BI。

SQL 自动执行交付：

1. 阅读 `docs/SQL自动执行说明.md`。
2. 根据真实原始数据、ODS 字段、业务口径，填写配置的 imports/checks/exports，默认 database.mode: temporary；无需用户数据库账号。仅自选 existing 时配置连接，不写入密码。
3. 校验查询放 `sql/04_checks/`，必须配置 zero_rows 或 scalar_equals；导出查询建议放 `sql/exports/`，只包含一条 SELECT。
4. 运行 `python scripts/run_sql_pipeline.py` 检查计划；没有真实 SQL 或校验时应失败，不能将母版注释当作已执行。
5. 用户已确认项目与 SQL、且执行环境支持临时 MySQL 时，运行 `python scripts/run_sql_pipeline.py --execute`；顺序为 ODS → 导入 → DWD → ADS → 校验 → 导出。
6. 读取本次 run.json，报告真实 MySQL 版本与清理状态；失败按文件及语句序号排错，不自动重跑。结果在 tables/、建模字段/DDL 在 model/、SQL 源码在 source/sql/。
7. 执行环境不支持临时 MySQL 或尚无执行授权时，说明缺少条件；不默认要求连接用户本机、不要求提供密码。existing 模式仅在用户选择时使用。

阶段结束时必须输出：

```text
下一步是否需要你手动操作：
如果需要，具体操作是什么：
操作完成后，请回复我什么：
```
