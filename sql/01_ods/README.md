# ODS 层 SQL

用于保存原始层建表和装载 SQL。

规则：

- 保留原始字段和原始粒度。
- 不在 ODS 层做业务清洗。
- 字段名不明确时在注释中标注“待确认”。

## 执行与产物

本层先建表，再由 `sql_pipeline.imports` 导入原始文件并核对行数。由 `scripts/run_sql_pipeline.py` 在默认临时 MySQL 8.0 中自动执行，无需逐层复制到 Navicat。先预览，确认 SQL 后执行；SQL 源码、结果及字段定义保存在本次运行目录，详见 [SQL 自动执行说明](../../docs/SQL自动执行说明.md)。
