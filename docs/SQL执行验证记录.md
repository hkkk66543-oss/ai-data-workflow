# 临时 MySQL 执行验证记录

本文是指定环境与日期的验证快照；当前操作方法见 [SQL 自动执行说明](SQL自动执行说明.md)。新的业务数据、SQL 和执行环境须独立验证。

验证日期：2026-10-16。数据：`examples/sql_pipeline_demo/` 中三行合成记录，仅验证程序行为，不代表真实业务成果。

## 实际环境

- MySQL Community Server 8.0.46，Linux x86_64，官方最小二进制包。
- 原生临时进程，私有临时数据目录，仅回环 TCP，随机端口和随机凭据。
- 当前执行环境不支持 AF_UNIX，使用 `temporary_mysql.transport: tcp`；没有 Docker 引擎。
- 本次真实运行：25 项测试通过，其中 3 项使用真实 MySQL 8.0；Docker 启停命令与清理范围采用模拟测试，不声称容器已实测。

## 正常链路

ODS 建表 → 导入三条记录（保留编号前导零）→ 类别维度/清洗明细 → ADS 类别汇总 → 主键和汇总勾稽校验 → 两张 CSV → 建模字段与 DDL → 源码及清单 → 删除临时实例。

| 类别 | 记录数 | 数值合计 |
| --- | ---: | ---: |
| A | 2 | 30.50 |
| B | 1 | 30.00 |

数据库实际提取：4 张表、12 个字段、1 条显式外键。原始编号 `001` 导出后仍为 `001`。正常结果状态 passed，runtime.cleanup 为 completed，临时进程和数据目录均已清理。

## 失败链路

- 将汇总校验期望值改错：真实 MySQL 校验失败，保留 SQL/运行报告，不发布 tables，临时实例清理完成。
- SQL 查询不存在的字段：真实 MySQL 返回错误 1054，记录具体 SQL 文件与语句序号，不执行后续交付，临时实例清理完成。
- 模拟模型保存失败/容器清理失败：不发布成功 tables；清理失败在报告中明确标记。
- 模拟容器操作核对：密码不在命令行参数中，只发布回环端口，只删除本次容器及匿名卷，不执行全局 prune。

## 复现

先安装项目 requirements。在支持 Docker 的执行环境直接运行演示；Linux/Unix 已准备官方二进制时，可设置 MYSQLD_PATH。真实集成测试还支持 MYSQL_NATIVE_TRANSPORT=tcp；所需动态库由执行环境准备。

```sh
python -m unittest discover -s tests -v
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

不配置 MYSQLD_PATH 时，3 项真实集成测试会明确跳过；不能将跳过计为实测通过。用户真实数据与生成的业务 SQL 尚未提供，业务结果验证需在下一次实际项目执行中完成。
