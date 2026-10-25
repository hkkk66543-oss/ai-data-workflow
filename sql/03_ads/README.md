# ADS 层 SQL

用于保存分析汇总层 SQL。

规则：

- 每张 ADS 表对应一个明确业务问题。
- 指标必须引用 `docs/指标口径.md`。
- SQL 注释必须写清楚统计周期、粒度和过滤条件。

## 执行与产物

本层在 DWD 后执行；校验通过后按 `sql_pipeline.exports` 导出所需结果，供 Power BI 工程生成。由 `scripts/run_sql_pipeline.py` 在默认临时 MySQL 8.0 中自动执行，无需逐层复制到 Navicat。先预览，确认 SQL 后执行；SQL 源码、结果及字段定义保存在本次运行目录，详见 [SQL 自动执行说明](../../docs/SQL自动执行说明.md)。
