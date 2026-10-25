# 临时 MySQL 流水线演示

三行合成记录，仅验证执行链路，不代表真实业务。预期 A 类两行、数值合计 30.50；B 类一行、数值合计 30.00。

从仓库根目录执行：

```sh
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml
python scripts/run_sql_pipeline.py --project-dir examples/sql_pipeline_demo --config config.yaml --execute
```

默认使用执行环境的 Docker；也可在 Linux/Unix 执行环境通过 MYSQLD_PATH 指定预先准备的 MySQL 8.0 mysqld 二进制，auto 后端会使用它。用户无需提供已有数据库账号。

运行结果在本目录 outputs/runs/ 下，包括 tables/、source/、model/、manifest.json 与 run.json。原始数据保留，临时数据库在结束时自动删除。

## 生成可编辑 Power BI 工程

确认刚才的运行状态为 passed 且临时清理 completed 后，将下面 RUN_DIR 替换为该次输出的 run.json 所在目录（不含文件名）：

```sh
python scripts/generate_powerbi.py --run-dir "RUN_DIR" --plan examples/sql_pipeline_demo/powerbi_design_plan.yaml --output outputs/powerbi/SqlBiDemo
```

输出目录必须不存在。此计划设置 `launcher: false`，直接打开生成的 PBIP；在 Desktop 的“转换数据 → 管理参数”中将 DataRoot 设为工程 `data` 文件夹完整路径，关闭并应用，再刷新。检查未筛选时 3 / 60.50，筛选 A 后 2 / 30.50，并核对日期、标签和筛选联动。支持的组件已生成，无需逐项复制 DAX 或拖字段。

生成成功不代表 Desktop 已验收。详见 [自动生成说明](../../docs/PowerBI自动生成说明.md) 与 [主题与布局说明](../../docs/PowerBI设计升级说明.md)。
