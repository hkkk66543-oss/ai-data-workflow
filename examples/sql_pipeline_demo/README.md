# 临时 MySQL 流水线演示

三行合成记录，仅验证执行链路，不代表真实业务。预期 A 类两行、数值合计 30.50；B 类一行、数值合计 30.00。

从仓库根目录执行：

```sh
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

默认使用执行环境的 Docker；也可在 Linux/Unix 执行环境通过 MYSQLD_PATH 指定预先准备的 MySQL 8.0 mysqld 二进制，auto 后端会使用它。用户无需提供已有数据库账号。

运行结果在本目录 outputs/runs/ 下，包括 tables/、source/、model/、manifest.json 与 run.json。原始数据保留，临时数据库在结束时自动删除。
